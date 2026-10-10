#!/usr/bin/env python3
"""SYNTHETIC forensic unit test. No synthetic Magic results enter real reports."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from triage_real_four_ai_strategy import audit,markdown
def player(seat,deck):
    return {
      "seat":seat,"deck":deck,"turns_taken":5,"lands_played":4,
      "spells_cast":3,"abilities_activated":1,"triggers_observed":2,
      "commander_casts_observed":0,
      "attacks_declared":1,"combat_damage_to_players":4,
      "combat_damage_received":3,"counter_spells_considered":0,
      "counter_profile_declines":0,"counter_commander_threats":0,
      "counter_lethal_life_threats":0,"counter_override_acceptances_not_casts":0,
      "slow_ai_evaluations":0,"winner_in_raw_log":False,
    }
decks=["Brimaz_V3","A","B","C"]
p=[player(i+1,d) for i,d in enumerate(decks)]
p[0]["commander_casts_observed"]=4
p[0]["lands_played"]=0
p[0]["slow_ai_evaluations"]=3
p[1]["winner_in_raw_log"]=True
sample={
 "type":"Forge four-seat action-level diagnostic (NOT a legal-action oracle)",
 "games":[{
   "identity":{"pod":"aristo","rotation":0,"seed":42,
               "policy":"synthetic_fixture_only","status":"complete"},
   "players":p,
   "brimaz":{"windows":5,"windows_with_phyrexian_tokens":3,
             "windows_with_outlet":0,"commander_battlefield_exits":3,
             "observed_incubator_transformations":2},
 }],
}
out=audit(sample)
assert out["game_count"]==1
assert out["signals"]["brimaz_commander_recast_heavy_games"]==1
assert out["signals"]["observed_3plus_turns_without_lands"]==1
assert out["signals"]["seats_with_slow_ai_decisions"]==1
assert out["signals"]["brimaz_phyrexian_windows_no_outlet_game"]==1
assert out["signals"]["incubator_token_activations_not_confirmed_transformations"]==2
assert out["per_deck"]["A"]["natural_observed_wins_unverified"]==1
assert "NOT a proven transform" not in markdown(out) or "Incubator Token activated" in markdown(out)
try:
    audit({"type":"invalid","games":sample["games"]})
    raise AssertionError("Accepted unrelated artifacts")
except ValueError:pass
bad=dict(sample)
bad["games"]=[sample["games"][0],sample["games"][0]]
try:
    audit(bad)
    raise AssertionError("Accepted duplicated four-seat game as two genuine matches")
except ValueError as exc:
    assert "Duplicate" in str(exc)
print("FOUR_AI_V27_STRATEGIC_TRIAGE_SYNTHETIC_TEST_PASS")
