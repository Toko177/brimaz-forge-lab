package forge.ai;

import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * V36 CHALLENGER: conditional, high-precision strategic interventions.
 *
 * V35 used broad role scores and a hypothetical next turn as if its abstract
 * forecast were a reason to override actual Forge AI. This policy ABSTAINS
 * unless a narrow play-order benefit is derivable from already known cards.
 *
 * A proposal is NOT payment, casting, card-resolution or Magic legal proof:
 * patched AiController still calls its original canPlayAndPayFor.
 */
public final class MultiplayerEvidenceGateV36 {
    private MultiplayerEvidenceGateV36() {}
    // Mana production next turn requires a known noncreature rock. Do not
    // count summoning-sick Myr / mana dorks or mana of unknown colors.
    private static final Set<String> ONE_MANA_ROCKS=Set.of(
        "Arcane Signet","Fellwar Stone","Mind Stone","Thought Vessel",
        "Talisman of Hierarchy","Orzhov Signet","Commander's Sphere");
    private static final Set<String> TWO_MANA_ROCKS=Set.of("Sol Ring");

    public record Evidence(MultiplayerStrategicSearchV35.CardPlan selected,
                           String reason,int candidatesInspected) {}
    public static int optimisticNextTurnRockMana(String name) {
        if(TWO_MANA_ROCKS.contains(name))return 2;
        if(ONE_MANA_ROCKS.contains(name))return 1;
        return 0;
    }
    /**
     * Pure, falsifiable comparison on visible board + our own known cards.
     * Returns null when observations are insufficient to justify overriding
     * the much broader original Forge AI.
     */
    public static Evidence choose(MultiplayerStrategicSearchV35.Table table,
                                  List<MultiplayerStrategicSearchV35.CardPlan> plans,
                                  int realCreatureTokens) {
        if(table==null || plans==null || plans.size()<2 || plans.size()>64
             || realCreatureTokens<0)return null;
        // We cannot establish legal blockers or survival from opponent power.
        // Under significant pressure preserve Forge's own combat-aware AI.
        if(MultiplayerStrategicSearchV35.underThreat(table))return null;
        List<MultiplayerStrategicSearchV35.CardPlan> affordable=new ArrayList<>();
        MultiplayerStrategicSearchV35.CardPlan knownCommander=null;
        boolean knownPhyrexian=false;
        for(var card:plans) {
            if(card==null)continue;
            if(card.role()==MultiplayerStrategicModel.Role.COMMANDER
                    && card.name().equals("Brimaz, Blight of Oreskos"))
                knownCommander=card;
            if(card.has(MultiplayerStrategicSearchV35.PHYREXIAN_CAST))
                knownPhyrexian=true;
            // Conservative: never take a speculative action costing more
            // than a current estimated mana resource.
            if(card.forgeTimingLegal() && card.cost()<=table.mana())
                affordable.add(card);
        }
        if(affordable.size()<2)return null;
        // Brimaz must already be on the battlefield for the Incubate cast
        // trigger. Future known Phyrexian cards never imply extra draws.
        if(!table.commanderPresent() && knownCommander!=null
             && knownPhyrexian && affordable.contains(knownCommander)
             && realCreatureTokens>=0) {
            return new Evidence(knownCommander,"BRIMAZ_BEFORE_KNOWN_PHYREXIAN",
                                affordable.size());
        }
        // Public cast trigger and type are known; don't hallucinate a
        // completed transform or usable sacrifice fodder.
        if(table.commanderPresent()) {
            for(var card:affordable) {
                if(card.role()==MultiplayerStrategicModel.Role.CREATURE
                    && card.has(MultiplayerStrategicSearchV35.PHYREXIAN_CAST))
                    return new Evidence(card,"KNOWN_PHYREXIAN_INCUBATE_CAST",
                                        affordable.size());
            }
        }
        if(!table.commanderPresent() && knownCommander!=null) {
            int withoutRamp=table.lands()+(table.handLands()>0?1:0);
            // This plan is relevant only when the known next-turn land
            // + rock unlocks the commander's printed mana value. Command
            // tax and colored costs are intentionally checked by Forge later.
            if(withoutRamp<knownCommander.cost()) {
                for(var card:affordable) {
                    int boost=optimisticNextTurnRockMana(card.name());
                    if(boost>0 && withoutRamp+boost>=knownCommander.cost())
                        return new Evidence(card,"KNOWN_COMMANDER_MANA_UNLOCK",
                                            affordable.size());
                }
            }
        }
        return null;
    }

    public static List<SpellAbility> rank(Player ai,List<SpellAbility> available) {
        if(!MultiplayerStrategicSequencerV35.enabledFor(ai)
            || ai==null || ai.getGame()==null || available==null
            || available.size()>120 || available.size()<2)return List.of();
        var phase=ai.getGame().getPhaseHandler();
        if(!phase.isPlayerTurn(ai) ||
           !(phase.is(PhaseType.MAIN1)||phase.is(PhaseType.MAIN2))
           || !ai.getGame().getStack().isEmpty())return List.of();
        var t=MultiplayerStrategicSequencerV35.observe(ai);
        List<MultiplayerStrategicSearchV35.CardPlan> cards=new ArrayList<>();
        List<SpellAbility> spells=new ArrayList<>();
        Set<Card> seen=new HashSet<>();
        int liveCreatureTokens=0;
        for(Card c:ai.getCardsIn(ZoneType.Battlefield)) {
            if(c.isToken() && c.isCreature())liveCreatureTokens++;
        }
        for(SpellAbility sa:available) {
            if(sa==null || sa.getHostCard()==null || !sa.isSpell()
                 || sa.isCopied() || sa.isLandAbility() || sa.usesTargeting())
                continue;
            Card c=sa.getHostCard();
            if((!c.isInZone(ZoneType.Hand) && !c.isInZone(ZoneType.Command))
                 || !(c.isCreature()||c.isArtifact()||c.isEnchantment()
                     ||c.isPlaneswalker()) || !seen.add(c))continue;
            sa.setActivatingPlayer(ai);
            var card=MultiplayerStrategicSequencerV35.describeCard(
                c,sa.canPlay() && sa.canCastTiming(ai));
            cards.add(card);
            spells.add(sa);
            if(cards.size()>=64)break;
        }
        Evidence e=choose(t,cards,liveCreatureTokens);
        if(e==null)return List.of();
        int idx=cards.indexOf(e.selected());
        if(idx<0)return List.of();
        // Both formats are intentional: old audit validates Forge's approved
        // action, and a separate V36 log exposes the evidence category.
        System.out.println("FOUR_AI_V36_EVIDENCE player="+ai.getName()
             +" turn="+phase.getTurn()+" reason="+e.reason()
             +" card="+e.selected().name()
             +" inspected="+e.candidatesInspected()
             +" creatureTokens="+liveCreatureTokens
             +" confirmedByForgePending=true");
        System.out.println("FOUR_AI_V35_WINDOW player="+ai.getName()
             +" turn="+phase.getTurn()+" rawAbilities="+available.size()
             +" eligiblePerms="+cards.size()+" estimatedMana="+t.mana()
             +" ranked=1 best="+e.selected().name()
             +" plannedSecond=none plannedNext=none searchNodes=0"
             +" immediateForgeApprovalPending=true");
        return List.of(spells.get(idx));
    }
}
