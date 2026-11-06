#!/usr/bin/env python3
"""Soak the fight pause; verify CPU/SPC progress, frozen gameplay and resume.

Example: python3 tools/test_fight_pause_soak_headless.py --minutes 7
Snes9x serializes SPC RAM at the beginning of its SND snapshot block. The
SNESMOD driver stores mod_row/mod_position at ARAM $19/$1A. Sampling these
catches a stuck music sequencer even if the DSP still produces a held tone.
"""
import argparse
import ctypes as C
import json
from pathlib import Path

from calibration.headless import Core
from capture_pair_headless import tap, wait
from test_boss_intro_headless import start_single

ROOT = Path(__file__).resolve().parents[1]


def music_cursor(core):
    state = core.save().raw
    start = state.index(b'SND:066560:') + 11
    return tuple(state[start + 0x19:start + 0x1B])


def run(minutes, stages, rom, output):
    core = Core('/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so', rom)
    batches = [0]
    report = []

    @C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
    def audio(data, size):
        if data and size and any(C.string_at(data, size * 4)):
            batches[0] += 1
        return size

    core.lib.retro_set_audio_sample_batch(audio)
    try:
        start_single(core)
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.step(30)
        base = core.save()
        for stage in stages:
            core.load(base)
            core.buttons = [set(), set()]
            # Use the real next-round path to load this stage and its song.
            core.ram[0x10C4] = stage
            core.ram[0x10E6] = 0
            core.ram[0x1084] = 1
            core.ram[0x1082] = 2
            core.ram[0x1020] = 0
            core.ram[0x1024] = 59
            core.step()
            wait(core, lambda: core.ram[0x1020] == 1, 'next round', 5000)
            assert core.ram[0x1087] == stage
            core.step(40)
            tap(core, 3)
            wait(core, lambda: core.ram[0x4FB0] == 1, 'pause open')
            frozen = tuple(core.word(addr) for addr in (0x4000, 0x4002, 0x4040, 0x4042))
            timer = core.ram[0x1076]
            for minute in range(minutes):
                cursors = {music_cursor(core)}
                batches[0] = 0
                for _ in range(4):
                    before = core.ram[0x1024]
                    core.step(900)
                    assert core.ram[0x1024] != before, f'stage {stage}: CPU stopped'
                    assert core.ram[0x1020] == 1 and core.ram[0x4FB0] == 1
                    assert tuple(core.word(addr) for addr in (0x4000, 0x4002, 0x4040, 0x4042)) == frozen
                    assert core.ram[0x1076] == timer, 'round clock advanced during pause'
                    cursors.add(music_cursor(core))
                assert len(cursors) > 1, f'stage {stage}: music sequencer stopped'
                assert batches[0] > 1800, f'stage {stage}: prolonged audio silence'
                report.append(dict(stage=stage, minute=minute+1,
                                   music_cursors=sorted(cursors), audio_batches=batches[0]))
                print(f'PASS stage {stage} paused minute {minute+1}: CPU, SPC, audio, frozen gameplay', flush=True)
            tap(core, 3)
            wait(core, lambda: core.ram[0x4FB0] == 0, 'resume')
            previous = core.word(0x4000)
            core.buttons[0] = {7}
            core.step(25)
            core.buttons[0] = set()
            assert core.ram[0x1020] == 1 and core.word(0x4000) != previous, 'fight did not resume'
            print(f'PASS stage {stage}: resume and fighter movement', flush=True)
    finally:
        core.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--minutes', type=int, default=7)
    parser.add_argument('--stages', type=int, nargs='+', default=list(range(10)))
    parser.add_argument('--rom', type=Path, default=ROOT / 'kof98-snes.sfc')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/long_pause/regression.json')
    args = parser.parse_args()
    assert args.minutes > 0 and all(0 <= stage < 10 for stage in args.stages)
    run(args.minutes, args.stages, args.rom, args.output)
