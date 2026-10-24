#!/usr/bin/env python3
"""Headless regression for Athena's specials and projectile animation.

The source CMD wires DP+P to the Psycho Sword (Gancho) and QCB+P to the
Psychic Ball.  The imported command table used to swap those rows, so
DP+P entered the Reflective Shield and QCB+strong entered the Psycho
Sword; the latter then froze on the animation's trailing hold because its
landing ChangeState had no native target.

This test also requires the Psychic Ball to play all eight AIR 1001 cels.
The effect compiler used to keep only the first and last frame.

Run after a PVSnesLib build:

    python3 tools/test_athena_projectile_anim_headless.py
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
F_STATE = 0x4008
SPARKS = 0x4200
SPK_SIZE = 20
OAM = 0x1800
START, A, DOWN, RIGHT, LEFT = 3, 8, 5, 7, 6
# Physical pad -> MUGEN button tokens used by the source CMD:
# SNES Y = x (light punch), SNES X = y (strong punch).
LIGHT_P, STRONG_P = 1, 9


def step_buttons(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()
    core.step(ticks)


def wait(core, pred, label, limit=8000):
    for _ in range(limit):
        if pred():
            return
        core.step()
    raise AssertionError(f"{label}: state={core.word(F_STATE)}")


def spark(core):
    raw = bytes(core.ram[SPARKS:SPARKS + SPK_SIZE])
    return {
        "anim": struct.unpack_from("<H", raw, 4)[0],
        "fidx": raw[6],
    }


def effect_cells(core):
    """Palette-2 OAM cells written by DrawSparks (sparks/projectiles)."""
    oam = bytes(core.ram[OAM:OAM + 512])
    return sum(1 for i in range(128) if (oam[i * 4 + 3] & 0x0E) == 4
               and oam[i * 4 + 1] < 0xF0)


def special(core, motion, button):
    for direction in motion:
        step_buttons(core, direction)
    step_buttons(core, {button})


def check_psychic_ball(core, label):
    special(core, ((DOWN,), (DOWN, LEFT), (LEFT,)), LIGHT_P)
    state = None
    seen = set()
    drawn = set()
    for _ in range(100):
        st = core.ram[F_STATE]
        if state is None and st:
            state = st
        if st == 48:
            sp = spark(core)
            if sp["anim"]:
                seen.add(sp["fidx"])
                if effect_cells(core) >= 3:
                    drawn.add(sp["fidx"])
        if state is not None and st == 0:
            break
        core.step()
    assert state == 48, (label, state)
    assert len(seen) == 8, (label, sorted(seen))
    assert drawn == seen, (label, sorted(seen), sorted(drawn))
    print(f"OK {label}: 8 projectile cels drawn")
    wait(core, lambda: core.word(F_STATE) == 0, "recover")


def check_psycho_sword(core, label):
    special(core, ((RIGHT,), (DOWN,), (DOWN, RIGHT)), LIGHT_P)
    state = None
    ticks = 0
    for _ in range(1000):
        st = core.ram[F_STATE]
        if state is None and st:
            state = st
        if state is not None:
            ticks += 1
        core.step()
        if state is not None and core.ram[F_STATE] == 0:
            break
    assert state == 49, (label, state)
    assert ticks < 120, (label, ticks, "landing transition missing")
    print(f"OK {label}: recovers in {ticks} ticks")
    wait(core, lambda: core.word(F_STATE) == 0, "recover")


def main():
    core = Core(CORE, ROM)
    try:
        select = boot_select(core)
        enter_fight(core, select, "athena", "kyo")
        check_psychic_ball(core, "Psychic Ball")
        check_psycho_sword(core, "Psycho Sword")
    finally:
        core.close()
    print("PASS: Athena's specials and projectile animation are wired")


if __name__ == "__main__":
    main()
