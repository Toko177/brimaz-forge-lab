#!/usr/bin/env python3
"""Brimaz V3->V4 paper-deck audit: EXACT combinatorics, NEVER Magic games.

Structural checks are strict; card role tags are reviewed human assumptions.
The hypergeometric output only measures cards physically SEEN in a random
n-card subset, never cast, resolved, activated, or sufficient to win.
Never infer bracket legality, AI strength or multiplayer win probability.
"""
import collections
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckbuild_prepare import read_deck

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/"decks/Brimaz_V3.txt"
CANDIDATE=ROOT/"decks/Brimaz_V4_B3.txt"
FORGE_V4=ROOT/"deck_candidates/Brimaz_V4_B3.dck"
FORGE_V3=ROOT/"forge_decks/Brimaz_V3.dck"
COMMANDER="Brimaz, Blight of Oreskos"

SWAPS=(
    ("Darksteel Splicer", "Nadier's Nightblade"),
    ("Chronomancer", "Myr Sire"),
    ("Phyrexian Delver", "Morbid Opportunist"),
    ("Tortured Existence", "Braids, Arisen Nightmare"),
    ("Inspiring Statuary", "Idol of Oblivion"),
    ("Norn's Wellspring", "Ichor Wellspring"),
    ("Etchings of the Chosen", "Rite of Oblivion"),
    ("Vault of the Archangel", "War Room"),
)
# Explicit conservative tags: a card listed is capable of the role under
# some conditions, not necessarily at that turn or without mana/other cards.
BRIMAZ_CASTS={
    "Activated Sleeper", "Arcbound Ravager", "Bloated Processor",
    "Priest of Gix", "Chronomancer", "Compleated Huntmaster",
    "Darksteel Splicer", "Elas il-Kor, Sadistic Pilgrim",
    "Elesh Norn", "Essence of Orthodoxy", "Filigree Vector",
    "Grafted Butcher", "Metastatic Evangel", "Mondrak, Glory Dominus",
    "Myr Retriever", "Norn's Inquisitor", "Ornithopter of Paradise",
    "Phyrexian Delver", "Phyrexian Fleshgorger", "Phyrexian Missionary",
    "Progenitor Exarch", "Roaming Throne", "Scheming Aspirant",
    "Gold Myr", "Vraan, Executioner Thane", "Vulpine Harvester",
    "Myr Sire",
}
# Deliberately exclude one-shot draw (Deadly Dispute/Ichor) and the
# uncertain triggers on cards that require other resources to function.
REPEATABLE_DRAW={
    "Skullclamp", "Caretaker's Talent", "Norn's Wellspring",
    "Castle Locthwain", "Yawgmoth, Thran Physician",
    "Idol of Oblivion", "Morbid Opportunist", "Braids, Arisen Nightmare",
    "War Room",
}
SACRIFICE_ACCESS={
    "Arcbound Ravager", "Bartolomé del Presidio", "Bloated Processor",
    "Compleated Huntmaster", "Ashnod's Altar", "Krark-Clan Ironworks",
    "Phyrexian Altar", "Throne of Geth", "Spawning Pit",
    "Yawgmoth, Thran Physician", "High Market", "Phyrexian Tower",
    "Braids, Arisen Nightmare", "Rite of Oblivion",
}
SACRIFICE_PAYOFF={
    "Marionette Apprentice", "Marionette Master", "Mirkwood Bats",
    "Vraan, Executioner Thane", "Elas il-Kor, Sadistic Pilgrim",
    "Nadier's Nightblade", "Athreos, God of Passage",
    "The Meathook Massacre",
}
LAND_SOURCES={
    "Bleachbone Verge","Bojuka Bog","Brightclimb Pathway","Caves of Koilos",
    "Castle Locthwain","Command Tower","Concealed Courtyard",
    "Eiganjo, Seat of the Empire","Exotic Orchard","Fetid Heath",
    "Godless Shrine","High Market","Isolated Chapel","Karn's Bastion",
    "Marsh Flats","Path of Ancestry","Phyrexian Tower",
    "Shattered Sanctum","Silent Clearing","Tainted Field",
    "Takenuma, Abandoned Mire","The Mycosynth Gardens","The Seedcore",
    "Urborg, Tomb of Yawgmoth","Urza's Saga","Vault of Champions",
    "Vault of the Archangel","War Room","Plains","Swamp",
    # These are modal spells: count as possible sources, not confirmed mana.
    "Agadeem's Awakening","Malakir Rebirth","Witch Enchanter",
}
BASIC={"Plains","Swamp"}

