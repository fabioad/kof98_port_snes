import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import build_fight
from build_fight import CHARS
from calibration import projectiles


class ProjectileCalibrationTests(unittest.TestCase):
    def test_body_animations_drive_kyo_iori_sids(self):
        self.assertEqual(projectiles.BODY_ANIMATIONS,
                         {"kyo": {48: 1000, 49: 1010},
                          "iori": {48: 1000, 49: 1010}})
        for name in ("kyo", "iori"):
            anims = CHARS[name]["anims"]
            self.assertEqual(anims[48], 1000)
            self.assertEqual(anims[49], 1010)

    def test_body_and_effect_actions_stay_separate(self):
        # the body launch anims never point at the projectile effect clip
        for name in ("kyo", "iori"):
            self.assertTrue(
                set(projectiles.BODY_ANIMATIONS[name].values()).isdisjoint(
                    {projectiles.PROJECTILE_ACTIONS[name]}))
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["iori"], 1001)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["kyo"], 1005)

    def test_shared_render_constants(self):
        self.assertEqual(projectiles.PROJECTILE_ZOOM, 2)
        self.assertEqual(projectiles.GROUND_PROJECTILES,
                         {"terry", "kyo", "iori", "kyonests", "kyoash",
                          "andy", "daimon", "geese", "leona", "mrbig",
                          "ralf", "shingo"})
        self.assertEqual(projectiles.PROJECTILE_SOURCE_PALETTES["iori"], 4)

    def test_yuri_kouken_uses_source_explod_sequence(self):
        # State 405/406 explods 2010+animelemno(0)-1 every tick; action 10000
        # is a different slash effect and must not drive the fireball.
        self.assertEqual(projectiles.PROJECTILE_ACTION_SEQUENCES["yuri"],
                         (2010, 2011, 2012, 2013, 2014, 2015))
        self.assertNotIn("yuri", projectiles.PROJECTILE_ACTIONS)
        self.assertEqual(projectiles.PROJECTILE_SOURCE_PALETTES["yuri"], 0)
        self.assertEqual(projectiles.PROJECTILE_ZOOM_BY_CHAR["yuri"], 1)

    def test_restored_projectile_art_actions(self):
        # Source action that actually carries the visible effect, not the
        # blank helper/projanim timeline.
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["saisyu"], 1025)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["benimaru"], 1002)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["geese"], 1053)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["leona"], 1115)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["mrbig"], 1020)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["eiji"], 3002)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["andy"], 1157)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["daimon"], 6045)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["ralf"], 11011)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["shermie"], 7220)
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["yamazaki"], 3141)

    def test_saisyu_reuses_kyo_projectile_art(self):
        # Saisyu's shot shares Kyo's compiled Yami Barai clip instead of
        # spending a separate atlas on the same flame streak.
        self.assertEqual(projectiles.PROJECTILE_FX_ALIAS["saisyu"], "kyo")
        self.assertEqual(CHARS["saisyu"]["projfx_alias"], "kyo")

    def test_false_positive_shots_are_excluded(self):
        # These source helpers are melee follow-ups, dives or teleports; the
        # generator used to turn their dash HitDefs into invisible shots.
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["billy"], (50, 53))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["benimaru"], (56, 57))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["choi"], (50, 51, 86))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["kim"], (53, 85, 86))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["mary"], (54, 55, 87))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["vega"],
                         (48, 49, 52, 53, 85, 86))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["yashiro"],
                         (48, 49, 85, 86))
        # Robert's Ryuga anti-airs chain into airborne follow-ups whose
        # HitDef inherits the jump VelSet, so they used to launch a shot.
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["robert"], (50, 51))

    def test_extra_projectile_moves_are_wired(self):
        self.assertEqual(build_fight.EXTRA_PROJECTILE_MOVES["andy"], {58: 1150})
        self.assertEqual(build_fight.EXTRA_PROJECTILE_MOVES["daimon"], {58: 300})
        self.assertEqual(build_fight.EXTRA_PROJECTILE_MOVES["shermie"],
                         {58: 7200, 59: 7300})
        self.assertEqual(build_fight.EXTRA_PROJECTILE_MOVES["yamazaki"],
                         {58: 1215, 85: 3140})
        self.assertEqual(projectiles.PROJECTILE_CALIBRATION["shermie"],
                         {58: (0x0100, 20), 59: (0x0400, 12)})

    def test_calibration_rows_match_generator_table(self):
        self.assertIs(build_fight.PROJECTILE_CALIBRATION,
                      projectiles.PROJECTILE_CALIBRATION)
        self.assertEqual(projectiles.PROJECTILE_CALIBRATION["iori"],
                         {48: (0x02C0, 12), 49: (0x03C0, 16)})
        self.assertEqual(projectiles.PROJECTILE_CALIBRATION["kyo"],
                         {48: (0x0300, 14), 49: (0x0400, 18)})

    def test_projectile_guard_mask_is_per_shot(self):
        # Projectile controllers carry a plain guardflag (MUGEN's default is
        # "MA").  An explicit empty value or guard.dist = 0 makes the shot
        # unblockable; the engine stores H/M/L/A<<4 like HitDef FlagsTab.
        self.assertEqual(build_fight.guard_flag_mask("MA"), 0x0A)
        self.assertEqual(build_fight.guard_flag_mask("h"), 0x01)
        self.assertEqual(build_fight.guard_flag_mask(""), 0x00)
        statedefs = {
            1000: [{"type": "Projectile", "velocity": "5", "damage": "70",
                    "guardflag": "H", "triggers": []}],
            1001: [{"type": "Projectile", "velocity": "5", "damage": "70",
                    "triggers": []}],
            1002: [{"type": "Projectile", "velocity": "5", "damage": "70",
                    "guardflag": "", "triggers": []}],
            1003: [{"type": "Projectile", "velocity": "5", "damage": "70",
                    "guardflag": "L", "guard.dist": "0",
                    "triggers": []}],
        }
        rows = build_fight.projectile_rules(
            statedefs, {},
            {48: 1000, 49: 1001, 50: 1002, 51: 1003}, 1)
        self.assertEqual(rows[48][3], 0x01)     # high only: stand guard
        self.assertEqual(rows[49][3], 0x0A)     # default MA
        self.assertEqual(rows[50][3], 0x00)     # explicitly unblockable
        self.assertEqual(rows[51][3], 0x00)     # guard.dist = 0

    def test_projectile_recovery_only_shortens_the_tail(self):
        # Benimaru's Raikouken: startup + release keep their ticks, the long
        # follow-through is rescaled so the fighter can act again.
        ticks = [1, 2, 2, 4, 2, 4, 27, 3, 3, 7]
        frames = [(0, 0, 0, 0, t, "", [], []) for t in ticks]
        capped = build_fight.cap_projectile_recovery(frames, 2, 24)
        self.assertEqual(len(capped), len(frames))
        self.assertEqual([f[4] for f in capped[:3]], ticks[:3])
        self.assertEqual(sum(f[4] for f in capped[3:]), 24)
        self.assertGreater(capped[6][4], capped[7][4])

    def test_projectile_recovery_leaves_holds_and_hitboxes_alone(self):
        frames = [(0, 0, 0, 0, t, "", [], []) for t in (2, 2, 40, 255)]
        self.assertIs(build_fight.cap_projectile_recovery(frames, 1, 12),
                      frames)
        frames = [(0, 0, 0, 0, t, "", [], []) for t in (2, 2, 40, 40)]
        frames[-1] = (0, 0, 0, 0, 40, "", [[1, 2, 3, 4]], [])
        self.assertIs(build_fight.cap_projectile_recovery(frames, 1, 12),
                      frames)


if __name__ == "__main__":
    unittest.main()
