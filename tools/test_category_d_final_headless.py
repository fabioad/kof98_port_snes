#!/usr/bin/env python3
"""Headless regression for the last two Category D items.

Kyo/Nests/Ash Orochinagi strong (3010) and Omega Rugal in the select
harness (hidden L+R on the Rugal cell).  Run after a PVSnesLib build:

    python3 tools/test_category_d_final_headless.py
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
R = 11

D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
DB = frozenset({DOWN, LEFT})
BACK = frozenset({LEFT})
QCF = (D, DF, F)
QCB = (D, DB, BACK)
HCB = (F, DF, D, DB, BACK)

# (character, label, directions, buttons, expected sid, min damage)
CASES = (
    ("kyo", "3010 Orochinagi S", HCB, {A, B_BTN}, 104, 10),
    ("kyonests", "3010 Orochinagi S", HCB, {A, B_BTN}, 104, 10),
    ("kyoash", "3010 Orochinagi S", HCB, {A, B_BTN}, 104, 10),
    ("omegarugal", "7100 Gravity Shot", QCF, {R}, 82, 10),
    ("omegarugal", "8000 RE", QCB, {R}, 107, 10),
    ("omegarugal", "1050 Gravity Smash", QCF, {X}, 107, 10),
    ("omegarugal", "1055 Gravity Smash S", QCF, {Y}, 108, 10),
    ("omegarugal", "2310 RE2", QCB, {X}, 109, 10),
    ("omegarugal", "1010 Dark dash", (F, D, DF), {A}, 110, 0),
    ("omegarugal", "1011 Dark dash B", (F, D, DF), {B_BTN}, 111, 0),
    ("clark", "Frankensteiner", (F, D, DF), {A}, 56, 20),
    ("sakura", "3010 Shou'ou Ken S", (D, DF, F, D, DF, F), {Y}, 86, 20),
)


def feed(core, steps, buttons):
    for token in steps:
        core.buttons[0] = set(token)
        core.step(3)
    core.buttons[0] = set(buttons)
    core.step(3)
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
        core.put(F_POWER, 4000)
        core.step(30)
        hp0 = core.word(F_HP2)
        feed(core, steps, buttons)
        seen = []
        max_damage = 0
        for _ in range(1500):
            core.step()
            st = core.ram[F_STATE]
            if not seen or seen[-1] != st:
                seen.append(st)
            max_damage = max(max_damage, hp0 - core.word(F_HP2))
            if st == 0 and len(seen) > 2:
                break
        assert want in seen, f"{char} {label}: states {seen[:12]}"
        assert max_damage >= min_dmg, (
            f"{char} {label}: only {max_damage} damage")
        return max_damage
    finally:
        core.close()


def main():
    rom = ROOT / "kof98-snes.sfc"
    for case in CASES:
        damage = run_case(rom, case)
        print(f"PASS {case[0]:10s} {case[1]:22s} {damage} damage", flush=True)
    print(f"PASS Category D final: {len(CASES)} moves")


if __name__ == "__main__":
    main()
