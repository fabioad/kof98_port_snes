#!/usr/bin/env python3
"""Decode the built ending screens (src/gen_menu/end/endNN.{chr,map,pal})
back into 256x224 PNGs, inverse of build_endings.build_frame.

Usage: python3 tools/decode_endings.py [first last] [outdir]
Defaults to ending2 (screens 05-10) -> assets/ending2/endNN.png
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src/gen_menu/end")


def _dec4(data):
    px = [0] * 64
    for y in range(8):
        b0, b1 = data[y * 2], data[y * 2 + 1]
        b2, b3 = data[16 + y * 2], data[16 + y * 2 + 1]
        for x in range(8):
            m = 1 << (7 - x)
            px[y * 8 + x] = ((b0 & m) != 0) | ((b1 & m) != 0) << 1 | \
                ((b2 & m) != 0) << 2 | ((b3 & m) != 0) << 3
    return px


def decode(base):
    from PIL import Image
    chrdata = open(base + ".chr", "rb").read()
    mwords = struct.unpack("<1024H", open(base + ".map", "rb").read())
    pal = struct.unpack("<64H", open(base + ".pal", "rb").read())

    def rgb(c):
        return ((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31,
                ((c >> 10) & 31) * 255 // 31)

    im = Image.new("RGB", (256, 224))
    for ty in range(28):
        for tx in range(32):
            w = mwords[ty * 32 + tx]
            tile = _dec4(chrdata[(w & 0x3FF) * 32:(w & 0x3FF) * 32 + 32])
            pbase = (w >> 10 & 0xF) * 16
            for y in range(8):
                for x in range(8):
                    im.putpixel((tx * 8 + x, ty * 8 + y),
                                rgb(pal[pbase + tile[y * 8 + x]]))
    return im


def main():
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    last = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    dst = sys.argv[3] if len(sys.argv) > 3 else \
        os.path.join(ROOT, "assets/ending2")
    os.makedirs(dst, exist_ok=True)
    for n in range(first, last + 1):
        base = os.path.join(SRC, f"end{n:02d}")
        out = os.path.join(dst, f"end{n:02d}.png")
        decode(base).save(out)
        print(f"  {out}")


if __name__ == "__main__":
    main()
