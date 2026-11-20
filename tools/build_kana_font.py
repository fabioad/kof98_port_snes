"""Build assets/fonts/kana8.chr: 8x8 2bpp kana tiles for the fight HUD.

The Japanese option uses the same 3-colour 8x8 HUD font as the ASCII text.
Kana are rendered from Noto Sans CJK JP Bold into a 7x7 body and get the same
1-pixel dark outline as the ASCII glyphs, then packed as 2bpp SNES tiles in
tools/kana_charset.KANA order.

Run from the project root:
    python3 tools/build_kana_font.py
The generated file is committed so the ROM build does not need a system
Japanese font.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kana_charset import KANA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "fonts", "kana8.chr")
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_INDEX = 2          # Noto Sans CJK JP


def _glyph(ch, size=9, threshold=105):
    font = ImageFont.truetype(FONT, size, index=FONT_INDEX)
    canvas = Image.new("L", (24, 24), 0)
    ImageDraw.Draw(canvas).text((0, 0), ch, font=font, fill=255,
                                anchor="lt")
    box = canvas.getbbox()
    if not box:
        return [[0] * 8 for _ in range(8)]
    im = canvas.crop(box)
    # Keep a 1-pixel outline around a 7x7 body, like the ASCII font.
    if im.width > 7 or im.height > 7:
        k = min(7 / im.width, 7 / im.height)
        im = im.resize((max(1, round(im.width * k)),
                        max(1, round(im.height * k))), Image.LANCZOS)
    cell = [[0] * 8 for _ in range(8)]
    ox = (8 - im.width) // 2
    oy = (8 - im.height) // 2
    for y in range(im.height):
        for x in range(im.width):
            if im.getpixel((x, y)) >= threshold:
                cell[oy + y][ox + x] = 3
    out = [row[:] for row in cell]
    for y in range(8):
        for x in range(8):
            if cell[y][x]:
                continue
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                yy, xx = y + dy, x + dx
                if 0 <= xx < 8 and 0 <= yy < 8 and cell[yy][xx] == 3:
                    out[y][x] = 1
                    break
    return out


def encode(cell):
    out = bytearray()
    for y in range(8):
        lo = hi = 0
        for x in range(8):
            lo |= (cell[y][x] & 1) << (7 - x)
            hi |= ((cell[y][x] >> 1) & 1) << (7 - x)
        out += bytes((lo, hi))
    return bytes(out)


def main():
    data = bytearray()
    for ch in KANA:
        data += encode(_glyph(ch))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    print(f"{OUT}: {len(KANA)} kana, {len(data)} bytes")


if __name__ == "__main__":
    main()
