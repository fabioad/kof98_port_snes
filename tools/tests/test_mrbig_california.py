import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "build", "gen_fight", "mrbig_spr.inc")
SIDS = (53, 56, 57, 58, 59, 60)


def table(text, label):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.startswith(label + ":"))
    return lines[start + 1:start + 1 + 98]


class MrBigCaliforniaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(PATH):
            raise unittest.SkipTest("run build_fight.py first")
        with open(PATH) as source:
            cls.text = source.read()

    def test_slices_have_four_contacts(self):
        active = table(self.text, "mrbigActiveTab")
        damage = table(self.text, "mrbigDamageTab")
        flags = table(self.text, "mrbigFlagsTab")
        want = {53: (4, 6), 56: (1, 6), 57: (2, 7),
                58: (1, 7), 59: (4, 5)}
        for sid, (act, dmg) in want.items():
            self.assertIn(f".dw {act}", active[sid])
            self.assertIn(f".dw {dmg}", damage[sid])
        # Intermediate slice 57 must not knock the victim down before the
        # launcher; the final slice 58 must keep the fall flag.
        self.assertEqual(int(flags[57].split()[-1]), 21024)
        self.assertEqual(int(flags[58].split()[-1]), 21665)

    def test_chain_reaches_the_launcher(self):
        chain = {
            (52, 59), (53, 56), (59, 56), (56, 57), (57, 58), (58, 60),
        }
        rows = set()
        lines = self.text.splitlines()
        start = next(i for i, line in enumerate(lines)
                     if line.startswith("mrbigTransTab:"))
        for i in range(start + 1, len(lines) - 1, 2):
            row = lines[i].strip()
            if not row.startswith(".db"):
                break
            parts = row.split(".db", 1)[1].split(",")
            if parts[0].strip() == "$FF":
                break
            rows.add((int(parts[0]), int(parts[1])))
        self.assertTrue(chain <= rows, chain - rows)


if __name__ == "__main__":
    unittest.main()
