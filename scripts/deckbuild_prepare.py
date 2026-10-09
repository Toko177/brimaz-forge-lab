#!/usr/bin/env python3
"""Prepare two independently auditable Commander deck candidates for Forge.

Input: Moxfield/MTGO quantity list or Forge .dck, each explicitly declares a
commander (via CLI or [Commander]). No deck contents are ever modified silently.
Live Scryfall validation happens separately, before the simulations.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

QUANTITY = re.compile(r"^(\d+)\s+(.+?)\s*$")
HEADERS = {"[metadata]","[main]","[commander]"}
BASES = {"Deck_Reference","Deck_Candidate"}


def read_deck(path, explicit_commander=None):
    counts=collections.Counter()
    commanders=collections.Counter()
    section=None
    for lineno, raw in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(),1):
        line=raw.strip()
        if not line or line.startswith(("#","//")):continue
        if line.lower() in HEADERS:
            section=line.lower()[1:-1]
            continue
        if line.lower().startswith("name=") and section=="metadata":continue
        match=QUANTITY.fullmatch(line)
        if not match:
            raise ValueError(f"{path}:{lineno}: expected 'quantity card name', got {line!r}")
        q,name=int(match[1]),match[2]
        if q<1:
            raise ValueError(f"{path}:{lineno}: nonpositive card quantity")
        counts[name]+=q
        if section=="commander":
            commanders[name]+=q
    if explicit_commander:
        names=[x.strip() for x in explicit_commander.split(";") if x.strip()]
        if not names or len(set(names))!=len(names):
            raise ValueError("Specify one or two different commanders")
        for name in names:
            if name not in counts:
                raise ValueError(f"Commander {name!r} not present in 100-card input")
        # In a Forge .dck the command zone must match explicit user intent.
        if commanders and set(commanders)!=set(names):
            raise ValueError("Declared [Commander] section differs from supplied --commander")
        commanders=collections.Counter({name:1 for name in names})
    if not commanders:
        raise ValueError(f"No commander declared for {path}; use --commander or [Commander]")
    if sum(commanders.values()) not in (1,2):
        raise ValueError("Expect one commander or two commanders with a legal pairing")
    if any(counts[name]<q for name,q in commanders.items()):
        raise ValueError("Commander is missing from total quantity list")
    if sum(counts.values())!=100:
        raise ValueError(f"Commander deck must have 100 cards, observed {sum(counts.values())}")
    if any(q<=0 for q in counts.values()):
        raise ValueError("Invalid quantity")
    return counts,commanders


def write_deck(path,counts,commanders,label):
    main=counts.copy()
    for name,q in commanders.items():
        main[name]-=q
        if main[name]<0:raise ValueError("Commander overdraw")
    lines=["[metadata]",f"Name={label}","[Main]"]
    lines.extend(f"{n} {card}" for card,n in sorted(main.items()) if n)
    lines+=["[Commander]"]+[f"{n} {card}" for card,n in sorted(commanders.items())]
    dest=Path(path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return hashlib.sha256(dest.read_bytes()).hexdigest()


def prepare(reference,candidate,out,reference_commander=None,candidate_commander=None):
    out=Path(out)
    specs=[("reference",Path(reference),reference_commander,"Deck_Reference"),
           ("candidate",Path(candidate),candidate_commander,"Deck_Candidate")]
    report={"version":1,"decks":{}}
    for role,source,commander,label in specs:
        if not source.is_file():raise FileNotFoundError(source)
        counts,cmdrs=read_deck(source,commander)
        output=out/(label+".dck")
        digest=write_deck(output,counts,cmdrs,label)
        report["decks"][role]={
            "label":label, "source_file":str(source),
            "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "forge_file":str(output),"forge_sha256":digest,
            "commander":dict(cmdrs),"cards":sum(counts.values()),
            "distinct":len(counts)}
    report["delta"]={
        "added":dict(sorted((collections.Counter(read_deck(candidate,candidate_commander)[0])-
                             collections.Counter(read_deck(reference,reference_commander)[0])).items())),
        "removed":dict(sorted((collections.Counter(read_deck(reference,reference_commander)[0])-
                               collections.Counter(read_deck(candidate,candidate_commander)[0])).items())),
    }
    manifest=out/"candidate-manifest.json"
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--candidate",type=Path,required=True)
    p.add_argument("--reference-commander")
    p.add_argument("--candidate-commander")
    p.add_argument("--out",type=Path,default=Path("forge_decks"))
    a=p.parse_args()
    report=prepare(a.reference,a.candidate,a.out,a.reference_commander,a.candidate_commander)
    print("DECKBUILD_PREPARED",json.dumps(report,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
