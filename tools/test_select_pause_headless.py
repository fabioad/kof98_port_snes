#!/usr/bin/env python3
"""Headless regression for the character-select pause menu.

START on a human pad opens a two-item CONTINUE / EXIT overlay.  CONTINUE
(or B) returns to the select screen; EXIT goes to the title.  START on a
CPU-driven pad still reclaims/joins that side (covered by
test_menu_p2_start_headless).

Run after a PVSnesLib build:

    python3 tools/test_select_pause_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select       # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
FRAME = 0x1024
CPU1, CPU2 = 0x1090, 0x1091
PZ_ON, PZ_SEL = 0x4FB0, 0x4FB1
SELPZ_OAM = 0x4FBE
OAMBUF = 0x1800

START, UP, DOWN = 3, 4, 5
PAUSE_TILES = [16, 1, 21, 19, 5]          # CHARSET indices for PAUSE
PAL_WHITE, PAL_YELLOW = 0x30, 0x32
CURSOR_TILE = 45                         # CHARSET '>'


def tap(core, button, frames=3):
    core.buttons[0] = {button}
    core.step(frames)
    core.buttons[0] = set()
    core.step(5)


def open_select(core):
    core.load(boot_select(core))
    core.ram[CPU1] = 0
    core.ram[CPU2] = 0
    core.step(10)
    assert core.ram[GS] == 5, core.ram[GS]


def pause_sprite(core, i):
    base = core.ram[SELPZ_OAM] + i * 4
    return (core.ram[OAMBUF + base], core.ram[OAMBUF + base + 1],
            core.ram[OAMBUF + base + 2], core.ram[OAMBUF + base + 3])


def check_pause_layout(core, selected):
    """Texts are horizontally/vertically centred and the selection is yellow."""
    title = [pause_sprite(core, i) for i in range(0, 5)]
    assert [s[2] for s in title] == PAUSE_TILES, (
        f"pause title cells {[s[2] for s in title]}")
    assert [(s[0], s[1]) for s in title] == [
        (108 + i * 8, 84) for i in range(5)], "PAUSE is not centred"
    assert all(s[3] == PAL_WHITE for s in title), "PAUSE should be white"

    cont = [pause_sprite(core, i) for i in range(5, 13)]
    assert [(s[0], s[1]) for s in cont] == [
        (96 + i * 8, 112) for i in range(8)], "CONTINUE is not centred"
    exit_ = [pause_sprite(core, i) for i in range(13, 17)]
    assert [(s[0], s[1]) for s in exit_] == [
        (112 + i * 8, 132) for i in range(4)], "EXIT is not centred"

    cont_pal = PAL_YELLOW if selected == 0 else PAL_WHITE
    exit_pal = PAL_YELLOW if selected == 1 else PAL_WHITE
    assert all(s[3] == cont_pal for s in cont), (
        "CONTINUE palette should be "
        f"{'yellow' if selected == 0 else 'white'}")
    assert all(s[3] == exit_pal for s in exit_), (
        "EXIT palette should be "
        f"{'yellow' if selected == 1 else 'white'}")

    cur = pause_sprite(core, 17)
    want_x = 80 if selected == 0 else 96
    want_y = 112 if selected == 0 else 132
    assert cur == (want_x, want_y, CURSOR_TILE, PAL_YELLOW), (
        f"yellow selector at {cur}, want {(want_x, want_y, CURSOR_TILE, PAL_YELLOW)}")


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        open_select(core)
        before = core.word(FRAME)

        tap(core, START)
        assert core.ram[PZ_ON] == 1, "START did not open the select pause"
        assert core.ram[PZ_SEL] == 0, "cursor did not start on CONTINUE"
        assert core.ram[GS] == 5, "select screen left while pausing"
        check_pause_layout(core, selected=0)
        print("PASS select pause: START opens a centred, yellow-selected menu")

        tap(core, DOWN)
        assert core.ram[PZ_ON] == 1 and core.ram[PZ_SEL] == 1, "DOWN failed"
        check_pause_layout(core, selected=1)
        tap(core, UP)
        assert core.ram[PZ_ON] == 1 and core.ram[PZ_SEL] == 0, "UP failed"
        check_pause_layout(core, selected=0)
        print("PASS select pause: UP/DOWN moves the yellow selector")

        tap(core, START)
        assert core.ram[PZ_ON] == 0, "CONTINUE did not close the pause"
        assert core.ram[GS] == 5, "CONTINUE left the select screen"
        assert core.word(FRAME) > before, "select tick stopped after CONTINUE"
        print("PASS select pause: CONTINUE returns to select")

        tap(core, START)
        assert core.ram[PZ_ON] == 1, "pause did not reopen"
        tap(core, DOWN)
        assert core.ram[PZ_SEL] == 1, "EXIT was not selected"
        tap(core, START)
        assert core.ram[PZ_ON] == 0, "EXIT left the pause flag set"
        assert core.ram[GS] == 0, f"EXIT did not reach the title (gs={core.ram[GS]})"
        print("PASS select pause: EXIT returns to the title")
    finally:
        core.close()
    print("PASS select pause menu")


if __name__ == "__main__":
    main()
