"""Heavy D! / Brian wiring and hit-row regression checks.

These fighters are imported from packages whose specials put the HitDef in a
follow-up helper state and whose CMD uses letter-labelled controllers.  The
tests pin the source motion map, the follow-up transitions and the projectile
rows so a future re-import cannot silently leave a special with no hitbox.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_fight as bf  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def _cfg(name):
    return bf.CHARS[name]


def _moves(name):
    cfg = _cfg(name)
    return bf.parse_cns(os.path.join(bf.ROOT, cfg["cns"]),
                        cfg.get("coord_scale", 1),
                        cfg.get("damage_scale", 1))[0]


def _transitions(name):
    cfg = _cfg(name)
    parsed = bf.parse_cns(os.path.join(bf.ROOT, cfg["cns"]),
                          cfg.get("coord_scale", 1),
                          cfg.get("damage_scale", 1))
    state_to_sid = {}
    for sid, state in cfg["moves"].items():
        state_to_sid.setdefault(state, sid)
    rows = bf.trans_rules(parsed[4], parsed[3], state_to_sid, cfg["buttons"])
    return set(rows) | {tuple(row) for row in cfg.get("extra_trans", ())}


class HeavyDCalibrationTests(unittest.TestCase):
    def test_source_motion_map(self):
        cfg = _cfg("heavyd")
        self.assertEqual(cfg["moves"][48], 1000)   # R.S.D. punch
        self.assertEqual(cfg["moves"][50], 1100)   # Blast Upper kick
        self.assertEqual(cfg["moves"][52], 1200)   # Soul Flower kick
        self.assertEqual(cfg["moves"][54], 1300)   # Ducking Combination
        self.assertEqual(cfg["moves"][56], 1400)   # Dancing Beat
        self.assertEqual(cfg["moves"][58], 1900)   # Shadow
        self.assertEqual(cfg["moves"][85], 2000)   # D. Crazy
        self.assertEqual(cfg["moves"][87], 2105)   # D. Magnum release

    def test_hit_followups_and_projectile(self):
        moves = _moves("heavyd")
        for state in (1110, 1210, 1300, 1350, 1400, 1450, 2000, 2050):
            with self.subTest(state=state):
                self.assertIn(state, moves)
                self.assertGreater(moves[state]["active"], 0)
                self.assertGreater(moves[state]["damage"], 0)
        self.assertIn((50, 60, 0, 0), _transitions("heavyd"))
        self.assertIn((52, 61, 0, 0), _transitions("heavyd"))
        self.assertEqual(bf.PROJECTILE_ACTIONS["heavyd"], 2113)
        self.assertIn(87, bf.PROJECTILE_CALIBRATION["heavyd"])
        self.assertIn(88, bf.PROJECTILE_CALIBRATION["heavyd"])

    def test_only_d_magnum_is_a_projectile(self):
        cfg = _cfg("heavyd")
        parsed = bf.parse_cns(os.path.join(bf.ROOT, cfg["cns"]),
                              cfg.get("coord_scale", 1),
                              cfg.get("damage_scale", 1))
        rows = bf.projectile_rules(parsed[4], parsed[3], cfg["moves"],
                                   cfg.get("damage_scale", 1))
        for sid in bf.PROJECTILE_EXCLUDE.get("heavyd", ()):
            rows.pop(sid, None)
        rows.update({sid: (*value, 0) for sid, value in
                     bf.PROJECTILE_CALIBRATION["heavyd"].items()})
        self.assertEqual(set(rows), {87, 88})

    def test_long_supers_are_prioritised(self):
        cfg = _cfg("heavyd")
        self.assertEqual(cfg["cmd_priority"][:4],
                         ["QQCF_A", "QQCF_B", "QQCF_X", "QQCF_Y"])
        self.assertEqual(cfg["pow_override"][87], -1000)
        self.assertEqual(cfg["pow_override"][88], -1000)


class BrianCalibrationTests(unittest.TestCase):
    def test_normals_use_their_own_source_states(self):
        moves = _cfg("brian")["moves"]
        self.assertEqual([moves[s] for s in (5, 6, 7, 8)],
                         [200, 220, 210, 230])
        self.assertEqual([moves[s] for s in (19, 20, 21, 22)],
                         [400, 420, 410, 430])
        self.assertEqual([moves[s] for s in (23, 24, 25, 26)],
                         [600, 620, 610, 630])

    def test_special_roots_link_to_active_followups(self):
        moves = _moves("brian")
        for state in (1010, 1060, 1110, 1160, 1210, 1260,
                      1310, 1360, 3005, 3055, 3110, 3210):
            with self.subTest(state=state):
                self.assertIn(state, moves)
                self.assertGreater(moves[state]["active"], 0)
        trans = _transitions("brian")
        for root, active in ((48, 58), (49, 59), (50, 60), (51, 62),
                             (56, 61), (57, 63), (52, 65), (53, 66),
                             (85, 64), (86, 89)):
            with self.subTest(root=root):
                self.assertIn((root, active, 0, 0), trans)

    def test_melee_followups_are_not_projectiles(self):
        cfg = _cfg("brian")
        parsed = bf.parse_cns(os.path.join(bf.ROOT, cfg["cns"]),
                              cfg.get("coord_scale", 1),
                              cfg.get("damage_scale", 1))
        rows = bf.projectile_rules(parsed[4], parsed[3], cfg["moves"],
                                   cfg.get("damage_scale", 1))
        for sid in bf.PROJECTILE_EXCLUDE.get("brian", ()):
            rows.pop(sid, None)
        self.assertEqual(rows, {})

    def test_qcfx2_supers_are_prioritised(self):
        cfg = _cfg("brian")
        self.assertEqual(cfg["cmd_priority"], ["SUP3", "SUP4", "SUP1", "SUP2"])
        # 87/88 begin in the active states, so they must charge explicitly;
        # 89 is the follow-up of the 3050 root and stays free.
        self.assertEqual(cfg["pow_override"][87], -1000)
        self.assertEqual(cfg["pow_override"][88], -1000)
        self.assertNotIn(89, cfg["pow_override"])


class InvisibleMoveAnimationTests(unittest.TestCase):
    """A move must never run on a helper-only (sprite -1) timeline.

    Heavy D!'s Blast Upper and Soul Flower keep their HitDef in invisible
    kama helper states (AIR 1110/1210).  Mapping those states onto the main
    fighter made the character vanish while the hitbox stayed active, which
    players see as "the hitbox playing instead of the animation".
    """

    def _repair(self, name):
        cfg = _cfg(name)
        air = bf.parse_air(os.path.join(bf.ROOT, cfg["air"]))
        anims = dict(cfg["anims"])
        repaired = bf.repair_invisible_move_anims(name, cfg, anims, air)
        return air, anims, repaired

    def test_heavyd_followups_draw_a_body_and_keep_their_hitboxes(self):
        air, anims, repaired = self._repair("heavyd")
        self.assertEqual({sid for sid, _old, _new in repaired}, {60, 61})
        for sid, source, parent in ((60, 1110, 1100), (61, 1210, 1200)):
            frames = air[anims[sid]][0]
            self.assertTrue(all(g >= 0 and n >= 0 for g, n, *_ in frames))
            # Ticks and Clsn1 timing/geometry come from the helper state...
            self.assertEqual([f[4] for f in frames],
                             [f[4] for f in air[source][0]])
            self.assertEqual([f[6] for f in frames],
                             [f[6] for f in air[source][0]])
            # ...while the pose is the visible parent's last frame.
            last = [f for f in air[parent][0] if f[0] >= 0 and f[1] >= 0][-1]
            self.assertEqual([(f[0], f[1]) for f in frames],
                             [(last[0], last[1])] * len(frames))


def _effective_cfg(name):
    """Character config with the late POST_CAL_TWEAKS merged in.

    POST_CAL_TWEAKS is applied inside build_char after apply_profile; the
    table tests need the same view of moves/anims/slices.
    """
    cfg = {key: (dict(value) if isinstance(value, dict) else value)
           for key, value in _cfg(name).items()}
    for key, value in bf.POST_CAL_TWEAKS.get(name, {}).items():
        if isinstance(value, dict):
            cfg.setdefault(key, {}).update(value)
        elif isinstance(value, (list, tuple, set)):
            current = list(cfg.get(key, ()))
            current += [item for item in value if item not in current]
            cfg[key] = current
        else:
            cfg[key] = value
    return cfg


def _table_text(name):
    path = ROOT / "build" / "gen_fight" / f"{name}_spr.inc"
    if not path.exists():
        raise unittest.SkipTest("run tools/build_fight.py first")
    return path.read_text()


def _section(text, label):
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.startswith(label + ":"))
    except StopIteration:
        return []
    body = []
    for line in lines[start + 1:]:
        if line and not line.startswith(" "):
            break
        body.append(line)
    return body


def _words(text, label):
    out = []
    for line in _section(text, label):
        if ".dw" in line:
            body = line.split(".dw", 1)[1].split(";", 1)[0]
            out += [int(v.strip().replace("$", "0x"), 0)
                    for v in body.split(",")]
    return out


def _db_rows(text, label):
    rows = []
    for line in _section(text, label):
        if ".db" not in line:
            continue
        body = line.split(".db", 1)[1].strip()
        if body.startswith("$FF"):
            break
        rows.append(tuple(int(v.strip().replace("$", "0x"), 0)
                          for v in body.split(",")))
    return rows


class ShadowStrongTests(unittest.TestCase):
    """D,D + strong (state 1950) must land four pins and a launcher.

    The source re-arms one HitDef on animelem 3/8/13/19 (ground.velocity 0,
    no knockdown) and uses a second, fall=1 HitDef on animelem 24.  Taking
    the state-level row alone applied the launcher's fall flag to the first
    contact, so the move dealt 1 damage instead of 5.
    """

    def test_config_splits_the_clip_and_keeps_the_finisher(self):
        cfg = _effective_cfg("heavyd")
        self.assertEqual(cfg["moves"][59], 1950)
        self.assertEqual(cfg["moves"][62], 1950)
        self.assertEqual(cfg["anims"][62], 1950)
        self.assertEqual(cfg["slices"][59], (1950, 0, 22))
        self.assertEqual(cfg["slices"][62], (1950, 23, None))
        self.assertEqual(cfg["slice_hits"], {59: (0, 62), 62: (1, 0)})
        self.assertEqual(cfg["hit_resets"][1950], [8, 13, 19])
        self.assertEqual(cfg["hitdef_override"][59]["gvx"], 0)
        self.assertEqual(cfg["hitdef_override"][59]["gvy"], 0)

    def test_tables_expose_four_pins_and_one_knockdown(self):
        text = _table_text("heavyd")
        active = _words(text, "heavydActiveTab")
        flags = _words(text, "heavydFlagsTab")
        damage = _words(text, "heavydDamageTab")
        vel = _words(text, "heavydHitVelTab")
        self.assertEqual(active[59], 3)          # element 3 hit window
        self.assertEqual(active[62], 1)          # element 24, local frame 0
        self.assertFalse(flags[59] & 0x0001)     # pins never knock down
        self.assertTrue(flags[62] & 0x0001)      # launcher falls
        self.assertEqual(damage[59], 1)
        self.assertEqual(damage[62], 1)
        # Pins hold the victim in place; the launcher keeps -4, -6.8.
        self.assertEqual(vel[59 * 4:59 * 4 + 2], [0, 0])
        self.assertEqual(vel[62 * 4], 4 << 8)
        self.assertEqual(vel[62 * 4 + 1] & 0xFFFF,
                         (-1741) & 0xFFFF)

    def test_act_rows_rearm_each_pin_and_chain_the_launcher(self):
        text = _table_text("heavyd")
        rows = _db_rows(text, "heavydAct59")
        resets = [frame for frame, op, _arg, _cond in rows if op == 18]
        self.assertEqual(resets, [7, 12, 18])
        trans = []
        lines = _section(text, "heavydTransTab")
        for i, line in enumerate(lines):
            if ".db" in line and i + 1 < len(lines) and ".dw" in lines[i + 1]:
                trans.append(tuple(int(v.strip().replace("$", "0x"), 0)
                                   for v in line.split(".db", 1)[1].split(",")))
        self.assertIn((59, 62, 0), trans)
        self.assertIn((62, 0, 0), trans)


if __name__ == "__main__":
    unittest.main()
