#!/usr/bin/env python3
"""Headless regression for Chin's Zake Attack gourd specials.

QCB+P (states 1000/1100) was never wired, so the only bottle move was the
command throw.  The two QCB buttons now reach their own states and play the
gourd-to-mouth frames (group 350) before the flail hit.

Run after a PVSnesLib build:

    python3 tools/test_chin_zake_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    boot_select, enter_fight, X, Y, DOWN, LEFT,
)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1_STATE, P1_X = 0x4008, 0x4000
P2_STATE, P2_HP, P2_X = 0x4048, 0x4050, 0x4040


def qcb(core, button):
    """Quarter-circle back for a right-facing Chin, then the attack."""
    for direction in ((DOWN,), (DOWN, LEFT), (LEFT,)):
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = set()
    core.step(1)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        failures = []
        # The source package maps x -> 1000 and y -> 1100; the SNES button
        # labels are swapped by the per-character calibration, so exercise
        # both physical punches and require both wired states.
        for button, expected in ((Y, 62), (X, 65)):
            enter_fight(core, select, "chin", "kyo")
            core.ram[0x1090] = 0
            core.ram[0x1091] = 0
            core.put(P1_X, 70 << 8)
            core.put(P2_X, 90 << 8)
            core.step(20)
            qcb(core, button)
            seen, hp_start = [], core.word(P2_HP)
            for _ in range(200):
                core.step()
                state = core.ram[P1_STATE]
                if not seen or seen[-1] != state:
                    seen.append(state)
            hp_end = core.word(P2_HP)
            if expected not in seen:
                failures.append(f"button {button}: state {expected} never "
                                f"reached: {seen}")
            if hp_end >= hp_start:
                failures.append(f"button {button}: flail did no damage "
                                f"({hp_start} -> {hp_end})")
            print(f"Zake button {button}: states={seen[:8]} "
                  f"hp {hp_start}->{hp_end}")
        if failures:
            for failure in failures:
                print("FAIL:", failure)
            return 1
        print("Chin Zake Attack: both QCB states play the gourd move OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
