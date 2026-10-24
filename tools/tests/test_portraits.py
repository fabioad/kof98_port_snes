import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import ROOT  # noqa: E402


class PortraitLayoutTests(unittest.TestCase):
    def test_p1_portrait_is_moved_to_left_edge(self):
        text = open(os.path.join(ROOT, "src/engine/fight.asm"),
                    encoding="utf-8").read()
        self.assertIn("#((1*32+0)*2).w", text)
        self.assertIn("PORTRAIT_P1.w", text)

    def test_p2_portrait_uses_mirrored_asset_table(self):
        fight = open(os.path.join(ROOT, "src/engine/fight.asm"),
                     encoding="utf-8").read()
        build = open(os.path.join(ROOT, "tools/build_fight.py"),
                     encoding="utf-8").read()
        self.assertIn("lda.l PortraitOfsP2,x", fight)
        self.assertIn("PortraitOfsP2:", build)
        self.assertIn("23 - x", build)
        self.assertIn('"PortraitOfsP2:\\n"', build)

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
