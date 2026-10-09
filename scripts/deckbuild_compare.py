#!/usr/bin/env python3
"""Winrate and quality comparison for two candidate Commander decks.

Use independently certified genuine Forge four-player games. Preserve censored
runs and evaluate pairs by seed only descriptively: same Forge RNG seed does
NOT guarantee the same game actions across modified decks.
"""
import argparse
from collections import Counter
import json
from math import sqrt
from pathlib import Path

PODS=("aristo","artifact")
ARMS=("reference","candidate")


def wilson(k,n,z=1.959963984540054):
    if n==0:return None
    if not 0<=k<=n:raise ValueError("Invalid win count")
    p=k/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [round(max(0,center-half),4),round(min(1,center+half),4)]


def statistic(rows):
    total=len(rows)
    natural=[r for r in rows if r["natural_verified"]]
    wins=sum(r["candidate_win"] is True for r in natural)
    unverified=total-len(natural)
    warnings=sum(not r["ai_warning_free"] for r in natural)
    return {
        "scheduled":total,"natural_certified":len(natural),
        "rejected_or_censored":unverified,
        "wins":wins,
        "certified_winrate":round(wins/len(natural),4) if natural else None,
        "wilson_95":wilson(wins,len(natural)),
        "winrate_lower_bound_all_scheduled":round(wins/total,4) if total else None,
        "winrate_upper_bound_all_scheduled":round((wins+unverified)/total,4) if total else None,
        "natural_games_with_ai_quality_warnings":warnings,
        "warning_free_wins":sum(r["candidate_win"] is True and r["ai_warning_free"] for r in natural),
        "ai_timeouts":sum(r["ai_quality_signatures"]["evaluation_timeouts"] for r in rows),
        "attack_fallbacks":sum(r["ai_quality_signatures"]["invalid_attack_fallbacks"] for r in rows),
        "estimated_wall_seconds_total":round(sum(r.get("wall_seconds") or 0 for r in rows),2),
        "winner_decks":dict(Counter(r["winner_deck"] for r in natural)),
    }


def analyze(certificate,manifest,repeats):
    if not 1<=repeats<=10:raise ValueError("Illegal number of repeats")
    rows=certificate["games"]
    expected=2*len(PODS)*4*repeats
    if len(rows)!=expected:
        raise ValueError(f"Incomplete matrix: {len(rows)} of {expected} expected games")
    observed={}
    for r in rows:
        arm=r["arm"]
        if arm not in ARMS or r["pod"] not in PODS or not 0<=r["rotation"]<4 or not 0<=r["repeat"]<repeats:
            raise ValueError("Unexpected arm/pod/rotation/repeat")
        spec=manifest["decks"][arm]
        if r["candidate_deck"]!=spec["label"] or r["candidate_sha256"]!=spec["forge_sha256"]:
            raise ValueError("Deck identity changed across simulations")
        if r["candidate_seat"] != 1+(4-r["rotation"])%4:
            raise ValueError("Unbalanced or incorrect candidate seat rotation")
        key=(arm,r["pod"],r["rotation"],r["repeat"])
        if key in observed:
            raise ValueError("Duplicate seed/arm/seat combination")
        observed[key]=r
    pairs=[]
    for pod in PODS:
        for rotation in range(4):
            for repeat in range(repeats):
                a=observed["reference",pod,rotation,repeat]
                b=observed["candidate",pod,rotation,repeat]
                if a["seed"]!=b["seed"]:
                    raise ValueError("Arms must use the same declared seed/pod/rotation for descriptive pairing")
                if a["policy"]!=b["policy"]:
                    raise ValueError("Do not attribute different AI versions to deck swaps")
                pairs.append({
                    "pod":pod,"rotation":rotation,"repeat":repeat,"seed":a["seed"],
                    "both_natural":a["natural_verified"] and b["natural_verified"],
                    "reference_win":a["candidate_win"] if a["natural_verified"] else None,
                    "candidate_win":b["candidate_win"] if b["natural_verified"] else None,
                    "reference_warning_free":a["ai_warning_free"] if a["natural_verified"] else None,
                    "candidate_warning_free":b["ai_warning_free"] if b["natural_verified"] else None,
                })
    by_arm={arm:statistic([r for r in rows if r["arm"]==arm]) for arm in ARMS}
    by_pod={pod:{arm:statistic([r for r in rows if r["pod"]==pod and r["arm"]==arm])
                 for arm in ARMS} for pod in PODS}
    by_seat={str(seat):{arm:statistic([r for r in rows if r["candidate_seat"]==seat and r["arm"]==arm])
                       for arm in ARMS} for seat in range(1,5)}
    both=[r for r in pairs if r["both_natural"]]
    a,b=by_arm["reference"],by_arm["candidate"]
    delta=round(b["certified_winrate"]-a["certified_winrate"],4) if a["certified_winrate"] is not None and b["certified_winrate"] is not None else None
    return {
        "summary":{
            "scheduled_matches":expected,
            "natural_certified_matches":a["natural_certified"]+b["natural_certified"],
            "matched_seed_pairs":len(pairs),
            "pairs_both_natural":len(both),
            "delta_candidate_minus_reference_conditional_winrate":delta,
            "reference":a,"candidate":b,
            "pairs_candidate_only_wins":sum(r["candidate_win"] is True and r["reference_win"] is False for r in both),
            "pairs_reference_only_wins":sum(r["reference_win"] is True and r["candidate_win"] is False for r in both),
            "pairs_both_win":sum(r["reference_win"] is True and r["candidate_win"] is True for r in both),
            "pairs_neither_win":sum(r["reference_win"] is False and r["candidate_win"] is False for r in both),
            "interpretation":"Screening evidence only; certify larger samples before ranking close decks. Deck changes perturb RNG, even at identical Forge seeds. Warning-free AI does not guarantee expert decisions.",
            "statistical_note":"Wilson intervals reflect conditional winrate uncertainty; censored games are separately exposed with conservative scheduled-outcome bounds."
        },
        "by_pod":by_pod,"by_candidate_seat":by_seat,"pairs":pairs,
        "candidate_deltas":manifest.get("delta",{}),
        "deck_manifest":manifest["decks"]
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--certificate",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--repeats",required=True,type=int)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=analyze(json.loads(a.certificate.read_text(encoding="utf-8")),
                   json.loads(a.manifest.read_text(encoding="utf-8")),a.repeats)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("DECKBUILD_AB_COMPARISON",json.dumps(report["summary"],ensure_ascii=False),flush=True)
    for arm in ARMS:
        s=report["summary"][arm]
        print("DECKBUILD_ARM",arm,"winrate",s["certified_winrate"],"wins",
              s["wins"],"valid",s["natural_certified"],"censored",s["rejected_or_censored"],flush=True)


if __name__=="__main__":
    main()
