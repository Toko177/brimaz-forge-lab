#!/usr/bin/env python3
"""Exact and deliberately NARROW Brimaz post-cast tempo audit.

This is not a Magic gameplay engine, mana simulator, multiplayer winrate,
or guarantee that drawn spells survive. It evaluates only whether a card
known to be a castable ONE-MANA PHYREXIAN/ARTIFACT-CREATURE spell is visible
under a fully specified mana/remaining-life scenario.

References are the printed Oracle mana costs/creature types independently
verified on mtg.wtf:
 Vault Skirge: {1}{B/P}, Artifact Creature — Phyrexian Imp, flying/lifelink,
               choose 2 life for {B/P}, mana value 2 => incubate 2.
 Changeling Outcast: {B}, Creature — Shapeshifter, changeling => Phyrexian
               on stack, cannot block/be blocked, MV 1 => incubate 1.
The script counts the two only because they are VERIFIED by specific Oracle
texts. It never infers all other costs merely from spell mana values.
"""
import argparse
from math import comb
from pathlib import Path
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from deckbuild_prepare import read_deck

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"decks/Brimaz_V4_B3.txt"
TRIAL=ROOT/"decks/Brimaz_V5_Tempo_Trial.txt"
COMMANDER="Brimaz, Blight of Oreskos"

# Source-verified, deliberately enumerated cards, not a comprehensive
# mapping for any arbitrary deck.
LOW_COST_TRIGGER_OPTIONS={
    "Vault Skirge": {
        "mana_to_pay": 1, "requires_black_mana": False,
        "life_to_pay": 2, "brimaz_incubate_x": 2,
        "phyrexian": True,"artifact_creature":True,
        "independent_combat":"Flying, lifelink",},
    "Changeling Outcast": {
        "mana_to_pay": 1, "requires_black_mana": True,
        "life_to_pay": 0,"brimaz_incubate_x": 1,
        "phyrexian":True,"artifact_creature":False,
        "independent_combat":"Cannot be blocked, cannot block",},
}

CUT_TO_ADD={
    "Throne of Geth":"Vault Skirge",
    "Myr Sire":"Changeling Outcast",
}

def at_least_one(total, copies, seen):
    if not (0<=copies<=total and 0<=seen<=total):
        raise ValueError("Invalid population")
    return 1-comb(total-copies,seen)/comb(total,seen)

def read_variant(path):
    card_counter, commanders=read_deck(path,COMMANDER)
    if commanders[COMMANDER]!=1 or sum(card_counter.values())!=100:
        raise ValueError("Invalid Commander variant")
    return card_counter

def run(seen=12):
    baseline=read_variant(SOURCE)
    candidate=read_variant(TRIAL)
    if seen not in range(1,100):
        raise ValueError("Sample outside valid range")
    removed=baseline-candidate
    added=candidate-baseline
    if dict(removed)!={k:1 for k in CUT_TO_ADD} or dict(added)!={k:1 for k in CUT_TO_ADD.values()}:
        raise ValueError("Variant modifications differ from the declared isolated test")
    if any(not (data["phyrexian"] or data["artifact_creature"])
           or data["mana_to_pay"]!=1
           or data["brimaz_incubate_x"]<=0
           for data in LOW_COST_TRIGGER_OPTIONS.values()):
        raise ValueError("Oracle role annotation invalid")

    # The current V4 has no printed one-mana trigger cast options at all
    # without a cost reducer. This assertion relies on the manual Oracle
    # audit of the baseline list, NOT on calculating MV from deck names.
    if any(n in baseline for n in LOW_COST_TRIGGER_OPTIONS):
        raise ValueError("Baseline already includes verified one-mana options")

    physical_total=sum(candidate.values())
    low_cost_any= [n for n in LOW_COST_TRIGGER_OPTIONS if n in candidate]
    no_black= [n for n in low_cost_any if not LOW_COST_TRIGGER_OPTIONS[n]["requires_black_mana"]]
    with_black=low_cost_any
    result={
        "baseline":str(SOURCE.relative_to(ROOT)),
        "candidate":str(TRIAL.relative_to(ROOT)),
        "copies":physical_total,
        "changed_cards":CUT_TO_ADD,
        "condition":(
          "Brimaz is on the battlefield, its first four mana were paid; "
          "exactly one extra mana is currently untapped, life>=3, no cost "
          "reducers. Chance of a verified cheap compatible spell IN CARDS SEEN, "
          "not chance of having cast Brimaz or played lands."),
        "assumptions":"Seven-card opener + five multiplayer draw steps = 12 seen, no mulligans, exact uniform random card order. Alternative input --seen allows other sizes.",
        "cards_seen":seen,
        "new_one_mana_phyrexian_or_artifact_creature_spells":low_cost_any,
        "v4_known_one_mana_followup_options":0,
        "v5_one_mana_followup_options_any_mana_unspent":len(no_black),
        "v5_one_mana_followup_options_black_mana_unspent":len(with_black),
        "prob_at_least_one_generic_mana_followup_v4":0.0,
        "prob_at_least_one_generic_mana_followup_v5":round(at_least_one(physical_total,len(no_black),seen),6),
        "prob_at_least_one_black_mana_followup_v4":0.0,
        "prob_at_least_one_black_mana_followup_v5":round(at_least_one(physical_total,len(with_black),seen),6),
        "unblockable_bodies_without_commander":int("Changeling Outcast" in candidate),
        "flying_lifelink_bodies_without_commander":int("Vault Skirge" in candidate),
        "explicit_losses":[
            "Throne of Geth repeatable sacrifice/proliferation outlet",
            "Myr Sire Phyrexian 1/1 death replacement body and easy recursion",
        ],
        "not_estimated":[
            "real land/mana probabilities","opponents/interactions","mulligans",
            "commander survival","timing and holding cards","incubator transformations",
            "damage per player","wins or winrates","deck optimum",
        ],
        "verdict":"Proven new tactical ONE-MANA casting options, NOT proven winrate or net deck strength.",
    }
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seen",type=int,default=12)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    output=run(args.seen)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("BRIMAZ_V5_TEMPO_EXACT_SCENARIO",json.dumps(output,ensure_ascii=False))
if __name__=="__main__":main()
