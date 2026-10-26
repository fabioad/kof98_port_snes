import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
CHARS = ("clark", "andy", "benimaru", "daimon", "ralf")


def rows(path, label):
    with open(path) as source:
        lines = source.read().splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.startswith(label + ":"))
    out = []
    for line in lines[start + 1:]:
        if not line.startswith("    .db"):
            break
        body = line.split(".db", 1)[1].strip()
        if body.startswith("$FF"):
            break
        out.append(tuple(int(x.strip(), 0) for x in body.split(",")))
    return out


class DodgeVelocityRowsTests(unittest.TestCase):
    def test_forward_and_back_rolls_move(self):
        for name in CHARS:
            path = os.path.join(ROOT, "build", "gen_fight",
                                f"{name}_spr.inc")
            if not os.path.exists(path):
                self.skipTest("run build_fight.py first")
            # sid 94 = L+BACK, sid 95 = L+FWD.  op5 args are signed bytes
            # (facing-relative px/frame): -5 -> $FB, +5 -> $05.
            back = [r for r in rows(path, f"{name}Act94")
                    if r[1] == 5]
            fwd = [r for r in rows(path, f"{name}Act95")
                   if r[1] == 5]
            self.assertTrue(any(r[2] == 0xFB for r in back),
                            f"{name}: ESQ_B lost its backward velocity")
            self.assertTrue(any(r[2] == 0x05 for r in fwd),
                            f"{name}: ESQ_F lost its forward velocity")


if __name__ == "__main__":
    unittest.main()
