#!/usr/bin/env python3
"""Certified-input-required, same-state policy evaluation on real 4-seat Forge logs.

Uses target options that Forge actually gave the AI, never hypothetical spells.
The reference/experimental runs may have diverged; pair statistics are descriptive.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

p=argparse.ArgumentParser()
p.add_argument("--pod",choices=["aristo","artifact"],required=True)
p.add_argument("--rotation",type=int,choices=range(4),required=True)
p.add_argument("--out",type=Path,required=True)
a=p.parse_args()
regex=re.compile(
    r"FOUR_AI_REMOVAL_SHADOW player=(Ai\([1-4]\)-.*?) options=(\d+) "
    r"baseline=(.*?) urgency=(.*?) chosen=(.*?) changed=(true|false) "
    r"baselineScore=(-?\d+) urgencyScore=(-?\d+)"
)
scores={}
for policy,folder in (("baseline","V20-stock-shadow"),("urgent","V20-urgent-shadow")):
    root=Path("results/batch")/a.pod/folder
    games=json.loads((root/"games.json").read_text(encoding="utf-8"))
    if len(games)!=1:raise ValueError(f"One genuine game per AI policy, got {len(games)}")
    game=games[0]
    raw=(root/Path(game["log"]).name).read_text(encoding="utf-8",errors="replace")
    observed=[]
    for ln in raw.splitlines():
        m=regex.search(ln)
        if m:
            player,n,stock,urgency,chosen,diff,stock_score,urgency_score=m.groups()
            observed.append({
                "actor":player,"options":int(n),
                "stock":stock,"urgency":urgency,"actually_chosen":chosen,
                "different":diff=="true",
                "score_stock":int(stock_score),"score_urgent":int(urgency_score)
            })
    # Same state counterfactual consistency: actual Forge choice must reflect
    # the policy it was configured to use. No fake winning action is added.
    bad=[x for x in observed if x["actually_chosen"]!=x[policy if policy=="baseline" else "urgency"]]
    if bad:raise AssertionError(f"{policy} choice mismatch: {bad[:2]}")
    events=[ln for ln in raw.splitlines() if
            ln.startswith(("Turn: ","Phase: ","Combat: ","Add To Stack: ","Game Outcome: "))
            and "Match Duration" not in ln]
    scores[policy]={
        "seats":game["seats"],"seed":game["seed"],"pod":game["pod"],
        "rotation":game["rotation"],"status":game["status"],
        "winner":game["winner_deck"],"brimaz_win":game["brimaz_win"],
        "wall_seconds":game["wall_seconds"],
        "shadow_decision_count":len(observed),
        "changed_target_opportunities":sum(x["different"] for x in observed),
        "candidate_ranking_by_player":dict(Counter(x["actor"] for x in observed)),
        "would_change_by_player":dict(Counter(x["actor"] for x in observed if x["different"])),
        "changed_examples":[x for x in observed if x["different"]][:20],
        "event_sha256":hashlib.sha256("\n".join(events).encode()).hexdigest(),
        "events":len(events)
    }
b,e=scores["baseline"],scores["urgent"]
for k in ("seats","seed","pod","rotation"):
    if b[k]!=e[k]:raise ValueError("Unmatched control/experiment "+k)
if b["rotation"]!=a.rotation:raise ValueError("Wrong rotation")
natural=b["status"]==e["status"]=="complete"
identical=natural and b["event_sha256"]==e["event_sha256"]
report={
    "name":"Same-state legal removal target counterfactual experiment, genuine 4-seat Forge",
    "pod":a.pod,"rotation":a.rotation,"real_forge_jvms":2,
    "control":b,"experiment":e,
    "same_natural_observable_game":identical,
    "ratio_only_if_identical_natural_game":
        round(b["wall_seconds"]/e["wall_seconds"],3)
        if identical and e["wall_seconds"]>0 else None,
    "inference":"A changed hypothetical target does NOT prove a removal spell was cast or that a winner would change.",
    "requires_independent_natural_outcome_and_legality_certification":True,
}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("FOUR_AI_V20_SAME_STATE_REMOVAL",json.dumps({
    "pod":a.pod,"rotation":a.rotation,"both_natural":natural,
    "same_events":identical,"wins":[b["winner"],e["winner"]],
    "control_decisions":b["shadow_decision_count"],"experiment_decisions":e["shadow_decision_count"],
    "would_change_if_enabled":b["changed_target_opportunities"],
    "actually_changed_rankings":e["changed_target_opportunities"],
    "players":e["candidate_ranking_by_player"]
},ensure_ascii=False),flush=True)
