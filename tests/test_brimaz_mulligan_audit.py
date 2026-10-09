import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from audit_brimaz_mulligan import inspect

GAME = {
    "pod": "aristo", "seed": 12, "brimaz_seat": 3,
    "policy": "V9-mulligan", "status": "complete",
    "winner_deck": "Other", "brimaz_win": False,
}
OVERRIDE = (
    "BRIMAZ_MULLIGAN: V9 hand=7 actualLands=2 potentialLandDrops=2"
    " cheapRamp=0 cheapDraw=0 expensive=3 cardsToReturn=0"
    " stockKeep=true overrideFreeMulligan=true\n"
)
MULLIGAN = ("Mulligan: Ai(3)-Brimaz V3 has mulliganed down to 7 cards.\n"
            "Mulligan: Ai(3)-Brimaz V3 has kept a hand of 7 cards\n")


class V9MulliganAuditTests(unittest.TestCase):
    def test_genuine_opening_hand_override(self):
        a = inspect(OVERRIDE + MULLIGAN, GAME)
        self.assertEqual(a["free_overrides"], 1)
        self.assertEqual(a["kept_hand_size"], 7)

    def test_paid_mulligan_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "documented gate"):
            inspect(OVERRIDE.replace("cardsToReturn=0", "cardsToReturn=1") + MULLIGAN, GAME)

    def test_no_mulligan_telemetry_is_rejected_for_v9(self):
        with self.assertRaisesRegex(ValueError, "No Brimaz"):
            inspect(MULLIGAN, GAME)

    def test_other_seat_mulligan_is_not_blamed_on_brimaz(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            inspect(OVERRIDE + MULLIGAN.replace("Ai(3)-", "Ai(1)-"), GAME)

    def test_two_modal_lands_potential_total_must_not_exceed_hand(self):
        with self.assertRaisesRegex(ValueError, "Invalid"):
            inspect(OVERRIDE.replace("potentialLandDrops=2", "potentialLandDrops=8") + MULLIGAN, GAME)


if __name__ == "__main__":
    unittest.main()
