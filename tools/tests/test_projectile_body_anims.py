import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import CHARS, parse_air

ASSET_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def load_air(char):
    return parse_air(os.path.join(ASSET_ROOT, CHARS[char]["air"]))


def sprite_ids(frames):
    return [(g, n) for g, n, *_ in frames]


class ProjectileBodyAnimTests(unittest.TestCase):
    def test_kyo_yamibarai_uses_body_launch_anims(self):
        anims = CHARS["kyo"]["anims"]
        self.assertEqual(anims[48], 1000)
        self.assertEqual(anims[49], 1010)

    def test_iori_yamibarai_uses_body_launch_anims(self):
        anims = CHARS["iori"]["anims"]
        self.assertEqual(anims[48], 1000)
        self.assertEqual(anims[49], 1010)

    def test_launch_anims_have_multiple_distinct_body_sprites(self):
        for char in ("kyo", "iori"):
            air = load_air(char)
            for action in (1000, 1010):
                self.assertIn(action, air, f"{char} AIR action {action}")
                frames, _ = air[action]
                self.assertGreaterEqual(len(set(sprite_ids(frames))), 3,
                                        f"{char} action {action} sprites")

    def test_projectile_effect_clips_are_separate_actions(self):
        iori_fx, _ = load_air("iori")[1001]
        self.assertEqual({g for g, _ in sprite_ids(iori_fx)}, {1001})
        kyo_fx, _ = load_air("kyo")[1005]
        self.assertEqual({g for g, _ in sprite_ids(kyo_fx)}, {1005})
        # neither body launch anim may point at the effect-only clip
        self.assertNotEqual(CHARS["iori"]["anims"][48], 1001)
        self.assertNotEqual(CHARS["iori"]["anims"][49], 1001)
        self.assertNotEqual(CHARS["kyo"]["anims"][48], 1005)
        self.assertNotEqual(CHARS["kyo"]["anims"][49], 1005)

    def test_yuri_kouken_frames_come_from_original_explod_actions(self):
        from calibration import projectiles
        air = load_air("yuri")
        actions = projectiles.PROJECTILE_ACTION_SEQUENCES["yuri"]
        self.assertEqual(actions, (2010, 2011, 2012, 2013, 2014, 2015))
        for action in actions:
            frames, _ = air[action]
            self.assertEqual(len(frames), 1)
            self.assertEqual(sprite_ids(frames), [(2010, action - 2010)])
        # The old mapping drove a red slash sequence, not the fireball.
        self.assertNotIn(10000, actions)
        self.assertNotEqual(CHARS["yuri"]["anims"][48], 10000)


if __name__ == "__main__":
    unittest.main()
