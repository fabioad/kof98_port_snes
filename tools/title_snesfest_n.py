"""Redraws the N of "THE SNESFEST" at the width of the other letters.

The edited arcade frame came with an N about 5 px wider than the H/U-style
two-stem letters.  This rebuilds that N pixel by pixel with the same rules the
arcade font uses (italic slant, 4 px faces, one color band per two rows, dark
blue extrusion 3 px to the right and 3 rows below), closes the gap by moving
"ESFEST" left and "THE S" right (the line keeps its center), and fills the
background that gets uncovered with the red texture from the untouched arcade
frame (THE SLUGFEST), or from the nearest clean texture where both frames had
text.

usage: python3 tools/title_snesfest_n.py [src.png] [arcade.png] [dst.png]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs/title_arcade/title_snesfest_src.png")
ARCADE = os.path.join(ROOT, "docs/title_arcade/title_slugfest_arcade.png")
DST = os.path.join(ROOT, "docs/title_arcade/title_snesfest.png")

Y0, Y1 = 118, 131                     # text rows (118..130)
X0, X1 = 84, 248                      # text columns
K = (0, 22, 138)                      # extrusion / outline
BAND = {118: (86, 169, 247), 119: (86, 169, 247),
        120: (103, 182, 247), 121: (103, 182, 247),
        122: (117, 190, 247), 123: (117, 190, 247),
        124: (152, 211, 255), 125: (152, 211, 255),
        126: (169, 217, 255), 127: (169, 217, 255)}
SLANT = {119: 0, 120: 0, 121: -1, 122: -1, 123: -2, 124: -2,
         125: -3, 126: -3, 127: -3}

N_BASE = 149                          # N left face x at row 120 (source)
E_BASE = 168                          # E left face x at row 120 (source)
R = int(os.environ.get("N_R", 9))                 # right stem offset (H uses 8)
DIAG_W = int(os.environ.get("N_W", 4))     # diagonal face width (horizontal)
FILL_SLIT = os.environ.get("N_FILL", "0") == "1"  # 4th shadow px into 1 px slits


def is_text(p):
    return not (p[1] < 30 and p[2] < 30)


def n_left(y, base):
    """First x of the N (incl. its outline) on row y."""
    if y <= 119:
        return base - 1
    if y <= 127:
        return base + SLANT[y] - (1 if y == 127 else 0)
    return base - 4 + (y - 128)


def e_left(y, base):
    """First x of the E on row y."""
    if y <= 119:
        return base
    if y <= 127:
        return base + SLANT[y] - (1 if y == 127 else 0)
    return base - 4 + (y - 128)


def draw_n(base):
    """{(x, y): rgb} for the new N with its left face at x=base on row 120."""
    face = {}
    for y in range(119, 128):
        t = (y - 119) / 8
        d = round(R * t)
        runs = set(range(0, 4)) | set(range(R, R + 4)) | \
            set(range(d, min(d + DIAG_W, R + 4)))
        if y == 127:                  # bottom bevel: one more pixel left
            runs |= {-1, R - 1}
        face[y] = sorted(base + SLANT[y] + u for u in runs)
    px = {}
    for y, xs in face.items():
        for x in xs:
            px[(x, y)] = BAND[y]
        s = set(xs)
        for x in xs:
            if x + 1 in s:
                continue
            # run ends at x: extrusion to the right
            if y == 119:
                n = 1
            else:
                n = 3
                gap = 0
                while gap < 6 and x + 1 + gap not in s:
                    gap += 1
                if gap == 4 and y >= 121 and FILL_SLIT:
                    n = 4             # fill the 1 px slit between faces
            for k in range(1, n + 1):
                if x + k not in s:
                    px[(x + k, y)] = K
        if y == 119:
            for x in xs:
                if x - 1 not in s:
                    px[(x - 1, y)] = K
    top = face[119]
    for x in top:                     # top bevel row
        for dx in (-1, 0, 1):
            px[(x + dx, 118)] = BAND[118]
    bot = sorted(face[127])
    runs, cur = [], [bot[0]]
    for x in bot[1:]:
        if x == cur[-1] + 1:
            cur.append(x)
        else:
            runs.append(cur)
            cur = [x]
    runs.append(cur)
    for r in runs:                    # bottom extrusion
        for i, y in enumerate((128, 129, 130)):
            for x in range(r[0] + i, r[-1] + 3):
                px[(x, y)] = K
    return px


def main(src=SRC, arcade=ARCADE, dst=DST):
    im = Image.open(src).convert("RGB")
    ar = Image.open(arcade).convert("RGB")
    W, H = im.size
    shrink = 13 - R                   # source N has its right stem at +13
    move_l = shrink // 2              # "THE S" moves right
    move_r = move_l - shrink          # "ESFEST" moves left

    # split the text layer into: left part, (old N, dropped), right part
    left, right = {}, {}
    for y in range(Y0, Y1):
        for x in range(X0, X1):
            p = im.getpixel((x, y))
            if not is_text(p):
                continue
            if x < n_left(y, N_BASE):
                left[(x, y)] = p
            elif x >= e_left(y, E_BASE):
                right[(x, y)] = p
    old_text = {(x, y) for y in range(Y0, Y1) for x in range(X0, X1)
                if is_text(im.getpixel((x, y)))}

    new = {}
    for (x, y), p in left.items():
        new[(x + move_l, y)] = p
    for (x, y), p in right.items():
        new[(x + move_r, y)] = p
    for xy, p in draw_n(N_BASE + move_l).items():
        # the N's extrusion never paints over a neighbour's face
        if p == K and xy in new and new[xy] != K:
            continue
        new[xy] = p

    out = im.copy()
    # background: arcade frame where it is clean there, else nearest clean
    holes = []
    for (x, y) in old_text:
        if (x, y) in new:
            continue
        a = ar.getpixel((x, y))
        if is_text(a):
            holes.append((x, y))
        else:
            out.putpixel((x, y), a)
    def clean(x, y):
        """Background pixel that is red texture in both frames, or None."""
        if not (0 <= x < W and 0 <= y < H):
            return None
        a, p = ar.getpixel((x, y)), im.getpixel((x, y))
        return p if (not is_text(a) and not is_text(p) and a == p) else None

    # copy from a whole-pixel offset (same offset for neighbours keeps the
    # texture's grain instead of smearing one colour)
    offsets = [(0, d) for d in (14, -14, 15, -15, 16, 13)] + \
              [(dx, d) for d in (14, 15, 16) for dx in (-8, 8, -16, 16)]
    for (x, y) in holes:
        for dx, dy in offsets:
            c = clean(x + dx, y + dy)
            if c:
                out.putpixel((x, y), c)
                break
        else:
            raise SystemExit(f"no texture for hole {(x, y)}")
    for (x, y), p in new.items():
        out.putpixel((x, y), p)
    out.save(dst)
    print(f"{dst}: N right stem +{R}, line shifted {move_l:+d}/{move_r:+d}, "
          f"{len(holes)} background px from texture")


if __name__ == "__main__":
    main(*sys.argv[1:4])
