import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from audit_incubate_support import analyze

GAME={"pod":"aristo","seed":20,"policy":"V12-incubate","status":"complete",
      "winner_deck":"Other","brimaz_win":False}
RAW="""No AI assigned for API: Incubate
Resolve Stack: Whenever you cast a Phyrexian creature spell, incubate X. (Create a token)
Add To Stack: Ai(3)-Brimaz V3 activated Incubator Token
Zone Change: Incubator Token (520) was put into Graveyard from Battlefield.
"""


class IncubateAuditTests(unittest.TestCase):
    def test_unknown_ai_is_separate_from_legally_resolved_mandatory_effect(self):
        g=analyze(RAW,GAME)
        self.assertEqual(g["unsupported_incubate_ai_warnings"],1)
        self.assertEqual(g["resolved_incubate_description_events"],1)

    def test_incubator_activations_are_actual_stack_events(self):
        g=analyze(RAW,GAME)
        self.assertEqual(g["incubator_transform_stack_activations"],1)
        self.assertEqual(g["incubator_zone_changes"],1)

    def test_prose_does_not_count_as_real_token_creation(self):
        g=analyze("Resolve Stack: When blah, incubate 3 (Create an Incubator token)\n",GAME)
        self.assertEqual(g["incubator_zone_changes"],0)
        self.assertEqual(g["incubator_transform_stack_activations"],0)

    def test_no_handler_warning_is_zero_with_patched_v12(self):
        g=analyze(RAW.replace("No AI assigned for API: Incubate\n",""),GAME)
        self.assertEqual(g["unsupported_incubate_ai_warnings"],0)


if __name__=="__main__":
    unittest.main()
