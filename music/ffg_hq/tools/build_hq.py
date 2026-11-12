#!/usr/bin/env python3
"""Convert the 17 KOF98 songs again from MIDI with the full FFG arrangement.

Does not touch the game: writes music/ffg_hq/it/*.it, SPCs, MP3 previews
and report.json.  Global volume is normalised to the loudness of the current (approved) module
on the emulated S-DSP, without exceeding TARGET_PEAK.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'music/ffg_energy'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from it_pattern_limit import fit_snesmod, layout, MAX_PATTERNS   # noqa: E402
from extract_reference import GME                                # noqa: E402
from spc_export import repair                                    # noqa: E402
import mid2it_ffg                                                # noqa: E402

SMCONV = '/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6/devkitsnes/tools/smconv'
BUDGET = 42850                  # tools/validate_snesmod.py (smconv -V total)
# Real ARAM footprint (module + BRR samples, as spcLoad uploads them).  The
# stage-8 regression (tools/test_stage8_music_headless.py) froze the winner
# theme load with a 45,090 B module and passes with 43,622 B (stg2).
REAL_BUDGET = 43622             # largest module proven by that test (stg2)
TARGET_PEAK = 24000             # raw S-DSP peak before export gain

# module -> (MIDI, longest stretch kept in seconds or None)
SONGS = {
    'stg0': ('music/EsakaVer3.mid', None),
    'stg1': ('music/kof98_dora.mid', None),
    'stg2': ('music/KOF98Arashi2.mid', None),
    'stg3': ('music/kof98_stown.mid', None),
    'stg4': ('music/Rumbling.mid', None),
    'stg5': ('music/rugalomega98.mid', None),
    'stg6': ('music/Fairy98.mid', None),
    'stg7': ('music/KOF98Slum.mid', None),
    'stg8': ('music/Ryu-ko_Final.mid', None),
    'stg9': ('music/Kurikinton_Gomame_Guitar_Ver_.mid', None),
    'menu_cipher': ('music/Cipher.mid', None),
    'menu_cipher_beta': ('music/Cipher_Beta.mid', None),
    'menu_kof': ('music/The_King_of_Fighters.mid', None),
    'menu_lastdance': ('music/kof02_lastdancerugal.mid', None),
    'menu_sunset': ('music/KOF94Sunset.mid', None),
    'menu_winner': ('music/W.mid', None),
    'menu_crystal': ('assets/survival_ending/kof00_crystal.mid', None),
}


def smconv_size(it):
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([SMCONV, '-V', '-o', f'{d}/x.spc', str(it)],
                           capture_output=True, text=True)
    m = re.search(r'Total:\s*\[\s*(\d+) bytes\]', r.stdout + r.stderr)
    if r.returncode or not m:
        return None
    return int(m.group(1))


def aram_size(it):
    """module + sample bytes spcLoad really sends (smconv soundbank parse)."""
    import struct
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([SMCONV, '-s', '-i', '-o', f'{d}/b', str(it)],
                           capture_output=True, text=True)
        if r.returncode:
            return None
        b = Path(f'{d}/b.bnk').read_bytes()

    def addr(table, i):
        o = table + 3 * i
        return b[o + 2] * 0x10000 + struct.unpack_from('<H', b, o)[0]
    p = addr(0x0004, 0)                           # SB_MODTABLE
    words, count = struct.unpack_from('<HH', b, p)
    sources = struct.unpack_from(f'<{count}H', b, p + 4)
    samples = sum((struct.unpack_from('<H', b, addr(0x0184, i))[0] + 1) // 2 * 2
                  for i in sources)               # SB_SRCTABLE, rounded to words
    return words * 2 + samples


def render(spc, seconds):
    g = GME(spc)
    try:
        raw = g.render(seconds)
    finally:
        g.close()
    return np.frombuffer(raw, dtype='<i2').astype(np.int32)


def export_spc(it, spc):
    subprocess.run([SMCONV, '-o', str(spc), str(it)], check=True,
                   stdout=subprocess.DEVNULL)
    repair(spc, it)


def mp3(x, out):
    pcm = np.clip(np.rint(x * .70), -32768, 32767).astype('<i2').tobytes()
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', '32000',
                        '-ac', '2', '-i', 'pipe:0', '-c:a', 'libmp3lame', '-b:a',
                        '192k', str(out)], input=pcm, capture_output=True)
    assert r.returncode == 0, r.stderr


def build(name, midi, max_seconds):
    out = HERE / 'it' / f'{name}.it'
    spc = HERE / 'spc' / f'{name}.spc'
    seconds = 12 if name == 'menu_winner' else 60
    mix = 96
    ref = reference_rms(name, seconds)
    info = None
    for attempt in range(8):
        info = mid2it_ffg.convert(str(HERE / 'capcom'), str(ROOT / midi), str(out),
                                  name, mix, max_seconds)
        data = fit_snesmod(out.read_bytes())
        out.write_bytes(data)
        size = smconv_size(out)
        real = aram_size(out)
        if size is None or size > BUDGET or real is None or real > REAL_BUDGET:
            # too big: keep a shorter stretch of the song
            dur = mido_length(ROOT / midi) if max_seconds is None else max_seconds
            max_seconds = dur * 0.93
            print(f'  {name}: {size}/{real} bytes > {BUDGET}/{REAL_BUDGET}, '
                  f'cutting to {max_seconds:.0f} s')
            continue
        export_spc(out, spc)
        x = render(spc, seconds)
        peak = int(abs(x).max())
        if peak == 0:
            raise SystemExit(f'{name}: silent render')
        rms = float(np.sqrt(np.mean(x.astype(float) ** 2)))
        # match the current module's loudness, never above TARGET_PEAK
        gain = min(ref / rms, TARGET_PEAK / peak)
        want = max(16, min(128, int(round(mix * gain))))
        if abs(want - mix) <= 2 or attempt == 7:
            break
        mix = want
    info.update(smconvBytes=size, aramBytes=real, patternsAfterFit=len(layout(out.read_bytes())[3]),
                rawPeak=peak, clipped=float(np.mean(abs(x) >= 32767)),
                rms=float(np.sqrt(np.mean(x.astype(float) ** 2))), keptSeconds=max_seconds)
    assert info['patternsAfterFit'] <= MAX_PATTERNS
    mp3(x, HERE / 'previews' / f'{name}_hq.mp3')
    return info


def reference_rms(name, seconds):
    spc = ROOT / 'music/ffg_energy/candidates' / f'{name}.spc'
    x = render(spc, seconds)
    return float(np.sqrt(np.mean(x.astype(float) ** 2)))


def mido_length(path):
    import mido
    return mido.MidiFile(str(path)).length


def main(only):
    for d in ('it', 'spc', 'previews'):
        (HERE / d).mkdir(exist_ok=True)
    report_path = HERE / 'report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    for name, (midi, cut) in SONGS.items():
        if only and name not in only:
            continue
        report[name] = build(name, midi, cut)
        r = report[name]
        print(f"  -> {name}: {r['smconvBytes']} B, mix {r['mix']}, peak {r['rawPeak']}, "
              f"clip {r['clipped']:.4f}", flush=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main(sys.argv[1:])
