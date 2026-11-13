"""Yuri's normal throw keeps the victim at King's lowered bind height.

King's normal-throw bind was dropped 35 px because the port's generic held
pose puts the victim's axis at the feet.  Yuri's normal throw (THROW_Y ->
state 301, runtime slot 75) uses the same pose, so its generated bind must
carry the same drop instead of the old -53 px hold.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "build" / "gen_fight"
YURI = GEN / "yuri_spr.inc"


def rows_of(text, label):
    match = re.search(rf"^{re.escape(label)}:\s*\n((?:\s*\.db[^\n]*\n)+)",
                      text, re.MULTILINE)
    if not match:
        return []
    out = []
    for line in match.group(1).splitlines():
        nums = [int(t[1:], 16) if t.startswith("$") else int(t)
                for t in re.findall(r"\$[0-9A-Fa-f]+|-?\d+", line)]
        if nums and nums[0] != 0xFF:
            out.append(tuple(nums))
    return out


def s8(value):
    return value - 256 if value >= 128 else value


@unittest.skipUnless(YURI.exists(), "run the PVSnesLib build first")
class NormalThrowBindHeightTest(unittest.TestCase):
    def test_yuri_throw_y_bind_is_lowered(self):
        bind = rows_of(YURI.read_text(), "yuriBind75")
        self.assertTrue(bind, "Yuri normal-throw bind (sid 75) is missing")
        for lo, hi, _dx, dy in bind:
            self.assertGreaterEqual(
                s8(dy), -30,
                f"Yuri bind {lo}-{hi} still hangs the victim at {s8(dy)} px")
            self.assertLessEqual(
                s8(dy), -1,
                f"Yuri bind {lo}-{hi} dropped the victim to the floor")


if __name__ == "__main__":
    unittest.main()
