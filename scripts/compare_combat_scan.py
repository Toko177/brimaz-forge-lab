#!/usr/bin/env python3
"""Compare paired four-seat Forge combat scan pilots, without inventing wins.

Run within one matrix job after three actual Forge subprocess experiments:
- control: original FCollection trigger scan
- optimized: nested traversal
- shadow: optimized traversal checked against original in each evaluation

Only report a speed ratio if both games have identical turn/phase/stack
transcripts and complete naturally. Excluded/censored runs are disclosed.
"""
import argparse
import hashlib
import json
import pathlib
import re

p = argparse.ArgumentParser()
p.add_argument("--pod", choices=["aristo", "artifact"], required=True)
p.add_argument("--out", default="results/combat_scan/differential.json")
args = p.parse_args()
root = pathlib.Path("results/batch") / args.pod

def load(tag):
    group = root / tag
    matches = json.loads((group / "games.json").read_text(encoding="utf-8"))
    if len(matches) != 1:
        raise ValueError(f"{tag}: expected one real Forge match, got {len(matches)}")
    entry = matches[0]
    log = pathlib.Path(entry["log"]).read_text(encoding="utf-8", errors="replace")
    # Excludes host diagnostics and milliseconds, keeps actual observed game
    # events. Equal streams are evidence of matching observable decisions,
    # not formal proof of complete Oracle equivalence.
    events = [
        line for line in log.splitlines()
        if line.startswith(("Turn: ", "Phase: ", "Add To Stack: ",
                            "Game Outcome: ", "Game Result: "))
        and not line.startswith(("Game Result: ", "Game Outcome: Match Duration "))
    ]
    # Exclude measured elapsed time: a real speedup changes this value
    # without changing any decision, play, phase or rule outcome.
    signature = hashlib.sha256("\n".join(events).encode("utf-8")).hexdigest()
    return entry, log, signature, len(events)

control, control_log, control_sig, control_events = load("control-scan")
fast, fast_log, fast_sig, fast_events = load("fast-scan")
verify, verify_log, verify_sig, verify_events = load("verified-scan")
for x in (control, fast, verify):
    if x["pod"] != args.pod:
        raise ValueError("Pod mismatch")
    if x["seed"] != control["seed"] or x["seats"] != control["seats"]:
        raise ValueError("Paired seeds/seats changed")
mismatch = "COMBAT_TRIGGER_SCAN_MISMATCH" in verify_log
checks = re.findall(r"COMBAT_TRIGGER_SHADOW_CHECKED\s+(\d+)", verify_log)
shadow_checks = int(checks[-1]) if checks else 0
identical = control_sig == fast_sig
speed_ok = identical and all(x["status"] == "complete" for x in (control, fast))
ratio = (round(control["wall_seconds"] / fast["wall_seconds"], 4)
         if speed_ok and fast["wall_seconds"] else None)
report = {
    "pod": args.pod, "rotation": control["rotation"], "seed": control["seed"],
    "all_four_ai_seats_share_patched_ComputerUtilCombat": True,
    "shadow_test_mismatch": mismatch,
    "shadow_checks_performed": shadow_checks,
    "observed_game_events_equal_control_fast": identical,
    "events_control": control_events, "events_fast": fast_events,
    "event_hash_control": control_sig, "event_hash_fast": fast_sig,
    "speedup_on_identical_complete_games_only": ratio,
    "runs": [
        {"mode": mode, "status": x["status"], "winner_deck": x["winner_deck"],
         "game_milliseconds": x["game_milliseconds"],
         "wall_seconds": x["wall_seconds"], "events": count}
        for mode, x, count in (
            ("reference", control, control_events),
            ("direct", fast, fast_events),
            ("shadow-check", verify, verify_events))
    ],
    "limits": [
        "The shadow check compares the booleans of both scanning strategies "
        "on the same attacker/blocker state; it does not validate Oracle rules.",
        "No valid speedup claim unless both naturally complete and the "
        "observable game streams match.",
        "Different outcomes after a timeout or nonmatching event streams "
        "are not treated as equivalent or as win-rate evidence.",
    ],
}
out = pathlib.Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("COMBAT_SCAN_DIFFERENTIAL", json.dumps(report, ensure_ascii=False), flush=True)
if mismatch:
    raise SystemExit("Direct scan disagreed with original reference scan")
if shadow_checks <= 0:
    raise SystemExit("No verified combat trigger evaluations occurred; refuse empty equivalence claim")
if verify["status"] in ("engine_fault", "engine_failed", "process_timeout"):
    raise SystemExit("Shadow verification failed or timed out; inspect logs")
