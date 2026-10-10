#!/usr/bin/env python3
"""Four-seat Forge Commander action-level forensic analytics.

Reads *real raw Forge logs*, not a simplified Magic combat simulator.
Produces per-seat timelines and actionable suspect patterns, never asserts
counterfactual legal missed plays or certifies Commander rules by itself.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

SEAT = re.compile(r"Ai\((?P<seat>[1-4])\)-")
TURN = re.compile(r"^Turn: Turn (\d+) \((Ai\([1-4]\)-.*?)\)$")
PLAY = re.compile(r"^Land: (Ai\([1-4]\)-.*?) played (.+)$")
STACK = re.compile(r"^Add To Stack: (Ai\([1-4]\)-.*?) (cast|activated|triggered) (.+)$")
ATTACK = re.compile(r"^Combat: (Ai\([1-4]\)-.*?) assigned (.*?) to attack (Ai\([1-4]\)-.*?)\.$")
BLOCK = re.compile(r"^Combat: (Ai\([1-4]\)-.*?) assigned (.*?) to block (.*?)\.$")
DAMAGE = re.compile(r"^Damage: (.+?) deals (\d+) combat damage to (Ai\([1-4]\)-.*?)\.$")
POISON = re.compile(r"^Damage: (Ai\([1-4]\)-.*?) receives (\d+) poison counter")
LIFE = re.compile(r"^Life: Life: (Ai\([1-4]\)-.*?) (-?\d+) > (-?\d+)$")
SLOW = re.compile(r"^AI_EVAL_SLOW_V10: player=(Ai\([1-4]\)-.*?) globalTurn=(\d+) phase=(\S+) elapsedMs=(\d+).*")
COVER = re.compile(r"^FOUR_AI_V17_COVERAGE controller=(Ai\([1-4]\)-.*?) threatPlayers=(\d+) baselinePermille=(\d+) afterPermille=(\d+) reserved=(\d+) turn=(\d+)(?: proactive=(true|false))?")
LOSS = re.compile(r"^Game Outcome: (Ai\([1-4]\)-.*?) has lost because (.*)$")
WIN = re.compile(r"^Game Outcome: (Ai\([1-4]\)-.*?) has won because (.*)$")
CARD = re.compile(r"\((\d+)\)")
CREATURE_GONE = re.compile(r"^Zone Change: (.+?) \((\d+)\) was put into (.+?) from Battlefield\.")
BRIMAZ = re.compile(r"^BRIMAZ_WINDOW: .*?turn=(\d+).*?selfTurn=(true|false).*?candidatePhyrexianTokens=(-?\d+).*?outletCardsOnBattlefield=(\d+).*")
CHOICE = re.compile(r"^FOUR_AI_TARGET: controller=(Ai\([1-4]\)-.*?) chosen=(Ai\([1-4]\)-.*?) visibleSafeDamage=(\d+)")
TITLE = "Forge four-seat action-level diagnostic (NOT a legal-action oracle)"

def seat_of(text):
    m=SEAT.search(text)
    return int(m.group("seat")) if m else None

def base_stats(seat, deck):
    return {
        "seat":seat,"deck":deck,"turns_taken":0,"lands_played":0,
        "spells_cast":0,"abilities_activated":0,"triggers_observed":0,
        "commander_casts_observed":0,"attacks_declared":0,
        "attacking_creatures_reported":0,"combat_damage_to_players":0,
        "combat_damage_received":0,"poison_counters_received":0,
        "life_gain_net_observed":0,"life_loss_net_observed":0,
        "battlefield_permanents_lost_known_owner":0,
        "slow_ai_evaluations":0,"slowest_evaluation_ms":0,
        "decision_slow_phases":Counter(),
        "target_checks":0,"target_switches":0,"defense_checks":0,
        "defensive_reserves":0,"peak_model_risk_permille":0,
        "last_life_observed":None,"winner_in_raw_log":False,
        "loss_reason_from_raw_log":None,
    }

def inspect_game(record, log_text):
    seats=record.get("seats",[])
    if len(seats)!=4 or len(set(seats))!=4:
        raise ValueError("Four unique player deck positions required")
    stats={i:base_stats(i,seats[i-1]) for i in range(1,5)}
    timelines={i:[] for i in range(1,5)}
    current_turn=None
    attacker_card_controller={}
    battlefield_known_owner={}
    last_targets={}
    gameplay_events=0
    evidence_warnings=[]
    outcome_winners=[]
    observed_turns=0
    brimaz_window=Counter()
    incubate_transformations=0
    commander_death_count=0

    def record_event(seat,kind,detail=None):
        if seat not in stats:return
        if detail is None:detail={}
        timelines[seat].append({"global_turn":current_turn,"kind":kind,**detail})

    for line in log_text.splitlines():
        m=TURN.match(line)
        if m:
            current_turn=int(m.group(1));observed_turns+=1
            who=seat_of(m.group(2))
            if who:stats[who]["turns_taken"]+=1
            continue
        m=PLAY.match(line)
        if m:
            seat=seat_of(m.group(1))
            if seat:
                stats[seat]["lands_played"]+=1
                card_id=CARD.search(m.group(2))
                if card_id:battlefield_known_owner[card_id.group(1)]=seat
                record_event(seat,"land",{"card":m.group(2)})
            gameplay_events+=1
            continue
        m=STACK.match(line)
        if m:
            seat=seat_of(m.group(1));kind=m.group(2);name=m.group(3)
            if seat:
                attr={"cast":"spells_cast","activated":"abilities_activated",
                      "triggered":"triggers_observed"}[kind]
                stats[seat][attr]+=1
                if kind=="cast" and (name.startswith("Brimaz, Blight of Oreskos")
                                    or "cast-commander" in name):
                    stats[seat]["commander_casts_observed"]+=1
                record_event(seat,kind,{"action":name[:200]})
            if kind=="activated" and name.startswith("Incubator Token"):
                incubate_transformations+=1
            gameplay_events+=1
            continue
        m=ATTACK.match(line)
        if m:
            src=seat_of(m.group(1));dst=seat_of(m.group(3))
            cardids=CARD.findall(m.group(2))
            if src:
                stats[src]["attacks_declared"]+=1
                stats[src]["attacking_creatures_reported"]+=len(cardids)
                for cardid in cardids:attacker_card_controller[cardid]=src
                record_event(src,"attack",{"against_seat":dst,
                                            "creatures":m.group(2)[:210],
                                            "creatures_count":len(cardids)})
            gameplay_events+=1
            continue
        m=BLOCK.match(line)
        if m:
            record_event(seat_of(m.group(1)),"block",{"creatures":m.group(2)[:200]})
            gameplay_events+=1
            continue
        m=DAMAGE.match(line)
        if m:
            damage=int(m.group(2));victim=seat_of(m.group(3))
            cid=CARD.search(m.group(1))
            source=attacker_card_controller.get(cid.group(1)) if cid else None
            if victim:
                stats[victim]["combat_damage_received"]+=damage
                record_event(victim,"received_combat_damage",{"amount":damage,"source_seat":source})
            if source:
                stats[source]["combat_damage_to_players"]+=damage
            gameplay_events+=1
            continue
        m=POISON.match(line)
        if m:
            victim=seat_of(m.group(1))
            if victim:stats[victim]["poison_counters_received"]+=int(m.group(2))
            gameplay_events+=1
            continue
        m=LIFE.match(line)
        if m:
            seat=seat_of(m.group(1));old,new=int(m.group(2)),int(m.group(3))
            if seat:
                stats[seat]["last_life_observed"]=new
                stats[seat]["life_gain_net_observed"]+=max(0,new-old)
                stats[seat]["life_loss_net_observed"]+=max(0,old-new)
            continue
        m=SLOW.match(line)
        if m:
            seat=seat_of(m.group(1));duration=int(m.group(4))
            if seat:
                stats[seat]["slow_ai_evaluations"]+=1
                stats[seat]["slowest_evaluation_ms"]=max(duration,stats[seat]["slowest_evaluation_ms"])
                stats[seat]["decision_slow_phases"][m.group(3)]+=1
                record_event(seat,"slow_ai",{"phase":m.group(3),"elapsed_ms":duration})
            continue
        m=COVER.match(line)
        if m:
            seat=seat_of(m.group(1))
            if seat:
                stats[seat]["defense_checks"]+=1
                stats[seat]["defensive_reserves"]+=int(m.group(5))
                stats[seat]["peak_model_risk_permille"]=max(
                    stats[seat]["peak_model_risk_permille"],int(m.group(3)))
                if int(m.group(5))>0:
                    record_event(seat,"reserve",{"blockers":int(m.group(5)),
                      "model_risk_before":int(m.group(3)),"model_risk_after":int(m.group(4))})
            continue
        m=CHOICE.match(line)
        if m:
            src=seat_of(m.group(1));dst=seat_of(m.group(2))
            if src:
                stats[src]["target_checks"]+=1
                if src in last_targets and last_targets[src]!=dst:stats[src]["target_switches"]+=1
                last_targets[src]=dst
            continue
        m=CREATURE_GONE.match(line)
        if m:
            name,identifier,destination=m.groups()
            original_owner=battlefield_known_owner.get(identifier)
            if original_owner is not None:
                stats[original_owner]["battlefield_permanents_lost_known_owner"]+=1
            # Brimaz's commander is unambiguous by name even when the card
            # wasn't logged as a cast (summoned by other means).
            if name=="Brimaz, Blight of Oreskos":commander_death_count+=1
            continue
        m=BRIMAZ.match(line)
        if m:
            brimaz_window["windows"]+=1
            if m.group(2)=="true":brimaz_window["self_turn_windows"]+=1
            if int(m.group(3))>0:brimaz_window["windows_with_phyrexian_tokens"]+=1
            if int(m.group(4))>0:brimaz_window["windows_with_outlet"]+=1
            continue
        m=WIN.match(line)
        if m:
            seat=seat_of(m.group(1));outcome_winners.append(seat)
            if seat:stats[seat]["winner_in_raw_log"]=True
            continue
        m=LOSS.match(line)
        if m:
            seat=seat_of(m.group(1))
            if seat:stats[seat]["loss_reason_from_raw_log"]=m.group(2)
            continue

    if observed_turns==0:evidence_warnings.append("No Forge Turn events")
    if record.get("status")=="complete" and outcome_winners!=[record.get("winner_seat")]:
        evidence_warnings.append("Game manifest winner differs from raw outcome")
    if record.get("status")!="complete":
        evidence_warnings.append("No natural finished-game claim: "+str(record.get("status")))
    if "Exception in thread" in log_text or "java.lang.NullPointerException" in log_text:
        evidence_warnings.append("Fatal Forge error present")
    for st in stats.values():
        st["decision_slow_phases"]=dict(st["decision_slow_phases"])
    return {
        "identity":{
            "pod":record.get("pod"),"rotation":record.get("rotation"),
            "seed":record.get("seed"),"policy":record.get("policy"),
            "status":record.get("status"),"winner_seat":record.get("winner_seat"),
            "observed_turn_events":observed_turns,"observed_game_events":gameplay_events,
            "raw_log_sha256":hashlib.sha256(log_text.encode("utf-8")).hexdigest(),
            "wall_seconds":record.get("wall_seconds"),
        },
        "players":[stats[i] for i in range(1,5)],
        "brimaz":dict(brimaz_window,commander_battlefield_exits=commander_death_count,
                      observed_incubator_transformations=incubate_transformations),
        "timelines":{str(i):timelines[i] for i in range(1,5)},
        "warnings":evidence_warnings,
        "certification":"UNVERIFIED. These are real logged actions, not oracle-legal alternatives.",
    }

def aggregate(records):
    seats=defaultdict(lambda:defaultdict(int))
    statuses=Counter()
    for g in records:
        statuses[g["identity"]["status"]]+=1
        for player in g["players"]:
            deck=player["deck"];dst=seats[deck]
            dst["participations"]+=1
            for k in ("spells_cast","lands_played","triggers_observed",
                      "attacks_declared","combat_damage_to_players",
                      "combat_damage_received","slow_ai_evaluations",
                      "defense_checks","defensive_reserves","target_checks",
                      "target_switches","commander_casts_observed"):
                dst[k]+=player[k]
            if player["winner_in_raw_log"] and g["identity"]["status"]=="complete":
                dst["observed_natural_wins_not_certified"]+=1
    return {"game_count":len(records),"status_counts":dict(statuses),
            "by_deck":{k:dict(v) for k,v in sorted(seats.items())}}

def render_markdown(report):
    text=[f"# {TITLE}","","## Scope",
          f"- Real game logs: {report['summary']['game_count']}",
          f"- Statuses: {report['summary']['status_counts']}",
          "- These statistics only describe actions Forge logged. No missed legal play, fair winrate, or superiority is inferred.",
          "","## Aggregate per deck","",
          "| Deck | Games | Casts | Lands | Attacks | Combat dmg dealt | Combat dmg received | Slow evaluations |",
          "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name,d in report["summary"]["by_deck"].items():
        text.append(f"| {name.replace('|','/')} | {d['participations']} | {d['spells_cast']} | "
                    f"{d['lands_played']} | {d['attacks_declared']} | "
                    f"{d['combat_damage_to_players']} | {d['combat_damage_received']} | "
                    f"{d['slow_ai_evaluations']} |")
    text.extend(["","## Game-level observations",""])
    for game in report["games"]:
        i=game["identity"]
        text.append(f"### {i['pod']} · rotation {i['rotation']} · seed {i['seed']} · {i['policy']}")
        text.append(f"Result: {i['status']}; winner seat {i['winner_seat']}; "
                    f"{i['observed_turn_events']} global turns; {i['wall_seconds']} s.")
        for player in game["players"]:
            if player["deck"]=="Brimaz_V3":
                text.append(f"Brimaz: casts {player['spells_cast']}, lands {player['lands_played']}, "
                            f"attacks {player['attacks_declared']}, combat damage "
                            f"{player['combat_damage_to_players']}, slow decisions "
                            f"{player['slow_ai_evaluations']}, commander casts "
                            f"{player['commander_casts_observed']}; commander exits "
                            f"{game['brimaz']['commander_battlefield_exits']}; "
                            f"incubator transforms {game['brimaz']['observed_incubator_transformations']}.")
        for warning in game["warnings"]:text.append(f"Warning: {warning}")
    return "\n".join(text)+"\n"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    files=sorted(args.input.rglob("games.json"))
    if not files:raise SystemExit("No actual Forge games.json files found")
    games=[]
    for manifest in files:
        for record in json.loads(manifest.read_text(encoding="utf-8")):
            log=manifest.parent/Path(record["log"]).name
            if not log.is_file():raise ValueError("Missing real game log "+str(log))
            games.append(inspect_game(record,log.read_text(encoding="utf-8",errors="replace")))
    report={"type":TITLE,"summary":aggregate(games),"games":games}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"four_seat_actions.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (args.output/"four_seat_summary.md").write_text(render_markdown(report),encoding="utf-8")
    print("FOUR_SEAT_FORENSICS",json.dumps(report["summary"],ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
