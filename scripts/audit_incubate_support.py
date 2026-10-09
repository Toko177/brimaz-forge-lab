#!/usr/bin/env python3
"""Audit whether Incubate AI is supported and whether Forge effects resolve.

The fact that an Incubate effect resolved does NOT prove that the AI
voluntarily selected it: Brimaz / Exarch also have mandatory triggers.
Do not count tokens shown in a text description as actual tokens created.
"""
import argparse
import json
from pathlib import Path
import re

ACTIVATION = re.compile(r"^Add To Stack: Ai\((\d+)\)-.* activated Incubator Token$", re.M)
INCUBATE_RESOLVED = re.compile(r"^Resolve Stack: .*\bincubate\b", re.I | re.M)
TOKEN_ZONE = re.compile(r"^Zone Change: Incubator Token \((\d+)\) was put into", re.M)


def analyze(raw, game):
    triggers = [m[0] for m in INCUBATE_RESOLVED.finditer(raw)]
    return {
        "pod": game["pod"], "seed": game["seed"], "policy": game["policy"],
        "status": game["status"], "winner": game.get("winner_deck"),
        "brimaz_win": game.get("brimaz_win"),
        "unsupported_incubate_ai_warnings": raw.count("No AI assigned for API: Incubate"),
        "resolved_incubate_description_events": len(triggers),
        "incubator_transform_stack_activations": len(ACTIVATION.findall(raw)),
        "incubator_zone_changes": len(TOKEN_ZONE.findall(raw)),
        "caveat": "Mandatory Incubate triggers can resolve even with no voluntary Incubate AI handler; text mentions are not token creation metrics."
    }


def audit(root):
    games=[]
    for manifest in sorted(root.rglob("games.json")):
        for g in json.loads(manifest.read_text(encoding="utf-8")):
            log=manifest.parent/Path(g["log"]).name
            if not log.is_file():
                raise FileNotFoundError(log)
            games.append(analyze(log.read_text(encoding="utf-8", errors="replace"),g))
    if not games:
        raise ValueError("No raw 4-player games available")
    total=lambda key: sum(g[key] for g in games)
    summary={
        "games": len(games),
        "natural_games": sum(g["status"]=="complete" for g in games),
        "brimaz_natural_wins": sum(g["status"]=="complete" and g["brimaz_win"] is True for g in games),
        "unsupported_incubate_ai_warnings":total("unsupported_incubate_ai_warnings"),
        "resolved_incubate_description_events":total("resolved_incubate_description_events"),
        "incubator_transform_stack_activations":total("incubator_transform_stack_activations"),
        "incubator_zone_changes":total("incubator_zone_changes"),
        "no_claim_of_more_voluntary_incubation_without_explicit_actions":True,
    }
    return {"summary":summary,"games":games}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=audit(a.input)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("INCUBATE_AI_REAL_FORGE_AUDIT",json.dumps(result["summary"],ensure_ascii=False))


if __name__=="__main__":
    main()
