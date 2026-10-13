#!/usr/bin/env python3
"""Offline test of Scryfall Oracle pool discovery. No fabricated games."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from scan_commander_oracle_pool import eligible,classify,evaluate

def card(name,typ,oracle,colors=(),cmc=2,legality="legal",gc=False):
    return {"name":name,"oracle_id":"oracle-"+name,"type_line":typ,
            "oracle_text":oracle,"color_identity":list(colors),"cmc":cmc,
            "game_changer":gc,"legalities":{"commander":legality}}
fixture=[
    card("Sunder the Gateway","Sorcery",
         "Destroy target nontoken artifact or enchantment an opponent controls. Incubate 2.",("W",)),
    card("Phyrexian Rager","Creature — Phyrexian Horror",
         "When this creature enters, draw a card and you lose 1 life.",("B",),3),
    card("Sculpted Perfection","Enchantment",
         "When this enchantment enters, incubate 2. Phyrexians you control get +1/+1.",("W","B"),4),
    card("Rhystic Study","Enchantment","Whenever an opponent casts a spell, draw a card.",("U",),3),
    card("Forbidden Card","Creature — Phyrexian", "Proliferate.",("B",),2,"banned"),
    card("Smothering Tithe","Enchantment","Whenever an opponent draws a card, create a Treasure token.",("W",),4,gc=True),
    card("Phyrexian Land","Land","{T}: Add {C}.",()),
    card("Skithiryx","Creature — Phyrexian Dragon","Flying, infect.",("B",),5),
]
assert eligible(fixture[0])
assert not eligible(fixture[3])
assert not eligible(fixture[4])
assert not eligible(fixture[5])
assert {"single_removal","incubate"} <= set(classify(fixture[0])["roles"])
assert "brimaz_cast" in classify(fixture[1])["roles"]
assert {"board_buff","incubate"} <= set(classify(fixture[2])["roles"])
assert classify(fixture[-1])["poison_or_infect_text"]
res=evaluate(fixture,{"updated_at":"fixed-fixture"},10)
assert res["counts"]["oracle_records"]==8
assert res["counts"]["eligible_WB_colorless_no_game_changer"]==5
assert len(res["eligible_index"])==5
assert "incubate" in res["roles"]
assert all(x["name"]!="Smothering Tithe" for x in res["eligible_index"])
assert all(x["name"]!="Rhystic Study" for x in res["eligible_index"])
assert res["warning"].startswith("Heuristic")
print("BRIMAZ_COMPLETE_ORACLE_POOL_DISCOVERY_OFFLINE_TEST_PASS")
