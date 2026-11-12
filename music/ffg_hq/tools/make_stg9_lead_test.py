#!/usr/bin/env python3
"""Sound test ROM for the USA Yard (stg9) lead options.

The long-note guitar line of USA Yard is MIDI ch1/ch4 (GM trumpet).  The HQ
conversion maps it to 'brass', dedupe() drops ch4 (pan 127) as a doubling of
ch1 (pan 0), so the lead ends up hard-ish left, at the same level as each of
the two centred rhythm guitars.  Variants (notes and order unchanged):

  ATUAL  approved module (assets/audio/ffg/stg9.it)
  A      dedupe merges the pan of the dropped doubling -> lead centred
  B      rhythm guitar instrument GV 128 -> 77 (-4.4 dB); the lead is
         already at the maximum (vol column 64, GV 128)
  C      lead uses the FFG 'lead' timbre (sample 09) instead of 'brass'
  A+B+C  all three

Global volume stays at the approved 99 in every variant, so the comparison
is not hidden by a loudness renormalisation.  Nothing in the game build or in
mid2it_ffg.py is changed: the options are applied by patching the module at
run time.  Output: kof98-stg9-lead-soundtest.sfc in the repo root.
"""
import copy
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
ST = HERE / 'soundtest_stg9'
SRC_ST = HERE / 'soundtest'
SDK = Path('/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6')
SMCONV = SDK / 'devkitsnes/tools/smconv'
MIDI = ROOT / 'music/Kurikinton_Gomame_Guitar_Ver_.mid'
APPROVED = ROOT / 'assets/audio/ffg/stg9.it'
MIX = 99                                   # approved stg9 global volume

sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from it_pattern_limit import fit_snesmod                          # noqa: E402
import mid2it_ffg as M                                            # noqa: E402
from build_hq import smconv_size, aram_size, BUDGET, REAL_BUDGET  # noqa: E402

GUITAR_GV = 77                             # 128 -> 77 = -4.4 dB

ORIG_MELODIC = copy.deepcopy(M.MELODIC)


def set_instrument_gv(it, prefix, gv):
    ordn, insn = struct.unpack_from('<HH', it, 0x20)
    hits = 0
    for p in struct.unpack_from(f'<{insn}I', it, 0xC0 + ordn):
        if it[p + 0x20:p + 0x3A].split(b'\0')[0].decode('latin1').startswith(prefix):
            it[p + 0x18] = gv
            hits += 1
    assert hits == 1, (prefix, hits)
ORIG_DEDUPE = M.dedupe


