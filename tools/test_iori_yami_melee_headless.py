#!/usr/bin/env python3
"""Headless regression for Iori's Yami Barai converted to a melee flame.

The port dropped the source helper projectile from 108 Shiki: Yami Barai
(sids 48/49).  The move must still enter the launch states, hit at close
range with the old damage (14 weak / 18 strong) and never spawn a travelling
shot in the spark pool.

Run after a PVSnesLib build:

    python3 tools/test_iori_yami_melee_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_HP, F_X = 0x4008, 0x4010, 0x4000
FP2 = 0x40
SPARKS, SPK_SIZE, SPK_ATTR = 0x4200, 20, 15
DOWN, RIGHT = 5, 7
Y, X = 1, 9                    # SNES Y = mugen x (weak), X = mugen y (strong)
WEAK, STRONG = 48, 49


def qcf(core, button, hold=3):
    for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
        core.buttons[0] = set(direction)
        core.step(hold)
    core.buttons[0] = {button}
    core.step(hold)
    core.buttons[0] = set()


def projectile_fired(core):
    """SPK_ATTR bit7 marks a pooled shot; hit sparks and Explods do not."""
    return any(core.ram[SPARKS + slot * SPK_SIZE + SPK_ATTR] & 0x80
               for slot in range(2))


def run(core, select, button, sid, damage):
    enter_fight(core, select, "iori", "kyo")
    core.put(F_X, 100 << 8)
    core.put(F_X + FP2, 145 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.put(0x4030, 3000)
    core.step(25)

    qcf(core, button)
    seen = False
    fired = False
    hit = False
    for _ in range(90):
        if core.ram[F_STATE] == sid:
            seen = True
        fired |= projectile_fired(core)
        if core.word(F_HP + FP2) < 200:
            hit = True
        core.step()
        if seen and core.ram[F_STATE] == 0:
            break

    if not seen:
        raise AssertionError(f"Yami Barai did not enter state {sid}")
    if fired:
        raise AssertionError("Yami Barai still spawned a travelling projectile")
    if not hit:
        raise AssertionError("Yami Barai lost its damage")
    lost = 200 - core.word(F_HP + FP2)
    if lost != damage:
        raise AssertionError(
            f"Yami Barai sid {sid}: damage {lost}, expected {damage}")
    if core.ram[F_STATE + FP2] not in (0, 9):
        raise AssertionError(
            f"victim did not enter hitstun; state={core.ram[F_STATE + FP2]}")
    return lost


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select = boot_select(core)
        lost = run(core, select, X, STRONG, 18)
        print(f"PASS Iori Yami Barai strong: melee flame, {lost} damage",
              flush=True)
        lost = run(core, select, Y, WEAK, 14)
        print(f"PASS Iori Yami Barai weak: melee flame, {lost} damage",
              flush=True)
        print("PASS Iori Yami Barai: no projectile, damage preserved",
              flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path,
                        default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, args.rom)
