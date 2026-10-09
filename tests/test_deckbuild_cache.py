#!/usr/bin/env python3
"""Security regression for real Forge reference-result reuse."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from deckbuild_cache import FILES,OPPONENTS,stamp,require_match,validate_reference_logs


def build_fixture(root,repeats=1):
    root=Path(root)
    d=root/"forge_decks";d.mkdir(parents=True)
    for f in FILES:
        path=root/f;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text("Code for "+f)
    (d/"Deck_Reference.dck").write_text("[Commander]\n1 Test Commander\n")
    sha=hashlib.sha256((d/"Deck_Reference.dck").read_bytes()).hexdigest()
    for group in OPPONENTS.values():
        for n in group:(d/(n+".dck")).write_text(f"[Main]\n99 Swamp\n[Commander]\n1 {n}\n")
    m={"decks":{"reference":{"label":"Deck_Reference","forge_sha256":sha,
                             "commander":{"Test Commander":1},
                             "source_sha256":"source_sha"}},
       "delta":{"added":{},"removed":{}}}
    (d/"candidate-manifest.json").write_text(json.dumps(m))
    return stamp(root,d,d/"candidate-manifest.json",seed_base=21410000,repeats=repeats)


def write_games(root,key):
    d=Path(root)/"cache-shards"
    rows=[]
    repeats=key["inputs"]["repeats"]
    for pod, opponents in OPPONENTS.items():
        for rot in range(4):
            shard=d/pod/f"r{rot}";shard.mkdir(parents=True,exist_ok=True)
            games=[]
            for rep in range(repeats):
                raw=f"Seed {21410000+(100000 if pod=='artifact' else 0)+10000*rot+rep} - actual transcript fixture\n"
                name=f"game_rot{rot}_rep{rep}.log"
                (shard/name).write_text(raw)
                seats=["Deck_Reference"]+opponents
                seats=seats[rot:]+seats[:rot]
                games.append({
                    "arm":"reference","pod":pod,"rotation":rot,"repeat":rep,
                    "seats":seats,"candidate_deck":"Deck_Reference",
                    "candidate_seat":seats.index("Deck_Reference")+1,
                    "seed":21410000+(100000 if pod=="artifact" else 0)+10000*rot+rep,
                    "clock_seconds":360,"policy":"V13-incubate-adaptive",
                    "profiles":["Default"]*4,"status":"complete",
                    "candidate_deck_sha256":key["inputs"]["reference_deck_sha256"],
                    "log":str(shard/name),"log_sha256":hashlib.sha256(raw.encode()).hexdigest()
                })
                rows.append(games[-1])
            (shard/"games.json").write_text(json.dumps(games))
    return d


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.key=build_fixture(self.root)
    def tearDown(self):
        self.temp.cleanup()

    def test_identical_environment_can_reuse_same_eight_shards(self):
        again=build_fixture(self.root)
        self.assertEqual(require_match(self.key,again),self.key["fingerprint"])
        path=write_games(self.root,self.key)
        d=validate_reference_logs(path,self.key)
        self.assertEqual(d["reference_games"],8)

    def test_any_patch_change_invalidates_all_cached_games(self):
        (self.root/FILES[1]).write_text("Changed V13 policy")
        changed=stamp(self.root,self.root/"forge_decks",self.root/"forge_decks/candidate-manifest.json",
                      seed_base=21410000,repeats=1)
        with self.assertRaisesRegex(ValueError,"INCOMPATIBLE"):
            require_match(self.key,changed)

    def test_seed_or_repeat_change_rejects_cache(self):
        d=copy.deepcopy(self.key)
        d["inputs"]["seed_base"]+=1
        with self.assertRaisesRegex(ValueError,"INCOMPATIBLE"):
            require_match(self.key,d)
        varied=build_fixture(self.root,repeats=2)
        with self.assertRaisesRegex(ValueError,"INCOMPATIBLE"):
            require_match(self.key,varied)

    def test_other_player_deck_change_invalidates_cache(self):
        (self.root/"forge_decks"/"Kaal_9594008.dck").write_text("Different deck!")
        changed=stamp(self.root,self.root/"forge_decks",self.root/"forge_decks/candidate-manifest.json",
                      seed_base=21410000,repeats=1)
        with self.assertRaisesRegex(ValueError,"INCOMPATIBLE"):
            require_match(self.key,changed)

    def test_tampered_reference_transcript_never_reused(self):
        path=write_games(self.root,self.key)
        log=next(path.rglob("*.log"));log.write_text("modified")
        with self.assertRaisesRegex(ValueError,"tampered"):
            validate_reference_logs(path,self.key)

    def test_missing_or_duplicate_shard_is_rejected(self):
        path=write_games(self.root,self.key)
        sample=next(path.rglob("games.json"))
        sample.unlink()
        with self.assertRaisesRegex(ValueError,"Expected exactly"):
            validate_reference_logs(path,self.key)

    def test_foreign_candidate_arm_is_rejected(self):
        path=write_games(self.root,self.key)
        sample=next(path.rglob("games.json"))
        g=json.loads(sample.read_text())
        g[0]["arm"]="candidate";sample.write_text(json.dumps(g))
        with self.assertRaisesRegex(ValueError,"foreign candidate"):
            validate_reference_logs(path,self.key)

    def test_legacy_cache_key_without_real_engine_hash_is_rejected(self):
        legacy={"fingerprint":self.key["fingerprint"]}
        with self.assertRaisesRegex(ValueError,"INCOMPATIBLE"):
            require_match(self.key,legacy)

    def test_cached_unknown_policy_is_not_reused(self):
        path=write_games(self.root,self.key)
        sample=next(path.rglob("games.json"))
        games=json.loads(sample.read_text())
        games[0]["policy"]="other AI"
        sample.write_text(json.dumps(games))
        with self.assertRaisesRegex(ValueError,"immutable reference configuration"):
            validate_reference_logs(path,self.key)


if __name__=="__main__":
    unittest.main()
