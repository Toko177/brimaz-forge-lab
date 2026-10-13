#!/usr/bin/env python3
"""V43 real seat-name contract regression; synthetic identities, canonical files.

Checks actual 7 original Forge DCK [metadata] labels in the repository.
No fabricated Forge game or claimed victory.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from forge_seat_identity import (
    canonical_label, display_for_seat, resolve_ai_player)
from run_local_four_ai import ROOT,validate_decks

deck_dir=ROOT/"forge_decks"
assert len(validate_decks(deck_dir,
    ROOT/"canonical/results/forge_normalization/report.json"))==7
assert canonical_label("Brimaz_V3",deck_dir)=="Brimaz V3"
assert canonical_label("Kaal_22193355",deck_dir)=="EDH Amalia"
assert canonical_label("Kaal_21930525",deck_dir)=="EDH Zimone and Dina aristo"
assert canonical_label("Kaal_23328062",deck_dir)=="EDH Lathril Nico"
assert display_for_seat("Brimaz_Challenger_A",deck_dir,True)=="Brimaz Challenger A"

seats=["Brimaz_V3","Kaal_21930525","Kaal_22193355","Kaal_11485202"]
cases=["Ai(1)-Brimaz V3","Ai(2)-EDH Zimone and Dina aristo",
       "Ai(3)-EDH Amalia","Ai(4)-EDH Urza"]
for i,p in enumerate(cases):
    assert resolve_ai_player(p,seats,deck_dir)==seats[i]
mirrors=["Brimaz_Challenger_A","Brimaz_Challenger_B",
         "Brimaz_Reference_A","Brimaz_Reference_B"]
assert resolve_ai_player("Ai(3)-Brimaz Reference A",mirrors,
                         deck_dir,True)==mirrors[2]
for invalid in ("Ai(2)-Brimaz V3","Ai(0)-Brimaz V3",
                "Ai(5)-Brimaz V3","Ai(1)-Brimaz V3 forged",
                "Ai(1)-EDH Amalia","Ai(12)-Brimaz V3",
                "Brimaz V3", "Ai(1)-Brimaz V3\nAi(2)-EDH Amalia"):
    try:resolve_ai_player(invalid,seats,deck_dir)
    except ValueError:pass
    else:raise AssertionError("Accepted unsafe Forge player identity: "+repr(invalid))
try:display_for_seat("Brimaz_Challenger_Z",deck_dir,True)
except ValueError:pass
else:raise AssertionError("Unknown mirror label accepted")
print("V43_FORGE_SEAT_IDENTITY_PASS canonical_metadata=7 no_real_games_claimed=true")
