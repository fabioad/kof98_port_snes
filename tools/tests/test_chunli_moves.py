"""Static regressions for Chun-Li's Tenshou Kyaku and Kikouken.

The imported CNS drives both moves with AnimElemTime controllers.  The
generic ActTab builder used to skip those controllers, leaving Tenshou Kyaku
grounded; Kikouken's projectile also spawned on the engine's default third
frame instead of the source release frame.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INC = ROOT / "build/gen_fight/chunli_spr.inc"


class ChunliMoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not INC.exists():
            raise unittest.SkipTest("run tools/build_fight.py first")
        cls.text = INC.read_text()

    def _block(self, label, terminator="\nchunli"):
        start = self.text.index(label + ":")
        end = self.text.find(terminator, start + len(label) + 1)
        return self.text[start:end if end >= 0 else None]

    def test_tenshou_launch_velocity(self):
        block = self._block("chunliAct50")
        rows = [tuple(int(v) for v in m)
                for m in re.findall(r"\.db\s+(\d+),(\d+),(\d+),(\d+)",
                                    block)]
        # Frame 2 is the source's AnimElem 3: x=5, y=-4 px/tick (op15 stores
        # quarter-pixels, so -4 -> -16 -> $F0=240).  Frame 8 stops x.
        self.assertIn((2, 5, 5, 0), rows)
        self.assertIn((2, 15, 240, 0), rows)
        self.assertIn((8, 5, 0, 0), rows)
        # The AnimElemTime(3) < 0 NotHitBy window must arm at entry (0x80)
        # and clear on element 3, not arm late for the whole state.
        self.assertIn((128, 11, 255, 0), rows)
        self.assertIn((2, 11, 0, 0), rows)

    def test_tenshou_landing_state(self):
        block = self._block("chunliTransTab")
        self.assertIn(".db 50,51,1", block)   # fall -> state 1410 (sid 51)
        self.assertIn(".db 51,0,0", block)    # landing anim end -> stand

    def test_kikouken_projectile_release(self):
        block = self._block("chunliProjTab")
        rows = block.splitlines()[1:]
        row = [line for line in rows if line.strip().startswith(".db")][48]
        vals = []
        for token in row.split(".db", 1)[1].split(","):
            token = token.strip()
            vals.append(int(token[1:], 16) if token.startswith("$")
                        else int(token))
        vx = vals[0] | (vals[1] << 8)
        present = vals[5]
        guard_xoff = vals[4] & 0x0F
        self.assertEqual(vx, 0x0300)          # 3 px/tick forward
        self.assertTrue(present & 0x01)       # shot exists
        self.assertEqual((present >> 3) & 0x1F, 7)   # AnimElem 7 -> 0-based 6
        self.assertEqual(guard_xoff, 5)       # 40 px spawn offset


if __name__ == "__main__":
    unittest.main()
