#!/usr/bin/env python3
"""Projectile specials must recover soon after the shot leaves.

Imported launch animations kept their full MUGEN follow-through, so a
fireball special could hold the fighter in the throw pose for ~50 ticks
after the shot was already flying (Benimaru's Raikouken was the clearest
case).  build_fight now rescales only the post-release tail of ground
projectile clips; startup and the shot itself are untouched.

Run after a PVSnesLib build:

    python3 tools/test_projectile_recovery_headless.py
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
F_STATE, FP2 = 0x4008, 0x40
F_X = 0x4000
SPARKS = 0x4200
DOWN, RIGHT = 5, 7
STRONG_P = 9    # SNES X -> MUGEN y
LIGHT_P = 1     # SNES Y -> MUGEN x


def press(core, buttons, ticks=1):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def qcf_p(core, button):
    for d in ({DOWN}, {DOWN, RIGHT}, {RIGHT}):
        core.buttons[0] = set(d)
        core.step(1)
    press(core, {button}, 2)


def measure(core, button, sid):
    qcf_p(core, button)
    for _ in range(20):
        if core.ram[F_STATE] == sid:
            break
        core.step()
    assert core.ram[F_STATE] == sid, f"state {sid} never started"

    duration = 0
    shot_at = None
    while core.ram[F_STATE] == sid and duration < 200:
        anim = struct.unpack_from("<H", core.ram, SPARKS + 4)[0]
        if shot_at is None and anim and (core.ram[SPARKS + 15] & 0x80):
            shot_at = duration
        core.step()
        duration += 1
    return duration, shot_at


def main():
    core = Core(CORE, ROM)
    try:
        sel = boot_select(core)
        for button, sid, name in ((LIGHT_P, 48, "light"),
                                  (STRONG_P, 49, "strong")):
            enter_fight(core, sel, "benimaru", "kyo")
            core.put(F_X, 64 << 8)
            core.put(F_X + FP2, 200 << 8)
            core.step(30)
            duration, shot_at = measure(core, button, sid)
            assert shot_at is not None, f"{name} Raikouken did not spawn"
            assert shot_at <= 10, (
                f"{name} Raikouken spawned at tick {shot_at} (want <= 10)")
            # Release lands on tick 5; 24 ticks of tail keep the whole state
            # under ~0.7 s even with the upload-aware minimum frame times
            # (the imported clip used to hold the pose for 58 ticks).
            assert duration <= 45, (
                f"{name} Raikouken recovery lasted {duration} ticks "
                f"(want <= 45)")
            print(f"OK {name} Raikouken: shot {shot_at}, "
                  f"state {duration} ticks")
        print("PASS projectile recovery")
    finally:
        core.close()


if __name__ == "__main__":
    main()
