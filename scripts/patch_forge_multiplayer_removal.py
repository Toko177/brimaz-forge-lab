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


# V20 instrumentation: inspect BOTH rankings on precisely the same public
# legal target list, without needing a second generated match or guessing which
# removal spells were available in a counterfactual game. The real selection
# still delegates to Forge's original aggregator, preventing synthetic choices.
choose_old = """        return Aggregates.itemWithMax(list, c -> evaluateRemovalTargetPriority(ai, c));
    }

    private static int evaluateRemovalTargetPriority"""
choose_new = """        final Card actual = Aggregates.itemWithMax(list, c -> evaluateRemovalTargetPriority(ai, c));
        if (Boolean.getBoolean("brimaz.removalShadowAudit") && ai != null) {
            Card baselineBest = null;
            Card urgentBest = null;
            int baselineScore = Integer.MIN_VALUE;
            int urgentScore = Integer.MIN_VALUE;
            int options = 0;
            final boolean urgencyEnabled = Boolean.getBoolean("brimaz.fourSeatRemovalUrgency");
            for (Card candidate : list) {
                int effective = evaluateRemovalTargetPriority(ai, candidate);
                int bonus = candidate.isCreature() && candidate.getController().isOpponentOf(ai)
                        ? MultiplayerRemovalUrgencyPolicy.publicThreatBonus(ai, candidate) : 0;
                int stock = urgencyEnabled ? effective - bonus : effective;
                int counterfactual = stock + bonus;
                options++;
                if (stock > baselineScore) { baselineScore = stock; baselineBest = candidate; }
                if (counterfactual > urgentScore) { urgentScore = counterfactual; urgentBest = candidate; }
            }
            if (options > 1) {
                boolean changed = baselineBest != urgentBest;
                System.out.println("FOUR_AI_REMOVAL_SHADOW player=" + ai.getName()
                        + " options=" + options + " baseline=" +
                        (baselineBest == null ? "none" : baselineBest.getName()+"#"+baselineBest.getId())
                        + " urgency=" +
                        (urgentBest == null ? "none" : urgentBest.getName()+"#"+urgentBest.getId())
                        + " chosen=" + (actual == null ? "none" : actual.getName()+"#"+actual.getId())
                        + " changed=" + changed
                        + " baselineScore=" + baselineScore
                        + " urgencyScore=" + urgentScore);
            }
        }
        return actual;
    }

    private static int evaluateRemovalTargetPriority"""
if code.count(choose_old)!=1:
    raise ValueError("Forge source drift: removal shadow choice anchor")
code=code.replace(choose_old,choose_new,1)

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
