#!/usr/bin/env python3
"""Takuma's Shouran Kyaku must run, grab on contact and land several kicks.

The source input is F, DF, D, DB, B + kick (HCB+K).  The common QCB+K
shorthand is wired to the same states.  The move runs forward and, when the
distance gate reaches the opponent, enters the grab attempt (1305 -> runtime
60).  The throw HitDef redirects the attacker to the held kick sequence
(1320 -> runtime 101) while the victim stays in S_VHELD (76); every kick
applies one TargetLifeAdd row.

Run after a PVSnesLib build:

    python3 tools/test_takuma_shouran_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                          # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE, F_X, F_HP, F_GRAB = 0x8, 0x0, 0x10, 52
B = 0                              # libretro B -> SNES B -> mugen weak kick
RIGHT, DOWN, LEFT = 7, 5, 6
RUN, GRAB, KICKS = 54, 60, 101
VICTIM_HELD = 76


def check_shouran(core, select_state):
    enter_fight(core, select_state, "takuma", "kyo")
    # Start far enough that the move has to run into the opponent.
    core.put(FP1 + F_X, 80 << 8)
    core.put(FP2 + F_X, 200 << 8)
    core.put(FP1 + F_HP, 200)
    core.put(FP2 + F_HP, 200)
    core.step(10)

    # QCB (down, down-back, back) + weak kick.  HCB+K reaches the same
    # states, so this also covers the documented input.
    for direction in ((DOWN,), (DOWN, LEFT), (LEFT,)):
        core.buttons[0] = set(direction)
        core.step(3)
    core.buttons[0] = {B}
    core.step(3)
    core.buttons[0] = set()

    hp0 = core.word(FP2 + F_HP)
    seen = []
    grabbed = False
    kicked = False
    for _ in range(260):
        p1 = core.ram[FP1 + F_STATE]
        p2 = core.ram[FP2 + F_STATE]
        if p1 not in seen:
            seen.append(p1)
        if p1 == KICKS and p2 == VICTIM_HELD:
            grabbed = True
            kicked = True
        core.step()

    if RUN not in seen:
        raise AssertionError(f"run state {RUN} never played (states={seen})")
    if GRAB not in seen:
        raise AssertionError(f"grab attempt {GRAB} never played (states={seen})")
    if not grabbed:
        raise AssertionError(f"victim was not held during kicks (states={seen})")

    damage = hp0 - core.word(FP2 + F_HP)
    if damage < 40:
        raise AssertionError(
            f"multi-kick sequence applied only {damage} damage (expected 7 hits)")

    # Let the attacker recover and the victim get up.
    for _ in range(500):
        if (core.ram[FP1 + F_STATE] == 0
                and core.ram[FP2 + F_STATE] == 0):
            break
        core.step()
    else:
        raise AssertionError(
            f"fighters did not recover: p1={core.ram[FP1 + F_STATE]} "
            f"p2={core.ram[FP2 + F_STATE]}")
    if core.ram[FP2 + F_GRAB]:
        raise AssertionError("victim stayed grabbed after the sequence")

    print(f"PASS Shouran Kyaku: states={seen}, damage={damage}", flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        check_shouran(core, boot_select(core))
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
