#!/usr/bin/env python3
"""Matched-seed baseline vs custom Brimaz AI analysis (real Forge logs only).
This is a diagnostic design, not a guaranteed common-random-numbers experiment:
changing choices can alter the RNG stream for subsequent events.
"""
import argparse,collections,json,pathlib,statistics

p=argparse.ArgumentParser()
p.add_argument("--baseline",required=True)
p.add_argument("--candidate",required=True)
p.add_argument("--output",required=True)
args=p.parse_args()

def load(root):
    result={}
    paths=sorted(pathlib.Path(root).rglob("games.json"))
    if not paths: raise ValueError("No game logs in "+root)
    for path in paths:
        records=json.loads(path.read_text(encoding="utf-8"))
        for g in records:
            if g.get("brimaz_profile","Default")!="Default":
                continue
            key=(g["pod"],g["rotation"],g["repeat"],g["seed"])
            if key in result:raise ValueError("Duplicate key "+repr(key))
            result[key]=g
    return result

base=load(args.baseline)
cand=load(args.candidate)
shared=sorted(set(base)&set(cand))
records=[]
for k in shared:
    x,y=base[k],cand[k]
    row={
      "pod":k[0],"rotation":k[1],"repeat":k[2],"seed":k[3],
      "baseline_status":x["status"],"candidate_status":y["status"],
      "baseline_win":x["brimaz_win"],"candidate_win":y["brimaz_win"],
      "baseline_cast_triggers":x["brimaz_triggered"],
      "candidate_cast_triggers":y["brimaz_triggered"],
      "baseline_incubator_transforms":x["incubator_transforms"],
      "candidate_incubator_transforms":y["incubator_transforms"],
      "planner_decisions":y.get("planner_decisions",0)
    }
    records.append(row)
both=[r for r in records if r["baseline_status"]=="complete" and r["candidate_status"]=="complete"]
summary={
 "matched_scheduled":len(shared),
 "matched_both_complete":len(both),
 "baseline_complete":sum(r["baseline_status"]=="complete" for r in records),
 "candidate_complete":sum(r["candidate_status"]=="complete" for r in records),
 "baseline_wins":sum(r["baseline_win"] is True for r in both),
 "candidate_wins":sum(r["candidate_win"] is True for r in both),
 "planner_decisions":sum(r["planner_decisions"] for r in records),
 "planner_activated_games":sum(r["planner_decisions"]>0 for r in records),
 "cast_triggers_baseline_mean":statistics.mean(r["baseline_cast_triggers"] for r in both) if both else None,
 "cast_triggers_candidate_mean":statistics.mean(r["candidate_cast_triggers"] for r in both) if both else None,
 "incubator_transforms_baseline_mean":statistics.mean(r["baseline_incubator_transforms"] for r in both) if both else None,
 "incubator_transforms_candidate_mean":statistics.mean(r["candidate_incubator_transforms"] for r in both) if both else None,
 "disclaimer":"Seed matched at initialization, but post-decision RNG divergence means exact same draws cannot be assumed. Short pilot; no improvement claimed solely from decisions or wins."
}
out=pathlib.Path(args.output)
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"summary":summary,"paired_matches":records},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("BRIMAZ_POLICY_COMPARISON",json.dumps(summary,ensure_ascii=False),flush=True)
if len(shared)<16:
    raise ValueError("Fewer than 16 matched games available")
