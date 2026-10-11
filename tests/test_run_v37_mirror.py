#!/usr/bin/env python3
"""Static synthetic checks for the real-JVM mirror. No mocked results claimed."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from run_v37_mirror import make_mirror_decks,classify,binomial_two_sided,summarize,PODS
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
s="Game Result: Game 1 ended in 100000 ms. Ai(1)-Brimaz Challenger has won!"
assert classify(s,"",0,False,420,["Brimaz_Challenger","Brimaz_Reference","X","Y"])==("complete","Brimaz_Challenger")
assert classify(s,"Exception in thread main",0,False,420,["Brimaz_Challenger","Brimaz_Reference","X","Y"])[0]=="engine_fault"
assert binomial_two_sided(0,0)==1.0 and binomial_two_sided(6,0)==0.03125
assert binomial_two_sided(5,1)==0.21875
r=summarize([{"status":"complete","winner":"Brimaz_Challenger"}]*6+
            [{"status":"clock_censored","winner":None}])
assert r["natural_finishes"]==6 and r["censored_or_faulted"]==1
assert r["two_sided_conditional_binomial_p"]==0.03125
print("V37_MIRROR_SYNTHETIC_PASS not_real_games=true")
