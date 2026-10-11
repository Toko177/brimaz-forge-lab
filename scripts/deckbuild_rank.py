#!/usr/bin/env python3
"""Rank screened Commander card-swap candidates sharing one certified reference.

Only compare candidates if EVERY reference transcript is identical by SHA256,
and the engine, opponents, seed cohort, AI profile and decks share the exact
reference fingerprint. An ordinal screening priority is not proof of a superior
deck; report wide CIs and selection bias transparently.
"""
import argparse
import json
from pathlib import Path


def baseline_key(report):
    env=report.get("reference_environment")
    if not isinstance(env,dict) or not env.get("fingerprint") or not env.get("inputs"):
        raise ValueError("Missing independent reference runtime/deck/seed provenance")
    return env["fingerprint"],env["inputs"]


def reference_proof(report):
    entries={}
    for p in report["pairs"]:
        key=(p["pod"],p["rotation"],p["repeat"],p["seed"])
        if key in entries:raise ValueError("Duplicate reference seat/seed entry")
        sha=p.get("reference_transcript_sha256")
        if not isinstance(sha,str) or len(sha)!=64:
            raise ValueError("No full SHA256 evidence for every original reference game")
        entries[key]=sha
    return entries


def rank(reports):
    if len(reports)<2:
        raise ValueError("Require at least two different deck candidates to rank")
    fingerprints=[baseline_key(r) for r in reports]
    first=fingerprints[0]
    if any(x!=first for x in fingerprints[1:]):
        raise ValueError("Incompatible reference deck, Forge patch or seed cohort")
    originals=reference_proof(reports[0])
    if any(reference_proof(x)!=originals for x in reports[1:]):
        raise ValueError("Reference game histories diverged despite matching predeclared seeds")
    seen=set()
    variants=[]
    for idx,document in enumerate(reports):
        summary=document["summary"]
        candidate=document["deck_manifest"]["candidate"]
        baseline=document["deck_manifest"]["reference"]
        if candidate.get("forge_sha256") in seen:
            raise ValueError("Same candidate deck benchmarked twice: avoid double-counting")
        seen.add(candidate["forge_sha256"])
        if baseline.get("forge_sha256")!=first[1]["reference_deck_sha256"]:
            raise ValueError("Unexpected baseline deck source hash")
        a,b=summary["reference"],summary["candidate"]
        if (a["scheduled"]!=len(originals) or
            b["scheduled"]!=len(originals) or
            summary["matched_seed_pairs"]!=len(originals)):
            raise ValueError("Inconsistent denominator or missing baseline reference game")
        variants.append({
            "candidate_sha256":candidate["forge_sha256"],
            "source_file":candidate.get("source_file"),
            "added":document["candidate_deltas"]["added"],
            "removed":document["candidate_deltas"]["removed"],
            "scheduled":b["scheduled"],
            "certified":b["natural_certified"],
            "wins":b["wins"],
            "observed_winrate":b["certified_winrate"],
            "wilson_95":b["wilson_95"],
            "censored":b["rejected_or_censored"],
            "timeouts":b["ai_timeouts"],
            "warning_free_wins":b["warning_free_wins"],
            "reference_wins":a["wins"],
            "reference_natural":a["natural_certified"],
            "screening_only":True,
            "control_AA":candidate["forge_sha256"]==baseline["forge_sha256"] if candidate["label"]==baseline["label"] else not bool(document["candidate_deltas"]["added"] or document["candidate_deltas"]["removed"]),
            "source_report_index":idx,
        })
    variants.sort(key=lambda x:(
        -(x["wilson_95"][0] if x["wilson_95"] else -1),
        -(x["observed_winrate"] if x["observed_winrate"] is not None else -1),
        x["censored"], x["timeouts"], x["candidate_sha256"]))
    for n,v in enumerate(variants,1):
        v["screening_priority"]=n
    return {
        "summary":{
            "variants_compared":len(variants),
            "unique_original_reference_games":len(originals),
            "reference_fingerprint":first[0],
            "reference_reused_without_replay":True,
            "no_statistical_winner_declared":True,
            "limitations":"Ranking is exploratory. Multiple variants, censoring, Forge AI skill and re-used opponent samples can bias comparisons; same RNG seed across different decks is not an equivalent game trajectory. Re-test any promising design with new seeds, more games and quality audits."
        },"ranking":variants
    }


def markdown_report(data):
    lines=[
        "# Commander deck candidates — provisional ranking",
        "",
        f"Same certified reference: {data['summary']['unique_original_reference_games']} raw Forge matches",
        "",
        "| Screening priority | Cards added | Cards removed | Wins / certified | Winrate | Wilson 95% | Censored | AI timeouts |",
        "|---:|---|---|---:|---:|---|---:|---:|"
    ]
    for x in data["ranking"]:
        add=", ".join(f"{n}× {c}" for c,n in x["added"].items()) or "No changes"
        remove=", ".join(f"{n}× {c}" for c,n in x["removed"].items()) or "No changes"
        ci=x["wilson_95"]
        ci_label=f"{ci[0]*100:.1f}–{ci[1]*100:.1f}%" if ci else "not estimated"
        p=x["observed_winrate"]
        wr=f"{p*100:.1f}%" if p is not None else "not estimated"
        lines.append(f"| {x['screening_priority']} | {add} | {remove} | {x['wins']}/{x['certified']} | {wr} | {ci_label} | {x['censored']} | {x['timeouts']} |")
    lines+=["", "**Exploratory screening only:** no deck is established as statistically superior.",
            "Repeat promising variants against new seeds; compare deck quality, not only raw wins.",
            ""]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reports",type=Path,nargs="+",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--markdown",type=Path)
    args=p.parse_args()
    reports=[json.loads(path.read_text(encoding="utf-8")) for path in args.reports]
    result=rank(reports)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True,exist_ok=True)
        args.markdown.write_text(markdown_report(result),encoding="utf-8")
    print("DECKBUILD_COMPATIBLE_CANDIDATES_RANKED",json.dumps(result["summary"],ensure_ascii=False))

if __name__=="__main__":
    main()
