"""Static regression for Chun-Li's five-hit Hyakuretsu Kyaku.

The compiled state must use the strong 1205 clip (45 frames, six attack
boxes), carry soft MoveHitReset rows (op18 arg 1) so the flurry counter
survives, and leave the knockdown bit clear until MoveHitFinisher forces it
on the fifth contact.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "gen_fight"


def read(name):
    path = OUT / name
    if not path.exists():
        raise unittest.SkipTest("run tools/build_fight.py first")
    return path.read_text()


def rows(text, label):
    start = text.index(label + ":")
    out = []
    for line in text[start:].splitlines()[1:]:
        line = line.strip()
        if not line.startswith(".db"):
            break
        body = line.split(".db", 1)[1]
        vals = [int(v.strip().replace("$", "0x"), 0)
                for v in body.split(",")]
        if vals and vals[0] == 0xFF:
            break
        out.append(vals)
    return out


def words(text, label):
    start = text.index(label + ":")
    out = []
    for line in text[start:].splitlines()[1:]:
        line = line.strip()
        if not line.startswith(".dw"):
            break
        out += [int(v.strip().replace("$", "0x"), 0)
                for v in line.split(".dw", 1)[1].split(",") if v.strip()]
    return out


class ChunLiHyakuretsuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read("chunli_spr.inc")

    def test_uses_the_strong_six_attack_clip(self):
        header = rows(self.text, "chunliAnim52")[0]
        self.assertGreaterEqual(header[0], 45)

    def test_soft_resets_keep_the_flurry_counter(self):
        act = [tuple(r[:3]) for r in rows(self.text, "chunliAct52")]
        for frame in (15, 19, 23, 27):
            self.assertIn((frame, 18, 1), act,
                          f"missing soft reset at frame {frame}")

    def test_first_four_hits_do_not_set_the_knockdown_bit(self):
        flags = words(self.text, "chunliFlagsTab")
        self.assertEqual(flags[52] & 1, 0)

    def test_per_hit_damage_is_a_multi_hit_value(self):
        damage = words(self.text, "chunliDamageTab")
        self.assertGreaterEqual(damage[52], 4)
        self.assertLessEqual(damage[52], 12)


if __name__ == "__main__":
    unittest.main()
