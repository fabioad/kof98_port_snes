"""Mr. Big's round-1 intro must ship the two girlfriend cels.

The source Statedef 191 spawns Explods 165/166 (sprites 192,0 and 193,0).
The native engine has no helpers, so they are drawn from a dedicated OAM
overlay.  This test keeps the generated overlay, the palette hook and the
engine wiring in sync.
"""
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import build_fight  # noqa: E402

ROOT = Path(build_fight.ROOT)
INC = ROOT / "build/gen_fight/intro_girls.inc"
CHR = ROOT / "build/gen_fight/intro_girls.chr"
FIGHT = ROOT / "src/engine/fight.asm"


def _cells(text, label):
    m = re.search(rf"{label}:\s*\n\s*\.db\s+(\d+)\n(.*?)(?=\n\w+Cells:|\Z)",
                  text, re.S)
    if not m:
        raise AssertionError(f"{label} missing from intro_girls.inc")
    rows = re.findall(r"\.db\s+(\d+),(\d+)\s*\n\s*\.dw\s+\$([0-9A-Fa-f]+)",
                      m.group(2))
    return int(m.group(1)), [(int(dx), int(dy), int(t, 16))
                              for dx, dy, t in rows]


class MrBigIntroTests(unittest.TestCase):
    def test_palette_includes_the_girlfriend_cels(self):
        self.assertEqual(build_fight.CHARS["mrbig"]["palette_extra_sprites"],
                         [(192, 0), (193, 0)])

    def test_overlay_fits_one_64_tile_page(self):
        text = INC.read_text()
        n_a, cells_a = _cells(text, "GirlACells")
        n_b, cells_b = _cells(text, "GirlBCells")
        self.assertEqual(n_a, len(cells_a))
        self.assertEqual(n_b, len(cells_b))
        self.assertGreater(n_a, 0)
        self.assertGreater(n_b, 0)
        total = n_a + n_b
        # OAM is 128 cells.  Two PRO-scale fighters spend 88 on their intro
        # poses, so the overlay must fit the remaining 40 or it disappears
        # once both are drawn (the bug that hid the girls on the right side).
        self.assertLessEqual(total, 40)
        self.assertEqual(total % 4, 0, "OAM high table is 4 cells per byte")
        tiles = set()
        for _dx, _dy, tile in cells_a + cells_b:
            page_tile = tile & 0x7FFF
            self.assertGreaterEqual(page_tile, 448)
            self.assertLessEqual(page_tile, 511)
            base = page_tile - 448
            if tile & 0x8000:              # 8x8 sprite: one atlas slot
                tiles.add(base)
            else:                          # 16x16: base, base+1, +16, +17
                tiles.update((base, base + 1, base + 16, base + 17))
        self.assertLessEqual(len(tiles), 64)
        self.assertEqual(CHR.stat().st_size, 2048)

    def test_engine_cell_count_matches_generated_overlay(self):
        text = INC.read_text()
        total = sum(int(m.group(1)) for m in
                    re.finditer(r"Girl[AB]Cells:\s*\n\s*\.db\s+(\d+)", text))
        cfg = ROOT / "build/gen_fight/intro_girls_cfg.inc"
        self.assertIn(f".DEFINE GIRL_CELLS {total}", cfg.read_text())
        self.assertIn('.INCLUDE "gen_fight/intro_girls_cfg.inc"',
                      FIGHT.read_text())

    def test_engine_wiring(self):
        text = FIGHT.read_text()
        self.assertIn('    jsl UploadIntroGirls', text)
        self.assertIn('    jsl DrawIntroGirls', text)
        self.assertIn('.INCLUDE "gen_fight/intro_girls.inc"', text)
        self.assertIn('cmp #CharMrbig.w', text)
        self.assertIn('cmp #S_INTRO.w', text)


if __name__ == "__main__":
    unittest.main()
