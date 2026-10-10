#!/usr/bin/env python3
"""Forge EDH batch: genuine independent 4-AI games, with seat rotation.

This is a REAL Forge subprocess driver, not a Monte Carlo draw proxy.
Unfinished games and simulation-clock "winners" are never counted as wins.
"""
import argparse
import collections
import json
import pathlib
import re
import subprocess
import sys
import time
from forge_result_evidence import inspect_ai_quality_signatures

p=argparse.ArgumentParser()
p.add_argument("--jar",required=True)
p.add_argument("--runtime-dir",default=None,
               help="Original Forge installation directory for resource lookups when using a copied patched JAR")
p.add_argument("--pod",choices=["aristo","artifact"],default="aristo")
p.add_argument("--clock",type=int,default=360)
p.add_argument("--timeout",type=int,default=445)
p.add_argument("--games-per-rotation",type=int,default=1)
p.add_argument("--rotation",type=int,choices=[0,1,2,3],default=None,
               help="Run only one seat rotation; enables distributed job matrix")
p.add_argument("--seed-base",type=int,default=20261009,
               help="Forge -s base RNG seed (per-rotation and repeat offset)")
p.add_argument("--profile-brimaz",choices=["Default","Experimental","Cautious","Reckless"],default="Default")
p.add_argument("--profile-opponents",choices=["Default","Experimental","Cautious","Reckless"],default="Default")
p.add_argument("--out-tag",default="baseline",help="Distinct output group to isolate A/B profiles")
p.add_argument("--policy-label",default="stock",help="Exact AI code variant; distinguishes patched from stock games")
p.add_argument("--require-canonical-decks",action="store_true",help="Refuse to reconstruct/overwrite the pre-verified commander deck")

args=p.parse_args()
assert 0 < args.clock < args.timeout
assert 1 <= args.games_per_rotation <= 10

PODS={
 "aristo": ["Brimaz_V3", "Kaal_9594008", "Kaal_10347090", "Kaal_21930525"],
 "artifact":["Brimaz_V3", "Kaal_23328062", "Kaal_11485202", "Kaal_22193355"],
}
decks=PODS[args.pod]
root=pathlib.Path.cwd()
directory=root/"forge_decks"
for name in decks:
    if name=="Brimaz_V3":
        continue
    path=directory/(name+".dck")
    if not path.is_file():
        raise FileNotFoundError(f"Missing required validated deck: {path}")

# Never overwrite a canonical Brimaz deck that was checked against Scryfall
# and Forge. Earlier code silently regenerated this file after its SHA check.
brimaz_file=directory/"Brimaz_V3.dck"
if not brimaz_file.is_file():
    if args.require_canonical_decks:
        raise FileNotFoundError("Pre-validated canonical Brimaz deck absent")
    source=root/"decks/Brimaz_V3.txt"
    entries=[]
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m=re.fullmatch(r"(\d+)\s+(.+)",line.strip())
        if not m: raise ValueError("Malformed Brimaz entry: "+line)
        entries.append((int(m.group(1)),m.group(2)))
    assert sum(q for q,n in entries)==100
    assert sum(q for q,n in entries if n=="Brimaz, Blight of Oreskos")==1
    brimaz_file.write_text(
        "[metadata]\nName=Brimaz V3\n[Main]\n" +
        "".join(f"{q} {name}\n" for q,name in entries if name!="Brimaz, Blight of Oreskos")+
        "[Commander]\n1 Brimaz, Blight of Oreskos\n",encoding="utf-8"
    )
jar=pathlib.Path(args.jar).resolve()
runtime_dir=pathlib.Path(args.runtime_dir).resolve() if args.runtime_dir else jar.parent
if not runtime_dir.is_dir():
    raise FileNotFoundError("Forge runtime directory missing: "+str(runtime_dir))
out=root/"results"/"batch"/args.pod/args.out_tag
out.mkdir(parents=True,exist_ok=True)
summary=[]
start=time.monotonic()

