#!/usr/bin/env python3
"""Locate the FIRST observable Forge gameplay divergence of genuinely paired games.

Same seed is NOT guaranteed deterministic under concurrent AI evaluation.
No speculation about hidden opponent cards or Oracle/legal missed plays.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

GAME_PREFIXES=("Turn: ","Phase: ","Add To Stack: ","Combat: ","Game Outcome: ",
               "Damage: ","Life: ","Zone Change: ","Land: ","Counter: ","Poison: ")

def events_and_timeouts(raw):
    moves=[];before=[];timeouts=0
    for line in raw.splitlines():
        if line.startswith("AI_EVAL_TIMEOUT_V10:"):
            timeouts+=1
        if line.startswith(GAME_PREFIXES) and "Match Duration" not in line:
            before.append(timeouts)
            moves.append(line)
    return moves,before,timeouts

def inspect(reference,experiment,matched):
    a,ca,ta=events_and_timeouts(reference)
    b,cb,tb=events_and_timeouts(experiment)
    if not a or not b:
        raise ValueError("Missing actual Forge game events")
    count=min(len(a),len(b))
    first=next((i for i in range(count) if a[i]!=b[i]),count)
    same=first==len(a)==len(b)
    return {
      "pod":matched["pod"],"rotation":matched["rotation"],"seed":matched["seed"],
      "reference_status":matched["reference_status"],
      "experimental_status":matched["experimental_status"],
      "reference_winner":matched["reference_winner"],
      "experimental_winner":matched["experimental_winner"],
      "entire_observable_event_sequences_equal":same,
      "reference_event_count":len(a),"experimental_event_count":len(b),
      "first_mismatch_index":None if same else first,
      "reference_at_mismatch":None if same or first>=len(a) else a[first],
      "experimental_at_mismatch":None if same or first>=len(b) else b[first],
      "reference_timeouts_before_mismatch":ca[first] if first<len(a) else ta,
      "experimental_timeouts_before_mismatch":cb[first] if first<len(b) else tb,
      "reference_total_timeouts":ta,"experimental_total_timeouts":tb,
      "reference_preceding_events":a[max(0,first-3):first] if not same else [],
      "experimental_preceding_events":b[max(0,first-3):first] if not same else [],
      "reference_following_events":a[first:first+4] if not same else [],
      "experimental_following_events":b[first:first+4] if not same else [],
      "interpretation":"The earliest log divergence is an observation; any causal link to the optimized method remains unproved.",
    }

def analyze(root):
    grouped={}
    for p in root.rglob("games.json"):
        game=json.loads(p.read_text(encoding="utf-8"))
        if len(game)!=1:raise ValueError("Expected one real Forge game per job")
        g=game[0]
        if len(g["seats"])!=4 or g["seats"].count("Brimaz_V3")!=1:
            raise ValueError("Invalid four-player Commander manifest")
        key=(g["pod"],g["rotation"])
        typ=g["policy"]
        if typ not in ("stock-combat-triggers","exact-negative-triggers"):
            raise ValueError("Unknown experimental policy in four-AI manifest: "+typ)
        record=grouped.setdefault(key,{})
        if typ in record:raise ValueError("Duplicate four-AI game "+str(key)+" "+typ)
        logfile=p.parent/Path(g["log"]).name
        if not logfile.is_file():raise ValueError("Missing true Forge raw game log "+str(logfile))
        record[typ]=(g,logfile.read_text(encoding="utf-8",errors="replace"))
    expected={(p,r) for p in ("aristo","artifact") for r in range(4)}
    if set(grouped)!=expected:raise ValueError("Missing one of eight real four-seat pair groups")
    rows=[]
    for (pod,rot),pair in sorted(grouped.items()):
        if set(pair)!={"stock-combat-triggers","exact-negative-triggers"}:
            raise ValueError("Reference/optimized four-AI games missing "+str((pod,rot)))
        ref,araw=pair["stock-combat-triggers"]
        opt,braw=pair["exact-negative-triggers"]
        for k in ("pod","rotation","seed","seats","repeat"):
            if ref[k]!=opt[k]:raise ValueError("Different paired seed/deck "+k)
        matched={"pod":pod,"rotation":rot,"seed":ref["seed"],
                 "reference_status":ref["status"],"experimental_status":opt["status"],
                 "reference_winner":ref["winner_deck"],"experimental_winner":opt["winner_deck"]}
        rows.append(inspect(araw,braw,matched))
    return {
      "method":"First observable difference in exact logged Forge game event sequences",
      "real_forge_four_ai_games_compared":16,
      "matched_pod_rotation_pairs":len(rows),
      "identical_event_pairs":sum(r["entire_observable_event_sequences_equal"] for r in rows),
      "different_natural_winner_pairs":sum(r["reference_status"]==r["experimental_status"]=="complete" and
                                         r["reference_winner"]!=r["experimental_winner"] for r in rows),
      "differences":rows,
      "limits":[
          "Identical RNG seed does not guarantee identical results with Forge's timed/multithreaded AI.",
          "A first divergent event or preceding timeout cannot by itself prove cause.",
          "This compares public Forge log events, not every internal Oracle rule state.",
          "A difference in winner after a timeout is not necessarily strategic improvement or degradation.",
      ],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    out=analyze(args.input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_FIRST_DIVERGENCE",json.dumps({
       "true_games":16,"identical_pairs":out["identical_event_pairs"],
       "different_winner_pairs":out["different_natural_winner_pairs"],
       "first_mismatches":[{"pod":r["pod"],"rotation":r["rotation"],
                            "first_event_index":r["first_mismatch_index"],
                            "timeouts_before":[r["reference_timeouts_before_mismatch"],
                                               r["experimental_timeouts_before_mismatch"]]}
                             for r in out["differences"] if not r["entire_observable_event_sequences_equal"]]
    },ensure_ascii=False),flush=True)
if __name__=="__main__":main()
