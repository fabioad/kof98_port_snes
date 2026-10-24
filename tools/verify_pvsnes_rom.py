#!/usr/bin/env python3
"""Validate the PVSnesLib Fast HiROM image produced by this project."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROM_SIZES = {8 * 1024 * 1024: 0x0D, 12 * 1024 * 1024: 0x0D,
             16 * 1024 * 1024: 0x0E}
HEADER_OFFSET = 0xFFC0


def fail(message: str) -> None:
    raise SystemExit(f"verify pvsnes: FAIL: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_pvsnes_rom.py kof98-snes.sfc")

    path = Path(sys.argv[1])
    data = path.read_bytes()
    if len(data) not in ROM_SIZES:
        fail(f"size is {len(data)}, expected one of {sorted(ROM_SIZES)}")

    header = data[HEADER_OFFSET : HEADER_OFFSET + 0x20]
    title = header[:21].decode("ascii", errors="replace").rstrip(" \0")
    if title != "KOF98 SNESFEST":
        fail(f"unexpected title {title!r}")
    if header[21] != 0x35:
        fail(f"map mode is ${header[21]:02X}, expected $35 (Fast ExHiROM)")
    if header[22] != 0x00 or header[24] != 0x00:
        fail("expected ROM-only cartridge without SRAM")
    if header[23] != ROM_SIZES[len(data)]:
        fail(f"ROM size byte is ${header[23]:02X}, "
             f"expected ${ROM_SIZES[len(data)]:02X} for {len(data)} bytes")

    complement, checksum = struct.unpack_from("<HH", data, HEADER_OFFSET + 0x1C)
    if checksum ^ complement != 0xFFFF:
        fail(f"checksum ${checksum:04X} / complement ${complement:04X} are not inverses")
    if sum(data) & 0xFFFF != checksum:
        fail(f"file checksum is ${sum(data) & 0xFFFF:04X}, header says ${checksum:04X}")

    vectors = data[HEADER_OFFSET + 0x20 : HEADER_OFFSET + 0x40]
    native_nmi = struct.unpack_from("<H", vectors, 0x0A)[0]
    emu_nmi = struct.unpack_from("<H", vectors, 0x1A)[0]
    reset = struct.unpack_from("<H", vectors, 0x1C)[0]
    if min(native_nmi, emu_nmi, reset) < 0x8000:
        fail("reset/NMI vectors do not point into the HiROM code window")

    soundbank_path = path.parent / "build/gen_audio/soundbank.bnk"
    if soundbank_path.exists():
        soundbank = soundbank_path.read_bytes()
        for offset in range(0, len(soundbank), 0x10000):
            bank = 51 + offset // 0x10000
            chunk = soundbank[offset : offset + 0x10000]
            rom_offset = bank * 0x10000
            if data[rom_offset : rom_offset + len(chunk)] != chunk:
                fail(f"soundbank chunk {offset // 0x10000} is not at bank {bank}, offset $0000")

    print(f"verify pvsnes: OK  {path}")
    print(f"  title     {title!r}")
    print("  map       Fast HiROM NTSC/U, ROM only, 4 MiB")
    print(f"  reset     ${reset:04X}")
    print(f"  nmi       native ${native_nmi:04X}  emu ${emu_nmi:04X}")
    print(f"  checksum  ${checksum:04X}")


if __name__ == "__main__":
    main()
