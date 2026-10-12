#!/usr/bin/env python3
"""Enumerate EVERY Commander-legal Orzhov/colorless Oracle card from Scryfall.

Discovery instrument, not an AI deck builder and not a power/win-rate proof.
Requires network at RUN TIME. Uses the current Scryfall bulk catalogue to
avoid paging/search ranking truncation. Outputs deterministic scored candidates,
always with role classifications and provenance.
"""
import argparse
import collections
import csv
import gzip
import json
import pathlib
import re
import urllib.request

SOURCE = "https://api.scryfall.com/bulk-data/oracle-cards"
USER_AGENT = "BrimazForgeLab/1.0 (noncommercial complete Commander pool research)"
COLORS = {"W", "B"}
EXCLUDE_THEMES = re.compile(r"\b(?:infect|toxic|poison counter|poisoned|poisonous)\b", re.I)
GENERIC_POWER = {
    "Esper Sentinel", "Smothering Tithe", "Demonic Tutor",
    "Vampiric Tutor", "Rhystic Study", "Necropotence",
    "The One Ring", "Mana Vault", "Ancient Tomb",
    "Urza's Saga", "Diabolic Intent", "The Meathook Massacre",
    "Phyrexian Altar", "Teferi's Protection",
    "Bolas's Citadel", "Drannith Magistrate", "Farewell",
}
PATTERNS = {
    "incubate": r"\bincubate\b|\bincubator\b",
    "proliferate": r"\bproliferate\b",
    "counter_synergy": r"\+1/\+1 counter|move.*counter|counter.*another|counters.*permanent",
    "board_buff": r"creatures you control get \+|phyrexians you control get|\+1/\+1 counter on each|creatures you control gain (?:flying|vigilance|trample|double strike)",
    "combat_evasion": r"\bflying\b|\bmenace\b|\btrample\b|\bdouble strike\b|can't be blocked",
    "single_removal": r"(?:destroy|exile) target (?:nonland |nontoken |nonartifact |nonblack |artifact|enchantment|creature|permanent|planeswalker)|target.*gets -[0-9]+/-[0-9]+",
    "boardwipe": r"destroy all|exile all creatures|all creatures get -[0-9]+/-[0-9]+|destroy each",
    "defense": r"\bhexproof\b|\bindestructible\b|phase out|gain protection from|cannot be destroyed",
    "card_advantage": r"draw (?:a|one|two|three|x) card|draw cards|whenever.*draw a card|return target creature card from your graveyard to your hand",
    "ramp": r"add \{[WBC]\}|add one mana|search your library for (?:a|up to two) basic land|add an amount of",
}
RE = {k: re.compile(v, re.I) for k, v in PATTERNS.items()}

def oracle_text(card):
    return "\n".join([card.get("oracle_text", "")] +
        [f.get("oracle_text", "") for f in card.get("card_faces", [])])

def eligible(card):
    if card.get("legalities", {}).get("commander") != "legal":
        return False
    if not set(card.get("color_identity", [])) <= COLORS:
        return False
    if card.get("game_changer") is True:
        return False
    if card.get("layout") in ("token", "emblem", "art_series", "scheme", "plane", "vanguard"):
        return False
    return True

def classify(card):
    name = card.get("name", "")
    txt = oracle_text(card)
    types = " ".join([card.get("type_line", "")] +
         [f.get("type_line", "") for f in card.get("card_faces", [])])
    is_creature = "Creature" in types
    is_phyrexian = bool(re.search(r"\bPhyrexian\b", types, re.I) or
                        re.search(r"\bchangeling\b", txt, re.I))
    is_artifact_creature = "Artifact Creature" in types
    mana = float(card.get("cmc", 0))
    roles = [tag for tag, exp in RE.items() if exp.search(txt)]
    if is_phyrexian or is_artifact_creature:
        roles.append("brimaz_cast")
    if not roles:
        return None
    score = sum({
        "brimaz_cast": 7, "incubate": 8, "proliferate": 8,
        "counter_synergy": 3, "board_buff": 6, "combat_evasion": 2,
        "single_removal": 6, "boardwipe": 7, "defense": 6,
        "card_advantage": 4, "ramp": 4,
    }.get(role, 0) for role in roles)
    if is_creature and (is_phyrexian or is_artifact_creature) and mana <= 3:
        score += 5
    if "incubate" in roles and "single_removal" in roles: score += 9
    if "incubate" in roles and "board_buff" in roles: score += 8
    if "proliferate" in roles and "counter_synergy" in roles: score += 4
    if "defense" in roles and "board_buff" in roles: score += 3
    if EXCLUDE_THEMES.search(txt) or EXCLUDE_THEMES.search(name): score -= 16
    if name in GENERIC_POWER: score -= 25
    if mana >= 7: score -= 6
    elif mana >= 5: score -= 2
    price = card.get("prices") or {}
    # Oracle bulk prices are often absent; never use 0/null to claim cheap.
    eur = price.get("eur")
    return {
        "name": name, "score": score, "mana_value": mana,
        "type_line": card.get("type_line", ""),
        "roles": roles, "color_identity": sorted(card.get("color_identity", [])),
        "game_changer": card.get("game_changer", False),
        "eur_if_present": eur,
        "generic_flag": name in GENERIC_POWER,
        "poison_or_infect_text": bool(EXCLUDE_THEMES.search(txt)),
        "oracle": txt[:1800],
        "oracle_id": card.get("oracle_id", ""),
        "scryfall_uri": card.get("scryfall_uri", ""),
    }

