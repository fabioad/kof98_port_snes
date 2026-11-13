"""Arcade-style fight HUD extras (BG3 tiles 704..1023, VRAM $3600-$3FFF).

The base HUD (hud.chr, tiles 0..383) is a flat 3-colour BG3 set.  This module
adds the KOF'98 arcade look on top of it:

* big gradient timer digits (Time.sff), combo digits + RUSH/HITS (Combo.sff),
  GO! and K.O. banners (fight.sff GO! art; K.O. redrawn in the same style),
  an italic COUNTER!! banner, italic fighter names and the blue POW stock
  digits (Power_Bar_P1.sff).
* BG3 palette 2 (CGRAM 9..11) is a *gradient* palette: three HDMA channels
  rewrite its three colours on every scanline, so one 2bpp tile set shows the
  arcade's vertical gradients and per-banner outline colours.  The tiles only
  use index 1 = outline, 2 = gradient fill, 3 = shade/bevel; each screen band
  (timer, P2 name, combo, COUNTER, GO/K.O.) gets its own colours.

Everything is emitted as data: hud2.chr, symbols/blocks in hud2.inc and the
three HDMA tables.  Tile numbers are absolute BG3 tile ids (704 + n) so map
words are simply `tile | attr << 8`.
"""
import os
from PIL import Image, ImageDraw

TILE0 = 704                      # first free BG3 tile ($3600 word address)
TILE_MAX = 1024
PRIO = 0x2000
PAL2 = PRIO | (2 << 10)          # gradient palette (HDMA)
PAL3 = PRIO | (3 << 10)          # navy / blue / white

# BG3 pixel rows of each HDMA band (screen line == BG line, BG3 VOFS = 0).
TIMER_Y = 8          # rows 1..3, 24 lines
NAME_Y = 32          # row 4, 8 lines
COMBO_Y = 56         # rows 7..9, 24 lines (digits); RUSH/HITS rows 8..9
COUNTER_Y = 80       # rows 10..11, 16 lines
BANNER_Y = 96        # rows 12..16, 40 lines (GO! / K.O.)
BANNER_ROWS = 5
# POW stock box: HudBottomMap rows 23-24 (BG lines 184-199).  The digit is
# composited into the box tiles in palette 2; these lines recolour it.
POW_Y = 184
POW_LINES = 16
POW_BLUE_END = 195   # line 195 carries the box's orange bottom edge
POW_DARK = (16, 16, 16)
POW_ORANGE = (246, 91, 8)
POW_CREAM = (255, 246, 201)
POW_BLUE = (32, 64, 246)
POW_COLS = ((0, 1), (30, 31))      # P1 / P2 map columns of the 2x2 digit
POW_DIGIT_X = (7, 0)               # digit x inside each side's 16x16 cell
POW_DIGIT_Y = 1                    # BG line 185
HDMA_LINES = POW_Y + POW_LINES


def tiles2bpp(pix, w, h):
    tw, th = (w + 7) // 8, (h + 7) // 8
    out = bytearray()
    for ty in range(th):
        for tx in range(tw):
            for row in range(8):
                y = ty * 8 + row
                lo = hi = 0
                for x in range(8):
                    px = pix[y * w + tx * 8 + x] if y < h and tx * 8 + x < w \
                        else 0
                    lo |= (px & 1) << (7 - x)
                    hi |= (px >> 1 & 1) << (7 - x)
                out += bytes((lo, hi))
    return out


def _lum(r, g, b):
    return (r * 77 + g * 150 + b * 29) >> 8


def _masks(im, dark=80):
    """Full-res (shape, fill) 'L' masks: fill = opaque and not outline-dark."""
    shape = Image.new('L', im.size, 0)
    fill = Image.new('L', im.size, 0)
    sp, fp, ip = shape.load(), fill.load(), im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = ip[x, y]
            if a >= 128:
                sp[x, y] = 255
                if _lum(r, g, b) >= dark:
                    fp[x, y] = 255
    return shape, fill


def _grid(w, h, v=0):
    return [[v] * w for _ in range(h)]


def _shrink(mask, w, h, thr=110):
    m = mask.resize((w, h), Image.BOX)
    p = m.load()
    return [[1 if p[x, y] >= thr else 0 for x in range(w)] for y in range(h)]


