"""Source/table contracts for all 106 normal-throw cases, without a ROM build.

These tests execute signed-byte damage timelines, not the 65816 engine. The
headless audit remains the final runtime check after a later build.
"""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_fight as bf
import normal_throws as nt
from audit_release_throws_headless import result_errors
from calibration.native import apply_profile


def source_data(name):
    cfg = copy.deepcopy(bf.CHARS[name])
    air = bf.parse_air(bf.asset_path(cfg["air"]))
    parsed = bf.parse_cns(bf.asset_path(cfg["cns"]), cfg.get("coord_scale", 1),
                          cfg.get("damage_scale", 1), char=name)
    anims = (bf.resolve_import_anims(cfg, air) if name in bf.NEW_CHARS
             else dict(cfg["anims"]))
    for state, life in cfg.get("target_life_fix", {}).items():
        parsed[6][state] = [(f, op, life if op == 3 else arg, cond)
                            for f, op, arg, cond in parsed[6].get(state, ())]
    apply_profile(ROOT, name, cfg, parsed[0], air)
    bf.wire_throw_chain(name, cfg, anims, air, parsed[0], parsed[3])
    return cfg, anims, air, parsed


def repair(name, data):
    cfg, anims, air, parsed = data
    return nt.repair(name, cfg, anims, air, parsed[0], parsed[3], parsed[4],
                     parsed[5], parsed[6], parsed[1])


class NormalThrowRepairsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = {name: source_data(name) for name in bf.CHARS}
        cls.fixed = copy.deepcopy(cls.original)
        for name, data in cls.fixed.items():
            repair(name, data)

    def test_all_106_roster_direction_cases(self):
        self.assertEqual(len(self.fixed), 53)
        checked = 0
        for name, (cfg, anims, air, parsed) in self.fixed.items():
            for facing in (1, -1):
                with self.subTest(character=name, facing=facing):
                    checked += 1
                    self.assertEqual(cfg["moves"][74], self.original[name][0]["moves"][74])
                    self.assertTrue(air[anims[74]][0])
                    if name not in nt.PLANS:
                        # Regression contract: keep already functional source
                        # wiring, art, calibration and events byte-for-byte.
                        self.assertEqual(self.fixed[name], self.original[name])
                        continue
                    self.assertEqual(cfg["moves"][75], nt.STATE)
                    self.assertEqual(cfg["hitdef_override"][74]["p1mugen"], nt.STATE)
                    self.assertEqual(cfg["hitdef_override"][74]["p2state"], 76)
                    frames, loop = air[anims[75]]
                    self.assertEqual(loop, -1)
                    self.assertLess(sum(f[4] for f in frames), 450)
                    self.assertTrue(all(0 < f[4] < 255 for f in frames))
                    rows = parsed[6][nt.STATE]
                    events = [row for row in rows if row[1] == 3]
                    expected = sum(hp for phase in nt.PLANS[name]
                                   for _element, hp in phase.hits)
                    self.assertGreater(expected, 2)
                    for initial in (100, 200):
                        hp = initial
                        for element in range(len(frames)):
                            for trigger, op, arg, cond in events:
                                if trigger != element:
                                    continue
                                self.assertEqual(cond, 0)
                                self.assertTrue(-128 <= arg < 0)
                                # Exactly what AO_tlife reads after .db.
                                byte = arg & 255
                                signed = byte - 256 if byte & 128 else byte
                                before = hp
                                hp = max(0, min(200, hp + signed))
                                self.assertLess(hp, before)
                        self.assertEqual(initial - hp, expected)
                    # Both inputs use this same safe impact schedule. Binds
                    # mirror with the owner instead of a source Turn event.
                    self.assertFalse(any(op in (0, 4) for _f, op, _a, _c in rows))
                    for lo, hi, dx, dy in parsed[5][nt.STATE]:
                        self.assertTrue(0 <= lo <= hi < len(frames))
                        self.assertLessEqual(-dy, 80)
                        self.assertTrue(-128 <= dx * facing <= 127)
                    wired = {state: sid for sid, state in cfg["moves"].items()}
                    trans = bf.trans_rules(parsed[4], parsed[3], wired, cfg["buttons"])
                    self.assertIn((75, 0, 0, 0), trans)
        self.assertEqual(checked, 106)

    def test_only_the_19_broken_characters_are_repaired(self):
        expected = {"kyo", "kyonests", "kyoash", "rugal", "omegarugal", "leona",
                    "mature", "vice", "andy", "ryo", "athena", "kensou", "mai",
                    "chizuru", "chang", "shermie", "billy", "lucky", "brian"}
        self.assertEqual(set(nt.PLANS), expected)

    def test_all_53_keep_the_requested_pad_layout(self):
        expected_buttons = {"x": 0x4000, "y": 0x0040,
                            "a": 0x8000, "b": 0x0080,
                            "c": 0x0020, "z": 0x0010}
        for name in self.fixed:
            with self.subTest(character=name):
                cfg = copy.deepcopy(self.fixed[name][0])
                bf.resolve_input_calibration(name, cfg)
                self.assertEqual(cfg["buttons"], expected_buttons)
                rows = bf.parse_cmd(bf.asset_path(cfg["cmd"]),
                                     cfg["buttons"], cfg["moves"])
                for posture, sids in (("stand", (5, 6, 7, 8)),
                                      ("crouch", (19, 20, 21, 22)),
                                      ("air", (23, 24, 25, 26))):
                    self.assertEqual(dict(rows[posture]),
                        dict(zip((0x4000, 0x0040, 0x8000, 0x0080), sids)))

    def test_repair_adds_no_sprite_cells_or_native_slots(self):
        for name in nt.PLANS:
            with self.subTest(character=name):
                cfg0, anims0, air0, _ = self.original[name]
                cfg, anims, air, _ = self.fixed[name]
                old_keys = {(f[0], f[1]) for f in air0[anims0[75]][0]}
                new_keys = {(f[0], f[1]) for f in air[anims[75]][0]}
                self.assertLessEqual(new_keys, old_keys)
                self.assertEqual(set(anims), set(anims0))
                self.assertEqual(max(cfg["moves"]), max(cfg0["moves"]))
                self.assertTrue(all(not f[6] for f in air[anims[75]][0]))

    def test_source_specials_and_victim_states_remain_intact(self):
        for name in nt.PLANS:
            with self.subTest(character=name):
                _cfg0, _an0, air0, parsed0 = self.original[name]
                _cfg, _an, air, parsed = self.fixed[name]
                for key, value in air0.items():
                    self.assertEqual(air[key], value)
                for index in (0, 1, 3, 4, 5, 6):
                    for state, value in parsed0[index].items():
                        self.assertEqual(parsed[index][state], value)

    def test_kyo_and_shermie_damage_elements_are_reachable(self):
        for name, element in (("kyo", 5), ("kyonests", 5), ("kyoash", 5), ("shermie", 10)):
            _c, _a, air, parsed = self.fixed[name]
            self.assertLess(element, len(air[nt.ACTION][0]))
            self.assertTrue(any(f == element and op == 3
                                for f, op, _v, _cond in parsed[6][nt.STATE]))

    def test_missing_followups_and_repeated_hits_are_restored(self):
        for name, contacts, total in (("andy", 2, 36), ("ryo", 1, 40),
                                       ("rugal", 8, 48), ("lucky", 8, 32),
                                       ("omegarugal", 9, 29)):
            rows = self.fixed[name][3][6][nt.STATE]
            damage = [arg for _f, op, arg, _c in rows if op == 3]
            self.assertEqual((len(damage), -sum(damage)), (contacts, total))

    def test_no_super_bind_or_aerial_attempt_borrowed(self):
        leona = self.fixed["leona"][0]["hitdef_override"][74]
        self.assertEqual(leona["p1mugen"], nt.STATE)
        self.assertEqual(nt.PLANS["leona"][0].state, 805)
        mai = self.fixed["mai"][0]["hitdef_override"][74]
        # Keep the existing command target, but take its HitDef from the
        # terrestrial 800 instead of the imported air throw 820.
        self.assertEqual(mai["active"], self.original["mai"][3][0][800]["active"])
        self.assertEqual(nt.PLANS["mai"][0].state, 801)

    def test_reserved_state_collision_fails_closed(self):
        data = copy.deepcopy(self.original["kyo"])
        data[3][3][nt.STATE] = {}
        with self.assertRaisesRegex(ValueError, "collision"):
            repair("kyo", data)

    def test_invalid_damage_event_fails_closed(self):
        for hp in (0, -1, 129):
            data = copy.deepcopy(self.original["kyo"])
            original = nt.PLANS["kyo"]
            try:
                nt.PLANS["kyo"] = (nt.Phase(810, 810, ((5, hp),)),)
                with self.assertRaisesRegex(ValueError, "unreachable or unencodable"):
                    repair("kyo", data)
            finally:
                nt.PLANS["kyo"] = original

    def test_throw_handler_honors_authored_velocity(self):
        asm = (ROOT / "src/engine/fight.asm").read_text()
        body = asm.split("StThrow:", 1)[1].split("ThrowBind:", 1)[0]
        self.assertIn("jsr PinVXUnlessVelSet", body)
        ryo_actions = self.fixed["ryo"][3][6][nt.STATE]
        self.assertTrue(any(op == 5 and arg for _f, op, arg, _c in ryo_actions))

    def test_ryo_finisher_keeps_its_entry_velocity_reset(self):
        _cfg, _anims, _air, parsed = self.fixed["ryo"]
        rows = parsed[6][nt.STATE]
        phase_start = len(self.original["ryo"][2][810][0])
        self.assertIn((phase_start, 5, 0, 0), rows)
        self.assertIn((phase_start, 15, 0, 0), rows)


class ThrowAuditAcceptanceTests(unittest.TestCase):
    def result(self, **changes):
        return {"cycle_complete": True, "final_damage": 41,
                "healing_observed": False, "grab_flags_clear": True, **changes}

    def test_capture_alone_does_not_pass(self):
        self.assertTrue(result_errors("kyo", self.result(final_damage=1)))

    def test_healing_below_initial_life_is_still_rejected(self):
        # 100 -> 60 -> 90 never goes above initial life but is a broken throw.
        self.assertTrue(result_errors("athena", self.result(
            final_damage=10, healing_observed=True)))

    def test_grab_flags_must_be_cleared(self):
        self.assertTrue(result_errors("kyo", self.result(grab_flags_clear=False)))

    def test_final_damage_not_peak_damage_is_required(self):
        self.assertTrue(result_errors("kyo", self.result(damage=41, final_damage=0)))

    def test_complete_throw_passes(self):
        self.assertEqual(result_errors("kyo", self.result()), [])


if __name__ == "__main__":
    unittest.main()
