import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from deckbuild_preflight import analyze,detail_for_deck,has_land_front,has_land_back

CARDS={
    "Plains":{"object":"card","type_line":"Basic Land — Plains","cmc":0,
              "legalities":{"commander":"legal"}},
    "Sol Ring":{"object":"card","type_line":"Artifact","cmc":1,
                "legalities":{"commander":"legal"}},
    "Brimaz, Blight of Oreskos":{"object":"card","type_line":"Legendary Creature — Phyrexian Cat","cmc":4,
                                 "legalities":{"commander":"legal"}},
    "Malakir Rebirth":{"object":"card","type_line":"Instant // Land","cmc":1,
                       "card_faces":[
                           {"type_line":"Instant","cmc":1},
                           {"type_line":"Land"}],
                       "legalities":{"commander":"legal"}},
}

def create_deck(root,name,with_mdfc=False):
    deck=pathlib.Path(root)/(name+".dck")
    lines=["[metadata]",f"Name={name}","[Main]"]
    if with_mdfc:
        lines+=["97 Plains","1 Malakir Rebirth","1 Sol Ring"]
    else:
        lines+=["98 Plains","1 Sol Ring"]
    lines+=["[Commander]","1 Brimaz, Blight of Oreskos"]
    deck.write_text("\n".join(lines)+"\n")
    return deck


class FactualScryfallDeckTests(unittest.TestCase):
    def test_modal_spell_land_counts_both_spells_and_land_capability(self):
        with tempfile.TemporaryDirectory() as d:
            deck=create_deck(d,"Deck_Candidate",with_mdfc=True)
            r=detail_for_deck(deck,CARDS)
            self.assertEqual(r["total_cards"],100)
            self.assertEqual(r["front_face_lands"],97)
            self.assertEqual(r["additional_spell_land_backfaces"],1)
            self.assertEqual(r["land_capable_cards"],98)
            self.assertEqual(r["non_front_land_cards"],3)
            self.assertEqual(r["mana_value_distribution"],{"1":2,"4":1})

    def test_full_reference_and_candidate_mana_curve_delta(self):
        with tempfile.TemporaryDirectory() as d:
            create_deck(d,"Deck_Reference",with_mdfc=False)
            create_deck(d,"Deck_Candidate",with_mdfc=True)
            output=analyze({"delta":{"added":{"Malakir Rebirth // Malakir Mire":1},
                                     "removed":{"Plains":1}}},CARDS,d)
            self.assertEqual(output["candidate_minus_reference"]["front_face_lands"],-1)
            self.assertEqual(output["candidate_minus_reference"]["land_capable_cards"],0)
            self.assertEqual(output["candidate_minus_reference"]["non_front_land_cards"],1)

    def test_legal_card_missing_from_scryfall_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=create_deck(d,"Deck_Reference")
            with self.assertRaisesRegex(ValueError,"No Scryfall metadata"):
                detail_for_deck(p,{"Plains":CARDS["Plains"]})

    def test_banned_cards_are_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            p=create_deck(d,"Deck_Reference")
            cards={n:dict(c) for n,c in CARDS.items()}
            cards["Sol Ring"]["legalities"]={"commander":"banned"}
            with self.assertRaisesRegex(ValueError,"no longer legal"):
                detail_for_deck(p,cards)

    def test_front_land_detected_separately_from_modal_back(self):
        self.assertTrue(has_land_front(CARDS["Plains"]))
        self.assertFalse(has_land_back(CARDS["Plains"]))
        self.assertFalse(has_land_front(CARDS["Malakir Rebirth"]))
        self.assertTrue(has_land_back(CARDS["Malakir Rebirth"]))


if __name__=="__main__":
    unittest.main()
