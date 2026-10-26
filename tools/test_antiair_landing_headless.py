#!/usr/bin/env python3
"""Rising anti-airs must land into S_LAND instead of holding 255 ticks.

Choi's Hien Zan (1500/1510) and Athena's Phoenix Arrow (1020) both have a
landing ChangeState guarded by an ``AnimElem = N,> 0`` window.  The native
TransTab extractor treated that guard as unsupported and dropped the landing
row, leaving the fighter on the animation's 255-tick trailing hold after
touching the floor (the "slow recovery" reported for Choi).

Run after a PVSnesLib build:

    python3 tools/test_antiair_landing_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                          # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE = 8
RIGHT, DOWN = 7, 5
A, B, Y = 8, 0, 1                 # libretro A/B/Y
LAND = 17                         # S_LAND
CASES = (
    ("choi", B, "Choi weak Hien Zan"),
    ("choi", A, "Choi strong Hien Zan"),
    ("athena", Y, "Athena Phoenix Arrow"),
)


def rise_and_land(core, select_state, char, button, label):
    enter_fight(core, select_state, char, "kyo")
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.put(FP1, 100 << 8)
    core.put(FP2, 190 << 8)
    core.step(8)

    # ~F, D, DF + button
    for direction in ({RIGHT}, {DOWN}, {DOWN, RIGHT}):
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = set()
    core.step(1)
    core.buttons[0] = {button}
    core.step(2)
    core.buttons[0] = set()

    states = []
    landing_ticks = 0
    in_landing = False
    for _ in range(300):
        core.step()
        state = core.ram[FP1 + F_STATE]
        if not states or states[-1] != state:
            states.append(state)
        if state == LAND:
            in_landing = True
            landing_ticks += 1
        elif in_landing:
            break
    if LAND not in states:
        raise AssertionError(f"{label}: never entered S_LAND: {states}")
    if landing_ticks > 8:
        raise AssertionError(
            f"{label}: S_LAND recovery took {landing_ticks} ticks: {states}")
    if core.ram[FP1 + F_STATE] != 0:
        raise AssertionError(
            f"{label}: did not recover: state={core.ram[FP1 + F_STATE]}")
    print(f"PASS {label}: states={states}, S_LAND={landing_ticks}t",
          flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for char, button, label in CASES:
            rise_and_land(core, select_state, char, button, label)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
