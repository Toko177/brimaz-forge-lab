import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from audit_edh_pacing import analyze

GAME = {
    "seats": ["Opponent A", "Opponent B", "Brimaz_V3", "Opponent C"],
    "brimaz_seat": 3,
    "status": "complete",
    "seed": 99,
    "winner_deck": "Opponent A",
}
LOG = """Turn: Turn 1 (Ai(1)-A)
Land: Ai(1)-A played Island (122)
Turn: Turn 2 (Ai(2)-B)
Land: Ai(2)-B played Forest (123)
Turn: Turn 3 (Ai(3)-Brimaz V3)
Land: Ai(3)-Brimaz V3 played Plains (124)
Add To Stack: Ai(3)-Brimaz V3 cast Sol Ring
Turn: Turn 4 (Ai(4)-C)
Turn: Turn 5 (Ai(1)-A)
Turn: Turn 6 (Ai(2)-B)
Turn: Turn 7 (Ai(3)-Brimaz V3)
Land: Ai(3)-Brimaz V3 played Swamp (125)
Add To Stack: Ai(3)-Brimaz V3 cast Brimaz, Blight of Oreskos
Turn: Turn 8 (Ai(4)-C)
"""


class PacingTests(unittest.TestCase):
    def test_global_eight_is_two_turns_per_player(self):
        r = analyze(LOG, GAME)
        self.assertEqual(r["global_turn_last"], 8)
        self.assertEqual(r["actual_player_turns"], {"1": 2, "2": 2, "3": 2, "4": 2})
        self.assertEqual(r["longest_observed_player_turn_count"], 2)

    def test_brimaz_first_cast_is_second_own_turn_not_global_seven(self):
        r = analyze(LOG, GAME)
        self.assertEqual(r["brimaz_first_cast_on_own_turn"], 2)
        self.assertEqual(r["brimaz_first_cast_global_turn"], 7)
        self.assertEqual(r["brimaz_lands_played_before_first_cast"], 2)
        self.assertEqual(r["brimaz_land_drops_by_own_turn"]["4"], 2)

    def test_missing_commander_cast_is_none_not_zero(self):
        r = analyze(LOG.replace("Add To Stack: Ai(3)-Brimaz V3 cast Brimaz, Blight of Oreskos", ""), GAME)
        self.assertIsNone(r["brimaz_first_cast_on_own_turn"])

    def test_combat_actions_not_confused_with_turns(self):
        r = analyze(LOG + "Combat: Ai(3)-Brimaz V3 declared attackers\n"
                        + "Damage: Ai(3)-Brimaz V3 dealt combat damage\n", GAME)
        self.assertEqual(r["total_combat_log_entries"], 1)
        self.assertEqual(r["total_damage_log_entries"], 1)
        self.assertEqual(r["global_turn_last"], 8)

    def test_manifest_seat_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "seat"):
            analyze(LOG, {**GAME, "brimaz_seat": 2})


if __name__ == "__main__":
    unittest.main()
