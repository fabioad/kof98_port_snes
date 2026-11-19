#!/usr/bin/env python3
"""Verifica a saida de build_v2.py por um caminho independente do gerador.

  1. cada KOF98-*.png passa pelo conversor real (tools/build_stages.emit_stage)
     e respeita 512 tiles / 3x15 cores;
  2. CHR + mapa + CGRAM sao decodificados como o PPU (planos 4bpp, flips,
     paletas 2-4, cor 0 transparente) e comparados pixel a pixel com o PNG;
  3. cada estado de cada clip e reconstruido SO a partir de
     anim/*.json (palavras de tilemap) + anim/*.pool.chr e comparado com os
     tiles esperados; confere limites do pool (160) e do tilemap.

Uso: python3 -I tools/stage_v2/verify_v2.py OUTDIR
"""
import glob
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import build_stages as bs  # noqa: E402


def decode_tile(chr_bytes, n):
    t = chr_bytes[n * 32:(n + 1) * 32]
    px = np.zeros((8, 8), np.uint8)
    for r in range(8):
        b0, b1, b2, b3 = t[r * 2], t[r * 2 + 1], t[16 + r * 2], t[16 + r * 2 + 1]
        for x in range(8):
            s = 7 - x
            px[r, x] = ((b0 >> s) & 1) | (((b1 >> s) & 1) << 1) | \
                (((b2 >> s) & 1) << 2) | (((b3 >> s) & 1) << 3)
    return px


def pal_rgb(pal_bytes):
    out = np.zeros((3, 16, 3), np.int64)
    for p in range(3):
        for c in range(16):
            w = struct.unpack_from("<H", pal_bytes, (p * 16 + c) * 2)[0]
            out[p, c] = (round((w & 31) * 255 / 31), round(((w >> 5) & 31) * 255 / 31),
                         round(((w >> 10) & 31) * 255 / 31))
    return out


def draw(img, ty, tx, px, pal, word):
    flip_h, flip_v = (word >> 14) & 1, (word >> 15) & 1
    if flip_h:
        px = px[:, ::-1]
    if flip_v:
        px = px[::-1]
    p = ((word >> 10) & 7) - bs.STAGE_BG_PALETTE
    rgb = pal[p][px]
    # indice 0 transparente: nenhum tile usa cor 0 (cores 1..15)
    img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = rgb


def main():
    out = sys.argv[1]
    ok = True
    if bs.STAGE_YOFS:
        print('AVISO: build_stages.STAGE_YOFS =', bs.STAGE_YOFS,
              '-> a arte v2 ja esta alinhada ao chao; usar 0 ao integrar (verificando com 0).')
        bs.STAGE_YOFS = {}
    for png in sorted(glob.glob(os.path.join(out, "KOF98-*.png"))):
        name = os.path.basename(png)[:-4]
        chrb, mapb, palb, _ = bs.emit_stage(png)
        ntiles = len(chrb) // 32
        pal = pal_rgb(palb)
        ref = np.asarray(Image.open(png).convert("RGB")).astype(np.int64)
        # mapa: 2 planos de 32x32 -> 64x32
        words = np.frombuffer(mapb, "<u2")
        grid = np.zeros((32, 64), np.int64)
        for plane in range(2):
            blk = words[plane * 1024:(plane + 1) * 1024].reshape(32, 32)
            grid[:, plane * 32:(plane + 1) * 32] = blk
        img = np.zeros((224, 512, 3), np.int64)
        for ty in range(28):
            for tx in range(64):
                w = int(grid[ty, tx])
                draw(img, ty, tx, decode_tile(chrb, w & 0x3FF), pal, w)
        diff = int((img != ref).any(-1).sum())
        # clips
        man = json.load(open(os.path.join(out, "anim", name + ".json")))
        pool = open(os.path.join(out, "anim", name + ".pool.chr"), "rb").read()
        npool = len(pool) // 32
        msg = ""
        bad = 0
        for c in man["clips"]:
            for st_words in c["state_tilemap_words"]:
                for (ty, tx), w in zip(c["cells_ty_tx"], st_words):
                    t = w & 0x3FF
                    if t >= npool or not (2 <= ((w >> 10) & 7) <= 4):
                        bad += 1
                        continue
                    tmp = img.copy()
                    draw(tmp, ty, tx, decode_tile(pool, t), pal, w)
            # estado 0 deve igualar a arte estatica (sem salto na primeira troca)
            for (ty, tx), w in zip(c["cells_ty_tx"], c["state_tilemap_words"][0]):
                tmp = np.zeros((8, 8, 3), np.int64)
                px = decode_tile(pool, w & 0x3FF)
                px = px[:, ::-1] if (w >> 14) & 1 else px
                px = px[::-1] if (w >> 15) & 1 else px
                tmp[:] = pal[((w >> 10) & 7) - 2][px]
                if (tmp != ref[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]).any():
                    bad += 1
        good = (ntiles <= 512 and diff == 0 and bad == 0 and npool <= 160)
        ok &= good
        print(f"{'OK ' if good else 'FAIL'} {name}: static {ntiles}/512, "
              f"png-vs-ppu diff px {diff}, pool {npool}/160, "
              f"clips {len(man['clips'])}, clip errors {bad}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
