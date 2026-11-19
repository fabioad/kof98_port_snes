#!/usr/bin/env python3
"""Reconstroi os 10 stages KOF98-* a partir do arcade (MUGEN) para o SNES.

Saida (diretorio separado, nao toca assets/stages/stages_png_snes):

  <out>/KOF98-X.png            512x224 indexado, 3x15 cores, <=512 tiles
                               (mesmo formato lido por tools/build_stages.py)
  <out>/anim/KOF98-X.json      clips de animacao do arcade (celulas/tiles/tempos)
  <out>/anim/KOF98-X.pool.chr  tiles 4bpp do pool dinamico do cenario
  <out>/preview/...            capturas decodificadas, comparativos e GIFs
  <out>/metrics.json

Uso:  python3 -I tools/stage_v2/build_v2.py OUTDIR [STAGE ...] [--no-gif]
"""
import glob
import json
import os
import struct
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import anim as A  # noqa: E402
import metrics as M  # noqa: E402
import mugen_bg as mb  # noqa: E402
import quant as Q  # noqa: E402
import source as S  # noqa: E402
import stage_requant as sr  # noqa: E402

MAX_GROUP_LAYERS = 4
MAX_PRE_STATES = 24
DYN_BUDGET = 160            # tiles do pool dinamico por cenario
STATIC_BUDGET = 512
PERM = sr.PERM
TW, TH = sr.TW, sr.TH
BIL_SIGMA, BIL_ITERS = 0.06, 2


def encode4bpp(idx64):
    """64 indices 0..14 (cor c -> valor c+1) -> 32 bytes SNES planar."""
    px = (np.asarray(idx64).reshape(8, 8) + 1).astype(np.uint8)
    out = bytearray()
    for planes in ((0, 1), (2, 3)):
        for r in range(8):
            lo = hi = 0
            for x in range(8):
                v = int(px[r, x])
                lo |= ((v >> planes[0]) & 1) << (7 - x)
                hi |= ((v >> planes[1]) & 1) << (7 - x)
            out += bytes((lo, hi))
    return bytes(out)


def water_fill(demand, weight, total):
    """reparte `total` entre grupos limitado pela demanda de cada um."""
    n = len(demand)
    alloc = [0] * n
    left = total
    active = [i for i in range(n) if demand[i] > 0]
    while active and left > 0:
        wsum = sum(weight[i] for i in active)
        done = []
        for i in active:
            share = max(1, int(left * weight[i] / wsum))
            if alloc[i] + share >= demand[i]:
                done.append(i)
        if not done:
            for i in active:
                alloc[i] += max(1, int(left * weight[i] / wsum))
            break
        for i in done:
            left -= demand[i] - alloc[i]
            alloc[i] = demand[i]
            active.remove(i)
    return alloc


def decode_rgb(idx_img, pal_rgb):
    return pal_rgb.reshape(-1, 3)[idx_img].astype(np.uint8)


