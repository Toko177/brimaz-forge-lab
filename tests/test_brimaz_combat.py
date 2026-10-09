import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from audit_brimaz_combat import inspect

GAME={"pod":"artifact","seed":20610001,"rotation":0,"brimaz_seat":1,
      "policy":"V12-incubate","status":"complete","winner_deck":"Brimaz_V3",
      "brimaz_win":True}
LOG="""Turn: Turn 1 (Ai(1)-Brimaz V3)
Combat: Ai(1)-Brimaz V3 assigned Phyrexian Token (15) and Brimaz, Blight of Oreskos (20) to attack Ai(4)-EDH Amalia.
Damage: Phyrexian Token (15) deals 8 combat damage to Ai(4)-EDH Amalia.
Damage: Brimaz, Blight of Oreskos (20) deals 4 combat damage to Ai(4)-EDH Amalia.
Damage: Other Token (500) deals 6 combat damage to Ai(4)-EDH Amalia.
Turn: Turn 2 (Ai(2)-Lathril)
Damage: Brimaz, Blight of Oreskos (20) deals 2 combat damage to Ai(4)-EDH Amalia.
Game Outcome: Ai(1)-Brimaz V3 has won because all opponents have lost
"""


class BrimazCombatTests(unittest.TestCase):
    def test_only_direct_combat_from_same_turn_declared_sources(self):
        r=inspect(LOG,GAME)
        self.assertEqual(r["damage_total_attributable_to_declared_attackers"],12)
        self.assertEqual(r["matched_combat_damage_events"],2)

    def test_other_players_damage_never_imputed(self):
        r=inspect(LOG,GAME)
        self.assertEqual(r["damage_by_brimaz_declared_attackers_to_opponents"],{4:12})

    def test_phyrexian_token_attack_count(self):
        r=inspect(LOG,GAME)
        self.assertEqual(r["identified_phyrexian_attackers"],1)
        self.assertEqual(r["identified_unique_attackers"],2)

    def test_natural_win_does_not_claim_those_attackers_killed_opponents(self):
        r=inspect(LOG,GAME)
        self.assertTrue(r["brimaz_natural_win"])
        self.assertIn("not a full life-loss causal trace",r["limitation"].lower())

    def test_censored_game_never_marked_a_win(self):
        g={**GAME,"status":"clock_censored"}
        self.assertFalse(inspect(LOG,g)["brimaz_natural_win"])


if __name__=="__main__":
    unittest.main()
