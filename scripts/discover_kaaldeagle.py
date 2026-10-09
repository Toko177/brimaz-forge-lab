#!/usr/bin/env python3
"""Discover PUBLIC Archidekt decks belonging to the named playgroup account.
The source API is unofficial. Save a reproducible JSON catalog, not credentials.
"""
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
import datetime
import sys

OWNER = "KaalDeagle"
ROOT = pathlib.Path("results/playgroup")
ROOT.mkdir(parents=True, exist_ok=True)
def request_json(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
        "Referer": "https://archidekt.com/u/KaalDeagle",
    })
    with urllib.request.urlopen(req, timeout=45) as res:
        return json.load(res)

catalog=[]
errors=[]
next_url="https://archidekt.com/api/decks/v3/?" + urllib.parse.urlencode({
    "ownerUsername": OWNER, "deckFormat": 3, "pageSize": 100, "orderBy": "-updatedAt"
})
page=0
while next_url and page < 10:
    page+=1
    try:
        data=request_json(next_url)
    except Exception as e:
        errors.append({"page":page,"error":str(e),"url":next_url})
        print("FETCH FAILED",str(e),flush=True)
        break
    (ROOT/f"index-page-{page}.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    rows=data.get("results",[]) if isinstance(data,dict) else []
    print("PAGE",page,"results",len(rows),flush=True)
    for r in rows:
        if not isinstance(r,dict): continue
        owner=r.get("owner") or {}
        owner_name=owner.get("username") if isinstance(owner,dict) else None
        deck={
            "id":r.get("id"),"name":r.get("name"),"size":r.get("size"),
            "edhBracket":r.get("edhBracket"),"deckFormat":r.get("deckFormat"),
            "owner":owner_name, "updatedAt":r.get("updatedAt"),
            "privateDeck":r.get("privateDeck"),"unlisted":r.get("unlisted")
        }
        if owner_name and owner_name.casefold()!=OWNER.casefold():
            continue
        if deck["privateDeck"]:
            continue
        catalog.append(deck)
    n=data.get("next") if isinstance(data,dict) else None
    if n and not n.startswith("http"):
        n=urllib.parse.urljoin("https://archidekt.com",n)
    next_url=n
catalog.sort(key=lambda x: (x.get("edhBracket") != 3, x.get("size") != 100, -(int(x.get("id") or 0))))
result={
    "owner":OWNER,"retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "total_public_listed":len(catalog),"decks":catalog,"errors":errors,
    "known_public_links":[
        "https://archidekt.com/decks/21930525/edh_zimone_and_dina_aristo",
        "https://archidekt.com/decks/23328062/edh_lathril_nico",
        "https://archidekt.com/decks/9542822/edh_liesa_stax",
    ]
}
(ROOT/"catalog.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
print("CATALOG",json.dumps(result,ensure_ascii=False),flush=True)
sys.exit(0 if catalog else 2)