def build_stage(name, out, gif=True, log=print):
    t0 = time.time()
    st = mb.Stage(os.path.join(S.STAGES, name))
    world0 = mb.render_world(st, 0)
    src_rgb = S.arcade_rgb(S.crop_rows(name, world0))
    lab0 = sr.srgb_to_oklab(np.round(src_rgb).astype(np.int64)).astype(np.float32)
    lab = S.bilateral_lab(lab0, sigma_r=BIL_SIGMA, iters=BIL_ITERS)

    # ---------------- animacoes do arcade -> grupos de celulas ------------
    clips = A.layer_clips(st)
    masks, lay_energy = A.detect_cells(st, name, clips, {}) if clips else ({}, {})
    groups = []
    skipped_layers = []
    for ids in A.group_layers(masks) if masks else []:
        # no maximo 4 camadas por grupo (as de maior energia): os estados
        # conjuntos crescem com o produto dos ciclos
        if len(ids) > MAX_GROUP_LAYERS:
            ids = sorted(ids, key=lambda i: -lay_energy[i])
            skipped_layers += ids[MAX_GROUP_LAYERS:]
            ids = sorted(ids[:MAX_GROUP_LAYERS])
        cells = np.zeros((TH, TW), bool)
        for i in ids:
            cells |= masks[i]
        states, seq, cyc = A.joint_states(clips, ids)
        if len(states) < 2:
            continue
        if len(states) > MAX_PRE_STATES:
            states, seq = _presample(states, seq)
        groups.append({"layers": ids, "cells": cells, "states": states,
                       "seq": seq, "cycle": cyc})
    # imagens de cada estado (OKLab suavizado so na regiao do grupo)
    for g in groups:
        ys, xs = np.where(g["cells"])
        y0, y1 = max(0, ys.min() * 8 - 4), min(224, ys.max() * 8 + 12)
        x0, x1 = max(0, xs.min() * 8 - 4), min(512, xs.max() * 8 + 12)
        imgs = []
        for tup in g["states"]:
            force = {i: k for i, k in zip(g["layers"], tup)}
            lab_s = A.out_lab(A.src.crop_rows(name, mb.render_world(st, 0, force=force)))
            full = lab.copy()
            full[y0:y1, x0:x1] = S.bilateral_lab(
                lab_s[y0:y1, x0:x1], sigma_r=BIL_SIGMA, iters=BIL_ITERS)
            imgs.append(full)
        g["imgs"] = imgs
        g["cell_list"] = [(int(y), int(x)) for y, x in zip(ys, xs)]
        # reduz estados demais (ex.: 69 poses de um letreiro) a no maximo 6
        if len(g["states"]) > 6:
            _reduce_states(g)
    # ---------------- paletas (incluem os pixels das poses) ---------------
    lab_t = sr.tiles_of(lab)
    ex_px, ex_w = [], []
    for g in groups:
        for s in range(1, len(g["imgs"])):
            for (ty, tx) in g["cell_list"]:
                ex_px.append(g["imgs"][s][ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].reshape(-1, 3))
    extra = None
    if ex_px:
        ex = np.concatenate(ex_px)
        extra = (ex.astype(np.float32), np.full(len(ex), 0.5))
    pal_lab, pal_rgb, grp = Q.design_palettes(lab_t, Q.hud_weights(), extra=extra)

    # ---------------- tiles de cada grupo, com orcamento ------------------
    for g in groups:
        g["res_full"] = A.group_tiles(g["imgs"], g["cell_list"], pal_lab, 10 ** 6)
        g["demand"] = len(g["res_full"]["patterns"])
        g["energy"] = sum(g["res_full"]["energy"].values())
    alloc = water_fill([g["demand"] for g in groups],
                       [max(g["energy"], 1e-6) for g in groups], DYN_BUDGET)
    for g, b in zip(groups, alloc):
        g["budget"] = b
        g["res"] = g["res_full"] if g["demand"] <= b else \
            A.group_tiles(g["imgs"], g["cell_list"], pal_lab, max(b, 1))
    # orcamento ocioso (podas por erro) volta para os proprios grupos
    for _ in range(2):
        used = sum(len(g["res"]["patterns"]) for g in groups)
        spare = DYN_BUDGET - used
        if spare <= 0:
            break
        grew = False
        for g in groups:
            if len(g["res"]["keep"]) < len(g["cell_list"]) and \
                    len(g["res"]["patterns"]) < g["demand"]:
                nb = min(g["demand"], len(g["res"]["patterns"]) + spare)
                if nb > len(g["res"]["patterns"]):
                    r = A.group_tiles(g["imgs"], g["cell_list"], pal_lab, nb)
                    if len(r["patterns"]) > len(g["res"]["patterns"]) and \
                            len(r["keep"]) >= len(g["res"]["keep"]):
                        spare -= len(r["patterns"]) - len(g["res"]["patterns"])
                        g["res"] = r
                        grew = True
        if not grew:
            break
    groups = [g for g in groups if len(g["res"]["keep"]) and g["budget"] > 0]
    pool_tiles = sum(len(g["res"]["patterns"]) for g in groups)

    # ---------------- arte estatica: orcamento 512 ------------------------
    anim_cells = np.zeros(sr.NT, bool)
    n0 = 0
    seen = set()
    for g in groups:
        for c in g["res"]["keep"]:
            anim_cells[c[0] * TW + c[1]] = True
            t, f, p = g["res"]["entries"][(0, c)]
            seen.add(A.canon_key(g["res"]["patterns"][t].astype(np.int64)))
    n0 = len(seen)
    tile_w = Q.position_weights(lab)
    tile_w[anim_cells] = 0.02
    K = STATIC_BUDGET - n0
    sr.LAMBDA = 3.0
    for attempt in range(4):
        med, arg, _ = sr.reduce_tiles(lab_t, pal_lab, k=K, weights=tile_w, seed=3)
        img = sr.compose(med, arg, pal_rgb)
        idx = np.asarray(img).astype(np.int64).copy()
        for g in groups:
            for c in g["res"]["keep"]:
                t, f, p = g["res"]["entries"][(0, c)]
                pat = g["res"]["patterns"][t].astype(np.int64)[PERM[f]].reshape(8, 8)
                idx[c[0] * 8:c[0] * 8 + 8, c[1] * 8:c[1] * 8 + 8] = p * 15 + pat
        n = sr.count_tiles(Image.fromarray(idx.astype(np.uint8), "P"))
        if n <= STATIC_BUDGET:
            break
        K -= (n - STATIC_BUDGET) + 2
    final = Image.fromarray(idx.astype(np.uint8), "P")
    final.putpalette([int(v) for v in pal_rgb.reshape(-1)] + [0] * (768 - pal_rgb.size))
    os.makedirs(os.path.join(out, "anim"), exist_ok=True)
    os.makedirs(os.path.join(out, "preview"), exist_ok=True)
    final.save(os.path.join(out, name + ".png"), optimize=True)

    # ---------------- validacao com o conversor real do jogo -------------
    import build_stages as bs
    chrb, mapb, palb, _ = bs.emit_stage(os.path.join(out, name + ".png"))
    static_tiles = len(chrb) // 32

    # ---------------- manifesto de animacao + pool.chr -------------------
    pool_chr = bytearray()
    clips_json = []
    base = 0
    for gi, g in enumerate(groups):
        r = g["res"]
        for pat in r["patterns"]:
            pool_chr += encode4bpp(pat)
        cells = sorted(r["keep"])
        states = []
        for s in range(len(g["states"])):
            ws = []
            for c in cells:
                t, f, p = r["entries"][(s, c)]
                ws.append(int((base + t) | ((2 + p) << 10) | A_FLIP[f]))
            states.append(ws)
        base += len(r["patterns"])
        clips_json.append({
            "id": f"{name}_clip{gi}",
            "arcade_layers": [{"bg_index": i, "name": st.layers[i].name,
                               "action": st.layers[i].action} for i in g["layers"]],
            "cells_ty_tx": [[int(y), int(x)] for y, x in cells],
            "pool_tiles": int(len(r["patterns"])),
            "pool_tile_base": int(base - len(r["patterns"])),
            "cycle_ticks": int(g["cycle"]),
            "sequence_state_ticks": [[int(a), int(b)] for a, b in g["seq"]],
            "state_tilemap_words": states,
            "note": "words = pool tile (relativo a base do pool) | (2+pal)<<10 | flip<<14",
        })
    with open(os.path.join(out, "anim", name + ".pool.chr"), "wb") as f:
        f.write(bytes(pool_chr))
    movers = movers_report(st)
    man = {"stage": name, "tick_rate": 60, "static_tiles": static_tiles,
           "pool_tiles": pool_tiles, "pool_budget": DYN_BUDGET,
           "dropped_layers": dropped_report(st, clips, masks, groups, skipped_layers),
           "clips": clips_json, "movers_not_in_tiles": movers}
    with open(os.path.join(out, "anim", name + ".json"), "w") as f:
        json.dump(man, f, indent=1, ensure_ascii=False)

    # ---------------- metricas e previas --------------------------------
    dec = decode_rgb(idx, pal_rgb)
    rec = sr.srgb_to_oklab(dec.astype(np.int64))
    nb = _nobudget(lab_t, pal_lab, pal_rgb)
    met = {"static_tiles": static_tiles, "pool_tiles": pool_tiles,
           "clips": len(groups),
           "pix_rmse": M.pix_rmse(rec, lab0), "blur_rmse": M.blur_rmse(rec, lab0),
           "block_rmse": M.blockiness(rec, lab0),
           "palette_only_pix": nb[0], "palette_only_blur": nb[1],
           "seconds": round(time.time() - t0, 1)}
    Image.fromarray(dec).save(os.path.join(out, "preview", name + "_snes.png"))
    Image.fromarray(np.round(src_rgb).astype(np.uint8)).save(
        os.path.join(out, "preview", name + "_arcade.png"))
    compare(name, out, src_rgb, dec)
    if gif:
        make_gif(name, out, st, dec, pal_rgb, groups)
    log(f"{name}: static {static_tiles}/512  pool {pool_tiles}/{DYN_BUDGET}  "
        f"clips {len(groups)}  pix {met['pix_rmse']:.4f} blur {met['blur_rmse']:.4f}  "
        f"({met['seconds']}s)")
    return met


