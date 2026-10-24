#!/usr/bin/env python3
"""TEAM PLAY: the HUD portraits must follow member swaps (P1 and P2).

TeamSwap uploads the 3x3 portrait tiles with a CPU loop (VrDma).  With the
display on, those VMDATA writes were dropped, leaving the first member's
face on screen while only the palette changed.  The upload now runs under
forced blank, like PpuInit/StagePick.
"""
from pathlib import Path
import ctypes as C
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from capture_pair_headless import tap, wait

GS = 0x1020
SEL1, SEL2 = 0x1085, 0x1086
TI1, TI2 = 0x10C8, 0x10C9
M_ITEM = 0xF070
HP1, HP2 = 0x4010, 0x4050

BG3CHR = 0x2000
hud = (ROOT / "build/gen_fight/hud.inc").read_text()
P1_TILE = int(re.search(r"PORTRAIT_P1 = (\d+)", hud).group(1))
P2_TILE = int(re.search(r"PORTRAIT_P2 = (\d+)", hud).group(1))
P1_BYTE = (BG3CHR + P1_TILE * 8) * 2
P2_BYTE = (BG3CHR + P2_TILE * 8) * 2

inc = (ROOT / "build/gen_fight/portraits.inc").read_text()
P1_OFS = [int(x) for x in re.findall(
    r"\d+", inc.split("PortraitOfs:\n", 1)[1].split("PortraitOfsP2:", 1)[0])]
P2_OFS = [int(x) for x in re.findall(
    r"\d+", inc.split("PortraitOfsP2:\n", 1)[1])]
PORTRAITS = (ROOT / "build/gen_fight/portraits.chr").read_bytes()


def main():
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    vram = (C.c_ubyte * core.lib.retro_get_memory_size(3)).from_address(
        core.lib.retro_get_memory_data(3))
    try:
        wait(core, lambda: core.ram[GS] == 7, "opening")
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 0, "title")
        core.step(4)
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 6, "menu")
        core.ram[M_ITEM] = 2                     # TEAM PLAY
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 5, "team select")
        core.step(20)
        for _ in range(10):
            before = core.ram[0x10C7]
            core.buttons[0] = {8}
            core.step(3)
            core.buttons[0] = set()
            if core.ram[0x10C7] > before and core.ram[0x10C7] >= 3:
                break
            core.buttons[0] = {7}
            core.step(3)
            core.buttons[0] = set()
            core.step(8)
        wait(core, lambda: core.ram[GS] == 1, "fight", 6000)
        core.step(120)

        def check(tag):
            p1 = bytes(vram[P1_BYTE:P1_BYTE + 144])
            p2 = bytes(vram[P2_BYTE:P2_BYTE + 144])
            s1, s2 = core.ram[SEL1], core.ram[SEL2]
            assert p1 == PORTRAITS[P1_OFS[s1]:P1_OFS[s1] + 144], \
                f"{tag}: P1 portrait is not sel {s1}"
            assert p2 == PORTRAITS[P2_OFS[s2]:P2_OFS[s2] + 144], \
                f"{tag}: P2 portrait is not sel {s2}"
            print(f"  {tag}: P1 sel {s1} OK, P2 sel {s2} OK")
            return s1, s2

        p1_0, p2_0 = check("battle 1")
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 0, "ko p2", 900)
        wait(core, lambda: core.ram[GS] == 1, "battle 2", 900)
        core.step(120)
        p1_1, p2_1 = check("after CPU swap")
        assert p2_1 != p2_0, "CPU portrait did not change"
        assert p1_1 == p1_0, "human portrait changed without a swap"
        core.put(HP1, 0)
        wait(core, lambda: core.ram[GS] == 0, "ko p1", 900)
        wait(core, lambda: core.ram[GS] == 1, "battle 3", 900)
        core.step(120)
        p1_2, p2_2 = check("after human swap")
        assert p1_2 != p1_1, "P1 portrait did not change"
        assert p2_2 == p2_1, "CPU portrait changed without a swap"
        print("PASS portraits follow P1 and P2 member swaps")
    finally:
        core.close()


if __name__ == "__main__":
    main()
