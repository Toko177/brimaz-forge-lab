#!/usr/bin/env python3
"""Pin and instrument Forge 2.0.15 read-only card property query statistics.

This is NOT a gameplay policy or a speed optimization; it never changes
cardHasProperty return values, game rules or stack execution. Opt-in.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile
import urllib.request

p=argparse.ArgumentParser()
p.add_argument("--jar",required=True,type=Path)
args=p.parse_args()
jar=args.jar.resolve()
if not jar.is_file():raise FileNotFoundError(str(jar))
url=("https://raw.githubusercontent.com/Card-Forge/forge/forge-2.0.15/"
     "forge-game/src/main/java/forge/game/card/CardProperty.java")
with urllib.request.urlopen(url,timeout=90) as response:
    raw=response.read().decode("utf-8")

anchor="    public static boolean cardHasProperty(Card card, String property, Player sourceController, Card source, CardTraitBase spellAbility) {\n"
injection=anchor+"""        // V28: opt-in READ-ONLY telemetry; always execute every actual
        // original Magic rules predicate and preserve its return value.
        if (CardPropertyQueryProfiler.ENABLED) {
            CardPropertyQueryProfiler.observe(property);
        }
"""
if raw.count(anchor)!=1:raise RuntimeError("Forge 2.0.15 CardProperty source drift")
raw=raw.replace(anchor,injection,1)
helper=(Path(__file__).resolve().parents[1]/
        "patches/java/forge/game/card/CardPropertyQueryProfiler.java")
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    pkg=root/"forge/game/card"
    pkg.mkdir(parents=True)
    (pkg/"CardProperty.java").write_text(raw,encoding="utf-8")
    (pkg/"CardPropertyQueryProfiler.java").write_text(
        helper.read_text(encoding="utf-8"),encoding="utf-8")
    cls=root/"classes"
    cls.mkdir()
    subprocess.run(["javac","--release","21","-cp",str(jar),"-d",str(cls),
                    str(pkg/"CardProperty.java"),
                    str(pkg/"CardPropertyQueryProfiler.java")],
                    check=True,timeout=240)
    classes=sorted((cls/"forge/game/card").glob("CardProperty*.class"))
    if not any(x.name=="CardProperty.class" for x in classes):
        raise RuntimeError("Patched source CardProperty.class not compiled")
    if not any(x.name=="CardPropertyQueryProfiler.class" for x in classes):
        raise RuntimeError("Property observer was not compiled")
    command=["jar","uf",str(jar)]
    for output in classes:
        command+=["-C",str(cls),"forge/game/card/"+output.name]
    subprocess.run(command,check=True,timeout=120)
    print("FOUR_AI_REAL_CARD_PROPERTY_PROFILE_READY",{
        "compiled_classes":len(classes),
        "original_card_property_body_unchanged":True,
        "always_opt_in":True,
        "jar_sha256":hashlib.sha256(jar.read_bytes()).hexdigest(),
    },flush=True)
