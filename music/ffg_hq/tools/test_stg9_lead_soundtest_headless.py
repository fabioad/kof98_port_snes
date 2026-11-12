#!/usr/bin/env python3
"""Headless check of kof98-stg9-lead-soundtest.sfc: every version plays from
the start (A) and from order 7 (X), R switches version, B stops.  Saves a
screenshot to build/stg9_lead_soundtest_screen.png."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from calibration.headless import Core                         # noqa: E402
from capture_clark_throws_headless import save_frame          # noqa: E402

CORE = '/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so'
B, Y, SELECT, START, UP, DOWN, LEFT, RIGHT, A, X, L, R = range(12)
NVER = 5


def tap(core, button, hold=3, after=70):
    core.buttons[0] = {button}
    core.step(hold)
    core.buttons[0] = set()
    core.step(after)


def audible(core, frames):
    core.audio_nonzero_batches = 0
    core.step(frames)
    return core.audio_nonzero_batches


def main(rom):
    core = Core(CORE, rom)
    core.capture_audio = True
    core.capture_video = True
    try:
        core.step(90)
        fails = []
        for v in range(NVER):
            if v:
                tap(core, DOWN)
            tap(core, A)
            core.step(40)
            a = audible(core, 150)
            tap(core, X)
            core.step(40)
            x = audible(core, 150)
            print(f'version {v}: start={a} order7={x}', flush=True)
            if a < 40 or x < 40:
                fails.append((v, a, x))
        tap(core, R)                         # wraps to version 0, keeps order 7
        core.step(40)
        r = audible(core, 120)
        core.step(5)
        save_frame(core.last_frame, ROOT / 'build/stg9_lead_soundtest_screen.png')
        tap(core, B, hold=8)
        core.step(10)
        silent = audible(core, 60)
        assert not fails, f'silent versions: {fails}'
        assert r > 30, 'R did not start the next version'
        assert silent < 10, f'B did not stop ({silent})'
        print(f'PASS stg9 lead soundtest: {NVER} versions audible (start and order 7), R and B OK')
    finally:
        core.close()


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'kof98-stg9-lead-soundtest.sfc')
