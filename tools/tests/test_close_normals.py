import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_fight as bf
import close_normals as cn


class CloseNormalTests(unittest.TestCase):
    def compile(self, name):
        cfg = bf.CHARS[name]
        parsed = bf.parse_cns(bf.asset_path(cfg['cns']), cfg.get('coord_scale', 1),
                              cfg.get('damage_scale', 1), char=name,
                              char_scale=bf.char_scale_for(name, cfg))
        rows = [parsed[0].get(cfg['moves'].get(sid), {}) for sid in range(9)]
        cn.profiles(name, cfg, parsed[0], parsed[8], rows,
                    bf.limit_normal_pushback, parsed[3], parsed[4])
        return cn.ROWS[name]

    def test_terry_hp_has_two_real_contacts_not_zero_damage_alternative(self):
        row = self.compile('terry')[1]
        self.assertEqual(row['source'], 215)
        self.assertEqual(row['contacts'], 2)
        self.assertEqual(row['words'][2], 18)
        self.assertGreater(row['words'][6], 0) # final-contact pushback retained

    def test_other_mode_animation_does_not_add_a_contact(self):
        # Kim 235 has one hit. Alternate mode anim 236 has two.
        row = self.compile('kim')[2]
        self.assertEqual(row['contacts'], 1)

    def test_roster_profiles_fit_and_do_not_invent_missing_moves(self):
        for name in bf.CHARS:
            with self.subTest(name=name):
                rows = self.compile(name)
                self.assertEqual(len(rows), 4)
                for row in rows:
                    self.assertEqual(len(row['words']), 16)
                    self.assertGreaterEqual(row['contacts'], 1)
                    self.assertLessEqual(row['contacts'], 3)
                    if row['source'] is None:
                        self.assertFalse(row['enabled'])
                    if row['enabled']:
                        self.assertGreater(row['words'][2], 0)
                        self.assertTrue(row['words'][13] & 0x2000) # no air guard


if __name__ == '__main__':
    unittest.main()
