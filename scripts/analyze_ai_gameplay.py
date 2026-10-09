#!/usr/bin/env python3
"""Audit observed Brimaz AI actions from genuine Forge game transcripts.

This measures actions that reached Forge's stack, not unseen legal opportunities,
rationality of a sacrifice, or proof of strategy improvement.  Transcript events
are buffered after live BRIMAZ_DEVELOPMENT diagnostics: correlate by game, not
by their physical proximity to those diagnostics.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re

TRACKED = (
    "Brimaz, Blight of Oreskos",
    "Incubator Token",
    "Krark-Clan Ironworks",
    "Orzhov Signet",
    "Spawning Pit",
    "Arcbound Ravager",
    "High Market",
    "Phyrexian Tower",
    "Throne of Geth",
    "Phyrexian Reclamation",
    "Tortured Existence",
    "Diabolic Intent",
    "Phyrexian Delver",
)
TURN = re.compile(r"^Turn: Turn (\d+) \(Ai\((\d+)\)-")
PHASE = re.compile(r"^Phase: Ai\((\d+)\)-.*'s (.+)$")
STACK = re.compile(r"^Add To Stack: Ai\((\d+)\)-.*? (cast|activated|triggered) (.+)$")


def audit_game(game, transcript):
    """Return actual stack actions separated by actor, action, card, and phase."""
    seat = game["brimaz_seat"]
    current_turn = None
    active_seat = None
    phase = None
    events = []
    counts = collections.Counter()
    for line in transcript.splitlines():
        turn_match = TURN.match(line)
        if turn_match:
            current_turn = int(turn_match[1])
            active_seat = int(turn_match[2])
            phase = None
            continue
        phase_match = PHASE.match(line)
        if phase_match:
            phase = phase_match[2]
            continue
        match = STACK.match(line)
        if not match or int(match[1]) != seat:
            continue
        verb, action = match[2], match[3]
        for card in TRACKED:
            if not (action == card or action.startswith(card + " ") or
                    action.startswith(card + " targeting")):
                continue
            counts[f"{verb}|{card}"] += 1
            if card == "Brimaz, Blight of Oreskos" and verb == "triggered":
                if phase == "End step":
                    counts["brimaz_end_step_triggers"] += 1
                    if active_seat != seat:
                        counts["brimaz_opponent_end_step_triggers"] += 1
            if verb == "activated" and card in (
                "Krark-Clan Ironworks", "Spawning Pit", "Arcbound Ravager",
                "High Market", "Phyrexian Tower", "Throne of Geth"
            ):
                counts["sacrifice_outlet_activations_observed"] += 1
                if active_seat is not None and active_seat != seat and phase != "End step":
                    counts["outlet_activations_opponent_before_end_step"] += 1
            events.append({
                "turn": current_turn, "active_seat": active_seat,
                "phase": phase, "verb": verb, "card": card
            })
            break
    diagnostics = {
        "commander_development_proposals": transcript.count("BRIMAZ_DEVELOPMENT: cast-commander"),
        "artifact_development_proposals": transcript.count("BRIMAZ_DEVELOPMENT: cast-engine"),
        "sacrifice_planner_proposals": transcript.count("BRIMAZ_PLANNER:"),
        "defensive_transformation_proposals": transcript.count("BRIMAZ_DEFENSE: transform-incubator"),
    }
    # KCI is a mana ability: mana abilities do NOT use the stack, and
    # "Mana: Krark-Clan Ironworks" in Forge may be ability enumeration,
    # not an activation. Never infer non-use from missing Add To Stack.
    cast_without_activation = [
        card for card in ("Spawning Pit",)
        if counts[f"cast|{card}"] > 0 and counts[f"activated|{card}"] == 0
    ]
    return {
        "pod": game.get("pod"), "policy": game.get("policy"),
        "rotation": game.get("rotation"), "seed": game.get("seed"),
        "brimaz_seat": seat, "status": game.get("status"),
        "winner_deck": game.get("winner_deck"),
        "transcript_sha256": hashlib.sha256(transcript.encode("utf-8")).hexdigest(),
        "actions": dict(sorted(counts.items())),
        "development_diagnostics": diagnostics,
        "cast_but_never_activated_in_game": cast_without_activation,
        "events": events,
        "limitation": (
            "No recorded stack activation does not prove a legal and advantageous "
            "activation was available. KCI mana activations are not observable "
            "as Add To Stack events. Forge phase logging does not reveal "
            "every private choice or whether using an outlet was strategically good."
        )
    }


def audit_tree(root):
    games = []
    for manifest in sorted(root.rglob("games.json")):
        for game in json.loads(manifest.read_text(encoding="utf-8")):
            # A manifest may originate from an artifact with an unrelated root
            # path; the basename is unique within the manifest's own shard.
            logfile = manifest.parent / pathlib.Path(game["log"]).name
            if not logfile.is_file():
                raise FileNotFoundError(f"Missing game transcript: {logfile}")
            raw = logfile.read_text(encoding="utf-8", errors="replace")
            games.append(audit_game(game, raw))
    if not games:
        raise ValueError("No Forge game manifests supplied")
    totals = collections.Counter()
    for game in games:
        totals.update(game["actions"])
        for key, value in game["development_diagnostics"].items():
            totals[key] += value
    return {
        "summary": {
            "games": len(games),
            "natural_games_in_manifest": sum(g["status"] == "complete" for g in games),
            "brimaz_wins_in_manifest": sum(g["winner_deck"] == "Brimaz_V3" and
                                           g["status"] == "complete" for g in games),
            "kci_mana_activation_auditability": "Not measured: mana abilities bypass the stack",
            "games_with_cast_unactivated_spawning_pit": sum(
                "Spawning Pit" in g["cast_but_never_activated_in_game"]
                for g in games),
            "observed_actions": dict(sorted(totals.items())),
            "interpretation": (
                "Action counts are observations, not missed-opportunity rates "
                "or verified improvements in AI skill. Game validity must be "
                "established independently by certify_commander_games.py."
            )
        },
        "games": games,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = audit_tree(pathlib.Path(args.input))
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FORGE_AI_ACTION_AUDIT", json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
