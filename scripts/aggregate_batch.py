#!/usr/bin/env python3
"""Aggregate independent GitHub Actions Forge shards. Reject clock-cutoff matches.

A/B results are descriptive only: seeds are matched, but AI decisions change RNG
consumption, so this is not a true common-random-numbers experiment.
"""
import argparse
import collections
import json
import math
import pathlib
import sys

p=argparse.ArgumentParser()
p.add_argument("--input",default="artifacts")
p.add_argument("--output",default="results/parallel/aggregate.json")
args=p.parse_args()
files=sorted(pathlib.Path(args.input).rglob("games.json"))
if not files:
    p.error("No games.json artifacts found; refusing to claim a result")
games=[]
for path in files:
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,list):
        raise ValueError("Invalid artifact: "+str(path))
    for item in data:
        item["artifact_file"]=str(path)
        games.append(item)

identities=[]
for g in games:
    identities.append((g["pod"],g["rotation"],g["repeat"],g.get("brimaz_profile","Default"),g.get("seed")))
if len(identities)!=len(set(identities)):
    raise ValueError("Duplicated game keys: artifact collision or rerun mixed into original sample")
grouped=collections.defaultdict(list)
for g in games:
    grouped[(g["pod"],g.get("brimaz_profile","Default"))].append(g)

def wilson(wins,n,z=1.96):
    if not n:return None
    phat=wins/n
    den=1+z*z/n
    middle=(phat+z*z/(2*n))/den
    half=z*math.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/den
    return [round(max(0,middle-half),4),round(min(1,middle+half),4)]

report={}
for (pod,profile), rows in sorted(grouped.items()):
    good=[x for x in rows if x["status"]=="complete"]
    wins=sum(x["brimaz_win"] is True for x in good)
    r={
      "pod":pod,"brimaz_profile":profile,
      "scheduled":len(rows),"valid_games":len(good),
      "invalid_by_reason":dict(collections.Counter(x["status"] for x in rows if x["status"]!="complete")),
      "brimaz_wins":wins,
      "win_rate":round(wins/len(good),4) if good else None,
      "wilson_95_interval":wilson(wins,len(good)),
      "winners":dict(collections.Counter(x.get("winner_deck") for x in good)),
      "brimaz_triggers_per_game":round(sum(x["brimaz_triggered"] for x in good)/len(good),2) if good else None,
      "incubator_transforms_per_game_all_players":round(sum(x["incubator_transforms"] for x in good)/len(good),2) if good else None,
      "mean_game_seconds":round(sum(x["game_milliseconds"] for x in good)/len(good)/1000,2) if good else None,
      "incubate_ai_warning_games":sum(bool(x.get("ai_incubate_warning")) for x in rows),
      "seats_covered":sorted(set(x["brimaz_seat"] for x in rows)),
    }
    report[pod+"/"+profile]=r
    print("GROUP",json.dumps(r,ensure_ascii=False),flush=True)

pairs=[]
by_seed=collections.defaultdict(dict)
for g in games:
    key=(g["pod"],g["rotation"],g["repeat"],g.get("seed"))
    by_seed[key][g.get("brimaz_profile","Default")]=g
for key,group in by_seed.items():
    if "Default" in group and "Experimental" in group:
        a,b=group["Default"],group["Experimental"]
        if a["status"]=="complete" and b["status"]=="complete":
            pairs.append({"pod":key[0],"rotation":key[1],"seed":key[3],
                          "default_win":a["brimaz_win"],"experimental_win":b["brimaz_win"]})
out={
  "games":len(games),"groups":report,"matched_seed_pairs":len(pairs),
  "profile_comparison_notes":"Default vs Experimental are existing Forge heuristics, not stronger AI by default. No causality or definitive ranking from small samples.",
  "limitations":["Actual rules engine; decisions are Forge heuristics, not expert human play",
                 "Per-game RNG seed recorded; changing decisions alters random draw consumption",
                 "Profile A/B cannot repair missing Incubate API handler or strategic end-step sacrificing",
                 "Censored games excluded; high censoring biases observed win rate",
                 "Deck power bracket and Game Changers must be validated separately",
                 "No LLM or external agent is taking actions during these games"],
  "games_detail":games
}
path=pathlib.Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("AGGREGATED",json.dumps({"games":len(games),"groups":len(report),"matched_seed_pairs":len(pairs)},ensure_ascii=False),flush=True)
sys.exit(0 if all(len(g)==4 for g in grouped.values()) else 0)
