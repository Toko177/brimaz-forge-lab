import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from compare_pacing_experiments import compare

def game(policy, lands, winner="A"):
    return {"pod": "artifact", "seed": 123, "policy": policy, "status": "complete",
        "winner_deck": winner, "brimaz_first_cast_on_own_turn": 4 if lands > 3 else None,
        "brimaz_land_drops_by_own_turn": {"8": lands}, "brimaz_own_turns": 8}


class CompareExperimentsTests(unittest.TestCase):
    def test_mana_delta_requires_identically_paired_pods_and_seed(self):
        r = compare({"games": [game("V8", 3)]},
                    {"games": [game("V9", 6)]},
                    {"games": [{"pod": "artifact", "seed": 123, "free_overrides": 1}]})
        self.assertEqual(r["summary"]["better_land_development_in_pairs"], 1)
        self.assertTrue(r["games"][0]["free_mulligan_override_applied"])
        self.assertIn("cannot be attributed", r["summary"]["no_causal_inference"])

    def test_unmatched_seed_rejected(self):
        with self.assertRaisesRegex(ValueError, "Pods/seeds differ"):
            compare({"games": [game("V8", 3)]},
                    {"games": [{**game("V9", 6), "seed": 124}]},
                    {"games": [{"pod": "artifact", "seed": 124, "free_overrides": 1}]})

    def test_duplicate_seeds_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            compare({"games": [game("V8", 3), game("V8", 3)]},
                    {"games": [game("V9", 6)]},
                    {"games": [{"pod": "artifact", "seed": 123, "free_overrides": 1}]})

    def test_identical_policy_rejected(self):
        with self.assertRaisesRegex(ValueError, "identical"):
            compare({"games": [game("V8", 3)]},
                    {"games": [game("V8", 6)]},
                    {"games": [{"pod": "artifact", "seed": 123, "free_overrides": 1}]})


if __name__ == "__main__":
    unittest.main()
