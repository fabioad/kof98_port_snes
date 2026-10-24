import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# MUGEN jump / walk / run action numbers.  These are the clips the player
# looks at constantly; trimming them to two poses turns motion into a
# teleport.
MOTION_ACTIONS = {20, 21, 41, 42, 43, 100, 105}


def frames(path, action):
    from build_fight import parse_air
    anims = parse_air(path)
    return anims.get(action, ([], 0))[0]


class AirSmoothingTests(unittest.TestCase):
    def test_kyo_jump_keeps_source_frames(self):
        path = os.path.join(ROOT, "assets/characters/Kyo-KOF98/Kyo.air")
        self.assertEqual(len(frames(path, 42)), 7)

    def test_restored_motion_actions_keep_at_least_four_poses(self):
        """Every compiled motion clip with a source backup must keep its
        in-betweens.  Without this guard the 655-element trim budget folds a
        seven-pose jump back into a two-pose hold."""
        from build_fight import CHARS, parse_air
        for name, cfg in CHARS.items():
            air = os.path.join(ROOT, cfg["air"])
            orig = air + ".orig"
            if not os.path.exists(orig):
                continue
            compiled = set(cfg.get("anims", {}).values())
            cur = parse_air(air)
            src = parse_air(orig)
            for action in sorted(MOTION_ACTIONS & compiled):
                if action not in cur or action not in src:
                    continue
                with self.subTest(character=name, action=action):
                    want = len(src[action][0])
                    got = len(cur[action][0])
                    if want >= 4:
                        self.assertGreaterEqual(got, 4)
                    else:
                        self.assertEqual(got, want)

    def test_trim_air_never_thins_motion(self):
        from trim_air import MOTION_ANIMS, plan_action
        elem = lambda num: type("E", (), {
            "num": num, "elems": [object()] * 7, "loop_idx": -1})()
        for action in MOTION_ANIMS:
            self.assertEqual(plan_action(elem(action), 0, None, 1.0), set())

    def test_trim_air_keeps_four_frames(self):
        from trim_air import plan_action
        elems = []
        for i in range(7):
            e = type("E", (), {})()
            e.g, e.n, e.t, e.atk = 10, i, 4, False
            elems.append(e)
        act = type("E", (), {"num": 9999, "elems": elems, "loop_idx": -1})()
        drop = plan_action(act, 0, None, 1.0)
        self.assertLessEqual(len(drop), 3)


if __name__ == "__main__":
    unittest.main()
