#!/usr/bin/env python3
"""Pinned Forge 2.0.15 five-literal card rule hot-path with exact stock fallback.

Optimized properties: IsCommander, Self, YouCtrl, YouOwn, Other.
Never cache state or infer hidden data. Only opt-in. Source original method
body is untouched except renaming to allow same-state reference checks.
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
with urllib.request.urlopen(url,timeout=90) as resp:
    original=resp.read().decode("utf-8")

anchor=("    public static boolean cardHasProperty(Card card, String property, "
        "Player sourceController, Card source, CardTraitBase spellAbility) {\n")
if original.count(anchor)!=1:raise RuntimeError("Original card-property entrypoint anchor changed")
stock=original.replace(anchor,anchor.replace(
    "public static boolean cardHasProperty(","private static boolean cardHasPropertyV30Stock("),1)
wrapper=(
"""    // V30: optional same-state, source-identical evaluation of five exact
    // literal property predicates. Unrecognized properties keep the original
    // Forge method and all its dynamic state checks completely intact.
    public static boolean cardHasProperty(Card card, String property,
            Player sourceController, Card source, CardTraitBase spellAbility) {
        if (CardPropertyLiteralFastPath.ENABLED && property != null
                && !card.isPhasedOut()) {
            // The five recognized cases do not read game combat state.
            // Always acquire the same LKI controller the stock method reads.
            // Unknown literals never enter this path.
            if ("IsCommander".equals(property) || "Self".equals(property)
                    || "YouCtrl".equals(property) || "YouOwn".equals(property)
                    || "Other".equals(property)) {
                final Game game = card.getGame();
                final Card lki = game.getChangeZoneLKIInfo(card);
                final Player controller = lki.getController();
                Boolean value = CardPropertyLiteralFastPath.evaluate(
                    card, property, sourceController, source, controller);
                if (value != null) {
                    CardPropertyLiteralFastPath.hit();
                    if (CardPropertyLiteralFastPath.SHADOW) {
                        // Call the EXACT original unmodified method body on
                        // the very same current Forge state. Validation may
                        // be slower and is never used as a speed benchmark.
                        final boolean stockValue=cardHasPropertyV30Stock(
                            card,property,sourceController,source,spellAbility);
                        CardPropertyLiteralFastPath.verify(
                            value.booleanValue(),stockValue,property);
                    }
                    return value.booleanValue();
                }
            }
        }
        return cardHasPropertyV30Stock(card,property,sourceController,source,spellAbility);
    }

""")
where=stock.index(anchor.replace(
    "public static boolean cardHasProperty(","private static boolean cardHasPropertyV30Stock("))
stock=stock[:where]+wrapper+stock[where:]
helper=(Path(__file__).resolve().parents[1]/
        "patches/java/forge/game/card/CardPropertyLiteralFastPath.java")
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    pkg=root/"forge/game/card"
    pkg.mkdir(parents=True)
    (pkg/"CardProperty.java").write_text(stock,encoding="utf-8")
    (pkg/"CardPropertyLiteralFastPath.java").write_text(
        helper.read_text(encoding="utf-8"),encoding="utf-8")
    classes=root/"classes"
    classes.mkdir()
    subprocess.run([
        "javac","--release","21","-cp",str(jar),"-d",str(classes),
        str(pkg/"CardProperty.java"),str(pkg/"CardPropertyLiteralFastPath.java"),
    ],check=True,timeout=240)
    outputs=sorted((classes/"forge/game/card").glob("CardProperty*.class"))
    required={"CardProperty.class","CardPropertyLiteralFastPath.class"}
    if not required.issubset({x.name for x in outputs}):
        raise RuntimeError("Compiled genuine Forge rules classes missing")
    command=["jar","uf",str(jar)]
    for item in outputs:
        command+=["-C",str(classes),"forge/game/card/"+item.name]
    subprocess.run(command,check=True,timeout=120)
    print("FOUR_AI_V30_SOURCE_EQUIVALENT_LITERAL_FASTPATH_COMPILED",{
        "actual_rule_engine_bytecodes":len(outputs),
        "pinned_stock_rules_body_renamed_not_rewritten":True,
        "five_literal_cases_only":True,
        "default_enabled":False,
        "jar_sha256":hashlib.sha256(jar.read_bytes()).hexdigest(),
    },flush=True)
