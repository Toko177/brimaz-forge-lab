#!/usr/bin/env python3
"""Paired genuine Forge V14/V15 combat executor audit for all four seats.

A/B has exact seed and seats but decisions may diverge, so do not confuse
wall-time deltas with proven speedup when event streams differ.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

p=argparse.ArgumentParser()
p.add_argument("--pod",choices=["aristo","artifact"],required=True)
p.add_argument("--out",required=True)
args=p.parse_args()
groups={}
for label, tag in [("v14","V14-target-control"),("v15","V15-serial-mandatory")]:
    path=Path("results/batch")/args.pod/tag/"games.json"
    games=json.loads(path.read_text(encoding="utf-8"))
    if not games: raise ValueError("No genuine games in "+str(path))
    bykey={}
    for game in games:
        key=(game["pod"],game["rotation"],game["seed"])
        if key in bykey: raise ValueError("Duplicate seeded 4-seat game")
        log=Path(game["log"]).read_text(encoding="utf-8",errors="replace")
        events=[x for x in log.splitlines()
                if x.startswith(("Turn: ","Phase: ","Add To Stack: ","Game Outcome: "))
                and "Match Duration" not in x]
        markers=re.findall(
            r"FOUR_AI_SERIAL_FORCED_ATTACKS controller=(.*?) candidates=(\d+)",log)
        choices=re.findall(r"FOUR_AI_TARGET: controller=(.*?) chosen=(.*?) visibleSafeDamage=",
                           log)
        attacks=re.findall(r"^Combat: (Ai\(\d+\)-.+?) assigned (.*?) to attack "
                           r"(Ai\(\d+\)-.+?)\.$",log,re.M)
        bykey[key]={
            "seats":game["seats"],
            "status":game["status"],
            "winner":game["winner_deck"],
            "brimaz_win":game["brimaz_win"],
            "wall_seconds":game["wall_seconds"],
            "events":len(events),
            "event_sha256":hashlib.sha256("\n".join(events).encode()).hexdigest(),
            "mandatory_attack_evaluations":len(markers),
            "mandatory_attack_candidates":sum(int(k[1]) for k in markers),
            "serial_controllers":dict(collections.Counter(k[0] for k in markers)),
            "tactical_target_events":len(choices),
            "attack_declarations":len(attacks),
        }
    groups[label]=bykey
if set(groups["v14"])!=set(groups["v15"]):
    raise ValueError("A/B mismatch: seeds and rotations")
out=[]
for key in sorted(groups["v14"]):
    a,b=groups["v14"][key],groups["v15"][key]
    if a["seats"]!=b["seats"]: raise ValueError("A/B seat mismatch")
    is_same=(a["status"]==b["status"]=="complete" and
             a["event_sha256"]==b["event_sha256"])
    out.append({
        "pod":key[0],"rotation":key[1],"seed":key[2],
        "v14":a,"v15":b,
        "identical_observed_complete_game":is_same,
        "wall_ratio_if_identical_observed_only":
            round(a["wall_seconds"]/b["wall_seconds"],3)
            if is_same and b["wall_seconds"]>0 else None,
        "observed_win_change_only_if_both_complete":
            int(bool(b["brimaz_win"]))-int(bool(a["brimaz_win"]))
            if a["status"]==b["status"]=="complete" else None
    })
report={
    "experiment":"V15 deterministic mandatory-attacker evaluation for all four Commander AIs",
    "paired_games":len(out),"forge_processes":len(out)*2,
    "serial_path_exercised":sum(x["v15"]["mandatory_attack_evaluations"] for x in out)>0,
    "v15_serial_evaluations":sum(x["v15"]["mandatory_attack_evaluations"] for x in out),
    "v15_serial_candidates":sum(x["v15"]["mandatory_attack_candidates"] for x in out),
    "observed_complete_equivalent_pairs":sum(x["identical_observed_complete_game"] for x in out),
    "pairs":out,
    "limitations":[
        "Serial evaluation removes a concurrent access pattern, but may alter gameplay timing.",
        "Identical seeds alone do not establish identical stochastic game paths.",
        "Partial, censored, timed out or diverging games yield no proven speedup.",
        "Game-completion status requires separate original Forge log certification before winrate use."
    ]
}
dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("V15_FOUR_AI_ENGINE_AUDIT",json.dumps(report,ensure_ascii=False),flush=True)
if not report["serial_path_exercised"]:
    raise SystemExit("Serial code not exercised in actual four-player game")
