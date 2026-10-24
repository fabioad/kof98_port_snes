"""Unit tests for the documented KOF motion shortcuts."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import build_fight as bf  # noqa: E402


class ShortcutTests(unittest.TestCase):
    def test_hcf_skips_diagonals(self):
        classic = [(8, 0), (10, 0), (2, 0), (6, 0), (4, 1)]
        self.assertEqual([(8, 0), (2, 0), (4, 1)],
                         bf.shortcut_elems(classic))

    def test_hcb_skips_diagonals(self):
        classic = [(4, 0), (6, 0), (2, 0), (10, 0), (8, 1)]
        self.assertEqual([(4, 0), (2, 0), (8, 1)],
                         bf.shortcut_elems(classic))

    def test_dp_ends_in_forward(self):
        classic = [(4, 0), (2, 0), (6, 0), (0, 2)]
        self.assertEqual([(4, 0), (2, 0), (4, 0), (0, 2)],
                         bf.shortcut_elems(classic))

    def test_rdp_ends_in_back(self):
        classic = [(8, 0), (2, 0), (10, 0), (0, 4)]
        self.assertEqual([(8, 0), (2, 0), (8, 0), (0, 4)],
                         bf.shortcut_elems(classic))

    def test_hcbx2_shortcut(self):
        classic = [(4, 0), (6, 0), (2, 0), (10, 0), (8, 0),
                   (4, 0), (6, 0), (2, 0), (10, 0), (8, 1)]
        self.assertEqual([(4, 0), (2, 0), (8, 0),
                          (4, 0), (2, 0), (8, 1)],
                         bf.shortcut_elems(classic))

    def test_qcbhcf_keeps_the_qcb_diagonal(self):
        classic = [(2, 0), (10, 0), (8, 0), (10, 0), (2, 0), (6, 0), (4, 1)]
        self.assertEqual([(2, 0), (10, 0), (8, 0), (2, 0), (4, 1)],
                         bf.shortcut_elems(classic))

    def test_qcfhcb_keeps_the_qcf_diagonal(self):
        classic = [(2, 0), (6, 0), (4, 0), (6, 0), (2, 0), (10, 0), (8, 1)]
        self.assertEqual([(2, 0), (6, 0), (4, 0), (2, 0), (8, 1)],
                         bf.shortcut_elems(classic))

    def test_shortcut_is_a_subsequence_of_the_classic_input(self):
        cases = [
            [(2, 0), (10, 0), (8, 0), (10, 0), (2, 0), (6, 0), (4, 1)],
            [(2, 0), (6, 0), (4, 0), (6, 0), (2, 0), (10, 0), (8, 1)],
            [(4, 0), (6, 0), (2, 0), (10, 0), (8, 0),
             (4, 0), (6, 0), (2, 0), (10, 0), (8, 1)],
            [(8, 0), (10, 0), (2, 0), (6, 0), (4, 0),
             (8, 0), (10, 0), (2, 0), (6, 0), (4, 1)],
            [(4, 0), (6, 0), (2, 0), (10, 0), (8, 0), (4, 1)],
        ]
        for classic in cases:
            short = bf.shortcut_elems(classic)
            self.assertIsNotNone(short)
            j = 0
            for d, b in classic:
                if j < len(short) and (d & 0x0F, b) == short[j]:
                    j += 1
            self.assertEqual(len(short), j, (classic, short))

    def test_qcf_and_qcb_keep_their_diagonals(self):
        # A two-input 2,3+P / 2,1+P would collide with crouching attacks
        # and is not a documented KOF shortcut.
        self.assertIsNone(bf.shortcut_elems([(2, 0), (6, 0), (4, 1)]))
        self.assertIsNone(bf.shortcut_elems([(2, 0), (10, 0), (8, 1)]))

    def test_classic_dp_still_kept_for_the_matcher(self):
        defs = {"DP": (0, [(4, 0), (2, 0), (6, 0), (0, 2)], 15)}
        bf.apply_half_circle_shortcuts(defs)
        self.assertEqual(defs["DP"][1], [(4, 0), (2, 0), (6, 0), (0, 2)])


if __name__ == "__main__":
    unittest.main()
