#!/usr/bin/env python3
"""Headless regression for the rest of Category D (04/11/2026).

Covers the Terry specials/supers that were still follow-up-only, the
Kyokugen trio's missing EX/Renbu variants, Rugal's Beads Destruction and
Iori's Ya Sakazuki.  Buster Wolf is checked for its three sequential
contacts (two rush hits + the 3205 finisher).

Run after a PVSnesLib build:

    python3 tools/test_category_d_remaining_headless.py
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
# libretro SNES ids: Y=1 (MUGEN x), X=9 (y), B=0 (a), A=8 (b), L=10 (c),
# R=11 (z).
X, Y, A, B_BTN, C, Z = 1, 9, 0, 8, 10, 11

D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
DB = frozenset({DOWN, LEFT})
BACK = frozenset({LEFT})
QCF = (D, DF, F)
QCB = (D, DB, BACK)
DP = (F, D, DF)
HCB = (F, DF, D, DB, BACK)
QCF2 = (D, DF, F, D, DF, F)

# (character, label, direction sequence, buttons, expected runtime sids,
#  minimum damage, exact contact count or None)
CASES = (
    # Terry
    ("terry", "1050 Power Wave EX", QCB, {X, Y}, {60}, 10, None),
    ("terry", "1450 Power Dunk MOW", DP, {A, B_BTN}, {61}, 8, None),
    ("terry", "1550 Power Charge MOW W", HCB, {A, B_BTN}, {64}, 20, None),
    ("terry", "1560 Power Charge MOW S", HCB, {X, Y}, {65}, 20, None),
    ("terry", "1600 Fire Kick", QCF, {A, B_BTN}, {62}, 10, None),
    ("terry", "1700 Double Kong", DP, {X, Y}, {63}, 10, None),
    ("terry", "3100 High Angle Geyser", QCF2, {A}, {105}, 20, None),
    ("terry", "3200 Buster Wolf", QCF2, {X}, {88}, 20, 3),
    ("terry", "3250 Buster Wolf MAX", QCF2, {X, Y}, {89}, 30, 3),
    ("terry", "3050 MAX Power Geyser", (BACK, F), {X, Y}, {87}, 30, None),
    # Andy
    ("andy", "1400 Gekiheki Haisui", QCF, {X}, {60}, 8, None),
    ("andy", "1450 Gekiheki Haisui Ura", QCF, {Z}, {61}, 5, None),
    ("andy", "1500 Genei Shiranui", DP, {X}, {62}, 8, None),
    ("andy", "1160 Hishou Ken EX", QCB, {Z}, {63}, 8, None),
    ("andy", "3000 Chou Reppa Dan", QCF2, {A}, {64}, 20, None),
    ("andy", "3010 Chou Reppa Dan S", QCF2, {B_BTN}, {65}, 25, None),
    ("andy", "3050 Chou Reppa Dan MAX", QCF2, {A, B_BTN}, {66}, 30, None),
    # Ryo
    ("ryo", "1150 Koho EX", QCF, {Z}, {55}, 15, None),
    ("ryo", "1160 Koho EX S", QCB, {Z}, {56}, 20, None),
    ("ryo", "1250 Hien Shippuu 95", DP, {A}, {62}, 8, None),
    ("ryo", "1260 Hien Shippuu 95 S", DP, {B_BTN}, {63}, 15, None),
    ("ryo", "2100 Ko'ou Geki", QCB, {X, Y}, {64}, 8, None),
    ("ryo", "3250 Tenchi Haoh MAX", QCF2, {A}, {103}, 20, None),
    # Robert
    ("robert", "1050 Ryuugeki Ken EX", QCF, {Z}, {60}, 8, None),
    ("robert", "3200 Muei Shippuu", QCF2, {A}, {62}, 12, None),
    ("robert", "3210 Muei Shippuu S", QCF2, {B_BTN}, {63}, 20, None),
    ("robert", "3220 Muei Shippuu MAX", QCF2, {A, B_BTN}, {64}, 25, None),
    ("robert", "3270 Muei Senpuu MAX",
     (D, DB, BACK, DB, D, DF, F), {A, B_BTN}, {65}, 25, None),
    # Rugal
    ("rugal", "1800 Beads Destruction", HCB, {X, Y}, {66}, 8, None),
    # Iori
    ("iori", "3100 Ya Sakazuki", QCB, {Z}, {106}, 4, None),
    ("iori", "3110 Ya Sakazuki S", QCB, {X, Y}, {107}, 5, None),
    ("iori", "3150 Ya Sakazuki MAX", QCF2, {Z}, {108}, 8, None),
)


def feed(core, steps, buttons, charge=None):
    if charge:
        core.buttons[0] = set(charge[0])
        core.step(charge[1])
    for token in steps:
        core.buttons[0] = set(token)
        core.step(2)
    core.buttons[0] = set(buttons)
    core.step(2)
    core.buttons[0] = set()


def run_case(rom, case):
    char, label, steps, buttons, want, min_dmg, contacts = case
    charge = (D, 20) if label.startswith("3050 MAX Power") else None
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
        feed(core, steps, buttons, charge)
        seen = set()
        hpseq = [hp0]
        for _ in range(1200):
            core.step()
            st = core.ram[F_STATE]
            seen.add(st)
            hp = core.word(F_HP2)
            if hp != hpseq[-1]:
                hpseq.append(hp)
            if st == 0 and len(seen) > 1:
                break
        damage = hp0 - core.word(F_HP2)
        assert seen & want, f"{char} {label}: states {sorted(seen)}"
        assert damage >= min_dmg, (
            f"{char} {label}: only {damage} damage ({hp0}->{core.word(F_HP2)})")
        if contacts is not None:
            assert len(hpseq) - 1 == contacts, (
                f"{char} {label}: {len(hpseq) - 1} contacts, expected {contacts}")
        return damage
    finally:
        core.close()


def main():
    rom = ROOT / "kof98-snes.sfc"
    for case in CASES:
        last = None
        for _attempt in range(2):
            try:
                dmg = run_case(rom, case)
                print(f"PASS {case[0]:7s} {case[1]:28s} {dmg} damage",
                      flush=True)
                break
            except AssertionError as exc:
                last = exc
        else:
            raise last
    print(f"PASS Category D remaining: {len(CASES)} moves")


if __name__ == "__main__":
    main()