def dedupe_centre(notes, grid):
    """dedupe(), but a kept channel takes the mean pan of the doublings it
    absorbed (ch1 pan 0 + ch4 pan 127 -> centre)."""
    kept_notes, drop = ORIG_DEDUPE(notes, grid)
    by, pan = {}, {}
    for n in notes:
        if n[4] != 9:
            by.setdefault(n[4], set()).add((n[0] // grid, n[2] % 12))
            pan.setdefault(n[4], n[6])
    newpan = {}
    for d in drop:
        for k in sorted(by, key=lambda c: (-len(by[c]), c)):
            if k not in drop and len(by[d] & by[k]) >= 0.85 * len(by[d]):
                newpan.setdefault(k, [pan[k]]).append(pan[d])
                break
    newpan = {k: round(sum(v) / len(v)) for k, v in newpan.items()}
    out = [n[:6] + (newpan[n[4]],) if n[4] in newpan else n for n in kept_notes]
    return out, drop


VARIANTS = [
    # (file stem, label, centre, louder, lead timbre)
    ('v0_atual', 'ATUAL (NO JOGO)', None, None, None),
    ('v1_a', 'A  LEAD CENTRO', True, False, False),
    ('v2_b', 'B  GUITARRA BASE -4DB', False, True, False),
    ('v3_c', 'C  TIMBRE LEAD', False, False, True),
    ('v4_abc', 'A+B+C', True, True, True),
]


def convert(out, centre, louder, timbre):
    M.MELODIC.clear()
    M.MELODIC.update(copy.deepcopy(ORIG_MELODIC))
    M.dedupe = dedupe_centre if centre else ORIG_DEDUPE
    lead = 'lead' if timbre else 'brass'
    if timbre:
        M.MELODIC['brass'] = M.MELODIC['lead']
    try:
        info = M.convert(str(HERE / 'capcom'), str(MIDI), str(out), 'stg9', MIX)
    finally:
        M.MELODIC.clear()
        M.MELODIC.update(ORIG_MELODIC)
        M.dedupe = ORIG_DEDUPE
    data = bytearray(out.read_bytes())
    if louder:
        # Every note carries a volume column, so sample default volumes are
        # ignored; the lead is already at the maximum (vol 64, GV 128).  The
        # balance moves through the rhythm guitar instrument GV instead.
        set_instrument_gv(data, 'guitar', GUITAR_GV)
    out.write_bytes(fit_snesmod(bytes(data)))
    size, real = smconv_size(out), aram_size(out)
    assert size and size <= BUDGET and real and real <= REAL_BUDGET, (out, size, real)
    return info, size, real, lead


def main():
    its = ST / 'it'
    if ST.exists():
        shutil.rmtree(ST)
    its.mkdir(parents=True)
    for f in ('Makefile', 'hdr.asm', 'data.asm', 'pvsneslibfont.bmp'):
        shutil.copyfile(SRC_ST / f, ST / f)
    mk = (ST / 'Makefile').read_text()
    mk = mk.replace('$(sort $(wildcard it/n*.it)) $(sort $(wildcard it/a*.it))',
                    '$(sort $(wildcard it/v*.it))')
    mk = mk.replace('KOF98FFGSOUNDTEST', 'KOF98STG9LEADTEST')
    (ST / 'Makefile').write_text(mk)
    shutil.copyfile(Path(__file__).resolve().parent / 'stg9_lead_jukebox.c',
                    ST / 'jukebox.c')

    # sanity: without options the converter reproduces the approved module
    probe = its / 'probe.it'
    convert(probe, False, False, False)
    assert probe.read_bytes() == APPROVED.read_bytes(), 'baseline differs from approved stg9.it'
    probe.unlink()

    files = []
    for stem, label, centre, louder, timbre in VARIANTS:
        dst = its / f'{stem}.it'
        if centre is None:
            dst.write_bytes(fit_snesmod(APPROVED.read_bytes()))
        else:
            info, size, real, lead = convert(dst, centre, louder, timbre)
            print(f'{label:18} {size} B smconv, {real} B ARAM, lost {info["lostNotes"]}')
        files.append(dst)

    rel = [str(f.relative_to(ST)) for f in files]
    (ST / 'res').mkdir(exist_ok=True)
    smc = [str(SMCONV), '-s', '-o', 'res/soundbank', '-V', '-b', '5', *rel]
    subprocess.run(smc, cwd=ST, check=True, stdout=subprocess.DEVNULL)
    asm = (ST / 'res/soundbank.asm').read_text()
    banks = sorted({int(n) for n in re.findall(r'SOUNDBANK__(\d+)', asm)})
    assert banks == list(range(len(banks))), banks

    h = ['/* generated by music/ffg_hq/tools/make_stg9_lead_test.py */',
         f'#define NSONGS {len(VARIANTS)}', '']
    h += ['extern char %s;' % ', '.join(f'SOUNDBANK__{b}' for b in banks), '']
    h.append('static const char *names[NSONGS] = {')
    h += [f'    "{label}",' for _, label, *_ in VARIANTS]
    h += ['};', '', 'static void registerBanks(void)', '{',
          '    /* banks must be registered last-to-first */']
    h += [f'    spcSetBank(&SOUNDBANK__{b});' for b in reversed(banks)]
    h += ['}', '']
    (ST / 'songs.h').write_text('\n'.join(h))

    size = 1
    while size < 5 + len(banks) + 1:
        size *= 2
    size = max(16, size)
    romsize = {16: 0x09, 32: 0x0A, 64: 0x0B, 128: 0x0C}[size]
    (ST / 'romsize.mk').write_text(f'ROMBANKS := {size}\nROMSIZE := {romsize:02X}\n')

    env = {**os.environ, 'PVSNESLIB_HOME': str(SDK)}
    subprocess.run(['make', '-C', str(ST), 'clean'], env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(smc, cwd=ST, check=True, stdout=subprocess.DEVNULL)
    r = subprocess.run(['make', '-C', str(ST)], env=env, capture_output=True, text=True)
    print(r.stdout[-1500:], r.stderr[-1500:])
    r.check_returncode()
    out = ROOT / 'kof98-stg9-lead-soundtest.sfc'
    shutil.copyfile(ST / 'soundtest.sfc', out)
    print('->', out)


if __name__ == '__main__':
    main()
