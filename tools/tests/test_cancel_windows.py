"""Special/super cancel windows after a connected normal.

Every normal opens after the first third of its animation, on contact.  The
same table drives the human CancelGate and the CPU's hit-confirm routes, so
these tests pin the per-normal open element.  Normal -> normal chains are not
part of this table; they are disabled in the engine.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf  # noqa: E402


def frames(ticks):
    """Generated AIR rows only need byte 4 (the element duration)."""
    return [(0, 0, 0, 0, tick, 0, 0, 0) for tick in ticks]


class NormalOpenTests(unittest.TestCase):
    def test_open_element_is_the_first_third(self):
        # 6 x 3 ticks: 18 ticks total, first third at tick 6 -> element 2.
        self.assertEqual(2, bf.normal_open_elem(frames([3, 3, 3, 3, 3, 3])))

    def test_variable_durations_use_accumulated_ticks(self):
        # starts at 0, 2, 10, 12; 24 / 3 = 8 -> element 2.
        self.assertEqual(2, bf.normal_open_elem(frames([2, 8, 2, 8])))

    def test_short_clip_opens_immediately(self):
        self.assertEqual(0, bf.normal_open_elem(frames([1, 1])))
        self.assertEqual(0, bf.normal_open_elem([]))

    def test_every_normal_gets_exactly_one_open(self):
        durations = {sid: frames([3, 3, 3]) for sid in range(5, 27)}
        rows = bf.cancel_windows(durations)
        self.assertEqual(list(bf.CANCEL_NORMAL_SIDS),
                         [sid for sid, _ in rows])
        self.assertEqual(len(rows), len(set(sid for sid, _ in rows)))
        for sid, open_elem in rows:
            self.assertGreaterEqual(open_elem, 0)
            self.assertLessEqual(open_elem, 0xFE)
            self.assertEqual(1, open_elem)     # 9 ticks / 3 -> element 1


if __name__ == "__main__":
    unittest.main()
