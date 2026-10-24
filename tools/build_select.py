#!/usr/bin/env python3
"""build_select.py — KOF98 character-select assets for the SNES build.

Sources (assets/kof98data):
  Select.sff  bg anim frame 0,44 = final layout (blue beams + 39 cells + bar)
  system.sff  150,0 cell box / 160,0 P1 cursor / 170,0 P2 cursor / 161 done
  <Char>.sff  9000,0 = 25x25 cell icon

Emits (src/gen_menu):
  select.chr   4bpp tiles: art + occupied-cell patches
  select.map   32x32 word map for BG1 (word $1800): art + cell portraits
  select.pal   8 BG palettes x16: 0 art, 1-7 grouped icon palettes
  selobj.chr   OBJ tiles: ring cursor 8 + fill 1 (menufont stays separate)
  selobj.pal   OBJ pals: 0 white font, 1 yellow, 2 P1 blue, 3 P2 red
  seldata.inc  geometry + cell->char map + movement neighbor table
               (char ids kept in CharSelTab order)

Grid is data-driven: ROSTER below maps char -> cell index; adding fighters
later only needs a new entry (cells not in ROSTER render as empty boxes).
The big portrait windows were dropped for the 41-char roster: their area
became NEW_CELLS below, and BG pals 1-7 (freed by the faces) now hold one
shared palette per ~6-char group so icons keep decent color depth.
"""
import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sff import Sff, tiles4bpp  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOF = os.path.join(ROOT, "assets", "kof98data")
CHARS = os.path.join(ROOT, "assets", "characters")
DST = os.path.join(ROOT, "src", "gen_menu")

# char id order must match CharSelTab in fight.asm:
#   0-13 original visible roster, 14 hidden Omega Rugal (L+R on the rugal
#   cell -> mirrors cell 37, no icon of its own), 15+ the mass MSU
#   import in NEW_CHARS order.  Entry = (sff, cell[, hidden]).
from newroster import NEW_CHARS            # noqa: E402


def _nsff(key):
    return NEW_CHARS[key]["sff"].split("assets/characters/", 1)[1]


ROSTER = [
    ("Kyo-KOF98/Kyo.sff",            3),   # 0  KYO    mid row0 col0
    ("Iori-KOF98/Iori.sff",          6),   # 1  IORI   right row0 col0
    ("Shingo-KOF98/Shingo.sff",      36),  # 2  SHINGO bottom row left
    ("Rugal-KOF98/OmegaRugal.sff",   37),  # 3  RUGAL  bottom row center
    ("Saisyu-KOF98/Saisyu.sff",      12),  # 4  SAISYU mid row1 col0
    ("Heidern-KOF98/Heidern.sff",    13),  # 5  HEIDERN mid row1 col1
    ("Takuma-KOF98/Takuma.sff",      14),  # 6  TAKUMA mid row1 col2
    ("Clark-KOF98/Clark.sff",        15),  # 7  CLARK  right row1 col0
    ("Ralf-KOF98/ralf.sff",          16),  # 8  RALF   right row1 col1
    ("Leona-KOF98/98Leona.sff",      17),  # 9  LEONA  right row1 col2
    ("Mature-KOF98/Mature.sff",      7),   # 10 MATURE right row0 col1
    ("Vice-KOF98/Vice.sff",          8),   # 11 VICE   right row0 col2
    ("Benimaru-KOF98/Benimaru.sff",  4),   # 12 BENIMARU mid row0 col1
    ("Daimon-KOF98/Daimon.sff",      5),   # 13 DAIMON mid row0 col2
    ("Rugal-KOF98/OmegaRugal.sff",   37, True),  # 14 hidden O.RUGAL
    # --- mass MSU import (ids 15-42, NEW_CHARS order) ---
    (_nsff("terry"),                 0),   # 15 TERRY   left row0
    (_nsff("andy"),                  1),   # 16 ANDY
    (_nsff("joe"),                   2),   # 17 JOE
    (_nsff("ryo"),                   9),   # 18 RYO     left row1
    (_nsff("robert"),                10),  # 19 ROBERT
    (_nsff("yuri"),                  11),  # 20 YURI    right of ROBERT
    (_nsff("athena"),                18),  # 21 ATHENA  row2 left
    (_nsff("kensou"),                19),  # 22 KENSOU
    (_nsff("chin"),                  20),  # 23 CHIN
    (_nsff("king"),                  21),  # 24 KING    row2 mid
    (_nsff("mai"),                   22),  # 25 MAI
    (_nsff("chizuru"),               23),  # 26 CHIZURU
    (_nsff("kim"),                   24),  # 27 KIM     row2 right
    (_nsff("chang"),                 25),  # 28 CHANG
    (_nsff("choi"),                  26),  # 29 CHOI
    (_nsff("yashiro"),               27),  # 30 YASHIRO row3 left
    (_nsff("shermie"),               28),  # 31 SHERMIE
    (_nsff("chris"),                 29),  # 32 CHRIS
    (_nsff("yamazaki"),              30),  # 33 YAMAZAKI row3 mid
    (_nsff("mary"),                  31),  # 34 MARY
    (_nsff("billy"),                 32),  # 35 BILLY
    (_nsff("lucky"),                 33),  # 36 LUCKY   row3 right
    (_nsff("heavyd"),                34),  # 37 HEAVY-D
    (_nsff("brian"),                 35),  # 38 BRIAN
    (_nsff("geese"),                 39),  # 39 GEESE   boss window L
    (_nsff("krauser"),               40),  # 40 KRAUSER
    (_nsff("mrbig"),                 41),  # 41 MR.BIG
    (_nsff("eiji"),                  38),  # 42 EIJI    next to Rugal
    (_nsff("vega"),                  42),  # 43 VEGA    beside Mr. Big
    (_nsff("ryu"),                   43),  # 44 RYU     lower-right top-left
    (_nsff("ken"),                   44),  # 45 KEN
    (_nsff("chunli"),                45),  # 46 CHUN-LI
    (_nsff("sakura"),                46),  # 47 SAKURA  lower-right bottom-right
    # hidden Kyo EX variants (ids 48/49): L/R on the Kyo cell; they borrow
    # Kyo's cell for SelChrCell so returning from a fight re-seeds there.
    (_nsff("kyonests"),               3, True),
    (_nsff("kyoash"),                 3, True),
]

