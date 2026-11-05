#!/usr/bin/env python3
"""Normal throws must bind the victim by the torso, not by the feet.

The source uses ChangeAnim2 for the held victim, whose pose is anchored at
the torso.  The port used the victim's standing hit animation (5000), whose
axis is at the feet, so a bound opponent looked like they were being held by
the feet.  Every source SFF carries the torso-anchored hold sprite (group
5011); the build now uses it for the held slot (sid 76) of every fighter.

Run after a PVSnesLib build:

    python3 tools/test_throw_hold_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
SYM = ROOT / "kof98-snes.sym"
FP1, FP2 = 0x4000, 0x4040
F_STATE, F_ANIM, F_Y = 8, 0x12, 2
RIGHT, X = 7, 9
PAIRS = (("king", "kyo"), ("kyo", "king"),
         ("yuri", "king"), ("king", "yuri"),
         ("kyo", "terry"))


def symbol_offset(label):
    for line in SYM.read_text().splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] == label:
            return int(fields[0], 16) & 0xFFFF
    raise AssertionError(f"{label} missing from {SYM.name}")


def throw(attacker, victim):
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, attacker, victim)
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(FP1, 100 << 8)
        core.put(FP2, 112 << 8)
        core.step(10)
        core.put(FP1, 100 << 8)
        core.put(FP2, 112 << 8)
        core.buttons[0] = {RIGHT}
        core.step(2)
        core.buttons[0] = {RIGHT, X}
        core.step(2)
        core.buttons[0] = set()
        for _ in range(30):
            core.step()
            if core.ram[FP2 + F_STATE] == 76:
                return core.word(FP2 + F_ANIM), core.word(FP2 + F_Y)
        raise AssertionError(
            f"{attacker} -> {victim}: victim never entered the held state "
            f"(attacker sid {core.ram[FP1 + F_STATE]})")
    finally:
        core.close()


def main():
    for attacker, victim in PAIRS:
        anim, y = throw(attacker, victim)
        expected = symbol_offset(f"{victim}Anim76")
        assert anim == expected, (
            f"{attacker} -> {victim}: held anim ${anim:04X} != ${expected:04X}")
        print(f"PASS {attacker} -> {victim}: torso-anchored held pose "
              f"(y={y})")


if __name__ == "__main__":
    main()
