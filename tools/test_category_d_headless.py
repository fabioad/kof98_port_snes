#!/usr/bin/env python3
"""Headless regression for the first Category D pass.

Covers the command grabs that were not entering their p1 follow-ups, the
under-damaged 108-Shiki, and the stationary Terry/Athena supers whose
helpers have no native body:

  * Kyo / Nests / Ash 3500 and 3550 (Chou Hissatsu Waza / MAX Mushiki)
  * Kyo 3305 (108-Shiki '99)
  * Terry 3000/3010/3050 (Power Geyser / Buster Wolf)
  * Athena 4000 (the working Phoenix Fang super)

Run after a PVSnesLib build:

    python3 tools/test_category_d_headless.py
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
F_HP1, F_HP2 = B + 0x10, B + 0x50
P1_X, P2_X = B + 0, B + 0x40

UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
WEAK, STRONG = 1, 9   # MUGEN x -> Y, MUGEN y -> X

D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
DB = frozenset({DOWN, LEFT})
BACK = frozenset({LEFT})
HCB2 = (F, DF, D, DB, BACK, F, DF, D, DB, BACK)
QCF2 = (D, DF, F, D, DF, F)


def feed(core, steps, buttons, hold=2, charge=None):
    """charge=(dir, ticks) holds a direction before the motion (DBF)."""
    if charge:
        core.buttons[0] = set(charge[0])
        core.step(charge[1])
    last = set()
    for token in steps:
        core.buttons[0] = set(token)
        last = set(token)
        core.step(hold)
    core.buttons[0] = set(buttons)
    core.step(hold)
    core.buttons[0] = set()


# name, steps, buttons, hold, charge, min damage, expected sids
CASES = (
    ("kyo 3500", HCB2, {WEAK}, 3, None, 30, {89, 65}),
    ("kyo 3550", HCB2, {WEAK, STRONG}, 3, None, 30, {87, 103}),
    ("kyo 3305", QCF2, {WEAK, STRONG}, 2, None, 15, {88}),
    ("kyonests 3500", HCB2, {WEAK}, 3, None, 30, {89, 65}),
    ("kyoash 3550", HCB2, {WEAK, STRONG}, 3, None, 30, {87, 103}),
    ("terry 3000", (BACK, F), {WEAK}, 2, (D, 20), 20, {85}),
    ("terry 3010", (BACK, F), {STRONG}, 2, (D, 20), 25, {86}),
    ("terry 3050", (BACK, F), {WEAK, STRONG}, 2, (D, 20), 15, {87}),
    ("athena 4000", (F, D, BACK, F, D, BACK), {STRONG}, 2, None, 50, {88}),
)


def run_case(rom, case):
    name, steps, buttons, hold, charge, min_dmg, want = case
    char = name.split()[0]
    core = Core(CORE, rom)
    try:
        select = boot_select(core)
        enter_fight(core, select, char, "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, 82 << 8)
        core.put(P2_X, 100 << 8)
        core.put(F_HP1, 200)
        core.put(F_HP2, 200)
        core.put(B + 0x30, 3000)
        core.step(30)
        hp0 = core.word(F_HP2)
        feed(core, steps, buttons, hold, charge)
        seen = set()
        for _ in range(900):
            core.step()
            seen.add(core.ram[F_STATE])
            if core.ram[F_STATE] == 0 and len(seen) > 1:
                if core.word(F_HP2) < hp0:
                    break
        hp1 = core.word(F_HP2)
        assert seen & want, f"{name}: states {sorted(seen)}"
        assert hp0 - hp1 >= min_dmg, (
            f"{name}: only {hp0 - hp1} damage ({hp0}->{hp1})")
        return hp0 - hp1
    finally:
        core.close()


def main():
    for case in CASES:
        dmg = run_case(ROOT / "kof98-snes.sfc", case)
        print(f"PASS Category D {case[0]}: {dmg} damage, states ok")
    print(f"PASS Category D: {len(CASES)} moves")


if __name__ == "__main__":
    main()
