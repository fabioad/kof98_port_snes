#!/usr/bin/env python3
"""Benimaru's DP anti-air kick (Super Inazuma) must be complete.

The source move lives in three states: 1400/1410 (intro), 1401/1411
(flying kick + HitDef) and 1402/1412 (landing).  The import only wired the
3-frame intro, so the kick never played, never hit and recovered instantly.
Runtime sids 107-110 now hold the kick/landing and chain from 54/55.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
BASE, FP2 = 0x4000, 0x40
F_STATE, F_HP, F_Y = 0x8, 0x10, 0x2
SPARKS, SPK_SIZE, SPK_ATTR = 0x4200, 20, 15
RIGHT, DOWN, UP, A, B = 7, 5, 4, 8, 0
S_DOWN = 10

CASES = (
    (B, 54, 107, 109, "weak"),
    (A, 55, 108, 110, "strong"),
)


def dp(core, button):
    # F, D, DF + button
    for direction in ((RIGHT,), (DOWN,), (RIGHT, DOWN)):
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = {button}
    core.step(2)
    core.buttons[0] = set()


def setup(core, select_state):
    enter_fight(core, select_state, "benimaru", "kyo")
    core.ram[0x1090] = core.ram[0x1091] = 0
    core.put(BASE, 80 << 8)
    core.put(BASE + FP2, 125 << 8)
    core.put(BASE + F_HP, 200)
    core.put(BASE + FP2 + F_HP, 200)
    core.buttons = [set(), set()]
    core.step(10)


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        for button, intro, kick, land, label in CASES:
            setup(core, select)
            hp0 = core.word(BASE + FP2 + F_HP)
            dp(core, button)
            states = []
            p2 = set()
            shot = False
            for _ in range(150):
                core.step()
                state = core.ram[BASE + F_STATE]
                if not states or states[-1] != state:
                    states.append(state)
                p2.add(core.ram[BASE + FP2 + F_STATE])
                if any(core.ram[SPARKS + i * SPK_SIZE + SPK_ATTR] & 0x80
                       for i in (0, 1)):
                    shot = True
            dmg = hp0 - core.word(BASE + FP2 + F_HP)
            assert states[:3] == [intro, kick, land], (label, states)
            assert dmg > 0, f"{label}: anti-air did not hit"
            assert S_DOWN in p2, f"{label}: victim never knocked down ({p2})"
            assert not shot, f"{label}: DP anti-air spawned a projectile"
            assert states[-1] == 0, f"{label}: move did not recover ({states})"
            print(f"PASS Super Inazuma {label}: {states[:3]}, "
                  f"{dmg} damage, knockdown")

        # Airborne target: the kick's high boxes must catch a jump.
        setup(core, select)
        hp0 = core.word(BASE + FP2 + F_HP)
        core.buttons[1] = {UP}
        core.step(2)
        core.buttons[1] = set()
        core.step(12)
        assert core.word(BASE + FP2 + F_Y) > 0
        dp(core, A)
        for _ in range(120):
            core.step()
        assert core.word(BASE + FP2 + F_HP) < hp0, \
            "Super Inazuma did not hit the jumping opponent"
        print("PASS Super Inazuma catches a jumping opponent")
    finally:
        core.close()


if __name__ == "__main__":
    main()
