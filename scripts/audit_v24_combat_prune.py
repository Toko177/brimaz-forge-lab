#!/usr/bin/env python3
"""Paired REAL Forge 4-seat Commander game audit of AI-only trigger optimization.

A filtered hypothetical trigger is NOT a suppressed real Magic trigger.
The only valid performance comparison requires natural completion and
strictly identical observable event fingerprints.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

p=argparse.ArgumentParser()
p.add_argument("--pod",choices=["aristo","artifact"],required=True)
p.add_argument("--rotation",type=int,choices=range(4),required=True)
p.add_argument("--out",required=True,type=Path)
a=p.parse_args()
root=Path("results/batch")/a.pod
s={}
for label,tag in (("control","V24-stock-trigger"),("optimized","V24-fast-negative-trigger")):
    manifest=json.loads((root/tag/"games.json").read_text(encoding="utf-8"))
    if len(manifest)!=1:raise ValueError("One genuine independent Forge JVM expected")
    r=manifest[0]
    raw=(root/tag/Path(r["log"]).name).read_text(encoding="utf-8",errors="replace")
    score=[x for x in raw.splitlines()
           if x.startswith(("Turn: ","Phase: ","Add To Stack: ","Combat: ","Game Outcome: "))
           and "Match Duration" not in x]
    hits=[int(n) for n in re.findall(r"FOUR_AI_FAST_COMBAT_TRIGGER_PRUNED count=(\d+)",raw)]
    timeout=list(re.finditer(r"AI_EVAL_TIMEOUT_V10: player=(.*?) globalTurn=(\d+) phase=(\w+)",raw))
    s[label]={
        "pod":r["pod"],"rotation":r["rotation"],"seed":r["seed"],"seats":r["seats"],
        "status":r["status"],"winner":r["winner_deck"],
        "brimaz_win":r["brimaz_win"],"wall_seconds":r["wall_seconds"],
        "events_sha256":hashlib.sha256("\n".join(score).encode()).hexdigest(),
        "events_count":len(score),
        "ai_timeout_count":len(timeout),
        "timeout_by_player":dict(Counter(x.group(1) for x in timeout)),
        "exact_negative_combat_trigger_evaluations_pruned":hits[-1] if hits else 0,
        "filter_shutdown_summary_seen":bool(hits),
    }
x,y=s["control"],s["optimized"]
for k in ("pod","rotation","seats","seed"):
    if x[k]!=y[k]:raise ValueError("Unpaired random seeds or deck rotation "+k)
if x["rotation"]!=a.rotation:raise ValueError("Rotation inconsistent")
same_natural=(x["status"]==y["status"]=="complete" and
              x["events_sha256"]==y["events_sha256"])
report={
    "type":"real Forge 2.0.15 four-seat AI-only combat trigger negative fast-path",
    "reference":x,"experiment":y,"real_jvms":2,
    "same_observable_complete_game":same_natural,
    "speed_ratio_only_when_identical_natural_game":
        round(x["wall_seconds"]/y["wall_seconds"],3)
        if same_natural and y["wall_seconds"]>0 else None,
    "limits":[
        "Filtering AI predictions is NOT filtering actual triggers in the Magic rules engine.",
        "No gameplay-strength or global throughput claim from one paired seed.",
        "A divergent event hash makes a time ratio invalid for a speed claim.",
        "Censored games cannot be counted as natural losses or wins.",
        "An observed negative-filter count is not an observed improvement in winrate.",
    ],
}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("FOUR_AI_V24_COMBAT_TRIGGER_AUDIT",json.dumps({
 "pod":a.pod,"rotation":a.rotation,"statuses":[x["status"],y["status"]],
 "winners":[x["winner"],y["winner"]],"pruned":y["exact_negative_combat_trigger_evaluations_pruned"],
 "trace_exists":y["filter_shutdown_summary_seen"],
 "timeouts":[x["ai_timeout_count"],y["ai_timeout_count"]],
 "same_natural_events":same_natural,
 "safe_speed_ratio":report["speed_ratio_only_when_identical_natural_game"]
},ensure_ascii=False),flush=True)
