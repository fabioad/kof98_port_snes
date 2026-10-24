import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import build_fight


class ReflectorTableTests(unittest.TestCase):
    def test_athena_ground_shields(self):
        self.assertEqual(build_fight.REFLECTORS["athena"],
                         [(50, 0, 255, 8, -105, 76, -10),
                          (51, 0, 255, 8, -105, 76, -10)])

    def test_rugal_dark_barrier_windows(self):
        self.assertEqual(build_fight.REFLECTORS["rugal"],
                         [(54, 11, 27, 48, -100, 96, -12),
                          (55, 14, 46, 48, -100, 96, -12)])

    def test_rows_are_byte_sized(self):
        # ReflectTab stores one byte per field; negative y edges wrap.
        for name, rows in build_fight.REFLECTORS.items():
            for sid, start, end, x0, y0, x1, y1 in rows:
                values = (sid, start, end, x0, y0, x1, y1)
                self.assertTrue(all(-128 <= v <= 255 for v in values),
                                f"{name}: {values}")


if __name__ == "__main__":
    unittest.main()
