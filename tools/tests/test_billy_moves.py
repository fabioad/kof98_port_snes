"""Static regressions for Billy's Kyoushuu Hishou Kon, Senpuu Kon and
Sansetsu Kon Chuudan Uchi.

The port used to wire only the opening state of each move: the vault never
reached its rising/dropping/landing states, the spinning staff landed a
single hit and the three-part staff had no follow-up.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INC = ROOT / "build/gen_fight/billy_spr.inc"


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


def trans_rows(text, sid):
    start = text.index("billyTransTab:")
    rows = []
    lines = text[start:].splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"\s*\.db (\d+),(\d+),(\d+)", line)
        if m and int(m.group(1)) == sid:
            arg = re.match(r"\s*\.dw \$([0-9A-Fa-f]+)", lines[i + 1])
            rows.append((int(m.group(2)), int(m.group(3)),
                         int(arg.group(1), 16) if arg else 0))
    return rows


class BillyMoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not INC.exists():
            raise unittest.SkipTest("run tools/build_fight.py first")
        cls.text = INC.read_text()

    def test_kyoushuu_hishou_states(self):
        active = dw_table(self.text, "billyActiveTab")
        damage = dw_table(self.text, "billyDamageTab")
        flags = dw_table(self.text, "billyFlagsTab")
        # 1300/1305 open the vault; the rush must not knock down before the
        # 1302 contacts, and 1301 has no hitbox of its own.
        for sid, act, dmg in ((52, 5, 17), (58, 6, 14), (61, 0, 0),
                              (63, 1, 8), (65, 0, 0)):
            self.assertEqual(active[sid], act, sid)
            self.assertEqual(damage[sid], dmg, sid)
        self.assertEqual(flags[52] & 1, 0)
        self.assertEqual(flags[58] & 1, 0)
        self.assertEqual(flags[63] & 1, 0)

    def test_kyoushuu_hishou_chain(self):
        self.assertIn((61, 0, 0), trans_rows(self.text, 52))
        self.assertIn((61, 0, 0), trans_rows(self.text, 58))
        self.assertIn((63, 0, 0), trans_rows(self.text, 61))
        self.assertIn((65, 1, 10), trans_rows(self.text, 63))
        self.assertIn((0, 0, 0), trans_rows(self.text, 65))
        # Time=0 cross-up PosAdd must reach the table.
        pos = db_block(self.text, "billyPos63")
        self.assertIn([0, 100], pos)

    def test_senpuu_kon_multi_hit(self):
        active = dw_table(self.text, "billyActiveTab")
        damage = dw_table(self.text, "billyDamageTab")
        flags = dw_table(self.text, "billyFlagsTab")
        self.assertEqual(active[54], 6)
        self.assertEqual(damage[54], 3)
        self.assertEqual(flags[54] & 1, 0)
        self.assertEqual(active[59], 4)
        self.assertEqual(damage[59], 5)
        self.assertEqual(flags[59] & 1, 0)
        resets = {r[0] for r in db_block(self.text, "billyAct54")
                  if r[1] == 18}
        self.assertTrue({7, 13, 15, 21, 23, 29, 31, 37, 39, 45, 47, 53, 55}
                        <= resets, resets)
        resets = {r[0] for r in db_block(self.text, "billyAct59")
                  if r[1] == 18}
        self.assertTrue({5, 8, 12, 17, 21, 23, 29} <= resets, resets)
        self.assertIn((0, 0, 0), trans_rows(self.text, 54))
        self.assertIn((0, 0, 0), trans_rows(self.text, 59))

    def test_sansetsu_chuudan_follow_up(self):
        active = dw_table(self.text, "billyActiveTab")
        damage = dw_table(self.text, "billyDamageTab")
        flags = dw_table(self.text, "billyFlagsTab")
        self.assertEqual(active[56], 4)
        self.assertEqual(damage[56], 28)
        self.assertEqual(active[55], 4)
        self.assertEqual(damage[55], 29)
        self.assertEqual(active[60], 3)
        self.assertEqual(damage[60], 11)
        self.assertEqual(flags[60] & 1, 1)
        self.assertIn((60, 3, 0), trans_rows(self.text, 56))
        self.assertIn((60, 3, 0), trans_rows(self.text, 55))
        self.assertIn((0, 0, 0), trans_rows(self.text, 60))


if __name__ == "__main__":
    unittest.main()
