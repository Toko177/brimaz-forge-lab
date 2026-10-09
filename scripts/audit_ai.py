#!/usr/bin/env python3
"""Evidence-based quality audit of actual 4-player Forge Commander transcripts.
Never equate 'no trigger' with 'missed legal play' without a reconstructed game state.
"""
import argparse
import collections
import json
import pathlib
import re

p=argparse.ArgumentParser()
p.add_argument("--logs",default="results/batch/aristo")
p.add_argument("--out",default="results/audit/ai_audit.json")
args=p.parse_args()
files=sorted(pathlib.Path(args.logs).glob("game_*.log"))
if not files: p.error("No Forge log files available")
engines=("Ashnod's Altar","Phyrexian Altar","Spawning Pit","Krark-Clan Ironworks",
         "Yawgmoth, Thran Physician","Arcbound Ravager","Bartolomé del Presidio",
         "Throne of Geth","Phyrexian Tower","High Market")
stats=[]
for path in files:
    raw=path.read_text(encoding="utf-8",errors="replace")
    lines=raw.splitlines()
    phase=""
    turn=""
    active_player=""
    current_endstep_active=""
    triggered_in_endstep=0
    triggered_during_opponent_endstep=0
    sacrificed=collections.Counter()
    activations=collections.Counter()
    incubated=collections.Counter()
    cast=collections.Counter()
    phases=collections.Counter()
    inactive_end_step_actions=0
    warnings=[]
    for line in lines:
        t=re.match(r"Turn: Turn\s+\d+\s+\((Ai\(\d+\)-.+?)\)$",line)
        if t:
            active_player=t.group(1)
            turn=t.group(0)
        ph=re.match(r"Phase:\s+(Ai\(\d+\)-.+?)'s\s+(.+)$",line)
        if ph:
            phase=ph.group(2)
            current_endstep_active=ph.group(1) if phase == "End step" else ""
            phases[phase]+=1
        caster=re.search(r"Add To Stack: (Ai\(\d+\)-.+?) cast (.+)$",line)
        if caster:cast[caster.group(1)+" | "+caster.group(2)]+=1
        act=re.search(r"Add To Stack: (Ai\(\d+\)-.+?) activated (.+)$",line)
        if act:
            player,card=act.groups()
            activations[player+" | "+card]+=1
            if "Brimaz" in player:
                for engine in engines:
                    if engine in card: sacrificed[engine]+=1
                if phase == "End step" and current_endstep_active and "Brimaz" not in current_endstep_active:
                    inactive_end_step_actions+=1
        if "Add To Stack:" in line and "triggered Brimaz, Blight of Oreskos" in line and phase == "End step":
            triggered_in_endstep+=1
            if current_endstep_active and "Brimaz" not in current_endstep_active:triggered_during_opponent_endstep+=1
        if "No AI assigned for API:" in line: warnings.append(line)
        if "activated Incubator Token" in line:
            inc=re.search(r"Add To Stack: (Ai\(\d+\)-.+?) activated Incubator Token",line)
            if inc: incubated[inc.group(1)]+=1
    logs={
      "file":str(path),
      "turn_lines":len(re.findall(r"^Turn: Turn ",raw,re.M)),
      "end_steps":phases["End step"],
      "brimaz_end_step_triggers":triggered_in_endstep,
      "brimaz_opponent_end_step_triggers":triggered_during_opponent_endstep,
      "brimaz_sacrifice_engine_activations":dict(sacrificed),
      "brimaz_nonactive_endstep_activations":inactive_end_step_actions,
      "all_incubator_transforms":dict(incubated),
      "brimaz_casts":sum(n for x,n in cast.items() if x.endswith("cast Brimaz, Blight of Oreskos") or " | Brimaz, Blight of Oreskos" in x),
      "all_brimaz_trigger_lines":raw.count("triggered Brimaz, Blight of Oreskos"),
      "unique_ai_api_warnings":sorted(set(warnings)),
      "quality_flags":[
        "Incubate AI API handler missing" if "No AI assigned for API: Incubate" in raw else "",
        "No observed Brimaz sacrifice-engine activations; availability unknown" if sum(sacrificed.values())==0 else "",
        "No observed Brimaz end-step proliferate triggers; death preconditions unknown" if triggered_in_endstep==0 else "",
      ]
    }
    logs["quality_flags"]=[x for x in logs["quality_flags"] if x]
    stats.append(logs)
report={
    "transcripts":stats,
    "aggregate":{
        "games":len(stats),
        "brimaz_end_step_triggers":sum(x["brimaz_end_step_triggers"] for x in stats),
        "brimaz_opponent_end_step_triggers":sum(x["brimaz_opponent_end_step_triggers"] for x in stats),
        "sacrifice_engine_activations":sum(sum(x["brimaz_sacrifice_engine_activations"].values()) for x in stats),
        "brimaz_opponent_end_step_activations":sum(x["brimaz_nonactive_endstep_activations"] for x in stats),
        "incubator_transforms":sum(sum(x["all_incubator_transforms"].values()) for x in stats),
        "ai_api_missing_incubate_games":sum(bool(x["unique_ai_api_warnings"]) for x in stats)
    },
    "interpretation_limits":[
      "An absent activation is not proof of an available missed activation.",
      "There is no full state reconstruction, hidden hand analysis, or policy optimality benchmark.",
      "Simple text-matching may miss alternative log renderings.",
      "Follow-up: instrument battlefield availability and compare AI profiles on matched random seeds."
    ]
}
out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("AI_AUDIT_SUMMARY",json.dumps(report["aggregate"],ensure_ascii=False),flush=True)
for row in stats:
    print("AI_AUDIT_GAME",json.dumps({k:v for k,v in row.items() if k not in ("unique_ai_api_warnings",)},ensure_ascii=False),flush=True)
