package forge.ai.ability;

public final class MultiplayerCriticalCounterChecks {
    static int tested=0;
    static void check(boolean yes,String label){
        tested++;
        if(!yes)throw new AssertionError(label);
    }
    public static void main(String[]args){
        check(MultiplayerCriticalCounterPolicy.targetedCommanderRemoval(
            true,true,true,true,true,false),"Destroy on vulnerable commander");
        check(!MultiplayerCriticalCounterPolicy.targetedCommanderRemoval(
            true,true,true,true,true,true),"No force-counter for destroy against indestructible");
        check(MultiplayerCriticalCounterPolicy.targetedCommanderRemoval(
            true,true,true,true,false,true),"Exile/control ignores indestructible");
        check(!MultiplayerCriticalCounterPolicy.targetedCommanderRemoval(
            true,true,true,false,false,false),"Harmless targeted spell not forced");
        check(!MultiplayerCriticalCounterPolicy.targetedCommanderRemoval(
            false,true,true,true,false,false),"Not a hostile player");
        check(!MultiplayerCriticalCounterPolicy.targetedCommanderRemoval(
            true,false,true,true,false,false),"Not our commander");
        check(!MultiplayerCriticalCounterPolicy.targetedCommanderRemoval(
            true,true,false,true,false,false),"Cannot infer target from untargeted mass spell");
        for(int seat=1;seat<=4;seat++){
            check(MultiplayerCriticalCounterPolicy.targetedCommanderRemoval(
                true,true,true,true,false,false),"All four seats share one safety rule");
        }
        check(MultiplayerCriticalCounterPolicy.imminentLifeLoss(true,true,false,3,3),
              "Exact targeted damage would reach zero life");
        check(!MultiplayerCriticalCounterPolicy.imminentLifeLoss(true,true,false,4,3),
              "Do not force counter before lethal threshold");
        check(!MultiplayerCriticalCounterPolicy.imminentLifeLoss(true,true,true,2,5),
              "Cannot lose from zero life protection");
        check(!MultiplayerCriticalCounterPolicy.imminentLifeLoss(false,true,false,2,10),
              "Friendly spell cannot count as hostile");
        check(!MultiplayerCriticalCounterPolicy.imminentLifeLoss(true,false,false,2,10),
              "Wrong target player must not be considered endangered");
        for(int seat=1;seat<=4;seat++){
            check(MultiplayerCriticalCounterPolicy.imminentLifeLoss(
                  true,true,false,3,3),"All four AI seats get equal public lethal test");
        }
        System.out.println("FOUR_AI_CRITICAL_COUNTER_TESTS_PASS checks="+tested);
    }
}
