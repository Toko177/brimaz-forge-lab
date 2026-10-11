#!/usr/bin/env python3
"""Evidence-limited measurement of Brimaz's ACTUAL attacks and combat damage.

Attribution only when a source card ID was explicitly declared attacking by
Brimaz in the SAME numbered Forge player turn. A player's natural victory
never proves they directly killed every opponent.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

TURN = re.compile(r"^Turn: Turn (\d+) \(Ai\((\d+)\)-")
DECLARE = re.compile(r"^Combat: Ai\((\d+)\)-.*? assigned (.*?) to attack Ai\((\d+)\)-")
ATTACK_CARD = re.compile(r"([A-Za-z][^,(]*?(?:, [^()]*?)?) \((\d+)\)")
DAMAGE = re.compile(r"^Damage: (.*?) \((\d+)\) deals (\d+) combat damage to Ai\((\d+)\)-")
PHYREXIAN = re.compile(r"\bPhyrexian\b", re.I)


def inspect(raw, game):
    seat = game["brimaz_seat"]
    opponents = set(range(1,5))-{seat}
    turn_no = None
    attacks_by_card = {}
    attacked_opponents = Counter()
    damage_by_opponent = Counter()
    attack_declarations = 0
    phyrexian_attack_declarations = 0
    assigned_attacker_ids = set()
    matched_damages = 0
    for line in raw.splitlines():
        m = TURN.match(line)
        if m:
            turn_no = int(m[1])
            attacks_by_card.clear()
            continue
        m = DECLARE.match(line)
        if m and int(m[1]) == seat and int(m[3]) in opponents:
            target = int(m[3])
            attack_declarations += 1
            attacked_opponents[target] += 1
            # The joined attacker list can include commas in creature names.
            # Record card IDs only; duplicate tokens are individual attackers.
            tokens = [(n,int(card_id)) for n,card_id in ATTACK_CARD.findall(m[2])]
            for n,card_id in tokens:
                attacks_by_card[card_id] = target
                assigned_attacker_ids.add(card_id)
                if PHYREXIAN.search(n):
                    phyrexian_attack_declarations += 1
            continue
        m = DAMAGE.match(line)
        if m and int(m[2]) in attacks_by_card:
            source_id = int(m[2])
            target = int(m[4])
            if target == attacks_by_card[source_id]:
                damage_by_opponent[target] += int(m[3])
                matched_damages += 1
    return {
        "pod":game["pod"],"seed":game["seed"],"rotation":game["rotation"],
        "policy":game["policy"],"status":game["status"],
        "winner_deck":game.get("winner_deck"),
        "brimaz_natural_win":game["status"]=="complete" and game.get("brimaz_win") is True,
        "brimaz_attack_declarations":attack_declarations,
        "identified_unique_attackers":len(assigned_attacker_ids),
        "identified_phyrexian_attackers":phyrexian_attack_declarations,
        "attacked_opponent_seats":dict(attacked_opponents),
        "damage_by_brimaz_declared_attackers_to_opponents":dict(damage_by_opponent),
        "damage_total_attributable_to_declared_attackers":sum(damage_by_opponent.values()),
        "matched_combat_damage_events":matched_damages,
        "reported_last_global_turn":turn_no,
        "limitation":"Only same-turn source IDs and combat damage to their explicitly attacked defender are counted. Not a full life-loss causal trace; direct spells, triggers, opponent actions and unlisted attacks are excluded."
    }


def audit(root):
    games=[]
    for manifest in sorted(root.rglob("games.json")):
        for g in json.loads(manifest.read_text(encoding="utf-8")):
            log=manifest.parent/Path(g["log"]).name
            if not log.exists():
                raise FileNotFoundError(log)
            games.append(inspect(log.read_text(encoding="utf-8",errors="replace"),g))
    if not games:
        raise ValueError("No real Forge logs")
    return {"summary":{
        "games":len(games),
        "brimaz_natural_wins_as_manifest_not_independent_certificates":sum(g["brimaz_natural_win"] for g in games),
        "observed_brimaz_attack_declarations":sum(g["brimaz_attack_declarations"] for g in games),
        "declared_phyrexian_attacker_tokens":sum(g["identified_phyrexian_attackers"] for g in games),
        "matched_brimaz_combat_damage":sum(g["damage_total_attributable_to_declared_attackers"] for g in games),
        "never_claims_three_opponent_kills_from_one_winner_record":True
    }, "games":games}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    r=audit(a.input)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("BRIMAZ_REAL_COMBAT_EVIDENCE",json.dumps(r["summary"],ensure_ascii=False))


if __name__=="__main__":
    main()
