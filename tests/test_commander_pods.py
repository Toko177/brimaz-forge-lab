#!/usr/bin/env python3
"""Regression for real Forge active pods. Never a simulated game result."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from commander_pods import PODS,OPPONENTS,ROSTER_VERSION,verify_rosters
from deckbuild_run import OPPONENTS as DECKBUILD_PODS
from run_local_four_ai import ROOT,CANONICAL_DECK_SHA256,validate_decks

assert verify_rosters()
assert ROSTER_VERSION == "2026-10-12-dungeon-replaces-amalia"
assert PODS["aristo"] == ("Brimaz_V3","Kaal_9594008",
                           "Kaal_10347090","Kaal_21930525")
assert PODS["artifact"] == ("Brimaz_V3","Kaal_23328062",
                             "Kaal_11485202","Kaal_10347090")
assert DECKBUILD_PODS == OPPONENTS
assert set(OPPONENTS["aristo"]) & set(OPPONENTS["artifact"]) == {"Kaal_10347090"}
assert all(len(set(decks))==4 for decks in PODS.values())
assert all("Kaal_22193355" not in decks for decks in PODS.values())
assert all(set(decks).issubset(CANONICAL_DECK_SHA256) for decks in PODS.values())
assert len(CANONICAL_DECK_SHA256)==7
assert "Kaal_22193355" in CANONICAL_DECK_SHA256 # original untouched
assert validate_decks(ROOT/"forge_decks",
    ROOT/"canonical/results/forge_normalization/report.json") == CANONICAL_DECK_SHA256
for p in ("scripts/batch.py","scripts/deckbuild_run.py"):
    source=(ROOT/p).read_text(encoding="utf-8")
    assert "from commander_pods import " in source
    assert "Kaal_22193355" not in source
# Explicitly catch future duplicated hardcoded rosters in active runners.
print("FOUR_AI_ACTIVE_ROSTER_PASS active_amalia=0 shared_dungeon=1 "
      "canonical_seven_unchanged=true synthetic_only=true")
