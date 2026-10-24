#!/usr/bin/env python3
"""Validate the initial KOF '98 ExHiROM bootstrap image."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROM_SIZE = 8 * 1024 * 1024
HEADER_OFFSET = 0x40FFC0
CODE_OFFSET = 0x408000


def fail(message: str) -> None:
    raise SystemExit(f"verify boot: FAIL: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_boot_rom.py build/neogeo_snes.sfc")

    path = Path(sys.argv[1])
    data = path.read_bytes()
    if len(data) != ROM_SIZE:
        fail(f"size is {len(data)}, expected {ROM_SIZE}")

    header = data[HEADER_OFFSET : HEADER_OFFSET + 0x20]
    title = header[:21].decode("ascii", errors="replace").rstrip(" \0")
    if header[21] != 0x35:
        fail(f"map mode is ${header[21]:02X}, expected $35 (Fast ExHiROM)")
    if header[23] != 0x0D:
        fail(f"ROM size byte is ${header[23]:02X}, expected $0D (8 MiB)")
    if header[22] != 0x00 or header[24] != 0x00:
        fail("expected ROM-only cartridge without SRAM")

    complement, checksum = struct.unpack_from("<HH", data, HEADER_OFFSET + 0x1C)
    if (checksum ^ complement) != 0xFFFF:
        fail(f"checksum ${checksum:04X} / complement ${complement:04X} are not inverses")

    vectors = data[HEADER_OFFSET + 0x20 : HEADER_OFFSET + 0x40]
    native_nmi = struct.unpack_from("<H", vectors, 0x0A)[0]
    emu_nmi = struct.unpack_from("<H", vectors, 0x1A)[0]
    reset = struct.unpack_from("<H", vectors, 0x1C)[0]
    if reset < 0x8000 or native_nmi < 0x8000 or emu_nmi < 0x8000:
        fail("reset/NMI vectors do not point into the ROM code window")
    if data[CODE_OFFSET] != 0x78:
        fail("reset entry does not begin with SEI")

    print(f"verify boot: OK  {path}")
    print(f"  title     {title!r}")
    print("  map       Fast ExHiROM NTSC/U, ROM only, 8 MiB")
    print(f"  reset     ${reset:04X}")
    print(f"  nmi       native ${native_nmi:04X}  emu ${emu_nmi:04X}")
    print(f"  checksum  ${checksum:04X}")


if __name__ == "__main__":
    main()
