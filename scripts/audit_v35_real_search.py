#!/usr/bin/env python3
"""Separate actual V35 stock-Forge-approved decisions from candidate forecasts.

Only authentic paired Forge 2.0.15 JVM transcripts with canonical provenance
may be supplied; parser assertions with fixtures are synthetic unit tests.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

APPROVED=re.compile(
    r"^FOUR_AI_V35_STOCK_APPROVED player=Ai\((?P<seat>[1-4])\)-"
    r"(?P<deck>.*?) turn=(?P<turn>\d+) card=(?P<card>.*?) "
    r"rejectedEarlier=(?P<rejected>\d+) genuineForgeAIDecision=true$",re.M)
WINDOW=re.compile(
    r"^FOUR_AI_V35_WINDOW player=Ai\((?P<seat>[1-4])\)-"
    r"(?P<deck>.*?) turn=(?P<turn>\d+) rawAbilities=(?P<raw>\d+) "
    r"eligiblePerms=(?P<eligible>\d+) estimatedMana=(?P<mana>\d+) "
    r"ranked=(?P<ranked>\d+) best=(?P<best>.*?) "
    r"plannedSecond=(?P<second>.*?) plannedNext=(?P<next>.*?) "
    r"searchNodes=(?P<nodes>\d+) immediateForgeApprovalPending=true$",re.M)
REJECTED=re.compile(
    r"^FOUR_AI_V35_STOCK_REJECTED player=Ai\((?P<seat>[1-4])\)-"
    r"(?P<deck>.*?) turn=(?P<turn>\d+) proposed=(?P<count>\d+) "
    r"stockFallback=true$",re.M)

def audit(report):
    if report.get("type")!="Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B":
        raise ValueError("Not the genuine Forge A/B format")
    ref=report.get("reference_provenance",{})
    exp=report.get("experiment_provenance",{})
    if ref.get("policy")!="v17_strict" or exp.get("policy")!="v35_strategy":
        raise ValueError("V35 audit requires unchanged v17_strict vs v35_strategy")
    if ref.get("canonical_seven_deck_sha256")!=exp.get("canonical_seven_deck_sha256"):
        raise ValueError("Deck identities changed between campaigns")
    pairs=report.get("pairs",[])
    if len(pairs)!=report.get("real_process_pairs") or not pairs:
        raise ValueError("Missing genuine matched JVMs")
    seat=Counter(); role=Counter(); by_pod=Counter(); per_arm=Counter()
    statuses=Counter(); changes=0; windows=0; proposed=0; fallback=0
    samples=[]
    for pair in pairs:
        a=pair["reference"];b=pair["experiment"]
        x=Path(a["log"]).read_text(encoding="utf-8",errors="replace")
        y=Path(b["log"]).read_text(encoding="utf-8",errors="replace")
        if "Ai(1)-" not in x or "Ai(4)-" not in y or "Turn: " not in y:
            raise ValueError("Missing four-seat real-game transcript markers")
        if APPROVED.search(x) or WINDOW.search(x) or REJECTED.search(x):
            raise ValueError("V35 code touched control arm")
        candidates=list(WINDOW.finditer(y))
        approvals=list(APPROVED.finditer(y))
        rejects=list(REJECTED.finditer(y))
        windows+=len(candidates)
        proposed+=sum(int(m["ranked"]) for m in candidates)
        fallback+=sum(int(m["count"]) for m in rejects)
        for m in approvals:
            index=int(m["seat"])
            if int(m["turn"])<1 or int(m["rejected"])>3:
                raise ValueError("Invalid V35 original Forge approval marker")
            if not candidates:
                raise ValueError("Approval without a V35 search window")
            seat[index]+=1
            by_pod[b["pod"]]+=1
            if len(samples)<25:samples.append({
                **m.groupdict(),"pod":b["pod"],"rotation":b["rotation"]})
        statuses[(a["status"],b["status"])]+=1
        changes+=int(a["event_sha256"]!=b["event_sha256"])
    if proposed==0 and seat:
        raise ValueError("Approved action without any ranked proposal")
    return {
      "real_forge_jvms":report["real_forge_jvm_processes"],
      "real_game_pairs":len(pairs),
      "naturally_finished_both_arms":report["both_natural_pairs"],
      "pairs_censored_or_faulted":report["pairs_with_any_censor_or_fault"],
      "natural_pairs_different_winners":report["natural_pairs_with_different_winner"],
      "different_game_event_sequences":changes,
      "diagnostic_windows_logged":windows,
      "candidate_slots_ranked":proposed,
      "stock_forge_rejections_before_fallback":fallback,
      "actual_stock_forge_approved_strategic_actions_not_cast_proof":sum(seat.values()),
      "approved_actions_by_seat":dict(sorted(seat.items())),
      "approved_actions_by_pod":dict(by_pod),
      "statuses":{str(k):v for k,v in statuses.items()},
      "approved_examples":samples,
      "limits":[
        "V35_WINDOW is only a bounded abstract search proposal",
        "V35_STOCK_APPROVED means original Forge AI agreed to play; it does not independently prove actual spell resolution",
        "Natural wins do not prove better strategy or statistically significant win rate",
        "Same-seed games are not guaranteed deterministic; censures are not losses",
      ],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--min-approved",type=int,default=0)
    args=ap.parse_args()
    if args.min_approved<0:ap.error("min-approved must be >=0")
    r=audit(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_V35_REAL_FORGE_STRATEGIC_AUDIT",json.dumps({
        k:r[k] for k in ("real_forge_jvms","real_game_pairs",
           "naturally_finished_both_arms","pairs_censored_or_faulted",
           "diagnostic_windows_logged","candidate_slots_ranked",
           "actual_stock_forge_approved_strategic_actions_not_cast_proof",
           "approved_actions_by_seat","different_game_event_sequences")
        }),flush=True)
    if r["actual_stock_forge_approved_strategic_actions_not_cast_proof"]<args.min_approved:
        raise SystemExit("V35_FAIL_NO_DEMONSTRATED_STOCK_FORGE_APPROVED_INTERVENTIONS")

if __name__=="__main__":main()
