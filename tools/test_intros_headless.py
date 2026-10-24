#!/usr/bin/env python3
"""Headless intro regression: every selectable fighter must play its own
entrance animation, on both P1 and P2.

A match starts in game state 4 with both fighters in sid 92 (S_INTRO).
The engine used to clobber the scratch byte holding that decision while
entering P1, so P2 always skipped its intro and stood idle.  This test
checks, for every selectable roster cell, that both fighters are in sid 92
and that F_ANIM points at the generated ``<name>Anim92`` record.  It then
waits for the intro to finish and both fighters to reach the stand state.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_roster import parse_tables                     # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
FRAME = 0x1024
F_STATE = 0x4008
F_ANIM = 0x4012
FP2 = 0x40
S_INTRO = 92


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(10)


def wait(core, predicate, label, limit=5000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.word(GS)}, frame={core.word(FRAME)}")


def load_symbols():
    syms = {}
    for line in (ROOT / "kof98-snes.sym").read_text().splitlines():
        fields = line.split()
        if len(fields) == 2:
            syms[fields[1]] = int(fields[0], 16)
    return syms


def to_versus_select(core):
    wait(core, lambda: core.word(GS) == 7, "opening")
    tap(core, 3)                                   # START skips the intro
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(60)                                 # let the title settle
    tap(core, 3)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    core.ram[0xF070] = 1                          # VERSUS
    tap(core, 3)
    wait(core, lambda: core.word(GS) == 5, "select")
    core.ram[0x1091] = 0                          # P2 is human


def lock(core, side, cell):
    lock_addr = 0x108E + side
    for _ in range(10):
        core.ram[0xF052 + side] = cell
        core.step(4)
        tap(core, 8, side)                        # A confirms the cell
        if core.ram[lock_addr] == 1:
            return
    raise AssertionError(f"player {side + 1} never locked cell {cell}")


def run(core_path, rom):
    roster = {v["name"]: v for v in parse_tables().values()}
    # Hidden extras share a visible cell (Omega with Rugal, the Kyo EX
    # variants with Kyo) and are not reachable with the bare cursor.
    hidden = {"omegarugal", "kyonests", "kyoash"}
    names = [v["name"] for _, v in sorted(roster.items())
             if v["name"] not in hidden]
    syms = load_symbols()

    core = Core(core_path, rom)
    try:
        to_versus_select(core)
        select_state = core.save()
        for i, p1name in enumerate(names):
            p2name = names[(i + 1) % len(names)]
            core.load(select_state)
            core.buttons = [set(), set()]
            lock(core, 0, roster[p1name]["cell"])
            lock(core, 1, roster[p2name]["cell"])
            tap(core, 3)                          # start the match

            wait(core, lambda: core.word(GS) == 4,
                 f"{p1name}/{p2name} intro start")
            for side, name in ((0, p1name), (1, p2name)):
                ofs = FP2 if side else 0
                state = core.ram[F_STATE + ofs]
                anim = core.word(F_ANIM + ofs)
                expected = syms[name + "Anim92"] & 0xFFFF
                if state != S_INTRO:
                    raise AssertionError(
                        f"{name}: state {state} != {S_INTRO}")
                if anim != expected:
                    raise AssertionError(
                        f"{name}: anim ${anim:04X} != ${expected:04X}")

            wait(core, lambda: core.word(GS) == 1,
                 f"{p1name}/{p2name} intro end", 1200)
            if core.ram[F_STATE] or core.ram[F_STATE + FP2]:
                raise AssertionError(
                    f"{p1name}/{p2name}: fighters did not reach stand")
            print(f"PASS {p1name} vs {p2name}", flush=True)
    finally:
        core.close()
    return len(names)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    count = run(args.core, args.rom)
    print(f"{count} selectable intros passed on both sides")
