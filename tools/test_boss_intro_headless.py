#!/usr/bin/env python3
"""Regression: Omega Rugal's entrance and final-boss hand-off.

Normal Rugal and Omega Rugal share the final confrontation.  In Single Play
the hand-off used to increment roundno, so Omega entered as round 2 and
StartFight skipped his intro.  It now starts a fresh round 1 (intro plays),
and a draw in the Omega fight still moves to round 2 without replaying it.

Team Play swaps Omega in through TeamSwap and Survival starts a new match,
so both must also show the entrance intro.

When Omega falls in Single Play or Team Play, the KO screen fades to black
and ending1 starts directly -- the "<name> WINS" banner is skipped.

Run after a PVSnesLib build:

    python3 tools/test_boss_intro_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from capture_pair_headless import tap, wait              # noqa: E402
from test_midfight_join_headless import start_team       # noqa: E402
from test_survivor_practice_headless import (            # noqa: E402
    boot as survivor_boot, lock_sides, open_select)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
NEXTF = 0x1084
ROUNDNO = 0x1082
FADELEVEL = 0x108D
E_SCR = 0xF078
SEL1, SEL2 = 0x1085, 0x1086
LOCK1, LOCK2 = 0x108E, 0x108F
CPU1, CPU2 = 0x1090, 0x1091
HP1, HP2 = 0x4010, 0x4050
F_STATE1, F_STATE2 = 0x4008, 0x4048
C_IDX = 0x10C1
C_STAGE = 0x10C4
T_I2, T_N2 = 0x10C9, 0x10CA
T_TEAM2 = 0x10CE
WINS1 = 0x1080
SURV_LIST, SURV_COUNT = 0x4F00, 0x4F30
S_INTRO = 92


def start_single(core):
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    core.ram[0xF070] = 0                 # SINGLE PLAY
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 5, "select")
    core.ram[SEL1] = 0
    core.ram[SEL2] = 1
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.ram[CPU1] = 0
    core.ram[CPU2] = 1
    core.step()
    wait(core, lambda: core.ram[GS] == 1, "single fight", 3600)


def single_boss_intro():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        start_single(core)

        # Jump to the final confrontation and let normal Rugal fall in round 1.
        core.ram[C_IDX] = 6
        core.ram[C_STAGE] = 5
        core.ram[SEL2] = 3
        core.step(2)
        core.put(HP2, 0)

        wait(core, lambda: core.ram[GS] == 4, "Omega entrance intro", 2000)
        assert core.ram[SEL2] == 14, f"Omega not loaded: sel2={core.ram[SEL2]}"
        assert core.ram[ROUNDNO] == 1, (
            f"Omega must start a fresh match: roundno={core.ram[ROUNDNO]}")
        assert core.ram[F_STATE1] == S_INTRO and core.ram[F_STATE2] == S_INTRO, (
            "Omega hand-off must play both entrance intros: "
            f"states={core.ram[F_STATE1]}/{core.ram[F_STATE2]}")
        wait(core, lambda: core.ram[GS] == 1, "round 1 ready", 2000)

        # One round is enough: defeating Omega must fade to black and open
        # ending1 directly, without the "<name> WINS" screen.
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 13, "boss fade", 2000)
        assert core.ram[NEXTF] != 2, "winner banner was armed"
        assert core.ram[FADELEVEL] > 0, "fade did not start"
        wait(core, lambda: core.ram[GS] == 8, "ending1", 3000)
        assert core.ram[E_SCR] == 0, f"ending screen {core.ram[E_SCR]} != 0"
        assert core.ram[FADELEVEL] == 0, "fade did not reach black"
        print("PASS single: Omega intro, one-round KO fades straight to ending1")
    finally:
        core.close()


def single_round2_no_intro():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        start_single(core)
        core.ram[C_IDX] = 6
        core.ram[C_STAGE] = 5
        core.ram[SEL2] = 3
        core.step(2)
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 4, "Omega entrance intro", 2000)
        wait(core, lambda: core.ram[GS] == 1, "round 1 ready", 2000)

        # A draw keeps the same boss match but must not replay the intro.
        core.put(HP1, 0)
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 0 and core.ram[NEXTF] == 1,
             "round 2 intermission", 2000)
        wait(core, lambda: core.ram[GS] == 1, "round 2 ready", 2000)

        assert core.ram[ROUNDNO] == 2, f"roundno={core.ram[ROUNDNO]}"
        assert core.ram[SEL2] == 14, f"Omega left the match: sel2={core.ram[SEL2]}"
        assert core.ram[F_STATE1] != S_INTRO and core.ram[F_STATE2] != S_INTRO, (
            "round 2 must not replay the intro: "
            f"states={core.ram[F_STATE1]}/{core.ram[F_STATE2]}")
        print("PASS single: round 2 does not replay the Omega intro")
    finally:
        core.close()


def team_boss_intro():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        start_team(core)
        core.ram[C_IDX] = 6
        core.ram[C_STAGE] = 5
        core.ram[T_TEAM2] = 3            # normal Rugal (current member)
        core.ram[T_TEAM2 + 1] = 14       # Omega enters next
        core.ram[T_N2] = 2
        core.ram[T_I2] = 0
        core.step(2)
        core.put(HP2, 0)

        wait(core, lambda: core.ram[GS] == 4, "Omega team entrance", 3000)
        assert core.ram[SEL2] == 14, f"Omega not swapped in: sel2={core.ram[SEL2]}"
        assert core.ram[F_STATE2] == S_INTRO, (
            f"Omega team entrance has no intro: state={core.ram[F_STATE2]}")
        wait(core, lambda: core.ram[GS] == 1, "team round ready", 3000)

        # The boss team is out: fade to black and open ending1 directly.
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 13, "team boss fade", 2000)
        assert core.ram[NEXTF] != 2, "team winner banner was armed"
        wait(core, lambda: core.ram[GS] == 8, "team ending1", 3000)
        assert core.ram[E_SCR] == 0, f"ending screen {core.ram[E_SCR]} != 0"
        print("PASS team: Omega intro on member entrance, KO fades straight "
              "to ending1")
    finally:
        core.close()


def survivor_boss_intro():
    core = survivor_boot()
    try:
        assert open_select(core, 4, 0) == 4
        lock_sides(core, cpu2=1)
        wait(core, lambda: core.ram[GS] == 1, "survivor fight", 3600)

        # Make normal Rugal the current foe and Omega the next one.
        core.ram[C_IDX] = 0
        core.ram[SURV_LIST] = 3
        core.ram[SURV_LIST + 1] = 14
        core.ram[SURV_COUNT] = 2
        core.ram[WINS1] = 1              # deciding win -> next foe
        core.step(2)
        core.put(HP2, 0)

        wait(core, lambda: core.ram[C_IDX] == 1, "Omega survivor setup", 4000)
        wait(core, lambda: core.ram[GS] == 4, "Omega survivor intro", 4000)
        assert core.ram[SEL2] == 14, f"Omega not loaded: sel2={core.ram[SEL2]}"
        assert core.ram[F_STATE2] == S_INTRO, (
            f"Omega survivor entrance has no intro: state={core.ram[F_STATE2]}")
        print("PASS survivor: Omega intro on the final fight")
    finally:
        core.close()


def main():
    single_boss_intro()
    single_round2_no_intro()
    team_boss_intro()
    survivor_boss_intro()


if __name__ == "__main__":
    main()
