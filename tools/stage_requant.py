#!/usr/bin/env python3
"""Re-export the SNES stage PNGs with three BG palettes and flip-aware tiles.

The fight engine already uploads three stage palettes (CGRAM 32-79, BG
palettes 2-4; see StagePick in src/engine/fight.asm), but the old exports
used only the first one.  Squeezing ~1700 distinct 8x8 tiles into 15
colours and 512 tiles produced the flat, square blocks visible on several
stages.  This tool rebuilds each stage from its high-detail reference:

  * 3 palettes x 15 colours, chosen per tile (RGB555-exact colours);
  * tiles may be reused with H/V flips and with any of the three palettes;
  * the 512-tile budget is met by a discrete k-medoids in OKLab: every
    cluster representative is a real index tile whose pixels minimise the
    error of all positions that use it, so no averaged/flat blocks appear.

Output PNG layout (read by tools/build_stages.py): 512x224, mode P,
45 palette entries; index p*15+c is colour c of palette p.  All pixels of
an 8x8 tile belong to the same palette group.

Sources: hires/<name>.png.  Stages whose art direction was repainted after
the hires references (retouch pass, see redesign/retouch/README.md) keep
the approved repaint: tiles that differ between retouch/before/ and the
current PNG are taken from the current PNG.  Transparent hires pixels also
fall back to the current PNG.

Usage:
  python3 tools/stage_requant.py OUTDIR [STAGE ...]
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PNG_DIR = os.path.join(ROOT, "assets/stages/stages_png_snes")
HIRES = os.path.join(PNG_DIR, "hires")
BEFORE = os.path.join(PNG_DIR, "redesign/retouch/before")

# Stages whose colours/content were deliberately repainted after hires.
KEEP_REPAINT = {"KOF98-JpnStreetStage", "KOF98-USAWharfStage",
                "KOF98-USAWharfStage-B"}

NPAL, NCOL, MAX_TILES = 3, 15, 512
W, H = 512, 224
TW, TH = W // 8, H // 8
NT = TW * TH


# --------------------------------------------------------------- colour --
def srgb_to_oklab(rgb):
    """rgb in 0..255, shape (...,3) -> OKLab float32."""
    c = np.asarray(rgb, np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    out = np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                    1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                    0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s],
                   -1)
    return out.astype(np.float32)


_V5 = np.round(np.arange(32) * 255 / 31).astype(np.int64)
_ALL555 = np.stack(np.meshgrid(_V5, _V5, _V5, indexing="ij"), -1).reshape(-1, 3)
_ALL555_LAB = srgb_to_oklab(_ALL555)


def snap555(lab):
    """OKLab centroids -> nearest RGB555-exact colours (rgb, lab)."""
    d = ((lab[:, None, :] - _ALL555_LAB[None]) ** 2).sum(-1)
    idx = d.argmin(1)
    return _ALL555[idx], _ALL555_LAB[idx]


def kmeans(pts, k, iters=25, seed=1):
    """Plain k-means++ / Lloyd on (N,3) points; returns centroids (k,3)."""
    rng = np.random.default_rng(seed)
    uniq = np.unique(pts, axis=0)
    if len(uniq) <= k:
        return np.concatenate([uniq, np.repeat(uniq[:1], k - len(uniq), 0)])
    cent = [pts[rng.integers(len(pts))]]
    d2 = ((pts - cent[0]) ** 2).sum(1)
    for _ in range(1, k):
        cent.append(pts[rng.choice(len(pts), p=d2 / d2.sum())])
        d2 = np.minimum(d2, ((pts - cent[-1]) ** 2).sum(1))
    cent = np.array(cent)
    for _ in range(iters):
        a = ((pts[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            sel = pts[a == j]
            if len(sel):
                cent[j] = sel.mean(0)
    return cent


# ------------------------------------------------------------ geometry --
def tiles_of(img):
    """(H,W,C) -> (NT,64,C) row-major 8x8 tiles."""
    c = img.shape[-1]
    return img.reshape(TH, 8, TW, 8, c).transpose(0, 2, 1, 3, 4).reshape(NT, 64, c)


def untile(t):
    c = t.shape[-1]
    return t.reshape(TH, TW, 8, 8, c).transpose(0, 2, 1, 3, 4).reshape(H, W, c)


_g = np.arange(64).reshape(8, 8)
# PERM[f][px] = medoid pixel shown at px for flip f (0 none, 1 H, 2 V, 3 HV)
PERM = np.stack([_g, _g[:, ::-1], _g[::-1, :], _g[::-1, ::-1]]).reshape(4, 64)


# -------------------------------------------------------------- source --
def load_source(name):
    cur = np.asarray(Image.open(os.path.join(PNG_DIR, name + ".png"))
                     .convert("RGB")).astype(np.int64)
    hi = np.asarray(Image.open(os.path.join(HIRES, name + ".png"))
                    .convert("RGBA")).astype(np.int64)
    src = hi[..., :3].copy()
    keep = hi[..., 3] < 255          # transparent hires falls back to the PNG
    yy = np.arange(H)[:, None] + np.zeros((1, W), int)
    reuse = True
    if name == "KOF98-USAWharfStage":
        # night sky + skyline repaint: tiles changed by the retouch pass,
        # grown by one tile, above the quay floor
        before = np.asarray(Image.open(os.path.join(BEFORE, name + ".png"))
                            .convert("RGB")).astype(np.int64)
        t = (cur != before).any(2).reshape(TH, 8, TW, 8).any((1, 3))
        g = t.copy()
        g[1:] |= t[:-1]; g[:-1] |= t[1:]; g[:, 1:] |= t[:, :-1]; g[:, :-1] |= t[:, 1:]
        keep |= np.kron(g, np.ones((8, 8), bool)) & (yy < 152)
    elif name == "KOF98-USAWharfStage-B":
        # uniform red sky: every red sky pixel of the approved PNG
        r, gr, b = cur[..., 0], cur[..., 1], cur[..., 2]
        keep |= (yy < 150) & (r > 140) & (gr < 60) & (b < 70)
    elif name == "KOF98-JpnStreetStage":
        # clean asphalt: approved flat asphalt tones on the road; markings,
        # crosswalk, kerb and manhole still come from hires.  The old export
        # left 8 px staircases on the asphalt edge, so a majority filter
        # rounds them and the holes become flat asphalt as well.
        asphalt = (((cur == (115, 107, 90)).all(2)) |
                   ((cur == (99, 90, 74)).all(2))) & (yy >= 145)
        smooth = _majority(asphalt, 6) & (yy >= 145)
        fill = cur.copy()
        fill[~asphalt] = (115, 107, 90)
        src[smooth] = fill[smooth]
        keep = smooth
        reuse = False
    if reuse:
        src[keep] = cur[keep]
    return src, keep


def _majority(mask, r):
    """Box majority filter of radius r (edges clamp)."""
    m = np.pad(mask.astype(np.int32), r, mode="edge")
    c = m.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    n = 2 * r + 1
    s = c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]
    return s * 2 > n * n


# ------------------------------------------------------------- palettes --
def design_palettes(lab_t, rounds=6):
    """lab_t (NT,64,3) -> pal_lab (3,15,3), pal_rgb, tile group (NT,)."""
    means = lab_t.mean(1)
    cent = kmeans(means, NPAL, seed=7)
    grp = ((means[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
    pal_lab = np.zeros((NPAL, NCOL, 3), np.float32)
    pal_rgb = np.zeros((NPAL, NCOL, 3), np.int64)
    err = np.zeros(len(lab_t))
    for _ in range(rounds):
        for p in range(NPAL):
            sel = lab_t[grp == p].reshape(-1, 3)
            if not len(sel):                       # empty group: worst tiles
                sel = lab_t[np.argsort(-err)[:64]].reshape(-1, 3)
            c = kmeans(sel, NCOL, seed=11 + p)
            pal_rgb[p], pal_lab[p] = snap555(c)
        err = np.stack([quant_err(lab_t, pal_lab[p]) for p in range(NPAL)], 1)
        grp = err.argmin(1)
        err = err.min(1)
    return pal_lab, pal_rgb, grp


def quant_err(lab_t, pal):
    d = ((lab_t[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
    return d.min(-1).sum(-1)


# ---------------------------------------------------------- tile budget --
def _blk():
    """Pixel -> 4x4 sub-block index (0..3) inside an 8x8 tile."""
    y, x = np.divmod(np.arange(64), 8)
    return (y // 4) * 2 + x // 4


BLK = _blk()
LAMBDA = 3.0          # weight of the 4x4 sub-block mean error (anti-block)


def _features(tiles_lab):
    """(N,64,3) -> (N,64*3+12) so that |F(a)-F(b)|^2 equals the cost."""
    n = len(tiles_lab)
    bm = np.zeros((n, 4, 3), np.float32)
    for b in range(4):
        bm[:, b] = tiles_lab[:, BLK == b].mean(1)
    return np.concatenate([tiles_lab.reshape(n, -1),
                           np.sqrt(16 * LAMBDA) * bm.reshape(n, -1)], 1)


def reduce_tiles(lab_t, pal_lab, k=MAX_TILES, iters=40, seed=3):
    """Discrete k-medoids over index tiles.

    cost(position, tile) = sum of per-pixel OKLab errors
                           + LAMBDA*16 * sum of 4x4 sub-block mean errors.
    The second term keeps the local brightness/colour of every quarter
    tile right, which is what reads as square blocks when it is wrong.
    Returns medoids (K,64) colour indices, per position (medoid, flip,
    palette) and the total cost."""
    D = np.stack([((lab_t[:, :, None, :] - pal_lab[p][None, None]) ** 2)
                  .sum(-1) for p in range(NPAL)]).astype(np.float32)
    best_p = D.min(-1).sum(-1).argmin(0)
    q_idx = D[best_p, np.arange(NT)].argmin(-1)
    src_bm = np.stack([lab_t[:, BLK == b].mean(1) for b in range(4)], 1)
    Fsrc = _features(lab_t)
    Fq = _features(pal_lab[best_p[:, None], q_idx])
    # init: k-means++ over the quantised tiles
    rng = np.random.default_rng(seed)
    _, first = np.unique(np.concatenate([q_idx, best_p[:, None]], 1),
                         axis=0, return_index=True)
    first = np.sort(first)
    if len(first) <= k:
        med = q_idx[first].copy()
    else:
        pick = [first[rng.integers(len(first))]]
        d2 = ((Fq[first] - Fq[pick[0]]) ** 2).sum(1)
        for _ in range(1, k):
            j = first[rng.choice(len(first), p=d2 / d2.sum())]
            pick.append(j)
            d2 = np.minimum(d2, ((Fq[first] - Fq[j]) ** 2).sum(1))
        med = q_idx[np.array(pick)].copy()
    src2 = (Fsrc ** 2).sum(1)
    prev = None
    for it in range(iters):
        K = len(med)
        # ---- assignment: every (medoid, flip, palette) candidate
        cand = []
        for f in range(4):
            for p in range(NPAL):
                cand.append(_features(pal_lab[p][med[:, PERM[f]]]))
        C = np.concatenate(cand)                         # (12K, F)
        cost = src2[:, None] - 2 * Fsrc @ C.T + (C ** 2).sum(1)[None]
        j = cost.argmin(1)
        best = np.maximum(cost[np.arange(NT), j], 0)
        fp, m = np.divmod(j, K)
        arg = np.stack([m, fp // NPAL, fp % NPAL], 1)
        total = float(best.sum())
        # ---- update: per-pixel optimum, then ICM sweeps with block term
        acc = np.zeros((K, 64, NCOL), np.float32)
        for f in range(4):
            for p in range(NPAL):
                sel = np.where((arg[:, 1] == f) & (arg[:, 2] == p))[0]
                if len(sel):
                    np.add.at(acc, (arg[sel, 0][:, None], PERM[f][None, :]),
                              D[p, sel])
        used = np.bincount(arg[:, 0], minlength=K) > 0
        newmed = med.copy()
        newmed[used] = acc[used].argmin(-1)
        _icm(newmed, arg, D, pal_lab, src_bm, sweeps=2)
        # ---- reseed unused / flip-duplicate medoids at worst positions
        canon, free = {}, list(np.where(~used)[0])
        for jm in np.where(used)[0]:
            key = min(newmed[jm][PERM[f]].tobytes() for f in range(4))
            if key in canon:
                free.append(jm)
            else:
                canon[key] = jm
        if free:
            taken, wi, worst = set(), 0, np.argsort(-best)
            for jm in free:
                while wi < NT and arg[worst[wi], 0] in taken:
                    wi += 1
                if wi >= NT:
                    break
                newmed[jm] = q_idx[worst[wi]]
                taken.add(arg[worst[wi], 0])
                wi += 1
        med = newmed
        if prev is not None and abs(prev - total) < 2e-4 * total and not free:
            break
        prev = total
    # final assignment for the final medoids
    cand = [_features(pal_lab[p][med[:, PERM[f]]])
            for f in range(4) for p in range(NPAL)]
    C = np.concatenate(cand)
    cost = src2[:, None] - 2 * Fsrc @ C.T + (C ** 2).sum(1)[None]
    j = cost.argmin(1)
    fp, m = np.divmod(j, len(med))
    arg = np.stack([m, fp // NPAL, fp % NPAL], 1)
    return med, arg, float(np.maximum(cost[np.arange(NT), j], 0).sum())


def _icm(med, arg, D, pal_lab, src_bm, sweeps=2):
    """Greedy per-pixel recolouring of medoids with the block-mean term."""
    K = len(med)
    pos = np.arange(NT)
    mi, fi, pi = arg[:, 0], arg[:, 1], arg[:, 2]
    w = 16 * LAMBDA
    for _ in range(sweeps):
        # current decoded block means for every position
        dec = pal_lab[pi[:, None], med[mi][np.arange(NT)[:, None],
                                           PERM[fi]]]          # (NT,64,3)
        bm = np.stack([dec[:, BLK == b].mean(1) for b in range(4)], 1)
        for q in range(64):
            px = PERM[fi, q]                    # position pixel showing q
            blk = BLK[px]
            c0 = med[mi, q]
            P0 = pal_lab[pi, c0]
            base_pix = D[pi, pos, px, c0]
            cur_bm = bm[pos, blk]
            tgt = src_bm[pos, blk]
            base_blk = ((tgt - cur_bm) ** 2).sum(1)
            deltas = np.zeros((NCOL, K), np.float32)
            for c in range(NCOL):
                Pc = pal_lab[pi, c]
                nb = cur_bm + (Pc - P0) / 16.0
                d = (D[pi, pos, px, c] - base_pix
                     + w * (((tgt - nb) ** 2).sum(1) - base_blk))
                deltas[c] = np.bincount(mi, weights=d, minlength=K)
            newc = deltas.argmin(0)
            ch = deltas[newc, np.arange(K)] < -1e-9
            if not ch.any():
                continue
            med[ch, q] = newc[ch]
            moved = ch[mi]
            sel = pos[moved]
            bm[sel, blk[moved]] += (pal_lab[pi[sel], med[mi[sel], q]]
                                    - P0[moved]) / 16.0


def compose(med, arg, pal_rgb):
    """Rebuild the indexed image: index = p*15 + colour."""
    idx = np.empty((NT, 64), np.int64)
    for i in range(NT):
        m, f, p = arg[i]
        idx[i] = p * NCOL + med[m][PERM[f]]
    img = untile(idx[..., None])[..., 0].astype(np.uint8)
    out = Image.fromarray(img, "P")
    out.putpalette([int(v) for v in pal_rgb.reshape(-1)] + [0] * (768 - NPAL * NCOL * 3))
    return out


def count_tiles(img):
    """Distinct 8x8 index tiles after palette-group and flip folding."""
    a = np.asarray(img).astype(np.int64)
    t = tiles_of(a[..., None])[..., 0] % NCOL
    return len({min(r[PERM[f]].tobytes() for f in range(4)) for r in t})


def run(name, outdir):
    src, keep = load_source(name)
    lab = srgb_to_oklab(src)
    lab_t = tiles_of(lab)
    pal_lab, pal_rgb, _ = design_palettes(lab_t)
    med, arg, total = reduce_tiles(lab_t, pal_lab)
    img = compose(med, arg, pal_rgb)
    n = count_tiles(img)
    assert n <= MAX_TILES, (name, n)
    img.save(os.path.join(outdir, name + ".png"), optimize=True)
    rec = srgb_to_oklab(np.asarray(img.convert("RGB")))
    rmse = float(np.sqrt(((rec - lab) ** 2).sum(-1).mean()))
    print(f"{name}: {n} tiles, oklab rmse {rmse:.4f}, "
          f"repaint-kept px {int(keep.sum())}", flush=True)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    names = sys.argv[2:] or sorted(os.path.splitext(f)[0] for f in
                                   os.listdir(HIRES) if f.endswith(".png"))
    for n in names:
        run(n, outdir)


if __name__ == "__main__":
    main()
