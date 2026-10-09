#!/usr/bin/env python3
"""Produce a 100-card Commander challenger by applying explicit one-for-one swaps.

Syntax:
    --swaps "1 Card Out -> 1 Card In; Plains -> Swamp"
    --base decks/Brimaz_V3.txt --commander "Brimaz, Blight of Oreskos"
No Scryfall legality guesswork: the downstream pipeline checks real Oracle
legality, color identity and any Game Changer exclusions before simulating.
"""
import argparse
import collections
from pathlib import Path
import re
from deckbuild_prepare import read_deck

QTY=re.compile(r"^(?:(\d+)\s+)?(.+?)\s*$")


def parse_component(text):
    match=QTY.fullmatch(text.strip())
    if not match:raise ValueError("Empty or malformed swap card name")
    qty=int(match[1] or 1)
    if not 1<=qty<=100 or not match[2].strip():
        raise ValueError("Invalid quantity or blank card name")
    return qty,match[2].strip()


def apply_swaps(base,commander,swaps):
    counts,commanders=read_deck(base,commander)
    chunks=[s.strip() for s in swaps.split(";") if s.strip()]
    if not chunks:
        raise ValueError("At least one explicit card replacement required")
    removals=collections.Counter()
    additions=collections.Counter()
    for chunk in chunks:
        parts=chunk.split("->")
        if len(parts)!=2:
            raise ValueError("Swap syntax requires 'card -> replacement' separated by semicolons")
        num_out,out_name=parse_component(parts[0])
        num_in,in_name=parse_component(parts[1])
        if num_out!=num_in:
            raise ValueError("Each swap must preserve exact deck card count")
        if out_name==in_name:
            raise ValueError("Swapping card for itself has no deckbuilding effect")
        removals[out_name]+=num_out
        additions[in_name]+=num_in
    for name,qty in removals.items():
        if qty>counts.get(name,0)-commanders[name]:
            raise ValueError(f"Cannot remove {qty} copies of {name}: not present or protected commander")
    for name,qty in removals.items():
        counts[name]-=qty
        if counts[name]==0:del counts[name]
    counts.update(additions)
    if sum(counts.values())!=100:
        raise ValueError("Swaps must keep exactly 100 cards")
    if any(counts[c]<n for c,n in commanders.items()):
        raise ValueError("Commander was removed from the list")
    return counts,commanders,removals,additions


def save_candidate(path,counts,commanders):
    # Plain numbered list, explicit commander supplied again to Scryfall/Forge.
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text("".join(f"{n} {name}\n" for name,n in sorted(counts.items())),encoding="utf-8")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--commander",required=True)
    p.add_argument("--swaps",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    counts,commanders,removed,added=apply_swaps(a.base,a.commander,a.swaps)
    save_candidate(a.out,counts,commanders)
    print("DECKBUILD_SWAPS_APPLIED",{"removed":dict(removed),"added":dict(added),
                                    "commander":dict(commanders),"cards":sum(counts.values())})


if __name__=="__main__":
    main()
