#!/usr/bin/env python3
"""Opt-in public-information removal targeting for ALL four Forge Commander AIs.

Modifies priority of already-legal enemy creature removal targets, never
their spell costs, legal targets, Magic rules or opponent hidden hands.
Source-pinned to Card-Forge/forge forge-2.0.15.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile
import urllib.request

p=argparse.ArgumentParser()
p.add_argument("--jar",type=Path,required=True)
args=p.parse_args()
jar=args.jar.resolve()
assert jar.is_file(),"Pinned Forge JAR missing"

src="forge-ai/src/main/java/forge/ai/ComputerUtilCard.java"
url="https://raw.githubusercontent.com/Card-Forge/forge/forge-2.0.15/"+src
with urllib.request.urlopen(url,timeout=90) as stream:
    code=stream.read().decode("utf-8")

needle="""        if (c.getController().isOpponentOf(ai)) {
            value += ComputerUtil.evaluateBoardPosition(ai, c.getController()) / 4;
        }
        return value;
    }

    /**
     * getBestCreatureAI."""
replacement="""        if (c.getController().isOpponentOf(ai)) {
            value += ComputerUtil.evaluateBoardPosition(ai, c.getController()) / 4;
            if (Boolean.getBoolean("brimaz.fourSeatRemovalUrgency") && c.isCreature()) {
                value += MultiplayerRemovalUrgencyPolicy.publicThreatBonus(ai, c);
            }
        }
        return value;
    }

    /**
     * getBestCreatureAI."""
if code.count(needle)!=1:
    raise ValueError("Forge 2.0.15 removal-target source drift")
code=code.replace(needle,replacement,1)

helper=Path(__file__).resolve().parents[1]/"patches/java/forge/ai/MultiplayerRemovalUrgencyPolicy.java"
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    package=root/"forge/ai"
    package.mkdir(parents=True)
    (package/"ComputerUtilCard.java").write_text(code,encoding="utf-8")
    (package/"MultiplayerRemovalUrgencyPolicy.java").write_text(helper.read_text(encoding="utf-8"),encoding="utf-8")
    classes=root/"classes"
    classes.mkdir()
    subprocess.run([
        "javac","--release","21","-cp",str(jar),"-d",str(classes),
        str(package/"ComputerUtilCard.java"),
        str(package/"MultiplayerRemovalUrgencyPolicy.java"),
    ],check=True,timeout=180)
    paths=("forge/ai/ComputerUtilCard.class","forge/ai/MultiplayerRemovalUrgencyPolicy.class")
    for name in paths:
        if not (classes/name).is_file():raise RuntimeError("Missing "+name)
    command=["jar","uf",str(jar)]
    for name in paths:
        command+=["-C",str(classes),name]
    subprocess.run(command,check=True,timeout=90)
    print("FOUR_AI_REMOVAL_PRIORITY_PATCHED",{
        "compiled_classes":len(paths),
        "helper_sha256":hashlib.sha256((classes/paths[1]).read_bytes()).hexdigest(),
        "jar_sha256":hashlib.sha256(jar.read_bytes()).hexdigest()
    },flush=True)
