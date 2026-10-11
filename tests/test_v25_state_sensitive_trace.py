#!/usr/bin/env python3
"""Clearly synthetic regression ONLY; never count fixtures as true Forge matches."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
seats=["Brimaz_V3","Kaal_9594008","Kaal_10347090","Kaal_21930525"]
HEADER="Ai(1)-Brimaz V3 vs Ai(2)-P2 vs Ai(3)-P3 vs Ai(4)-P4 - one game of Commander seed 12345\n"
EVENTS=("Turn: Turn 1 (Ai(1)-Brimaz V3)\n"
        "Phase: Beginning of turn\n"
        "Add To Stack: Ai(1)-Brimaz V3 cast Sol Ring\n"
        "Life: Life: Ai(1)-Brimaz V3 40 > 39\n"
        "Damage: Test deals 1 combat damage to Ai(1)-Brimaz V3.\n"
        "Game Outcome: Ai(1)-Brimaz V3 has won because all opponents have lost.\n")
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    for tag in ("V24-stock-trigger","V24-fast-negative-trigger"):
        folder=root/"results/batch/aristo"/tag
        folder.mkdir(parents=True)
        rec={"pod":"aristo","rotation":0,"repeat":0,"seed":12345,
             "seats":seats,"brimaz_seat":1,"status":"complete",
             "winner_deck":"Brimaz_V3","winner_seat":1,
             "brimaz_win":True,"wall_seconds":42.0,
             "log":"fixture.log"}
        (folder/"games.json").write_text(json.dumps([rec]))
        text=HEADER+EVENTS
        if tag=="V24-fast-negative-trigger":
            text+="FOUR_AI_FAST_COMBAT_TRIGGER_PRUNED count=17\n"
        (folder/"fixture.log").write_text(text)
    experiment=root/"results/batch/aristo/V24-fast-negative-trigger/fixture.log"
    script=ROOT/"scripts/audit_v24_combat_prune.py"
    out=root/"audit.json"
    cmd=[sys.executable,str(script),"--pod","aristo","--rotation","0","--out",str(out)]
    r=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
    assert r.returncode==0,(r.stdout,r.stderr)
    identical=json.loads(out.read_text())
    assert identical["same_observable_complete_game"]
    assert identical["experiment"]["exact_negative_combat_trigger_evaluations_pruned"]==17
    experiment.write_text(HEADER+EVENTS.replace("40 > 39","40 > 38")
        +"FOUR_AI_FAST_COMBAT_TRIGGER_PRUNED count=17\n")
    r=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
    assert r.returncode==0,(r.stdout,r.stderr)
    divergent=json.loads(out.read_text())
    assert not divergent["same_observable_complete_game"],"Life change falsely treated as identical"
    assert divergent["speed_ratio_only_when_identical_natural_game"] is None
    experiment.write_text("no real four-seat match declaration\n"+EVENTS)
    r=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
    assert r.returncode!=0 and "Not a genuine declared four-AI" in r.stderr
print("FOUR_AI_V25_STATE_TRACE_SYNTHETIC_REGRESSION_PASS")
