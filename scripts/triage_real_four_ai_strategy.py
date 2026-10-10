#!/usr/bin/env python3
"""Rank *observed* tactical/development failure signals for real four-AI Forge.

No inference of which Magic actions were legal but missed. The scores are
diagnostic signals, NOT legal-state counterfactuals or AI quality grades.
"""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

def audit(forensic):
    if forensic.get("type")!="Forge four-seat action-level diagnostic (NOT a legal-action oracle)":
        raise ValueError("Expected raw Forge four-seat forensic schema")
    games=forensic.get("games",[])
    if not games:raise ValueError("No genuine four-AI game analysis")
    seen=set()
    counts=Counter()
    by_pod=defaultdict(Counter)
    by_deck=defaultdict(Counter)
    by_policy=defaultdict(Counter)
    examples=defaultdict(list)
    for g in games:
        identity=g["identity"]
        key=(identity["pod"],identity["rotation"],identity["seed"],identity["policy"])
        if key in seen:raise ValueError("Duplicate Forge pod/seed/rotation/policy")
        seen.add(key)
        players=g["players"]
        if len(players)!=4 or sorted(p["seat"] for p in players)!=[1,2,3,4]:
            raise ValueError("Not four independent AI seats")
        if len({p["deck"] for p in players})!=4:
            raise ValueError("Duplicate Commander player decks")
        if sum(p["deck"]=="Brimaz_V3" for p in players)!=1:
            raise ValueError("Exactly one Brimaz deck expected")
        status=identity["status"]
        if status not in ("complete","clock_censored","engine_fault","process_timeout",
                          "engine_failed","unparsed"):
            raise ValueError("Unexpected real Forge match status")
        counts["games_observed"]+=1
        counts["status_"+status]+=1
        pod=identity["pod"]
        policy=identity["policy"]
        by_pod[pod]["games"]+=1
        by_policy[policy]["games"]+=1
        for p in players:
            d=p["deck"]
            agg=by_deck[d]
            agg["appearances"]+=1
            for item in ("turns_taken","lands_played","spells_cast",
                         "abilities_activated","triggers_observed",
                         "commander_casts_observed","attacks_declared",
                         "combat_damage_to_players","combat_damage_received",
                         "counter_spells_considered","counter_profile_declines",
                         "counter_commander_threats","counter_lethal_life_threats",
                         "counter_override_acceptances_not_casts",
                         "slow_ai_evaluations"):
                agg[item]+=p[item]
            if p["turns_taken"]>=3 and p["lands_played"]==0:
                counts["observed_3plus_turns_without_lands"]+=1
                examples["observed_3plus_turns_without_lands"].append({
                    "pod":pod,"policy":policy,"seed":identity["seed"],
                    "deck":d,"turns":p["turns_taken"]})
            if p["slow_ai_evaluations"]>0:
                counts["seats_with_slow_ai_decisions"]+=1
                by_pod[pod]["slow_ai_evaluations"]+=p["slow_ai_evaluations"]
            if status=="complete" and p["winner_in_raw_log"]:
                agg["natural_observed_wins_unverified"]+=1
        brimaz=next(p for p in players if p["deck"]=="Brimaz_V3")
        casts=brimaz["commander_casts_observed"]
        exits=g["brimaz"]["commander_battlefield_exits"]
        if casts>=3 and exits>=2:
            counts["brimaz_commander_recast_heavy_games"]+=1
            examples["brimaz_commander_recast_heavy_games"].append({
              "pod":pod,"seed":identity["seed"],"policy":policy,
              "commander_casts":casts,"battlefield_exits":exits})
        bw=g["brimaz"]
        w=bw.get("windows",0)
        counts["brimaz_decision_windows"]+=w
        counts["brimaz_windows_with_phyrexian_tokens"]+=bw.get("windows_with_phyrexian_tokens",0)
        counts["brimaz_windows_with_outlet"]+=bw.get("windows_with_outlet",0)
        if w>0 and bw.get("windows_with_phyrexian_tokens",0)>0 \
              and bw.get("windows_with_outlet",0)==0:
            counts["brimaz_phyrexian_windows_no_outlet_game"]+=1
        # This is an activated ability attempt, NOT proof of a token
        # transformed successfully: label explicitly to avoid false wins.
        counts["incubator_token_activations_not_confirmed_transformations"]+=bw.get(
            "observed_incubator_transformations",0)
        if status=="complete":
            counts["natural_games"]+=1
        else:counts["censored_or_fault_games"]+=1

    ranked=[]
    evidence=[
      ("AI decision slow hot paths","seats_with_slow_ai_decisions",
       "Profile with JFR and inspect real Java stack. Do not blame lastCandidate card."),
      ("Repeated Brimaz recast / exit loops","brimaz_commander_recast_heavy_games",
       "Audit MAIN1 commander priority against all currently legal Forge actions before adjusting tempo."),
      ("Phyrexian tokens visible but no sacrifice outlet","brimaz_phyrexian_windows_no_outlet_game",
       "Check whether a legally affordable outlet was present; the trace alone does not prove a missed play."),
      ("No observed land drop across at least 3 own turns","observed_3plus_turns_without_lands",
       "Inspect hands and legal land availability before calling this a mana sequencing mistake."),
    ]
    for title,key,next_step in evidence:
        ranked.append({"investigation":title,"games_or_seats_with_signal":counts[key],
                       "observation_key":key,"next_proof_required":next_step})
    ranked.sort(key=lambda x:-x["games_or_seats_with_signal"])
    return {
      "source":"Real Forge 2.0.15 four-seat gameplay transcripts; action-only forensics",
      "game_count":len(games),"pod_counts":{k:dict(v) for k,v in sorted(by_pod.items())},
      "policy_counts":{k:dict(v) for k,v in sorted(by_policy.items())},
      "signals":dict(counts),"per_deck":{k:dict(v) for k,v in sorted(by_deck.items())},
      "prioritized_investigations":ranked,
      "sample_events":{k:v[:10] for k,v in examples.items()},
      "limits":[
        "The gameplay log does not reveal legal alternative actions or private cards to other players.",
        "A skipped land drop may be legal if the AI had no land; absence of a logged outlet is not a missed legal opportunity.",
        "Incubator Token activated is NOT a proven transform or value generation.",
        "Natural winner status is Forge-observed, not independent Oracle card/priority certification.",
        "No scoring of human-level tactical competence or statistical winrate from overlapping paired A/B games.",
      ],
    }

