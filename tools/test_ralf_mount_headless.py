#!/usr/bin/env python3
"""Headless regression for Ralf's Running Super mount.

The mount is a throw: the first connecting HitDef must leave the victim on
its own sprite data (F_GRAB bit1 clear).  If the flag is set, DrawFighter
reads Ralf's character data for the victim and the screen shows two Ralfs.

Run after a PVSnesLib build:

    python3 tools/test_ralf_mount_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (boot_select, enter_fight,
                                        B, DOWN, LEFT, RIGHT)  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
FRAME = 0x1024
F_STATE, F_HP, F_X, F_GRAB, F_OWNER = 0x4008, 0x4010, 0x4000, 0x4034, 0x4035
FP2 = 0x40


def wait(core, pred, label, limit=4000):
    for _ in range(limit):
        if pred():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.ram[GS]} p1={core.ram[F_STATE]} "
        f"p2={core.ram[F_STATE + FP2]} frame={core.ram[FRAME]}")


def motion(core, dirs, button):
    for direction in dirs:
        core.buttons[0] = set(direction)
        core.step(3)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "ralf", "kyo")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(F_X, 80 << 8)
        core.put(F_X + FP2, 125 << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.put(0x4030, 3000)             # meter for the super
        core.step(10)

        # QCBHCF + weak punch: D, DB, B, DB, D, DF, F, B (MUGEN a -> SNES B).
        motion(core, ((DOWN,), (DOWN, LEFT), (LEFT,), (DOWN, LEFT),
                      (DOWN,), (DOWN, RIGHT), (RIGHT,)), B)

        last = core.ram[FRAME]
        stall = 0
        mounted = False
        for _ in range(500):
            core.step()
            frame = core.ram[FRAME]
            if frame == last:
                stall += 1
                if stall > 90:
                    raise AssertionError("fight loop froze during the mount")
            else:
                stall = 0
            last = frame
            if core.ram[F_STATE + FP2] == 76:
                mounted = True
                break
        assert mounted, (
            "victim never entered the held state: "
            f"p1={core.ram[F_STATE]} p2={core.ram[F_STATE + FP2]}")
        grab = core.ram[F_GRAB + FP2]
        assert grab & 0x02 == 0, (
            f"victim uses the attacker's animation data (F_GRAB={grab:#x})")
        assert grab & 0x01 == 1, (
            f"victim is not bound to the mount (F_GRAB={grab:#x})")
        hp = core.word(F_HP + FP2)

        # Let the twelve strikes and the final throw finish.
        wait(core, lambda: core.ram[F_STATE] == 0, "attacker recovery", 1200)
        assert core.word(F_HP + FP2) < hp, "mount strikes did not damage"
        print(
            "PASS Ralf mount: victim F_GRAB=%#x, HP %d -> %d, p1 back to 0"
            % (grab, hp, core.word(F_HP + FP2)))
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, str(args.rom))
