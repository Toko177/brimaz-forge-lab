package forge.ai;

import java.util.List;

/** Synthetic pure-model assertions. NOT Magic rules certification or real games. */
public class MultiplayerStrategicModelChecks {
    static int checked = 0;
    static void yes(boolean b, String message) {
        checked++;
        if (!b) throw new AssertionError(message);
    }
    static MultiplayerStrategicModel.Option o(String n, int mana,
            MultiplayerStrategicModel.Role role, int power, boolean playable) {
        return new MultiplayerStrategicModel.Option(n, mana, role, power, playable);
    }
    public static void main(String[] args) {
        var ramp = o("Signet",2,MultiplayerStrategicModel.Role.RAMP,0,true);
        var commanderLater = o("Commander",4,MultiplayerStrategicModel.Role.COMMANDER,4,false);
        var bear = o("Bear",3,MultiplayerStrategicModel.Role.CREATURE,2,true);
        var safe = new MultiplayerStrategicModel.Snapshot(3,3,35,5,4,1,0,0,0,4,10);
        var plan = MultiplayerStrategicModel.choose(safe,
            List.of(ramp, commanderLater, bear));
        yes(plan != null && plan.selected() == ramp, "early ramp must unlock four mana commander");
        yes(plan.projectedNext() == commanderLater, "own next-turn commander step retained");
        yes(plan.runnerUp() == bear, "both current legal candidates ranked");
        yes(plan.margin() > 0, "choice discriminates non-equal actions");
        yes(MultiplayerStrategicModel.projectedMana(safe,ramp)==5,
            "next-turn mana includes anticipated land and rock");

        var endangered = new MultiplayerStrategicModel.Snapshot(3,3,8,5,4,0,0,0,0,4,14);
        var blocker = o("Defensive 4/4",3,MultiplayerStrategicModel.Role.CREATURE,4,true);
        yes(endangered.critical(), "combined two-opponent danger matters");
        yes(MultiplayerStrategicModel.choose(endangered, List.of(ramp,blocker))
                .selected()==blocker, "under combined threat prioritize blocker rather than tempo");

        var nearButNotLethal = new MultiplayerStrategicModel.Snapshot(3,3,17,5,4,0,0,0,0,4,14);
        yes(!nearButNotLethal.critical(), "do not classify noncritical life as lethal");

        var outlet = o("Spawning Pit",2,MultiplayerStrategicModel.Role.SAC_OUTLET,0,true);
        var cmd = o("Brimaz",4,MultiplayerStrategicModel.Role.COMMANDER,4,true);
        var liveTokens = new MultiplayerStrategicModel.Snapshot(5,5,30,3,2,5,4,3,3,4,18);
        yes(MultiplayerStrategicModel.choose(liveTokens,List.of(outlet,cmd))
                .selected()==outlet, "active tokens and engines prioritize legal sac outlet");
        var noTokens = new MultiplayerStrategicModel.Snapshot(5,5,30,3,2,5,4,0,3,4,18);
        yes(MultiplayerStrategicModel.choose(noTokens,List.of(outlet,cmd))
                .selected()==cmd, "dead sac outlet must not block commander development");
        yes(MultiplayerStrategicModel.immediate(noTokens,outlet)
                < MultiplayerStrategicModel.immediate(liveTokens,outlet),
            "sac payoff depends on tokens actually existing");

        var nonPlayable = o("Unaffordable",9,MultiplayerStrategicModel.Role.ENGINE,0,false);
        yes(MultiplayerStrategicModel.choose(safe,List.of(nonPlayable))==null,
            "cannot directly select unavailable actions");
        yes(MultiplayerStrategicModel.choose(safe,List.of())==null,
            "no options fail closed");
        yes(MultiplayerStrategicModel.choose(safe,null)==null,
            "null options fail closed");
        var noMana = new MultiplayerStrategicModel.Snapshot(0,0,40,0,0,0,0,0,0,0,1);
        yes(MultiplayerStrategicModel.choose(noMana,List.of(bear))==null,
            "must never choose unaffordable action");
        var one = MultiplayerStrategicModel.choose(safe,List.of(ramp));
        yes(one.runnerUp()==null && one.margin()==Integer.MAX_VALUE,
            "single legal action represented explicitly, no fabricated runner up");
        yes(MultiplayerStrategicModel.choose(safe,List.of(ramp,commanderLater,bear))
                 .selected()==plan.selected(), "deterministic pure state/action ranking");
        try {
            new MultiplayerStrategicModel.Snapshot(-1,0,40,0,0,0,0,0,0,4,3);
            throw new AssertionError("negative public mana accepted");
        } catch (IllegalArgumentException expected) { checked++; }
        try {
            o("invalid", -1, MultiplayerStrategicModel.Role.ENGINE,0,true);
            throw new AssertionError("negative spell mana accepted");
        } catch (IllegalArgumentException expected) { checked++; }
        System.out.println("FOUR_AI_V33_SYNTHETIC_TWO_TURN_MODEL_PASS checks="+checked
            +" real_game_claims=0");
    }
}