def fetch_metadata():
    req = urllib.request.Request(SOURCE, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=70) as response:
        return json.load(response)

def all_oracle_cards(meta):
    address = meta.get("jsonl_download_uri") or meta.get("download_uri")
    if not address:
        raise RuntimeError("Scryfall bulk oracle_cards has no recognized download URI")
    req = urllib.request.Request(address, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=180) as response:
        if ".jsonl" in address:
            stream = gzip.GzipFile(fileobj=response) if address.endswith(".gz") else response
            for line in stream:
                if line.strip():
                    yield json.loads(line)
        else:
            # Legacy JSON array: bounded by Oracle-card dataset, not all prints.
            stream = gzip.GzipFile(fileobj=response) if address.endswith(".gz") else response
            for card in json.load(stream):
                yield card

def evaluate(cards, bulk_info, limit=80):
    stats = collections.Counter()
    by_role = collections.defaultdict(list)
    others = []
    full_eligible_index = []
    seen = set()
    for card in cards:
        stats["oracle_records"] += 1
        if not eligible(card):
            continue
        key = card.get("oracle_id") or card.get("name")
        if key in seen: continue
        seen.add(key)
        stats["eligible_WB_colorless_no_game_changer"] += 1
        row = classify(card)
        full_eligible_index.append({
            "name": card.get("name",""), "oracle_id": card.get("oracle_id",""),
            "mana_value": float(card.get("cmc",0)),
            "type": card.get("type_line",""),
            "roles": row["roles"] if row else [],
            "candidate_score": row["score"] if row else 0,
            "scryfall_uri": card.get("scryfall_uri",""),
        })
        if row is None: continue
        stats["classified_with_relevant_text_or_type"] += 1
        others.append(row)
        for role in row["roles"]:
            by_role[role].append(row)
    sortby = lambda x: (-x["score"], x["mana_value"], x["name"])
    def compact(x):
        return {
            "name": x["name"], "score": x["score"],
            "mv": x["mana_value"], "roles": x["roles"],
            "eur": x["eur_if_present"], "oracle": x["oracle"],
            "url": x["scryfall_uri"],
        }
    return {
        "data_source": SOURCE,
        "bulk_updated_at": bulk_info.get("updated_at"),
        "format": "oracle_cards, one canonical record per Oracle card",
        "filters": {"commander_legal": True, "color_identity_subset": ["W","B"],
                    "game_changer": False},
        "exclusions": {"poison/infect": "scoring penalty, NOT silently removed",
                       "generic_auto_includes": sorted(GENERIC_POWER)},
        "counts": dict(stats),
        "eligible_index": sorted(full_eligible_index,key=lambda x:x["name"]),
        "roles": {k: {"count": len(v), "top": [compact(x) for x in sorted(v,key=sortby)[:limit]]}
                  for k, v in sorted(by_role.items())},
        "overall_top": [compact(x) for x in sorted(others,key=sortby)[:limit]],
        "warning": "Heuristic candidate discovery only, NOT an optimal deck solver, cost validation, rules engine or winrate.",
    }

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results/oracle-pool"))
    a.add_argument("--top", type=int, default=60)
    args = a.parse_args()
    if not 10 <= args.top <= 300: raise ValueError("top outside bounds")
    meta = fetch_metadata()
    report = evaluate(all_oracle_cards(meta), meta, args.top)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "orzhov-legal-full-pool.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    with (args.out / "orzhov-legal-shortlist.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["role","name","heuristic_score","mana_value","eur_if_present","oracle","scryfall_uri"])
        for role,v in report["roles"].items():
            for row in v["top"]:
                writer.writerow([role,row["name"],row["score"],row["mv"],row["eur"],
                                 row["oracle"],row["url"]])
    with (args.out / "all-eligible-WB-colorless-index.csv").open("w",newline="",encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name","oracle_id","mana_value","type","roles","candidate_score","scryfall_uri"])
        for row in report["eligible_index"]:
            writer.writerow([row["name"],row["oracle_id"],row["mana_value"],
                             row["type"],";".join(row["roles"]),
                             row["candidate_score"],row["scryfall_uri"]])
    print("FULL_ORACLE_POOL_COUNTS", json.dumps(report["counts"],ensure_ascii=False))
    for role,item in report["roles"].items():
        print("FULL_ORACLE_POOL_ROLE",json.dumps({"role":role,"total":item["count"],
              "top": [{"name":c["name"],"score":c["score"]}
                      for c in item["top"][:12]]},ensure_ascii=False))
    print("FULL_ORACLE_POOL_RESEARCH_ONLY", "No Magic matches or evidence of optimality")

if __name__ == "__main__": main()
