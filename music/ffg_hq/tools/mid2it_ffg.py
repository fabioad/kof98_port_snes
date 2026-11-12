#!/usr/bin/env python3
"""MIDI -> Impulse Tracker (.it) for SNESMOD/smconv with the Capcom
(Final Fight Guy) BRR instruments extracted by ff_extract_samples.py.

Based on ddzeebo_port_snes/tools/mid2it_capcom.py (full arrangement, eight
voices, GM -> Capcom mapping) with these additions for the KOF98 port:

 * stereo: every MIDI channel keeps its CC10 pan (narrowed toward the
   centre); instruments that share a sample only differ by default pan,
   so the extra stereo costs no ARAM;
 * volume envelopes with a short release, so note-offs fade instead of
   clicking, and plucked/struck families decay naturally;
 * the least important IT channels are moved to 7-8, the voices the
   game's combat effects and streamed voices borrow first;
 * the global volume is a parameter, so the build can normalise loudness
   (SNESMOD scales by the IT global volume and ignores mixing volume).

usage: mid2it_ffg.py samples_dir out.it song.mid [--name N] [--mix 48]
"""
import argparse
import json
import os
import struct
import wave

import mido

NCH = 8
MAX_RATE = 127000          # S-DSP pitch limit is ~4x 32 kHz
STEREO_WIDTH = 0.6         # 1.0 = MIDI pan as is

# family -> (Capcom base sample, transpose, envelope kind, gain 0..64)
MELODIC = {
    'piano':   (12, 0, 'struck', 60),
    'epiano':  (1, 0, 'struck', 58),
    'chrom':   (13, 0, 'struck', 54),
    'organ':   (9, 0, 'held', 48),
    'guitar':  (0, 0, 'pluck', 56),
    'bass':    (3, 12, 'pluck', 64),
    'strings': (11, 0, 'held', 46),
    'brass':   (2, 0, 'held', 54),
    'reed':    (1, 0, 'held', 52),
    'pipe':    (13, 0, 'held', 50),
    'lead':    (9, 0, 'held', 54),
    'pad':     (11, 0, 'held', 40),
    'fx':      (10, 0, 'held', 40),
}
PRIORITY = {'bass': 88, 'lead': 84, 'guitar': 82, 'brass': 82, 'piano': 80,
            'epiano': 80, 'reed': 80, 'organ': 76, 'chrom': 76, 'pipe': 76,
            'strings': 70, 'pad': 64, 'fx': 60}


def gm_family(p):
    if p < 4: return 'piano'
    if p < 8: return 'epiano'
    if p < 16: return 'chrom'
    if p < 24: return 'organ'
    if p < 32: return 'guitar'
    if p < 40: return 'bass'
    if p < 56: return 'strings'
    if p < 64: return 'brass'
    if p < 72: return 'reed'
    if p < 80: return 'pipe'
    if p < 88: return 'lead'
    if p < 96: return 'pad'
    return 'fx'


# GM drum note -> (kit piece, IT note to play, priority)
DRUMS = {
    35: ('kick', 60, 95), 36: ('kick', 60, 95),
    38: ('snare', 60, 94), 40: ('snare', 60, 94), 39: ('snare', 64, 70),
    37: ('snare', 67, 50),
    41: ('tom', 55, 75), 43: ('tom', 58, 75), 45: ('tom', 61, 75),
    47: ('tom', 63, 75), 48: ('tom', 66, 75), 50: ('tom', 69, 75),
    42: ('hat', 64, 40), 44: ('hat', 64, 40), 46: ('ohat', 62, 45),
    49: ('crash', 60, 60), 57: ('crash', 62, 60), 55: ('crash', 66, 55),
    52: ('crash', 57, 55), 51: ('ride', 60, 45), 53: ('ride', 62, 45),
    59: ('ride', 60, 45),
}
# piece -> (sample id, length cap in samples or None, volume, pan 0..64)
KIT = {
    'kick': (7, None, 64, 32), 'snare': (6, None, 60, 32),
    'tom': (8, None, 58, 26), 'hat': (15, 1200, 34, 40),
    'ohat': (15, 3008, 34, 40), 'crash': (19, None, 46, 22),
    'ride': (17, None, 38, 42),
}

