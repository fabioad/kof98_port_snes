#!/usr/bin/env python3
"""SFF v1/v2 reader + SNES 4bpp converter.

Usage:
  sff.py list <file.sff>
  sff.py dump <file.sff> --out dir/          # indexed PNGs + meta.json
"""
import io
import json
import os
import struct
import sys


class Sprite:
    __slots__ = ("group", "number", "w", "h", "ax", "ay", "palidx",
                 "pix", "link", "size")


def _rle8_decode(rle, w, h):
    p = bytearray(w * h)
    i = j = 0
    n = len(rle)
    while j < len(p) and i < n:
        d = rle[i]
        i += 1
        cnt = 1
        if d & 0xC0 == 0x40:
            cnt = d & 0x3F
            d = rle[i] if i < n else 0
            i += 1
        for _ in range(cnt):
            if j < len(p):
                p[j] = d
                j += 1
    return bytes(p)


def _rle5_decode(rle, w, h):
    p = bytearray(w * h)
    i = j = 0
    n = len(rle)
    while j < len(p) and i < n:
        rl = rle[i]
        i += 1
        dl = rle[i] & 0x7F if i < n else 0
        c = 0
        if i < n and rle[i] >> 7:
            i += 1
            c = rle[i] if i < n else 0
        i += 1
        while True:
            if j < len(p):
                p[j] = c
                j += 1
            rl -= 1
            if rl < 0:
                dl -= 1
                if dl < 0:
                    break
                c = rle[i] & 0x1F if i < n else 0
                rl = rle[i] >> 5 if i < n else 0
                i += 1
    return bytes(p)


def _lz5_decode(rle, w, h):
    p = bytearray(w * h)
    i = j = 0
    n = len(rle)
    if not n:
        return bytes(p)
    ct = rle[i]
    i += 1
    cts = 0
    rb = 0
    rbc = 0
    while j < len(p) and i < n:
        d = rle[i]
        i += 1
        if ct & (1 << cts):
            if d & 0x3F == 0:
                d = ((d << 2) | (rle[i] if i < n else 0)) + 1
                i += 1
                cnt = (rle[i] if i < n else 0) + 2
                i += 1
            else:
                rb |= (d & 0xC0) >> rbc
                rbc += 2
                cnt = d & 0x3F
                if rbc < 8:
                    d = (rle[i] if i < n else 0) + 1
                    i += 1
                else:
                    d = rb + 1
                    rb = rbc = 0
            while True:
                if j < len(p):
                    p[j] = p[j - d]
                    j += 1
                cnt -= 1
                if cnt < 0:
                    break
        else:
            if d & 0xE0 == 0:
                cnt = (rle[i] if i < n else 0) + 8
                i += 1
            else:
                cnt = d >> 5
                d &= 0x1F
            for _ in range(cnt):
                if j < len(p):
                    p[j] = d
                    j += 1
        cts += 1
        if cts >= 8:
            ct = rle[i] if i < n else 0
            i += 1
            cts = 0
    return bytes(p)


