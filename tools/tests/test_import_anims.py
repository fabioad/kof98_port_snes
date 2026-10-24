import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import parse_air, resolve_import_anims
from newroster import NEW_CHARS


class ImportAnimTests(unittest.TestCase):
    def test_missing_attack_uses_nearby_action_not_stand(self):
        frame = (0, 0, 0, 0, 5, "", [], [])
        second = (0, 1, 0, 0, 5, "", [], [])
        air = {47: ([frame], 0), 2100: ([frame, second], 0),
               2200: ([frame, second], 0), 240: ([frame, second], 0)}
        cfg = {"anims": {7: 47, 47: 47, 48: 47, 52: 47, 85: 47},
               "moves": {7: 230, 47: 160, 48: 2050, 52: 2250, 85: 3000}}
        result = resolve_import_anims(cfg, air)
        self.assertEqual([result[s] for s in (7, 47, 48, 52, 85)],
                         [240, 47, 2100, 2200, 47])
        self.assertEqual(cfg["anims"][48], 47)

    def test_real_imported_missing_action(self):
        cfg = NEW_CHARS["kensou"]
        air = parse_air(os.path.join(os.path.dirname(__file__), "..", "..",
                                     cfg["air"]))
        result = resolve_import_anims(cfg, air)
        self.assertNotEqual(result[48], 47)
        self.assertNotEqual(result[52], 47)
        self.assertEqual(result[50], cfg["anims"][50])


if __name__ == "__main__":
    unittest.main()
