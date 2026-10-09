#!/usr/bin/env python3
"""Run a four-AI Commander smoke test; distinguish a clock cutoff from a valid win."""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument("--deck", default="decks/Brimaz_V3.txt")
p.add_argument("--jar", required=True)
p.add_argument("--games", type=int, default=1)
p.add_argument("--opponents", nargs="*", default=[], help="Three opponent deck filenames without .dck")
p.add_argument("--clock", type=int, default=360,
               help="Forge per-game clock limit in seconds")
p.add_argument("--timeout", type=int, default=450,
               help="Process hard timeout in seconds")
args = p.parse_args()
if args.timeout <= args.clock:
    p.error("--timeout must exceed --clock")

lines = pathlib.Path(args.deck).read_text(encoding="utf-8").splitlines()
cards = []
for line in lines:
    if not line.strip():
        continue
    m = re.fullmatch(r"(\d+)\s+(.+)", line.strip())
    if not m:
        raise ValueError("Bad deck line: " + line)
    cards.append((int(m.group(1)), m.group(2)))
if sum(q for q, _ in cards) != 100:
    raise ValueError("Exactly 100 cards required")
if sum(q for q, n in cards if n == "Brimaz, Blight of Oreskos") != 1:
    raise ValueError("Exactly one Brimaz commander required")
out = pathlib.Path("forge_decks").resolve()
out.mkdir(exist_ok=True)
dck = out / "Brimaz_V3.dck"
dck.write_text("[metadata]\nName=Brimaz V3\n[Main]\n"
               + "".join(f"{q} {n}\n" for q, n in cards if n != "Brimaz, Blight of Oreskos")
               + "[Commander]\n1 Brimaz, Blight of Oreskos\n", encoding="utf-8")
jar = pathlib.Path(args.jar).resolve()
if args.opponents and len(args.opponents) != 3:
    p.error("--opponents requires exactly three deck names")
seats = ["Brimaz_V3.dck"] + ([name + ".dck" for name in args.opponents] if args.opponents else ["Brimaz_V3.dck"] * 3)
for name in seats:
    if not (out / name).is_file():
        raise FileNotFoundError(out / name)
cmd = ["java", "-Xmx4g", "-jar", str(jar), "sim", "-d",
       *seats,
       "-D", str(out), "-f", "Commander", "-n", str(args.games),
       "-c", str(args.clock)]
results = pathlib.Path("results")
results.mkdir(exist_ok=True)
print("COMMAND:", " ".join(cmd), flush=True)
start = time.monotonic()
returncode = None
process_timed_out = False
try:
    proc = subprocess.run(cmd, cwd=jar.parent, capture_output=True,
                          text=True, errors="replace", timeout=args.timeout)
    stdout, stderr = proc.stdout, proc.stderr
    returncode = proc.returncode
except subprocess.TimeoutExpired as exc:
    process_timed_out = True
    stdout = (exc.stdout or b"").decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
    stderr = (exc.stderr or b"").decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")

raw = stdout + "\n[STDERR]\n" + stderr
(results / "forge-smoke.log").write_text(raw, encoding="utf-8")
# A normal process exit does NOT prove that a winner emerged naturally.
# Forge emits a winner even when its -c simulation clock is reached.
game_results = re.findall(r"Game Result: Game\s+\d+\s+ended in\s+(\d+)\s*ms\.\s*(.*?)\s+has won!", stdout)
outcomes = re.findall(r"^Game Outcome: (.*)$", stdout, re.M)
clock_censored = any(int(ms) >= 1000 * args.clock - 2500 for ms, _ in game_results)
all_players_won = sum("has won because all opponents have lost" in t for t in outcomes) > 1
ai_warnings = sorted(set(re.findall(r"^No AI assigned for API: (.+)$", stderr, re.M)))
if process_timed_out:
    status = "process_timeout"
elif returncode != 0:
    status = "engine_failed"
elif clock_censored or all_players_won:
    status = "clock_censored"
elif len(game_results) != args.games:
    status = "missing_game_result"
else:
    status = "complete"
summary = {
    "status": status,
    "forge_returncode": returncode,
    "elapsed_seconds": round(time.monotonic() - start, 2),
    "clock_seconds": args.clock,
    "requested_games": args.games,
    "seats": seats,
    "games_with_result_lines": len(game_results),
    "clock_censored": clock_censored,
    "multiple_winner_outcomes": all_players_won,
    "results": [{"milliseconds": int(ms), "winner": name} for ms, name in game_results],
    "ai_warnings": ai_warnings,
    "commander_casts": len(re.findall(r"cast Brimaz, Blight of Oreskos", stdout)),
    "brimaz_cast_triggers": len(re.findall(r"triggered Brimaz, Blight of Oreskos", stdout)),
    "incubator_transforms": len(re.findall(r"activated Incubator Token", stdout)),
    "end_step_mentions": len(re.findall(r"Phase: .* End step", stdout)),
    "natural_win_claimed": status == "complete",
}
(results / "smoke.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("RESULT:", json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
sys.exit(0 if status == "complete" else 2)
