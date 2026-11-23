#!/usr/bin/env python3
"""Master the GTA theme and CJ's callout for the single intro SFX channel."""

import argparse
from pathlib import Path
import subprocess
import wave

import numpy as np

from build_spc_neogeo import load_mugen_snd, load_wav_mono_bytes, resample_mono


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / 'music/Michael_Hunter_-_GTA_San_Andreas_Theme_Song_(mp3.pm).aac'
RATE = 4000
SAMPLES = 8320  # 520 BRR blocks; retain the existing intro playback window
SPEECH_START = int(0.48 * RATE)
THEME_LEAD_DB = 3.0
MUSIC_DUCK_DB = -9.0


def rms(samples):
    return np.sqrt(np.mean(samples ** 2))


def mix():
    # Seek after decoding to hit the same beat regardless of AAC seek rounding.
    raw = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(THEME), '-ss', '9.930',
        '-t', str(SAMPLES / RATE), '-af', 'highpass=f=85',
        '-ac', '1', '-ar', str(RATE), '-f', 's16le', 'pipe:1',
    ])
    theme = np.frombuffer(raw, dtype='<i2').astype(float)
    assert len(theme) == SAMPLES
    # Lift the quieter notes without letting the first drum transient
    # determine the level of the whole clip.
    theme = np.tanh(2.2 * theme / np.max(np.abs(theme)))
    theme[:16] *= np.linspace(0, 1, 16)
    fade = int(0.40 * RATE)
    theme[-fade:] *= np.linspace(1, 0, fade) ** 1.5

    snd = load_mugen_snd(ROOT / 'assets/characters/cj/cj.snd')
    pcm, rate = load_wav_mono_bytes(snd[(21, 0)])
    callout = np.asarray(resample_mono(pcm, rate, RATE), dtype=float)
    active = np.flatnonzero(np.abs(callout) > 600)
    callout = callout[active[0]:active[-1] + 1].copy()
    callout[:16] *= np.linspace(0, 1, 16)
    callout[-32:] *= np.linspace(1, 0, 32)
    overlap = slice(SPEECH_START, SPEECH_START + len(callout))
    callout *= rms(theme[overlap]) / (rms(callout) * 10 ** (THEME_LEAD_DB / 20))
    speech = np.zeros(SAMPLES)
    speech[overlap] = callout
    # Duck the theme under the callout so the voice sits above the music it
    # shares the 4 kHz channel with, while the beat stays full before/after.
    duck = 10 ** (MUSIC_DUCK_DB / 20)
    ramp = int(0.05 * RATE)
    envelope = np.ones(SAMPLES)
    envelope[overlap] = duck
    envelope[overlap.start - ramp:overlap.start] = np.linspace(1, duck, ramp)
    envelope[overlap.stop:overlap.stop + ramp] = np.linspace(duck, 1, ramp)
    theme *= envelope
    scale = 30000 / np.max(np.abs(theme + speech))
    return theme * scale, speech * scale


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'assets/audio/cj_intro_0.wav')
    args = parser.parse_args()
    theme, speech = mix()
    with wave.open(str(args.out), 'wb') as wav:
        wav.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        wav.writeframes(np.rint(theme + speech).astype('<i2').tobytes())


if __name__ == '__main__':
    main()
