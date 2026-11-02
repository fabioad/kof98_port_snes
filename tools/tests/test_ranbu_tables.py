"""Static regressions for the Ryuko Ranbu family tables.

The source flurries keep one HitDef and re-arm it between contacts through
MoveHitReset (Ryo 3120, Robert 3105) or by re-issuing the HitDef on each
AnimElem (Sakura 3100).  These checks pin the generated native rows so a
future table change cannot silently collapse the flurry back to one hit or
turn its launcher into an ordinary non-knockdown punch.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "gen_fight"


def read(name):
    path = OUT / f"{name}_spr.inc"
    if not path.exists():
        raise unittest.SkipTest("run tools/build_fight.py first")
    return path.read_text()


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
    start = text.index(f"TransTab:")
    block = text[start:]
    rows = []
    lines = block.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"\.db (\d+),(\d+),(\d+)", line.strip())
        if not m:
            continue
        if int(m.group(1)) == sid:
            rows.append((int(m.group(2)), int(m.group(3))))
    return rows


class RanbuTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ryo = read("ryo")
        cls.robert = read("robert")
        cls.sakura = read("sakura")

    def test_ryo_flurry_resets_and_launcher(self):
        active = dw_table(self.ryo, "ryoActiveTab")
        damage = dw_table(self.ryo, "ryoDamageTab")
        flags = dw_table(self.ryo, "ryoFlagsTab")
        self.assertEqual(active[88], 4)
        self.assertEqual(damage[88], 4)
        self.assertEqual(flags[88] & 1, 0)          # rush must not knock down
        rows = db_block(self.ryo, "ryoAct88")
        resets = {row[0] for row in rows if row[1] == 18}
        self.assertTrue({5, 7, 10, 15, 19, 24, 29, 37, 42, 45, 49}
                        <= resets, resets)
        # Launcher: second HitDef (element 6), fall=1, 20 base damage.
        self.assertEqual(active[89], 6)
        self.assertEqual(damage[89], 20)
        self.assertEqual(flags[89] & 1, 1)
        self.assertIn((89, 0), trans_rows(self.ryo, 88))

    def test_ryo_flurry_has_no_stray_projectile(self):
        start = self.ryo.index("ryoProjTab:")
        rows = [line.strip() for line in self.ryo[start:].splitlines()[1:]
                if line.strip().startswith(".db")]
        for sid in (88, 89):
            self.assertEqual(rows[sid].split(",")[-1].strip(), "0")

    def test_robert_flurry_resets_and_launcher(self):
        active = dw_table(self.robert, "robertActiveTab")
        damage = dw_table(self.robert, "robertDamageTab")
        flags = dw_table(self.robert, "robertFlagsTab")
        self.assertEqual(active[85], 2)
        self.assertEqual(damage[85], 4)
        self.assertEqual(flags[85] & 1, 0)
        rows = db_block(self.robert, "robertAct85")
        resets = {row[0] for row in rows if row[1] == 18}
        self.assertTrue({3, 6, 10, 14, 20, 27, 46} <= resets, resets)
        self.assertEqual(active[86], 8)
        self.assertEqual(damage[86], 20)
        self.assertEqual(flags[86] & 1, 1)
        self.assertIn((86, 0), trans_rows(self.robert, 85))

    def test_robert_flurry_has_no_stray_projectile(self):
        start = self.robert.index("robertProjTab:")
        rows = [line.strip() for line in self.robert[start:].splitlines()[1:]
                if line.strip().startswith(".db")]
        for sid in (85, 86):
            self.assertEqual(rows[sid].split(",")[-1].strip(), "0")

    def test_sakura_haru_ichiban_slices(self):
        active = dw_table(self.sakura, "sakuraActiveTab")
        damage = dw_table(self.sakura, "sakuraDamageTab")
        flags = dw_table(self.sakura, "sakuraFlagsTab")
        # First slice: source element 8 (frame 7), four rush contacts.
        self.assertEqual(active[88], 8)
        self.assertEqual(damage[88], 5)
        self.assertEqual(flags[88] & 1, 0)
        rows = db_block(self.sakura, "sakuraAct88")
        resets = {row[0] for row in rows if row[1] == 18}
        self.assertTrue({11, 15, 19} <= resets, resets)
        # Second slice: element 26 becomes local element 1.
        self.assertEqual(active[89], 1)
        self.assertEqual(damage[89], 20)
        self.assertEqual(flags[89] & 1, 1)
        self.assertIn((89, 0), trans_rows(self.sakura, 88))
        self.assertIn((0, 0), trans_rows(self.sakura, 89))


if __name__ == "__main__":
    unittest.main()
