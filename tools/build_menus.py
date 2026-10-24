"""Import the menu/title/intro art from the sibling kof98snes project.

Copies the pre-rendered SNES assets (4bpp tiles + 32x32 maps + 4 banded
palettes, and the packed mode-7 intro frames) into src/gen_menu/ so the
ROM build doesn't depend on the sibling tree.  Also emits menufont.chr:
the fight HUD font (49 tiles of hud.chr, 2bpp) padded out to 4bpp
so it can live in the OBJ tile area for sprite-drawn menu text.

intro15 (the logo finale frame) is built here from the reconstructed
title-logo.png: 256x224, four 7-row palette bands of 15 colors like the
title screen — the inherited intro15 assets render corrupted and its
SCR1-derived art predates the current logo.
"""
import os
import shutil
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(sys.argv[1] if len(sys.argv) > 1 else
                   "/run/media/fabio/Dados/Fabio/kof98snes",
                   "build/assets")
TITLE_LOGO = (sys.argv[2] if len(sys.argv) > 2 else
              "/run/media/fabio/Dados/Fabio/kof98java/opening_ending/"
              "reconstructed/scenes/title-logo.png")
DST = os.path.join(ROOT, "src/gen_menu")
INTRO_DST = os.path.join(DST, "intro")
GEN_FIGHT = os.path.join(ROOT, "src/gen_fight")

FONT_TILES = 49          # hud charset + ",@\"" for the MSU credits line
CUR_TILE_IDX = 60        # OBJ tile index the bracket pair lands on


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


def build_intro15():
    """title-logo.png -> intro15.chr/.map/.pal (4bpp, 32x32 map, 4 bands).

    The engine shows the frame on BG2 with palette 0-3 (same banded trick
    as the title screen): band b covers tile rows b*7..b*7+6 and selects
    pal b; .pal stores the four bands contiguously (color0 of each band
    black) so a single CGRAM copy covers colors 0-63.
    """
    from PIL import Image
    im = Image.open(TITLE_LOGO).convert("RGB").resize((256, 224),
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
    chr_b = b"".join(tiles)
    map_b = b"".join(struct.pack("<H", w) for w in mwords)
    open(os.path.join(INTRO_DST, "intro15.chr"), "wb").write(chr_b)
    open(os.path.join(INTRO_DST, "intro15.map"), "wb").write(map_b)
    open(os.path.join(INTRO_DST, "intro15.pal"), "wb").write(pal)
    print(f"  intro15: {len(tiles)} tiles ({len(chr_b)}B), "
          f"4x16 colors, {len(map_b)}B map")
    return len(chr_b) + len(map_b) + len(pal)


def cp(name):
    src = os.path.join(SRC, name)
    dst = os.path.join(DST, name)
    shutil.copyfile(src, dst)
    return os.path.getsize(dst)


def main():
    os.makedirs(INTRO_DST, exist_ok=True)

    total = 0
    for base in ("title", "modes"):
        for ext in ("tiles", "map", "pal"):
            total += cp(f"{base}.{ext}")
    total += cp("cur.tiles")

    # intro frames: full-screen stills + packed 16x14 mode-7 windows are
    # rebuilt from the reconstructed scene plates (tools/build_intro.py);
    # intro15 keeps coming from title-logo.png below
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_intro
    build_intro.main()
    n = 15
    total += build_intro15()

    # hud font -> 4bpp OBJ tiles (2bpp planes 0/1, planes 2/3 zero)
    hud = open(os.path.join(GEN_FIGHT, "hud.chr"), "rb").read()
    font = bytearray()
    for i in range(FONT_TILES):
        font += hud[i * 16:(i + 1) * 16]
        font += bytes(16)
    open(os.path.join(DST, "menufont.chr"), "wb").write(bytes(font))
    total += len(font)

    print(f"gen_menu: {n} intro files + title/modes + "
          f"{FONT_TILES} font tiles = {total} bytes")


if __name__ == "__main__":
    main()
