#!/usr/bin/env python3
"""Headless regression for Chizuru's clone specials and supers.

The source specials are clone/Helper attacks.  The port keeps the main body
as the attacker and uses the source HitDef/damage rows, so each command must
reach its wired state and connect.  The HCB pair used to lose to QCB because
both shortened to four matcher elements; this test guards that priority.

Run after a PVSnesLib build:

    python3 tools/test_chizuru_clones_headless.py
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
QCF = (D, DF, F)
QCB = (D, DB, BACK)
HCB = (F, DF, D, DB, BACK)


def feed(core, steps, buttons, hold=2):
    last = set()
    for token in steps:
        core.buttons[0] = set(token)
        last = set(token)
        core.step(hold)
    core.buttons[0] = last | set(buttons)
    core.step(hold)
    core.buttons[0] = set()


# label, steps, buttons, min damage, expected sids
CASES = (
    ("QCF weak", QCF, {WEAK}, 20, {48}),
    ("QCF strong", QCF, {STRONG}, 20, {49}),
    ("QCB weak", QCB, {WEAK}, 12, {50}),
    ("QCB strong", QCB, {STRONG}, 12, {51}),
    ("HCB weak", HCB, {WEAK}, 12, {54}),
    ("HCB strong", HCB, {STRONG}, 12, {55}),
    ("RDP", (BACK, D, DB), {WEAK}, 12, {56}),
    ("Super 2000", QCF + QCF, {WEAK}, 30, {85}),
    ("Super 2100", QCF + QCF, {STRONG}, 40, {86}),
    ("Super 2200", (D, BACK, D, BACK), {WEAK}, 40, {87}),
)


def run_case(rom, case):
    label, steps, buttons, min_dmg, want = case
    core = Core(CORE, rom)
    try:
        select = boot_select(core)
        enter_fight(core, select, "chizuru", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, 82 << 8)
        core.put(P2_X, 100 << 8)
        core.put(F_HP1, 200)
        core.put(F_HP2, 200)
        core.put(B + 0x30, 3000)
        core.step(30)
        hp0 = core.word(F_HP2)
        feed(core, steps, buttons)
        seen = set()
        for _ in range(900):
            core.step()
            seen.add(core.ram[F_STATE])
            if core.ram[F_STATE] == 0 and len(seen) > 1:
                if core.word(F_HP2) < hp0:
                    break
        hp1 = core.word(F_HP2)
        assert seen & want, f"{label}: states {sorted(seen)}"
        assert hp0 - hp1 >= min_dmg, (
            f"{label}: only {hp0 - hp1} damage ({hp0}->{hp1})")
        return hp0 - hp1
    finally:
        core.close()


def main():
    for case in CASES:
        dmg = run_case(ROOT / "kof98-snes.sfc", case)
        print(f"PASS Chizuru {case[0]}: {dmg} damage, states ok")
    print(f"PASS Chizuru: {len(CASES)} clone moves")


if __name__ == "__main__":
    main()
