#!/usr/bin/env python3
"""Forensic review of REAL Forge Commander transcript and game metadata.

No invented outcomes. Save stderr/exceptions and actual turn logs. This is
especially useful for clock-stopped games or suspiciously passive commander AI.
"""
import argparse,collections,json,pathlib,re

p=argparse.ArgumentParser()
p.add_argument("--source",default="artifacts")
p.add_argument("--output",default="results/postmortem/report.json")
args=p.parse_args()
out=[]
for manifest in sorted(pathlib.Path(args.source).rglob("games.json")):
    for game in json.loads(manifest.read_text(encoding="utf-8")):
        f=manifest.parent / pathlib.Path(game.get("log","")).name
        if not f.is_file():
            print("MISSING_LOG",manifest,game["seed"],flush=True)
            continue
        raw=f.read_text(encoding="utf-8",errors="replace")
        s=raw.splitlines()
        lines=[
            (i+1,line) for i,line in enumerate(s)
            if re.search(r"Exception in thread|NullPointerException|IllegalStateException|StackOverflowError|Card not found|Unknown card|No AI assigned for API:|Unable to create card|could not find card|Fatal",line,re.I)
        ]
        phases=collections.Counter(re.findall(r"^Phase: .+?'s ([^\n]+)$",raw,re.M))
        active_commander=len(re.findall(r"^Add To Stack: Ai\(\d+\)-Brimaz_V3 cast Brimaz, Blight of Oreskos",raw,re.M))
        # The engine uses different AI names, so also support the general cast line.
        brimaz_casts=len(re.findall(r"^Add To Stack: .+ cast Brimaz, Blight of Oreskos",raw,re.M))
        end_step_prolifs=0
        phase=""
        last_active=""
        for line in s:
            pm=re.match(r"^Phase: (.+?)'s (.+)$",line)
            if pm: last_active,phase=pm.group(1),pm.group(2)
            if phase=="End step" and "triggered Brimaz, Blight of Oreskos" in line:end_step_prolifs+=1
        fatal=[{"line":idx,"text":msg.strip()} for idx,msg in lines if
               "No AI assigned for API:" not in msg][:15]
        warnings=sorted(set(msg.strip() for _,msg in lines if "No AI assigned for API:" in msg))
        turns=[int(x) for x in re.findall(r"^Turn: Turn (\d+)",raw,re.M)]
        report={
            "pod":game["pod"],"policy":game["policy"],"rotation":game["rotation"],
            "repeat":game["repeat"],"seed":game["seed"],"status":game["status"],
            "winner":game.get("winner_deck"),"brimaz_win":game.get("brimaz_win"),
            "brimaz_casts_log":brimaz_casts,"brimaz_endstep_triggers":end_step_prolifs,
            "incubator_transform_actions":len(re.findall(r"activated Incubator Token",raw)),
            "brimaz_planner_proposals":raw.count("BRIMAZ_PLANNER:"),
            "turns_seen":len(turns),"last_turn":max(turns) if turns else None,
            "phase_endsteps":phases.get("End step",0),
            "forge_warnings":warnings,"errors":fatal,
            "raw_match_start":s[:14] if game["status"]!="complete" else [],
            "raw_match_end":s[-55:] if game["status"]!="complete" else [],
        }
        out.append(report)
        print("GAME_DIAGNOSTIC",json.dumps({k:v for k,v in report.items()
                 if k not in ("raw_match_start","raw_match_end")},ensure_ascii=False),flush=True)
        if fatal:print("ENGINE_ERRORS",json.dumps(fatal,ensure_ascii=False),flush=True)
        if game["status"]!="complete":
            print("CENSORED_CONTEXT",json.dumps({"pod":game["pod"],"policy":game["policy"],
                  "seed":game["seed"],"first_lines":s[:8],"tail":s[-40:]},ensure_ascii=False),flush=True)
agg={
 "games":len(out),"by_status":dict(collections.Counter(r["status"] for r in out)),
 "by_policy":dict(collections.Counter(r["policy"] for r in out)),
 "natural_brimaz_wins":sum(r["status"]=="complete" and r["brimaz_win"] is True for r in out),
 "games_with_errors":sum(bool(r["errors"]) for r in out),
 "games_no_brimaz_cast":sum(r["brimaz_casts_log"]==0 for r in out),
 "average_brimaz_cast":round(sum(r["brimaz_casts_log"] for r in out)/max(1,len(out)),2),
 "games_no_brimaz_endstep_prolif":sum(r["brimaz_endstep_triggers"]==0 for r in out),
}
print("FORENSIC_AGGREGATE",json.dumps(agg,ensure_ascii=False),flush=True)
dest=pathlib.Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps({"summary":agg,"games":out},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
