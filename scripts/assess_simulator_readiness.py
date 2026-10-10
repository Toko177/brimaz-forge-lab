#!/usr/bin/env python3
"""Release-readiness evidence gates for REAL four-AI Forge match transcripts.

Does not claim a winrate is valid without independent legal-deck and engine
certification. This gate makes functional readiness independent from tactical
quality, throughput and statistical power. It never uses synthetic data to
claim readiness, and refuses missing logs/failed game observations.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

def evaluate(report, *, min_games=8, min_distinct_seeds=2):
    games=report["games"]
    issues=[]
    if not games: issues.append("No genuine Forge games")
    if len(games)<min_games: issues.append(f"Only {len(games)} of {min_games} required exploratory games")
    seeds={g["identity"]["seed"] for g in games}
    if len(seeds)<min_distinct_seeds:
        issues.append(f"Only {len(seeds)} distinct seeds, need {min_distinct_seeds}")
    games_by_status=Counter(g["identity"]["status"] for g in games)
    genuine=sum(g["identity"]["status"]=="complete" for g in games)
    if genuine < max(4,min_games*3//4):
        issues.append(f"Only {genuine} naturally completed game transcripts")
    # A natural-language warning on a clock-censored match is EXPECTED:
    # it honestly says there was no natural winner. Treating this note as an
    # engine fault made every 14-natural/2-censored V25 sample fail readiness.
    # Other warnings on a censored game (NPE, winner mismatch) remain fatal.
    unexpected_warnings=[
        {"pod":g["identity"].get("pod"),"seed":g["identity"]["seed"],"warning":w}
        for g in games
        for w in g["warnings"]
        if not (g["identity"]["status"]=="clock_censored"
                and w=="No natural finished-game claim: clock_censored")
    ]
    if unexpected_warnings:
        issues.append("At least one genuine match has an unexpected log/manifest discrepancy or engine fault")
    if any(g["identity"]["observed_turn_events"]<4 for g in games):
        issues.append("At least one game has fewer than 4 observable global turns")
    for g in games:
        if len(g["players"])!=4 or len({x["seat"] for x in g["players"]})!=4:
            issues.append("Four distinct real AI seats missing from one game")
            break
    all_decks={p["deck"] for g in games for p in g["players"]}
    no_activity={p["deck"] for g in games for p in g["players"]
                 if p["turns_taken"] and
                 (p["lands_played"]+p["spells_cast"]+p["abilities_activated"])==0}
    if no_activity:
        issues.append("Some active AI seats did not log any development actions: "+", ".join(sorted(no_activity)))
    slow_by_deck=Counter()
    for g in games:
        for p in g["players"]:slow_by_deck[p["deck"]]+=p["slow_ai_evaluations"]
    issue_gaps=[
        "No per-decision counterfactual legal choices or opponent response search yet.",
        "Not all official Magic rules are independently audited.",
        "No complete video-verified human action corpus is loaded.",
        "Win-rate significance is not established by an eight-process pilot.",
    ]
    return {
        "engine_pilot_gate":"PASS" if not issues else "BLOCKED",
        "ready_for_exploratory_4_ai_simulation":not issues,
        "statistically_validated_brimaz_winrate":False,
        "human_like_ai_demonstrated":False,
        "official_oracle_rules_certified":False,
        "sources":"Raw Forge 2.0.15 logs and SHA256; must additionally run certify_commander_games.py with Scryfall legality before citing wins",
        "game_count":len(games),
        "naturally_finished_count":genuine,
        "status_counts":dict(games_by_status),
        "distinct_decks":sorted(all_decks),
        "distinct_seed_count":len(seeds),
        "observed_slow_decisions_by_deck":dict(slow_by_deck),
        "unexpected_warnings":unexpected_warnings,
        "expected_clock_censored_games_kept_in_denominator":games_by_status.get("clock_censored",0),
        "blocking_issues":issues,
        "known_quality_gaps":issue_gaps,
        "methodology":"A functional engine pilot is not a winrate, expert decision or universal rules certification",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--forensics",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--min-games",type=int,default=8)
    a=p.parse_args()
    raw=json.loads(a.forensics.read_text(encoding="utf-8"))
    if not raw.get("type","").startswith("Forge four-seat action-level"):
        raise ValueError("Input is not the four-seat raw-log forensic schema")
    r=evaluate(raw,min_games=a.min_games)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_RELEASE_READINESS",json.dumps(r,ensure_ascii=False),flush=True)
    if r["engine_pilot_gate"]!="PASS":
        raise SystemExit("Not ready even for exploratory 4-AI simulations")
if __name__=="__main__":
    main()
