#!/usr/bin/env python3
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from audit_matched_replay import analyze, events_from_transcript

GAME = {
    "seed": 42, "pod": "aristo", "rotation": 3, "brimaz_seat": 2,
    "seats": ["A", "Brimaz_V3", "C", "D"], "profiles": ["Default"] * 4,
    "clock_seconds": 360, "status": "complete", "winner_deck": "Brimaz_V3",
    "game_milliseconds": 100000,
}
LOG = """Turn: Turn 1 (Ai(1)-A)
Add To Stack: Ai(1)-A cast Arcane Signet
Turn: Turn 2 (Ai(2)-Brimaz V3)
Add To Stack: Ai(2)-Brimaz V3 cast Norn's Inquisitor
Game Result: Game 1 ended in 100000 ms. Ai(2)-Brimaz V3 has won!
"""


class ReproducibilityTests(unittest.TestCase):
    def test_identical_replay_is_stable(self):
        d = analyze(GAME, LOG, GAME, LOG)
        self.assertTrue(d["outcome_reproduced"])
        self.assertTrue(d["event_sequence_identical"])

    def test_divergent_event_is_detected_by_turn(self):
        new = LOG.replace("Norn's Inquisitor", "Orzhov Signet")
        d = analyze(GAME, LOG, {**GAME, "winner_deck": "C"}, new)
        self.assertFalse(d["outcome_reproduced"])
        self.assertEqual(d["identical_event_prefix"], 1)
        self.assertEqual(d["first_divergence_reference"]["turn"], 2)
        self.assertIn("Orzhov Signet", d["first_divergence_replay"]["line"])

    def test_unmatched_seed_rejected(self):
        with self.assertRaisesRegex(ValueError, "seed"):
            analyze(GAME, LOG, {**GAME, "seed": 43}, LOG)

    def test_changed_clock_is_not_same_as_changed_seed(self):
        d = analyze(GAME, LOG, {**GAME, "clock_seconds": 900}, LOG)
        self.assertTrue(d["identical_inputs_verified"])
        self.assertEqual(d["clock_seconds"], [360, 900])

    def test_game_events_keep_actual_turn(self):
        self.assertEqual([x["turn"] for x in events_from_transcript(LOG)], [1, 2])


if __name__ == "__main__":
    unittest.main()
