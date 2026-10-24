#!/usr/bin/env python3
"""Headless regression: M.Bison's crouch strong kick slides half a screen.

MUGEN state 440 (sid 22) gives the sweep a VelSet at animation element 4
with VelMul damping.  Crouching attack states used to pin F_VX to zero on
every tick, so the compiled ActTab op5 rows never moved the fighter.  The
state handler now keeps F_VX for moves whose FlagsTab bit12 is set, and the
tuned VelSet makes the sweep travel about half of the 256 px screen.

Run after a PVSnesLib build:

    python3 tools/test_vega_sweep_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_X = 0x4008, 0x4000
FP2 = 0x40
DOWN, A = 5, 8                           # libretro down + SNES A (strong kick)
SWEEP = 22                               # MUGEN 440
HALF_SCREEN = 128
TOLERANCE = 8                            # px; Q8 damping + clamp in the engine


def sweep(core, select_state, p1x, p2x):
    enter_fight(core, select_state, "vega", "kyo")
    core.put(F_X, p1x << 8)
    core.put(F_X + FP2, p2x << 8)
    core.step(20)
    x0 = core.word(F_X)
    core.buttons[0] = {DOWN}
    core.step(6)
    core.buttons[0] = {DOWN, A}
    core.step(3)
    core.buttons[0] = set()
    entered = False
    for _ in range(90):
        entered = entered or core.ram[F_STATE] == SWEEP
        core.step()
    return x0, core.word(F_X), entered


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        # Face right and left; keep the opponent out of body-separation range
        # so the measurement is the move's full free-space travel.
        for label, p1x, p2x, sign in (("right", 40, 230, 1),
                                      ("left", 200, 40, -1)):
            x0, x1, entered = sweep(core, select_state, p1x, p2x)
            dx = (x1 - x0) / 256.0
            assert entered, f"{label}: never entered state {SWEEP}"
            assert dx * sign > 0, f"{label}: sweep moved the wrong way ({dx})"
            assert abs(abs(dx) - HALF_SCREEN) <= TOLERANCE, (
                f"{label}: sweep travelled {dx:.1f} px, expected "
                f"{HALF_SCREEN}±{TOLERANCE}")
            print(f"OK {label}: state {SWEEP}, {abs(dx):.1f} px travel")
    finally:
        core.close()
    print("PASS: M.Bison's crouch strong kick slides half a screen")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
