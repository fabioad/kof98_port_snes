"""Point-blank hit guarantees must stay wired.

Imported hurt boxes can sit just beyond a short jab's authored reach, and a
pinned overlap can leave a fighter facing away.  The engine extends every
attacker's box to a 20 px forward floor and turns close attacks toward the
opponent during startup.  This keeps the two helper calls from being lost in
a future engine edit.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIGHT = ROOT / "src/engine/fight.asm"


class CloseHitTests(unittest.TestCase):
    def test_reach_floor_is_wired(self):
        text = FIGHT.read_text()
        self.assertIn("    jsl MinReachBox", text)
        self.assertIn("MinReachBox:", text)
        self.assertIn("adc #20.w", text)

    def test_close_attacks_turn_toward_the_opponent(self):
        text = FIGHT.read_text()
        self.assertIn("    jsl FaceCloseAttack", text)
        self.assertIn("FaceCloseAttack:", text)
        self.assertIn("FCA_ok:", text)


if __name__ == "__main__":
    unittest.main()
