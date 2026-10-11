#!/usr/bin/env python3
"""Compare genuine four-seat Forge games with/without finite slow-card cooldown.

A faster clock-censored game does not count as a winner or tactical improvement.
A reduced count of AI timeouts is an observed responsiveness result only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

p=argparse.ArgumentParser()
p.add_argument("--pod",choices=["aristo","artifact"],required=True)
p.add_argument("--rotation",type=int,required=True)
p.add_argument("--out",type=Path,required=True)
a=p.parse_args()
root=Path("results/batch")/a.pod
stats={}
for name,tag in (("control","V23-cooldown-control"),("cooldown","V23-cooldown-enabled")):
    manifest=json.loads((root/tag/"games.json").read_text(encoding="utf-8"))
    if len(manifest)!=1: raise ValueError("Require one genuine four-player Forge match")
    g=manifest[0]
    raw=(root/tag/Path(g["log"]).name).read_text(encoding="utf-8",errors="replace")
    details=re.findall(
      r"FOUR_AI_TIMEOUT_COOLDOWN_V23 player=(.*?) card=(.*?) cardId=(\d+) untilGlobalTurn=(\d+) strikeCount=(\d+)",raw)
    timeouts=re.findall(r"AI_EVAL_TIMEOUT_V10: player=(.*?) globalTurn=(\d+) phase=(\S+)",raw)
    score=[x for x in raw.splitlines()
           if x.startswith(("Turn: ","Phase: ","Add To Stack: ","Combat: ","Game Outcome: "))
           and "Match Duration" not in x]
    stats[name]={
        "seats":g["seats"],"seed":g["seed"],"pod":g["pod"],
        "rotation":g["rotation"],"status":g["status"],"winner":g["winner_deck"],
        "brimaz_win":g["brimaz_win"],"wall_seconds":g["wall_seconds"],
        "ai_timeouts":len(timeouts),
        "timeout_by_player":{name:sum(x[0]==name for x in timeouts) for name in sorted(set(x[0] for x in timeouts))},
        "cards_temporarily_deprioritized":[{"player":d[0],"card":d[1],
           "card_id":int(d[2]),"until_global_turn":int(d[3]),"strikes":int(d[4])} for d in details],
        "observed_event_sha256":hashlib.sha256("\n".join(score).encode("utf-8")).hexdigest(),
    }
b,e=stats["control"],stats["cooldown"]
for k in ("seats","seed","pod","rotation"):
    if b[k]!=e[k]:raise ValueError("Unmatched game "+k)
if b["rotation"]!=a.rotation:raise ValueError("Unexpected rotation")
natural=b["status"]==e["status"]=="complete"
same=natural and b["observed_event_sha256"]==e["observed_event_sha256"]
report={
  "pilot":"Shared AI evaluator timeout quarantine 4/8/12/16 global turns, main-phase actions only",
  "actual_forge_jvms":2,"pod":a.pod,"rotation":a.rotation,
  "baseline":b,"experimental":e,
  "naturally_ended_in_both":natural,"same_natural_observable_game":same,
  "observed_ai_timeout_delta":e["ai_timeouts"]-b["ai_timeouts"],
  "speed_ratio_only_when_same_events":round(b["wall_seconds"]/e["wall_seconds"],3)
        if same and e["wall_seconds"]>0 else None,
  "limitations":[
   "This experimental finite cooldown can skip strategically important cards and requires side-effect regression tests.",
   "It never applies to stack response candidate evaluation (skipCounter=false).",
   "A reduced timeout count or censored game is not a certified Commander win.",
   "Single-seed paired games have stochastic variability; no global speed claim.",
  ]
}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("FOUR_AI_V23_COOLDOWN_AUDIT",json.dumps({
    "pod":a.pod,"rotation":a.rotation,"statuses":[b["status"],e["status"]],
    "time_outs":[b["ai_timeouts"],e["ai_timeouts"]],
    "quarantine_events":len(e["cards_temporarily_deprioritized"]),
    "same_natural_events":same,"winners":[b["winner"],e["winner"]]
},ensure_ascii=False),flush=True)
