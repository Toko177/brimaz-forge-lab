#!/usr/bin/env python3
"""Forensic side-by-side of actual Forge Commander V13/V14 four-seat games.

Never treats status 'complete' or same seed as proof of superior strategy.
Requires both policies to have the same pod, seats and seed for each pair.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument("--pod", choices=["aristo", "artifact"], required=True)
p.add_argument("--out", default="results/target_pilot/forensic.json")
args = p.parse_args()
root = Path("results/batch") / args.pod
groups = {}
for policy, tag in (("control", "V13-target-control"),
                    ("tactical", "V14-four-seat-target")):
    records = json.loads((root / tag / "games.json").read_text(encoding="utf-8"))
    if not records:
        raise ValueError(f"No real games for {policy}")
    by_key = {}
    for x in records:
        key = (x["pod"], x["rotation"], x["seed"])
        if key in by_key:
            raise ValueError(f"Duplicate seed in {policy}: {key}")
        log = Path(x["log"]).read_text(encoding="utf-8", errors="replace")
        turns = re.findall(r"^Turn: Turn\s+(\d+)\s+\(([^)]+)\)", log, re.M)
        # Normalise away wall time and runtime status text. Game rules still
        # determine actual validity; comparison is descriptive only.
        moves = [line for line in log.splitlines()
                 if line.startswith(("Turn: ", "Phase: ", "Add To Stack: ",
                                     "Game Outcome: "))
                 and "Match Duration" not in line]
        choices = re.findall(
            r"FOUR_AI_TARGET: controller=(.*?) chosen=(.*?) "
            r"visibleSafeDamage=(\d+) opponentsScored=(\d+) score=(-?\d+) globalTurn=(\d+)",
            log)
        by_key[key] = {
            "manifest": x,
            "turns_observed": len(turns),
            "moves_sha256": hashlib.sha256("\n".join(moves).encode()).hexdigest(),
            "events": len(moves),
            "choice_count": len(choices),
            "controllers_actually_choosing": dict(Counter(k[0] for k in choices)),
            "visible_unblocked_damage_windows": sum(int(k[2]) > 0 for k in choices),
            "chosen_targets": dict(Counter(k[1] for k in choices)),
            "choice_samples": choices[:12],
            "log_sha256": hashlib.sha256(log.encode()).hexdigest(),
        }
    groups[policy] = by_key
if set(groups["control"]) != set(groups["tactical"]):
    raise ValueError("Mismatched canonical pods/seat rotations/seeds; reject")
rows = []
for key in sorted(groups["control"]):
    a, b = groups["control"][key], groups["tactical"][key]
    x, y = a["manifest"], b["manifest"]
    if x["seats"] != y["seats"]:
        raise ValueError("Not the same opponents/Brimaz seat in paired A/B")
    rows.append({
        "pod": key[0], "rotation": key[1], "seed": key[2],
        "four_seats": x["seats"],
        "control": {
            "status": x["status"], "winner": x["winner_deck"],
            "wall_seconds": x["wall_seconds"],
            "turn_events": a["turns_observed"],
            "observed_actions": a["events"],
        },
        "tactical": {
            "status": y["status"], "winner": y["winner_deck"],
            "wall_seconds": y["wall_seconds"],
            "turn_events": b["turns_observed"],
            "observed_actions": b["events"],
            "target_choices_logged": b["choice_count"],
            "controllers": b["controllers_actually_choosing"],
            "visible_unblocked_damage_windows": b["visible_unblocked_damage_windows"],
            "chosen_targets": b["chosen_targets"],
        },
        "same_observable_game_events": a["moves_sha256"] == b["moves_sha256"],
        "brimaz_win_change_if_both_natural": (
            int(y["brimaz_win"]) - int(x["brimaz_win"])
            if x["status"] == y["status"] == "complete" else None),
    })
report = {
    "pod": args.pod,
    "paired_real_game_count": len(rows),
    "real_game_executions": len(rows) * 2,
    "tactical_policy_activated": sum(r["tactical"]["target_choices_logged"] for r in rows) > 0,
    "total_target_choices_logged": sum(r["tactical"]["target_choices_logged"] for r in rows),
    "per_seat_controller_counts": dict(Counter(
        k for r in rows for k, n in r["tactical"]["controllers"].items()
        for _ in range(n)
    )),
    "records": rows,
    "limits": [
        "Observed attacker target choices, not a full proof of optimal gameplay.",
        "Visible unblocked attack damage is a tactical estimate; instant responses remain unknown.",
        "Only a run with independent game/deck certification can contribute to a win-rate estimate.",
        "Matching seeds do not guarantee identical cards once player decisions consume RNG differently.",
        "Four-seat capability does not mean that every seat had a legal profitable attack in each match."
    ],
}
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("FOUR_AI_MULTIPLAYER_TACTICAL_AUDIT", json.dumps(report, ensure_ascii=False), flush=True)
if not report["tactical_policy_activated"]:
    raise SystemExit("V14 code compiled but no actual target-choice execution was observed")
