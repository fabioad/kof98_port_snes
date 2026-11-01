#!/usr/bin/env python3
"""Export indexed PNG frames as per-frame SNES Mode-7 assets.

Input is ``assets/video/Wmva3m93t34/frames`` (128x112, 256 colours).  Each
frame becomes the exact pair consumed by the intro's ``InLM7`` loader:

    frame_00000.m7pak   header + tile 0 + 8x8 8bpp tiles + 16x14 cell map
    frame_00000.m7pal   256-colour CGRAM palette (R/B pre-swapped)

The conversion preserves the PNG palette indices, so a decoded pak matches
the source PNG pixel-for-pixel.

Usage:
  python3 tools/export_snes_frames.py
"""
import argparse
import json
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "assets/video/Wmva3m93t34/frames"
DEFAULT_OUT = ROOT / "assets/video/Wmva3m93t34/frames_snes"
W, H = 128, 112
COLS, ROWS = W // 8, H // 8
MAP0 = (52 << 7) | 56          # intro Mode-7 window centre ($1A38)


def snes_color(c):
    r, g, b = c
    return (r * 31 // 255) | ((g * 31 // 255) << 5) | ((b * 31 // 255) << 10)


def swapped(c):
    r, g, b = c
    return snes_color((b, g, r))


def convert(path):
    im = Image.open(path)
    if im.mode != "P" or im.size != (W, H):
        raise ValueError(f"{path.name}: expected a {W}x{H} P-mode PNG, "
                         f"got {im.mode} {im.size}")
    pixels = bytes(im.getdata())
    pal = list(im.getpalette() or [])
    pal += [0] * (768 - len(pal))

    tiles = []
    seen = {bytes(64): 0}       # all-black tile is tile 0
    cells = bytearray()
    for cy in range(ROWS):
        for cx in range(COLS):
            tb = bytes(pixels[(cy * 8 + y) * W + cx * 8 + x]
                       for y in range(8) for x in range(8))
            idx = seen.get(tb)
            if idx is None:
                idx = len(tiles) + 1
                seen[tb] = idx
                tiles.append(tb)
            cells.append(idx)
    if len(tiles) + 1 > 256:
        raise ValueError(f"{path.name}: {len(tiles) + 1} tiles > 256")

    pak = struct.pack("<HHH", len(tiles) + 1, COLS | (ROWS << 8), MAP0)
    pak += bytes(64)             # tile 0: solid black
    pak += b"".join(tiles)
    pak += bytes(cells)

    # The existing Mode-7 renderer swaps R/B, so the CGRAM copy is pre-swapped.
    cg = bytearray()
    for i in range(256):
        cg += struct.pack("<H", swapped(tuple(pal[i * 3:i * 3 + 3])))
    return pak, bytes(cg), len(tiles)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", type=Path, default=DEFAULT_IN)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    frames = sorted(args.frames.glob("frame_*.png"))
    if not frames:
        raise SystemExit(f"no frame_*.png under {args.frames}")
    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("frame_*.m7*"):
        old.unlink()

    total_pak = total_pal = 0
    max_tiles = 0
    for i, path in enumerate(frames):
        pak, cg, ntiles = convert(path)
        stem = args.out / f"frame_{i:05d}"
        stem.with_suffix(".m7pak").write_bytes(pak)
        stem.with_suffix(".m7pal").write_bytes(cg)
        total_pak += len(pak)
        total_pal += len(cg)
        max_tiles = max(max_tiles, ntiles)
        if (i + 1) % 50 == 0 or i + 1 == len(frames):
            print(f"  converted {i + 1}/{len(frames)}")

    manifest = {
        "source": str(args.frames.relative_to(ROOT)),
        "output": str(args.out.relative_to(ROOT)),
        "frame_count": len(frames),
        "resolution": [W, H],
        "colors": 256,
        "format": "SNES Mode-7 .m7pak + .m7pal (InLM7-compatible)",
        "frame_ticks": "7/8 alternating",
        "duration_seconds": 54.0,
        "total_pak_bytes": total_pak,
        "total_pal_bytes": total_pal,
        "max_unique_tiles": max_tiles,
    }
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"exported {len(frames)} frames to {args.out}")
    print(f"  pak {total_pak} B, pal {total_pal} B, "
          f"max {max_tiles} unique tiles")


if __name__ == "__main__":
    main()
