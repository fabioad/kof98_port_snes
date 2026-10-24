#!/usr/bin/env python3
"""SINGLE PLAY: every round must start with the clock at 99.

Round 2+ skips the intro (gamestate 4), and IntroTick used to be the only
place that reset rsecs.  The clock carried over from round 1; after a
time-over it wrapped 0 -> 255 and DrawTimer clamped it to 99, so the timer
looked frozen for ~156 s and the round never ended on time.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from capture_pair_headless import tap, wait
from test_roster import parse_tables

GS, FRAME = 0x1020, 0x1024
RSECS, RFRAME = 0x1076, 0x1077
ROUNDNO, M_ITEM = 0x1082, 0xF070
HUD, TIMER_X = 0x4700, (2 * 32 + 15) * 2


def main():
    roster = parse_tables()
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        wait(core, lambda: core.ram[GS] == 7, "opening")
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 0, "title")
        core.step(4)
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 6, "menu")
        core.ram[M_ITEM] = 0                     # SINGLE PLAY
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 5, "select")
        core.step(10)
        core.ram[0xF052] = roster[0]["cell"]
        for _ in range(12):
            tap(core, 8)
            if core.ram[0x108E]:
                break
        wait(core, lambda: core.ram[GS] == 1, "round 1 live", 6000)
        wait(core, lambda: core.word(0x4008) == 0
             and core.word(0x4048) == 0, "idle")

        assert core.ram[RSECS] == 99, \
            f"round 1 clock={core.ram[RSECS]}"
        core.step(130)
        assert core.ram[RSECS] == 97, \
            f"round 1 clock did not count: {core.ram[RSECS]}"

        # worst case: round 1 ends at 0:00, so the old code carried 0 into
        # round 2 and wrapped it to 255 on the first tick
        core.ram[RSECS] = 1
        wait(core, lambda: core.ram[GS] == 2, "time over", 300)
        wait(core, lambda: core.ram[GS] == 0, "intermission", 600)
        wait(core, lambda: core.ram[GS] == 1, "round 2 live", 600)
        assert core.ram[ROUNDNO] == 2, f"roundno={core.ram[ROUNDNO]}"
        assert core.ram[RSECS] == 99, \
            f"round 2 clock={core.ram[RSECS]} (carried over)"
        row2 = core.ram[HUD + TIMER_X:HUD + TIMER_X + 4]
        assert row2[:2] != [0, 0], f"round 2 timer not drawn: {list(row2)}"

        f0 = core.ram[FRAME]
        core.step(130)
        assert core.ram[FRAME] != f0, "fight stopped advancing in round 2"
        assert core.ram[GS] == 1, f"round 2 left the fight: gs={core.ram[GS]}"
        # CPU hits put the match in hit-stop (FightTick stalls the clock), so
        # require at least one second ticked instead of an exact 97.
        assert core.ram[RSECS] < 99, \
            f"round 2 clock did not count: {core.ram[RSECS]}"
        print("PASS solo round 1 99->97, time-over, round 2 clock counts")
    finally:
        core.close()


if __name__ == "__main__":
    main()