if os.environ.get("KOF_BASE4"):        # 8 MiB fallback: original roster
    ROSTER = ROSTER[:4]

BG_FRAME = (0, 44)          # final bg anim frame (cells + beams + bar)
CUR_P1 = (160, 0)           # active cursor sprites in system.sff
CUR_P2 = (170, 0)
CELL_BG = (150, 0)
ICON_SPR = (9000, 0)        # cell icon in each char sff

# extra cell rects (x0,y0,x1,y1) drawn where the two portrait windows
# used to live: 2x2 cells at the left and right window footprints.
NEW_CELLS = [(8, 143, 27, 165), (30, 143, 49, 165),
             (8, 168, 27, 190), (30, 168, 49, 190),
             (206, 143, 225, 165), (228, 143, 247, 165),
             (206, 168, 225, 190), (228, 168, 247, 190)]

# name/CPU-tag anchors (8px tile coords), kept from the face windows so
# the OBJ name row still reads "left side = P1, right side = P2".
FACE_L = 1                  # left anchor col (x8)
FACE_R = 25                 # right anchor col (x200)
FACE_ROW = 17               # CPU tag row (y136)
NAME_Y = 203                # OBJ name row under the bottom cells
CUR_SIZE = 24               # cursor ring px (3x3 tiles minus center)


def sprite_rgb(sff, group, number):
    """v2 PNG payload (4-byte prefix) -> PIL RGBA, honoring sff palette
    for already-indexed sprites."""
    sp = sff.get(group, number)
    if sp is None:
        raise ValueError(f"sprite {group},{number} not in {sff}")
    # true links (size==0) may resolve to a PNG payload sprite: chase the
    # link so the PNG fallback below reads the source sprite's data
    while sp.pix is None and getattr(sp, "size", 1) == 0 \
            and sp.link < len(sff.sprites):
        sp = sff.sprites[sp.link]
    if sp.pix is not None:
        im = Image.new("P", (sp.w, sp.h))
        im.putdata(sp.pix)
        pal = sff.palettes[sp.palidx] if sp.palidx is not None else None
        if pal:
            im.putpalette([c for rgb in pal for c in rgb]
                          + [0] * (768 - len(pal) * 3))
        im = im.convert("RGBA")
        # index 0 is the transparent color in mugen sprites
        if pal:
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    r, g, b, a = px[x, y]
                    if a == 255 and sp.pix[y * sp.w + x] == 0:
                        px[x, y] = (r, g, b, 0)
        return im, (sp.ax, sp.ay)
    # truecolor png payload
    import struct as st
    d = sff.data
    spr_ofs, nspr, _pal_ofs, _npal, lofs, _d1, tofs = st.unpack_from(
        "<7I", d, 0x24)
    for i in range(nspr):
        o = spr_ofs + i * 28
        (g, n, w, h, ax, ay, _link, _fmt, _dep, ofs, siz, _pi, fl) = \
            st.unpack_from("<hhHHhhHBBIIHH", d, o)
        if (g, n) == (sp.group, sp.number):
            base = tofs if fl & 1 else lofs
            raw = d[base + ofs: base + ofs + siz]
            if raw[:4] != b"\x89PNG":
                raw = raw[4:]
            return Image.open(io.BytesIO(raw)).convert("RGBA"), (ax, ay)
    raise ValueError(f"sprite {group},{number} payload not found")


