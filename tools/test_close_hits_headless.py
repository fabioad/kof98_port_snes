#!/usr/bin/env python3
"""Point-blank normals must connect, even after an overlap turns a fighter.

Lucky/Heavy D-style short jabs used to whiff when the fighters were touching:
the authored hit box ended just short of the victim's hurt box, and a pinned
overlap could leave the attacker facing away.  The engine now guarantees a
20 px forward reach and turns close attacks toward the opponent during their
startup.

Run after a PVSnesLib build:

    python3 tools/test_close_hits_headless.py
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
F_X, F_STATE, F_HP, F_FACING = 0, 8, 16, 14
COMBO = 0x4FC0
DOWN = 5
LIGHT_P = 1


def press(core, buttons, ticks=3):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def run_jab(core, select_state, char, distance=24, crouch=False):
    enter_fight(core, select_state, char, "kyo")
    core.ram[0x1091] = 0                # human dummy so the stance is stable
    core.put(FP1 + F_X, (120 - distance // 2) << 8)
    core.put(FP2 + F_X, (120 + distance // 2) << 8)
    core.put(FP1 + F_HP, 200)
    core.put(FP2 + F_HP, 200)
    core.step(20)
    hp0 = core.word(FP2 + F_HP)
    if crouch:
        core.buttons[0] = {DOWN}
        core.step(4)
        press(core, {DOWN, LIGHT_P})
    else:
        press(core, {LIGHT_P})
    for _ in range(80):
        core.step()
    return hp0 - core.word(FP2 + F_HP)


def run_facing_away(core, select_state):
    enter_fight(core, select_state, "kyo", "kyo")
    core.ram[0x1091] = 0
    core.put(FP1 + F_X, 100 << 8)
    core.put(FP2 + F_X, 130 << 8)
    core.put(FP1 + F_HP, 200)
    core.put(FP2 + F_HP, 200)
    core.step(20)
    hp0 = core.word(FP2 + F_HP)
    core.buttons[0] = {LIGHT_P}
    core.step(1)
    core.buttons[0] = set()
    core.step(1)
    if core.ram[FP1 + F_STATE] != 5:
        raise AssertionError("jab did not start")
    core.put(FP1 + F_FACING, 0xFFFF)     # force the attack to face away
    for _ in range(60):
        core.step()
    return hp0 - core.word(FP2 + F_HP)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for char in ("lucky", "heavyd", "kyo"):
            damage = run_jab(core, select_state, char)
            if damage <= 0:
                raise AssertionError(
                    f"{char}: point-blank jab whiffed (damage {damage})")
            print(f"PASS {char:8} point-blank jab: {damage} damage", flush=True)
        damage = run_jab(core, select_state, "lucky", crouch=True)
        if damage <= 0:
            raise AssertionError("crouching point-blank jab whiffed")
        print("PASS crouching point-blank jab", flush=True)
        damage = run_facing_away(core, select_state)
        if damage <= 0:
            raise AssertionError("attack forced to face away still whiffed")
        print("PASS close attack turns back toward the opponent", flush=True)
        print("PASS point-blank normals connect", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
