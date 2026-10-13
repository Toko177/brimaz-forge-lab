#!/usr/bin/env python3
"""Fail-closed regression gate for isolated V4 -> V5 cheap-trigger hypothesis."""
import math
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from brimaz_v5_tempo_audit import run,at_least_one

report=run(12)
assert report["copies"]==100
assert report["changed_cards"]=={"Throne of Geth":"Vault Skirge","Myr Sire":"Changeling Outcast"}
assert report["v4_known_one_mana_followup_options"]==0
assert report["v5_one_mana_followup_options_any_mana_unspent"]==1
assert report["v5_one_mana_followup_options_black_mana_unspent"]==2
assert report["prob_at_least_one_generic_mana_followup_v4"]==0
assert report["prob_at_least_one_black_mana_followup_v4"]==0
assert report["prob_at_least_one_generic_mana_followup_v5"]==0.12
assert report["prob_at_least_one_black_mana_followup_v5"]==0.226667
assert math.isclose(at_least_one(100,2,12),1-(88*87)/(100*99),rel_tol=0,abs_tol=1e-14)
assert run(7)["prob_at_least_one_black_mana_followup_v5"]==0.135758
assert at_least_one(100,0,12)==0
assert at_least_one(100,100,12)==1
for invalid in [-1,101]:
    try:
        at_least_one(100,2,invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid sample size did not fail")

assert "winrate" in " ".join(report["not_estimated"])
assert len(report["explicit_losses"])==2
print("BRIMAZ_V5_TEMPO_TARGETED_TEST_PASS")
