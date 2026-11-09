#!/usr/bin/env python3
"""Native 256x224 ORDER SELECT art; BG1 sits behind the six 32x32 BG3 faces.

Uses one 4bpp palette at CGRAM 32, leaving all six portrait palettes and
both text palettes intact. No portrait pixels are resized or baked here.
"""
import struct
from pathlib import Path

from PIL import Image, ImageDraw
from build_select import snes_c
from sff import tiles4bpp

ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / 'src/gen_menu'
COLORS = [(0, 0, 0), (8, 8, 24), (8, 16, 64), (16, 32, 112),
          (24, 64, 184), (88, 152, 240), (48, 8, 24), (104, 16, 32),
          (160, 24, 40), (240, 96, 72), (112, 64, 16), (232, 168, 40),
          (255, 232, 136), (248, 248, 248), (112, 136, 176), (32, 40, 56)]


GLYPHS = {
    'O': (14, 17, 17, 17, 17, 17, 14),
    'R': (30, 17, 17, 30, 20, 18, 17),
    'D': (30, 17, 17, 17, 17, 17, 30),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'S': (15, 16, 16, 14, 1, 1, 30),
    'L': (16, 16, 16, 16, 16, 16, 31),
    'C': (14, 17, 16, 16, 16, 17, 14),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'V': (17, 17, 17, 17, 17, 10, 4),
}


def label(image, text, cx, y, scale=2):
    mask = Image.new('L', (len(text) * 6 - 1, 7))
    for i, ch in enumerate(text):
        for yy, bits in enumerate(GLYPHS[ch]):
            for xx in range(5):
                if bits & (1 << (4 - xx)):
                    mask.putpixel((i * 6 + xx, yy), 255)
    mask = mask.resize((mask.width * scale, mask.height * scale),
                       Image.Resampling.NEAREST)
    x = cx - mask.width // 2
    image.paste(1, (x + 1, y + 2), mask)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        image.paste(10, (x + dx, y + dy), mask)
    for row in range(mask.height):
        strip = mask.crop((0, row, mask.width, row + 1))
        image.paste(12 if row < mask.height // 3 else 11,
                    (x, y + row), strip)


def artwork():
    image = Image.new('P', (256, 224), 1)
    image.putpalette([v for c in COLORS for v in c] + [0] * (768 - 48))
    d = ImageDraw.Draw(image)
    # Layered angular blue/red fields, separated by a dark central seam.
    for side, base, mid, light, edge in ((0, 2, 3, 4, 5), (1, 6, 7, 8, 9)):
        x = side * 128
        d.rectangle((x, 0, x + 127, 223), fill=base)
        d.polygon([(x, 0), (x + 95, 0), (x + 127, 80),
                   (x + 127, 223), (x + 70, 223)], fill=mid)
        for yy in range(-80, 250, 32):
            d.line((x, yy, x + 127, yy + 96), fill=light, width=1)
        d.line((x + (3 if side == 0 else 124), 0,
                x + (3 if side == 0 else 124), 223), fill=edge)
    d.polygon([(94, 0), (162, 0), (141, 40), (115, 40)], fill=1)
    d.line((127, 64, 127, 193), fill=10)
    d.line((128, 64, 128, 193), fill=12)
    # Header wings and the double-line gold title.
    for points in ([(8, 9), (63, 9), (80, 31), (8, 31)],
                   [(248, 9), (193, 9), (176, 31), (248, 31)]):
        d.line(points + points[:1], fill=11)
    label(image, 'ORDER', 128, 2)
    label(image, 'SELECT', 128, 18)
    # Side panels: chamfered corners, a bright inner edge and dark content.
    for x, mid, edge in ((7, 3, 5), (135, 7, 9)):
        poly = [(x + 4, 44), (x + 109, 44), (x + 115, 50),
                (x + 115, 189), (x + 111, 193), (x + 4, 193),
                (x, 189), (x, 48)]
        d.polygon(poly, fill=1)
        d.line(poly + poly[:1], fill=edge)
        d.line((x + 4, 45, x + 108, 45), fill=13)
        d.line((x + 1, 49, x + 1, 188), fill=mid)
        d.rectangle((x + 3, 47, x + 111, 59), fill=mid)
        # Keep the dynamic portrait's exact 32x32 footprint at x16/144.
        for yy in (64, 104, 144):
            px = x + 9
            d.rectangle((px - 2, yy - 2, px + 33, yy + 33), fill=15)
            d.rectangle((px - 1, yy - 1, px + 32, yy + 32), outline=edge)
            d.line((px - 2, yy + 33, px - 2, yy - 2,
                    px + 33, yy - 2), fill=13)
            d.rectangle((px + 34, yy, x + 112, yy + 31), fill=mid)
            d.line((px + 34, yy + 31, x + 112, yy + 31), fill=edge)
        d.rectangle((x + 7, 181, x + 108, 192), fill=mid, outline=edge)
    d.polygon([(110, 41), (146, 41), (150, 45), (146, 61),
               (110, 61), (106, 57)], fill=1, outline=11)
    label(image, 'VS', 128, 44)
    # Dark footer protects the small controller instructions.
    d.rectangle((7, 197, 248, 222), fill=1)
    d.line((7, 196, 248, 196), fill=11)
    d.line((7, 223, 248, 223), fill=10)
    return image


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
