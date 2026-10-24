#!/usr/bin/env python3
"""Verify diagnostic boot samples, live counters and rendered field values."""
import json
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from test_kyo_variants_headless import wait, tap, lock
from test_roster import parse_tables

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "build/msu_diag/kof98-msu-diag.sfc"
CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:!?'-/+>,@\""


def screenshot(core, path):
    from PIL import Image
    w, h, pitch, data, fmt = core.last_frame
    pixels = []
    for y in range(h):
        for x in range(w):
            n = int.from_bytes(data[y * pitch + x * (4 if fmt == 1 else 2):
                                    y * pitch + (x + 1) * (4 if fmt == 1 else 2)], 'little')
            if fmt == 1:
                pixels.append(((n >> 16) & 255, (n >> 8) & 255, n & 255))
            elif fmt == 2:
                pixels.append((((n >> 11) & 31) * 255 // 31,
                               ((n >> 5) & 63) * 255 // 63, (n & 31) * 255 // 31))
            else:
                pixels.append((((n >> 10) & 31) * 255 // 31,
                               ((n >> 5) & 31) * 255 // 31, (n & 31) * 255 // 31))
    im = Image.new("RGB", (w, h))
    im.putdata(pixels)
    im.save(path)


def main():
    global ROM
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', choices=(1, 2, 3, 4), type=int, default=1)
    version = parser.parse_args().version
    if version >= 2:
        ROM = ROOT / f'build/msu_diag{version}/kof98-msu-diag{version}.sfc'
    manifest = json.loads((ROM.parent / 'manifest.json').read_text())
    sample_count = len(manifest['samples'])
    c = Core(CORE, ROM)
    report = {}
    try:
        wait(c, lambda: c.word(0x1020) == 7, "opening")
        assert c.ram[0x107A] == 1, "MSU not detected"
        assert c.word(0x5418) == sample_count * 8, "boot did not complete all samples"
        assert [c.word(a) for a in (0x5400, 0x5402, 0x5416)] == [0, 0, 0]
        if version >= 2:
            for i, offset in enumerate(manifest['samples'].values()):
                base = 0x5440 + i * 32
                assert [c.word(base + n) for n in (0, 2, 4)] == [0, 0, 0]
                expected = (ROM.parent / f'sample{i}.bin').read_bytes()[:4]
                words = [int.from_bytes(expected[n:n + 2], 'big') for n in (0, 2)]
                for delta in (6, 10, 14, 18):
                    assert [c.word(base + delta), c.word(base + delta + 2)] == words
                assert [c.word(base + n) for n in (22, 24, 26)] == [0xFFFF] * 3
                if version >= 3:
                    assert c.word(base + 28) | c.word(base + 30) << 16 == offset
            report['boot'] = f'{sample_count} CPU/RAM/VRAM samples and first bytes matched'
            if version == 4:
                assert c.word(0x542C) == sample_count, 'sequential checkpoints incomplete'
                assert c.word(0x5428) | c.word(0x542A) << 16 == 0x800000
                report['boot'] = '8 direct CPU/DMA and sequential DMA checkpoints matched'
        else:
            report['boot'] = 'three CPU/MSU-DMA-VRAM samples matched'
        tap(c, 3)
        wait(c, lambda: c.word(0x1020) == 0, "title")
        c.step(60)
        tap(c, 3)
        wait(c, lambda: c.word(0x1020) == 6, "mode menu")
        c.ram[0xF070] = 1
        tap(c, 3)
        wait(c, lambda: c.word(0x1020) == 5, "select")
        c.ram[0x1091] = 0
        roster = {v['name']: v for v in parse_tables().values()}
        lock(c, 0, roster['rugal']['cell'])
        lock(c, 1, roster['leona']['cell'])
        tap(c, 3)
        wait(c, lambda: c.word(0x1020) == 1, "fight")
        c.buttons = [set(), set()]
        c.ram[0x1090] = c.ram[0x1091] = 0
        c.capture_video = True
        c.step(240)
        before = [c.word(a) for a in range(0x5404, 0x540E, 2)]
        for frame in range(180):
            c.buttons[0] = {1} if frame % 40 < 2 else set()
            c.buttons[1] = {8} if frame % 40 < 2 else set()
            c.step()
        c.buttons = [set(), set()]
        c.step(32)
        after = [c.word(a) for a in range(0x5404, 0x540E, 2)]
        req, ready, timeout, p1, p2 = after
        assert req == (ready + timeout) & 0xFFFF, after
        assert timeout == 0, after
        assert p1 > before[3] and p2 > before[4], (before, after)
        map_base, row_count = ((0x14400, 20 if version >= 3 else 13) if version >= 2
                               else (0x4700 + 5*64, 4))
        def read_rows():
            return [''.join(CHARSET[c.word(map_base + row * 64 + col * 2) & 0x3FF]
                            for col in range(32)).rstrip() for row in range(row_count)]
        rows = read_rows()
        if version == 4:
            assert rows[0] == 'MSU D4 LIMIT B0000 SQ0008', rows
            for i, (name, offset) in enumerate(manifest['samples'].items()):
                assert rows[1 + i * 2] == f'{name} {offset:08X} C0000 M0000 S0000', rows
                raw = (ROM.parent / f'sample{i}.bin').read_bytes()[:4].hex().upper()
                assert rows[2 + i * 2] == f'E {raw} M{raw} S{raw}', rows
            assert rows[17].startswith('REQ ') and rows[19].startswith('POS '), rows
        elif version == 3:
            assert rows[0] == 'MSU D3 SEEK B 0000', rows
            for i, (name, offset) in enumerate(manifest['samples'].items()):
                assert rows[1 + i * 2] == f'{name} {offset:08X} C0000 M0000 V0000', rows
                raw = (ROM.parent / f'sample{i}.bin').read_bytes()[:4].hex().upper()
                assert rows[2 + i * 2] == f'E {raw} C{raw} M{raw}', rows
            assert rows[17].startswith('REQ ') and rows[19].startswith('POS '), rows
        elif version == 2:
            assert rows[0] == 'MSU D2 VIA RAM B 0000', rows
            for i, name in enumerate(('RUG', 'CHI', 'KEN')):
                assert rows[1 + i * 3] == f'{name} C0000 M0000 V0000', rows
                raw = (ROM.parent / f'sample{i}.bin').read_bytes()[:4].hex().upper()
                assert rows[2 + i * 3] == f'E {raw} C {raw}', rows
                assert rows[3 + i * 3] == f'M {raw} V {raw}', rows
            assert rows[10].startswith('REQ ') and rows[12].startswith('POS '), rows
        else:
            assert rows[0] == 'MSU D1 CPU 0000 VRAM 0000', rows
            assert rows[1].startswith('REQ ') and rows[3].endswith('B 0000'), rows
        # The renderer must display actual 16-bit values, including A-F,
        # rather than a static template. Exercise it through real game frames.
        value1, value2 = (0x5440, 0x5442) if version >= 2 else (0x5400, 0x5402)
        c.put(value1, 0xABCD)
        c.put(value2, 0x1234)
        if version >= 2:
            c.put(0x5420, 0)
        c.step(32)
        if version == 4:
            assert read_rows()[1] == '00 0000FF00 CABCD M1234 S0000', read_rows()
        elif version == 3:
            assert read_rows()[1] == 'R0 00008000 CABCD M1234 V0000', read_rows()
        elif version == 2:
            assert read_rows()[1] == 'RUG CABCD M1234 V0000', read_rows()
        else:
            assert read_rows()[0] == 'MSU D1 CPU ABCD VRAM 1234', read_rows()
        c.put(value1, 0)
        c.put(value2, 0)
        if version >= 2:
            c.put(0x5420, 0)
        c.step(32)
        screenshot(c, ROM.parent / 'diagnostico_emulador.png')
        report.update(status='passed', counters=dict(zip(
            ('requests', 'ready', 'timeout', 'p1_dma', 'p2_dma'), after)), rows=rows)
        (ROM.parent / 'test-results.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    finally:
        c.close()


if __name__ == '__main__':
    main()
