#!/usr/bin/env python3
"""Audit Forge Commander turn pacing in *player turns*, not global turn ids.

Calibration source: https://playgroup.gg/commander/how-to-play
547,279 real multiplayer games, median 9 rounds (October 2026).
Brimaz-specific reference: https://playgroup.gg/commanders/2396-brimaz-blight-of-oreskos
Approximate 10 own turns in winning games. These are aggregate reference
statistics, not legal rules, hard caps, or a training dataset.

The maximum number of observed individual turns is a proxy for completed
table rotations, NOT necessarily precise with dead seats, extra turns, etc.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import statistics

TURN = re.compile(r"^Turn: Turn (\d+) \(Ai\((\d+)\)-", re.M)
LAND = re.compile(r"^Land: Ai\((\d+)\)-.* played (.+?)(?: \(\d+\))?$")
CAST = re.compile(r"^Add To Stack: Ai\((\d+)\)-.*? cast (.+)$")
DAMAGE = re.compile(r"^Damage: ")


def analyze(raw, manifest):
    seats = manifest.get("seats", [])
    if len(seats) != 4 or sorted(seats).count("Brimaz_V3") != 1:
        raise ValueError("Expected four players, one using canonical Brimaz_V3")
    brimaz = manifest["brimaz_seat"]
    if not 1 <= brimaz <= 4 or seats[brimaz - 1] != "Brimaz_V3":
        raise ValueError("Brimaz seat inconsistent with manifest")
    turns = Counter()
    lands = Counter()
    casts = Counter()
    land_drops_by_turn = {i: Counter() for i in range(1, 5)}
    spells_by_turn = {i: Counter() for i in range(1, 5)}
    first_cast_own = None
    first_cast_global = None
    first_cast_lands = None
    max_global = 0
    active_seat = None
    out_of_turn_spells = Counter()
    combat_lines = 0
    damage_lines = 0
    for line in raw.splitlines():
        m = TURN.match(line)
        if m:
            max_global = max(max_global, int(m[1]))
            active_seat = int(m[2])
            turns[active_seat] += 1
            continue
        if line.startswith("Combat:"):
            combat_lines += 1
        if DAMAGE.match(line):
            damage_lines += 1
        m = LAND.match(line)
        if m:
            seat = int(m[1])
            lands[seat] += 1
            land_drops_by_turn[seat][turns[seat]] += 1
            continue
        m = CAST.match(line)
        if m:
            seat = int(m[1])
            casts[seat] += 1
            spells_by_turn[seat][turns[seat]] += 1
            if active_seat is not None and active_seat != seat:
                out_of_turn_spells[seat] += 1
            if seat == brimaz and m[2].strip().startswith("Brimaz, Blight of Oreskos") and first_cast_own is None:
                first_cast_own = turns[seat]
                first_cast_global = max_global
                first_cast_lands = lands[seat]
    if max_global < 1 or not turns:
        raise ValueError("No actual Forge player turns observed")
    land_curve = {str(n): sum(count for t, count in land_drops_by_turn[brimaz].items() if t <= n)
                  for n in [2, 3, 4, 5, 6, 8]}
    spell_curve = {str(n): sum(count for t, count in spells_by_turn[brimaz].items() if t <= n)
                   for n in [2, 3, 4, 5, 6, 8]}
    return {
        "pod": manifest.get("pod"),
        "seed": manifest.get("seed"),
        "policy": manifest.get("policy"),
        "status": manifest.get("status"),
        "winner_deck": manifest.get("winner_deck"),
        "global_turn_last": max_global,
        "actual_player_turns": {str(i): turns[i] for i in range(1, 5)},
        "longest_observed_player_turn_count": max(turns.values()),
        "brimaz_own_turns": turns[brimaz],
        "brimaz_first_cast_on_own_turn": first_cast_own,
        "brimaz_first_cast_global_turn": first_cast_global,
        "brimaz_lands_played_before_first_cast": first_cast_lands,
        "brimaz_land_drops_by_own_turn": land_curve,
        "brimaz_spells_cast_by_own_turn": spell_curve,
        "brimaz_total_lands_played": lands[brimaz],
        "brimaz_total_spells_cast": casts[brimaz],
        "brimaz_casts_on_opponents_turns": out_of_turn_spells[brimaz],
        "total_combat_log_entries": combat_lines,
        "total_damage_log_entries": damage_lines,
        "ai_evaluation_timeouts": raw.count("java.util.concurrent.TimeoutException"),
        "is_naturally_complete": manifest.get("status") == "complete",
    }


def audit_tree(root):
    games = []
    for manifest in sorted(root.rglob("games.json")):
        for game in json.loads(manifest.read_text(encoding="utf-8")):
            log = manifest.parent / Path(game["log"]).name
            if not log.is_file():
                raise FileNotFoundError(str(log))
            games.append(analyze(log.read_text(encoding="utf-8", errors="replace"), game))
    if not games:
        raise ValueError("No game manifests")
    completed = [g for g in games if g["is_naturally_complete"]]
    first_casts = [g["brimaz_first_cast_on_own_turn"] for g in completed
                   if g["brimaz_first_cast_on_own_turn"] is not None]
    summary = {
        "games": len(games),
        "natural_finishes": len(completed),
        "median_longest_player_turns": statistics.median(
            g["longest_observed_player_turn_count"] for g in completed) if completed else None,
        "brimaz_never_cast_games": sum(g["brimaz_first_cast_on_own_turn"] is None for g in completed),
        "brimaz_first_cast_own_turn_median_if_cast": statistics.median(first_casts) if first_casts else None,
        "brimaz_first_cast_after_own_turn_6": sum(n > 6 for n in first_casts),
        "benchmark_real_multiplayer_median_rounds": 9,
        "benchmark_source": "https://playgroup.gg/commander/how-to-play",
        "benchmark_brimaz_win_turns_approx": 10,
        "benchmark_brimaz_source": "https://playgroup.gg/commanders/2396-brimaz-blight-of-oreskos",
        "caveat": (
            "Forge global turns are individual player turns. Maximum per-seat turn "
            "count is a round proxy, not an exact round clock after extra turns / "
            "elimination. Empirical benchmark aggregates are observational; they "
            "must never be used to force an artificial game ending or change rules. "
            "4 games cannot establish normality or Brimaz win rate."
        ),
    }
    return {"summary": summary, "games": games}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = audit_tree(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("EDH_EMPIRICAL_PACING_SUMMARY", json.dumps(report["summary"], ensure_ascii=False))
    for g in report["games"]:
        print("EDH_EMPIRICAL_PACING_GAME", json.dumps(g, ensure_ascii=False))


if __name__ == "__main__":
    main()
