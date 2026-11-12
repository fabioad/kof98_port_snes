#!/usr/bin/env python3
"""Headless check of kof98-ffg-soundtest.sfc: every song plays in both
versions (NOVA and ATUAL) and the list wraps around.  Saves a screenshot."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from calibration.headless import Core                         # noqa: E402
from capture_clark_throws_headless import save_frame          # noqa: E402

CORE = '/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so'
B, SELECT, START, UP, DOWN, A = 0, 2, 3, 4, 5, 8
NSONGS = 17


def tap(core, button, hold=3, after=70):
    # spcLoad blocks the main loop up to ~1.1 s (largest module), and pad
    # edges that start and end inside it are not seen: wait it out.
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
        core.step(90)                       # boots straight into song 0 NOVA
        fails = []
        for song in range(NSONGS):
            if song:
                tap(core, DOWN)
            row = []
            for version in ('NOVA', 'ATUAL'):
                tap(core, A)
                core.step(40)               # spcLoad + first ticks
                n = audible(core, 150)
                row.append(f'{version}={n}')
                # some arrangements have rests (stg7, stg9): just need sound
                if n < 40:
                    fails.append((song, version, n))
                tap(core, SELECT)           # switch version (restarts song)
            tap(core, SELECT)               # back to NOVA
            print(f'song {song:2d}: ' + ' '.join(row), flush=True)
        core.step(60)                       # let the last spcLoad finish
        tap(core, B, hold=8)
        core.step(10)
        silent = audible(core, 60)
        tap(core, DOWN)                     # wraps to song 0
        tap(core, A)
        core.step(40)
        wrapped = audible(core, 60)
        core.step(5)
        save_frame(core.last_frame, ROOT / 'build/ffg_soundtest_screen.png')
        assert not fails, f'silent songs: {fails}'
        assert silent < 10, f'B did not stop the music ({silent} audible batches)'
        assert wrapped > 30, 'list did not wrap to song 0'
        print(f'PASS soundtest: {NSONGS} songs x 2 versions audible, stop and wrap OK')
    finally:
        core.close()


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'kof98-ffg-soundtest.sfc')
