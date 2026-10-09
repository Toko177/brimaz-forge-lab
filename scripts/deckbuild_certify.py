#!/usr/bin/env python3
"""Independent general Commander A/B certification of real Forge transcripts.

Natural win evidence, Scryfall deck legality, candidate identity and warning-
free AI quality are separate gates. Reuses the strict four-player Magic outcome
auditor; never promotes timeout-censored games to wins.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from forge_result_evidence import verify_result_evidence,inspect_ai_quality_signatures,describe_outcome_modes

FATAL=("Exception in thread","java.lang.NullPointerException","java.lang.IllegalStateException",
       "StackOverflowError","OutOfMemoryError","Illegal move","Simulation: Couldn't play land")
RESULT=re.compile(r"Game Result: Game\s+\d+\s+ended in\s+(\d+)\s*ms\.\s*Ai\((\d+)\)-(.+?) has won!")
START=re.compile(r"^Ai\(1\)-(.+?) vs Ai\(2\)-(.+?) vs Ai\(3\)-(.+?) vs Ai\(4\)-(.+?) - one game of Commander seed",re.M)


def certify_one(g,raw,legality,deck_manifest):
    issues=[]
    seat_names=g.get("seats",[])
    arm=g.get("arm")
    expected=deck_manifest.get("decks",{}).get(arm,{})
    candidate=expected.get("label")
    if candidate not in ("Deck_Reference","Deck_Candidate"):
        issues.append("Candidate manifest is absent or not A/B")
    if g.get("candidate_deck")!=candidate or g.get("candidate_deck_sha256")!=expected.get("forge_sha256"):
        issues.append("Candidate name or SHA256 mismatch")
    if len(seat_names)!=4 or len(set(seat_names))!=4:
        issues.append("Requires four different deck identities")
    elif candidate not in seat_names or g.get("candidate_seat")!=seat_names.index(candidate)+1:
        issues.append("Candidate seat does not match four-player manifest")
    if g.get("status")=="complete" and g.get("winner_seat") is not None:
        if g["candidate_win"] is not (g["winner_seat"]==g.get("candidate_seat")):
            issues.append("Candidate win flag inconsistent with winner seat")
    elif g.get("candidate_win") is not None:
        issues.append("Censored game claims candidate win flag")
    for name in seat_names:
        report=legality.get(name)
        if not report or not report.get("structurally_and_legality_valid"):
            issues.append("No valid Scryfall Commander legality audit for "+name)
    if not raw:
        issues.append("Missing complete raw Forge transcript")
    else:
        results=RESULT.findall(raw)
        if len(results)!=1:
            issues.append(f"Expected one Forge result line, got {len(results)}")
        elif (g.get("winner_seat")!=int(results[0][1]) or
              not (1<=int(results[0][1])<=4) or
              g.get("winner_deck")!=seat_names[int(results[0][1])-1]):
            issues.append("Winner seat or deck differs from four-player Forge result")
        if not START.search(raw):
            issues.append("Missing Forge four-player Commander start")
        if not re.search(r"^Turn: Turn \d+",raw,re.M):
            issues.append("Missing real turn sequence")
        for fatal in FATAL:
            if fatal in raw:issues.append("Fatal Forge signature: "+fatal)
        issues+=verify_result_evidence(raw,g,seat_names)
    if g.get("status")!="complete":issues.append("Game is not naturally complete")
    if g.get("process_exit")!=0:issues.append("Forge returncode not zero")
    digest=hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw else None
    if digest!=g.get("log_sha256"):
        issues.append("Real raw Forge transcript hash differs from runner manifest")
    quality=inspect_ai_quality_signatures(raw)
    legal=all(name in legality and legality[name].get("structurally_and_legality_valid") for name in seat_names)
    return {
        "arm":arm,"candidate_deck":candidate,"candidate_sha256":g.get("candidate_deck_sha256"),
        "pod":g.get("pod"),"rotation":g.get("rotation"),"repeat":g.get("repeat"),
        "seed":g.get("seed"),"policy":g.get("policy"),"candidate_seat":g.get("candidate_seat"),
        "status":g.get("status"),"winner_deck":g.get("winner_deck"),
        "candidate_win":g.get("candidate_win"),
        "natural_verified":not issues,"legal_deck_gate":legal,
        "ai_quality_signatures":quality,"ai_warning_free":not any(quality.values()),
        "game_milliseconds":g.get("game_milliseconds"),"wall_seconds":g.get("wall_seconds"),
        "transcript_sha256":digest,
        "outcome_modes":describe_outcome_modes(raw),
        "rejection_reasons":issues,
        "limitation":"Natural legal outcomes do not establish expert AI decisions or exact reproducibility.",
    }


def certify_tree(root,legality,manifest):
    games=[]
    for path in sorted(Path(root).rglob("games.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            transcript=path.parent/Path(row["log"]).name
            if not transcript.is_file():
                raise FileNotFoundError(transcript)
            games.append(certify_one(row,transcript.read_text(encoding="utf-8",errors="replace"),
                                     legality,manifest))
    if not games:
        raise ValueError("No real Forge Commander game manifests")
    return {"summary":{
        "scheduled":len(games),
        "certified":sum(g["natural_verified"] for g in games),
        "excluded":sum(not g["natural_verified"] for g in games),
        "reference_certified":sum(g["arm"]=="reference" and g["natural_verified"] for g in games),
        "candidate_certified":sum(g["arm"]=="candidate" and g["natural_verified"] for g in games),
        "certified_warning_free":sum(g["natural_verified"] and g["ai_warning_free"] for g in games),
        "quality_signatures":dict(Counter({k:sum(g["ai_quality_signatures"][k] for g in games) for k in (
            "evaluation_timeouts","invalid_attack_fallbacks","incubate_handler_warnings","decision_thread_timeout_samples")})),
        "reject_causes":dict(Counter(e for g in games for e in g["rejection_reasons"])),
    }, "games":games}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--legality",type=Path,required=True)
    p.add_argument("--candidate-manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=json.loads(a.legality.read_text(encoding="utf-8"))
    legal={Path(item["file"]).stem:item for item in report["reports"]}
    manifest=json.loads(a.candidate_manifest.read_text(encoding="utf-8"))
    result=certify_tree(a.input,legal,manifest)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("DECKBUILD_CERTIFIED_RESULTS",json.dumps(result["summary"],ensure_ascii=False),flush=True)
    # Empty or zero-natural results are not good enough for deckbuilding.
    if result["summary"]["certified"]==0:sys.exit(2)


if __name__=="__main__":
    main()
