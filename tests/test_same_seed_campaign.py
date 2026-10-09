import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from audit_same_seed_campaign import compare_campaigns

RAW="Turn: Turn 1 (Ai(1)-A)\nLand: Ai(1)-A played Plains (4)\n"
A={"pod":"aristo","rotation":0,"repeat":0,"seed":13,"policy":"V12-incubate",
   "clock_seconds":360,"seats":["Brimaz_V3","A","B","C"],
   "profiles":["Default"]*4,"brimaz_seat":1,"status":"complete",
   "winner_deck":"Brimaz_V3"}
KEY=("aristo",0,0,13)


class ReplayCampaignTests(unittest.TestCase):
    def test_identical_real_trace_reported_as_same_events_and_winner(self):
        d=compare_campaigns({KEY:(A,RAW)},{KEY:(A.copy(),RAW)},expected=1)
        self.assertEqual(d["summary"]["seed_pairs"],1)
        self.assertEqual(d["summary"]["both_natural_same_winner"],1)
        self.assertEqual(d["summary"]["identical_event_sequences"],1)

    def test_different_winner_not_passed_as_reproduced(self):
        b={**A,"winner_deck":"A"}
        d=compare_campaigns({KEY:(A,RAW)},{KEY:(b,RAW.replace("Plains","Island"))},expected=1)
        self.assertEqual(d["summary"]["both_natural_different_winner"],1)
        self.assertEqual(d["summary"]["changed_event_sequences"],1)

    def test_same_seed_not_counted_twice_as_independent_wins(self):
        d=compare_campaigns({KEY:(A,RAW)},{KEY:(A,RAW)},expected=1)
        self.assertIn("not 64",d["summary"]["not_independent_samples"])

    def test_missing_one_of_pods_and_seeds_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"different pods"):
            compare_campaigns({KEY:(A,RAW)},{("artifact",0,0,13):({**A,"pod":"artifact"},RAW)},expected=1)

    def test_unbalanced_campaign_rejected(self):
        with self.assertRaisesRegex(ValueError,"Need all"):
            compare_campaigns({KEY:(A,RAW)},{KEY:(A,RAW)},expected=32)

    def test_changed_deck_profile_rejected(self):
        b={**A,"profiles":["Reckless"]*4}
        with self.assertRaisesRegex(ValueError,"same profiles"):
            compare_campaigns({KEY:(A,RAW)},{KEY:(b,RAW)},expected=1)

    def test_censored_is_never_counted_as_natural_winner(self):
        b={**A,"status":"clock_censored","winner_deck":None}
        d=compare_campaigns({KEY:(A,RAW)},{KEY:(b,RAW)},expected=1)
        self.assertEqual(d["summary"]["both_natural"],0)
        self.assertEqual(d["summary"]["one_or_both_censored_or_invalid"],1)


if __name__=="__main__":
    unittest.main()
