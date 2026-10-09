#!/usr/bin/env python3
"""Audit missing Forge AI handlers in genuine multiseat EDH simulation logs.

'No AI assigned for API' is a decision-handler gap, not a direct proof that
the game rules were violated. Do not synthesize effects, outcomes or casts.
"""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import re

MISSING = re.compile(r"No AI assigned for API: ([A-Za-z][A-Za-z0-9]*)")


def inspect(raw, game):
    apis=Counter(MISSING.findall(raw))
    return {"pod":game["pod"],"seed":game["seed"],
            "policy":game.get("policy"),"status":game.get("status"),
            "brimaz_win":game.get("brimaz_win"),
            "missing_apis":dict(apis),
            "warnings":sum(apis.values())}


def audit(root):
    games=[]
    for manifest in sorted(root.rglob("games.json")):
        for g in json.loads(manifest.read_text(encoding="utf-8")):
            log=manifest.parent/Path(g["log"]).name
            if not log.is_file():
                raise FileNotFoundError(log)
            games.append(inspect(log.read_text(encoding="utf-8",errors="replace"),g))
    if not games:
        raise ValueError("Cannot infer engine completeness without raw matches")
    totals=Counter()
    affected=Counter()
    per_pod=defaultdict(Counter)
    for g in games:
        totals.update(g["missing_apis"])
        per_pod[g["pod"]].update(g["missing_apis"])
        affected.update(g["missing_apis"].keys())
    return {"summary":{
        "games":len(games),
        "completed_manifests":sum(g["status"]=="complete" for g in games),
        "games_with_missing_ai_handler":sum(g["warnings"]>0 for g in games),
        "warnings_total":sum(totals.values()),
        "missing_api_counts":dict(totals.most_common()),
        "affected_games_by_api":dict(affected),
        "warning_counts_by_pod":{pod:dict(counter) for pod,counter in sorted(per_pod.items())},
        "caveat":"An absent AI handler is a missing decision policy, not necessarily an illegal rules-engine action. Silence does not demonstrate optimal AI play."
    },"games":games}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    report=audit(a.input)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FORGE_COMMANDER_MISSING_AI_HANDLERS",json.dumps(report["summary"],ensure_ascii=False))


if __name__=="__main__":
    main()
