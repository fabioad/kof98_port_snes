#!/usr/bin/env python3
"""Exercise the PRACTICE command-list submenu through the real menu flow.

Checks:
  * SELECT -> pause -> COMMAND LIST opens the overlay; B/START returns to
    the pause menu;
  * the active character's list is rendered (name + command + category tag);
  * P1/P2 usage markers are tracked independently;
  * L/R switches sides, UP/DOWN scrolls the 12-row page;
  * the list keeps the fight frozen while it is open.
"""
import ctypes as C
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
GS = 0x1020
FRAME = 0x1024
RSECS = 0x1076
M_ITEM = 0xF070
MSUOK = 0x107A
G_MODE = 0x10C0
SEL1 = 0x1085
SEL2 = 0x1086
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
# PRACTICE command list state (see CL_VARS in fight.asm)
CL_OPEN = 0x4F40
CL_SIDE = 0x4F41
CL_SEL = 0x4F42
CL_TOP = 0x4F43
CL_COUNT = 0x4F44
CL_LAST1 = 0x4F45
CL_LAST2 = 0x4F46
CL_SEEN1 = 0x4F50
CL_SEEN2 = 0x4F80
# Pause menu state shares the tail of the command-list block.
PZ_ON = 0x4FB0
PZ_SEL = 0x4FB1
PZ_SIDE = 0x4FB5
RT_HUDFULL = 0x5100
HUDMAP = 0x4700
BG3MAP = 0x5000               # VRAM word address of the HUD tilemap
# CHARSET tiles used by the small HUD font (must match tools/build_fight.py).
CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:!?'-/+>,@\""
TXT_ATTR = 0x2C
CUR_TILE = CHARSET.index(">")
USED_TILE = CHARSET.index("+")

START = 3
UP = 4
DOWN = 5
LEFT = 6
RIGHT = 7
SELECT = 2
A = 8
B = 0                      # SNES B (MUGEN a/LK)
Y = 1                      # SNES Y (MUGEN x/LP)
SIDE_A = 0


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


def wait(core, predicate, label, limit=6000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.ram[GS]} frame={core.ram[FRAME]}")


def boot():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, START)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    return core


def start_practice(core, p2=1, cpu2=1):
    core.ram[MSUOK] = 0
    core.ram[M_ITEM] = 5
    for _ in range(30):
        tap(core, START)
        for _ in range(20):
            if core.ram[GS] == 5:
                break
            core.step()
        if core.ram[GS] == 5:
            break
    wait(core, lambda: core.ram[GS] == 5, "select")
    assert core.ram[G_MODE] == 5
    core.ram[SEL1] = 0
    core.ram[SEL2] = p2
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.ram[CPU1] = 0
    core.ram[CPU2] = cpu2
    wait(core, lambda: core.ram[GS] == 1, "practice fight")
    core.step(30)


def open_command_list(core):
    """SELECT -> pause -> DOWN to COMMAND LIST -> A."""
    press(core, SELECT)
    core.step(4)
    press(core, DOWN)
    press(core, A)
    wait(core, lambda: core.ram[CL_OPEN] == 1, "command list open")


def row_tiles(core, row, count=32):
    return [core.ram[HUDMAP + (row * 32 + i) * 2] for i in range(count)]


def row_attrs(core, row, count=32):
    return [core.ram[HUDMAP + (row * 32 + i) * 2 + 1]
            for i in range(count)]


def text(core, row, start, length):
    return "".join(CHARSET[b] for b in
                   row_tiles(core, row, 32)[start:start + length])


def vram_row(core, row):
    """BG3 tilemap row as actually uploaded to VRAM (not the HUD shadow)."""
    core.lib.retro_get_memory_data.restype = C.c_void_p
    vram = (C.c_ubyte * core.lib.retro_get_memory_size(3)).from_address(
        core.lib.retro_get_memory_data(3))
    base = BG3MAP * 2 + row * 64
    return [vram[base + i * 2] | (vram[base + i * 2 + 1] << 8)
            for i in range(32)]


def test_open_draw_and_close():
    core = boot()
    try:
        start_practice(core)
        assert core.ram[CL_OPEN] == 0
        open_command_list(core)
        assert core.ram[CL_OPEN] == 1
        assert core.ram[CL_SIDE] == 0
        assert core.ram[CL_SEL] == 0
        assert core.ram[CL_COUNT] > 12
        assert text(core, 7, 2, 12) == "COMMAND LIST"
        assert text(core, 7, 29, 2) == "P1"
        assert row_attrs(core, 7, 13)[2] == TXT_ATTR
        assert text(core, 8, 0, 3) == "NRM"
        assert text(core, 9, 2, 8) == "STAND LP"
        assert text(core, 9, 18, 1) == "Y"
        assert text(core, 9, 29, 3) == "NRM"
        # The physical pad remap: LP=Y, HP=X, LK=B, HK=A.
        assert text(core, 10, 2, 8) == "STAND HP"
        assert text(core, 10, 18, 1) == "X"
        assert text(core, 11, 2, 8) == "STAND LK"
        assert text(core, 11, 18, 1) == "B"
        assert text(core, 12, 2, 8) == "STAND HK"
        assert text(core, 12, 18, 1) == "A"
        assert text(core, 13, 18, 5) == "D + Y"
        assert text(core, 16, 18, 5) == "D + A"
        assert text(core, 17, 18, 7) == "AIR + Y"
        assert text(core, 20, 18, 7) == "AIR + A"
        assert text(core, 21, 1, 6) == "UP/DN "

        press(core, DOWN)
        assert core.ram[CL_SEL] == 1
        assert row_tiles(core, 9, 1)[0] == 0
        assert row_tiles(core, 10, 1)[0] == CUR_TILE

        press(core, RIGHT)
        assert core.ram[CL_SIDE] == 1
        assert text(core, 7, 29, 2) == "P2"
        press(core, LEFT)
        assert core.ram[CL_SIDE] == 0

        press(core, START)
        assert core.ram[CL_OPEN] == 0
        assert row_tiles(core, 7, 1)[0] == 0
        print("PASS command list: open, draw, navigate, close")
    finally:
        core.close()


