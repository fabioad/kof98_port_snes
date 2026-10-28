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
        rows = rows_of(self.text, "clarkBind86")
        self.assertIsNotNone(rows, "clarkBind86 missing")
        self.assertNotIn((0, 254), [r[:2] for r in rows])
        self.assertEqual(rows, [(0, 1, 40, 0), (2, 2, 32, 0),
                                (3, 3, 36, 176), (4, 4, 20, 176),
                                (5, 5, 8, 176), (255,)])

    def test_mount_bind_follows_each_element(self):
        """clarkBind53 (state 1210) used to glue the victim to one offset."""
        rows = rows_of(self.text, "clarkBind53")
        self.assertIsNotNone(rows, "clarkBind53 missing")
        self.assertNotIn((0, 254), [r[:2] for r in rows])
        self.assertIn((1, 1, 6, 0), rows)
        self.assertIn((2, 3, 8, 177), rows)      # elems 3-4 share one pos
        self.assertIn((4, 4, 252, 176), rows)


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
