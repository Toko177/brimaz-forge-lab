#!/usr/bin/env python3
"""Explicitly synthetic isolated tests, not simulated Magic Commander games."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from run_local_four_ai import validate_decks,policy_flags,PODS,POLICIES

DECKS=("Brimaz_V3","Kaal_9594008","Kaal_10347090","Kaal_21930525",
       "Kaal_23328062","Kaal_11485202","Kaal_22193355")
with tempfile.TemporaryDirectory() as temp:
    import hashlib
    root=Path(temp)
    src=root/"forge_decks"
    src.mkdir()
    entries=[]
    for deck in DECKS:
        data=f"[metadata]\nName={deck}\n".encode()
        (src/(deck+".dck")).write_bytes(data)
        entries.append({"deck":deck,"normalized_sha256":hashlib.sha256(data).hexdigest()})
    report=root/"report.json"
    report.write_text(json.dumps({"decks":entries,"errors":[]}))
    result=validate_decks(src,report)
    assert len(result)==7 and set(result)==set(DECKS)
    (src/"Kaal_9594008.dck").write_text("CHANGED, not canonical")
    try:
        validate_decks(src,report)
        raise AssertionError("Mutated opponent deck passed preflight")
    except ValueError as exc:
        assert "SHA256 mismatch" in str(exc)
    (src/"Kaal_9594008.dck").unlink()
    try:
        validate_decks(src,report)
        raise AssertionError("Missing canonical opponent deck allowed")
    except FileNotFoundError:
        pass

assert len(PODS)==2 and len(DECKS)==7
for policy in POLICIES:
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
try:
    policy_flags("pretend_wins")
    raise AssertionError("Unrecognized policy accepted")
except ValueError:pass

print("FOUR_AI_LOCAL_OPERATOR_UNIT_PASS synthetic_deck_integrity_and_symmetric_policy=true")
