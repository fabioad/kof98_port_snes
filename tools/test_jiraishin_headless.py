#!/usr/bin/env python3
"""Regression: Daimon's weak Jiraishin is a full-screen trip.

The weak punch version (Y + DP) must knock down a grounded opponent anywhere
on the stage, stay blockable from stand or crouch, and whiff while the victim
is airborne.  The CPU should block most attempts, not every attempt.

Run after a PVSnesLib build:

    python3 tools/test_jiraishin_headless.py
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    enter_fight, tap, wait, GS, START)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
P1, P2 = 0x4000, 0x4040
F_STATE, F_HP, F_Y = 0x4008, 0x4010, 0x4002
FP2 = 0x40
DOWN, LEFT, RIGHT, UP, Y = 5, 6, 7, 4, 1
GUARD_STATES = {27, 28, 30, 31, 79, 81}


def word(core, addr):
    return core.word(addr)


def press(core, button, frames=3):
    core.buttons[0] = {button}
    core.step(frames)
    core.buttons[0] = set()
    core.step(1)


def jiraishin_weak(core):
    """DP + weak punch (SNES Y) -> state 48."""
    for direction in ((RIGHT,), (DOWN,), (DOWN, RIGHT), (RIGHT,)):
        core.buttons[0] = set(direction)
        core.step(2)
    core.step(1)
    press(core, Y)


def boot_select(core):
    """Skip the MSU opening (gs14) and stop on the character select."""
    wait(core, lambda: core.word(GS) == 14, "msu opening", 4000)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(60)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    core.ram[0xF070] = 0                       # SINGLE PLAY
    tap(core, START)
    wait(core, lambda: core.word(GS) == 5, "select")
    core.step(10)
    return core.save()


def run_case(core, select_state, label, p1x, p2x, hold=None, jump=False,
             cpu=False):
    enter_fight(core, select_state, "daimon", "kyo")
    core.ram[0x1090] = 0
    core.ram[0x1091] = 1 if cpu else 0
    core.put(P1, p1x << 8)
    core.put(P2, p2x << 8)
    core.step(random.randint(2, 25) if cpu else 20)
    hp0 = word(core, F_HP + FP2)
    if jump:
        core.buttons[1] = {UP}
    elif hold and not cpu:
        core.buttons[1] = set(hold)
    jiraishin_weak(core)
    if jump:
        core.step(2)
        core.buttons[1] = set()
    min_hp = hp0
    down = guarded = False
    for _ in range(90):
        if hold and not cpu and not jump:
            core.buttons[1] = set(hold)
        core.step()
        state2 = core.ram[F_STATE + FP2]
        min_hp = min(min_hp, word(core, F_HP + FP2))
        down |= state2 == 10
        guarded |= state2 in GUARD_STATES
    core.buttons[1] = set()
    return hp0 - min_hp, down, guarded


def main():
    core = Core(CORE, str(ROM))
    try:
        select = boot_select(core)
        fails = []

        loss, down, guarded = run_case(core, select, "far idle", 60, 200)
        if loss < 40 or not down or guarded:
            fails.append(f"far idle: loss={loss} down={down} guarded={guarded}")

        loss, down, guarded = run_case(core, select, "close idle", 60, 90)
        if loss < 40 or not down or guarded:
            fails.append(f"close idle: loss={loss} down={down} guarded={guarded}")

        for label, hold in (("stand block", (RIGHT,)),
                            ("crouch block", (RIGHT, DOWN))):
            loss, down, guarded = run_case(
                core, select, label, 60, 200, hold=hold)
            if loss > 2 or down or not guarded:
                fails.append(
                    f"{label}: loss={loss} down={down} guarded={guarded}")

        loss, down, guarded = run_case(core, select, "air whiff", 60, 200,
                                       jump=True)
        if loss != 0 or down:
            fails.append(f"air whiff: loss={loss} down={down}")

        blocks = hits = 0
        for _ in range(12):
            loss, down, guarded = run_case(
                core, select, "cpu", random.choice((50, 80)),
                random.choice((170, 210)), cpu=True)
            if loss >= 20 or down:
                hits += 1
            else:
                blocks += 1
        if blocks < 6:
            fails.append(f"cpu block rate: blocks={blocks} hits={hits}")

        if fails:
            for failure in fails:
                print("FAIL:", failure)
            return 1
        print("Jiraishin: full-screen trip, blockable, air whiff, CPU blocks "
              f"{blocks}/12")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
