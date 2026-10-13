#!/usr/bin/env python3
"""Synthetic fixtures only. Never credited as real Magic games."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from compare_local_four_ai_campaigns import compare,load_campaign
from commander_pods import ROSTER_VERSION

DECKS=["Brimaz_V3","Kaal_9594008","Kaal_10347090","Kaal_21930525"]
def make_campaign(root,policy,lose_one=False,alter_status=False):
    root.mkdir()
    provenance={
       "original_forge_sha256":"same-official-pinned-source",
       "canonical_seven_deck_sha256":{"a":"hash-a","b":"hash-b"},
       "profile_applied_identically_to_all_four_seats":"Default",
       "pods":["aristo"],"games_per_rotation":1,
       "roster_version":ROSTER_VERSION,"active_pods":{"aristo":DECKS},
       "base_seed":50000,"clock_seconds":420,
       "planned_independent_jvms":4,
       "policy":policy,
    }
    (root/"provenance.json").write_text(json.dumps(provenance))
    for rot in range(4):
        if lose_one and rot==3:continue
        folder=root/"games"/"aristo"/f"rotation{rot}"
        folder.mkdir(parents=True)
        seats=DECKS[rot:]+DECKS[:rot]
        seed=50000+10000*rot
        game_name=f"game_rot{rot}_rep000_seat{seats.index('Brimaz_V3')+1}.log"
        raw=("Turn: Turn 1 (Ai(1)-Brimaz V3)\n"
             "Ai(1)-Brimaz V3\nPhase: Upkeep\n"
             "Game Outcome: Ai(1)-Brimaz V3 has won because all opponents have lost.\n")
        (folder/game_name).write_text(raw)
        status="clock_censored" if alter_status and rot==1 else "complete"
        record={"pod":"aristo","rotation":rot,"repeat":0,"seed":seed,
                "roster_version":ROSTER_VERSION,
                "seats":seats,"brimaz_seat":seats.index("Brimaz_V3")+1,
                "policy":policy,"clock_seconds":420,"profiles":["Default"]*4,
                "status":status,
                "winner_seat":1 if status=="complete" else None,
                "winner_deck":seats[0] if status=="complete" else None,
                "brimaz_win":(seats[0]=="Brimaz_V3") if status=="complete" else None,
                "wall_seconds":20.0,
                "log":str(Path("results/batch/aristo")/game_name)}
        (folder/"games.json").write_text(json.dumps([record]))
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    a,b,c=root/"a",root/"b",root/"c"
    make_campaign(a,"v17_strict")
    make_campaign(b,"v24_trigger_prune",alter_status=True)
    make_campaign(c,"v24_trigger_prune",lose_one=True)
    r=compare(a,b)
    assert r["real_forge_jvm_processes"]==8
    assert r["both_natural_pairs"]==3
    assert r["pairs_with_any_censor_or_fault"]==1
    assert r["natural_pairs_with_identical_observable_actions"]==3
    assert r["natural_pairs_with_different_winner"]==0
    try:
        compare(a,c)
        raise AssertionError("Incomplete seeded 4-seat matrix incorrectly accepted")
    except ValueError as exc:
        assert "Missing one or more" in str(exc)
    # The same pod label and seed cannot silently mean new opponents.
    swapped=json.loads((b/"provenance.json").read_text())
    swapped["active_pods"]["aristo"][-1]="Kaal_23328062"
    (b/"provenance.json").write_text(json.dumps(swapped))
    try:
        compare(a,b)
        raise AssertionError("Mismatched pod roster incorrectly accepted")
    except ValueError as exc:
        assert "roster" in str(exc)
    swapped["active_pods"]["aristo"][-1]=DECKS[-1]
    (b/"provenance.json").write_text(json.dumps(swapped))
    first=b/"games/aristo/rotation0"
    games=json.loads((first/"games.json").read_text())
    games[0]["profiles"][2]="Reckless"
    (first/"games.json").write_text(json.dumps(games))
    try:
        compare(a,b)
        raise AssertionError("Asymmetric four-seat profile accepted")
    except ValueError as exc:
        assert "differs across four seats" in str(exc)
print("FOUR_AI_LOCAL_PAIRED_UNIT_PASS fixtures=SYNTHETIC_ONLY")
