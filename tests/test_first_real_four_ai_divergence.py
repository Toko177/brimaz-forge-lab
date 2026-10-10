#!/usr/bin/env python3
"""SYNTHETIC audit fixture; NOT a genuine Forge gameplay outcome."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from first_real_four_ai_divergence import inspect
identity={"pod":"aristo","rotation":0,"seed":5,"reference_status":"complete",
          "experimental_status":"complete","reference_winner":"Brimaz_V3",
          "experimental_winner":"Kaal_9594008"}
header=("Turn: Turn 1 (Ai(1)-Brimaz V3)\n"
        "Phase: Upkeep\n"
        "Add To Stack: Ai(1)-Brimaz V3 cast Sol Ring\n")
a=header+"AI_EVAL_TIMEOUT_V10: player=Ai(1)-Brimaz V3 globalTurn=1 phase=MAIN1\n"+"Life: Life: Ai(1)-Brimaz V3 40 > 39\n"
b=header+"AI_EVAL_TIMEOUT_V10: player=Ai(1)-Brimaz V3 globalTurn=1 phase=MAIN1\n"+"Life: Life: Ai(1)-Brimaz V3 40 > 37\n"
v=inspect(a,b,identity)
assert not v["entire_observable_event_sequences_equal"]
assert v["first_mismatch_index"]==3
assert v["reference_timeouts_before_mismatch"]==1
assert v["experimental_timeouts_before_mismatch"]==1
assert v["reference_at_mismatch"].endswith("40 > 39")
assert v["experimental_at_mismatch"].endswith("40 > 37")
w=inspect(a,a,identity)
assert w["entire_observable_event_sequences_equal"]
assert w["first_mismatch_index"] is None
assert w["reference_total_timeouts"]==1
print("FOUR_AI_FIRST_DIVERGENCE_SYNTHETIC_TEST_PASS")
