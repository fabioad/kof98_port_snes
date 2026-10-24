#!/usr/bin/env python3
"""Headless regression: the title attract demo ends when a fighter wins.

Boots the release ROM in Snes9x, skips the opening with START, forces the
title idle deadline and checks the CPU-vs-CPU bout.  Cases:

* with the release .msu present, streamed fighters are eligible;
* in a temp directory without the .msu, only RomFlags=1 (ROM) fighters are
  picked, so the demo never streams tiles from a missing data file;
* START or A on either pad leaves the bout immediately for PRESS START.

After a winner the KO fall plays and the demo cuts to the opening intro, just
like the 30 s deadline.  A draw still rerolls the pair/stage without resetting
the clock.  The 30 s clock is forced from the engine's own idle counter, so the
test does not wait 22 real seconds before the demo starts.
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from calibration.headless import Core

START = 3
GS = 0x1020
SEL1, SEL2 = 0x1085, 0x1086
CPU1, CPU2 = 0x1090, 0x1091
G_MODE = 0x10C0
MSUOK = 0x107A
DM_TICK, DM_ON = 0xF068, 0xF06A
S_WAIT = 0xF074
HP1, HP2 = 0x4010, 0x4050
X1, X2 = 0x4000, 0x4040
ROUNDWIN = 0x1083
ROM_IDS = {0, 1, 2, 12, 13, 15}       # kyo, iori, shingo, benimaru,
                                      # daimon, terry (CHR in the ROM)


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(12)


def reach_title(core):
    for _ in range(5000):
        if core.word(GS) == 7:       # opening intro
            break
        core.step()
    else:
        raise AssertionError(f'opening intro never appeared: gs={core.word(GS)}')
    tap(core, START)
    for _ in range(900):
        if core.word(GS) == 0:
            break
        core.step()
    else:
        raise AssertionError(f'title never appeared: gs={core.word(GS)}')
    core.step(30)                    # let the title song/load settle
    assert core.ram[DM_ON] == 0, 'attract demo flag set on the title'


def start_demo(core):
    core.buttons = [set(), set()]
    core.put(S_WAIT, 1329)           # next TitleTickNew reaches the deadline
    for _ in range(900):
        if core.ram[DM_ON] == 1 and core.word(GS) in (1, 4):
            return
        core.step()
    raise AssertionError(
        f'demo never started: gs={core.word(GS)} dm_on={core.ram[DM_ON]}')


def wait_live(core):
    for _ in range(900):
        if core.word(GS) == 1:
            return
        core.step()
    raise AssertionError(f'demo round never went live: gs={core.word(GS)}')


def run_case(core_path, rom, expect_msu):
    core = Core(core_path, rom)
    try:
        reach_title(core)
        assert core.ram[MSUOK] == expect_msu, \
            f'msuok={core.ram[MSUOK]} expected {expect_msu}'
        start_demo(core)
        assert core.word(G_MODE) == 0, 'demo must use free-versus staging'
        assert core.ram[CPU1] == 1 and core.ram[CPU2] == 1, \
            'both demo sides must be CPU-driven'
        if not expect_msu:
            assert core.ram[SEL1] in ROM_IDS, \
                f'P1 picked MSU-only char {core.ram[SEL1]} without MSU'
            assert core.ram[SEL2] in ROM_IDS, \
                f'P2 picked MSU-only char {core.ram[SEL2]} without MSU'
        first_tick = core.word(DM_TICK)
        first_pair = (core.ram[SEL1], core.ram[SEL2])

        wait_live(core)
        x1, x2 = core.word(X1), core.word(X2)
        moved = False
        for _ in range(240):
            # Keep both fighters alive: a natural KO during the motion check
            # would mask the draw/winner transitions below.
            core.put(HP1, 1000)
            core.put(HP2, 1000)
            core.step()
            if (core.word(X1), core.word(X2)) != (x1, x2):
                moved = True
        assert moved, 'CPU sides never moved'
        assert core.word(GS) == 1, \
            f'demo left the fight unexpectedly: gs={core.word(GS)}'

        # A draw must still reroll fighters/stage without resetting the clock.
        core.put(HP1, 0)
        core.put(HP2, 0)
        for _ in range(60):
            if core.word(GS) == 2:
                break
            core.step()
        assert core.word(GS) == 2, 'forced double KO did not enter KoTick'
        assert core.ram[ROUNDWIN] == 0, \
            f'double KO must be a draw, roundwin={core.ram[ROUNDWIN]}'
        ko_tick = core.word(DM_TICK)
        assert ko_tick <= first_tick, 'demo clock reset during the KO'
        for _ in range(360):
            if core.word(GS) == 4:
                break
            core.step()
        assert core.word(GS) == 4, 'demo did not reroll after a draw'
        assert core.ram[DM_ON] == 1, 'demo flag lost on reroll'
        assert core.word(DM_TICK) <= ko_tick, 'reroll reset the 30 s clock'
        new_pair = (core.ram[SEL1], core.ram[SEL2])
        if not expect_msu:
            assert new_pair[0] in ROM_IDS and new_pair[1] in ROM_IDS

        # With MSU present, the pool includes streamed fighters; two random
        # pairs are enough to prove the demo is not stuck on the ROM subset.
        if expect_msu:
            assert (first_pair[0] not in ROM_IDS or
                    first_pair[1] not in ROM_IDS or
                    new_pair[0] not in ROM_IDS or
                    new_pair[1] not in ROM_IDS), \
                f'MSU pool never used a streamed fighter: {first_pair} {new_pair}'

        # A decided bout must let the KO fall play and then cut to the intro.
        wait_live(core)
        core.put(HP1, 0)
        core.put(HP2, 1000)
        for _ in range(60):
            if core.word(GS) == 2:
                break
            core.step()
        assert core.word(GS) == 2, 'forced KO did not enter KoTick'
        assert core.ram[ROUNDWIN] == 2, \
            f'P2 must win the forced KO, roundwin={core.ram[ROUNDWIN]}'
        for _ in range(360):
            if core.word(GS) == 7:
                break
            core.step()
        assert core.word(GS) == 7, 'demo did not cut to the intro after a win'
        assert core.ram[DM_ON] == 0, 'demo flag not cleared after a win'

        # The original deadline still cuts to the opening intro.  Leave the
        # intro for the title and force the clock down on a fresh demo.
        tap(core, START)
        for _ in range(900):
            if core.word(GS) == 0:
                break
            core.step()
        assert core.word(GS) == 0, 'intro did not return to the title'
        core.step(30)
        start_demo(core)
        core.put(DM_TICK, 1)
        for _ in range(300):
            if core.word(GS) == 7:
                break
            core.step()
        assert core.word(GS) == 7, 'demo did not cut to the opening intro'
        assert core.ram[DM_ON] == 0, 'demo flag not cleared at the cut'
        return first_pair
    finally:
        core.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core',
                        default='/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so')
    parser.add_argument('--rom', type=Path, default=ROOT / 'kof98-snes.sfc')
    args = parser.parse_args()
    rom = args.rom.resolve()
    if not rom.exists():
        parser.error(f'ROM not found: {rom}')

    print('case: MSU available', flush=True)
    pair = run_case(args.core, str(rom), True)
    print('PASS attract demo with MSU (first pair %s)' % (pair,), flush=True)

    # START or A on either pad leaves the bout immediately for PRESS START;
    # the AI's own synthetic A presses must not trigger it.
    core = Core(args.core, str(rom))
    try:
        reach_title(core)
        start_demo(core)
        for _ in range(240):
            core.step()
        assert core.ram[DM_ON] == 1 and core.word(GS) in (1, 2, 4), \
            'demo ended without real input'
        tap(core, 8, 0)                   # A, pad 1
        for _ in range(900):
            if core.word(GS) == 0:
                break
            core.step()
        assert core.word(GS) == 0 and core.ram[DM_ON] == 0, \
            'A did not return to PRESS START'
        start_demo(core)
        tap(core, START, 1)               # START, pad 2
        for _ in range(900):
            if core.word(GS) == 0:
                break
            core.step()
        assert core.word(GS) == 0 and core.ram[DM_ON] == 0, \
            'START did not return to PRESS START'
        print('PASS attract demo skip via START/A', flush=True)
    finally:
        core.close()

    # No .msu next to the ROM: Snes9x must leave msuok=0 and the demo must
    # only pick ROM-resident fighters.
    with tempfile.TemporaryDirectory(prefix='kof98-nomsu-') as tmp:
        bare = Path(tmp) / rom.name
        shutil.copyfile(rom, bare)
        print('case: MSU absent', flush=True)
        run_case(args.core, str(bare), False)
        print('PASS attract demo without MSU', flush=True)


if __name__ == '__main__':
    main()
