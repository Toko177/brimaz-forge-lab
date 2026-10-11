#!/usr/bin/env python3
"""Separate actual V35 stock-Forge-approved decisions from candidate forecasts.

Only authentic paired Forge 2.0.15 JVM transcripts with canonical provenance
may be supplied; parser assertions with fixtures are synthetic unit tests.
"""
import argparse
from collections import Counter
import json
from math import comb, sqrt
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


TACTICAL_WINDOW=re.compile(
    r"^FOUR_AI_V35_TACTICAL_WINDOW player=Ai\((?P<seat>[1-4])\)-"
    r"(?P<deck>.*?) turn=(?P<turn>\d+) intervention=(?P<type>\w+) "
    r"ownCreatures=(?P<own>\d+) enemyCreatures=(?P<enemy>\d+) "
    r"worstOpponentPower=(?P<power>\d+) life=(?P<life>-?\d+) "
    r"candidateSpells=(?P<candidates>\d+) originalForgeValidationPending=true$",re.M)
TACTICAL_APPROVED=re.compile(
    r"^FOUR_AI_V35_TACTICAL_STOCK_APPROVED player=Ai\((?P<seat>[1-4])\)-"
    r"(?P<deck>.*?) turn=(?P<turn>\d+) card=(?P<card>.*?) "
    r"rejectedEarlier=(?P<rejected>\d+) genuineForgeAIDecision=true$",re.M)
TACTICAL_REJECTED=re.compile(
    r"^FOUR_AI_V35_TACTICAL_STOCK_REJECTED player=Ai\((?P<seat>[1-4])\)-"
    r"(?P<deck>.*?) turn=(?P<turn>\d+) rejected=(?P<count>\d+) "
    r"stockFallback=true$",re.M)

def paired_brimaz_evidence(rows):
    """Exact two-sided discordant-pair sign test; descriptive, never a Magic skill proof."""
    n=len(rows)
    experimental_only=sum(1 for r in rows
                           if r["improved_brimaz_win"] and not r["stock_brimaz_win"])
    original_only=sum(1 for r in rows
                      if r["stock_brimaz_win"] and not r["improved_brimaz_win"])
    discordant=experimental_only+original_only
    pvalue=min(1.0, 2*sum(comb(discordant,i) for i in range(min(
        experimental_only,original_only)+1))/2**discordant) if discordant else 1.0
    ref=sum(r["stock_brimaz_win"] for r in rows)
    exp=sum(r["improved_brimaz_win"] for r in rows)
    def wilson(wins):
        if not n:return None
        z=1.959963984540054
        den=1+z*z/n
        center=(wins/n+z*z/(2*n))/den
        radius=z*sqrt((wins/n)*(1-wins/n)/n+z*z/(4*n*n))/den
        return [round(max(0,center-radius),4),round(min(1,center+radius),4)]
    return {
      "both_natural_pairs":n,
      "brimaz_wins_stock_reference":ref,
      "brimaz_wins_v35":exp,
      "v35_only_brimaz_wins":experimental_only,
      "stock_only_brimaz_wins":original_only,
      "two_sided_p_value_on_discordant_pairs":round(pvalue,6),
      "stock_win_fraction_wilson95":wilson(ref),
      "v35_win_fraction_wilson95":wilson(exp),
      "insufficient_to_claim_general_ai_superiority":True,
      "requires_direct_mixed_policy_matchups_and_many_more_games":True,
    }


