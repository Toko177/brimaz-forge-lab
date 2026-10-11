#!/usr/bin/env python3
"""Add strictly opt-in four-AI protection from already-targeted commander removal.

The complete Forge 2.0.15 stack, legality, target, and mana checks stay intact;
only a profile-based chance/CMC refusal near the end of CounterAi is overridden
when opponent's PUBLIC spell explicitly targets our own commander for removal.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile
import urllib.request

ap=argparse.ArgumentParser()
ap.add_argument("--jar",required=True,type=Path)
args=ap.parse_args()
jar=args.jar.resolve()
assert jar.is_file(),"No real Forge pinned desktop JAR found"
url=("https://raw.githubusercontent.com/Card-Forge/forge/forge-2.0.15/"
     "forge-ai/src/main/java/forge/ai/ability/CounterAi.java")
with urllib.request.urlopen(url,timeout=90) as handle:
    source=handle.read().decode("utf-8")

needle="""        if (dontCounter) {
            return new AiAbilityDecision(0, AiPlayDecision.CantPlayAi);
        }

        return new AiAbilityDecision(100, AiPlayDecision.WillPlay);"""
repl="""        final boolean v22CommanderRemoval = MultiplayerCriticalCounterPolicy.isCommanderRemovalThreat(ai, tgtSA);
        final boolean v22LethalLife = MultiplayerCriticalCounterPolicy.isLethalTargetedLifeSpell(ai, tgtSA);
        if (Boolean.getBoolean("brimaz.counterDecisionAudit") && tgtSA != null) {
            System.out.println("FOUR_AI_COUNTER_DECISION player="+ai.getName()
                    +" spell="+(tgtSA.getHostCard()==null?"none":tgtSA.getHostCard().getName())
                    +" originalDecline="+dontCounter
                    +" threatensCommander="+v22CommanderRemoval
                    +" threatensLethalLife="+v22LethalLife
                    +" policyActive="+Boolean.getBoolean("brimaz.fourSeatCounterCritical"));
        }
        if (dontCounter && Boolean.getBoolean("brimaz.fourSeatCounterCritical")
                && (v22CommanderRemoval || v22LethalLife)) {
            // Original stack-target legality and affordability already passed
            // above. Only override the low-CMC/profile chance to ignore this.
            System.out.println("FOUR_AI_CRITICAL_COUNTER accepted player="+ai.getName()
                    +" hostileSpell="+(tgtSA.getHostCard()==null ? "ability" : tgtSA.getHostCard().getName())
                    +" protectedCommander="+(v22CommanderRemoval && tgtSA.getTargetCard()!=null ? tgtSA.getTargetCard().getName() : "none")
                    +" imminentLife="+v22LethalLife);
            dontCounter = false;
        }
        if (dontCounter) {
            return new AiAbilityDecision(0, AiPlayDecision.CantPlayAi);
        }

        return new AiAbilityDecision(100, AiPlayDecision.WillPlay);"""
if source.count(needle)!=1:raise ValueError("CounterAi source not pinned to expected 2.0.15")
source=source.replace(needle,repl,1)
helper=Path(__file__).resolve().parents[1]/"patches/java/forge/ai/ability/MultiplayerCriticalCounterPolicy.java"
with tempfile.TemporaryDirectory() as temporary:
    folder=Path(temporary)/"forge/ai/ability"
    folder.mkdir(parents=True)
    (folder/"CounterAi.java").write_text(source,encoding="utf-8")
    (folder/"MultiplayerCriticalCounterPolicy.java").write_text(helper.read_text(encoding="utf-8"),encoding="utf-8")
    cls=Path(temporary)/"classes"
    cls.mkdir()
    subprocess.run(["javac","--release","21","-cp",str(jar),"-d",str(cls),
                   str(folder/"CounterAi.java"),
                   str(folder/"MultiplayerCriticalCounterPolicy.java")],check=True,timeout=240)
    for name in ("CounterAi","MultiplayerCriticalCounterPolicy"):
        if not (cls/"forge/ai/ability"/(name+".class")).is_file():
            raise RuntimeError("Missing compiled Forge counter AI bytecode "+name)
    cmd=["jar","uf",str(jar)]
    for name in ("CounterAi","MultiplayerCriticalCounterPolicy"):
        cmd+=["-C",str(cls),"forge/ai/ability/"+name+".class"]
    subprocess.run(cmd,check=True,timeout=90)
    print("FOUR_AI_COUNTER_CRITICAL_PATCHED",
          "jar_sha256="+hashlib.sha256(jar.read_bytes()).hexdigest(),flush=True)
