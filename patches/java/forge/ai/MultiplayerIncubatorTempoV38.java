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

    private static int latestTurn = Integer.MIN_VALUE;

    public static SpellAbility choose(Player ai, List<SpellAbility> spells) {
        if(!Boolean.getBoolean("brimaz.v38IncubatorTempo") ||
           !Boolean.getBoolean("brimaz.v37Challenger") ||
           !Boolean.getBoolean("brimaz.v37ControlledDuel") ||
           ai==null || ai.getGame()==null || spells==null ||
           !ai.getName().contains("Brimaz Challenger"))return null;
        var phase=ai.getGame().getPhaseHandler();
        if(!phase.isPlayerTurn(ai) || !phase.is(PhaseType.MAIN2)
             || !ai.getGame().getStack().isEmpty()
             || latestTurn==phase.getTurn())return null;

        boolean commanderPresent=false;
        int readyBlockers=0,enemyPower=0;
        for(Card c:ai.getCardsIn(ZoneType.Battlefield)) {
            if(c.getName().equals("Brimaz, Blight of Oreskos"))commanderPresent=true;
            if(c.isCreature() && !c.isTapped() && c.getNetToughness()>0)
                readyBlockers++;
        }
        for(Player opp:ai.getOpponents()) {
            int power=0;
            for(Card c:opp.getCardsIn(ZoneType.Battlefield)) {
                if(c.isCreature() && c.getNetPower()>0)
                    power+=Math.min(20,c.getNetPower());
            }
            enemyPower=Math.max(enemyPower,power);
        }
        SpellAbility best=null;
        int bestSize=-1;
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
            if(!shouldTransform(size,ai.getLife(),readyBlockers,enemyPower,
                                commanderPresent))continue;
            sa.setActivatingPlayer(ai);
            if(!sa.canPlay() || !sa.canCastTiming(ai) ||
               !ComputerUtilCost.canPayCost(sa,ai,false))continue;
            if(size>bestSize){bestSize=size;best=sa;}
        }
        if(best!=null) {
            latestTurn=phase.getTurn();
            System.out.println("FOUR_AI_V38_TRANSFORM_PROPOSAL player="
                 +ai.getName()+" turn="+phase.getTurn()+" incubatorSize="+bestSize
                 +" blockers="+readyBlockers+" enemyBoardPower="+enemyPower
                 +" commanderPresent="+commanderPresent
                 +" stockForgeApprovalPending=true");
        }
        return best;
    }
}
