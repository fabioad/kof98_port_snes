#!/usr/bin/env python3
"""Headless regression for Mature and Vice grab specials/supers.

The source CMD enters a root state whose HitDef redirects the attacker
(p1stateno) to a follow-up that owns the TargetBind/TargetLifeAdd rows.
Those follow-ups must live in the 103..114 grab window, and the shared
life-add byte must stay inside the signed 8-bit range.  This test feeds
the real motions and checks the attacker follow-up, the held victim and
a meaningful HP loss.

Run after a PVSnesLib build:

    python3 tools/test_mature_vice_grabs_headless.py
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
F_HP2 = B + 0x50
P1_X, P2_X, P2_STATE = B + 0, B + 0x40, B + 0x48

# libretro SNES button ids
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
Y, X, B_BTN, A_BTN, L, R = 1, 9, 0, 8, 10, 11

# Facing-right directions.  A diagonal is the set of both cardinal keys.
D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
DB = frozenset({DOWN, LEFT})
B = frozenset({LEFT})
VHELD = 76


def press_motion(core, steps, buttons, hold=2):
    last = set()
    for token in steps:
        dirs = set(token) if isinstance(
            token, (set, frozenset, tuple, list)) else {token}
        core.buttons[0] = dirs
        last = dirs
        core.step(hold)
    core.buttons[0] = last | set(buttons)
    core.step(hold)
    core.buttons[0] = set()


# character, label, expected attacker sids, motion, buttons, min damage
CASES = (
    ("mature", "Decide", {52, 103}, (B, D, F), {A_BTN}, 20),
    ("mature", "Heaven's Gates a", {85, 105, 106, 107},
     (D, DB, B, DB, D, DF, F), {B_BTN}, 40),
    ("mature", "Heaven's Gates b", {85, 105, 106, 107},
     (D, DB, B, DB, D, DF, F), {A_BTN}, 40),
    ("vice", "Deicide Slayer a", {48, 108}, (F, D, B), {B_BTN}, 20),
    ("vice", "Deicide Slayer b", {49, 108}, (F, D, B), {A_BTN}, 20),
    ("vice", "Black Out x", {52, 109}, (F, D, DF), {Y}, 20),
    ("vice", "Black Out y", {52, 109}, (F, D, DF), {X}, 20),
    ("vice", "Gore Fest x", {54, 110}, (F, D, B, F), {Y}, 25),
    ("vice", "Gore Fest y", {54, 110}, (F, D, B, F), {X}, 25),
    ("vice", "Negative Gain a", {88, 111}, (F, D, B, F, D, B), {B_BTN}, 30),
    ("vice", "Negative Gain b", {89, 112}, (F, D, B, F, D, B), {A_BTN}, 30),
)


def run_case(core_path, rom, case):
    name, label, want_sids, steps, buttons, min_dmg = case
    core = Core(core_path, rom)
    try:
        select = boot_select(core)
        enter_fight(core, select, name, "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, 82 << 8)
        core.put(P2_X, 100 << 8)
        core.put(F_HP2, 200)
        core.put(F_POWER, 3000)
        core.step(30)
        hp0 = core.word(F_HP2)
        press_motion(core, steps, buttons)
        seen1, seen2 = set(), set()
        for _ in range(320):
            core.step()
            seen1.add(core.ram[F_STATE])
            seen2.add(core.ram[P2_STATE])
        hp1 = core.word(F_HP2)
        assert seen1 & want_sids, (
            f"{name} {label}: attacker states {sorted(seen1)} did not "
            f"include {sorted(want_sids)}")
        assert VHELD in seen2, (
            f"{name} {label}: victim never entered the held pose "
            f"(states {sorted(seen2)})")
        assert hp0 - hp1 >= min_dmg, (
            f"{name} {label}: only {hp0 - hp1} damage ({hp0}->{hp1}), "
            f"wanted at least {min_dmg}")
        return hp0 - hp1
    finally:
        core.close()


def main():
    for case in CASES:
        dmg = run_case(CORE, ROOT / "kof98-snes.sfc", case)
        print(f"PASS {case[0]} {case[1]}: {dmg} damage, held + follow-up ok")
    print(f"PASS Mature/Vice grabs: {len(CASES)} commands")


if __name__ == "__main__":
    main()
