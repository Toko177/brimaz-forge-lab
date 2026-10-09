#!/usr/bin/env python3
"""Forge 2.0.15: fix AI card-text evaluation NPE for Charm abilities.

Failure trace:
ComputerUtilCost.checkDiscardCost -> Card.getAbilityText ->
CharmEffect.makeFormatedDescription -> makePossibleOptions ->
TargetRestrictions.getAllCandidates -> sa.getActivatingPlayer().getGame()

The original CharmEffect fallback that sets the activating player comes
AFTER makePossibleOptions, too late for mode targeting. Set the mode's
activating player from its parent ability or the card controller first.

No card text, mana cost, targets or rules resolution is changed. Patch is
opt-in and must pass exact seeded failure reproductions.
"""
import argparse,hashlib,pathlib,subprocess,tempfile,urllib.request
p=argparse.ArgumentParser();p.add_argument("--jar",required=True);args=p.parse_args()
jar=pathlib.Path(args.jar).resolve()
url="https://raw.githubusercontent.com/Card-Forge/forge/forge-2.0.15/forge-game/src/main/java/forge/game/ability/effects/CharmEffect.java"
with urllib.request.urlopen(url,timeout=70) as r: src=r.read().decode("utf-8")
old="""            for (AbilitySub ch : choices) {
                // 603.3c If one of the modes would be illegal, that mode can't be chosen."""
new="""            for (AbilitySub ch : choices) {
                // Commander AI invokes Card.getAbilityText() when comparing
                // discard-cost candidates. At this stage ch can have no active
                // player; target enumeration would otherwise throw an NPE.
                // Preserve any explicitly set activating player.
                if (ch.getActivatingPlayer() == null) {
                    if (sa.getActivatingPlayer() != null) {
                        ch.setActivatingPlayer(sa.getActivatingPlayer());
                    } else if (source.getController() != null) {
                        ch.setActivatingPlayer(source.getController());
                    }
                }
                // 603.3c If one of the modes would be illegal, that mode can't be chosen."""
if src.count(old)!=1:raise RuntimeError("Forge CharmEffect source mismatch; refused patch")
src=src.replace(old,new,1)
with tempfile.TemporaryDirectory() as tmp:
    root=pathlib.Path(tmp)
    java=root/"forge/game/ability/effects/CharmEffect.java"
    java.parent.mkdir(parents=True)
    java.write_text(src,encoding="utf-8")
    classes=root/"classes";classes.mkdir()
    subprocess.run(["javac","--release","21","-cp",str(jar),"-d",str(classes),str(java)],check=True,timeout=180)
    compiled=classes/"forge/game/ability/effects/CharmEffect.class"
    if not compiled.is_file():raise RuntimeError("Missing CharmEffect compiled class")
    subprocess.run(["jar","uf",str(jar),"-C",str(classes),"forge/game/ability/effects/CharmEffect.class"],check=True)
    print("CHARM_CONTEXT_PATCHED_SHA256",hashlib.sha256(compiled.read_bytes()).hexdigest(),flush=True)
print("PATCHED_FORGE_JAR_SHA256",hashlib.sha256(jar.read_bytes()).hexdigest(),flush=True)
