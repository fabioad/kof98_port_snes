#!/usr/bin/env python3
"""Stand (Action 0) com mais quadros e ritmo de KOF98.

Parte dos 7 quadros 0,0..0,6 já com contorno reforçado e gera:
  * intercalações de 1 px no balanço do corpo (pés fixos; uma linha da
    coxa/joelho é duplicada ou removida, como num esticão de pixel art);
  * fita da bandana com atraso de um passo em relação ao corpo (movimento
    secundário contínuo, como bandana/cabelo de Kyo, Iori e Athena no KOF98),
    inclusive nas pausas do topo e do fundo do balanço.

Uso:
  python3 tools/stand_kof98.py preview   # só GIFs/PNG em output/
  python3 tools/stand_kof98.py apply     # grava 0,7..0,15 no SFF e Action 0 no AIR
"""
import struct
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from sff_reader import Sff  # noqa: E402

SFF = ROOT / 'Sakura.sff'
AIR = ROOT / 'Sakura.air'
OUT = ROOT / 'output'
W, H, OX, OY = 100, 112, 40, 104

# Deslocamento vertical da cabeça de cada quadro original (medido por
# alinhamento do rosto contra 0,0; negativo = para cima).
HEAD = [0, -3, -5, -3, 0, 1, 0]
# (corpo, ajuste vertical do tronco, fita, ticks). Cabeça resultante:
# 0,-2,-3,-4,-5,-5,-4,-3,-2,-1,0,+1,0,0 -> balanço senoidal com pausas.
SEQ = [(0, 0, 6, 4), (1, 1, 0, 4), (1, 0, 0, 4), (2, 1, 1, 4), (2, 0, 1, 5),
       (2, 0, 2, 5), (3, -1, 2, 4), (3, 0, 3, 4), (3, 1, 3, 4), (4, -1, 4, 4),
       (4, 0, 4, 4), (5, 0, 5, 5), (6, 0, 5, 4), (6, 0, 6, 4)]
CLSN = """Clsn2Default:2
  Clsn2[0] = -16,-76,23,-1
  Clsn2[1] = -8,-88,15,-65"""


def load(sff):
    frames = []
    for i in range(7):
        f = sff.get(0, i)
        a = np.frombuffer(f.pix, np.uint8).reshape(f.h, f.w)
        c = np.zeros((H, W), np.uint8)
        c[OY - f.ay:OY - f.ay + f.h, OX - f.ax:OX - f.ax + f.w] = a
        frames.append(c)
    return frames


def ribbon_mask(c, dy):
    """Fita da bandana: tons claros/contorno à esquerda da cabeça."""
    m = np.zeros(c.shape, bool)
    ylo, yhi, xhi = 18 + dy, 42 + dy, 33
    q = deque((y, x) for y in range(ylo, yhi) for x in range(xhi)
              if c[y, x] in (10, 11, 12))
    for y, x in q:
        m[y, x] = True
    while q:
        y, x = q.popleft()
        for ny in (y - 1, y, y + 1):
            for nx in (x - 1, x, x + 1):
                if ylo <= ny < yhi and 0 <= nx < xhi and not m[ny, nx] \
                        and 10 <= c[ny, nx] <= 15:
                    m[ny, nx] = True
                    q.append((ny, nx))
    # contorno encostado em pele/luva pertence ao corpo
    for y, x in zip(*np.nonzero(m)):
        if c[y, x] == 15 and any(1 <= c[y + a, x + b] <= 9 for a, b in
                                 ((1, 0), (-1, 0), (0, 1), (0, -1))):
            m[y, x] = False
    return m


def best_cut(c):
    return min(range(78, 96),
               key=lambda y: ((c[y] != c[y + 1]).sum(), abs(y - 86)))


def shift_body(c, d, cut):
    if d == 0:
        return c.copy()
    o = np.zeros_like(c)
    o[cut + 1:] = c[cut + 1:]
    if d < 0:
        o[:cut + 1 + d] = c[-d:cut + 1]
        o[cut + 1 + d:cut + 1] = c[cut]
    else:
        o[d:cut + 1] = c[:cut + 1 - d]
    return o


def vshift(a, dy):
    o = np.zeros_like(a)
    if dy >= 0:
        o[dy:] = a[:len(a) - dy]
    else:
        o[:dy] = a[-dy:]
    return o


def build(frames):
    masks = [ribbon_mask(frames[i], HEAD[i]) for i in range(7)]
    out = []
    for b, d, r, _ in SEQ:
        cut = best_cut(frames[b])
        body = shift_body(frames[b], d, cut)
        if r != b:
            body[shift_body(masks[b].astype(np.uint8), d, cut) > 0] = 0
            dy = HEAD[b] + d - HEAD[r]
            rib, mr = vshift(frames[r], dy), vshift(masks[r], dy)
            put = mr & (body == 0)  # fita fica atrás da luva e da cabeça
            body[put] = rib[put]
        out.append(body)
    return out


def palette(sff, bg=(60, 68, 84)):
    pal = [v for rgb in sff.palettes[sff.get(0, 0).palidx] for v in rgb]
    pal[0:3] = bg
    return pal


