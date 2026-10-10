package forge.ai;

/** Unit invariants for multi-opponent removal urgency; Forge legality remains external. */
public final class MultiplayerRemovalUrgencyChecks {
    private static int count=0;
    static void ok(boolean value,String title){
        count++;
        if(!value)throw new AssertionError(title);
    }
    static int score(int damage,int life,int poison,int commanderAlready,
                     boolean infect,boolean commander,
                     boolean unblocked,boolean lp,boolean pp,boolean cp,
                     boolean canAttack){
        return MultiplayerRemovalUrgencyPolicy.urgencyScore(
            damage,life,poison,commanderAlready,infect,commander,
            unblocked,lp,pp,cp,canAttack);
    }
    public static void main(String[] args){
        ok(score(10,10,0,0,false,false,true,false,false,false,true)==900,
           "Unblocked exact life lethal gets largest priority");
        ok(score(9,10,0,0,false,false,true,false,false,false,true)==160,
           "Near-lethal unblocked creature matters");
        ok(score(4,10,0,0,false,false,true,false,false,false,true)==70,
           "40 percent damage adds limited urgency");
        ok(score(3,10,0,0,false,false,true,false,false,false,true)==0,
           "Low chip damage should not displace valuable engines");
        ok(score(10,10,0,0,false,false,false,false,false,false,true)==0,
           "Possible blocking prevents claiming a certain lethal hit");
        ok(score(10,10,0,0,false,false,true,true,false,false,true)==0,
           "Cannot lose life-based game at zero prevents life lethal bonus");
        ok(score(2,40,8,0,true,false,true,false,false,false,true)==900,
           "Infect hits ten poison counters");
        ok(score(2,40,8,0,true,false,true,false,true,false,true)==0,
           "Poison-specific prevention respected");
        ok(score(3,40,0,18,false,true,true,false,false,false,true)==900,
           "Single commander reaches twenty-one combat damage");
        ok(score(3,40,0,18,false,true,true,false,false,true,true)==0,
           "Commander-specific loss prevention respected");
        ok(score(1,40,0,19,false,true,true,false,false,false,true)==160,
           "Near-combat commander lethal, not same as 21");
        ok(score(30,1,9,20,true,true,true,false,false,false,false)==0,
           "Cannot attack specific defending player => no threat bonus");
        for(int seat=1;seat<=4;seat++){
            ok(score(10,10,0,0,false,false,true,false,false,false,true)
                    ==900,"Same public target priority for all four AI seats");
        }
        System.out.println("FOUR_AI_REMOVAL_URGENCY_TESTS_PASS checks="+count);
    }
}
