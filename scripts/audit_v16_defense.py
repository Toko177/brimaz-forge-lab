#!/usr/bin/env python3
"""Evidence of V16 public-board tactical defense on genuine Forge Commander games.

The opponent policy, seat assignment, seed, time limits, and deck hashes match.
The only A/B toggle is fourSeatDefensiveReserve. No winrate claims from
uncertified logs, no speed comparison on divergent decision streams.
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
root=Path("results/batch")/args.pod
games={}
for label,tag in (("V15","V15-defensive-control"),("V16","V16-defensive-reserve")):
    rows=json.loads((root/tag/"games.json").read_text(encoding="utf-8"))
    if not rows: raise ValueError("Missing real 4-player games for "+label)
    group={}
    for row in rows:
        key=(row["pod"],row["rotation"],row["seed"])
        if key in group: raise ValueError("Duplicate seed/pod/rotation "+str(key))
        log=Path(row["log"]).read_text(encoding="utf-8",errors="replace")
        trace=[l for l in log.splitlines()
               if l.startswith(("Turn: ","Phase: ","Add To Stack: ","Combat: ","Game Outcome: "))
               and "Match Duration" not in l]
        reserve=re.findall(
            r"FOUR_AI_DEFENSE_RESERVE controller=(.*?) held=(\d+) "
            r"dangerousOpponents=(\d+) maxVisibleLifePressure=(\d+) turn=(\d+)",log)
        choices=re.findall(r"FOUR_AI_TARGET: controller=(.*?) chosen=(.*?) visibleSafeDamage=",log)
        attacks=re.findall(r"^Combat: (Ai\(\d+\)-.+?) assigned (.*?) to attack "
                           r"(Ai\(\d+\)-.+?)\.$",log,re.M)
        group[key]={
          "seats":row["seats"],"status":row["status"],
          "winner":row["winner_deck"],"brimaz_win":row["brimaz_win"],
          "wall_seconds":row["wall_seconds"],"events":len(trace),
          "trace_sha256":hashlib.sha256("\n".join(trace).encode("utf-8")).hexdigest(),
          "reserve_decisions":len(reserve),"reserved_blockers":sum(int(x[1]) for x in reserve),
          "ai_reserving":dict(collections.Counter(x[0] for x in reserve)),
          "max_dangerous_opponents":max([int(x[2]) for x in reserve] or [0]),
          "target_evaluations":len(choices),"declared_attacks":len(attacks),
        }
    games[label]=group
if set(games["V15"])!=set(games["V16"]):
    raise ValueError("Unpaired seed or rotation; reject benchmark")
pairs=[]
for key in sorted(games["V15"]):
    a,b=games["V15"][key],games["V16"][key]
    if a["seats"]!=b["seats"]: raise ValueError("Different canonical deck positions")
    equivalent=(a["status"]==b["status"]=="complete"
                and a["trace_sha256"]==b["trace_sha256"])
    pairs.append({
        "pod":key[0],"rotation":key[1],"seed":key[2],
        "V15":a,"V16":b,
        "identical_observed_complete_game":equivalent,
        "wall_ratio_only_if_identical_completed":
            round(a["wall_seconds"]/b["wall_seconds"],3)
            if equivalent and b["wall_seconds"]>0 else None
    })
out={
    "feature":"Shared 4-seat defense against public life, infect and commander counterattacks",
    "paired_games":len(pairs),"true_forge_jvm_executions":2*len(pairs),
    "tactical_reserve_actually_triggered":any(k["V16"]["reserve_decisions"] for k in pairs),
    "total_reserved_blockers":sum(k["V16"]["reserved_blockers"] for k in pairs),
    "observably_identical_natural_pairs":sum(k["identical_observed_complete_game"] for k in pairs),
    "pairs":pairs,
    "limits":[
        "No assumed hidden hands, Oracle-perfect attack forecasts or political deals.",
        "Only observed decisions: cannot prove the presence of a legal missed action.",
        "Commander, poison and life threat values reflect current PUBLIC battlefield.",
        "Censored games are not victories and are not speedup samples.",
        "A/B seed equality does not guarantee deterministic Forge timing or choices.",
        "A log status of 'complete' is not independent natural-Commander certification.",
    ],
}
path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("FOUR_AI_V16_DEFENSE_AUDIT",json.dumps(out,ensure_ascii=False),flush=True)
