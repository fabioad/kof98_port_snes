#!/usr/bin/env python3
"""Headless regression for the boss run/backdash animation frames.

M. Bison, Omega Rugal and Mr. Karate must enter the generic run/backdash
states (45/46) with real multi-pose clips:
  * Vega's run starts at the AIR 100 Loopstart, not the two oversized crouch
    startup cels;
  * Omega's source 105 only has one backdash cel, so the port reuses the
    five-pose jump-back clip (AIR 43);
  * Mr. Karate also uses the seven-pose jump-back clip instead of Robert's
    two-cel source 105 plus synthetic dissolves.

Run after a PVSnesLib build:

    python3 tools/test_boss_dash_frames_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                 # noqa: E402
    boot_select, enter_fight, HIDDEN)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_FRAME, F_NFR, F_X = 0x4008, 0x400A, 0x4014, 0x4000
FP2 = 0x40
LEFT, RIGHT = 6, 7

CASES = {
    # name: (run state, backdash state, min run poses, min backdash poses)
    "vega": (45, 46, 7, 4),
    "omegarugal": (45, 46, 8, 5),
    "mrkarate": (45, 46, 8, 7),
}


def double(core, direction):
    core.buttons[0] = {direction}
    core.step(3)
    core.buttons[0] = set()
    core.step(3)
    core.buttons[0] = {direction}
    core.step(3)


def sample(core, state, hold=None, frames=50):
    if hold is not None:
        core.buttons[0] = {hold}
    seen = False
    poses = 0
    for _ in range(frames):
        if core.ram[F_STATE] == state:
            seen = True
            poses = max(poses, core.ram[F_NFR] or 0)
        core.step()
        if seen and core.ram[F_STATE] == 0:
            break
    core.buttons[0] = set()
    return seen, poses


def main(core_path, rom):
    HIDDEN["mrkarate"] = {10, 11}
    core = Core(core_path, rom)
    try:
        select = boot_select(core)
        for name, (run_sid, back_sid, run_poses, back_poses) in CASES.items():
            enter_fight(core, select, name, "kyo")
            core.put(F_X, 100 << 8)
            core.put(F_X + FP2, 180 << 8)
            core.step(20)

            double(core, RIGHT)
            seen, poses = sample(core, run_sid, hold=RIGHT)
            if not seen:
                raise AssertionError(f"{name}: FF did not enter run state")
            if poses < run_poses:
                raise AssertionError(
                    f"{name}: run clip has {poses} poses, expected "
                    f">= {run_poses}")

            core.step(20)
            double(core, LEFT)
            seen, poses = sample(core, back_sid)
            if not seen:
                raise AssertionError(f"{name}: BB did not enter backdash state")
            if poses < back_poses:
                raise AssertionError(
                    f"{name}: backdash clip has {poses} poses, expected "
                    f">= {back_poses}")

            print(f"PASS {name}: run {run_poses}+ poses, "
                  f"backdash {back_poses}+ poses", flush=True)
        print("PASS boss run/backdash frames are active", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path,
                        default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, args.rom)
