#!/usr/bin/env python3
"""Audit Brimaz V9 mulligan decisions actually printed by four-player Forge.

A logged override is an AI choice, not proof that a free mulligan improved
the hand or win probability. The real Forge 'Mulligan:' outcomes still govern.
"""
import argparse
import json
from pathlib import Path
import re

CANDIDATE = re.compile(
    r"^BRIMAZ_MULLIGAN: V9 hand=(\d+) actualLands=(\d+)"
    r" potentialLandDrops=(\d+) cheapRamp=(\d+) cheapDraw=(\d+)"
    r" expensive=(\d+) cardsToReturn=(\d+)"
    r" stockKeep=(true|false) overrideFreeMulligan=(true|false)$",
    re.M,
)
KEPT = re.compile(r"^Mulligan: Ai\((\d+)\)-.* has kept a hand of (\d+) cards", re.M)
MULLED = re.compile(r"^Mulligan: Ai\((\d+)\)-.* has mulliganed down to (\d+) cards", re.M)


def inspect(raw, game):
    actions = []
    for m in CANDIDATE.finditer(raw):
        hand, lands, potential, ramp, draw, expensive, bottom = map(int, m.groups()[:7])
        stock, override = m.group(8) == "true", m.group(9) == "true"
        if not (0 <= lands <= potential <= hand <= 7):
            raise ValueError("Invalid V9 opening hand telemetry")
        if override and (bottom != 0 or not stock or potential != 2 or ramp or draw or expensive < 2):
            raise ValueError("V9 used free override outside documented gate")
        actions.append({
            "hand": hand, "actual_lands": lands, "potential_land_drops": potential,
            "cheap_ramp": ramp, "cheap_draw": draw, "expensive": expensive,
            "cards_to_bottom": bottom, "stock_keep": stock, "override": override
        })
    seat = game["brimaz_seat"]
    kept = [int(n) for s, n in KEPT.findall(raw) if int(s) == seat]
    mulligans = [int(n) for s, n in MULLED.findall(raw) if int(s) == seat]
    if game.get("status") == "complete" and len(kept) != 1:
        raise ValueError("Expected exactly one logged Brimaz kept opening hand")
    if game.get("policy") == "V9-mulligan" and not actions:
        raise ValueError("No Brimaz V9 mulligan telemetry despite V9 pilot")
    return {
        "pod": game["pod"], "seed": game["seed"], "status": game["status"],
        "winner_deck": game.get("winner_deck"), "brimaz_win": game.get("brimaz_win"),
        "opening_decisions": actions, "free_overrides": sum(int(x["override"]) for x in actions),
        "logged_mulligans": mulligans, "kept_hand_size": kept[-1] if kept else None
    }


def run(root):
    games = []
    for manifest in sorted(root.rglob("games.json")):
        for game in json.loads(manifest.read_text(encoding="utf-8")):
            path = manifest.parent / Path(game["log"]).name
            if not path.exists():
                raise FileNotFoundError(path)
            games.append(inspect(path.read_text(encoding="utf-8", errors="replace"), game))
    if not games:
        raise ValueError("No games to audit")
    summary = {
        "games": len(games), "natural_games": sum(x["status"] == "complete" for x in games),
        "free_mulligan_overrides": sum(x["free_overrides"] for x in games),
        "games_using_override": sum(x["free_overrides"] > 0 for x in games),
        "brimaz_natural_wins": sum(x["status"] == "complete" and x["brimaz_win"] is True for x in games),
        "never_assume_outcome_improvement_from_an_override": True,
    }
    return {"summary": summary, "games": games}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = run(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("BRIMAZ_V9_MULLIGAN_AUDIT", json.dumps(report["summary"], ensure_ascii=False))
    for game in report["games"]:
        print("BRIMAZ_V9_MULLIGAN_GAME", json.dumps(game, ensure_ascii=False))


if __name__ == "__main__":
    main()
