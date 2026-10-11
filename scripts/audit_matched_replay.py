#!/usr/bin/env python3
"""Compare genuine Forge transcripts from matched seeds without assuming determinism.

A different clock is an experimental condition, not a proof that a clock
changed the winner. Differences may come from AI randomness, concurrency,
implementation specifics or timeouts; do not assign causality from two logs.
"""
import argparse
import hashlib
import json
import pathlib
import re

EVENT_PREFIXES = ("Add To Stack:", "Land:", "Life:", "Mana:", "Damage:")
TURN = re.compile(r"^Turn: Turn (\d+)")
WINNER = re.compile(r"^Game Result: Game \d+ ended in (\d+) ms\. Ai\((\d+)\)-(.+?) has won!", re.M)


def events_from_transcript(raw):
    turn = None
    events = []
    for line in raw.splitlines():
        m = TURN.match(line)
        if m:
            turn = int(m[1])
        elif line.startswith(EVENT_PREFIXES):
            events.append({"turn": turn, "line": line})
    return events


def load_game(root):
    manifests = list(pathlib.Path(root).rglob("games.json"))
    if len(manifests) != 1:
        raise ValueError(f"Expected exactly one game manifest, found {len(manifests)} at {root}")
    games = json.loads(manifests[0].read_text(encoding="utf-8"))
    if len(games) != 1:
        raise ValueError("Expected one exact seed / pod / rotation per arm")
    game = games[0]
    log = manifests[0].parent / pathlib.Path(game["log"]).name
    if not log.exists():
        raise FileNotFoundError(log)
    raw = log.read_text(encoding="utf-8", errors="replace")
    return game, raw


def analyze(ref_game, ref_raw, replay_game, replay_raw):
    for field in ("seed", "pod", "rotation", "brimaz_seat", "seats", "profiles"):
        if ref_game.get(field) != replay_game.get(field):
            raise ValueError(f"Unmatched input condition: {field}")
    old = events_from_transcript(ref_raw)
    new = events_from_transcript(replay_raw)
    common = 0
    for x, y in zip(old, new):
        if x != y:
            break
        common += 1
    divergent = common < max(len(old), len(new))
    old_win = WINNER.findall(ref_raw)
    new_win = WINNER.findall(replay_raw)
    return {
        "identical_inputs_verified": True,
        "seed": ref_game["seed"], "pod": ref_game["pod"], "rotation": ref_game["rotation"],
        "clock_seconds": [ref_game.get("clock_seconds", 360), replay_game.get("clock_seconds", 360)],
        "reference_winner": ref_game.get("winner_deck"),
        "replay_winner": replay_game.get("winner_deck"),
        "reference_status": ref_game.get("status"),
        "replay_status": replay_game.get("status"),
        "reference_game_ms": ref_game.get("game_milliseconds"),
        "replay_game_ms": replay_game.get("game_milliseconds"),
        "outcome_reproduced": (
            ref_game.get("status") == "complete" and replay_game.get("status") == "complete"
            and ref_game.get("winner_deck") == replay_game.get("winner_deck")),
        "event_sequence_identical": not divergent,
        "reference_event_count": len(old),
        "replay_event_count": len(new),
        "identical_event_prefix": common,
        "first_divergence_reference": old[common] if common < len(old) else None,
        "first_divergence_replay": new[common] if common < len(new) else None,
        "raw_timeout_exception_occurrences": [
            ref_raw.count("java.util.concurrent.TimeoutException"),
            replay_raw.count("java.util.concurrent.TimeoutException")
        ],
        "reference_log_sha256": hashlib.sha256(ref_raw.encode("utf-8")).hexdigest(),
        "replay_log_sha256": hashlib.sha256(replay_raw.encode("utf-8")).hexdigest(),
        "limits": (
            "Two runs with different clock limits are not a controlled proof of "
            "what caused the winner change. Forge uses AI choices and may have "
            "timeout-dependent or nondeterministic behavior. TimeoutException "
            "signatures are diagnostic warnings, not by themselves illegal "
            "Magic game actions. A winning result is not evidence of expert AI."
        )
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--replay", required=True)
    parser.add_argument("--output", required=True)
    a = parser.parse_args()
    x, xlog = load_game(a.reference)
    y, ylog = load_game(a.replay)
    result = analyze(x, xlog, y, ylog)
    dest = pathlib.Path(a.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("FORGE_MATCHED_SEED_REPLAY_AUDIT", json.dumps({
        key: result[key] for key in (
            "seed", "outcome_reproduced", "reference_winner", "replay_winner",
            "identical_event_prefix", "first_divergence_reference", "first_divergence_replay",
            "raw_timeout_exception_occurrences"
        )}, ensure_ascii=False))


if __name__ == "__main__":
    main()
