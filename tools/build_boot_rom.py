#!/usr/bin/env python3
"""Wrap the linked 32 KiB ExHiROM boot image into an 8 MiB SNES ROM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROM_SIZE = 8 * 1024 * 1024
EXHIROM_BANK0_FILE_OFFSET = 0x408000
HEADER_OFFSET = 0x40FFC0
FLAT_SIZE = 0x8000


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_boot_rom.py LINKED_FLAT OUTPUT_ROM")

    flat_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    flat = flat_path.read_bytes()
    if len(flat) != FLAT_SIZE:
        raise SystemExit(
            f"linked bootstrap is {len(flat)} bytes; expected {FLAT_SIZE} bytes"
        )

    rom = bytearray(ROM_SIZE)
    rom[EXHIROM_BANK0_FILE_OFFSET : EXHIROM_BANK0_FILE_OFFSET + FLAT_SIZE] = flat

    # The checksum fields are included as zero while computing the checksum.
    checksum_offset = HEADER_OFFSET + 0x1E
    complement_offset = HEADER_OFFSET + 0x1C
    struct.pack_into("<HH", rom, complement_offset, 0, 0)
    checksum = sum(rom) & 0xFFFF
    complement = checksum ^ 0xFFFF
    struct.pack_into("<HH", rom, complement_offset, complement, checksum)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(rom)
    print(f"built {output_path} ({len(rom)} bytes, checksum ${checksum:04X})")


if __name__ == "__main__":
    main()
