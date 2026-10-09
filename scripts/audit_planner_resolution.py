#!/usr/bin/env python3
"""Correlate V3 planner decisions with ACTUAL Forge actions by TURN NUMBER.

Forge prints System.out diagnostics in real-time but flushes the in-game event
log only after the simulation. Therefore file line order is NOT chronological.
Do not search adjacent lines for the action; index by Turn: Turn N instead.
"""
import argparse
import collections
import json
import pathlib
import re

p=argparse.ArgumentParser()
p.add_argument("--logs",default="artifacts")
p.add_argument("--out",default="results/audit/planner-resolution.json")
args=p.parse_args()
events=[]
for logfile in sorted(pathlib.Path(args.logs).rglob("game_*.log")):
    lines=logfile.read_text(encoding="utf-8",errors="replace").splitlines()
    turn_events={}
    turn=None
    for line in lines:
        m=re.match(r"^Turn: Turn\s+(\d+)\s+\((.+?)\)",line)
        if m:
            turn=int(m.group(1))
            turn_events[turn]=[line]
        elif turn is not None:
            turn_events[turn].append(line)
    for line in lines:
        if "BRIMAZ_PLANNER:" not in line:continue
        round_m=re.search(r"\bturn=(\d+)\b",line)
        outlet_m=re.search(r"\boutlet=(.+?)\s*$",line)
        active_m=re.search(r"\bactive=(.+?)\s+outlet=",line)
        if not (round_m and outlet_m and active_m):
            events.append({"file":str(logfile),"proposal":line,"status":"unparseable_proposal"})
            continue
        turn_no=int(round_m.group(1))
        outlet=outlet_m.group(1).strip()
        actor=active_m.group(1).strip()
        turn_log=turn_events.get(turn_no,[])
        activations=[
            item for item in turn_log
            if item.startswith("Add To Stack: ") and
               item.startswith("Add To Stack: "+actor+" activated ") and
               outlet in item
        ]
        phase=""
        triggered=0
        for event in turn_log:
            if event.startswith("Phase: "):
                phase=event.rsplit("'s ",1)[-1]
            if (phase=="End step" and "Add To Stack:" in event and
                    "triggered Brimaz, Blight of Oreskos" in event):
                triggered+=1
        events.append({
            "file":str(logfile),"outlet":outlet,"turn":turn_no,
            "actor":actor,"proposal":line,
            "turn_found":bool(turn_log),
            "activation_count":len(activations),
            "activation_observed":bool(activations),
            "end_step_trigger_observed":triggered>0,
            "brimaz_end_step_triggers":triggered,
            "note":"One turn's end-step trigger can have another death cause; observed association does not establish causation."
        })
agg={
    "proposals":len(events),
    "games_with_proposal":len({x["file"] for x in events}),
    "turn_found":sum(bool(x.get("turn_found")) for x in events),
    "activation_observed":sum(bool(x.get("activation_observed")) for x in events),
    "end_step_trigger_observed":sum(bool(x.get("end_step_trigger_observed")) for x in events),
    "proposals_by_outlet":dict(collections.Counter(x.get("outlet","unknown") for x in events)),
}
dest=pathlib.Path(args.out)
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps({"summary":agg,"events":events},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PLANNER_RESOLUTION_AUDIT",json.dumps(agg,ensure_ascii=False),flush=True)
for e in events:
    print("PLANNER_RESOLUTION_EVENT",json.dumps(e,ensure_ascii=False),flush=True)
