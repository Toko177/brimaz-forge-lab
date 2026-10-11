#!/usr/bin/env python3
"""Ranking must never mix non-identical Forge reference games or engine variants."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from deckbuild_compare import analyze
from deckbuild_rank import rank,markdown_report
from test_deckbuild_pipeline import trial


def reports():
    data,m=trial()
    provenance={"fingerprint":"a"*64,"inputs":{"reference_deck_sha256":"ref",
                 "policy":"V13-incubate-adaptive","seed_base":21410000}}
    a=analyze(data,m,1,reference_cache_key=provenance)
    b=copy.deepcopy(a)
    b["deck_manifest"]["candidate"]["forge_sha256"]="different-candidate"
    # baseline and seed-specific reference log hashes remain identical;
    # candidate result changes only and its card swap differs.
    b["candidate_deltas"]={"added":{"Orzhov Signet":1},"removed":{"Plains":1}}
    b["summary"]["candidate"]["wins"]=4
    b["summary"]["candidate"]["certified_winrate"]=0.5
    b["summary"]["candidate"]["wilson_95"]=[0.2152,0.7848]
    return a,b


class MultipleVariantTests(unittest.TestCase):
    def test_rank_two_variants_only_with_exact_shared_reference_history(self):
        a,b=reports()
        d=rank([a,b])
        self.assertEqual(d["summary"]["variants_compared"],2)
        self.assertEqual(d["summary"]["unique_original_reference_games"],8)
        self.assertEqual(d["ranking"][0]["wins"],8)
        self.assertTrue(d["summary"]["no_statistical_winner_declared"])
        self.assertIn("Exploratory screening only",markdown_report(d))

    def test_changed_ai_engine_fingerprint_rejects_comparison(self):
        a,b=reports()
        b["reference_environment"]["fingerprint"]="b"*64
        with self.assertRaisesRegex(ValueError,"Incompatible reference"):
            rank([a,b])

    def test_reference_log_different_on_same_seed_rejects_ranking(self):
        a,b=reports()
        b["pairs"][0]["reference_transcript_sha256"]="e"*64
        with self.assertRaisesRegex(ValueError,"diverged"):
            rank([a,b])

    def test_duplicate_candidate_deck_rejects_pseudoreplication(self):
        a,b=reports()
        b["deck_manifest"]["candidate"]["forge_sha256"]=a["deck_manifest"]["candidate"]["forge_sha256"]
        with self.assertRaisesRegex(ValueError,"Same candidate"):
            rank([a,b])

    def test_missing_log_sha_rejects_reused_reference(self):
        a,b=reports()
        del a["pairs"][0]["reference_transcript_sha256"]
        with self.assertRaisesRegex(ValueError,"No full SHA256"):
            rank([a,b])

    def test_only_one_candidate_is_not_a_ranked_multi_variant_benchmark(self):
        a,_=reports()
        with self.assertRaisesRegex(ValueError,"at least two"):
            rank([a])

    def test_repeated_pod_seed_is_rejected(self):
        a,b=reports()
        a["pairs"].append(a["pairs"][0])
        with self.assertRaisesRegex(ValueError,"Duplicate reference"):
            rank([a,b])

    def test_reference_baseline_deck_must_be_same(self):
        a,b=reports()
        b["deck_manifest"]["reference"]["forge_sha256"]="mutated"
        with self.assertRaisesRegex(ValueError,"Unexpected baseline"):
            rank([a,b])


if __name__=="__main__":
    unittest.main()
