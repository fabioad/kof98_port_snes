#!/usr/bin/env python3
"""Downsample every PCM sample inside an Impulse Tracker .it module.

SNESMOD converts each sample to BRR at link time, so ARAM use scales with
raw PCM length.  Halving the sample rate quarters the BRR size with only a
mild top-end loss.  For each sample we low-pass filter it and keep every k-th
sample (k chosen so rate/k <= TARGET_RATE), then divide C5Speed by k,
preserving pitch.

The FIR is the important part for drums: dropping every k-th sample without
a filter folds high frequencies back as aliasing, which is the "dirty vinyl"
hiss heard on the decimated 909-kit samples.  The filter costs no ARAM; the
BRR size depends only on the number of samples, not on 8/16-bit depth.

Only uncompressed 8/16-bit mono PCM is supported (that's what midi2tracker
and the shipped .iti instruments emit).
"""
import math
import struct
import sys

try:
    import numpy as _np
except ImportError:                    # keep the tool usable without numpy
    _np = None

TARGET_RATE = 5500                     # esaka's samples sit around 5 kHz


def _lowpass(k):
    """Normalised windowed-sinc low-pass for integer decimation by k."""
    fc = 0.45 / k                      # just below the new Nyquist
    ntaps = max(15, 8 * k + 1)
    if ntaps % 2 == 0:
        ntaps += 1
    mid = (ntaps - 1) // 2
    h = []
    for i in range(ntaps):
        x = i - mid
        sinc = 2.0 * fc if x == 0 else math.sin(2.0 * math.pi * fc * x) / (
            math.pi * x)
        window = 0.54 - 0.46 * math.cos(2.0 * math.pi * i / (ntaps - 1))
        h.append(sinc * window)
    gain = sum(h)
    return [v / gain for v in h], mid


def _resample(pcm, step, k, newlen):
    """Anti-aliased decimation; returns newlen samples in the same PCM format."""
    if k <= 1 or newlen <= 0:
        return pcm[:newlen * step]
    taps, mid = _lowpass(k)
    if _np is not None:
        if step == 1:
            src = _np.frombuffer(pcm, dtype=_np.uint8).astype(_np.float64) - 128.0
        else:
            src = _np.frombuffer(pcm, dtype='<i2').astype(_np.float64)
        out = _np.convolve(src, _np.asarray(taps), mode='same')[::k][:newlen]
        if step == 1:
            out = _np.clip(_np.rint(out), -128, 127).astype(_np.int16) + 128
            return out.astype(_np.uint8).tobytes()
        return _np.clip(_np.rint(out), -32768, 32767).astype('<i2').tobytes()

    if step == 1:
        src = [b - 128 for b in pcm]
    else:
        src = list(struct.unpack(f'<{len(pcm) // 2}h', pcm))
    out = bytearray()
    for m in range(newlen):
        centre = m * k
        acc = 0.0
        for j, tap in enumerate(taps):
            idx = centre + j - mid
            if 0 <= idx < len(src):
                acc += src[idx] * tap
        value = int(round(acc))
        if step == 1:
            out.append(max(-128, min(127, value)) + 128)
        else:
            out += struct.pack('<h', max(-32768, min(32767, value)))
    return bytes(out)


def reduce_it(src_path, dst_path, target_rate=TARGET_RATE):
    d = bytearray(open(src_path, "rb").read())
    assert d[:4] == b"IMPM"
    ordnum, insnum, smpnum = struct.unpack("<3H", d[0x20:0x26])
    ip = 0xC0 + ordnum + 4 * insnum
    smp_ptrs = struct.unpack(f"<{smpnum}I",
                             d[ip:ip + 4 * smpnum])
    # Collect every sample: non-resampled ones keep their old PCM in the
    # rebuilt file, so their data pointers must be shifted when earlier
    # sample spans are removed.  Leaving them pointing at the old offsets
    # made them read whatever happened to land there (often past EOF).
    samples = []
    edits = []
    for sp in smp_ptrs:
        if not sp or d[sp:sp + 4] != b"IMPS":
            continue
        flg = d[sp + 0x12]
        assert not (flg & 0x0C), "compressed/stereo samples unsupported"
        is16 = bool(flg & 0x02)
        length = struct.unpack("<I", d[sp + 0x30:sp + 0x34])[0]
        c5 = struct.unpack("<I", d[sp + 0x3C:sp + 0x40])[0]
        data_ptr = struct.unpack("<I", d[sp + 0x48:sp + 0x4C])[0]
        step = 2 if is16 else 1
        if not length or not data_ptr or not c5:
            samples.append((sp, data_ptr, 0, False))
            continue
        k = max(1, round(c5 / target_rate))
        if k <= 1:
            samples.append((sp, data_ptr, length * step, False))
            continue
        loops = [struct.unpack("<I", d[sp + o:sp + o + 4])[0]
                 for o in (0x34, 0x38, 0x40, 0x44)]
        pcm = bytes(d[data_ptr:data_ptr + length * step])
        newlen = len(pcm) // (step * k)
        new = _resample(pcm, step, k, newlen)
        edits.append((sp, data_ptr, len(pcm), new, newlen,
                      max(1, c5 // k),
                      [min(v // k, newlen) for v in loops]))
        samples.append((sp, data_ptr, len(pcm), True))
    if not edits:
        open(dst_path, "wb").write(d)
        return 0
    # rebuild: copy everything but each old sample span; new data appended
    edits.sort(key=lambda e: e[1])
    out = bytearray()
    pos = 0
    new_ptr = {}
    for e in edits:
        sp, data_ptr, oldlen, new, newlen, newc5, _l = e
        out += d[pos:data_ptr]
        pos = data_ptr + oldlen
    out += d[pos:]
    base = len(out)
    delta = 0
    # append all new sample data contiguously after the trimmed file
    for e in edits:
        new_ptr[e[0]] = base + delta
        delta += len(e[3])
    for e in edits:
        out += e[3]
    # patch headers
    for e in edits:
        sp, _dp, _ol, _new, newlen, newc5, nloops = e
        struct.pack_into("<I", out, sp + 0x30, newlen)
        for i, o in enumerate((0x34, 0x38, 0x40, 0x44)):
            struct.pack_into("<I", out, sp + o, nloops[i])
        struct.pack_into("<I", out, sp + 0x3C, newc5)
        struct.pack_into("<I", out, sp + 0x48, new_ptr[sp])
    # shift pointers of samples that were not resampled
    spans = sorted((e[1], e[2]) for e in edits)
    for sp, data_ptr, oldlen, edited in samples:
        if edited:
            continue
        if oldlen == 0:
            newptr = base
        else:
            newptr = data_ptr - sum(n for p, n in spans if p < data_ptr)
        struct.pack_into("<I", out, sp + 0x48, newptr)
    open(dst_path, "wb").write(bytes(out))
    return len(edits)


if __name__ == "__main__":
    n = reduce_it(sys.argv[1], sys.argv[2],
                  int(sys.argv[3]) if len(sys.argv) > 3 else TARGET_RATE)
    print(f"{sys.argv[2]}: resampled {n} sample(s)")