def quant(img, colors):
    """img RGB -> (palette list[(r,g,b)] <=colors, index list row-major)."""
    q = img.quantize(colors=colors, method=Image.MEDIANCUT,
                     dither=Image.NONE)
    pal = [tuple(q.getpalette()[i * 3:i * 3 + 3])
           for i in range(colors)]
    return pal, list(q.getdata())


def find_cells(bg):
    """orange boxes -> [(x0,y0,x1,y1)] sorted row-major."""
    px = bg.load()
    seen = set()
    boxes = []
    for y in range(bg.height):
        for x in range(bg.width):
            if (x, y) in seen:
                continue
            p = px[x, y]
            if not (p[0] > 200 and 100 < p[1] < 200 and p[2] < 80):
                continue
            stack, xs, ys = [(x, y)], [], []
            seen.add((x, y))
            while stack:
                a, b = stack.pop()
                xs.append(a)
                ys.append(b)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = a + dx, b + dy
                    if (0 <= nx < bg.width and 0 <= ny < bg.height
                            and (nx, ny) not in seen):
                        q = px[nx, ny]
                        if q[0] > 200 and 100 < q[1] < 200 and q[2] < 80:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
            if len(xs) > 40:
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
    boxes.sort(key=lambda b: (b[1] // 16, b[0]))
    return boxes


def enc4(tile_pix):
    return tiles4bpp(tile_pix, 8, 8)[0]


class TileSet:
    """dedup pool of 4bpp tiles; append() -> tile index."""
    def __init__(self):
        self.lut = {}
        self.tiles = []

    def append(self, pix8x8):
        enc = enc4(pix8x8)
        if enc not in self.lut:
            self.lut[enc] = len(self.tiles)
            self.tiles.append(enc)
        return self.lut[enc]

    def blob(self):
        return b"".join(self.tiles)


def region_tiles(img, tileset, base_tile=0):
    """img WxH (multiple of 8) -> (mapwords list row-major via tileset)."""
    w, h = img.size
    out = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            px = [img.getpixel((tx * 8 + x, ty * 8 + y))
                  for y in range(8) for x in range(8)]
            out.append(tileset.append(px))
    return out


def main():
    os.makedirs(DST, exist_ok=True)
    sel_sff = Sff(os.path.join(KOF, "Select.sff"))
    sys_sff = Sff(os.path.join(KOF, "system.sff"))

    # ---- background: final anim frame, downscaled to the SNES screen ----
    bg640, _ = sprite_rgb(sel_sff, *BG_FRAME)
    bg = bg640.convert("RGB").resize((256, 224), Image.LANCZOS)

    # cells detected on the bare frame, plus the rects freed by removing
    # the portrait windows (NEW_CELLS) appended as cells 39+
    cells = find_cells(bg) + NEW_CELLS
    assert len(cells) == 39 + len(NEW_CELLS), \
        f"expected 39+{len(NEW_CELLS)} cells, got {len(cells)}"

    # ROSTER entries may carry a 3rd "hidden" element (Omega Rugal): it
    # owns no icon and simply borrows its mirror cell for SelChrCell.
    vis = [(cid, e[1]) for cid, e in enumerate(ROSTER) if len(e) == 2]

    # ---- occupied-cell faces: char icon composited inside the box ----
    faces_px = {}   # charid -> RGBA icon sized to the detected box
    for cid, cell in vis:
        sff_rel = ROSTER[cid][0]
        csff = Sff(os.path.join(CHARS, sff_rel))
        icon, _ = sprite_rgb(csff, *ICON_SPR)
        box = cells[cell]
        iw, ih = box[2] - box[0] - 1, box[3] - box[1] - 1
        # Preserve the portrait's aspect ratio and center it in the cell's
        # usable area. The newly added portraits have different source
        # bounds (Mr. Big is one pixel narrower), so stretching each sprite
        # to fill the box makes their faces appear uneven.
        scale = min(iw / icon.width, ih / icon.height)
        fw = max(1, min(iw, round(icon.width * scale)))
        fh = max(1, min(ih, round(icon.height * scale)))
        face = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
        face.alpha_composite(icon.resize((fw, fh), Image.Resampling.NEAREST),
                             ((iw - fw) // 2, (ih - fh) // 2))
        faces_px[cid] = face

    # composite into a bg copy: redraw every cell with the REAL cell sprite
    # (150,0: crisp white border + orange fill -- the 640->256 downscale had
    # been blurring them), then paste the occupied-cell icons inside.
    cellbox, _ = sprite_rgb(sys_sff, *CELL_BG)
    bgi = bg.copy()
    for box in cells:
        bgi.paste(cellbox.resize((box[2] - box[0] + 1, box[3] - box[1] + 1),
                                 Image.LANCZOS), (box[0], box[1]))
    for cid, cell in vis:
        box = cells[cell]
        bgi.paste(faces_px[cid], (box[0] + 1, box[1] + 1), faces_px[cid])

    # ---- palettes ------------------------------------------------------
    # pal0: whole composed art quantized to 15 colors.
    art_pal, art_idx = quant(bgi, 15)

    # icon pals: pals 1-7 (all free now that the face windows are gone)
    # groups are about six chars. Keep the final five portraits together so
    # Geese, Krauser, Mr. Big and Eiji share enough colors to remain legible.
    # Border colors stay pinned at idx
    # 1-3 so boundary tiles read the same no matter the pal bits.
    group_of = {}                    # charid -> palette index 1..7
    pals = [art_pal]
    cell_palidx = {}
    GRP = 6
    if len(vis) == 47:
        # Balance the seven SNES icon palettes. The lower-right fighters
        # share one palette group without overloading it with the old final
        # ten portraits.
        sizes = [7, 7, 7, 7, 7, 5, 7]
        palette_chunks, start = [], 0
        for size in sizes:
            palette_chunks.append(vis[start:start + size])
            start += size
    elif len(vis) > 36:
        # The last thirteen imported faces include the portraits with
        # distinctive palettes. Give the final group six faces, moving Heavy-D
        # into the preceding group instead of quantizing all six together.
        palette_chunks = ([vis[i:i + GRP] for i in range(0, 30, GRP)]
                          + [vis[30:37], vis[37:]])
    else:
        palette_chunks = [vis[i:i + GRP]
                          for i in range(0, len(vis), GRP)]
    for pidx, chunk in enumerate(palette_chunks, start=1):
        mw = max(faces_px[cid].width for cid, _cell in chunk)
        sheet = Image.new("RGB", (mw, sum(faces_px[cid].height
                                          for cid, _cell in chunk)))
        yoff, spans = 0, []
        for cid, _cell in chunk:
            im = faces_px[cid].convert("RGB")
            sheet.paste(im, (0, yoff))
            spans.append((cid, yoff, im.width, im.height))
            yoff += im.height
        spal, sidx = quant(sheet, 12)
        pals.append([(255, 255, 255), (245, 150, 10), (16, 24, 64)]
                    + spal)
        for cid, oy, iw, ih in spans:
            group_of[cid] = pidx
            cell_palidx[cid] = [sidx[(oy + r) * mw + c] + 4
                                for r in range(ih) for c in range(iw)]
    while len(pals) < 8:
        pals.append([(0, 0, 0)] * 15)

    # ---- tile pool -------------------------------------------------------
    ts = TileSet()
    mapw = [0] * (32 * 32)

    # art: whole composed frame quantized once to 15 colors -> pal0
    bpx = bgi.load()
    qfull = bgi.quantize(colors=15, method=Image.MEDIANCUT,
                         dither=Image.NONE)
    art_pal = [tuple(qfull.getpalette()[i * 3:i * 3 + 3]) for i in range(15)]
    qpx = qfull.load()
    # pixels of cell interiors that belong to a char pal get written later;
    # art tiles see raw quantized indices +1 (index0 reserved transparent)
    for ty in range(28):
        for tx in range(32):
            px = [qpx[tx * 8 + x, ty * 8 + y] + 1
                  for y in range(8) for x in range(8)]
            mapw[ty * 32 + tx] = ts.append(px)

    # Cells do not line up to the 8px SNES tile grid. Adjacent portraits can
    # therefore share a tile; compose each tile once so processing a later
    # cell cannot erase pixels from the previous one.
    owners = {}                 # (x,y) -> (charid, local_x, local_y)
    tile_candidates = {}        # (tx,ty) -> {charid: opaque pixel count}
    for cid, cell in vis:
        box = cells[cell]
        iw, ih = box[2] - box[0] - 1, box[3] - box[1] - 1
        for iy in range(ih):
            for ix in range(iw):
                gx, gy = box[0] + 1 + ix, box[1] + 1 + iy
                owners[(gx, gy)] = (cid, ix, iy)
                if faces_px[cid].getpixel((ix, iy))[3] >= 128:
                    key = (gx // 8, gy // 8)
                    by_char = tile_candidates.setdefault(key, {})
                    by_char[cid] = by_char.get(cid, 0) + 1
    for cid, cell in vis:
        box = cells[cell]
        x0 = max(0, box[0] - 1) // 8
        y0 = max(0, box[1] - 1) // 8
        x1 = min(255, box[2] + 1) // 8
        y1 = min(223, box[3] + 1) // 8
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                tile_candidates.setdefault((tx, ty), {}).setdefault(cid, 0)

    for (tx, ty), candidates in tile_candidates.items():
        # A shared tile gets the palette used by the most visible pixels.
        # Colors from another portrait are mapped to the nearest available
        # icon color in this tile's palette, preserving its silhouette.
        cid = max(candidates, key=candidates.get)
        pidx = group_of[cid]
        icon_colors = pals[pidx][3:15]
        outpx = []
        for y in range(8):
            for x in range(8):
                gx, gy = tx * 8 + x, ty * 8 + y
                owner = owners.get((gx, gy))
                if owner:
                    owner_cid, ix, iy = owner
                    ic = faces_px[owner_cid].getpixel((ix, iy))
                    if ic[3] < 128:
                        outpx.append(2)      # transparent -> orange
                    elif group_of[owner_cid] == pidx:
                        iw = faces_px[owner_cid].width
                        outpx.append(cell_palidx[owner_cid][iy * iw + ix])
                    else:
                        nearest = min(range(len(icon_colors)), key=lambda i:
                                      sum((ic[c] - icon_colors[i][c]) ** 2
                                          for c in range(3)))
                        outpx.append(nearest + 4)
                else:
                    p = bpx[gx, gy]
                    if p[0] > 200 and p[1] > 190 and p[2] > 190:
                        outpx.append(1)      # white border
                    elif p[0] > 200 and 100 < p[1] < 200 and p[2] < 80:
                        outpx.append(2)      # orange box
                    else:
                        outpx.append(3)      # bg/outline
        t = ts.append(outpx)
        mapw[ty * 32 + tx] = t | (pidx << 10)

    chr_b = ts.blob()
    map_b = b"".join(struct.pack("<H", w) for w in mapw)

    # BG palette file: pal0 art + pals 1-7 grouped icon pals (built above)
    pal_b = bytearray()
    for p in pals:
        pal_b += struct.pack("<H", 0)
        pal_b += b"".join(struct.pack("<H", snes_c(c)) for c in p[:15])

    inc = []
    inc.append("; generated by tools/build_select.py -- do not edit")
    inc.append(f"SEL_NTILES = {len(ts.tiles)}")
    inc.append(f"SEL_FACEL = {FACE_L}")
    inc.append(f"SEL_FACER = {FACE_R}")
    inc.append(f"SEL_FACEROW = {FACE_ROW}")
    inc.append(f"SEL_NAMEY = {NAME_Y}")
    inc.append("")

    # cell geometry for the engine: x,y (pixel), charid per cell
    inc.append(f"SEL_NCELLS = {len(cells)}")
    xs = "SelCellX: .db " + ",".join(str(b[0] - 2) for b in cells)
    ys = "SelCellY: .db " + ",".join(str(b[1] - 2) for b in cells)
    inc += [xs, ys]
    char_of = {cell: cid for cid, cell in vis}
    inc.append("SelCellChr: .db " + ",".join(str(char_of.get(i, 255))
               for i in range(len(cells))))
    chrcell = [ROSTER[cid][1] for cid in range(len(ROSTER))]
    inc.append("SelChrCell: .db " + ",".join(str(c) for c in chrcell))

    # movement neighbors: cell*4+dir -> nearest occupied cell (full table so
    # the runtime can index by the cursor's cell directly; empty cells point
    # at themselves and are unreachable)
    occ = sorted(char_of)
    def center(b):
        return ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
    move = []
    for cell in range(len(cells)):
        cx, cy = center(cells[cell])
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            best, bd = cell, 1 << 30
            for o in occ:
                if o == cell:
                    continue
                ox, oy = center(cells[o])
                vx, vy = ox - cx, oy - cy
                if dx and (vx * dx <= 8 or abs(vy) > abs(vx) * 2):
                    continue
                if dy and (vy * dy <= 8 or abs(vx) > abs(vy) * 2):
                    continue
                dd = vx * vx + vy * vy
                if dd < bd:
                    bd, best = dd, o
            move.append(best)
    inc.append("SelMoveTab: .db " + ",".join(str(v) for v in move))

    # ---- OBJ: cursor ring from system.sff 160,0 (neutral gray ramp in the
    # tile data; blue/red come from OBJ pals 2/3) ---------------------------
    cur1, _ = sprite_rgb(sys_sff, *CUR_P1)
    cur = cur1.resize((CUR_SIZE, CUR_SIZE), Image.LANCZOS)
    # grayscale indices by luminance of the bracket (alpha<128 -> 0)
    curpx = cur.load()
    ring = []
    for ty in range(3):
        for tx in range(3):
            if tx == 1 and ty == 1:
                continue                      # center stays transparent
            t = []
            for y in range(8):
                for x in range(8):
                    r, g, b, a = curpx[tx * 8 + x, ty * 8 + y]
                    if a < 128:
                        t.append(0)
                    else:
                        lum = (r + g + b) // 3
                        t.append(1 + min(14, lum * 15 // 256))
            ring.append(t)
    ots = TileSet()
    ring_idx = [ots.append(t) for t in ring]
    # locked-fill tile: checkerboard dither (dims the portrait under the ring)
    fill = [((x + y) & 1) * 8 + 1 for y in range(8) for x in range(8)]
    fill_idx = ots.append(fill)
    obj_chr = ots.blob()

    # OBJ pals: 2 cursor ramps + slot for a dim ring (unused font pals live
    # in MnObjPal which SelLoad still uploads first)
    def ramp(cr, cg, cb):
        return [(0, 0, 0)] + [(int(cr * i / 15), int(cg * i / 15),
                               int(cb * i / 15)) for i in range(15)]
    opal = ramp(90, 140, 255) + ramp(255, 80, 60)   # pals 2,3
    opal_b = b"".join(struct.pack("<H", snes_c(c)) for c in opal)

    inc.append(f"SEL_CUR_TILE = 48")
    inc.append("SelRingMap: .db "
               + ",".join(str(48 + i) for i in ring_idx))
    inc.append("SelRingX: .db 0,8,16,0,16,0,8,16")
    inc.append("SelRingY: .db 0,0,0,8,8,16,16,16")
    inc.append(f"SEL_FILL_TILE = {48 + fill_idx}")
    inc.append("")

    open(os.path.join(DST, "select.chr"), "wb").write(chr_b)
    open(os.path.join(DST, "select.map"), "wb").write(map_b)
    open(os.path.join(DST, "select.pal"), "wb").write(bytes(pal_b))
    open(os.path.join(DST, "selobj.chr"), "wb").write(obj_chr)
    open(os.path.join(DST, "selobj.pal"), "wb").write(opal_b)
    open(os.path.join(DST, "seldata.inc"), "w").write("\n".join(inc) + "\n")
    print(f"  select: {len(ts.tiles)} tiles ({len(chr_b)}B chr), "
          f"{len(cells)} cells, {len(ROSTER)} chars")


def snes_c(c):
    r, g, b = c
    return (r * 31 // 255) | ((g * 31 // 255) << 5) | ((b * 31 // 255) << 10)


if __name__ == "__main__":
    main()
