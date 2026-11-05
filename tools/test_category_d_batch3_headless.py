#!/usr/bin/env python3
"""Headless regression for the fourth Category D batch (05/11/2026).

Covers Kensou, Chin, Chang and Choi.  Run after a PVSnesLib build:

    python3 tools/test_category_d_batch3_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
B = 0x4000
F_STATE = B + 8
F_HP2 = B + 0x50
F_POWER = B + 0x30

DOWN, LEFT, RIGHT = 5, 6, 7
X, Y, A, B_BTN, C, Z = 1, 9, 0, 8, 10, 11

D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
DB = frozenset({DOWN, LEFT})
BACK = frozenset({LEFT})
QCF = (D, DF, F)
QCB = (D, DB, BACK)
DP = (F, D, DF)
QCF2 = (D, DF, F, D, DF, F)
QCB2 = (D, DB, BACK, D, DB, BACK)
HCB = (F, DF, D, DB, BACK)
HCB2 = (F, DF, D, DB, BACK, F, DF, D, DB, BACK)

# (character, label, directions, buttons, expected sids, min damage)
CASES = (
    # Kensou
    ("kensou", "1300 Sen Shippo", QCB, {A}, {107}, 8),
    ("kensou", "1330 Sen Shippo S", QCB, {B_BTN}, {108}, 8),
    ("kensou", "2000 Niku Man", QCF2, {A}, {109}, 0),
    ("kensou", "2100 Sen Ki Hakkei", QCB2, {A}, {110}, 15),
    ("kensou", "2200 Chouryuu Renken", HCB2, {A}, {111}, 10),
    # Chin
    ("chin", "1203 Fire Zake", HCB, {A}, {107}, 10),
    ("chin", "1300 Fire Zake S", HCB, {B_BTN}, {108}, 10),
    ("chin", "1400 Upper strong", DP, {A}, {109}, 8),
    ("chin", "1750 Super Long Walk", QCF2, {A}, {110}, 15),
    ("chin", "2200 Hyper Long Walk", HCB2, {A}, {111}, 20),
    # Chang
    ("chang", "1400 Haki Kyaku", QCF, {A}, {107}, 10),
    ("chang", "3400 Tekkyuu L2", QCB, {X, Y}, {108}, 20),
    # Choi
    ("choi", "1000 Tatsumaki", QCB, {A}, {107}, 15),
    ("choi", "1010 Tatsumaki S", QCB, {B_BTN}, {108}, 15),
    ("choi", "1100 Senpuu", QCF, {A, B_BTN}, {109}, 10),
    ("choi", "1200 Hishou", QCF2, {A, B_BTN}, {110}, 10),
    ("choi", "1600 Shissou", HCB, {A}, {111}, 10),
    ("choi", "2400 Ultimate Storm", QCF2, {A}, {112}, 15),
    ("choi", "3100 Zan En Getsu Rin", QCB2, {A}, {113}, 15),
    ("choi", "3200 Houou Kyaku", QCB2, {A, B_BTN}, {114}, 15),
)


def feed(core, steps, buttons):
    hold = 2 if len(steps) >= 8 else 3
    for token in steps:
        core.buttons[0] = set(token)
        core.step(hold)
    core.buttons[0] = set(buttons)
    core.step(hold)
    core.buttons[0] = set()


def run_case(rom, case):
    char, label, steps, buttons, want, min_dmg = case
    core = Core(CORE, rom)
    try:
        select = boot_select(core)
        enter_fight(core, select, char, "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(B, 82 << 8)
        core.put(B + 0x40, 100 << 8)
        core.put(B + 0x10, 200)
        core.put(F_HP2, 200)
        core.put(F_POWER, 3000)
        core.step(30)
        hp0 = core.word(F_HP2)
        feed(core, steps, buttons)
        seen = set()
        max_damage = 0
        for _ in range(1500):
            core.step()
            st = core.ram[F_STATE]
            seen.add(st)
            max_damage = max(max_damage, hp0 - core.word(F_HP2))
            if st == 0 and len(seen) > 1:
                break
        assert seen & want, f"{char} {label}: states {sorted(seen)}"
        assert max_damage >= min_dmg, (
            f"{char} {label}: only {max_damage} damage")
        return max_damage
    finally:
        core.close()


def main():
    rom = ROOT / "kof98-snes.sfc"
    for case in CASES:
        damage = run_case(rom, case)
        print(f"PASS {case[0]:7s} {case[1]:28s} {damage} damage", flush=True)
    print(f"PASS Category D batch 3: {len(CASES)} moves")


if __name__ == "__main__":
    main()
