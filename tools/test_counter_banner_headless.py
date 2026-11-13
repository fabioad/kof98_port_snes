#!/usr/bin/env python3
"""Headless regression for the COUNTER!! banner.

The arcade banner is the 10x2 HudCounter block from hud2.inc, drawn on the
attacker's side (P1: row 10, col 1).  It must match the block word for
word and force a full HUD upload, because rows 10/11 are outside the live
HUD bands.  When the flash timer expires both rows must be erased and
uploaded again.

Run after a PVSnesLib build:

    python3 tools/test_counter_banner_headless.py
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
F_STATE, F_HP, F_X = 0x4008, 0x4010, 0x4000
FP2 = 0x40
HUDMAP = 0x4700
HUDDIRTY = 0x1026
RT_HUDFULL = 0x5100
FUS_FLASH = 0x505C
HUD_FULL = 0x80
TOP_ROW, COL = 10, 1                     # P1 attacker side
LEN = 10


def parse_banner():
    text = (ROOT / "build/gen_fight/hud2.inc").read_text()
    m = re.search(r"HudCounter: \.db (\d+),(\d+)\n\s*\.dw ([^\n]+)", text)
    cols, rows = int(m.group(1)), int(m.group(2))
    assert (cols, rows) == (LEN, 2), (cols, rows)
    words = [int(v.strip().lstrip("$"), 16) for v in m.group(3).split(",")]
    cells = [(w & 0xFF, w >> 8) for w in words]
    return cells[:LEN], cells[LEN:]


def cell(core, row, col):
    offset = HUDMAP + (row * 32 + col) * 2
    return core.ram[offset], core.ram[offset + 1]


def wait(core, pred, label, limit=2000):
    for _ in range(limit):
        if pred():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.ram[GS]} flash={core.ram[FUS_FLASH]} "
        f"p1={core.ram[F_STATE]} p2={core.ram[F_STATE + FP2]}")


def main(core_path, rom):
    expected_top, expected_bottom = parse_banner()
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "ralf", "kyo")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, 125 << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.step(20)

        # P2 starts a strong punch; P1's faster normal lands while P2 is in
        # an attack state -> counter hit.
        core.buttons[1] = {9}
        core.step(2)
        core.buttons[1] = set()
        core.step(3)
        core.buttons[0] = {1}
        core.step(2)
        core.buttons[0] = set()

        wait(core, lambda: core.ram[FUS_FLASH] > 0, "counter hit")
        assert core.ram[F_STATE] in (5, 6, 7, 8), (
            f"P1 was not attacking: state {core.ram[F_STATE]}")

        got_top = [cell(core, TOP_ROW, COL + i) for i in range(LEN)]
        got_bottom = [cell(core, TOP_ROW + 1, COL + i) for i in range(LEN)]
        assert got_top == expected_top, (got_top, expected_top)
        assert got_bottom == expected_bottom, (got_bottom, expected_bottom)

        # Rows 10/11 are outside the live bands: the full upload must run so
        # the shadow really reaches VRAM.
        wait(core, lambda: core.word(RT_HUDFULL) == 0 and
             not (core.ram[HUDDIRTY] & HUD_FULL), "full HUD upload")

        wait(core, lambda: core.ram[FUS_FLASH] == 0, "banner expiry")
        wait(core, lambda: core.word(RT_HUDFULL) == 0 and
             not (core.ram[HUDDIRTY] & HUD_FULL), "clear upload")
        cleared_top = [cell(core, TOP_ROW, COL + i) for i in range(LEN)]
        cleared_bottom = [cell(core, TOP_ROW + 1, COL + i) for i in range(LEN)]
        assert cleared_top == [(0, 0)] * LEN, cleared_top
        assert cleared_bottom == [(0, 0)] * LEN, cleared_bottom
        print("PASS COUNTER!! banner: 10x2 block on rows 10/11, erased on expiry")
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, str(args.rom))