def _ring(fill, w, h, diag=True):
    """Pixels adjacent to fill (8- or 4-neighbourhood) that are not fill."""
    out = _grid(w, h)
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diag:
        nb += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    for y in range(h):
        for x in range(w):
            if fill[y][x]:
                continue
            for dx, dy in nb:
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and fill[yy][xx]:
                    out[y][x] = 1
                    break
    return out


def glyph(im, w, h, dark=80, bevel=False, thr=110):
    """Source sprite -> w x h index grid: 1 outline, 2 fill, 3 left bevel.

    The fill shape is down-sampled from the bright pixels; the outline is the
    down-sampled dark border plus a guaranteed one-pixel ring, so the glyph
    keeps the arcade's solid contour at SNES size."""
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    shape, fill = _masks(im, dark)
    # Leave a 1 px border for the ring.
    f = _shrink(fill, w - 2, h - 2, thr)
    s = _shrink(shape, w - 2, h - 2, 96)
    F = _grid(w, h)
    S = _grid(w, h)
    for y in range(h - 2):
        for x in range(w - 2):
            F[y + 1][x + 1] = f[y][x]
            S[y + 1][x + 1] = s[y][x]
    ring = _ring(F, w, h)
    out = _grid(w, h)
    for y in range(h):
        for x in range(w):
            if F[y][x]:
                out[y][x] = 2
            elif S[y][x] or ring[y][x]:
                out[y][x] = 1
    if bevel:
        # Arcade timer/combo digits: a dark shade on the outer left edge
        # only (the leftmost fill pixel of every row), not around holes.
        for y in range(h):
            for x in range(1, w):
                if out[y][x] == 2:
                    if out[y][x - 1] == 1:
                        out[y][x] = 3
                    break
    return out


