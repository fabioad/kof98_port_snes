#!/usr/bin/env python3
"""Andy's Kuuha Dan: two hits up close, one at range, last hit knocks down.

The source states 1300/1310 carry four HitDefs with MoveHitReset between the
active elements.  At point-blank range the first two contacts connect; far
contacts stay a single knockdown.  This checks both cases (and a crouching
victim, which used to sit under the high first hit box).

Run after a PVSnesLib build:

    python3 tools/test_andy_kuuha_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_X, F_STATE, F_HP = 0, 8, 16
COMBO = 0x4FC0
DOWN, LEFT, RIGHT = 5, 6, 7
DOWN_LEFT, DOWN_RIGHT = (DOWN, LEFT), (DOWN, RIGHT)
A, B = 8, 0                              # SNES A -> strong, B -> weak
S_HIT, S_DOWN = 9, 10
KUUHA_WEAK, KUUHA_STRONG = 48, 49


def hold(core, buttons, ticks=3):
    core.buttons[0] = set(buttons)
    core.step(ticks)


def press(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def kuuha(core, button):
    # B, DB, D, DF, F + punch (source: half-circle back to forward).
    for direction in ({LEFT}, DOWN_LEFT, {DOWN}, DOWN_RIGHT, {RIGHT}):
        hold(core, direction, 3)
    press(core, {button})


def run(core, select_state, distance, button, crouch):
    enter_fight(core, select_state, "andy", "kyo")
    core.ram[0x1091] = 0                 # human P2 so the crouch is stable
    core.put(FP1 + F_X, (120 - distance // 2) << 8)
    core.put(FP2 + F_X, (120 + distance // 2) << 8)
    core.put(FP1 + F_HP, 200)
    core.put(FP2 + F_HP, 200)
    core.step(20)
    if crouch:
        core.buttons[1] = {DOWN}
        core.step(4)

    hp0 = core.word(FP2 + F_HP)
    kuuha(core, button)

    peak = 0
    states = set()
    for _ in range(200):
        core.step()
        if crouch:
            core.buttons[1] = {DOWN}
        peak = max(peak, core.ram[COMBO])
        states.add(core.ram[FP2 + F_STATE])
    core.buttons[1] = set()
    damage = hp0 - core.word(FP2 + F_HP)
    return peak, damage, states


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for button, sid, name in ((A, KUUHA_STRONG, "strong"),
                                  (B, KUUHA_WEAK, "weak")):
            peak, damage, states = run(core, select_state, 0, button, False)
            if peak != 2:
                raise AssertionError(
                    f"{name} point-blank Kuuha Dan hit {peak} times, wanted 2")
            if S_DOWN not in states:
                raise AssertionError(
                    f"{name} point-blank Kuuha Dan did not knock down: "
                    f"{sorted(states)}")
            if not 30 <= damage <= 50:
                raise AssertionError(
                    f"{name} point-blank Kuuha Dan damage {damage}, wanted "
                    "two contacts")

        peak, damage, states = run(core, select_state, 16, A, True)
        if peak != 2 or S_DOWN not in states:
            raise AssertionError(
                f"crouching point-blank Kuuha Dan: combo {peak}, "
                f"states {sorted(states)}")

        peak, damage, states = run(core, select_state, 80, A, False)
        if peak != 1:
            raise AssertionError(
                f"far Kuuha Dan hit {peak} times, wanted a single hit")
        if S_DOWN not in states:
            raise AssertionError(
                f"far Kuuha Dan did not knock down: {sorted(states)}")

        print("PASS Andy Kuuha Dan: 2 hits point-blank, 1 at range, "
              "knockdown on the last contact", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
