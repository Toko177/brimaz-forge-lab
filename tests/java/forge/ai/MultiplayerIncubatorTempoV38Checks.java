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
        System.out.println("FOUR_AI_V38_INCUBATOR_SYNTHETIC_PASS checks="+n
             +" realGameWinsClaimed=0");
    }
}
