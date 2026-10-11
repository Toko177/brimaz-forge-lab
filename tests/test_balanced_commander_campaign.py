import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from audit_balanced_commander_campaign import summarize,wilson

PODS={"aristo":["Brimaz_V3","Radha","Tazri","Zimone"],
      "artifact":["Brimaz_V3","Lathril","Urza","Amalia"]}

def inputs(count=1):
    ms=[];cs=[]
    for pod,decks in PODS.items():
        for rotation in range(4):
            seats=decks[rotation:]+decks[:rotation]
            for repeat in range(count):
                seed=22000000+100000*list(PODS).index(pod)+10000*rotation+repeat
                seat=seats.index("Brimaz_V3")+1
                g={"pod":pod,"seed":seed,"rotation":rotation,"brimaz_seat":seat,
                   "seats":seats,"policy":"V12-incubate","status":"complete",
                   "winner_deck":"Brimaz_V3" if repeat==0 else next(d for d in seats if d!="Brimaz_V3"),
                   "brimaz_win":repeat==0}
                c={k:g[k] for k in ("pod","seed","brimaz_seat","policy","status","winner_deck","brimaz_win")}
                c.update(engine_natural_and_consistent=True,legal_deck_gate=True,
                         rejection_reasons=[],ai_warning_free=True,
                         ai_quality_signatures={"evaluation_timeouts":0,"invalid_attack_fallbacks":0,
                                                "incubate_handler_warnings":0,"decision_thread_timeout_samples":0})
                ms.append(g);cs.append(c)
    return ms,{"games":cs}


class CampaignAuditTests(unittest.TestCase):
    def test_full_balanced_two_pod_four_seat_matrix(self):
        ms,cs=inputs(2)
        r=summarize(ms,cs,games_per_rotation=2)
        self.assertEqual(r["summary"]["scheduled"],16)
        self.assertEqual(r["summary"]["certified"],16)
        self.assertEqual(r["summary"]["wins"],8)
        self.assertEqual(r["summary"]["groups_pod_rotation"],8)
        self.assertEqual(r["by_brimaz_seat"]["1"]["scheduled"],4)

    def test_wilson_interval_is_wide_for_tiny_sample(self):
        self.assertEqual(wilson(0,0),None)
        self.assertGreater(wilson(1,4)[1],0.5)
        self.assertLess(wilson(1,4)[0],0.1)

    def test_missing_games_fail_before_claiming_winrate(self):
        ms,cs=inputs()
        with self.assertRaisesRegex(ValueError,"expected"):
            summarize(ms[:-1],cs,games_per_rotation=1)

    def test_duplicate_seed_cannot_be_passed_off_as_independent(self):
        ms,cs=inputs()
        ms[1]["seed"]=ms[0]["seed"]
        with self.assertRaisesRegex(ValueError,"Duplicated global seed"):
            summarize(ms,cs,games_per_rotation=1)

    def test_invalid_natural_result_cannot_be_counted_as_win(self):
        ms,cs=inputs()
        cs["games"][0]["engine_natural_and_consistent"]=False
        cs["games"][0]["rejection_reasons"]=["Illegal game"]
        r=summarize(ms,cs,games_per_rotation=1)
        self.assertEqual(r["summary"]["certified"],7)
        self.assertEqual(r["summary"]["wins"],7)
        self.assertEqual(r["summary"]["censored_or_rejected"],1)

    def test_warning_free_win_is_distinct_from_legal_win(self):
        ms,cs=inputs()
        cs["games"][0]["ai_warning_free"]=False
        cs["games"][0]["ai_quality_signatures"]["evaluation_timeouts"]=2
        r=summarize(ms,cs,games_per_rotation=1)
        self.assertEqual(r["summary"]["wins"],8)
        self.assertEqual(r["summary"]["warning_free_wins"],7)

    def test_wrong_commander_seat_rejected(self):
        ms,cs=inputs()
        ms[0]["brimaz_seat"]=4
        with self.assertRaisesRegex(ValueError,"seat mismatch"):
            summarize(ms,cs,games_per_rotation=1)

    def test_mixed_policy_rejected(self):
        ms,cs=inputs()
        ms[0]["policy"]="Other"
        with self.assertRaisesRegex(ValueError,"Mixed AI variant"):
            summarize(ms,cs,games_per_rotation=1)

    def test_illegal_natural_certificate_is_rejected(self):
        ms,cs=inputs()
        cs["games"][0]["legal_deck_gate"]=False
        with self.assertRaisesRegex(ValueError,"illegal/censored"):
            summarize(ms,cs,games_per_rotation=1)

    def test_censored_game_keeps_denominator_honest(self):
        ms,cs=inputs()
        ms[0].update(status="clock_censored",winner_deck=None,brimaz_win=None)
        cs["games"][0].update(status="clock_censored",winner_deck=None,brimaz_win=None,
                             engine_natural_and_consistent=False,rejection_reasons=["clock cutoff"])
        r=summarize(ms,cs,games_per_rotation=1)
        self.assertEqual(r["summary"]["scheduled"],8)
        self.assertEqual(r["summary"]["certified"],7)
        self.assertEqual(r["summary"]["censored_or_rejected"],1)


if __name__=="__main__":
    unittest.main()
