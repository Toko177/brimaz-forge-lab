#!/usr/bin/env python3
"""Evidence gate for Forge AI Commander results.

Labels are intentionally conservative:
- DECKS_LEGAL = Scryfall says Commander legal / color identity / quantity.
- ENGINE_NATURAL = Forge has one non-timed winner, zero fatal exceptions,
  four distinct AI seats, and consistent result.
- NOT a claim that every Forge card interaction matches MTG Oracle perfectly.
- NOT a claim that an AI makes expert-level choices.

Neither a truncated game nor absent/full data may produce a certified win.
"""
import argparse,collections,hashlib,json,pathlib,re,sys
from forge_result_evidence import verify_result_evidence, inspect_ai_quality_signatures, describe_outcome_modes

p=argparse.ArgumentParser()
p.add_argument("--input",required=True)
p.add_argument("--legality",required=True)
p.add_argument("--out",default="results/certification")
args=p.parse_args()
root=pathlib.Path(args.input)
target=pathlib.Path(args.out)
target.mkdir(parents=True,exist_ok=True)
reports=json.loads(pathlib.Path(args.legality).read_text(encoding="utf-8"))["reports"]
legal={pathlib.Path(item["file"]).stem:item for item in reports}
errors=[];games=[]
fatal_patterns=["Exception in thread","java.lang.NullPointerException","java.lang.IllegalStateException",
                "StackOverflowError","OutOfMemoryError","Illegal move","Simulation: Couldn't play land"]
for record_path in sorted(root.rglob("games.json")):
    for g in json.loads(record_path.read_text(encoding="utf-8")):
        seats=[pathlib.Path(n).stem for n in g["seats"]]
        local=[]
        if len(seats)!=4 or len(set(seats))!=4:
            local.append("Expected four distinct AI deck seats")
        for seat in seats:
            if seat not in legal:local.append("No Scryfall legal deck manifest for "+seat)
            elif not legal[seat].get("structurally_and_legality_valid",False):
                local.append("Scryfall rejected deck "+seat)
        log=record_path.parent/pathlib.Path(g["log"]).name
        if not log.exists():local.append("Missing raw Forge transcript")
        raw=log.read_text(encoding="utf-8",errors="replace") if log.exists() else ""
        if raw:
            wins=re.findall(r"Game Result: Game\s+\d+\s+ended in\s+(\d+)\s*ms\.\s*Ai\((\d+)\)-(.+?) has won!",raw)
            if len(wins)!=1:local.append(f"Found {len(wins)} winner log entries, expected exactly 1")
            elif (int(wins[0][1]) != g.get("winner_seat")
                  or g.get("winner_deck") != seats[int(wins[0][1])-1]):
                local.append("Winner in raw Forge transcript differs from summary")
            start=re.search(r"^Ai\(1\)-(.+?) vs Ai\(2\)-(.+?) vs Ai\(3\)-(.+?) vs Ai\(4\)-(.+?) - one game of Commander seed",raw,re.M)
            if not start:local.append("No 4-player Commander Forge match declaration")
            if not re.search(r"^Turn: Turn\s+\d+",raw,re.M):
                local.append("Missing numbered in-game turns")
            for pattern in fatal_patterns:
                if pattern in raw:local.append("Fatal/problem signature: "+pattern)
            if "Stopping slow match as draw" in raw:
                local.append("Clock-forced draw")
            if "No AI assigned for API: Incubate" in raw:
                # This is a real warning about AI quality, not a rule error.
                pass
            # Full four-seat evidence and per-game clock cross-check.
            # This supersedes the old hard-coded 360s-only 357500ms threshold.
            local.extend(verify_result_evidence(raw, g, seats))
        if g.get("status")!="complete":local.append("Game was not naturally complete: "+g.get("status",""))
        if g.get("process_exit")!=0:local.append("Forge subprocess exit was nonzero")
        if g.get("brimaz_win") is True and g.get("winner_deck")!="Brimaz_V3":
            local.append("Brimaz claimed win but different winning deck")
        quality=inspect_ai_quality_signatures(raw)
        # Separate rules/outcome validity from AI quality. No source proves a
        # warning-free game has expert AI, but warnings are objective red flags.
        warning_free_ai=all(v==0 for v in quality.values())
        report={
          "pod":g.get("pod"),"policy":g.get("policy"),"seed":g.get("seed"),
          "seat":g.get("brimaz_seat"),"winner_deck":g.get("winner_deck"),
          "brimaz_win":g.get("brimaz_win"),"status":g.get("status"),
          "legal_deck_gate":all(n in legal and legal[n]["structurally_and_legality_valid"] for n in seats),
          "transcript_sha256":hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw else None,
          "engine_natural_and_consistent":not local,
          "rejection_reasons":local,
          "ai_quality_signatures":quality,
          "ai_warning_free":warning_free_ai,
          "outcome_modes":describe_outcome_modes(raw),
          "victory_causality_verified":False,
          "caveat":"This audit verifies raw Forge outcomes and Scryfall legality, not a formal MTG rules proof. The Forge JAR may include disclosed bugfix or policy patches."
        }
        games.append(report)
        print("CERTIFIED_GAME" if not local else "REJECTED_GAME",json.dumps(report,ensure_ascii=False),flush=True)
summary={
    "checked_games":len(games),
    "games_with_ai_eval_timeouts":sum(x["ai_quality_signatures"]["evaluation_timeouts"]>0 for x in games),
    "total_ai_eval_timeouts":sum(x["ai_quality_signatures"]["evaluation_timeouts"] for x in games),
    "games_with_invalid_ai_attack_fallbacks":sum(x["ai_quality_signatures"]["invalid_attack_fallbacks"]>0 for x in games),
    "accepted_natural_games":sum(x["engine_natural_and_consistent"] for x in games),
    "accepted_brimaz_wins":sum(x["engine_natural_and_consistent"] and x["brimaz_win"] is True for x in games),
    "accepted_warning_free_natural_games":sum(x["engine_natural_and_consistent"] and x["ai_warning_free"] for x in games),
    "accepted_warning_free_brimaz_wins":sum(x["engine_natural_and_consistent"] and x["ai_warning_free"] and x["brimaz_win"] is True for x in games),
    "excluded_games":sum(not x["engine_natural_and_consistent"] for x in games),
    "acceptance_standard":"Scryfall legal deck manifest + Forge 2.0.15 (original or disclosed patched build) + four seats + a natural winner + raw log hash. Audit does not prove full Oracle rule fidelity.",
}
(target/"certificate.json").write_text(json.dumps({"summary":summary,"games":games},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("GAME_CERTIFICATION_SUMMARY",json.dumps(summary,ensure_ascii=False),flush=True)
if not games:sys.exit(3)
# Censored matches are expected and excluded; fail only if every game is invalid.
if summary["accepted_natural_games"]==0:sys.exit(2)