class Sff:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        d = self.data
        if d[:12] != b"ElecbyteSpr\x00":
            raise ValueError("not an SFF")
        self.ver0 = d[15]
        self.sprites = []
        self.palettes = []  # list of list of (r,g,b)
        if self.ver0 == 1:
            self._parse_v1()
        else:
            self._parse_v2()

    def _parse_v1(self):
        d = self.data
        count, shofs = struct.unpack_from("<II", d, 0x14)
        shared = d[0x24]  # 1 = shared palette
        subofs = shofs
        pals = []
        for _ in range(count):
            (xofs, size, ax, ay, group, number, link, samepal) = \
                struct.unpack_from("<IIhhHHHB", d, subofs)
            s = Sprite()
            s.group, s.number, s.ax, s.ay = group, number, ax, ay
            s.link = link
            s.palidx = None
            s.size = size
            if size == 0:
                s.pix = None
                s.w = s.h = 0
            else:
                pcx = d[subofs + 32:subofs + 32 + size]
                s.w, s.h, s.pix, pal = _pcx_decode(pcx)
                if not samepal or len(pals) == 0:
                    pals.append(pal)
                    s.palidx = len(pals) - 1
                else:
                    s.palidx = len(pals) - 1
            self.sprites.append(s)
            subofs = xofs
        self.palettes = pals
        for s in self.sprites:
            if s.pix is None and s.size == 0 \
                    and s.link < len(self.sprites):
                src = self.sprites[s.link]
                s.pix, s.w, s.h = src.pix, src.w, src.h
                s.palidx = src.palidx

    def _parse_v2(self):
        d = self.data
        (spr_ofs, nspr, pal_ofs, npal, lofs, _d1, tofs) = \
            struct.unpack_from("<7I", d, 0x24)
        nodes = []
        for i in range(nspr):
            o = spr_ofs + i * 28
            (group, number, w, h, ax, ay, link, fmt, depth,
             ofs, size, palidx, flags) = \
                struct.unpack_from("<hhHHhhHBBIIHH", d, o)
            nodes.append((group, number, w, h, ax, ay, link, fmt,
                          depth, ofs, size, palidx, flags))
        for (group, number, w, h, ax, ay, link, fmt, depth,
             ofs, size, palidx, flags) in nodes:
            s = Sprite()
            s.group, s.number = group, number
            s.w, s.h, s.ax, s.ay = w, h, ax, ay
            s.link = link
            s.palidx = palidx
            s.pix = None
            s.size = size
            if size:
                base = tofs if flags & 1 else lofs
                raw = d[base + ofs: base + ofs + size]
                if fmt == 0:
                    s.pix = raw[:w * h] if depth == 8 else None
                elif fmt == 2:
                    s.pix = _rle8_decode(raw[4:], w, h)
                elif fmt == 3:
                    s.pix = _rle5_decode(raw[4:], w, h)
                elif fmt == 4:
                    s.pix = _lz5_decode(raw[4:], w, h)
                elif fmt in (10, 11, 12):
                    s.pix = _png_decode(raw[4:], fmt)
            self.sprites.append(s)
        for i in range(npal):
            o = pal_ofs + i * 16
            group, number, numcols, link, ofs, siz = \
                struct.unpack_from("<hhhHII", d, o)
            if siz == 0 or siz == 0x80000000:
                self.palettes.append(None)
                continue
            raw = d[lofs + ofs: lofs + ofs + siz]
            pal = []
            for k in range(min(siz // 4, 256)):
                r, g, b, a = raw[k * 4:k * 4 + 4]
                pal.append((r, g, b))
            self.palettes.append(pal)
        # resolve linked sprite copies: only sprites with NO payload of their
        # own (size == 0) are true links -- a fmt-12 PNG sprite must not fall
        # back to sprite[0] just because link defaults to 0
        for s in self.sprites:
            if s.pix is None and s.size == 0 \
                    and s.link < len(self.sprites):
                src = self.sprites[s.link]
                s.pix, s.w, s.h = src.pix, src.w, src.h
        for i, p in enumerate(self.palettes):
            if p is None:
                o = pal_ofs + i * 16
                _, _, _, link, _, _ = struct.unpack_from("<hhhHII", d, o)
                if link < len(self.palettes):
                    self.palettes[i] = self.palettes[link]

    def get(self, group, number):
        for s in self.sprites:
            if s.group == group and s.number == number:
                return s
        return None


def _pcx_decode(pcx):
    """Decode Elecbyte PCX blob -> (w, h, indexed pixels, palette)."""
    if pcx[:12] == b"ElecbytePcx\x00":
        pcx = pcx[12:]
    bio = io.BytesIO(pcx)
    hdr = bio.read(128)
    w = struct.unpack_from("<H", hdr, 8)[0] - struct.unpack_from("<H", hdr, 4)[0] + 1
    h = struct.unpack_from("<H", hdr, 10)[0] - struct.unpack_from("<H", hdr, 6)[0] + 1
    bpl = struct.unpack_from("<H", hdr, 66)[0]
    img = bytearray()
    while len(img) < bpl * h:
        b = bio.read(1)
        if not b:
            break
        b = b[0]
        if b & 0xC0 == 0xC0:
            img += bio.read(1) * (b & 0x3F)
        else:
            img.append(b)
    # palette at end, marker 0x0C + 768 bytes
    tail = pcx[-769:]
    pal = [(0, 0, 0)] * 256
    if len(tail) == 769 and tail[0] == 0x0C:
        pal = [tuple(tail[1 + i * 3: 4 + i * 3]) for i in range(256)]
    pix = b"".join(img[r * bpl: r * bpl + w] for r in range(h))
    return w, h, pix, pal


def _png_decode(raw, fmt):
    from PIL import Image
    img = Image.open(io.BytesIO(raw))
    if fmt == 10:
        return bytes(img.convert("P").tobytes())
    return None  # truecolor not supported for 4bpp output


def snes_pal(pal, ncolors=16):
    """RGB888 palette -> SNES BGR555 words (index 0 forced 0)."""
    out = bytearray()
    for i in range(ncolors):
        r, g, b = pal[i] if i < len(pal) else (0, 0, 0)
        out += struct.pack("<H", (b >> 3) << 10 | (g >> 3) << 5 | (r >> 3))
    return bytes(out)


def tiles4bpp(pix, w, h, remap=None):
    """Indexed pixels -> SNES 4bpp tile stream (8x8 tiles, row major)."""
    tw, th = (w + 7) // 8, (h + 7) // 8
    out = bytearray()
    for ty in range(th):
        for tx in range(tw):
            for plane in (0, 2):
                for row in range(8):
                    y = ty * 8 + row
                    lo = hi = 0
                    for x in range(8):
                        px = pix[y * w + tx * 8 + x] if y < h and tx * 8 + x < w else 0
                        if remap:
                            px = remap[px]
                        bit = 7 - x
                        if plane == 0:
                            lo |= (px & 1) << bit
                            hi |= (px >> 1 & 1) << bit
                        else:
                            lo |= (px >> 2 & 1) << bit
                            hi |= (px >> 3 & 1) << bit
                    out += bytes((lo, hi))
    return bytes(out), tw, th


def cmd_list(path):
    s = Sff(path)
    print(f"{path}: SFF v{s.ver0}, {len(s.sprites)} sprites, "
          f"{len(s.palettes)} palettes")
    groups = {}
    for sp in s.sprites:
        groups.setdefault(sp.group, 0)
        groups[sp.group] += 1
    for g in sorted(groups):
        print(f"  group {g}: {groups[g]} sprites")


def cmd_dump(path, out):
    from PIL import Image
    os.makedirs(out, exist_ok=True)
    s = Sff(path)
    meta = []
    for i, sp in enumerate(s.sprites):
        name = f"{sp.group}_{sp.number}"
        if sp.pix and s.palettes and sp.palidx is not None and \
                sp.palidx < len(s.palettes) and s.palettes[sp.palidx]:
            pal = [c for rgb in s.palettes[sp.palidx] for c in rgb]
            pal += [0] * (768 - len(pal))
            img = Image.frombytes("P", (sp.w, sp.h), sp.pix)
            img.putpalette(pal)
            img.save(os.path.join(out, name + ".png"))
        meta.append({"group": sp.group, "number": sp.number, "w": sp.w,
                     "h": sp.h, "ax": sp.ax, "ay": sp.ay,
                     "pal": sp.palidx, "empty": sp.pix is None})
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=0)
    print(f"dumped {len(meta)} sprite entries to {out}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "list":
        cmd_list(sys.argv[2])
    elif len(sys.argv) >= 5 and sys.argv[1] == "dump":
        cmd_dump(sys.argv[2], sys.argv[4])
    else:
        print(__doc__)
