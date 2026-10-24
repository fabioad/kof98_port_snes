#!/usr/bin/env python3
"""Headless regression for the documented SNES face-button layout.

    Y = weak punch (WP), X = strong punch (SP),
    B = weak kick  (WK), A = strong kick  (SK),
    L = dodge, L+back/fwd = roll, R = blowback, L+R = taunt.

Presses each physical pad button in a real fight and checks the state the
engine enters, so a label/mask swap in the generator or in PushHist cannot
silently ship again.

Run after a PVSnesLib build:

    python3 tools/test_face_buttons_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, GS = 0x4008, 0x1020
LEFT, RIGHT = 6, 7
B, Y, A, X, L, R = 0, 1, 8, 9, 10, 11

STAND_WP, STAND_SP, STAND_WK, STAND_SK = 5, 6, 7, 8
DODGE, BLOWBACK, TAUNT, ROLL_BACK, ROLL_FWD = 69, 67, 47, 94, 95


def tap(core, buttons, ticks=3):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    state = core.ram[F_STATE]
    core.buttons[0] = set()
    core.step(6)
    return state


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "terry", "kyo")
        for _ in range(800):
            if core.word(GS) == 1:
                break
            core.step()
        else:
            raise AssertionError(f"round never went live: gs={core.word(GS)}")
        core.put(0x4000, 80 << 8)
        core.put(0x4040, 200 << 8)
        core.step(20)
        base = core.save()

        face = {
            Y: (STAND_WP, "Y -> weak punch"),
            X: (STAND_SP, "X -> strong punch"),
            B: (STAND_WK, "B -> weak kick"),
            A: (STAND_SK, "A -> strong kick"),
        }
        for button, (expected, label) in face.items():
            core.load(base)
            core.buttons[0] = set()
            core.step(2)                     # settle the restored frame
            state = tap(core, {button})
            assert state == expected, (label, state, expected)
            print(f"PASS {label}: state {state}")

        shoulders = (
            ({L}, DODGE, "L -> standing dodge"),
            ({R}, BLOWBACK, "R -> blowback"),
            ({L, R}, TAUNT, "L+R -> taunt"),
            ({L, LEFT}, ROLL_BACK, "L+back -> roll back"),
            ({L, RIGHT}, ROLL_FWD, "L+fwd -> roll forward"),
        )
        for buttons, expected, label in shoulders:
            core.load(base)
            state = tap(core, buttons)
            assert state == expected, (label, state, expected)
            print(f"PASS {label}: state {state}")

        print("PASS face buttons and shoulder shortcuts")
    finally:
        core.close()


if __name__ == "__main__":
    main()
