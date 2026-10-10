#!/usr/bin/env python3
"""Actual Forge 4-AI A/B audit: Brimaz legal engine alternative shadow only.

This diagnoses possible strategic competition at the SAME CURRENT state;
it does NOT change policy or assert the alternate would be optimal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

PATTERN=re.compile(
    r"^FOUR_AI_COMMANDER_TEMPO_SHADOW player=(Ai\([1-4]\)-.*?) "
    r"globalTurn=(\d+) life=(-?\d+) greatestVisibleEnemyPower=(-?\d+) "
    r"legalEngineAlternatives=(\d+) engineNames=(\S+) selected=Brimaz$",re.M)
EVENTS=("Turn: ","Phase: ","Add To Stack: ","Combat: ","Game Outcome: ",
        "Damage: ","Life: ","Zone Change: ","Land: ","Poison: ","Counter: ")

def inspect(raw):
    hits=[]
    for m in PATTERN.finditer(raw):
        hits.append({
           "four_ai_player":m.group(1),"global_turn":int(m.group(2)),
           "self_life":int(m.group(3)),"greatest_visible_enemy_power":int(m.group(4)),
           "legally_payable_engine_option_count":int(m.group(5)),
           "legal_engine_names":m.group(6).split(",") if m.group(6)!="none" else [],
           "actually_chosen_spell":"Brimaz, Blight of Oreskos",
           "evidence":"Forge spell timing, canPlay and canPayCost checked for each proposed engine alternative",
        })
    return hits

def audit(root,pod,rotation):
    matches={}
    for name,tag in (("reference","V29-tactic-control"),
                     ("shadow","V29-tactic-shadow")):
        manifest=root/pod/tag/"games.json"
        r=json.loads(manifest.read_text(encoding="utf-8"))
        if len(r)!=1:raise ValueError("One genuine 4-AI match per policy expected")
        game=r[0]
        raw=(manifest.parent/Path(game["log"]).name).read_text(encoding="utf-8",errors="replace")
        if not re.search(r"^Ai\(1\)-.+? vs Ai\(2\)-.+? vs Ai\(3\)-.+? vs Ai\(4\)-.+? - one game of Commander seed",raw,re.M):
            raise ValueError("Missing genuine four-AI Commander match declaration")
        events=[s for s in raw.splitlines() if s.startswith(EVENTS)]
        if not events:raise ValueError("Missing actual Forge gameplay events")
        matches[name]={
           "pod":game["pod"],"rotation":game["rotation"],
           "seed":game["seed"],"seats":game["seats"],
           "status":game["status"],"winner":game["winner_deck"],
           "gameplay_sha256":hashlib.sha256("\n".join(events).encode()).hexdigest(),
           "shadow":inspect(raw),
        }
    a,b=matches["reference"],matches["shadow"]
    for key in ("pod","rotation","seed","seats"):
        if a[key]!=b[key]:raise ValueError("Unpaired Commander policy comparisons: "+key)
    if a["rotation"]!=rotation or a["pod"]!=pod:
        raise ValueError("Unexpected pod/rotation")
    if len(a["seats"])!=4 or a["seats"].count("Brimaz_V3")!=1:
        raise ValueError("Invalid four distinct seats")
    for obj in (a,b):
        if obj["status"]!="complete" and obj["winner"] is not None:
            raise ValueError("Censored Forge match has fake winner")
    return {
       "pod":pod,"rotation":rotation,"real_forge_jvms":2,
       "both_naturally_complete":a["status"]==b["status"]=="complete",
       "naturally_identical_events":a["status"]==b["status"]=="complete" and a["gameplay_sha256"]==b["gameplay_sha256"],
       "statuses":[a["status"],b["status"]],"winners":[a["winner"],b["winner"]],
       "actual_commander_choice_audit_count":len(b["shadow"]),
       "commander_choices_with_legal_mana_or_outlet_alternatives":
           sum(x["legally_payable_engine_option_count"]>0 for x in b["shadow"]),
       "state_matched_candidate_details":b["shadow"],
       "limitations":[
          "The shadow instruments only the three whitelisted mana/outlet spells in the existing Brimaz planner.",
          "Both commander and an enabler may be individually payable without both being simultaneously payable.",
          "A legal alternative is NOT evidence it was optimal or that another AI was legally allowed to choose it.",
          "Shadow logs do not replace true Forge stack legality or represent a legal game branch rollout.",
          "Same Forge seed may produce a different game after AI timeouts or schedule variation.",
       ],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--pod",choices=["aristo","artifact"],required=True)
    p.add_argument("--rotation",type=int,required=True)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    o=audit(args.input,args.pod,args.rotation)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_V29_REAL_COMMANDER_TEMPO_SHADOW",json.dumps({
        "pod":args.pod,"rotation":args.rotation,"natural":o["both_naturally_complete"],
        "identical_events":o["naturally_identical_events"],
        "audited_commander_casts":o["actual_commander_choice_audit_count"],
        "commander_over_legal_engine_choices":o["commander_choices_with_legal_mana_or_outlet_alternatives"],
        "winners":o["winners"]
    },ensure_ascii=False),flush=True)
if __name__=="__main__":main()
