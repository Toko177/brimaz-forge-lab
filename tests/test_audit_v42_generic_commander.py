#!/usr/bin/env python3
"""Synthetic audit fixtures only; NO fake results treated as Forge play."""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_v42_generic_commander import audit

with tempfile.TemporaryDirectory() as d:
    root=Path(d)
    seats=["Brimaz_V3","Kaal_9594008","Kaal_10347090","Kaal_21930525"]
    ref=root/"reference.log"
    exp=root/"experiment.log"
    ref.write_text("Turn: Turn 1\n",encoding="utf-8")
    window=("FOUR_AI_V42_WINDOW player={} turn=5 options=2 ranked=1 "
            "margin=18 pressure=false reason=distinct_public_development_preference "
            "nativeForgeApprovalPending=true\n")
    approval=("FOUR_AI_V42_STOCK_APPROVED player={} turn=5 card=Any Card "
              "rejectedEarlier=0 nativeForgeAIDecision=true notResolvedYet=true\n")
    exp.write_text("Turn: Turn 1\n"+"".join(window.format(x) for x in seats)
                   +approval.format(seats[1]),encoding="utf-8")
    refp={"policy":"v37_stock_control","patches":["same-real-source"],
          "canonical_seven_deck_sha256":{"pinned":"hash"},
          "java_tool_options":"-Dbrimaz.v37ControlledDuel=true"}
    expp={**refp,"policy":"v42_commander_general",
          "java_tool_options":"-Dbrimaz.v37ControlledDuel=true "
                              "-Dcommander.v42GeneralPolicy=true"}
    def game(path):
        return {"seats":seats,"status":"complete","winner":"Brimaz_V3",
                "log":str(path)}
    obj={"type":"Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B",
         "reference_provenance":refp,"experiment_provenance":expp,
         "real_process_pairs":1,
         "pairs":[{"pod":"aristo","rotation":0,"repeat":0,"seed":20261129,
                   "reference":game(ref),"experiment":game(exp)}]}
    r=audit(obj)
    assert r["four_seat_observed_distinct_decks"]==sorted(seats)
    assert r["approved_not_resolved_by_deck"]=={seats[1]:1}
    assert r["natural_pairs"]==1 and not r["skill_gain_proven"]
    ref.write_text(window.format(seats[0]),encoding="utf-8")
    try:audit(obj);raise AssertionError("control contamination passed")
    except ValueError:pass
    ref.write_text("Turn: Turn 1\n",encoding="utf-8")
    exp.write_text(window.format(seats[0])+approval.format(seats[0]))
    try:audit(obj);raise AssertionError("one-deck Brimaz-only behavior passed")
    except ValueError:pass
    exp.write_text(window.format("Unknown_Player")+approval.format(seats[0]))
    try:audit(obj);raise AssertionError("unknown participant passed")
    except ValueError:pass
    exp.write_text("".join(window.format(x) for x in seats))
    try:audit(obj);raise AssertionError("zero real approvals passed")
    except ValueError:pass
    assert audit(obj,require_approvals=False)["natural_pairs"]==1
print("V42_GENERIC_AUDIT_FIXTURE_PASS synthetic_only=true")
