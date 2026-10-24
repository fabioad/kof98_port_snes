#!/usr/bin/env python3
"""Kyo EX selection regression: L/R on the Kyo cell picks the hidden Nests
and Ash variants (MSU only); without MSU the same input keeps normal Kyo."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_roster import parse_tables                     # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
SEL1 = 0x1085
MSUOK = 0x107A
F_STATE = 0x4008
F_CHAR = 0x402C
S_INTRO = 92
START, A, L, R = 3, 8, 10, 11


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(10)


def wait(core, predicate, label, limit=6000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(f"{label}: gs={core.word(GS)}")


def symbols():
    result = {}
    for line in (ROOT / "kof98-snes.sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2:
            result[fields[1]] = int(fields[0], 16)
    return result


def lock(core, side, cell, hold=()):
    addr = 0x108E + side
    for _ in range(10):
        core.ram[0xF052 + side] = cell
        core.buttons[side] = set(hold) | {A}
        core.step(5)
        core.buttons[side] = set(hold)
        core.step(3)
        if core.ram[addr] == 1:
            return
    raise AssertionError(f"player {side + 1} never locked cell {cell}")


def main(core_path, rom):
    syms = symbols()
    roster = {v["name"]: v for v in parse_tables().values()}
    core = Core(core_path, rom)
    try:
        wait(core, lambda: core.word(GS) == 7, "opening")
        tap(core, START)
        wait(core, lambda: core.word(GS) == 0, "title")
        core.step(60)
        tap(core, START)
        wait(core, lambda: core.word(GS) == 6, "mode menu")
        core.ram[0xF070] = 1
        tap(core, START)
        wait(core, lambda: core.word(GS) == 5, "select")
        core.ram[0x1091] = 0
        select = core.save()

        cases = ((0, (), "CharKyo"),
                 (48, (L,), "CharKyonests"),
                 (49, (R,), "CharKyoash"))
        for expected_id, hold, symbol in cases:
            core.load(select)
            core.buttons = [set(), set()]
            core.step(4)
            lock(core, 0, roster["kyo"]["cell"], hold)
            if core.ram[SEL1] != expected_id:
                raise AssertionError(
                    f"{symbol}: sel1={core.ram[SEL1]} != {expected_id}")
            lock(core, 1, roster["iori"]["cell"])
            tap(core, START)
            wait(core, lambda: core.word(GS) in (1, 4), symbol + " fight")
            wait(core, lambda: core.word(F_STATE) == S_INTRO,
                 symbol + " intro")
            got = core.word(F_CHAR)
            want = syms[symbol] & 0xFFFF
            if got != want:
                raise AssertionError(
                    f"{symbol}: descriptor ${got:04X} != ${want:04X}")
            print(f"PASS {symbol}", flush=True)

        # Simulate a cartridge without the MSU data file: the override must
        # not fire and the normal (ROM-resident) Kyo must lock.
        core.load(select)
        core.buttons = [set(), set()]
        core.step(4)
        core.ram[MSUOK] = 0
        lock(core, 0, roster["kyo"]["cell"], (L,))
        if core.ram[SEL1] != 0:
            raise AssertionError("no-MSU L still selected a variant")
        print("PASS no-MSU fallback", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, args.rom)
