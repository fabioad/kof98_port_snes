#!/usr/bin/env python3
"""Headless regression: Yuri's Ko'ou Ken must draw its animated frames.

The effect page is streamed by FxPrepareBoth at the vblank that presents the
OAM built at the end of the previous tick.  DrawSparks used to skip projectile
cells whenever FX_CACHE still pointed at the previous frame, which made every
multi-frame projectile invisible (the sprite slot advanced but no OAM cells
were emitted).  This test fires Ko'ou Ken and requires both the frame index
and the palette-2 OAM cells to be present across the flight.

Run after a PVSnesLib build:

    python3 tools/test_yuri_projectile_anim_headless.py
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
START, A, DOWN, RIGHT = 3, 8, 5, 7
# SNES Y = MUGEN x (weak punch); SNES X = MUGEN y (strong punch).
WEAK, STRONG = 1, 9


def step_buttons(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


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
        "attr": raw[15],
    }


def effect_cells(core):
    """Palette-2 OAM cells written by DrawSparks (sparks/projectiles)."""
    oam = bytes(core.ram[OAM:OAM + 512])
    return sum(1 for i in range(128) if (oam[i * 4 + 3] & 0x0E) == 4
               and oam[i * 4 + 1] < 0xF0)


def check_shot(core, button, sid):
    for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
        step_buttons(core, direction)
    step_buttons(core, {button})

    seen_frames = set()
    drawn_frames = set()
    cell_counts = {}
    for _ in range(80):
        core.step()
        sp = spark(core)
        if sp["anim"] and core.ram[F_STATE] == sid:
            seen_frames.add(sp["fidx"])
            count = effect_cells(core)
            cell_counts[sp["fidx"]] = max(count, cell_counts.get(sp["fidx"], 0))
            if count >= 5:
                drawn_frames.add(sp["fidx"])
        if seen_frames and core.ram[F_STATE] == 0:
            break
    assert seen_frames, f"sid {sid}: projectile never spawned"
    assert len(seen_frames) >= 4, (sid, sorted(seen_frames),
                                   "cells", cell_counts)
    assert len(drawn_frames) >= 4, (sid, sorted(drawn_frames),
                                    "cells", cell_counts)
    print(f"OK sid {sid}: animated frames {sorted(seen_frames)}, "
          f"drawn {sorted(drawn_frames)}, cells {cell_counts}")


def main():
    core = Core(CORE, ROM)
    try:
        select = boot_select(core)
        enter_fight(core, select, "yuri", "kyo")
        check_shot(core, WEAK, 48)
        wait(core, lambda: core.word(F_STATE) == 0, "recover")
        check_shot(core, STRONG, 49)
    finally:
        core.close()
    print("PASS: Yuri's Ko'ou Ken animates on screen")


if __name__ == "__main__":
    main()
