#!/usr/bin/env python3
"""Select-screen navigation with no MSU-1 data file.

Without the .msu, the cursor must still reach the ROM-resident roster.  This
covers the two special cases:
  * left on Terry's cell goes to Shingo's cell;
  * the Rugal cell stays on the cursor path and shows O.RUGAL, but only
    L+R selects the ROM-resident Omega form.  Plain A is denied (normal
    Rugal needs streamed CHR), so no normal Rugal can be picked.

Run after a PVSnesLib build:

    python3 tools/test_select_nomsu_headless.py
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select       # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
MSUOK = 0x107A
SEL1 = 0x1085
LOCK1 = 0x108E
SCUR1 = 0xF052
SFACE1 = 0xF054

A, L, R = 8, 10, 11
LEFT, RIGHT = 6, 7
TERRY_CELL = 0
SHINGO_CELL = 36
RUGAL_CELL = 37


def tap(core, buttons, ticks=3, settle=4):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()
    core.step(settle)


def select_state(core, state):
    core.load(state)
    core.buttons = [set(), set()]
    core.step(10)


def main(core_path, rom):
    with tempfile.TemporaryDirectory(prefix="kof98-nomsu-") as tmp:
        nomsu = Path(tmp) / "kof98-snes.sfc"
        shutil.copyfile(rom, nomsu)      # deliberately no matching .msu
        core = Core(core_path, nomsu)
        try:
            state = boot_select(core)
            if core.ram[MSUOK] != 0:
                raise AssertionError("expected msuok=0 without the .msu file")
            if core.word(GS) != 5:
                raise AssertionError(f"select screen not live: gs={core.word(GS)}")

            # Terry -> LEFT -> Shingo.
            select_state(core, state)
            core.ram[SCUR1] = TERRY_CELL
            core.step(4)
            tap(core, {LEFT})
            if core.ram[SCUR1] != SHINGO_CELL:
                raise AssertionError(
                    f"Terry LEFT landed on cell {core.ram[SCUR1]}, "
                    f"expected Shingo ({SHINGO_CELL})")
            if core.ram[SFACE1] != 2:
                raise AssertionError(
                    f"Shingo cell name id is {core.ram[SFACE1]}, expected 2")
            print("PASS Terry LEFT -> Shingo", flush=True)

            # Shingo -> RIGHT -> Rugal cell (walkable without MSU).
            core.ram[SCUR1] = SHINGO_CELL
            core.step(4)
            tap(core, {RIGHT})
            if core.ram[SCUR1] != RUGAL_CELL:
                raise AssertionError(
                    f"Shingo RIGHT landed on cell {core.ram[SCUR1]}, "
                    f"expected Rugal ({RUGAL_CELL})")
            if core.ram[SFACE1] != 14:
                raise AssertionError(
                    f"Rugal cell shows char {core.ram[SFACE1]}, "
                    f"expected Omega (14)")
            print("PASS Shingo RIGHT -> O.RUGAL cell", flush=True)

            # Plain A on the Rugal cell is denied: no normal Rugal.
            select_state(core, state)
            core.ram[SCUR1] = RUGAL_CELL
            core.step(4)
            tap(core, {A})
            if core.ram[LOCK1]:
                raise AssertionError("normal Rugal locked without MSU")
            print("PASS plain A on Rugal cell denied", flush=True)

            # L+R+A on the same cell selects the ROM-resident Omega.
            core.buttons[0] = {L, R}
            core.step(4)
            tap(core, {L, R, A})
            core.buttons[0] = set()
            core.step(4)
            if not core.ram[LOCK1]:
                raise AssertionError("L+R did not lock Omega Rugal")
            if core.ram[SEL1] != 14:
                raise AssertionError(
                    f"L+R locked char {core.ram[SEL1]}, expected Omega (14)")
            print("PASS L+R on Rugal cell -> Omega Rugal", flush=True)
        finally:
            core.close()
    print("PASS: no-MSU select navigation and hidden Omega gating")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
