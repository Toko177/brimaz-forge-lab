#!/usr/bin/env python3
"""Synthetic parser fixture, NOT genuine Forge outcomes or fabricated gameplay."""
import sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from analyze_v41_sacrifice_bottlenecks import parse_window,bottleneck,analyze

line=("2026-10-11T21:00:00Z FOUR_AI_V41_SAC_WINDOW "
      "player=Brimaz Challenger A turn=18 pilotAuthorized=true "
      "commanderPresent=true alreadyDead=false phyrexianCreatureTokens=2 "
      "outletPermanents=1 listedActualOutletAbilities=0 proposalNotResolution=true")
w=parse_window(line)
assert w["player"]=="Brimaz Challenger A" and w["turn"]==18
assert bottleneck(w)=="outlet_ability_not_offered"
assert parse_window("unrelated log")==None
expect=[
    ({"pilotAuthorized":False},"unauthorized_pilot"),
    ({"commanderPresent":False},"commander_absent"),
    ({"alreadyDead":True},"death_trigger_already_satisfied"),
    ({"phyrexianCreatureTokens":0},"no_transformed_phyrexian_token"),
    ({"outletPermanents":0},"no_sacrifice_outlet_permanent"),
    ({"listedActualOutletAbilities":1},"candidate_present_requires_cost_and_ai_approval"),
]
for changes,want in expect:
    s={**w,**changes}
    if "listedActualOutletAbilities" in changes:s["outletPermanents"]=1
    assert bottleneck(s)==want,(changes,bottleneck(s))
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    a=root/"aristo"/"rotation0_rep0"
    a.mkdir(parents=True)
    (a/"result.json").write_text(json.dumps({
        "status":"complete","winner":"Brimaz_Challenger_A"}),encoding="utf-8")
    (a/"game.log").write_text(line+"\n"+line+
        "\nFOUR_AI_V38_TRANSFORM_STOCK_APPROVED player=Brimaz Challenger A\n"+
        "FOUR_AI_V37_POSITIVE_SAC_FORGE_APPROVED player=Brimaz Challenger A\n",
        encoding="utf-8")
    report=analyze(root)
    assert report["totals"]["jvm_games"]==1
    assert report["totals"]["natural_games"]==1
    assert report["totals"]["distinct_v41_own_main2_windows"]==1
    assert report["totals"]["sacrifice_approved_not_resolved"]==1
    assert report["totals"]["transform_approved_not_resolved"]==1
    assert report["primary_bottleneck_by_own_turn"]=={"outlet_ability_not_offered":1}
    (a/"game.log").write_text(line+"\n"+line.replace(
        "listedActualOutletAbilities=0","listedActualOutletAbilities=1"),
        encoding="utf-8")
    try:
        analyze(root)
        raise AssertionError("Contradictory same-turn telemetry accepted")
    except ValueError:
        pass
print("V41_SAC_BOTTLENECK_PARSER_SYNTHETIC_PASS no_real_games_claimed=true")
