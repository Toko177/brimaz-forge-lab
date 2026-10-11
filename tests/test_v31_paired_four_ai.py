#!/usr/bin/env python3
"""Synthetic operator-contract tests; NEVER evidence of real Commander play."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_local_four_ai import POLICIES, policy_flags
from run_paired_four_ai import build_command, locate_real_campaign, pair_summary
from compare_local_four_ai_campaigns import timing_eligible

assert "v30_exact_rules" in POLICIES
assert "v30_shadow_verify" in POLICIES
for p in ("v17_strict", "v24_trigger_prune", "v30_exact_rules",
          "v30_shadow_verify"):
    flags = policy_flags(p)
    assert "-Dbrimaz.fastCardPropertyExactLiterals=false" in flags
    assert "-Dbrimaz.cardPropertyShadowVerify=false" in flags
    assert "-Dbrimaz.cardPropertyFastTrace=false" in flags
assert policy_flags("v30_exact_rules").endswith(
    "-Dbrimaz.fastCardPropertyExactLiterals=true "
    "-Dbrimaz.cardPropertyFastTrace=true")
assert policy_flags("v30_shadow_verify").endswith(
    "-Dbrimaz.fastCardPropertyExactLiterals=true "
    "-Dbrimaz.cardPropertyFastTrace=true "
    "-Dbrimaz.cardPropertyShadowVerify=true")
assert not policy_flags("v24_trigger_prune").endswith(
    "-Dbrimaz.fastCardPropertyExactLiterals=true")
assert timing_eligible({"policy": "v17_strict"}, {"policy": "v30_exact_rules"})
assert not timing_eligible({"policy": "v30_shadow_verify"}, {"policy": "v17_strict"})
assert not timing_eligible({"diagnostic_shadow_verification": True},
                           {"policy": "v17_strict"})
assert not timing_eligible({"policy": "v17_strict"}, {"jfr_enabled": True})

a = argparse.Namespace(
    jar=Path("original.jar"), decks=Path("forge_decks"),
    canonical_report=Path("canonical/report.json"), pod="both", profile="Default",
    games_per_rotation=2, parallel=2, clock=420, seed_base=20610001,
    jfr=False, scryfall_legality_report=None,
)
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    ca = build_command(a, "v17_strict", t / "ref")
    cb = build_command(a, "v30_exact_rules", t / "experiment")
    assert "--jar" in ca and "--canonical-report" in ca
    assert "--require-canonical-decks" not in ca  # run_local enables it internally
    assert "--seed-base" in ca and ca[ca.index("--seed-base") + 1] == "20610001"
    assert "--policy" in ca and ca[ca.index("--policy") + 1] == "v17_strict"
    assert "--policy" in cb and cb[cb.index("--policy") + 1] == "v30_exact_rules"
    for immutable in ("--jar", "--decks", "--canonical-report", "--pod",
                      "--profile", "--games-per-rotation", "--clock", "--seed-base"):
        assert ca[ca.index(immutable) + 1] == cb[cb.index(immutable) + 1]
    assert "--preflight-only" in build_command(
        a, "v17_strict", t / "ref", preflight=True)
    a.jfr = True
    a.scryfall_legality_report = t / "scryfall.json"
    cc = build_command(a, "v30_shadow_verify", t / "exp")
    assert "--jfr" in cc and "--scryfall-legality-report" in cc
    try:
        locate_real_campaign(t)
        raise AssertionError("Empty campaign root was incorrectly accepted")
    except ValueError:
        pass
    one = t / "one"
    one.mkdir()
    (one / "provenance.json").write_text("{}")
    assert locate_real_campaign(t) == one
    two = t / "two"
    two.mkdir()
    (two / "provenance.json").write_text("{}")
    try:
        locate_real_campaign(t)
        raise AssertionError("Ambiguous campaign root was incorrectly accepted")
    except ValueError:
        pass

report = {
    "real_process_pairs": 8, "real_forge_jvm_processes": 16,
    "both_natural_pairs": 5, "pairs_with_any_censor_or_fault": 3,
    "natural_pairs_with_identical_observable_actions": 3,
    "natural_pairs_with_different_winner": 1,
}
assert pair_summary(report)["no_fabricated_winners"]
assert pair_summary(report)["real_forge_jvm_processes"] == 16
print("FOUR_AI_V31_SYNTHETIC_OPERATOR_CONTRACT_PASS rules_modes=2 paired_validation=true real_games_claimed=0")