def gradient(im, rows, dark=80):
    """Average fill colour of `im` per output row (rows = glyph height)."""
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    p = im.load()
    acc = [[0, 0, 0, 0] for _ in range(rows)]
    for y in range(im.height):
        oy = min(rows - 1, y * rows // im.height)
        for x in range(im.width):
            r, g, b, a = p[x, y]
            if a >= 128 and _lum(r, g, b) >= dark:
                t = acc[oy]
                t[0] += r
                t[1] += g
                t[2] += b
                t[3] += 1
    out = []
    last = (255, 200, 40)
    for r, g, b, n in acc:
        if n:
            last = (r // n, g // n, b // n)
        out.append(last)
    return out


def lerp(c0, c1, n):
    return [tuple(round(c0[i] + (c1[i] - c0[i]) * k / max(1, n - 1))
                  for i in range(3)) for k in range(n)]


def shade(c, k=0.55):
    return tuple(int(v * k) for v in c)


def paste(dst, src, ox, oy):
    for y, row in enumerate(src):
        for x, v in enumerate(row):
            if v and 0 <= oy + y < len(dst) and 0 <= ox + x < len(dst[0]):
                dst[oy + y][ox + x] = v


def flat(grid):
    return bytes(v for row in grid for v in row)


class Pool:
    """Tile allocator for the $3600 block (absolute BG3 tile ids)."""

    def __init__(self):
        self.data = bytearray()
        self.dedup = {}

    @property
    def next(self):
        return TILE0 + len(self.data) // 16

    def raw(self, grid):
        """Append every 8x8 tile of `grid` in row-major tile order."""
        h, w = len(grid), len(grid[0])
        first = self.next
        self.data += tiles2bpp(flat(grid), w, h)
        return first

    def block(self, grid, attr):
        """Deduplicated map words (blank tile -> 0) for a cols x rows block."""
        h, w = len(grid), len(grid[0])
        words = []
        for ty in range(h // 8):
            for tx in range(w // 8):
                cell = [grid[ty * 8 + y][tx * 8:tx * 8 + 8] for y in range(8)]
                raw = bytes(tiles2bpp(flat(cell), 8, 8))
                if not any(raw):
                    words.append(0)
                    continue
                t = self.dedup.get(raw)
                if t is None:
                    t = self.next
                    self.dedup[raw] = t
                    self.data += raw
                words.append(attr | t)
        return w // 8, h // 8, words


def _italic(grid, slope):
    """Shear right: row y shifts by round((h-1-y) * slope)."""
    h, w = len(grid), len(grid[0])
    extra = int(round((h - 1) * slope))
    out = _grid(w + extra, h)
    for y in range(h):
        d = int(round((h - 1 - y) * slope))
        for x in range(w):
            out[y][x + d] = grid[y][x]
    return out


def name_glyph(spr):
    """KOF99DM 8x8 name glyph -> italic 8x8 cell (1 navy, 2 low, 3 high)."""
    lit = _grid(8, 8)
    if spr is not None:
        im = spr if spr.width == 8 else spr.resize((8, spr.height),
                                                   Image.LANCZOS)
        p = im.load()
        for y in range(min(8, im.height)):
            for x in range(8):
                r, g, b, a = p[x, y]
                if a >= 96 and _lum(r, g, b) >= 70:
                    lit[y][x] = 1
    # The strip glyphs are 7 px wide with a drop shadow; keep the letter
    # body (cols 0..5, rows 0..6) and slant the top half one pixel right.
    body = _grid(6, 7)
    for y in range(7):
        for x in range(6):
            body[y][x] = lit[y][x]
    sl = _grid(7, 7)
    for y in range(7):
        d = 1 if y < 4 else 0
        for x in range(6):
            if body[y][x]:
                sl[y][x + d] = 1
    cell = _grid(8, 8)
    for y in range(7):
        for x in range(7):
            if sl[y][x]:
                cell[y][x] = 3 if y < 4 else 2      # baked 2-tone (P1)
    ring = _ring([[1 if v else 0 for v in r] for r in cell], 8, 8,
                 diag=False)
    for y in range(8):
        for x in range(8):
            if ring[y][x]:
                cell[y][x] = 1
    return cell


def text_italic(glyphs, s, h=11, cw=7, gap=1, slope=0.25):
    """Arcade name-font text (Life Names.fnt) as an italic fill mask."""
    cells = []
    for ch in s:
        spr = glyphs.get(ch)
        if ch == '!' and spr is None:       # Life Names.fnt has no '!'
            bang = _grid(3, h)
            for y in list(range(h - 3)) + [h - 2, h - 1]:
                for x in range(3):
                    bang[y][x] = 1
            cells.append(bang)
            continue
        if spr is None:
            cells.append(_grid(cw // 2, h))
            continue
        bb = spr.getbbox()
        spr = spr.crop(bb) if bb else spr
        wch = cw if ch.isalnum() else max(2, round(spr.width * h / spr.height))
        wch = min(wch, cw)
        _shape, fill = _masks(spr, 70)
        cells.append(_shrink(fill, wch, h, 100))
    width = sum(len(c[0]) + gap for c in cells) - gap
    out = _grid(width, h)
    x = 0
    for c in cells:
        paste(out, c, x, 0)
        x += len(c[0]) + gap
    return _italic(out, slope)


def build(lb_dir, files, fspr, go_key, ko_key, fnt_v1, sff_imgs, fnt_v2_sff,
          charset, out_dir, pow_box=None):
    pool = Pool()
    inc = []
    small = fnt_v1(os.path.join(lb_dir, files['font7']))
    names = fnt_v1(os.path.join(lb_dir, files['font1']))
    tfont = sff_imgs(fnt_v2_sff(os.path.join(lb_dir, files['font2'])))
    cfont = sff_imgs(fnt_v2_sff(os.path.join(lb_dir, files['font6'])))
    pfont = sff_imgs(fnt_v2_sff(os.path.join(lb_dir, files['font3'])),
                     {(0, ord(c)) for c in "0123"})
    preview = {}

    # --- italic name font (8x8, CHARSET-indexed lookup) -------------------
    used = " ABCDEFGHIJKLMNOPQRSTUVWXYZ.-!"
    nmap = []
    for ch in charset:
        if ch not in used or ch == ' ':
            nmap.append(0)
            continue
        spr = small.get(ch) or small.get(ch.lower())
        cell = name_glyph(spr)
        nmap.append(pool.raw(cell))
        preview.setdefault('names', []).append(cell)
    inc.append("NameIMap: .dw " + ",".join(str(v) for v in nmap) + "\n")

    # --- timer digits: Time.sff, 16x24 cells (glyph 14x24) ----------------
    tdig = pool.next
    for d in range(10):
        g = glyph(tfont[0, 48 + d], 14 if d != 1 else 12, 24, bevel=True)
        cell = _grid(16, 24)
        paste(cell, g, (16 - len(g[0])) // 2, 0)
        pool.raw(cell)
        preview.setdefault('timer', []).append(cell)
    t_grad = gradient(tfont[0, 48], 24)

    # --- combo digits: Combo.sff (blue outline), 16x24 --------------------
    cdig = pool.next
    for d in range(10):
        g = glyph(cfont[0, 48 + d], 15 if d != 1 else 12, 24, dark=60,
                  bevel=True)
        cell = _grid(16, 24)
        paste(cell, g, (16 - len(g[0])) // 2, 0)
        pool.raw(cell)
        preview.setdefault('combo', []).append(cell)
    c_grad = gradient(cfont[0, 48], 24, dark=60)

    # RUSH / HITS: white letters, blue outline, palette 3 (3 white, 2 blue).
    blocks = {}
    for label, code in (("HudRush", 66), ("HudHits", 65)):
        g = glyph(cfont[0, code], 32, 14, dark=110)
        cell = _grid(32, 16)
        for y, row in enumerate(g):
            for x, v in enumerate(row):
                cell[y + 2][x] = {0: 0, 1: 2, 2: 3, 3: 3}[v]
        blocks[label] = pool.block(cell, PAL3)
        preview[label] = cell

    # --- COUNTER!!: italic arcade name font, white outline ----------------
    txt = text_italic(names, "COUNTER!!", h=11, cw=7, gap=1, slope=0.3)
    w = len(txt[0]) + 4
    cell = _grid(80, 16)
    ox = max(0, (80 - w) // 2)
    fillm = _grid(80, 16)
    paste(fillm, txt, ox + 2, 2)
    white = _ring(fillm, 80, 16)
    both = [[1 if fillm[y][x] or white[y][x] else 0 for x in range(80)]
            for y in range(16)]
    outer = _ring(both, 80, 16, diag=False)
    for y in range(16):
        for x in range(80):
            cell[y][x] = 2 if fillm[y][x] else 1 if white[y][x] else \
                3 if outer[y][x] else 0
    blocks["HudCounter"] = pool.block(cell, PAL2)
    preview["HudCounter"] = cell
    k_grad = lerp((255, 236, 64), (255, 120, 16), 8) + \
        lerp((250, 104, 12), (200, 24, 8), 8)

    # --- GO! (fight.sff art) and K.O. in the same style -------------------
    bh = BANNER_ROWS * 8
    go = fspr[go_key]
    gw = round(go.getbbox() and (go.getbbox()[2] - go.getbbox()[0]) * (bh - 2)
               / (go.getbbox()[3] - go.getbbox()[1]))
    ggo = glyph(go, gw + 2, bh, dark=70)
    cols = (len(ggo[0]) + 7) // 8
    cell = _grid(cols * 8, bh)
    paste(cell, ggo, (cols * 8 - len(ggo[0])) // 2, 0)
    blocks["HudGo"] = pool.block(cell, PAL2)
    preview["HudGo"] = cell
    g_grad = gradient(go, bh, dark=70)
    # K.O.: fight.sff's K.O. shape (outline + fill only) with GO!'s outline
    # and gradient; letters sized to GO!'s cap height.
    ko = fspr[ko_key]
    bb = ko.getbbox()
    kw = round((bb[2] - bb[0]) * (bh - 6) / (bb[3] - bb[1]))
    gko = glyph(ko, kw + 2, bh - 4, dark=50)
    # fight.sff spells "K.O"; copy its period (the columns lit only in the
    # lower part, between K and O) after the O for the arcade "K.O.".
    kh, kwid = len(gko), len(gko[0])
    low = [x for x in range(kwid)
           if any(gko[y][x] for y in range(kh))
           and not any(gko[y][x] for y in range(kh // 2))]
    groups = []
    for x in low:
        if groups and x == groups[-1][-1] + 1:
            groups[-1].append(x)
        else:
            groups.append([x])
    groups = [g for g in groups if len(g) >= 4]
    per = None
    if groups:
        x0, x1 = groups[0][0], groups[0][-1] + 1
        per = [row[x0:x1] for row in gko]
    pw = (len(per[0]) + 1) if per else 0
    cols = (kwid + pw + 7) // 8
    cell = _grid(cols * 8, bh)
    ox = (cols * 8 - kwid - pw) // 2
    paste(cell, gko, ox, 2)
    if per:
        paste(cell, per, ox + kwid + 1 - 1, 2)
    blocks["HudKo"] = pool.block(cell, PAL2)
    preview["HudKo"] = cell

    # --- POW stock digits: blue, composited into the cream box ------------
    # pow_box = (HudBottomMap words, BG3 2bpp tile bytes).  The box tiles
    # use palette 7 (1 dark, 2 orange, 3 cream); the composite keeps those
    # indices in palette 2, whose colours HDMA swaps to the box colours on
    # lines 184-199 -- index 2 is blue down to line 194 and orange on 195.
    bmap, btiles = pow_box

    def decode(tile):
        raw = btiles[tile * 16:tile * 16 + 16]
        return [[(raw[2 * y] >> (7 - x) & 1) | (raw[2 * y + 1] >> (7 - x) & 1) << 1
                 for x in range(8)] for y in range(8)]

    # The font3 digits are 38x44; boxed down to 9x10 they turn into blobs,
    # so the box digits are drawn by hand: a 2 px blue stroke (7x8) with a
    # 1 px dark outline on the outside only (counters stay cream).
    POW_GLYPHS = (
        (".#####.", "##...##", "##...##", "##...##",
         "##...##", "##...##", "##...##", ".#####."),
        ("...##..", "..###..", ".####..", "...##..",
         "...##..", "...##..", "...##..", ".######"),
        (".#####.", "##...##", ".....##", "....##.",
         "..###..", ".##....", "##.....", "#######"),
        ("######.", ".....##", ".....##", "..####.",
         ".....##", ".....##", ".....##", "######."),
    )
    dw, dh = 9, 10
    digits = []
    for rows in POW_GLYPHS:
        g = _grid(dw, dh)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == '#':
                    g[y + 1][x + 1] = 2
        outside = set()
        todo = [(x, y) for x in range(dw) for y in (0, dh - 1)] + \
               [(x, y) for y in range(dh) for x in (0, dw - 1)]
        while todo:
            x, y = todo.pop()
            if (x, y) in outside or not (0 <= x < dw and 0 <= y < dh) \
                    or g[y][x]:
                continue
            outside.add((x, y))
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        for x, y in outside:
            if any(0 <= x + i < dw and 0 <= y + j < dh
                   and g[y + j][x + i] == 2
                   for i in (-1, 0, 1) for j in (-1, 0, 1)):
                g[y][x] = 1
        for y in range(dh):
            for x in range(dw):
                if not g[y][x]:
                    g[y][x] = 3            # cream backing (box colour)
        digits.append(g)
    pdig = []
    for side, cols in enumerate(POW_COLS):
        base = [[0] * 16 for _ in range(16)]
        for ty in range(2):
            for k, tx in enumerate(cols):
                w = bmap[ty * 32 + tx]
                t = decode(w & 0x3FF) if w & 0x3FF else [[0] * 8] * 8
                for y in range(8):
                    base[ty * 8 + y][k * 8:k * 8 + 8] = t[y]
        pdig.append(pool.next)
        for d, g in enumerate(digits):
            cell = [row[:] for row in base]
            paste(cell, g, POW_DIGIT_X[side], POW_DIGIT_Y)
            dx, dy = POW_DIGIT_X[side], POW_DIGIT_Y
            for y in range(16):
                if POW_Y + y >= POW_BLUE_END:
                    continue
                if any(base[y][x] == 2 and not (
                        0 <= y - dy < dh and 0 <= x - dx < dw
                        and g[y - dy][x - dx]) for x in range(16)):
                    raise ValueError(f"POW box side {side} line {POW_Y + y}"
                                     " has orange where the digit is blue")
            pool.raw(cell)
            preview.setdefault('pow', []).append(cell)

    if pool.next > TILE_MAX:
        raise ValueError(f"arcade HUD uses {pool.next - TILE0} tiles; only "
                         f"{TILE_MAX - TILE0} fit in $3600-$3FFF")
    open(os.path.join(out_dir, "hud2.chr"), "wb").write(pool.data)

    # --- HDMA colour tables for CGRAM 9 / 10 / 11 -------------------------
    black = (0, 0, 0)
    lines = []
    rest = (black, (255, 160, 32), (120, 60, 8))
    cur = rest
    for y in range(HDMA_LINES):
        if TIMER_Y <= y < TIMER_Y + 24:
            c = t_grad[y - TIMER_Y]
            cur = (black, c, shade(c, 0.6))
        elif NAME_Y <= y < NAME_Y + 8:
            c = lerp((255, 236, 96), (232, 40, 16), 7)[min(6, y - NAME_Y)]
            cur = ((40, 8, 4), c, c)
        elif COMBO_Y <= y < COMBO_Y + 24:
            c = c_grad[y - COMBO_Y]
            cur = ((16, 32, 168), c, shade(c, 0.62))
        elif COUNTER_Y <= y < COUNTER_Y + 16:
            c = k_grad[y - COUNTER_Y]
            cur = ((255, 255, 255), c, (72, 8, 8))
        elif BANNER_Y <= y < BANNER_Y + bh:
            c = g_grad[y - BANNER_Y]
            cur = (black, c, shade(c, 0.6))
        elif POW_Y - 1 <= y < POW_Y - 1 + POW_LINES:
            # HDMA counts screen lines; BG3 shows BG line y + 1 on screen
            # line y, so the box's BG lines map one HDMA line earlier.
            cur = (POW_DARK,
                   POW_BLUE if y < POW_BLUE_END - 1 else POW_ORANGE,
                   POW_CREAM)
        lines.append(cur)

    def bgr(c):
        r, g, b = c
        return (b >> 3) << 10 | (g >> 3) << 5 | (r >> 3)

    for ch in range(3):
        cg = 9 + ch
        seq = [bgr(l[ch]) for l in lines]
        out = []
        pending = []

        def flush():
            while pending:
                part = pending[:127]
                del pending[:127]
                body = ",".join(f"{cg},{cg},${v & 255:02X},${v >> 8:02X}"
                                for v in part)
                out.append(f"    .db ${0x80 | len(part):02X},{body}\n")

        i = 0
        while i < len(seq):
            j = i
            while j < len(seq) and seq[j] == seq[i] and j - i < 127:
                j += 1
            if j - i >= 3:                  # hold: one write, n lines
                flush()
                out.append(f"    .db {j - i},{cg},{cg},${seq[i] & 255:02X},"
                           f"${seq[i] >> 8:02X}\n")
            else:                           # repeat mode: a write per line
                pending.extend(seq[i:j])
            i = j
        flush()
        # Extra terminators: a channel re-armed mid-frame (HDMAEN written
        # after the line-0 init, e.g. snes9x re-activates a finished channel)
        # resumes right after the last 0 it read.  Without padding it walks
        # into the next table misaligned and writes colour bytes to CGADD,
        # scrambling the whole palette.  Each stray re-arm eats one 0 here.
        inc.append(f"HudHdma{ch + 1}:\n" + "".join(out)
                   + "    .db 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n")
    # CGRAM 8..11: colour 0 (transparent slot) + the three HDMA colours.
    rest_pal = b"".join(bgr(c).to_bytes(2, 'little') for c in (black,) + rest)

    for label, (cols, rows, words) in blocks.items():
        inc.append(f"{label}: .db {cols},{rows}\n    .dw " +
                   ",".join(f"${w:04X}" for w in words) + "\n")
    inc.append(f"HUD2_TILES = {pool.next - TILE0}\n"
               f"TDIG_W = ${PAL2 | tdig:04X}\n"
               f"CDIG_W = ${PAL2 | cdig:04X}\n"
               f"PDIG1_W = ${PAL2 | pdig[0]:04X}\n"
               f"PDIG2_W = ${PAL2 | pdig[1]:04X}\n"
               f"NAMEI_P1 = ${PAL3:04X}\n"
               f"NAMEI_P2 = ${PAL2:04X}\n")
    inc.append("HudPal2Rest: .dw " + ",".join(
        f"${bgr(c):04X}" for c in (black,) + rest) + "\n")
    open(os.path.join(out_dir, "hud2.inc"), "w").write(
        "; generated by tools/build_hud_arcade.py -- do not edit\n" +
        "".join(inc))
    return {"preview": preview, "lines": lines, "tiles": pool.next - TILE0,
            "rest": rest_pal}
