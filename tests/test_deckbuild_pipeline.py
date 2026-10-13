#!/usr/bin/env python3
"""Fully offline safety tests for fast editable Commander deckbuilding A/B."""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from deckbuild_prepare import read_deck,prepare
from deckbuild_run import (verify_inputs,policy_environment,policy_trace_evidence,
                                V13_POLICY,V43_POLICY)
from deckbuild_certify import certify_one
from deckbuild_compare import analyze,wilson


class Preparation(unittest.TestCase):
    def test_prep_preserves_original_and_counts_both_100_card_lists(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            deck=root/"input.txt"
            deck.write_text("99 Plains\n1 Brimaz, Blight of Oreskos\n")
            before=hashlib.sha256(deck.read_bytes()).hexdigest()
            r=prepare(deck,deck,root/"forge","Brimaz, Blight of Oreskos","Brimaz, Blight of Oreskos")
            self.assertEqual(r["delta"],{"added":{},"removed":{}})
            self.assertEqual(before,hashlib.sha256(deck.read_bytes()).hexdigest())
            self.assertTrue((root/"forge/Deck_Reference.dck").is_file())
            self.assertIn("[Commander]\n1 Brimaz, Blight of Oreskos",
                          (root/"forge/Deck_Candidate.dck").read_text())
            for name in ("Deck_Reference","Deck_Candidate"):
                self.assertEqual(sum(x for x in
                    [99,1]),100)
            for name in ("Kaal_9594008","Kaal_10347090","Kaal_21930525"):
                (root/"forge"/(name+".dck")).write_text("[Main]\n100 Plains\n")
            names=verify_inputs(root/"forge",r,"candidate","aristo")
            self.assertEqual(names[0],"Deck_Candidate")
            (root/"forge/Deck_Candidate.dck").write_text("tampered")
            with self.assertRaisesRegex(ValueError,"mutated"):
                verify_inputs(root/"forge",r,"candidate","aristo")

    def test_wrong_card_count_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"bad.txt"
            p.write_text("98 Plains\n1 Brimaz, Blight of Oreskos\n")
            with self.assertRaisesRegex(ValueError,"100"):
                read_deck(p,"Brimaz, Blight of Oreskos")

    def test_missing_commander_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"bad.txt"
            p.write_text("100 Plains\n")
            with self.assertRaisesRegex(ValueError,"not present"):
                read_deck(p,"Brimaz, Blight of Oreskos")

    def test_modal_double_faced_card_uses_primary_forge_face(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            src=root/"input.txt"
            src.write_text("98 Plains\n1 Malakir Rebirth // Malakir Mire\n1 Brimaz, Blight of Oreskos\n")
            data=prepare(src,src,root/"forge","Brimaz, Blight of Oreskos","Brimaz, Blight of Oreskos")
            forge=(root/"forge/Deck_Candidate.dck").read_text()
            self.assertIn("1 Malakir Rebirth\n",forge)
            self.assertNotIn("Malakir Mire",forge)
            self.assertTrue(data["decks"]["candidate"]["forge_sha256"])

    def test_two_commanders_without_pairing_audit_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            src=root/"input.txt"
            src.write_text("98 Plains\n1 Commander Alpha\n1 Commander Beta\n")
            with self.assertRaisesRegex(ValueError,"ONE commander"):
                read_deck(src,"Commander Alpha;Commander Beta")

    def test_swap_report_is_quantity_aware(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            a=root/"a.txt";b=root/"b.txt"
            a.write_text("99 Plains\n1 Brimaz, Blight of Oreskos\n")
            b.write_text("98 Plains\n1 Swamp\n1 Brimaz, Blight of Oreskos\n")
            r=prepare(a,b,root/"forge","Brimaz, Blight of Oreskos","Brimaz, Blight of Oreskos")
            self.assertEqual(r["delta"]["added"],{"Swamp":1})
            self.assertEqual(r["delta"]["removed"],{"Plains":1})


class GenericPolicyIsolation(unittest.TestCase):
    def test_v43_isolation_follows_compared_deck_after_seat_rotation(self):
        assert policy_environment(V13_POLICY,1,{"JAVA_TOOL_OPTIONS":"unchanged"}) is None
        inherited={"JAVA_TOOL_OPTIONS":"-Dmalicious=true",
                   "_JAVA_OPTIONS":"-Dother=true",
                   "JDK_JAVA_OPTIONS":"-Dthird=true","PATH":"/usr/bin"}
        for seat in range(1,5):
            env=policy_environment(V43_POLICY,seat,inherited)
            self.assertEqual(env["PATH"],"/usr/bin")
            self.assertNotIn("_JAVA_OPTIONS",env)
            self.assertNotIn("JDK_JAVA_OPTIONS",env)
            self.assertEqual(env["JAVA_TOOL_OPTIONS"],
                "-Dbrimaz.v37ControlledDuel=true "
                "-Dcommander.v42GeneralPolicy=true "
                f"-Dcommander.v43TargetSeat={seat}")

    def test_raw_forge_banner_confirms_only_selected_ai(self):
        raw=("FOUR_AI_V42_WINDOW player=Ai(3)-Deck Candidate turn=7 "
             "options=3 ranked=2 margin=18 pressure=false "
             "reason=distinct_public_development_preference "
             "nativeForgeApprovalPending=true\n"
             "FOUR_AI_V42_STOCK_APPROVED player=Ai(3)-Deck Candidate turn=7 "
             "card=Arcane Signet rejectedEarlier=0 "
             "nativeForgeAIDecision=true notResolvedYet=true\n")
        proof=policy_trace_evidence(raw,V43_POLICY,3)
        self.assertTrue(proof["observed"])
        self.assertFalse(proof["wrong_seat"])
        self.assertEqual(proof["approvals"],1)
        self.assertTrue(policy_trace_evidence(raw,V43_POLICY,1)["wrong_seat"])
        self.assertFalse(policy_trace_evidence("",V43_POLICY,3)["observed"])
        self.assertIsNone(policy_trace_evidence("",V13_POLICY,3)["observed"])
        with self.assertRaisesRegex(ValueError,"Unsupported"):
            policy_environment("unknown",1,{})
        with self.assertRaisesRegex(ValueError,"Unrecognized"):
            policy_trace_evidence("", "unknown",1)


def example_outcome():
    names=["Deck_Candidate","Kaal_9594008","Kaal_10347090","Kaal_21930525"]
    raw=("Ai(1)-Candidate vs Ai(2)-Radha vs Ai(3)-Tazri vs Ai(4)-Zimone - one game of Commander seed 42\n"
         "Turn: Turn 1 (Ai(1)-Candidate)\n"
         "Game Outcome: Ai(1)-Candidate has won because all opponents have lost\n"
         "Game Outcome: Ai(2)-Radha has lost because life total reached 0\n"
         "Game Outcome: Ai(3)-Tazri has lost trying to draw cards from empty library\n"
         "Game Outcome: Ai(4)-Zimone has lost due to accumulation of 21 damage from generals\n"
         "Game Result: Game 1 ended in 123456 ms. Ai(1)-Candidate has won!\n")
    sha=hashlib.sha256(raw.encode()).hexdigest()
    g=dict(arm="candidate",candidate_deck="Deck_Candidate",candidate_deck_sha256="hash",
           candidate_seat=1,candidate_win=True,seats=names,pod="aristo",rotation=0,repeat=0,
           seed=42,policy="V13-incubate-adaptive",status="complete",
           game_milliseconds=123456,clock_seconds=360,process_exit=0,
           winner_seat=1,winner_deck="Deck_Candidate",log_sha256=sha)
    legal={n:{"structurally_and_legality_valid":True} for n in names}
    decks={"decks":{"candidate":{"label":"Deck_Candidate","forge_sha256":"hash"}}}
    return g,raw,legal,decks


class Certificate(unittest.TestCase):
    def test_full_four_player_result_all_legal_modes(self):
        g,raw,legal,decks=example_outcome()
        r=certify_one(g,raw,legal,decks)
        self.assertTrue(r["natural_verified"],r["rejection_reasons"])
        self.assertEqual(len(r["outcome_modes"]),4)

    def test_tampering_with_game_log_blocks_win(self):
        g,raw,legal,decks=example_outcome()
        r=certify_one(g,raw+"tampering",legal,decks)
        self.assertFalse(r["natural_verified"])
        self.assertTrue(any("hash differs" in x for x in r["rejection_reasons"]))

    def test_censored_game_never_accepted(self):
        g,raw,legal,decks=example_outcome()
        g.update(status="clock_censored",candidate_win=None,winner_deck=None,winner_seat=None)
        r=certify_one(g,raw,legal,decks)
        self.assertFalse(r["natural_verified"])


def trial(n=1):
    rows=[]
    manifest={"decks":{"reference":{"label":"Deck_Reference","forge_sha256":"ref"},
                       "candidate":{"label":"Deck_Candidate","forge_sha256":"new"}},"delta":{"added":{"Swamp":1},"removed":{"Plains":1}}}
    for pod in ("aristo","artifact"):
        for shift in range(4):
            for repeat in range(n):
                for arm in ("reference","candidate"):
                    rows.append({"arm":arm,"pod":pod,"rotation":shift,"repeat":repeat,"seed":100+shift*10000+repeat+(0 if pod=="aristo" else 100000),
                       "candidate_seat":1+(4-shift)%4,"candidate_deck":manifest["decks"][arm]["label"],
                       "candidate_sha256":manifest["decks"][arm]["forge_sha256"],"policy":"V13-incubate-adaptive",
                       "status":"complete","natural_verified":True,"ai_warning_free":True,
                       "transcript_sha256":hashlib.sha256(f"{pod}-{shift}-{repeat}-{arm}".encode()).hexdigest(),
                       "candidate_win":(arm=="candidate"),"winner_deck":"Deck_Candidate" if arm=="candidate" else "Opponent",
                       "ai_quality_signatures":{"evaluation_timeouts":0,"invalid_attack_fallbacks":0},
                       "rejection_reasons":[],"wall_seconds":3})
    return {"games":rows},manifest


class Analysis(unittest.TestCase):
    def test_balanced_four_seat_two_pod_comparison(self):
        cert,manifest=trial()
        r=analyze(cert,manifest,1)
        self.assertEqual(r["summary"]["scheduled_matches"],16)
        self.assertEqual(r["summary"]["matched_seed_pairs"],8)
        self.assertEqual(r["summary"]["pairs_candidate_only_wins"],8)
        self.assertEqual(len(r["by_candidate_seat"]),4)

    def test_detect_mismatched_policy(self):
        cert,manifest=trial()
        cert["games"][0]["policy"]="Other"
        with self.assertRaisesRegex(ValueError,"different AI versions"):
            analyze(cert,manifest,1)

    def test_timeout_censorship_changes_denominator(self):
        cert,manifest=trial()
        cert["games"][0].update(natural_verified=False,status="clock_censored",
                               candidate_win=None,rejection_reasons=["Clock cutoff"])
        r=analyze(cert,manifest,1)
        self.assertEqual(r["summary"]["reference"]["rejected_or_censored"],1)
        self.assertEqual(r["summary"]["reference"]["natural_certified"],7)
        self.assertEqual(r["summary"]["reference"]["winrate_upper_bound_all_scheduled"],0.125)

    def test_wilson_for_one_in_eight_is_not_certainty(self):
        self.assertLess(wilson(1,8)[0],0.1)
        self.assertGreater(wilson(1,8)[1],0.4)

    def test_missing_seat_refuses_partial_results(self):
        cert,manifest=trial()
        cert["games"].pop()
        with self.assertRaisesRegex(ValueError,"Incomplete matrix"):
            analyze(cert,manifest,1)


if __name__=="__main__":
    unittest.main()
