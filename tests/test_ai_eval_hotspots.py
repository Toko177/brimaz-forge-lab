import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from audit_ai_eval_hotspots import inspect, classify_stack

GAME = {"pod": "aristo", "seed": 22, "status": "complete",
        "policy": "V10-observer", "winner_deck": "Other",
        "brimaz_seat": 3}
OPENING = (
    "AI_OPENING_V10: player=Ai(1)-Other hand=7 lands=3 cheapSpells=2 cardsToBottom=0\n")
TIMEOUT = (
    "AI_EVAL_TIMEOUT_V10: player=Ai(3)-Brimaz V3 globalTurn=18"
    " phase=MAIN1 elapsedMs=5018 timeoutSecs=5 listed=13"
    " considered=4 lastCandidate=Phyrexian Delver\n"
    "java.util.concurrent.TimeoutException\n"
    "AI eval thread at timeout:\n"
    "\tat forge.game.card.Card.updateStaticAbilities(Card.java:6967)\n"
    "\tat forge.ai.ComputerUtilCombat.canDestroyBlocker(ComputerUtilCombat.java:1919)\n"
    "\tat forge.ai.AiBlockController.getSafeBlockers(AiBlockController.java:107)\n"
)


class ForensicsTests(unittest.TestCase):
    def test_timeout_identifies_seat_and_actual_card(self):
        g = inspect(OPENING + TIMEOUT, GAME)
        self.assertEqual(g["events"][0]["seat"], 3)
        self.assertEqual(g["events"][0]["stalled_candidate"], "Phyrexian Delver")
        self.assertEqual(g["original_timeout_exceptions"], 1)

    def test_classify_nested_combat_cost_even_with_card_top_frame(self):
        g = inspect(OPENING + TIMEOUT, GAME)
        self.assertEqual(g["timeout_stacks"][0]["classification"], "deep_combat_and_block_prediction")

    def test_opening_hand_all_seats(self):
        g = inspect(OPENING + TIMEOUT, GAME)
        self.assertEqual(g["opening_hands"][0]["lands"], 3)
        self.assertEqual(g["opening_hands"][0]["seat"], 1)

    def test_disallow_telemetry_without_matching_timeout(self):
        with self.assertRaisesRegex(ValueError, "differs"):
            inspect(OPENING + TIMEOUT.replace("java.util.concurrent.TimeoutException\n", ""), GAME)

    def test_bad_hand_counts_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid V10 hand"):
            inspect(OPENING.replace("lands=3", "lands=8") + TIMEOUT, GAME)

    def test_no_opening_hand_rejected(self):
        with self.assertRaisesRegex(ValueError, "No V10 opening"):
            inspect(TIMEOUT, GAME)

    def test_legacy_v9_log_can_still_be_classified_without_v10_fields(self):
        g = inspect("java.util.concurrent.TimeoutException\n", {**GAME, "policy": "V9-mulligan"})
        self.assertEqual(len(g["events"]), 0)
        self.assertEqual(g["original_timeout_exceptions"], 1)


if __name__ == "__main__":
    unittest.main()
