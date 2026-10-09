#!/usr/bin/env python3
"""Opt-in, auditable patch of Forge 2.0.15's missing Incubate AI API mapping.

We DO NOT patch MTG rules or rig games. This is AI policy only:
Incubate API gets the generic AlwaysPlayAi handler instead of CannotPlayAi.
Requires a separate A/B evaluation before considering this "stronger".
"""
import argparse
import hashlib
import pathlib
import subprocess
import tempfile
import urllib.request

p=argparse.ArgumentParser()
p.add_argument("--jar",required=True)
args=p.parse_args()
jar=pathlib.Path(args.jar).resolve()
if not jar.is_file(): p.error("Missing jar "+str(jar))
url=("https://raw.githubusercontent.com/Card-Forge/forge/"
     "forge-2.0.15/forge-ai/src/main/java/forge/ai/SpellApiToAi.java")
with urllib.request.urlopen(url,timeout=60) as response:
    source=response.read().decode("utf-8")
target="            .put(ApiType.ImmediateTrigger, ImmediateTriggerAi.class)"
if source.count(target)!=1 or "put(ApiType.Incubate," in source:
    raise ValueError("Unexpected Forge source; patch refused")
patched=source.replace(target,target+"\n            .put(ApiType.Incubate, AlwaysPlayAi.class)",1)
with tempfile.TemporaryDirectory() as directory:
    root=pathlib.Path(directory)
    java=root/"forge"/"ai"/"SpellApiToAi.java"
    java.parent.mkdir(parents=True,exist_ok=True)
    java.write_text(patched,encoding="utf-8")
    classes=root/"classes"
    classes.mkdir()
    subprocess.run(["javac","--release","21","-cp",str(jar),"-d",str(classes),
                    str(java)],check=True,timeout=180)
    cls=classes/"forge"/"ai"/"SpellApiToAi.class"
    if not cls.is_file(): raise ValueError("Compiled class missing")
    subprocess.run(["jar","uf",str(jar),"-C",str(classes),
                    "forge/ai/SpellApiToAi.class"],check=True,timeout=120)
    print("PATCHED_INCUBATE",cls.stat().st_size,"bytes",
          "class sha256",hashlib.sha256(cls.read_bytes()).hexdigest(),flush=True)
print("PATCHED_JAR_SHA256",hashlib.sha256(jar.read_bytes()).hexdigest(),flush=True)
