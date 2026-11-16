"""Heidern's Neck Rolling / Final Bringer must leave the ground and land.

The source states 1201/1211/3001/3011/3051 set VelSet y=-8 and return to the
floor through their own landing rules.  The flattened native timelines used to
keep the leap animation but drop the velocity, so the body stayed on the floor
and the whole recovery ran in place.  Pin the generated rows so that cannot
come back silently.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "build" / "gen_fight" / "heidern_spr.inc"

# sids whose generated clip is the leap: Neck Rolling weak/strong and Final
# Bringer strong/MAX; 103 is the weak Final Bringer's 3001 follow-up.
LEAP_SIDS = (52, 53, 86, 87, 103)
# Moon Slasher states: source elements 5-7 each step 8 px forward.
MOON_SLASHER_POS = {50: 3, 51: 3}


def body(lines, label):
    start = next((i for i, line in enumerate(lines)
                  if line.startswith(label + ":")), None)
    if start is None:
        return []
    out = []
    for line in lines[start + 1:]:
        if line and not line.startswith((" ", "\t")):
            break
        out.append(line.strip())
    return out


def signed(value):
    value = int(value, 0)
    return value - 256 if value >= 0x80 else value


@unittest.skipUnless(TABLES.exists(), "generated Heidern tables missing")
class HeidernLeapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = TABLES.read_text().splitlines()

    def test_leap_states_rise(self):
        act = body(self.lines, "heidernActTab")
        rising = set()
        for line in act:
            m = re.search(r"\.dw\s+(\w+Act(\d+))", line)
            if not m:
                continue
            sid = int(m.group(2))
            for row in body(self.lines, m.group(1)):
                if not row.startswith(".db"):
                    continue
                parts = [p.strip() for p in row.split(".db", 1)[1].split(",")]
                if len(parts) >= 3 and int(parts[1], 0) == 15:
                    if signed(parts[2]) < 0:
                        rising.add(sid)
        self.assertEqual([s for s in LEAP_SIDS if s not in rising], [])

    def test_leap_states_have_landing_rows(self):
        trans = body(self.lines, "heidernTransTab")
        landing = set()
        i = 0
        while i + 1 < len(trans):
            if not trans[i].startswith(".db"):
                break
            parts = [p.strip() for p in
                     trans[i].split(".db", 1)[1].split(",")]
            landing.add((int(parts[0], 0), int(parts[2], 0)))
            i += 2
        self.assertEqual([s for s in LEAP_SIDS if (s, 1) not in landing], [])

    def test_leap_clips_hold_until_landing(self):
        anim_tab = body(self.lines, "heidernAnimTab")
        labels = {}
        for sid, line in enumerate(anim_tab):
            m = re.search(r"\.dw\s+(\w+Anim\d+)", line)
            if m:
                labels[sid] = m.group(1)
        last_ticks = {}
        for sid in LEAP_SIDS:
            ticks = []
            for row in body(self.lines, labels[sid]):
                if not row.startswith(".db"):
                    continue
                parts = [p.strip() for p in row.split(".db", 1)[1].split(",")]
                if len(parts) >= 6 and parts[0].isdigit():
                    ticks.append(int(parts[0]))
            last_ticks[sid] = ticks[-1] if ticks else None
        self.assertEqual({s: t for s, t in last_ticks.items() if t != 255}, {})

    def test_moon_slasher_keeps_three_forward_steps(self):
        pos = body(self.lines, "heidernPosTab")
        for sid, count in MOON_SLASHER_POS.items():
            m = re.search(r"\.dw\s+(\w+Pos\d+)", pos[sid])
            self.assertIsNotNone(m, sid)
            rows = [r for r in body(self.lines, m.group(1))
                    if r.startswith(".db") and "$FF" not in r]
            self.assertEqual(len(rows), count, sid)
            self.assertEqual({int(r.split(".db", 1)[1].split(",")[1])
                              for r in rows}, {8}, sid)


if __name__ == "__main__":
    unittest.main()
