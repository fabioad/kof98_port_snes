#!/usr/bin/env python3
"""Load all 17 approved songs from the built ROM, using its sound-test UI.
Check each live SPC module header against the reviewed preview and observe
actual audio plus progressing game ticks across every upload handshake.
"""
import json
from pathlib import Path

from calibration.headless import Core
from test_start_transition import tap, wait_for

ROOT = Path(__file__).resolve().parents[1]
CORE = '/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so'
GS, FRAME, ITEM, OPT, SONG = 0x1020, 0x1024, 0xF070, 0xF079, 0xF07A
# smconv SPC of each approved module (music/ffg_hq/tools/build_hq.py)
PREVIEWS = ROOT / 'music/ffg_hq/spc'
ORDER = ['menu_cipher', 'menu_cipher_beta', 'menu_kof', 'menu_lastdance',
         'menu_sunset', 'menu_winner', 'menu_crystal'] + [f'stg{i}' for i in range(10)]


def apu(core):
    state = core.save().raw
    pos = state.index(b'SND:')
    size = int(state[pos+4:pos+10])
    assert size == 66560
    return state[pos+11:pos+11+65536]


def main():
    core = Core(CORE, ROOT / 'kof98-snes.sfc')
    rows = []
    try:
        wait_for(core, lambda: core.word(GS) in (7, 14), 'opening', 8000)
        tap(core, 3)
        wait_for(core, lambda: core.word(GS) == 0, 'title', 8000)
        core.step(20)                       # title song load (see test_start_transition)
        tap(core, 3)
        wait_for(core, lambda: core.word(GS) == 6, 'mode menu', 8000)
        core.ram[ITEM] = 6
        tap(core, 3)
        wait_for(core, lambda: core.word(GS) == 11, 'options')
        tap(core, 5)
        tap(core, 5)
        wait_for(core, lambda: core.ram[OPT] == 2, 'sound test')
        core.capture_audio = True
        for index, name in enumerate(ORDER):
            wait_for(core, lambda: core.ram[SONG] == index, name + ' select')
            preview = (PREVIEWS / (name+'.spc')).read_bytes()
            expected = preview[256+0x1a00:256+0x1a20]
            wait_for(core, lambda: apu(core)[0x1a00:0x1a20] == expected,
                     name + ' module uploaded', 1200)
            audio_before = core.audio_nonzero_batches
            frames = set()
            for _ in range(240):
                core.step()
                frames.add(core.word(FRAME))
            assert core.word(GS) == 11 and len(frames) > 120, name + ' game froze'
            assert core.audio_nonzero_batches > audio_before, name + ' no sound'
            assert apu(core)[0x1a00:0x1a20] == expected, name + ' ARAM header changed'
            rows.append(dict(song=name, index=index, status='passed',
                             liveHeaderMatchesPreview=True, uniqueGameTicks=len(frames),
                             audibleBatches=core.audio_nonzero_batches-audio_before))
            print('PASS sound-test', index, name, flush=True)
            tap(core, 7)
        assert core.ram[SONG] == 0, 'sound-test wrap failed'
        wait_for(core, lambda: apu(core)[0x1a00:0x1a20] ==
                 (PREVIEWS / 'menu_cipher.spc').read_bytes()[256+0x1a00:256+0x1a20],
                 'wrap module uploaded')
    finally:
        core.close()
    out = ROOT / 'build/ffg_music_runtime.json'
    out.write_text(json.dumps(rows, indent=2)+'\n')
    print('PASS all 17 approved modules: real ROM upload, live ARAM, audio and UI wrap')


if __name__ == '__main__':
    main()
