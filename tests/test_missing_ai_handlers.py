import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from audit_missing_ai_handlers import inspect, audit

GAME={"pod":"artifact","seed":55,"policy":"V12-incubate",
      "status":"complete","brimaz_win":False}


class MissingAiApiTests(unittest.TestCase):
    def test_missing_api_counts_and_categories(self):
        r=inspect("No AI assigned for API: Incubate\nNo AI assigned for API: Incubate\n"
                  "No AI assigned for API: MakeToken\n",GAME)
        self.assertEqual(r["missing_apis"],{"Incubate":2,"MakeToken":1})
        self.assertEqual(r["warnings"],3)

    def test_v12_valid_game_without_missing_api_warnings(self):
        r=inspect("Resolve Stack: When Brimaz casts, incubate 3.\n",GAME)
        self.assertEqual(r["missing_apis"],{})
        self.assertEqual(r["warnings"],0)

    def test_log_prose_about_api_does_not_invent_warning(self):
        r=inspect("Description: No AI assigned for API may be printed in the future\n",GAME)
        self.assertEqual(r["warnings"],0)

    def test_other_non_ai_errors_not_misclassified(self):
        r=inspect("java.util.concurrent.TimeoutException\nAI Attack declaration invalid\n",GAME)
        self.assertEqual(r["warnings"],0)

    def test_warning_labels_do_not_count_as_magic_rules_violations(self):
        r=inspect("No AI assigned for API: Incubate\n",GAME)
        self.assertEqual(r["status"],"complete")
        self.assertEqual(r["warnings"],1)


if __name__=="__main__":
    unittest.main()