def hypergeom_at_least(total,success,seen,threshold=1):
    if not (0<=success<=total and 0<=seen<=total and threshold>=0):
        raise ValueError("Invalid population")
    d=math.comb(total,seen)
    return sum(math.comb(success,k)*math.comb(total-success,seen-k)
               for k in range(threshold,min(success,seen)+1)
               if seen-k <= total-success)/d

def both_seen(total,left,right,seen):
    # Inclusion/exclusion with overlapping role classes.
    a,b=len(left),len(right)
    union=len(left|right)
    c=lambda k: math.comb(k,seen) if k>=seen else 0
    return (math.comb(total,seen)-c(total-a)-c(total-b)+c(total-union))/math.comb(total,seen)

def validate():
    a,ca=read_deck(REFERENCE,COMMANDER)
    b,cb=read_deck(CANDIDATE,COMMANDER)
    c,cc=read_deck(FORGE_V4,COMMANDER)
    v3,cv3=read_deck(FORGE_V3,COMMANDER)
    if b!=c or a!=v3 or ca!=cb or ca!=cc or ca!=cv3:
        raise ValueError("Moxfield and Forge files diverge from their paired DCK")
    if ca!=collections.Counter({COMMANDER:1}):
        raise ValueError("Unexpected commander")
    if sum(a.values())!=100 or sum(b.values())!=100:
        raise ValueError("Commander must be 100 physical cards")
    if any(n!=1 for name,n in b.items() if name not in BASIC):
        raise ValueError("Nonbasic duplicate")
    deleted=a-b
    added=b-a
    if deleted!=collections.Counter(x for x,_ in SWAPS):
        raise ValueError("Unexpected V3 removals")
    if added!=collections.Counter(y for _,y in SWAPS):
        raise ValueError("Unexpected V4 additions")
    if b["Plains"]!=4 or b["Swamp"]!=4:
        raise ValueError("Unexpected basic lands")
    for label,deck in (("V3",a),("V4",b)):
        if sum(n for card,n in deck.items() if card in LAND_SOURCES)!=38:
            raise ValueError(label+" land-source assumptions changed")
    return a,b

def rows(deck):
    expanded=list(itertools.chain.from_iterable(
        itertools.repeat(card,n) for card,n in deck.items()))
    if len(expanded)!=100:raise AssertionError("Unbalanced physical cards")
    def subset(tags):
        return {index for index,card in enumerate(expanded) if card in tags}
    seen10=10 # 7 starting hand + 3 draw steps, simplified, no mulligans
    seen13=13 # 7 + 6 draw steps
    land=subset(LAND_SOURCES)
    draw=subset(REPEATABLE_DRAW)
    casts=subset(BRIMAZ_CASTS)
    outlet=subset(SACRIFICE_ACCESS)
    payoff=subset(SACRIFICE_PAYOFF)
    return {
        "possible_land_cards":len(land),
        "brimaz_eligible_cast_names":len(casts),
        "repeatable_draw_source_names":len(draw),
        "sacrifice_access_names":len(outlet),
        "sacrifice_payoff_names":len(payoff),
        "p_3plus_land_sources_seen_in_10":round(hypergeom_at_least(100,len(land),seen10,3),6),
        "p_1plus_repeatable_draw_source_seen_in_10":round(hypergeom_at_least(100,len(draw),seen10),6),
        "p_2plus_brimaz_eligible_casts_seen_in_13":round(hypergeom_at_least(100,len(casts),seen13,2),6),
        "p_sacrifice_access_and_payoff_seen_in_13":round(both_seen(100,outlet,payoff,seen13),6),
    }

def report():
    a,b=validate()
    return {
        "method":"EXACT HYPERGEOMETRIC RANDOM CARD VISIBILITY; NOT GAMEPLAY",
        "v3_sha256":hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        "v4_sha256":hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "removed":list((a-b).elements()),
        "added":list((b-a).elements()),
        "v3":rows(a),"v4":rows(b),
        "not_measured":["mana payment","land drop sequencing","colored sources",
                        "MDFCs entering tapped","mulligan strategy",
                        "casting and resolved effects","four-player interactions",
                        "games and wins","winrate","bracket certification"],
    }
if __name__=="__main__":
    print("BRIMAZ_V4_STATIC_VISIBILITY_AUDIT",json.dumps(report(),ensure_ascii=False))
