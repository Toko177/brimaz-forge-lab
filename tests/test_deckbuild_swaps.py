import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from deckbuild_swaps import apply_swaps,save_candidate

class DirectCommanderSwapTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.base=pathlib.Path(self.temp.name)/"base.txt"
        self.base.write_text("98 Plains\n1 Swamp\n1 Brimaz, Blight of Oreskos\n")
        self.cmd="Brimaz, Blight of Oreskos"
    def tearDown(self):
        self.temp.cleanup()

    def test_one_card_swap_keeps_100_and_commander(self):
        result=apply_swaps(self.base,self.cmd,"Plains -> Orzhov Basilica")
        counts,commanders,removed,added=result
        self.assertEqual(sum(counts.values()),100)
        self.assertEqual(counts["Orzhov Basilica"],1)
        self.assertEqual(removed["Plains"],1)
        self.assertEqual(commanders[self.cmd],1)
        target=pathlib.Path(self.temp.name)/"variant.txt"
        save_candidate(target,counts,commanders)
        self.assertIn("1 Orzhov Basilica",target.read_text())

    def test_multiple_quantity_preserving_swaps(self):
        c,*_=apply_swaps(self.base,self.cmd,"2 Plains -> 2 Swamp; Plains -> Sol Ring")
        self.assertEqual(c["Plains"],95)
        self.assertEqual(c["Swamp"],3)
        self.assertEqual(c["Sol Ring"],1)

    def test_card_count_must_not_change(self):
        with self.assertRaisesRegex(ValueError,"exact deck card count"):
            apply_swaps(self.base,self.cmd,"2 Plains -> 1 Swamp")

    def test_commander_cannot_be_replaced(self):
        with self.assertRaisesRegex(ValueError,"protected commander"):
            apply_swaps(self.base,self.cmd,"Brimaz, Blight of Oreskos -> Sol Ring")

    def test_cannot_remove_absent_card(self):
        with self.assertRaisesRegex(ValueError,"not present"):
            apply_swaps(self.base,self.cmd,"Mana Crypt -> Sol Ring")

    def test_empty_or_malformed_swap_rejected(self):
        with self.assertRaises(ValueError):
            apply_swaps(self.base,self.cmd,"")
        with self.assertRaises(ValueError):
            apply_swaps(self.base,self.cmd,"Plains : Sol Ring")

if __name__=="__main__":
    unittest.main()
