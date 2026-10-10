#!/usr/bin/env python3
"""Compare two complete, genuine locally-run four-AI Forge campaigns.

Only actual process logs count. Same seed is a pairing key, NOT proof of
identical game paths; controlled speed comparisons require natural endings
AND identical observable event fingerprints. Never infer win rate from
clock-censored games or count paired observations as independent samples.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

EVENT_PREFIXES=("Turn: ","Phase: ","Combat: ","Add To Stack: ",
                "Game Outcome: ","Damage: ","Life: ","Zone Change: ","Land: ")

def load_campaign(root):
    provenance=json.loads((root/"provenance.json").read_text(encoding="utf-8"))
    files=sorted((root/"games").rglob("games.json"))
    if not files:
        raise ValueError("No actual Forge four-AI game manifests: "+str(root))
    data={}
    for manifest in files:
        rows=json.loads(manifest.read_text(encoding="utf-8"))
        if not rows:raise ValueError("Empty manifest "+str(manifest))
        for r in rows:
            if len(r["seats"])!=4 or len(set(r["seats"]))!=4:
                raise ValueError("Not four distinct real Commander seats")
            if r["seats"].count("Brimaz_V3")!=1:
                raise ValueError("Missing unique Brimaz seat")
            log=manifest.parent/Path(r["log"]).name
            if not log.is_file():
                raise ValueError("Actual Forge game log missing "+str(log))
            raw=log.read_text(encoding="utf-8",errors="replace")
            if not ("Turn: Turn " in raw and "Ai(1)-" in raw):
                raise ValueError("Not a real logged Forge 4-seat game "+str(log))
            if r["status"]=="complete":
                seat=r["winner_seat"]
                if seat not in (1,2,3,4) or r["seats"][seat-1]!=r["winner_deck"]:
                    raise ValueError("Inconsistent declared natural game winner")
            else:
                if r["winner_deck"] is not None:
                    raise ValueError("Censored/error game falsely labeled with winner")
            key=(r["pod"],r["rotation"],r["repeat"],r["seed"])
            if key in data:raise ValueError("Duplicate real game key "+str(key))
            events=[line for line in raw.splitlines()
                    if line.startswith(EVENT_PREFIXES) and "Match Duration" not in line]
            data[key]={
                "pod":r["pod"],"rotation":r["rotation"],"repeat":r["repeat"],
                "seed":r["seed"],"seats":r["seats"],"status":r["status"],
                "winner":r["winner_deck"],"brimaz_win":r["brimaz_win"],
                "wall_seconds":r["wall_seconds"],"game_milliseconds":r.get("game_milliseconds"),
                "clock_seconds":r["clock_seconds"],"profiles":r["profiles"],
                "raw_sha256":hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                "event_sha256":hashlib.sha256("\n".join(events).encode("utf-8")).hexdigest(),
                "event_count":len(events),
                "log":str(log),
            }
    return provenance,data

def compare(root_a,root_b):
    meta_a,games_a=load_campaign(root_a)
    meta_b,games_b=load_campaign(root_b)
    for key in ("original_forge_sha256","canonical_seven_deck_sha256",
                "profile_applied_identically_to_all_four_seats","pods",
                "games_per_rotation","base_seed","clock_seconds"):
        if meta_a.get(key)!=meta_b.get(key):
            raise ValueError("Not a fair canonical Forge A/B: "+key)
    if games_a.keys()!=games_b.keys():
        raise ValueError("Game rotations/repeats/seeds do not fully pair. Refuse partial cherry-picking")
    pairs=[]
    for key in sorted(games_a):
        a,b=games_a[key],games_b[key]
        for field in ("seats","clock_seconds","profiles"):
            if a[field]!=b[field]:raise ValueError("Mismatched "+field+" in "+str(key))
        natural=a["status"]==b["status"]=="complete"
        matching=natural and a["event_sha256"]==b["event_sha256"]
        pairs.append({
            "pod":a["pod"],"rotation":a["rotation"],"repeat":a["repeat"],
            "seed":a["seed"],
            "reference":a,"experiment":b,
            "both_natural":natural,
            "same_observable_events_if_natural":matching,
            "winner_changed_if_both_natural":(a["winner"]!=b["winner"]) if natural else None,
            "wall_speed_ratio_only_same_natural_game":
                round(a["wall_seconds"]/b["wall_seconds"],4)
                if matching and b["wall_seconds"]>0 else None,
        })
    natural_pairs=[x for x in pairs if x["both_natural"]]
    identical=[x for x in pairs if x["same_observable_events_if_natural"]]
    censored=[x for x in pairs if not x["both_natural"]]
    return {
        "type":"Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B",
        "reference_provenance":meta_a,"experiment_provenance":meta_b,
        "real_process_pairs":len(pairs),"real_forge_jvm_processes":len(pairs)*2,
        "both_natural_pairs":len(natural_pairs),
        "pairs_with_any_censor_or_fault":len(censored),
        "natural_pairs_with_identical_observable_actions":len(identical),
        "natural_pairs_with_different_winner":sum(x["winner_changed_if_both_natural"] for x in natural_pairs),
        "natural_winners_reference":dict(Counter(x["reference"]["winner"] for x in natural_pairs)),
        "natural_winners_experiment":dict(Counter(x["experiment"]["winner"] for x in natural_pairs)),
        "pairs":pairs,
        "limitations":[
          "Matched seeds may diverge due to AI search scheduling and changing behavior.",
          "A speed ratio is presented ONLY for two natural games with identical tracked events.",
          "Two paired games are not independent draws for a reliable winrate estimate.",
          "Censored, process-timeout and engine-fault games are not counted as wins/losses.",
          "Source equivalence and Oracle rules are not independently certified here.",
        ]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",required=True,type=Path)
    p.add_argument("--experiment",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    data=compare(a.reference,a.experiment)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_LOCAL_PAIRED_EVIDENCE",json.dumps({
      "real_jvms":data["real_forge_jvm_processes"],
      "natural_pairs":data["both_natural_pairs"],
      "censored_or_fault_pairs":data["pairs_with_any_censor_or_fault"],
      "identical_game_pairs":data["natural_pairs_with_identical_observable_actions"],
      "different_natural_winner_pairs":data["natural_pairs_with_different_winner"],
    },ensure_ascii=False),flush=True)

if __name__=="__main__":main()
