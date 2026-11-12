#!/usr/bin/env python3
"""Capture before/after PNG frames of Clark's grabs in the running ROM.

Boots versus with Clark on P1 (or P2), performs a grab, and saves one PNG
per requested tick plus a contact-sheet strip.  The tick numbers come from
``tools/trace_clark_throws_headless.py`` so both tools describe the same
timeline.

Usage:
    python3 tools/capture_clark_throws_headless.py \
        --case "Ultra Argentine weak" --victim kyo \
        --frames 40,46,72,133,170,230,330,353,413 \
        --out build/clark_throw_caps/before
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                                   # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight          # noqa: E402
from trace_clark_throws_headless import CASES, motion, snap             # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040
F_X, F_HP, F_POWER, F_GRAB = 0, 16, 48, 52


def save_frame(frame, output):
    width, height, pitch, raw, fmt = frame
    if fmt == 1:  # XRGB8888
        image = Image.frombytes("RGB", (width, height), raw, "raw", "BGRX",
                                pitch)
    else:
        rgb = bytearray(width * height * 3)
        for y in range(height):
            for x in range(width):
                p = y * pitch + x * 2
                word = raw[p] | raw[p + 1] << 8
                if fmt == 2:  # RGB565
                    r, g, b = word >> 11 & 31, word >> 5 & 63, word & 31
                    g = g * 255 // 63
                    b = b * 255 // 31
                    r = r * 255 // 31
                else:        # BGR555
                    r, g, b = word & 31, word >> 5 & 31, word >> 10 & 31
                    r, g, b = r * 255 // 31, g * 255 // 31, b * 255 // 31
                q = y * width * 3 + x * 3
                rgb[q], rgb[q + 1], rgb[q + 2] = r, g, b
        image = Image.frombytes("RGB", (width, height), bytes(rgb))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return image


def run(core, base, case, victim, p2side, x0, ticks, limit):
    label, mot, buttons, gap, _normal = case
    att, _vic = (P2, P1) if p2side else (P1, P2)
    pad = 1 if p2side else 0
    core.load(base)
    core.buttons = [set(), set()]
    if p2side:
        core.put(P2 + F_X, x0 << 8)
        core.put(P1 + F_X, (x0 - gap) << 8)
    else:
        core.put(P1 + F_X, x0 << 8)
        core.put(P2 + F_X, (x0 + gap) << 8)
    core.put(att + F_POWER, 3000)
    core.put(P1 + F_HP, 200)
    core.put(P2 + F_HP, 200)
    core.step(20)
    fwd_right = snap(core, att)["facing"] > 0
    steps = motion(mot, fwd_right)
    for tok in steps:
        core.buttons[pad] = set(tok)
        core.step(2)
    core.buttons[pad] = set(steps[-1]) | set(buttons)
    core.step(2)
    core.buttons[pad] = set()
    core.capture_video = True
    core.step(1)
    out = {}
    for t in range(limit + 1):
        if t in ticks:
            out[t] = core.last_frame
        core.step(1)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    ap.add_argument("--victim", default="kyo")
    ap.add_argument("--p2", action="store_true")
    ap.add_argument("--x", type=int, default=110)
    ap.add_argument("--case", default="Ultra Argentine weak")
    ap.add_argument("--frames", default="40,46,72,133,170,230,330,353,413")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=430)
    args = ap.parse_args()
    ticks = {int(v) for v in args.frames.split(",") if v.strip()}
    case = next(c for c in CASES if c[0] == args.case)
    core = Core(CORE, args.rom)
    try:
        sel = boot_select(core)
        p1, p2 = ((args.victim, "clark") if args.p2 else ("clark", args.victim))
        enter_fight(core, sel, p1, p2)
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.step(20)
        base = core.save()
        frames = run(core, base, case, args.victim, args.p2, args.x, ticks,
                     args.limit)
    finally:
        core.close()
    images = []
    for t in sorted(frames):
        path = args.out / f"{args.case.replace(' ', '_').lower()}_{args.victim}_t{t:03d}.png"
        images.append((t, save_frame(frames[t], path)))
        print("saved", path)
    if images:
        w, h = images[0][1].size
        sheet = Image.new("RGB", (w, h * len(images)))
        for i, (_t, im) in enumerate(images):
            sheet.paste(im, (0, i * h))
        sheet_path = args.out / f"{args.case.replace(' ', '_').lower()}_{args.victim}_sheet.png"
        sheet.save(sheet_path)
        print("saved", sheet_path)


if __name__ == "__main__":
    main()
