#!/usr/bin/env python3
"""Static synthetic checks for the real-JVM mirror. No mocked results claimed."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from run_v37_mirror import (
    make_mirror_decks,make_four_mirror_decks,classify,binomial_two_sided,
    summarize,category,expected_display_name,verify_v41_pilot_identity,PODS,FOUR_MIRRORS)
from run_local_four_ai import sha,ROOT
with tempfile.TemporaryDirectory() as td:
    for pod in PODS:
        decks=Path(td)/pod
        seats=make_mirror_decks(ROOT/"forge_decks",decks,pod)
        assert len(seats)==4 and len(set(seats))==4
        orig=(ROOT/"forge_decks"/"Brimaz_V3.dck").read_text()
        for name,label in (("Brimaz_Challenger","Brimaz Challenger"),
                           ("Brimaz_Reference","Brimaz Reference")):
            clone=(decks/(name+".dck")).read_text()
            assert clone.replace("Name="+label,"Name=Brimaz V3")==orig
        for x in PODS[pod]:assert sha(decks/(x+".dck"))==sha(ROOT/"forge_decks"/(x+".dck"))
with tempfile.TemporaryDirectory() as td:
    four=Path(td)/"four"
    names=make_four_mirror_decks(ROOT/"forge_decks",four)
    original=(ROOT/"forge_decks"/"Brimaz_V3.dck").read_bytes()
    assert names==FOUR_MIRRORS and len(names)==len(set(names))==4
    for name in names:
        cloned=(four/(name+".dck")).read_bytes()
        assert cloned.replace(("Name="+name.replace("_"," ")+"\n").encode(),
                              b"Name=Brimaz V3\n",1)==original
    assert category("Brimaz_Challenger_A")=="challenger"
    assert category("Brimaz_Reference_B")=="reference"
    assert category("Kaal_9594008")=="opponent"
s="Game Result: Game 1 ended in 100000 ms. Ai(1)-Brimaz Challenger has won!"
assert classify(s,"",0,False,420,["Brimaz_Challenger","Brimaz_Reference","X","Y"])==("complete","Brimaz_Challenger")
assert classify(s,"Exception in thread main",0,False,420,["Brimaz_Challenger","Brimaz_Reference","X","Y"])[0]=="engine_fault"
assert expected_display_name("Brimaz_Reference_B")=="Brimaz Reference B"
mismatch=s.replace("Brimaz Challenger has won","Brimaz Reference has won")
assert classify(mismatch,"",0,False,420,["Brimaz_Challenger","Brimaz_Reference","X","Y"])==("name_mismatch",None)
assert binomial_two_sided(0,0)==1.0 and binomial_two_sided(6,0)==0.03125
assert binomial_two_sided(5,1)==0.21875
r=summarize([{"status":"complete","winner":"Brimaz_Challenger"}]*6+
            [{"status":"clock_censored","winner":None}])
assert r["natural_finishes"]==6 and r["censored_or_faulted"]==1
assert r["two_sided_conditional_binomial_p"]==0.03125
four=[{"mode":"all-brimaz","status":"complete",
       "winner":"Brimaz_Challenger_A"}]*9
four += [{"mode":"all-brimaz","status":"complete",
          "winner":"Brimaz_Reference_B"}]*7
m=summarize(four)
assert m["all_brimaz_natural_games"]==16
assert m["same_deck_2vs2_required_winner_integrity"] is True
assert m["challenger_brimaz_wins"]==9
assert m["reference_brimaz_wins"]==7
four[0]["winner"]="Kaal_Wrong"
assert summarize(four)["same_deck_2vs2_required_winner_integrity"] is False

# Actual Forge player.getName() is 'Ai(seat)-Name='; seat must match.
seats=("Brimaz_Challenger_A","Brimaz_Challenger_B",
       "Brimaz_Reference_A","Brimaz_Reference_B")
def window(player,approved):
    return (f"FOUR_AI_V41_SAC_WINDOW player={player} turn=4 "
            f"pilotAuthorized={str(approved).lower()} commanderPresent=true")
v=verify_v41_pilot_identity(
    window("Ai(1)-Brimaz Challenger A",True)+"\n"+
    window("Ai(2)-Brimaz Challenger B",True)+"\n"+
    window("Ai(3)-Brimaz Reference A",False)+"\n",seats)
assert v["challenger_windows"]==2 and not v["bad_windows"]
assert verify_v41_pilot_identity(
    window("Ai(1)-Brimaz Challenger A",False),seats)["bad_windows"]
assert verify_v41_pilot_identity(
    window("Ai(4)-Brimaz Reference B",True),seats)["bad_windows"]
assert verify_v41_pilot_identity(
    window("Ai(2)-Brimaz Challenger A",True),seats)["bad_windows"]
assert verify_v41_pilot_identity(
    window("Ai(5)-Brimaz Challenger A",True),seats)["bad_windows"]
assert verify_v41_pilot_identity("ordinary Forge result",seats)["windows"]==0
print("V37_MIRROR_SYNTHETIC_PASS not_real_games=true")
