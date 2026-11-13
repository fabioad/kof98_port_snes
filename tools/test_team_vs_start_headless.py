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
T_STEP2 = T_PICK_SIDE                    # Team VS reuses it as P2's count
T_TEAM1, T_TEAM2 = 0x10CB, 0x10CE
LOCK1, LOCK2 = 0x108E, 0x108F
C_STAGE, STAGEIDX = 0x10C4, 0x1087


def pick_trio(core, side, cursor, lock):
    counter = (T_STEP, T_STEP2)[side]
    guard = 0
    while not core.ram[lock] and guard < 24:
        step = core.ram[counter]
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
        core.step(4)                          # let the menu latch the new row
        for _ in range(30):
            tap(core, 3)
            for _ in range(20):
                if core.ram[GS] == 5:
                    break
                core.step()
            if core.ram[GS] == 5:
                break
        wait(core, lambda: core.ram[GS] == 5, "team vs select", 600)

        # Both pads own a cursor, so one frame of input must move both.
        core.ram[0xF052] = 3
        core.ram[0xF053] = 6
        core.step(4)
        before = (core.ram[0xF052], core.ram[0xF053])
        core.buttons = [{7}, {7}]             # RIGHT on pad 1 and pad 2
        core.step(4)
        core.buttons = [set(), set()]
        core.step(10)
        after = (core.ram[0xF052], core.ram[0xF053])
        assert after[0] != before[0] and after[1] != before[1], (
            f"cursors did not move together: {before} -> {after}")
        print("PASS both pads move their cursor in the same frame")

        # Same-frame confirm: both sides bank their first pick at once.
        core.ram[0xF052] = 3
        core.ram[0xF053] = 6
        core.step(8)
        core.buttons = [{8}, {8}]             # A on pad 1 and pad 2
        core.step(4)
        core.buttons = [set(), set()]
        core.step(12)
        assert core.ram[T_STEP] == 1 and core.ram[T_STEP2] == 1, (
            f"same-frame confirm: steps {core.ram[T_STEP]}/{core.ram[T_STEP2]}")
        assert list(core.ram[T_TEAM1:T_TEAM1 + 1]) == [0]
        assert list(core.ram[T_TEAM2:T_TEAM2 + 1]) == [1]
        assert core.ram[0xF052] == 4 and core.ram[0xF053] == 7, (
            f"cursor did not advance right: {core.ram[0xF052]}/"
            f"{core.ram[0xF053]}")
        print("PASS both pads confirm and advance their cursor to the right")

        # A pick on the right edge falls back to the portrait on the left.
        core.ram[0xF052] = 35
        core.step(8)
        core.buttons = [{8}, set()]
        core.step(4)
        core.buttons = [set(), set()]
        core.step(12)
        assert core.ram[0xF052] == 34, (
            f"right-edge pick left cursor at {core.ram[0xF052]}, expected 34")
        assert core.ram[T_STEP] == 2
        core.buttons = [{0}, set()]           # undo the edge pick
        core.step(4)
        core.buttons = [set(), set()]
        core.step(12)
        assert core.ram[T_STEP] == 1
        print("PASS right-edge pick moves the cursor left")

        # B undoes only the pad that pressed it.
        core.buttons = [set(), {0}]
        core.step(4)
        core.buttons = [set(), set()]
        core.step(12)
        assert core.ram[T_STEP] == 1 and core.ram[T_STEP2] == 0, (
            f"P2 B touched P1: steps {core.ram[T_STEP]}/{core.ram[T_STEP2]}")
        print("PASS B cancels only the pressing side")

        pick_trio(core, 0, 0xF052, LOCK1)
        # P2 is always human in Team VS; the P2 cursor ring must be visible
        # once it is Pad2's turn (cpu2 defaults to 1 and used to hide it).
        best_ring = 0
        for _ in range(24):
            core.step()
            best_ring = max(best_ring, sum(
                1 for i in range(128)
                if core.ram[0x1800 + i * 4 + 3] == 0x36))
        assert best_ring >= 8, f"P2 ring cells missing: {best_ring}"
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
