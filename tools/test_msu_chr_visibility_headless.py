#!/usr/bin/env python3
"""Compare visible MSU fighter pages in VRAM byte-for-byte with the .msu.

Unlike a gameplay/clock smoke test, this fails when actors update but their
displayed tiles were never uploaded. Exercises both fighters and attacks.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'kof98-snes.sfc')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--screenshot', type=Path)
    args = parser.parse_args()
    image = args.rom.read_bytes()
    msu = args.rom.with_suffix('.msu').read_bytes()
    symbols = {f[1]: int(f[0], 16) & 0xFFFFFF
               for line in args.rom.with_suffix('.sym').read_text().splitlines()
               if len(f := line.split()) == 2}

    def filepos(address):
        bank, offset = (address >> 16) & 255, address & 65535
        if bank >= 0xC0:
            return (bank - 0xC0) * 65536 + offset
        if bank < 0x40 and offset >= 0x8000:
            return 0x400000 + bank * 65536 + offset
        if 0x40 <= bank < 0x7E:
            return bank * 65536 + offset
        raise AssertionError(f'unexpected ROM address ${address:06X}')

    def word_at(position):
        return int.from_bytes(image[position:position + 2], 'little')

    c = Core('/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so', args.rom.resolve())
    c.capture_video = bool(args.screenshot)
    checked, poses = 0, set()
    try:
        select = boot_select(c)
        vram = (C.c_ubyte * 65536).from_address(c.lib.retro_get_memory_data(3))
        for pair in (('rugal', 'leona'), ('chizuru', 'ken')):
            enter_fight(c, select, *pair)
            c.ram[0x1090] = c.ram[0x1091] = 0
            for frame in range(240):
                c.buttons = [{1} if frame % 50 < 2 else set(),
                             {8} if frame % 60 < 2 else set()]
                c.step()
                for side, name in enumerate(pair):
                    fp = 0x4000 + side * 0x40
                    descriptor = filepos(symbols['Char' + name.capitalize()])
                    assert c.word(fp + 44) == (symbols['Char' + name.capitalize()] & 65535)
                    assert image[descriptor + 23] & 1, name + ' is not MSU'
                    meta = c.word(fp + 22)
                    assert meta != 0, name + ' has no visible meta'
                    record = filepos(image[descriptor + 82] * 65536 + meta)
                    tilebase, length = word_at(record + 1), word_at(record + 3)
                    assert 0 < length <= 3072, (name, meta, length)
                    slice_index = (word_at(descriptor + 20) << 8) | image[descriptor + 22]
                    offset = slice_index * 32768 + tilebase * 32
                    expected = msu[offset:offset + length]
                    assert len(expected) == length
                    page = (0x6000 if side == 0 else 0x7000) * 2 + c.ram[fp + 27] * 32
                    actual = bytes(vram[page:page + length])
                    assert actual == expected, (
                        f'{name} frame={frame} meta=${meta:04X} page=${page:04X} '
                        f'MSU=${offset:08X} length={length}: '
                        f'{sum(a != b for a, b in zip(actual, expected))} tile bytes differ')
                    checked += 1
                    poses.add((name, meta))
        result = {'status': 'passed', 'visible_pages_checked': checked,
                  'distinct_character_poses': len(poses)}
        if args.screenshot:
            from test_msu_diag_headless import screenshot
            screenshot(c, args.screenshot)
        if args.output:
            args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
    finally:
        c.close()


if __name__ == '__main__':
    main()
