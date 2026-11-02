"""Static regressions for Blue Mary's lunging command grabs.

The Goodnight attempt had a single frame-0 grab box and only a 12 px step
after it, so it grabbed at point-blank only.  1900 (the running face lock)
had the same problem at the far edge of its dash.  The port now adds a
short entry lunge and keeps the grab box alive through it.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INC = ROOT / "build/gen_fight/mary_spr.inc"


def dw_table(text, label):
    start = text.index(label + ":")
    rows = []
    for line in text[start:].splitlines()[1:]:
        line = line.strip()
        if not line.startswith(".dw"):
            break
        rows.append(int(line.split()[1]))
    return rows


def db_block(text, label):
    start = text.index(label + ":")
    rows = []
    for line in text[start:].splitlines()[1:]:
        line = line.strip()
        if not line.startswith(".db"):
            break
        if "$FF" in line:
            break
        rows.append([int(v.strip(), 0)
                     for v in line.split(".db", 1)[1].split(",")])
    return rows


def anim_frames(text, label):
    """AnimTab body -> atkbox byte for each frame."""
    start = text.index(label + ":")
    lines = text[start:].splitlines()
    atk = []
    i = 2                                  # skip label + {count,loopstart}
    while i + 1 < len(lines):
        sprite = lines[i].strip()
        data = lines[i + 1].strip()
        if not sprite.startswith(".dw") or not data.startswith(".db"):
            break
        vals = [int(v.strip(), 0) for v in data.split(".db", 1)[1].split(",")]
        atk.append(vals[4])
        i += 2
    return atk


class MaryGrabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not INC.exists():
            raise unittest.SkipTest("run tools/build_fight.py first")
        cls.text = INC.read_text()

    def test_goodnight_lunge_and_grab_window(self):
        pos = db_block(self.text, "maryPos52")
        self.assertIn([0, 10], pos)
        self.assertIn([1, 10], pos)
        self.assertIn([2, 10], pos)
        self.assertIn([3, 12], pos)       # source step kept
        atk = anim_frames(self.text, "maryAnim52")
        self.assertTrue(all(atk[:4]), atk)

    def test_face_lock_entry_lunge(self):
        pos = db_block(self.text, "maryPos49")
        self.assertIn([0, 8], pos)
        self.assertIn([1, 8], pos)

    def test_grab_success_chains(self):
        start = self.text.index("maryTargetTab:")
        rows = [line.strip() for line in self.text[start:].splitlines()[1:]
                if line.strip().startswith(".db")]
        def byte(v):
            v = v.strip()
            return int(v[1:], 16) if v.startswith("$") else int(v, 0)
        target = [[byte(v) for v in row.split(".db", 1)[1].split(",")]
                  for row in rows]
        self.assertEqual(target[52][2], 0x6D)   # 1305 -> custom sid 109
        self.assertEqual(target[49][2], 0x6E)   # 1910 -> custom sid 110
        trans = self.text[self.text.index("maryTransTab:"):]
        self.assertRegex(trans, r"\.db 110,98,0")


if __name__ == "__main__":
    unittest.main()
