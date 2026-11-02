"""Static regressions for the compact magic effects and Chin's bottle.

Athena/Kensou's Explod orbs and Chin's drink bottle were not in the shared
spark atlas, so their moves played without the visible magic.  The effects
are compiled as one-cell clips; Chin's bottle is emitted by the 860 drink
hold at each sip.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "gen_fight"


def read(name):
    path = OUT / name
    if not path.exists():
        raise unittest.SkipTest("run tools/build_fight.py first")
    return path.read_text()


def _vals(line):
    return [int(v.strip(), 0) if not v.strip().startswith("$")
            else int(v.strip()[1:], 16)
            for v in line.split(".db", 1)[1].split(",")]


def db_rows(text, label):
    start = text.index(label + ":")
    rows = []
    for line in text[start:].splitlines()[1:]:
        line = line.strip()
        if not line.startswith(".db"):
            break
        row = _vals(line)
        if not row or row[0] == 0xFF:      # $FF terminator
            break
        rows.append(row)
    return rows


def exp_rows(text, label):
    """ExpTab has a .db row followed by a .dw payload per entry."""
    start = text.index(label + ":")
    rows = []
    for line in text[start:].splitlines()[1:]:
        line = line.strip()
        if line.startswith(".db"):
            rows.append(_vals(line))
        elif line.startswith(".dw"):
            continue
        elif line.endswith(":"):
            break
    return rows


class MagicEffectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = read("spark.inc")
        cls.athena = read("athena_spr.inc")
        cls.kensou = read("kensou_spr.inc")
        cls.chin = read("chin_spr.inc")

    def test_spark_labels_have_cells(self):
        for label in ("MagicOrbA", "MagicOrbK", "Bottle"):
            self.assertIn(label + ":", self.spark)
            start = self.spark.index(label + ":")
            block = self.spark[start:self.spark.index("f0:", start) + 4]
            # label -> one frame row `.db ticks,count`; count must be >= 1
            m = re.search(r"f0:\s*\n\s*\.db (\d+),(\d+)", self.spark[start:])
            self.assertIsNotNone(m, label)
            self.assertGreaterEqual(int(m.group(2)), 1, label)

    def test_explod_rows_use_the_new_clips(self):
        self.assertTrue(any(row[0] == 6 for row in exp_rows(self.athena, "athenaExpTab")))
        self.assertTrue(any(row[0] == 7 for row in exp_rows(self.kensou, "kensouExpTab")))
        self.assertTrue(any(row[0] == 8 for row in exp_rows(self.chin, "chinExpTab")))

    def test_athena_and_kensou_acts_emit_the_effect(self):
        for text, sid in ((self.athena, 49), (self.athena, 85),
                          (self.kensou, 48), (self.kensou, 85)):
            rows = db_rows(text, f"{'athena' if text is self.athena else 'kensou'}Act{sid}")
            self.assertTrue(any(row[1] == 14 for row in rows), (sid, rows))

    def test_chin_bottle_follows_each_sip(self):
        # ExpTab row 1 is the Bottle; op14 must fire at the eight sip times.
        rows = db_rows(self.chin, "chinAct75")
        bottle = [row for row in rows if row[1] == 14 and row[2] == 1]
        self.assertEqual(len(bottle), 8, bottle)
        sip_times = {row[0] & 0x7F for row in bottle}
        self.assertTrue({8, 20, 30, 40, 50, 60, 70, 80} <= sip_times,
                        sip_times)
        drain = [row for row in rows if row[1] == 3]
        self.assertEqual(len(drain), 8, drain)
        self.assertEqual(drain[0][2], 0xF8)       # -8 life


if __name__ == "__main__":
    unittest.main()
