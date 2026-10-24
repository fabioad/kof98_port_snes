import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_char_cfg import synth_air


def fake_sff(*sprites):
    return SimpleNamespace(
        sprites=[SimpleNamespace(group=g, number=n, ax=0, ay=0, w=32, h=48)
                 for g, n in sprites])


class SynthAirTests(unittest.TestCase):
    def test_emitted_refs_are_real_sprites(self):
        # sparse group 0 (numbers 2 and 7) plus nonconsecutive group 200
        sff = fake_sff((0, 2), (0, 7), (200, 3), (200, 9))
        with tempfile.TemporaryDirectory() as td, \
                mock.patch("sff.Sff", return_value=sff):
            synth_air(td, "x.sff", "out.air")
            txt = open(os.path.join(td, "out.air")).read()
        # every "g, n, x, y, t" element line must reference a real sprite
        elems = {}
        action = None
        for line in txt.splitlines():
            if line.startswith("[Begin Action "):
                action = int(line.split()[-1].rstrip("]"))
                elems[action] = []
            elif "," in line and action is not None:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == 5:
                    elems[action].append((int(parts[0]), int(parts[1])))
        real = {(0, 2), (0, 7), (200, 3), (200, 9)}
        for act, refs in elems.items():
            with self.subTest(action=act):
                self.assertTrue(all(r in real for r in refs))
        # group 0 action uses the real numbers, not a renumbered 0..n range
        self.assertEqual(sorted(elems[0]), [(0, 2), (0, 7)])
        # nonconsecutive group preserved verbatim
        self.assertEqual(sorted(elems[200]), [(200, 3), (200, 9)])
        # alias action 47 points at the stand sprites (group 0), not group 47
        self.assertEqual(sorted(elems[47]), [(0, 2), (0, 7)])


MIXED_CASE_AIR = """[Begin Action 0]
0, 0, 0, 0, 10
0, 1, 0, 0, 8

[begin action 1000]
1000, 0, 0, 0, 5

[BEGIN  ACTION   1010]
1010, 0, 0, 0, 3
"""


class AirParserCaseTests(unittest.TestCase):
    """Real MUGEN AIRs use lowercase '[Begin action N]'; both parsers must
    accept mixed case/whitespace so complete source files aren't mistaken
    for stubs and synthesized over."""

    def test_parse_air_ids_case_insensitive(self):
        from gen_char_cfg import parse_air_ids
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "x.air")
            open(p, "w").write(MIXED_CASE_AIR)
            self.assertEqual(parse_air_ids(p), {0, 1000, 1010})

    def test_build_fight_parse_air_case_insensitive(self):
        from build_fight import parse_air
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "x.air")
            open(p, "w").write(MIXED_CASE_AIR)
            anims = parse_air(p)
        self.assertEqual(set(anims), {0, 1000, 1010})
        self.assertEqual([f[4] for f in anims[0][0]], [10, 8])
        self.assertEqual([f[4] for f in anims[1000][0]], [5])
        self.assertEqual([f[4] for f in anims[1010][0]], [3])


class RestoredSourceAirTests(unittest.TestCase):
    EXPECTED = {
        "kensou": {
            "air": "assets/characters/Kensou/kensou.air",
            "anims": {7: 230, 48: 2050, 49: 2050, 52: 2250, 53: 2250,
                      55: 1140, 57: 1010, 59: 1230, 63: 1425, 65: 1525,
                      74: 800, 75: 800, 94: 775},
        },
        "shermie": {
            "air": "assets/characters/Shermie-KOF98/shermie.air",
            "anims": {48: 2200, 49: 2250, 52: 2150, 53: 2150, 54: 1400,
                      55: 1450, 85: 8050, 86: 8050, 94: 775},
        },
        "chris": {
            "air": "assets/characters/Chris-KOF98/chris.air",
            "anims": {48: 2250, 49: 2250, 55: 2150, 85: 8150, 86: 8150,
                      94: 775},
        },
    }

    def test_cfgs_use_original_air_and_source_backed_anims(self):
        from newroster import NEW_CHARS
        for name, exp in self.EXPECTED.items():
            with self.subTest(character=name):
                cfg = NEW_CHARS[name]
                self.assertEqual(cfg["air"], exp["air"])
                for sid, action in exp["anims"].items():
                    self.assertEqual(cfg["anims"][sid], action,
                                     f"{name} sid {sid}")

    def test_referenced_actions_exist_in_source_air(self):
        from build_fight import parse_air
        from newroster import NEW_CHARS
        root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        for name in self.EXPECTED:
            with self.subTest(character=name):
                cfg = NEW_CHARS[name]
                anims = parse_air(os.path.join(root, cfg["air"]))
                for sid, action in self.EXPECTED[name]["anims"].items():
                    self.assertIn(action, anims, f"{name} sid {sid}")
                    self.assertTrue(anims[action][0],
                                    f"{name} action {action} empty")


if __name__ == "__main__":
    unittest.main()
