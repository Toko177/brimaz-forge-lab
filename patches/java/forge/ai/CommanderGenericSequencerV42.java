package forge.ai;

import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Forge bridge for V42, deliberately independent of Brimaz, deck IDs and
 * opponent identities. No hidden opponent zones, fabricated stack entries,
 * modified payment, scripted Magic rules or non-interactive casting.
 */
public final class CommanderGenericSequencerV42 {
    private CommanderGenericSequencerV42() {}

    public static boolean enabled() {
        return Boolean.getBoolean("commander.v42GeneralPolicy");
    }

    /** Only the controlled opt-in arm may use the new policy. */
    public static boolean eligible(Player ai) {
        return enabled() && ai != null && ai.getGame() != null;
    }

    private static boolean producesMana(Card c) {
        // Forge's genuine printed/granted abilities, not an Oracle-text
        // substring or a fixed list of mana rocks.
        for (SpellAbility ability : c.getSpellAbilities()) {
            if (ability != null && ability.getApi() == ApiType.Mana)
                return true;
        }
        return false;
    }

    private static CommanderGenericModelV42.Kind kind(Card c) {
        if (c.isCommander())return CommanderGenericModelV42.Kind.COMMANDER;
        if (c.isCreature())return CommanderGenericModelV42.Kind.CREATURE;
        if (c.isArtifact())return CommanderGenericModelV42.Kind.ARTIFACT;
        if (c.isEnchantment())return CommanderGenericModelV42.Kind.ENCHANTMENT;
        return CommanderGenericModelV42.Kind.PLANESWALKER;
    }

    private static CommanderGenericModelV42.State observe(Player ai) {
        int lands=0,creatures=0,blockers=0;
        boolean commanderPresent=false;
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (c.isLand())lands++;
            if (c.isCommander())commanderPresent=true;
            if (c.isCreature()) {
                creatures++;
                if (!c.isTapped() && c.getNetToughness()>0)blockers++;
            }
        }
        int[] enemy={0,0,0};int index=0;
        for (Player opponent : ai.getOpponents()) {
            if(index==3)break;
            int power=0;
            for (Card c : opponent.getCardsIn(ZoneType.Battlefield)) {
                if (c.isCreature() && c.getNetPower()>0)
                    power += Math.min(20,c.getNetPower());
            }
            enemy[index++]=Math.min(200,power);
        }
        return new CommanderGenericModelV42.State(
                ai.getGame().getPhaseHandler().getTurn(),
                Math.max(0,ComputerUtilMana.getAvailableManaEstimate(ai,true)),
                lands,ai.getLife(),ai.getCardsIn(ZoneType.Hand).size(),
                creatures,blockers,commanderPresent,
                enemy[0],enemy[1],enemy[2]);
    }

    /**
     * Non-targeting, known hand or command-zone permanents only.
     * The original AiController.canPlayAndPayFor() is still the definitive
     * independent permission gate. Never propose instants or interaction
     * in place of stock Forge.
     */
    public static List<SpellAbility> rank(Player ai,List<SpellAbility> available) {
        if (!eligible(ai) || available == null || available.size()<2
                || available.size()>120
                || ai.getCardsIn(ZoneType.Battlefield).size()>100)return List.of();
        var game=ai.getGame();
        var phase=game.getPhaseHandler();
        if (!phase.isPlayerTurn(ai)
                || !(phase.is(PhaseType.MAIN1) || phase.is(PhaseType.MAIN2))
                || !game.getStack().isEmpty())return List.of();

        List<CommanderGenericModelV42.Candidate> candidates=new ArrayList<>();
        Map<CommanderGenericModelV42.Candidate,SpellAbility> sources=
                new IdentityHashMap<>();
        Set<Card> seen=java.util.Collections.newSetFromMap(new IdentityHashMap<>());
        for (SpellAbility sa:available) {
            if(sa==null || !sa.isSpell() || sa.isCopied()
                    || sa.usesTargeting() || sa.isLandAbility()
                    || sa.getHostCard()==null)continue;
            Card c=sa.getHostCard();
            if(!c.isInZone(ZoneType.Hand) && !c.isInZone(ZoneType.Command))
                continue;
            if(!(c.isCreature() || c.isArtifact() || c.isEnchantment()
                    || c.isPlaneswalker()) || !seen.add(c))continue;
            sa.setActivatingPlayer(ai);
            boolean playable=sa.canPlay() && sa.canCastTiming(ai)
                    && ComputerUtilCost.canPayCost(sa,ai,false);
            CommanderGenericModelV42.Candidate candidate=
                new CommanderGenericModelV42.Candidate(
                    c.getName(),kind(c),Math.max(0,c.getCMC()),
                    c.isCreature()?Math.max(0,c.getNetPower()):0,
                    c.isCreature()?Math.max(0,c.getNetToughness()):0,
                    producesMana(c),playable);
            candidates.add(candidate);
            sources.put(candidate,sa);
            if(candidates.size()>=24)break;
        }
        if(candidates.size()<2)return List.of();
        var state=observe(ai);
        var decision=CommanderGenericModelV42.decide(state,candidates);
        List<SpellAbility> ranked=new ArrayList<>();
        for(var candidate:decision.ranked()) {
            var sa=sources.get(candidate);
            if(sa!=null)ranked.add(sa);
        }
        System.out.println("FOUR_AI_V42_WINDOW player="+ai.getName()
                +" turn="+state.turn()+" options="+candidates.size()
                +" ranked="+ranked.size()+" margin="+decision.leadingMargin()
                +" pressure="+decision.underPressure()
                +" reason="+decision.reason()
                +" nativeForgeApprovalPending=true");
        return ranked;
    }
}
