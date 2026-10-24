#!/usr/bin/env python3
"""Capture the actual Snes9x video output for a selected versus pair."""
import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from test_roster import parse_tables


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def wait(core, predicate, label, limit=2400):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(f"{label}: gs={core.ram[0x1020]} frame={core.ram[0x1024]}")


def save_frame(frame, output):
    width, height, pitch, raw, fmt = frame
    if fmt == 1:  # RETRO_PIXEL_FORMAT_XRGB8888
        image = Image.frombytes("RGB", (width, height), raw, "raw", "BGRX", pitch)
    else:
        rgb = bytearray(width * height * 3)
        for y in range(height):
            for x in range(width):
                p = y * pitch + x * 2
                word = raw[p] | raw[p + 1] << 8
                if fmt == 2:  # RGB565
                    r, g, b = word >> 11 & 31, word >> 5 & 63, word & 31
                    g = g * 255 // 63
                else:  # 0RGB1555
                    r, g, b = word >> 10 & 31, word >> 5 & 31, word & 31
                    g = g * 255 // 31
                i = (y * width + x) * 3
                rgb[i:i+3] = bytes((r * 255 // 31, g, b * 255 // 31))
        image = Image.frombytes("RGB", (width, height), bytes(rgb))
    image.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("p1", type=int)
    parser.add_argument("p2", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--no-idle", action="store_true")
    args = parser.parse_args()
    roster = parse_tables()
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        for _ in range(60):
            if core.ram[0x1020] == 6:
                break
            tap(core, 3)  # START through opening/title
        wait(core, lambda: core.ram[0x1020] == 6, "menu")
        core.ram[0xF070] = 1  # versus
        tap(core, 3)
        wait(core, lambda: core.ram[0x1020] == 5, "select")
        core.ram[0x1091] = 0  # human P2
        core.ram[0xF053] = roster[args.p2]["cell"]
        tap(core, 8, 1)
        assert core.ram[0x108F] == 1, "P2 did not lock"
        core.ram[0xF052] = roster[args.p1]["cell"]
        tap(core, 8, 0)
        wait(core, lambda: core.ram[0x1020] == 1, "fight")
        if not args.no_idle:
            wait(core, lambda: core.word(0x4008) == 0 and core.word(0x4048) == 0,
                 "idle")
        before_frame = core.ram[0x1024]
        core.capture_video = True
        core.step(args.frames)
        save_frame(core.last_frame, args.output)
        print(f"saved {args.output} (gs={core.ram[0x1020]}, "
              f"sel={core.ram[0x1085]},{core.ram[0x1086]}, "
              f"stage={core.ram[0x1087]}, video={core.last_frame[:3]}, "
              f"fmt={core.pixel_format}, framecnt={before_frame}->{core.ram[0x1024]})")
        print("MSU seek/read:", bytes(core.ram[0x0910:0x0914]).hex(),
              bytes(core.ram[0x0920:0x0930]).hex(),
              "DMA:", bytes(core.ram[0x4016:0x401C]).hex(),
              bytes(core.ram[0x4056:0x405C]).hex())
        print("OAM top:", core.word(0x102A),
              "low:", bytes(core.ram[0x1800:0x1820]).hex(),
              "hi:", bytes(core.ram[0x1A00:0x1A20]).hex())
        hud_middle = core.ram[0x4700 + 7*64:0x4700 + 22*64]
        print("HUD middle nonzero:", sum(v != 0 for v in hud_middle),
              "row8:", bytes(core.ram[0x4700 + 8*64:0x4700 + 9*64]).hex())
    finally:
        core.close()


if __name__ == "__main__":
    main()
