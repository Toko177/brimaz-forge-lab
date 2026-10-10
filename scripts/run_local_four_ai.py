#!/usr/bin/env python3
"""Run genuine Forge 2.0.15 four-AI Commander tournaments locally.

No mock matches, no invented winners, no opponent deck rewrites.
Use with Java 21, canonical seven .dck files and signed normalization report.
Independent Forge JVMs run concurrently; each receives the SAME AI policy.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
PODS=("aristo","artifact")
POLICIES=("v17_strict","v19_removal","v20_shadow","critical_counter",
          "v23_cooldown","v24_trigger_prune")

def sha(path):
    d=hashlib.sha256()
    with path.open("rb") as f:
        for x in iter(lambda:f.read(4*1024*1024),b""):d.update(x)
    return d.hexdigest()

def validate_decks(deckdir,normalization):
    if not normalization.is_file():
        raise FileNotFoundError("Canonical normalization report missing: "+str(normalization))
    data=json.loads(normalization.read_text(encoding="utf-8"))
    decks=data["decks"]
    if data.get("errors") or len(decks)!=7:
        raise ValueError("The original canonical seven-deck normalization report is invalid")
    hashes={}
    for rec in decks:
        name=rec["deck"]
        path=deckdir/(name+".dck")
        if not path.is_file():raise FileNotFoundError(str(path))
        actual=sha(path)
        if actual!=rec["normalized_sha256"]:
            raise ValueError("Deck SHA256 mismatch (refuse altered players): "+name)
        hashes[name]=actual
    if set(hashes)!={"Brimaz_V3","Kaal_9594008","Kaal_10347090",
                     "Kaal_21930525","Kaal_23328062","Kaal_11485202",
                     "Kaal_22193355"}:
        raise ValueError("Not the seven expected canonical Commander decks")
    return hashes

def java_version():
    result=subprocess.run(["java","-version"],text=True,capture_output=True)
    raw=(result.stdout+result.stderr)
    if result.returncode!=0 or not re.search(r'version "21(?:[."+-]|$)',raw):
        raise RuntimeError("Java 21 is required on PATH; found: "+raw[:200])
    return raw.splitlines()[0]

def policy_flags(policy):
    base=[
      "-Dbrimaz.fourSeatCombatTarget=true",
      "-Dbrimaz.deterministicForcedAttacks=true",
      "-Dbrimaz.fourSeatDefenseCoverage=true",
      "-Dbrimaz.coverageProactive=false",
      "-Dbrimaz.fourSeatRemovalUrgency=false",
      "-Dbrimaz.fourSeatCounterCritical=false",
      "-Dbrimaz.aiTimeoutCooldown=false",
      "-Dbrimaz.fastCombatTriggerNegativePrune=false",
    ]
    opts={
      "v17_strict":[],
      "v19_removal":["-Dbrimaz.fourSeatRemovalUrgency=true"],
      "v20_shadow":["-Dbrimaz.removalShadowAudit=true"],
      "critical_counter":["-Dbrimaz.fourSeatCounterCritical=true",
                          "-Dbrimaz.counterDecisionAudit=true"],
      "v23_cooldown":["-Dbrimaz.aiTimeoutCooldown=true"],
      "v24_trigger_prune":["-Dbrimaz.fastCombatTriggerNegativePrune=true",
                           "-Dbrimaz.fastCombatTriggerTrace=true"],
    }
    if policy not in opts:raise ValueError("Unsupported AI policy "+policy)
    # Last Java property wins; reset flag overrides in one location.
    return " ".join(base+opts[policy])

def patch_jar(original,output,policy):
    if not original.is_file():raise FileNotFoundError(str(original))
    if output.exists():raise FileExistsError("Will not overwrite "+str(output))
    shutil.copy2(original,output)
    scripts=["patch_forge_charm_context.py","patch_forge_brimaz_v13.py",
             "patch_forge_four_ai_targets.py"]
    if policy in ("v19_removal","v20_shadow"):
        scripts+=["patch_forge_multiplayer_removal.py"]
    if policy=="critical_counter":
        scripts+=["patch_forge_counter_critical.py"]
    if policy=="v24_trigger_prune":
        scripts+=["patch_forge_combat_trigger_prune.py"]
    for file in scripts:
        subprocess.run([sys.executable,str(ROOT/"scripts"/file),
                        "--jar",str(output)],check=True,cwd=ROOT)
    return sha(output),scripts

def run_job(campaign_root,jar,runtime_dir,pod,rotation,seed_base,count,clock,profile,policy,flags,tag,jfr):
    source_tag=f"{tag}-rot{rotation}"
    env=os.environ.copy()
    env["JAVA_TOOL_OPTIONS"]=" ".join((env.get("JAVA_TOOL_OPTIONS",""),flags)).strip()
    cmd=[sys.executable,str(ROOT/"scripts/batch.py"),"--jar",str(jar),
         "--runtime-dir",str(runtime_dir),
         "--pod",pod,"--rotation",str(rotation),
         "--games-per-rotation",str(count),
         "--seed-base",str(seed_base),"--clock",str(clock),
         "--timeout",str(clock+85),
         "--profile-brimaz",profile,"--profile-opponents",profile,
         "--out-tag",source_tag,"--policy-label",policy,"--require-canonical-decks"]
    if jfr:cmd.append("--jfr")
    proc=subprocess.run(cmd,text=True,capture_output=True,cwd=ROOT,env=env)
    generated=ROOT/"results/batch"/pod/source_tag
    target=campaign_root/"games"/pod/("rotation"+str(rotation))
    target.mkdir(parents=True)
    if generated.exists():
        for file in generated.iterdir():
            if file.is_file():shutil.copy2(file,target/file.name)
    (target/"driver.stdout.log").write_text(proc.stdout,encoding="utf-8")
    (target/"driver.stderr.log").write_text(proc.stderr,encoding="utf-8")
    return {"pod":pod,"rotation":rotation,"driver_returncode":proc.returncode,
            "game_manifest_present":(target/"games.json").is_file()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jar",type=Path,required=True,
                   help="Extract original Forge 2.0.15 gui desktop JAR from installer first")
    p.add_argument("--decks",type=Path,default=ROOT/"forge_decks")
    p.add_argument("--canonical-report",type=Path,
                   default=ROOT/"canonical/results/forge_normalization/report.json")
    p.add_argument("--scryfall-legality-report",type=Path,
                   help="Optional separate Scryfall legality results JSON for genuine natural-win certification")
    p.add_argument("--pod",choices=["both",*PODS],default="both")
    p.add_argument("--policy",choices=POLICIES,default="v17_strict")
    p.add_argument("--profile",choices=["Default","Experimental","Cautious","Reckless"],
                   default="Default")
    p.add_argument("--games-per-rotation",type=int,default=1)
    p.add_argument("--parallel",type=int,default=2)
    p.add_argument("--clock",type=int,choices=[360,420,480],default=420)
    p.add_argument("--seed-base",type=int,default=20261027)
    p.add_argument("--campaign-root",type=Path,default=ROOT/"results/local_campaigns")
    p.add_argument("--jfr",action="store_true",
                   help="Save up to 128MB JDK21 Java Flight Recorder per genuine JVM game; profiling changes timing")
    p.add_argument("--preflight-only",action="store_true",
                   help="Check Java 21 and all seven SHA256 decks without patching or running a JVM game")
    args=p.parse_args()
    if not 1<=args.games_per_rotation<=5 or not 1<=args.parallel<=4:
        p.error("1–5 games per rotation, 1–4 parallel JVM jobs")
    if args.games_per_rotation>3 and args.clock==480:
        p.error("480-second clock only permitted with up to 3 games/rotation")
    if args.seed_base<1 or args.seed_base>2_000_000_000:
        p.error("seed-base must be a positive int smaller than 2e9")
    if args.decks.resolve()!= (ROOT/"forge_decks").resolve():
        p.error("batch.py uses the repository forge_decks directory; copy canonical decks there")
    java=java_version()
    deck_hashes=validate_decks(args.decks,args.canonical_report)
    if args.scryfall_legality_report and not args.scryfall_legality_report.is_file():
        raise FileNotFoundError("Scryfall legality report missing: "+str(args.scryfall_legality_report))
    pods=PODS if args.pod=="both" else (args.pod,)
    if not args.jar.is_file():
        raise FileNotFoundError("Original Forge desktop fat JAR not found: "+str(args.jar))
    if args.preflight_only:
        print("FOUR_AI_LOCAL_PREFLIGHT_OK",json.dumps({
            "java":java,"jar":str(args.jar.resolve()),
            "canonical_unchanged_seven_decks":len(deck_hashes),
            "pods":list(pods),"rotation_count":4,
            "planned_real_forge_jvms":len(pods)*4*args.games_per_rotation,
            "policy":args.policy,"uniform_profile":args.profile,
            "clock_seconds":args.clock
        },ensure_ascii=False),flush=True)
        return
    campaign_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8]
    dest=args.campaign_root.resolve()/campaign_id
    dest.mkdir(parents=True,exist_ok=False)
    output_jar=dest/"forge-2.0.15-4AI-patched.jar"
    jar_sha,patches=patch_jar(args.jar.resolve(),output_jar,args.policy)
    runtime_dir=args.jar.resolve().parent
    flags=policy_flags(args.policy)
    meta={
        "title":"Genuine independent Forge 2.0.15 four-AI Commander games",
        "policy":args.policy,"profile_applied_identically_to_all_four_seats":args.profile,
        "pods":list(pods),"four_seat_rotations":[0,1,2,3],
        "games_per_rotation":args.games_per_rotation,
        "planned_independent_jvms":len(pods)*4*args.games_per_rotation,
        "clock_seconds":args.clock,"base_seed":args.seed_base,
        "java":java,"original_forge_sha256":sha(args.jar.resolve()),
        "original_forge_runtime_directory":str(runtime_dir),
        "patched_forge_sha256":jar_sha,"patches":patches,
        "canonical_seven_deck_sha256":deck_hashes,
        "scryfall_legality_report_file":str(args.scryfall_legality_report.resolve()) if args.scryfall_legality_report else None,
        "java_tool_options":flags,
        "jfr_enabled":bool(args.jfr),
        "warning_on_jfr":"JFR sampling may alter timing; do not interpret profile-on/off timing as game engine speedup",
        "source_commit":subprocess.run(["git","rev-parse","HEAD"],
                            cwd=ROOT,capture_output=True,text=True).stdout.strip(),
        "proof_warning":"A successful process is not independent Scryfall/Magic Oracle certification. Censored games are not wins.",
    }
    (dest/"provenance.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False)+"\n")
    tag="local-"+campaign_id
    tasks=[(pod,rot) for pod in pods for rot in range(4)]
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures={pool.submit(run_job,dest,output_jar,runtime_dir,pod,rot,args.seed_base,
                args.games_per_rotation,args.clock,args.profile,args.policy,
                flags,tag,args.jfr):(pod,rot) for pod,rot in tasks}
        jobs=[]
        for future in as_completed(futures):
            result=future.result()
            jobs.append(result)
            print("REAL_FOUR_AI_MATRIX",json.dumps(result),flush=True)
    (dest/"matrix_jobs.json").write_text(json.dumps(jobs,indent=2)+"\n")
    if args.jfr:
        jfr_files=sorted((dest/"games").rglob("*.jfr"))
        jfr_dir=dest/"jfr_summaries"
        jfr_dir.mkdir()
        for path in jfr_files:
            rel=path.relative_to(dest/"games")
            name="__".join(rel.parts)
            for title,cmd in (
                ("summary",["jfr","summary",str(path)]),
                ("hot_methods",["jfr","view","--width","160","hot-methods",str(path)]),
                ("cpu_load",["jfr","view","thread-cpu-load",str(path)]),
            ):
                proc=subprocess.run(cmd,text=True,capture_output=True,
                                    cwd=ROOT,timeout=180)
                (jfr_dir/(name+"."+title+".txt")).write_text(
                    proc.stdout+"\n[STDERR]\n"+proc.stderr,encoding="utf-8")
        print("FOUR_AI_JFR_REAL_JVM_PROFILES",len(jfr_files),
              "source=JDK21_execution_samples",flush=True)
    jobs_bad=[x for x in jobs if x["driver_returncode"]!=0 or not x["game_manifest_present"]]
    if jobs_bad:
        print("Some real Forge jobs failed; logs preserved in "+str(dest),
              file=sys.stderr)
    subprocess.run([sys.executable,str(ROOT/"scripts/aggregate_four_ai_tournament.py"),
             "--input",str(dest/"games"),"--out",str(dest/"summary"),
             "--expected-jobs",str(len(tasks)),
             "--expected-games",str(len(tasks)*args.games_per_rotation)],
             check=True,cwd=ROOT)
    subprocess.run([sys.executable,str(ROOT/"scripts/forensic_four_seat.py"),
             "--input",str(dest/"games"),"--output",str(dest/"forensics")],
             check=True,cwd=ROOT)
    subprocess.run([sys.executable,str(ROOT/"scripts/analyze_four_ai_timeout_stacks.py"),
             "--input",str(dest/"games"),"--out",str(dest/"timeouts")],
             check=True,cwd=ROOT)
    # This strict, evidence-based exploratory-readiness report is separate
    # from the true-game process exit and natural win counts. Small/censored
    # pilots can legitimately be blocked without erasing raw results.
    readiness=subprocess.run([
        sys.executable,str(ROOT/"scripts/assess_simulator_readiness.py"),
        "--forensics",str(dest/"forensics/four_seat_actions.json"),
        "--out",str(dest/"readiness.json"),
        "--min-games","8"
    ],cwd=ROOT,text=True,capture_output=True)
    (dest/"readiness.stdout.log").write_text(readiness.stdout,encoding="utf-8")
    (dest/"readiness.stderr.log").write_text(readiness.stderr,encoding="utf-8")
    if (dest/"readiness.json").is_file():
        state=json.loads((dest/"readiness.json").read_text(encoding="utf-8"))
        print("FOUR_AI_EXPLORATORY_READINESS_GATE",json.dumps({
             "gate":state["engine_pilot_gate"],
             "natural":state["naturally_finished_count"],
             "blocking_issues":state["blocking_issues"],
             "human_like_ai_demonstrated":state["human_like_ai_demonstrated"],
        },ensure_ascii=False),flush=True)
    else:
        raise RuntimeError("Readiness report generation failed; inspect preserved stdout/stderr")
    if args.scryfall_legality_report:
        certificate_dir=dest/"certification"
        proc=subprocess.run([
            sys.executable,str(ROOT/"scripts/certify_commander_games.py"),
            "--input",str(dest/"games"),
            "--legality",str(args.scryfall_legality_report),
            "--out",str(certificate_dir)],
            cwd=ROOT,text=True,capture_output=True)
        (dest/"certification.stdout.log").write_text(proc.stdout,encoding="utf-8")
        (dest/"certification.stderr.log").write_text(proc.stderr,encoding="utf-8")
        cert_file=certificate_dir/"certificate.json"
        if not cert_file.is_file():
            raise RuntimeError("Natural-game certification produced no report: "+proc.stderr)
        results=json.loads(cert_file.read_text(encoding="utf-8"))["summary"]
        data=json.loads((dest/"summary/tournament.json").read_text(encoding="utf-8"))
        natural=data["games_naturally_complete_unindependently_certified"]
        if results["accepted_natural_games"]!=natural or results["checked_games"]!=data["games_started"]:
            raise RuntimeError("REAL_FOUR_AI_CERTIFICATION_REJECTED: "
                 f"Forge natural={natural}, independently accepted={results['accepted_natural_games']}. "
                 "See preserved certification logs for rules/deck discrepancies.")
        print("REAL_FOUR_AI_SCRYFALL_AND_FORGE_NATURAL_GATE",
              json.dumps({"checked":results["checked_games"],"accepted_natural":natural,
                          "censored_or_failed":data["games_started"]-natural}),
              flush=True)
    print("REAL_FOUR_AI_CAMPAIGN_COMPLETE",str(dest),flush=True)
    if jobs_bad:raise SystemExit(2)

if __name__=="__main__":main()
