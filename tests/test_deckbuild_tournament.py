import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from deckbuild_cache import FILES
from deckbuild_run import OPPONENTS
from deckbuild_tournament import parse_recipe,prepare_tournament,assemble


class MultiVariantTournamentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.repo=self.root/"repo"
        self.repo.mkdir()
        for name in FILES:
            file=self.repo/name
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text("identical pinned runtime "+name)
        self.base=self.root/"Brimaz.txt"
        self.base.write_text("99 Plains\n1 Brimaz, Blight of Oreskos\n")
        self.opponents=self.root/"opponents"
        self.opponents.mkdir()
        for names in OPPONENTS.values():
            for name in names:
                (self.opponents/(name+".dck")).write_text(f"[Main]\n99 Swamp\n[Commander]\n1 {name}\n")
        self.recipe=self.root/"swaps.json"
        self.recipe.write_text(json.dumps({"variants":[
            {"id":"mana-fix","swaps":"1 Plains -> 1 Swamp"},
            {"id":"fetchland","swaps":"1 Plains -> 1 Fabled Passage"},
        ]}))
    def tearDown(self):
        self.temp.cleanup()

    def build(self):
        return prepare_tournament(
            base=self.base,commander="Brimaz, Blight of Oreskos",
            recipe=self.recipe,opponents=self.opponents,
            root=self.root/"tournament",repo_root=self.repo,seed_base=21410000,repeats=1)

    def simulate_manifest_transcripts(self,plan):
        root=self.root/"real_games"
        for j in plan["jobs"]:
            slug=j["variant"];pod=j["pod"];rotation=j["rotation"];arm=j["arm"]
            source=self.root/"tournament/variants"/slug/"forge_decks/candidate-manifest.json"
            m=json.loads(source.read_text())
            item=m["decks"][arm]
            path=root/f"{arm}-{slug}-{pod}-r{rotation}"
            path.mkdir(parents=True)
            log="Raw Forge 4player source for "+repr(j)
            (path/"real.log").write_text(log)
            seats=[item["label"]]+OPPONENTS[pod]
            seats=seats[rotation:]+seats[:rotation]
            game={"arm":arm,"pod":pod,"rotation":rotation,"repeat":0,
                  "seed":21410000+(100000 if pod=="artifact" else 0)+10000*rotation,
                  "candidate_deck":item["label"],"candidate_deck_sha256":item["forge_sha256"],
                  "policy":"V13-incubate-adaptive","seats":seats,
                  "candidate_seat":seats.index(item["label"])+1,
                  "log":str(path/"real.log"),
                  "log_sha256":hashlib.sha256(log.encode()).hexdigest()}
            (path/"games.json").write_text(json.dumps([game]))
        return root

    def test_two_candidates_share_only_eight_real_reference_games(self):
        plan=self.build()
        self.assertEqual(plan["scheduled"],24)
        self.assertEqual(len(plan["jobs"]),24)
        self.assertEqual(sum(x["arm"]=="reference" for x in plan["jobs"]),8)
        self.assertEqual(sum(x["arm"]=="candidate" for x in plan["jobs"]),16)
        self.assertEqual(len(plan["variants"]),2)
        self.assertTrue(len(plan["reference_fingerprint"])==64)

    def test_original_brimaz_deck_is_never_modified(self):
        raw=self.base.read_bytes()
        self.build()
        self.assertEqual(raw,self.base.read_bytes())

    def test_malformed_duplicate_candidate_rejected(self):
        self.recipe.write_text(json.dumps({"variants":[
            {"id":"mana-fix","swaps":"1 Plains -> 1 Swamp"},
            {"id":"mana-fix","swaps":"1 Plains -> 1 Fabled Passage"}]}))
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            self.build()

    def test_duplicate_replacement_contents_rejected_even_with_different_recipe(self):
        self.recipe.write_text(json.dumps({"variants":[
            {"id":"one","swaps":"1 Plains -> 1 Swamp"},
            {"id":"two","swaps":"2 Plains -> 2 Swamp; 1 Plains -> 1 Swamp"}]}))
        with self.assertRaisesRegex(ValueError,"identical|Duplicate"):
            # Same resulting deck? no, three swamps vs one. Re-check actual
            # duplicate same result with a net-neutral swap combination.
            self.recipe.write_text(json.dumps({"variants":[
                {"id":"one","swaps":"1 Plains -> 1 Swamp"},
                {"id":"two","swaps":"1 Plains -> 1 Swamp; 1 Plains -> 1 Plains"}]}))
            self.build()

    def test_real_game_shards_assemble_for_each_candidate_without_duplication(self):
        plan=self.build()
        real=self.simulate_manifest_transcripts(plan)
        result=assemble(plan=self.root/"tournament/tournament.json",
                        game_root=real,output=self.root/"staging")
        self.assertEqual(result["shared_reference_games"],8)
        self.assertEqual(result["candidate_games"],16)
        for slug in plan["variants"]:
            all_manifests=list((self.root/"staging"/slug).rglob("games.json"))
            self.assertEqual(len(all_manifests),16)
            self.assertEqual(sum("reference" in str(p) for p in all_manifests),8)

    def test_missing_match_refuses_fabricated_tournament_result(self):
        plan=self.build()
        real=self.simulate_manifest_transcripts(plan)
        next(real.rglob("games.json")).unlink()
        with self.assertRaisesRegex(ValueError,"Missing actual Forge job shards"):
            assemble(plan=self.root/"tournament/tournament.json",game_root=real,output=self.root/"staging")

    def test_changed_raw_game_log_rejected(self):
        plan=self.build()
        real=self.simulate_manifest_transcripts(plan)
        next(real.rglob("real.log")).write_text("tampered")
        with self.assertRaisesRegex(ValueError,"Missing/tampered"):
            assemble(plan=self.root/"tournament/tournament.json",game_root=real,output=self.root/"staging")

    def test_unknown_extra_candidate_shard_rejected(self):
        plan=self.build()
        real=self.simulate_manifest_transcripts(plan)
        other=real/"other"
        other.mkdir()
        (other/"games.json").write_text(json.dumps([{"arm":"candidate","pod":"aristo",
                         "rotation":0,"candidate_deck_sha256":"unrecognized"}]))
        with self.assertRaisesRegex(ValueError,"exactly one planned variant|missing repeats"):
            assemble(plan=self.root/"tournament/tournament.json",game_root=real,output=self.root/"staging")

    def test_refuses_to_write_second_tournament_into_existing_staging(self):
        plan=self.build()
        real=self.simulate_manifest_transcripts(plan)
        target=self.root/"staging"
        assemble(plan=self.root/"tournament/tournament.json",game_root=real,output=target)
        with self.assertRaisesRegex(ValueError,"must be empty"):
            assemble(plan=self.root/"tournament/tournament.json",game_root=real,output=target)


if __name__=="__main__":
    unittest.main()
