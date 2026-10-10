#!/usr/bin/env python3
"""Observe real Forge 4-AI CPU hotspots using JDK Flight Recorder, no rules patch.

JFR samples are *statistical* CPU stacks, not proof of a bug in any card.
The profiler is opt-in, separate from scorekeeping; JFR overhead makes this
run unsuitable for comparing deck performance or winrates.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import time

from deckbuild_run import OPPONENTS

def method_name(frame):
    method=frame.get("method") or {}
    owner=(method.get("type") or {}).get("name") or ""
    return owner.replace("/",".")+"."+(method.get("name") or "<unknown>")

def summarize(data):
    events=(data.get("recording") or {}).get("events") or []
    cpu=Counter()
    ai=Counter()
    frames=Counter()
    category=Counter()
    ai_samples=0
    for event in events:
        if event.get("type")!="jdk.ExecutionSample":
            continue
        stack=(event.get("values") or {}).get("stackTrace") or {}
        chain=[method_name(f) for f in (stack.get("frames") or [])]
        if not chain:
            continue
        cpu[chain[0]]+=1
        ai_chain=[f for f in chain if f.startswith("forge.ai.")]
        if not ai_chain:
            continue
        ai_samples+=1
        frames[ai_chain[0]]+=1
        names=set(ai_chain)
        if any("AiBlockController." in v for v in names):
            category["block_assignment_or_prediction"]+=1
        elif any("AiAttackController." in v for v in names):
            category["attack_prediction"]+=1
        elif any("ComputerUtilCombat." in v for v in names):
            category["combat_util"]+=1
        elif any("ComputerUtilMana." in v for v in names):
            category["mana_search"]+=1
        else:
            category["other_forge_ai"]+=1
        for name in names:
            ai[name]+=1
    return {
        "events":len(events),
        "java_cpu_samples_with_stack":sum(cpu.values()),
        "java_cpu_samples_reaching_forge_ai":ai_samples,
        "share_of_cpu_samples_in_ai":round(ai_samples/max(1,sum(cpu.values())),4),
        "combat_related_samples":sum(category[v] for v in ("block_assignment_or_prediction",
                        "attack_prediction","combat_util")),
        "classified_ai_samples":dict(category),
        "ai_methods_in_sample_stack":dict(ai.most_common(30)),
        "top_ai_method_nearest_cpu":dict(frames.most_common(30)),
        "raw_top_cpu_methods":dict(cpu.most_common(15)),
        "interpretation":"Sampling observation, not proof of which optimization is correct; no game outcome or CPU comparison claimed.",
    }

def jfr_file_report(path):
    out=subprocess.run(["jfr","print","--json","--events","jdk.ExecutionSample",str(path)],
                       capture_output=True,text=True,timeout=180,check=True)
    data=json.loads(out.stdout)
    return summarize(data)

def run_probe(*,jar,decks,pod,rotation,seed,clock,timeout,output):
    if pod not in OPPONENTS or rotation not in range(4) or clock<20 or timeout<=clock:
        raise ValueError("Invalid real Commander profiler parameters")
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    names=["Brimaz_V3"]+OPPONENTS[pod]
    seats=names[rotation:]+names[:rotation]
    decks=Path(decks).resolve()
    jar=Path(jar).resolve()
    for name in seats:
        if not (decks/(name+".dck")).is_file():
            raise FileNotFoundError(name+".dck")
    jfr=output/"real-four-ai-cpu.jfr"
    cmd=["java","-Xmx4g",
         f"-XX:StartFlightRecording=filename={jfr},settings=profile,maxsize=48m,dumponexit=true",
         "-jar",str(jar),"sim","-d",*[name+".dck" for name in seats],
         "-D",str(decks),"-f","Commander","-n","1","-c",str(clock),
         "-s",str(seed),"-a",*["Default"]*4]
    start=time.monotonic()
    censored=False
    try:
        p=subprocess.run(cmd,cwd=jar.parent,capture_output=True,text=True,
                         errors="replace",timeout=timeout)
        stdout,stderr,rc=p.stdout,p.stderr,p.returncode
    except subprocess.TimeoutExpired as e:
        censored=True
        stdout=e.stdout.decode(errors="replace") if isinstance(e.stdout,bytes) else e.stdout or ""
        stderr=e.stderr.decode(errors="replace") if isinstance(e.stderr,bytes) else e.stderr or ""
        rc=None
    (output/"original-forge-game.log").write_text(stdout+"\n[STDERR]\n"+stderr,encoding="utf-8")
    result={
        "pod":pod,"rotation":rotation,"seed":seed,"actual_four_seats":seats,
        "clock_seconds":clock,"wall_seconds":round(time.monotonic()-start,2),
        "process_exit":rc,"process_timed_out":censored,
        "game_winner_claimed":False,
        "jfr_file_exists":jfr.exists(),
    }
    if not jfr.exists():
        raise ValueError("No JFR recording from true Forge JVM; refuse fictional profiling")
    result["profile"]=jfr_file_report(jfr)
    (output/"cpu-profile.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("REAL_FOUR_AI_FORGE_JFR_COMBAT_PROFILE",json.dumps(result,ensure_ascii=False),flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--jar",required=True,type=Path)
    p.add_argument("--decks",required=True,type=Path)
    p.add_argument("--pod",required=True,choices=sorted(OPPONENTS))
    p.add_argument("--rotation",type=int,default=0)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--clock",type=int,default=360)
    p.add_argument("--timeout",type=int,default=445)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    run_probe(jar=a.jar,decks=a.decks,pod=a.pod,rotation=a.rotation,
              seed=a.seed,clock=a.clock,timeout=a.timeout,output=a.output)

if __name__=="__main__":
    main()
