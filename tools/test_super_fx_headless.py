#!/usr/bin/env python3
"""Kyo's super flash/dim is generic for every character's super.

Kyo's source super helper 7000 draws a full-screen white flash for four
frames, then a dark full-screen overlay for the 28-frame SuperPause, and
plays s9,0 at the transition.  The port implements the visual part with
SNES color math on BG1/BG2 and reuses the s9,0 sample as SFX_SUPER.  Enter
State triggers the effect whenever a state's PowTab cost is at least one
stock, so special-slot supers and MAX activations get it too.

Run after a PVSnesLib build:

    python3 tools/test_super_fx_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                 # noqa: E402
    boot_select, enter_fight, A, B, X, Y, UP, DOWN, LEFT, RIGHT)
from PIL import Image                                    # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE = 0x4008
F_X = 0x4000
F_POWER = 0x4030
SUPERFX = 0x51F0
SUPERFX_MODE = 0x51F1
FLASH_REGION = (140, 20, 220, 60)


def shot(core, path):
    w, h, pitch, data, fmt = core.last_frame
    im = Image.new("RGB", (w, h))
    px = []
    for y in range(h):
        for x in range(w):
            step = 4 if fmt == 1 else 2
            n = int.from_bytes(data[y * pitch + x * step:
                                    y * pitch + (x + 1) * step], "little")
            if fmt == 1:
                px.append(((n >> 16) & 255, (n >> 8) & 255, n & 255))
            elif fmt == 2:
                px.append((((n >> 11) & 31) * 255 // 31,
                           ((n >> 5) & 63) * 255 // 63,
                           (n & 31) * 255 // 31))
            else:
                px.append((((n >> 10) & 31) * 255 // 31,
                           ((n >> 5) & 31) * 255 // 31,
                           (n & 31) * 255 // 31))
    im.putdata(px)
    im.save(path)
    return im


def brightness(im, box):
    px = im.load()
    x0, y0, x1, y1 = box
    total = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b = px[x, y]
            total += r + g + b
    return total / (3 * (x1 - x0) * (y1 - y0))


def press(core, buttons, frames=2):
    core.buttons[0] = set(buttons)
    core.step(frames)


def motion(core, seq, button):
    for direction in seq:
        press(core, direction, 2)
    core.buttons[0] = set(button)
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def main(core_path, rom):
    core = Core(core_path, rom)
    core.capture_video = True
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "kyo", "iori")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(F_X, 80 << 8)
        core.put(0x4040, 120 << 8)
        core.put(F_POWER, 3000)
        core.step(30)

        pre_img = shot(core, "/tmp/super_fx_pre.png")
        pre = brightness(pre_img, FLASH_REGION)

        motion(core, ((DOWN,), (DOWN, RIGHT), (RIGHT,),
                      (DOWN,), (DOWN, RIGHT), (RIGHT,)), (X,))

        flash = dark = None
        flash_value = dark_value = None
        saw_mode1 = saw_mode2 = False
        for _ in range(80):
            core.step()
            fx = core.ram[SUPERFX]
            mode = core.ram[SUPERFX_MODE]
            if fx and mode == 1 and flash is None:
                saw_mode1 = True
                flash = shot(core, "/tmp/super_fx_flash.png")
                flash_value = brightness(flash, FLASH_REGION)
            if fx and mode == 2 and dark is None:
                saw_mode2 = True
                dark = shot(core, "/tmp/super_fx_dark.png")
                dark_value = brightness(dark, FLASH_REGION)
            if saw_mode2 and not fx:
                break
        else:
            raise AssertionError(
                f"super FX did not finish: fx={core.ram[SUPERFX]} "
                f"mode={core.ram[SUPERFX_MODE]} state={core.ram[F_STATE]}")
        assert saw_mode1, "super FX never entered the white flash phase"
        assert saw_mode2, "super FX never entered the dark phase"
        assert core.ram[SUPERFX] == 0 and core.ram[SUPERFX_MODE] == 0
        assert flash_value > pre + 50, (pre, flash_value)
        assert dark_value < pre * 0.75, (pre, dark_value)
        print(f"PASS super FX: pre={pre:.1f} flash={flash_value:.1f} "
              f"dark={dark_value:.1f}")
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", default=str(ROOT / "kof98-snes.sfc"))
    args = parser.parse_args()
    main(args.core, args.rom)
