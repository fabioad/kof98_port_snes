"""Close standing normals (KOF '98) stay wired end to end.

The source `.cmd` files gate a per-button close state with p2bodydist; the
port maps it to a dedicated runtime sid while keeping the far state in sids
5..8.  These checks cover the source table, the generated button/command
tables and the engine selector so a future rebuild cannot silently drop the
mechanic.
"""
import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from close_normals import (CLOSE_NORMALS, CLOSE_SIDS, CLOSE_NORMAL_SKIP,
                           BUTTON_ORDER, close_sids_for)   # noqa: E402
import build_fight as fight                                  # noqa: E402
from gen_char_cfg import parse_statedefs, parse_air_ids      # noqa: E402

OUT = ROOT / "build" / "gen_fight"
FIGHT = ROOT / "src" / "engine" / "fight.asm"
CANCEL = ROOT / "src" / "engine" / "cancel_gate.asm"


def _table(text, start, end):
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[a:b]


class CloseNormalTableTests(unittest.TestCase):
    def test_every_source_state_and_animation_exists(self):
        for name, buttons in CLOSE_NORMALS.items():
            cfg = fight.CHARS[name]
            cns = (ROOT / cfg["cns"]).read_text(encoding="utf-8-sig",
                                                errors="replace")
            st = parse_statedefs(cns)
            air = parse_air_ids(str(ROOT / cfg["air"]))
            for btn, (close, far, _dist) in buttons.items():
                for state in (close, far):
                    self.assertIn(state, st, f"{name} {btn} state {state}")
                    anim = st[state].get("anim")
                    if anim is None:
                        anim = state
                    self.assertIn(anim, air, f"{name} {btn} anim {anim}")
                self.assertNotEqual(close, far, f"{name} {btn}")

    def test_skip_list_only_contains_known_roster(self):
        self.assertTrue(CLOSE_NORMAL_SKIP <= set(fight.CHARS))

    def test_partial_characters_keep_the_button_slot(self):
        # Shermie only has a close strong punch; it must still use the HP
        # slot so CancelGate maps it to the HP far row.
        sids = close_sids_for("shermie", fight.CHARS["shermie"]["moves"])
        self.assertEqual(sids, {"y": 83})
        sids = close_sids_for("choi", fight.CHARS["choi"]["moves"])
        self.assertEqual(sids, {"x": 82, "y": 83, "a": 93})

    def test_engine_selector_is_wired(self):
        text = FIGHT.read_text()
        for needle in ("S_CLPUNCH", "S_CLSPUNCH", "S_CLKICK", "S_CLSKICK",
                       "AS_take_close", "cpy scr2"):
            self.assertTrue(needle in text, needle)
        cancel = CANCEL.read_text()
        for needle in ("CG_row0", "S_CLSKICK_ALT",
                       "IsCloseNormal:", "IsCloseNormal8:"):
            self.assertTrue(needle in cancel, needle)


class GeneratedCloseTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terry = (OUT / "terry_spr.inc").read_text()
        cls.king = (OUT / "king_spr.inc").read_text()
        cls.choi = (OUT / "choi_spr.inc").read_text()

    def button_rows(self, text, name):
        seg = _table(text, f"{name}ButtonTab:\n", f"{name}ButtonTabEnd:")
        return [(int(a, 16), int(b, 16)) for a, b in
                re.findall(r"\.dw \$([0-9A-Fa-f]{4}),\$?([0-9A-Fa-f]+)",
                           seg)]

    def cmd_rows(self, text, name):
        seg = _table(text, f"{name}CmdTab:\n", "    .db $FF")
        return [[int(x) for x in ln.split(",")]
                for ln in re.findall(r"\.db ([0-9,]+)", seg)]

    def test_terry_button_table_selects_close_and_far(self):
        rows = self.button_rows(self.terry, "terry")
        self.assertEqual(len(rows), 8)
        masks = [0x4000, 0x0040, 0x8000, 0x0080]
        sids = [82, 83, 93, 98]
        gates = [46, 64, 58, 78]
        for i, (mask, gate, sid) in enumerate(zip(masks, gates, sids)):
            self.assertEqual(rows[i], (mask, (gate << 8) | sid))
        self.assertEqual([r[1] for r in rows[4:]], [5, 6, 7, 8])

    def test_king_uses_the_same_sids_for_different_source_states(self):
        rows = self.button_rows(self.king, "king")
        self.assertEqual(rows[1], (0x0040, (55 << 8) | 83))
        self.assertEqual(rows[5], (0x0040, 6))

    def test_partial_character_keeps_a_disabled_close_row(self):
        rows = self.button_rows(self.choi, "choi")
        self.assertEqual(rows[3][0], 0)          # no close strong kick
        self.assertEqual([r[1] for r in rows[4:]], [5, 6, 7, 8])

    def test_terry_cmdtab_has_gated_close_before_far(self):
        rows = self.cmd_rows(self.terry, "terry")
        close_y = [r for r in rows if len(r) == 7 and r[4] == 64 and r[6] == 83]
        far_y = [r for r in rows if len(r) == 7 and r[4] == 0 and r[6] == 6]
        self.assertTrue(close_y)
        self.assertTrue(far_y)
        self.assertLess(rows.index(close_y[0]), rows.index(far_y[0]))

    def test_close_animation_differs_from_far(self):
        seg = _table(self.terry, "terryAnimTab:", "terryAnim0:")
        ptrs = [ln.strip() for ln in seg.splitlines()
                if ln.strip().startswith(".dw")]
        self.assertEqual(len(ptrs), 103)
        self.assertEqual(ptrs[83], ".dw terryAnim83")
        self.assertEqual(ptrs[6], ".dw terryAnim6")
        self.assertNotEqual(ptrs[83], ptrs[6])


if __name__ == "__main__":
    unittest.main()