def markdown(report):
    lines=["# Real four-AI Commander strategic forensic triage","",
           f"Real Forge games inspected: **{report['game_count']}**",
           f"Statuses: { {k:v for k,v in report['signals'].items() if k.startswith('status_')} }",
           "","## Candidate AI failures to investigate (signals, not proven legal errors)","",
           "| Signal | Games/seats observed | Follow-up evidence needed |",
           "|---|---:|---|"]
    for r in report["prioritized_investigations"]:
        lines.append(f"| {r['investigation']} | {r['games_or_seats_with_signal']} | {r['next_proof_required']} |")
    lines+=["","## Observed actions by actual deck","","| Deck | Games | Turns | Lands | Spells | Commander casts | Damage dealt | Damage received |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for deck,d in report["per_deck"].items():
        lines.append(f"| {deck} | {d['appearances']} | {d['turns_taken']} | {d['lands_played']} | "
                     f"{d['spells_cast']} | {d['commander_casts_observed']} | "
                     f"{d['combat_damage_to_players']} | {d['combat_damage_received']} |")
    lines+=["","## Strict limits",""]+["- "+x for x in report["limits"]]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    data=json.loads(args.input.read_text(encoding="utf-8"))
    report=audit(data)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"strategic_triage.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (args.output/"strategic_triage.md").write_text(markdown(report),encoding="utf-8")
    print("FOUR_AI_STRATEGIC_TRIAGE",json.dumps({
        "real_games":report["game_count"],"ranked_signals":report["prioritized_investigations"],
        "natural":report["signals"].get("natural_games",0),
    },ensure_ascii=False),flush=True)
if __name__=="__main__":main()
