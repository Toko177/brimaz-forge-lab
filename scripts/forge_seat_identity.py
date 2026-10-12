#!/usr/bin/env python3
"""Strict real-Forge AI seat-to-deck identity resolver.

The simulator's deck file is e.g. Kaal_10347090.dck but the JVM logs
"player=Ai(4)-EDH Dungeon Party Time". Identity is a two-part contract: seat number
and exact [metadata] Name from the corresponding deck. Never substitute
a substring match or guess the winner from a name alone.
"""
from pathlib import Path
import re

AI_NAME=re.compile(r"^Ai\(([1-4])\)-([^\r\n]+)$")

def canonical_label(deck_id,deck_dir):
    """Read only version-controlled DCK metadata; fail on ambiguity."""
    if not re.fullmatch(r"[A-Za-z0-9_]+",deck_id):
        raise ValueError("Unsafe deck ID")
    path=Path(deck_dir)/(deck_id+".dck")
    if not path.is_file():raise ValueError("Missing canonical deck "+deck_id)
    raw=path.read_text(encoding="utf-8-sig")
    if not raw.startswith("[metadata]\n"):
        raise ValueError("Missing initial [metadata] section: "+deck_id)
    head=raw.split("\n[",1)[0]
    names=[line[len("Name="):].strip() for line in head.splitlines()
           if line.startswith("Name=")]
    if len(names)!=1 or not names[0]:
        raise ValueError("No unique [metadata] Name: "+deck_id)
    return names[0]

def display_for_seat(deck_id,deck_dir,mirror=False):
    if mirror and (deck_id.startswith("Brimaz_Challenger")
                   or deck_id.startswith("Brimaz_Reference")):
        accepted={"Brimaz_Challenger","Brimaz_Reference",
                  "Brimaz_Challenger_A","Brimaz_Challenger_B",
                  "Brimaz_Reference_A","Brimaz_Reference_B"}
        if deck_id not in accepted:raise ValueError("Unknown mirror deck identity")
        return deck_id.replace("_"," ")
    return canonical_label(deck_id,deck_dir)

def resolve_ai_player(raw,seats,deck_dir,mirror=False):
    """Return original pinned deck ID; reject wrong seat or spoofed display."""
    if len(seats)!=4 or len(set(seats))!=4:
        raise ValueError("Exactly four distinct game seats required")
    match=AI_NAME.fullmatch(raw)
    if match is None:raise ValueError("Invalid Forge Ai(n)-Name identity: "+raw)
    index=int(match.group(1))-1
    deck=seats[index]
    expected=display_for_seat(deck,deck_dir,mirror=mirror)
    if match.group(2)!=expected:
        raise ValueError("Forged/wrong seat display: "+
                         repr(raw)+" expected "+repr(expected))
    return deck
