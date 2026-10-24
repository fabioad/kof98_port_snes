import os
import re
import statistics
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import ROOT  # noqa: E402

NORMAL_SIDS = (5, 6, 7, 8, 19, 20, 21, 22, 23, 24, 25, 26)
# Imported fighters whose source scale produced near-one-hit-KO normals.
NORMALIZED = (
    "athena", "billy", "brian", "chang", "chin", "chizuru", "choi",
    "chris", "chunli", "heavyd", "king", "leona", "lucky", "mai",
    "mary", "mature", "shermie", "vice",
)


def damage_tab(name):
    path = os.path.join(ROOT, "build/gen_fight", name + "_spr.inc")
    text = open(path, encoding="utf-8").read()
    start = text.index(name + "DamageTab:") 
    vals = []
    for line in text[start:].splitlines()[1:]:
        m = re.match(r"\s*\.dw\s+(\d+)\s*$", line)
        if not m:
            break
        vals.append(int(m.group(1)))
    return vals


class DamageNormalizationTests(unittest.TestCase):
    def test_kyo_is_the_reference_baseline(self):
        vals = damage_tab("kyo")
        normals = [vals[sid] for sid in NORMAL_SIDS if sid < len(vals) and vals[sid]]
        self.assertEqual(statistics.median(normals), 18)

    def test_billy_no_longer_one_hit_kos(self):
        vals = damage_tab("billy")
        normals = [vals[sid] for sid in NORMAL_SIDS if sid < len(vals) and vals[sid]]
        self.assertEqual(statistics.median(normals), 18)
        self.assertLessEqual(max(vals), 63)

    def test_other_high_damage_imports_are_normalized(self):
        kyo_max = max(damage_tab("kyo"))
        cap = kyo_max * 1.25
        for name in NORMALIZED:
            vals = damage_tab(name)
            normals = [vals[sid] for sid in NORMAL_SIDS
                       if sid < len(vals) and vals[sid]]
            self.assertTrue(normals, name)
            self.assertLessEqual(statistics.median(normals), 21, name)
            self.assertLessEqual(max(vals), cap, (name, max(vals), cap))


if __name__ == "__main__":
    unittest.main()
