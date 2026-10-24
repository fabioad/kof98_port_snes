#!/usr/bin/env python3
"""Campaign defeat must enter its own gamestate and expose a movable cursor.

The YOU LOSE menu used to reuse gamestate 6, which MainLoop dispatches to the
mode menu (MenuTick).  YouLoseTick was unreachable, so the defeat screen sat
frozen: D-pad/confirm did nothing and the selection cursor never moved.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
GS = 0x1020
FRAME = 0x1024
M_ITEM = 0xF070
SEL1 = 0x1085
SEL2 = 0x1086
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
WINS1 = 0x1080
WINS2 = 0x1081
HUDMAP = 0x4700
YL_SEL = 0x4FBA
GS_YOULOSE = 12

CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:!?'-/+>"
CUR_TILE = CHARSET.index(">")
ATT_YEL = 0x34

START = 3
UP = 4
DOWN = 5
A = 8


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def press(core, button, port=0):
    core.buttons[port] = {button}
    core.step(10)
    core.buttons[port] = set()
    core.step(20)


def wait(core, predicate, label, limit=12000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.ram[GS]} frame={core.ram[FRAME]}")


def cell(core, row, col):
    ofs = HUDMAP + (row * 32 + col) * 2
    return core.ram[ofs], core.ram[ofs + 1]


def lose_campaign_fight(core):
    """Start SINGLE PLAY, lock the pair and fake a 0-2 campaign defeat."""
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, START)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    core.ram[M_ITEM] = 0
    tap(core, START)
    wait(core, lambda: core.ram[GS] == 5, "select")
    core.ram[SEL1] = 0
    core.ram[SEL2] = 1
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.ram[CPU1] = 0
    core.ram[CPU2] = 1
    wait(core, lambda: core.ram[GS] == 1, "fight")
    core.step(60)
    core.ram[WINS1] = 0
    core.ram[WINS2] = 2
    core.put(0x4000 + 16, 0)              # P1 HP -> 0
    wait(core, lambda: core.ram[GS] == GS_YOULOSE, "YOU LOSE")
    core.step(120)


def test_youlose_cursor_and_navigation():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        lose_campaign_fight(core)
        assert core.ram[GS] == GS_YOULOSE
        assert core.ram[YL_SEL] == 0
        # One 8x8 cursor on the selected row, two cells left of the text.
        assert cell(core, 12, 10) == (CUR_TILE, ATT_YEL), cell(core, 12, 10)
        assert cell(core, 14, 7)[0] == 0
        assert cell(core, 16, 12)[0] == 0

        press(core, DOWN)
        assert core.ram[YL_SEL] == 1, core.ram[YL_SEL]
        assert cell(core, 14, 7) == (CUR_TILE, ATT_YEL), cell(core, 14, 7)
        assert cell(core, 12, 10)[0] == 0

        press(core, DOWN)
        assert core.ram[YL_SEL] == 2, core.ram[YL_SEL]
        assert cell(core, 16, 12) == (CUR_TILE, ATT_YEL), cell(core, 16, 12)
        assert cell(core, 14, 7)[0] == 0

        press(core, UP)
        assert core.ram[YL_SEL] == 1

        # Confirm the highlighted option; SELECT FIGHTER reopens gs 5.
        press(core, A)
        wait(core, lambda: core.ram[GS] == 5, "select fighter")
        print("PASS YOU LOSE: movable cursor + SELECT FIGHTER")
    finally:
        core.close()


if __name__ == "__main__":
    test_youlose_cursor_and_navigation()
