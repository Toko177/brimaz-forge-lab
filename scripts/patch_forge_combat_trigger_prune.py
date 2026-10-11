#!/usr/bin/env python3
"""Opt-in low-risk fast negatives in Forge 2.0.15 combat AI prediction.

No actual Magic trigger processing is changed: only expensive hypothetical
AI combat evaluation for cases that ALWAYS return false in stock Forge.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile
import urllib.request

p=argparse.ArgumentParser()
p.add_argument("--jar",type=Path,required=True)
a=p.parse_args()
jar=a.jar.resolve()
if not jar.is_file():raise ValueError("Pinned Forge desktop JAR is missing")
url=("https://raw.githubusercontent.com/Card-Forge/forge/forge-2.0.15/"
    "forge-ai/src/main/java/forge/ai/ComputerUtilCombat.java")
with urllib.request.urlopen(url,timeout=90) as resp:
    code=resp.read().decode("utf-8")

anchor="""        if (!trigger.zonesCheck(game.getZoneOf(trigger.getHostCard()))) {
            return false;
        }
        if (!trigger.requirementsCheck(game)) {
            return false;
        }"""
fast="""        // V24 OPT-IN: exact negative cases established by downstream
        // branch conditions; avoid expensive requirementsCheck for cases
        // that could NEVER trigger in this hypothetical combat state.
        if (CombatTriggerNegativePrune.ENABLED
                && CombatTriggerNegativePrune.shouldSkip(mode,
                    defender != null,
                    mode == TriggerType.Attacks && combat.isAttacking(attacker),
                    mode == TriggerType.Attacks && trigger.hasParam("Alone")
                        && plannedAttackers != null && plannedAttackers.size() != 1)) {
            return false;
        }
"""
if code.count(anchor)!=1:raise ValueError("Combat trigger predictor source drift from forge-2.0.15")
code=code.replace(anchor,fast+anchor,1)
source=(Path(__file__).resolve().parents[1]/
        "patches/java/forge/ai/CombatTriggerNegativePrune.java")
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    pkg=root/"forge/ai"
    pkg.mkdir(parents=True)
    (pkg/"ComputerUtilCombat.java").write_text(code,encoding="utf-8")
    (pkg/"CombatTriggerNegativePrune.java").write_text(
        source.read_text(encoding="utf-8"),encoding="utf-8")
    classes=root/"classes"
    classes.mkdir()
    subprocess.run([
        "javac","--release","21","-cp",str(jar),"-d",str(classes),
        str(pkg/"ComputerUtilCombat.java"),str(pkg/"CombatTriggerNegativePrune.java"),
    ],check=True,timeout=240)
    outputs=sorted((classes/"forge/ai").glob("ComputerUtilCombat*.class"))
    outputs += sorted((classes/"forge/ai").glob("CombatTriggerNegativePrune*.class"))
    if not outputs or not (classes/"forge/ai/ComputerUtilCombat.class").exists() \
        or not (classes/"forge/ai/CombatTriggerNegativePrune.class").exists():
        raise RuntimeError("Missing compiled combat prediction optimizer")
    cmd=["jar","uf",str(jar)]
    for f in outputs:cmd+=["-C",str(classes),f"forge/ai/{f.name}"]
    subprocess.run(cmd,check=True,timeout=120)
    print("FOUR_AI_V24_COMBAT_NEGATIVE_PRUNE_COMPILED",{
        "class_count":len(outputs),
        "jar_sha256":hashlib.sha256(jar.read_bytes()).hexdigest()
    },flush=True)
