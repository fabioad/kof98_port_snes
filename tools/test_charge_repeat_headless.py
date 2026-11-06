#!/usr/bin/env python3
"""Charge specials must not repeat from a bare button after one use.

Kyo and M. Bison use a back-charge then forward+button command.  The input
ring keeps the charged direction entry so commands sharing a prefix still
work, but the charged entry itself must be spent when the special fires;
otherwise holding forward and pressing the button again repeats the move
without a new 40-tick charge.

Run after a PVSnesLib build:

    python3 tools/test_charge_repeat_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040
F_STATE = P1 + 8
LEFT, RIGHT = 6, 7
WEAK = 1
SPECIAL_SID = 48          # state 1000 on both Kyo and Vega
FRESH_CHARGE = 70


def reset(core):
    core.ram[0x1090] = core.ram[0x1091] = 0
    core.put(P1, 82 << 8)
    core.put(P2, 100 << 8)
    core.put(P1 + 0x10, 200)
    core.put(P2 + 0x10, 200)
    core.buttons = [set(), set()]
    core.step(20)


def charge_and_fire(core):
    core.buttons[0] = {LEFT}
    core.step(FRESH_CHARGE)
    core.buttons[0] = {RIGHT, WEAK}
    core.step(3)
    core.buttons[0] = {RIGHT}       # keep forward held, as the bug report does
    path = []
    for _ in range(240):
        core.step()
        state = core.ram[F_STATE]
        if not path or path[-1] != state:
            path.append(state)
        if state == 0 and len(path) > 2:
            break
    return path


def bare_button(core):
    core.step(5)
    core.buttons[0] = {RIGHT, WEAK}
    core.step(3)
    core.buttons[0] = {RIGHT}
    path = []
    for _ in range(120):
        core.step()
        state = core.ram[F_STATE]
        if not path or path[-1] != state:
            path.append(state)
    return path


def run(core, char):
    enter_fight(core, boot_select(core), char, "kyo")
    reset(core)
    first = charge_and_fire(core)
    assert SPECIAL_SID in first, f"{char}: charge command did not fire: {first}"
    reset(core)
    second = bare_button(core)
    assert SPECIAL_SID not in second, (
        f"{char}: bare button reused the old charge: {second}")
    reset(core)
    fresh = charge_and_fire(core)
    assert SPECIAL_SID in fresh, f"{char}: fresh charge did not rearm: {fresh}"
    return first, second, fresh


def main():
    for char in ("kyo", "vega"):
        core = Core(CORE, ROOT / "kof98-snes.sfc")
        try:
            first, second, fresh = run(core, char)
            print(f"PASS {char}: first {first}, bare {second}, fresh {fresh}")
        finally:
            core.close()


if __name__ == "__main__":
    main()
