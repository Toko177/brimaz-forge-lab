#!/usr/bin/env python3
"""Raise only Forge AI per-decision evaluation budget, never Magic game rules.

Forge 2.0.15 Game.AI_TIMEOUT defaults to 5 seconds; AiController can log
java.util.concurrent.TimeoutException and abandon an evaluation. This patch
increases the budget equally for *all four seats* in headless simulation.
It may improve deliberation and/or increase runtime; both must be measured.
"""
import argparse
import hashlib
import pathlib
import subprocess
import tempfile
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("--jar", required=True)
p.add_argument("--tag", default="forge-2.0.15")
p.add_argument("--seconds", type=int, default=10)
a = p.parse_args()
if not 5 <= a.seconds <= 20:
    p.error("AI time budget must be 5..20 seconds")
jar = pathlib.Path(a.jar).resolve()
if not jar.is_file():
    p.error("Forge JAR not found")
url = ("https://raw.githubusercontent.com/Card-Forge/forge/" + a.tag +
       "/forge-gui-desktop/src/main/java/forge/view/SimulateMatch.java")
with urllib.request.urlopen(url, timeout=90) as res:
    source = res.read().decode("utf-8")
anchor = "        final Game g1 = mc.createGame();"
if source.count(anchor) != 1:
    raise ValueError("Unexpected Forge headless Game instantiation anchor")
patch = (
    anchor + "\n"
    + f"        g1.AI_TIMEOUT = {a.seconds}; // Equal per-action CPU thinking budget for all seats.\n"
    + f'        System.out.println("FORGE_AI_THINK_SECONDS={a.seconds}");'
)
source = source.replace(anchor, patch, 1)
with tempfile.TemporaryDirectory() as d:
    root = pathlib.Path(d)
    file = root / "forge" / "view" / "SimulateMatch.java"
    file.parent.mkdir(parents=True)
    file.write_text(source, encoding="utf-8")
    classes = root / "classes"
    classes.mkdir()
    subprocess.run(["javac", "--release", "21", "-cp", str(jar), "-d", str(classes), str(file)],
                   check=True, timeout=240)
    cl = classes / "forge" / "view" / "SimulateMatch.class"
    if not cl.is_file():
        raise ValueError("Patched SimulateMatch.class missing")
    subprocess.run(["jar", "uf", str(jar), "-C", str(classes), "forge/view/SimulateMatch.class"],
                   check=True, timeout=90)
    print("FORGE_AI_THINK_CLASS_SHA256", hashlib.sha256(cl.read_bytes()).hexdigest(), flush=True)
print("FORGE_AI_THINK_JAR_SHA256", hashlib.sha256(jar.read_bytes()).hexdigest(), flush=True)
