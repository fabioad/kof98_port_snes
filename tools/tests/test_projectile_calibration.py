import os
import re
import sys
import unittest
from pathlib import Path

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

    def test_mrbig_compiles_his_own_ground_blaster(self):
        # The Heavy D beam alias left the streaky source's transparent gaps
        # visible as coloured speckles over the white core.  Mr. Big's own
        # action 1020 is the flame wave and now gets its own atlas.
        self.assertNotIn("mrbig", projectiles.PROJECTILE_FX_ALIAS)
        self.assertNotIn("projfx_alias", CHARS["mrbig"])
        self.assertEqual(projectiles.PROJECTILE_ACTIONS["mrbig"], 1020)

    def test_false_positive_shots_are_excluded(self):
        # These source helpers are melee follow-ups, dives or teleports; the
        # generator used to turn their dash HitDefs into invisible shots.
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["billy"], (50, 53))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["benimaru"], (56, 57))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["choi"],
                         (50, 51, 86, 109, 111, 112, 116))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["kim"], (53, 85, 86))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["mary"], (54, 55, 87))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["vega"],
                         (48, 49, 52, 53, 85, 86))
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["yashiro"],
                         (48, 49, 85, 86))
        # Robert's Ryuga anti-airs chain into airborne follow-ups whose
        # HitDef inherits the jump VelSet, so they used to launch a shot.
        # 85/86 are the ranbu flurry/finish, also melee.
        self.assertEqual(build_fight.PROJECTILE_EXCLUDE["robert"],
                         (50, 51, 85, 86))

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
        # Iori's Yami Barai was converted to a melee flame, so it has no
        # projectile calibration row anymore.
        self.assertNotIn("iori", projectiles.PROJECTILE_CALIBRATION)
        self.assertIn(48, build_fight.PROJECTILE_EXCLUDE["iori"])
        self.assertIn(49, build_fight.PROJECTILE_EXCLUDE["iori"])
        self.assertEqual(projectiles.PROJECTILE_CALIBRATION["kyo"],
                         {48: (0x0300, 14), 49: (0x0400, 18)})

    def test_andy_qcb_hishouken_is_a_short_range_burst(self):
        # QCB+P is states 1100/1110 (sids 52/53).  The helper 1105 HitDef is
        # a stationary palm burst ~80 px ahead, not the QCF+c travelling
        # projectile (sid 58).  The guard low nibble carries the 80/8 = 10
        # spawn-offset code; 8-15 also mark the short 12-tick lifetime.
        self.assertEqual(projectiles.PROJECTILE_X_OFFSET["andy"],
                         {52: 80, 53: 80})
        self.assertEqual(projectiles.PROJECTILE_RELEASE["andy"],
                         {52: 4, 53: 5, 58: 3, 63: 3})
        self.assertEqual(projectiles.PROJECTILE_CALIBRATION["andy"],
                         {52: (0x0000, 26), 53: (0x0000, 28),
                          58: (0x0400, 14)})
        # The ROM budget keeps the compiled Ko'ou Ken orb; only the front
        # shot's range/timing differ from the back projectile.
        self.assertEqual(projectiles.PROJECTILE_FX_ALIAS["andy"], "yuri")
        spr = (Path(build_fight.ROOT) / "build/gen_fight/andy_spr.inc").read_text()
        self.assertIn("    .db $00,$00,26,5,$AA,41\n", spr)  # sid 52
        self.assertIn("    .db $00,$00,28,5,$AA,49\n", spr)  # sid 53
        self.assertIn("    .db $00,$04,14,5,$A0,33\n", spr)  # sid 58, release 3

    def test_yuri_kouken_is_enlarged_to_kyo_size(self):
        # The old 48x80 Ko'ou Ken looked half Kyo's size.  Yuri now uses the
        # rational 3/2 resize and a per-frame atlas quantizer: the orb grows
        # to 64x128 (frame 0) / 80x96 (frame 2) while still fitting 16 unique
        # 16x16 cells per page.
        self.assertEqual(projectiles.PROJECTILE_RESIZE["yuri"], (3, 2))
        self.assertEqual(projectiles.PROJECTILE_ZOOM_BY_CHAR["yuri"], 1)
        meta = (Path(build_fight.ROOT) /
                "build/gen_fight/projectiles_meta.inc").read_text()
        lines = meta.splitlines()
        frames = {}
        i = 0
        while i < len(lines):
            m = re.match(r"yuriProjFxF(\d+): \.db (\d+),(\d+)", lines[i])
            if not m:
                i += 1
                continue
            fi, ticks, count = int(m.group(1)), int(m.group(2)), int(m.group(3))
            cells, slots = [], set()
            j = i + 1
            while j < len(lines) and not re.match(r"^\S", lines[j]):
                cm = re.match(r"\s*\.db (-?\d+),(-?\d+)", lines[j])
                if cm and j + 1 < len(lines):
                    sm = re.search(r"\.dw \$([0-9A-F]+)", lines[j + 1])
                    if sm:
                        x, y = int(cm.group(1)), int(cm.group(2))
                        if x > 127:
                            x -= 256
                        if y > 127:
                            y -= 256
                        cells.append((x, y))
                        slots.add(sm.group(1))
                        j += 2
                        continue
                j += 1
            frames[fi] = (ticks, count, cells, slots)
            i = j
        self.assertEqual(set(frames), set(range(6)))
        for fi, (ticks, count, cells, slots) in frames.items():
            self.assertEqual(count, len(cells), fi)
            self.assertLessEqual(len(slots), 16, fi)
        w0 = max(x for x, _y in frames[0][2]) - min(x for x, _y in frames[0][2]) + 16
        h0 = max(y for _x, y in frames[0][2]) - min(y for _x, y in frames[0][2]) + 16
        self.assertGreaterEqual(w0 * h0, 2 * 48 * 80)
        self.assertGreaterEqual(w0, 64)
        self.assertGreaterEqual(h0, 112)
        w2 = max(x for x, _y in frames[2][2]) - min(x for x, _y in frames[2][2]) + 16
        h2 = max(y for _x, y in frames[2][2]) - min(y for _x, y in frames[2][2]) + 16
        self.assertEqual((w2, h2), (80, 96))     # Kyo's frame 0 bbox

    def test_kensou_projectile_has_athena_size(self):
        # Kensou's orb cels match Athena's dimensions.  Compiling all eight
        # frames instead of the generic first/last pair keeps the same cell
        # grid and therefore the same on-screen bbox as Athena's Psycho Ball.
        self.assertIn("kensou", build_fight.PROJECTILE_ALL_FRAMES)
        meta = (Path(build_fight.ROOT) /
                "build/gen_fight/projectiles_meta.inc").read_text()
        lines = meta.splitlines()

        def sizes(prefix):
            result = {}
            i = 0
            label = re.compile(rf"{prefix}ProjFxF(\d+): \.db (\d+),(\d+)")
            while i < len(lines):
                m = label.match(lines[i])
                if not m:
                    i += 1
                    continue
                fi = int(m.group(1))
                cells = []
                j = i + 1
                while j < len(lines) and not re.match(r"^\S", lines[j]):
                    cm = re.match(r"\s*\.db (-?\d+),(-?\d+)", lines[j])
                    if cm and j + 1 < len(lines) and \
                            re.search(r"\.dw \$[0-9A-F]+", lines[j + 1]):
                        x, y = int(cm.group(1)), int(cm.group(2))
                        if x > 127:
                            x -= 256
                        if y > 127:
                            y -= 256
                        cells.append((x, y))
                        j += 2
                        continue
                    j += 1
                result[fi] = (max(x for x, _ in cells) -
                              min(x for x, _ in cells) + 16,
                              max(y for _, y in cells) -
                              min(y for _, y in cells) + 16)
                i = j
            return result

        athena = sizes("athena")
        kensou = sizes("kensou")
        self.assertEqual(len(kensou), 8)
        self.assertEqual(kensou, athena)

    def test_lucky_death_bound_is_a_diagonal_hand_shot(self):
        # The arcade Death Bound leaves Lucky's hand and travels diagonally
        # down/forward: spawn at 120 px, 4 px/tick forward, 11/16 gravity.
        # It is not the vertical sky/drop shot from the source Death Shoot.
        self.assertEqual(projectiles.PROJECTILE_BALLISTIC["lucky"],
                         {"height": 120, "gravity": 11, "drift": 0})
        self.assertEqual(projectiles.PROJECTILE_CALIBRATION["lucky"],
                         {87: (0x0400, 22)})
        self.assertNotIn("lucky", projectiles.TORSO_PROJECTILES)
        root = Path(build_fight.ROOT)
        meta = (root / "build/gen_fight/projectiles_meta.inc").read_text()
        self.assertIn(
            "luckyProjFxTab: .dw luckyProjFxAnim, luckyProjFxAnim\n"
            "    .db 0\n"
            "    .db 120,11,$01\n", meta)
        spr = (root / "build/gen_fight/lucky_spr.inc").read_text()
        # sid 87: vx $0400, damage 22, HitDef sound 5, guard $A0, present
        self.assertIn("    .db $00,$04,22,5,$A0,1\n", spr)

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

    def test_shoto_fireball_windup_reaches_the_extended_arm_fast(self):
        # Ryu/Ken/Ryo/Robert/Takuma/Yuri: the fireball body animation drops
        # redundant wind-up poses and pins the source release frame, so the
        # shot leaves on the extended-arm pose without adding startup time.
        expected = {
            "ryu": {48: 4, 49: 4, 52: 4, 53: 4},
            "ken": {54: 4, 55: 4},
            "ryo": {60: 3, 61: 4},
            "robert": {58: 5, 59: 5},
            "takuma": {48: 5, 49: 5},
            "yuri": {48: 6, 49: 6},
        }
        self.assertEqual(
            {n: set(s) for n, s in
             build_fight.PROJECTILE_STARTUP_SPEEDUP.items()},
            {n: set(s) for n, s in expected.items()})
        for name, rows in expected.items():
            for sid, release in rows.items():
                self.assertEqual(
                    projectiles.PROJECTILE_RELEASE[name][sid], release)
        # The two-ticks-later release is paid back by a shorter recovery so
        # the special keeps its total duration.
        self.assertEqual(projectiles.PROJECTILE_RECOVERY["takuma"],
                         {48: 20, 49: 20})
        self.assertEqual(projectiles.PROJECTILE_RECOVERY["yuri"],
                         {48: 22, 49: 22})

    def test_projectile_startup_speedup_keeps_release_pose_and_tail(self):
        ticks = [3, 2, 4, 3, 2, 4, 18, 4]
        frames = [(i, 0, 0, 0, t, "", [], [])
                  for i, t in enumerate(ticks)]
        fast = build_fight.speed_up_projectile_startup(frames, 4)
        self.assertEqual([f[4] for f in fast], [1, 1, 1, 1, 2, 4, 18, 4])
        self.assertEqual(fast[4:], frames[4:])
        self.assertIs(
            build_fight.speed_up_projectile_startup(frames, 0), frames)

        held = [(0, 0, 0, 0, 255, "", [], [])] + frames[1:]
        self.assertIs(
            build_fight.speed_up_projectile_startup(held, 4), held)
        hitbox = list(frames)
        hitbox[1] = (1, 0, 0, 0, 2, "", [[1, 2, 3, 4]], [])
        self.assertIs(
            build_fight.speed_up_projectile_startup(hitbox, 4), hitbox)

    def test_projectile_startup_compaction_keeps_release_and_tail(self):
        # The upload budget forces 2 ticks on the large fireball cels, so the
        # wind-up must lose redundant in-between poses to stay fast.  The
        # extended-arm release pose and every recovery frame stay untouched.
        ticks = [2, 2, 2, 2, 2, 2, 4, 3, 9, 4]
        frames = [(i, 0, 0, 0, t, "", [], [])
                  for i, t in enumerate(ticks)]
        self.assertEqual(build_fight.projectile_startup_keyframes(4),
                         [0, 2, 3])
        self.assertEqual(build_fight.projectile_startup_keyframes(6),
                         [0, 3, 5])
        compacted, frame_map, drop = \
            build_fight.compact_projectile_startup(frames, 6)
        self.assertEqual(drop, 3)
        self.assertEqual(frame_map, {0: 0, 3: 1, 5: 2})
        self.assertEqual(len(compacted), len(frames) - 3)
        self.assertEqual(compacted[3], frames[6])      # release pose
        self.assertEqual(compacted[4:], frames[7:])    # recovery tail

    def test_projectile_startup_remaps_act_and_pos_timelines(self):
        # A dropped wind-up PosAdd must not lose movement, and frame-triggered
        # actions move with their pose to the compacted index.
        acts = {1000: [(0, 7, 51, 0), (4, 7, 52, 0), (128, 7, 53, 0)]}
        pos = {1000: [(1, 4), (2, 12), (3, 4), (6, 8)]}
        build_fight.remap_startup_timeline(
            1000, {0: 0, 3: 1, 5: 2}, 6, 3, acts, pos)
        self.assertEqual(acts[1000],
                         [(0, 7, 51, 0), (2, 7, 52, 0), (128, 7, 53, 0)])
        # old 1/2 are dropped and merged into old 3; old 3 keeps its own dx.
        self.assertEqual(pos[1000], [(1, 20), (3, 8)])


if __name__ == "__main__":
    unittest.main()
