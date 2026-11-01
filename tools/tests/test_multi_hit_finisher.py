"""Same-move multi-hit finisher rule.

A special or super that connects five times must knock the victim down on
the fifth contact.  Free-form combos of different attacks must not inherit
the rule, so the engine keys the counter by the attacker's runtime move id
and restarts it when a fresh combo starts.  ``air.fall`` launchers also need
the native knockdown flag on the emitted row.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_fight  # noqa: E402

FIGHT = ROOT / "src/engine/fight.asm"
BUILD = ROOT / "tools/build_fight.py"


class MultiHitFinisherTests(unittest.TestCase):
    def test_engine_counts_same_move_and_forces_fall(self):
        text = FIGHT.read_text()
        self.assertIn(".DEFINE movehits    $5070", text)
        self.assertIn(".DEFINE lastsid     $50B2", text)
        self.assertIn("    jsl MoveHitFinisher", text)
        m = re.search(r"MoveHitFinisher:\n(.*?)\n\nDrawIntroGirls:",
                      text, re.S)
        self.assertIsNotNone(m, "MoveHitFinisher routine missing")
        body = m.group(1)
        self.assertIn("cmp #S_SPECIAL.w", body)
        self.assertIn("cmp #S_SUPPER.w", body)
        self.assertIn("cmp #5.b", body)
        self.assertIn("ora #$0001.w", body)     # force knockdown flag
        self.assertIn("sta lastsid,x", body)
        self.assertIn("sta movehits,x", body)

    def test_air_fall_launchers_get_the_knockdown_row(self):
        text = BUILD.read_text()
        self.assertIn('hitdef.get("air.fall", "0")', text)
        self.assertIn('row["fall"] = 1', text)

    def test_build_carries_the_girlfriend_palette_hook(self):
        self.assertEqual(build_fight.CHARS["mrbig"]["palette_extra_sprites"],
                         [(192, 0), (193, 0)])


if __name__ == "__main__":
    unittest.main()
