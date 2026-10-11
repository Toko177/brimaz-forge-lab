import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from audit_adaptive_ai_budget import analyze

GAME = {"pod":"aristo", "seed":3, "status":"complete", "winner_deck":"Other",
        "brimaz_win":False, "policy":"V11-adaptive"}
T0 = "java.util.concurrent.TimeoutException\n"
A1 = "AI_ADAPTIVE_BUDGET_V11: previousSeconds=5 currentSeconds=10 appliedTo=ALL_FOUR_SEATS\n"
A2 = "AI_ADAPTIVE_BUDGET_V11: previousSeconds=10 currentSeconds=15 appliedTo=ALL_FOUR_SEATS\n"


class AdaptiveBudgetTests(unittest.TestCase):
    def test_v13_all_seat_budget_policy_after_one_timeout(self):
        log = T0 + "AI_ADAPTIVE_BUDGET_V13: previousSeconds=5 currentSeconds=10 appliedTo=ALL_FOUR_SEATS\n"
        result = analyze(log, {**GAME, "policy": "V13-incubate-adaptive"})
        self.assertEqual(result["final_ai_timeout_seconds"], 10)
        self.assertEqual(result["adaptations"][0]["instrumentation_version"], 13)

    def test_v13_rejects_accidental_v11_only_telemetry(self):
        with self.assertRaisesRegex(ValueError, "does not match AI policy"):
            analyze(T0 + A1, {**GAME, "policy": "V13-incubate-adaptive"})

    def test_no_timeout_stays_at_five(self):
        self.assertEqual(analyze("", GAME)["final_ai_timeout_seconds"], 5)

    def test_single_timeout_increases_shared_budget(self):
        r = analyze(T0+A1, GAME)
        self.assertEqual(r["final_ai_timeout_seconds"], 10)

    def test_second_timeout_may_raise_to_fifteen(self):
        r = analyze(T0+A1+T0+A2, GAME)
        self.assertEqual(r["final_ai_timeout_seconds"], 15)

    def test_no_budget_increase_without_real_timeout(self):
        with self.assertRaisesRegex(ValueError, "without original"):
            analyze(A1, GAME)

    def test_no_repeat_or_regression_in_budget(self):
        with self.assertRaisesRegex(ValueError, "monotone"):
            analyze(T0+A1+T0+A1, GAME)

    def test_never_overshoot_fifteen_seconds(self):
        with self.assertRaisesRegex(ValueError, "monotone"):
            analyze(T0+A1+T0+"AI_ADAPTIVE_BUDGET_V11: previousSeconds=10 currentSeconds=20 appliedTo=ALL_FOUR_SEATS\n", GAME)

    def test_timeout_without_adaptation_detected(self):
        with self.assertRaisesRegex(ValueError, "without shared"):
            analyze(T0, GAME)


if __name__ == "__main__":
    unittest.main()
