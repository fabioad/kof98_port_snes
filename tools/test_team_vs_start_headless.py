#!/usr/bin/env python3
"""TEAM VS: both players pick a trio and the fight must actually start.

Team VS never called CampStart, so C_STAGE was left at the $55 WRAM fill
pattern.  CampStage copied that into STAGEF, StagePick indexed StageTab far
outside the 10 stages and the CPU hung with the screen blanked (the select
theme kept playing).  The winner screen also needs a valid stage for the
second/third members, hence the swap check at the end.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                       # noqa: E402
from capture_pair_headless import tap, wait                 # noqa: E402
from test_midfight_join_headless import GS                  # noqa: E402

HP1, HP2 = 0x4010, 0x4050

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
CELLS = (3, 6, 36)
T_STEP, T_PICK_SIDE = 0x10C7, 0x10D2
T_TEAM1, T_TEAM2 = 0x10CB, 0x10CE
LOCK1, LOCK2 = 0x108E, 0x108F
C_STAGE, STAGEIDX = 0x10C4, 0x1087


def pick_trio(core, side, cursor, lock):
    guard = 0
    while not core.ram[lock] and guard < 24:
        step = core.ram[T_STEP]
        core.ram[cursor] = CELLS[min(step, 2)]
        core.step(8)
        tap(core, 8, side)
        guard += 1
    assert core.ram[lock] == 1, f"side {side + 1} never locked (guard={guard})"


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        for _ in range(80):
            if core.ram[GS] == 6:
                break
            tap(core, 3)
        assert core.ram[GS] == 6, f"mode menu not reached: gs={core.ram[GS]}"
        core.ram[0xF070] = 3                  # TEAM VS
        for _ in range(30):
            tap(core, 3)
            for _ in range(20):
                if core.ram[GS] == 5:
                    break
                core.step()
            if core.ram[GS] == 5:
                break
        wait(core, lambda: core.ram[GS] == 5, "team vs select", 600)

        pick_trio(core, 0, 0xF052, LOCK1)
        pick_trio(core, 1, 0xF053, LOCK2)
        assert list(core.ram[T_TEAM1:T_TEAM1 + 3]) == [0, 1, 2]
        assert list(core.ram[T_TEAM2:T_TEAM2 + 3]) == [0, 1, 2]

        wait(core, lambda: core.ram[GS] == 1, "team vs battle 1", 3600)
        stage = core.ram[STAGEIDX]
        assert stage < 10, f"invalid STAGEF loaded: stageidx={stage}"
        assert core.ram[C_STAGE] < 10, f"C_STAGE not initialised: {core.ram[C_STAGE]}"
        assert core.word(HP1) == 200 and core.word(HP2) == 200
        print(f"PASS team VS picks -> battle 1 (stage {stage})")

        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 2, "ko", 500)
        wait(core, lambda: core.ram[GS] == 0, "intermission", 900)
        wait(core, lambda: core.ram[GS] == 1, "battle 2", 1200)
        core.step(30)
        assert core.ram[STAGEIDX] == stage, \
            f"swap changed stage {stage} -> {core.ram[STAGEIDX]}"
        assert core.word(HP1) == 200 and core.word(HP2) == 200
        print(f"PASS team VS swap -> battle 2 (stage {stage})")
    finally:
        core.close()


if __name__ == "__main__":
    main()
