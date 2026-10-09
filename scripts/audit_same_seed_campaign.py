#!/usr/bin/env python3
"""Analyze repeatability of TWO independent real Forge campaign runs with same seeds.

Pairs are technical replicates, not distinct IID observations for winrate CI.
Differences can arise from timeouts, RNG consumption, concurrency, or other
nondeterminism; never conclude a specific cause from correlated observations.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from audit_matched_replay import analyze as compare_transcripts


def key(g):
    return (g["pod"],g["rotation"],g["repeat"],g["seed"])


def read_real_games(root):
    found={}
    for manifest in sorted(Path(root).rglob("games.json")):
        for g in json.loads(manifest.read_text(encoding="utf-8")):
            k=key(g)
            if k in found:
                raise ValueError(f"Duplicate game from artifact shards: {k}")
            path=manifest.parent/Path(g["log"]).name
            if not path.is_file():
                raise FileNotFoundError(path)
            found[k]=(g,path.read_text(encoding="utf-8",errors="replace"))
    return found


def compare_campaigns(a,b,expected=32):
    if expected<1 or len(a)!=expected or len(b)!=expected:
        raise ValueError(f"Need all {expected} scheduled games per campaign")
    if set(a)!=set(b):
        raise ValueError("Two GitHub campaigns have different pods/rotations/seeds")
    games=[]
    for k in sorted(a):
        g1,raw1=a[k];g2,raw2=b[k]
        for field in ("policy","clock_seconds","seed","rotation","pod","repeat","seats","profiles","brimaz_seat"):
            if g1.get(field)!=g2.get(field):
                raise ValueError(f"Not the same {field} for seed {k}")
        r=compare_transcripts(g1,raw1,g2,raw2)
        games.append({
            "pod":k[0],"rotation":k[1],"repeat":k[2],"seed":k[3],
            "reference_status":g1["status"],"replay_status":g2["status"],
            "reference_winner":g1.get("winner_deck"),
            "replay_winner":g2.get("winner_deck"),
            "winner_agreement_if_both_complete":r["outcome_reproduced"],
            "same_event_sequence":r["event_sequence_identical"],
            "first_diff_reference":r["first_divergence_reference"],
            "first_diff_replay":r["first_divergence_replay"],
            "timeout_counts":r["raw_timeout_exception_occurrences"],
            "log_sha256":[r["reference_log_sha256"],r["replay_log_sha256"]],
        })
    both=[g for g in games if g["reference_status"]=="complete" and g["replay_status"]=="complete"]
    return {
        "summary":{
            "seed_pairs":len(games),
            "both_natural":len(both),
            "one_or_both_censored_or_invalid":len(games)-len(both),
            "both_natural_same_winner":sum(g["winner_agreement_if_both_complete"] for g in both),
            "both_natural_different_winner":sum(not g["winner_agreement_if_both_complete"] for g in both),
            "identical_event_sequences":sum(g["same_event_sequence"] for g in games),
            "changed_event_sequences":sum(not g["same_event_sequence"] for g in games),
            "by_pod":{p:{"paired":sum(x["pod"]==p for x in games),
                         "both_natural":sum(x["pod"]==p for x in both),
                         "winners_disagree":sum(x["pod"]==p and not x["winner_agreement_if_both_complete"] for x in both)}
                      for p in ("aristo","artifact")},
            "not_independent_samples":"These are the SAME 32 RNG seeds rerun, not 64 independent draws. Do not pool for a 64-game Wilson CI.",
            "no_causality_claim":"Identical seeds need not yield identical actions; do not attribute differences exclusively to CPU timeouts without controlled evidence."
        }, "pairs":games}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--first",required=True,type=Path)
    parser.add_argument("--second",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--expected",type=int,default=32)
    args=parser.parse_args()
    d=compare_campaigns(read_real_games(args.first),read_real_games(args.second),expected=args.expected)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FORGE_SAME_SEED_32_GAME_REPLICATION_AUDIT",json.dumps(d["summary"],ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
