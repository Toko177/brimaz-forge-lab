#!/usr/bin/env python3
"""Inspect genuine Forge 4-seat Java AI timeout stacks, without causal guessing.

Never infer that the lastCandidate card actually CAUSED the timeout. Consume
real raw Forge logs (not simulator fixtures) and report observed Java frames.
"""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import re

TIMEOUT=re.compile(r"^AI_EVAL_TIMEOUT_V10: player=(Ai\([1-4]\)-.*?) globalTurn=(\d+) phase=(\S+) elapsedMs=(\d+) timeoutSecs=(\d+) listed=(\d+) considered=(\d+) lastCandidate=(.*)$")
SLOW=re.compile(r"^AI_EVAL_SLOW_V10: player=(Ai\([1-4]\)-.*?) globalTurn=(\d+) phase=(\S+) elapsedMs=(\d+).*")
FRAME=re.compile(r"^\s*at\s+([A-Za-z0-9_$\.]+)\(([^()]*)\)\s*$")

def classify(frames):
    text="\n".join(frames)
    tags=[]
    if "forge.ai.AiBlockController." in text or "forge.ai.ComputerUtilCombat." in text or "forge.game.combat.CombatUtil." in text:
        tags.append("combat_search")
    if "forge.game.staticability." in text or "updateStaticAbilities" in text or "getStaticAbilities" in text:
        tags.append("static_abilities")
    if "forge.game.replacement." in text or "updateReplacementEffects" in text or "getReplacementEffects" in text:
        tags.append("replacement_effects")
    if "forge.game.trigger." in text or "combatTriggerWillTrigger" in text:
        tags.append("trigger_requirements")
    if "forge.game.keyword." in text:
        tags.append("keyword_expansion")
    if not tags:tags=["unclassified"]
    return tags

def examine(log_text,identity):
    lines=log_text.splitlines()
    out=[]
    slow=[]
    for i,line in enumerate(lines):
        m=SLOW.match(line)
        if m:slow.append({"player":m.group(1),"turn":int(m.group(2)),
                          "phase":m.group(3),"elapsed_ms":int(m.group(4))})
        m=TIMEOUT.match(line)
        if not m:continue
        frames=[]
        # Original Forge may write budget-adaptation lines before the stack.
        stackstart=next((j for j in range(i+1,min(i+25,len(lines)))
                        if lines[j].strip()=="AI eval thread at timeout:"),None)
        if stackstart is not None:
            for txt in lines[stackstart+1:stackstart+36]:
                f=FRAME.match(txt)
                if not f:break
                frames.append(f.group(1))
        out.append({
            "source":identity,"player":m.group(1),"global_turn":int(m.group(2)),
            "phase":m.group(3),"elapsed_ms":int(m.group(4)),
            "allowed_seconds":int(m.group(5)),"listed_candidates":int(m.group(6)),
            "visited_candidates":int(m.group(7)),
            "last_visited_card_not_proven_cause":m.group(8),
            "stack_available":bool(frames),"java_frames":frames,
            "observed_stack_categories":classify(frames),
        })
    return out,slow

def analyze(root):
    manifests=sorted(root.rglob("games.json"))
    if not manifests:raise ValueError("No genuine Forge game manifests found")
    events=[];slows=[];statuses=Counter()
    logs=0
    for manifest in manifests:
        rows=json.loads(manifest.read_text(encoding="utf-8"))
        for r in rows:
            name=Path(r["log"]).name
            log=manifest.parent/name
            if not log.is_file():raise ValueError("Missing source game log "+str(log))
            raw=log.read_text(encoding="utf-8",errors="replace")
            if "Turn: Turn " not in raw or "Ai(1)-" not in raw:
                raise ValueError("Not a real Forge four-seat gameplay log "+str(log))
            logs+=1;statuses[r["status"]]+=1
            ident={"pod":r["pod"],"rotation":r["rotation"],"seed":r["seed"],
                   "policy":r["policy"],"log":str(log)}
            a,b=examine(raw,ident)
            events.extend(a)
            slows.extend([{**x,"source":ident} for x in b])
    cats=Counter(x for e in events for x in e["observed_stack_categories"])
    return {
        "real_game_log_count":logs,
        "real_game_statuses":dict(statuses),
        "timeout_count":len(events),
        "slow_complete_evaluations":len(slows),
        "timeouts_by_player":dict(Counter(e["player"] for e in events)),
        "timeouts_by_phase":dict(Counter(e["phase"] for e in events)),
        "timeout_java_stack_category_counts_not_causes":dict(cats),
        "slow_evaluation_phase_counts":dict(Counter(e["phase"] for e in slows)),
        "timeouts":events,
        "limitations":[
            "The lastCandidate is only the latest evaluated card, NOT necessarily the cause.",
            "A Java stack is a point-in-time observation and cannot prove causal CPU contribution.",
            "Multiple stack categories can overlap for one timeout.",
            "No fabricated natural-game outcomes; censored processes remain censored.",
        ],
    }

def render(r):
    lines=["# Real four-AI Forge Java timeout diagnostics","",
           f"- Genuine JVM game logs examined: **{r['real_game_log_count']}**",
           f"- Statuses: {r['real_game_statuses']}",
           f"- Observed AI timeouts: **{r['timeout_count']}**",
           f"- Completed but slow AI evaluations: **{r['slow_complete_evaluations']}**",
           "", "## Observed stack hot-path categories (overlapping)", ""]
    for k,n in sorted(r["timeout_java_stack_category_counts_not_causes"].items(),
                      key=lambda x:-x[1]):lines.append(f"- {k}: {n}")
    lines.extend(["","## Individual genuine timeouts","",
                  "| Pod / policy | Global turn | Player | Phase | Budget | Last candidate (NOT root cause) | Stack tags |",
                  "|---|---:|---|---|---:|---|---|"])
    for e in r["timeouts"]:
        src=e["source"]
        lines.append(f"| {src['pod']} / {src['policy']} | {e['global_turn']} | "
                     f"{e['player']} | {e['phase']} | {e['allowed_seconds']}s | "
                     f"{e['last_visited_card_not_proven_cause']} | "
                     f"{', '.join(e['observed_stack_categories'])} |")
    lines+=["","## Limitations",""]+["- "+x for x in r["limitations"]]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=analyze(a.input)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"ai_timeout_stacks.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (a.out/"ai_timeout_stacks.md").write_text(render(report),encoding="utf-8")
    print("FOUR_AI_TIMEOUT_STACK_AUDIT",json.dumps({
        "real_game_logs":report["real_game_log_count"],
        "timeouts":report["timeout_count"],
        "categories":report["timeout_java_stack_category_counts_not_causes"],
        "censoring":report["real_game_statuses"],
    },ensure_ascii=False),flush=True)
if __name__=="__main__":main()
