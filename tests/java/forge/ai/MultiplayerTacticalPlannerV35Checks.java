package forge.ai;

/** Deterministic tactical triage tests; not a playable-game or win-rate proof. */
public final class MultiplayerTacticalPlannerV35Checks {
    private static int checks;
    private static void yes(boolean ok,String why) {
        checks++;
        if(!ok)throw new AssertionError(why);
    }
    private static MultiplayerTacticalPlannerV35.Board board(int life,int ours,
            int ownPower,int tokens,int grave,boolean commander,
            int enemyCount,int enemyPower,int strongest,int second,int largestCount) {
        return new MultiplayerTacticalPlannerV35.Board(life,ours,ownPower,
            tokens,grave,commander,enemyCount,enemyPower,strongest,second,largestCount);
    }
    public static void main(String[] args) {
        var safe=board(37,2,4,1,2,true,9,33,16,11,5);
        yes(MultiplayerTacticalPlannerV35.choosePublicAction(safe)
            == MultiplayerTacticalPlannerV35.Intervention.HOLD,
            "no need to cast a proactive answer at safe life");
        var noAttackers=board(3,0,0,0,0,false,0,0,0,0,0);
        yes(MultiplayerTacticalPlannerV35.choosePublicAction(noAttackers)
            == MultiplayerTacticalPlannerV35.Intervention.HOLD,
            "low life with zero opponent attack power must not force a wipe");
        var emergency=board(9,1,2,0,0,false,12,55,25,18,6);
        yes(MultiplayerTacticalPlannerV35.choosePublicAction(emergency)
            == MultiplayerTacticalPlannerV35.Intervention.EXILE_SWEEP,
            "severe hostile board advantage justifies considering Sunfall");
        var rebuilding=board(9,1,2,0,7,false,12,55,25,18,6);
        yes(MultiplayerTacticalPlannerV35.choosePublicAction(rebuilding)
            == MultiplayerTacticalPlannerV35.Intervention.GRAVEYARD_SWEEP,
            "large own graveyard changes correct proposed emergency line");
        var single=board(11,0,0,0,0,false,1,12,12,0,1);
        yes(MultiplayerTacticalPlannerV35.choosePublicAction(single)
            == MultiplayerTacticalPlannerV35.Intervention.PREEMPTIVE_REMOVAL,
            "one huge visible threat should not trigger a global wipe");
        var defended=board(22,9,32,2,0,true,9,34,23,11,5);
        yes(MultiplayerTacticalPlannerV35.choosePublicAction(defended)
            == MultiplayerTacticalPlannerV35.Intervention.HOLD,
            "preserve valuable commander board when protected");
        var pressure=board(8,0,0,0,0,false,3,17,15,2,2);
        yes(MultiplayerTacticalPlannerV35.danger(pressure)==15,
            "one strongest opponent defines potential immediate danger");
        var blockers=board(8,4,5,0,0,false,3,17,15,2,2);
        yes(MultiplayerTacticalPlannerV35.danger(blockers)==7,
            "visible creatures reduce abstract attack exposure");
        yes(MultiplayerTacticalPlannerV35.choosePublicAction(blockers)
            == MultiplayerTacticalPlannerV35.Intervention.PREEMPTIVE_REMOVAL,
            "avoid wipes against small enemy boards");
        try {
            board(20,-1,0,0,0,false,0,0,0,0,0);
            throw new AssertionError("negative creatures accepted");
        }catch(IllegalArgumentException expected){checks++;}
        System.out.println("FOUR_AI_V35_TACTICAL_SYNTHETIC_PASS checks="+checks
                           +" realGamesClaimed=0");
    }
}
