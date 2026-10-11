#!/usr/bin/env python3
"""Strict release gate for two authentic paired Forge 2.0.15 four-AI campaigns.

Input MUST be the output of compare_local_four_ai_campaigns.compare, whose
loader reads all 4-seat raw Forge game transcripts. This gate never creates
games or winners and is explicitly separate from Magic Oracle certification
or competitive human-like AI quality. Censured games fail this narrow pilot.
"""
import argparse
from collections import Counter
import json
from pathlib import Path


def audit(data, expected_pairs=4, require_identical=True, require_natural=True):
    if data.get("type") != "Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B":
        raise ValueError("Input is not the genuine Forge four-AI paired comparison schema")
    if not isinstance(expected_pairs, int) or expected_pairs < 1:
        raise ValueError("Expected real process pairs must be positive")
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != expected_pairs:
        raise ValueError("Missing/extra real game pairs: "
                         + str(len(pairs) if isinstance(pairs, list) else "invalid"))
    if data.get("real_process_pairs") != expected_pairs or \
       data.get("real_forge_jvm_processes") != expected_pairs * 2:
        raise ValueError("Real 4-AI JVM process count inconsistent with pairs")
    original = data.get("reference_provenance", {})
    experiment = data.get("experiment_provenance", {})
    required = ("canonical_seven_deck_sha256", "original_forge_sha256",
                "profile_applied_identically_to_all_four_seats", "clock_seconds",
                "base_seed")
    for key in required:
        if not original.get(key) or original[key] != experiment.get(key):
            raise ValueError("Original/candidate provenance mismatch: " + key)
    if len(original["canonical_seven_deck_sha256"]) != 7:
        raise ValueError("Exactly seven original deck SHA256 values required")
    seen=set()
    statuses=Counter()
    identical=0
    natural=0
    winners_changed=0
    for pair in pairs:
        key=(pair.get("pod"),pair.get("rotation"),pair.get("repeat"),pair.get("seed"))
        if key in seen:
            raise ValueError("Repeated same Forge match key")
        seen.add(key)
        if pair.get("rotation") not in (0,1,2,3):
            raise ValueError("Four-seat rotation outside 0–3")
        a,b=pair["reference"],pair["experiment"]
        for k in ("seats","clock_seconds","profiles"):
            if a.get(k)!=b.get(k):
                raise ValueError("Mispaired Forge game: "+k)
        if len(a["seats"])!=4 or len(set(a["seats"]))!=4 or \
           a["seats"].count("Brimaz_V3")!=1:
            raise ValueError("This was not a four-deck Commander game")
        if a.get("status")=="complete" and b.get("status")=="complete":
            natural+=1
        for arm,rec in (("reference",a),("experiment",b)):
            statuses[rec.get("status")]+=1
            if rec.get("status") != "complete" and rec.get("winner") is not None:
                raise ValueError("A censored Forge game was given a winner")
            if rec.get("status") == "complete" and rec.get("winner") not in rec["seats"]:
                raise ValueError("Game's natural winner not seated in genuine four AI match")
            if not isinstance(rec.get("raw_sha256"),str) or len(rec["raw_sha256"])!=64:
                raise ValueError("Missing actual log SHA256 for "+arm)
            if not isinstance(rec.get("event_sha256"),str) or len(rec["event_sha256"])!=64:
                raise ValueError("Missing actual action transcript SHA256 for "+arm)
            if rec.get("event_count",0)<1:
                raise ValueError("Zero original Forge action observations")
        if pair.get("both_natural") != (a["status"] == b["status"] == "complete"):
            raise ValueError("Pair natural-finish bit contradicted real game statuses")
        is_same=(a["status"]==b["status"]=="complete" and
                 a["event_sha256"]==b["event_sha256"])
        if pair.get("same_observable_events_if_natural") != is_same:
            raise ValueError("Forged action-equivalence flag")
        if is_same:
            identical+=1
        if a["status"]==b["status"]=="complete" and a["winner"]!=b["winner"]:
            winners_changed+=1
    if data.get("both_natural_pairs")!=natural or \
       data.get("natural_pairs_with_identical_observable_actions")!=identical or \
       data.get("natural_pairs_with_different_winner")!=winners_changed:
        raise ValueError("Aggregates contradict individual original Forge observations")
    if data.get("pairs_with_any_censor_or_fault")!=expected_pairs-natural:
        raise ValueError("Reported censor count contradicts real statuses")
    problems=[]
    if require_natural and natural != expected_pairs:
        problems.append(f"Only {natural}/{expected_pairs} pairs naturally ended")
    if require_identical and identical != expected_pairs:
        problems.append(f"Only {identical}/{expected_pairs} pairs same observable actions")
    return {
        "type": "strict evidence gate for authentic four-seat Forge outcomes",
        "real_forge_jvm_processes": expected_pairs*2,
        "real_paired_games":expected_pairs,
        "fully_natural_pairs":natural,
        "identical_observable_action_pairs":identical,
        "status_counts":dict(statuses),
        "changed_winner_pairs":winners_changed,
        "functional_release_gate":"PASS" if not problems else "BLOCKED",
        "blocking_issues":problems,
        "certified_magic_oracle_rules":False,
        "human_like_ai_demonstrated":False,
        "statistically_validated_winrate":False,
        "scope":"Checks logs and provenance reported by the authentic raw-Forge campaign comparator, not all Magic rules.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path)
    p.add_argument("--expected-pairs",type=int,default=4)
    p.add_argument("--allow-censored",action="store_true")
    p.add_argument("--allow-different-actions",action="store_true")
    args=p.parse_args()
    data=json.loads(args.input.read_text(encoding="utf-8"))
    result=audit(data,args.expected_pairs,
                 require_identical=not args.allow_different_actions,
                 require_natural=not args.allow_censored)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_STRICT_REAL_SIMULATOR_GATE",
          json.dumps(result,ensure_ascii=False),flush=True)
    if result["functional_release_gate"] != "PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