# envelope kind -> (nodes [(tick, level)], sustain node index)
# SNESMOD ignores IT fadeout; after a note-off the envelope just runs past
# its sustain node, so every shape reaches sustain quickly and then releases
# in 8 ticks (~100-170 ms) instead of ringing on.
ENVELOPES = {
    'held':   ([(0, 64), (2, 64), (10, 0)], 1),
    'struck': ([(0, 64), (4, 52), (24, 40), (32, 0)], 2),
    'pluck':  ([(0, 64), (3, 56), (20, 44), (28, 0)], 2),
}


def load_wav(path):
    w = wave.open(path)
    return list(struct.unpack('<%dh' % w.getnframes(), w.readframes(w.getnframes())))


# ---- MIDI -----------------------------------------------------------------
def read_midi(path):
    """-> notes [(start, end, note, vol0..1, ch, prog, pan)], tempos, ppq, end"""
    mf = mido.MidiFile(path)
    notes, tempos = [], []
    on = {}
    prog = [0] * 16
    cc7 = [100] * 16
    cc11 = [127] * 16
    pan = [64] * 16
    end = 0
    for tr in mf.tracks:
        t = 0
        for m in tr:
            t += m.time
            if m.type == 'set_tempo':
                tempos.append((t, m.tempo))
            elif m.type == 'program_change':
                prog[m.channel] = m.program
            elif m.type == 'control_change':
                if m.control == 7: cc7[m.channel] = m.value
                if m.control == 11: cc11[m.channel] = m.value
                if m.control == 10: pan[m.channel] = m.value
            elif m.type == 'note_on' and m.velocity:
                v = (m.velocity / 127) * (cc7[m.channel] / 127) * (cc11[m.channel] / 127)
                on.setdefault((m.channel, m.note), []).append(
                    (t, v, prog[m.channel], pan[m.channel]))
            elif m.type in ('note_off', 'note_on'):
                q = on.get((m.channel, m.note))
                if q:
                    st, v, p, pn = q.pop(0)
                    notes.append((st, t, m.note, v, m.channel, p, pn))
        end = max(end, t)
    for (ch, n), q in on.items():
        for st, v, p, pn in q:
            notes.append((st, end, n, v, ch, p, pn))
    tempos.sort()
    return notes, tempos or [(0, 500000)], mf.ticks_per_beat, end


