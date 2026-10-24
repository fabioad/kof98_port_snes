#!/usr/bin/env python3
"""Headless ROM regression: Start must reach a responsive fight in each mode.

Uses the installed Snes9x libretro core. All menu/selection actions are real
controller input; savestates only restore the mode menu between cases.
"""
import argparse
from pathlib import Path

from calibration.headless import Core

ROOT = Path(__file__).resolve().parents[1]
START, DOWN, RIGHT = 3, 5, 7
GS, FRAME = 0x1020, 0x1024


def wait_for(core, predicate, label, limit=1200):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.word(GS)}, frame={core.word(FRAME)}, "
        f"marker={core.ram[0x4614]:02X}")


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def run(library, rom):
    core = Core(library, rom)
    passed = []
    try:
        wait_for(core, lambda: core.word(GS) == 7, "opening")
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 0, "title")
        core.step(4)                 # let TitleEnter release the skip press
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 6, "mode menu")
        menu = core.save()
        for mode, name in enumerate(("single", "versus")):
            label = name
            core.load(menu)
            core.buttons = [set(), set()]
            for _ in range(mode):
                tap(core, DOWN)
            tap(core, START)
            wait_for(core, lambda: core.word(GS) == 5, label + " select")
            core.step(10)
            # ShowSelect rebuilds VRAM for several frames.  Retry the A press
            # so an input consumed before SelTick starts does not leave the
            # side unlocked and this regression stuck on the select screen.
            for _ in range(12):
                tap(core, 8)            # P1 confirms the default cell
                if core.ram[0x108E]:
                    break
            if mode == 1:
                for _ in range(12):
                    tap(core, 8, port=1)   # VERSUS: P2 confirms
                    if core.ram[0x108F]:
                        break
            assert core.ram[0x108E], label + " P1 never locked"
            if mode == 1:
                assert core.ram[0x108F], label + " P2 never locked"
            wait_for(core, lambda: core.word(GS) == 1, label + " fight")
            wait_for(core, lambda: core.word(0x4008) == 0,
                     label + " idle")
            before = core.word(0x4000)
            tap(core, RIGHT)
            assert core.word(0x4000) != before, label + " movement frozen"
            # A frozen frame can still contain valid fighter state.
            frames = set()
            for _ in range(120):
                core.step()
                frames.add(core.word(FRAME))
            assert len(frames) > 30, label + " frame counter frozen"
            passed.append(label)
            print("PASS", label, flush=True)
    finally:
        core.close()
    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default="/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    cases = run(args.core, args.rom)
    print(f"{len(cases)} Start transitions passed")