def audit(report):
    if report.get("type")!="Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B":
        raise ValueError("Not the genuine Forge A/B format")
    ref=report.get("reference_provenance",{})
    exp=report.get("experiment_provenance",{})
    if ref.get("policy") not in ("v17_strict","forge_stock","forge_stock_compat","v37_stock_control") or exp.get("policy") not in ("v35_strategy","v35_brimaz_duel","v36_brimaz_challenger","v37_brimaz_challenger"):
        raise ValueError("Invalid Forge stock/V17 control or V35 experiment")
    if exp["policy"] in ("v35_brimaz_duel","v36_brimaz_challenger") and ref["policy"]!="v17_strict":
        raise ValueError("Mixed-seat v35_brimaz_duel requires stable identical v17 opponents")
    if exp["policy"]=="v37_brimaz_challenger":
        if ref["policy"]!="v37_stock_control" or ref.get("patches")!=exp.get("patches"):
            raise ValueError("V37 reference and challenger must use identical patched jar")
        refopts=ref.get("java_tool_options","")
        expopts=exp.get("java_tool_options","")
        if ("v37ControlledDuel=true" not in refopts or
            "v37ControlledDuel=true" not in expopts or
            "v37Challenger=true" not in expopts or
            "v35StrategicSearch=true" not in expopts or
            "v36EvidenceGate=true" not in expopts or
            "v35BrimazOnly=true" not in expopts or
            "v37Challenger=true" in refopts or
            "v35StrategicSearch=true" in refopts or
            "fourSeatCombatTarget=true" in refopts+expopts or
            "fourSeatRemovalUrgency=true" in refopts+expopts or
            "fourSeatCounterCritical=true" in refopts+expopts):
            raise ValueError("V37 comparison contaminated by unwanted global AI policies")
    if exp["policy"] in ("v35_brimaz_duel","v36_brimaz_challenger"):
        if ref.get("patches")!=exp.get("patches"):
            raise ValueError("Mixed-seat comparator has different Java patches on opponent seats")
        if ref.get("java_tool_options") is None or exp.get("java_tool_options") is None:
            raise ValueError("Mixed-seat comparison missing JVM property evidence")
        if ("v35BrimazOnly=true" not in exp["java_tool_options"]
            or "v35StrategicSearch=true" not in exp["java_tool_options"]
            or "v35StrategicSearch=false" not in ref["java_tool_options"]
            or (exp["policy"]=="v36_brimaz_challenger"
                and "v36EvidenceGate=true" not in exp["java_tool_options"])
            or "fourSeatRemovalUrgency=true" in exp["java_tool_options"]
            or "fourSeatCounterCritical=true" in exp["java_tool_options"]):
            raise ValueError("V35 Brimaz-only test was contaminated by global strategy flags")
    if ref.get("policy")=="forge_stock_compat":
        if (ref.get("stock_ai_with_shared_charm_engine_hotfix") is not True
            or ref.get("upstream_forge_unmodified") is True
            or ref.get("upstream_byte_identical") is True
            or ref.get("patches")!=["patch_forge_charm_context.py"]
            or not ref.get("original_forge_sha256")):
            raise ValueError("Forge AI + shared Charm compatibility baseline has wrong provenance")
    if ref.get("policy")=="forge_stock":
        if (ref.get("upstream_forge_unmodified") is not True
            or ref.get("upstream_byte_identical") is not True
            or ref.get("patches") != []
            or ref.get("patched_forge_sha256") != ref.get("original_forge_sha256")):
            raise ValueError("Claimed genuine stock Forge control is not original byte-for-byte")
    if ref.get("canonical_seven_deck_sha256")!=exp.get("canonical_seven_deck_sha256"):
        raise ValueError("Deck identities changed between campaigns")
    pairs=report.get("pairs",[])
    if len(pairs)!=report.get("real_process_pairs") or not pairs:
        raise ValueError("Missing genuine matched JVMs")
    seat=Counter(); by_pod=Counter()
    wins_reference=Counter();wins_experiment=Counter()
    natural_reference=0;natural_experiment=0;completed_pairs=0
    brimaz_comparisons=[]
    statuses=Counter(); changes=0; windows=0; proposed=0; fallback=0
    tactical_windows=0; tactical_approved=Counter(); tactical_rejected=0
    tactical_by_card=Counter()
    samples=[]
    for pair in pairs:
        a=pair["reference"];b=pair["experiment"]
        x=Path(a["log"]).read_text(encoding="utf-8",errors="replace")
        y=Path(b["log"]).read_text(encoding="utf-8",errors="replace")
        if "Ai(1)-" not in x or "Ai(4)-" not in y or "Turn: " not in y:
            raise ValueError("Missing four-seat real-game transcript markers")
        if any(regex.search(x) for regex in (APPROVED,WINDOW,REJECTED,TACTICAL_WINDOW,TACTICAL_APPROVED,TACTICAL_REJECTED)):
            raise ValueError("V35 code touched control arm")
        candidates=list(WINDOW.finditer(y))
        approvals=list(APPROVED.finditer(y))
        if exp["policy"] in ("v35_brimaz_duel","v36_brimaz_challenger","v37_brimaz_challenger"):
            for marker in candidates+list(TACTICAL_WINDOW.finditer(y)):
                if b["seats"][int(marker["seat"])-1]!="Brimaz_V3":
                    raise ValueError("V35 diagnostic window leaked into unchanged opponent")
        rejects=list(REJECTED.finditer(y))
        windows+=len(candidates)
        proposed+=sum(int(m["ranked"]) for m in candidates)
        fallback+=sum(int(m["count"]) for m in rejects)
        task_windows=list(TACTICAL_WINDOW.finditer(y))
        task_approvals=list(TACTICAL_APPROVED.finditer(y))
        task_rejects=list(TACTICAL_REJECTED.finditer(y))
        tactical_windows+=len(task_windows)
        tactical_rejected+=sum(int(m["count"]) for m in task_rejects)
        for approved in task_approvals:
            if (exp["policy"] in ("v35_brimaz_duel","v36_brimaz_challenger","v37_brimaz_challenger")
                and b["seats"][int(approved["seat"])-1]!="Brimaz_V3"):
                raise ValueError("V35 tactical policy leaked into unchanged opponent")
            if int(approved["turn"])<1 or int(approved["rejected"])>5:
                raise ValueError("Invalid original Forge tactical approval")
            if not task_windows:
                raise ValueError("Tactical approval without public-board decision window")
            tactical_approved[int(approved["seat"])]+=1
            tactical_by_card[approved["card"]]+=1
        for m in approvals:
            index=int(m["seat"])
            if exp["policy"] in ("v35_brimaz_duel","v36_brimaz_challenger","v37_brimaz_challenger") and b["seats"][index-1]!="Brimaz_V3":
                raise ValueError("V35 strategy leaked into an unchanged v17 opponent")
            if int(m["turn"])<1 or int(m["rejected"])>3:
                raise ValueError("Invalid V35 original Forge approval marker")
            if not candidates:
                raise ValueError("Approval without a V35 search window")
            seat[index]+=1
            by_pod[b["pod"]]+=1
            if len(samples)<25:samples.append({
                **m.groupdict(),"pod":b["pod"],"rotation":b["rotation"]})
        statuses[(a["status"],b["status"])]+=1
        if a["status"]=="complete":
            natural_reference+=1
            wins_reference[a["winner"]]+=1
        if b["status"]=="complete":
            natural_experiment+=1
            wins_experiment[b["winner"]]+=1
        if a["status"]==b["status"]=="complete":
            completed_pairs+=1
            brimaz_comparisons.append({
                "pod":b["pod"],"rotation":b["rotation"],
                "stock_brimaz_win":a["winner"]=="Brimaz_V3",
                "improved_brimaz_win":b["winner"]=="Brimaz_V3",
                "seed_identifies_pair_not_identical_rng":True
            })
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
      "public_board_tactical_windows_logged":tactical_windows,
      "tactical_stock_forge_approved_not_cast_proof":sum(tactical_approved.values()),
      "tactical_approved_by_seat":dict(sorted(tactical_approved.items())),
      "tactical_approved_by_card":dict(tactical_by_card),
      "tactical_candidates_rejected_by_forge":tactical_rejected,
      "statuses":{str(k):v for k,v in statuses.items()},
      "v36_challenger": exp["policy"]=="v36_brimaz_challenger",
      "v37_stock_ai_mixed_seat_challenger":exp["policy"]=="v37_brimaz_challenger",
      "reference_policy":ref["policy"],
      "experimental_policy":exp["policy"],
      "reference_is_byte_identical_to_stock_forge":ref["policy"]=="forge_stock",
      "reference_is_stock_ai_with_shared_compatibility_fix":ref["policy"]=="forge_stock_compat",
      "mixed_seat_brimaz_vs_v17_opponents":exp["policy"] in ("v35_brimaz_duel","v36_brimaz_challenger"),
      "arm_natural_finishes":{"reference":natural_reference,"experiment":natural_experiment},
      "wins_by_deck_all_natural_reference":dict(wins_reference),
      "wins_by_deck_all_natural_experiment":dict(wins_experiment),
      "paired_natural_brimaz_wins":{
          "reference":sum(x["stock_brimaz_win"] for x in brimaz_comparisons),
          "experiment":sum(x["improved_brimaz_win"] for x in brimaz_comparisons),
          "both_natural_pairs":completed_pairs,
      },
      "note_on_evidence":"All four AIs have the same policy within each match; comparing Brimaz win rates is NOT direct AI-vs-AI head-to-head, and cannot by itself certify stronger general AI.",
      "brimaz_comparisons":brimaz_comparisons,
      "paired_brimaz_evidence":paired_brimaz_evidence(brimaz_comparisons),
      "approved_examples":samples,
      "limits":[
        "V35_WINDOW is only a bounded abstract search proposal",
        "V35_TACTICAL_WINDOW is a potential emergency, not proof the card was usable or cast",
        "V35_STOCK_APPROVED means original Forge AI agreed to play; it does not independently prove actual spell resolution",
        "forge_stock_compat is stock AI with a shared CharmEffect crash fix, not a byte-identical original JAR",
        "For v35_strategy all four seats use the same upgraded policy: NOT a mixed-seat head-to-head",
        "For v35_brimaz_duel Brimaz uses V35 while opponents retain v17_modified baseline, NOT pristine upstream Forge",
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
           "approved_actions_by_seat","different_game_event_sequences",
           "public_board_tactical_windows_logged","tactical_stock_forge_approved_not_cast_proof",
           "tactical_approved_by_card","paired_brimaz_evidence")
        }),flush=True)
    if r["actual_stock_forge_approved_strategic_actions_not_cast_proof"]<args.min_approved:
        raise SystemExit("V35_FAIL_NO_DEMONSTRATED_STOCK_FORGE_APPROVED_INTERVENTIONS")

if __name__=="__main__":main()
