#!/usr/bin/env python3
"""No Forge download needed: fail-closed regression fixtures for evidence gate."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from forge_result_evidence import verify_result_evidence, inspect_ai_quality_signatures, describe_outcome_modes
from analyze_ai_gameplay import audit_game

SEATS = ["Brimaz_V3", "Kaal_9594008", "Kaal_10347090", "Kaal_21930525"]
GAME = {
    "seats": SEATS, "brimaz_seat": 1, "status": "complete",
    "winner_seat": 1, "winner_deck": "Brimaz_V3",
    "brimaz_win": True, "process_exit": 0,
    "clock_seconds": 360, "game_milliseconds": 123456,
}
RAW = """Ai(1)-Brimaz V3 vs Ai(2)-Radha vs Ai(3)-Tazri vs Ai(4)-Zimone - one game of Commander seed 42
Turn: Turn 1 (Ai(1)-Brimaz V3)
Phase: Ai(1)-Brimaz V3's Main phase, precombat
Add To Stack: Ai(1)-Brimaz V3 cast Krark-Clan Ironworks
Turn: Turn 2 (Ai(2)-Radha)
Phase: Ai(2)-Radha's End step
Add To Stack: Ai(1)-Brimaz V3 triggered Brimaz, Blight of Oreskos
Game Outcome: Ai(1)-Brimaz V3 has won because all opponents have lost
Game Outcome: Ai(2)-Radha has lost because life total reached 0
Game Outcome: Ai(3)-Tazri has lost because life total reached 0
Game Outcome: Ai(4)-Zimone has lost because life total reached 0
Game Result: Game 1 ended in 123456 ms. Ai(1)-Brimaz V3 has won!
"""


class TranscriptEvidenceTests(unittest.TestCase):
    def check(self, raw=RAW, **mod):
        return verify_result_evidence(raw, {**GAME, **mod}, SEATS)

    def test_valid_four_outcome_result(self):
        self.assertEqual(self.check(), [])

    def test_library_deckout_loss_is_valid_fourth_player_elimination(self):
        # Actual Forge 2.0.15 prints 'lost trying to draw cards from empty library'
        # rather than 'lost because ...'. This must NOT reject a real win.
        raw = RAW.replace(
            "Game Outcome: Ai(3)-Tazri has lost because life total reached 0",
            "Game Outcome: Ai(3)-Tazri has lost trying to draw cards from empty library")
        self.assertEqual(self.check(raw), [])

    def test_missing_library_deckout_elimination_is_still_rejected(self):
        raw = RAW.replace(
            "Game Outcome: Ai(3)-Tazri has lost because life total reached 0\n", "")
        self.assertTrue(any("four individual Game Outcome" in issue for issue in self.check(raw)))

    def test_distinguish_opponent_deckout_from_lethal_damage(self):
        raw = RAW.replace("Ai(3)-Tazri has lost because life total reached 0",
                          "Ai(3)-Tazri has lost trying to draw cards from empty library")
        outcomes = describe_outcome_modes(raw)
        self.assertEqual(len(outcomes), 4)
        self.assertEqual({x["mode"] for x in outcomes if x["seat"] == 3}, {"library_depletion"})
        self.assertEqual({x["mode"] for x in outcomes if x["seat"] == 2}, {"life_total_zero"})
        self.assertEqual({x["mode"] for x in outcomes if x["seat"] == 1}, {"survivor_won"})

    def test_commander_damage_21_is_valid_four_player_elimination(self):
        raw = RAW.replace("Ai(3)-Tazri has lost because life total reached 0",
                          "Ai(3)-Tazri has lost due to accumulation of 21 damage from generals")
        self.assertEqual(self.check(raw), [])
        mode = [x["mode"] for x in describe_outcome_modes(raw) if x["seat"] == 3]
        self.assertEqual(mode, ["commander_damage_21"])

    def test_unsupported_due_to_reason_does_not_weaken_result_certification(self):
        raw = RAW.replace("Ai(3)-Tazri has lost because life total reached 0",
                          "Ai(3)-Tazri has lost due to an unknown invented rule")
        self.assertTrue(any("Unknown or unsupported due-to elimination" in x for x in self.check(raw)))

    def test_two_commander_damage_losses_and_life_loss_are_four_valid_records(self):
        raw = RAW.replace("Ai(2)-Radha has lost because life total reached 0",
                          "Ai(2)-Radha has lost due to accumulation of 21 damage from generals")
        raw = raw.replace("Ai(4)-Zimone has lost because life total reached 0",
                          "Ai(4)-Zimone has lost due to accumulation of 21 damage from generals")
        self.assertEqual(self.check(raw), [])

    def test_unrecognized_loss_reason_is_not_silently_accepted(self):
        raw = RAW.replace("Ai(3)-Tazri has lost because life total reached 0",
                          "Ai(3)-Tazri has lost for unknown reasons")
        self.assertTrue(any("four individual Game Outcome" in issue for issue in self.check(raw)))

    def test_win_must_still_have_legal_winning_reason(self):
        raw = RAW.replace("Ai(1)-Brimaz V3 has won because all opponents have lost",
                          "Ai(1)-Brimaz V3 has won trying to draw cards from empty library")
        self.assertTrue(any("one won outcome" in issue for issue in self.check(raw)))

    def test_missing_eliminations_are_rejected(self):
        self.assertIn("Expected four individual Game Outcome entries, found 3",
                      self.check(RAW.replace(
                          "Game Outcome: Ai(4)-Zimone has lost because life total reached 0\n", "")))

    def test_double_winner_is_rejected(self):
        raw = RAW.replace("Ai(4)-Zimone has lost because life total reached 0",
                          "Ai(4)-Zimone has won because alternate winning condition")
        self.assertTrue(any("one won outcome" in x for x in self.check(raw)))

    def test_outcome_name_mismatch(self):
        raw = RAW.replace("Ai(3)-Tazri has lost", "Ai(3)-Other name has lost")
        self.assertTrue(any("seat name" in x for x in self.check(raw)))

    def test_manifest_winner_mismatch(self):
        self.assertTrue(any("winner seat" in x for x in self.check(winner_seat=2)))

    def test_too_close_to_360_second_cutoff(self):
        raw = RAW.replace("123456 ms", "359000 ms")
        self.assertTrue(any("cutoff" in x for x in self.check(raw, game_milliseconds=359000)))

    def test_game_clock_is_not_hard_coded_to_360(self):
        raw = RAW.replace("123456 ms", "412000 ms")
        self.assertEqual(self.check(raw, game_milliseconds=412000, clock_seconds=600), [])

    def test_custom_clock_never_invents_winner(self):
        raw = RAW.replace("123456 ms", "59900 ms")
        self.assertTrue(any("cutoff" in x for x in self.check(raw, clock_seconds=60,
                                                              game_milliseconds=59900)))

    def test_ai_timeout_quality_flag_does_not_forge_an_outcome(self):
        raw = (RAW + "java.util.concurrent.TimeoutException\n"
               + "AI Attack declaration invalid, defaulting to: {}\n")
        flags = inspect_ai_quality_signatures(raw)
        self.assertEqual(flags["evaluation_timeouts"], 1)
        self.assertEqual(flags["invalid_attack_fallbacks"], 1)
        self.assertEqual(self.check(raw), [])

    def test_ai_incubate_warning_is_quality_not_game_legality(self):
        raw = RAW + "No AI assigned for API: Incubate\n"
        self.assertEqual(inspect_ai_quality_signatures(raw)["incubate_handler_warnings"], 1)
        self.assertEqual(self.check(raw), [])

    def test_forced_draw_rejected(self):
        self.assertTrue(any("artificially" in x for x in
                            self.check(RAW + "Stopping slow match as draw\n")))

    def test_legacy_clock_without_metadata_is_360(self):
        legacy = {k: v for k, v in GAME.items() if k != "clock_seconds"}
        self.assertEqual(verify_result_evidence(RAW, legacy, SEATS), [])


class AiAuditTests(unittest.TestCase):
    def test_counts_resolved_stack_actions_only(self):
        data = audit_game(GAME, RAW)
        self.assertEqual(data["actions"]["cast|Krark-Clan Ironworks"], 1)
        self.assertEqual(data["actions"]["brimaz_end_step_triggers"], 1)
        self.assertEqual(data["actions"]["brimaz_opponent_end_step_triggers"], 1)
        self.assertEqual(data["cast_but_never_activated_in_game"], [])

    def test_opponent_turn_sacrifice_timing(self):
        raw = RAW.replace("Phase: Ai(2)-Radha's End step",
                          "Turn: Turn 2 (Ai(2)-Radha)\nPhase: Ai(2)-Radha's Main phase, postcombat\n"
                          "Add To Stack: Ai(1)-Brimaz V3 activated Spawning Pit\n"
                          "Phase: Ai(2)-Radha's End step")
        data = audit_game(GAME, raw)
        self.assertEqual(data["actions"]["outlet_activations_opponent_before_end_step"], 1)
        self.assertEqual(data["actions"]["brimaz_opponent_end_step_triggers"], 1)


if __name__ == "__main__":
    unittest.main()
