#!/usr/bin/env python3
"""Headless regression for the second Category D batch (05/11/2026).

Covers Takuma, Joe, Mai, Kim, King, Yuri, Mr. Big and Eiji.  Run after a
PVSnesLib build:

    python3 tools/test_category_d_batch2_headless.py
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
HCB2 = (F, DF, D, DB, BACK, F, DF, D, DB, BACK)

# (character, label, directions, buttons, expected sids, min damage)
CASES = (
    # Takuma
    ("takuma", "1400 Mouko Burai Gan", QCB, {X, Y}, {107}, 8),
    ("takuma", "1600 Koho", DP, {A, B_BTN}, {108}, 8),
    ("takuma", "1050 Ko'ou Ken ura", QCF, {X, Y}, {109}, 8),
    ("takuma", "1060 Ko'ou Ken ura S", QCF, {A, B_BTN}, {110}, 10),
    ("takuma", "1500 Haoh Shikou Ken", QCF2, {X, Y}, {111}, 10),
    ("takuma", "3100 Shin Kishin Geki", QCB2, {X, Y}, {113}, 15),
    ("takuma", "3300 Kyokugen Koho", QCF2, {A, B_BTN}, {114}, 15),
    # Joe
    ("joe", "3010 Screw Upper", QCB, {X, Y}, {107}, 10),
    ("joe", "3100 Bakuretsu", QCF2, {A, B_BTN}, {108}, 15),
    ("joe", "3200 Thunder Fire", QCF2, {X}, {110}, 10),
    ("joe", "3250 Thunder Fire MAX", QCF2, {X, Y}, {112}, 15),
    ("joe", "1310 Slash Kick S", QCF, {B_BTN}, {114}, 8),
    # Mai
    ("mai", "1038 Bachi", QCB2, {A, B_BTN}, {107}, 0),
    ("mai", "1050 Toki Tsubute", QCB2, {X, Y}, {108}, 8),
    ("mai", "1080 Hishou Ryuu'en Jin", QCF2, {A}, {109}, 10),
    ("mai", "1082 Hishou Ryuu'en Jin S", QCF2, {B_BTN}, {110}, 12),
    ("mai", "2030 MAX2", QCF2, {A, B_BTN}, {111}, 5),
    # Kim
    ("kim", "3000 Houou Kyaku", QCB2, {A}, {107}, 8),
    ("kim", "3020 Houou Kyaku MAX", QCB2, {A, B_BTN}, {108}, 10),
    ("kim", "3200 Houou Hiten", QCF2, {A}, {109}, 8),
    ("kim", "3210 Houou Hiten S", QCF2, {B_BTN}, {111}, 8),
    ("kim", "3220 Houou Hiten MAX", QCF2, {A, B_BTN}, {112}, 20),
    # King
    ("king", "1500 Mirage Dance", DP, {X, Y}, {107}, 8),
    ("king", "3200 MAX Illusion", QCF2, {X, Y}, {108}, 15),
    ("king", "3300 Silent Flash", QCF2, {X}, {109}, 12),
    ("king", "3400 Silent Flash S", QCF2, {Y}, {110}, 15),
    ("king", "3600 Surprise Rose", QCF2, {A}, {111}, 10),
    ("king", "3700 Surprise Rose S", QCF2, {B_BTN}, {112}, 12),
    ("king", "3800 Dragooner", QCB2, {X, Y}, {113}, 15),
    # Yuri
    ("yuri", "550 MAX Haoh", QCF2, {X, Y}, {107}, 10),
    ("yuri", "560 MAX Ryuuko", QCF2, {A, B_BTN}, {108}, 8),
    # Mr. Big
    ("mrbig", "1100 Crazy Drum", QCF, {A, B_BTN}, {107}, 8),
    ("mrbig", "1500 Drum Shot", QCB, {X, Y}, {109}, 8),
    ("mrbig", "3050 MAX Blaster Wave", QCF2, {X, Y}, {110}, 12),
    ("mrbig", "3100 Rising Spear", DP, {A, B_BTN}, {111}, 10),
    # Eiji
    ("eiji", "1000 Kikouhou", QCF2, {X, Y}, {107}, 8),
    ("eiji", "1600 Mukuro Nui", DP, {A, B_BTN}, {108}, 8),
    ("eiji", "3100 Zantetsu", QCB2, {X}, {109}, 8),
    ("eiji", "3120 MAX Zantetsu", QCB2, {X, Y}, {110}, 10),
    ("eiji", "3200 Yamikari", HCB2, {A, B_BTN}, {111}, 10),
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
    print(f"PASS Category D batch 2: {len(CASES)} moves")


if __name__ == "__main__":
    main()
