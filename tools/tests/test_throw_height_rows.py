import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_fight  # noqa: E402

GEN = ROOT / "build" / "gen_fight"

MAX_HOLD_LIFT = 80          # px above the floor for TargetBind holds
MAX_GUARD_LAUNCH = 1664     # 8.8 fixed: 6.5 px/tick upward


def val(token):
    return int(token[1:], 16) if token.startswith("$") else int(token)


def s8(v):
    return v - 256 if v >= 128 else v


def s16(v):
    return v - 65536 if v >= 32768 else v


class ThrowHeightRowsTests(unittest.TestCase):
    def test_targetbind_hold_height_is_capped(self):
        """Throw/grab binds must not lift the victim into the HUD/off-screen."""
        tables = sorted(GEN.glob("*_spr.inc"))
        self.assertTrue(tables, "run the fight build before this test")
        bad = []
        for path in tables:
            if path.name == "kfm_spr.inc":
                continue
            text = path.read_text(errors="ignore")
            for m in re.finditer(
                    r"^\w+Bind\d+:\s*\n((?:\s*\.db[^\n]*\n)+)",
                    text, re.M):
                for line in m.group(1).splitlines():
                    nums = [val(x) for x in re.findall(
                        r"\$[0-9A-Fa-f]+|\d+", line)]
                    if len(nums) < 4 or nums[0] == 0xFF:
                        continue
                    lift = -s8(nums[3])
                    if lift > MAX_HOLD_LIFT:
                        bad.append(f"{path.name}: lift {lift}: {line.strip()}")
        self.assertEqual(bad, [])

    def test_guard_cancel_launch_is_capped(self):
        """Sid 67 (X+A guard cancel) must not launch the victim too high."""
        tables = sorted(GEN.glob("*_spr.inc"))
        self.assertTrue(tables, "run the fight build before this test")
        bad = []
        for path in tables:
            if path.name == "kfm_spr.inc":
                continue
            m = re.search(
                r"^\w+HitVelTab:\s*\n((?:\s*\.dw[^\n]*\n)+)",
                path.read_text(errors="ignore"), re.M)
            if not m:
                continue
            rows = [[val(x) for x in re.findall(
                r"\$[0-9A-Fa-f]+|\d+", line)]
                for line in m.group(1).splitlines()]
            rows = [r for r in rows if len(r) >= 4]
            if len(rows) <= 67:
                continue
            gvy, avy = s16(rows[67][1]), s16(rows[67][3])
            if gvy < -MAX_GUARD_LAUNCH or avy < -MAX_GUARD_LAUNCH:
                bad.append(f"{path.name}: sid67 gvy={gvy} avy={avy}")
        self.assertEqual(bad, [])


class ThrowBindScaleTests(unittest.TestCase):
    """Bind offsets follow the fighter art scale.

    At char_scale 0.81 a source -64 px hold becomes -52 px; at 1.0 it stays
    -64 px.  This keeps a thrown opponent at the same body-relative height
    when the roster scale changes.
    """

    def _binds(self, name, scale):
        cfg = build_fight.CHARS[name]
        cns = build_fight.parse_cns(
            os.path.join(build_fight.ROOT, cfg["cns"]),
            cfg.get("coord_scale", 1), cfg.get("damage_scale", 1),
            char=name, char_scale=scale)
        return cns[5]

    def test_chris_bind_follows_art_scale(self):
        scaled = self._binds("chris", 0.81)[860]
        full = self._binds("chris", 1.0)[860]
        self.assertIn(-52, [dy for _lo, _hi, _dx, dy in scaled])
        self.assertIn(-64, [dy for _lo, _hi, _dx, dy in full])

    def test_source_hold_lift_is_clamped_in_port_pixels(self):
        for scale in (0.81, 1.0):
            binds = self._binds("kyo", scale)
            lifts = [-dy for rows in binds.values() for _lo, _hi, _dx, dy in rows]
            self.assertLessEqual(max(lifts, default=0), MAX_HOLD_LIFT)


if __name__ == "__main__":
    unittest.main()
