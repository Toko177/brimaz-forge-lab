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
