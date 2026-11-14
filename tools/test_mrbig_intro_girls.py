#!/usr/bin/env python3
"""Mr. Big's round-1 intro must draw both girlfriends on screen.

The girls are not helpers in this engine: they ride a dedicated OAM overlay
loaded into the second effect page.  This headless check enters Mr. Big vs
Kyo, waits for the intro state and verifies that OAM contains cells from
that page on both sides of Big.  After the intro the cells must be gone so
they cannot linger over the fight.

Run after a PVSnesLib build:

    python3 tools/test_mrbig_intro_girls.py
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, tap, wait  # noqa: E402
from test_roster import parse_tables                     # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS, F_STATE, F_X = 0x1020, 0x4008, 0x4000
FP2 = 0x40
OAM, OAMTOP = 0x1800, 0x102A
A = 8
LOCK1, LOCK2 = 0x108E, 0x108F


def enter_fight(core, select_state, p1, p2):
    roster = {v["name"]: v for v in parse_tables().values()}
    core.load(select_state)
    core.buttons = [set(), set()]
    core.step(4)
    for side, char, lock in ((0, p1, LOCK1), (1, p2, LOCK2)):
        core.ram[0xF052 + side] = roster[char]["cell"]
        for _ in range(10):
            core.step(4)
            tap(core, A, side)
            if core.ram[lock] == 1:
                break
        else:
            raise AssertionError(f"side {side + 1} did not lock")
    tap(core, 3)  # START


def girl_cells(core):
    """OAM cells using the second effect page (tiles 448..511)."""
    top = core.word(OAMTOP) // 4
    out = []
    for i in range(top):
        x, y, tile, attr = core.ram[OAM + i * 4:OAM + i * 4 + 4]
        if (attr & 0x01) and tile >= 0xC0:
            out.append((x, y, tile, attr))
    return out


def expected_girl_cells():
    """Cell count emitted by build_intro_girls (8x8 + packed 16x16)."""
    text = (ROOT / "build/gen_fight/intro_girls.inc").read_text()
    return sum(int(m.group(1)) for m in re.finditer(
        r"Girl[AB]Cells:\s*\n\s*\.db (\d+)", text))


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "mrbig", "kyo")
        wait(core, lambda: core.word(GS) == 4 and core.ram[F_STATE] == 92,
             "intro")
        core.step(20)
        cells = girl_cells(core)
        expected = expected_girl_cells()
        if len(cells) < expected:
            raise AssertionError(
                f"only {len(cells)}/{expected} girlfriend cells during the intro")
        big_x = core.word(F_X) >> 8
        if not any(x < big_x for x, *_ in cells):
            raise AssertionError("no girlfriend cell left of Mr. Big")
        if not any(x > big_x for x, *_ in cells):
            raise AssertionError("no girlfriend cell right of Mr. Big")

        wait(core, lambda: core.word(GS) == 1 and
             core.ram[F_STATE] == 0 and core.ram[F_STATE + FP2] == 0,
             "round start")
        core.step(30)
        left = girl_cells(core)
        if left:
            raise AssertionError(
                f"{len(left)} girlfriend cells survived the intro")
        print(f"PASS Mr. Big intro: {len(cells)} girlfriend cells, "
              "cleared for the round", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
