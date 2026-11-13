#!/usr/bin/env python3
"""Native 256x224 ORDER SELECT art; BG1 sits behind the six 32x32 BG3 faces.

Only the background is redrawn: the blue/red fields now use the arcade
capture's textures and the title/VS are the real arcade logos, pasted exactly
where the old procedural lettering sat.  Panels, frames, name plates and the
footer keep the previous geometry, so the screen code is untouched.

Uses one 4bpp palette at CGRAM 32, leaving all six portrait palettes and
both text palettes intact.
"""
import struct
from pathlib import Path

from PIL import Image, ImageDraw

from build_select import snes_c
from sff import tiles4bpp

ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / 'src/gen_menu'
ARCADE = ROOT / 'docs/order_select_arcade/01_order_select_sem_lutadores.png'
ARCADE_CLEAN = ROOT / 'docs/order_select_arcade/02_fundo_mais_vs.png'

COLORS = [(0, 0, 0), (8, 8, 24), (8, 16, 64), (16, 32, 112),
          (24, 64, 184), (88, 152, 240), (48, 8, 24), (104, 16, 32),
          (160, 24, 40), (240, 96, 72), (112, 64, 16), (232, 168, 40),
          (255, 232, 136), (248, 248, 248), (112, 136, 176), (32, 40, 56)]

# Old procedural lettering occupied: ORDER/SELECT x93..163 y2..32, VS x117..139
# y44..58.  The arcade logos go in the same boxes.
TITLE_BOX = (93, 2, 163, 32)          # ORDER SELECT
TITLE_SRC = (116, 18, 204, 55)
VS_BOX = (114, 36, 142, 66)           # centred on the old badge (128, 51)
VS_SRC = (129, 130, 191, 197)


def rgb(i):
    return COLORS[i]


def quantize(image):
    pal = Image.new('P', (1, 1))
    pal.putpalette([v for c in COLORS for v in c] + [0] * (768 - 48))
    return image.quantize(palette=pal, dither=Image.Dither.NONE)


def logo(src, box, size):
    """Crop a gold/orange logo and scale it to `size`, with a soft mask."""
    crop = src.crop(box).convert('RGB')
    mask = Image.new('L', crop.size, 0)
    px, mp = crop.load(), mask.load()
    for y in range(crop.size[1]):
        for x in range(crop.size[0]):
            r, g, b = px[x, y]
            if min(r, g, b) > 150 or (r > 150 and g > 90 and b < 140):
                mp[x, y] = 255
    crop = crop.resize(size, Image.LANCZOS)
    mask = mask.resize(size, Image.LANCZOS).point(lambda v: 255 if v > 96 else 0)
    return crop, mask


def fields(image):
    """Arcade blue/red textures in the two halves, dark seam in the middle."""
    clean = Image.open(ARCADE_CLEAN).convert('RGB')
    blue = clean.crop((32, 0, 128, 224)).resize((128, 224), Image.LANCZOS)
    red = clean.crop((192, 0, 288, 224)).resize((128, 224), Image.LANCZOS)
    image.paste(blue, (0, 0))
    image.paste(red, (128, 0))
    # arcade-style edge shading: dark strip on the outer side of each field
    d = ImageDraw.Draw(image)
    d.line((3, 0, 3, 223), fill=2)
    d.line((252, 0, 252, 223), fill=6)
    d.line((126, 0, 126, 223), fill=1)
    d.line((129, 0, 129, 223), fill=1)


def artwork():
    image = Image.new('RGB', (256, 224), rgb(1))
    fields(image)
    d = ImageDraw.Draw(image)
    # dark central seam and the gold divider of the port's layout
    d.polygon([(94, 0), (162, 0), (141, 40), (115, 40)], fill=1)
    d.line((127, 64, 127, 193), fill=10)
    d.line((128, 64, 128, 193), fill=12)
    # header wings
    for points in ([(8, 9), (63, 9), (80, 31), (8, 31)],
                   [(248, 9), (193, 9), (176, 31), (248, 31)]):
        d.line(points + points[:1], fill=11)
    # side panels: chamfered corners, bright inner edge, toned-down band
    shade = Image.eval(image, lambda v: int(v * 0.34))
    for x, mid, edge in ((7, 3, 5), (135, 7, 9)):
        poly = [(x + 4, 44), (x + 109, 44), (x + 115, 50),
                (x + 115, 189), (x + 111, 193), (x + 4, 193),
                (x, 189), (x, 48)]
        m = Image.new('L', image.size, 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        image.paste(shade, (0, 0), m)
        d.polygon(poly, outline=None)
        d.line(poly + poly[:1], fill=edge)
        d.line((x + 4, 45, x + 108, 45), fill=13)
        d.line((x + 1, 49, x + 1, 188), fill=mid)
        d.rectangle((x + 3, 47, x + 111, 59), fill=mid)
        # keep the dynamic portrait's exact 32x32 footprint at x16/144
        for yy in (64, 104, 144):
            px = x + 9
            d.rectangle((px - 2, yy - 2, px + 33, yy + 33), fill=15)
            d.rectangle((px - 1, yy - 1, px + 32, yy + 32), outline=edge)
            d.line((px - 2, yy + 33, px - 2, yy - 2,
                    px + 33, yy - 2), fill=13)
            d.rectangle((px + 34, yy, x + 112, yy + 31), fill=mid)
            d.line((px + 34, yy + 31, x + 112, yy + 31), fill=edge)
        d.rectangle((x + 7, 181, x + 108, 192), fill=mid, outline=edge)
    # VS badge (same footprint as before) and the arcade logo inside it
    d.polygon([(110, 41), (146, 41), (150, 45), (146, 61),
               (110, 61), (106, 57)], fill=1, outline=11)
    # dark footer protects the small controller instructions
    d.rectangle((7, 197, 248, 222), fill=1)
    d.line((7, 196, 248, 196), fill=11)
    d.line((7, 223, 248, 223), fill=10)

    src = Image.open(ARCADE).convert('RGB')
    for box, srcrect in ((TITLE_BOX, TITLE_SRC), (VS_BOX, VS_SRC)):
        crop, mask = logo(src, srcrect, (box[2] - box[0], box[3] - box[1]))
        image.paste(crop, (box[0], box[1]), mask)
    return quantize(image)


def main():
    image = artwork()
    pixels = list(image.getdata())
    tiles, lookup, words = [], {}, []
    for ty in range(28):
        for tx in range(32):
            tile = bytes(pixels[(ty * 8 + y) * 256 + tx * 8 + x]
                         for y in range(8) for x in range(8))
            encoded = tiles4bpp(tile, 8, 8)[0]
            if encoded not in lookup:
                lookup[encoded] = len(tiles)
                tiles.append(encoded)
            words.append(lookup[encoded] | (2 << 10))
    # BG1 CHR occupies $0000..$1FFF words; BG3's font starts at $2000.
    assert len(tiles) <= 512, 'ORDER SELECT art overlaps BG3 character memory'
    words.extend([words[0]] * (1024 - len(words)))
    DST.mkdir(exist_ok=True)
    (DST / 'order.chr').write_bytes(b''.join(tiles))
    (DST / 'order.map').write_bytes(struct.pack('<1024H', *words))
    (DST / 'order.pal').write_bytes(struct.pack('<16H', *(snes_c(c) for c in COLORS)))
    out = ROOT / 'build/team_order'
    out.mkdir(parents=True, exist_ok=True)
    image.resize((768, 672), Image.Resampling.NEAREST).save(out / 'background.png')
    print(f'order art: {len(tiles)} tiles, palette 2; six 32x32 portraits reserved')


if __name__ == '__main__':
    main()
