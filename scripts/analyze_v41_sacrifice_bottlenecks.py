#!/usr/bin/env python3
"""Read ONLY genuine Forge game logs and identify Brimaz sacrifice bottlenecks.

This is a *forensic* report, never a simulated result or a policy optimizer.
It cannot establish ability resolution just from an AI approval banner.
All counters are linked to an immutable real game log / matching game record.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

PREFIX="FOUR_AI_V41_SAC_WINDOW "
T="true"
VAL=re.compile(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)")
PLAYER=re.compile(r"\bplayer=(.*?)\s+turn=(\d+)\b")

def parse_window(line):
    if PREFIX not in line:return None
    text=line.split(PREFIX,1)[1]
    player=PLAYER.search(text)
    if not player:raise ValueError("V41 window missing exact player/turn")
    facts=dict(VAL.findall(text))
    required=("pilotAuthorized","commanderPresent","alreadyDead",
              "phyrexianCreatureTokens","outletPermanents",
              "listedActualOutletAbilities")
    if not all(k in facts for k in required):
        raise ValueError("Incomplete real Brimaz opportunity window")
    for key in required[:3]:
        if facts[key] not in ("true","false"):
            raise ValueError("Boolean window invariant violated: "+key)
    parsed={"player":player.group(1),"turn":int(player.group(2))}
    parsed.update({k:facts[k]=="true" for k in required[:3]})
    parsed.update({k:int(facts[k]) for k in required[3:]})
    if any(parsed[k]<0 for k in required[3:]):
        raise ValueError("Negative public board count in Forge log")
    return parsed

def bottleneck(w):
    """One primary reason per own-main-phase window; not rules-proof."""
    if not w["pilotAuthorized"]:return "unauthorized_pilot"
    if not w["commanderPresent"]:return "commander_absent"
    if w["alreadyDead"]:return "death_trigger_already_satisfied"
    if not w["phyrexianCreatureTokens"]:return "no_transformed_phyrexian_token"
    if not w["outletPermanents"]:return "no_sacrifice_outlet_permanent"
    if not w["listedActualOutletAbilities"]:return "outlet_ability_not_offered"
    return "candidate_present_requires_cost_and_ai_approval"

def analyze(root:Path):
    if not root.is_dir():raise FileNotFoundError(root)
    records=sorted(root.rglob("result.json"))
    if not records:raise ValueError("No actual recorded Forge JVM games")
    totals=Counter()
    reasons=Counter()
    by_player={}
    game_rows=[]
    for record_path in records:
        rec=json.loads(record_path.read_text(encoding="utf-8"))
        logfile=record_path.parent/"game.log"
        if not logfile.is_file():raise FileNotFoundError(logfile)
        raw=logfile.read_text(encoding="utf-8",errors="replace")
        windows={}
        for line in raw.splitlines():
            w=parse_window(line)
            if w is not None:
                key=(w["player"],w["turn"])
                if key in windows:
                    # Preserve unique turn-level evidence, never double-count
                    # a repeated artificial logging line as a second action.
                    if windows[key]!=w:
                        raise ValueError("Contradictory duplicate V41 window")
                else:
                    windows[key]=w
        approved=raw.count("FOUR_AI_V37_POSITIVE_SAC_FORGE_APPROVED")
        transform=raw.count("FOUR_AI_V38_TRANSFORM_STOCK_APPROVED")
        totals["jvm_games"]+=1
        totals["natural_games"]+=rec.get("status")=="complete"
        totals["invalid_or_censored_games"]+=rec.get("status")!="complete"
        totals["sacrifice_approved_not_resolved"]+=approved
        totals["transform_approved_not_resolved"]+=transform
        totals["distinct_v41_own_main2_windows"]+=len(windows)
        for w in windows.values():
            reason=bottleneck(w)
            reasons[reason]+=1
            p=by_player.setdefault(w["player"],{"windows":0,"bottlenecks":Counter()})
            p["windows"]+=1
            p["bottlenecks"][reason]+=1
        game_rows.append({
            "record":str(record_path.relative_to(root)),
            "status":rec.get("status"),
            "winner":rec.get("winner"),
            "v41_windows":len(windows),
            "forge_sacrifice_approvals_not_resolutions":approved,
            "forge_transform_approvals_not_resolutions":transform,
        })
    return {
        "report_type":"ACTUAL_V41_FORGE_SACRIFICE_BOTTLENECK_AUDIT",
        "source_policy":"Real recorded Forge 2.0.15 four-player JVM games",
        "strength_claim":"NONE: proposals, approvals and windows cannot prove superiority",
        "totals":dict(totals),
        "primary_bottleneck_by_own_turn":dict(reasons),
        "by_pilot":{k:{"windows":v["windows"],
                    "bottlenecks":dict(v["bottlenecks"])}
                    for k,v in sorted(by_player.items())},
        "raw_game_references":game_rows,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=analyze(args.input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("V41_REAL_SACRIFICE_BOTTLENECKS",json.dumps({
        "totals":result["totals"],
        "reasons":result["primary_bottleneck_by_own_turn"]},ensure_ascii=False),flush=True)
    if result["primary_bottleneck_by_own_turn"].get("unauthorized_pilot",0):
        raise SystemExit("V41 forensic gate FAILED: a real AI pilot was unauthorized; "
                         "this is not a valid policy comparison")

if __name__=="__main__":
    main()
