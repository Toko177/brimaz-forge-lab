#!/usr/bin/env python3
"""Only synthetic parser fixtures, NEVER actual Forge Commander outcome evidence."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_v29_commander_tempo import inspect

test=("Turn: Turn 1 (Ai(1)-Brimaz V3)\n"
      "FOUR_AI_COMMANDER_TEMPO_SHADOW player=Ai(1)-Brimaz V3 "
      "globalTurn=17 life=27 greatestVisibleEnemyPower=5 "
      "legalEngineAlternatives=2 engineNames=Orzhov_Signet,Spawning_Pit selected=Brimaz\n"
      "FOUR_AI_COMMANDER_TEMPO_SHADOW player=Ai(1)-Brimaz V3 "
      "globalTurn=25 life=11 greatestVisibleEnemyPower=7 "
      "legalEngineAlternatives=0 engineNames=none selected=Brimaz\n")
items=inspect(test)
assert len(items)==2
assert items[0]["global_turn"]==17
assert items[0]["legally_payable_engine_option_count"]==2
assert items[0]["legal_engine_names"]==["Orzhov_Signet","Spawning_Pit"]
assert items[1]["legally_payable_engine_option_count"]==0
assert items[1]["legal_engine_names"]==[]
assert not inspect("No real Commander decisions")
print("FOUR_AI_V29_TEMPO_SHADOW_SYNTHETIC_TEST_PASS")
