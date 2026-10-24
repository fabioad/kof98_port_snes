#!/usr/bin/env python3
"""Headless regression for the mid-fight START join.

While a Single Play / Team Play fight is running, START on the pad of the
CPU-driven side opens the character select.  The side already fighting keeps
its current character (single) or trio (team) and waits locked; the newcomer
picks, then the confrontation restarts with full health.

Run after a PVSnesLib build:

    python3 tools/test_midfight_join_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from capture_pair_headless import tap, wait              # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
SEL1, SEL2 = 0x1085, 0x1086
LOCK1, LOCK2 = 0x108E, 0x108F
CPU1, CPU2 = 0x1090, 0x1091
JOIN_ACTIVE, JOIN_SIDE = 0x4FB2, 0x4FB3
G_MODE, C_PVP = 0x10C0, 0x10C2
T_STEP, T_I1, T_I2, T_N2 = 0x10C7, 0x10C8, 0x10C9, 0x10CA
T_TEAM1, T_TEAM2, T_PICK_SIDE = 0x10CB, 0x10CE, 0x10D2
C_HUMAN_SIDE = 0x10EA
MSUOK = 0x107A
S_MODE = 0xF070
SCUR1, SCUR2 = 0xF052, 0xF053
FP1, FP2, F_HP = 0x4000, 0x4040, 16

# src/gen_menu/seldata.inc: SelChrCell[0..2]
SEL_CHR_CELL = [3, 6, 36]


def press(core, port, button, frames=3):
    core.buttons[port] = {button}
    core.step(frames)
    core.buttons[port] = set()
    core.step(2)


def enter_mode(core, mode):
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    assert core.ram[GS] == 6, f"mode menu not reached: gs={core.ram[GS]}"
    core.ram[S_MODE] = mode
    for _ in range(30):
        tap(core, 3)
        for _ in range(20):
            if core.ram[GS] == 5:
                break
            core.step()
        if core.ram[GS] == 5:
            break
    wait(core, lambda: core.ram[GS] == 5, "character select")


def start_single(core):
    enter_mode(core, 0)
    core.ram[SEL1] = 0
    core.ram[SEL2] = 1
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.step()
    wait(core, lambda: core.ram[GS] == 1, "single fight", 3600)
    core.buttons = [set(), set()]
    core.step(30)


def start_team(core):
    enter_mode(core, 2)
    core.ram[T_TEAM1] = 0
    core.ram[T_TEAM1 + 1] = 1
    core.ram[T_STEP] = 2
    core.ram[T_PICK_SIDE] = 0
    core.ram[SCUR1] = SEL_CHR_CELL[2]
    core.ram[CPU1] = 0
    press(core, 0, 8)
    wait(core, lambda: core.ram[GS] == 1, "team fight", 3600)
    core.buttons = [set(), set()]
    core.step(30)


def open_join(core, side):
    press(core, side, 3)
    wait(core, lambda: core.ram[GS] == 5, "join select", 300)
    assert core.ram[JOIN_ACTIVE] == 1, "join flag not set"
    assert core.ram[JOIN_SIDE] == side, "wrong joining side"
    assert core.ram[LOCK1] == (1 if side else 0), "waiting side not locked"
    assert core.ram[LOCK2] == (0 if side else 1), "joiner should be free"
    assert core.ram[CPU1] == 0 and core.ram[CPU2] == 0, "joining pad stays CPU"


def test_single(core, side):
    start_single(core)
    # Simulate the campaign side that is under CPU control.
    core.ram[CPU1] = 1 if side == 0 else 0
    core.ram[CPU2] = 1 if side == 1 else 0
    core.step(2)
    wait_sel = core.ram[SEL2] if side == 0 else core.ram[SEL1]
    open_join(core, side)

    core.ram[SCUR1 if side == 0 else SCUR2] = SEL_CHR_CELL[2]
    press(core, side, 8)
    wait(core, lambda: core.ram[GS] == 1, "joined single fight", 3600)
    core.step(20)

    assert core.ram[JOIN_ACTIVE] == 0
    assert core.ram[CPU1] == 0 and core.ram[CPU2] == 0
    assert core.ram[C_PVP] == 1
    assert core.ram[C_HUMAN_SIDE] == (1 - side)
    assert (core.ram[SEL2] if side == 0 else core.ram[SEL1]) == wait_sel
    assert (core.ram[SEL1] if side == 0 else core.ram[SEL2]) == 2
    assert core.word(FP1 + F_HP) == 200 and core.word(FP2 + F_HP) == 200
    print(f"PASS single P{side + 1} join")


def test_team(core, side):
    start_team(core)
    old1 = [core.ram[T_TEAM1 + i] for i in range(3)]
    old2 = [core.ram[T_TEAM2 + i] for i in range(3)]
    core.ram[CPU1] = 1 if side == 0 else 0
    core.ram[CPU2] = 1 if side == 1 else 0
    core.step(2)
    open_join(core, side)

    picks = (2, 0, 1)
    for char in picks:
        core.ram[SCUR1 if side == 0 else SCUR2] = SEL_CHR_CELL[char]
        press(core, side, 8)
        core.step(4)
    wait(core, lambda: core.ram[GS] == 1, "joined team fight", 3600)
    core.step(20)

    assert core.ram[JOIN_ACTIVE] == 0
    assert core.ram[CPU1] == 0 and core.ram[CPU2] == 0
    assert core.ram[C_PVP] == 1
    assert core.ram[C_HUMAN_SIDE] == (1 - side)
    assert core.ram[T_N2] == 3
    assert core.ram[T_I1] == 0 and core.ram[T_I2] == 0
    waiting = old2 if side == 0 else old1
    joined = [core.ram[T_TEAM1 + i] if side == 0 else core.ram[T_TEAM2 + i]
              for i in range(3)]
    assert joined == list(picks)
    if side == 1:
        assert [core.ram[T_TEAM1 + i] for i in range(3)] == old1
    else:
        assert [core.ram[T_TEAM2 + i] for i in range(3)] == waiting
    assert core.word(FP1 + F_HP) == 200 and core.word(FP2 + F_HP) == 200
    print(f"PASS team P{side + 1} join")


def run(rom, core_path, fn, side):
    core = Core(core_path, rom)
    try:
        fn(core, side)
    finally:
        core.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()

    for side in (1, 0):
        run(args.rom, args.core, test_single, side)

    probe = Core(args.core, args.rom)
    try:
        for _ in range(80):
            if probe.ram[GS] == 6:
                break
            tap(probe, 3)
        has_msu = probe.ram[MSUOK] != 0
    finally:
        probe.close()
    if not has_msu:
        print("SKIP team joins: MSU-1 data file not found")
        return

    for side in (1, 0):
        run(args.rom, args.core, test_team, side)


if __name__ == "__main__":
    main()
