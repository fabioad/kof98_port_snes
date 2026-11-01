#!/usr/bin/env python3
"""Ken and Sakura strong Shoryuken: five hits and a knockdown.

The source DP+P strong variants already carry a five-contact follow-up
chain.  This regression drives the command and requires the combo counter to
reach 5 and the victim to end in S_DOWN (10).

Run after a PVSnesLib build:

    python3 tools/test_shoryuken_five_hits_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_X, F_HP = 0x4008, 0x4000, 0x4010
FP2 = 0x40
COMBO = 0x4FC0
DOWN, RIGHT = 5, 7
DOWN_RIGHT = (DOWN, RIGHT)
STRONG_P = 9


def hold(core, buttons, ticks):
    core.buttons[0] = set(buttons)
    core.step(ticks)


def press(core, buttons, ticks=1):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def run_case(core, select_state, name):
    enter_fight(core, select_state, name, "kyo")
    core.put(F_X, 100 << 8)
    core.put(F_X + FP2, 135 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.step(20)

    hold(core, {RIGHT}, 3)                # ~F, D, DF + strong punch
    hold(core, {DOWN}, 3)
    hold(core, DOWN_RIGHT, 3)
    press(core, {STRONG_P}, 2)

    peak = 0
    min_hp = 200
    states = set()
    for _ in range(140):
        core.step()
        peak = max(peak, core.ram[COMBO])
        min_hp = min(min_hp, core.word(F_HP + FP2))
        states.add(core.ram[F_STATE + FP2])
    return peak, min_hp, states


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for name in ("ken", "sakura"):
            peak, min_hp, states = run_case(core, select_state, name)
            if peak != 5:
                raise AssertionError(
                    f"{name}: Shoryuken combo peak {peak}, wanted 5")
            if 10 not in states:
                raise AssertionError(
                    f"{name}: victim was not knocked down "
                    f"(states={sorted(states)})")
            print(f"PASS {name:7} strong Shoryuken: 5 HITS, "
                  f"{200 - min_hp} damage, knockdown", flush=True)
        print("PASS Shoryuken five-hit knockdown", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
