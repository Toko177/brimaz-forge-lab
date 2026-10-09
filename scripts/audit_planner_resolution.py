#!/usr/bin/env python3
"""Correlate custom Brimaz AI proposals with actions and subsequent end-step triggers.

This is observational replay from ACTUAL Forge logs. Does not claim causal
attribution without a counterfactual game-state transition.
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
    for i,line in enumerate(lines):
        if "BRIMAZ_PLANNER:" not in line:
            continue
        outlet=re.search(r"outlet=(.+?)(?:\s*$)",line)
        if outlet: name=outlet.group(1).strip()
        else:
            older=re.search(r"via (.+?) / active turn",line)
            name=older.group(1).strip() if older else "unknown"
        # One priority window is bounded by the start of the next turn.
        next_turn=next((j for j in range(i+1,len(lines)) if lines[j].startswith("Turn: Turn ")),len(lines))
        window=lines[i+1:next_turn]
        activation=[z for z in window if "Add To Stack:" in z and "activated " in z and name in z]
        death=[z for z in window if "sacrificed" in z.lower() and "phyrexian" in z.lower()]
        # This records a trigger on the stack, not proof of its resolution.
        end_phase=False
        triggered=0
        for text in window:
            if text.startswith("Phase: "):
                end_phase=text.rsplit("'s ",1)[-1]=="End step"
            if end_phase and "Add To Stack:" in text and "triggered Brimaz, Blight of Oreskos" in text:
                triggered+=1
        events.append({
            "file":str(logfile),"outlet":name,
            "proposal":line,"activation_lines":len(activation),
            "observed_phyrexian_sacrifice_text_lines":len(death),
            "brimaz_end_step_triggers_before_next_turn":triggered,
            "activation_observed":bool(activation),
            "reached_endstep_with_trigger":triggered>0,
            "caveat":"Observed trigger might result from other qualifying death; cannot prove this proposal caused it."
        })
agg={
    "proposals":len(events),
    "games_with_proposal":len({x["file"] for x in events}),
    "activation_observed":sum(x["activation_observed"] for x in events),
    "end_step_trigger_observed":sum(x["reached_endstep_with_trigger"] for x in events),
    "proposals_by_outlet":dict(collections.Counter(x["outlet"] for x in events)),
}
dest=pathlib.Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps({"summary":agg,"events":events},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PLANNER_RESOLUTION_AUDIT",json.dumps(agg,ensure_ascii=False),flush=True)
