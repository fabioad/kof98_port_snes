#!/usr/bin/env python3
"""Headless regression for Eiji's specials outside slots 107-111.

Category D batch 2 only covers the five reactivated slots (Kikouhou,
Mukuro Nui, Zantetsu Tourouken, MAX Zantetsu and Yamikari).  The slots the
character has had since v1.1.5 (Kotsu Hazaki, Ryuuei-jin, Tenmakyaku,
Kageutsushi, Kasumi-giri and the three Zantetsuha supers) had no headless
coverage, so a missing transition or a broken ProjTab row could ship
silently.  See docs/AUDITORIA_EIJI_2026-11-15.md.

    python3 tools/test_eiji_specials_headless.py [rom.sfc]
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
RDP = (BACK, D, DB)
HCB = (F, DF, D, DB, BACK)
QCF2RDP = (D, DF, F, DF, D, DB, BACK)   # Zantetsuha: QCF then reverse DP

# (character, label, directions, buttons, expected sids, min damage)
CASES = (
    ("eiji", "1300 Kotsu Hazaki W", HCB, {A}, {48}, 20),
    ("eiji", "1310 Kotsu Hazaki S", HCB, {B_BTN}, {49}, 20),
    ("eiji", "1200 Ryuuei-jin W", DP, {X}, {50}, 15),
    ("eiji", "1210 Ryuuei-jin S", DP, {Y}, {51}, 15),
    ("eiji", "1400 Tenmakyaku W", RDP, {A}, {52}, 10),
    ("eiji", "1410 Tenmakyaku S", RDP, {B_BTN}, {53}, 10),
    ("eiji", "1500 Kageutsushi W", QCF, {A}, {54}, 0),
    ("eiji", "1510 Kageutsushi S", QCF, {B_BTN}, {55}, 0),
    ("eiji", "1100 Kasumi-giri W", QCB, {X}, {56}, 20),
    ("eiji", "1110 Kasumi-giri S", QCB, {Y}, {57}, 20),
    ("eiji", "3000 Zantetsuha W", QCF2RDP, {X}, {85}, 40),
    ("eiji", "3010 Zantetsuha S", QCF2RDP, {Y}, {86}, 40),
    ("eiji", "3020 MAX Zantetsuha", QCF2RDP, {X, Y}, {87}, 40),
)


def feed(core, steps, buttons):
    # The synthetic table gives every motion an 18-frame window, so long
    # motions (7 tokens) need two ticks per token to land in time.
    hold = 2
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
    rom = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "kof98-snes.sfc"
    for case in CASES:
        damage = run_case(rom, case)
        print(f"PASS {case[0]:6s} {case[1]:26s} {damage:>3} damage", flush=True)
    print(f"PASS Eiji specials: {len(CASES)} moves")


if __name__ == "__main__":
    main()
