#!/usr/bin/env python3
"""Import public Archidekt Commander lists with strict count and commander checks.

Store exact source JSON snapshots for later audit. No fabricated replacements.
"""
import argparse
import collections
import json
import pathlib
import sys
import urllib.request

PANEL = [
    ("Krenko_B3", 10174296, "Krenko, Mob Boss"),
    ("Muldrotha_B3", 3732210, "Muldrotha, the Gravetide"),
    # Yuriko source 5411992 is excluded: archived deck validates to only 96 cards.
]
options=argparse.ArgumentParser()
options.add_argument("--offline", action="store_true", help="Use previously archived JSON snapshots only")
args=options.parse_args()
OUT = pathlib.Path("forge_decks")
RAW = pathlib.Path("results/archidekt_snapshots")
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

def fetch_deck(deck_id):
    url = "https://archidekt.com/api/decks/%d/" % deck_id
    request = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; BrimazForgeLab/1.0; deck validation)"
    })
    with urllib.request.urlopen(request, timeout=50) as resp:
        data = json.load(resp)
    return data

def get_name(entry):
    card = entry.get("card") or {}
    oracle = card.get("oracleCard") or card.get("oracle_card") or {}
    return oracle.get("name") or card.get("displayName") or card.get("name") or ""

def parse_deck(data):
    # Archidekt categories have name, id, and includedInDeck.
    cats = data.get("categories", [])
    cat_by_id = {str(c.get("id")): c for c in cats if isinstance(c, dict)}
    cat_by_name = {c.get("name"): c for c in cats if isinstance(c, dict)}
    counts = collections.Counter()
    excluded = []
    debug_categories = collections.Counter()
    debug_samples = {}
    for entry in data.get("cards", []):
        category_objs = []
        for category in entry.get("categories") or []:
            if isinstance(category, dict):
                category_objs.append(category)
            elif str(category) in cat_by_id:
                category_objs.append(cat_by_id[str(category)])
            elif str(category) in cat_by_name:
                category_objs.append(cat_by_name[str(category)])
            else:
                category_objs.append({"name": str(category)})
        if category_objs:
            # Exclude only sections that belong outside the 100-card deck.
            # Any ambiguous category not marked excluded is treated as playable,
            # and total_count validation prevents silent misuse.
            names = {str(c.get("name", "")).lower() for c in category_objs}
            if names and names <= {"sideboard", "maybeboard", "considering", "acquireboard"}:
                excluded.append({"name":get_name(entry), "categories":sorted(names), "primary":entry.get("category")})
                continue
            if any(c.get("includedInDeck") is False for c in category_objs):
                excluded.append({"name":get_name(entry), "categories":sorted(names), "primary":entry.get("category")})
                continue
        name = get_name(entry)
        qty = int(entry.get("quantity", entry.get("qty", 1)))
        if not name or qty < 1:
            raise ValueError("Bad card: " + repr(entry)[:200])
        counts[name] += qty
        key = ", ".join(sorted(str(x.get("name")) for x in category_objs))
        debug_categories[key] += qty
        debug_samples.setdefault(key, []).append(name)
    print("EXCLUDED CARDS", data.get("name"), json.dumps(excluded, ensure_ascii=False), flush=True)
    print("CATEGORY BREAKDOWN", data.get("name"), json.dumps({
        "by_category": dict(debug_categories),
        "sample_names": {k: v[:4] for k, v in debug_samples.items()},
        "category_definitions": cats,
    }, ensure_ascii=False), flush=True)
    return counts

def make_dck(label, commander, counts):
    total = sum(counts.values())
    if total != 100:
        raise ValueError(f"{label}: expected 100 cards, found {total}")
    if counts[commander] != 1:
        raise ValueError(f"{label}: commander {commander!r} found {counts[commander]} times")
    others = sorted((name, qty) for name, qty in counts.items() if name != commander)
    basic = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes", "Snow-Covered Plains",
             "Snow-Covered Island", "Snow-Covered Swamp", "Snow-Covered Mountain", "Snow-Covered Forest"}
    duplicates = [(n,q) for n,q in others if q > 1 and n not in basic]
    if duplicates:
        raise ValueError(f"{label}: nonbasic duplicates: {duplicates}")
    txt = "[metadata]\nName=" + label + "\n[Main]\n" + "".join(f"{q} {n}\n" for n,q in others)
    txt += "[Commander]\n1 " + commander + "\n"
    (OUT / (label + ".dck")).write_text(txt, encoding="utf-8")
    return {"deck": label,"commander":commander,"cards":total,"distinct":len(counts)}

reports=[]
for label, deck_id, commander in PANEL:
    try:
        snapshot = RAW / f"{deck_id}.json"
        if snapshot.exists():
            raw = json.loads(snapshot.read_text(encoding="utf-8"))
            print("REUSED SNAPSHOT", snapshot, flush=True)
        elif args.offline:
            raise FileNotFoundError(str(snapshot))
        else:
            raw = fetch_deck(deck_id)
            snapshot.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        summary = make_dck(label, commander, parse_deck(raw))
        summary["source"] = f"https://archidekt.com/decks/{deck_id}"
        reports.append(summary)
        print("IMPORTED", json.dumps(summary, ensure_ascii=False), flush=True)
    except Exception as e:
        reports.append({"deck":label,"error":str(e),"source":f"https://archidekt.com/decks/{deck_id}"})
        print("IMPORT FAILED",label,repr(e),flush=True)
pathlib.Path("results/panel.json").write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")
if any("error" in r for r in reports):
    sys.exit(1)
