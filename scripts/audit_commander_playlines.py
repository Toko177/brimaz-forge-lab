#!/usr/bin/env python3
"""Read all real four-player Forge actions, preserving actual decisions by seat.

Diagnostic, not an expert oracle: logs contain actions taken, NOT every hand,
legal target or mana line available; no "missed optimal play" is asserted
without an independent snapshot of alternatives.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

TURN=re.compile(r"^Turn: Turn (\d+) \((Ai\((\d+)\)-.+)\)$")
CAST=re.compile(r"^Add To Stack: (Ai\((\d+)\)-.+?) cast (.+?)(?: targeting .*)?$")
ACTIVATE=re.compile(r"^Add To Stack: (Ai\((\d+)\)-.+?) activated (.+?)(?: targeting .*)?$")
LAND=re.compile(r"^Land: (Ai\((\d+)\)-.+?) played (.+?)(?: \(\d+\))?$")
COMBAT=re.compile(r"^Combat: (Ai\((\d+)\)-.+?) assigned (.+?) to attack (.+?)\.$")
OUTCOME=re.compile(r"^Game Outcome: (Ai\((\d+)\)-.+?) has (won|lost) ")
PHYREXIAN="Whenever you cast a Phyrexian creature or artifact creature spell, incubate X"
PROLIFERATE="At the beginning of each end step, if a Phyrexian died under your control"
TRANSFORM=" - Transform Phyrexian Token ("
DECK_MARK=("Deck_Candidate","Deck_Reference","Brimaz_V3")
LONG_EVENT=140

def extract(log, max_events=1500):
    raw=Path(log).read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    # Manifest status is not independent certification, but lets the action
    # explorer FLAG clock-forced pseudo-winners instead of miscounting them.
    manifest=Path(log).parent/"games.json"
    game_status="unknown"
    if manifest.exists():
        rows=json.loads(manifest.read_text(encoding="utf-8"))
        matches=[row for row in rows
                 if Path(row.get("log","")).name==Path(log).name]
        if len(matches)!=1:
            raise ValueError("Raw action log not uniquely linked to original game's manifest")
        if matches[0].get("log_sha256")!=digest:
            raise ValueError("Original transcript SHA256 differs from game manifest")
        game_status=matches[0].get("status","unknown")
    text=raw.decode("utf-8",errors="replace")
    lines=text.splitlines()
    current=None
    seats={}
    local_turn=defaultdict(int)
    actions=[]
    outcomes={}
    stats=defaultdict(Counter)
    cast_buckets=defaultdict(list)
    pending_incubator_owners=[]
    for num,line in enumerate(lines,1):
        m=TURN.match(line)
        if m:
            global_turn,player,seat=int(m[1]),m[2],int(m[3])
            local_turn[seat]+=1
            seats[seat]=player
            current={"global_turn":global_turn,"player":player,
                     "seat":seat,"local_turn":local_turn[seat]}
            pending_incubator_owners.clear()
            continue
        m=OUTCOME.match(line)
        if m:outcomes[int(m[2])]={"player":m[1],"result":m[3]}
        if current is None:continue
        kind=None
        player=None
        card=None
        target=None
        if (m:=CAST.match(line)):
            kind="cast";player=m[1];card=m[3]
        elif (m:=ACTIVATE.match(line)):
            kind="activate";player=m[1];card=m[3]
        elif (m:=LAND.match(line)):
            kind="land";player=m[1];card=m[3]
        elif (m:=COMBAT.match(line)):
            kind="attack";player=m[1];card=m[3];target=m[4]
        elif line.startswith("Resolve Stack: ") and PHYREXIAN in line:
            kind="incubate_trigger";card="Brimaz-trigger"
        elif line.startswith("Resolve Stack: ") and PROLIFERATE in line:
            kind="endstep_proliferate";card="Brimaz-trigger"
        elif line.startswith("Resolve Stack: ") and TRANSFORM in line:
            kind="incubator_transform_resolved";card="Phyrexian Token"
        elif line.startswith("AI_EVAL_TIMEOUT_V10:"):
            kind="ai_timeout";card=None
        elif line.startswith("AI Attack declaration invalid"):
            kind="invalid_attack_fallback";card=None
        if kind is None:continue
        # Brimaz triggered abilities may resolve during *another* player's
        # turn. Assign their effects to the controller, not the active seat.
        if kind=="incubator_transform_resolved" and pending_incubator_owners:
            # Attribute actual completed transformation to the preceding
            # activating player, rather than the active player's turn.
            seat=pending_incubator_owners.pop()
        elif kind in ("incubate_trigger","endstep_proliferate"):
            # At most one Brimaz commander deck in this audited pod.
            found=[n for n,v in seats.items() if any(t in v for t in DECK_MARK)]
            if len(found)!=1:
                raise ValueError("Cannot tie Brimaz trigger to unique owner")
            seat=found[0]
        else:
            seat=(int(re.search(r"Ai\((\d+)\)",player)[1]) if player else current["seat"])
        record={**current,"acting_seat":seat,"kind":kind,
                "card":card,"line":num}
        if target is not None:
            record["target"]=target
        if kind in ("attack","ai_timeout","invalid_attack_fallback"):
            record["detail"]=line[:LONG_EVENT]
        if len(actions)<max_events:actions.append(record)
        stats[seat][kind]+=1
        if kind=="activate" and card=="Incubator Token":
            pending_incubator_owners.append(seat)
        if kind=="cast":cast_buckets[seat].append(record)
    if not current:
        raise ValueError("No actual Forge 'Turn:' lines; refuse speculative reconstruction")
    brimaz_seats=[seat for seat,name in seats.items() if any(key in name for key in DECK_MARK)]
    if len(brimaz_seats)!=1:
        raise ValueError("Cannot identify exactly one Brimaz deck seat")
    seat=brimaz_seats[0]
    mine=[a for a in actions if a["acting_seat"]==seat]
    casts=[x for x in mine if x["kind"]=="cast"]
    commander_casts=[x for x in casts if x["card"]=="Brimaz, Blight of Oreskos"]
    total_actions=sum(sum(x.values()) for x in stats.values())
    # Full-game table politics proxy: attacker declarations TARGETING a player.
    # Not equivalent to number of attacking creatures, their power, or threat.
    attacks_to=Counter()
    for action in actions:
        if action["kind"]=="attack" and "target" in action:
            m=re.search(r"Ai\((\d+)\)",action["target"])
            if m and action["acting_seat"]!=int(m[1]):
                attacks_to[int(m[1])]+=1
    if len(actions)==max_events and total_actions>max_events:
        raise ValueError("Action buffer exhausted: full chronological audit required")
    return {
      "file":str(log),"sha256":digest,"launcher_status":game_status,
      "seats":seats,"outcomes":outcomes,
      "global_turns_observed":current["global_turn"],
      "all_player_actions_by_kind":{str(s):dict(v) for s,v in sorted(stats.items())},
      "brimaz":{
         "seat":seat,"player":seats[seat],
         "personal_turns_observed":local_turn[seat],
         "first_commander_cast_personal_turn":commander_casts[0]["local_turn"] if commander_casts else None,
         "commander_cast_count":len(commander_casts),
         "incubate_triggers_resolved":stats[seat]["incubate_trigger"],
         "endstep_proliferate_triggers_resolved":stats[seat]["endstep_proliferate"],
         "incubator_transforms_resolved":stats[seat]["incubator_transform_resolved"],
         "creature_and_other_spell_casts":len(casts),
         "cast_cards":dict(Counter(x["card"] for x in casts)),
         "land_plays":stats[seat]["land"],
         "attacks_declared":stats[seat]["attack"],
         "attacker_declarations_targeting_brimaz":attacks_to[seat],
         "attacker_declarations_targeting_other_players":sum(v for k,v in attacks_to.items() if k!=seat),
         "notes":[
           "No hidden hand/mana data is present in ordinary Forge logs; slow deployment does not by itself prove legal options were ignored.",
           "Resolved triggered abilities are counted on the active player turn, not necessarily their controller; cross-player stack resolution may require controller trace instrumentation.",
           "Cast counts do not measure card advantage, strategic targets, availability of opposing responses or correct play."
         ]
      },
      "actions":actions
    }

def aggregate(rows):
    games=len(rows)
    first=[r["brimaz"]["first_commander_cast_personal_turn"] for r in rows]
    return {
      "games":games,
      "brimaz_raw_winner_labels_UNCERTIFIED":sum(
          any(v["result"]=="won" for k,v in r["outcomes"].items()
              if int(k)==r["brimaz"]["seat"]) for r in rows),
      "raw_winner_label_warning":"Raw Game Outcome labels can be present even in clock-censored/artificially stopped games. NEVER count them as accepted victories; use deckbuild_certify.py only.",
      "brimaz_raw_winner_labels_in_censored_games":sum(
          r["launcher_status"]!="complete" and
          r["outcomes"].get(r["brimaz"]["seat"],{}).get("result")=="won"
          for r in rows),
      "clock_censored_games_by_manifest":sum(
          r["launcher_status"]=="clock_censored" for r in rows),
      "brimaz_games_without_cast":sum(x is None for x in first),
      "first_cast_turn_histogram":dict(sorted(Counter(str(x) for x in first).items())),
      "attack_declarations_received_by_brimaz":sum(r["brimaz"]["attacker_declarations_targeting_brimaz"] for r in rows),
      "attack_declarations_targeting_other_players":sum(r["brimaz"]["attacker_declarations_targeting_other_players"] for r in rows),
      "games_with_zero_incubate_trigger":sum(not r["brimaz"]["incubate_triggers_resolved"] for r in rows),
      "games_with_zero_proliferate_trigger":sum(not r["brimaz"]["endstep_proliferate_triggers_resolved"] for r in rows),
      "games_with_zero_incubator_transforms":sum(not r["brimaz"]["incubator_transforms_resolved"] for r in rows),
      "total_incubate_triggers_observed":sum(r["brimaz"]["incubate_triggers_resolved"] for r in rows),
      "total_proliferate_triggers_observed":sum(r["brimaz"]["endstep_proliferate_triggers_resolved"] for r in rows),
      "total_incubator_transforms_observed":sum(r["brimaz"]["incubator_transforms_resolved"] for r in rows),
      "confidence":"Observed Forge full move transcript only; human move-by-move comparable alternatives not supplied, so these are NOT proven tactical mistakes."
    }

def analyze(directory,output):
    directory=Path(directory)
    logs=sorted(directory.rglob("*.log"))
    if not logs:
        raise ValueError("No real Forge logs provided")
    unique={}
    for log in logs:
        row=extract(log)
        key=row["sha256"]
        if key in unique:
            raise ValueError("Duplicate original Forge transcript would double-count a game")
        unique[key]=row
    all_rows=list(unique.values())
    report={"summary":aggregate(all_rows),"games":all_rows}
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("COMMANDER_PLAY_BY_PLAY_AUDIT",json.dumps(report["summary"],ensure_ascii=False))
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    analyze(a.input,a.output)

if __name__=="__main__":main()
