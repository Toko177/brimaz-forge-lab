package forge.ai;

import forge.game.card.Card;
import forge.game.card.CounterType;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.util.List;

/**
 * V38 selective Incubator-to-creature activation.
 *
 * Incubate produces an artifact with +1/+1 counters, NOT a creature until
 * it is transformed. Prior V37 was attempting Phyrexian-death synergies
 * without provisioning these actual creatures on a dependable path.
 *
 * This code selects an existing activated SpellAbility on our battlefield.
 * All legality, activation payment, replacement effects and resolution
 * remain exclusively with actual Forge AiController and rules.
 */
public final class MultiplayerIncubatorTempoV38 {
    private MultiplayerIncubatorTempoV38() {}

    /**
     * Public, conservative threshold. Never consumes an Incubator as
     * sacrificial fodder before it is actually a creature in Forge.
     */
    public static boolean shouldTransform(int size, int life,
                                           int ownReadyBlockers,
                                           int largestEnemyBoardPower,
                                           boolean commanderPresent) {
        if(size<2 || life<=0 || ownReadyBlockers<0 || largestEnemyBoardPower<0)
            return false;
        if(size>=5)return true;
        // Turn a sizeable 3/3+ into a permanent blocker/attacker when our
        // battlefield is relatively light and the enemy can attack.
        if(size>=3 && ownReadyBlockers<=1 && largestEnemyBoardPower>=3)
            return true;
        // Brimaz creates Incubators as part of normal Phyrexian casting;
        // transform one decent-sized resource to make the death-trigger
        // engine available in actual game state, not a hypothetical score.
        if(size>=3 && commanderPresent && ownReadyBlockers<=2)
            return true;
        if(size>=2 && life<=16 && ownReadyBlockers<=1
                && largestEnemyBoardPower>=5)return true;
        return false;
    }

    // V38/39 historical behavior is retained for reproducibility.
    // V40 fixes its shared, proposal-time latestTurn: there are TWO
    // independent Challenger players in the genuine 2-vs-2 mirrors.
    // A proposal that Forge rejects must not exhaust a player's allowance.
    private static int latestTurn = Integer.MIN_VALUE;
    private static final java.util.Map<Object,Integer> approvedSeatTurns =
        java.util.Collections.synchronizedMap(new java.util.WeakHashMap<>());

    static boolean approvedForSeatTurn(Object seat,int turn) {
        if(seat==null)return false;
        synchronized(approvedSeatTurns) {
            return java.util.Objects.equals(approvedSeatTurns.get(seat),turn);
        }
    }

    static void recordSeatApproved(Object seat,int turn) {
        if(seat==null)return;
        synchronized(approvedSeatTurns) { approvedSeatTurns.put(seat,turn); }
    }

    /** Called ONLY after unchanged Forge AiController returns WillPlay.
     * An approved proposal is not evidence that the ability resolved. */
    public static void confirmForgeApproval(Player ai) {
        if(!Boolean.getBoolean("brimaz.v40SeatScopedActions")
              || ai==null || ai.getGame()==null)return;
        int turn=ai.getGame().getPhaseHandler().getTurn();
        recordSeatApproved(ai,turn);
        System.out.println("FOUR_AI_V40_TRANSFORM_APPROVED_BY_SEAT player="
             +ai.getName()+" turn="+turn+" approvedNotResolved=true");
    }

    private static final java.util.Set<String> PRIORITY_RAMP=java.util.Set.of(
        "Sol Ring","Arcane Signet","Orzhov Signet","Fellwar Stone",
        "Talisman of Hierarchy","Mind Stone","Thought Vessel",
        "Commander's Sphere");
    private static final java.util.Set<String> SACRIFICE_OUTLETS=java.util.Set.of(
        "Arcbound Ravager","Spawning Pit","Bartolomé del Presidio",
        "Krark-Clan Ironworks","Throne of Geth");