def test_p1_p2_usage_markers():
    core = boot()
    try:
        start_practice(core, p2=1, cpu2=0)
        # P1: SNES B maps to MUGEN a -> sid 7 (Stand Light Kick).
        tap(core, B, 0)
        core.step(15)
        assert core.ram[CL_LAST1] == 7, core.ram[CL_LAST1]
        assert core.ram[CL_SEEN1 + 2] == 1
        # P2: same normal on pad 2.
        tap(core, B, 1)
        core.step(15)
        assert core.ram[CL_LAST2] == 7, core.ram[CL_LAST2]
        assert core.ram[CL_SEEN2 + 2] == 1

        open_command_list(core)
        # sid 7 is the third list row (screen row 11).
        assert row_tiles(core, 11, 1)[0] == USED_TILE
        press(core, RIGHT)
        assert core.ram[CL_SIDE] == 1
        assert row_tiles(core, 11, 1)[0] == USED_TILE
        # The cursor row is always highlighted even when unused.
        assert row_tiles(core, 9, 1)[0] == CUR_TILE
        print("PASS command list: P1/P2 usage markers")
    finally:
        core.close()


def test_scrolling_and_freeze():
    core = boot()
    try:
        start_practice(core)
        open_command_list(core)
        assert core.ram[CL_OPEN] == 1
        before_frame = core.ram[FRAME]
        before_secs = core.ram[RSECS]
        before_x = core.word(0x4000)
        core.step(20)
        # The renderer keeps running, but the fight does not advance.
        assert core.ram[FRAME] > before_frame
        assert core.ram[RSECS] == before_secs
        assert core.word(0x4000) == before_x

        for _ in range(14):
            press(core, DOWN)
        assert core.ram[CL_SEL] == 14, core.ram[CL_SEL]
        assert core.ram[CL_TOP] == 3, core.ram[CL_TOP]
        for _ in range(20):
            press(core, UP)
        assert core.ram[CL_SEL] == 0
        assert core.ram[CL_TOP] == 0
        print("PASS command list: scrolling and frozen fight")
    finally:
        core.close()


def test_close_with_b():
    core = boot()
    try:
        start_practice(core)
        open_command_list(core)
        assert core.ram[CL_OPEN] == 1
        press(core, B)
        assert core.ram[CL_OPEN] == 0
        print("PASS command list: B closes")
    finally:
        core.close()


def test_pause_either_pad_and_continue_clears_vram():
    core = boot()
    try:
        start_practice(core)
        for port, side in ((0, 0), (1, 1)):
            press(core, SELECT, port=port)
            core.step(4)
            assert core.ram[PZ_ON] == 1, port
            assert core.ram[PZ_SIDE] == side, port
            assert any(vram_row(core, 7)), "pause title is not in VRAM"
            # The pad that opened the pause owns the command-list side.
            press(core, DOWN, port=port)
            press(core, A, port=port)
            wait(core, lambda: core.ram[CL_OPEN] == 1, "command list")
            assert core.ram[CL_SIDE] == side, port
            press(core, B, port=port)      # back to the pause menu
            assert core.ram[CL_OPEN] == 0
            assert core.ram[PZ_ON] == 1
            # COMMAND LIST is selected on return; move up to CONTINUE.
            press(core, UP, port=port)
            assert core.ram[PZ_SEL] == 0
            # Confirm on the frame the menu closes: the cleared HUD must be
            # scheduled for a full VRAM upload, then the overlay rows vanish.
            core.buttons[port] = {A}
            for _ in range(8):
                core.step()
                if core.ram[PZ_ON] == 0:
                    break
            core.buttons[port] = set()
            assert core.ram[PZ_ON] == 0
            assert core.ram[RT_HUDFULL] == 1
            core.step(4)
            assert not any(vram_row(core, 7))
            assert not any(vram_row(core, 10))
        print("PASS pause: either pad opens, side list follows, CONTINUE "
              "clears the overlay from VRAM")
    finally:
        core.close()


def test_system_moves_show_shoulder_buttons():
    core = boot()
    try:
        start_practice(core)
        open_command_list(core)
        # Walk every row: blowback sits in the CMD category, the remaining
        # shoulder moves are at the end of the list.
        rows = {}
        for _ in range(core.ram[CL_COUNT]):
            row = 9 + core.ram[CL_SEL] - core.ram[CL_TOP]
            line = text(core, row, 0, 32)
            rows[line[2:18].strip()] = line[18:29].strip()
            press(core, DOWN)

        def command_for(label):
            return next(cmd for name, cmd in rows.items() if label in name)

        assert command_for("BLOWBACK") == "R", rows
        assert command_for("TAUNT") == "L+R", rows
        assert command_for("DODGE") == "L", rows
        assert command_for("ROLL BACK") == "L + BACK", rows
        assert command_for("ROLL FWD") == "L + FWD", rows
        print("PASS command list: L/R shoulder moves show physical buttons")
    finally:
        core.close()


if __name__ == "__main__":
    test_open_draw_and_close()
    test_p1_p2_usage_markers()
    test_scrolling_and_freeze()
    test_close_with_b()
    test_pause_either_pad_and_continue_clears_vram()
    test_system_moves_show_shoulder_buttons()
