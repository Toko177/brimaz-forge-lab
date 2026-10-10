import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from audit_forge_ai_card_support import classify,slug,inspect,parse_deck

class ExactForgeAIHints(unittest.TestCase):
    def test_diabolic_intent_is_ai_excluded(self):
        r=classify("Diabolic Intent",
                   "Name:Diabolic Intent\nAI:RemoveDeck:All\n")
        self.assertEqual(r["status"],"ai_hard_exclusion")
        self.assertTrue(r["remove_deck_all"])

    def test_phyrexian_reclamation_is_ai_excluded(self):
        self.assertEqual(classify("Phyrexian Reclamation",
           "Name:Phyrexian Reclamation\nAI:RemoveDeck:All\n")["status"],"ai_hard_exclusion")

    def test_mana_engine_has_only_conditional_planner_override(self):
        r=classify("Spawning Pit","Name:Spawning Pit\nAI:RemoveDeck:All\n")
        self.assertEqual(r["status"],"narrow_policy_override")
        self.assertIsNotNone(r["override"])

    def test_no_tag_is_not_equivalent_to_strategic_competence(self):
        r=classify("Sol Ring","Name:Sol Ring\n")
        self.assertEqual(r["status"],"no_hard_exclusion_tag")
        self.assertIn("does not prove",r["disclaimer"])

    def test_missing_official_card_definition_remains_unknown(self):
        self.assertEqual(classify("Missing",None)["status"],"unresolved")

    def test_covered_100_card_deck_never_drops_unknown_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"deck.txt"
            p.write_text("98 Plains\n1 Diabolic Intent\n1 Spawning Pit\n")
            dct={"Plains":"Name:Plains\n","Diabolic Intent":"Name:Diabolic Intent\nAI:RemoveDeck:All\n",
                 "Spawning Pit":"Name:Spawning Pit\nAI:RemoveDeck:All\n"}
            def fake(name):return name,dct.get(name),None
            report=inspect(p,fetch=fake,max_workers=2)
            self.assertEqual(report["summary"]["physical_cards"],100)
            self.assertEqual(report["summary"]["ai_hard_exclusion_cards"],1)
            self.assertEqual(report["summary"]["narrow_conditional_override_cards"],1)

    def test_short_deck_is_rejected_as_invalid_commander_sample(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"deck.txt"
            p.write_text("1 Plains\n")
            with self.assertRaisesRegex(ValueError,"100"):
                parse_deck(p)

    def test_card_name_normalization_handles_accents(self):
        self.assertEqual(slug("Bartolomé del Presidio"),
                         "b/bartolome_del_presidio.txt")

if __name__=="__main__":unittest.main()
