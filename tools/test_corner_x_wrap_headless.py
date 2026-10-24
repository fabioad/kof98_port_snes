#!/usr/bin/env python3
"""Regression: corner movement must never wrap a fighter to the far wall.

A 16-bit `adc` on the 8.8 X coordinate wraps when a cornered fighter is
pushed past the bound: 24 - 25 px became $FFFF, and ClampX read the wrapped
value as past the *right* wall, teleporting the victim to the opposite
corner.  The same happened on the right corner (232 + 25 px -> $0100 ->
clamped to the left bound).  Throw binds had the same problem: a negative
bind offset near the left wall wrote a wrapped X and the victim snapped to
the other corner when released.

Run after a PVSnesLib build:

    python3 tools/test_corner_x_wrap_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
GS = 0x1020
FP1, FP2 = 0x4000, 0x4040
F_X, F_Y, F_VX, F_VY = 0, 2, 4, 6
F_STATE, F_FRAME, F_FTICK, F_FACING = 8, 10, 12, 14
F_NFR, F_HTIMER, F_SLIDE, F_OWNER = 20, 40, 42, 53
F_JOYPR, F_STIME = 34, 60
S_STAND, S_HIT, S_TSEQ, S_VHELD = 0, 9, 75, 76
STAGE_L, STAGE_R = 24, 232


def x(core, base):
    return core.word(base + F_X) / 256.0


def assert_inside(core, label):
    x1, x2 = x(core, FP1), x(core, FP2)
    assert STAGE_L <= x1 <= STAGE_R and STAGE_L <= x2 <= STAGE_R, (
        f"{label}: fighter outside the stage: {x1:.1f}/{x2:.1f}")


def hit_corner(core, start, velocity):
    """Put P2 in hitstun at a wall and step one tick of Physics."""
    core.put(FP1 + F_X, 150 << 8)
    core.put(FP2 + F_X, start << 8)
    core.put(FP2 + F_VX, velocity)
    core.put(FP2 + F_VY, 0)
    core.put(FP2 + F_Y, 0)
    core.put(FP2 + F_HTIMER, 30)
    core.put(FP2 + F_FRAME, 0)
    core.ram[FP2 + F_FTICK] = 5
    core.ram[FP2 + F_SLIDE] = 0
    core.ram[FP2 + F_STATE] = S_HIT
    core.step()
    assert core.ram[FP2 + F_STATE] == S_HIT, "victim left hitstun"
    assert_inside(core, f"hit from {start}px at {velocity / 256:+.0f}px/t")
    assert abs(x(core, FP2) - start) <= 1.0, (
        f"hit at {start}px, vx={velocity / 256:+.0f}: victim jumped to "
        f"{x(core, FP2):.1f}px")


def bind_corner(core):
    """Billy's throw bind steps back 82px at frame 6; at x=80 that crosses
    the left wall and used to wrap to $FFFE."""
    core.put(FP1 + F_X, 80 << 8)
    core.put(FP1 + F_VX, 0)
    core.put(FP1 + F_FACING, 1)
    core.put(FP1 + F_FRAME, 6)
    core.put(FP1 + F_NFR, 20)
    core.ram[FP1 + F_FTICK] = 200
    core.ram[FP1 + F_STATE] = S_TSEQ
    core.put(FP2 + F_X, 150 << 8)
    core.ram[FP2 + F_STATE] = S_VHELD
    core.ram[FP2 + F_OWNER] = 0
    core.put(FP2 + F_JOYPR, 0)
    core.put(FP2 + F_STIME, 20)
    core.put(FP2 + F_FRAME, 0)
    core.put(FP2 + F_NFR, 20)
    core.ram[FP2 + F_FTICK] = 200
    core.step()
    assert_inside(core, "throw bind behind the left corner")
    assert abs(x(core, FP2) - STAGE_L) <= 1.0, (
        f"throw bind placed the victim at {x(core, FP2):.1f}px "
        f"instead of the left wall")


def main(core_path=CORE, rom=ROM):
    core = Core(core_path, rom)
    try:
        sel = boot_select(core)
        enter_fight(core, sel, "kyo", "kyo")
        hit_corner(core, STAGE_L, -25 << 8)   # underflow at the left wall
        hit_corner(core, STAGE_R, 25 << 8)    # overflow at the right wall
        print("OK hit pushback saturates at both stage bounds")

        core.buttons = [set(), set()]
        core.load(sel)
        enter_fight(core, sel, "billy", "kyo")
        bind_corner(core)
        print("OK throw bind saturates at the stage bound")
        print("PASS corner X never wraps to the opposite corner")
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROM)
    args = ap.parse_args()
    main(args.core, args.rom)