A_FLIP = [0, 0x4000, 0x8000, 0xC000]


def _nobudget(lab_t, pal_lab, pal_rgb):
    D = np.stack([((lab_t[:, :, None, :] - pal_lab[p][None, None]) ** 2).sum(-1)
                  for p in range(len(pal_lab))])
    bp = D.min(-1).sum(-1).argmin(0)
    q = D[bp, np.arange(len(lab_t))].argmin(-1)
    rec = sr.srgb_to_oklab(sr.untile(pal_rgb[bp[:, None], q]).astype(np.int64))
    lab = sr.untile(lab_t)
    return M.pix_rmse(rec, lab), M.blur_rmse(rec, lab)


def _presample(states, seq, keep=MAX_PRE_STATES):
    """Antes de renderizar: limita os estados a `keep` (amostragem
    uniforme na ordem de aparicao; o estado 0 fica)."""
    n = len(states)
    pick = sorted({0} | {int(round(i * (n - 1) / (keep - 1))) for i in range(keep)})
    remap = {}
    for s in range(n):
        remap[s] = min(pick, key=lambda p: (abs(p - s), p))
    new_idx = {p: k for k, p in enumerate(pick)}
    out = []
    for s, t in seq:
        j = new_idx[remap[s]]
        if out and out[-1][0] == j:
            out[-1][1] += t
        else:
            out.append([j, t])
    return [states[p] for p in pick], [tuple(x) for x in out]


