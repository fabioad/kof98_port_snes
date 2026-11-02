#!/usr/bin/env python3
"""Headless regression: Blue Mary's command grabs must step in and connect
at the arcade's normal range.

The Goodnight attempt had a single frame-0 grab box and a 12 px step after
it; 1900 (running face lock) had the same gap at the far edge of its dash.
Both now lunge before the grab window closes.

Run after a PVSnesLib build:

    python3 tools/test_mary_grab_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    enter_fight, tap, wait, GS, START, A, Y,
    DOWN, LEFT, RIGHT,
)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1_STATE, P1_X = 0x4008, 0x4000
P2_STATE, P2_HP = 0x4048, 0x4050
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


def press(core, direction, frames=2):
    core.buttons[0] = set(direction)
    core.step(frames)


def goodnight(core, button):
    for d in ((LEFT,), (DOWN, LEFT), (DOWN,), (DOWN, RIGHT), (RIGHT,)):
        press(core, d)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def face_lock(core, button):
    for d in ((RIGHT,), (DOWN, RIGHT), (DOWN,), (DOWN, LEFT),
              (LEFT,), (RIGHT,)):
        press(core, d)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def run(core, select, motion, button, p2x, wanted, min_damage):
    enter_fight(core, select, "mary", "kyo")
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.put(P1_X, 60 << 8)
    core.put(0x4040, p2x << 8)
    core.step(20)
    motion(core, button)

    seen, drops = [], []
    last = core.word(P2_HP)
    down = False
    max_x = core.word(P1_X) >> 8
    for _ in range(300):
        core.step()
        state = core.ram[P1_STATE]
        if not seen or seen[-1] != state:
            seen.append(state)
        hp = core.word(P2_HP)
        if hp < last:
            drops.append((state, last - hp))
            last = hp
        down |= core.ram[P2_STATE] == DOWN_STATE
        max_x = max(max_x, core.word(P1_X) >> 8)
    total = sum(d for _, d in drops)
    fails = []
    for state in wanted:
        if state not in seen:
            fails.append(f"state {state} never reached: {seen}")
    if total < min_damage:
        fails.append(f"only {total} damage: {drops}")
    if not down:
        fails.append("victim was not knocked down")
    if max_x < 75:
        fails.append(f"fighter only moved to x={max_x}")
    return fails, seen, total, max_x


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    fails = []
    try:
        select = boot_select(core)
        cases = [
            ("goodnight", goodnight, Y, 130, (109,), 100),
            ("face lock", face_lock, A, 130, (110, 98), 20),
        ]
        for label, motion, button, p2x, wanted, damage in cases:
            case_fails, seen, total, max_x = run(
                core, select, motion, button, p2x, wanted, damage)
            if case_fails:
                fails.extend(f"{label}: {f}" for f in case_fails)
            print(f"{label}: states={seen[:8]} total={total} x={max_x}")
        if fails:
            for failure in fails:
                print("FAIL:", failure)
            return 1
        print("Blue Mary: Goodnight and face lock step in and grab OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
