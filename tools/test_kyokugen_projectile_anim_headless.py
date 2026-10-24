#!/usr/bin/env python3
"""Headless regression: the Kyokugen team shares Yuri's Ko'ou Ken effect.

Ryo, Robert and Takuma used shorter/older projectile cels.  PROJECTILE_FX_ALIAS
now points their descriptors at Yuri's six-cel animation, so every fireball
must expose the same six frame indices and draw its palette-2 OAM cells.

Run after a PVSnesLib build:

    python3 tools/test_kyokugen_projectile_anim_headless.py
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
EXPECTED_FRAMES = set(range(6))

# Yuri's Ko'ou Ken uses the weak button; the other three expose the shared
# effect on the projectile rows reached by QCF+strong in this port.  Ryo and
# Robert keep the weak shot on their original sid and the strong one on the
# next free special slot (61 and 59); Takuma already had both wired (48/49).
CASES = (("yuri", 48, WEAK), ("ryo", 61, STRONG),
         ("robert", 59, STRONG), ("takuma", 49, STRONG))


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
    for _ in range(120):
        core.step()
        sp = spark(core)
        if sp["anim"] and core.ram[F_STATE] == sid:
            seen_frames.add(sp["fidx"])
            count = effect_cells(core)
            cell_counts[sp["fidx"]] = max(count,
                                          cell_counts.get(sp["fidx"], 0))
            if count >= 5:
                drawn_frames.add(sp["fidx"])
        if seen_frames and core.ram[F_STATE] == 0:
            break
    assert seen_frames == EXPECTED_FRAMES, (sid, sorted(seen_frames),
                                            "cells", cell_counts)
    assert drawn_frames == EXPECTED_FRAMES, (sid, sorted(drawn_frames),
                                             "cells", cell_counts)
    print(f"OK sid {sid}: frames {sorted(seen_frames)}, "
          f"cells {cell_counts}")


def main():
    core = Core(CORE, ROM)
    try:
        select = boot_select(core)
        for name, sid, button in CASES:
            enter_fight(core, select, name, "kyo")
            check_shot(core, button, sid)
            wait(core, lambda: core.word(F_STATE) == 0, "recover")
            print(f"PASS {name}")
    finally:
        core.close()
    print("PASS: Kyokugen projectiles share Yuri's six-cel animation")


if __name__ == "__main__":
    main()
