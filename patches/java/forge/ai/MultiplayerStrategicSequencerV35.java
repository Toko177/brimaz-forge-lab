package forge.ai;

import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Non-mutating V35 bridge. Do NOT simulate a Magic state or override Forge's
 * legality; only propose an ordered short list of actual known spell abilities.
 * AiController alone can approve them via stock canPlayAndPayFor(...).
 */
public final class MultiplayerStrategicSequencerV35 {
    private MultiplayerStrategicSequencerV35() {}

    public static final boolean ENABLED =
        Boolean.getBoolean("brimaz.v35StrategicSearch");
    /**
     * Controlled A/B: in v35_brimaz_duel only one seeded deck seat receives
     * new strategy, while the other three share the identical v17 baseline.
     * This still is NOT a duel against byte-identical upstream Forge.
     */
    public static boolean enabledFor(Player ai) {
        if(!ENABLED || ai==null)return false;
        if(!Boolean.getBoolean("brimaz.v35BrimazOnly"))return true;
        // Stable pinned Forge-deck display name ("Brimaz V3") is the
        // controller identity even when the commander leaves command zone.
        return ai.getName().contains("Brimaz");
    }
    private static final AtomicInteger WINDOWS=new AtomicInteger();
    private static final Set<String> MANA=Set.of(
        "Sol Ring","Arcane Signet","Orzhov Signet","Fellwar Stone","Mind Stone",
        "Thought Vessel","Talisman of Hierarchy","Talisman of Dominance",
        "Talisman of Progress","Talisman of Conviction","Ornithopter of Paradise",
        "Gold Myr","Marble Diamond","Charcoal Diamond","Commander's Sphere");
    private static final Set<String> OUTLETS=Set.of(
        "Spawning Pit","Ashnod's Altar","Phyrexian Altar",
        "Krark-Clan Ironworks","Altar of Dementia","Viscera Seer",
        "Carrion Feeder","Woe Strider","Yahenni, Undying Partisan",
        "Arcbound Ravager","Bartolomé del Presidio","Throne of Geth",
        "Yawgmoth, Thran Physician");
    private static final Set<String> PAYOFFS=Set.of(
        "Mirkwood Bats","Marionette Apprentice","Marionette Master",
        "Elas il-Kor, Sadistic Pilgrim","Vraan, Executioner Thane",
        "Scheming Aspirant","The Meathook Massacre","Athreos, God of Passage");
    private static final Set<String> DOUBLERS=Set.of(
        "Anointed Procession","Mondrak, Glory Dominus","Roaming Throne");
    private static final Set<String> TOKENS=Set.of(
        "Brimaz, Blight of Oreskos","Essence of Orthodoxy",
        "Norn's Inquisitor","Progenitor Exarch","Compleated Huntmaster",
        "Darksteel Splicer","Otharri, Suns' Glory",
        "Adeline, Resplendent Cathar","Caretaker's Talent");
    private static final Set<String> DRAW=Set.of(
        "Skullclamp","Phyrexian Arena","Esper Sentinel","Rhystic Study",
        "Mystic Remora","The One Ring","Idol of Oblivion",
        "Norn's Wellspring","Caretaker's Talent");
    private static final Set<String> RECURSION=Set.of(
        "Lurrus of the Dream-Den","Phyrexian Reclamation","Tortured Existence",
        "Myr Retriever","Vulpine Harvester","Phyrexian Delver");
    private static final Set<String> PROTECTION=Set.of(
        "Lightning Greaves","Swiftfoot Boots","Whispersilk Cloak",
        "Etchings of the Chosen");

    private static MultiplayerStrategicModel.Role role(Card c) {
        String name=c.getName();
        if(c.isCommander())return MultiplayerStrategicModel.Role.COMMANDER;
        if(MANA.contains(name))return MultiplayerStrategicModel.Role.RAMP;
        if(OUTLETS.contains(name))return MultiplayerStrategicModel.Role.SAC_OUTLET;
        if(TOKENS.contains(name))return MultiplayerStrategicModel.Role.TOKEN_ENGINE;
        if(DRAW.contains(name))return MultiplayerStrategicModel.Role.DRAW_ENGINE;
        if(PROTECTION.contains(name))return MultiplayerStrategicModel.Role.PROTECTION;
        if(c.isCreature())return MultiplayerStrategicModel.Role.CREATURE;
        if(c.isArtifact() || c.isEnchantment() || c.isPlaneswalker())
            return MultiplayerStrategicModel.Role.ENGINE;
        return MultiplayerStrategicModel.Role.OTHER;
    }

    private static int features(Card c) {
        String name=c.getName();
        int v=0;
        if(PAYOFFS.contains(name))v|=MultiplayerStrategicSearchV35.DEATH_PAYOFF;
        if(DOUBLERS.contains(name))v|=MultiplayerStrategicSearchV35.TOKEN_MULTIPLIER;
        if(TOKENS.contains(name))v|=MultiplayerStrategicSearchV35.INCUBATE_ENGINE;
        if(RECURSION.contains(name))v|=MultiplayerStrategicSearchV35.RECURSION;
        if(c.isCreature() && c.getType().hasCreatureType("Phyrexian"))
            v|=MultiplayerStrategicSearchV35.PHYREXIAN_CAST;
        if(c.getCMC()>=6 && !c.isCreature())v|=
            MultiplayerStrategicSearchV35.EXPENSIVE_NONCREATURE;
        // Only fixed known cards with a genuine immediate positive mana ability.
        if(name.equals("Sol Ring"))v|=MultiplayerStrategicSearchV35.INSTANT_MANA;
        return v;
    }

