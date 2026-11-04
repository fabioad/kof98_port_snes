#!/usr/bin/env python3
"""Headless regression for the Category A commands (2026-11-04).

Covers the eleven fighters whose CMD entries did not reach a wired state in
the first audit, plus the two Kyo EX variants that share base Kyo's
Orochinagi.  Each case feeds the real motion and checks that the move (or
its p1 grab follow-up) is entered and removes a meaningful amount of the
victim's 200-point life bar.

Run after a PVSnesLib build:

    python3 tools/test_category_a_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
B = 0x4000
F_STATE, F_POWER = B + 8, B + 0x30
F_HP1, F_HP2 = B + 0x10, B + 0x50
P1_X, P2_X, P2_STATE = B + 0, B + 0x40, B + 0x48

# libretro SNES button ids
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
Y, X, B_BTN, A_BTN, L, R = 1, 9, 0, 8, 10, 11

# Facing-right directions: F = right, B = left.  The libretro pad reports
# one bit per physical button, so diagonals are sets, not OR-ed masks.
D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
DB = frozenset({DOWN, LEFT})
B = frozenset({LEFT})


def press_motion(core, steps, buttons, hold=2, extra_hold=()):
    last = set()
    for token in steps:
        if isinstance(token, (set, frozenset, tuple, list)):
            dirs = set(token)
        else:
            dirs = {token}
        core.buttons[0] = dirs
        last = dirs
        core.step(hold)
    # Keep the last direction on the button frame: L only becomes the c
    # token with a direction held, and R supplies y|b|z while held.
    core.buttons[0] = last | set(extra_hold) | set(buttons)
    core.step(hold)
    core.buttons[0] = set()


# name, state, expected sids, steps, buttons, min damage, p1 x, p2 x, jump
CASES = (
    ("joe", 3150, {87}, (D, DF, F, DF, D, DB, B), {Y, X}, 40, 82, 100, False),
    ("chin", 1920, {87}, (D, DF, F, D, DF, F), {R}, 30, 82, 100, False),
    ("mai", 2070, {87, 103}, (D, DF, F, D, DF, F), {R}, 20, 82, 100, False),
    ("yamazaki", 3150, {87, 104}, (F, DF, D, DB, B, F, DF, D, DB, B),
     {Y, X}, 25, 82, 100, False),
    ("yamazaki", 3000, {88}, (D, DF, F, D, DF, F), {Y}, 15, 82, 100, False),
    ("yamazaki", 3010, {89}, (D, DF, F, D, DF, F), {X}, 15, 82, 100, False),
    ("mary", 3060, {87, 104}, (D, DB, B, D, DB, B), {L}, 20, 50, 130, False),
    ("mary", 4000, {88, 111, 105}, (D, DF, F, D, DF, F), {B_BTN}, 20,
     82, 100, True),
    ("geese", 3250, {87, 103, 104}, (B, D, F), {A_BTN, B_BTN}, 15,
     82, 100, False),
    ("krauser", 3070, {88}, (D, DF, F), {Y, X}, 30, 82, 100, False),
    ("krauser", 3220, {87, 103, 104}, (F, DF, D, DB, B, F, DF, D, DB, B),
     {Y, X}, 20, 82, 100, False),
    ("ken", 3050, {87}, (D, DF, F, D, DF, F), {Y, X}, 15, 82, 100, False),
    ("chunli", 3300, {87}, (D, B, D, B), {L}, 15, 82, 100, False),
    ("kyo", 3000, {98, 60}, (D, DF, F), {A_BTN, B_BTN}, 30, 82, 100, False),
    ("kyonests", 3000, {98, 60}, (D, DF, F), {A_BTN, B_BTN}, 30,
     82, 100, False),
    ("kyoash", 3000, {98, 60}, (D, DF, F), {A_BTN, B_BTN}, 30,
     82, 100, False),
)


def run_case(core_path, rom, case):
    name, state, want_sids, steps, buttons, min_dmg, x1, x2, jump = case
    extra_hold = {UP} if name == "geese" else set()
    core = Core(core_path, rom)
    try:
        select = boot_select(core)
        enter_fight(core, select, name, "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, x1 << 8)
        core.put(P2_X, x2 << 8)
        core.put(F_HP1, 200)
        core.put(F_HP2, 200)
        core.put(F_POWER, 3000)
        core.step(30)
        if jump:
            core.buttons[0] = {UP}
            core.step(4)
            core.buttons[0] = set()
            core.step(6)
        hp0 = core.word(F_HP2)
        press_motion(core, steps, buttons, extra_hold=extra_hold)
        seen = set()
        for _ in range(800):
            core.step()
            seen.add(core.ram[F_STATE])
            if core.ram[F_STATE] == 0 and len(seen) > 1:
                # Keep a little room for the last TargetLifeAdd after the
                # attacker's state returns to 0.
                if core.word(F_HP2) < hp0:
                    break
        hp1 = core.word(F_HP2)
        assert seen & want_sids, (
            f"{name} {state}: states {sorted(seen)} did not include "
            f"{sorted(want_sids)}")
        assert hp0 - hp1 >= min_dmg, (
            f"{name} {state}: only {hp0 - hp1} damage ({hp0}->{hp1}), "
            f"wanted at least {min_dmg}")
        return hp0 - hp1
    finally:
        core.close()


def main():
    for case in CASES:
        dmg = run_case(CORE, ROOT / "kof98-snes.sfc", case)
        print(f"PASS {case[0]} {case[1]}: {dmg} damage, states ok")
    print(f"PASS Category A: {len(CASES)} commands")


if __name__ == "__main__":
    main()
