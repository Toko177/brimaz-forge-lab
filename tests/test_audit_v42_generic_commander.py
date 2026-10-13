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
    from forge_seat_identity import display_for_seat
    displays=[f"Ai({i+1})-"+display_for_seat(deck,
              Path(__file__).resolve().parents[1]/"forge_decks")
              for i,deck in enumerate(seats)]
    window=("FOUR_AI_V42_WINDOW player={} turn=5 options=2 ranked=1 "
            "margin=18 pressure=false reason=distinct_public_development_preference "
            "nativeForgeApprovalPending=true\n")
    approval=("FOUR_AI_V42_STOCK_APPROVED player={} turn=5 card=Any Card "
              "rejectedEarlier=0 nativeForgeAIDecision=true notResolvedYet=true\n")
    exp.write_text("Turn: Turn 1\n"+"".join(window.format(x) for x in displays)
                   +approval.format(displays[1]),encoding="utf-8")
    refp={"policy":"v37_stock_control","patches":["same-real-source"],
          "canonical_seven_deck_sha256":{"pinned":"hash"},
          "java_tool_options":"-Dbrimaz.v37ControlledDuel=true"}
    refp["roster_version"]="synthetic-roster-contract"
    refp["active_pods"]={"aristo":seats}
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
    assert r["roster_version"]=="synthetic-roster-contract"
    assert r["by_pod"]["aristo"]["natural"]==1
    assert r["by_pod"]["aristo"]["censored"]==0
    ref.write_text(window.format(displays[0]),encoding="utf-8")
    try:audit(obj);raise AssertionError("control contamination passed")
    except ValueError:pass
    ref.write_text("Turn: Turn 1\n",encoding="utf-8")
    exp.write_text(window.format(displays[0])+approval.format(displays[0]))
    try:audit(obj);raise AssertionError("one-deck Brimaz-only behavior passed")
    except ValueError:pass
    exp.write_text(window.format("Ai(1)-EDH WRONG NAME")+approval.format(displays[0]))
    try:audit(obj);raise AssertionError("unknown participant passed")
    except ValueError:pass
    exp.write_text("".join(window.format(x) for x in displays))
    try:audit(obj);raise AssertionError("zero real approvals passed")
    except ValueError:pass
    assert audit(obj,require_approvals=False)["natural_pairs"]==1
    # V43 A/B: only seat 1 is experimental; other three remain Forge.
    obj["experiment_provenance"]={
        **expp, "policy":"v43_commander_single_seat",
        "java_tool_options":expp["java_tool_options"]
                             +" -Dcommander.v43TargetSeat=1"}
    exp.write_text(window.format(displays[0])+approval.format(displays[0]),
                   encoding="utf-8")
    isolated=audit(obj,min_distinct_decks=1)
    assert isolated["head_to_head_one_challenger_vs_three_controls"]
    assert isolated["distinct_rotated_target_decks"]==[seats[0]]
    assert isolated["natural_both_candidate_win_pairs"]==1
    assert isolated["natural_candidate_only_wins"]==0
    assert isolated["by_pod"]["aristo"]["both_candidate_wins"]==1
    exp.write_text(window.format(displays[1])+approval.format(displays[1]),
                   encoding="utf-8")
    try:audit(obj,min_distinct_decks=1);raise AssertionError("wrong seat got V43")
    except ValueError:pass
    obj["experiment_provenance"]["java_tool_options"] = expp["java_tool_options"]
    try:audit(obj,min_distinct_decks=1);raise AssertionError("V43 missing target flag")
    except ValueError:pass
    obj["experiment_provenance"]["java_tool_options"] += " -Dcommander.v43TargetSeat=1"
    exp.write_text(window.format(displays[0])+approval.format(displays[0]),
                   encoding="utf-8")
    try:audit(obj,min_distinct_decks=3);raise AssertionError("one target deck called multideck")
    except ValueError:pass
    obj["experiment_provenance"]["roster_version"]="forged-other-opponents"
    try:
        audit(obj,min_distinct_decks=1)
        raise AssertionError("Incompatible pod roster accepted")
    except ValueError as exc:
        assert "roster" in str(exc)
print("V42_GENERIC_AUDIT_FIXTURE_PASS synthetic_only=true")
