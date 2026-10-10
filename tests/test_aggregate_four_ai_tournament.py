#!/usr/bin/env python3
"""Synthetic unit fixture ONLY: does not count as game or validate Magic rules."""
from pathlib import Path
import tempfile,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from aggregate_four_ai_tournament import aggregate,wilson,markdown
assert wilson(0,0) is None
assert wilson(0,4)[0]==0.0
assert wilson(4,4)[1]==1.0
with tempfile.TemporaryDirectory() as d:
    root=Path(d)
    for pod in ("aristo","artifact"):
        folder=root/pod/"source"/"batch"
        folder.mkdir(parents=True)
        seats=["Brimaz_V3","Kaal_1","Kaal_2","Kaal_3"]
        rows=[]
        for repeat in range(2):
            seed=12345+repeat+(1000 if pod=="artifact" else 0)
            name=f"real-looking-but-synthetic-{repeat}.log"
            (folder/name).write_text("Turn: Turn 1 (Ai(1)-Brimaz V3)\n"
                                     "Turn: Turn 2 (Ai(2)-AI)\n"
                                     "Ai(1)-Brimaz V3\n",encoding="utf-8")
            rows.append({"pod":pod,"rotation":0,"repeat":repeat,"seed":seed,
                         "policy":"unit-fixture","seats":seats,"brimaz_seat":1,
                         "winner_seat":1 if repeat==0 else None,
                         "winner_deck":"Brimaz_V3" if repeat==0 else None,
                         "brimaz_win":repeat==0 if repeat==0 else None,
                         "wall_seconds":12.5,
                         "status":"complete" if repeat==0 else "clock_censored",
                         "log":str(Path(pod)/"source"/"batch"/name)})
        (folder/"games.json").write_text(json.dumps(rows))
    out=aggregate(root,expected_games=4,expected_jobs=2)
    assert out["games_started"]==4,out
    assert out["games_naturally_complete_unindependently_certified"]==2,out
    assert out["censored_or_engine_failed_count"]==2,out
    assert out["brimaz_wins_observed_uncertified"]==2,out
    assert out["pods"]["aristo"]["brimaz_wins_observed_uncertified"]==1,out
    assert "Wilson" in markdown(out)
    try:
        aggregate(root,expected_games=5,expected_jobs=2)
        raise AssertionError("Incomplete tournament was not rejected")
    except ValueError as exc:
        assert "Missing true matches" in str(exc),exc
    (root/"artifact"/"source"/"batch"/"real-looking-but-synthetic-1.log").unlink()
    try:
        aggregate(root,expected_games=4,expected_jobs=2)
        raise AssertionError("Missing log accepted")
    except ValueError as exc:
        assert "Missing genuine Forge log" in str(exc),exc
print("FOUR_AI_TOURNAMENT_SYNTHETIC_UNIT_PASS claims_of_real_games=0")