    public static MultiplayerStrategicSearchV35.Table observe(Player ai) {
        int lands=0,handLands=0, creatures=0,tokens=0,artifacts=0;
        int outlets=0,payoffs=0,doublers=0,engines=0;
        boolean commander=false;
        for(Card c: ai.getCardsIn(ZoneType.Battlefield)) {
            if(c.isLand())lands++;
            if(c.isCreature())creatures++;
            if(c.isToken())tokens++;
            if(c.isArtifact())artifacts++;
            String n=c.getName();
            if(OUTLETS.contains(n))outlets++;
            if(PAYOFFS.contains(n))payoffs++;
            if(DOUBLERS.contains(n))doublers++;
            if(TOKENS.contains(n))engines++;
            if(c.isCommander())commander=true;
        }
        for(Card c:ai.getCardsIn(ZoneType.Hand))if(c.isLand())handLands++;
        int[] power={0,0,0}, life={40,40,40};int oppIndex=0;
        for(Player opp:ai.getOpponents()) {
            if(oppIndex>=3)break;
            int p=0;
            for(Card c:opp.getCardsIn(ZoneType.Battlefield)) {
                if(c.isCreature())p+=Math.max(0,Math.min(20,c.getNetPower()));
            }
            power[oppIndex]=Math.min(150,p);
            life[oppIndex]=opp.getLife();
            oppIndex++;
        }
        return new MultiplayerStrategicSearchV35.Table(
            Math.max(0,ComputerUtilMana.getAvailableManaEstimate(ai,true)),
            lands,handLands,ai.getLife(),ai.getCardsIn(ZoneType.Hand).size(),
            creatures,tokens,artifacts,outlets,payoffs,doublers,engines,
            commander,power[0],power[1],power[2],life[0],life[1],life[2],
            ai.getGame().getPhaseHandler().getTurn());
    }

    /**
     * Max four ranked non-targeting candidate SPELLS. No mana payment occurs.
     * Forge checks actual colors, commander tax, timing, exceptions, targets,
     * cost choice, replacement effects and stack timing afterwards.
     */
    public static List<SpellAbility> rank(Player ai,List<SpellAbility> available) {
        if(!enabledFor(ai) || available==null || available.isEmpty()
                || ai.getGame()==null)return List.of();
        var game=ai.getGame();
        var phase=game.getPhaseHandler();
        if(!phase.isPlayerTurn(ai) ||
             !(phase.is(PhaseType.MAIN1) || phase.is(PhaseType.MAIN2))
             || !game.getStack().isEmpty())return List.of();
        if(available.size()>120 || ai.getCardsIn(ZoneType.Battlefield).size()>90)
            return List.of();

        int raw=available.size(),eligible=0;
        var table=observe(ai);
        List<MultiplayerStrategicSearchV35.CardPlan> choices=new ArrayList<>();
        Map<MultiplayerStrategicSearchV35.CardPlan,SpellAbility> spells=
                new IdentityHashMap<>();
        Set<Card> seen=new HashSet<>();
        for(SpellAbility sa:available) {
            if(sa==null || sa.getHostCard()==null || !sa.isSpell()
                    || sa.usesTargeting() || sa.isCopied() || sa.isLandAbility())
                continue;
            Card card=sa.getHostCard();
            if(!(card.isCreature()||card.isArtifact()||card.isEnchantment()
                    ||card.isPlaneswalker()) ||
                    (!card.isInZone(ZoneType.Hand) && !card.isInZone(ZoneType.Command)))
                continue;
            if(!seen.add(card))continue;
            eligible++;
            sa.setActivatingPlayer(ai);
            boolean timed=sa.canPlay() && sa.canCastTiming(ai);
            var c=new MultiplayerStrategicSearchV35.CardPlan(
                card.getName(),Math.max(0,card.getCMC()),role(card),
                card.isCreature()?Math.max(0,card.getNetPower()):0,features(card),timed);
            choices.add(c);
            spells.put(c,sa);
            if(choices.size()==20)break;
        }
        // With a single choice stock Forge already handles the spell.
        if(choices.size()<2)return List.of();
        List<SpellAbility> result=new ArrayList<>(4);
        MultiplayerStrategicSearchV35.Result best=null;
        for(int pass=0;pass<4;pass++) {
            var x=MultiplayerStrategicSearchV35.choose(table,choices);
            if(x==null || x.first()==null)break;
            if(best==null)best=x;
            // Avoid overriding an existing stock AI ordering on a tie.
            if(pass==0 && x.margin()<125)break;
            SpellAbility sa=spells.get(x.first());
            if(sa!=null)result.add(sa);
            choices.remove(x.first());
        }
        int sample=WINDOWS.incrementAndGet();
        if(sample<=16 || sample%512==0 || !result.isEmpty()) {
            System.out.println("FOUR_AI_V35_WINDOW player="+ai.getName()
                +" turn="+table.turn()+" rawAbilities="+raw
                +" eligiblePerms="+eligible+" estimatedMana="+table.mana()
                +" ranked="+result.size()
                +" best="+(best==null?"none":best.first().name())
                +" plannedSecond="+(best==null||best.currentFollowup()==null?
                    "none":best.currentFollowup().name())
                +" plannedNext="+(best==null||best.nextTurnFollowup()==null?
                    "none":best.nextTurnFollowup().name())
                +" searchNodes="+(best==null?0:best.nodesExplored())
                +" immediateForgeApprovalPending=true");
        }
        return result;
    }
}
