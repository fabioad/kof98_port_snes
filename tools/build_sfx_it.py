#!/usr/bin/env python3
"""Build sfx.it: a minimal Impulse Tracker module carrying the fight SFX
samples, for the SNESMOD soundbank.

Only the samples matter -- the module has no instruments/patterns and is
never played; smconv exports each sample as a soundbank "source" that the
SNESMOD driver plays through spcEffect().  SNESMOD caps loaded effects at
16, so near-duplicate runtime ids share one source.

Also emits spc_sfxmap.inc mapping each runtime SFX_* id (same numbering as
build_audio.py) to its preloaded effect slot + IT volume nibble.
"""

from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_spc_neogeo import (  # noqa: E402
    load_mugen_snd,
    load_wav_mono_bytes,
    resample_mono,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "audio" / "esaka" / "sfx.it"
INC = ROOT / "build" / "gen_audio" / "spc_sfxmap.inc"
SAMPLE_RATE = 4000

KYO = "assets/characters/Kyo-KOF98/Kyo.snd"

UI = "assets/ui"
WINNER_VOICE = "assets/audio/announcer/common_00052.wav"
SELECT_VOICE = "assets/audio/announcer/common_00062.wav"
MOVE_SOUND = "assets/audio/announcer/common_00112.wav"
BACK_SOUND = "assets/audio/announcer/common_00114.wav"
SELECT_SOUND = "assets/audio/announcer/common_00113.wav"
FIGHT_VOICES = (
    "assets/audio/announcer/common_00063.wav",   # READY
    "assets/audio/announcer/common_00073.wav",   # GO
)

# 16 soundbank sources (source index = position). SNESMOD has a fixed
# 16-entry EffectDirectory, so near-duplicate combat effects share sources;
# unused later-round slots carry menu navigation and back sounds.
SNDX = "assets/kof98data/Lifebar/snd_extract"
SOURCES = [
    ("swing",     KYO,    (0, 0), None),      # 0: attack swing, not a voice
    ("hit_light", KYO,    (1, 0), None),      # 1: light HitDef impact
    ("hit_heavy", KYO,    (1, 3), None),      # 2: strong HitDef impact
    ("winner_voice", WINNER_VOICE, None, None),  # 3: winner-screen announcer
    ("ui_select", SELECT_SOUND, None, None),       # 4: menu confirm
    ("fight",     FIGHT_VOICES, None, None),             # 5: paired GO call
    ("ko",        f"{SNDX}/2_1.wav", None, 3500),      # 6
] + [
    (f"round{i}", f"{SNDX}/1_{i}.wav", None, 2600)
    for i in range(1, 6)                     # 7-11: round voices 1-5
] + [
    ("menu_back", BACK_SOUND, None, 960),                # 12, 240 ms
    ("menu_move", MOVE_SOUND, None, 720),                # 13, 180 ms
    ("select_start_voice", SELECT_VOICE, None, None),  # 14
    ("round9", f"{SNDX}/1_9.wav", None, 2600),         # 15: FINAL ROUND
]

# runtime SFX_* id -> (source index, IT volume nibble)
MAP = [
    (0,  11),  # SFX_SWISH_LP
    (0,  11),  # SFX_SWISH_SP
    (0,  11),  # SFX_SWISH_LK
    (0,  11),  # SFX_SWISH_SK
    (1,  14),  # SFX_HIT_LIGHT
    (2,  13),  # SFX_HIT_MED
    (2,  14),  # SFX_HIT_STRONG
    (2,  12),  # SFX_GUARD   -> strong impact
    (2,  11),  # SFX_LAND    -> strong impact
    (7,  15),  # SFX_ROUND1  -> round voice 1
    (3,  15),  # SFX_FIGHT   -> fight-module slot 3 = source 5 (see FightFxSrc)
    (4,  15),  # SFX_KO      -> fight-module slot 4 = source 6
    (0,  11),  # SFX_YELL   -> attack swing; no character voice yet
    (0,  11),  # SFX_VOICE  -> attack swing; no character voice yet
    (0,  12),  # SFX_GRAB   -> swish
    (2,  14),  # SFX_THROW
    (0,  12),  # SFX_DASH   -> swish
    (3,  14),  # SFX_WIN    -> winner-screen announcer
    (2,  14),  # SFX_HIT_HEAVY
    (2,  15),  # SFX_HIT_MAX
    (2,  13),  # SFX_WALL   -> strong impact
    (4,  14),  # SFX_SELECT -> ui beep
    (7,  14),  # SFX_MOVE   -> cursor/navigation sound in effect slot 7
    (8,  14),  # SFX_BACK   -> back/MSU unavailable sound in effect slot 8
]


def load_pcm(snd_rel: str | tuple[str, ...], key: tuple[int, int] | None, cap: int | None,
             cache: dict) -> bytes:
    if isinstance(snd_rel, tuple):
        # Join the two announcer phrases into one sample so the existing
        # fight-start event plays them back-to-back without stalling the game.
        pcm_joined = bytearray()
        for wav_rel in snd_rel:
            pcm, rate = load_wav_mono_bytes((ROOT / wav_rel).read_bytes())
            pcm = resample_mono(pcm, rate, SAMPLE_RATE)
            while pcm and abs(pcm[0]) < 600:
                pcm.pop(0)
            while pcm and abs(pcm[-1]) < 600:
                pcm.pop()
            pcm_joined.extend((v >> 8) & 0xFF for v in pcm)
        if cap is not None:
            del pcm_joined[cap:]
        return bytes(pcm_joined)
    if snd_rel.endswith(".wav"):               # standalone UI wav
        pcm, rate = load_wav_mono_bytes((ROOT / snd_rel).read_bytes())
        pcm = resample_mono(pcm, rate, SAMPLE_RATE)
        while pcm and abs(pcm[0]) < 600:
            pcm.pop(0)
        while pcm and abs(pcm[-1]) < 600:
            pcm.pop()
        if cap is not None:
            pcm = pcm[:cap]
        return bytes(((v >> 8) & 0xFF) for v in pcm)
    if snd_rel not in cache:
        cache[snd_rel] = load_mugen_snd(ROOT / snd_rel)
    raw = cache[snd_rel].get(key)
    if raw is None:
        raise SystemExit(f"{snd_rel}: missing SND sample {key}")
    pcm, rate = load_wav_mono_bytes(raw)
    pcm = resample_mono(pcm, rate, SAMPLE_RATE)
    if cap is not None:
        pcm = pcm[:cap]
    peak = max((abs(v) for v in pcm), default=1) or 1
    if peak > 30000:
        pcm = [int(v * 30000 / peak) for v in pcm]
    # signed 8-bit PCM for the IT sample body
    return bytes(((v >> 8) & 0xFF) for v in pcm)


def write_it(samples: list[bytes]) -> bytes:
    n = len(samples)
    hdr = bytearray(0xC0)
    hdr[0:4] = b"IMPM"
    hdr[4:30] = b"kof98 sfx".ljust(26, b"\0")
    struct.pack_into("<HHHH", hdr, 0x20, 1, 0, n, 0)  # ord, ins, smp, pat
    struct.pack_into("<HH", hdr, 0x28, 0x0214, 0x0214)
    struct.pack_into("<HH", hdr, 0x2C, 0x09, 0)  # stereo + instruments
    hdr[0x30:0x36] = bytes((128, 48, 6, 125, 128, 0))
    hdr[0x40:0x48] = bytes((32, 8, 56, 8, 56, 8, 56, 8))  # default ch pan
    hdr[0x80:0xC0] = bytes([64] * 64)
    body = bytearray(hdr)
    body += b"\xff"  # order list: end marker
    smpptr = 0xC0 + 1 + n * 4  # orders + sample para table
    # sample data area follows the headers
    hdr_area = smpptr + n * 80
    cursor = hdr_area
    ptrs = []
    for i, pcm in enumerate(samples):
        ptrs.append(smpptr + i * 80)
    for p in ptrs:
        body += struct.pack("<I", p)
    for i, pcm in enumerate(samples):
        sh = bytearray(80)
        sh[0:4] = b"IMPS"
        sh[4:16] = f"sfx{i:02d}".encode().ljust(12, b"\0")
        sh[0x11] = 64            # global volume
        sh[0x12] = 0x01          # sample present
        sh[0x13] = 64            # default volume
        sh[0x14:0x2E] = f"sfx{i:02d}".encode().ljust(26, b"\0")
        sh[0x2E] = 1             # signed 8-bit
        struct.pack_into("<III", sh, 0x30, len(pcm), 0, 0)
        struct.pack_into("<III", sh, 0x3C, SAMPLE_RATE, 0, 0)
        struct.pack_into("<I", sh, 0x48, cursor)
        cursor += len(pcm)
        body += sh
    for pcm in samples:
        body += pcm
    return bytes(body)


def main() -> None:
    cache: dict[str, dict] = {}
    pcms = [load_pcm(snd, key, cap, cache) for _, snd, key, cap in SOURCES]
    OUT.write_bytes(write_it(pcms))
    INC.parent.mkdir(parents=True, exist_ok=True)
    INC.write_text(
        "; generated by build_sfx_it.py -- runtime sfx id -> source idx,vol\n"
        "IkSfxMap:\n"
        + "".join(f"    .db {src}, {vol}\n" for src, vol in MAP)
        + f".DEFINE SFX_SELECT {len(MAP) - 3}\n"   # ui_* MAP rows carry the
        + f".DEFINE SFX_MOVE {len(MAP) - 2}\n"     #   menu/select-screen ids
        + f".DEFINE SFX_BACK {len(MAP) - 1}\n"
    )
    total = sum(len(p) for p in pcms)
    print(f"sfx.it: {OUT.stat().st_size} bytes, {len(pcms)} sources, "
          f"{total} pcm bytes @ {SAMPLE_RATE} Hz")
    for i, ((name, _, _, _), p) in enumerate(zip(SOURCES, pcms)):
        print(f"  src {i:2d} {name:12s} {len(p):5d} B")


if __name__ == "__main__":
    main()
