#!/usr/bin/env python3
"""Live HUD bands must not starve: keep LIFE dirty and watch the timer.

The old FlushHudLive always started at HUD_LIFE and sent at most one band
per frame.  With the life bar dirty every frame (damage/chip), the TIMER
band stayed stale in VRAM.  The band cursor also lived in DP $8B, which the
select screen uses as scratch, so it could start misaligned and clear the
wrong dirty bits, leaving HUD tiles blank for the whole fight.
"""
from pathlib import Path
import ctypes as C
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from capture_pair_headless import tap, wait
from test_roster import parse_tables

GS = 0x1020
RSECS = 0x1076
HUDMAP_W = 0x4700
BG3MAP_BYTE = 0x5000 * 2
TIMER_H = HUDMAP_W + (2 * 32 + 15) * 2
TIMER_V = BG3MAP_BYTE + (2 * 32 + 15) * 2
HP1 = 0x4010
TEL_HUD_BYTES = 0x51B8
TEL_HUD_FRAMES = 0x51BC


def main():
    # no .msu beside the ROM: the MSU handshake can stall Snes9x headless and
    # this regression only needs the ROM-resident HUD
    tmp = Path(tempfile.mkdtemp(prefix="kofhud"))
    rom = tmp / "kof98-snes.sfc"
    shutil.copyfile(ROOT / "kof98-snes.sfc", rom)
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so", rom)
    vram = (C.c_ubyte * core.lib.retro_get_memory_size(3)).from_address(
        core.lib.retro_get_memory_data(3))
    try:
        wait(core, lambda: core.ram[GS] == 7, "opening")
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 0, "title")
        core.step(4)
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 6, "menu")
        core.ram[0xF070] = 1                     # SINGLE VS
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 5, "select")
        core.step(10)
        roster = parse_tables()
        core.ram[0x1091] = 0
        core.ram[0xF053] = roster[1]["cell"]
        for _ in range(12):
            tap(core, 8, 1)
            if core.ram[0x108F]:
                break
        core.ram[0xF052] = roster[0]["cell"]
        for _ in range(12):
            tap(core, 8, 0)
            if core.ram[0x108E]:
                break
        wait(core, lambda: core.ram[GS] == 1, "fight", 6000)
        wait(core, lambda: core.word(0x4008) == 0
             and core.word(0x4048) == 0, "idle")
        core.step(30)

        def cells():
            return (bytes(core.ram[TIMER_H:TIMER_H + 4]),
                    bytes(vram[TIMER_V:TIMER_V + 4]))

        hud, vr = cells()
        assert hud == vr, f"timer cells not flushed at fight start: {hud} {vr}"
        assert vr != b"\x55\x55\x55\x55", "timer cells never uploaded"

        seen = core.ram[RSECS]
        pending = None
        for f in range(200):
            core.ram[HP1] = 199 if f & 1 else 200   # LIFE dirty every frame
            core.step()
            if core.ram[RSECS] != seen:
                seen = core.ram[RSECS]
                pending = 0
            if pending is not None:
                pending += 1
                hud, vr = cells()
                if hud == vr:
                    pending = None
                elif pending > 12:
                    raise AssertionError(
                        f"timer starvation: HUDMAP={list(hud)} "
                        f"VRAM={list(vr)} rsecs={seen}")
        assert seen < 99, f"timer never counted: {seen}"

        # A live band is 0x40/0x80 bytes; HUD_FULL is 0x800.  A larger
        # average means a band index/word ran off HudBandTab and FlushHudRange
        # is DMAing a chunk of WRAM over the stage and sprite pages.
        hud_bytes = (core.ram[TEL_HUD_BYTES]
                     | core.ram[TEL_HUD_BYTES + 1] << 8
                     | core.ram[TEL_HUD_BYTES + 2] << 16
                     | core.ram[TEL_HUD_BYTES + 3] << 24)
        hud_frames = core.word(TEL_HUD_FRAMES)
        assert hud_bytes <= hud_frames * 4096 + 4096, (
            f"HUD DMA overflow: {hud_bytes} bytes in {hud_frames} flushes")
        print(f"PASS HUD bands: timer reached {seen} with LIFE dirty every frame")
    finally:
        core.close()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
