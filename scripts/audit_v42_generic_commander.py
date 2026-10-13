#!/usr/bin/env python3
"""Validate real four-seat V42 policy execution from paired Forge transcripts.

This tool NEVER simulates outcomes. A Forge approval is not a resolved spell.
A same-seed A/B pair is not an identical RNG trajectory or independent winrate
sample. Missing or contaminated experimental evidence fails closed.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from forge_seat_identity import resolve_ai_player

WINDOW=re.compile(
    r"^FOUR_AI_V42_WINDOW player=(.*?) turn=(\d+) options=(\d+) "
    r"ranked=(\d+) margin=(\d+) pressure=(true|false) "
    r"reason=([a-z_]+) nativeForgeApprovalPending=true$", re.M)
APPROVED=re.compile(
    r"^FOUR_AI_V42_STOCK_APPROVED player=(.*?) turn=(\d+) card=(.*?) "
    r"rejectedEarlier=(\d+) nativeForgeAIDecision=true notResolvedYet=true$",re.M)
REJECTED=re.compile(r"^FOUR_AI_V42_STOCK_REJECTED player=(.*?) rejected=(\d+) "
                    r"fallback=originalForge$",re.M)

def _read(path):
    p=Path(path)
    if not p.is_file():raise ValueError("Missing recorded Forge game.log: "+str(p))
    return p.read_text(encoding="utf-8",errors="replace")

def audit(report, *, min_distinct_decks=3, require_approvals=True):
    if report.get("type")!="Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B":
        raise ValueError("Not a genuine Forge 2.0.15 paired comparison")
    ref=report.get("reference_provenance",{})
    exp=report.get("experiment_provenance",{})
    if ref.get("policy")!="v37_stock_control" or exp.get("policy") not in (
            "v42_commander_general","v43_commander_single_seat"):
        raise ValueError("V42/V43 requires V37 original-decision Forge control")
    isolated=exp["policy"]=="v43_commander_single_seat"
    if not ref.get("patches") or ref.get("patches")!=exp.get("patches"):
        raise ValueError("Asymmetric Java patches: cannot compare decisions")
    if ref.get("canonical_seven_deck_sha256")!=exp.get("canonical_seven_deck_sha256"):
        raise ValueError("Canonical decks changed across arms")
    for field in ("roster_version","active_pods"):
        if ref.get(field)!=exp.get(field):
            raise ValueError("Reference/experiment pod roster mismatch: "+field)
    ro=ref.get("java_tool_options","")
    eo=exp.get("java_tool_options","")
    if "commander.v42GeneralPolicy=true" not in eo or "brimaz.v37ControlledDuel=true" not in eo:
        raise ValueError("V42 opt-in or shared controlled baseline missing")
    if ("commander.v42GeneralPolicy=true" in ro
            or "commander.v43TargetSeat=" in ro
            or "brimaz.v37Challenger=true" in eo
            or ("commander.v43TargetSeat=1" in eo)!=isolated
            or (not isolated and "commander.v43TargetSeat=" in eo)):
        raise ValueError("Experiment/control policy contamination or wrong target seat")
    pairs=report.get("pairs",[])
    if not pairs or len(pairs)!=report.get("real_process_pairs"):
        raise ValueError("Missing paired real JVM records")
    deck_dir=Path(__file__).resolve().parents[1]/"forge_decks"
    windows=Counter(); approvals=Counter(); refusals=Counter(); reasons=Counter()
    statuses=Counter(); seen_keys=set(); natural=[]
    by_pod={}
    candidate_only_wins=0; reference_only_wins=0; both_candidate_wins=0
    distinct_target_decks=set()
    for pair in pairs:
        a,b=pair["reference"],pair["experiment"]
        pod=pair["pod"]
        segment=by_pod.setdefault(pod,{"pairs":0,"natural":0,"censored":0,
             "candidate_only_wins":0,"reference_only_wins":0,
             "both_candidate_wins":0})
        segment["pairs"]+=1
        if a.get("seats")!=b.get("seats") or len(a.get("seats",[]))!=4:
            raise ValueError("Four identical seats required in both Forge arms")
        if len(set(a["seats"]))!=4:
            raise ValueError("Duplicate Commander seat")
        key=(pair["pod"],pair["rotation"],pair["repeat"],pair["seed"])
        if key in seen_keys:raise ValueError("Duplicate seed/rotation/pod key")
        seen_keys.add(key)
        raw_ref=_read(a["log"]);raw_exp=_read(b["log"])
        if WINDOW.search(raw_ref) or APPROVED.search(raw_ref) or REJECTED.search(raw_ref):
            raise ValueError("Reference controller executed V42 experimental code")
        if isolated:
            distinct_target_decks.add(b["seats"][0])
        for player,turn,options,ranked,margin,pressure,reason in WINDOW.findall(raw_exp):
            deck=resolve_ai_player(player,b["seats"],deck_dir)
            if isolated and deck!=b["seats"][0]:
                raise ValueError("V43 touched a control seat "+deck)
            if int(options)<2 or int(ranked)>3 or int(ranked)>int(options):
                raise ValueError("Incoherent V42 public decision window")
            windows[deck]+=1
            reasons[reason]+=1
        for player,turn,card,rejected in APPROVED.findall(raw_exp):
            deck=resolve_ai_player(player,b["seats"],deck_dir)
            if isolated and deck!=b["seats"][0]:
                raise ValueError("V43 approval on non-target reference seat")
            approvals[deck]+=1
        for player,count in REJECTED.findall(raw_exp):
            deck=resolve_ai_player(player,b["seats"],deck_dir)
            if isolated and deck!=b["seats"][0]:
                raise ValueError("V43 rejection on non-target reference seat")
            refusals[deck]+=int(count)
        statuses[(a["status"],b["status"])]+=1
        if a["status"]=="complete" and b["status"]=="complete":
            segment["natural"]+=1
            natural.append((a.get("winner"),b.get("winner")))
            if isolated:
                target=b["seats"][0]
                old_won=a.get("winner")==target
                new_won=b.get("winner")==target
                candidate_only_wins+=new_won and not old_won
                reference_only_wins+=old_won and not new_won
                both_candidate_wins+=old_won and new_won
                segment["candidate_only_wins"]+=bool(new_won and not old_won)
                segment["reference_only_wins"]+=bool(old_won and not new_won)
                segment["both_candidate_wins"]+=bool(old_won and new_won)
        else:
            segment["censored"]+=1
    if isolated and len(distinct_target_decks)<min_distinct_decks:
        raise ValueError("Not enough rotated target decks for V43 head-to-head")
    if len(windows)<min_distinct_decks:
        raise ValueError("Generic AI did not observe enough distinct deck controllers")
    if require_approvals and not sum(approvals.values()):
        raise ValueError("V42 made no native-Forge-approved action: no proven behavior")
    active=exp.get("active_pods") or {}
    shared=[]
    if "aristo" in active and "artifact" in active:
        shared=sorted((set(active["aristo"]) & set(active["artifact"])) -
                      {"Brimaz_V3"})
    return {
        "roster_version":exp.get("roster_version"),
        "shared_opponents_across_pods":shared,
        "by_pod":dict(sorted(by_pod.items())),
        "evidence":"Actual Forge 2.0.15 paired four-seat logs, not simulated",
        "real_process_pairs":len(pairs),
        "natural_pairs":len(natural),
        "winner_changed_if_both_natural":sum(a!=b for a,b in natural),
        "censored_or_faulted_pairs":len(pairs)-len(natural),
        "policy":exp["policy"],
        "head_to_head_one_challenger_vs_three_controls":isolated,
        "target_seat_number":1 if isolated else None,
        "distinct_rotated_target_decks":sorted(distinct_target_decks),
        "natural_candidate_only_wins":candidate_only_wins if isolated else None,
        "natural_reference_only_wins":reference_only_wins if isolated else None,
        "natural_both_candidate_win_pairs":both_candidate_wins if isolated else None,
        "four_seat_observed_distinct_decks":sorted(windows),
        "windows_by_deck":dict(sorted(windows.items())),
        "approved_not_resolved_by_deck":dict(sorted(approvals.items())),
        "stock_rejections_by_deck":dict(sorted(refusals.items())),
        "decision_reasons":dict(sorted(reasons.items())),
        "status_pairs":{"/".join(k):v for k,v in statuses.items()},
        "skill_gain_proven":False,
        "rules_oracle_independently_certified":False,
        "caveat":"Forge approvals are not spell resolutions. Same seeds can diverge; "
                 "sample size and independent pods determine possible future claims."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--min-distinct-decks",type=int,default=3)
    p.add_argument("--allow-zero-approvals",action="store_true")
    args=p.parse_args()
    result=audit(json.loads(args.input.read_text(encoding="utf-8")),
                 min_distinct_decks=args.min_distinct_decks,
                 require_approvals=not args.allow_zero_approvals)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("V42_REAL_GENERIC_COMMANDER_AUDIT",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
