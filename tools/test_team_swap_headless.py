#!/usr/bin/env python3
"""Regression: team member swaps must not spawn glued/back-turned.

A losing member is replaced while the survivor keeps its position.  The
newcomer used to appear at the fixed home slot (80/176), so whenever the
survivor stood near that slot the two overlapped for the whole entrance
and the fixed facing could leave one fighter with its back to the other.
TeamSwap now keeps a full round-start gap and faces both toward each other.

Run after a PVSnesLib build:

    python3 tools/test_team_swap_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                       # noqa: E402
from capture_pair_headless import wait                      # noqa: E402
from test_midfight_join_headless import start_team, GS       # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
NEXTF = 0x1084
HP1, HP2 = 0x4010, 0x4050
X1, X2 = 0x4000, 0x4040
FAC1, FAC2 = 0x400E, 0x404E
CPU1, CPU2 = 0x1090, 0x1091
STAGE_L, STAGE_R = 24, 232
MIN_GAP = 96


def x(core, addr):
    return core.word(addr) / 256.0


def facing(core, addr):
    return 1 if (core.word(addr) & 0xFFFF) == 1 else -1


def check(core, label):
    x1, x2 = x(core, X1), x(core, X2)
    f1, f2 = facing(core, FAC1), facing(core, FAC2)
    assert STAGE_L <= x1 <= STAGE_R and STAGE_L <= x2 <= STAGE_R, (
        f"{label}: fighter outside the stage: {x1:.1f}/{x2:.1f}")
    assert abs(x1 - x2) >= MIN_GAP - 0.5, (
        f"{label}: newcomer glued to the survivor: {x1:.1f}/{x2:.1f}")
    if x1 < x2:
        assert f1 == 1 and f2 == -1, (
            f"{label}: not facing each other: {f1}/{f2} at {x1:.1f}/{x2:.1f}")
    else:
        assert f1 == -1 and f2 == 1, (
            f"{label}: not facing each other: {f1}/{f2} at {x1:.1f}/{x2:.1f}")


def run_case(core, p2_wins, survivor_x):
    start_team(core)
    core.ram[CPU1] = 0                         # keep the survivor still
    core.ram[CPU2] = 0
    if p2_wins:
        core.put(X1, 224 << 8)
        core.put(X2, int(survivor_x * 256))
    else:
        core.put(X1, int(survivor_x * 256))
        core.put(X2, 224 << 8)
    core.step(4)
    core.put(HP1 if p2_wins else HP2, 0)       # the other side is eliminated
    wait(core, lambda: core.word(GS) == 0 and core.ram[NEXTF] == 1,
         "team intermission", 3000)
    wait(core, lambda: core.word(GS) == 4, "member entrance", 3000)

    label = f"{'P2' if p2_wins else 'P1'} survivor at {survivor_x:.0f}"
    check(core, label)                         # first entrance frame
    for _ in range(30):
        core.step()
        check(core, label)
    wait(core, lambda: core.word(GS) == 1, "next fight", 3000)
    core.step()
    check(core, label)                         # facing survives the intro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()

    cases = [(False, 176), (False, 232), (False, 190),
             (True, 80), (True, 24), (True, 100)]
    for p2_wins, survivor_x in cases:
        core = Core(args.core, args.rom)
        try:
            run_case(core, p2_wins, survivor_x)
            print(f"PASS team swap, {'P2' if p2_wins else 'P1'} survivor "
                  f"at {survivor_x}")
        finally:
            core.close()
    print(f"{len(cases)} team swap cases passed")


if __name__ == "__main__":
    main()
