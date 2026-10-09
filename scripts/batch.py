#!/usr/bin/env python3
"""Forge EDH batch: 4 independent games, rotating the four deck seat positions.

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

p=argparse.ArgumentParser()
p.add_argument("--jar",required=True)
p.add_argument("--pod",choices=["aristo","artifact"],default="aristo")
p.add_argument("--clock",type=int,default=360)
p.add_argument("--timeout",type=int,default=445)
p.add_argument("--games-per-rotation",type=int,default=1)
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
    path=directory/(name+".dck")
    if not path.is_file():
        raise FileNotFoundError(f"Missing required validated deck: {path}")

# The previously validated smoke-run script writes a Forge .dck for Brimaz;
# the same exact baseline is created here for independent batch execution.
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
(directory/"Brimaz_V3.dck").write_text(
    "[metadata]\nName=Brimaz V3\n[Main]\n" +
    "".join(f"{q} {name}\n" for q,name in entries if name!="Brimaz, Blight of Oreskos")+
    "[Commander]\n1 Brimaz, Blight of Oreskos\n",encoding="utf-8"
)
jar=pathlib.Path(args.jar).resolve()
out=root/"results"/"batch"/args.pod
out.mkdir(parents=True,exist_ok=True)
summary=[]
start=time.monotonic()

for shift in range(4):
    seats=decks[shift:]+decks[:shift]
    br_index=seats.index("Brimaz_V3")+1
    for repeat in range(args.games_per_rotation):
        num=len(summary)+1
        cmd=["java","-Xmx4g","-jar",str(jar),"sim","-d",
             *[x+".dck" for x in seats],"-D",str(directory),
             "-f","Commander","-n","1","-c",str(args.clock)]
        print("START",num,"seats",seats,"Brimaz seat",br_index,flush=True)
        st=time.monotonic()
        proc_timeout=False
        try:
            proc=subprocess.run(cmd,cwd=jar.parent,text=True,capture_output=True,
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
        logfile=out/f"game_{num:03d}_seat{br_index}.log"
        logfile.write_text(raw,encoding="utf-8")
        winners=re.findall(r"Game Result: Game\s+\d+\s+ended in\s+(\d+)\s*ms\.\s*Ai\((\d+)\)-(.+?) has won!",stdout)
        outcomes=re.findall(r"^Game Outcome: (.+)$",stdout,re.M)
        multiple_winners=sum("has won because all opponents have lost" in x for x in outcomes)>1
        clock_cutoff=any(int(ms)>=args.clock*1000-2500 for ms,_,_ in winners)
        if proc_timeout:status="process_timeout"
        elif rc!=0:status="engine_failed"
        elif clock_cutoff or multiple_winners:status="clock_censored"
        elif len(winners)!=1:status="unparsed"
        else:status="complete"
        winner_index=int(winners[-1][1]) if status=="complete" else None
        record={
            "game":num,"pod":args.pod,"rotation":shift,"repeat":repeat,
            "seats":seats,"brimaz_seat":br_index,
            "status":status,"winner_seat":winner_index,
            "winner_deck":seats[winner_index-1] if winner_index else None,
            "brimaz_win":winner_index==br_index if winner_index else None,
            "game_milliseconds":int(winners[-1][0]) if winners else None,
            "wall_seconds":elapsed,"process_exit":rc,
            "brimaz_casts":len(re.findall(r"\bcast Brimaz, Blight of Oreskos\b",stdout)),
            "brimaz_triggered":len(re.findall(r"\btriggered Brimaz, Blight of Oreskos\b",stdout)),
            "incubator_transforms":len(re.findall(r"\bactivated Incubator Token\b",stdout)),
            "end_step_mentions":len(re.findall(r"Phase: .* End step",stdout)),
            "ai_incubate_warning":"No AI assigned for API: Incubate" in stderr,
            "log":str(logfile.relative_to(root)),
        }
        summary.append(record)
        (out/"games.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print("FINISH",json.dumps({k:record[k] for k in ("game","status","winner_deck","brimaz_win","wall_seconds","brimaz_triggered","incubator_transforms")},ensure_ascii=False),flush=True)

valid=[x for x in summary if x["status"]=="complete"]
stats={
  "pod":args.pod,"games_total":len(summary),"games_complete":len(valid),
  "brimaz_wins":sum(x["brimaz_win"] for x in valid),
  "brimaz_win_rate":round(sum(x["brimaz_win"] for x in valid)/len(valid),4) if valid else None,
  "wins_by_deck":dict(collections.Counter(x["winner_deck"] for x in valid)),
  "status_counts":dict(collections.Counter(x["status"] for x in summary)),
  "elapsed_total_seconds":round(time.monotonic()-start,2),
  "method":"4 independent Forge processes, one Brimaz per pod, one rotation per seat",
  "caveat":"Small pilot sample. AI quality, card support and bracket legality not completely audited."
}
(out/"summary.json").write_text(json.dumps(stats,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("POD SUMMARY",json.dumps(stats,ensure_ascii=False),flush=True)
sys.exit(0 if len(valid)==len(summary) else 2)
