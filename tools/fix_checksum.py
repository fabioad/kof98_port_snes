#!/usr/bin/env python3
"""Rewrite the SNES checksum/complement so it covers the whole file.

WLA-dx computes the .SNESHEADER checksum over the first 8 MiB only, which
is wrong once the ROM grows to 16 MiB (BIGROM=1).  We pick the checksum so
that sum(file) & 0xFFFF == checksum, matching tools/verify_pvsnes_rom.py.
"""

import struct
import sys

HEADER_OFFSET = 0xFFC0


def main(path):
    data = bytearray(open(path, "rb").read())
    comp, chk = struct.unpack_from("<HH", data, HEADER_OFFSET + 0x1C)
    rest = (sum(data) - comp - chk) & 0xFFFF
    comp = (-rest) & 0xFFFF         # rest + comp + chk == chk (mod 0x10000)
    chk = comp ^ 0xFFFF
    struct.pack_into("<HH", data, HEADER_OFFSET + 0x1C, comp, chk)
    # the ExHiROM header mirrors at file offset 0x40FFC0
    struct.pack_into("<HH", data, 0x40FFC0 + 0x1C, comp, chk)
    open(path, "wb").write(data)
    print(f"checksum ${chk:04X} / complement ${comp:04X}")


if __name__ == "__main__":
    main(sys.argv[1])
