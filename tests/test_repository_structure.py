#!/usr/bin/env python3
"""Repository-layout checks, not mock Commander match results."""
from pathlib import Path
import importlib.util
import re
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_local_four_ai import validate_decks, CANONICAL_DECK_SHA256

expected = {
    "README.md", "NEXT_CHAT_START_HERE.md",
    "docs/REPOSITORY_STRUCTURE.md", "docs/RUN_LOCAL_4AI_COMMANDER.md",
    "docs/V33_MULTIPLAYER_STRATEGIC_PLANNER.md",
    "docs/V35_STRATEGIC_SEARCH.md",
    "scripts/run_local_four_ai.py", "scripts/run_paired_four_ai.py",
    "scripts/batch.py", "scripts/compare_local_four_ai_campaigns.py",
    "scripts/patch_forge_brimaz_v13.py", "scripts/setup_and_run_four_ai.ps1",
    "scripts/certify_commander_games.py", "scripts/validate_commander_legality.py",
    "scripts/audit_v33_real_strategy.py",
    "scripts/audit_v35_real_search.py",
    "patches/java/forge/ai/MultiplayerStrategicModel.java",
    "patches/java/forge/ai/MultiplayerStrategicSequencer.java",
    "patches/java/forge/ai/MultiplayerStrategicSearchV35.java",
    "patches/java/forge/ai/MultiplayerStrategicSequencerV35.java",
    "canonical/results/forge_normalization/report.json",
    ".github/workflows/strategic-java21-gate.yml",
    ".github/workflows/strategic-real-4ai-ab.yml",
    ".github/workflows/v31-operator-validation.yml",
    ".github/workflows/repository-health.yml",
    ".github/workflows/commander-four-ai-simulator.yml",
    "docs/REAL_FOUR_AI_BRIMAZ_WIN_REFERENCE.md",
}
assert all((ROOT / p).is_file() for p in expected), "Active source or documentation was removed"
hashes = validate_decks(
    ROOT / "forge_decks",
    ROOT / "canonical/results/forge_normalization/report.json",
)
assert hashes == CANONICAL_DECK_SHA256, "Canonical Commander deck bytes were changed"
assert len(list((ROOT / "forge_decks").glob("*.dck"))) == 7, "Unexpected canonical deck count"
workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
assert len(workflows) == 16, f"Expected exactly 16 maintained workflows, got {len(workflows)}"
for version in ("", *(f"_v{i}" for i in range(2, 13))):
    assert not (ROOT / ("scripts/patch_forge_brimaz" + version + ".py")).exists(), "Legacy patch not pruned"

required_code = {
    "scripts/run_local_four_ai.py": ("v33_strategy", "v35_strategy", "patch_forge_brimaz_v13.py"),
    "scripts/patch_forge_brimaz_v13.py": ("MultiplayerStrategicSequencer", "MultiplayerStrategicModel"),
    "scripts/audit_v33_real_strategy.py": ("FOUR_AI_V33_STRATEGIC_ACTION", "require-intervention"),
    "scripts/audit_v35_real_search.py": ("FOUR_AI_V35_STOCK_APPROVED", "min-approved"),
    "scripts/patch_forge_brimaz_v13.py": ("MultiplayerStrategicSearchV35", "MultiplayerStrategicSequencerV35"),
}
for path, markers in required_code.items():
    s = (ROOT / path).read_text(encoding="utf-8")
    assert all(marker in s for marker in markers), f"Missing strategic integration from {path}"
for file in workflows:
    text = file.read_text(encoding="utf-8")
    # All literal checked-in source references in the active workflow must resolve.
    for match in re.findall(r"(?:scripts|tests)/[A-Za-z0-9_./-]+\.(?:py|ps1)", text):
        assert (ROOT / match).is_file(), f"Active workflow {file.name} references missing {match}"
for p in ("README.md", "NEXT_CHAT_START_HERE.md", "docs/RUN_LOCAL_4AI_COMMANDER.md"):
    content = (ROOT / p).read_text(encoding="utf-8")
    assert "main" in content
print("FOUR_AI_V34_REPOSITORY_CLEAN_PASS",
      {"decks": len(hashes), "workflows": len(workflows), "protected_paths": len(expected),
       "legacy_patch_variants_removed": 12, "real_games_claimed": 0})
