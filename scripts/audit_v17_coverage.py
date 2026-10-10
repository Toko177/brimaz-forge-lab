#!/usr/bin/env python3
"""Evidence-only V16/V17 paired real Forge Commander game comparison.

No proxy rules, no inventing tactical kills, no declaring winrate gains from
a few games, no treating equal seeds as guaranteed identical games.
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
runs={}
for label,tag in (("V16","V16-coverage-control"),("V17","V17-coverage-optimizer")):
    records=json.loads((root/tag/"games.json").read_text(encoding="utf-8"))
    if len(records)!=1:
        raise ValueError("One genuine Forge run per policy, got "+str(len(records)))
    row=records[0]
    log=Path(row["log"]).read_text(encoding="utf-8",errors="replace")
    events=[line for line in log.splitlines()
            if line.startswith(("Turn: ","Phase: ","Add To Stack: ","Combat: ","Game Outcome: "))
            and "Match Duration" not in line]
    checks=re.findall(r"FOUR_AI_V17_COVERAGE controller=(.*?) "
                      r"threatPlayers=(\d+) baselinePermille=(\d+) "
                      r"afterPermille=(\d+) reserved=(\d+) turn=(\d+)",log)
    reserves=re.findall(r"FOUR_AI_V17_RESERVE controller=(.*?) "
                        r"held=(\d+) riskReduction=(\d+)",log)
    old_checks=re.findall(r"FOUR_AI_DEFENSE_CHECK controller=",log)
    attack_lines=[x for x in log.splitlines() if x.startswith("Combat: ")]
    runs[label]={
        "pod":row["pod"],"rotation":row["rotation"],"seed":row["seed"],
        "seats":row["seats"],"status":row["status"],
        "winner":row["winner_deck"],"brimaz_win":row["brimaz_win"],
        "wall_seconds":row["wall_seconds"],"game_log":row["log"],
        "event_count":len(events),
        "event_sha256":hashlib.sha256("\n".join(events).encode()).hexdigest(),
        "combat_events":len(attack_lines),
        "coverage_checks":len(checks),
        "actual_defensive_reserve_events":len(reserves),
        "held_blocker_count":sum(int(x[1]) for x in reserves),
        "controllers_checked":dict(collections.Counter(x[0] for x in checks)),
        "max_threat_players":max([int(x[1]) for x in checks] or [0]),
        "old_v16_checks":len(old_checks),
    }
x,y=runs["V16"],runs["V17"]
for f in ("pod","rotation","seed","seats"):
    if x[f]!=y[f]:raise ValueError("Mismatch "+f)
if x["rotation"]!=args.rotation:raise ValueError("Wrong requested rotation")
complete_same=x["status"]==y["status"]=="complete"
equal=complete_same and x["event_sha256"]==y["event_sha256"]
report={
    "comparison":"V16 old policy vs V17 blocker-coverage policy (all four seats)",
    "pod":args.pod,"rotation":args.rotation,
    "actual_forge_jvm_processes":2,
    "same_source_decks_and_seeds":True,
    "reference":x,"experimental":y,
    "same_observed_complete_game":equal,
    "win_change_only_if_both_natural":
        int(bool(y["brimaz_win"]))-int(bool(x["brimaz_win"]))
        if complete_same else None,
    "speed_ratio_only_when_observed_games_identical":
        round(x["wall_seconds"]/y["wall_seconds"],3)
        if equal and y["wall_seconds"]>0 else None,
    "safety_and_limitations":[
        "No instant-speed responses, hidden information, complex multi-block rules or combat tricks simulated.",
        "A legal blocker graph approximates one normal attacker stopped per blocker.",
        "Target-specific attacker legality comes from real Forge, not a card-name proxy.",
        "A run ending at the clock limit has no counted winner.",
        "A complete status alone is not enough for independent EDH win certification.",
        "Two fixed pods and a few seeds cannot support a global winrate conclusion.",
    ],
}
args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("FOUR_AI_V17_COVERAGE_AUDIT",json.dumps({
    "pod":args.pod,"rotation":args.rotation,"statuses":[x["status"],y["status"]],
    "winners":[x["winner"],y["winner"]],"checked":y["coverage_checks"],
    "controllers":y["controllers_checked"],
    "reserved_blockers":y["held_blocker_count"],
    "same_events":equal,"speed_ratio_if_equivalent":
        report["speed_ratio_only_when_observed_games_identical"]}),flush=True)
if not y["coverage_checks"]:
    raise SystemExit("V17 compiled but its real-game AI code path was not exercised")
