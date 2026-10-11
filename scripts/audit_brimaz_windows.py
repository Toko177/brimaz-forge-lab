#!/usr/bin/env python3
"""Read opt-in V7 Forge AI decision-window telemetry from real game logs.

Only reports observations. A candidate token is NOT necessarily a legal
sacrifice target, and an unused outlet is NOT necessarily a tactical mistake.
"""
import argparse
import collections
import json
import pathlib
import re

WINDOW = re.compile(
    r"^BRIMAZ_WINDOW: V7 turn=(\d+) active=(.*?) selfTurn=(true|false)"
    r" brimazOnBattlefield=(true|false) phyrexianDeathsSoFar=(-?\d+)"
    r" candidatePhyrexianTokens=(\d+) outletCardsOnBattlefield=(\d+)"
    r" listedSacrificeOutletAbilities=(\d+) availableAbilities=(\d+)$",
    re.M,
)


def extract_windows(raw):
    items = []
    for m in WINDOW.finditer(raw):
        items.append({
            "turn": int(m[1]),
            "active": m[2],
            "self_turn": m[3] == "true",
            "brimaz_on_battlefield": m[4] == "true",
            "phyrexian_deaths_before_end_step": int(m[5]),
            "candidate_phyrexian_tokens": int(m[6]),
            "outlet_cards_on_battlefield": int(m[7]),
            "listed_sacrifice_outlet_abilities": int(m[8]),
            "listed_total_abilities": int(m[9]),
        })
    return items


def summarize(games):
    c = collections.Counter()
    for game in games:
        c["games"] += 1
        c["natural_games"] += int(game["status"] == "complete")
        c["brimaz_wins"] += int(game["brimaz_win"] is True and game["status"] == "complete")
        for w in game["decision_windows"]:
            c["decision_windows_observed"] += 1
            if not w["self_turn"]:
                c["opponent_main2_windows_observed"] += 1
            if not w["brimaz_on_battlefield"]:
                c["brimaz_absent_windows"] += 1
                continue
            c["brimaz_on_battlefield_windows"] += 1
            if w["phyrexian_deaths_before_end_step"] != 0:
                c["death_already_occurred_windows"] += 1
                continue
            c["end_step_death_not_yet_met_windows"] += 1
            if w["candidate_phyrexian_tokens"] == 0:
                c["no_candidate_phyrexian_token_windows"] += 1
            elif w["outlet_cards_on_battlefield"] == 0:
                c["no_outlet_permanent_on_board_windows"] += 1
            elif w["listed_sacrifice_outlet_abilities"] == 0:
                c["outlet_on_board_but_absent_from_main_action_list_windows"] += 1
            else:
                c["candidate_token_and_listed_outlet_windows"] += 1
    return dict(sorted(c.items()))


def inspect(root):
    games = []
    for manifest in sorted(root.rglob("games.json")):
        for g in json.loads(manifest.read_text(encoding="utf-8")):
            p = manifest.parent / pathlib.Path(g["log"]).name
            if not p.is_file():
                raise FileNotFoundError(str(p))
            logs = p.read_text(encoding="utf-8", errors="replace")
            windows = extract_windows(logs)
            games.append({
                "pod": g["pod"], "seed": g["seed"], "rotation": g["rotation"],
                "policy": g["policy"], "status": g["status"],
                "brimaz_win": g.get("brimaz_win"),
                "development_proposals": logs.count("BRIMAZ_DEVELOPMENT:"),
                "sacrifice_planner_proposals": logs.count("BRIMAZ_PLANNER:"),
                "decision_windows": windows,
            })
    if not games:
        raise ValueError("No game manifests")
    return {
        "summary": summarize(games), "games": games,
        "caveats": [
            "Only the first encountered empty-stack second-main-phase decision per turn is recorded.",
            "Candidate tokens, outlet permanents and main-action-list membership do not prove legal, payable or beneficial activations.",
            "Forge mana abilities may be intentionally absent from the main stack-action candidate list.",
            "No gameplay improvement is claimed: V7 is a V6 strategy plus observer instrumentation."
        ],
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    out = pathlib.Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    report = inspect(pathlib.Path(a.input))
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("BRIMAZ_V7_WINDOW_SUMMARY", json.dumps(report["summary"], ensure_ascii=False))
