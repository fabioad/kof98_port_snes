#!/usr/bin/env python3
"""Mr. Big's California Romance must run and connect as a combo.

The strong source state (1410) carries four HitDefs, but the native table
kept only the first one.  The weak command entered state 1400, whose hits
live in the helper-driven 1401/1402 states -- none of those were wired, so
the move animated but never hit.  Both commands now use the four-contact
1410 timeline (the weak one after its 1400 startup), with damage totals
similar to Sakura's anti-air.

Run after a PVSnesLib build:

    python3 tools/test_mrbig_california_headless.py
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
F_STATE, F_HP = 8, 16
RIGHT, DOWN = 7, 5
LIGHT_P, STRONG_P = 1, 9        # libretro Y -> MUGEN x; X -> y
CHAIN = (56, 57, 58)


def run(core, state, button, label):
    core.load(state)
    core.buttons = [set(), set()]
    core.step(4)
    core.put(FP1, 110 << 8)
    core.put(FP2, 155 << 8)
    core.step(8)

    # ~F, D, DF + button (the source command for California Romance).
    for direction in ({RIGHT}, {DOWN}, {DOWN, RIGHT}):
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = set()
    core.step(1)
    core.buttons[0] = {button}
    core.step(2)
    core.buttons[0] = set()

    states = []
    hp = 200
    hits = []
    last = hp
    for _ in range(300):
        core.step()
        st = core.ram[FP1 + F_STATE]
        if not states or states[-1] != st:
            states.append(st)
        now = core.word(FP2 + F_HP)
        if now < last:
            hits.append(last - now)
            last = now
        hp = min(hp, now)
    total = 200 - hp
    if len(hits) < 4:
        raise AssertionError(f"{label}: only {len(hits)} contacts, "
                             f"states={states}, hits={hits}")
    if not 22 <= total <= 28:
        raise AssertionError(f"{label}: damage {total}, expected ~26")
    for sid in CHAIN:
        if sid not in states:
            raise AssertionError(f"{label}: slice {sid} never ran: {states}")
    if core.ram[FP1 + F_STATE] or core.ram[FP2 + F_STATE]:
        raise AssertionError(
            f"{label}: fighters did not recover: "
            f"{core.ram[FP1 + F_STATE]}/{core.ram[FP2 + F_STATE]}")
    print(f"PASS {label}: states={states}, {len(hits)} hits, "
          f"damage={total}", flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "mrbig", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        baseline = core.save()
        run(core, baseline, LIGHT_P, "weak California Romance")
        run(core, baseline, STRONG_P, "strong California Romance")
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
