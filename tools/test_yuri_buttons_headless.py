#!/usr/bin/env python3
"""Headless regression for Yuri's separate button layout.

ohgaki's Yuri package uses Neo-Geo token order (a=LP, x=HP, b=LK, y=HK).
gen_char_cfg.py rewrites her command strings to the pack's standard tokens,
so the shared Y/X/B/A pad still means:

    Y = weak punch, X = strong punch, B = weak kick, A = strong kick.

This test exercises the real ROM: normals must enter the standard sids and
the four special motions must fire with the matching physical button.

Run after a PVSnesLib build:

    python3 tools/test_yuri_buttons_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS, F_STATE = 0x1020, 0x4008
DOWN, LEFT, RIGHT = 5, 6, 7
B, Y, A, X = 0, 1, 8, 9

QCF = ((DOWN,), (DOWN, RIGHT), (RIGHT,))
QCB = ((DOWN,), (DOWN, LEFT), (LEFT,))
HCB = ((RIGHT,), (RIGHT, DOWN), (DOWN,), (DOWN, LEFT), (LEFT,))
DP = ((RIGHT,), (DOWN,), (DOWN, RIGHT))

# physical button -> (normal sid, special state)
SPECIALS = (
    ("QCF+Y  Ko-Ou-Ken weak", QCF, Y, 48),
    ("QCF+X  Ko-Ou-Ken strong", QCF, X, 49),
    ("QCB+Y  Saiha weak", QCB, Y, 50),
    ("QCB+X  Saiha strong", QCB, X, 51),
    ("HCB+B  Senkai Kyaku weak", HCB, B, 52),
    ("HCB+A  Senkai Kyaku strong", HCB, A, 53),
    ("DP+B   Kuuga weak", DP, B, 54),
    ("DP+A   Kuuga strong", DP, A, 55),
)


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "yuri", "kyo")
        for _ in range(800):
            if core.word(GS) == 1:
                break
            core.step()
        else:
            raise AssertionError(f"round never went live: gs={core.word(GS)}")
        core.put(0x4000, 100 << 8)
        core.put(0x4040, 150 << 8)
        core.step(20)
        base = core.save()

        for button, sid, label in ((Y, 5, "Y weak punch"), (X, 6, "X strong punch"),
                                   (B, 7, "B weak kick"), (A, 8, "A strong kick")):
            core.load(base)
            core.buttons[0] = set()
            core.step(2)
            core.buttons[0] = {button}
            core.step(2)
            state = core.ram[F_STATE]
            core.buttons[0] = set()
            core.step(30)
            assert state == sid, (label, state, sid)
            print(f"PASS {label}: state {state}")

        def motion(seq, button):
            core.load(base)
            core.buttons[0] = set()
            core.step(2)
            for direction in seq:
                core.buttons[0] = set(direction)
                core.step(2)
            core.buttons[0] = {button}
            core.step(2)
            state = core.ram[F_STATE]
            core.buttons[0] = set()
            core.step(30)
            return state

        for label, seq, button, expected in SPECIALS:
            state = motion(seq, button)
            assert state == expected, (label, state, expected)
            print(f"PASS {label}: state {state}")

        # Shoulder shortcuts use the shared pad: L dodge, L+back/fwd rolls,
        # R blowback and L+R taunt.  The forward roll is the one that used to
        # exit on the first tick for Yuri.
        for label, buttons, expected in (
                ("L dodge", {10}, 69),
                ("L+back roll", {10, LEFT}, 94),
                ("L+fwd roll", {10, RIGHT}, 95),
                ("R blowback", {11}, 67),
                ("L+R taunt", {10, 11}, 47)):
            core.load(base)
            core.buttons[0] = set()
            core.step(2)
            core.buttons[0] = set(buttons)
            core.step(2)
            state = core.ram[F_STATE]
            core.buttons[0] = set()
            core.step(30)
            assert state == expected, (label, state, expected)
            print(f"PASS {label}: state {state}")

        print("PASS Yuri: shared Y/X/B/A layout with translated token order")
    finally:
        core.close()


if __name__ == "__main__":
    main()
