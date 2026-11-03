#!/usr/bin/env python3
"""Headless regression for the COUNTER banner.

The banner string is drawn with the shared 8x16 big font.  It must write
both rows (top tile at row 10, tile+1 at row 11) and force a full HUD
upload, because rows 10/11 are outside the live HUD bands.  When the flash
timer expires both rows must be erased and uploaded again.

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
TOP_ROW, COL = 10, 12
LEN = 7


def parse_banner():
    text = (ROOT / "build/gen_fight/hud.inc").read_text()
    line = re.search(r"CounterTxt: \.db ([^\n]+)", text).group(1)
    values = [int(v.strip()) for v in line.split(",")]
    assert values[0] == LEN, values
    attr = int(re.search(r"ATT_YEL = \$([0-9A-Fa-f]+)", text).group(1), 16)
    return values[1:], attr


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
    top, attr = parse_banner()
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

        expected_top = [(tile, attr) for tile in top]
        expected_bottom = [(tile + 1, attr) for tile in top]
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
        print("PASS COUNTER banner: 8x16 glyphs on rows 10/11, erased on expiry")
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, str(args.rom))
