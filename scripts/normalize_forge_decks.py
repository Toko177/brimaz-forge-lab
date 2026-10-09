#!/usr/bin/env python3
"""Convert Archidekt's combined face names to Forge's primary oracle face.

The original public deck snapshots remain unchanged for provenance.
This is exclusively an *identifier serialization* change: 100-card quantities
and commander choices MUST remain identical.
"""
import argparse,collections,hashlib,json,pathlib,re,sys
p=argparse.ArgumentParser()
p.add_argument("--input",default="forge_decks")
p.add_argument("--output",default="forge_normalized")
p.add_argument("--legality",default="legality/report.json")
args=p.parse_args()
src=pathlib.Path(args.input);dest=pathlib.Path(args.output);dest.mkdir(exist_ok=True)
report=json.loads(pathlib.Path(args.legality).read_text(encoding="utf-8"))
legal={pathlib.Path(d["file"]).stem:d for d in report["reports"]}
transforms=[];errors=[]
for name,meta in legal.items():
    file=src/(name+".dck")
    if not file.is_file():errors.append("Missing verified source: "+str(file));continue
    if not meta.get("structurally_and_legality_valid"):
        errors.append("Scryfall deck not legal: "+name);continue
    if hashlib.sha256(file.read_bytes()).hexdigest()!=meta["sha256"]:
        errors.append("Deck source checksum changed after Scryfall validation: "+name);continue
    lines=file.read_text(encoding="utf-8").splitlines()
    output=[]
    counts=collections.Counter()
    changed=[]
    for line in lines:
        m=re.fullmatch(r"(\d+)\s+(.+)",line.strip())
        if m:
            n=int(m.group(1));old=m.group(2)
            primary=old.split(" // ")[0] if " // " in old else old
            counts[primary]+=n
            output.append(str(n)+" "+primary)
            if primary!=old: changed.append({"from":old,"to":primary,"quantity":n})
        else:
            output.append(line)
    if sum(counts.values())!=100:
        errors.append("Count changed: "+name);continue
    if len(counts)!=len(set(counts)):
        errors.append("Name collision: "+name);continue
    target=dest/file.name
    target.write_text("\n".join(output)+"\n",encoding="utf-8")
    transforms.append({"deck":name,"source_sha256":meta["sha256"],
                      "normalized_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                      "cards":sum(counts.values()),"name_transformations":changed})
    print("NORMALIZED",name,"changes",len(changed),flush=True)
    for change in changed:print("NAME_MAPPING",name,json.dumps(change,ensure_ascii=False),flush=True)
pathlib.Path("results/forge_normalization").mkdir(parents=True,exist_ok=True)
pathlib.Path("results/forge_normalization/report.json").write_text(
    json.dumps({"decks":transforms,"errors":errors},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("NORMALIZATION_SUMMARY",len(transforms),"decks; errors",errors,flush=True)
if errors:sys.exit(2)
