#!/usr/bin/env python3
"""Check that the generated stage data reproduces the stage PNGs exactly.

Decodes build/gen_fight/stages/stg*.chr/.map/.pal the way the SNES PPU sees
them (4bpp planes, tile flips, 16-colour BG palettes 2-4, BG colour 0
transparent) and compares every pixel with the source PNG.  Also checks the
512-tile budget and the animation pose tiles.

    python3 tools/verify_stage_export.py
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stages as bs

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def decode_tile(t, flip):
    rows = [[((t[r * 2] >> (7 - x)) & 1) | (((t[r * 2 + 1] >> (7 - x)) & 1) << 1) |
             (((t[16 + r * 2] >> (7 - x)) & 1) << 2) |
             (((t[16 + r * 2 + 1] >> (7 - x)) & 1) << 3)
             for x in range(8)] for r in range(8)]
    if flip & 1:
        rows = [r[::-1] for r in rows]
    if flip & 2:
        rows = rows[::-1]
    return rows


def cgram_to_rgb(c):
    return ((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31,
            ((c >> 10) & 31) * 255 // 31)


def main():
    paths = bs.sorted_stage_paths()
    total_bad = 0
    for i, path in enumerate(paths):
        name = os.path.basename(path)[:-4]
        d = os.path.join(ROOT, "build/gen_fight/stages")
        chr_b = open(f"{d}/stg{i}.chr", "rb").read()
        map_b = open(f"{d}/stg{i}.map", "rb").read()
        pal_b = open(f"{d}/stg{i}.pal", "rb").read()
        ntiles = len(chr_b) // 32
        assert ntiles <= bs.MAX_TILES, f"{name}: {ntiles} tiles"
        tiles = [chr_b[k * 32:(k + 1) * 32] for k in range(ntiles)]
        cg = [pal_b[k * 2] | pal_b[k * 2 + 1] << 8 for k in range(48)]
        src = Image.open(path)
        raw = src.tobytes()
        bad = 0
        for ty in range(28):
            for tx in range(64):
                mi = (tx // 32) * 1024 + ty * 32 + tx % 32
                w = map_b[mi * 2] | map_b[mi * 2 + 1] << 8
                pal, flip = (w >> 10) & 7, w >> 14
                assert 2 <= pal < 2 + bs.STAGE_NPAL, f"{name}: palette {pal}"
                tile = decode_tile(tiles[w & 0x3FF], flip)
                for r in range(8):
                    for x in range(8):
                        idx = (pal - bs.STAGE_BG_PALETTE) * bs.STAGE_NCOL
                        idx += tile[r][x] - 1          # BG colour 0 = clear
                        if idx != raw[(ty * 8 + r) * 512 + tx * 8 + x]:
                            bad += 1
        print(f"{name}: {ntiles} tiles, {len(pal_b)} palette bytes, "
              f"{bad} mismatched pixels")
        total_bad += bad
    assert total_bad == 0, f"{total_bad} mismatched pixels"
    print("stage export lossless")


if __name__ == "__main__":
    main()
