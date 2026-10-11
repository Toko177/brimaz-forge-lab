#!/usr/bin/env python3
"""General four-AI Forge Commander tournament, not hardcoded to Brimaz.

Two immutable A/B variants face identical opponent sets and seat rotations.
Each game uses an independent JVM and the full raw log is retained. The
launcher status is provisional until deckbuild_certify.py runs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from forge_result_evidence import inspect_ai_quality_signatures

OPPONENTS={
    "aristo":["Kaal_9594008","Kaal_10347090","Kaal_21930525"],
    "artifact":["Kaal_23328062","Kaal_11485202","Kaal_22193355"],
}
RESULT=re.compile(r"Game Result: Game\s+\d+\s+ended in\s+(\d+)\s*ms\.\s*Ai\((\d+)\)-(.+?) has won!")


def verify_inputs(directory,manifest,arm,pod):
    spec=manifest["decks"][arm]
    target=spec["label"]
    if target not in ("Deck_Reference","Deck_Candidate"):
        raise ValueError("Unknown A/B variant label")
    names=[target]+OPPONENTS[pod]
    for name in names:
        f=directory/(name+".dck")
        if not f.is_file():
            raise FileNotFoundError(f)
        if name==target and hashlib.sha256(f.read_bytes()).hexdigest()!=spec["forge_sha256"]:
            raise ValueError(f"Candidate deck mutated since SHA256 verification: {name}")
    if len(set(names))!=4:
        raise ValueError("Four distinct deck identities required")
    return names


def run_games(*,jar,directory,manifest,arm,pod,rotation,seed_base,repeats,clock,timeout,out,
              profile="Default",policy="V13-incubate-adaptive"):
    if pod not in OPPONENTS or arm not in ("reference","candidate"):
        raise ValueError("Unknown opponent pod or candidate arm")
    if not (0<=rotation<=3 and 1<=repeats<=10 and 20<=clock<timeout):
        raise ValueError("Invalid rotation/game count/timeout")
    if profile not in ("Default","Experimental","Cautious","Reckless"):
        raise ValueError("Unknown Forge AI profile")
    directory=Path(directory).resolve()
    jar=Path(jar).resolve()
    names=verify_inputs(directory,manifest,arm,pod)
    seats=names[rotation:]+names[:rotation]
    label=manifest["decks"][arm]["label"]
    seat=seats.index(label)+1
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    results=[]
    for rep in range(repeats):
        seed=seed_base+10000*rotation+rep
        command=["java","-Xmx4g","-jar",str(jar),"sim","-d",
                 *[n+".dck" for n in seats],"-D",str(directory),
                 "-f","Commander","-n","1","-c",str(clock),
                 "-s",str(seed),"-a",*[profile]*4]
        print("DECKBUILD_START",json.dumps({"arm":arm,"pod":pod,"rotation":rotation,
              "seed":seed,"seat":seat,"decks":seats}),flush=True)
        st=time.monotonic()
        process_timeout=False
        try:
            p=subprocess.run(command,cwd=jar.parent,capture_output=True,text=True,
                             errors="replace",timeout=timeout)
            stdout,stderr,rc=p.stdout,p.stderr,p.returncode
        except subprocess.TimeoutExpired as e:
            process_timeout=True
            stdout=e.stdout.decode("utf-8",errors="replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
            stderr=e.stderr.decode("utf-8",errors="replace") if isinstance(e.stderr,bytes) else (e.stderr or "")
            rc=None
        raw=stdout+"\n[STDERR]\n"+stderr
        name=f"game_{arm}_{pod}_rot{rotation}_rep{rep}.log"
        log=out/name
        log.write_text(raw,encoding="utf-8")
        matches=RESULT.findall(raw)
        outcomes=re.findall(r"^Game Outcome: (.+)$",raw,re.M)
        cutoff=(any(int(ms)>=clock*1000-2500 for ms,_,_ in matches)
                or "Stopping slow match as draw" in raw
                or sum("has won because all opponents have lost" in x for x in outcomes)>1)
        engine_fault=any(x in raw for x in (
            "Exception in thread","java.lang.NullPointerException","java.lang.IllegalStateException",
            "StackOverflowError","OutOfMemoryError","Simulation: Couldn't play land"))
        if engine_fault: status="engine_fault"
        elif process_timeout: status="process_timeout"
        elif rc!=0: status="engine_failed"
        elif cutoff: status="clock_censored"
        elif len(matches)!=1: status="unparsed"
        else: status="complete"
        winner_seat=int(matches[0][1]) if status=="complete" else None
        game_ms=int(matches[0][0]) if matches else None
        item={
            "arm":arm,"candidate_deck":label,"candidate_seat":seat,"candidate_win":(winner_seat==seat if winner_seat else None),
            "pod":pod,"rotation":rotation,"repeat":rep,"seed":seed,
            "seats":seats,"policy":policy,"profiles":[profile]*4,
            "clock_seconds":clock,"process_exit":rc,"game_milliseconds":game_ms,
            "winner_seat":winner_seat,"winner_deck":seats[winner_seat-1] if winner_seat else None,
            "status":status,"engine_fault_detected":engine_fault,
            "wall_seconds":round(time.monotonic()-st,2),
            "log":str(log.resolve()),"log_sha256":hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "candidate_deck_sha256":manifest["decks"][arm]["forge_sha256"],
            "ai_quality_signatures":inspect_ai_quality_signatures(raw),
        }
        results.append(item)
        (out/"games.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("DECKBUILD_FINISH",json.dumps({k:item[k] for k in
            ("arm","pod","seed","status","winner_deck","candidate_win","wall_seconds")},ensure_ascii=False),flush=True)
    return results


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--jar",required=True,type=Path)
    p.add_argument("--decks",type=Path,default=Path("forge_decks"))
    p.add_argument("--manifest",type=Path,default=Path("forge_decks/candidate-manifest.json"))
    p.add_argument("--arm",choices=["reference","candidate"],required=True)
    p.add_argument("--pod",choices=sorted(OPPONENTS),required=True)
    p.add_argument("--rotation",type=int,choices=range(4),required=True)
    p.add_argument("--seed-base",type=int,required=True)
    p.add_argument("--repeats",type=int,default=1)
    p.add_argument("--clock",type=int,default=360)
    p.add_argument("--timeout",type=int,default=445)
    p.add_argument("--profile",default="Default")
    p.add_argument("--policy",default="V13-incubate-adaptive")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
    rows=run_games(jar=a.jar,directory=a.decks,manifest=manifest,arm=a.arm,pod=a.pod,
                   rotation=a.rotation,seed_base=a.seed_base,repeats=a.repeats,
                   clock=a.clock,timeout=a.timeout,out=a.out,profile=a.profile,policy=a.policy)
    sys.exit(2 if any(g["status"] in ("engine_fault","process_timeout","engine_failed","unparsed") for g in rows) else 0)


if __name__=="__main__":
    main()
