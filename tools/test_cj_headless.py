#!/usr/bin/env python3
"""Verify CJ's shared select slot, CPU pools, and inputs on the SNES ROM."""
import argparse
import re
from pathlib import Path

from test_counter_grab_headless import (
    A, CORE, GS, ROOT, Core, boot_select, enter_fight, parse_tables, wait,
)
from test_gta_trio_headless import (
    B, X, Y, QCF, QCF2, QCB2, P1_POWER, P1_STATE, P1_X, P2_X, motion,
)

P1_HP = 0x4010
P1_INVUL = 0x403E
SPARKS = 0x4200
L, LEFT, RIGHT = 10, 6, 7


def check_mobility(core, ready):
    for forward, back in ((RIGHT, LEFT), (LEFT, RIGHT)):
        sign = 1 if forward == RIGHT else -1
        for sid, buttons, direction in ((69, {L}, 0), (94, {L, back}, -1),
                                        (95, {L, forward}, 1),
                                        (45, {forward}, 1), (46, {back}, -1)):
            core.load(ready)
            core.buttons = [set(), set()]
            core.put(P1_X, (80 if sign == 1 else 176) << 8)
            core.put(P2_X, (205 if sign == 1 else 51) << 8)
            core.step(12)
            if sid in (45, 46):
                core.buttons[0] = buttons
                core.step(4)
                core.buttons[0] = set()
                core.step(4)
            x0 = core.word(P1_X)
            core.buttons[0] = buttons
            wait(core, lambda: core.ram[P1_STATE] == sid, f'CJ mobility {sid}', 12)
            if sid in (69, 94, 95):
                assert core.ram[P1_INVUL] > 0, sid
            if sid == 45:
                core.step(6)
            core.buttons[0] = set()
            wait(core, lambda: core.ram[P1_STATE] == 0, f'CJ mobility recovery {sid}', 90)
            dx = sign * (core.word(P1_X) - x0)
            if direction:
                assert dx * direction >= 8 << 8, (sid, dx)
            else:
                assert abs(dx) <= 2 << 8, (sid, dx)
            assert core.ram[P1_INVUL] == 0, sid


def projectile_starts(core, frames=120):
    count = 0
    last = (False, False)
    for _ in range(frames):
        core.step()
        active = tuple(bool(core.word(slot + 4) and core.ram[slot + 15] & 0x80)
                       for slot in (SPARKS, SPARKS + 20))
        count += sum(a and not b for a, b in zip(active, last))
        last = active
    return count


def check_helper_scale(rom):
    # Test the linked clip, not just the source scale knob: the old compiler
    # reduced the ally again when all four poses exceeded one OBJ page.
    sym = rom.with_suffix('.sym')
    if not sym.is_file():
        return
    data = rom.read_bytes()
    symbols = {}
    for line in sym.read_text().splitlines():
        m = re.fullmatch(r'(?:00)?([\da-fA-F]{2}):?([\da-fA-F]{4})\s+(cjProjFx2F\d+)',
                         line.strip())
        if m:
            bank, addr = (int(m[i], 16) for i in (1, 2))
            rom_bank = bank - (0xC0 if bank >= 0xC0 else bank & 0x80)
            symbols[m[3]] = (rom_bank << 16) | addr
    assert len(symbols) >= 3, 'missing linked CJ helper poses'
    for offset in symbols.values():
        count = data[offset + 1]
        dy = [y if y < 128 else y - 256
              for y in data[offset + 6:offset + 6 + 4 * count:4]]
        assert 1 <= count <= 16 and max(dy) - min(dy) >= 48, (count, dy)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'kof98-snes.sfc')
    args = parser.parse_args()
    check_helper_scale(args.rom)
    roster = parse_tables()
    ids = {row['name']: i for i, row in roster.items()}
    cj, john = ids['cj'], ids['john']
    assert roster[cj]['cell'] == roster[john]['cell']
    text = (ROOT / 'build/gen_fight/newchars_tabs.inc').read_text()
    cpu = re.search(r'^CpuPool:\s*\.db ([\d,]+)((?:\n\s+\.db [\d,]+)*)', text, re.M)
    assert cj in [int(n) for line in cpu[0].splitlines()
                  for n in line.split('.db')[1].strip().split(',')]
    hidden = re.search(r'^HiddenTab:\s*\.db ([\d,]+)', text, re.M)
    assert hidden[1].split(',')[cj] == '0'
    qcb = QCB2[:3]
    core = Core(CORE, args.rom)
    try:
        select = boot_select(core)
        for held, want in ((set(), john), ({10}, john), ({11}, john), ({10, 11}, cj)):
            core.load(select)
            core.buttons = [set(), set()]
            core.ram[0xF052] = roster[john]['cell']
            core.step(8)
            core.buttons[0] = held | {A}
            core.step(8)
            assert core.ram[0x108E] == 1 and core.ram[0x1085] == want, (held, want)
        enter_fight(core, select, 'cj', 'kyo')
        assert core.word(GS) == 1 and core.ram[0x1085] == cj
        core.put(P1_X, 90 << 8)
        core.put(P2_X, 172 << 8)
        core.step(8)
        ready = core.save()
        check_mobility(core, ready)
        for seq, buttons, sid in (
            (QCF, {Y}, 48), (qcb, {Y}, 49), (QCF, {B}, 50), (qcb, {B}, 51),
            (QCF, {Y, X}, 52), (qcb, {Y, X}, 53), (QCF, {B, A}, 54),
            (qcb, {B, A}, 55), (QCF2, {Y}, 85), (QCF2, {B}, 86),
            (QCB2, {Y}, 87), (QCB2, {B}, 88),
        ):
            core.load(ready)
            core.buttons = [set(), set()]
            core.put(P1_POWER, 3000)
            core.put(P1_HP, 100)
            motion(core, seq, buttons)
            assert core.ram[P1_STATE] == sid, (sid, core.ram[P1_STATE])
            if sid in (52, 53):
                assert projectile_starts(core) >= (2 if sid == 52 else 1), sid
            if sid == 49:
                wait(core, lambda: core.ram[P1_STATE] == 118, 'CJ riding BMX', 90)
            core.step(350)
            assert core.word(GS) == 1 and core.ram[P1_STATE] == 0, sid
            if sid == 55:
                assert core.word(P1_HP) == 150
    finally:
        core.close()
    core = Core(CORE, args.rom)
    try:
        # Enter Survivor from the real menu and inspect its shuffled list.
        boot_select(core, item=4)
        core.buttons[0] = {A}
        core.step(8)
        core.buttons[0] = set()
        wait(core, lambda: core.word(GS) in (1, 4), 'survivor fight')
        count = core.ram[0x4F3C]
        assert cj in core.ram[0x4F00:0x4F00 + count]
    finally:
        core.close()
    print('PASS CJ: selection, CPU pools, Survivor, dodges, dashes, specials and supers')


if __name__ == '__main__':
    main()
