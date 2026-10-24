"""Convert the KOF'98 ending frame PNGs into Mode-1 BG2 screens.

Same pipeline as build_menus.build_intro15: 256x224, 4bpp tiles, 32x32
map, four 7-row palette bands of 15 colors (band b -> palette b, so a
single 128B CGRAM copy covers colors 0-63).  Output goes to
src/gen_menu/end/endNN.{chr,map,pal}; endings 00-04 are the Rugal-defeat
cinematic (ending1), 05-22 the credits/"Thank you" sequence (ending2).

ending2 screens 06-20 are the fifteen per-team ending+credits pairs
from assets/ending_pairs; they run as a fast montage (60 frames each,
same total as the three 300-frame screens they replaced: 1880/2902/
3445).  21-22 remain the SNK logo + "Thank you" cards.
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = (sys.argv[1] if len(sys.argv) > 1 else
       "/run/media/fabio/Dados/Fabio/kof98java/opening_ending")
PAIRS = os.path.join(ROOT, "assets/ending_pairs")
DST = os.path.join(ROOT, "src/gen_menu/end")

FRAMES = [
    "endinng_001/frame_000145.png",
    "endinng_001/frame_000233.png",
    "endinng_001/frame_000530.png",
    "endinng_001/frame_001010.png",
    "endinng_001/frame_001529.png",
    "ending_002/frame_001603.png",
    "ending_002/frame_003446.png",
    "ending_002/frame_004162.png",
]

# pair PNGs fill ending screens 6-20, in sorted (team) order
PAIR_FILES = sorted(os.listdir(PAIRS))


def main():
    os.makedirs(DST, exist_ok=True)
    seq = ([os.path.join(SRC, f) for f in FRAMES[:6]] +
           [os.path.join(PAIRS, f) for f in PAIR_FILES] +
           [os.path.join(SRC, f) for f in FRAMES[6:]])
    assert len(seq) == 23, len(seq)
    for i, path in enumerate(seq):
        n = build_frame(path, os.path.join(DST, f"end{i:02d}"))
        print(f"  end{i:02d}: {os.path.basename(path)} -> {n}B chr")


def _rgb_to_snes(c):
    r, g, b = c
    return (r * 31 // 255) | ((g * 31 // 255) << 5) | ((b * 31 // 255) << 10)


def _enc4(px):
    out = bytearray()
    for y in range(8):
        b0 = b1 = 0
        for x in range(8):
            v = px[y * 8 + x]
            b0 |= (v & 1) << (7 - x)
            b1 |= ((v >> 1) & 1) << (7 - x)
        out += bytes((b0, b1))
    for y in range(8):
        b2 = b3 = 0
        for x in range(8):
            v = px[y * 8 + x]
            b2 |= ((v >> 2) & 1) << (7 - x)
            b3 |= ((v >> 3) & 1) << (7 - x)
        out += bytes((b2, b3))
    return bytes(out)


def build_frame(path, outbase):
    from PIL import Image
    im = Image.open(path).convert("RGB").resize((256, 224),
                                                Image.LANCZOS)
    tiles, lut = [], {}
    pal = bytearray()
    mwords = [0] * (32 * 32)
    for band in range(4):
        crop = im.crop((0, band * 56, 256, (band + 1) * 56)).convert("RGB")
        q = crop.quantize(colors=15, method=Image.MEDIANCUT,
                          dither=Image.NONE)
        qp = q.getpalette()
        ncol = len(qp) // 3
        qc = sorted(tuple(qp[i * 3:i * 3 + 3]) for i in range(ncol))
        qc += [(0, 0, 0)] * (15 - len(qc))
        rank = {c: i + 1 for i, c in enumerate(qc)}
        qlut = list(q.getdata())
        raw = [tuple(qp[i * 3:i * 3 + 3]) for i in range(ncol)]
        pal += struct.pack("<H", 0)
        pal += b"".join(struct.pack("<H", _rgb_to_snes(c)) for c in qc)
        for ty in range(7):
            for tx in range(32):
                px = [rank[raw[qlut[(ty * 8 + y) * 256 + tx * 8 + x]]]
                      for y in range(8) for x in range(8)]
                enc = _enc4(px)
                if enc not in lut:
                    lut[enc] = len(tiles)
                    tiles.append(enc)
                mwords[(band * 7 + ty) * 32 + tx] = lut[enc] | (band << 10)
    open(outbase + ".chr", "wb").write(b"".join(tiles))
    open(outbase + ".map", "wb").write(
        b"".join(struct.pack("<H", w) for w in mwords))
    open(outbase + ".pal", "wb").write(bytes(pal))
    return len(tiles) * 32


if __name__ == "__main__":
    main()
