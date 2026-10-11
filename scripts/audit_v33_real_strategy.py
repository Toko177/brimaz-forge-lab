#!/usr/bin/env python3
"""Audit TRUE 4-AI Forge paired experiments for actual V33 interventions.

This never treats policy-selection logging as successful spell resolution,
and never turns censored games into wins or losses.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

CHOICE = re.compile(
    r"^FOUR_AI_V33_STRATEGIC_CHOICE player=Ai\((?P<seat>[1-4])\)-"
    r"(?P<deck>.*?) turn=(?P<turn>\d+) first=(?P<first>.*?) role="
    r"(?P<role>\w+) second=(?P<second>.*?) alternative=(?P<alternative>.*?) "
    r"immediate=(?P<immediate>-?\d+) future=(?P<future>-?\d+) "
    r"margin=(?P<margin>\d+) .*realForgeLegalAndPayable=true$", re.M)


ACTION = re.compile(
    r"^FOUR_AI_V33_STRATEGIC_ACTION player=Ai\\((?P<seat>[1-4])\\)-"
    r"(?P<deck>.*?) turn=(?P<turn>\\d+) first=(?P<first>.*?) "
    r"acceptedByStockForgeAI=true$", re.M)


def key(d):
    return d["seat"], d["turn"], d["first"]


def audit(report):
    if report.get("type") != "Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B":
        raise ValueError("Expected real Forge paired four-AI log comparison")
    if report["reference_provenance"]["policy"] != "v17_strict":
        raise ValueError("Not the pinned unchanged baseline strategy")
    if report["experiment_provenance"]["policy"] != "v33_strategy":
        raise ValueError("Not the new strategic policy")
    pairs = report["pairs"]
    if not pairs or len(pairs) != report["real_process_pairs"]:
        raise ValueError("No complete real JVM match pairing")
    by_seat = Counter()
    by_role = Counter()
    by_pod = Counter()
    by_status = Counter()
    changed = 0
    examples = []
    for pair in pairs:
        ref = pair["reference"]
        exp = pair["experiment"]
        raw_ref = Path(ref["log"]).read_text(encoding="utf-8", errors="replace")
        raw_exp = Path(exp["log"]).read_text(encoding="utf-8", errors="replace")
        if "Ai(1)-" not in raw_ref or "Ai(4)-" not in raw_exp or "Turn: " not in raw_exp:
            raise ValueError("Real four-seat Forge game logs missing")
        if CHOICE.search(raw_ref) or ACTION.search(raw_ref):
            raise ValueError("Disabled reference engine produced V33 strategic selection")
        rows = list(CHOICE.finditer(raw_exp))
        accepted = list(ACTION.finditer(raw_exp))
        proposed = {key(m.groupdict()): m.groupdict() for m in rows}
        for act in accepted:
            if key(act.groupdict()) not in proposed:
                raise ValueError("Real Forge-approved action has no preceding strategy proposal")
        for m in accepted:
            d = proposed[key(m.groupdict())]
            index = int(d["seat"])
            if index not in (1, 2, 3, 4) or int(d["turn"]) < 1:
                raise ValueError("Invalid 4-AI decision identifier")
            if int(d["margin"]) < 700 or int(d["immediate"]) < 12:
                raise ValueError("Bad V33 strategy acceptance margin")
            by_seat[index] += 1
            by_role[d["role"]] += 1
            by_pod[exp["pod"]] += 1
            if len(examples) < 25:
                examples.append({**d,"pod":exp["pod"],"rotation":exp["rotation"]})
        by_status[(ref["status"], exp["status"])] += 1
        if ref["event_sha256"] != exp["event_sha256"]:
            changed += 1
    return {
        "actual_forge_jvm_processes":report["real_forge_jvm_processes"],
        "genuine_full_game_pairs":len(pairs),
        "strategy_evaluations_accepted_not_proven_resolved":sum(by_seat.values()),
        "strategy_proposals_before_original_forge_ai_approval":sum(
            len(CHOICE.findall(Path(pair["experiment"]["log"]).read_text(encoding="utf-8",errors="replace")))
            for pair in pairs),
        "seat_counts":dict(sorted(by_seat.items())),
        "role_counts":dict(by_role),
        "pod_counts":dict(by_pod),
        "paired_status":{str(k):v for k,v in by_status.items()},
        "pairs_with_changed_observable_game_events":changed,
        "both_natural":report["both_natural_pairs"],
        "censored_or_failed_pair":report["pairs_with_any_censor_or_fault"],
        "changed_natural_winner":report["natural_pairs_with_different_winner"],
        "examples":examples,
        "provenance_limitations":[
            "All events originate in genuine Forge 2.0.15 four-AI JVM games",
            "Selected means recommended before Forge payment/resolution, NOT proven cast",
            "Chosen spell remains subject to normal actual Forge costs and triggers",
            "A changed game trace does not establish improved strategic decisions",
            "Small same-seed A/B games are not a statistically valid winrate proof",
            "Censures and timeouts remain neither natural wins nor natural losses",
        ]
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--require-intervention", action="store_true")
    a=p.parse_args()
    r=audit(json.loads(a.input.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_V33_GENUINE_STRATEGIC_DIAGNOSTICS",json.dumps({
        k:r[k] for k in ("actual_forge_jvm_processes","genuine_full_game_pairs",
         "strategy_evaluations_accepted_not_proven_resolved","seat_counts",
         "role_counts","pairs_with_changed_observable_game_events","both_natural",
         "censored_or_failed_pair","changed_natural_winner")
    },ensure_ascii=False),flush=True)
    if a.require_intervention and not r["strategy_evaluations_accepted_not_proven_resolved"]:
        raise SystemExit("V33 has zero decisions in genuine four-player Forge logs")


if __name__=="__main__":
    main()
