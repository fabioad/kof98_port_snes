#!/usr/bin/env python3
"""Blue Mary's advancing leg grab must finish in the choke/damage state.

The source 1900 grab binds the victim and hands over to 1910; the choke
damage lives in state 1065.  The native import previously stopped at 1910,
so the move held the opponent and then released without damage.  This checks
the full chain: 1900/1910 hold -> 1065 choke -> victim held and knocked down.

Run after a PVSnesLib build:

    python3 tools/test_mary_choke_headless.py
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
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
DOWN_LEFT, DOWN_RIGHT = (DOWN, LEFT), (DOWN, RIGHT)
STRONG_K = 8


def hold(core, buttons, ticks):
    core.buttons[0] = set(buttons)
    core.step(ticks)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "mary", "kyo")
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, 135 << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.step(20)

        # Command: F, DF, D, DB, B, F + strong kick (Mary's advancing grab).
        for direction in ({RIGHT}, DOWN_RIGHT, {DOWN}, DOWN_LEFT,
                          {LEFT}, {RIGHT}):
            hold(core, direction, 3)
        hold(core, {STRONG_K}, 3)
        core.buttons[0] = set()

        p1_states = set()
        p2_states = set()
        min_hp = 200
        for _ in range(300):
            core.step()
            p1_states.add(core.ram[F_STATE])
            p2_states.add(core.ram[F_STATE + FP2])
            min_hp = min(min_hp, core.word(F_HP + FP2))

        if 110 not in p1_states:
            raise AssertionError(
                f"grab hold state 110 missing (P1 states={sorted(p1_states)})")
        if 98 not in p1_states:
            raise AssertionError(
                f"choke/damage state 98 missing (P1 states={sorted(p1_states)})")
        if 76 not in p2_states:
            raise AssertionError(
                f"victim was not held (P2 states={sorted(p2_states)})")
        if 10 not in p2_states:
            raise AssertionError(
                f"victim was not knocked down (P2 states={sorted(p2_states)})")
        damage = 200 - min_hp
        if not 20 <= damage <= 25:
            raise AssertionError(
                f"choke damage {damage}, wanted ~20 (source 150/1500 life)")
        print(f"PASS Blue Mary grab: hold -> choke {damage} damage -> knockdown",
              flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
