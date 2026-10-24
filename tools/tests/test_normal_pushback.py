import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from build_fight import (CHARS, DAMAGE_NORMAL_SIDS,  # noqa: E402
                         NORMAL_PUSH_LIMIT, ROOT)


def _table(text, name):
    """Read a generated ``.dw`` table as a list of integer lists."""
    start = text.index(name + ":\n")
    values = []
    for line in text[start:].splitlines()[1:]:
        line = line.strip()
        if not line.startswith(".dw"):
            break
        cells = []
        for cell in line[3:].split(","):
            cell = cell.strip()
            cells.append(int(cell[1:], 16) if cell.startswith("$")
                         else int(cell, 10))
        values.append(cells)
    return values


def _signed(value):
    return value - 0x10000 if value >= 0x8000 else value


class NormalPushbackTests(unittest.TestCase):
    def test_normals_stay_within_a_third_of_the_screen(self):
        """Imported arcade velocities must not pin the victim to the wall."""
        checked = 0
        for name in sorted(CHARS):
            path = os.path.join(ROOT, "build/gen_fight",
                                f"{name}_spr.inc")
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
            try:
                hittime = _table(text, name + "HitTimeTab")
                slide = _table(text, name + "SlideTab")
                hits = _table(text, name + "HitVelTab")
                guard = _table(text, name + "GVelTab")
            except ValueError:
                continue
            for sid in DAMAGE_NORMAL_SIDS:
                if sid >= len(hittime) or sid >= len(slide):
                    continue
                ground = min(hittime[sid][0], slide[sid][0])
                air = slide[sid][0]
                if ground <= 0 and air <= 0:
                    continue
                # HitVel is (ground vx, ground vy, air vx, air vy);
                # GVel is (ground vx, air vx, air vy).
                for label, table, idx, window in (
                        ("hit", hits, 0, ground),
                        ("air hit", hits, 2, air),
                        ("guard", guard, 0, ground),
                        ("air guard", guard, 1, air)):
                    if sid >= len(table) or window <= 0:
                        continue
                    velocity = _signed(table[sid][idx])
                    travel = abs(velocity) * window / 256.0
                    self.assertLessEqual(
                        travel, NORMAL_PUSH_LIMIT + 0.5,
                        f"{name} sid {sid} {label} travels {travel:.1f}px")
                    checked += 1
        self.assertGreater(checked, 100)


if __name__ == "__main__":
    unittest.main()
