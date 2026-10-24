"""Input calibrator: physical pad layout and per-character overrides."""
import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import build_fight as bf  # noqa: E402


PHYSICAL_LAYOUT = {
    "x": "Y",      # weak punch
    "y": "X",      # strong punch
    "a": "B",      # weak kick
    "b": "A",      # strong kick
    "c": "L",      # dodge / rolls
    "z": "R",      # blowback
}


def _profile_data():
    path = os.path.join(bf.ROOT, "assets", "calibration",
                        "input_profiles.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class InputButtonCalibrationTests(unittest.TestCase):
    def test_calibrator_default_is_the_physical_layout(self):
        data = _profile_data()
        self.assertEqual(PHYSICAL_LAYOUT, data["buttons"]["default"])
        self.assertIsInstance(data["buttons"]["characters"], dict)

    def test_default_matches_the_global_character_layout(self):
        masks = {key: bf.SNES_BTN_MASK[value]
                 for key, value in PHYSICAL_LAYOUT.items()}
        for name, cfg in bf.CHARS.items():
            with self.subTest(char=name):
                for key, mask in masks.items():
                    self.assertEqual(mask, cfg["buttons"][key], key)

    def test_character_override_merges_over_the_default(self):
        layout = bf.button_layout({
            "buttons": {
                "default": PHYSICAL_LAYOUT,
                "characters": {"example": {"a": "X", "b": "Y"}},
            }
        }, "example")
        self.assertEqual("X", layout["a"])
        self.assertEqual("Y", layout["b"])
        self.assertEqual("Y", layout["x"])      # untouched default
        self.assertEqual("R", layout["z"])
        self.assertEqual(PHYSICAL_LAYOUT,
                         bf.button_layout({"buttons": {"default":
                                                       PHYSICAL_LAYOUT}},
                                          "example"))

    def test_apply_accepts_labels_and_raw_masks(self):
        cfg = {"buttons": {}}
        bf.apply_button_calibration(cfg, {"x": "Y", "z": 0x0010})
        self.assertEqual(bf.SNES_BTN_MASK["Y"], cfg["buttons"]["x"])
        self.assertEqual(0x0010, cfg["buttons"]["z"])

    def test_apply_rejects_unknown_buttons_and_labels(self):
        with self.assertRaises(ValueError):
            bf.apply_button_calibration({}, {"nope": "Y"})
        with self.assertRaises(ValueError):
            bf.apply_button_calibration({}, {"x": "Q"})
        with self.assertRaises(ValueError):
            bf.apply_button_calibration({}, {"x": 0})

    def test_resolve_applies_default_and_returns_assigned_timing(self):
        cfg = copy.deepcopy(bf.CHARS["terry"])
        cfg["buttons"] = {}
        profile = bf.resolve_input_calibration("terry", cfg)
        self.assertIsNotNone(profile)
        self.assertEqual(18, profile["special_default_frames"])
        for key, value in PHYSICAL_LAYOUT.items():
            self.assertEqual(bf.SNES_BTN_MASK[value], cfg["buttons"][key], key)

    def test_resolve_applies_default_without_timing_profile(self):
        cfg = copy.deepcopy(bf.CHARS["kyo"])
        cfg["buttons"] = {}
        self.assertIsNone(bf.resolve_input_calibration("kyo", cfg))
        self.assertEqual(bf.SNES_BTN_MASK["Y"], cfg["buttons"]["x"])
        self.assertEqual(bf.SNES_BTN_MASK["A"], cfg["buttons"]["b"])


if __name__ == "__main__":
    unittest.main()
