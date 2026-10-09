#!/usr/bin/env python3
"""Snapshot and validate selected PUBLIC Archidekt decks belonging to KaalDeagle.
Do not invent cards to repair incomplete lists. Nondeck categories are excluded.
"""
import argparse
import collections
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

p=argparse.ArgumentParser()
p.add_argument("--limit", type=int, default=8)
p.add_argument("--catalog", default="results/playgroup/catalog.json")
p.add_argument("--pause", type=float, default=0.8)
args=p.parse_args()
DATA=pathlib.Path("results/playgroup")
DATA.mkdir(parents=True,exist_ok=True)
OUTPUT=pathlib.Path("forge_decks")
OUTPUT.mkdir(parents=True,exist_ok=True)
CATALOG=json.loads(pathlib.Path(args.catalog).read_text(encoding="utf-8"))
DECKS=CATALOG["decks"]
PREFERRED_IDS=[9594008,10347090,21930525,23328062,11485202,20861410,22106142,22193355,15398527,14798701,12231310]
by_id={int(d["id"]):d for d in DECKS}
chosen=[by_id[i] for i in PREFERRED_IDS if i in by_id and by_id[i].get("size")==100]
if args.limit:
    chosen=chosen[:args.limit]
BASICS={"Plains","Island","Swamp","Mountain","Forest","Wastes",
"Snow-Covered Plains","Snow-Covered Island","Snow-Covered Swamp",
"Snow-Covered Mountain","Snow-Covered Forest"}
MULTI_ALLOWED={"Dragon's Approach","Shadowborn Apostle","Relentless Rats",
"Persistent Petitioners","Rat Colony","Slime Against Humanity","Hare Apparent",
"Seven Dwarves","Nazgûl"}
def get_json(url):
    req=urllib.request.Request(url,headers={
        "Accept":"application/json",
        "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
        "Referer":"https://archidekt.com/u/KaalDeagle",
    })
    with urllib.request.urlopen(req,timeout=45) as res:
        return json.load(res)
def get_name(entry):
    card=entry.get("card") or {}
    oracle=card.get("oracleCard") or card.get("oracle_card") or {}
    return oracle.get("name") or card.get("displayName") or card.get("name")
def export_one(meta,raw):
    cats=raw.get("categories") or []
    idmap={str(c.get("id")):c for c in cats if isinstance(c,dict)}
    namemap={c.get("name"):c for c in cats if isinstance(c,dict)}
    cards=collections.Counter()
    commanders=collections.Counter()
    excluded=[]
    for entry in raw.get("cards") or []:
        names=[]
        defined=[]
        for c in entry.get("categories") or []:
            d=c if isinstance(c,dict) else idmap.get(str(c),namemap.get(c,{"name":str(c)}))
            defined.append(d)
            names.append(str(d.get("name","")).lower())
        name=get_name(entry)
        qty=int(entry.get("quantity") or 1)
        if not name or qty<1:
            raise ValueError("Missing name or invalid quantity in card: "+str(entry)[:100])
        if (any(c.get("includedInDeck") is False for c in defined)
            or any(n in {"maybeboard","consider","considering","sideboard","acquireboard"} for n in names)):
            excluded.append({"name":name,"categories":names})
            continue
        cards[name]+=qty
        if "commander" in names: commanders[name]+=qty
    total=sum(cards.values())
    if total!=100:
        raise ValueError(f"Deck has {total} included cards, expected 100 (excluded {len(excluded)})")
    if not commanders or sum(commanders.values()) not in (1,2):
        raise ValueError("No unambiguous commander(s): "+repr(dict(commanders)))
    illegal_dup=[(n,q) for n,q in cards.items() if q>1 and n not in BASICS and n not in MULTI_ALLOWED]
    if illegal_dup:
        raise ValueError("Duplicate nonbasic names: "+repr(illegal_dup))
    name="Kaal_"+str(meta["id"])
    lines=["[metadata]","Name="+meta["name"],"[Main]"]
    for card,qty in sorted(cards.items()):
        if card not in commanders: lines.append(f"{qty} {card}")
    lines.append("[Commander]")
    for card,qty in sorted(commanders.items()): lines.append(f"{qty} {card}")
    (OUTPUT/(name+".dck")).write_text("\n".join(lines)+"\n",encoding="utf-8")
    return {
        "id":meta["id"],"name":meta["name"],"forge_deck":name,
        "source":f'https://archidekt.com/decks/{meta["id"]}',
        "commander":list(commanders),"count":total,
        "distinct":len(cards),"archidekt_bracket":meta.get("edhBracket"),
        "archidekt_size":meta.get("size"),
        "excluded_entries":len(excluded),"status":"validated_structure"
    }
report=[]
for index,meta in enumerate(chosen):
    if index: time.sleep(args.pause)
    id=meta["id"]
    archive=DATA/f"cards-{id}.json"
    try:
        if archive.exists(): raw=json.loads(archive.read_text(encoding="utf-8"))
        else:
            raw=get_json(f"https://archidekt.com/api/decks/{id}/")
            archive.write_text(json.dumps(raw,ensure_ascii=False),encoding="utf-8")
        result=export_one(meta,raw)
        print("IMPORTED",json.dumps(result,ensure_ascii=False),flush=True)
        report.append(result)
    except Exception as e:
        failure={"id":id,"name":meta["name"],"status":"rejected","error":str(e),"source":f"https://archidekt.com/decks/{id}"}
        print("REJECTED",json.dumps(failure,ensure_ascii=False),flush=True)
        report.append(failure)
(DATA/"import-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("SUMMARY",sum(x["status"]=="validated_structure" for x in report),"validated of",len(report))
# Partial valid lists are preserved as build artifacts to permit continuation.
sys.exit(0 if any(x["status"]=="validated_structure" for x in report) else 2)