def previews(frames, out, pal):
    def im(c, s):
        i = Image.fromarray(c[12:110, 4:84], 'P')
        i.putpalette(pal)
        return i.resize((80 * s, 98 * s), Image.NEAREST)

    def save(ticks, path):
        imgs, durs, acc, prev, i = [], [], 0.0, 0, 0
        while i < len(ticks):
            j = i
            while j < len(ticks) and ticks[j] is ticks[i]:
                j += 1
            acc += (j - i) * 1000 / 60
            ms = int(round(acc / 10) * 10) - prev
            prev += ms
            imgs.append(ticks[i])
            durs.append(ms)
            i = j
        imgs[0].save(path, save_all=True, append_images=imgs[1:],
                     duration=durs, loop=0, disposal=1)

    new = [im(c, 4) for c in out]
    save([new[k] for k, s in enumerate(SEQ) for _ in range(s[3])],
         OUT / 'sakura-stand-novo.gif')
    old_ticks = [i for i in [0, 1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5]
                 for _ in range(6)]
    new_ticks = [k for k, s in enumerate(SEQ) for _ in range(s[3])]
    cache, seq = {}, []
    for t in range(len(new_ticks) * 4):
        key = (old_ticks[t % len(old_ticks)], new_ticks[t % len(new_ticks)])
        if key not in cache:
            a, b = im(frames[key[0]], 3).convert('RGB'), \
                im(out[key[1]], 3).convert('RGB')
            pair = Image.new('RGB', (a.width * 2 + 6, a.height), (20, 20, 24))
            pair.paste(a, (0, 0))
            pair.paste(b, (a.width + 6, 0))
            cache[key] = pair
        seq.append(cache[key])
    save(seq, OUT / 'sakura-stand-antes-depois.gif')
    sheet = np.concatenate([np.pad(c, ((0, 0), (0, 2))) for c in out], 1)
    s = Image.fromarray(sheet[12:110], 'P')
    s.putpalette(pal)
    s.resize((s.width * 3, s.height * 3), Image.NEAREST) \
        .save(OUT / 'sakura-stand-quadros.png')


def pcx(header, tail, a):
    h, w = a.shape
    stride = (w + 1) & ~1
    hd = bytearray(header)
    struct.pack_into('<HHHH', hd, 4, 0, 0, w - 1, h - 1)
    struct.pack_into('<H', hd, 66, stride)
    body = bytearray()
    for y in range(h):
        row = bytes(a[y]) + b'\0' * (stride - w)
        x = 0
        while x < stride:
            v, n = row[x], 1
            while x + n < stride and n < 63 and row[x + n] == v:
                n += 1
            if n > 1 or v >= 192:
                body += bytes((192 | n, v))
            else:
                body.append(v)
            x += n
    return bytes(hd) + bytes(body) + tail


def apply(frames, out):
    data = SFF.read_bytes()
    count, first = struct.unpack_from('<II', data, 20)
    recs, o = [], first
    for _ in range(count):
        hdr = bytearray(data[o:o + 32])
        size = struct.unpack_from('<I', hdr, 4)[0]
        recs.append([hdr, data[o + 32:o + 32 + size]])
        o = struct.unpack_from('<I', hdr, 0)[0]
    keys = [struct.unpack_from('<HH', r[0], 12) for r in recs]
    if (0, 7) in keys:
        sys.exit('0,7 já existe no SFF: stand KOF98 já aplicado.')
    pos = keys.index((0, 6))
    src_hdr, src_body = recs[pos]
    pcx_header = src_body[:128]
    # paleta final do PCX (marcador 0x0C + 768 bytes), se houver
    tail = src_body[-769:] if src_body[-769] == 0x0C else b''

    numbers, new = [], []
    nxt = 7
    for k, (b, d, r, _) in enumerate(SEQ):
        if d == 0 and b == r:
            numbers.append(b)
            continue
        numbers.append(nxt)
        c = out[k]
        ys, xs = np.nonzero(c)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        hdr = bytearray(src_hdr)
        body = pcx(pcx_header, tail, np.ascontiguousarray(c[y0:y1, x0:x1]))
        struct.pack_into('<hhHHHB', hdr, 8, OX - x0, OY - y0, 0, nxt, 0, 1)
        new.append([hdr, body])
        nxt += 1
    n = len(new)
    for hdr, body in recs:  # vínculos são índices: compensar a inserção
        link = struct.unpack_from('<H', hdr, 16)[0]
        if not body and link > pos:
            struct.pack_into('<H', hdr, 16, link + n)
    recs[pos + 1:pos + 1] = new
    parts, cur = [bytearray(data[:first])], first
    struct.pack_into('<I', parts[0], 20, len(recs))
    for i, (hdr, body) in enumerate(recs):
        cur += 32 + len(body)
        struct.pack_into('<II', hdr, 0, 0 if i == len(recs) - 1 else cur,
                         len(body))
        parts += [hdr, body]
    backup = ROOT / 'backups/Sakura.pre-stand-kof98.sff'
    if not backup.exists():
        backup.write_bytes(data)
    SFF.write_bytes(b''.join(parts))

    air = AIR.read_bytes().decode('latin-1')
    start = air.index('[Begin Action 0]')
    end = air.index('[Begin Action 5]')
    lines = ['[Begin Action 0]', '; Stand KOF98: 14 passos, fita com atraso',
             CLSN]
    lines += [f'0,{numbers[k]},0,0,{s[3]},,' for k, s in enumerate(SEQ)]
    abackup = ROOT / 'backups/Sakura.pre-stand-kof98.air'
    if not abackup.exists():
        abackup.write_bytes(AIR.read_bytes())
    newline = '\r\n' if '\r\n' in air[start:end] else '\n'
    AIR.write_bytes((air[:start] + newline.join(lines) + newline * 2
                     + air[end:]).encode('latin-1'))
    print(f'{n} sprites novos (0,7..0,{nxt - 1}); Action 0 = '
          + ' '.join(map(str, numbers)))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    sff = Sff(SFF)
    frames = load(sff)
    out = build(frames)
    OUT.mkdir(exist_ok=True)
    previews(frames, out, palette(sff))
    if mode == 'apply':
        apply(frames, out)


if __name__ == '__main__':
    main()
