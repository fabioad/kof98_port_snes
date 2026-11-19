#!/usr/bin/env python3
"""Extracao das animacoes ORIGINAIS do arcade como clips de tiles do SNES.

Para cada camada [BG] animada e estatica em posicao (sem BGCtrl/sin/velocidade)
medimos que celulas 8x8 do mapa de 512x224 realmente mudam entre as poses.
Camadas cujas celulas se tocam viram um grupo; o grupo percorre os estados
conjuntos reais do arcade (com os tempos do .def, 60 ticks/s).  Cada estado
vira tiles 8x8 quantizados nas paletas do cenario.  O orcamento do pool
dinamico (160 tiles por cenario) e respeitado por fusao de tiles parecidos
e poda das celulas de menor energia visual.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import mugen_bg as mb  # noqa: E402
import source as src  # noqa: E402
import stage_requant as sr  # noqa: E402

TW, TH = sr.TW, sr.TH
PERM = sr.PERM


def lcm(a, b):
    return a * b // math.gcd(a, b)


# -------------------------------------------------------------- timeline --
def layer_clips(st):
    """camadas animadas fixas: {i: (frames[(key,dur)], total)}"""
    ctrl_ids = {i for d in st.ctrldefs for i in d["ids"]}
    out = {}
    for i, L in enumerate(st.layers):
        if L.type != "anim":
            continue
        a = st.actions.get(L.action)
        if not a or a.forever or a.total <= 0:
            continue
        # balanco leve (<=4 px, ex.: barco da China) nao conta como deslocamento
        big_sin = max([abs(v) for v in (L.sinx[:1] + L.siny[:1])] + [0]) > 4
        mover = (L.id in ctrl_ids) or any(L.vel0) or big_sin
        if mover:
            continue
        frames = [((f[0], f[1], f[2], f[3], f[5]), f[4]) for f in a.frames if f[4] > 0]
        if len({k for k, _ in frames}) < 2:
            continue
        out[i] = (frames, a.total)
    return out


def pose_at(frames, t):
    t %= sum(d for _, d in frames)
    acc = 0
    for k, d in frames:
        acc += d
        if t < acc:
            return k
    return frames[-1][0]


# -------------------------------------------------------- region imaging --
def out_lab(world_rgba):
    """world RGBA 752x240 -> OKLab float32 512x224 (sem bilateral)."""
    a = src.arcade_rgb(world_rgba)
    return sr.srgb_to_oklab(np.round(a).astype(np.int64)).astype(np.float32)


def render_variant(st, name, force, tick0=0):
    w = mb.render_world(st, tick0, force=force)
    return src.crop_rows(name, w)


def detect_cells(st, name, clips, base_force, thr=0.035, min_px=3):
    """celulas (TH,TW) bool por camada em que alguma pose difere."""
    ref_w = src.crop_rows(name, mb.render_world(st, 0, force=base_force))
    ref = out_lab(ref_w)
    masks = {}
    energy = {}
    for i, (frames, _) in clips.items():
        keys = {k for k, _ in frames}
        e = np.zeros(ref.shape[:2], np.float32)
        for k in keys:
            f = dict(base_force)
            f[i] = k
            lab = out_lab(src.crop_rows(name, mb.render_world(st, 0, force=f)))
            e = np.maximum(e, np.sqrt(((lab - ref) ** 2).sum(-1)))
        cell = (e > thr).reshape(TH, 8, TW, 8).sum((1, 3)) >= min_px
        if cell.any():
            masks[i] = cell
            energy[i] = float(e[e > thr].sum())
    return masks, energy


def group_layers(masks):
    ids = list(masks)
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a in ids:
        for b in ids:
            if a < b and (masks[a] & masks[b]).any():
                parent[find(a)] = find(b)
    groups = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def joint_states(clips, layer_ids, cap=3600):
    """timeline conjunta -> (states[tuple of keys], seq[(state_idx, ticks)])"""
    cyc = 1
    for i in layer_ids:
        cyc = lcm(cyc, clips[i][1])
        if cyc > cap:
            cyc = cap
            break
    bounds = {0, cyc}
    for i in layer_ids:
        frames, total = clips[i]
        t = 0
        while t < cyc:
            for _, d in frames:
                if t < cyc:
                    bounds.add(t)
                t += d
    bounds = sorted(b for b in bounds if b <= cyc)
    states, seq = [], []
    for a, b in zip(bounds[:-1], bounds[1:]):
        tup = tuple(pose_at(clips[i][0], a) for i in layer_ids)
        if tup not in states:
            states.append(tup)
        s = states.index(tup)
        if seq and seq[-1][0] == s:
            seq[-1][1] += b - a
        else:
            seq.append([s, b - a])
    # estado 0 = o do tick 0 (a arte estatica mostra esse)
    first = tuple(pose_at(clips[i][0], 0) for i in layer_ids)
    if first in states and states.index(first) != 0:
        k = states.index(first)
        states[0], states[k] = states[k], states[0]
        for s in seq:
            s[0] = 0 if s[0] == k else (k if s[0] == 0 else s[0])
    return states, [tuple(s) for s in seq], cyc


# ------------------------------------------------------------ quantizing --
def canon_key(idx):
    return min(idx[PERM[f]].tobytes() for f in range(4))


def tile_from(lab_cell, pal_lab):
    """(8,8,3) -> (idx64, pal, err) melhor paleta, vizinho mais proximo."""
    px = lab_cell.reshape(64, 3)
    best = None
    for p in range(len(pal_lab)):
        d = ((px[:, None] - pal_lab[p][None]) ** 2).sum(-1)
        e = d.min(1).sum()
        if best is None or e < best[2]:
            best = (d.argmin(1), p, e)
    return best


def agglomerate(tiles, weights, target, iters=12, seed=5):
    """Reduz N tiles (N,64,3) a `target` representantes reais (k-medoids
    ponderado).  Retorna rep[N] com o indice do representante."""
    n = len(tiles)
    if n <= target:
        return np.arange(n)
    X = tiles.reshape(n, -1).astype(np.float32)
    w = weights.astype(np.float64) + 1e-6
    rng = np.random.default_rng(seed)
    med = [int(rng.choice(n, p=w / w.sum()))]
    d2 = ((X - X[med[0]]) ** 2).sum(1)
    for _ in range(1, target):
        q = d2 * w
        j = int(rng.choice(n, p=q / q.sum())) if q.sum() > 0 else int(rng.integers(n))
        med.append(j)
        d2 = np.minimum(d2, ((X - X[j]) ** 2).sum(1))
    med = np.array(med)
    for _ in range(iters):
        D = np.stack([((X - X[m]) ** 2).sum(1) for m in med], 1)
        a = D.argmin(1)
        new = med.copy()
        for k in range(target):
            m = np.where(a == k)[0]
            if not len(m):
                continue
            c = (X[m] * w[m, None]).sum(0) / w[m].sum()
            new[k] = m[((X[m] - c) ** 2).sum(1).argmin()]
        if (new == med).all():
            break
        med = new
    D = np.stack([((X - X[m]) ** 2).sum(1) for m in med], 1)
    return med[D.argmin(1)]


def group_tiles(states_lab, cells, pal_lab, budget, cell_cap=0.085,
                min_tiles_per_cell=0.9):
    """Quantiza os estados de um grupo em tiles 4bpp respeitando `budget`.

    states_lab: lista [S] de imagens OKLab 512x224 (estado 0 = arte estatica)
    cells: [(ty,tx)] celulas candidatas.
    A fusao de tiles parecidos nunca pode produzir um tile "estranho": toda
    celula cujo pior estado fique com erro por pixel (OKLab RMS) acima de
    `cell_cap` e podada (fica como arte estatica), junto com as de menor
    energia visual enquanto o orcamento nao fechar.

    Retorna dict(keep, patterns (M,64), entries{(s,cell):(tile,flip,pal)},
    energy, err)."""
    S = len(states_lab)
    en = {}
    for (ty, tx) in cells:
        blk = np.stack([L[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] for L in states_lab])
        en[(ty, tx)] = float(np.sqrt(((blk - blk.mean(0)) ** 2).sum(-1)).mean())
    keep = sorted(cells, key=lambda c: -en[c])
    cache = {}
    while True:
        pats, first_pal, order, ent = {}, [], [], {}
        for s in range(S):
            for c in keep:
                if (s, c) not in cache:
                    ty, tx = c
                    cell = states_lab[s][ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                    idx, p, _ = tile_from(cell, pal_lab)
                    cache[(s, c)] = (idx, p, cell, canon_key(idx))
                idx, p, cell, key = cache[(s, c)]
                if key not in pats:
                    pats[key] = len(order)
                    order.append(np.frombuffer(key, dtype=idx.dtype).copy())
                    first_pal.append(p)
                ent[(s, c)] = (pats[key], idx, p, cell)
        n = len(order)
        if not keep:
            P = np.zeros((0, 64), np.int64)
            rep = np.arange(0)
            break
        P = np.array(order, np.int64)
        if n <= budget:
            rep = np.arange(n)
        else:
            dec = np.stack([pal_lab[first_pal[k]][P[k]] for k in range(n)]).astype(np.float32)
            w = np.zeros(n)
            for (_, _), (t, _, _, _) in ent.items():
                w[t] += 1
            rep = agglomerate(dec, w, budget)
        # erro por celula depois da fusao (melhor flip, paleta propria)
        cell_err = {c: 0.0 for c in keep}
        for (s, c), (t, idx, p, cell) in ent.items():
            pat = P[int(rep[t])]
            e = min(float(((pal_lab[p][pat[PERM[f]]] - cell.reshape(64, 3)) ** 2)
                          .sum(-1).mean()) for f in range(4))
            cell_err[c] = max(cell_err[c], e ** 0.5)
        bad = [c for c in keep if cell_err[c] > cell_cap]
        # fusao pesada (menos de ~1 tile por celula) le como blocos: poda
        n_used = len(set(int(v) for v in rep))
        if not bad and n_used < min_tiles_per_cell * len(keep):
            keep = keep[:max(4, int(n_used / min_tiles_per_cell))]
            continue
        if not bad:
            break
        keep = [c for c in keep if c not in set(bad)]
    uniq = sorted(set(int(x) for x in rep))
    nid = {u: k for k, u in enumerate(uniq)}
    patterns = P[uniq] if len(uniq) else P
    entries = {}
    for (s, c), (t, idx, p, cell) in ent.items():
        r = int(rep[t])
        pat = P[r]
        best = None
        for f in range(4):
            e = float(((pal_lab[p][pat[PERM[f]]] - cell.reshape(64, 3)) ** 2).sum())
            if best is None or e < best[0]:
                best = (e, f)
        entries[(s, c)] = (nid[r], best[1], p)
    return {"keep": keep, "patterns": patterns.astype(np.uint8), "entries": entries,
            "energy": en, "err": cell_err if keep else {}}
