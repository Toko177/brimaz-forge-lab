#!/usr/bin/env python3
"""Run two matched REAL Forge 2.0.15 four-AI Commander campaigns and compare.

Never substitutes mock games. Each game uses a separate genuine Forge JVM;
one failed campaign aborts comparison without inventing missing results.
Same seeds are pairing identifiers, not identical-RNG replay guarantees.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_local_four_ai_campaigns import compare
from run_local_four_ai import POLICIES


def build_command(args, policy, root, *, preflight=False):
    """Identical controlled inputs for both arms, except policy and output."""
    cmd = [
        sys.executable, str(ROOT / "scripts" / "run_local_four_ai.py"),
        "--jar", str(args.jar), "--decks", str(args.decks),
        "--canonical-report", str(args.canonical_report),
        "--pod", args.pod, "--policy", policy, "--profile", args.profile,
        "--games-per-rotation", str(args.games_per_rotation),
        "--parallel", str(args.parallel), "--clock", str(args.clock),
        "--seed-base", str(args.seed_base), "--campaign-root", str(root),
    ]
    if args.jfr:
        cmd.append("--jfr")
    if args.scryfall_legality_report:
        cmd += ["--scryfall-legality-report", str(args.scryfall_legality_report)]
    if preflight:
        cmd.append("--preflight-only")
    return cmd


def locate_real_campaign(folder):
    children = [p for p in folder.iterdir()
                if p.is_dir() and (p / "provenance.json").is_file()]
    if len(children) != 1:
        raise ValueError("Expected exactly one preserved real campaign in "
                         + str(folder) + "; found " + str(len(children)))
    return children[0]


def execute(cmd, log_root, label):
    """Preserve all subprocess evidence even if the real JVM run fails."""
    log_root.mkdir(parents=True, exist_ok=True)
    (log_root / "command.json").write_text(
        json.dumps({"command": cmd}, indent=2) + "\n", encoding="utf-8")
    with (log_root / "stdout.log").open("w", encoding="utf-8") as out, \
         (log_root / "stderr.log").open("w", encoding="utf-8") as err:
        rc = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=err,
                            check=False).returncode
    print("FOUR_AI_PAIR_ARM", json.dumps(
        {"arm": label, "returncode": rc,
         "stdout": str(log_root / "stdout.log"),
         "stderr": str(log_root / "stderr.log")}), flush=True)
    if rc:
        # The CI job must surface the root error without downloading a huge
        # artifact or pretending this faulty arm lost the Commander game.
        for filename in ("stderr.log","stdout.log"):
            path=log_root/filename
            if path.is_file():
                lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
                relevant=[x for x in lines if any(t in x for t in (
                    "Traceback","Exception","Error:","RuntimeError",
                    "ValueError","failed","engine_fault","engine_failed",
                    "profile directory","NullPointerException",
                    "Raw Forge 4-seat game actions not present"))]
                print("FOUR_AI_FAILED_ARM_DIAGNOSTIC",
                      json.dumps({"arm":label,"source":filename,
                                  "tail":lines[-6:],
                                  "critical":relevant[-12:]},
                                 ensure_ascii=False),flush=True)
        raise RuntimeError(label + " genuine Forge campaign failed with exit "
                           + str(rc) + ". Logs preserved in " + str(log_root))


def pair_summary(report):
    return {
        "real_process_pairs": report["real_process_pairs"],
        "real_forge_jvm_processes": report["real_forge_jvm_processes"],
        "both_natural_pairs": report["both_natural_pairs"],
        "pairs_with_any_censor_or_fault": report["pairs_with_any_censor_or_fault"],
        "natural_pairs_with_identical_observable_actions":
            report["natural_pairs_with_identical_observable_actions"],
        "natural_pairs_with_different_winner":
            report["natural_pairs_with_different_winner"],
        "no_fabricated_winners": True,
        "paired_seed_does_not_guarantee_identical_actions": True,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jar", required=True, type=Path)
    p.add_argument("--decks", type=Path, default=ROOT / "forge_decks")
    p.add_argument("--canonical-report", type=Path,
                   default=ROOT / "canonical/results/forge_normalization/report.json")
    p.add_argument("--scryfall-legality-report", type=Path)
    p.add_argument("--reference-policy", choices=POLICIES, default="v17_strict")
    p.add_argument("--experiment-policy", choices=POLICIES, required=True)
    p.add_argument("--pod", choices=("both", "aristo", "artifact"), default="both")
    p.add_argument("--profile", choices=("Default", "Experimental",
                                       "Cautious", "Reckless"), default="Default")
    p.add_argument("--games-per-rotation", type=int, default=1)
    p.add_argument("--parallel", type=int, default=2)
    p.add_argument("--clock", type=int, choices=(360, 420, 480), default=420)
    p.add_argument("--seed-base", type=int, default=20261027)
    p.add_argument("--jfr", action="store_true")
    p.add_argument("--preflight-only", action="store_true")
    p.add_argument("--out", type=Path, default=ROOT / "results/local_pairs")
    args = p.parse_args()
    if not (1 <= args.games_per_rotation <= 5 and 1 <= args.parallel <= 4):
        p.error("Expected 1–5 games per rotation and 1–4 parallel JVMs")
    if args.clock == 480 and args.games_per_rotation > 3:
        p.error("480s clock supports up to 3 games per rotation")
    if not (1 <= args.seed_base <= 2_000_000_000):
        p.error("Invalid RNG seed base")
    pair_count = (2 if args.pod == "both" else 1) * 4 * args.games_per_rotation
    if args.preflight_only:
        for label, policy in (("reference", args.reference_policy),
                              ("experiment", args.experiment_policy)):
            execute(build_command(args, policy, args.out / label, preflight=True),
                    args.out / "preflight_logs" / label, label)
        print("FOUR_AI_PAIRED_PREFLIGHT_OK",
              json.dumps({"planned_real_jvms": 2 * pair_count,
                          "reference": args.reference_policy,
                          "experiment": args.experiment_policy}), flush=True)
        return

    pair_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pair_id += "-" + uuid4().hex[:8]
    target = args.out.resolve() / pair_id
    target.mkdir(parents=True, exist_ok=False)
    plan = {
        "type": "planned genuine Forge four-AI paired evaluation (not game proof)",
        "reference_policy": args.reference_policy,
        "experiment_policy": args.experiment_policy,
        "pods": ["aristo", "artifact"] if args.pod == "both" else [args.pod],
        "planned_process_pairs": pair_count,
        "planned_real_forge_jvms": 2 * pair_count,
        "clock_seconds": args.clock,
        "seed_base": args.seed_base,
        "jfr_changes_timing": args.jfr,
        "status": "planned_only",
    }
    plan_file = target / "plan.json"
    plan_file.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    for label, policy in (("reference", args.reference_policy),
                          ("experiment", args.experiment_policy)):
        campaigns_dir = target / label / "campaigns"
        execute(build_command(args, policy, campaigns_dir),
                target / label / "logs", label)

    first = locate_real_campaign(target / "reference/campaigns")
    second = locate_real_campaign(target / "experiment/campaigns")
    result = compare(first, second)
    if result["real_process_pairs"] != pair_count:
        raise RuntimeError("Missing a real Forge JVM match in the completed A/B")
    (target / "comparison.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan["status"] = "compared_genuine_logs"
    plan_file.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print("FOUR_AI_REAL_PAIRED_EVIDENCE",
          json.dumps(pair_summary(result), ensure_ascii=False), flush=True)
    print("FOUR_AI_REAL_PAIRED_REPORT", str(target / "comparison.json"), flush=True)


if __name__ == "__main__":
    main()
