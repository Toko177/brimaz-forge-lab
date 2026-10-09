#!/usr/bin/env python3
"""Classify real Forge AI evaluation timeouts and slow choices, for all seats.

Only extract events from transcripts. Does NOT weaken opponents, alter card
effects, or treat an AI decision timeout as a Magic rules violation.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

LINE = re.compile(
    r"^AI_EVAL_(SLOW|TIMEOUT)_V10: player=(.*?)"
    r" globalTurn=(\d+) phase=(\S+) elapsedMs=(\d+) timeoutSecs=(\d+)"
    r" listed=(\d+) considered=(\d+) lastCandidate=(.*)$", re.M)
STACK = re.compile(r"^AI eval thread at timeout:\s*\n((?:\s*at [^\n]+\n?){1,30})", re.M)
OPENING = re.compile(
    r"^AI_OPENING_V10: player=(.*?) hand=(\d+) lands=(\d+)"
    r" cheapSpells=(\d+) cardsToBottom=(\d+)$", re.M)
SEAT = re.compile(r"Ai\((\d+)\)-")


def classify_stack(frames):
    text = "\n".join(frames)
    # Look beyond first JVM frame: hot branches are frequently generic
    # Card.get*() invoked *from* the blocker/combat prediction loop.
    if ("forge.ai.AiBlockController" in text or
            "forge.ai.ComputerUtilCombat" in text or
            "forge.ai.ComputerUtil.predictNextCombatsRemainingLife" in text):
        return "deep_combat_and_block_prediction"
    if "forge.game.replacement.ReplacementHandler" in text:
        return "replacement_effect_enumeration"
    if "forge.game.card.Card" in text or "forge.game.staticability" in text:
        return "card_static_or_spell_ability_recomputation"
    if "forge.ai." in text:
        return "other_ai_heuristics"
    return "unknown_or_other"


def seat_of(player):
    m = SEAT.match(player)
    return int(m[1]) if m else None


def inspect(raw, game):
    records = []
    for m in LINE.finditer(raw):
        kind, player, global_turn, phase, ms, limit, listed, considered, candidate = m.groups()
        ms, limit, listed, considered = map(int, (ms, limit, listed, considered))
        if ms < 0 or limit <= 0 or listed < 0 or considered < 0:
            raise ValueError("Invalid V10 evaluation metrics")
        if considered > 100000 or listed > 100000:
            raise ValueError("Unrealistically large V10 action candidate list")
        records.append({
            "kind": kind.lower(), "player": player, "seat": seat_of(player),
            "global_turn": int(global_turn), "phase": phase,
            "elapsed_ms": ms, "budget_seconds": limit,
            "candidates_listed": listed, "candidates_inspected": considered,
            "stalled_candidate": candidate,
        })
    openings = []
    for m in OPENING.finditer(raw):
        player = m[1]
        hand, lands, cheap, bottom = map(int, m.groups()[1:])
        if not (0 <= lands <= hand <= 7 and 0 <= cheap <= hand and 0 <= bottom <= 7):
            raise ValueError("Invalid V10 hand size telemetry")
        openings.append({"player": player, "seat": seat_of(player),
                         "hand": hand, "lands": lands, "cheap_spells": cheap,
                         "cards_to_bottom": bottom})

    stacks = []
    for m in STACK.finditer(raw):
        frames = re.findall(r"^\s*at ([^\n]+)", m[1], re.M)
        stacks.append({"classification": classify_stack(frames),
                       "top_frame": frames[0] if frames else None,
                       "frames": frames[:12]})
    timeout_records = [x for x in records if x["kind"] == "timeout"]
    if game.get("policy", "").startswith("V10") and (
            len(timeout_records) != raw.count("java.util.concurrent.TimeoutException")):
        raise ValueError("V10 AI timeout telemetry count differs from real Forge exceptions")
    if game.get("policy", "").startswith("V10") and not openings:
        raise ValueError("No V10 opening-hand traces in four-player game")
    if len(stacks) > raw.count("java.util.concurrent.TimeoutException"):
        raise ValueError("More timeout stack samples than timeout exceptions")

    return {
        "pod": game["pod"], "seed": game["seed"], "policy": game["policy"],
        "status": game["status"], "winner": game.get("winner_deck"),
        "brimaz_seat": game.get("brimaz_seat"),
        "events": records, "opening_hands": openings,
        "timeout_stacks": stacks,
        "original_timeout_exceptions": raw.count("java.util.concurrent.TimeoutException"),
        "original_invalid_attacks": raw.count("AI Attack declaration invalid"),
        "brimaz_mulligan_overrides": raw.count("overrideFreeMulligan=true"),
    }


def audit(root):
    games = []
    for path in sorted(root.rglob("games.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for g in manifest:
            log = path.parent / Path(g["log"]).name
            if not log.is_file():
                raise FileNotFoundError(log)
            games.append(inspect(log.read_text(encoding="utf-8", errors="replace"), g))
    if not games:
        raise ValueError("No games in root")
    all_events = [e for g in games for e in g["events"]]
    timeouts = [e for e in all_events if e["kind"] == "timeout"]
    slow = [e for e in all_events if e["kind"] == "slow"]
    stacks = [stack for g in games for stack in g["timeout_stacks"]]
    per_seat = Counter(x["seat"] for x in timeouts)
    hot = Counter(x["stalled_candidate"] for x in timeouts)
    return {
        "summary": {
            "games": len(games),
            "natural_games": sum(g["status"] == "complete" for g in games),
            "brimaz_wins": sum(g["status"] == "complete" and g["winner"] == "Brimaz_V3" for g in games),
            "ai_timeout_exceptions": sum(g["original_timeout_exceptions"] for g in games),
            "instrumented_timeout_events": len(timeouts),
            "slow_decisions_over_1000ms": len(slow),
            "invalid_attack_fallbacks": sum(g["original_invalid_attacks"] for g in games),
            "timeouts_by_seat": dict(sorted(per_seat.items())),
            "timeout_stalled_cards": dict(hot.most_common(12)),
            "stack_classes": dict(Counter(x["classification"] for x in stacks)),
            "openings_observed": sum(len(g["opening_hands"]) for g in games),
            "forced_brimaz_free_mulligans": sum(g["brimaz_mulligan_overrides"] for g in games),
            "caveat": "Forensic logging only: does not improve Forge AI, guarantee deterministic RNG, or verify Oracle rules."
        },
        "games": games,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = audit(a.input)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("ALL_FOUR_AI_V10_EVALUATION_SUMMARY", json.dumps(result["summary"], ensure_ascii=False))
    for g in result["games"]:
        print("AI_V10_GAME", json.dumps({
            "pod":g["pod"], "seed":g["seed"], "status":g["status"],
            "winner":g["winner"], "timeouts":g["original_timeout_exceptions"],
            "slow_decisions":sum(x["kind"]=="slow" for x in g["events"]),
            "forced_mulligans":g["brimaz_mulligan_overrides"]
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
