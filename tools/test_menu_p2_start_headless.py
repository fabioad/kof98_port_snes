#!/usr/bin/env python3
"""Menu / select START ownership for the second player.

Pressing START on the P2 pad in the mode menu must open the select screen
with Pad2 live (not hand the only active cursor to P1).  Pressing START on
Pad2 while the select screen is showing must likewise take the CPU/P2 side
over.  The old code ORed both pads and always started P1.

Run after a PVSnesLib build:

    python3 tools/test_menu_p2_start_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from capture_pair_headless import tap, wait              # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
GS = 0x1020
CPU1, CPU2 = 0x1090, 0x1091
LOCK1, LOCK2 = 0x108E, 0x108F
SCUR1, SCUR2 = 0xF052, 0xF053
M_START_SIDE = 0x4FBA
START, RIGHT = 3, 7


def to_menu(core):
    for _ in range(120):
        if core.ram[GS] == 6:
            return
        tap(core, START)
    raise AssertionError(f"mode menu not reached: gs={core.ram[GS]}")


def start_menu(core, side):
    to_menu(core)
    core.buttons[side] = {START}
    core.step(4)
    core.buttons[side] = set()
    wait(core, lambda: core.ram[GS] == 5, "character select", 600)


def move_p2(core):
    core.ram[SCUR2] = 3
    core.step(4)
    before = core.ram[SCUR2]
    core.buttons[1] = {RIGHT}
    core.step(3)
    core.buttons[1] = set()
    core.step(4)
    assert core.ram[SCUR2] != before, (
        f"P2 cursor did not move ({before} -> {core.ram[SCUR2]})")


def main():
    core = Core(CORE, str(ROM))
    try:
        # P2 starts the mode: Pad2 is human and its own cursor is live.
        start_menu(core, 1)
        assert core.ram[M_START_SIDE] == 1
        assert core.ram[CPU1] == 0 and core.ram[CPU2] == 0, (
            f"P2 start left cpu1/cpu2={core.ram[CPU1]}/{core.ram[CPU2]}")
        assert core.ram[LOCK1] == 0 and core.ram[LOCK2] == 0
        move_p2(core)
        print("PASS P2 START in the menu opens a live Pad2 cursor")

        # P1 starts the menu; P2 START on the select screen must take over.
        core.close()
        core = Core(CORE, str(ROM))
        start_menu(core, 0)
        assert core.ram[M_START_SIDE] == 0
        assert core.ram[CPU2] == 1, "campaign should start with CPU P2"
        core.buttons[1] = {START}
        core.step(4)
        core.buttons[1] = set()
        core.step(10)
        assert core.ram[CPU2] == 0 and core.ram[LOCK2] == 0, (
            f"P2 START on select did not enable P2: cpu2={core.ram[CPU2]}")
        move_p2(core)
        print("PASS P2 START on the select screen enables the opponent pad")
    finally:
        core.close()
    print("PASS menu/select START ownership")


if __name__ == "__main__":
    main()
