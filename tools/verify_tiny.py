#!/usr/bin/env python3
"""Verify kof98-snes-tiny.sfc and its shared MSU-1 layout CRC.

The TINY ROM reuses the traditional kof98-snes.msu.  Its MsuDetect probe
compares the 8-byte "KOF98MSU" signature plus the 16-bit layout CRC stored
at bytes 8-9 of the .msu.  This script fixes the ROM checksum, runs the
standard PVSnesLib verification and asserts that the CRC linked into the
tiny ROM is the same one stored in the traditional .msu and in
build/gen_fight/msu1_bases.inc.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: verify_tiny.py <tiny.sfc> <kof98-snes.msu>")
    rom_path = Path(sys.argv[1])
    msu_path = Path(sys.argv[2])
    subprocess.run([sys.executable, str(ROOT / "tools" / "fix_checksum.py"),
                    str(rom_path)], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "verify_pvsnes_rom.py"),
                    str(rom_path)], check=True)

    rom = rom_path.read_bytes()
    msu = msu_path.read_bytes()
    if msu[:8] != b"KOF98MSU":
        raise SystemExit(f"{msu_path}: bad MSU signature")
    msu_crc = int.from_bytes(msu[8:10], "little")

    inc = (ROOT / "build" / "gen_fight" / "msu1_bases.inc").read_text()
    m = re.search(r"MSU_LAYOUT\s*=\s*\$([0-9A-Fa-f]+)", inc)
    if not m:
        raise SystemExit("MSU_LAYOUT not found in msu1_bases.inc")
    layout = int(m.group(1), 16)

    # MsuSig is the ROM copy of the signature + CRC.  It is the occurrence
    # followed by the expected CRC (the string also appears in diagnostics).
    rom_crc = None
    start = 0
    while True:
        i = rom.find(b"KOF98MSU", start)
        if i < 0:
            break
        crc = int.from_bytes(rom[i + 8:i + 10], "little")
        if crc == layout:
            rom_crc = crc
            break
        start = i + 1
    if rom_crc is None:
        raise SystemExit("tiny ROM does not link the traditional MSU_LAYOUT CRC")

    if not (rom_crc == msu_crc == layout):
        raise SystemExit(f"CRC mismatch: rom={rom_crc:#06x} "
                         f"msu={msu_crc:#06x} inc={layout:#06x}")
    print(f"tiny MSU detector CRC OK: ${layout:04X} "
          f"(shared with {msu_path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
