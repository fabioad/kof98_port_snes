import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_fight import CHARS, cmd_rules, parse_air, parse_command_defs

ROOT = Path(__file__).resolve().parents[2]


class TerryCalibrationTests(unittest.TestCase):
    def test_fast_sprite_path_and_power_waves(self):
        cfg = CHARS["terry"]
        self.assertFalse(cfg["msu"])
        self.assertEqual(cfg["projs"][58], (0x0300, 22, 4))
        self.assertEqual(cfg["projs"][59], (0x0400, 26, 4))
        anims = parse_air(ROOT / cfg["air"])
        for sid in (5, 6, 7, 8, 45, 48, 50, 58, 59):
            with self.subTest(sid=sid):
                self.assertGreaterEqual(len(anims[cfg["anims"][sid]][0]), 3)

    def test_movement_and_wave_commands_are_wired(self):
        cfg = CHARS["terry"]
        path = ROOT / cfg["cmd"]
        defs = parse_command_defs(path)
        wired = {state: sid for sid, state in cfg["moves"].items()}
        rules = cmd_rules(path, defs, wired)
        by_sid = {rule["state"] for rule in rules}
        self.assertTrue({45, 46, 58, 59, 94, 95} <= by_sid)
        by_motion = {rule["motion"]: rule["state"] for rule in rules}
        self.assertEqual(by_motion["ESQ_L"], 69)
        self.assertEqual(by_motion["ESQ_F"], 95)
        self.assertEqual(by_motion["ESQ_B"], 94)


if __name__ == "__main__":
    unittest.main()