def _reduce_states(g, k=6):
    """k-medoids sobre os estados (distancia = erro OKLab na regiao)."""
    cells = g["cell_list"]
    feats = np.stack([np.concatenate([im[c[0] * 8:c[0] * 8 + 8, c[1] * 8:c[1] * 8 + 8].ravel()
                                      for c in cells]) for im in g["imgs"]])
    n = len(feats)
    d = ((feats[:, None] - feats[None]) ** 2).sum(-1)
    med = [0]                                        # estado 0 fixo
    while len(med) < k:
        dm = d[:, med].min(1)
        med.append(int(dm.argmax()))
    for _ in range(8):
        a = d[:, med].argmin(1)
        for j in range(1, k):
            m = np.where(a == j)[0]
            if len(m):
                med[j] = int(m[d[np.ix_(m, m)].sum(1).argmin()])
    a = d[:, med].argmin(1)
    new_states = [g["states"][m] for m in med]
    new_imgs = [g["imgs"][m] for m in med]
    seq = []
    for s, t in g["seq"]:
        j = int(a[s])
        if seq and seq[-1][0] == j:
            seq[-1][1] += t
        else:
            seq.append([j, t])
    g["states"], g["imgs"], g["seq"] = new_states, new_imgs, [tuple(x) for x in seq]


