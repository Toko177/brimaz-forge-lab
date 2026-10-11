#!/usr/bin/env python3
"""SYNTHETIC UNIT FIXTURES ONLY. No fabricated matches enter real evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from aggregate_v25_eight_seats import combine

PODS={
    "aristo":["Brimaz_V3","Kaal_9594008","Kaal_10347090","Kaal_21930525"],
    "artifact":["Brimaz_V3","Kaal_23328062","Kaal_11485202","Kaal_22193355"],
}
def fixture(pod,rot):
    seats=PODS[pod][rot:]+PODS[pod][:rot]
    ref={"pod":pod,"rotation":rot,"seed":20261025+10000*rot,
         "seats":seats,"status":"complete","winner":seats[1],
         "brimaz_win":seats[1]=="Brimaz_V3","wall_seconds":20.0,
         "events_sha256":"abc","events_count":100,
         "ai_timeout_count":0,"exact_negative_combat_trigger_evaluations_pruned":0}
    exp={**ref,"wall_seconds":18.0,
         "exact_negative_combat_trigger_evaluations_pruned":87,
         "filter_shutdown_summary_seen":True}
    return {"reference":ref,"experiment":exp,"real_jvms":2,
            "same_observable_complete_game":True,
            "speed_ratio_only_when_identical_natural_game":1.111}
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    for pod in PODS:
        for rot in range(4):
            (root/f"{pod}_rotation{rot}.json").write_text(json.dumps(fixture(pod,rot)))
    good=combine(root)
    assert good["real_independent_forge_jvm_processes"]==16
    assert good["matched_two_policy_games"]==8
    assert good["natural_pairs_with_identical_observable_actions"]==8
    assert good["pruned_impossible_ai_trigger_evaluations"]==8*87
    assert good["descriptive_speedup_on_natural_identical_events_only"]["median_baseline_over_optimized"]>1
    (root/"aristo_rotation3.json").unlink()
    try:combine(root);raise AssertionError("Missing rotation was accepted")
    except ValueError as exc:assert "Exactly 8" in str(exc)
    (root/"aristo_rotation3.json").write_text(json.dumps(fixture("aristo",3)))
    bad=fixture("aristo",1)
    bad["experiment"]["status"]="clock_censored"
    bad["experiment"]["winner"]=None
    bad["same_observable_complete_game"]=False
    bad["speed_ratio_only_when_identical_natural_game"]=None
    (root/"aristo_rotation1.json").write_text(json.dumps(bad))
    mixed=combine(root)
    assert mixed["censored_or_nonnatural_pairs"]==1
    assert mixed["natural_pairs_with_identical_observable_actions"]==7
    other=fixture("aristo",1)
    other["experiment"]["filter_shutdown_summary_seen"]=False
    (root/"aristo_rotation1.json").write_text(json.dumps(other))
    try:combine(root);raise AssertionError("No real Java event count accepted")
    except ValueError as exc:assert "counter absent" in str(exc)
    fake=fixture("aristo",1)
    fake["experiment"]["winner"]="Unknown"
    (root/"aristo_rotation1.json").write_text(json.dumps(fake))
    try:combine(root);raise AssertionError("Unknown Forge winner accepted")
    except ValueError as exc:assert "non-player" in str(exc)
print("FOUR_AI_V25_AGGREGATE_SYNTHETIC_REGRESSION_PASS")
