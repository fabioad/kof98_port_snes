#!/usr/bin/env python3
"""Headless regression: projectile art mirrors when it travels left.

King's shot is strongly directional (head on the leading edge, tail behind).
The source cells are authored facing right, so a left-flying shot must set the
OAM hflip bit and mirror each 16x16 cell's X offset.  The port used to draw
both directions with the right-facing art.

Run after a PVSnesLib build:

    python3 tools/test_projectile_flip_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
SPARKS, SPK_SIZE = 0x4200, 20
OAM = 0x1800
DOWN, LEFT, RIGHT = 5, 6, 7
STRONG = 9


def step_buttons(core, port, buttons, ticks=2):
    core.buttons[port] = set(buttons)
    core.step(ticks)
    core.buttons[port] = set()


def shot(core, port, seq, limit):
    for direction in seq:
        step_buttons(core, port, direction)
    step_buttons(core, port, {STRONG})
    for _ in range(90):
        core.step()
        raw = bytes(core.ram[SPARKS:SPARKS + SPK_SIZE])
        anim = raw[4] | raw[5] << 8
        if not anim or raw[6] != 0:
            continue
        slot_x = raw[0] | raw[1] << 8
        if not limit(slot_x):
            continue
        oam = bytes(core.ram[OAM:OAM + 512])
        cells = [(oam[i * 4], oam[i * 4 + 3]) for i in range(128)
                 if (oam[i * 4 + 3] & 0x0E) == 4
                 and oam[i * 4 + 1] < 0xF0]
        if cells:
            return slot_x, cells
    raise AssertionError(f"no projectile frame for port {port}")


def main():
    core = Core(CORE, ROM)
    try:
        select = boot_select(core)
        enter_fight(core, select, "king", "king")
        right_x, right = shot(core, 0, ((DOWN,), (DOWN, RIGHT), (RIGHT,)),
                              lambda x: x >= 140)
        assert all(attr & 0x40 == 0 for _x, attr in right), right
        core.step(60)

        left_x, left = shot(core, 1, ((DOWN,), (DOWN, LEFT), (LEFT,)),
                            lambda x: x <= 160)
        assert all(attr & 0x40 for _x, attr in left), left

        right_offsets = sorted(x - right_x for x, _a in right)
        left_offsets = sorted(x - left_x for x, _a in left)
        assert right_offsets == sorted(-o - 16 for o in left_offsets), (
            right_offsets, left_offsets)
        print(f"OK right offsets {right_offsets}")
        print(f"OK left  offsets {left_offsets} (hflip set)")
    finally:
        core.close()
    print("PASS: projectiles mirror when travelling left")


if __name__ == "__main__":
    main()
