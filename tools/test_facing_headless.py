#!/usr/bin/env python3
"""Regression: close attacks must face the opponent beyond 128 px.

FaceCloseAttack used to subtract the two 8.8 X words and test the sign; a
distance of 128 px or more overflows bit 15, so P1 at the left corner turned
his back to P2 and attacked the wrong way.

Run after a PVSnesLib build:

    python3 tools/test_facing_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import enter_fight, tap, wait  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS, START, X = 0x1020, 3, 9
P1_X, P2_X = 0x4000, 0x4040
P1_FACING = 0x400E


def boot_select(core):
    wait(core, lambda: core.word(GS) == 14, "msu opening", 4000)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(60)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    core.ram[0xF070] = 1
    tap(core, START)
    wait(core, lambda: core.word(GS) == 5, "select")
    core.ram[0x1091] = 0
    core.step(10)
    return core.save()


def face_after_attack(core, select, p1x, p2x):
    enter_fight(core, select, "kyo", "kyo")
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.put(P1_X, p1x << 8)
    core.put(P2_X, p2x << 8)
    core.step(20)
    core.buttons[0] = {X}
    core.step(3)
    core.buttons[0] = set()
    return core.word(P1_FACING), core.ram[0x4008]


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        cases = [
            # (p1x, p2x, expected facing, label)
            (20, 200, 1, "left corner, 180 px"),
            (60, 200, 1, "mid screen, 140 px"),
            (60, 140, 1, "boundary, 80 px"),
            (60, 40, -1, "crossed, opponent left"),
            (200, 20, -1, "right corner, opponent left"),
        ]
        for p1x, p2x, want, label in cases:
            got, state = face_after_attack(core, select, p1x, p2x)
            signed = -1 if got & 0x8000 else 1
            if signed != want:
                print(f"FAIL {label}: facing={signed} wanted {want} "
                      f"(state {state})")
                return 1
            print(f"OK facing {label}: {signed:+d}")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
