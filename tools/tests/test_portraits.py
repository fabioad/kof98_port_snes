import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import ROOT  # noqa: E402


class PortraitLayoutTests(unittest.TestCase):
    def test_hud_faces_draw_on_the_bg2_overlay(self):
        text = open(os.path.join(ROOT, "src/engine/fight.asm"),
                    encoding="utf-8").read()
        self.assertIn("HudPortraitMap", text)
        self.assertIn("BG2CHR", text)
        self.assertIn("HUD_P1_TILE", text)
        self.assertIn("HUD_PAL_P1", text)

    def test_p2_portrait_mirrors_through_the_map_flip_bit(self):
        fight = open(os.path.join(ROOT, "src/engine/fight.asm"),
                     encoding="utf-8").read()
        build = open(os.path.join(ROOT, "tools/build_fight.py"),
                     encoding="utf-8").read()
        self.assertIn("lda.l PortraitOfsP2,x", fight)
        self.assertIn("PortraitOfsP2:", build)
        self.assertIn("0x4000", build)
        self.assertIn('"PortraitOfsP2:\\n"', build)

    def test_portraits_are_4bpp_with_15_colours(self):
        build = open(os.path.join(ROOT, "tools/build_fight.py"),
                     encoding="utf-8").read()
        self.assertIn("def _face_palette", build)
        self.assertIn("colors=min(15, len(set(px)))", build)
        self.assertIn("tiles4bpp(bytes(vals), size, size)[0]", build)

    def test_portraits_load_after_active_team_member_is_selected(self):
        """Team modes must not DMA the select-cursor pick into the HUD."""
        text = open(os.path.join(ROOT, "src/engine/fight.asm"),
                    encoding="utf-8").read()
        full = text.index("SF_full:")
        team_sel = text.index("lda.w T_TEAM2,x", full)
        portraits = text.index("jsr LoadPortraits", full)
        palettes = text.index("jsr LoadCharPals", full)
        self.assertLess(team_sel, portraits)
        self.assertLess(portraits, palettes)


if __name__ == "__main__":
    unittest.main()
