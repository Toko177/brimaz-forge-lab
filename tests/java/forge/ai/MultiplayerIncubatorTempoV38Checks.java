package forge.ai;

/** Pure adversarial tests: NOT game wins or proof a spell resolved. */
public final class MultiplayerIncubatorTempoV38Checks {
    private static int n=0;
    private static void check(boolean x,String m){n++;if(!x)throw new AssertionError(m);}
    public static void main(String[] unused) {
        check(!MultiplayerIncubatorTempoV38.shouldTransform(0,40,0,10,true),
              "zero counters not a useful resource");
        check(!MultiplayerIncubatorTempoV38.shouldTransform(1,40,0,10,true),
              "one counter never triggers this tempo override");
        check(!MultiplayerIncubatorTempoV38.shouldTransform(3,40,5,0,true),
              "no threat and substantial blocking board");
        check(MultiplayerIncubatorTempoV38.shouldTransform(5,40,5,0,false),
              "size 5 becomes an independently meaningful 5/5");
        check(MultiplayerIncubatorTempoV38.shouldTransform(3,40,1,8,false),
              "three-power blocker helps when opponent develops a board");
        check(MultiplayerIncubatorTempoV38.shouldTransform(3,40,2,0,true),
              "Brimaz with few blockers enables an actual transformed resource");
        check(!MultiplayerIncubatorTempoV38.shouldTransform(3,40,3,8,true),
              "do not transform just for flavor with well-protected board");
        check(!MultiplayerIncubatorTempoV38.shouldTransform(2,40,0,5,true),
              "small Incubator not rushed in healthy game");
        check(MultiplayerIncubatorTempoV38.shouldTransform(2,15,1,5,false),
              "risk of lethal makes an additional real blocker worthwhile");
        check(!MultiplayerIncubatorTempoV38.shouldTransform(2,17,1,5,false),
              "defense-only exception has a bounded life threshold");
        check(!MultiplayerIncubatorTempoV38.shouldTransform(5,0,0,8,true),
              "already eliminated player cannot create value");
        check(!MultiplayerIncubatorTempoV38.shouldTransform(5,40,-1,8,true),
              "invalid public blocker count fails closed");
        check(!MultiplayerIncubatorTempoV38.shouldTransform(5,40,0,-1,true),
              "invalid enemy board count fails closed");
        Object pilotA=new Object(),pilotB=new Object();
        int turn=19;
        check(!MultiplayerIncubatorTempoV38.approvedForSeatTurn(pilotA,turn),
              "first player begins with a clean allowance");
        check(!MultiplayerIncubatorTempoV38.approvedForSeatTurn(pilotB,turn),
              "second player begins with a separate clean allowance");
        // Calling a chooser cannot exhaust the quota: only native Forge's
        // actual WillPlay confirmation calls recordSeatApproved.
        check(!MultiplayerIncubatorTempoV38.approvedForSeatTurn(pilotA,turn),
              "proposal or rejection never marks seat approved");
        MultiplayerIncubatorTempoV38.recordSeatApproved(pilotA,turn);
        check(MultiplayerIncubatorTempoV38.approvedForSeatTurn(pilotA,turn),
              "approve once per player per turn");
        check(!MultiplayerIncubatorTempoV38.approvedForSeatTurn(pilotB,turn),
              "pilot A approval must not suppress pilot B's same game turn");
        MultiplayerIncubatorTempoV38.recordSeatApproved(pilotB,turn);
        check(MultiplayerIncubatorTempoV38.approvedForSeatTurn(pilotB,turn),
              "pilot B independently receives own approval");
        check(!MultiplayerIncubatorTempoV38.approvedForSeatTurn(pilotA,turn+1),
              "player A is free on following turn");
        check(!MultiplayerIncubatorTempoV38.approvedForSeatTurn(pilotB,turn+1),
              "player B is free on following turn");
        check(!MultiplayerIncubatorTempoV38.approvedForSeatTurn(null,turn),
              "null player fails closed");
        MultiplayerIncubatorTempoV38.recordSeatApproved(null,turn);
        check(!MultiplayerIncubatorTempoV38.approvedForSeatTurn(null,turn),
              "null approval cannot poison another player");
        System.out.println("FOUR_AI_V38_INCUBATOR_SYNTHETIC_PASS checks="+n
             +" realGameWinsClaimed=0");
    }
}
