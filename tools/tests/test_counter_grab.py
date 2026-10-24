import copy
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import build_fight  # noqa: E402
from build_fight import (CHARS, COUNTER_GRAB_POST_CAL, ROOT as ROOT_STR,
                         parse_cns, wire_counter_grabs)  # noqa: E402
from calibration import projectiles  # noqa: E402

# Characters whose ReversalDef has a p2stateno: a hit becomes a counter-grab.
ROOT = Path(ROOT_STR)

COUNTER_GRAB_STATES = {
    "mary": (1505, 1510, 1505),
}

COUNTER_GRAB = {
    "daimon": (1410, 1415),
    "geese": (1410, 1411),
    "heidern": (1420, 1430),
    "krauser": (1610, 1615),
    "takuma": (1705, 1706),
    "mary": (1505, 1510),
}

# ReversalDef states whose stance is reachable in the port and therefore
# must turn the parry into a throw (runtime slots 99/100 and 101/102).
COUNTER_GRAB_WIRED = {
    "geese": {"hi": (1410, 1411, 1410), "lo": (1420, 1421, 1420)},
    "heidern": {"hi": (1420, 1430, 1420)},
    "mary": {"hi": (1505, 1510, 1505), "lo": (1525, 1530, 1525)},
    "takuma": {"hi": (1705, 1706, 1705)},
}
COUNTER_GRAB_SLOTS = {"hi": (99, 100), "lo": (101, 102)}


