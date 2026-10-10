#!/usr/bin/env python3
"""Audit ACTUAL official Forge 2.0.15 card AI exclusion tags for a 100-card deck.

AI:RemoveDeck:All means Forge normally excludes card plays/abilities from the
AI. The Brimaz V13 planner has a narrowly scoped, state-dependent override for
a few cards. Do not call partially whitelisted cards 'fully supported' or make
claims about any card whose official Forge definition could not be resolved.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import unicodedata
from urllib.error import HTTPError,URLError
from urllib.request import urlopen

FORGE_TAG="forge-2.0.15"
PIN_BASE=f"https://raw.githubusercontent.com/Card-Forge/forge/{FORGE_TAG}/forge-gui/res/cardsfolder/"
OVERRIDES={
 "Orzhov Signet":"cast-only: AI mana/cost checks still apply",
 "Spawning Pit":"restricted cast and conditional sacrifice; token creation not guaranteed",
 "Krark-Clan Ironworks":"conditional cast and 1-for-1 token sacrifice; mana routing not proven",
 "Throne of Geth":"conditional sacrifice only; not fully supported",
}
KNOWN_UNWHITELISTED={"Diabolic Intent","Phyrexian Reclamation","Phyrexian Delver"}

def slug(name):
    if " // " in name:name=name.split(" // ",1)[0]
    unaccent=unicodedata.normalize("NFKD",name)
    text="".join(x for x in unaccent if not unicodedata.combining(x))
    text=re.sub(r"[^a-z0-9]+","_",text.lower()).strip("_")
    if not text or not text[0].isalpha():
        raise ValueError("Unresolvable card name")
    return text[0]+"/"+text+".txt"

def parse_deck(path):
    result=Counter()
    for row in Path(path).read_text(encoding="utf-8").splitlines():
        row=row.strip()
        if not row or row.startswith("#"):continue
        m=re.fullmatch(r"(\d+)\s+(.+)",row)
        if not m:raise ValueError("Unrecognized decklist row "+row)
        result[m[2]]+=int(m[1])
    if sum(result.values())!=100:
        raise ValueError("Exactly 100 physical Commander cards required")
    return result

def classify(name,body):
    expected=slug(name)
    if not body:
        return {"name":name,"source":expected,"status":"unresolved","uncertainty":"No official pinned Forge card definition verified"}
    removed=any(re.fullmatch(r"AI:RemoveDeck:(All|Default|Experimental)",l.strip(),re.I)
                for l in body.splitlines())
    all_blocked=bool(re.search(r"(?m)^AI:RemoveDeck:All\s*$",body))
    if all_blocked and name in OVERRIDES:
        status="narrow_policy_override"
    elif all_blocked:
        status="ai_hard_exclusion"
    elif removed:
        status="other_ai_exclusion"
    else:
        status="no_hard_exclusion_tag"
    return {"name":name,"source":expected,"status":status,
            "remove_deck_all":all_blocked,
            "override":OVERRIDES.get(name) if all_blocked else None,
            "disclaimer":"Not excluded by an explicit All tag does not prove correct target selection, spell timing or opponent tactics"}

def load_card(name,timeout=15):
    path=slug(name)
    url=PIN_BASE+path
    try:
        with urlopen(url,timeout=timeout) as f:
            text=f.read().decode("utf-8")
        first=next((line.split(":",1)[1].strip() for line in text.splitlines()
                    if line.startswith("Name:")),"")
        # Some filenames normalize differently: never silently claim another
        # card's AI tag as evidence about the user's deck card.
        if first not in (name,name.split(" // ",1)[0]):
            return name,None,"name mismatch from pinned Forge"
        return name,text,None
    except (HTTPError,URLError,TimeoutError,ValueError) as e:
        return name,None,str(e)[:110]

def inspect(deck,fetch=load_card,max_workers=8):
    counts=parse_deck(deck)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        looked=list(pool.map(fetch,counts))
    results=[]
    for name,content,error in looked:
        r=classify(name,content)
        r["count"]=counts[name]
        if error:r["retrieval_error"]=error
        results.append(r)
    excluded=[x for x in results if x["status"]=="ai_hard_exclusion"]
    narrow=[x for x in results if x["status"]=="narrow_policy_override"]
    unresolved=[x for x in results if x["status"]=="unresolved"]
    return {
      "official_forge_tag":FORGE_TAG,
      "summary":{
         "physical_cards":sum(counts.values()),
         "unique_card_definitions_requested":len(counts),
         "ai_hard_exclusion_cards":sum(x["count"] for x in excluded),
         "narrow_conditional_override_cards":sum(x["count"] for x in narrow),
         "unresolved_cards":sum(x["count"] for x in unresolved),
         "hard_excluded_names":[x["name"] for x in excluded],
         "conditional_override_names":[x["name"] for x in narrow],
         "warning":"AI:RemoveDeck:All is a concrete AI restriction. Conditional Brimaz overrides are not generic card support. Missing source is UNKNOWN, never compatible. Other unsupported abilities can exist without any exclusion tag."
      },
      "cards":results
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--deck",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    report=inspect(args.deck)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("FORGE_PINNED_CARD_AI_SUPPORT_AUDIT",json.dumps(report["summary"],ensure_ascii=False))
    for name in sorted(KNOWN_UNWHITELISTED):
        hits=[x for x in report["cards"] if x["name"]==name]
        if hits and hits[0]["status"]!="ai_hard_exclusion":
            raise RuntimeError("Official Forge unexpectedly stopped excluding "+name+"; investigate source/heuristics before interpreting results.")

if __name__=="__main__":main()
