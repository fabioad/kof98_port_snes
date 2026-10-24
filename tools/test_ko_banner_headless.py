#!/usr/bin/env python3
"""Headless regression for the K.O. banner overrun.

The 6x2 K.O. logo used to be written with a 16-bit row-counter decrement:
the stale high byte of the scratch word turned it into hundreds of rows,
scribbling HUD tiles down (and past) the BG3 map.  On screen that showed up
as a garbled vertical column over the falling loser and stalled the KO
sequence.  This checks that only rows 9-10 change and that KoTick advances.

Run after a PVSnesLib build:

    python3 tools/test_ko_banner_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_roster import parse_tables                     # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
GS, FP, FP2 = 0x1020, 0x4000, 0x40
F_STATE, F_Y, F_HP = 8, 2, 16
KOTIMER, FRAMECNT, HUDMAP = 0x1028, 0x1024, 0x4700
START, A, X = 3, 8, 9


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def wait(core, pred, label, limit=8000):
    for _ in range(limit):
        if pred():
            return
        core.step()
    raise AssertionError(f"{label}: gs={core.word(GS)}")


def boot_select(core):
    wait(core, lambda: core.word(GS) == 7, "opening")
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(60)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    core.ram[0xF070] = 1
    tap(core, START)
    wait(core, lambda: core.word(GS) == 5, "select")
    core.ram[0x1091] = 0
    core.step(10)
    return core.save()


def enter_fight(core, select_state, p1, p2):
    roster = {v["name"]: v for v in parse_tables().values()}
    core.load(select_state)
    core.buttons = [set(), set()]
    core.step(4)
    for side, char, lock in ((0, p1, 0x108E), (1, p2, 0x108F)):
        core.ram[0xF052 + side] = roster[char]["cell"]
        for _ in range(10):
            core.step(4)
            tap(core, A, side)
            if core.ram[lock] == 1:
                break
        else:
            raise AssertionError(f"side {side + 1} did not lock")
    tap(core, START)
    # The READY+GO announcer keeps gamestate 4 for ~113 frames after both
    # fighters stand; only then do inputs become live.
    wait(core, lambda: core.word(GS) == 1, "fight")
    wait(core, lambda: core.ram[FP + F_STATE] == 0 and
         core.ram[FP + FP2 + F_STATE] == 0, "idle")
    core.step(40)


def hud_row(core, row, col, width):
    return [core.ram[HUDMAP + (row * 32 + col + i) * 2] |
            core.ram[HUDMAP + (row * 32 + col + i) * 2 + 1] << 8
            for i in range(width)]


def main(core_path=CORE, rom=ROM):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "yuri", "kyo")
        core.put(FP, 70 << 8)
        core.put(FP + FP2, 110 << 8)
        core.put(FP + F_HP, 200)
        core.put(FP + FP2 + F_HP, 1)
        core.step(20)
        core.buttons[0] = {X}                     # standing strong punch
        core.step(3)
        core.buttons[0] = set()
        wait(core, lambda: core.word(GS) == 2, "KO")
        assert core.word(FP + FP2 + F_HP) == 0
        # K.O. logo = 6x2 cells at row 9, col 13 (tiles 140-151).
        assert hud_row(core, 9, 13, 6) == [0x348C + i for i in range(6)], \
            hud_row(core, 9, 13, 6)
        assert hud_row(core, 10, 13, 6) == [0x3492 + i for i in range(6)], \
            hud_row(core, 10, 13, 6)
        # Nothing may spill outside the declared block.
        for row in (8, 11, 12, 13, 14, 15, 16, 17, 18, 19):
            assert hud_row(core, row, 13, 6) == [0, 0, 0, 0, 0, 0], \
                f"row {row} spilled: {hud_row(core, row, 13, 6)}"
        # KoTick must run immediately, not stall for hundreds of frames.
        start = core.ram[KOTIMER]
        frame0 = core.word(FRAMECNT)
        core.step(30)
        assert core.ram[KOTIMER] < start, "KoTick did not advance"
        assert core.word(FRAMECNT) != frame0, "main loop stalled"
        # The loser falls, lands and stays down without leaving S_DOWN.
        wait(core, lambda: core.word(FP + FP2 + F_Y) == 0, "landing",
             limit=400)
        for _ in range(60):
            core.step()
        assert core.ram[FP + FP2 + F_STATE] == 10
        assert core.word(FP + FP2 + F_Y) == 0
        print("K.O. banner: 6x2 only, KoTick advances, loser lands cleanly")
    finally:
        core.close()


if __name__ == "__main__":
    main()
