"""Title screen art (MnLoadArt 0) from an arcade-style 320x224 PNG.

Writes src/gen_menu/title.tiles / title.map / title.pal in the layout the
engine expects:

  * title.tiles: 4bpp tiles, loaded at BG1 tile base (VRAM word $4000).  At
    most 896 tiles (32x28) so the upload stays below $7800.
  * title.map:   32x28 map words (tile index | palette << 10).
  * title.pal:   4 palettes x 15 colors (colors 1..15; color 0 is never used,
    so no pixel is transparent).

The 320-pixel arcade frame is resized to 256 wide: both are shown 4:3 on a
TV, so the picture keeps its proportions.  Each tile picks the best of four
15-colour palettes (k-means over tiles), which keeps the logo gradients much
cleaner than fixed horizontal bands.

usage: python3 tools/build_title.py [source.png]
"""
import os
import struct
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(ROOT, "docs/title_arcade/title_snesfest.png")
DST = os.path.join(ROOT, "src/gen_menu")

W, H = 256, 224
TW, TH = W // 8, H // 8
NPAL, NCOL = 4, 15
MAX_TILES = 896


def snes5(rgb):
    """8-bit RGB -> what the SNES shows (5 bits per channel), as floats."""
    q = np.floor(rgb * 31 / 255 + 0.5)
    return q * 255 / 31


def kmeans(px, k, iters=12, seed=0):
    """Plain k-means on N x 3 colours; returns k centres (snapped to 5 bit)."""
    uniq = np.unique(px, axis=0)
    if len(uniq) <= k:
        cent = uniq.astype(float)
    else:
        rng = np.random.default_rng(seed)
        # k-means++ seeding
        cent = [uniq[rng.integers(len(uniq))].astype(float)]
        for _ in range(1, k):
            d = np.min(((uniq[:, None, :] - np.array(cent)[None]) ** 2).sum(2), 1)
            cent.append(uniq[rng.choice(len(uniq), p=d / d.sum())].astype(float))
        cent = np.array(cent)
        for _ in range(iters):
            lab = np.argmin(((px[:, None, :] - cent[None]) ** 2).sum(2), 1)
            for j in range(k):
                sel = px[lab == j]
                if len(sel):
                    cent[j] = sel.mean(0)
    cent = snes5(cent)
    if len(cent) < k:
        cent = np.vstack([cent, np.zeros((k - len(cent), 3))])
    return cent


def tile_err(tiles, pal):
    """Per-tile squared error when every pixel takes its nearest colour."""
    d = ((tiles[:, :, None, :] - pal[None, None]) ** 2).sum(3)
    return d.min(2).sum(1)


def enc4(idx):
    out = bytearray()
    for y in range(8):
        row = idx[y * 8:(y + 1) * 8]
        b0 = b1 = 0
        for x, v in enumerate(row):
            b0 |= (v & 1) << (7 - x)
            b1 |= ((v >> 1) & 1) << (7 - x)
        out += bytes((b0, b1))
    for y in range(8):
        row = idx[y * 8:(y + 1) * 8]
        b2 = b3 = 0
        for x, v in enumerate(row):
            b2 |= ((v >> 2) & 1) << (7 - x)
            b3 |= ((v >> 3) & 1) << (7 - x)
        out += bytes((b2, b3))
    return bytes(out)


def main(src=DEFAULT_SRC):
    im = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
    a = np.asarray(im, dtype=float)
    tiles = (a.reshape(TH, 8, TW, 8, 3).transpose(0, 2, 1, 3, 4)
             .reshape(TH * TW, 64, 3))

    # start from horizontal bands, then let tiles migrate to the palette that
    # fits them best and refit the palettes (a few rounds settle it)
    assign = np.repeat(np.arange(NPAL), TH * TW // NPAL)
    for rnd in range(6):
        pals = []
        for p in range(NPAL):
            px = tiles[assign == p].reshape(-1, 3)
            if not len(px):
                px = tiles.reshape(-1, 3)
            pals.append(kmeans(px, NCOL, seed=rnd * 7 + p))
        pals = np.array(pals)
        err = np.stack([tile_err(tiles, pals[p]) for p in range(NPAL)], 1)
        new = err.argmin(1)
        total = err.min(1).sum()
        print(f"  round {rnd}: rms {np.sqrt(total / tiles.size):.2f}")
        if (new == assign).all():
            break
        assign = new

    # Tile 0 stays a solid dark tile: MnLoadArt fills map rows 28-31 with
    # word 0, and the bottom scanline shows row 28.
    dark = int(np.argmin(pals[0].sum(1)))
    blank = enc4([dark + 1] * 64)
    chars, lut, mwords = [blank], {blank: 0}, []
    preview = np.zeros_like(a)
    for t in range(TH * TW):
        pal = pals[assign[t]]
        idx = ((tiles[t][:, None, :] - pal[None]) ** 2).sum(2).argmin(1)
        enc = enc4([int(i) + 1 for i in idx])          # colours 1..15
        if enc not in lut:
            lut[enc] = len(chars)
            chars.append(enc)
        mwords.append(lut[enc] | (int(assign[t]) << 10))
        ty, tx = divmod(t, TW)
        preview[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = pal[idx].reshape(8, 8, 3)
    assert len(chars) <= MAX_TILES, len(chars)

    pal_b = bytearray()
    for p in range(NPAL):
        for c in pals[p]:
            r, g, b = (int(round(v * 31 / 255)) for v in c)
            pal_b += struct.pack("<H", r | (g << 5) | (b << 10))
    open(os.path.join(DST, "title.tiles"), "wb").write(b"".join(chars))
    open(os.path.join(DST, "title.map"), "wb").write(
        b"".join(struct.pack("<H", w) for w in mwords))
    open(os.path.join(DST, "title.pal"), "wb").write(bytes(pal_b))
    prev = os.environ.get("KOF_TITLE_PREVIEW")
    if prev:
        Image.fromarray(preview.astype(np.uint8)).save(prev)
    print(f"title: {len(chars)} tiles ({len(chars) * 32} B), "
          f"palette use {np.bincount(assign, minlength=NPAL).tolist()}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC)
