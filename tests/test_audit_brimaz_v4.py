#!/usr/bin/env python3
"""V3 immutability and proposed V4 100-card structural / draw-audit gate.

No Oracle certification or simulated games. Exact role-draw probabilities
are just blind random-card visibility and not proof of power.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_brimaz_v4 import (SWAPS,BRIMAZ_CASTS,REPEATABLE_DRAW,
    SACRIFICE_ACCESS,SACRIFICE_PAYOFF,LAND_SOURCES,FORGE_V3,
    FORGE_V4,REFERENCE,CANDIDATE,validate,report,hypergeom_at_least,both_seen)

# These are the SHA-pinned originals, stored in source before a V4 existed.
from run_local_four_ai import CANONICAL_DECK_SHA256
assert hashlib.sha256(FORGE_V3.read_bytes()).hexdigest()==CANONICAL_DECK_SHA256["Brimaz_V3"]
assert len(CANONICAL_DECK_SHA256)==7
assert len(SWAPS)==21 and len({a for a,b in SWAPS})==21 and len({b for a,b in SWAPS})==21
a,b=validate()
assert len(a)==len(b)==94 and len(b)!=100 # Plains / Swamp quantities >1.
assert a!=b
assert all(b[name]==0 for name in ("Krark-Clan Ironworks","Spawning Pit","Living Death","Activated Sleeper","Anointed Procession","Aron, Benalia's Ruin"))
assert all(b[name]==1 for name in ("Everflowing Chalice","Scrap Trawler"))
assert all(b[name]==1 for name in ("Sunder the Gateway","Stroke of Midnight","Phyrexian Scriptures"))
assert all(b[name]==0 for name in ("Esper Sentinel","Urza's Saga","Phyrexian Altar","Diabolic Intent","The Meathook Massacre"))
assert all(b[name]==1 for name in ("Gixian Infiltrator","Steel Overseer","Resourceful Defense","Phyrexian Awakening","Vault of the Archangel"))
assert all(b[name]==1 for name in ("Mondrak, Glory Dominus","Yawgmoth, Thran Physician"))
data=report()
assert data["method"].startswith("EXACT HYPERGEOMETRIC")
assert set(data["removed"])=={x for x,_ in SWAPS}
assert set(data["added"])=={y for _,y in SWAPS}
assert data["v3"]["possible_land_cards"]==data["v4"]["possible_land_cards"]==38
assert data["v4"]["repeatable_draw_source_names"]>data["v3"]["repeatable_draw_source_names"]
assert data["v4"]["combat_support_or_finisher_cards"]>data["v3"]["combat_support_or_finisher_cards"]
assert data["v4"]["explicit_drain_engine_cards"]<data["v3"]["explicit_drain_engine_cards"]
assert data["v4"]["combat_support_or_finisher_cards"]>=7
assert data["v4"]["targeted_interaction_names"]>=6
assert data["v4"]["early_mana_accelerator_cards"]==data["v3"]["early_mana_accelerator_cards"]+1
assert data["v4"]["p_1plus_early_mana_accelerator_seen_in_10"]>data["v3"]["p_1plus_early_mana_accelerator_seen_in_10"]
assert data["v4"]["ramp_sources_that_can_help_pay_transforms"]>data["v3"]["ramp_sources_that_can_help_pay_transforms"]
assert data["v4"]["targeted_interaction_names"]>data["v3"]["targeted_interaction_names"]
assert data["v4"]["board_sweeper_names"]>=2
assert data["v4"]["board_protection_names"]>=4
assert data["v4"]["brimaz_eligible_cast_names"]>=data["v3"]["brimaz_eligible_cast_names"]
assert data["v4"]["p_1plus_combat_support_seen_in_13"]>data["v3"]["p_1plus_combat_support_seen_in_13"]
assert data["v4"]["p_1plus_repeatable_draw_source_seen_in_10"]>data["v3"]["p_1plus_repeatable_draw_source_seen_in_10"]
assert data["v4"]["p_3plus_land_sources_seen_in_10"]==data["v3"]["p_3plus_land_sources_seen_in_10"]
assert hypergeom_at_least(100,0,10)==0
assert hypergeom_at_least(100,100,10)==1
assert abs(both_seen(100,set(range(3)),set(range(3)),10)-hypergeom_at_least(100,3,10))<1e-12
for source in (REFERENCE,CANDIDATE,FORGE_V4):
    assert source.is_file()
    assert source.read_text().endswith("\n")
print("BRIMAZ_V4_B3_STRUCTURAL_TEST_PASS "+json.dumps({
    "v3":data["v3"],"v4":data["v4"],"board_oriented_swaps":len(SWAPS),
    "gameplay":"NOT_SIMULATED","Oracle":"NOT_CERTIFIED"}))
