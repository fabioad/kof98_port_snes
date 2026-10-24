#!/usr/bin/env python3
"""Build the SPC700 data set for the standalone boot ROM.

Reuses the KOF '98 pipeline (build_spc_neogeo.py, same directory) so the
Neo Geo sample pack (ngbank) and the improved timbre bank apply here too.
Outputs into --out (src/gen_neogeo):

  spc_brr.bin / spc_dir.bin / spc_pitch.bin   instrument + SFX bank
  spc_perc.inc / spc_sfxframes.inc            driver tables
  song_mario.bin                              sequenced mario.mid song
  spc_songmeta.inc                            SONG_MARIO_BYTES define
"""

from __future__ import annotations

import argparse
import json
import struct
import wave
from pathlib import Path

import build_spc_neogeo as k


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--midi", type=Path, required=True, help="mario.mid to compile")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--timbre-bank", type=Path)
    ap.add_argument(
        "--neogeo-bank",
        type=Path,
        help="ngbank.json; pack slots override the generated timbres/percussion/SFX",
    )
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    waves = [
        ("piano", True, k.wave_cycle("piano")),
        ("bass", True, k.wave_cycle("tri", amp=20000)),
        ("guitar", True, k.wave_cycle("guitar", amp=14000)),
        ("square", True, k.wave_cycle("square", amp=12000)),
        ("strings", True, k.wave_cycle("strings", amp=10000)),
        ("flute", True, k.wave_cycle("sine", amp=16000)),
        ("vibes", True, k.wave_cycle("sine", amp=17000)),
        ("pad", True, k.wave_cycle("pad", amp=12000)),
        ("hit", False, k.gen_hit()),
        ("kick", False, k.gen_kick()),
        ("snare", False, k.gen_snare()),
        ("hat", False, k.gen_hat()),
    ]

    pack_slots: dict[int, dict] = {}
    if args.neogeo_bank:
        pack_meta = json.loads(args.neogeo_bank.read_text())
        pack_bin = (args.neogeo_bank.parent / "ngbank.bin").read_bytes()
        for key, v in pack_meta["slots"].items():
            v = dict(v)
            v["brr"] = pack_bin[v["off"] : v["off"] + v["len"]]
            pack_slots[int(key)] = v
        print(f"neogeo-bank: {len(pack_slots)} slots from {args.neogeo_bank}")

    brr_blob = bytearray()
    dir_blob = bytearray(64 * 4)
    starts: list[int] = []
    loops: list[int] = []
    addr = 0x1000
    for slot, (name, loop, pcm) in enumerate(waves):
        if slot in pack_slots:
            brr = pack_slots[slot]["brr"]
            loop = pack_slots[slot]["loop"]
        else:
            brr = k.encode_brr(pcm, loop)
        starts.append(addr)
        loops.append(addr if loop else 0)
        brr_blob += brr
        addr += len(brr)
        print(f"inst {name}: {len(brr)} bytes loop={loop}")

    # Repo-local sfx/<name>.wav overrides win over the pack; otherwise take the
    # pack slot or a synthesized fallback.
    repo_sfx = Path(__file__).resolve().parents[1] / "sfx"
    sfx_override_frames: dict[int, int] = {}
    sfx_override_pitch: dict[int, int] = {}
    for i, name in enumerate(k.SFX_NAMES):
        slot = k.INST_SFX0 + i
        wav = repo_sfx / f"{name}.wav"
        if wav.exists() or slot not in pack_slots:
            if wav.exists():
                samples, rate = k.load_wav_mono(wav)
            else:
                samples, rate = k.fallback_sfx(name)
            samples = k.resample_mono(samples, rate, 12000)
            if len(samples) > 128:
                samples = samples[:-64]
            peak = max((abs(x) for x in samples), default=1) or 1
            if peak < 8000:
                g = 16000 / peak
                samples = [int(x * g) for x in samples]
            brr = k.encode_brr(samples, False)
            sfx_override_frames[slot] = min(255, (len(samples) + 199) // 200)
            sfx_override_pitch[slot] = round(12000 * 4096 / 32000)
        else:
            brr = pack_slots[slot]["brr"]
        starts.append(addr)
        loops.append(0)
        brr_blob += brr
        addr += len(brr)
        print(f"sfx {name}: {len(brr)} bytes")

    for i, (st, lp) in enumerate(zip(starts, loops)):
        struct.pack_into("<HH", dir_blob, i * 4, st, lp)

    if args.timbre_bank and not all(s in pack_slots for s in range(k.TIMBRE_COUNT)):
        improved = args.timbre_bank.read_bytes()
        if len(improved) < k.TIMBRE_BRR_BYTES:
            raise SystemExit(
                f"{args.timbre_bank}: expected at least {k.TIMBRE_BRR_BYTES} bytes "
                "for the eight melodic timbres"
            )
        timbres = improved[: k.TIMBRE_BRR_BYTES]
        for i in range(k.TIMBRE_COUNT):
            headers = timbres[i * 18 : (i + 1) * 18 : 9]
            if headers[0] & 1 or not headers[1] & 1:
                raise SystemExit(
                    f"{args.timbre_bank}: timbre {i} must have exactly two BRR blocks "
                    "with END only on the second block"
                )
        brr_blob[: k.TIMBRE_BRR_BYTES] = timbres
        print(f"timbres: replaced first {k.TIMBRE_BRR_BYTES} bytes from {args.timbre_bank}")

    VOX_FIRST_SRCN = 22
    VOX_LAST_SRCN = 29
    VOX_PITCH = round(6000 * 4096 / 32000)
    perc = []
    for slot in range(k.INST_KICK, VOX_LAST_SRCN + 1):
        if slot in sfx_override_pitch:
            perc.append(sfx_override_pitch[slot])
            continue
        entry = pack_slots.get(slot)
        if entry is not None:
            perc.append(entry["pitch"])
        elif VOX_FIRST_SRCN <= slot <= VOX_LAST_SRCN:
            perc.append(VOX_PITCH)
        else:
            perc.append({9: 0x0600, 10: 0x0800, 11: 0x0C00, 12: 0x0A00}.get(slot, 0x0800))
    sfx_frames = []
    for i in range(len(k.SFX_NAMES)):
        slot = k.INST_SFX0 + i
        if slot in sfx_override_frames:
            sfx_frames.append(sfx_override_frames[slot])
            continue
        entry = pack_slots.get(slot)
        if entry is not None:
            sfx_frames.append(min(255, entry["frames"]))
        else:
            sfx_frames.append([10, 10, 18, 14, 10, 33, 48, 4, 5, 24][i])
    sfx_frames += [48] * 8
    (out / "spc_perc.inc").write_text(
        "; generated by build_mario_spc.py -- PercPTab entries\n    .dw "
        + ", ".join(f"${v:04X}" for v in perc)
        + "\n"
    )
    (out / "spc_sfxframes.inc").write_text(
        "; generated by build_mario_spc.py -- SfxFrames entries\n    .db "
        + ", ".join(str(v) for v in sfx_frames)
        + "\n"
    )

    (out / "spc_pitch.bin").write_bytes(k.pitch_table())
    (out / "spc_dir.bin").write_bytes(bytes(dir_blob))
    (out / "spc_brr.bin").write_bytes(bytes(brr_blob))

    song = k.compile_midi(args.midi, voice_limit=6)
    # The upload handshake moves 3 bytes per group; pad so the driver's load
    # counter never waits for bytes the CPU did not send.
    pad = (-len(song)) % 3
    song += bytes(pad)
    if len(song) > 0x7E00:
        raise SystemExit(
            f"{args.midi}: compiled song is {len(song)} bytes; exceeds the "
            "$8200-$FFFF SPC song window"
        )
    (out / "song_mario.bin").write_bytes(song)
    (out / "spc_songmeta.inc").write_text(f".DEFINE SONG_MARIO_BYTES {len(song)}\n")
    print(f"song_mario.bin: {len(song)} bytes (pad {pad})")
    print(f"brr end ${0x1000 + len(brr_blob):04X} total brr={len(brr_blob)}")


if __name__ == "__main__":
    main()
