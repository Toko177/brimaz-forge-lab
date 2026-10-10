package forge.ai;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Deterministic V17 risk and blocker-coverage invariants independent of Forge UI. */
public final class DefenseCoverageModelChecks {
    static int checks=0;
    static void assertTrue(boolean ok,String description){
        checks++;
        if(!ok)throw new AssertionError(description);
    }
    static DefenseCoverageModel.Threat hit(int d,boolean infect,String commander,
                                             int previous,boolean blockable,boolean... edges) {
        return new DefenseCoverageModel.Threat(d,infect,commander,previous,blockable,edges);
    }
    static int risk(List<DefenseCoverageModel.Threat> threats, boolean[] available,
                    int life,int poison) {
        return DefenseCoverageModel.forecast(threats,available,life,poison,
                false,false,false).riskPermille;
    }
    public static void main(String[] args){
        // Straight lethal is blocked only when the visible card can legally
        // block that specific attacker, not just any creature.
        var direct=List.of(hit(10,false,null,0,true,true,false));
        assertTrue(risk(direct,new boolean[]{false,false},10,0)==1000,"Life lethal observed");
        assertTrue(risk(direct,new boolean[]{true,false},10,0)==0,"Legal one-on-one block stops ordinary damage");
        assertTrue(risk(direct,new boolean[]{false,true},10,0)==1000,"Wrong blocker cannot stop attack");
        var unblockable=List.of(hit(10,false,null,0,true,false,false));
        assertTrue(risk(unblockable,new boolean[]{true,true},10,0)==1000,"Unblockable attack must stay lethal");
        var trample=List.of(hit(10,false,null,0,false,true,true));
        assertTrue(risk(trample,new boolean[]{true,true},10,0)==1000,
                "Trample is not assumed wholly prevented by a single blocker");

        // Ordinary blocker capacity is one attack per defender, not infinite.
        var twoHits=List.of(hit(6,false,null,0,true,true,true),
                            hit(6,false,null,0,true,true,true));
        assertTrue(risk(twoHits,new boolean[]{false,false},10,0)==1200,
                "Two unblocked attacks sum to 12");
        assertTrue(risk(twoHits,new boolean[]{true,false},10,0)==600,
                "One defender blocks only one attacker");
        assertTrue(risk(twoHits,new boolean[]{true,true},10,0)==0,
                "Two legal blockers can cover two ordinary attacks");

        var poison=List.of(hit(2,true,null,0,true,true));
        assertTrue(risk(poison,new boolean[]{false},40,8)>=1000,"8 poison + 2 is lethal");
        assertTrue(risk(poison,new boolean[]{true},40,8)==800,
                "Existing poison remains but blocking prevents additional poison");
        var commander=List.of(hit(3,false,"Brimaz",18,true,true));
        assertTrue(risk(commander,new boolean[]{false},40,0)>=1000,
                "Same commander reaches 21 combat damage");
        assertTrue(risk(commander,new boolean[]{true},40,0)==857,
                "Legal block prevents new commander damage but retains old damage");

        // Distinct commanders do not pool their existing commander damage.
        var separate=List.of(hit(1,false,"A",18,true,false),
                             hit(1,false,"B",18,true,false));
        assertTrue(risk(separate,new boolean[]{false},40,0)<1000,
                "Distinct commanders must not pool to 20 + 2");
        var mixed=List.of(hit(1,true,"A",20,true,true));
        assertTrue(risk(mixed,new boolean[]{false},40,0)>=1000,
                "Commander combat damage still counts when also dealing infect");

        boolean[] available=new boolean[]{false};
        boolean[] candidates=new boolean[]{true};
        var pod=List.of(direct);
        assertTrue(DefenseCoverageModel.bestReservation(pod,available,candidates,
                     10,0,false,false,false)==0,"Reserve a blocker preventing visible fatal combat");
        assertTrue(!available[0],"Candidate assessment must not mutate current blocker state");

        // With two opponents, reserve against the worst exposure, not merely
        // the opponent randomly selected as our attack target.
        var three=List.of(
            List.of(hit(2,false,null,0,true,true,false)),
            List.of(hit(12,false,null,0,true,false,true)),
            new ArrayList<DefenseCoverageModel.Threat>());
        assertTrue(DefenseCoverageModel.bestReservation(
                 three,new boolean[]{false,false},new boolean[]{true,true},
                 10,0,false,false,false)==1,
                 "Correct defense against a different dangerous opponent");

        assertTrue(DefenseCoverageModel.forecast(
            direct,new boolean[]{false,false},10,0,true,false,false).riskPermille==0,
            "Cannot lose from zero life when properly protected");
        assertTrue(DefenseCoverageModel.forecast(
            poison,new boolean[]{false},40,8,false,true,false).riskPermille==0,
            "Poison-specific protection prevents poisoning loss");
        assertTrue(DefenseCoverageModel.forecast(
            commander,new boolean[]{false},40,0,false,false,true).riskPermille<1000,
            "Commander-specific protection prevents commander kill");

        // Two distinct opponents can both kill us. The first blocker may
        // leave the *maximum* risk unchanged, but is still necessary for a
        // two-blocker defense. The total-risk tie-break must make progress.
        var twoLethalOpponents=List.of(
            List.of(hit(12,false,null,0,true,true,false)),
            List.of(hit(12,false,null,0,true,false,true)));
        var initialHeld=new boolean[]{false,false};
        var eligible=new boolean[]{true,true};
        int first=DefenseCoverageModel.bestReservation(twoLethalOpponents,
                    initialHeld,eligible,10,0,false,false,false);
        assertTrue(first==0,"Do not stall on tied worst-case risks");
        initialHeld[first]=true;
        int second=DefenseCoverageModel.bestReservation(twoLethalOpponents,
                    initialHeld,eligible,10,0,false,false,false);
        assertTrue(second==1,"A second defender must now cover the other opponent");
        initialHeld[second]=true;
        assertTrue(DefenseCoverageModel.worstRisk(twoLethalOpponents,initialHeld,
                    10,0,false,false,false)==0,
                    "Two distinct enemies' otherwise lethal attacks are blockable");
        // Proactive variant considers risk before exact visible lethal, but
        // leaves the strict 100% threshold unchanged for historical A/B.
        var nearLethal=List.of(hit(9,false,null,0,true,true));
        assertTrue(DefenseCoverageModel.bestReservation(List.of(nearLethal),
                    new boolean[]{false},new boolean[]{true},10,0,
                    false,false,false)==-1,
                    "Strict V17 must not reserve below the lethal threshold");
        assertTrue(DefenseCoverageModel.bestReservation(List.of(nearLethal),
                    new boolean[]{false},new boolean[]{true},10,0,
                    false,false,false,850)==0,
                    "Optional proactive mode should defend at 90 percent life risk");
        var lowPressure=List.of(hit(6,false,null,0,true,true));
        assertTrue(DefenseCoverageModel.bestReservation(List.of(lowPressure),
                    new boolean[]{false},new boolean[]{true},10,0,
                    false,false,false,850)==-1,
                    "Proactive mode must not hold back an attacker under 85 percent risk");
        System.out.println("FOUR_AI_V17_COVERAGE_CHECKS_PASS checks="+checks);
    }
}
