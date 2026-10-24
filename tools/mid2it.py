#!/usr/bin/env python3
# mid2it.py - MIDI -> Impulse Tracker (.it) via template splice.
#
# smconv's IT loader is picky about generated files, so instead of
# writing a .it from scratch we take a known-good template .it and
# replace ONLY the order list + patterns. Header, instruments and
# samples come through untouched.
#
# Template: any working .it (we use pvsneslib's overworld.it).
# Mapping: all melodic MIDI channels -> template instrument 1,
# MIDI ch10 (drums) -> instrument 2.
#
# usage: mid2it.py in.mid template.it out.it

import argparse
import struct

ROWS_PER_BEAT = 4          # keep each module within SPC RAM alongside SFX
IT_SPEED      = 6          # ticks/row -> effective 24 ticks/beat
TEMPLATE_CH   = 8          # channels available in the template patterns


def read_vlq(b, i):
    v = 0
    while True:
        c = b[i]; i += 1
        v = (v << 7) | (c & 0x7F)
        if not (c & 0x80):
            return v, i


def parse_midi(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'MThd'
    hlen, fmt, ntrk, div = struct.unpack('>IH HH', d[4:14])
    trks = []
    off = 8 + hlen
    for _ in range(ntrk):
        ln = struct.unpack('>I', d[off+4:off+8])[0]
        trks.append(d[off+8:off+8+ln])
        off += 8 + ln

    notes_on = {}
    notes = []
    tempos = []
    max_tick = 0
    for t in trks:
        i = 0; tick = 0; running = 0
        while i < len(t):
            delta, i = read_vlq(t, i)
            tick += delta
            st = t[i]
            if st < 0x80:
                st = running
            else:
                running = st
                i += 1
            if st == 0xFF:
                ty = t[i]; ln = t[i+1]; i += 2
                data = t[i:i+ln]; i += ln
                if ty == 0x51:
                    tempos.append((tick, int.from_bytes(data, 'big')))
                if ty == 0x2F:
                    break
            elif st in (0xF0, 0xF7):
                ln = t[i]; i += 1 + ln
            else:
                typ = st & 0xF0; ch = st & 0x0F
                if typ in (0xC0, 0xD0):
                    i += 1
                else:
                    d1 = t[i]; d2 = t[i+1]; i += 2
                    if typ == 0x90 and d2:
                        notes_on.setdefault((ch, d1), []).append((tick, d2))
                    elif typ in (0x80, 0x90):
                        q = notes_on.get((ch, d1))
                        if q:
                            st0, vel = q.pop(0)
                            notes.append((st0, tick, d1, vel, ch))
        max_tick = max(max_tick, tick)
    return notes, div, (tempos[0][1] if tempos else 500000), max_tick


def splice(mid, tpl_path, out_path, drop_channels=(), drop_drums=(),
           drum_stride=1, transpose=0):
    notes, div, tempo, max_tick = parse_midi(mid)
    drum_count = {}
    kept = []
    for n in notes:
        if n[4] in drop_channels or (n[4] == 9 and n[2] in drop_drums):
            continue
        if n[4] == 9:
            drum_count[n[2]] = drum_count.get(n[2], 0) + 1
            if (drum_count[n[2]] - 1) % drum_stride:
                continue
        kept.append(n)
    notes = kept
    scale = ROWS_PER_BEAT / div
    total_rows = int(max_tick * scale) + 64

    # MIDI channel -> template channel + instrument
    # ch9 (drums) -> tpl ch7/ins2 ; melodic -> round-robin tpl ch0-6, ins1
    mel = {}
    next_ch = 0
    ev = {}
    last_end = {}   # template channel -> end row of its latest note;
                    # an explicit cut is only needed before a real gap
    for st, en, nt, vel, ch in sorted(notes):
        if ch == 9:
            tc, ins = 7, 2
        else:
            if ch not in mel:
                mel[ch] = next_ch % 7
                next_ch += 1
            tc, ins = mel[ch], 1
        r0 = int(st * scale)
        r1 = max(int(en * scale), r0 + 1)
        if ch != 9 and last_end.get(tc, -1) < r0 and tc in last_end:
            ev.setdefault(last_end[tc], []).append((tc, 0xFF, ins, 0))
        ev.setdefault(r0, []).append((tc, nt + transpose, ins, vel))
        if ch == 9:      # drums: short hit, cut quickly
            ev.setdefault(min(r0 + 2, r1), []).append((tc, 0xFF, ins, 0))
        else:
            last_end[tc] = max(last_end.get(tc, 0), r1)
    for tc, r1 in last_end.items():     # last note per channel
        ev.setdefault(r1, []).append((tc, 0xFF, 0, 0))
    for rows in ev.values():
        # snesmod reads ONE mask group per channel, in channel order:
        # merge collisions (a new note already cuts the previous one)
        # and sort by channel so the emitted groups line up with the
        # driver's channel-bit walk.
        rows.sort(key=lambda e: (e[0], e[1] == 0xFF))
        merged = []
        for e in rows:
            if merged and merged[-1][0] == e[0]:
                continue
            merged.append(e)
        rows[:] = merged

    npat = (total_rows + 63) // 64
    pats = []
    for pi in range(npat):
        rows = bytearray()
        for r in range(64):
            gr = pi * 64 + r
            if gr in ev:
                for tc, note, ins, vel in ev[gr]:
                    rows += bytes([0x80 | (tc + 1), 0x07,
                                   note & 0xFF, ins,
                                   min(64, vel // 2)])
            rows.append(0)
        pats.append(bytes(rows))

    t = open(tpl_path, 'rb').read()
    ordnum, insnum, smpnum, patnum = struct.unpack('<4H', t[0x20:0x28])
    orders = bytes(range(npat))

    # rebuild file: header(0xC0) + orders + ins/smp para + pat para + blob
    hdr = bytearray(t[:0xC0])
    struct.pack_into('<H', hdr, 0x20, npat)     # ordnum
    struct.pack_into('<H', hdr, 0x26, npat)     # patnum
    hdr[0x32] = IT_SPEED
    hdr[0x33] = max(32, min(255, int(60000000 / tempo)))
    # channel pans: enable TEMPLATE_CH channels
    for i in range(64):
        hdr[0x40 + i] = 32 if i < TEMPLATE_CH else 0xA0
        hdr[0x80 + i] = 64 if i < TEMPLATE_CH else 0

    ins_para = list(struct.unpack('<%dI' % insnum, t[0xC0+ordnum:0xC0+ordnum+4*insnum]))
    smp_para = list(struct.unpack('<%dI' % smpnum, t[0xC0+ordnum+4*insnum:0xC0+ordnum+4*(insnum+smpnum)]))
    pat_para = list(struct.unpack('<%dI' % patnum, t[0xC0+ordnum+4*(insnum+smpnum):0xC0+ordnum+4*(insnum+smpnum+patnum)]))

    # instrument+sample blob: from first ins para to first pat para
    blob_start = min(ins_para + smp_para)
    blob_end = min(pat_para)
    inssmp = t[blob_start:blob_end]

    base = 0xC0 + len(orders) + 4 * (insnum + smpnum + npat)
    blob_off = base
    new_ins = [blob_off + (p - blob_start) for p in ins_para]
    new_smp = [blob_off + (p - blob_start) for p in smp_para]
    cur = blob_off + len(inssmp)
    pat_blk = bytearray()
    new_pat = []
    for pd in pats:
        new_pat.append(cur)
        blk = struct.pack('<HH', len(pd), 64) + b'\0' * 4 + pd
        pat_blk += blk
        cur += len(blk)

    out = bytearray(hdr + orders)
    for v in new_ins: out += struct.pack('<I', v)
    for v in new_smp: out += struct.pack('<I', v)
    for v in new_pat: out += struct.pack('<I', v)
    out += inssmp + bytes(pat_blk)

    # The copied IMPS headers still carry the template's SamplePointer
    # values, which now land inside the pattern block.  Append each
    # sample's PCM data after the patterns and fix the pointer.
    for i, para in enumerate(smp_para):
        if not para:
            continue
        flags = t[para + 0x12]
        slen = struct.unpack_from('<I', t, para + 0x30)[0]
        src = struct.unpack_from('<I', t, para + 0x48)[0]
        nbytes = slen * (2 if flags & 0x02 else 1) * (2 if flags & 0x04 else 1)
        if not (flags & 0x01) or not nbytes or src + nbytes > len(t):
            struct.pack_into('<I', out, new_smp[i] + 0x48, 0)
            continue
        struct.pack_into('<I', out, new_smp[i] + 0x48, len(out))
        out += t[src:src + nbytes]
    open(out_path, 'wb').write(bytes(out))
    print(f'{mid}: {len(notes)} notes, {npat} patterns, bpm {int(60000000/tempo)} -> {out_path}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('midi')
    ap.add_argument('template')
    ap.add_argument('output')
    ap.add_argument('--drop-channels', default='')
    ap.add_argument('--drop-drums', default='')
    ap.add_argument('--drum-stride', type=int, default=1)
    ap.add_argument('--transpose', type=int, default=0,
                    help='extra semitones on top of the MIDI note')
    a = ap.parse_args()
    def nums(s):
        return {int(x) for x in s.split(',') if x}
    splice(a.midi, a.template, a.output,
           nums(a.drop_channels), nums(a.drop_drums), a.drum_stride,
           a.transpose)