for shift in ([args.rotation] if args.rotation is not None else range(4)):
    seats=decks[shift:]+decks[:shift]
    br_index=seats.index("Brimaz_V3")+1
    for repeat in range(args.games_per_rotation):
        num=len(summary)+1
        seed=args.seed_base + 10000*shift + repeat
        profiles=[args.profile_brimaz if d=="Brimaz_V3" else args.profile_opponents for d in seats]
        cmd=["java","-Xmx4g","-jar",str(jar),"sim","-d",
             *[x+".dck" for x in seats],"-D",str(directory),
             "-f","Commander","-n","1","-c",str(args.clock),
             "-s",str(seed),"-a",*profiles]

        print("START",num,"seats",seats,"Brimaz seat",br_index,flush=True)
        st=time.monotonic()
        proc_timeout=False
        try:
            proc=subprocess.run(cmd,cwd=runtime_dir,text=True,capture_output=True,
                                errors="replace",timeout=args.timeout)
            stdout,stderr=proc.stdout,proc.stderr
            rc=proc.returncode
        except subprocess.TimeoutExpired as err:
            proc_timeout=True
            stdout=(err.stdout or b"").decode("utf-8",errors="replace") if isinstance(err.stdout,bytes) else (err.stdout or "")
            stderr=(err.stderr or b"").decode("utf-8",errors="replace") if isinstance(err.stderr,bytes) else (err.stderr or "")
            rc=None
        elapsed=round(time.monotonic()-st,2)
        raw=stdout+"\n[STDERR]\n"+stderr
        logfile=out/f"game_rot{shift}_rep{repeat:03d}_seat{br_index}.log"
        logfile.write_text(raw,encoding="utf-8")
        winners=re.findall(r"Game Result: Game\s+\d+\s+ended in\s+(\d+)\s*ms\.\s*Ai\((\d+)\)-(.+?) has won!",stdout)
        outcomes=re.findall(r"^Game Outcome: (.+)$",stdout,re.M)
        multiple_winners=sum("has won because all opponents have lost" in x for x in outcomes)>1
        clock_cutoff=any(int(ms)>=args.clock*1000-2500 for ms,_,_ in winners)
        # Forge may print a winner despite earlier repeated Java exceptions.
        # Such games are never evidence of valid Commander outcomes.
        engine_fault = any(x in raw for x in (
            "java.lang.NullPointerException", "Exception in thread",
            "java.lang.IllegalStateException", "StackOverflowError",
            "OutOfMemoryError", "Simulation: Couldn't play land"))
        if engine_fault:status="engine_fault"
        elif proc_timeout:status="process_timeout"
        elif rc!=0:status="engine_failed"
        elif clock_cutoff or multiple_winners or "Stopping slow match as draw" in stdout:status="clock_censored"
        elif len(winners)!=1:status="unparsed"
        else:status="complete"
        winner_index=int(winners[-1][1]) if status=="complete" else None
        record={
            "game":num,"pod":args.pod,"rotation":shift,"repeat":repeat,
            "clock_seconds":args.clock,
            "seed":seed,"profiles":profiles,"brimaz_profile":args.profile_brimaz,
            "policy":args.policy_label,"planner_decisions":raw.count("BRIMAZ_PLANNER:"),
            "development_actions":raw.count("BRIMAZ_DEVELOPMENT:"),
            "commander_priority_actions":raw.count("BRIMAZ_DEVELOPMENT: cast-commander"),
            "incubator_priority_actions":raw.count("BRIMAZ_DEVELOPMENT: transform-incubator"),
            "seats":seats,"brimaz_seat":br_index,
            "status":status,"engine_fault_detected":engine_fault,"winner_seat":winner_index,
            "winner_deck":seats[winner_index-1] if winner_index else None,
            "brimaz_win":winner_index==br_index if winner_index else None,
            "game_milliseconds":int(winners[-1][0]) if winners else None,
            "wall_seconds":elapsed,"process_exit":rc,
            "brimaz_casts":len(re.findall(r"\bcast Brimaz, Blight of Oreskos\b",stdout)),
            "brimaz_triggered":len(re.findall(r"\btriggered Brimaz, Blight of Oreskos\b",stdout)),
            "incubator_transforms":len(re.findall(r"\bactivated Incubator Token\b",stdout)),
            "end_step_mentions":len(re.findall(r"Phase: .* End step",stdout)),
            "ai_incubate_warning":"No AI assigned for API: Incubate" in stderr,
            "ai_quality_signatures":inspect_ai_quality_signatures(raw),
            "log":str(logfile.relative_to(root)),
        }
        summary.append(record)
        (out/"games.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print("FINISH",json.dumps({k:record[k] for k in ("game","status","winner_deck","brimaz_win","wall_seconds","brimaz_triggered","incubator_transforms")},ensure_ascii=False),flush=True)

valid=[x for x in summary if x["status"]=="complete"]
stats={
  "pod":args.pod,"profile":args.profile_brimaz,"policy":args.policy_label,"rotation":args.rotation,"seed_base":args.seed_base,
  "games_total":len(summary),"games_complete":len(valid),
  "brimaz_wins":sum(x["brimaz_win"] for x in valid),
  "brimaz_win_rate":round(sum(x["brimaz_win"] for x in valid)/len(valid),4) if valid else None,
  "wins_by_deck":dict(collections.Counter(x["winner_deck"] for x in valid)),
  "status_counts":dict(collections.Counter(x["status"] for x in summary)),
  "elapsed_total_seconds":round(time.monotonic()-start,2),
  "method":"Independent Forge JVM processes with fixed -s seeds; same seed DOES NOT guarantee identical gameplay; isolated matrix jobs",
  "caveat":"Seeded independent games can diverge across replays due to AI timing or nondeterminism. Status complete is NOT sufficient for a certified win: independently run certify_commander_games.py."
}
(out/"summary.json").write_text(json.dumps(stats,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("POD SUMMARY",json.dumps(stats,ensure_ascii=False),flush=True)
# Timeout/clock cutoff is an expected censored observation, not a failed CI job.
# Engine exceptions, process timeouts and unparseable matches remain failures.
bad={"engine_failed","engine_fault","process_timeout","unparsed"}
sys.exit(2 if any(x["status"] in bad for x in summary) else 0)
