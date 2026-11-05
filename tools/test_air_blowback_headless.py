#!/usr/bin/env python3
"""Air blowback (R in the air) must hit with the whole body.

The engine reuses sid 24's strong-air normal as the air blowback.  Its
authored Clsn1 only covers the fist/arm, so a blowback that crosses the
opponent's body can whiff.  The air-blowback latch (F_TFLAGS bit 4) now
selects a full-body box inside MinReachBox; the normal strong-air attack
keeps the authored arm box.

The check jumps to a fixed height above a standing opponent.  At that
height the authored arm box misses; R (blowback) must connect, while X
(the same animation without the latch) must not.

Run after a PVSnesLib build:

    python3 tools/test_air_blowback_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE = FP1 + 8
F_Y, F_VY = FP1 + 2, FP1 + 6
F_TFLAGS = FP1 + 51
HP2 = FP2 + 0x10
UP, R, X = 4, 11, 9
AIR_BLOW_LATCH = 0x10


def attempt(core, select, character, button):
    enter_fight(core, select, character, "kyo")
    core.ram[0x1090] = core.ram[0x1091] = 0
    core.put(FP1, 100 << 8)
    core.put(FP2, 110 << 8)
    core.put(HP2, 200)
    core.step(30)
    hp_before = core.word(HP2)

    core.buttons[0] = {UP}
    core.step(2)
    core.buttons[0] = set()
    core.step(4)
    # Wait for the actual StJump handler: state 14 is the one-frame jump
    # start, which would route R through the normal attack table.
    for _ in range(20):
        if core.ram[F_STATE] in (4, 15, 16):
            break
        core.step()
    assert core.ram[F_STATE] in (4, 15, 16), (
        f"{character}: unexpected jump state {core.ram[F_STATE]}")

    # Fixed height: the authored arm box is above the standing opponent's
    # hurtbox, while a full-body box still overlaps the head/upper body.
    core.put(F_Y, 80 << 8)
    core.put(F_VY, 0)
    core.buttons[0] = {button}
    core.step(2)
    core.buttons[0] = set()
    latch = core.ram[F_TFLAGS] & AIR_BLOW_LATCH

    states = []
    for _ in range(60):
        core.step()
        state = core.ram[F_STATE]
        if not states or states[-1] != state:
            states.append(state)
        if core.word(HP2) != hp_before:
            break
    return hp_before, core.word(HP2), states, latch


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        for character in ("kyo", "terry", "chang", "mai"):
            hp0, hp1, states, latch = attempt(core, select, character, R)
            assert 24 in states, f"{character}: air blowback state missing ({states})"
            assert latch, f"{character}: air-blowback latch not set"
            assert hp1 < hp0, (
                f"{character}: air blowback missed the body ({hp0} -> {hp1}, {states})")
            print(f"PASS {character}: air blowback hit at body range "
                  f"({hp0} -> {hp1})")

        # Control: the same sid-24 clip without the latch keeps the authored
        # arm box and misses the same fixed-height body overlap.
        hp0, hp1, states, latch = attempt(core, select, "kyo", X)
        assert 24 in states, f"control: strong air punch state missing ({states})"
        assert not latch, "control: normal strong-air attack set the blowback latch"
        assert hp1 == hp0, (
            f"control: normal strong air punch gained the full-body box ({states})")
        print("PASS control: normal strong air punch keeps the arm box")
    finally:
        core.close()


if __name__ == "__main__":
    main()
