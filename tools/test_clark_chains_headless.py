#!/usr/bin/env python3
"""Headless regression for Clark's Ultra Argentine / Running Three chains.

The ROM diet used to drop Clark's 87-89 slots, leaving the MAX Ultra
Argentine (3050) and both Running Three roots (3100/3110) without a wired
state.  This test feeds each command and checks that the grab/follow-up
chain runs and removes life:

  * 3000 / 3050  Ultra Argentine weak / MAX  (HCBHCB+X and MAX_SUPER)
  * 3100 / 3110  Running Three weak / strong (HCFHCF+A/B)
  * 3150         Running Three MAX (double-HCF+C, port-side input)
  * 1600         Flashing Elbow (QCF+C, port-side input)

Run after a PVSnesLib build:

    python3 tools/test_clark_chains_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
B = 0x4000
F_STATE, F_POWER = B + 8, B + 0x30
F_HP1, F_HP2 = B + 0x10, B + 0x50
P1_X, P2_X = B + 0, B + 0x40

UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
Y, X, PHYS_B, PHYS_A, L = 1, 9, 0, 8, 10  # MUGEN x/y/a/b -> Y/X/B/A

D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
DB = frozenset({DOWN, LEFT})
B = frozenset({LEFT})

HCB_X = (F, DF, D, DB, B, F, DF, D, DB, B)
HCB_Y = HCB_X
HCB_XY = HCB_X
HCF_A = (B, DB, D, DF, F, B, DB, D, DF, F)
HCF_B = HCF_A
QCF = (D, DF, F)


def feed(core, steps, buttons, hold=2):
    last = set()
    for token in steps:
        core.buttons[0] = set(token)
        last = set(token)
        core.step(hold)
    core.buttons[0] = last | set(buttons)
    core.step(hold)
    core.buttons[0] = set()


# name, steps, buttons, min damage, expected states, p1 x, p2 x
CASES = (
    ("Ultra Argentine weak", HCB_X, {X}, 60,
     {85, 109, 110, 111, 103, 104, 105, 106}, 82, 100),
    ("Ultra Argentine MAX", HCB_XY, {X, Y}, 60,
     {87, 109, 110, 111, 103, 104, 105, 106}, 82, 100),
    ("Running Three weak", HCF_A, {PHYS_B}, 40,
     {88, 62, 66, 60}, 82, 100),
    ("Running Three strong", HCF_B, {PHYS_A}, 40,
     {62, 66, 60}, 82, 100),
    ("Running Three MAX", HCF_A, {L}, 40,
     {86, 64, 66, 60}, 82, 100),
    ("Flashing Elbow", QCF, {L}, 8,
     {112, 113, 114}, 60, 110),
)


def run_case(rom, case):
    label, steps, buttons, min_dmg, want, x1, x2 = case
    core = Core(CORE, rom)
    try:
        select = boot_select(core)
        enter_fight(core, select, "clark", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, x1 << 8)
        core.put(P2_X, x2 << 8)
        core.put(F_HP1, 200)
        core.put(F_HP2, 200)
        core.put(F_POWER, 3000)
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
        print(f"PASS Clark {case[0]}: {dmg} damage, states ok")
    print(f"PASS Clark: {len(CASES)} chains")


if __name__ == "__main__":
    main()
