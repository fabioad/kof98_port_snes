#!/usr/bin/env python3
"""Tiras de quadros de cada clip, decodificadas como o PPU faria.

Le apenas o PNG estatico, anim/<stage>.json e anim/<stage>.pool.chr: compoe
cada estado do clip sobre a arte e recorta a regiao animada, gerando
preview/anim_<stage>_<clip>.png (estados lado a lado, 2x) e um indice
preview/anim_index.png.

Uso: python3 -I tools/stage_v2/anim_sheet.py OUTDIR [STAGE ...]
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verify_v2 import decode_tile  # noqa: E402


def load_stage(out, name):
    png = Image.open(os.path.join(out, name + ".png"))
    idx = np.asarray(png).astype(np.int64)
    pal = np.array(png.getpalette()).reshape(-1, 3)[:45]
    pool = open(os.path.join(out, "anim", name + ".pool.chr"), "rb").read()
    man = json.load(open(os.path.join(out, "anim", name + ".json")))
    return idx, pal, pool, man


def compose(idx, pal, pool, clip, state):
    img = pal[idx]        # RGB 224x512x3
    for (ty, tx), w in zip(clip["cells_ty_tx"], clip["state_tilemap_words"][state]):
        px = decode_tile(pool, w & 0x3FF)
        if (w >> 14) & 1:
            px = px[:, ::-1]
        if (w >> 15) & 1:
            px = px[::-1]
        p = ((w >> 10) & 7) - 2
        # tile guarda a cor como c+1 (0 = transparente)
        img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = pal[p * 15 + np.maximum(px - 1, 0)]
    return img


def main():
    out = os.path.abspath(sys.argv[1])
    names = sys.argv[2:] or sorted(os.path.basename(p[:-4]) for p in
                                   glob.glob(os.path.join(out, "KOF98-*.png")))
    index = []
    for name in names:
        idx, pal, pool, man = load_stage(out, name)
        for k, clip in enumerate(man["clips"]):
            ys = [c[0] for c in clip["cells_ty_tx"]]
            xs = [c[1] for c in clip["cells_ty_tx"]]
            y0, y1 = max(0, min(ys) * 8 - 8), min(224, (max(ys) + 1) * 8 + 8)
            x0, x1 = max(0, min(xs) * 8 - 8), min(512, (max(xs) + 1) * 8 + 8)
            frames = [Image.fromarray(compose(idx, pal, pool, clip, s)[y0:y1, x0:x1]
                                      .astype(np.uint8))
                      for s in range(len(clip["state_tilemap_words"]))]
            z = 2 if (x1 - x0) <= 200 else 1
            w, h = (x1 - x0) * z, (y1 - y0) * z
            sheet = Image.new("RGB", (len(frames) * (w + 4), h + 16), (18, 18, 18))
            d = ImageDraw.Draw(sheet)
            for i, f in enumerate(frames):
                sheet.paste(f.resize((w, h), Image.NEAREST), (i * (w + 4), 14))
                d.text((i * (w + 4) + 3, 2), f"estado {i}", fill=(255, 220, 80))
            d.text((3, h + 4), f"{name} · {clip['id']} · células x{len(ys)} · "
                              f"{len(frames)} estados · ciclo {clip['cycle_ticks']/60:.2f}s",
                   fill=(200, 200, 200))
            fn = f"anim_{name}_{k}.png"
            sheet.save(os.path.join(out, "preview", fn))
            index.append((name, k, fn, len(frames), clip["cycle_ticks"] / 60.0,
                          len(clip["cells_ty_tx"]), x0, y0, x1 - x0, y1 - y0))
    # indice: uma miniatura (estado 0) por clip, em grade
    cols = 4
    cell_w, cell_h = 200, 74
    rows = (len(index) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell_w + 8), rows * (cell_h + 30) + 4), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    for i, (name, k, fn, nst, cyc, ncell, x0, y0, w, h) in enumerate(index):
        im = Image.open(os.path.join(out, "preview", fn)).convert("RGB")
        im.thumbnail((cell_w, cell_h))
        x, y = (i % cols) * (cell_w + 8), (i // cols) * (cell_h + 30) + 4
        sheet.paste(im, (x, y + 12))
        d.text((x + 2, y), f"{name.replace('KOF98-','')} clip{k}", fill=(255, 220, 80))
        d.text((x + 2, y + 12 + im.size[1] + 1),
               f"{nst} est · {cyc:.1f}s · {ncell} cel · ({x0},{y0})",
               fill=(190, 190, 190))
    sheet.save(os.path.join(out, "preview", "anim_index.png"))
    print(f"{len(index)} clips -> preview/anim_*.png + preview/anim_index.png")


if __name__ == "__main__":
    main()