    public static SpellAbility choose(Player ai, List<SpellAbility> spells) {
        if(!Boolean.getBoolean("brimaz.v38IncubatorTempo") ||
           !Boolean.getBoolean("brimaz.v37Challenger") ||
           !Boolean.getBoolean("brimaz.v37ControlledDuel") ||
           ai==null || ai.getGame()==null || spells==null ||
           !(Boolean.getBoolean("brimaz.v41SacrificeAccess")
              ? MultiplayerSacrificeAccessV41.authorized(
                    ai.getName(),Boolean.getBoolean("brimaz.v37MirrorDuel"))
              : ai.getName().contains("Brimaz Challenger")))return null;
        var phase=ai.getGame().getPhaseHandler();
        if(!phase.isPlayerTurn(ai) || !phase.is(PhaseType.MAIN2)
             || !ai.getGame().getStack().isEmpty()
             || (Boolean.getBoolean("brimaz.v40SeatScopedActions")
                    ? approvedForSeatTurn(ai,phase.getTurn())
                    : latestTurn==phase.getTurn()))return null;

        final boolean v39=Boolean.getBoolean("brimaz.v39EngineEconomics");
        boolean commanderPresent=false,hasOutlet=false,payableRamp=false;
        int readyBlockers=0,enemyPower=0,counteredPermanents=0;
        for(Card c:ai.getCardsIn(ZoneType.Battlefield)) {
            if(c.getName().equals("Brimaz, Blight of Oreskos"))commanderPresent=true;
            if(c.isCreature() && !c.isTapped() && c.getNetToughness()>0)
                readyBlockers++;
            if(c.hasCounters())counteredPermanents++;
            if (SACRIFICE_OUTLETS.contains(c.getName())
                    || (Boolean.getBoolean("brimaz.v41SacrificeAccess")
                        && (c.getName().equals("Ashnod's Altar")
                            || c.getName().equals("Phyrexian Altar"))))
                hasOutlet=true;
        }
        for(Player opp:ai.getOpponents()) {
            int power=0;
            for(Card c:opp.getCardsIn(ZoneType.Battlefield)) {
                if(c.isCreature() && c.getNetPower()>0)
                    power+=Math.min(20,c.getNetPower());
            }
            enemyPower=Math.max(enemyPower,power);
        }
        if(v39) {
            for(SpellAbility sa:spells) {
                if(sa==null || !sa.isSpell() || sa.getHostCard()==null
                     || !sa.getHostCard().isInZone(ZoneType.Hand)
                     || !PRIORITY_RAMP.contains(sa.getHostCard().getName()))
                    continue;
                sa.setActivatingPlayer(ai);
                if(sa.canPlay() && sa.canCastTiming(ai) &&
                     ComputerUtilCost.canPayCost(sa,ai,false)) {
                    payableRamp=true;
                    break;
                }
            }
            if(MultiplayerIncubatorEngineV39.shouldPreserveManaForRamp(
                 payableRamp,ai.getLife(),enemyPower,readyBlockers))return null;
        }
        SpellAbility best=null;
        int bestSize=-1,bestPriority=Integer.MIN_VALUE;
        boolean bestEngine=false;
        int bestEngineBenefit=0;
        for(SpellAbility sa:spells) {
            if(sa==null || sa.getHostCard()==null ||
               !sa.isActivatedAbility() ||
               sa.getApi()!=forge.game.ability.ApiType.SetState ||
               !"Transform".equals(sa.getParam("Mode")))continue;
            Card c=sa.getHostCard();
            if(!c.isInZone(ZoneType.Battlefield) || c.getController()!=ai ||
               !c.isToken() || c.isCreature() ||
               !"Incubator Token".equals(c.getName()))continue;
            int size=c.getCounters(CounterType.getType("P1P1"));
            boolean tempo=shouldTransform(size,ai.getLife(),readyBlockers,
                                           enemyPower,commanderPresent);
            int others=Math.max(0,counteredPermanents-
                                  (c.hasCounters()?1:0));
            int engineBenefit=v39
                ? MultiplayerIncubatorEngineV39.minimumVisibleNetEngineValue(
                    size,others,commanderPresent,hasOutlet) : 0;
            int priority=v39
                ? MultiplayerIncubatorEngineV39.visibleTransformationPriority(
                    size,tempo,engineBenefit) : (tempo?size:-1);
            if(priority<0)continue;
            sa.setActivatingPlayer(ai);
            if(!sa.canPlay() || !sa.canCastTiming(ai) ||
               !ComputerUtilCost.canPayCost(sa,ai,false))continue;
            if(priority>bestPriority) {
                bestPriority=priority;
                bestSize=size;
                best=sa;
                bestEngine=v39 && engineBenefit>0;
                bestEngineBenefit=engineBenefit;
            }
        }
        if(best!=null) {
            if(!Boolean.getBoolean("brimaz.v40SeatScopedActions"))
                latestTurn=phase.getTurn();
            System.out.println("FOUR_AI_V38_TRANSFORM_PROPOSAL player="
                 +ai.getName()+" turn="+phase.getTurn()+" incubatorSize="+bestSize
                 +" blockers="+readyBlockers+" enemyBoardPower="+enemyPower
                 +" commanderPresent="+commanderPresent
                 +" source="+(bestEngine?"KNOWN_COUNTER_ENGINE":"DEFENSIVE_TEMPO")
                 +" engineBenefit="+bestEngineBenefit
                 +" realOutletPresent="+hasOutlet
                 +" payableRampSeen="+payableRamp
                 +" approvalScope="+(Boolean.getBoolean("brimaz.v40SeatScopedActions")
                      ?"INDIVIDUAL_PLAYER_AFTER_FORGE_APPROVAL":"LEGACY_SHARED_PROPOSAL")
                 +" stockForgeApprovalPending=true");
        }
        return best;
    }
}
