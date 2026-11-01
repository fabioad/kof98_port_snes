"""Clark's Ultra Argentine wiring and throw-bind windows.

Two defects in the generated Clark data made the super look like a frozen
fight:

* the strong Ultra Argentine command (HCBHCB+Y) pointed at state 3010, the
  throw *follow-up*, instead of the starter 3000.  Entering 3010 without a
  bound victim leaves Clark in an invulnerable pose with no hit and no exit
  of its own;
* the generated TargetBind window for 3010 contained a catch-all
  ``0,254,8,176`` row (an ``AnimElemTime(6) = 0`` guard the compiler did not
  understand) that held the victim 80 px above the floor for 254 frames.

The bind tables also used to be emitted in source order, while the engine
takes the *first* matching window: MUGEN runs every matching TargetBind and
the last one wins, so a broad early row shadowed every specific row after
it.  ``canon_bind`` resolves that at build time.

Run after a PVSnesLib build:

    python3 -m unittest tools.tests.test_clark_super_bind
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "build" / "gen_fight"
CMD = ROOT / "assets" / "characters" / "Clark-KOF98" / "Clark_SNES.cmd"

import sys
sys.path.insert(0, str(ROOT / "tools"))
import build_fight  # noqa: E402

CLARK_SCALE = build_fight.CHARS["clark"].get("char_scale", 1.0)


def sc(value):
    """Source offset -> emitted bind offset at the current art scale."""
    return int(round(value * CLARK_SCALE))


def rows_of(text, label):
    m = re.search(rf"^{re.escape(label)}:\s*\n((?:\s*\.db[^\n]*\n)+)",
                  text, re.M)
    if not m:
        return None
    out = []
    for line in m.group(1).splitlines():
        nums = [int(t[1:], 16) if t.startswith("$") else int(t)
                for t in re.findall(r"\$[0-9A-Fa-f]+|\d+", line)]
        if nums:
            out.append(tuple(nums))
    return out


class ClarkUltraArgentineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = GEN / "clark_spr.inc"
        if not path.exists():
            raise unittest.SkipTest("run tools/build_fight.py first")
        cls.text = path.read_text(errors="ignore")

    def test_asset_strong_super_enters_starter_state(self):
        """Both strengths must enter 3000; 3010 is the throw follow-up."""
        text = CMD.read_text(encoding="utf-8-sig")
        m = re.search(
            r"\[State -1, Ultra Argentine strong\]\s*\n"
            r"type = ChangeState\s*\nvalue = (\d+)", text)
        self.assertIsNotNone(m, "strong Ultra Argentine rule not found")
        self.assertEqual(m.group(1), "3000")

    def test_generated_command_table_targets_starter(self):
        rows = rows_of(self.text, "clarkCmdTab")
        self.assertTrue(rows, "clarkCmdTab missing")
        # {motion, ?, ?, cond, ?, ?, sid}: HCBHCB weak/strong are motions
        # 1 and 2 and must both start the super at sid 85 (state 3000).
        for motion in (1, 2):
            match = [r for r in rows if len(r) >= 7 and r[0] == motion]
            self.assertTrue(match, f"motion {motion} row missing")
            self.assertEqual(match[0][-1], 85,
                             f"motion {motion} must enter sid 85 (3000)")

    def test_followup_bind_has_no_catch_all_hold(self):
        # 3010 now lives in the imported grab slot 109 (the chain below),
        # not in the generic success-pose slot 86.
        rows = rows_of(self.text, "clarkBind109")
        self.assertIsNotNone(rows, "clarkBind109 missing")
        self.assertNotIn((0, 254), [r[:2] for r in rows])
        # One window per held element; the offsets follow the art scale.
        self.assertEqual([r[:2] for r in rows if len(r) >= 2],
                         [(0, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
        self.assertEqual([r[2] for r in rows[:-1]],
                         [sc(40), sc(32), sc(36), sc(20), sc(8)])
        for r in rows[:-1]:
            dy = r[3] - 256 if r[3] >= 128 else r[3]
            self.assertLessEqual(-dy, 80)

    def test_full_hold_chain_is_wired(self):
        """3010 -> 3011 -> 3012 -> 3013 -> 3014 -> 3015 -> 3016 -> stand."""
        target = rows_of(self.text, "clarkTargetTab")
        self.assertIsNotNone(target, "clarkTargetTab missing")
        # On hit the attacker goes to sid 109 (state 3010) and the victim
        # stays in the generic held slot 76.
        self.assertEqual(target[85][0], 76)
        self.assertEqual(target[85][2], 109)

        seg = self.text.split("clarkTransTab:", 1)[1]
        trans = [(int(a), int(b), int(c)) for a, b, c
                 in re.findall(r"\.db\s+(\d+),(\d+),(\d+)\n\s*\.dw", seg)]
        self.assertEqual(
            [(a, b) for a, b, _k in trans if a >= 103],
            [(103, 104), (104, 105), (105, 106), (106, 0),
             (109, 110), (110, 111), (111, 103)])
        for sid in (109, 110, 111, 103, 104, 105, 106):
            self.assertTrue(rows_of(self.text, f"clarkAct{sid}"),
                            f"clarkAct{sid} missing")

    def test_mount_bind_follows_each_element(self):
        """clarkBind53 (state 1210) used to glue the victim to one offset."""
        rows = rows_of(self.text, "clarkBind53")
        self.assertIsNotNone(rows, "clarkBind53 missing")
        self.assertNotIn((0, 254), [r[:2] for r in rows])
        self.assertIn((1, 1, sc(6), 0), rows)
        self.assertTrue(any(r[0] == 2 and r[1] == 3 and r[2] == sc(8)
                            for r in rows))     # elems 3-4 share one pos
        self.assertTrue(any(r[0] == 4 and r[1] == 4 and r[2] == (sc(-4) & 0xFF)
                            for r in rows))


class BindShadowingTests(unittest.TestCase):
    """No BindTab row may hide a later, more specific row."""

    def test_no_row_shadows_a_later_window(self):
        tables = sorted(GEN.glob("*_spr.inc"))
        self.assertTrue(tables, "run the fight build first")
        bad = []
        for path in tables:
            text = path.read_text(errors="ignore")
            for m in re.finditer(
                    r"^(\w+Bind\d+):\s*\n((?:\s*\.db[^\n]*\n)+)",
                    text, re.M):
                rows = [tuple(int(t[1:], 16) if t.startswith("$") else int(t)
                              for t in re.findall(
                                  r"\$[0-9A-Fa-f]+|\d+", line))
                        for line in m.group(2).splitlines()]
                rows = [r for r in rows if len(r) >= 2]
                for i, (lo, hi, *_rest) in enumerate(rows):
                    if hi < lo:
                        continue              # reversed: never matches
                    for lo2, hi2, *_r2 in rows[i + 1:]:
                        if hi2 < lo2:
                            continue
                        if (lo, hi) == (lo2, hi2):
                            continue          # same window: last wins
                        if lo <= lo2 and hi2 <= hi:
                            bad.append((path.name, m.group(1),
                                        (lo, hi), (lo2, hi2)))
        self.assertEqual(bad, [], f"shadowed bind rows: {bad[:10]}")


if __name__ == "__main__":
    unittest.main()
