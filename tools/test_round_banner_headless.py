#!/usr/bin/env python3
"""Regression: the ROUND intermission must not keep stale fight OAM.

F_META and the spark animation pointers are 16-bit.  ShowTitle used to clear
only their low bytes (8-bit A), leaving a $XX00 pointer that made BuildOam
paint a garbage metasprite row over the bottom of the ROUND screen.  This
drives a real round transition and checks both the pointers and the OAM
shadow.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from capture_pair_headless import tap, wait

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
GS = 0x1020
FRAME = 0x1024
NEXTFLAG = 0x1084
SEL1 = 0x1085
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
HP2 = 0x4050
F_META1 = 0x4016
F_META2 = 0x4056
SPK0 = 0x4204
SPK1 = 0x4216
OAMBUF = 0x1800


def word(core, addr):
    return core.ram[addr] | core.ram[addr + 1] << 8


def main():
    if not CORE.exists():
        raise SystemExit(f"missing libretro core: {CORE}")
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        for _ in range(80):
            if core.ram[GS] == 6:
                break
            tap(core, 3)
        wait(core, lambda: core.ram[GS] == 6, "mode menu")
        core.ram[0xF070] = 0               # SINGLE PLAY
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 5, "select")
        core.ram[SEL1] = 0
        core.ram[LOCK1] = 1
        core.ram[LOCK2] = 1
        core.ram[CPU1] = 0
        core.ram[CPU2] = 1
        core.step()
        wait(core, lambda: core.ram[GS] == 1, "round 1")
        core.put(HP2, 0)                   # P1 takes round 1 -> ROUND 2
        wait(core, lambda: core.ram[GS] == 0 and
             core.ram[NEXTFLAG] == 1, "ROUND 2 banner", limit=1500)
        core.step(10)

        assert word(core, F_META1) == 0, hex(word(core, F_META1))
        assert word(core, F_META2) == 0, hex(word(core, F_META2))
        assert word(core, SPK0) == 0, hex(word(core, SPK0))
        assert word(core, SPK1) == 0, hex(word(core, SPK1))

        stale = [i for i in range(128)
                 if core.ram[OAMBUF + i * 4 + 1] != 0xF0]
        assert not stale, f"stale OAM cells on ROUND banner: {stale[:8]}"
        print("PASS ROUND 2 banner has no stale fight OAM",
              "frame", core.ram[FRAME], "nextflag", core.ram[NEXTFLAG])
    finally:
        core.close()


if __name__ == "__main__":
    main()
