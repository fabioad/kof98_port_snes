#!/usr/bin/env python3
"""Headless regression for Billy's Kyoushuu Hishou Kon, Senpuu Kon and
Sansetsu Kon Chuudan Uchi.

Each move must play its full source chain: the vault rises, drops for three
extra contacts and lands; the spinning staff registers its multi-hit; the
three-part staff follows its first contact with the Fire Cane finish and
knocks down.

Run after a PVSnesLib build:

    python3 tools/test_billy_moves_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    enter_fight, tap, wait, GS, START, A, B, X, Y,
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


def dp(core, button):
    for d in ((RIGHT,), (DOWN,), (DOWN, RIGHT)):
        press(core, d)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def wheel(core, button):
    press(core, (DOWN,), 3)
    core.buttons[0] = set()
    core.step(2)
    press(core, (DOWN,), 3)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def qcf(core, button):
    for d in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
        press(core, d)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def run(core, select, motion, button, rush_states, min_drops, want_down):
    enter_fight(core, select, "billy", "kyo")
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.put(P1_X, 60 << 8)
    core.put(0x4040, 120 << 8)
    core.step(20)
    motion(core, button)

    seen, drops = [], []
    last = core.word(P2_HP)
    down = False
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

    rush_hits = [d for s, d in drops if s in rush_states]
    total = sum(d for _, d in drops)
    fails = []
    for state in rush_states:
        if state not in seen:
            fails.append(f"state {state} never reached: {seen}")
    if len(rush_hits) < min_drops:
        fails.append(f"only {len(rush_hits)} contacts: {drops}")
    if down != want_down:
        fails.append(f"knockdown {down}, wanted {want_down}")
    if not 20 <= total <= 70:
        fails.append(f"total damage {total} outside 20..70")
    return fails, seen, drops, total


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    fails = []
    try:
        select = boot_select(core)
        cases = [
            # (label, motion, SNES button, required states, contacts, down)
            ("kyoushuu", dp, B, (52, 61, 63, 65), 3, True),
            ("senpuu", wheel, Y, (54,), 8, False),
            ("sansetsu", qcf, Y, (56, 60), 2, True),
        ]
        for label, motion, button, states, hits, down in cases:
            case_fails, seen, drops, total = run(
                core, select, motion, button, states, hits, down)
            if case_fails:
                fails.extend(f"{label}: {f}" for f in case_fails)
            print(f"{label}: states={seen[:8]} drops={drops} total={total}")
        if fails:
            for failure in fails:
                print("FAIL:", failure)
            return 1
        print("Billy: Kyoushuu Hishou Kon, Senpuu Kon and Sansetsu "
              "Chuudan Uchi OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
