#!/usr/bin/env python3
"""Audit same-for-every-seat 5->10->15s timeout recovery experiment.

This audit does NOT treat higher computational expenditure as stronger AI.
"""
import argparse
import json
from pathlib import Path
import re

RE = re.compile(
    r"^AI_ADAPTIVE_BUDGET_V(11|13): previousSeconds=(\d+)"
    r" currentSeconds=(\d+) appliedTo=ALL_FOUR_SEATS$", re.M)


def analyze(raw, game):
    changes = [{"instrumentation_version": int(version),
                "previous_seconds": int(a), "current_seconds": int(b)}
               for version, a, b in RE.findall(raw)]
    previous = 5
    for ch in changes:
        if ch["previous_seconds"] != previous or ch["current_seconds"] != min(15, previous+5):
            raise ValueError("V11 AI budget did not follow monotone global 5 -> 10 -> 15 rule")
        previous = ch["current_seconds"]
    if len({c["instrumentation_version"] for c in changes}) > 1:
        raise ValueError("Mixed V11 and V13 budget telemetry in one game")
    if changes and "V" + str(changes[0]["instrumentation_version"]) not in game["policy"]:
        raise ValueError("Adaptation trace version does not match AI policy label")
    if len(changes) > 2:
        raise ValueError("Adaptive AI cannot exceed two shared budget increases")
    actual_timeout_exceptions = raw.count("java.util.concurrent.TimeoutException")
    if len(changes) > actual_timeout_exceptions:
        raise ValueError("V11 budget increase occurred without original Forge timeout")
    if game["policy"].startswith(("V11", "V13")) and actual_timeout_exceptions > 0 and not changes:
        raise ValueError("V11 timeout occurred without shared budget adaptation")
    return {
        "pod": game["pod"], "seed": game["seed"], "status": game["status"],
        "winner": game.get("winner_deck"), "brimaz_win": game.get("brimaz_win"),
        "actual_timeout_exceptions": actual_timeout_exceptions,
        "invalid_attacks": raw.count("AI Attack declaration invalid"),
        "final_ai_timeout_seconds": previous, "adaptations": changes,
    }


def audit(root):
    games = []
    for manifest in sorted(root.rglob("games.json")):
        for g in json.loads(manifest.read_text(encoding="utf-8")):
            log = manifest.parent / Path(g["log"]).name
            if not log.exists():
                raise FileNotFoundError(log)
            games.append(analyze(log.read_text(encoding="utf-8", errors="replace"), g))
    if not games:
        raise ValueError("No match records")
    return {
        "summary": {
            "games": len(games),
            "natural_games": sum(g["status"]=="complete" for g in games),
            "brimaz_natural_wins": sum(g["status"]=="complete" and g["brimaz_win"] is True for g in games),
            "ai_future_timeouts": sum(g["actual_timeout_exceptions"] for g in games),
            "games_using_adaptive_budget": sum(bool(g["adaptations"]) for g in games),
            "increases_to_10_seconds": sum(ch["current_seconds"]==10 for g in games for ch in g["adaptations"]),
            "increases_to_15_seconds": sum(ch["current_seconds"]==15 for g in games for ch in g["adaptations"]),
            "caveat": "Game-wide timeout applies fairly to every seat. This is not evidence of stronger or more realistic decisions without controlled quality and CPU cost analysis."
        },
        "games": games
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = audit(a.input)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("AI_ADAPTIVE_V11_OUTCOME", json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
