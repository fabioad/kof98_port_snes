import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FightPaletteUploadTests(unittest.TestCase):
    """Guard the CGRAM windows used by the in-fight OBJ palettes."""

    def setUp(self):
        path = os.path.join(ROOT, "src", "engine", "fight.asm")
        self.fight = open(path, encoding="utf-8").read()
        match = re.search(r"UpCharPals:\n(.*?)\n\s*plx\n\s*rts",
                          self.fight, re.S)
        self.assertIsNotNone(match, "UpCharPals block not found")
        self.block = match.group(1)

    def test_base_palette_starts_at_obj_palette_zero(self):
        # P1 base = CGRAM 128 (OBJ palette 0); P2 adds side*16 -> 144.
        # 68/84 are BG palette slots and used to leave the fighters showing
        # boot/intro colours (white/gray and black/yellow).
        self.assertIn("lda #128.w", self.block)
        self.assertNotIn("lda #68.w", self.block)

    def test_ghost_and_flash_palettes_keep_their_obj_slots(self):
        self.assertIn("lda #176.w", self.block)   # P1 dim / P2 192
        self.assertIn("lda #208.w", self.block)   # P1 flash / P2 224
        self.assertIn("sta scr5", self.block)     # side*16 offset

    def test_hud_palettes_start_at_palette_three(self):
        # HudPal is 20 colors (5 x 4): palettes 3-7 live at CGRAM 12-31.
        # Loading at CGADD 6 left palette 7 (the POWER bars / stock digits)
        # uninitialised, so they showed whatever CGRAM held.
        self.assertIn("lda #12", self.fight)
        self.assertIn("2bpp HUD palettes 3-7 -> CGRAM 12-31", self.fight)


if __name__ == "__main__":
    unittest.main()
