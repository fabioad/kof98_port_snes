"""Blue Mary's imported specials must not stall on the AIR 255-tick hold.

The generated roster wiring only mapped the root statedefs, so the Vertical
Arrow air phase never ran and the Spinfall/Spider/Typhoon states froze on the
last hold frame.  The recovery tuning is spread over the roster config, the
generated TransTab/EVelTab tables and the native dispatch table; this test
keeps all three in sync.
"""
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import build_fight  # noqa: E402

ROOT = Path(build_fight.ROOT)
SPR = ROOT / "build/gen_fight/mary_spr.inc"
FIGHT = ROOT / "src/engine/fight.asm"


def _table(text, label, end):
    return text.split(label, 1)[1].split(end, 1)[0]


def _rows(text):
    """Parse a generated {.db from,to,kind /.dw arg} TransTab."""
    rows = []
    for m in re.finditer(r"\.db\s+([^,\n]+),([^,\n]+),([^\n]+)\n\s*\.dw\s+(\S+)",
                         text):
        rows.append((int(m.group(1), 0), int(m.group(2), 0),
                     int(m.group(3), 0), m.group(4)))
    return rows


class MaryRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = build_fight.CHARS["mary"]
        cls.text = SPR.read_text() if SPR.exists() else ""

    def test_followup_states_are_wired(self):
        for sid, state in ((107, 1101), (108, 1111), (109, 1305),
                           (110, 1910), (111, 4010)):
            self.assertEqual(self.cfg["moves"].get(sid), state, sid)
            self.assertIn(sid, self.cfg["anims"], sid)

    def test_air_and_grab_transitions_are_present(self):
        rows = {(f, t, k) for f, t, k, _a in
                self.cfg.get("extra_trans", ())}
        for row in ((54, 107, 0), (55, 108, 0),   # startup -> air phase
                    (107, 17, 1), (108, 17, 1),   # air -> landing
                    (59, 17, 1), (60, 17, 1),     # Spinfall -> landing
                    (56, 17, 1), (57, 17, 1),     # Spider -> landing
                    (49, 17, 1)):                 # Typhoon whiff -> landing
            self.assertIn(row, rows)

    def test_vertical_arrow_launch_velocity(self):
        self.assertEqual(self.cfg["state_vel"][107], (3.6, -5.4))
        self.assertEqual(self.cfg["state_vel"][108], (4.7, -7.5))

    def test_generated_transtab_has_the_recovery_rows(self):
        if not self.text:
            self.skipTest("generated tables not built")
        rows = {(f, t, k) for f, t, k, _a in
                _rows(_table(self.text, "maryTransTab:", "maryEVelTab:"))}
        for row in ((54, 107, 0), (55, 108, 0), (107, 17, 1),
                    (108, 17, 1), (59, 17, 1), (60, 17, 1),
                    (56, 17, 1), (57, 17, 1), (49, 17, 1)):
            self.assertIn(row, rows)

    def test_generated_entry_velocities(self):
        if not self.text:
            self.skipTest("generated tables not built")
        seg = _table(self.text, "maryEVelTab:", "maryPosTab:")
        self.assertIn(".db 107\n    .dw $039A,$FA9A", seg)
        self.assertIn(".db 108\n    .dw $04B3,$F880", seg)

    def test_followup_slots_share_existing_throw_cels(self):
        if not self.text:
            self.skipTest("generated tables not built")
        seg = _table(self.text, "maryAnimTab:", "maryAnim0:")
        ptrs = [l.strip() for l in seg.splitlines() if l.strip().startswith(".dw")]
        self.assertEqual(len(ptrs), 112)
        self.assertEqual(ptrs[107], ".dw maryAnim107")
        self.assertEqual(ptrs[108], ".dw maryAnim107")   # same AIR 1111
        self.assertEqual(ptrs[109], ".dw maryAnim99")    # reuse 1505 cels
        self.assertEqual(ptrs[110], ".dw maryAnim99")
        self.assertEqual(ptrs[111], ".dw maryAnim101")   # reuse 1525 cels

    def test_startup_clip_no_longer_holds_for_255_ticks(self):
        if not self.text:
            self.skipTest("generated tables not built")
        # sid 54/55 own anim 1110; the trimmed tail must be short.  Find the
        # body label for sid 54 from the AnimTab and inspect its last frame.
        seg = _table(self.text, "maryAnimTab:", "maryAnim0:")
        ptrs = [l.strip().split()[-1] for l in seg.splitlines()
                if l.strip().startswith(".dw")]
        body = _table(self.text, ptrs[54] + ":", "\nmaryAnim")
        ticks = [int(x) for x in re.findall(r"^\s*\.db (\d+),", body, re.M)]
        self.assertTrue(ticks)
        self.assertLessEqual(ticks[-1], 8,
                             f"{ptrs[54]} still holds {ticks[-1]} ticks")

    def test_intro_stops_before_the_stalling_wide_pose(self):
        # The source intro's element 17 is a wide double cel that stalls the
        # presenter on the current build.  Ending the clip one pose earlier
        # keeps the round start reachable.
        self.assertEqual(self.cfg.get("frame_cap", {}).get(92), 16)
        if not self.text:
            self.skipTest("generated tables not built")
        self.assertIn("maryAnim92:\n    .db 16,", self.text)

    def test_engine_dispatches_and_binds_the_new_slots(self):
        asm = FIGHT.read_text()
        self.assertIn(
            ".dw StAirSpec, StAirSpec, StSpecial, StSpecial, StAirSpec",
            asm)
        self.assertIn(".DEFINE S_EXT_LAST 111", asm)
        self.assertIn(".DEFINE S_EXT_GRAB 109", asm)
        # HitOne/AI/survivor must treat the imported follow-ups as attacks.
        self.assertIn("S_EXT_LAST-S_REVACT+1", asm)
        self.assertIn("S_EXT_LAST+1", asm)
        # StVictimHeld keeps the victim bound while an imported throw plays.
        self.assertIn("cmp #S_EXT_GRAB.w", asm)
        self.assertIn("cmp #(S_EXT_LAST+1).w", asm)


if __name__ == "__main__":
    unittest.main()
