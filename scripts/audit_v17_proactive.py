#!/usr/bin/env python3
"""True four-seat Forge strict-vs-proactive defense paired audit.

No statistical winner is declared based on eight independent game processes.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

a=argparse.ArgumentParser()
a.add_argument("--pod",choices=["aristo","artifact"],required=True)
a.add_argument("--rotation",type=int,choices=range(4),required=True)
a.add_argument("--out",type=Path,required=True)
args=a.parse_args()
root=Path("results/batch")/args.pod
records={}
for label,tag in (("strict","V17-strict-coverage"),("proactive","V17-proactive-coverage")):
    path=root/tag/"games.json"
    samples=json.loads(path.read_text(encoding="utf-8"))
    if len(samples)!=1:raise ValueError("Expected one actual four-player game, got "+str(len(samples)))
    g=samples[0]
    log=Path(g["log"]).read_text(encoding="utf-8",errors="replace")
    choices=re.findall(
        r"FOUR_AI_V17_COVERAGE controller=(.*?) threatPlayers=(\d+) "
        r"baselinePermille=(\d+) afterPermille=(\d+) reserved=(\d+) "
        r"turn=(\d+) proactive=(true|false)",log)
    holds=[q for q in choices if int(q[4])>0]
    moves=[x for x in log.splitlines()
           if x.startswith(("Turn: ","Phase: ","Add To Stack: ","Combat: ","Game Outcome: "))
           and "Match Duration" not in x]
    if choices and any((q[6]=="true")!=(label=="proactive") for q in choices):
        raise ValueError("V17 policy activation mismatch with JVM flag")
    records[label]={
        "pod":g["pod"],"rotation":g["rotation"],"seed":g["seed"],
        "seats":g["seats"],"status":g["status"],"winner":g["winner_deck"],
        "brimaz_win":g["brimaz_win"],"wall_seconds":g["wall_seconds"],
        "quality":g.get("ai_quality_signatures",{}),
        "checks":len(choices),"held_actions":len(holds),
        "total_held_creatures":sum(int(x[4]) for x in holds),
        "controllers":dict(collections.Counter(q[0] for q in choices)),
        "controllers_holding":dict(collections.Counter(q[0] for q in holds)),
        "nearest_lethal_risks":sorted([int(x[2]) for x in choices],reverse=True)[:6],
        "observed_game_events":len(moves),
        "event_sha256":hashlib.sha256("\n".join(moves).encode()).hexdigest(),
    }
x,y=records["strict"],records["proactive"]
for col in ("pod","rotation","seed","seats"):
    if x[col]!=y[col]:raise ValueError("A/B mismatch "+col)
if x["rotation"]!=args.rotation:raise ValueError("Wrong requested seat rotation")
natural=x["status"]==y["status"]=="complete"
eq=natural and x["event_sha256"]==y["event_sha256"]
report={
    "policy":"V17 strict lethal vs proactive 85%-risk defensive coverage, all 4 AIs",
    "real_forge_jvm_processes":2,"pod":args.pod,"rotation":args.rotation,
    "strict":x,"proactive":y,"observed_natural_events_equal":eq,
    "descriptive_brimaz_win_delta_only_if_both_natural":
        int(bool(y["brimaz_win"]))-int(bool(x["brimaz_win"])) if natural else None,
    "speedup_only_if_same_natural_game":round(x["wall_seconds"]/y["wall_seconds"],3)
        if eq and y["wall_seconds"]>0 else None,
    "limitations":[
        "Proactive actions are intended risk choices, not proof of rational or optimal gameplay.",
        "Status complete does not replace an independent card legality + Forge-outcome certification.",
        "Matching seeds can yield divergent game actions because of AI timing and nondeterminism.",
        "Ordinary one-to-one blocker coverage is not exact Oracle combat resolution.",
        "No winrate inference or confident speedup from a few matched simulations.",
    ]
}
args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("FOUR_AI_PROACTIVE_COVERAGE_AUDIT",json.dumps({
    "pod":args.pod,"rotation":args.rotation,
    "natural":natural,"same_events":eq,
    "strict_winner":x["winner"],"proactive_winner":y["winner"],
    "proactive_checks":y["checks"],"proactive_held":y["total_held_creatures"],
    "proactive_controllers":y["controllers"],"baseline_seconds":x["wall_seconds"],
    "experimental_seconds":y["wall_seconds"]},ensure_ascii=False),flush=True)
if y["checks"]==0:raise SystemExit("No real V17 proactive defensive check executed")
