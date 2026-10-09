package forge.ai;
/** Deterministic, side-effect-free Brimaz sacrifice evaluation contract. */
public final class BrimazV4ScoringChecks {
    static int score(int p,int ally,int neg,int death,int prolif,int life,int attack,String outlet) {
        return BrimazTurnPlanner.scoreHypothetical(p,ally,neg,death,prolif,life,attack,outlet);
    }
    static void ok(String name,boolean test) {
        if(!test)throw new AssertionError(name);
        System.out.println("V4_TEST_OK "+name);
    }
    public static void main(String[] argv) {
        String ravager="Arcbound Ravager";
        ok("No counter/drain payoff: preserve token",score(2,0,0,0,0,40,0,ravager)<=0);
        ok("Friendly counters reward proliferation",score(1,3,0,0,0,40,0,ravager)>0);
        ok("Proliferation payoff with Throne",score(1,3,0,0,0,40,0,"Throne of Geth")>score(1,3,0,0,0,40,0,ravager));
        ok("Death drain engines provide incremental payoff",score(1,1,0,2,0,40,0,ravager)>score(1,1,0,0,0,40,0,ravager));
        ok("Scheming Aspirant increases value of proliferate",score(1,1,0,0,1,40,0,ravager)>score(1,1,0,0,0,40,0,ravager));
        ok("Throne plus Aspirant can trigger proliferate twice",score(1,1,0,0,1,40,0,"Throne of Geth")>score(1,1,0,0,1,40,0,ravager));
        ok("Low life against high attacker penalizes sacrifice",score(1,3,0,0,0,8,6,ravager)<score(1,3,0,0,0,40,0,ravager));
        ok("Don't sacrifice 4-power token for small synergy",score(4,1,0,0,0,40,0,ravager)<=0);
        System.out.println("BRIMAZ_V4_SCORING_TESTS_OK");
    }
}
