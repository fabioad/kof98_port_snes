#!/usr/bin/env python3
"""In-fight SELECT/START swap regression.

During a fight, SELECT now emits the taunt command (`s` token) and START
opens the pause menu, on both pads.  Other buttons and the menus outside
the fight are untouched.

Run after a PVSnesLib build:

    python3 tools/test_fight_select_start_swap_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE1, F_STATE2 = FP1 + 8, FP2 + 8
CPU1, CPU2 = 0x1090, 0x1091
PZ_ON = 0x4FB0                      # CL_VARS($4F40) + $70
SELECT, START = 2, 3
TAUNT = 47


def wait_state(core, addr, value, limit=240):
    for _ in range(limit):
        if core.ram[addr] == value:
            return True
        core.step()
    return core.ram[addr] == value


def tap_pad(core, port, button, frames=3):
    core.buttons[port] = {button}
    core.step(frames)
    core.buttons[port] = set()
    core.step(2)


def check_pad(core, port, state_addr):
    # SELECT -> taunt, not pause.
    tap_pad(core, port, SELECT)
    assert core.ram[PZ_ON] == 0, f"P{port + 1} SELECT opened pause"
    assert wait_state(core, state_addr, TAUNT), (
        f"P{port + 1} SELECT did not taunt (state {core.ram[state_addr]})")
    assert core.ram[PZ_ON] == 0, f"P{port + 1} taunt opened pause"
    assert wait_state(core, state_addr, 0), (
        f"P{port + 1} taunt did not finish (state {core.ram[state_addr]})")

    # START -> pause, not taunt.
    tap_pad(core, port, START)
    assert core.ram[state_addr] != TAUNT, f"P{port + 1} START taunted"
    assert core.ram[PZ_ON] == 1, (
        f"P{port + 1} START did not open pause (PZ_ON={core.ram[PZ_ON]})")

    # START confirms the default CONTINUE entry.
    tap_pad(core, port, START)
    assert wait_state(core, PZ_ON, 0, 60), (
        f"P{port + 1} START did not close pause")
    wait_state(core, state_addr, 0)


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "mature", "kyo")
        # Both pads human so the command scanner runs on both sides.
        core.ram[CPU1] = 0
        core.ram[CPU2] = 0
        core.step(30)
        check_pad(core, 0, F_STATE1)
        check_pad(core, 1, F_STATE2)
        print("PASS in-fight SELECT=taunt / START=pause on both pads")
    finally:
        core.close()


if __name__ == "__main__":
    main()
