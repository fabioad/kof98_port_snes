#!/usr/bin/env python3
"""Extract the Capcom sound-driver samples (BRR) from Final Fight Guy (J).

The game uploads a base APU image from $08:8000 (driver + 21 shared samples,
DIR=$4800, instrument table at $4A00, 6 bytes/instrument) and then one of 14
per-stage sample banks (table at $01:83E7) that extend the directory.

Output: <out>/<bank>/sNN.brr, sNN.wav and <out>/samples.json
usage: ff_extract_samples.py rom.sfc outdir
"""
import json, os, struct, sys, wave

ROM = sys.argv[1]
OUT = sys.argv[2]
d = open(ROM, 'rb').read()


def lo2file(a):
    return ((a >> 16) & 0x7f) * 0x8000 + ((a & 0xffff) - 0x8000)


def parse_stream(ptr):
    a = ptr
    def byte():
        nonlocal a
        v = d[lo2file(a)]
        a += 1
        if a & 0xffff == 0:
            a += 0x8000
        return v
    def word():
        return byte() | byte() << 8
    blocks = []
    while True:
        n = word(); dst = word()
        if n == 0:
            return blocks
        blocks.append((dst, bytes(byte() for _ in range(n))))


def brr_decode(ram, start):
    """Decode BRR starting at start; returns (pcm list, brr bytes, loop_block_index or None)."""
    out = []; p1 = p2 = 0; pos = start; raw = bytearray()
    for _ in range(4000):
        hdr = ram[pos]
        shift = hdr >> 4; filt = (hdr >> 2) & 3
        raw += ram[pos:pos + 9]
        for i in range(16):
            b = ram[pos + 1 + i // 2]
            n = (b >> 4) if i % 2 == 0 else (b & 15)
            if n >= 8: n -= 16
            s = (n << shift) >> 1 if shift <= 12 else (-2048 if n < 0 else 0)
            if filt == 1: s += p1 + ((-p1) >> 4)
            elif filt == 2: s += (p1 << 1) + ((-p1 * 3) >> 5) - p2 + (p2 >> 4)
            elif filt == 3: s += (p1 << 1) + ((-p1 * 13) >> 6) - p2 + ((p2 * 3) >> 4)
            s = max(-32768, min(32767, s))
            s = ((s << 1) & 0xffff); s = s - 0x10000 if s & 0x8000 else s
            s >>= 1
            p2, p1 = p1, s
            out.append(s << 1)
        pos += 9
        if hdr & 1:
            return out, bytes(raw), bool(hdr & 2)
    return out, bytes(raw), False


def write_wav(path, pcm, rate=32000):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in pcm))


def dump_bank(name, ram, idx_range, inst_tab, ninst):
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    meta = {'samples': {}, 'instruments': []}
    for i in idx_range:
        st, lp = struct.unpack_from('<HH', ram, 0x4800 + i * 4)
        if st in (0, 0xffff):
            continue
        pcm, raw, loops = brr_decode(ram, st)
        loop_smp = (lp - st) // 9 * 16 if loops else None
        open(os.path.join(OUT, name, f's{i:02d}.brr'), 'wb').write(raw)
        write_wav(os.path.join(OUT, name, f's{i:02d}.wav'), pcm)
        peak = max(abs(x) for x in pcm) or 1
        zc = sum(1 for a, b in zip(pcm, pcm[1:]) if (a < 0) != (b < 0)) / max(1, len(pcm))
        meta['samples'][i] = dict(start=st, loop=lp, loops=loops, loop_sample=loop_smp,
                                  length=len(pcm), peak=peak, zcr=round(zc, 4))
    for k in range(ninst):
        e = ram[inst_tab + k * 6: inst_tab + k * 6 + 6]
        if e[0] == 0xff and e[1] == 0xff:
            break
        meta['instruments'].append(dict(srcn=e[0], adsr1=e[1], adsr2=e[2], gain=e[3],
                                        pitch=(e[4] << 8) | e[5]))
    return meta


def main():
    base = bytearray(0x10000)
    for a, x in parse_stream(0x088000):
        base[a:a + len(x)] = x
    allmeta = {'base': dump_bank('base', base, range(0, 21), 0x4a00, 21)}
    tab = lo2file(0x0183E7)
    seen = {}
    for b in range(14):
        p = d[tab + b * 3] | d[tab + b * 3 + 1] << 8 | d[tab + b * 3 + 2] << 16
        if p in seen:
            continue
        seen[p] = b
        ram = bytearray(base)
        bl = parse_stream(p)
        for a, x in bl:
            ram[a:a + len(x)] = x
        first = (bl[0][0] - 0x4800) // 4
        cnt = len(bl[0][1]) // 4
        itab = bl[1][0]
        allmeta[f'bank{b:02d}'] = dump_bank(f'bank{b:02d}', ram, range(first, first + cnt), 0x4a00, (itab - 0x4a00) // 6 + len(bl[1][1]) // 6)
        allmeta[f'bank{b:02d}']['instruments'] = allmeta[f'bank{b:02d}']['instruments'][(itab - 0x4a00) // 6:]
    json.dump(allmeta, open(os.path.join(OUT, 'samples.json'), 'w'), indent=1)
    for k, v in allmeta.items():
        print(k, len(v['samples']), 'samples', len(v['instruments']), 'instruments')


main()