class CounterGrabTests(unittest.TestCase):
    def test_discovered_counter_grab_characters(self):
        found = {}
        for path in sorted((ROOT / "assets/characters").glob("*/*_SNES.cns")):
            name = path.parent.name
            key = {"Daimon-KOF98": "daimon", "Geese-KOF98": "geese",
                   "Heidern-KOF98": "heidern", "Krauser-KOF98": "krauser",
                   "Takuma-KOF98": "takuma", "bluemary-kofa": "mary",
                   }.get(name)
            if key is None:
                continue
            cns = parse_cns(path, 1, 1)
            reversals = cns[7]
            for state, row in reversals.items():
                if row[3] >= 0:
                    found.setdefault(key, set()).add((row[1], row[3]))
        for key, pair in COUNTER_GRAB.items():
            self.assertIn(key, found, key)
            self.assertIn(pair, found[key], key)

    def test_counter_grab_followups_are_wired(self):
        for key, (_p1, _p2, _anim) in COUNTER_GRAB_STATES.items():
            self.assertEqual(CHARS[key]["moves"][99], _p1, key)
            self.assertEqual(CHARS[key]["moves"][100], _p2, key)
            self.assertEqual(CHARS[key]["anims"][99], _anim, key)

    def test_reachable_reversal_stances_grab_instead_of_parry(self):
        for key, rows in COUNTER_GRAB_WIRED.items():
            cfg = copy.deepcopy(CHARS[key])
            wire_counter_grabs(cfg, COUNTER_GRAB_POST_CAL.get(key, {}))
            for height, (p1, p2, anim) in rows.items():
                actor, victim = COUNTER_GRAB_SLOTS[height]
                self.assertEqual(cfg["moves"].get(actor), p1,
                                 f"{key} {height} actor")
                self.assertEqual(cfg["moves"].get(victim), p2,
                                 f"{key} {height} victim")
                self.assertEqual(cfg["anims"].get(actor), anim,
                                 f"{key} {height} anim")

    def test_geese_counter_states_are_wired_to_runtime_slots(self):
        cfg = CHARS["geese"]
        self.assertEqual(cfg["moves"][99], 1410)
        self.assertEqual(cfg["moves"][100], 1411)
        self.assertEqual(cfg["moves"][101], 1420)
        self.assertEqual(cfg["moves"][102], 1421)
        self.assertEqual(cfg["anims"][99], 1410)
        self.assertEqual(cfg["anims"][101], 1420)
        # Held victim rows use the generic hit pose, available for any char.
        for sid in (100, 102):
            self.assertEqual(cfg["anims"].get(sid, 5000), 5000)

    def test_generated_revtab_keeps_victim_sid(self):
        text = (ROOT / "build/gen_fight/geese_spr.inc").read_text()
        self.assertIn("geeseRev48:\n    .db 8,99,4,100", text)
        self.assertIn("geeseRev51:\n    .db 8,99,1,100", text)
        self.assertIn("geeseAnim99:", text)
        self.assertIn("geeseAnim101:", text)
        self.assertIn("geeseBind99:", text)
        self.assertIn("geeseAct99:", text)
        # TargetLifeAdd (-19 x damage_scale 2) compiled into the actor state.
        act = text[text.index("geeseAct99:"):text.index("geeseAct101:")]
        self.assertRegex(act, r"\n    \.db 4,3,218,0")

    def test_engine_dispatches_all_four_runtime_slots(self):
        text = (ROOT / "src/engine/fight.asm").read_text()
        self.assertRegex(
            text, r"\.dw StThrow, StVictimHeld, StThrow, StVictimHeld")
        for name in ("ThrowBind", "StVictimHeld"):
            self.assertIn(name, text)
        self.assertIn(".DEFINE S_CGRAB_HI", text)
        self.assertIn(".DEFINE S_CGRAB_LOV", text)

    def test_parry_counter_followups_get_runtime_slots(self):
        # Yamazaki/Kyo/Shingo/Billy have a ReversalDef with p1stateno but no
        # p2stateno: the parry must enter their counter-attack state, not the
        # old invalid $FF.  wire_reversal_followups assigns slots 103+.
        for key in ("yamazaki", "kyo", "shingo", "billy"):
            cfg = copy.deepcopy(CHARS[key])
            cns = parse_cns(cfg["cns"], 1, 1)
            anims = dict(cfg["anims"])
            air = build_fight.parse_air(os.path.join(ROOT_STR, cfg["air"]))
            wired = build_fight.wire_reversal_followups(
                cfg, anims, air, cns[3], cns[4], cns[7])
            self.assertTrue(wired, key)
            for stance, slot in wired.items():
                self.assertIn(slot, build_fight.REVERSAL_ACTOR_SLOTS, key)
                self.assertEqual(cfg["moves"][slot], cns[7][stance][1], key)
                self.assertIn(slot, anims, key)

    def test_helper_state_is_not_wired_as_counter_attack(self):
        # Chizuru's p1stateno (1051) is a transient helper (type U), not a
        # fighter pose; it must stay unmapped rather than teleporting the
        # player into the helper.
        cfg = copy.deepcopy(CHARS["chizuru"])
        cns = parse_cns(cfg["cns"], 1, 1)
        anims = dict(cfg["anims"])
        air = build_fight.parse_air(os.path.join(ROOT_STR, cfg["air"]))
        wired = build_fight.wire_reversal_followups(
            cfg, anims, air, cns[3], cns[4], cns[7])
        self.assertEqual(wired, {})

    def test_engine_rejects_unmapped_followup_sid(self):
        text = (ROOT / "src/engine/fight.asm").read_text()
        rev = text[text.index("RevCheck:"):text.index("AddPower:")]
        self.assertIn("cmp #$FF.b", rev)
        self.assertIn("beq RC_no", rev)
        state = text[text.index("StateTab:"):text.index("StateRet:")]
        self.assertIn(".dw StSpecial, StSpecial, StSpecial, StSpecial", state)

    def test_generated_revtab_rows_point_at_counter_slots(self):
        expected = {"yamazaki": 48, "kyo": 52, "shingo": 54, "billy": 48}
        for key, sid in expected.items():
            text = (ROOT / "build/gen_fight" / f"{key}_spr.inc").read_text()
            self.assertRegex(
                text, rf"{key}Rev{sid}:\n    \.db 8,10[3-6],",
                f"{key} counter follow-up was not wired")


if __name__ == "__main__":
    unittest.main()
