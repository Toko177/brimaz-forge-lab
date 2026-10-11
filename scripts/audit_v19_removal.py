#!/usr/bin/env python3
"""Paired actual Forge 4-AI removal urgency opportunity and outcome evidence.

An urgency score is an evaluation, NOT proof a removal spell was cast or the
target was legal in some counterfactual turn. Equal seeds may diverge by timing.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--pod",choices=["aristo","artifact"],required=True)
p.add_argument("--rotation",type=int,choices=range(4),required=True)
p.add_argument("--out",type=Path,required=True)
args=p.parse_args()
root=Path("results/batch")/args.pod
records={}
for label,tag in (("reference","V18-removal-control"),
                  ("experimental","V19-removal-urgency")):
    g=json.loads((root/tag/"games.json").read_text(encoding="utf-8"))
    if len(g)!=1:raise ValueError("Expected one true Forge process for "+label)
    r=g[0]
    raw=(root/tag/Path(r["log"]).name).read_text(encoding="utf-8",errors="replace")
    evaluations=re.findall(r"FOUR_AI_REMOVAL_URGENCY target=(.*?) player=(.*?) "
                           r"scoreBonus=(\d+) predictedDamage=(\d+)",raw)
    spell_targets=[s for s in raw.splitlines() if s.startswith("Add To Stack: ")
                   and " targeting [" in s]
    events=[s for s in raw.splitlines()
            if s.startswith(("Turn: ","Phase: ","Combat: ","Add To Stack: ","Game Outcome: "))
            and "Match Duration" not in s]
    records[label]={
        "pod":r["pod"],"rotation":r["rotation"],"seed":r["seed"],
        "seats":r["seats"],"status":r["status"],
        "winner":r["winner_deck"],"brimaz_win":r["brimaz_win"],
        "wall_seconds":r["wall_seconds"],
        "raw_log_sha256":hashlib.sha256(raw.encode()).hexdigest(),
        "observable_events_sha256":hashlib.sha256("\n".join(events).encode()).hexdigest(),
        "targeted_stack_actions":len(spell_targets),
        "urgency_evaluations":len(evaluations),
        "by_ai_controller":dict(collections.Counter(v[1] for v in evaluations)),
        "score_bonus_counts":dict(collections.Counter(v[2] for v in evaluations)),
        "unique_urgent_targets_observed":sorted(set(v[0] for v in evaluations)),
        "ai_quality_signatures":r.get("ai_quality_signatures",{}),
    }
a,b=records["reference"],records["experimental"]
for key in ("pod","rotation","seed","seats"):
    if a[key]!=b[key]:raise ValueError("Not a matched Forge pod/rotation/seed: "+key)
if a["rotation"]!=args.rotation:raise ValueError("Rotation differs from requested matrix")
natural=a["status"]==b["status"]=="complete"
same=natural and a["observable_events_sha256"]==b["observable_events_sha256"]
report={
    "experiment":"V19 four-seat public imminently-lethal removal priority",
    "real_jvm_processes":2,"pod":args.pod,"rotation":args.rotation,
    "reference":a,"experimental":b,
    "same_observed_complete_game":same,
    "identical_natural_game_speed_ratio":round(a["wall_seconds"]/b["wall_seconds"],3)
        if same and b["wall_seconds"]>0 else None,
    "limits":[
        "A target priority evaluation is NOT a cast spell, a legal target chosen, or a proven beneficial removal.",
        "One game pair per matrix is insufficient to infer winrate improvement.",
        "Same seed does not guarantee same mutable Forge game path.",
        "Legality and natural-end certificate needs Scryfall+raw-game certification separately.",
    ],
}
args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("FOUR_AI_V19_REMOVAL_AUDIT",json.dumps({
 "pod":args.pod,"rotation":args.rotation,"natural_both":natural,
 "same_events":same,"reference_winner":a["winner"],"experimental_winner":b["winner"],
 "evaluations":b["urgency_evaluations"],"controllers":b["by_ai_controller"],
 "raw_targeted_stack_actions":b["targeted_stack_actions"]
},ensure_ascii=False),flush=True)
