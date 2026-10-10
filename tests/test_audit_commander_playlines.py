#!/usr/bin/env python3
"""Use authentic synthetic Forge action syntax to prevent fake play-by-play."""
from pathlib import Path
import sys,tempfile,unittest,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_commander_playlines import extract,aggregate,analyze

def sample(brimaz_cast=True,turn2=True):
    return "\n".join([
      "Simulation mode",
      "Turn: Turn 1 (Ai(2)-Opponent A)",
      "Land: Ai(2)-Opponent A played Swamp (12)",
      "Add To Stack: Ai(2)-Opponent A cast Sol Ring",
      "Turn: Turn 2 (Ai(1)-Deck_Candidate)",
      "Land: Ai(1)-Deck_Candidate played Plains (8)",
      "Add To Stack: Ai(1)-Deck_Candidate cast Sol Ring",
      "Turn: Turn 3 (Ai(3)-Opponent B)",
      "Add To Stack: Ai(1)-Deck_Candidate cast Deadly Dispute",
      "Turn: Turn 4 (Ai(4)-Opponent C)",
      "Add To Stack: Ai(4)-Opponent C cast Wrath of God",
      "Turn: Turn 5 (Ai(1)-Deck_Candidate)" if turn2 else "",
      "Add To Stack: Ai(1)-Deck_Candidate cast Brimaz, Blight of Oreskos" if brimaz_cast else "",
      "Turn: Turn 6 (Ai(2)-Opponent A)",
      "Add To Stack: Ai(1)-Deck_Candidate cast Priest of Gix",
      "Resolve Stack: Whenever you cast a Phyrexian creature or artifact creature spell, incubate X, where X is that spell's mana value. [Card: Priest of Gix (11), Activator: Ai(1)-Deck_Candidate]",
      "Resolve Stack: At the beginning of each end step, if a Phyrexian died under your control this turn, proliferate. [Phase: Ai(2)-Opponent A]",
      "Add To Stack: Ai(1)-Deck_Candidate activated Incubator Token",
      "Resolve Stack: Phyrexian Token (21) - Transform Phyrexian Token (21).",
      "Game Outcome: Ai(1)-Deck_Candidate has won because all opponents have lost",
      "Game Outcome: Ai(2)-Opponent A has lost because life total reached 0",
      "Game Outcome: Ai(3)-Opponent B has lost because life total reached 0",
      "Game Outcome: Ai(4)-Opponent C has lost because life total reached 0",
    ])+"\n"

class PlayByPlayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"actual.log"
        self.path.write_text(sample())
    def tearDown(self):self.tmp.cleanup()

    def test_counts_real_actions_by_actor_even_on_other_turn(self):
        p=extract(self.path)
        b=p["brimaz"]
        self.assertEqual(b["first_commander_cast_personal_turn"],2)
        self.assertEqual(b["creature_and_other_spell_casts"],4)
        self.assertEqual(b["incubate_triggers_resolved"],1)
        self.assertEqual(b["endstep_proliferate_triggers_resolved"],1)
        self.assertEqual(b["incubator_transforms_resolved"],1)
        self.assertEqual(p["all_player_actions_by_kind"]["2"]["land"],1)
        self.assertEqual(b["land_plays"],1)
        self.assertEqual(aggregate([p])["brimaz_wins"],1)

    def test_clock_censored_raw_winner_never_becomes_certified_win(self):
        import hashlib
        raw=self.path.read_bytes()
        manifest=[{"log":str(self.path),"log_sha256":hashlib.sha256(raw).hexdigest(),
                   "status":"clock_censored"}]
        (self.path.parent/"games.json").write_text(json.dumps(manifest))
        row=extract(self.path)
        stats=aggregate([row])
        self.assertEqual(stats["brimaz_raw_winner_labels_UNCERTIFIED"],1)
        self.assertEqual(stats["brimaz_raw_winner_labels_in_censored_games"],1)
        self.assertEqual(stats["clock_censored_games_by_manifest"],1)

    def test_tampered_game_manifest_fails_action_audit(self):
        (self.path.parent/"games.json").write_text(json.dumps([{
           "log":str(self.path),"log_sha256":"0"*64,"status":"complete"}]))
        with self.assertRaisesRegex(ValueError,"SHA256"):
            extract(self.path)

    def test_cast_timing_without_commander_is_explicit_null(self):
        self.path.write_text(sample(brimaz_cast=False))
        b=extract(self.path)["brimaz"]
        self.assertIsNone(b["first_commander_cast_personal_turn"])
        self.assertEqual(b["commander_cast_count"],0)

    def test_refuses_empty_logs_without_real_turns(self):
        self.path.write_text("Simulation mode\nGame Result: UNKNOWN\n")
        with self.assertRaisesRegex(ValueError,"No actual Forge"):
            extract(self.path)

    def test_duplicate_raw_logs_fail_no_pseudoreplication(self):
        p=self.path.parent/"dupe.log"
        p.write_bytes(self.path.read_bytes())
        with self.assertRaisesRegex(ValueError,"Duplicate original Forge"):
            analyze(self.path.parent,self.path.parent/"out.json")

    def test_action_chronology_and_original_line_numbers_preserved(self):
        p=extract(self.path)
        self.assertEqual(p["actions"][0]["kind"],"land")
        self.assertEqual(p["actions"][0]["global_turn"],1)
        self.assertEqual(p["actions"][-1]["kind"],"incubator_transform_resolved")
        self.assertTrue(all(x["line"]>0 for x in p["actions"]))

    def test_action_limit_refuses_lossy_pseudocomplete_audit(self):
        with self.assertRaisesRegex(ValueError,"Action buffer exhausted"):
            extract(self.path,max_events=2)

if __name__=="__main__":unittest.main()
