#!/usr/bin/env python3
"""Commander legality gate using live Scryfall Oracle / Commander legality data.

Fail closed. This does not assert that Forge reproduces every Oracle interaction.
Original Scryfall responses and SHA256s are archived for audit.
"""
import argparse,collections,datetime,hashlib,json,pathlib,re,sys,time,urllib.request,urllib.error

p=argparse.ArgumentParser()
p.add_argument("--deck",action="append",default=[],help="Path to .dck or Moxfield txt list; may be repeated")
p.add_argument("--out",default="results/legality")
p.add_argument("--require-no-game-changers",action="store_true")
args=p.parse_args()
output=pathlib.Path(args.out);output.mkdir(parents=True,exist_ok=True)
BASICS={"Plains","Island","Swamp","Mountain","Forest","Wastes",
"Snow-Covered Plains","Snow-Covered Island","Snow-Covered Swamp",
"Snow-Covered Mountain","Snow-Covered Forest"}
ALLOWED_MULTIPLES={"Rat Colony","Shadowborn Apostle","Relentless Rats",
"Persistent Petitioners","Dragon's Approach","Slime Against Humanity","Hare Apparent"}
LIMITED={"Nazgûl":9,"Seven Dwarves":7}
def parse(path):
    entries=collections.Counter();commanders=collections.Counter();section=None
    for x in path.read_text(encoding="utf-8").splitlines():
        line=x.strip()
        if not line or line.startswith("//") or line.startswith("#"):continue
        if line.lower() in ("[metadata]","[main]","[commander]"):
            section=line.lower().strip("[]");continue
        if line.lower().startswith("name="):continue
        m=re.fullmatch(r"(\d+)\s+(.+)",line)
        if not m:raise ValueError(f"Invalid deck row {path}: {line}")
        qty=int(m.group(1));name=m.group(2).strip()
        if not qty:raise ValueError(f"Zero-count card {name}")
        entries[name]+=qty
        if section=="commander" or (section is None and name=="Brimaz, Blight of Oreskos"):
            commanders[name]+=qty
    if not commanders:raise ValueError("No commander explicitly identified in "+str(path))
    return entries,commanders
def post_collection(names):
    cards={};not_found=[]
    for start in range(0,len(names),70):
        batch=names[start:start+70]
        body=json.dumps({"identifiers":[{"name":n} for n in batch]}).encode()
        req=urllib.request.Request("https://api.scryfall.com/cards/collection",data=body,headers={
            "Content-Type":"application/json","Accept":"application/json",
            "User-Agent":"BrimazForgeLab/1.0 (noncommercial Commander deck legality audit)"
        },method="POST")
        try:
            with urllib.request.urlopen(req,timeout=70) as response:
                payload=json.load(response)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Scryfall HTTP {e.code}; validation MUST FAIL CLOSED") from e
        for card in payload.get("data",[]):
            cards[card["name"]]=card
        not_found.extend(payload.get("not_found",[]))
        if start+70<len(names):time.sleep(0.18)
    return cards,not_found
def main():
    decks=[]
    for path in args.deck:
        file=pathlib.Path(path);entries,commanders=parse(file)
        decks.append((file,entries,commanders))
    if not decks:p.error("At least one --deck is required")
    names=sorted(set(name for _,entries,_ in decks for name in entries))
    cards,not_found=post_collection(names)
    snap={"retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "source":"https://api.scryfall.com/cards/collection",
          "cards":cards,"unrecognized":not_found}
    (output/"scryfall-snapshot.json").write_text(json.dumps(snap,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    report=[]
    for file,entries,commanders in decks:
        errors=[];warn=[];distinct=len(entries);qty=sum(entries.values())
        if qty!=100:errors.append(f"Expected 100 cards INCLUDING commanders, got {qty}")
        if sum(commanders.values()) not in (1,2):
            errors.append("Expected one commander or two partners/backgrounds")
        for n,q in entries.items():
            if q>1 and n not in BASICS and n not in ALLOWED_MULTIPLES and q>LIMITED.get(n,1):
                errors.append(f"Too many copies ({q}) of {n}")
            if n not in cards:
                errors.append("Unknown or unsupported card name: "+n)
        commander_color=set()
        for n in commanders:
            c=cards.get(n)
            if c:
                commander_color.update(c.get("color_identity",[]))
                if "Legendary Creature" not in c.get("type_line","") and "can be your commander" not in c.get("oracle_text","").lower():
                    # Background / Doctor's companion checks require more than this simple gate.
                    warn.append("Non-creature commander requires separate pairing audit: "+n)
        for n in entries:
            c=cards.get(n)
            if not c:continue
            legality=c.get("legalities",{}).get("commander")
            if legality!="legal":errors.append(f"{n} Commander legality = {legality}")
            outside=set(c.get("color_identity",[]))-commander_color
            if outside:errors.append(f"Color identity violation {n}: {sorted(outside)}")
            gc=c.get("game_changer")
            if gc is True:
                warn.append("Game Changer: "+n)
                if args.require_no_game_changers:errors.append("Forbidden Game Changer: "+n)
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        result={"file":str(file),"sha256":digest,"cards":qty,"distinct":distinct,
                "commanders":dict(commanders),"colors":sorted(commander_color),
                "errors":sorted(set(errors)),"warnings":sorted(set(warn)),
                "structurally_and_legality_valid":not errors}
        report.append(result)
        print("DECK_LEGALITY",json.dumps(result,ensure_ascii=False),flush=True)
    (output/"report.json").write_text(json.dumps({
        "reports":report,"unknown_cards":not_found,
        "source":"Scryfall (Oracle data, commander legality, color identity)",
        "note":"Card legality is not proof of every Forge interaction being implemented correctly.",
        "checked_on_utc":snap["retrieved_utc"]
    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if any(x["errors"] for x in report):sys.exit(2)
    print("ALL_DECKS_VALIDATED",len(report),flush=True)
if __name__=="__main__":main()
