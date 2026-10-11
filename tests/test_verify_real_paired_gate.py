#!/usr/bin/env python3
"""Synthetic falsification fixtures only. ZERO fabricated real Commander wins."""
from copy import deepcopy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from verify_real_paired_gate import audit

P="f"*64
Q="e"*64
def report():
    decks={
      "Brimaz_V3":P,"Kaal_9594008":P,"Kaal_10347090":P,
      "Kaal_21930525":P,"Kaal_23328062":P,
      "Kaal_11485202":P,"Kaal_22193355":P,
    }
    m={"canonical_seven_deck_sha256":decks,
       "original_forge_sha256":P,
       "profile_applied_identically_to_all_four_seats":"Default",
       "clock_seconds":420,"base_seed":20261111}
    out={"type":"Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B",
         "reference_provenance":deepcopy(m),"experiment_provenance":deepcopy(m),
         "real_process_pairs":4,"real_forge_jvm_processes":8,
         "both_natural_pairs":4,"pairs_with_any_censor_or_fault":0,
         "natural_pairs_with_identical_observable_actions":4,
         "natural_pairs_with_different_winner":0,"pairs":[]}
    for rot in range(4):
        seats=["Brimaz_V3","Kaal_23328062","Kaal_11485202","Kaal_22193355"]
        seats=seats[rot:]+seats[:rot]
        rec={"seats":seats,"clock_seconds":420,"profiles":["Default"]*4,
             "status":"complete","winner":seats[1],
             "raw_sha256":P,"event_sha256":Q,"event_count":430}
        out["pairs"].append({"pod":"artifact","rotation":rot,"repeat":0,
                             "seed":20261111+10000*rot,
                             "reference":deepcopy(rec),"experiment":deepcopy(rec),
                             "both_natural":True,
                             "same_observable_events_if_natural":True})
    return out

def fail(data,reason):
    try:
        audit(data,expected_pairs=4)
    except ValueError:
        return
    raise AssertionError("Invalid synthetic evidence accepted: "+reason)

x=report()
gate=audit(x)
assert gate["functional_release_gate"]=="PASS"
assert gate["real_forge_jvm_processes"]==8
assert not gate["certified_magic_oracle_rules"]
assert not gate["human_like_ai_demonstrated"]
assert not gate["statistically_validated_winrate"]

y=report();y["pairs"].pop();fail(y,"missing pair")
y=report();y["real_forge_jvm_processes"]=6;fail(y,"fabricated JVM count")
y=report();y["pairs"][1]["experiment"]["winner"]="UNKNOWN";fail(y,"phantom winner")
y=report();y["pairs"][1]["experiment"]["raw_sha256"]="";fail(y,"no log SHA")
y=report();y["pairs"][1]["seed"]=y["pairs"][0]["seed"];y["pairs"][1]["rotation"]=0;fail(y,"duplicate")
y=report();y["reference_provenance"]["canonical_seven_deck_sha256"].pop("Brimaz_V3");fail(y,"missing canonical deck")
y=report();y["pairs"][1]["experiment"]["status"]="clock_censored";y["pairs"][1]["experiment"]["winner"]=None;fail(y,"false natural pair")
y=report();y["pairs"][1]["experiment"]["event_sha256"]=P;fail(y,"forged same events")
y=report();y["pairs"][1]["reference"]["event_count"]=0;fail(y,"zero real actions")
y=report();y["pairs"][1]["reference"]["seats"][1]="Brimaz_V3";fail(y,"not four distinct decks")
y=report();y["pairs"][1]["experiment"]["status"]="clock_censored"
y["pairs"][1]["experiment"]["winner"]=None
y["pairs"][1]["both_natural"]=False
y["pairs"][1]["same_observable_events_if_natural"]=False
y["both_natural_pairs"]=3
y["natural_pairs_with_identical_observable_actions"]=3
y["pairs_with_any_censor_or_fault"]=1
assert audit(y)["functional_release_gate"]=="BLOCKED"
assert audit(y,require_natural=False,require_identical=False)["functional_release_gate"]=="PASS"
print("FOUR_AI_V32_RELEASE_GATES_SYNTHETIC_PASS falsifications=10 fake_real_games_claimed=0")
