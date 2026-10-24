#!/usr/bin/env python3
"""A projectile fired facing left must mirror the right-facing cells exactly.

DrawSparks sign-extended each cell dx into A but stored the raw byte back in
scr3; the mirrored path (dx' = origin - dx - 16) then subtracted the unsigned
byte.  Cells with negative dx were pushed ~240 px left and clipped, which made
every left-facing shot look cut off.
"""
from pathlib import Path
import struct
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, FP2 = 0x4008, 0x40
F_X = 0x4000
SPARKS, SPK = 0x4200, 20
OAM = 0x1800
DOWN, LEFT, RIGHT = 5, 6, 7
LIGHT_P = 9


def press(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()
    core.step(ticks)


def effect_cells(core):
    ox = struct.unpack_from("<H", core.ram, SPARKS)[0]
    oy = struct.unpack_from("<H", core.ram, SPARKS + 2)[0]
    oam = bytes(core.ram[OAM:OAM + 512])
    rel, hflip = [], None
    for i in range(128):
        x, y, tile, a = oam[i * 4:i * 4 + 4]
        if (a & 0x0E) == 4 and y < 0xF0 and abs(x - ox) < 64 \
                and abs(y - oy) < 64:
            rel.append(x - ox)
            hflip = bool(a & 0x40)
    return sorted(rel), hflip


def main():
    tmp = Path(tempfile.mkdtemp(prefix="kofproj"))
    rom = tmp / "kof98-snes.sfc"
    shutil.copyfile(ROOT / "kof98-snes.sfc", rom)
    core = Core(CORE, rom)
    try:
        sel = boot_select(core)
        enter_fight(core, sel, "terry", "terry")   # Terry/Andy/Joe are ROM-resident
        core.put(F_X, 60 << 8)
        core.put(F_X + FP2, 210 << 8)
        core.step(20)
        for d in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
            press(core, d)
        press(core, {LIGHT_P})
        snap = None
        for _ in range(60):
            if struct.unpack_from("<H", core.ram, SPARKS + 4)[0]:
                right, hf = effect_cells(core)
                if right:
                    assert not hf, "right-facing cells must not be h-flipped"
                    snap = bytes(core.ram[SPARKS:SPARKS + SPK])
                    break
            core.step()
        assert snap, "no right-facing projectile captured"

        slot = bytearray(snap)
        struct.pack_into("<H", slot, 0, 120)       # origin x
        vx = struct.unpack_from("<H", slot, 8)[0]
        struct.pack_into("<H", slot, 8, (-vx) & 0xFFFF)
        slot[15] |= 0x10                          # fired facing left
        slot[14] = 30
        core.ram[SPARKS:SPARKS + SPK] = slot
        core.step(2)
        left, hf = effect_cells(core)
        want = sorted(-v - 16 for v in right)
        assert hf, "mirrored cells must set the OAM h-flip bit"
        assert left == want, (left, want)
        print(f"PASS projectile mirror: {right} -> {left}")
    finally:
        core.close()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
