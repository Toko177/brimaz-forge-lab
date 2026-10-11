#!/usr/bin/env python3
"""OFFLINE-FROM-USER-JAR Forge 2.0.15 V24 Java compile and injection smoke.

Requires GitHub internet for precisely pinned 2.0.15 Java sources.
This checks actual patched class bytecode and 16 Java tactical invariants.
No fabricated matches, no mutation of the original installation.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--jar",type=Path,required=True)
a=p.parse_args()
original=a.jar.resolve()
if not original.is_file():raise FileNotFoundError(str(original))
with tempfile.TemporaryDirectory(prefix="forge-v24-compile-") as tmp:
    root=Path(tmp)
    patch=root/"forge-v24-compiled-fat.jar"
    shutil.copy2(original,patch)
    for script in ("patch_forge_charm_context.py",
                   "patch_forge_brimaz_v13.py",
                   "patch_forge_four_ai_targets.py",
                   "patch_forge_combat_trigger_prune.py"):
        print("V24_PINNED_FORGE_PATCH",script,flush=True)
        subprocess.run([sys.executable,str(ROOT/"scripts"/script),
                        "--jar",str(patch)],cwd=ROOT,check=True)
    jar_listing=subprocess.run(["jar","tf",str(patch)],capture_output=True,
                               text=True,check=True).stdout.splitlines()
    required=(
        "forge/ai/CombatTriggerNegativePrune.class",
        "forge/ai/ComputerUtilCombat.class",
        "forge/ai/AiTimeoutCooldownPolicy.class",
        "forge/ai/AiController.class",
    )
    missing=set(required)-set(jar_listing)
    if missing:raise RuntimeError("Patched REAL Forge JAR lacks classes "+str(missing))
    javap=subprocess.run(["javap","-c","-classpath",str(patch),
                          "forge.ai.ComputerUtilCombat"],
                         capture_output=True,text=True,check=True)
    if "forge/ai/CombatTriggerNegativePrune.shouldSkip" not in javap.stdout:
        raise RuntimeError("New predictor fast path is not present in actual compiled Forge bytecode")
    cls=root/"checks"
    cls.mkdir()
    testfile=ROOT/"tests/java/forge/ai/CombatTriggerNegativePruneChecks.java"
    subprocess.run(["javac","--release","21","-cp",str(patch),"-d",str(cls),
                    str(testfile)],cwd=ROOT,check=True)
    result=subprocess.run(["java","-cp",str(patch)+os.pathsep+str(cls),
                           "forge.ai.CombatTriggerNegativePruneChecks"],
                          capture_output=True,text=True,cwd=ROOT,check=True)
    if "FOUR_AI_V24_COMBAT_PRUNE_TESTS_PASS checks=16" not in result.stdout:
        raise RuntimeError("Expected 16 deterministic tactical invariants: "
                           +result.stdout+result.stderr)
    print(result.stdout.strip())
    print("V24_REAL_FORGE_2_0_15_BYTECODE_AND_TESTS_PASS",{
      "new_bytecode_classes":len(required),
      "true_combat_predictor_injection":True,
      "java_test_invariants":16,
      "patched_jar_sha256":hashlib.sha256(patch.read_bytes()).hexdigest(),
      "simulation_matches_executed":0,
      "original_jar_left_unchanged":True,
    },flush=True)
