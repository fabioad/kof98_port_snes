#!/usr/bin/env python3
"""Build the SNES fighting engine SPC700 sample bank.

The fight ROM needs only short one-shots for the current vertical slice.  This
script extracts selected WAV payloads from the original Elecbyte SND files,
resamples them to a common 8 kHz rate and emits the BRR/sample-directory data
used by src/audio/spc.asm.
"""

from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_spc_neogeo import (  # noqa: E402
    encode_brr,
    gen_hat,
    gen_kick,
    gen_snare,
    load_mugen_snd,
    load_wav_mono,
    load_wav_mono_bytes,
    pitch_table,
    resample_mono,
    wave_cycle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "gen_audio"
SAMPLE_RATE = 8000
DSP_PITCH = round(SAMPLE_RATE * 4096 / 32000)
DIR_BASE = 0x1000

# Runtime event id -> source SND tuple.  Kyo-N.cns uses group 0 for attack
# swings, group 1 for HitDef impacts and group 2 for guards.  These non-vocal
# samples are shared by every fighter in the SNES port.
SAMPLES = [
    ("SFX_SWISH_LP", "swish weak punch", "assets/characters/Kyo-KOF98/Kyo.snd", (0, 0), 0x58),
    ("SFX_SWISH_SP", "swish strong punch", "assets/characters/Kyo-KOF98/Kyo.snd", (0, 1), 0x58),
    ("SFX_SWISH_LK", "swish weak kick", "assets/characters/Kyo-KOF98/Kyo.snd", (0, 0), 0x58),
    ("SFX_SWISH_SK", "swish strong kick", "assets/characters/Kyo-KOF98/Kyo.snd", (0, 1), 0x58),
    ("SFX_HIT_LIGHT", "hit light", "assets/characters/Kyo-KOF98/Kyo.snd", (1, 0), 0x70),
    ("SFX_HIT_MED", "hit medium", "assets/characters/Kyo-KOF98/Kyo.snd", (1, 1), 0x70),
    ("SFX_HIT_STRONG", "hit strong", "assets/characters/Kyo-KOF98/Kyo.snd", (1, 3), 0x70),
    ("SFX_GUARD", "guard", "assets/characters/Kyo-KOF98/Kyo.snd", (2, 0), 0x60),
    ("SFX_LAND", "landing", "assets/characters/_excluded/kfm/kfm.snd", (40, 0), 0x58),
    ("SFX_ROUND1", "round 1 announcer", "assets/data/fight.snd", (0, 1), 0x70),
    ("SFX_FIGHT", "fight announcer", "assets/data/fight.snd", (1, 0), 0x70),
    ("SFX_KO", "KO announcer", "assets/data/fight.snd", (2, 0), 0x70),
    ("SFX_YELL", "kfm strong yell", "assets/characters/_excluded/kfm/kfm.snd", (0, 2), 0x68),
    ("SFX_VOICE", "kfm palm voice", "assets/characters/_excluded/kfm/kfm.snd", (0, 3), 0x70),
    ("SFX_GRAB", "grab whiff", "assets/characters/_excluded/kfm/kfm.snd", (1, 1), 0x60),
    ("SFX_THROW", "throw slam", "assets/characters/Kyo-KOF98/Kyo.snd", (1, 4), 0x70),
    ("SFX_DASH", "dash whoosh", "assets/characters/_excluded/kfm/kfm.snd", (100, 0), 0x60),
    ("SFX_WIN", "win quote", "assets/characters/_excluded/kfm/kfm.snd", (11, 0), 0x70),
    ("SFX_HIT_HEAVY", "hit heavy", "assets/characters/Kyo-KOF98/Kyo.snd", (1, 3), 0x70),
    ("SFX_HIT_MAX", "hit max", "assets/characters/Kyo-KOF98/Kyo.snd", (1, 4), 0x70),
    ("SFX_WALL", "wall impact", "assets/characters/Kyo-KOF98/Kyo.snd", (1, 4), 0x68),
]


# --- BGM: small looping stage theme -----------------------------------------
# Event format (shared with the neogeo sequencer port): 3-byte records
# [wait][op][arg]; op < $80 = MIDI note (arg = duration), $80 rest,
# $81 inst, $82 vol, $83 pan, $FE loop, $FF end.  Waits are absolute deltas:
# an event fires <wait> ticks after the previous one on that channel.
OP_REST, OP_INST, OP_VOL, OP_PAN, OP_LOOP = 0x80, 0x81, 0x82, 0x83, 0xFE

# Dir slots for music instruments (after the SFX entries).
I_TRI, I_SQR, I_STR = len(SAMPLES), len(SAMPLES) + 1, len(SAMPLES) + 2
I_KICK, I_SNARE, I_HAT = len(SAMPLES) + 3, len(SAMPLES) + 4, len(SAMPLES) + 5

# Note names (MIDI): A2=45 C3=48 D3=50 E3=52 F3=53 G3=55 A3=57 C4=60 D4=62
# E4=64 F4=65 G4=67 A4=69 C5=72 D5=74 E5=76 G5=79
A2, C3, E3, G3 = 45, 48, 52, 55
A3, C4, D4, E4, F4, G4 = 57, 60, 62, 64, 65, 67
A4, C5, D5, E5, G5 = 69, 72, 74, 76, 79
E2, F2, G2 = 40, 41, 43

E = 4   # eighth note = 4 ticks (grid: 2 ticks = 16th)
Q = 8   # quarter
H = 16  # half
BAR = 32


def track(events: list[tuple[int, int, int]], total: int) -> bytes:
    """events: absolute (tick, op, arg) sorted by tick; pads with rest to
    `total`, then OP_LOOP back to the track start."""
    blob = bytearray()
    t = 0
    for tick, op, arg in sorted(events):
        while tick - t > 255:
            blob += bytes((255, OP_REST, 1))
            t += 255
        blob += bytes((tick - t, op, arg))
        t = tick
    while total - t > 255:
        blob += bytes((255, OP_REST, 1))
        t += 255
    if t < total:
        blob += bytes((total - t, OP_REST, 1))
    blob += bytes((0, OP_LOOP, 0))
    return bytes(blob)


def build_song() -> bytes:
    """Stage BGM: compile the licensed MIDI when present; fall back to the
    16-bar hand-composed dojo loop otherwise."""
    try:
        import build_stage_song
        return build_stage_song.build()
    except Exception as exc:  # missing midi/tooling keeps the fallback theme
        print(f"stage midi unavailable ({exc}); using composed loop")
        return build_composed_song()


def build_composed_song() -> bytes:
    """Compose the 16-bar (~8.5s) dojo loop. Channels: 0 lead square,
    1 tri bass, 2 strings arp, 3 kick, 4 snare, 5 hat."""
    lead, bass, arp, kick, snare, hat = [], [], [], [], [], []

    # -- Lead: two 8-bar phrases over an Am martial vamp ----------------------
    # Bar phrase helper: append (midi, dur) pairs at a bar offset.
    def phrase(dst, bar, notes, vol_note=None):
        t = bar * BAR
        for note, dur in notes:
            if note is not None:
                dst.append((t, note, dur))
            t += dur

    p1 = [
        (A4, E), (None, E), (C5, E), (E5, E), (D5, E), (C5, E), (A4, E),
    ]
    p1 += [(A4, E)]
    p2 = [
        (A4, E), (G4, E), (A4, E), (C5, E), (E5, Q), (D5, E), (C5, E),
    ]
    p2 += [(D5, E)]
    p3 = [
        (E5, E), (D5, E), (C5, E), (D5, E), (E5, E), (G4, E), (A4, Q),
    ]
    p3 += [(A4, E)]
    p4 = [(A4, BAR)]
    p5 = [
        (A4, E), (None, E), (C5, E), (E5, E), (D5, E), (C5, E), (D5, E),
    ]
    p5 += [(C5, E)]
    p6 = [
        (E5, E), (D5, E), (C5, E), (D5, E), (E5, E), (E5, E), (D5, Q),
    ]
    p6 += [(C5, E)]
    p7 = [
        (A4, E), (C5, E), (D5, E), (E5, E), (D5, E), (C5, E), (D5, E),
    ]
    p7 += [(C5, E)]
    p8 = [(A4, BAR)]
    lead = [(0, OP_INST, I_SQR), (0, OP_VOL, 0x40), (0, OP_PAN, 2)] + lead
    for i, p in enumerate((p1, p2, p3, p4, p5, p6, p7, p8)):
        phrase(lead, i, p)

    # -- Bass: driving 8ths, Am-F-G-E vamp ------------------------------------
    roots = [A2, A2, F2, G2, A2, A2, G2, E2, A2, A2, F2, G2, A2, C3, G3, A3]
    for bar, root in enumerate(roots):
        for e in range(4):
            up = root + 12 if e == 3 else root
            bass.append((bar * BAR + e * Q, up, E))
            bass.append((bar * BAR + e * Q + E, root, E))
    bass = [(0, OP_INST, I_TRI), (0, OP_VOL, 0x58), (0, OP_PAN, 2)] + bass

    # -- Arp: 16th-note broken chords (Am F G E) --------------------------------
    B3 = 59
    chords = [
        [A3, C4, E4], [A3, C4, E4], [A3 - 4, A3, C4], [G3, B3, D4],
        [A3, C4, E4], [A3, C4, E4], [G3, B3, D4], [E2 + 12, G3, B3],
        [A3, C4, E4], [A3, C4, E4], [A3 - 4, A3, C4], [G3, B3, D4],
        [A3, C4, E4], [C4, E4, A4], [G3, B3, D4], [A3, C4, E4],
    ]
    for bar, chord in enumerate(chords):
        seq = [chord[0], chord[1], chord[2], chord[2] + 12,
               chord[2], chord[1], chord[0], chord[1]]
        for i, n in enumerate(seq * 2):
            arp.append((bar * BAR + i * 2, n, 2))
    arp = [(0, OP_INST, I_STR), (0, OP_VOL, 0x28), (0, OP_PAN, 1)] + arp

    # -- Drums ------------------------------------------------------------------
    for bar in range(16):
        kick += [(bar * BAR, 60, 4), (bar * BAR + 16, 60, 4)]
        if bar % 2:
            kick += [(bar * BAR + 24, 60, 4)]
        snare += [(bar * BAR + 8, 60, 4), (bar * BAR + 24, 60, 4)]
        for e in range(8):
            hat.append((bar * BAR + e * E, 60, 2))
    kick = [(0, OP_INST, I_KICK), (0, OP_VOL, 0x5C), (0, OP_PAN, 2)] + kick
    snare = [(0, OP_INST, I_SNARE), (0, OP_VOL, 0x48), (0, OP_PAN, 2)] + snare
    hat = [(0, OP_INST, I_HAT), (0, OP_VOL, 0x24), (0, OP_PAN, 3)] + hat

    total = 16 * BAR
    tracks = [
        track(lead, total), track(bass, total), track(arp, total),
        track(kick, total), track(snare, total), track(hat, total),
    ]
    header = bytearray(16)
    header[0] = 6
    off = 16
    for i, t in enumerate(tracks):
        struct.pack_into("<H", header, 2 + i * 2, off)
        off += len(t)
    song = bytes(header) + b"".join(tracks)
    print(f"song: {len(song)} bytes, {total} ticks (~{total/60:.1f}s loop)")
    return song


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    snd_cache: dict[str, dict[tuple[int, int], bytes]] = {}
    brr_blob = bytearray()
    dir_blob = bytearray(64 * 4)
    ids = []
    table = []

    for srcn, (name, desc, snd_rel, key, volume) in enumerate(SAMPLES):
        if snd_rel.endswith(".wav"):
            pcm, source_rate = load_wav_mono(ROOT / snd_rel)
        else:
            if snd_rel not in snd_cache:
                snd_cache[snd_rel] = load_mugen_snd(ROOT / snd_rel)
            raw = snd_cache[snd_rel].get(key)
            if raw is None:
                raise SystemExit(f"{snd_rel}: missing SND sample {key}")
            pcm, source_rate = load_wav_mono_bytes(raw)
        pcm = resample_mono(pcm, source_rate, SAMPLE_RATE)
        # Trim leading/trailing silence: the announcer WAVs carry dead air
        # and the SPC bank sits at the top of the 64 KiB audio RAM.
        floor = 600
        while pcm and abs(pcm[0]) < floor:
            pcm.pop(0)
        while pcm and abs(pcm[-1]) < floor:
            pcm.pop()
        peak = max((abs(v) for v in pcm), default=1) or 1
        # Avoid BRR clipping when a source already rides at full scale.
        if peak > 30000:
            gain = 30000 / peak
            pcm = [int(v * gain) for v in pcm]
        brr = encode_brr(pcm, loop=False)
        start = DIR_BASE + len(brr_blob)
        brr_blob += brr
        struct.pack_into("<HH", dir_blob, srcn * 4, start, start)
        ids.append(f".DEFINE {name} {srcn}\n")
        table.append(f"    .db {srcn}, ${volume:02X}    ; {desc}\n")
        print(
            f"{name:17s} {snd_rel}:{key[0] if key else '-'},"
            f"{key[1] if key else '-'} "
            f"{source_rate} Hz -> {SAMPLE_RATE} Hz, {len(pcm)} samples, "
            f"{len(brr)} BRR bytes"
        )

    # Music instrument slots follow the SFX clips in the same DIR bank.
    # Slots 21-23 are 32-sample melodic loops (PitchTab rate); 24-26 are
    # one-shot percussion at fixed PercPTab rates.
    insts = [
        ("INST_TRI", wave_cycle("tri", amp=20000), True, 0),
        ("INST_SQR", wave_cycle("square", amp=12000), True, 0),
        ("INST_STR", wave_cycle("strings", amp=11000), True, 0),
        ("INST_KICK", gen_kick(), False, 0x0400),
        ("INST_SNARE", gen_snare(), False, 0x0500),
        ("INST_HAT", gen_hat(), False, 0x0600),
    ]
    perc_rates = []
    for slot, (name, pcm, loop, rate) in enumerate(insts, start=len(SAMPLES)):
        brr = encode_brr(pcm, loop=loop)
        start = DIR_BASE + len(brr_blob)
        brr_blob += brr
        struct.pack_into("<HH", dir_blob, slot * 4, start, start if loop else 0)
        ids.append(f".DEFINE {name} {slot}\n")
        if not loop:
            perc_rates.append(rate)
        print(f"inst {name:10s} slot {slot}: {len(brr)} BRR bytes loop={loop}")

    (OUT / "spc_brr.bin").write_bytes(bytes(brr_blob))
    (OUT / "spc_dir.bin").write_bytes(bytes(dir_blob))
    (OUT / "spc_ids.inc").write_text(
        "; generated by build_audio.py\n" + "".join(ids)
        + ".DEFINE SPC_MUS_PLAY 30\n"
        + ".DEFINE SPC_MUS_STOP 31\n"

        + f".DEFINE INST_PERC {len(SAMPLES) + 3}\n"
    )
    (OUT / "spc_pitch.bin").write_bytes(pitch_table())
    (OUT / "spc_perc.inc").write_text(
        "; generated by build_audio.py -- PercPTab entries\n"
        "PercPTab:\n"
        + "".join(f"    .dw ${r:04X}\n" for r in perc_rates)
    )
    (OUT / "spc_song.bin").write_bytes(build_song())
    (OUT / "spc_tables.inc").write_text(
        "; generated by build_audio.py\n"
        f".DEFINE SFX_COUNT {len(SAMPLES)}\n"
        f".DEFINE SFX_PITCH ${DSP_PITCH:04X}\n"
        "IkSfxTable:\n" + "".join(table)
    )
    print(
        f"audio: {len(SAMPLES)} clips, {len(brr_blob)} BRR bytes, "
        f"end=${DIR_BASE + len(brr_blob):04X}"
    )


if __name__ == "__main__":
    main()
