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
        System.out.println("FOUR_AI_CRITICAL_COUNTER_TESTS_PASS checks="+tested);
    }
}
