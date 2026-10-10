package forge.ai;

import forge.game.trigger.TriggerType;

public final class CombatTriggerNegativePruneChecks {
    private static int checks;
    private static void eq(boolean actual,boolean expected,String desc) {
        checks++;
        if(actual!=expected)throw new AssertionError(desc+": "+actual);
    }
    public static void main(String[]args){
        eq(CombatTriggerNegativePrune.impossible(TriggerType.Attacks,false,true,false),
           true,"Already-attacking trigger cannot be predicted again");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.Attacks,true,false,true),
           true,"Alone trigger and more than one planned attacker");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.Attacks,false,false,false),
           false,"First attack can trigger");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.AttackerUnblocked,true,false,false),
           true,"Cannot be unblocked with a blocker");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.AttackerUnblocked,false,false,false),
           false,"Unblocked attack can trigger");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.Blocks,false,false,false),
           true,"Blocks trigger requires a defender");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.AttackerBlocked,false,false,false),
           true,"AttackerBlocked requires a defender");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.AttackerBlockedByCreature,false,false,false),
           true,"AttackerBlockedByCreature requires defender");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.DamageDone,false,false,false),
           true,"This hypothetical blocker damage trigger requires defender");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.Blocks,true,false,false),
           false,"Actual legal block trigger may trigger");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.DamageDone,true,false,false),
           false,"Valid damage pair must be evaluated");
        eq(CombatTriggerNegativePrune.impossible(TriggerType.AttackerBlocked,true,false,false),
           false,"Blocked attacker is relevant");
        for(int seat=1;seat<=4;seat++){
            eq(CombatTriggerNegativePrune.impossible(TriggerType.Blocks,false,false,false),
               true,"All four AI seats share same pure filter");
        }
        System.out.println("FOUR_AI_V24_COMBAT_PRUNE_TESTS_PASS checks="+checks);
    }
}
