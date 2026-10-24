"""Per-character CPU personality data and move-table wiring."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf


class AiProfileTests(unittest.TestCase):
    def test_every_character_has_a_profile(self):
        self.assertEqual([], [k for k in bf.CHARS if k not in bf.AI_TUNING])
        self.assertEqual([], [k for k in bf.AI_TUNING if k not in bf.CHARS])

    def test_profiles_are_in_range_and_ordered(self):
        for name, (zlo, zhi, *rates, flags) in bf.AI_TUNING.items():
            with self.subTest(name=name):
                self.assertGreaterEqual(zlo, 0)
                self.assertLess(zlo, zhi)
                self.assertLessEqual(zhi, 255)
                for value in rates:
                    self.assertGreaterEqual(value, 0)
                    self.assertLessEqual(value, 255)
                self.assertEqual(0, flags & ~0x0F)

    def test_kyo_is_the_generic_fallback(self):
        self.assertIn("kyo", bf.AI_TUNING)
        self.assertEqual("kyoAiTab", self._ai_label("kyoash"))
        self.assertEqual("kyoAiTab", self._ai_label("not-in-roster"))

    def _ai_label(self, key):
        # Mirrors emit_newchars_inc.ai_label without building the ROM.
        return ("kyoAiTab" if (key in ("kyonests", "kyoash")
                               or not bf.AI_COUNTS.get(key))
                else f"{key}AiTab")

    def test_move_table_keeps_throw_and_fits_scan_window(self):
        rules = [
            {"state": 48, "motion": "QCF_X", "dist": 0},
            {"state": 50, "motion": "DP_X", "dist": 0},
            {"state": 74, "motion": "y", "dist": 173},  # gate 45 | posture
            {"state": 85, "motion": "QCF_X", "dist": 0},
            {"state": 88, "motion": "QCF_X", "dist": 0},
        ]
        (style, aggr, deff, spec, super_rate, rows,
         profile) = bf.ai_move_table(
            "kyo", rules, {48: 1000, 50: 1100, 74: 800, 85: 3000,
                           88: 3210}, {}, {}, {}, {"moves": {96: 750}})
        self.assertLessEqual(len(rows), 8)
        self.assertLessEqual(len(rows), 16)       # AI_ScanMove uses &$0F
        throw = [r for r in rows if r[0] == 74]
        self.assertEqual(1, len(throw))
        self.assertTrue(throw[0][3] & bf.AI_F_THROW)
        self.assertEqual(45, throw[0][2])         # bit7 posture gate stripped
        self.assertEqual(bf.AI_TUNING["kyo"][2], aggr)
        self.assertEqual(bf.AI_TUNING["kyo"][3], deff)
        tune = bf.AI_TUNING["kyo"]
        self.assertEqual((tune[0], tune[1], tune[4], tune[5], tune[6],
                          tune[7]), profile)

    def test_posture_only_throw_gets_close_range(self):
        # Many source throws carry only the bit7 posture gate (no numeric
        # p2bodydist).  Without a default range the generated row would be
        # hi=0, so the AI could never pick its throw.
        rules = [{"state": 74, "motion": "y", "dist": 0x80}]
        (_style, _aggr, _def, _spec, _super, rows,
         profile) = bf.ai_move_table(
            "clark", rules, {74: 800}, {}, {}, {}, {})
        throw = [r for r in rows if r[0] == 74]
        self.assertEqual(1, len(throw))
        self.assertTrue(throw[0][3] & bf.AI_F_THROW)
        self.assertEqual(45, throw[0][2])
        self.assertGreater(profile[3], 0)

    def test_character_without_throw_has_zero_throw_rate(self):
        rows = [{"state": 48, "motion": "QCF_X", "dist": 0}]
        (_style, _aggr, _def, _spec, _super, _rows,
         profile) = bf.ai_move_table(
            "clark", rows, {48: 1000}, {}, {}, {}, {})
        self.assertEqual(0, profile[3])

    def test_omegarugal_has_a_no_meter_close_plan(self):
        # Omega's specials are expensive boss moves.  A wide zoner band made
        # him stand at mid-screen blocking forever at 0 meter; keep his
        # preferred range short and his pressure flag on so normals carry
        # the no-meter phase.
        zlo, zhi, *_rest, flags = bf.AI_TUNING["omegarugal"]
        self.assertFalse(flags & bf.AI_PF_ZONER)
        self.assertTrue(flags & bf.AI_PF_PRESSURE)
        self.assertLessEqual(zhi, 80)
        self.assertLessEqual(zlo, 40)

    def test_max_flag_requires_state_96(self):
        rows = [{"state": 48, "motion": "QCF_X", "dist": 0}]
        (_style, _aggr, _def, _spec, _super, _rows,
         profile) = bf.ai_move_table(
            "athena", rows, {48: 1000}, {}, {}, {}, {})
        self.assertFalse(profile[5] & bf.AI_PF_METER)
        (_style, _aggr, _def, _spec, _super, _rows,
         profile) = bf.ai_move_table(
            "athena", rows, {48: 1000}, {}, {}, {}, {"moves": {96: 750}})
        self.assertTrue(profile[5] & bf.AI_PF_METER)


if __name__ == "__main__":
    unittest.main()
