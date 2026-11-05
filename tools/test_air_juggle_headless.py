#!/usr/bin/env python3
"""Airborne projectile juggle rule.

A falling opponent can be hit by a projectile, which starts another fall and
extends the combo.  Only one *single-hit* shot may land per fall so two
fireballs cannot loop forever; a multi-hit super projectile (the port marks
it at spawn) is exempt and keeps all its contacts.  Landing clears the
budget for the next fall.

Run after a PVSnesLib build:

    python3 tools/test_air_juggle_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_X1, F_X2 = FP1, FP2
F_Y2 = FP2 + 2
F_VY2 = FP2 + 6
F_STATE1, F_STATE2 = FP1 + 8, FP2 + 8
F_HP2 = FP2 + 0x10
F_POWER1 = FP1 + 0x30

DOWN, RIGHT = 5, 7
LIGHT_P, STRONG_P = 1, 9
QCF = (frozenset({DOWN}), frozenset({DOWN, RIGHT}), frozenset({RIGHT}))
AIR_Y = 20 << 8


def qcf(core, button, twice=False):
    for _ in range(2 if twice else 1):
        for direction in QCF:
            core.buttons[0] = set(direction)
            core.step(3)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()


def hold_air(core, ticks):
    for _ in range(ticks):
        core.put(F_Y2, AIR_Y)
        core.put(F_VY2, 0)
        core.step()


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "sakura", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(F_X1, 40 << 8)
        core.put(F_X2, 180 << 8)
        core.put(F_HP2, 200)
        core.put(F_POWER1, 3000)
        # Put Kyo in an airborne fall (S_DOWN with height) and keep him there
        # while the shots arrive; a real launcher would do the same.
        core.ram[F_STATE2] = 10
        core.put(F_Y2, AIR_Y)
        core.put(F_VY2, 0)
        core.step(5)

        qcf(core, LIGHT_P)
        hold_air(core, 70)
        hp1 = core.word(F_HP2)
        assert hp1 == 186, f"first shot on a falling foe: hp={hp1}, want 186"
        print("PASS air juggle: falling foe hit by the first projectile")

        qcf(core, LIGHT_P)
        hold_air(core, 70)
        hp2 = core.word(F_HP2)
        assert hp2 == hp1, (
            f"second one-hit shot was not blocked: hp={hp2}, want {hp1}")
        print("PASS air juggle: a second single-hit shot passes through")

        qcf(core, STRONG_P, twice=True)
        hold_air(core, 120)
        hp3 = core.word(F_HP2)
        assert hp3 == hp2 - 70, (
            f"multi-hit super lost contacts: hp={hp3}, want {hp2 - 70}")
        print("PASS air juggle: multi-hit super keeps all five contacts")

        core.put(F_Y2, 0)
        core.put(F_VY2, 0)
        core.ram[F_STATE2] = 10
        core.step(6)
        qcf(core, LIGHT_P)
        hold_air(core, 70)
        hp4 = core.word(F_HP2)
        assert hp4 == hp3 - 14, (
            f"landing did not clear the air-juggle budget: hp={hp4}")
        print("PASS air juggle: landing restores one shot per new fall")
        print("PASS airborne projectile juggle rule")
    finally:
        core.close()


if __name__ == "__main__":
    main()
