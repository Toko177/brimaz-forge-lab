#!/usr/bin/env python3
"""Opt-in four-player stack-controller fix + hybrid simulation for Brimaz pilot.

Not a solved 4-agent lookahead engine. Removes one opponent-only limitation
from copied-state trigger resolution. Hybrid is enabled ONLY with a JVM
system property and only for the Brimaz seat. Base Forge remains unchanged.
"""
import argparse
import hashlib
import pathlib
import subprocess
import tempfile
import urllib.request

p=argparse.ArgumentParser()
p.add_argument("--jar",required=True)
p.add_argument("--tag",default="forge-2.0.15")
args=p.parse_args()
jar=pathlib.Path(args.jar).resolve()
if not jar.is_file():p.error("Jar not found")
def source(path):
    url=f"https://raw.githubusercontent.com/Card-Forge/forge/{args.tag}/{path}"
    with urllib.request.urlopen(url,timeout=75) as res:
        return res.read().decode("utf-8")

sim_path="forge-ai/src/main/java/forge/ai/simulation/GameSimulator.java"
cli_path="forge-gui-desktop/src/main/java/forge/view/SimulateMatch.java"
sim=source(sim_path)
cli=source(cli_path)

old=r'''    public static void resolveStack(final Game game, final Player opponent) {
        // TODO: This needs to set an AI controller for all opponents, in case of multiplayer.
        PlayerControllerAi sim = new PlayerControllerAi(game, opponent, opponent.getLobbyPlayer());
        sim.getAi().setUseSimulation(AIOption.USE_FULL_SIMULATION);
        opponent.runWithController(() -> {
            final Set<Card> allAffectedCards = new HashSet<>();
            game.getAction().checkStateEffects(false, allAffectedCards);
            game.getStack().addAllTriggeredAbilitiesToStack();
            while (!game.getStack().isEmpty() && !game.isGameOver()) {
                debugPrint("Resolving:" + game.getStack().peekAbility());

                // Resolve the top effect on the stack.
                game.getStack().resolveStack();

                // Evaluate state based effects as a result of resolving stack.
                // Note: Needs to happen after resolve stack rather than at the
                // top of the loop to ensure state effects are evaluated after the
                // last resolved effect
                game.getAction().checkStateEffects(false, allAffectedCards);

                // Add any triggers additional triggers as a result of the above.
                // Must be below state effects, since legendary rule is evaluated
                // as part of state effects and trigger come afterward. (e.g. to
                // correctly handle two Dark Depths - one having no counters).
                game.getStack().addAllTriggeredAbilitiesToStack();

                // Continue until stack is empty.
            }
        }, sim);
    }'''
new=r'''    // Register simulated controllers for *all four participants* in a copy,
    // rather than only getWeakestOpponent(). This supports mandatory and
    // optional triggers controlled by multiple opponents during stack resolution.
    private static void withSimulationControllers(final Game game,
                                                   final List<Player> all,
                                                   final int index, final Runnable resolve) {
        if (index == all.size()) {
            resolve.run();
            return;
        }
        final Player p = all.get(index);
        final PlayerControllerAi controller =
                new PlayerControllerAi(game, p, p.getLobbyPlayer());
        controller.getAi().setUseSimulation(AIOption.USE_FULL_SIMULATION);
        p.runWithController(
                () -> withSimulationControllers(game, all, index + 1, resolve),
                controller);
    }

    public static void resolveStack(final Game game, final Player unusedOpponent) {
        final List<Player> all = new ArrayList<>();
        for (Player p : game.getPlayers()) {
            if (p.isInGame()) all.add(p);
        }
        withSimulationControllers(game, all, 0, () -> {
            final Set<Card> affected = new HashSet<>();
            game.getAction().checkStateEffects(false, affected);
            game.getStack().addAllTriggeredAbilitiesToStack();
            while (!game.getStack().isEmpty() && !game.isGameOver()) {
                debugPrint("Resolving:" + game.getStack().peekAbility());
                game.getStack().resolveStack();
                game.getAction().checkStateEffects(false, affected);
                game.getStack().addAllTriggeredAbilitiesToStack();
            }
        });
    }'''
if sim.count(old)!=1: raise ValueError("Forge GameSimulator 2.0.15 source differs: abort")
sim=sim.replace(old,new,1)

if "import forge.ai.AIOption;" not in cli:
    cli=cli.replace("import forge.ai.AiProfileUtil;","import forge.ai.AiProfileUtil;\nimport forge.ai.AIOption;",1)
old_cli='                rp.setPlayer(GamePlayerUtil.createAiPlayer(name, i - 1, profile));'
new_cli=r'''                final boolean useHybrid = Boolean.getBoolean("brimaz.multiplayerHybrid")
                        && d.getName().contains("Brimaz");
                if (useHybrid) {
                    rp.setPlayer(GamePlayerUtil.createAiPlayer(name, i - 1, 0,
                            EnumSet.of(AIOption.USE_HYBRID_SIMULATION), profile));
                    System.out.println("EDH_HYBRID_EXPERIMENT: enabled for " + name);
                } else {
                    rp.setPlayer(GamePlayerUtil.createAiPlayer(name, i - 1, profile));
                }'''
if cli.count(old_cli)!=1: raise ValueError("Forge SimulateMatch AI construction anchor changed")
cli=cli.replace(old_cli,new_cli,1)
with tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d)
    for path,src in [(sim_path,sim),(cli_path,cli)]:
        dest=root.joinpath(*path.split("/")[3:]) if False else None
        pkg="forge/ai/simulation/GameSimulator.java" if path==sim_path else "forge/view/SimulateMatch.java"
        dest=root/pkg
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(src,encoding="utf-8")
    out=root/"classes";out.mkdir()
    subprocess.run(["javac","--release","21","-cp",str(jar),"-d",str(out),
                    str(root/"forge/ai/simulation/GameSimulator.java"),
                    str(root/"forge/view/SimulateMatch.java")],check=True,timeout=240)
    for path in ["forge/ai/simulation/GameSimulator.class","forge/view/SimulateMatch.class"]:
        if not (out/path).is_file():raise ValueError("Compiled class missing "+path)
    subprocess.run(["jar","uf",str(jar),
                    "-C",str(out),"forge/ai/simulation/GameSimulator.class",
                    "-C",str(out),"forge/view/SimulateMatch.class"],
                   check=True,timeout=120)
    # Nested class compiled from GameSimulator? retain if present.
    print("COMPILED_EDH_SIM_CLASSES",[str(x.relative_to(out)) for x in out.rglob("*.class")],flush=True)
print("PATCHED_EDH_HYBRID_JAR_SHA256",hashlib.sha256(jar.read_bytes()).hexdigest(),flush=True)
