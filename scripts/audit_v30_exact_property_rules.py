#!/usr/bin/env python3
"""A/B evidence from authentic four-AI Forge gameplay for V30 literal rules fast path.

Third game verifies optimized return values against the EXACT original Forge
CardProperty method at the same state (fail-closed). No fake wins/throughput.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

PFX=("Turn: ","Phase: ","Add To Stack: ","Combat: ","Game Outcome: ",
     "Damage: ","Life: ","Zone Change: ","Land: ","Counter: ","Poison: ")
PROOF=re.compile(r"^FOUR_AI_V30_CARD_PROPERTY_FAST_STATS hits=(\d+) verified=(\d+) mismatches=(\d+)$",re.M)
TAGS=(("control","V30-stock-exact"),("fast","V30-fast-exact"),
      ("shadow","V30-shadow-verified"))

def parse(root,pod,rotation):
    entries={}
    for label,tag in TAGS:
        manifest=root/pod/tag/"games.json"
        rec=json.loads(manifest.read_text(encoding="utf-8"))
        if len(rec)!=1:raise ValueError("Expected one actual four-seat game for "+label)
        game=rec[0]
        raw=(manifest.parent/Path(game["log"]).name).read_text(encoding="utf-8",errors="replace")
        match=(r"^Ai\(1\)-.+? vs Ai\(2\)-.+? vs Ai\(3\)-.+? vs "
               r"Ai\(4\)-.+? - one game of Commander seed")
        if not re.search(match,raw,re.M):
            raise ValueError("Not original four-seat Forge Commander transcript")
        if len(game["seats"])!=4 or len(set(game["seats"]))!=4 \
           or game["seats"].count("Brimaz_V3")!=1:
            raise ValueError("Actual canonical Commander seats missing")
        status=game["status"]
        if status=="complete":
            if game["winner_seat"] not in (1,2,3,4) or \
                game["seats"][game["winner_seat"]-1]!=game["winner_deck"]:
                raise ValueError("Inconsistent claimed natural winner")
        elif game["winner_deck"] is not None:
            raise ValueError("Non-natural Forge game cannot claim a winner")
        events=[x for x in raw.splitlines() if x.startswith(PFX)
                and "Match Duration" not in x]
        if not events or not any(x.startswith("Turn: ") for x in events):
            raise ValueError("Empty real Forge action transcript")
        counters=PROOF.findall(raw)
        proof={"fast_calls":int(counters[-1][0]),
               "stock_same_state_checks":int(counters[-1][1]),
               "rule_mismatches":int(counters[-1][2])} if counters else None
        entries[label]={
          "seed":game["seed"],"seats":game["seats"],"pod":game["pod"],
          "rotation":game["rotation"],"status":status,
          "winner":game["winner_deck"],"wall_seconds":game["wall_seconds"],
          "actual_game_events_sha256":hashlib.sha256("\n".join(events).encode()).hexdigest(),
          "observed_events":len(events),"real_card_rule_checks":proof,
          "ai_timeouts":raw.count("AI_EVAL_TIMEOUT_V10:"),
        }
    ctrl,fast,shadow=(entries[k] for k in ("control","fast","shadow"))
    for k in ("seed","seats","pod","rotation"):
        if ctrl[k]!=fast[k] or ctrl[k]!=shadow[k]:
            raise ValueError("Mispaired real Forge 4-AI games "+k)
    if ctrl["pod"]!=pod or ctrl["rotation"]!=rotation:
        raise ValueError("Unexpected pod/seat")
    if fast["real_card_rule_checks"] is None:
        raise ValueError("Missing genuine JVM fast-hit evidence")
    if shadow["real_card_rule_checks"] is None:
        raise ValueError("Missing same-state stock rules audit evidence")
    if shadow["real_card_rule_checks"]["stock_same_state_checks"]<1000:
        raise ValueError("Insufficient actual same-state Oracle rule comparisons")
    if (shadow["real_card_rule_checks"]["rule_mismatches"]!=0
            or fast["real_card_rule_checks"]["rule_mismatches"]!=0):
        raise ValueError("Card property Oracle semantic mismatch")
    same=(ctrl["status"]==fast["status"]=="complete"
          and ctrl["actual_game_events_sha256"]==fast["actual_game_events_sha256"])
    return {
      "pod":pod,"rotation":rotation,"real_forge_jvms":3,
      "baseline":ctrl,"optimized":fast,"same_state_oracle_shadow":shadow,
      "verified_original_rules_same_state_comparisons":
          shadow["real_card_rule_checks"]["stock_same_state_checks"],
      "original_rule_comparison_mismatches":0,
      "natural_event_trace_identical":same,
      "speed_ratio_only_same_natural_game":round(
          ctrl["wall_seconds"]/fast["wall_seconds"],4)
          if same and fast["wall_seconds"]>0 else None,
      "limitations":[
        "The original Forge method body is unchanged and called as shadow on each chosen fast literal.",
        "Shadow validation increases compute cost and is never used for speed comparison.",
        "A natural identical observable action sequence does not prove complete Magic Oracle correctness.",
        "Unmatched timing after AI timeouts may cause divergent games with the same seed.",
        "Do not count clock censures as losses or wins.",
        "A small pair does not establish general throughput improvement.",
      ],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("results/batch"))
    p.add_argument("--pod",choices=("aristo","artifact"),required=True)
    p.add_argument("--rotation",type=int,required=True)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    report=parse(a.input,a.pod,a.rotation)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FOUR_AI_V30_GENUINE_ORACLE_RULES_AUDIT",json.dumps({
      "pod":a.pod,"rotation":a.rotation,
      "natural_equal_actions":report["natural_event_trace_identical"],
      "rule_same_state_checks":report["verified_original_rules_same_state_comparisons"],
      "mismatches":report["original_rule_comparison_mismatches"],
      "fast_calls":report["optimized"]["real_card_rule_checks"]["fast_calls"],
      "status":[report["baseline"]["status"],report["optimized"]["status"],
                report["same_state_oracle_shadow"]["status"]],
      "speed_ratio":report["speed_ratio_only_same_natural_game"],
    },ensure_ascii=False),flush=True)

if __name__=="__main__":main()
