import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import CHARGE_ANIMS, CHARS, charge_frames, parse_air


class ChargeAnimTests(unittest.TestCase):
    def test_charge_uses_nonstand_sprites_and_no_attack_boxes(self):
        self.assertTrue(CHARGE_ANIMS)
        self.assertTrue(set(CHARGE_ANIMS) <= set(CHARS))
        for name, (action, element) in CHARGE_ANIMS.items():
            with self.subTest(character=name):
                cfg = CHARS[name]
                air = parse_air(cfg["air"])
                frames, loop = charge_frames(name, air, cfg["anims"][97])
                self.assertTrue(frames)
                self.assertTrue(all(g >= 0 and n >= 0 for g, n, *_ in frames))
                self.assertTrue(all(not f[6] for f in frames))
                stand = {(g, n) for g, n, *_ in air[cfg["anims"][0]][0]}
                self.assertTrue(any((g, n) not in stand
                                    for g, n, *_ in frames))
                if element is not None:
                    self.assertEqual(len(frames), 1)
                    self.assertEqual(frames[0][:2],
                                     air[action][0][element][:2])
                    self.assertEqual(frames[0][4], 255)
                    self.assertEqual(loop, 0)

    def test_existing_charge_action_is_unchanged(self):
        cfg = CHARS["kyo"]
        air = parse_air(cfg["air"])
        frames, loop = charge_frames("kyo", air, cfg["anims"][97])
        self.assertEqual([f[:6] for f in frames],
                         [f[:6] for f in air[cfg["anims"][97]][0]])
        self.assertEqual(loop, air[cfg["anims"][97]][1])


if __name__ == "__main__":
    unittest.main()
