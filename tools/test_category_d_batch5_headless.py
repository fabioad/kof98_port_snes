#!/usr/bin/env python3
"""Headless regression for the last Category D batch (05/11/2026).

Covers Yamazaki, Blue Mary, Geese, Krauser, Ken, Chun-Li, Sakura,
Heavy D, Brian, Billy and Lucky.  Run after a PVSnesLib build:

    python3 tools/test_category_d_batch5_headless.py
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

# (character, label, directions, buttons, expected sids)
CASES = (
    ("yamazaki", "1400 Bakudan Pachiki", QCF, {A}, {107}),
    ("yamazaki", "1600 Todome", QCB2, {A}, {108}),
    ("yamazaki", "3020 MAX Guillotine", HCB, {A}, {110}),
    ("mary", "1600 Straight Slicer", QCF, {X}, {112}),
    ("mary", "3000 Super Dunk", DP, {X}, {114}),
    ("mary", "3100 Dynamite Swing", QCB2, {X}, {62}),
    ("mary", "3300 Splash Rose", HCB, {X}, {64}),
    ("mary", "3800 Typhoon", QCB, {X}, {68}),
    ("mary", "50000 Infinity Rose", QCB, {Y}, {68}),
    ("geese", "1500 Raimei Gouha Nage", QCB, {A}, {107}),
    ("geese", "1600 Shinkuu Nage", HCB2, {A}, {108}),
    ("krauser", "1600 Phoenix Throw", DP, {X}, {107}),
    ("krauser", "1700 Kaiser Claw", QCB2, {A}, {108}),
    ("krauser", "3100 Kaiser Inferno", HCB, {A}, {109}),
    ("krauser", "3150 MAX Kaiser Inferno", HCB, {B_BTN}, {110}),
    ("krauser", "3300 Unlimited Desire", QCF2, {A}, {111}),
    ("krauser", "3310 Unlimited Desire S", QCF2, {B_BTN}, {112}),
    ("krauser", "3320 MAX Unlimited Desire", QCF2, {A, B_BTN}, {113}),
    ("ken", "1250 Tatsumaki aereo", DP, {A}, {107}),
    ("ken", "1320 Oosoto Mawashi", QCB, {X}, {108}),
    ("ken", "3100 Shippuu Jinrai", HCB, {A}, {109}),
    ("ken", "3200 Shinryuuken", QCB2, {A}, {111}),
    ("chunli", "1050 Kikouken", QCF, {Y}, {107}),
    ("chunli", "1250 Spinning Bird aereo", DP, {X}, {108}),
    ("chunli", "3000 Kikou Shou", QCB2, {A}, {109}),
    ("chunli", "3100 Houyoku Sen", HCB, {A}, {110}),
    ("chunli", "3200 Hazan Tenshou", QCF2, {A}, {111}),
    ("sakura", "1400 Ouka Kyaku", QCB, {X}, {54}),
    ("sakura", "3150 Haru Ichiban", HCB, {A}, {108}),
    ("sakura", "3200 Midare Zakura", QCB2, {A}, {109}),
    ("sakura", "3250 MAX Midare Zakura", QCB2, {B_BTN}, {110}),
    ("sakura", "3300 Shun Goku Satsu", QCF, {A}, {114}),
    ("heavyd", "2200 D. Shadow", HCB, {A}, {107}),
    ("brian", "3300 American Supernova", QCB, {A}, {107}),
    ("brian", "3400 Galaxy Cyclone", HCB, {A}, {108}),
    ("brian", "3500 Big Bang Tackle", QCB2, {A}, {109}),
    ("brian", "3600 American Final Tackle", QCB2, {B_BTN}, {110}),
    ("billy", "1860 Flaming Stick Spin", QCF, {A}, {107}),
    ("billy", "2510 Super Stick Swing S", QCB2, {A}, {108}),
    ("billy", "2600 Chou HongRenSalgon S", HCB, {A}, {109}),
    ("billy", "6000 MAX2", QCF2, {A}, {110}),
    ("lucky", "2200 Shoot 2", QCB, {X}, {107}),
    ("lucky", "2300 Shoot 3", QCB, {Y}, {107}),
    ("lucky", "2400 Shoot 4", QCB, {X, Y}, {107}),
    ("lucky", "2500 Finger Roll", HCB, {A}, {108}),
    ("lucky", "2700 Slam", QCB2, {A}, {109}),
    ("lucky", "4700 Air Slam", QCB2, {B_BTN}, {110}),
    ("lucky", "3100 Finger Roll SDM", DP, {X, Y}, {111}),
    ("lucky", "3400 Shoot Out", QCF, {A, B_BTN}, {112}),
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
    char, label, steps, buttons, want = case
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
        for _ in range(1200):
            core.step()
            st = core.ram[F_STATE]
            seen.add(st)
            max_damage = max(max_damage, hp0 - core.word(F_HP2))
            if st == 0 and len(seen) > 1:
                break
        assert seen & want, f"{char} {label}: states {sorted(seen)}"
        return max_damage
    finally:
        core.close()


def main():
    rom = ROOT / "kof98-snes.sfc"
    for case in CASES:
        damage = run_case(rom, case)
        print(f"PASS {case[0]:8s} {case[1]:28s} {damage} damage", flush=True)
    print(f"PASS Category D batch 5: {len(CASES)} moves")


if __name__ == "__main__":
    main()
