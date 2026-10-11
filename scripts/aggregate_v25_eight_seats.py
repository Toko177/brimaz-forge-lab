#!/usr/bin/env python3
"""Strict 8-position / 16-real-JVM evidence aggregate for V25 Forge 2.0.15.

Input: 8 per-pair JSON results from REAL four-seat Forge logs, generated
by audit_v24_combat_prune.py, not synthetic game proxies.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics

EXPECTED={(pod,rotation) for pod in ("aristo","artifact") for rotation in range(4)}
GOOD={"complete","clock_censored"}

def combine(root):
    paths=sorted(root.rglob("*_rotation*.json"))
    if len(paths)!=8:
        raise ValueError(f"Exactly 8 four-AI Forge A/B paired audits expected; got {len(paths)}")
    data={}
    for path in paths:
        obj=json.loads(path.read_text(encoding="utf-8"))
        pod,rotation=obj["reference"]["pod"],obj["reference"]["rotation"]
        key=(pod,rotation)
        if key in data or key not in EXPECTED:raise ValueError("Duplicate/unexpected pod rotation: "+str(key))
        if obj["real_jvms"]!=2:
            raise ValueError("Not two real Forge JVM games per matched seat")
        ref,exp=obj["reference"],obj["experiment"]
        for field in ("seats","seed","pod","rotation"):
            if ref[field]!=exp[field]:
                raise ValueError("Mismatched real Forge A/B "+field+" "+str(key))
        if len(ref["seats"])!=4 or len(set(ref["seats"]))!=4 or ref["seats"].count("Brimaz_V3")!=1:
            raise ValueError("Bad 4 AI seats in "+str(key))
        if ref["seats"].index("Brimaz_V3")!=(4-rotation)%4:
            raise ValueError("Seat rotation doesn't match Brimaz Commander position "+str(key))
        if ref["status"] not in GOOD or exp["status"] not in GOOD:
            raise ValueError("Engine fault, unparsed or process timeout in "+str(key))
        if ref["status"]=="complete" and ref["winner"] not in ref["seats"]:
            raise ValueError("Reference game won by a non-player")
        if exp["status"]=="complete" and exp["winner"] not in exp["seats"]:
            raise ValueError("Optimized game won by a non-player")
        if ref["status"]=="clock_censored" and ref["winner"] is not None:
            raise ValueError("Censored reference faked a winner")
        if exp["status"]=="clock_censored" and exp["winner"] is not None:
            raise ValueError("Censored experiment faked a winner")
        if exp["exact_negative_combat_trigger_evaluations_pruned"]<0:
            raise ValueError("Negative pruned count")
        if not exp["filter_shutdown_summary_seen"]:
            raise ValueError("Expected actual Java termination counter absent "+str(key))
        if not ref["events_sha256"] or not exp["events_sha256"]:
            raise ValueError("Missing real logged game event hashes")
        data[key]=obj
    if set(data)!=EXPECTED:
        raise ValueError("Missing 4 seat rotations for either multiplayer Commander pod")
    naturally_equal=[(k,x) for k,x in data.items() if x["same_observable_complete_game"]]
    observed_seconds=[(x["reference"]["wall_seconds"],x["experiment"]["wall_seconds"])
                      for _,x in naturally_equal]
    # Distinct game hashes can have same winners; never claim equal gameplay.
    counts={
       "reference":dict(Counter(x["reference"]["status"] for x in data.values())),
       "optimized":dict(Counter(x["experiment"]["status"] for x in data.values()))
    }
    counts_natural=sum(x["reference"]["status"]==x["experiment"]["status"]=="complete"
                       for x in data.values())
    clean_ratio=[round(a/b,4) for a,b in observed_seconds if b>0]
    return {
      "experiment":"Real Forge 2.0.15 four-AI exact combat-negative prefilter",
      "real_independent_forge_jvm_processes":16,
      "matched_two_policy_games":8,
      "tested_all_four_brimaz_seats_in_each_pod":True,
      "pruned_impossible_ai_trigger_evaluations":
          sum(x["experiment"]["exact_negative_combat_trigger_evaluations_pruned"]
              for x in data.values()),
      "game_status_counts":counts,
      "pairs_with_both_natural_outcomes":counts_natural,
      "natural_pairs_with_identical_observable_actions":len(naturally_equal),
      "natural_pairs_with_divergent_observable_actions":counts_natural-len(naturally_equal),
      "censored_or_nonnatural_pairs":8-counts_natural,
      "descriptive_speedup_on_natural_identical_events_only":{
        "eligible_pairs":len(clean_ratio),
        "median_baseline_over_optimized":round(statistics.median(clean_ratio),4) if clean_ratio else None,
        "min":min(clean_ratio) if clean_ratio else None,
        "max":max(clean_ratio) if clean_ratio else None,
        "eligible_pairs_speedups":clean_ratio,
      },
      "games":[{"pod":k[0],"rotation":k[1],
                "reference_status":x["reference"]["status"],
                "experimental_status":x["experiment"]["status"],
                "same_natural_actions":x["same_observable_complete_game"],
                "reference_winner":x["reference"]["winner"],
                "experiment_winner":x["experiment"]["winner"],
                "impossible_predictions_skipped":x["experiment"]["exact_negative_combat_trigger_evaluations_pruned"],
                "speed_ratio_only_if_identical":x["speed_ratio_only_when_identical_natural_game"]}
               for k,x in sorted(data.items())],
      "limits":[
        "Fixed seeds/rotation are paired observations, not independent tournament samples.",
        "Identical observable event sequences do not certify Oracle rule correctness.",
        "Time comparisons are descriptive: runner variability and setup affect durations.",
        "Censored games are not defeats or wins; never silently omit them.",
        "Counts of skipped computations do not establish strategic playing strength.",
      ]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=combine(args.input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_V25_EIGHT_ROTATIONS",json.dumps({
      "real_jvms":result["real_independent_forge_jvm_processes"],
      "natural_identical":result["natural_pairs_with_identical_observable_actions"],
      "pruned":result["pruned_impossible_ai_trigger_evaluations"],
      "speed_median":result["descriptive_speedup_on_natural_identical_events_only"]["median_baseline_over_optimized"],
      "status_counts":result["game_status_counts"],
    },ensure_ascii=False),flush=True)

if __name__=="__main__":main()
