#!/usr/bin/env python3
"""Rebuild the opening-intro art so every image fills the screen.

The inherited assets showed every frame as a 12x10-cell (96x80 px) window
parked near screen centre.  This regenerates them from the reconstructed
scene plates:

- mode-1 stills (intro00s/02s/12s): full 256x224, same 4-banded-palette
  pipeline as intro15/endings (tools/build_endings.build_frame);
- mode-7 windows (introNN.m7pak/.m7pal): 16x14 cells = 128x112 texels,
  which is exactly the visible area at the new rest scale 0.5 (menucore
  InFxParams were halved and the M7 pivot re-anchored to screen centre).
  Cell value = pak tile index; tile 0 is a reserved black tile for the
  out-of-window cells (map is cleared to 0 before the window is drawn).
  Window centre texel stays (512,472) -> map0 = (52<<7)|56 = $1A38.

Screen -> scene mapping (reconstructed/scenes/*.png):
  00 title-card      01 speed-streak     02 snk-presents
  03 warriors-text   04 special-ring     05 special-edition
  06 fighter-fragments 07 kyo-portrait   08 team-silhouettes
  09 iori-full       10 team-collage     11 white-flash
  12 leg-action      13 iori-close       14 man-backlight
  15 title-logo (unchanged, built by build_menus.build_intro15)
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_endings import build_frame, _rgb_to_snes          # noqa: E402

SCENES = (sys.argv[1] if len(sys.argv) > 1 else
          "/run/media/fabio/Dados/Fabio/kof98java/opening_ending/"
          "reconstructed/scenes")
DST = os.path.join(ROOT, "src/gen_menu/intro")

SCENE_FOR = {
    0: "title-card", 1: "speed-streak", 2: "snk-presents",
    3: "warriors-text", 4: "special-ring", 5: "special-edition",
    6: "fighter-fragments", 7: "kyo-portrait", 8: "team-silhouettes",
    9: "iori-full", 10: "team-collage", 11: "white-flash",
    12: "leg-action", 13: "iori-close", 14: "man-backlight",
}
STILLS = (0, 2, 12)
COLS, ROWS = 16, 14          # 128x112 texels == visible area at rest 0.5
MAP0 = (52 << 7) | 56        # window centre texel (512,472) = M7 pivot


def build_m7(png, outbase):
    from PIL import Image
    im = Image.open(png).convert("RGB").resize((COLS * 8, ROWS * 8),
                                               Image.LANCZOS)
    q = im.quantize(colors=255, method=Image.MEDIANCUT,
                    dither=Image.NONE)
    qp = q.getpalette()
    ncol = len(qp) // 3
    lut = list(q.getdata())

    tiles = []                      # pak tiles, index >= 1 (0 = black)
    seen = {bytes(64): 0}           # all-zero pixel tile -> cell 0
    cells = bytearray()
    for cy in range(ROWS):
        for cx in range(COLS):
            tb = bytes(lut[(cy * 8 + y) * COLS * 8 + cx * 8 + x] + 1
                       for y in range(8) for x in range(8))
            if tb not in seen:
                seen[tb] = len(tiles) + 1
                tiles.append(tb)
            cells.append(seen[tb])
    assert len(tiles) + 1 <= 256, f"{png}: {len(tiles)} tiles > 255"

    pak = struct.pack("<HHH", len(tiles) + 1, COLS | ROWS << 8, MAP0)
    pak += bytes(64)                # tile 0: solid backdrop colour
    pak += b"".join(tiles)
    pak += bytes(cells)

    # NOTE: the engine's Mode-7 path renders the palette with R and B
    # swapped (verified on the real libretro core — the inherited art
    # showed blue flames).  Bake the swap here so .m7pal colours land
    # correctly; mode-1 assets keep the normal encoding.
    def swap(c):
        r, g, b = c
        return _rgb_to_snes((b, g, r))

    pal = bytearray(struct.pack("<H", 0))
    for i in range(255):
        c = tuple(qp[i * 3:i * 3 + 3]) if i < ncol else (0, 0, 0)
        pal += struct.pack("<H", swap(c))

    open(outbase + ".m7pak", "wb").write(pak)
    open(outbase + ".m7pal", "wb").write(bytes(pal))
    return len(tiles), len(pak)


def main():
    os.makedirs(DST, exist_ok=True)
    for n, scene in SCENE_FOR.items():
        src = os.path.join(SCENES, scene + ".png")
        if n in STILLS:
            b = build_frame(src, os.path.join(DST, f"intro{n:02d}s"))
            print(f"  intro{n:02d}s: {scene} -> {b}B chr")
        else:
            t, size = build_m7(src, os.path.join(DST, f"intro{n:02d}"))
            print(f"  intro{n:02d}: {scene} -> {t} tiles, {size}B pak")


if __name__ == "__main__":
    main()
