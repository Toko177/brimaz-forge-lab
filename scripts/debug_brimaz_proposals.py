#!/usr/bin/env python3
"""Print raw play-by-play context around V3 planner proposals for QA."""
import argparse,pathlib
p=argparse.ArgumentParser()
p.add_argument("--dir",default="artifacts")
args=p.parse_args()
count=0
for file in sorted(pathlib.Path(args.dir).rglob("game_*.log")):
    lines=file.read_text(encoding="utf-8",errors="replace").splitlines()
    for i,line in enumerate(lines):
        if "BRIMAZ_PLANNER:" not in line:
            continue
        count+=1
        print(f"===== PROPOSAL {count} {file} line {i+1} =====",flush=True)
        for k in range(max(0,i-12),min(len(lines),i+120)):
            txt=lines[k]
            if k<=i+8 or any(tok in txt for tok in
                 ("Add To Stack:", "activated", "Phase:", "Turn:", "sacrif", "Game Result:",
                  "BRIMAZ_PLANNER:", "resolved", "Resolve", "Error", "Counter", "Cost", "No AI")):
                print(f"{k+1}: {txt[:400]}",flush=True)
        print("===== END =====",flush=True)
print("PROPOSALS_INSPECTED",count)
