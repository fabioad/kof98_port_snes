"""Regression checks for the Chizuru/Lucky/King import fixes.

These three packages select normal animations from command-state variants
and use forward/back + button throws.  The generic importer used to alias
every kick to the same punch and wired the throw to x+y.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from build_fight import parse_cns  # noqa: E402
from newroster import NEW_CHARS  # noqa: E402


class NormalsThrowSoundTests(unittest.TestCase):
    def cfg(self, key):
        return NEW_CHARS[key]

    def test_chizuru_has_four_distinct_normals_per_posture(self):
        cfg = self.cfg("chizuru")
        stand = [cfg["moves"][sid] for sid in range(5, 9)]
        crouch = [cfg["moves"][sid] for sid in range(19, 23)]
        air = [cfg["moves"][sid] for sid in range(23, 27)]
        self.assertEqual(stand, [200, 202, 201, 203])
        self.assertEqual(crouch, [400, 402, 401, 403])
        self.assertEqual(air, [600, 601, 602, 603])
        self.assertEqual([cfg["anims"][sid] for sid in range(5, 9)],
                         [200, 220, 210, 230])
        self.assertEqual([cfg["anims"][sid] for sid in range(19, 23)],
                         [400, 420, 410, 430])
        self.assertEqual([cfg["anims"][sid] for sid in range(23, 27)],
                         [600, 620, 610, 630])

    def test_chizuru_throw_uses_direction_and_has_a_self_bind(self):
        cfg = self.cfg("chizuru")
        self.assertEqual(361, cfg["moves"][74])
        self.assertEqual(360, cfg["throw_self_bind"])
        cmd = open(os.path.join(ROOT, cfg["cmd"]), encoding="utf-8").read()
        self.assertIn("value = 361", cmd)
        self.assertIn('trigger1 = command = "holdfwd"', cmd)
        self.assertIn('trigger2 = command = "holdback"', cmd)

    def test_king_jump_normals_are_not_the_blowback_state(self):
        cfg = self.cfg("king")
        self.assertEqual([cfg["moves"][sid] for sid in range(23, 27)],
                         [500, 510, 520, 530])
        self.assertEqual([cfg["anims"][sid] for sid in range(23, 27)],
                         [500, 510, 520, 530])

    def test_lucky_normals_and_throw(self):
        cfg = self.cfg("lucky")
        self.assertEqual([cfg["moves"][sid] for sid in range(5, 9)],
                         [200, 240, 220, 260])
        self.assertEqual([cfg["moves"][sid] for sid in range(19, 23)],
                         [400, 440, 420, 460])
        self.assertEqual([cfg["moves"][sid] for sid in range(23, 27)],
                         [600, 640, 620, 660])
        self.assertEqual(310, cfg["moves"][74])

    def test_chizuru_hit_sounds_are_not_all_silent(self):
        cfg = self.cfg("chizuru")
        parsed = parse_cns(os.path.join(ROOT, cfg["cns"]), 1, 2.0)
        hitsnds = parsed[10]
        # S444,IfElse(...) used to fall through the numeric parser and emit
        # $FF (silent) for every normal/special.
        self.assertNotEqual(0xFF, hitsnds.get(200))
        self.assertEqual(4, hitsnds.get(200))
        # The throw HitDef declares hitsound = -1 and must stay silent.
        self.assertEqual(0xFF, hitsnds.get(360, 0xFF))


if __name__ == "__main__":
    unittest.main()
