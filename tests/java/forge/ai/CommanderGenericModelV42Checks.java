package forge.ai;

import java.util.List;

/** Pure model tests. Not real games or evidence of a higher Commander winrate. */
public final class CommanderGenericModelV42Checks {
    private static int tests;
    private static void ok(boolean value,String message) {
        tests++;
        if(!value)throw new AssertionError(message);
    }
    private static CommanderGenericModelV42.State state(int mana,int lands,int life,
                                                        int blockers,int enemyPower) {
        return new CommanderGenericModelV42.State(4,mana,lands,life,5,2,blockers,
                false,enemyPower,3,4);
    }
    private static CommanderGenericModelV42.Candidate c(String name,
            CommanderGenericModelV42.Kind kind,int mv,int p,int t,
            boolean mana,boolean payable) {
        return new CommanderGenericModelV42.Candidate(name,kind,mv,p,t,mana,payable);
    }
    public static void main(String[] args) {
        var ramp=c("Generic mana artifact",CommanderGenericModelV42.Kind.ARTIFACT,
                2,0,0,true,true);
        var stone=c("Ordinary artifact",CommanderGenericModelV42.Kind.ARTIFACT,
                2,0,0,false,true);
        var soldier=c("Generic soldier",CommanderGenericModelV42.Kind.CREATURE,
                3,2,2,false,true);
        var commander=c("Any legal commander",CommanderGenericModelV42.Kind.COMMANDER,
                4,4,4,false,true);
        var early=state(4,3,40,1,3);
        ok(CommanderGenericModelV42.score(early,ramp)>
           CommanderGenericModelV42.score(early,stone),"mana API changes ramp value");
        ok(CommanderGenericModelV42.decide(early,List.of(ramp,stone,soldier))
            .ranked().get(0)==ramp,"early genuine generic ramp prioritized");
        ok(CommanderGenericModelV42.decide(early,List.of(commander,stone))
            .ranked().get(0)==commander,"commander-zone identity works without specific names");
        var dead=state(4,4,6,0,10);
        ok(CommanderGenericModelV42.decide(dead,List.of(ramp,soldier))
            .ranked().isEmpty(),"under lethal-looking public threat do not force development");
        ok(CommanderGenericModelV42.decide(dead,List.of(ramp,soldier))
            .underPressure(),"visible pressure logged");
        var undecided=state(4,4,35,2,2);
        ok(CommanderGenericModelV42.decide(undecided,List.of(
                stone,c("Other artifact",CommanderGenericModelV42.Kind.ARTIFACT,
                        2,0,0,false,true))).ranked().isEmpty(),
                "ties preserve Forge original decisions");
        ok(CommanderGenericModelV42.decide(early,List.of(
                ramp,c("Not payable",CommanderGenericModelV42.Kind.CREATURE,
                        7,7,7,false,false))).ranked().isEmpty(),
                "cannot force costs not approved by real candidate checks");
        var reduced=c("Expensive printed MV but real Forge payment verified",
                CommanderGenericModelV42.Kind.CREATURE,8,7,7,false,true);
        ok(CommanderGenericModelV42.score(early,reduced)!=Integer.MIN_VALUE,
                "cost reduction/alternative payment must not be vetoed by printed MV");
        var stillNotPayable=c("Cannot pay in real Forge",
                CommanderGenericModelV42.Kind.CREATURE,8,7,7,false,false);
        ok(CommanderGenericModelV42.score(early,stillNotPayable)==Integer.MIN_VALUE,
                "actual native Forge payment still blocks forbidden action");
        ok(CommanderGenericModelV42.decide(early,List.of(ramp,stone,soldier))
                .ranked().equals(CommanderGenericModelV42.decide(
                    early,List.of(ramp,stone,soldier)).ranked()),
                "deterministic pure state evaluation");
        ok(CommanderGenericModelV42.decide(early,List.of()).ranked().isEmpty(),
                "empty list safely abstains");
        ok(!CommanderGenericModelV42.danger(state(4,4,38,1,3)),
                "does not combine three opponents' boards as one attack");
        try {
            state(-1,3,35,2,4);
            throw new AssertionError("negative public resources accepted");
        } catch (IllegalArgumentException expected) { tests++; }
        try {
            c("invalid",CommanderGenericModelV42.Kind.CREATURE,
                    -1,1,1,false,true);
            throw new AssertionError("negative mana value accepted");
        } catch (IllegalArgumentException expected) { tests++; }
        System.out.println("V42_GENERIC_COMMANDER_MODEL_PASS checks="+tests
                +" realGamesClaimed=0 winrateClaimed=false");
    }
}
