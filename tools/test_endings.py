#!/usr/bin/env python3
"""Exercise every ending screen in the real SNES renderer.

The old ExHiROM placement rendered the same two-color stripe pattern on all
screens because the CPU read from the unmapped lower half of banks $32-$3D.
"""
import argparse
import ctypes as C
import hashlib
from pathlib import Path

from calibration.headless import Core
from test_start_transition import GS, START, tap, wait_for

ROOT = Path(__file__).resolve().parents[1]


def run(core_path, rom):
    core = Core(core_path, rom)
    frames = []

    @C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
    def video(data, width, height, pitch):
        if data:
            frame = C.string_at(data, pitch * height)
            frames[:] = [b"".join(frame[y * pitch:y * pitch + width * 2]
                                 for y in range(height))]

    core.lib.retro_set_video_refresh(video)
    try:
        wait_for(core, lambda: core.word(GS) == 7, "opening")
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 0, "title")
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 6, "menu")
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 5, "select")
        tap(core, START)
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 1, "fight")

        # Resolve the final campaign match through the normal game loop.
        core.ram[0xF040] = 1     # single play
        core.ram[0xF041] = 6     # Rugal confrontation
        core.ram[0x1080] = 2     # wins1
        core.ram[0x1081] = 0     # wins2
        core.ram[0x1084] = 2     # match-over banner
        core.ram[0x1024] = 59    # next tick resolves the result
        core.ram[GS] = 0
        wait_for(core, lambda: core.word(GS) == 8, "ending")

        hashes = set()
        for screen in range(23):
            wait_for(core, lambda: core.ram[0xF078] == screen,
                     f"ending screen {screen}")
            # sample mid-hold: normal screens finish the white fade-in
            # around frame 124, montage cards (6-20) around frame 16
            core.step(30 if 6 <= screen <= 20 else 140)
            assert frames, "no video output"
            colors = set(memoryview(frames[0]).cast("H"))
            # sepia pair cards quantize down to ~11-17 colors; normal
            # screens carry 24+.  the assertion only needs to catch the
            # old flat-stripe failure mode
            want = 8 if 6 <= screen <= 20 else 16
            assert len(colors) > want, (
                f"ending screen {screen} has only {len(colors)} colors")
            digest = hashlib.sha256(frames[0]).digest()
            assert digest not in hashes, f"ending screen {screen} repeats art"
            hashes.add(digest)
            print(f"PASS ending {screen:02d}: {len(colors)} colors", flush=True)
            if screen < 22:
                tap(core, START)
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 0, "return to title")
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default="/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    run(args.core, args.rom)
