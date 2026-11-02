#!/usr/bin/env python3
"""Headless regression for Chin's drink command throw and its bottle.

The source 850 grab hands over to 860, which drains life eight times and
spawns the 861 bottle Explod at the mouth, then releases through 865/866.
The port used the generic blowback on the throw input, so neither the drink
hold nor the bottle appeared.

Run after a PVSnesLib build:

    python3 tools/test_chin_drink_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    enter_fight, tap, wait, GS, START, X, Y,
)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1_STATE, P1_X = 0x4008, 0x4000
P2_STATE, P2_HP = 0x4048, 0x4050
SPK_ANIM0 = 0x4204
DOWN_STATE = 10


def boot_select(core):
    wait(core, lambda: core.word(GS) == 14, "msu opening", 8000)
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


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        enter_fight(core, select, "chin", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, 60 << 8)
        core.put(0x4040, 80 << 8)
        core.step(20)
        core.buttons[0] = {X, Y}
        core.step(4)
        core.buttons[0] = set()
        core.step(2)

        seen, drops, victim_states = [], [], []
        bottle = False
        last = core.word(P2_HP)
        down = False
        for _ in range(360):
            core.step()
            state = core.ram[P1_STATE]
            if not seen or seen[-1] != state:
                seen.append(state)
            hp = core.word(P2_HP)
            if hp < last:
                drops.append((state, last - hp))
                last = hp
            vstate = core.ram[P2_STATE]
            if not victim_states or victim_states[-1] != vstate:
                victim_states.append(vstate)
            down |= vstate == DOWN_STATE
            bottle |= bool(core.word(SPK_ANIM0))
        total = sum(d for _, d in drops)
        fails = []
        for state in (75, 59, 61, 0):
            if state not in seen:
                fails.append(f"attacker state {state} never reached: {seen}")
        if victim_states and victim_states[0] != 76:
            fails.append(f"victim never entered held state: {victim_states}")
        if len(drops) < 6 or not all(d == 8 for _, d in drops):
            fails.append(f"expected eight 8-point sips, got {drops}")
        if total < 40:
            fails.append(f"only {total} damage")
        if not bottle:
            fails.append("bottle Explod never occupied a spark slot")
        if not down:
            fails.append("victim was not knocked down")
        if fails:
            for failure in fails:
                print("FAIL:", failure)
            return 1
        print(f"Chin drink: states={seen[:8]} sips={len(drops)} "
              f"damage={total} bottle={bottle} down={down}")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
