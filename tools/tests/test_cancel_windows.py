"""Special/super cancel windows compiled from the MUGEN var(1) Combo blocks."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf  # noqa: E402


class CancelWindowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _cns(self, text):
        path = self.root / "chars.cns"
        path.write_text(text)
        return path

    def test_strong_normals_open_on_first_contact(self):
        path = self._cns(
            "[State -1, Combo]\n"
            "type = VarSet\n"
            "trigger1 = stateno = 210 && AnimElemTime(5) > 0 "
            "&& AnimElemTime(6) < 0\n"
            "trigger2 = stateno = 400 && AnimElemTime(2) > 0 "
            "&& AnimElemTime(3) < 0\n"
            "var(1) = 1\n"
            "[State -1, Not a cancel]\n"
            "type = VarSet\n"
            "trigger1 = stateno = 230 && AnimElemTime(4) > 0\n"
            "var(1) = 2\n")
        rows = dict(bf.cancel_windows(
            path, {6: 210, 19: 400, 7: 230},
            {6: 10, 19: 6, 7: 12}))
        # Strong punch: CancelGate itself checks F_HITDONE, so the table
        # opens on the first element to allow an immediate hit-confirm.
        self.assertEqual(0, rows[6])
        # crouching light punch: MUGEN elem 2 -> 0-based 1.
        self.assertEqual(1, rows[19])
        # var(1) = 2 is a follow-up state, not a normal cancel window.
        self.assertEqual(0, rows[7])

    def test_strong_normals_open_on_contact_without_a_source_window(self):
        path = self._cns("[Statedef 0]\n")
        rows = dict(bf.cancel_windows(
            path, {6: 210}, {6: 10, 7: 10}))
        self.assertEqual(0, rows[6])       # strong punch: contact-only
        self.assertEqual(0, rows[7])       # light kick: contact-only

    def test_all_normals_get_exactly_one_row(self):
        path = self._cns("[Statedef 0]\n")
        rows = bf.cancel_windows(path, {}, {sid: 8 for sid in range(5, 27)})
        self.assertEqual(list(bf.CANCEL_NORMAL_SIDS), [sid for sid, _ in rows])
        self.assertEqual(len(rows), len(set(sid for sid, _ in rows)))
        for sid, open_elem in rows:
            self.assertGreaterEqual(open_elem, 0)
            self.assertLessEqual(open_elem, 0xFE)
            if sid in bf.CANCEL_STRONG_SIDS:
                self.assertEqual(open_elem, 0)

    def test_real_roster_strong_attacks_open_on_contact(self):
        anim_len = {sid: 10 for sid in range(5, 27)}
        for name, cfg in bf.CHARS.items():
            with self.subTest(name=name):
                rows = dict(bf.cancel_windows(
                    ROOT / cfg["cns"], cfg["moves"], anim_len))
                for sid in bf.CANCEL_STRONG_SIDS:
                    self.assertIn(sid, rows)
                    self.assertEqual(rows[sid], 0)


if __name__ == "__main__":
    unittest.main()
