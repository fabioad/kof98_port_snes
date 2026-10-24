#!/usr/bin/env python3
"""TEAM PLAY: a member swap must not clobber the other side's sel or stageidx.

TeamMemberIn stored sel1/sel2 with a 16-bit accumulator.  `sta.b sel1` also
wrote sel2, so a P1-only swap left the CPU's sel at 0 and LoadCharPals
uploaded Kyo's palette for the CPU.  `sta.b sel2` also wrote stageidx ($87),
so a P2 swap pointed the stage-animation clips at the wrong stage.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from capture_pair_headless import tap, wait

GS = 0x1020
SEL1, SEL2 = 0x1085, 0x1086
STAGEIDX = 0x1087
TI1, TI2 = 0x10C8, 0x10C9
TEAM2 = 0x10CE
M_ITEM = 0xF070
HP1, HP2 = 0x4010, 0x4050
CHAR2 = 0x406C


def main():
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        wait(core, lambda: core.ram[GS] == 7, "opening")
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 0, "title")
        core.step(4)
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 6, "menu")
        core.ram[M_ITEM] = 2                      # TEAM PLAY
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 5, "team select")
        core.step(20)
        for _ in range(10):
            before = core.ram[0x10C7]
            core.buttons[0] = {8}
            core.step(3)
            core.buttons[0] = set()
            if core.ram[0x10C7] > before:
                if core.ram[0x10C7] >= 3:
                    break
            core.buttons[0] = {7}
            core.step(3)
            core.buttons[0] = set()
            core.step(8)
        wait(core, lambda: core.ram[GS] == 1, "battle 1", 6000)

        stage0 = core.ram[STAGEIDX]
        cpu_sel_before = core.ram[SEL2]

        # CPU member out -> battle 2: sel2 must still match T_TEAM2[T_I2]
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 2, "ko 1", 300)
        wait(core, lambda: core.ram[GS] == 0, "intermission 1", 600)
        wait(core, lambda: core.ram[GS] == 1, "battle 2", 600)
        expect = core.ram[TEAM2 + core.ram[TI2]]
        assert core.ram[STAGEIDX] == stage0, \
            f"P2 swap changed stageidx {stage0} -> {core.ram[STAGEIDX]}"
        assert core.ram[SEL2] == expect, \
            f"CPU sel after P2 swap = {core.ram[SEL2]}, want {expect}"

        # Human member out -> battle 3: the CPU side did not change, so its
        # sel (and palette) must survive the P1-side TeamMemberIn call.
        core.put(HP1, 0)
        wait(core, lambda: core.ram[GS] == 2, "ko 2", 300)
        wait(core, lambda: core.ram[GS] == 0, "intermission 2", 600)
        wait(core, lambda: core.ram[GS] == 1, "battle 3", 600)
        expect = core.ram[TEAM2 + core.ram[TI2]]
        assert core.ram[STAGEIDX] == stage0, \
            f"P1 swap changed stageidx {stage0} -> {core.ram[STAGEIDX]}"
        assert core.ram[SEL2] == expect, \
            f"CPU sel after P1 swap = {core.ram[SEL2]}, want {expect}"
        assert core.ram[SEL2] != 0 or expect == 0, \
            "CPU sel was cleared by the P1-side swap"
        assert core.word(CHAR2) != 0, "CPU fighter descriptor was lost"
        print(f"PASS team swaps: stageidx={stage0}, "
              f"CPU sel {cpu_sel_before}->{core.ram[SEL2]}, "
              f"char=${core.word(CHAR2):04X}")
    finally:
        core.close()


if __name__ == "__main__":
    main()
