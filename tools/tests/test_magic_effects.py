"""Static regressions for the magic bursts and Chin's drink bottle.

Athena/Kensou's big Explod bursts and Chin's Zake Attack were not wired, so
the moves played without the visible magic/gourd.  Athena and Kensou share a
2x2 burst clip; Chin's bottle is painted into the 350/850 sprite frames and
his drink throw also emits the 861 spray at each sip.
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


def spark_labels(text):
    start = text.index("SparkAnimTab:")
    block = text[start:text.index("SparkHit:", start)]
    return re.findall(r"\.dw (\w+)", block)


def exp_indexes(text, label, label_index):
    """ExpTab row numbers whose animation byte is the given spark label."""
    return {i for i, row in enumerate(exp_rows(text, label))
            if row[0] == label_index}


def air_groups(path, action):
    text = Path(path).read_text(errors="replace")
    start = text.index(f"[Begin Action {action}]")
    block = text[start:].split("\n", 1)[1].split("[Begin Action", 1)[0]
    return [int(g) for g in re.findall(r"^\s*(-?\d+),", block, re.M)]


class MagicEffectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = read("spark.inc")
        cls.athena = read("athena_spr.inc")
        cls.kensou = read("kensou_spr.inc")
        cls.chin = read("chin_spr.inc")
        cls.labels = spark_labels(cls.spark)

    def index_of(self, label):
        self.assertIn(label, self.labels)
        return self.labels.index(label)

    def test_shared_page_holds_the_effects(self):
        tiles = set(re.findall(r"\.dw \$(00[0-9A-F]{2})", self.spark))
        self.assertLessEqual(len(tiles), 16, sorted(tiles))
        for label in ("MagicBurst", "Bottle"):
            self.index_of(label)
        # The shared burst is a 2x2 block, not a one-cell dot.
        start = self.spark.index("MagicBurstf0:")
        m = re.search(r"\.db (\d+),(\d+)", self.spark[start:])
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(2)), 4)

    def test_explod_rows_use_the_new_clips(self):
        burst = self.index_of("MagicBurst")
        bottle = self.index_of("Bottle")
        self.assertTrue(any(row[0] == burst
                            for row in exp_rows(self.athena, "athenaExpTab")))
        self.assertTrue(any(row[0] == burst
                            for row in exp_rows(self.kensou, "kensouExpTab")))
        self.assertTrue(any(row[0] == bottle
                            for row in exp_rows(self.chin, "chinExpTab")))

    def test_athena_and_kensou_acts_emit_the_effect(self):
        burst = self.index_of("MagicBurst")
        for text, name, sid in ((self.athena, "athena", 49),
                                (self.athena, "athena", 85),
                                (self.kensou, "kensou", 48),
                                (self.kensou, "kensou", 85)):
            rows = db_rows(text, f"{name}Act{sid}")
            valid = exp_indexes(text, f"{name}ExpTab", burst)
            self.assertTrue(any(row[1] == 14 and row[2] in valid
                                for row in rows), (sid, rows))

    def test_chin_bottle_follows_each_sip(self):
        bottle = self.index_of("Bottle")
        rows = db_rows(self.chin, "chinAct75")
        valid = exp_indexes(self.chin, "chinExpTab", bottle)
        bottle_rows = [row for row in rows
                       if row[1] == 14 and row[2] in valid]
        self.assertEqual(len(bottle_rows), 8, bottle_rows)
        sip_times = {row[0] & 0x7F for row in bottle_rows}
        self.assertTrue({8, 20, 30, 40, 50, 60, 70, 80} <= sip_times,
                        sip_times)
        drain = [row for row in rows if row[1] == 3]
        self.assertEqual(len(drain), 8, drain)
        self.assertEqual(drain[0][2], 0xF8)       # -8 life

    def test_chin_zake_attack_plays_the_gourd_frames(self):
        # QCB+x/y reach states 1000/1100, whose first frames carry the
        # gourd-to-mouth poses (group 350).
        cmd = (ROOT / "assets/characters/chin-kofa/Chin_SNES.cmd").read_text(
            errors="replace")
        self.assertIn('name = "QCB_x"', cmd)
        self.assertIn('name = "QCB_y"', cmd)
        self.assertIn("value = 1000", cmd)
        self.assertIn("value = 1100", cmd)
        air = ROOT / "assets/characters/chin-kofa/Chin-KOFM.air"
        for action in (1000, 1100):
            groups = air_groups(air, action)
            self.assertIn(350, groups[:4], (action, groups[:8]))
            self.assertTrue(groups, action)
        for sid in (62, 65):
            self.assertTrue(db_rows(self.chin, f"chinAct{sid}"), sid)


if __name__ == "__main__":
    unittest.main()
