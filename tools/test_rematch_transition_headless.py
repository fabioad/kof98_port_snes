#!/usr/bin/env python3
"""Regression: select -> fight must survive repeated Versus matches.

The second module swap used to deadlock inside snesmod's spcLoad handshake,
freezing the console while still on the character-select screen.  This drives
three complete Versus matches through the real ROM and checks that each
select -> fight transition reaches the fight state.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core

GS = 0x1020
FRAME = 0x1024
SEL1 = 0x1085
SEL2 = 0x1086
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
WINS1 = 0x1080
P2HP = 0x4050
MUSIC_VALID = 0x10E6


def tap(core, button, port=0, settle=3):
    core.step(settle)
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(12)


def wait(core, predicate, label, limit=3000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.ram[GS]:02X} frame={core.word(FRAME):03X}")


def lock(core, p1=0, p2=1):
    core.ram[SEL1] = p1
    core.ram[SEL2] = p2
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.ram[CPU1] = 0
    core.ram[CPU2] = 0
    core.step(2)


def run(library, rom, matches=3):
    core = Core(library, rom)
    try:
        wait(core, lambda: core.word(GS) == 7, "opening")
        tap(core, 3)                                     # skip intro
        wait(core, lambda: core.word(GS) == 0, "title")
        core.step(4)
        tap(core, 3)                                     # mode menu
        wait(core, lambda: core.word(GS) == 6, "menu")
        core.ram[0xF070] = 1                             # SINGLE VS
        tap(core, 3)
        wait(core, lambda: core.word(GS) == 5, "select")
        core.step(30)

        for match in range(matches):
            lock(core)
            wait(core, lambda: core.word(GS) == 1,
                 f"fight {match + 1} starts", 1500)
            print(f"PASS fight {match + 1} reached", flush=True)

            if match + 1 == matches:
                break

            # End the match through the real KO/winner path.
            core.ram[WINS1] = 1
            core.put(P2HP, 0)
            core.step(2)
            wait(core, lambda: core.word(GS) == 0, f"winner {match + 1}")
            wait(core, lambda: core.word(GS) == 5,
                 f"select after match {match + 1}")
            core.step(30)                                # let assets settle

        return matches
    finally:
        core.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--core",
        default="/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    count = run(args.core, args.rom)
    print(f"{count} rematch transitions passed")
