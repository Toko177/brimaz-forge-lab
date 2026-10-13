package forge.ai;

import java.util.List;
import java.util.ArrayList;

/** Pure synthetic counterfactuals; does NOT certify actual Magic legality. */
public final class MultiplayerStrategicSearchV35Checks {
    private static int checks;
    private static void ok(boolean value, String explanation) {
        checks++;
        if (!value) throw new AssertionError(explanation);
    }
    private static MultiplayerStrategicSearchV35.CardPlan card(
            String name,int cmc,MultiplayerStrategicModel.Role role,int power,
            int features,boolean timed) {
        return new MultiplayerStrategicSearchV35.CardPlan(
            name,cmc,role,power,features,timed);
    }
    private static MultiplayerStrategicSearchV35.Table table(
            int mana,int lands,int handLands,int life,int tokens,int payoff,
            int outlet,int engines,int[] threat) {
        return new MultiplayerStrategicSearchV35.Table(mana,lands,handLands,life,
            4,2,tokens,2,outlet,payoff,0,engines,false,
            threat[0],threat[1],threat[2],40,40,40,10);
    }
    public static void main(String[] args) {
        var ramp=card("Arcane Signet",2,MultiplayerStrategicModel.Role.RAMP,0,0,true);
        var commander=card("Brimaz",4,MultiplayerStrategicModel.Role.COMMANDER,3,
                MultiplayerStrategicSearchV35.INCUBATE_ENGINE,false);
        var bear=card("Defensive creature",3,MultiplayerStrategicModel.Role.CREATURE,3,0,true);
        var safe=table(3,3,1,38,0,0,0,0,new int[]{3,3,2});
        var a=MultiplayerStrategicSearchV35.choose(safe,List.of(ramp,commander,bear));
        ok(a!=null && a.first()==ramp,"early ramp beats weak creature and unlocks commander");
        ok(a.nodesExplored()>0,"actual bounded tree expansions performed");
        ok(a.nextTurnFollowup()==commander ||
           a.currentFollowup()==bear, "known-card development sequence recorded");
        ok(!a.underThreat(),"safe board not marked as lethal");
        var risky=table(3,3,1,7,0,0,0,0,new int[]{12,9,5});
        var blocker=card("Defensive 4/4",3,MultiplayerStrategicModel.Role.CREATURE,4,0,true);
        var b=MultiplayerStrategicSearchV35.choose(risky,List.of(ramp,blocker));
        ok(b.underThreat(),"public three-player board pressure detected");
        ok(b.first()==blocker,"under acute threat prioritize actual board development");
        ok(!MultiplayerStrategicSearchV35.underThreat(table(3,3,0,12,0,0,0,0,new int[]{5,5,5})),
                "three modest opponents do not magically combine into one lethal attack");
        ok(!MultiplayerStrategicSearchV35.underThreat(table(2,3,0,3,0,0,0,0,new int[]{0,0,0})),
                "no public attackers means no threat even on three life");
        var altar=card("Ashnod's Altar",3,MultiplayerStrategicModel.Role.SAC_OUTLET,0,0,true);
        var cmd=card("Brimaz",3,MultiplayerStrategicModel.Role.COMMANDER,4,
                MultiplayerStrategicSearchV35.INCUBATE_ENGINE,true);
        var live=table(3,5,0,35,4,2,0,2,new int[]{3,2,1});
        var noToken=table(3,5,0,35,0,2,0,0,new int[]{3,2,1});
        ok(MultiplayerStrategicSearchV35.evaluate(live,altar,4,0,2,0,2,false)>
           MultiplayerStrategicSearchV35.evaluate(noToken,altar,0,0,2,0,0,false),
           "sacrifice engine's score depends on existing expendable tokens");
        ok(MultiplayerStrategicSearchV35.choose(noToken,List.of(altar,cmd))
                  .first()==cmd,"do not install dead outlet before commander on empty board");
        var doubler=card("Anointed Procession",4,MultiplayerStrategicModel.Role.ENGINE,
                0,MultiplayerStrategicSearchV35.TOKEN_MULTIPLIER,true);
        var plain=card("4-cost vanilla artifact",4,MultiplayerStrategicModel.Role.ENGINE,0,0,true);
        ok(MultiplayerStrategicSearchV35.evaluate(live,doubler,4,0,2,0,3,false)>
           MultiplayerStrategicSearchV35.evaluate(live,plain,4,0,2,0,3,false),
           "token doubler improves payoff of known token engine");
        ok(MultiplayerStrategicSearchV35.choose(table(4,5,0,35,4,2,0,3,
              new int[]{3,2,1}),List.of(doubler,plain)).first()==doubler,
           "choose doubler over same-cost non-synergistic permanent");
        var withBrimaz=new MultiplayerStrategicSearchV35.Table(
            4,4,0,29,3,3,0,2,1,1,0,1,true,
            4,3,2,40,40,40,6);
        var phyrexian=card("Phyrexian Fleshgorger",3,
            MultiplayerStrategicModel.Role.CREATURE,3,
            MultiplayerStrategicSearchV35.PHYREXIAN_CAST,true);
        var sameCostVanilla=card("Vanilla creature",3,
            MultiplayerStrategicModel.Role.CREATURE,3,0,true);
        ok(MultiplayerStrategicSearchV35.evaluate(
             withBrimaz,phyrexian,0,1,1,0,1,true)
           > MultiplayerStrategicSearchV35.evaluate(
             withBrimaz,sameCostVanilla,0,1,1,0,1,true),
           "cast Phyrexian creature with Brimaz online to obtain incubation trigger");
        ok(MultiplayerStrategicSearchV35.choose(
             withBrimaz,List.of(phyrexian,sameCostVanilla)).first()==phyrexian,
           "rank genuine Phyrexian type ahead of equal-cost vanilla creature");
        ok(MultiplayerStrategicSearchV35.evaluate(
             withBrimaz,phyrexian,0,1,1,0,1,false)
           == MultiplayerStrategicSearchV35.evaluate(
             withBrimaz,sameCostVanilla,0,1,1,0,1,false),
           "no imagined Brimaz cast trigger before commander is on battlefield");
        var illegal=card("Unavailable",7,MultiplayerStrategicModel.Role.ENGINE,0,0,false);
        ok(MultiplayerStrategicSearchV35.choose(safe,List.of(illegal))==null,
           "never override Forge timing legality");
        var tooExpensive=card("Unaffordable",10,MultiplayerStrategicModel.Role.ENGINE,0,0,true);
        ok(MultiplayerStrategicSearchV35.choose(safe,List.of(tooExpensive))==null,
           "estimated mana bound prevents implausible first action");
        ok(MultiplayerStrategicSearchV35.choose(safe,List.of())==null,
           "empty choices fail closed");
        ok(MultiplayerStrategicSearchV35.choose(safe,null)==null,
           "null choices fail closed");
        ok(MultiplayerStrategicSearchV35.choose(safe,List.of(ramp,commander,bear))
                    .first()==a.first(), "pure model deterministic");
        var large=new ArrayList<MultiplayerStrategicSearchV35.CardPlan>();
        for(int i=0;i<60;i++)large.add(card("creature"+i,1,
                MultiplayerStrategicModel.Role.CREATURE,1,0,true));
        var capped=MultiplayerStrategicSearchV35.choose(safe,large);
        ok(capped!=null && capped.nodesExplored()<=8000,
           "bounded search even for oversized list");
        try {
            table(-1,1,1,15,0,0,0,0,new int[]{0,0,0});
            throw new AssertionError("invalid table was not rejected");
        } catch(IllegalArgumentException expected) { checks++; }
        try {
            card("invalid",-1,MultiplayerStrategicModel.Role.RAMP,0,0,true);
            throw new AssertionError("invalid card was not rejected");
        } catch(IllegalArgumentException expected) { checks++; }
        System.out.println("FOUR_AI_V35_SYNTHETIC_SEARCH_PASS checks="+checks
            +" visited="+capped.nodesExplored()
            +" real_games_claimed=0");
    }
}