def movers_report(st):
    ctrl_ids = {i for d in st.ctrldefs for i in d["ids"]}
    out = []
    for i, L in enumerate(st.layers):
        big_sin = max([abs(v) for v in (L.sinx[:1] + L.siny[:1])] + [0]) > 4
        if not ((L.id in ctrl_ids) or any(L.vel0) or big_sin):
            continue
        a = st.actions.get(L.action)
        out.append({"bg_index": i, "name": L.name, "action": L.action,
                    "poses": len({(f[0], f[1]) for f in a.frames}) if a else 0,
                    "kind": ("sin" if (any(L.sinx) or any(L.siny)) else
                             "velocity" if any(L.vel0) else "bgctrl")})
    return out


def dropped_report(st, clips, masks, groups, skipped_layers):
    used = {i for g in groups for i in g["layers"]}
    return [{"bg_index": i, "name": st.layers[i].name, "action": st.layers[i].action,
             "reason": "sem mudanca visivel" if i not in masks else
             "fora do orcamento/estados"} for i in clips if i not in used]


def compare(name, out, src_rgb, dec):
    a = np.round(src_rgb).astype(np.uint8)
    old_path = os.path.join(S.STAGES, "stages_png_snes", name + ".png")
    old = np.asarray(Image.open(old_path).convert("RGB"))
    sheet = Image.new("RGB", (512, 224 * 3 + 8), (20, 20, 20))
    sheet.paste(Image.fromarray(a), (0, 0))
    sheet.paste(Image.fromarray(old), (0, 228))
    sheet.paste(Image.fromarray(dec), (0, 456))
    sheet.save(os.path.join(out, "preview", name + "_compare.png"))


def make_gif(name, out, st, dec, pal_rgb, groups, step=6, maxframes=48):
    cyc = max([g["cycle"] for g in groups] + [1])
    ticks = list(range(0, min(max(cyc, 120), step * maxframes), step))
    frames = []
    for t in ticks:
        w = A.src.crop_rows(name, mb.render_world(st, t))
        arc = np.round(S.arcade_rgb(w)).astype(np.uint8)
        snes = dec.copy()
        for g in groups:
            tt = t % g["cycle"]
            acc, s = 0, g["seq"][-1][0]
            for sidx, d in g["seq"]:
                acc += d
                if tt < acc:
                    s = sidx
                    break
            r = g["res"]
            for c in r["keep"]:
                tile, f, p = r["entries"][(s, c)]
                pat = r["patterns"][tile].astype(np.int64)[PERM[f]].reshape(8, 8)
                snes[c[0] * 8:c[0] * 8 + 8, c[1] * 8:c[1] * 8 + 8] = \
                    pal_rgb[p][pat].astype(np.uint8)
        frames.append(Image.fromarray(np.concatenate([arc, snes], 1)))
    frames[0].save(os.path.join(out, "preview", name + ".gif"), save_all=True,
                   append_images=frames[1:], duration=int(step * 1000 / 60),
                   loop=0, optimize=False)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = os.path.abspath(args[0])
    names = args[1:] or sorted(os.path.basename(f)[:-4]
                               for f in glob.glob(os.path.join(S.STAGES, "KOF98-*.def")))
    os.makedirs(out, exist_ok=True)
    allm = {}
    mp = os.path.join(out, "metrics.json")
    if os.path.exists(mp):
        allm = json.load(open(mp))
    for n in names:
        allm[n] = build_stage(n, out, gif="--no-gif" not in sys.argv)
        json.dump(allm, open(mp, "w"), indent=1)


if __name__ == "__main__":
    main()
