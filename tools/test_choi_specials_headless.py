#!/usr/bin/env python3
"""Focused headless regression for Choi's specials, supers and MAX moves.

Covers the four moves that were missing from the CmdTab (1210, 1610, 3110,
3250), the multi-hit supers (3000, 3100, 3110) and the grab supers
(2400, 3200, 3250).  Run after a PVSnesLib build:

    python3 tools/test_choi_specials_headless.py
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
DBDB = (D, BACK, D, BACK)
DFDF = (D, F, D, F)

# (character, label, directions, buttons, expected sids, min damage, grab)
CASES = (
    ("choi", "1000 Tatsumaki", QCB, {A}, {107}, 15, False),
    ("choi", "1010 Tatsumaki S", QCB, {B_BTN}, {108}, 15, False),
    ("choi", "1100 Senpuu", QCF, {A, B_BTN}, {109}, 10, False),
    ("choi", "1200 Hishou", QCF2, {A, B_BTN}, {110}, 10, False),
    ("choi", "1210 Hishou S", QCF2, {C}, {115}, 15, False),
    ("choi", "1300 Kaiten", QCB, {X}, {50}, 10, False),
    ("choi", "1310 Kaiten S", QCB, {Y}, {51}, 10, False),
    ("choi", "1500 Hien-sen", DP, {A}, {48}, 15, False),
    ("choi", "1510 Hien-sen S", DP, {B_BTN}, {49}, 15, False),
    ("choi", "1600 Shissou", HCB, {A}, {111}, 10, False),
    ("choi", "1610 Shissou S", HCB, {C}, {116}, 10, False),
    ("choi", "2400 Ultimate Storm", QCF2, {A}, {112, 64}, 20, True),
    ("choi", "3000 Shinkuu Tatsumaki", DBDB, {X}, {87}, 30, False),
    ("choi", "3100 En Getsu Rin", QCB2, {A}, {113}, 15, False),
    ("choi", "3110 En Getsu Rin S", QCB2, {C}, {117}, 15, False),
    ("choi", "3200 Houou Kyaku", QCB2, {A, B_BTN}, {114, 60}, 20, True),
    ("choi", "3250 Houou Kyaku MAX", QCB2, {Z}, {118, 62}, 20, True),
    # Air-only moves: the helper jumps before the command.
    ("choi", "1400 Hishou Kyaku", QCF, {A}, {52}, 10, False, True),
    ("choi", "1410 Hishou Kyaku S", QCF, {B_BTN}, {53}, 10, False, True),
    ("choi", "3050 Toppa L", DFDF, {X}, {85}, 20, False, True),
    ("choi", "3060 Toppa S", DFDF, {Y}, {86}, 20, False, True),
    ("choi", "3500 Shakushi MAX2", QCF2, {X}, {88}, 40, False, True),
)


def feed(core, steps, buttons, hold=None):
    if hold is None:
        hold = 2 if len(steps) >= 8 else 3
    for token in steps:
        core.buttons[0] = set(token)
        core.step(hold)
    core.buttons[0] = set(buttons)
    core.step(hold)
    core.buttons[0] = set()


def run_case(rom, case):
    char, label, steps, buttons, want, min_dmg, grab = case[:7]
    air = len(case) > 7 and case[7]
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
        core.put(F_POWER, 9000)
        core.step(60)
        if air:
            core.buttons[0] = {4}          # UP: leave the ground
            core.step(6)
            core.buttons[0] = set()
            core.put(B + 2, 72 << 8)
            core.put(B + 6, (-6 * 256) & 0xFFFF)
        hp0 = core.word(F_HP2)
        feed(core, steps, buttons, hold=2 if air else None)
        seen = set()
        victim = set()
        max_damage = 0
        for _ in range(1600):
            core.step()
            st = core.ram[F_STATE]
            seen.add(st)
            victim.add(core.ram[B + 0x40 + 8])
            max_damage = max(max_damage, hp0 - core.word(F_HP2))
            if st == 0 and len(seen) > 1:
                break
        assert seen & want, f"{char} {label}: states {sorted(seen)}"
        assert max_damage >= min_dmg, (
            f"{char} {label}: only {max_damage} damage")
        if grab:
            assert 76 in victim, (
                f"{char} {label}: victim never entered S_VHELD ({sorted(victim)})")
        return max_damage
    finally:
        core.close()


def main():
    rom = ROOT / "kof98-snes.sfc"
    for case in CASES:
        damage = run_case(rom, case)
        tag = " grab" if case[6] else ""
        print(f"PASS {case[0]:5s} {case[1]:28s} {damage:3d} damage{tag}",
              flush=True)
    print(f"PASS Choi specials: {len(CASES)} moves")


if __name__ == "__main__":
    main()
