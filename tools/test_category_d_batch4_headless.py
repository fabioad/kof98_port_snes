#!/usr/bin/env python3
"""Headless regression for the fifth Category D batch (05/11/2026).

Covers Yashiro, Shermie and Chris.  Run after a PVSnesLib build:

    python3 tools/test_category_d_batch4_headless.py
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
    # Yashiro
    ("yashiro", "2200 Odoru Daichi", QCF, {A}, {107}, 8),
    ("yashiro", "2210 Odoru Daichi S", QCF, {B_BTN}, {107}, 8),
    ("yashiro", "2300 Kujiku Daichi", QCB, {A}, {108}, 8),
    ("yashiro", "2310 Kujiku Daichi S", QCB, {B_BTN}, {108}, 8),
    ("yashiro", "3020 MAX Million Bash", QCF2, {X, Y}, {109}, 15),
    ("yashiro", "3100 Final Impact", QCB2, {B_BTN}, {110}, 15),
    ("yashiro", "3600 Araburu Daichi", HCB, {A}, {111}, 10),
    ("yashiro", "3700 Ankoku Jigoku", HCB2, {A}, {112}, 15),
    # Shermie
    ("shermie", "1000 Axle Spin Kick", QCF, {X}, {107}, 8),
    ("shermie", "1050 Axle Spin Kick S", QCF, {Y}, {107}, 8),
    ("shermie", "1100 Shermie Shoot", QCB2, {A}, {107}, 8),
    ("shermie", "1200 Shermie Whip", QCB, {X}, {108}, 10),
    ("shermie", "1300 Shermie Spiral", DP, {X}, {109}, 10),
    ("shermie", "2100 Shermie Carnival", QCF2, {X}, {110}, 15),
    ("shermie", "7100 Shajitsu no Odori", HCB, {X}, {111}, 10),
    ("shermie", "7225 Mugetsu no Raiun", HCB2, {X}, {112}, 15),
    ("shermie", "8000 Shukumei", QCB, {X, Y}, {113}, 20),
    ("shermie", "8100 Ankoku Raikouken", QCF2, {X, Y}, {114}, 10),
    # Chris
    ("chris", "1300 Slide Touch", QCF, {X}, {107}, 10),
    ("chris", "1350 Slide Touch S", QCF, {Y}, {107}, 10),
    ("chris", "1500 Direction Change", QCB, {A}, {108}, 8),
    ("chris", "1600 Shooting Dancer", DP, {X}, {109}, 8),
    ("chris", "2100 Twister Drive", QCF2, {A, B_BTN}, {110}, 8),
    ("chris", "7000 Taiyou o Iru Honoo", QCF2, {X, Y}, {111}, 10),
    ("chris", "7200 Tsuki o Tsumu Honoo", QCB2, {A}, {112}, 12),
    ("chris", "7300 Shishi o Kamu Honoo", HCB2, {A}, {113}, 15),
    ("chris", "8000 Daichi o Harau Gouka", QCB, {X, Y}, {114}, 20),
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
        core.put(F_POWER, 4000)
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
        print(f"PASS {case[0]:8s} {case[1]:28s} {damage} damage", flush=True)
    print(f"PASS Category D batch 4: {len(CASES)} moves")


if __name__ == "__main__":
    main()
