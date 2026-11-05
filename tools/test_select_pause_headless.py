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


def pause_cells(core):
    base = core.ram[SELPZ_OAM]
    return [core.ram[OAMBUF + base + i * 4 + 2] for i in range(5)]


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        open_select(core)
        before = core.word(FRAME)

        tap(core, START)
        assert core.ram[PZ_ON] == 1, "START did not open the select pause"
        assert core.ram[PZ_SEL] == 0, "cursor did not start on CONTINUE"
        assert core.ram[GS] == 5, "select screen left while pausing"
        assert pause_cells(core) == PAUSE_TILES, (
            f"pause title cells {pause_cells(core)}")
        print("PASS select pause: START opens CONTINUE/EXIT")

        tap(core, DOWN)
        assert core.ram[PZ_ON] == 1 and core.ram[PZ_SEL] == 1, "DOWN failed"
        tap(core, UP)
        assert core.ram[PZ_ON] == 1 and core.ram[PZ_SEL] == 0, "UP failed"
        print("PASS select pause: UP/DOWN moves the cursor")

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
