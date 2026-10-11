#!/usr/bin/env python3
"""Paired observational comparison of two *real* Forge 4-player EDH pilots.

Forge RNG seed alone does NOT ensure game trace identity. Pairing the same
pod/seat/seed is useful for describing changes but is NOT causal proof that
one AI is stronger, especially with mulligan affecting shuffle and drawing.
"""
import argparse
import json
from pathlib import Path


def keyed(pacing, title):
    out = {}
    for g in pacing["games"]:
        key = (g["pod"], g["seed"])
        if key in out:
            raise ValueError(f"Duplicate pod/seed in {title}: {key}")
        out[key] = g
    if not out:
        raise ValueError(f"No games in {title}")
    return out


def compare(reference, candidate, mulligan):
    left = keyed(reference, "reference")
    right = keyed(candidate, "candidate")
    treated = keyed(mulligan, "mulligan")
    if set(left) != set(right) or set(right) != set(treated):
        raise ValueError("Pods/seeds differ across the three experiment reports")
    entries = []
    for key in sorted(left):
        old, new, opening = left[key], right[key], treated[key]
        if old["policy"] == new["policy"]:
            raise ValueError(f"Reference and candidate policies identical: {key}")
        before = int(old["brimaz_land_drops_by_own_turn"]["8"])
        after = int(new["brimaz_land_drops_by_own_turn"]["8"])
        entries.append({
            "pod": key[0], "seed": key[1],
            "reference_policy": old["policy"],
            "candidate_policy": new["policy"],
            "free_mulligan_override_applied": opening["free_overrides"] > 0,
            "reference_natural_finish": old["status"] == "complete",
            "candidate_natural_finish": new["status"] == "complete",
            "reference_winner": old.get("winner_deck"),
            "candidate_winner": new.get("winner_deck"),
            "reference_brimaz_win": old.get("winner_deck") == "Brimaz_V3" and old["status"] == "complete",
            "candidate_brimaz_win": new.get("winner_deck") == "Brimaz_V3" and new["status"] == "complete",
            "reference_first_commander_cast_own_turn": old["brimaz_first_cast_on_own_turn"],
            "candidate_first_commander_cast_own_turn": new["brimaz_first_cast_on_own_turn"],
            "reference_land_drops_through_own_turn_8": before,
            "candidate_land_drops_through_own_turn_8": after,
            "change_in_land_drops_through_turn_8": after - before,
            "reference_total_brimaz_own_turns": old["brimaz_own_turns"],
            "candidate_total_brimaz_own_turns": new["brimaz_own_turns"],
        })
    natural_pairs = [r for r in entries if r["reference_natural_finish"] and r["candidate_natural_finish"]]
    return {
        "summary": {
            "paired_pod_seed_comparisons": len(entries),
            "both_naturally_completed": len(natural_pairs),
            "candidate_games_with_free_mulligan_override": sum(r["free_mulligan_override_applied"] for r in entries),
            "better_land_development_in_pairs": sum(r["change_in_land_drops_through_turn_8"] > 0 for r in natural_pairs),
            "worse_land_development_in_pairs": sum(r["change_in_land_drops_through_turn_8"] < 0 for r in natural_pairs),
            "same_land_development_in_pairs": sum(r["change_in_land_drops_through_turn_8"] == 0 for r in natural_pairs),
            "brimaz_reference_wins_natural": sum(r["reference_brimaz_win"] for r in natural_pairs),
            "brimaz_candidate_wins_natural": sum(r["candidate_brimaz_win"] for r in natural_pairs),
            "no_causal_inference": "Forge can diverge with identical seed and decks; game outcomes cannot be attributed solely to AI or mulligan policy differences.",
            "no_win_rate_claim": "These are four pilot games per variant, not a statistical Commander performance estimate."
        }, "games": entries
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--mulligan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    res = compare(
        json.loads(a.reference.read_text(encoding="utf-8")),
        json.loads(a.candidate.read_text(encoding="utf-8")),
        json.loads(a.mulligan.read_text(encoding="utf-8")),
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("BRIMAZ_OBSERVATIONAL_AB_V8_V9", json.dumps(res["summary"], ensure_ascii=False))
    for game in res["games"]:
        print("BRIMAZ_AB_GAME", json.dumps(game, ensure_ascii=False))


if __name__ == "__main__":
    main()
