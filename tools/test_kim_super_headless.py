#!/usr/bin/env python3
"""Headless check for Kim's Houou Kyaku supers (sids 107/108)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040
STATE, HP, POWER = 0x4008, 0x4010, 0x4030
DOWN, LEFT, RIGHT = 5, 6, 7
Y, X, B, A = 1, 9, 0, 8


def seq_press(core, seq, buttons):
    for d in seq:
        core.buttons[0] = set(d)
        core.step(HOLD)
    core.buttons[0] = set(seq[-1]) | set(buttons)
    core.step(2)
    core.buttons[0] = set()


# QCB x2 + kick (Houou Kyaku)
HOLD = int(__import__("os").environ.get("HOLD", "2"))
QCF2 = [(DOWN,), (DOWN, LEFT), (LEFT,)] * 2


def run(core, select, buttons, power=3000):
    enter_fight(core, select, "kim", "kyo")
    core.put(P1, 80 << 8)
    core.put(P2, 100 << 8)
    core.put(HP, 300)
    core.put(HP + 0x40, 300)
    core.put(POWER, power)
    core.step(10)
    start = core.word(HP + 0x40)
    seq_press(core, QCF2, buttons)
    path = []
    for _ in range(260):
        core.step()
        s = core.ram[STATE]
        if not path or path[-1] != s:
            path.append(s)
    return path, start - core.word(HP + 0x40)


def main():
    core = Core(CORE, __import__("os").environ.get("ROM", str(ROOT / "kof98-snes.sfc")))
    fail = 0
    try:
        select = boot_select(core)
        for name, buttons, sid in (("Houou Kyaku", [A], 107),
                                   ("Houou Kyaku MAX", [A, B], 108)):
            path, dmg = run(core, select, buttons)
            ok = sid in path and dmg > 0
            print("PASS" if ok else "FAIL", name, f"dmg={dmg} path={path}")
            fail += not ok
    finally:
        core.close()
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
