#!/usr/bin/env python3
"""Regression: a super move must not wipe the stage VRAM.

A large fighter sprite upload during a super used to let SprDmaP's DMA cursor
run past its 3 KiB ping-pong page when the sprite record/cursor was bad.
VRAM wrapped into $0000 and zeroed most of BG1/BG3, leaving the stage full of
garbage.  This test forces JpnStreet (the animated-crowd stage), performs
Kyo's super and watches BG1 CHR/map directly through libretro VRAM.

Only the BG1 CHR is expected to stay byte-identical; its crowd animation
also patches a handful of map cells, hence the small map allowance.
"""
from pathlib import Path
import ctypes as C
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from capture_pair_headless import tap, wait

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
ROM = ROOT / "kof98-snes.sfc"
SYMFILE = ROOT / "kof98-snes.symfull"
MSU = ROOT / "kof98-snes.msu"
GS = 0x1020
SEL1 = 0x1085
SEL2 = 0x1086
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
P1X = 0x4000
P2X = 0x4040
P1POW = 0x4030
P1STATE = 0x4008
P2STATE = 0x4048
DOWN, RIGHT, LEFT, X = 5, 7, 6, 9
SYM_BIAS = 0xC00000
VRAM_ID = 3
BG1CHR = (0x0000, 0x2000)             # words
BG1MAP = (0x4000, 0x4800)


def stage0_rom(tmpdir: Path) -> Path:
    """Patch CampStage's free-VS random pick to always return stage 0."""
    match = re.search(r"^([0-9a-fA-F]+) CampStage$", SYMFILE.read_text(), re.M)
    if not match:
        raise AssertionError("CampStage missing from kof98-snes.symfull")
    start = int(match.group(1), 16) - SYM_BIAS
    data = bytearray(ROM.read_bytes())
    pos = data.find(bytes((0xA9, 0xFF)), start, start + 80)
    if pos < 0:
        raise AssertionError("StagePick random immediate not found")
    data[pos + 1] = 0x00
    rom = tmpdir / "super-vram.sfc"
    rom.write_bytes(data)
    if MSU.exists():
        msu = tmpdir / "super-vram.msu"
        try:
            msu.symlink_to(MSU)
        except OSError:
            shutil.copyfile(MSU, msu)
    return rom


def qcf(core):
    for btns in ((DOWN,), (DOWN, RIGHT), (RIGHT,),
                 (DOWN,), (DOWN, RIGHT), (RIGHT,)):
        core.buttons[0] = set(btns)
        core.step(3)
        core.buttons[0] = set()
        core.step(1)


def diff_words(a, b, lo, hi):
    return sum(1 for i in range(lo * 2, hi * 2, 2) if a[i:i + 2] != b[i:i + 2])


def main():
    if not CORE.exists():
        raise SystemExit(f"missing libretro core: {CORE}")
    if not ROM.exists():
        raise SystemExit(f"build the ROM first: {ROM}")
    with tempfile.TemporaryDirectory(prefix="super-vram-",
                                     dir=ROOT / "build") as td:
        rom = stage0_rom(Path(td))
        core = Core(CORE, rom)
        try:
            vram_size = core.lib.retro_get_memory_size(VRAM_ID)
            vram_ptr = core.lib.retro_get_memory_data(VRAM_ID)
            if vram_size != 65536 or not vram_ptr:
                raise AssertionError("libretro VRAM is unavailable")
            vram = (C.c_ubyte * vram_size).from_address(vram_ptr)

            for _ in range(80):
                if core.ram[GS] == 6:
                    break
                tap(core, 3)
            wait(core, lambda: core.ram[GS] == 6, "mode menu")
            core.ram[0xF070] = 1               # SINGLE VS
            for _ in range(30):
                tap(core, 3)
                for _ in range(20):
                    if core.ram[GS] == 5:
                        break
                    core.step()
                if core.ram[GS] == 5:
                    break
            wait(core, lambda: core.ram[GS] == 5, "select")
            core.ram[SEL1] = 0                 # Kyo
            core.ram[SEL2] = 1                 # Iori
            core.ram[LOCK1] = 1
            core.ram[LOCK2] = 1
            core.ram[CPU1] = 0
            core.ram[CPU2] = 0
            core.step()
            wait(core, lambda: core.ram[GS] == 1, "fight")
            core.step(30)
            core.put(P1X, 100 << 8)
            core.put(P2X, 104 << 8)
            core.put(P1POW, 1000)
            core.step(20)

            base = bytes(vram)
            qcf(core)
            core.buttons[0] = {X}
            core.step(2)
            core.buttons[0] = set()

            states = []
            for tick in range(1, 220):
                core.step()
                state = core.ram[P1STATE]
                if not states or states[-1] != state:
                    states.append(state)
                cur = bytes(vram)
                chr_diff = diff_words(cur, base, *BG1CHR)
                map_diff = diff_words(cur, base, *BG1MAP)
                if chr_diff > 100 or map_diff > 400:
                    raise AssertionError(
                        f"stage VRAM wiped at tick {tick}: chr_diff={chr_diff} "
                        f"map_diff={map_diff} state={state} "
                        f"p2={core.ram[P2STATE]} states={states}")
            print("PASS super move kept the stage VRAM intact",
                  "states", states, "ticks", 220)
        finally:
            core.close()


if __name__ == "__main__":
    main()
