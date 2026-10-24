#!/usr/bin/env python3
"""TEAM PLAY: CONTINUE and SELECT FIGHTER must replay the whole CPU trio.

After a loss both teams restart at member 1, so the player faces the CPU
from the first fighter to the last again.  Run without arguments to test
both paths (each in its own process).
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from capture_pair_headless import tap, wait

GS = 0x1020
SEL1, SEL2 = 0x1085, 0x1086
TI1, TI2 = 0x10C8, 0x10C9
TEAM1, TEAM2 = 0x10CB, 0x10CE
M_ITEM = 0xF070
HP1, HP2 = 0x4010, 0x4050
CHAR2 = 0x406C
YL_SEL = 0x4FBA


def pick_trio(core):
    core.step(20)
    for _ in range(10):
        before = core.ram[0x10C7]
        core.buttons[0] = {8}
        core.step(3)
        core.buttons[0] = set()
        if core.ram[0x10C7] > before and core.ram[0x10C7] >= 3:
            break
        core.buttons[0] = {7}
        core.step(3)
        core.buttons[0] = set()
        core.step(8)


def boot_team(core):
    wait(core, lambda: core.ram[GS] == 7, "opening")
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 0, "title")
    core.step(4)
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "menu")
    core.ram[M_ITEM] = 2                       # TEAM PLAY
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 5, "team select")
    pick_trio(core)
    wait(core, lambda: core.ram[GS] == 1, "battle 1", 6000)


def next_round(core, ko_p1, final=False):
    core.put(HP1 if ko_p1 else HP2, 0)
    wait(core, lambda: core.ram[GS] == 2, "ko", 300)
    wait(core, lambda: core.ram[GS] == 0, "result", 900)
    if final:
        wait(core, lambda: core.ram[GS] == 12, "you lose", 1500)
    else:
        wait(core, lambda: core.ram[GS] in (1, 4), "next", 900)
        wait(core, lambda: core.ram[GS] == 1, "next live", 900)


def run(mode):
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        boot_team(core)
        cpu_first = core.word(CHAR2)
        cpu_first_sel = core.ram[SEL2]
        human_first_sel = core.ram[SEL1]

        # beat the first two CPU members, then lose the human trio
        next_round(core, ko_p1=False)
        next_round(core, ko_p1=False)
        next_round(core, ko_p1=True)
        next_round(core, ko_p1=True)
        next_round(core, ko_p1=True, final=True)
        assert core.ram[GS] == 12, f"no YOU LOSE screen: gs={core.ram[GS]}"
        assert core.ram[TI1] == 3 and core.ram[TI2] == 2, \
            f"bad loss state T=({core.ram[TI1]},{core.ram[TI2]})"

        if mode == "continue":
            tap(core, 3)                        # CONTINUE is the default row
        else:
            tap(core, 5)                        # SELECT FIGHTER
            assert core.ram[YL_SEL] == 1, f"YL_SEL={core.ram[YL_SEL]}"
            tap(core, 3)
            wait(core, lambda: core.ram[GS] == 5, "select", 3000)
            assert core.ram[0x4FBD] == 1, "YL_REPICK not armed"
            pick_trio(core)

        wait(core, lambda: core.ram[GS] == 1, f"{mode} fight", 6000)
        assert core.ram[TI1] == 0, \
            f"{mode}: human member={core.ram[TI1]}, want 0"
        assert core.ram[TI2] == 0, \
            f"{mode}: CPU member={core.ram[TI2]}, want 0"
        assert core.word(CHAR2) == cpu_first, \
            f"{mode}: CPU char ${core.word(CHAR2):04X}, want ${cpu_first:04X}"
        assert core.ram[SEL2] == cpu_first_sel, \
            f"{mode}: CPU sel {core.ram[SEL2]}, want {cpu_first_sel}"
        assert core.ram[SEL1] == human_first_sel, \
            f"{mode}: human sel {core.ram[SEL1]}, want {human_first_sel}"
        assert core.word(HP1) == 200 and core.word(HP2) == 200, \
            f"{mode}: HP {core.word(HP1)}/{core.word(HP2)}"
        print(f"PASS {mode}: rematch from member 1, CPU char ${cpu_first:04X}")
    finally:
        core.close()


def main():
    if len(sys.argv) > 1:
        run(sys.argv[1])
        return
    for mode in ("continue", "repick"):
        subprocess.run([sys.executable, str(Path(__file__).resolve()),
                        mode], check=True)


if __name__ == "__main__":
    main()
