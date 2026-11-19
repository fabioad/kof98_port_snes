#!/usr/bin/env python3
"""Reducao SNES v2: 3 paletas x 15 cores, <=512 tiles 8x8 (com flips).

Diferencas para tools/stage_requant.py:

  * fonte = renderizacao do arcade (mugen_bg), nao a arte redesenhada;
  * paletas desenhadas sobre cores unicas ponderadas (k-means ponderado em
    OKLab, agrupamento de tiles com coerencia espacial);
  * pesos por posicao: areas sob o HUD pesam menos, bordas pesam mais;
  * depois do k-medoids, um passo MRF/ICM escolhe, para cada posicao, entre
    os melhores candidatos (medoide, flip, paleta) o que minimiza erro de
    pixel + descontinuidade nas bordas entre tiles vizinhas em relacao a
    fonte.  Isso ataca os "quadrados" visiveis, que vem de bordas de tile
    que nao se emendam, nao do erro medio.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import stage_requant as sr  # noqa: E402

NPAL, NCOL, MAX_TILES = sr.NPAL, sr.NCOL, sr.MAX_TILES
W, H, TW, TH, NT = sr.W, sr.H, sr.TW, sr.TH, sr.NT
PERM = sr.PERM


# ------------------------------------------------------------- weights --
def hud_weights(hud_top=4, hud_bot=3, hud_w=0.45):
    row = np.repeat(np.arange(TH), TW)
    w = np.ones(NT, np.float32)
    w[row < hud_top] = hud_w
    w[row >= TH - hud_bot] = hud_w
    return w


def position_weights(lab, hud_top=4, hud_bot=3, hud_w=0.45):
    """Peso por tile: linhas cobertas pelo HUD pesam menos; bordas mais."""
    t = sr.tiles_of(lab)
    # saliencia: variancia local (detalhe) em escala suave
    var = t.var(1).sum(-1)
    sal = 1.0 + 1.5 * np.clip(var / (np.percentile(var, 90) + 1e-9), 0, 1)
    row = np.repeat(np.arange(TH), TW)
    w = np.ones(NT, np.float32)
    w[row < hud_top] = hud_w
    w[row >= TH - hud_bot] = hud_w
    return (w * sal).astype(np.float32)


# ------------------------------------------------------------ palettes --
def wkmeans(pts, wts, k, iters=30, seed=1):
    """k-means++ / Lloyd ponderado em (N,3)."""
    rng = np.random.default_rng(seed)
    n = len(pts)
    if n <= k:
        return np.concatenate([pts, np.repeat(pts[:1], k - n, 0)])
    p = wts / wts.sum()
    cent = [pts[rng.choice(n, p=p)]]
    d2 = ((pts - cent[0]) ** 2).sum(1)
    for _ in range(1, k):
        q = d2 * wts
        if q.sum() <= 0:
            q = wts
        cent.append(pts[rng.choice(n, p=q / q.sum())])
        d2 = np.minimum(d2, ((pts - cent[-1]) ** 2).sum(1))
    cent = np.array(cent)
    for _ in range(iters):
        a = ((pts[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            m = a == j
            if m.any():
                cent[j] = (pts[m] * wts[m, None]).sum(0) / wts[m].sum()
    return cent


def design_palettes(lab_t, tile_w, rounds=10, extra=None, seed=7):
    """lab_t (NT,64,3) -> pal_lab (3,15,3), pal_rgb, grupo (NT,).

    `extra` = (lab_px (N,3), weight (N,)) pixels adicionais (poses de
    animacao) que a paleta tambem precisa cobrir."""
    means = lab_t.mean(1)
    std = lab_t.std(1)
    row = (np.arange(NT) // TW) / TH
    feat = np.concatenate([means, 0.5 * std, 0.12 * row[:, None]], 1)
    cent = sr.kmeans(feat, NPAL, seed=seed)
    grp = ((feat[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
    pal_lab = np.zeros((NPAL, NCOL, 3), np.float32)
    pal_rgb = np.zeros((NPAL, NCOL, 3), np.int64)
    # cores unicas (RGB555) por tile para o k-means ponderado ficar barato
    pix = lab_t.reshape(-1, 3)
    pw = np.repeat(tile_w, 64)
    err = np.zeros(NT)
    ex_lab = ex_w = None
    if extra is not None:
        ex_lab, ex_w = extra
    for r in range(rounds):
        for p in range(NPAL):
            sel = grp == p
            if not sel.any():
                sel = np.zeros(NT, bool)
                sel[np.argsort(-err)[:64]] = True
            pts = lab_t[sel].reshape(-1, 3)
            wts = np.repeat(tile_w[sel], 64)
            if ex_lab is not None:
                # pixels extras entram na paleta onde ficam mais perto
                d = ((ex_lab[:, None] - pal_lab[None, :, :, :].reshape(1, -1, 3)) ** 2
                     ).sum(-1).min(1) if r else np.zeros(len(ex_lab))
                near = np.full(len(ex_lab), p) if r == 0 else (
                    ((ex_lab[:, None] - pal_lab.reshape(1, -1, 3)) ** 2)
                    .sum(-1).argmin(1) // NCOL)
                m = near == p
                pts = np.concatenate([pts, ex_lab[m]])
                wts = np.concatenate([wts, ex_w[m]])
            # reduz a cores unicas aproximadas (grade fina em OKLab)
            key = np.round(pts / 0.004).astype(np.int64)
            uk, inv = np.unique(key, axis=0, return_inverse=True)
            inv = inv.ravel()
            cnt = np.bincount(inv, weights=wts)
            ssum = np.stack([np.bincount(inv, weights=pts[:, c] * wts)
                             for c in range(3)], 1)
            up = (ssum / cnt[:, None]).astype(np.float32)
            c = wkmeans(up, cnt.astype(np.float64), NCOL, seed=11 + p + r)
            pal_rgb[p], pal_lab[p] = sr.snap555(c)
        e = np.stack([_tile_err(lab_t, pal_lab[p], tile_w) for p in range(NPAL)], 1)
        grp = e.argmin(1)
        err = e.min(1)
    return pal_lab, pal_rgb, grp


def _tile_err(lab_t, pal, w):
    d = ((lab_t[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
    return d.min(-1).sum(-1) * w


# ------------------------------------------------- candidate refinement --
def decode_candidates(med, pal_lab):
    """(K,64) indices -> (12K,8,8,3) lab: ordem f*NPAL+p, depois medoide."""
    out = []
    for f in range(4):
        for p in range(NPAL):
            out.append(pal_lab[p][med[:, PERM[f]]].reshape(len(med), 8, 8, 3))
    return np.concatenate(out)


def refine_mrf(lab_t, lab_img, med, arg, pal_lab, tile_w, topk=10, mu=0.9,
               sweeps=6):
    """Escolhe, por posicao, entre os `topk` melhores candidatos aquele que
    minimiza erro de pixel + descontinuidade de borda contra a fonte."""
    K = len(med)
    cand = decode_candidates(med, pal_lab)              # (12K,8,8,3)
    NC = len(cand)
    flat = cand.reshape(NC, -1)
    src = lab_t.reshape(NT, -1)
    # custo pixel por (posicao, candidato)
    cost = ((src ** 2).sum(1)[:, None] - 2 * src @ flat.T
            + (flat ** 2).sum(1)[None])
    cost = np.maximum(cost, 0)
    top = np.argpartition(cost, topk, axis=1)[:, :topk]  # (NT,topk)
    tcost = np.take_along_axis(cost, top, 1)
    # bordas dos candidatos: esquerda, direita, topo, base (8,3)
    cl, cr = cand[:, :, 0], cand[:, :, 7]
    ct, cb = cand[:, 0, :], cand[:, 7, :]
    s = lab_t.reshape(NT, 8, 8, 3)
    sl, sr_, st, sb = s[:, :, 0], s[:, :, 7], s[:, 0, :], s[:, 7, :]
    cur = np.array([np.argmin(tcost[i]) for i in range(NT)])
    sel = top[np.arange(NT), cur]                        # candidato atual
    idx = np.arange(NT).reshape(TH, TW)
    par = [(idx[(np.add.outer(np.arange(TH), np.arange(TW)) % 2) == k]) for k in (0, 1)]
    wgt = tile_w
    for sw in range(sweeps):
        for P in par:
            ys, xs = np.divmod(P, TW)
            tot = tcost[P] * 1.0                         # (n,topk)
            tot = tot.copy()
            c = top[P]                                   # (n,topk) cand ids
            # vizinho direito: borda esq. do vizinho vs borda dir. do candidato
            for dy, dx, own_b, nb_b, s_own, s_nb in (
                    (0, 1, cr, cl, sr_, sl),
                    (0, -1, cl, cr, sl, sr_),
                    (1, 0, cb, ct, sb, st),
                    (-1, 0, ct, cb, st, sb)):
                ny, nx = ys + dy, xs + dx
                ok = (ny >= 0) & (ny < TH) & (nx >= 0) & (nx < TW)
                nid = np.where(ok, ny * TW + nx, 0)
                nb_cand = sel[nid]                       # (n,)
                # diferenca de borda decodificada vs diferenca da fonte
                dec_d = own_b[c] - nb_b[nb_cand][:, None]    # (n,topk,8,3)
                src_d = (s_own[P] - s_nb[nid])[:, None]       # (n,1,8,3)
                pen = ((dec_d - src_d) ** 2).sum((-1, -2))
                tot += mu * pen * ok[:, None]
            cur_P = tot.argmin(1)
            sel[P] = c[np.arange(len(P)), cur_P]
    # sel -> (medoide, flip, paleta)
    fp, m = np.divmod(sel, K)
    return np.stack([m, fp // NPAL, fp % NPAL], 1)


# ---------------------------------------------------------------- main --
def quantize(lab, tile_w=None, extra=None, lam=3.0, mu=0.9, topk=10,
             verbose=True, seed=3):
    sr.LAMBDA = lam
    lab_t = sr.tiles_of(lab)
    if tile_w is None:
        tile_w = position_weights(lab)
    pal_lab, pal_rgb, _ = design_palettes(lab_t, hud_weights(), extra=extra)
    med, arg, total = sr.reduce_tiles(lab_t, pal_lab, weights=tile_w, seed=seed)
    if mu > 0:
        arg = refine_mrf(lab_t, lab, med, arg, pal_lab, tile_w, topk=topk, mu=mu)
    img = sr.compose(med, arg, pal_rgb)
    return img, med, arg, pal_lab, pal_rgb


def count_tiles(img):
    return sr.count_tiles(img)


# ------------------------------------------------------------ dithering --
def bayer(n):
    m = np.array([[0]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)


def ordered_dither(lab_t, pal_lab, grp, beta=0.6, order=4):
    """Pontilhado ordenado alinhado ao tile (matriz order x order) com
    mistura de PARES de cores da paleta do tile (Yliluoma).

    Tiles que representam o mesmo degrade recebem o mesmo padrao, entao o
    degrade continua entre tiles vizinhas (sem emenda) e os tiles ficam
    iguais entre si (sem gastar orcamento).  Retorna indices (NT,64)."""
    thr = np.tile(bayer(order), (8 // order, 8 // order)).reshape(64)
    out = np.zeros((NT, 64), np.int64)
    for p in range(NPAL):
        sel = np.where(grp == p)[0]
        if not len(sel):
            continue
        P = pal_lab[p]                                       # (15,3)
        T = lab_t[sel]                                       # (n,64,3)
        ii, jj = np.triu_indices(NCOL, 1)                    # pares i<j
        ci, cj = P[ii], P[jj]                                # (np,3)
        dv = cj - ci
        dd = (dv ** 2).sum(-1) + 1e-9
        pen = beta * dd
        # alpha otimo por (pixel,par), limitado a [0,1]
        rel = T[:, :, None, :] - ci[None, None]              # (n,64,np,3)
        a = np.clip((rel * dv).sum(-1) / dd, 0, 1)
        err = ((rel - a[..., None] * dv) ** 2).sum(-1) + pen
        # inclui as cores puras (a=0 com i==j)
        pure = ((T[:, :, None, :] - P[None, None]) ** 2).sum(-1)   # (n,64,15)
        best_pair = err.argmin(-1)
        e_pair = err.min(-1)
        best_pure = pure.argmin(-1)
        e_pure = pure.min(-1)
        use_pure = e_pure <= e_pair
        al = np.take_along_axis(a, best_pair[..., None], -1)[..., 0]
        pi = ii[best_pair]
        pj = jj[best_pair]
        pick = np.where(al > thr[None], pj, pi)
        out[sel] = np.where(use_pure, best_pure, pick)
    return out


def quantize_dithered(lab, tile_w=None, extra=None, lam=3.0, beta=0.6, order=4,
                      mu=0.0, topk=10, seed=3):
    """Pipeline v2: paletas -> pontilhado ordenado -> k-medoids no alvo
    pontilhado (orcamento de tiles) -> (opcional) MRF de bordas."""
    sr.LAMBDA = lam
    lab_t = sr.tiles_of(lab)
    if tile_w is None:
        tile_w = position_weights(lab)
    pal_lab, pal_rgb, grp = design_palettes(lab_t, hud_weights(hud_w=hud_w) if 'hud_w' in dir() else hud_weights(), extra=extra)
    idx = ordered_dither(lab_t, pal_lab, grp, beta=beta, order=order)
    tgt_t = pal_lab[grp[:, None], idx].astype(np.float32)      # alvo pontilhado
    med, arg, total = sr.reduce_tiles(tgt_t, pal_lab, weights=tile_w, seed=seed)
    if mu > 0:
        arg = refine_mrf(tgt_t, None, med, arg, pal_lab, tile_w, topk=topk, mu=mu)
    img = sr.compose(med, arg, pal_rgb)
    return img, med, arg, pal_lab, pal_rgb


def nearest_idx(lab_t, pal_lab, grp):
    out = np.zeros((NT, 64), np.int64)
    for p in range(NPAL):
        sel = np.where(grp == p)[0]
        if len(sel):
            d = ((lab_t[sel][:, :, None, :] - pal_lab[p][None, None]) ** 2).sum(-1)
            out[sel] = d.argmin(-1)
    return out


def quantize_hybrid(lab, tile_w=None, extra=None, lam=3.0, beta=0.6, order=4,
                    smooth_pct=55, hud_w=0.45, seed=3, mu=0.0, topk=10):
    """Pontilha so os tiles suaves (degrades: ceu, asfalto, paredes) e usa
    o vizinho mais proximo nos tiles de detalhe (contornos nitidos)."""
    sr.LAMBDA = lam
    lab_t = sr.tiles_of(lab)
    if tile_w is None:
        tile_w = position_weights(lab, hud_w=hud_w)
    pal_lab, pal_rgb, grp = design_palettes(lab_t, hud_weights(hud_w=hud_w) if 'hud_w' in dir() else hud_weights(), extra=extra)
    var = lab_t.var(1).sum(-1)
    smooth = var <= np.percentile(var, smooth_pct)
    idx_n = nearest_idx(lab_t, pal_lab, grp)
    idx_d = ordered_dither(lab_t, pal_lab, grp, beta=beta, order=order)
    idx = np.where(smooth[:, None], idx_d, idx_n)
    tgt_t = pal_lab[grp[:, None], idx].astype(np.float32)
    med, arg, total = sr.reduce_tiles(tgt_t, pal_lab, weights=tile_w, seed=seed)
    if mu > 0:
        arg = refine_mrf(tgt_t, None, med, arg, pal_lab, tile_w, topk=topk, mu=mu)
    img = sr.compose(med, arg, pal_rgb)
    return img, med, arg, pal_lab, pal_rgb
