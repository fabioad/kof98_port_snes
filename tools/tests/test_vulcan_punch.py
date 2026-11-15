"""Ralf/Clark Vulcan Punch: hitstun and pushback, never a forced launcher.

The source re-issues the HitDef on every contact.  The port keeps those
contacts with hard MoveHitReset rows (so MoveHitFinisher cannot force a
knockdown on the fifth hit) and clears the ground vertical velocity while
keeping the source air velocity for juggles.
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


def rows(text, label):
    start = text.index(label + ":")
    out = []
    for line in text[start:].splitlines()[1:]:
        line = line.strip()
        if not line.startswith(".db"):
            break
        body = line.split(".db", 1)[1]
        out.append([int(v.strip().replace("$", "0x"), 0)
                    for v in body.split(",")])
    return out


def signed(word):
    return word - 0x10000 if word & 0x8000 else word


class VulcanPunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {name: read(f"{name}_spr.inc")
                      for name in ("ralf", "clark")}

    def test_ground_hits_push_back_without_a_launch(self):
        for name, text in self.tables.items():
            hitvel = words(text, f"{name}HitVelTab")
            flags = words(text, f"{name}FlagsTab")
            for sid in (48, 49):
                gvx, gvy, avx, avy = hitvel[sid * 4:sid * 4 + 4]
                self.assertGreater(gvx, 0,
                                   f"{name} sid {sid}: no ground pushback")
                self.assertEqual(gvy, 0,
                                 f"{name} sid {sid}: ground launch not cleared")
                self.assertGreater(avx, 0,
                                   f"{name} sid {sid}: no air pushback")
                self.assertLess(signed(avy), 0,
                                f"{name} sid {sid}: air juggle lost")
                self.assertEqual(flags[sid] & 1, 0,
                                 f"{name} sid {sid}: knockdown bit set")

    def test_resets_are_hard_so_the_fifth_hit_never_forces_a_launcher(self):
        for name, text in self.tables.items():
            for sid in (48, 49):
                resets = [row for row in rows(text, f"{name}Act{sid}")
                          if len(row) > 2 and row[1] == 18]
                self.assertTrue(resets, f"{name} sid {sid}: no MoveHitReset")
                for row in resets:
                    self.assertEqual(row[2], 0,
                                     f"{name} sid {sid}: soft reset keeps "
                                     "MoveHitFinisher's knockdown counter")


if __name__ == "__main__":
    unittest.main()
