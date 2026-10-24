import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import CHARS, ROOT, resolve_p2_palette  # noqa: E402


class MirrorPaletteTests(unittest.TestCase):
    def test_kyo_mirror_uses_the_next_source_palette(self):
        _, alt = resolve_p2_palette("kyo", CHARS["kyo"])
        self.assertIsNotNone(alt)
        self.assertEqual(os.path.basename(alt), "act03.act")
        self.assertTrue(os.path.exists(alt))

    def test_every_character_has_a_p2_palette(self):
        missing = [name for name, cfg in CHARS.items()
                   if not (resolve_p2_palette(name, cfg)[1]
                           or "").endswith(".act")]
        self.assertEqual(missing, [])

    def test_mature_falls_back_to_the_act_folder(self):
        _, alt = resolve_p2_palette("mature", CHARS["mature"])
        self.assertIsNotNone(alt)
        self.assertEqual(os.path.basename(alt), "Mature01.act")

    def test_engine_switches_p2_palette_only_for_mirrors(self):
        fight = open(os.path.join(ROOT, "src/engine/fight.asm"),
                     encoding="utf-8").read()
        alt = open(os.path.join(ROOT, "src/engine/alt_pals.asm"),
                   encoding="utf-8").read()
        self.assertIn("cmp sel2", fight)
        self.assertIn("LCP_alt:", fight)
        self.assertIn("jsl UpCharPalsAltFar", fight)
        self.assertIn("UpCharPalsAltFar:", alt)
        self.assertIn("AltPalRow,x", alt)

    def test_builder_emits_the_p2_palette_tables(self):
        text = open(os.path.join(ROOT, "tools/build_fight.py"),
                    encoding="utf-8").read()
        self.assertIn('_pal_p2.bin', text)
        self.assertIn('"AltPalRow:\\n"', text)
        self.assertIn('engine/alt_pals.asm', text)
        self.assertIn('PalP2Dim', text)


if __name__ == "__main__":
    unittest.main()
