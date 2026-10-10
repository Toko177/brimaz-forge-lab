#!/usr/bin/env python3
"""Compare real four-AI EDH counterspell decisions with optional V21 protection.

Forcing a previously rejected counterspell is evidence of changed tactical
logic, NOT proof that countering was legal/effective unless Forge casts it.
"""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--pod",choices=["aristo","artifact"],required=True)
p.add_argument("--rotation",type=int,required=True)
p.add_argument("--out",type=Path,required=True)
a=p.parse_args()
root=Path("results/batch")/a.pod
out={}
for label,tag in (("reference","critical-counter-control"),("critical","critical-counter-enabled")):
    rows=json.loads((root/tag/"games.json").read_text(encoding="utf-8"))
    if len(rows)!=1:raise ValueError("Expected one actual four-player Forge game")
    row=rows[0]
    raw=(root/tag/Path(row["log"]).name).read_text(encoding="utf-8",errors="replace")
    forced=re.findall(r"FOUR_AI_CRITICAL_COUNTER accepted player=(.*?) hostileSpell=(.*?) protectedCommander=(.*)",raw)
    events=[x for x in raw.splitlines() if x.startswith(("Turn: ","Phase: ","Combat: ","Add To Stack: ","Game Outcome: "))
            and "Match Duration" not in x]
    out[label]={
        "seats":row["seats"],"pod":row["pod"],"seed":row["seed"],"rotation":row["rotation"],
        "status":row["status"],"winner":row["winner_deck"],"brimaz_win":row["brimaz_win"],
        "wall_seconds":row["wall_seconds"],
        "actual_critical_counter_acceptances":[{"controller":x[0],"hostile":x[1],"protected":x[2]} for x in forced],
        "observed_event_sha256":hashlib.sha256("\n".join(events).encode()).hexdigest(),
        "events":len(events),
    }
x,y=out["reference"],out["critical"]
for k in ("seats","pod","seed","rotation"):
    if x[k]!=y[k]:raise ValueError("Mismatched Forge experiment "+k)
if x["rotation"]!=a.rotation:raise ValueError("Wrong seat rotation")
natural=x["status"]==y["status"]=="complete"
equal=natural and x["observed_event_sha256"]==y["observed_event_sha256"]
report={
    "experiment":"Four-AI public targeted commander removal counter safety",
    "actual_forge_processes":2,"pod":a.pod,"rotation":a.rotation,
    "control":x,"critical_counter":y,"identical_natural_observable_events":equal,
    "speed_ratio_only_if_same_natural_game":round(x["wall_seconds"]/y["wall_seconds"],3) if equal and y["wall_seconds"]>0 else None,
    "limits":["Any accepted counter opportunity still needs proof of a cast on the stack.",
              "Results from two games do not prove winrate or expert-level response timing.",
              "No hidden hands, speculative opponent answers or bypassed Forge targeting/mana costs."],
}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("FOUR_AI_CRITICAL_COUNTER_AUDIT",json.dumps({
    "pod":a.pod,"rotation":a.rotation,"both_natural":natural,"same_events":equal,
    "actual_critical_counter_acceptances":len(y["actual_critical_counter_acceptances"]),
    "winners":[x["winner"],y["winner"]]
},ensure_ascii=False),flush=True)
