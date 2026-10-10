#!/usr/bin/env python3
"""Negative unit tests: synthetic records may not pass real-game evidence gate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from assess_simulator_readiness import evaluate
base={"identity":{"seed":1,"status":"clock_censored","observed_turn_events":2},
      "warnings":["No natural finished-game claim"],
      "players":[{"seat":i,"deck":f"Deck{i}","turns_taken":1,
                  "lands_played":0,"spells_cast":0,"abilities_activated":0,
                  "slow_ai_evaluations":0} for i in range(1,5)]}
bad=evaluate({"games":[base]},min_games=8)
assert bad["engine_pilot_gate"]=="BLOCKED",bad
assert not bad["ready_for_exploratory_4_ai_simulation"]
assert bad["statistically_validated_brimaz_winrate"] is False
assert any("naturally completed" in x for x in bad["blocking_issues"])
assert any("fewer than 4" in x for x in bad["blocking_issues"])
assert any("did not log" in x for x in bad["blocking_issues"])
print("FOUR_SEAT_READINESS_GATE_NEGATIVE_TEST_PASS never_claim_winrate=true")

# SYNTHETIC POSITIVE-CENSOR REGRESSION: an honest clock cutoff must NOT
# masquerade as a Java engine bug when a 16-match pilot otherwise has
# 14 real-format naturally completed and productive four-seat histories.
from copy import deepcopy
sample=[]
for n in range(16):
    row=deepcopy(base)
    row["identity"]={"pod":"aristo" if n<8 else "artifact",
                     "rotation":n%4,"seed":1000+n,
                     "status":"clock_censored" if n in (0,8) else "complete",
                     "observed_turn_events":17}
    row["warnings"]=(
       ["No natural finished-game claim: clock_censored"] if n in (0,8) else [])
    for x in row["players"]:
        x["turns_taken"]=4
        x["lands_played"]=3
        x["spells_cast"]=2
        x["abilities_activated"]=1
    sample.append(row)
pass_report=evaluate({"games":sample},min_games=8)
assert pass_report["engine_pilot_gate"]=="PASS",pass_report
assert pass_report["naturally_finished_count"]==14
assert pass_report["expected_clock_censored_games_kept_in_denominator"]==2
assert not pass_report["unexpected_warnings"]
# A genuine contradictory game warning remains BLOCKING even for censored games.
broken=deepcopy(sample)
broken[0]["warnings"].append("Fatal Forge error present")
error_report=evaluate({"games":broken},min_games=8)
assert error_report["engine_pilot_gate"]=="BLOCKED",error_report
assert error_report["unexpected_warnings"]
print("FOUR_SEAT_READINESS_SYNTHETIC_CENSOR_CONSISTENCY_PASS")
