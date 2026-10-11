#!/usr/bin/env python3
"""Synthetic parser fixtures; intentionally NOT evidence of real Magic games."""
from pathlib import Path
import json
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_v33_real_strategy import audit

raw = "Ai(1)-Brimaz vs Ai(2)-A vs Ai(3)-B vs Ai(4)-C - one game of Commander seed 100\n"
raw += "Turn: Turn 1\n"
proposal = ("FOUR_AI_V33_STRATEGIC_PROPOSAL player=Ai(2)-A turn=3 "
    "first=Arcane Signet role=RAMP second=A Commander alternative=3/3 "
    "immediate=24 future=20 margin=900 mana=3 life=40 "
    "opponentPower1=5 opponentPower2=4 realForgeLegalAndPayable=true\n")
accepted = ("FOUR_AI_V33_STRATEGIC_ACTION player=Ai(2)-A turn=3 "
            "first=Arcane Signet acceptedByStockForgeAI=true\n")
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)
    (path/"baseline.log").write_text(raw+"Ai(4)-C\n")
    (path/"experiment.log").write_text(raw+proposal+accepted+"Ai(4)-C\n")
    def report():
        return {
            "type":"Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B",
            "reference_provenance":{"policy":"v17_strict"},
            "experiment_provenance":{"policy":"v33_strategy"},
            "real_process_pairs":1,"real_forge_jvm_processes":2,
            "both_natural_pairs":1,"pairs_with_any_censor_or_fault":0,
            "natural_pairs_with_different_winner":0,
            "pairs":[{"reference":{
                "log":str(path/"baseline.log"),"status":"complete"},
                "experiment":{"log":str(path/"experiment.log"),"status":"complete",
                "pod":"artifact","rotation":0},
                "event_sha256":"ref123",
                }]
        }
    x=audit(report())
    assert x["genuine_full_game_pairs"]==1
    assert x["strategy_proposals_before_original_forge_ai_approval"]==1
    assert x["strategy_evaluations_accepted_not_proven_resolved"]==1
    assert x["seat_counts"]=={2:1}
    assert x["role_counts"]=={"RAMP":1}
    assert x["examples"][0]["first"]=="Arcane Signet"
    (path/"baseline.log").write_text(raw+proposal+accepted+"Ai(4)-C\n")
    try:
        audit(report())
        raise AssertionError("Control actions not rejected")
    except ValueError:
        pass
    (path/"baseline.log").write_text(raw+"Ai(4)-C\n")
    (path/"experiment.log").write_text(raw+accepted+"Ai(4)-C\n")
    try:
        audit(report())
        raise AssertionError("Action without recorded proposal not rejected")
    except ValueError:
        pass
    (path/"experiment.log").write_text(raw+proposal+"Ai(4)-C\n")
    x=audit(report())
    assert x["strategy_proposals_before_original_forge_ai_approval"]==1
    assert x["strategy_evaluations_accepted_not_proven_resolved"]==0
print("FOUR_AI_V33_SYNTHETIC_AUDIT_TEST_PASS real_game_claims=0")
