import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import CHARS  # noqa: E402
from sff import Sff  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AthenaPaletteTests(unittest.TestCase):
    def test_roster_forces_palette_bank_zero(self):
        # The SFF's body cels reference palette 1, a dark-red dim copy.
        # build_char must force bank 0 (blue/white costume) before upload.
        self.assertEqual(CHARS["athena"].get("palette_bank"), 0)

    def test_bank_zero_is_the_colour_bank(self):
        sff = Sff(os.path.join(ROOT, CHARS["athena"]["sff"]))
        self.assertGreaterEqual(len(sff.palettes), 2)
        blue = sff.palettes[0][249]
        dim = sff.palettes[1][249]
        self.assertGreater(blue[2], blue[0])       # blue/white costume
        self.assertGreater(sum(blue), sum(dim))    # bank 1 is the dim copy
        self.assertGreater(
            sum(1 for sprite in sff.sprites if sprite.palidx == 1), 100)


if __name__ == "__main__":
    unittest.main()
