#!/usr/bin/env python3
"""Exercise Fusion power gain, manual charge and MAX activation in Snes9x."""
from pathlib import Path

from calibration.headless import Core
from capture_pair_headless import tap, wait
from test_roster import parse_tables
from test_voice_stream import to_select

ROOT = Path(__file__).resolve().parents[1]
P1_POWER, P2_POWER = 0x4030, 0x4070
P1_STATE, P1_MAX = 0x4008, 0x403B


def main():
    roster = parse_tables()
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        to_select(core)
        core.ram[0xF053] = roster[1]["cell"]
        tap(core, 8, 1)
        core.ram[0xF052] = roster[0]["cell"]
        tap(core, 8, 0)
        wait(core, lambda: core.ram[0x1020] == 1, "fight", 1200)
        wait(core, lambda: core.word(P1_STATE) == 0, "idle", 1000)
        core.ram[0x1090] = core.ram[0x1091] = 0

        core.put(0x4000, 100 << 8)
        core.put(0x4040, 124 << 8)
        core.buttons[0] = {9}  # X: standing punch
        core.step(30)
        core.buttons[0] = set()
        assert core.word(P1_POWER) == 75, core.word(P1_POWER)
        assert core.word(P2_POWER) == 38, core.word(P2_POWER)
        wait(core, lambda: core.word(P1_STATE) == 0, "punch recovery")

        core.buttons[0] = {11, 1, 0, 9}  # R+Y+B+X: manual charge
        core.step(24)
        core.buttons[0] = set()
        assert core.word(P1_POWER) >= 160, core.word(P1_POWER)
        wait(core, lambda: core.word(P1_STATE) == 0, "charge release")

        core.put(P1_POWER, 1050)
        core.buttons[0] = {1, 0, 9}  # Y+B+X: spend one stock
        wait(core, lambda: core.word(P1_STATE) == 96, "MAX burst", 30)
        assert core.word(P1_POWER) == 50, core.word(P1_POWER)
        assert core.ram[P1_MAX] >= 239, core.ram[P1_MAX]
        core.buttons[0] = set()
        core.step(250)
        assert core.ram[P1_MAX] == 0, core.ram[P1_MAX]
        print("PASS: hit +75/+38, charge, MAX -1000, MAX expires")
    finally:
        core.close()

    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        to_select(core)
        core.ram[0xF053] = roster[0]["cell"]
        tap(core, 8, 1)
        core.ram[0xF052] = roster[15]["cell"]  # imported Terry
        tap(core, 8, 0)
        wait(core, lambda: core.ram[0x1020] == 1, "MSU fight", 1200)
        wait(core, lambda: core.word(P1_STATE) == 0, "MSU idle", 1000)
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(P1_POWER, 1000)
        core.buttons[0] = {1, 0, 9}
        wait(core, lambda: core.word(P1_STATE) == 96, "MSU MAX burst", 30)
        assert core.word(P1_POWER) == 0, core.word(P1_POWER)
        assert core.ram[P1_MAX], "MSU MAX timer not armed"
        print("PASS: Terry MSU MAX costs one stock and arms timer")
    finally:
        core.close()


if __name__ == "__main__":
    main()
