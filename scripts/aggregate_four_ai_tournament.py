#!/usr/bin/env python3
"""Aggregate genuine, separately executed Forge EDH 4-AI match manifests.

Disclose denominator, censoring, deck-pool bias, rotations, SHA provenance
and 95% Wilson descriptive intervals. NOT independent card legality, natural
ending or Commander Oracle rules certification. Reject missing/duplicate logs.
"""
import argparse
from collections import Counter,defaultdict
import hashlib,json,math
from pathlib import Path

def wilson(success,n,z=1.959963984540054):
    if n<=0:return None
    phat=success/n
    denom=1+z*z/n
    center=(phat+z*z/(2*n))/denom
    arm=z*math.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/denom
    return [round(max(0.,center-arm),5),round(min(1.,center+arm),5)]

def aggregate(root,expected_games=None,expected_jobs=None):
    manifests=sorted(root.rglob("games.json"))
    if not manifests:raise ValueError("No actual four-AI Forge games.json manifests")
    seen=set();seen_groups=set();games=[];sources=[]
    for manifest in manifests:
        records=json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(records,list) or not records:
            raise ValueError("Empty/corrupt Forge match manifest: "+str(manifest))
        for r in records:
            seats=r["seats"]
            if len(seats)!=4 or len(set(seats))!=4 or seats.count("Brimaz_V3")!=1:
                raise ValueError("Not four distinct Commander decks with one Brimaz")
            if r["brimaz_seat"]!=seats.index("Brimaz_V3")+1:
                raise ValueError("Mismatched Brimaz seat")
            key=(r["pod"],r["rotation"],r["repeat"],r["seed"],r["policy"])
            if key in seen:raise ValueError("Duplicate seeded game "+str(key))
            seen.add(key)
            if r["rotation"] not in range(4) or not isinstance(r["seed"],int):
                raise ValueError("Invalid rotation or seed")
            log=manifest.parent/Path(r["log"]).name
            if not log.is_file():raise ValueError("Missing genuine Forge log "+str(log))
            raw=log.read_text(encoding="utf-8",errors="replace")
            if "Turn: " not in raw or "Ai(1)-" not in raw:
                raise ValueError("Raw Forge 4-seat game actions not present "+str(log))
            if r["status"]=="complete" and (r["winner_seat"] not in range(1,5)
                                           or seats[r["winner_seat"]-1]!=r["winner_deck"]):
                raise ValueError("Manifest winner/seat contradiction")
            games.append({**r,"raw_log_sha256":hashlib.sha256(raw.encode()).hexdigest()})
        group=(records[0]["pod"],records[0]["rotation"],records[0]["policy"])
        if group in seen_groups:raise ValueError("Duplicate job group "+str(group))
        seen_groups.add(group)
        sources.append(str(manifest))
    if expected_jobs is not None and len(manifests)!=expected_jobs:
        raise ValueError(f"Missing job reports: {len(manifests)} != {expected_jobs}")
    if expected_games is not None and len(games)!=expected_games:
        raise ValueError(f"Missing true matches: {len(games)} != {expected_games}")

    status=Counter(g["status"] for g in games)
    naturally_finished=[g for g in games if g["status"]=="complete"]
    winners=Counter(g["winner_deck"] for g in naturally_finished)
    by_pod={}
    for pod in sorted(set(g["pod"] for g in games)):
        subset=[g for g in games if g["pod"]==pod]
        finished=[g for g in subset if g["status"]=="complete"]
        wins=Counter(g["winner_deck"] for g in finished)
        by_pod[pod]={
            "started":len(subset),"natural":len(finished),
            "censored_or_failed":len(subset)-len(finished),
            "winners_observed_uncertified":dict(wins),
            "brimaz_wins_observed_uncertified":wins.get("Brimaz_V3",0),
            "brimaz_win_fraction_of_natural_only":(
                round(wins.get("Brimaz_V3",0)/len(finished),5) if finished else None),
            "brimaz_wilson95_descriptive_only":wilson(wins.get("Brimaz_V3",0),len(finished)),
        }
    completed_walls=[g["wall_seconds"] for g in naturally_finished]
    report={
        "source":"ACTUAL Forge 2.0.15 4-player AI JVM transcripts, SHA256 verified present",
        "source_manifest_count":len(manifests),
        "games_started":len(games),
        "games_naturally_complete_unindependently_certified":len(naturally_finished),
        "censored_or_engine_failed_count":len(games)-len(naturally_finished),
        "status_counts":dict(status),
        "unique_seat_pod_seed_policy_games":len(seen),
        "pod_rotation_coverage":{
            p:sorted(set(g["rotation"] for g in games if g["pod"]==p))
            for p in sorted(set(g["pod"] for g in games))
        },
        "winners_observed_uncertified":dict(winners),
        "brimaz_wins_observed_uncertified":winners.get("Brimaz_V3",0),
        "brimaz_win_fraction_descriptive":round(winners.get("Brimaz_V3",0)/len(naturally_finished),5) if naturally_finished else None,
        "brimaz_wilson95_descriptive_only":wilson(winners.get("Brimaz_V3",0),len(naturally_finished)),
        "pods":by_pod,
        "completed_game_median_wall_seconds":round(sorted(completed_walls)[len(completed_walls)//2],2) if completed_walls else None,
        "total_sum_game_wall_seconds":round(sum(g["wall_seconds"] for g in games),2),
        "all_game_sha256_and_provenance":[{
            "pod":g["pod"],"rotation":g["rotation"],"repeat":g["repeat"],
            "seed":g["seed"],"status":g["status"],
            "winner_uncertified":g["winner_deck"],"sha256":g["raw_log_sha256"]
        } for g in games],
        "methodological_limits":[
            "Not independent Scryfall deck legality or complete Oracle rules certification.",
            "Natural ending is inferred from Forge's own raw log, not an external rules referee.",
            "Wilson interval is descriptive; shared opponents, seed structure and Forge AI nondeterminism may violate iid assumptions.",
            "Never count censored/draw/engine-fault games as wins or losses in natural-win denominator.",
            "No claim of expert human-like play, no full video-verified human dataset.",
            "Do not conflate parallel job wall time with summed JVM CPU/wall time.",
        ],
    }
    return report

def markdown(r):
    lines=["# Real Forge four-AI Commander tournament","",
           f"Processes: **{r['games_started']}** genuine logged games · "
           f"**{r['games_naturally_complete_unindependently_certified']}** natural finishes · "
           f"**{r['censored_or_engine_failed_count']}** censored/errors.",
           "",f"Raw status counts: {r['status_counts']}",
           f"Four-seat pod coverage: {r['pod_rotation_coverage']}","",
           "## Results by pod (unverified independent certification)","",
           "| Pod | Games | Natural finishes | Brimaz wins | Brimaz fraction | 95% Wilson (descriptive) |",
           "|---|---:|---:|---:|---:|---|"]
    for pod,x in r["pods"].items():
        ci=x["brimaz_wilson95_descriptive_only"]
        lines.append(f"| {pod} | {x['started']} | {x['natural']} | "
                     f"{x['brimaz_wins_observed_uncertified']} | "
                     f"{x['brimaz_win_fraction_of_natural_only']} | {ci} |")
    lines.extend(["","## Critical limitations",""])
    lines.extend("- "+v for v in r["methodological_limits"])
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--expected-games",type=int)
    p.add_argument("--expected-jobs",type=int)
    a=p.parse_args()
    r=aggregate(a.input,a.expected_games,a.expected_jobs)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"tournament.json").write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (a.out/"tournament.md").write_text(markdown(r),encoding="utf-8")
    print("FOUR_AI_REAL_TOURNAMENT",json.dumps({
        "games":r["games_started"],"natural":r["games_naturally_complete_unindependently_certified"],
        "censored":r["censored_or_engine_failed_count"],
        "winners_uncertified":r["winners_observed_uncertified"],
        "brimaz_wilson95_descriptive_only":r["brimaz_wilson95_descriptive_only"]
    },ensure_ascii=False),flush=True)
if __name__=="__main__":
    main()
