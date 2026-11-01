#!/usr/bin/env python3
"""Embed the M1VID1 opening video inside the game's kof98-snes.msu.

The SNES port ships a single MSU-1 data file.  Keeping the intro video in a
second file would force the user to copy two files to the SD card and would
make the intro depend on a file the game does not open.  This tool appends
the M1VID1 container to the existing game data at a 32 KiB boundary.

The layout CRC in bytes 8-9 of the 32 KiB MSU header is deliberately left
untouched: it versions the streamed-fighter CHR slices and must keep matching
the CRC linked into the ROM.  The video offset/length are stored in header
bytes 10-17 (previously unused), so tools can find the payload without
scanning a 30+ MiB file.

Idempotent: an existing embedded copy is replaced, not duplicated.

Writes:
    build/gen_fight/kof98-snes.msu   (build source of truth)
    kof98-snes.msu                   (runtime copy, atomic rename)
    build/gen_fight/msu1_bases.inc   (video constants for the engine)
    assets/video/Wmva3m93t34/manifest.json (msu metadata)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "assets/video/Wmva3m93t34/snes_video/Wmva3m93t34.m1vid"
MSU_BUILD = ROOT / "build/gen_fight/kof98-snes.msu"
MSU_ROOT = ROOT / "kof98-snes.msu"
BASES = ROOT / "build/gen_fight/msu1_bases.inc"
MANIFEST = ROOT / "assets/video/Wmva3m93t34/manifest.json"
ALIGN = 32768
VIDEO_MAGIC = b"M1VID1\0\0"


def parse_video(blob: bytes) -> dict:
    if blob[:8] != VIDEO_MAGIC:
        raise SystemExit(f"{VIDEO}: not an M1VID1 container")
    w, h, fps, flags = struct.unpack_from("<HHHH", blob, 8)
    count, duration_ms = struct.unpack_from("<II", blob, 16)
    data_start = 24 + count * 8
    if data_start > len(blob):
        raise SystemExit(f"{VIDEO}: truncated frame table")
    return {
        "width": w,
        "height": h,
        "fps": fps,
        "flags": flags,
        "frames": count,
        "duration_ms": duration_ms,
        "data_start": data_start,
    }


def find_old_video(msu: bytearray) -> int | None:
    """Return the offset of an already embedded M1VID1 blob, if any."""
    off = int.from_bytes(msu[10:14], "little")
    length = int.from_bytes(msu[14:18], "little")
    if off and length and off + 8 <= len(msu) and msu[off:off + 8] == VIDEO_MAGIC:
        if off % ALIGN == 0:
            return off
    # Fallback for files produced before the header metadata existed.
    for cand in range(ALIGN, len(msu) - 8, ALIGN):
        if msu[cand:cand + 8] == VIDEO_MAGIC:
            return cand
    return None


def write_atomic(path: Path, data: bytes):
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def update_bases(off: int, size: int, meta: dict):
    text = BASES.read_text() if BASES.exists() else ""
    text = "\n".join(
        line for line in text.splitlines()
        if not line.startswith("MSU_VIDEO_")
    )
    if text and not text.endswith("\n"):
        text += "\n"
    text += (
        "; opening FMV payload inside kof98-snes.msu (M1VID1)\n"
        f"MSU_VIDEO_SLICE = {off // ALIGN}\n"
        f"MSU_VIDEO_OFFSET = ${off:06X}\n"
        f"MSU_VIDEO_OFF0 = ${off & 0xFF:02X}\n"
        f"MSU_VIDEO_OFF1 = ${(off >> 8) & 0xFF:02X}\n"
        f"MSU_VIDEO_OFF2 = ${(off >> 16) & 0xFF:02X}\n"
        f"MSU_VIDEO_OFF3 = ${(off >> 24) & 0xFF:02X}\n"
        f"MSU_VIDEO_SIZE = {size}\n"
        f"MSU_VIDEO_FRAMES = {meta['frames']}\n"
        f"MSU_VIDEO_FPS = {meta['fps']}\n"
        f"MSU_VIDEO_DATA = {meta['data_start']}\n"
        f"MSU_VIDEO_BASE_LO = ${(off + meta['data_start']) & 0xFFFF:04X}\n"
        f"MSU_VIDEO_BASE_HI = ${((off + meta['data_start']) >> 16) & 0xFFFF:04X}\n"
        f"MSU_VIDEO_TABLE_LO = ${(off + 24) & 0xFFFF:04X}\n"
        f"MSU_VIDEO_TABLE_HI = ${((off + 24) >> 16) & 0xFFFF:04X}\n"
    )
    BASES.write_text(text)


def main() -> int:
    if not VIDEO.exists():
        raise SystemExit(f"missing {VIDEO}; run tools/build_snes_video.py first")
    if not MSU_BUILD.exists() and not MSU_ROOT.exists():
        raise SystemExit("no kof98-snes.msu found; build the game first")

    blob = VIDEO.read_bytes()
    meta = parse_video(blob)
    sha = hashlib.sha256(blob).hexdigest()

    source = MSU_BUILD if MSU_BUILD.exists() else MSU_ROOT
    msu = bytearray(source.read_bytes())
    if msu[:8] != b"KOF98MSU":
        raise SystemExit(f"{source}: not a KOF98MSU data file")
    crc_before = bytes(msu[8:10])

    old = find_old_video(msu)
    if old is not None:
        msu = msu[:old]
        print(f"replacing embedded video at {old:#x}")

    pad = (-len(msu)) % ALIGN
    msu += b"\0" * pad
    off = len(msu)
    msu += blob
    assert len(msu) == off + len(blob)

    # Header metadata only; bytes 8-9 (layout CRC) stay exactly as generated.
    struct.pack_into("<I", msu, 10, off)
    struct.pack_into("<I", msu, 14, len(blob))
    assert bytes(msu[8:10]) == crc_before, "layout CRC must not change"

    write_atomic(MSU_BUILD, bytes(msu))
    if MSU_ROOT.resolve() != MSU_BUILD.resolve():
        write_atomic(MSU_ROOT, bytes(msu))
    update_bases(off, len(blob), meta)

    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text())
        manifest["msu"] = {
            "file": "kof98-snes.msu",
            "embedded": True,
            "offset": off,
            "offset_hex": f"0x{off:06X}",
            "size": len(blob),
            "sha256": sha,
            "layout_crc": f"0x{crc_before[0] | (crc_before[1] << 8):04X}",
            "note": "same .msu file as the game data; no second runtime file",
        }
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)
                            + "\n")

    print(f"video : {VIDEO.name} {len(blob)} bytes sha256 {sha[:16]}...")
    print(f"msu   : {MSU_ROOT} {len(msu)} bytes")
    print(f"offset: 0x{off:06X} (slice {off // ALIGN}, 32 KiB aligned)")
    print(f"consts: {BASES} (MSU_VIDEO_OFFSET=0x{off:06X})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