def dedupe(notes, grid):
    """drop channels whose notes (on the row grid, any octave) are >=85%
    covered by an already-kept channel: chorus/unison/octave doublings"""
    by = {}
    for n in notes:
        if n[4] != 9:
            by.setdefault(n[4], set()).add((n[0] // grid, n[2] % 12))
    kept, drop = [], set()
    for ch in sorted(by, key=lambda c: (-len(by[c]), c)):
        s = by[ch]
        if any(len(s & by[k]) >= 0.85 * len(s) for k in kept):
            drop.add(ch)
        else:
            kept.append(ch)
    return [n for n in notes if n[4] not in drop], drop


# ---- IT writer ------------------------------------------------------------
def imps(name, pcm, c5, loop=None, vol=64):
    b = bytearray(80)
    b[0:4] = b'IMPS'
    b[4:16] = name[:12].encode().ljust(12, b'\0')
    b[17] = 64
    b[18] = 0x03 | (0x10 if loop else 0)
    b[19] = vol
    b[20:46] = name[:26].encode().ljust(26, b'\0')
    b[46] = 1
    lb, le = loop if loop else (0, 0)
    struct.pack_into('<IIIIII', b, 48, len(pcm), lb, le, c5, 0, 0)
    return b


def envelope(nodes, sustain):
    b = bytearray(82)
    b[0] = 0x01 | (0x04 if sustain is not None else 0)
    b[1] = len(nodes)
    if sustain is not None:
        b[4] = b[5] = sustain
    for i, (tick, level) in enumerate(nodes):
        struct.pack_into('<BH', b, 6 + 3 * i, level, tick)
    return b


def impi(name, smp_index, nna=0, fadeout=256, pan=None, gv=128, env=None):
    b = bytearray(554)
    b[0:4] = b'IMPI'
    b[4:16] = name[:12].encode().ljust(12, b'\0')
    # 0x11 NNA, 0x12 DCT, 0x13 DCA, 0x14 FadeOut, 0x16 PPS, 0x17 PPC,
    # 0x18 GbV, 0x19 DfP (bit7 = don't use), 0x1A RV, 0x1B RP, 0x1C TrkVers
    dfp = 0xA0 if pan is None else max(0, min(64, pan)) | 0x80
    struct.pack_into('<BBBHbBBBBBH', b, 0x11, nna, 0, 0, fadeout,
                     0, 60, gv, dfp, 0, 0, 0x0214)
    b[0x1E] = 1
    b[32:58] = name[:26].encode().ljust(26, b'\0')
    for n in range(120):
        b[64 + n * 2] = n
        b[65 + n * 2] = smp_index + 1
    if env:
        b[0x130:0x130 + 82] = envelope(*env)
    return b


def build_it(title, instruments, samples, patterns, orders, speed, tempo, pans, mix):
    """instruments: [(name, sample index, nna, pan, env)];
    samples: [(name, pcm, c5, loop, vol)]; patterns: [(rows, bytes)]"""
    ni, ns = len(instruments), len(samples)
    out = bytearray()
    out += b'IMPM' + title[:25].encode().ljust(26, b'\0')
    out += struct.pack('<H', 0x1004)
    out += struct.pack('<HHHHHHHH', len(orders), ni, ns, len(patterns),
                       0x0214, 0x0214, 0x000D, 0)   # stereo|instruments|linear
    out += bytes((mix, 48, speed, tempo, 128, 0))   # SNESMOD scales by GV
    out += struct.pack('<HII', 0, 0, 0)
    out += bytes(pans[i] if i < NCH else 128 for i in range(64))
    out += bytes([64] * 64)
    out += bytes(orders)
    para = len(out)
    out += b'\0' * (4 * (ni + ns + len(patterns)))
    pi = []
    for k, ins in enumerate(instruments):
        pi.append(len(out))
        name, smp, nna, pan, env = ins
        # Default pan wins over the channel pan (IT DfP with bit7 clear is
        # "use", so build the byte by hand: value only).
        blk = impi(name, smp, nna=nna, env=env)
        blk[0x19] = 0x80 if pan is None else max(0, min(64, pan))
        out += blk
    ps = []
    for s in samples:
        ps.append(len(out))
        out += imps(s[0], s[1], s[2], s[3], s[4])
    pp = []
    for rows, data in patterns:
        pp.append(len(out))
        out += struct.pack('<HH', len(data), rows) + b'\0' * 4 + data
    for k, s in enumerate(samples):
        struct.pack_into('<I', out, ps[k] + 72, len(out))
        out += struct.pack('<%dh' % len(s[1]), *s[1])
    struct.pack_into('<%dI' % ni, out, para, *pi)
    struct.pack_into('<%dI' % ns, out, para + 4 * ni, *ps)
    struct.pack_into('<%dI' % len(pp), out, para + 4 * (ni + ns), *pp)
    return bytes(out)


# ---- conversion -----------------------------------------------------------
def choose_grid(notes, ppq):
    """pick rows/beat (and speed so rows*speed = 24 ticks/beat)"""
    best = None
    for rpb, spd in ((4, 6), (6, 4), (8, 3), (12, 2)):
        err = sum(min(n[0] * rpb % ppq, ppq - n[0] * rpb % ppq) for n in notes) / ppq / max(1, len(notes))
        if best is None:
            best = (rpb, spd, err)
        if err < 0.02:
            return rpb, spd, err
        if err < best[2] * 0.6:
            best = (rpb, spd, err)
    return best


def pan_bucket(cc10):
    """MIDI CC10 -> IT pan 0..64 narrowed toward the centre, 8-step buckets"""
    p = 32 + (cc10 - 64) / 64 * 32 * STEREO_WIDTH
    return int(round(p / 4)) * 4


def convert(sdir, mid, out, name, mix=96, max_seconds=None):
    meta = json.load(open(os.path.join(sdir, 'samples.json')))['base']['samples']
    notes, tempos, ppq, end = read_midi(mid)
    total = -(-end // ppq) * ppq
    if max_seconds:
        # Cut very long songs at a bar so the module fits the ARAM budget.
        t, limit = 0.0, None
        for tick in range(0, total, ppq * 4):          # one 4/4 bar per step
            seg = [u for tt, u in tempos if tt <= tick]
            t += 4 * (seg[-1] if seg else tempos[0][1]) / 1e6
            if t > max_seconds:
                limit = tick + ppq * 4
                break
        if limit:
            total = limit
            notes = [(a, min(b, total), n, v, c, p, pn) for a, b, n, v, c, p, pn in notes if a < total]
    rpb, speed, qerr = choose_grid(notes, ppq)
    notes, dropped = dedupe(notes, ppq // rpb)
    row = lambda t: int(round(t * rpb / ppq))

    samples, smp_of = [], {}
    insts, ins_of = [], {}

    def add_sample(sid, c5, loop, vol, cap=None):
        key = (sid, cap)
        if key in smp_of:
            return smp_of[key]
        pcm = load_wav(os.path.join(sdir, 'base', 's%02d.wav' % sid))
        if cap:
            pcm = pcm[:cap]
            fade = min(256, len(pcm))
            for i in range(fade):
                pcm[-fade + i] = pcm[-fade + i] * (fade - i) // fade
        samples.append(('ffg%02d' % sid, pcm, c5, loop, vol))
        smp_of[key] = len(samples) - 1
        return smp_of[key]

    def add_inst(key, smp, nna, pan, env):
        if key in ins_of:
            return ins_of[key]
        insts.append(('%s %s' % (key[0], key[1]) if len(key) > 1 else key[0], smp, nna, pan, env))
        ins_of[key] = len(insts)
        return ins_of[key]

    def melodic_inst(prog, cc10):
        fam = gm_family(prog)
        sid, tr, kind, gain = MELODIC[fam]
        m = meta[str(sid)]
        period = m['length'] - m['loop_sample']
        c5 = int(round(261.626 * period))
        smp = add_sample(sid, c5, (m['loop_sample'], m['length']), gain)
        pan = pan_bucket(cc10)
        return add_inst((fam, pan), smp, 0, pan, ENVELOPES[kind]), c5, tr, fam

    evs = []
    maxv = max([n[3] for n in notes] or [1])
    for st, en, nt, v, ch, p, pn in notes:
        vol = max(8, min(64, int(round(64 * (v / maxv) ** 0.7))))
        r0 = row(st)
        if ch == 9:
            if nt not in DRUMS:
                continue
            piece, itn, prio = DRUMS[nt]
            sid, cap, dv, dpan = KIT[piece]
            smp = add_sample(sid, 32000, None, dv, cap)
            ins = add_inst((piece,), smp, 3, dpan, None)
            evs.append((r0, None, itn, ins, vol, prio, ch))
        else:
            ins, c5, tr, fam = melodic_inst(p, pn)
            n = nt + tr
            while n > 12 and c5 * 2 ** ((n - 60) / 12) > MAX_RATE:
                n -= 12
            r1 = max(row(en), r0 + 1)
            evs.append((r0, r1, n, ins, vol, PRIORITY[fam], ch))
    evs.sort(key=lambda e: (e[0], -e[5], -e[2]))

    # voice allocation
    busy = [None] * NCH        # (end_row, prio, srcch)
    cells = {}                 # (row, ch) -> [note, ins, vol, cmd, arg]
    weight = [0] * NCH
    lost = 0
    for r0, r1, n, ins, vol, prio, src in evs:
        free = [c for c in range(NCH) if busy[c] is None or busy[c][0] <= r0]
        free = [c for c in free if (r0, c) not in cells]
        cand = None
        if free:
            same = [c for c in free if busy[c] and busy[c][2] == src]
            cand = (same or free)[0]
        else:
            low = min((c for c in range(NCH) if (r0, c) not in cells),
                      key=lambda c: busy[c][1], default=None)
            if low is not None and busy[low][1] < prio:
                cand = low
        if cand is None:
            lost += 1
            continue
        cells[(r0, cand)] = [n, ins, vol, 0, 0]
        weight[cand] += prio
        busy[cand] = (r1, prio, src) if r1 is not None else (r0 + 1, prio, src)
    # note-offs where a melodic note ends before the channel's next note
    placed = sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0]))
    ends = {}
    for (r, c), cell in placed:
        ends.setdefault(c, []).append(r)
    end_of = {}
    for r0, r1, n, ins, vol, prio, src in evs:
        if r1 is not None:
            end_of.setdefault((r0, n, ins), r1)
    for c, rows in ends.items():
        for i, r in enumerate(rows):
            cell = cells[(r, c)]
            r1 = end_of.get((r, cell[0], cell[1]))
            if r1 is None:
                continue
            nxt = rows[i + 1] if i + 1 < len(rows) else None
            if nxt is None or r1 < nxt:
                if (r1, c) not in cells:
                    cells[(r1, c)] = [255, 0, None, 0, 0]   # note off (release)

    # most important channels first: 7-8 are the ones effects borrow
    order = sorted(range(NCH), key=lambda c: -weight[c])
    remap = {old: new for new, old in enumerate(order)}
    cells = {(r, remap[c]): v for (r, c), v in cells.items()}

    total_rows = row(total)
    tempo_rows = [(row(t), u) for t, u in tempos]

    def put_fx(r, cmd, arg):
        for c in range(NCH):
            cell = cells.get((r, c))
            if cell is None:
                cells[(r, c)] = [None, 0, None, cmd, arg]
                return
            if cell[3] == 0:
                cell[3], cell[4] = cmd, arg
                return
        raise SystemExit('no free effect slot at row %d' % r)

    bpm0 = None
    for r, u in tempo_rows:
        bpm = max(32, min(255, int(round(60000000 / u))))
        if r == 0 and bpm0 is None:
            bpm0 = bpm
        elif r < total_rows:
            put_fx(r, 20, bpm)          # Txx
    bpm0 = bpm0 or 120
    last = total_rows - 1
    # No Bxx: the song restarts at the end of the order list, and the last
    # pattern is cut to the song length (no trailing silence).  Keeping flow
    # commands out also lets it_pattern_limit repack long songs.

    npat = total_rows // 64 + 1
    pats = []
    for p in range(npat):
        data = bytearray()
        nrows = min(64, total_rows - p * 64)
        if nrows <= 0:
            break
        for r in range(nrows):
            gr = p * 64 + r
            for c in range(NCH):
                cell = cells.get((gr, c))
                if not cell:
                    continue
                note, ins, vol, cmd, arg = cell
                mask = 0
                body = bytearray()
                if note is not None:
                    mask |= 1; body.append(note)
                if ins:
                    mask |= 2; body.append(ins)
                if vol is not None:
                    mask |= 4; body.append(vol)
                if cmd:
                    mask |= 8; body += bytes((cmd, arg))
                data += bytes((0x80 | (c + 1), mask)) + body
            data.append(0)
        pats.append((nrows, bytes(data)))
    while pats and len(pats) - 1 > last // 64:
        pats.pop()
    orders = list(range(len(pats))) + [255]
    pans = [32] * NCH                   # instruments carry the stereo image
    it = build_it(name, insts, samples, pats, orders, speed, bpm0, pans, mix)
    open(out, 'wb').write(it)
    info = dict(name=name, midi=os.path.basename(mid), notes=len(notes),
                droppedChannels=sorted(c + 1 for c in dropped), rowsPerBeat=rpb,
                quantError=round(qerr, 3), bpm=bpm0, patterns=len(pats),
                instruments=len(insts), samples=len(samples), lostNotes=lost,
                mix=mix, rows=total_rows)
    print('%-16s %5d notes  dup-ch %-12s rpb %2d bpm %3d  %3d pat  %2d ins/%2d smp  lost %d'
          % (name, len(notes), info['droppedChannels'] or '-', rpb, bpm0,
             len(pats), len(insts), len(samples), lost))
    return info


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('samples')
    ap.add_argument('out')
    ap.add_argument('mid')
    ap.add_argument('--name', default=None)
    ap.add_argument('--mix', type=int, default=96, help='IT global volume 0..128')
    ap.add_argument('--max-seconds', type=float, default=None)
    a = ap.parse_args()
    convert(a.samples, a.mid, a.out, a.name or os.path.splitext(os.path.basename(a.out))[0],
            a.mix, a.max_seconds)
