#!/usr/bin/env python3
"""Cheap factual Commander deck-structure summary from live Scryfall cards.

This is an evidence-grounded preflight, NOT a deck power score or a simulation.
One commander is included in the 100-card totals. Split and MDFC primary faces
are matched through the same Scryfall object as the legality validation stage.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

def primary(name):
    return name.split(" // ",1)[0]

def card_faces(card):
    return card.get("card_faces") or [card]

def has_land_front(card):
    faces=card_faces(card)
    return "Land" in faces[0].get("type_line","").split(" — ")[0].split()

def has_land_back(card):
    # Only a modal DFC lets the player choose to play a back-face land from
    # hand. A transform DFC which becomes a land after transforming is NOT
    # an additional starting land source.
    return card.get("layout")=="modal_dfc" and any(
        "Land" in f.get("type_line","").split(" — ")[0].split()
        for f in card_faces(card)[1:])

def mana_value(card):
    if "cmc" in card:
        return float(card["cmc"])
    faces=card_faces(card)
    if "cmc" in faces[0]:
        return float(faces[0]["cmc"])
    raise ValueError("Scryfall card has no converted mana value")

def parse_forge(file):
    counts=Counter()
    section=None
    for line in Path(file).read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if line.lower() in ("[main]","[commander]"):
            section=line.lower()[1:-1];continue
        if not line or line.lower()=="[metadata]" or line.lower().startswith("name="):
            continue
        q,sep,name=line.partition(" ")
        if not sep or not q.isdigit() or section not in ("main","commander"):
            raise ValueError(f"Malformed Forge preflight deck: {line}")
        counts[name]+=int(q)
    if sum(counts.values())!=100:
        raise ValueError("Preflight requires exactly 100 real deck cards")
    return counts

def detail_for_deck(deckfile,cards):
    counts=parse_forge(deckfile)
    front_lands=0;land_backs=0;nonlands=0;mana_values=[]
    histogram=Counter();types=Counter()
    for name,qty in counts.items():
        card=cards.get(name) or cards.get(primary(name))
        if not card:
            raise ValueError("No Scryfall metadata for real deck card: "+name)
        if card.get("object")=="card" and card.get("legalities",{}).get("commander")!="legal":
            raise ValueError("Card no longer legal in Commander: "+name)
        front=has_land_front(card)
        back=has_land_back(card)
        if front:
            front_lands+=qty
        if back and not front:
            land_backs+=qty
        # Modal spells with a land on the back are spells for the mana curve.
        if not front:
            v=mana_value(card)
            if v<0 or v>100:
                raise ValueError("Invalid Scryfall mana value")
            nonlands+=qty
            mana_values.extend([v]*qty)
            histogram[str(int(v)) if v<7 else "7+"]+=qty
        for token in ("Creature","Artifact","Enchantment","Instant","Sorcery","Planeswalker"):
            face_type=card_faces(card)[0].get("type_line",card.get("type_line",""))
            if token in face_type:
                types[token]+=qty
    return {
        "total_cards":sum(counts.values()),
        "front_face_lands":front_lands,
        "additional_spell_land_backfaces":land_backs,
        "land_capable_cards":front_lands+land_backs,
        "non_front_land_cards":nonlands,
        "mean_spell_mana_value":round(sum(mana_values)/len(mana_values),3) if mana_values else None,
        "mana_value_distribution":dict(sorted(histogram.items(),key=lambda x:int(x[0].rstrip("+")))),
        "face_type_counts":dict(sorted(types.items())),
        "caveats":[
            "Land-capable MDFCs are not equivalent to normal lands in all decisions; no mulligan assumptions are made.",
            "This reports first-face spell mana values, not casting modes, alternate costs, discounts, or mana production.",
            "Card-type categories overlap for artifact creatures etc; no heuristic card power ranking."
        ]
    }

def analyze(manifest,cards,decks):
    reference=detail_for_deck(Path(decks)/"Deck_Reference.dck",cards)
    candidate=detail_for_deck(Path(decks)/"Deck_Candidate.dck",cards)
    def delta(key):
        a=reference[key];b=candidate[key]
        return round(b-a,3) if a is not None and b is not None else None
    return {
        "source":"Scryfall fresh legality collection (archived by deckbuild workflow)",
        "reference":reference,"candidate":candidate,
        "candidate_minus_reference":{
            "front_face_lands":delta("front_face_lands"),
            "land_capable_cards":delta("land_capable_cards"),
            "mean_spell_mana_value":delta("mean_spell_mana_value"),
            "non_front_land_cards":delta("non_front_land_cards")
        },
        "card_swaps":manifest["delta"],
        "note":"Instant structural preflight, NOT simulated winrate or evidence of optimal card choices."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--decks",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--scryfall",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    deck_manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
    snapshot=json.loads(a.scryfall.read_text(encoding="utf-8"))
    if snapshot.get("source")!="https://api.scryfall.com/cards/collection":
        raise ValueError("Only the original Scryfall API snapshot is accepted")
    report=analyze(deck_manifest,snapshot["cards"],a.decks)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("DECKBUILD_QUICK_MANA_CURVE",json.dumps(report["candidate_minus_reference"],ensure_ascii=False))
    print("DECKBUILD_INSTANT_PREFLIGHT",json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
