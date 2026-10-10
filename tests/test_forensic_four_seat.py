#!/usr/bin/env python3
"""Tiny synthetic parser fixture; never counted as an actual Forge game."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from forensic_four_seat import inspect_game,aggregate,render_markdown

record={
    "seats":["Brimaz_V3","Kaal_22193355","Kaal_11485202","Kaal_10347090"],
    "pod":"artifact","policy":"synthetic-parser-only","rotation":0,
    "seed":42,"status":"complete","winner_seat":1,"wall_seconds":1.0
}
raw="""Ai(1)-Brimaz V3 [Default] vs Ai(2)-EDH Amalia [Default] vs Ai(3)-EDH Urza [Default] vs Ai(4)-EDH Lathril [Default] - one game of Commander seed 42
Turn: Turn 1 (Ai(1)-Brimaz V3)
Land: Ai(1)-Brimaz V3 played Plains (100)
Add To Stack: Ai(1)-Brimaz V3 cast Brimaz, Blight of Oreskos
Add To Stack: Ai(1)-Brimaz V3 triggered Brimaz, Blight of Oreskos
Add To Stack: Ai(1)-Brimaz V3 activated Incubator Token
Turn: Turn 2 (Ai(2)-EDH Amalia)
Add To Stack: Ai(2)-EDH Amalia cast Ajani's Welcome
Turn: Turn 3 (Ai(1)-Brimaz V3)
Combat: Ai(1)-Brimaz V3 assigned Brimaz, Blight of Oreskos (300) to attack Ai(2)-EDH Amalia.
Damage: Brimaz, Blight of Oreskos (300) deals 4 combat damage to Ai(2)-EDH Amalia.
Damage: Ai(2)-EDH Amalia receives 1 poison counter from Ai(1)-Brimaz V3
Life: Life: Ai(2)-EDH Amalia 40 > 36
AI_EVAL_SLOW_V10: player=Ai(1)-Brimaz V3 globalTurn=3 phase=COMBAT_BEGIN elapsedMs=2500 timeoutSecs=5 listed=6 considered=2 lastCandidate=Plains
FOUR_AI_TARGET: controller=Ai(1)-Brimaz V3 chosen=Ai(2)-EDH Amalia visibleSafeDamage=4 visibleSafePoison=0
FOUR_AI_V17_COVERAGE controller=Ai(1)-Brimaz V3 threatPlayers=3 baselinePermille=900 afterPermille=0 reserved=1 turn=3 proactive=true
Zone Change: Brimaz, Blight of Oreskos (300) was put into Graveyard from Battlefield.
Game Outcome: Ai(1)-Brimaz V3 has won because all opponents have lost
Game Outcome: Ai(2)-EDH Amalia has lost because life total reached 0
"""
g=inspect_game(record,raw)
a,b=g["players"][0],g["players"][1]
assert a["turns_taken"]==2,a
assert a["lands_played"]==1,a
assert a["spells_cast"]==1,a
assert a["commander_casts_observed"]==1,a
assert g["brimaz"]["observed_incubator_transformations"]==1,g
assert a["triggers_observed"]==1,a
assert a["combat_damage_to_players"]==4,a
assert a["slow_ai_evaluations"]==1 and a["slowest_evaluation_ms"]==2500,a
assert a["defensive_reserves"]==1 and a["peak_model_risk_permille"]==900,a
assert a["target_checks"]==1,a
assert b["combat_damage_received"]==4 and b["poison_counters_received"]==1,b
assert g["brimaz"]["commander_battlefield_exits"]==1,g
assert g["identity"]["observed_turn_events"]==3,g
assert g["warnings"]==[],g
assert sum(x["winner_in_raw_log"] for x in g["players"])==1,g
r={"summary":aggregate([g]),"games":[g]}
assert "Brimaz" in render_markdown(r)
bad=inspect_game({**record,"status":"clock_censored","winner_seat":None},raw)
assert any("No natural" in w for w in bad["warnings"]),bad
print("FOUR_SEAT_FORENSIC_TEST_PASS synthetic_parser_fixture_only=true")
