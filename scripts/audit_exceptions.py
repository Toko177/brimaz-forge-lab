#!/usr/bin/env python3
import pathlib,re
files=sorted(pathlib.Path("artifacts").rglob("game_*.log"))
for path in files:
    lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
    for i,line in enumerate(lines):
        if re.search(r"NullPointerException|Exception in thread|IllegalStateException|StackOverflowError",line):
            print("EXCEPTION_CONTEXT",path,"line",i+1,flush=True)
            print("\n".join(f"{j+1}: {lines[j][:300]}" for j in range(max(0,i-7),min(len(lines),i+17))),flush=True)
print("SCANNED",len(files),"game transcripts",flush=True)
