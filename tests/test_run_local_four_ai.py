#!/usr/bin/env python3
"""Synthetic operator and REAL deck bytes SHA checks, NOT Commander games."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_local_four_ai import (validate_decks,policy_flags,patch_jar,sha,PODS,POLICIES,
                               CANONICAL_DECK_SHA256)

DECKS=("Brimaz_V3","Kaal_9594008","Kaal_10347090","Kaal_21930525",
       "Kaal_23328062","Kaal_11485202","Kaal_22193355")
orig=ROOT/"canonical/results/forge_normalization/report.json"
existing=ROOT/"forge_decks"
assert orig.is_file()
assert len(PODS)==2 and len(DECKS)==7
assert set(DECKS)==set(CANONICAL_DECK_SHA256)
verified=validate_decks(existing,orig)
assert verified==CANONICAL_DECK_SHA256
with tempfile.TemporaryDirectory() as temp:
    folder=Path(temp)
    src=folder/"forge_decks"
    src.mkdir()
    for deck in DECKS:
        shutil.copyfile(existing/(deck+".dck"),src/(deck+".dck"))
    report=folder/"report.json"
    shutil.copyfile(orig,report)
    assert validate_decks(src,report)==CANONICAL_DECK_SHA256
    deck=src/"Kaal_9594008.dck"
    deck.write_text("CHANGED, not canonical")
    try:
        validate_decks(src,report)
        raise AssertionError("Mutated opponent passed preflight")
    except ValueError as exc:
        assert "SHA256 mismatch" in str(exc)
    data=json.loads(report.read_text(encoding="utf-8"))
    for row in data["decks"]:
        if row["deck"]=="Kaal_9594008":
            row["normalized_sha256"]=hashlib.sha256(deck.read_bytes()).hexdigest()
    report.write_text(json.dumps(data))
    try:
        validate_decks(src,report)
        raise AssertionError("Tampered deck AND tampered report passed pinned original SHA")
    except ValueError as exc:
        assert "Pinned original canonical deck SHA256 mismatch" in str(exc)
    deck.unlink()
    try:
        validate_decks(src,report)
        raise AssertionError("Missing opponent passed")
    except FileNotFoundError:
        pass
assert "forge_stock" in POLICIES
assert policy_flags("forge_stock") == ""
assert "forge_stock_compat" in POLICIES
assert policy_flags("forge_stock_compat") == ""
from run_local_four_ai import prepare_forge_shared_profile_paths
with tempfile.TemporaryDirectory() as tmp:
    path=prepare_forge_shared_profile_paths(tmp)
    assert path.is_dir() and path.as_posix().endswith("/.forge/decks/planar")
    assert prepare_forge_shared_profile_paths(tmp)==path
    for part in ("decks/constructed","decks/draft","decks/sealed",
                 "decks/scheme","decks/planar","decks/commander",
                 "decks/oathbreaker","decks/net","decks/network-events",
                 "quest/saves","preferences","gauntlet"):
        assert (Path(tmp)/".forge"/part).is_dir(),part
    for part in ("pics/cards","pics/tokens","pics/icons","pics/boosters",
                 "pics/fatpacks","pics/boosterboxes","pics/precons",
                 "pics/tournamentpacks","pics/planechase","db"):
        assert (Path(tmp)/".cache"/"forge"/part).is_dir(),part


with tempfile.TemporaryDirectory() as td:
    original=Path(td)/"upstream_original.jar"
    out=Path(td)/"stock_copy.jar"
    original.write_bytes(b"Fake upstream JAR bytes - synthetic byte equality ONLY")
    oldhash=sha(original)
    newhash,patches=patch_jar(original,out,"forge_stock")
    assert newhash==oldhash==sha(out), "Stock comparator JAR was patched or modified"
    assert patches==[], "Stock Forge comparator must have ZERO patches"
for policy in POLICIES:
    if policy in ("forge_stock","forge_stock_compat","v37_stock_control","v37_brimaz_challenger","v38_brimaz_challenger","v39_brimaz_challenger"):
        continue
    flags=policy_flags(policy)
    assert "fourSeatCombatTarget=true" in flags
    assert "deterministicForcedAttacks=true" in flags
    assert "aiTimeoutCooldown=false" in flags
    assert "fourSeatCounterCritical=false" in flags
assert "aiTimeoutCooldown=true" in policy_flags("v23_cooldown")
assert "fastCombatTriggerNegativePrune=true" in policy_flags("v24_trigger_prune")
assert "removalShadowAudit=true" in policy_flags("v20_shadow")
assert "fourSeatRemovalUrgency=true" in policy_flags("v19_removal")
assert "fourSeatCounterCritical=true" in policy_flags("critical_counter")
assert "fastCardPropertyExactLiterals=true" in policy_flags("v30_exact_rules")
assert "v35_strategy" in POLICIES
assert "v35StrategicSearch=true" in policy_flags("v35_strategy")
assert "fourSeatRemovalUrgency=true" in policy_flags("v35_strategy")
assert "fourSeatCounterCritical=true" in policy_flags("v35_strategy")
assert "v37_stock_control" in POLICIES
assert "v39_brimaz_challenger" in POLICIES
assert "v39EngineEconomics=true" in policy_flags("v39_brimaz_challenger")
assert "v38IncubatorTempo=true" in policy_flags("v39_brimaz_challenger")
assert "v39EngineEconomics=true" not in policy_flags("v37_stock_control")
assert "v38_brimaz_challenger" in POLICIES
assert "v38IncubatorTempo=true" in policy_flags("v38_brimaz_challenger")
assert "v38IncubatorTempo=true" not in policy_flags("v37_stock_control")
assert "v37_brimaz_challenger" in POLICIES
assert "v37ControlledDuel=true" in policy_flags("v37_stock_control")
assert "v35StrategicSearch=true" not in policy_flags("v37_stock_control")
assert "v37Challenger=true" not in policy_flags("v37_stock_control")
assert "v37Challenger=true" in policy_flags("v37_brimaz_challenger")
assert "fourSeatCombatTarget=true" not in policy_flags("v37_brimaz_challenger")
assert "v36_brimaz_challenger" in POLICIES
assert "v36EvidenceGate=true" in policy_flags("v36_brimaz_challenger")
assert "v35BrimazOnly=true" in policy_flags("v36_brimaz_challenger")
assert "fourSeatCounterCritical=true" not in policy_flags("v36_brimaz_challenger")
assert "v35_brimaz_duel" in POLICIES
assert "v35StrategicSearch=true" in policy_flags("v35_brimaz_duel")
assert "v35BrimazOnly=true" in policy_flags("v35_brimaz_duel")
assert "fourSeatRemovalUrgency=true" not in policy_flags("v35_brimaz_duel")
assert "fourSeatCounterCritical=true" not in policy_flags("v35_brimaz_duel")
assert "fourSeatRemovalUrgency=false" in policy_flags("v17_strict")
assert "fourSeatCounterCritical=false" in policy_flags("v17_strict")
assert "v35StrategicSearch=false" in policy_flags("v17_strict")
assert "v35StrategicSearch=false" in policy_flags("v33_strategy")
try:
    policy_flags("pretend_wins")
    raise AssertionError("Unrecognized policy accepted")
except ValueError:
    pass
print("FOUR_AI_V32_OPERATOR_CANONICAL_DECK_SHA_PASS seven_originals=7 tampered_data_and_report_rejected=true real_games_claimed=0")
