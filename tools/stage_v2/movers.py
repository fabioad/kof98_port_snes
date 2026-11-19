#!/usr/bin/env python3
"""Exporta os elementos que SE DESLOCAM no arcade (aves, gato, vaga-lumes,
pessoas caminhando) como folhas de poses RGBA reduzidas + movimento original.

Eles nao entram nos clips de tiles (a celula mudaria a cada tick); servem de
base para sprites OBJ numa etapa futura.  Nada aqui e usado pela ROM.
Uso: movers.py OUTDIR [STAGE ...]
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mugen_bg as mb  # noqa: E402
import source as S  # noqa: E402

XS = 512 / 752.0


def scaled_sprite(st, key, trans=True):
    g, n = key[0], key[1]
    sp = st.spr.get((g, n))
    if sp is None or sp.pix is None:
        return None
    rgba = st.sprite_rgba(sp, 1)
    if rgba is None:
        return None
    w = max(1, int(round(sp.w * XS)))
    pm = rgba.astype(np.float32)
    a = pm[..., 3:4] / 255.0
    pm[..., :3] = S.srgb_to_lin(pm[..., :3]) * a
    chans = []
    for c in range(4):
        ch = pm[..., c] if c < 3 else pm[..., 3] / 255.0
        im = Image.fromarray(ch.astype(np.float32), "F").resize((w, sp.h), Image.LANCZOS)
        chans.append(np.asarray(im))
    alpha = np.clip(chans[3], 0, 1)
    rgb = np.where(alpha[..., None] > 1e-3, np.stack(chans[:3], -1) / np.maximum(alpha[..., None], 1e-3), 0)
    out = np.zeros((sp.h, w, 4), np.uint8)
    out[..., :3] = np.round(S.lin_to_srgb(rgb)).astype(np.uint8)
    out[..., 3] = np.where(alpha > 0.5, 255, 0)
    return out, int(round(sp.ax * XS)), sp.ay


def export(name, outdir):
    st = mb.Stage(os.path.join(S.STAGES, name))
    ctrl = {}
    for d in st.ctrldefs:
        for i in d["ids"]:
            ctrl.setdefault(i, []).append(d)
    res = []
    for i, L in enumerate(st.layers):
        big_sin = max([abs(v) for v in (L.sinx[:1] + L.siny[:1])] + [0]) > 4
        moving = (L.id in ctrl) or any(L.vel0) or big_sin
        if not moving:
            continue
        keys = []
        acts = {L.action}
        for d in ctrl.get(L.id, []):
            for c in d["ctrls"]:
                if c.get("type", "").lower() == "anim":
                    acts.add(int(float(c["value"])))
        for a_id in sorted(acts):
            a = st.actions.get(a_id)
            if not a:
                continue
            for f in a.frames:
                k = (f[0], f[1])
                if k not in keys:
                    keys.append(k)
        sprites = [scaled_sprite(st, k) for k in keys]
        sprites = [(k, s) for k, s in zip(keys, sprites) if s]
        if not sprites:
            continue
        W = sum(s[0].shape[1] + 2 for _, s in sprites)
        Hh = max(s[0].shape[0] for _, s in sprites)
        sheet = np.zeros((Hh, W, 4), np.uint8)
        x = 0
        meta = []
        for k, (img, ax, ay) in sprites:
            sheet[:img.shape[0], x:x + img.shape[1]] = img
            meta.append({"sprite": list(k), "x": x, "w": int(img.shape[1]),
                         "h": int(img.shape[0]), "axis": [ax, ay]})
            x += img.shape[1] + 2
        stem = f"{name}_bg{i}"
        os.makedirs(os.path.join(outdir, "movers"), exist_ok=True)
        Image.fromarray(sheet).save(os.path.join(outdir, "movers", stem + ".png"))
        res.append({"sheet": f"movers/{stem}.png", "bg_index": i, "name": L.name,
                    "start": L.start, "delta": L.delta, "velocity": L.vel0,
                    "sin_x": L.sinx, "sin_y": L.siny, "layerno": L.layerno,
                    "actions": {str(a): [[f[0], f[1], f[4]] for f in st.actions[a].frames]
                                for a in sorted(acts) if a in st.actions},
                    "bgctrl": [{"time": c.get("time"), "type": c.get("type"),
                                "x": c.get("x"), "y": c.get("y"), "value": c.get("value"),
                                "loop_ticks": d["loop"]}
                               for d in ctrl.get(L.id, []) for c in d["ctrls"]],
                    "poses": meta, "scale_x": XS})
    json.dump(res, open(os.path.join(outdir, "anim", name + ".movers.json"), "w"),
              indent=1, ensure_ascii=False)
    return len(res)


if __name__ == "__main__":
    out = os.path.abspath(sys.argv[1])
    names = sys.argv[2:] or sorted(os.path.basename(f)[:-4]
                                   for f in glob.glob(os.path.join(S.STAGES, "KOF98-*.def")))
    for n in names:
        print(n, export(n, out))
