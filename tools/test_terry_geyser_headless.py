#!/usr/bin/env python3
"""Headless regression: Terry's Power Geyser uses an animated projectile.

The source move paints a stationary helper pillar (AIR 3020) at the ground
punch, but the port only had one ProjFx clip per fighter, so the super either
reused the Power Wave flame or spawned no effect at all.  The generated
alternate clip and the ProjTab release/alt bits keep the geyser in place,
animate its three compact poses, hit once and free the one-shot slot.

Run after a PVSnesLib build:

    python3 tools/test_terry_geyser_headless.py
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
F_FRAME = 0x400A
F_X = 0x4000
F_HP = 0x4010
F_POWER = 0x4030
FP2 = 0x40
SPARKS = 0x4200
SPK_SIZE = 20
OAM = 0x1800
DOWN, LEFT, RIGHT = 5, 6, 7
WEAK = 1
GEYSER_SIDS = {85, 86}
EXPECTED_FRAMES = {0, 1, 2}


def step_buttons(core, buttons, ticks=3):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def motion(core, steps, button, hold=3):
    for step in steps:
        step_buttons(core, step, hold)
    step_buttons(core, {button}, hold)
    core.step(4)


def spark(core):
    raw = bytes(core.ram[SPARKS:SPARKS + SPK_SIZE])
    return {
        "x": struct.unpack_from("<H", raw, 0)[0],
        "y": struct.unpack_from("<H", raw, 2)[0],
        "anim": struct.unpack_from("<H", raw, 4)[0],
        "fidx": raw[6],
        "vx": struct.unpack_from("<H", raw, 8)[0],
        "attr": raw[15],
    }


def effect_cells(core):
    """Palette-2 OAM cells written by DrawSparks (16x16 OBJ cells)."""
    oam = bytes(core.ram[OAM:OAM + 512])
    return sum(1 for i in range(128) if (oam[i * 4 + 3] & 0x0E) == 4
               and oam[i * 4 + 1] < 0xF0)


def setup(core, victim_x):
    core.put(F_X, 60 << 8)
    core.put(F_X + FP2, victim_x << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.put(F_POWER, 3000)
    core.step(10)


def fire_geyser(core):
    motion(core, ((DOWN,), (LEFT,), (RIGHT,)), WEAK)


def main():
    core = Core(CORE, ROM)
    try:
        select = boot_select(core)

        # Whiff far away: the projectile must show its three poses and free
        # itself at the end of the one-shot clip instead of looping.
        enter_fight(core, select, "terry", "terry")
        setup(core, 210)
        fire_geyser(core)
        frames = {}
        entered_state = False
        released = False
        for _ in range(140):
            sp = spark(core)
            if core.word(F_STATE) in GEYSER_SIDS:
                entered_state = True
            if sp["anim"]:
                assert sp["vx"] == 0, sp
                assert sp["attr"] & 0x80, sp          # hitbox projectile
                assert sp["attr"] & 0x08, sp          # one-shot clip
                frames.setdefault(sp["fidx"], set()).add(effect_cells(core))
                if sp["fidx"] in (1, 2):
                    released = True
            elif released:
                break
            core.step()
        else:
            raise AssertionError("geyser projectile never freed")
        assert entered_state, "Power Geyser state was never entered"
        assert set(frames) == EXPECTED_FRAMES, frames
        assert max(frames[0]) >= 1
        assert max(frames[1]) >= 5, frames
        assert max(frames[2]) >= 5, frames
        print(f"OK Power Geyser animation: frames {sorted(frames)}, "
              f"cells { {k: max(v) for k, v in frames.items()} }")

        # Close range: the stationary pillar must connect for super damage.
        enter_fight(core, select, "terry", "terry")
        setup(core, 105)
        fire_geyser(core)
        hit = False
        for _ in range(120):
            if core.word(F_HP + FP2) <= 174:
                hit = True
                break
            core.step()
        assert hit, core.word(F_HP + FP2)
        print(f"OK Power Geyser hit: hp 200 -> "
              f"{core.word(F_HP + FP2)}")
    finally:
        core.close()
    print("PASS: Terry's Power Geyser animates and hits")


if __name__ == "__main__":
    main()
