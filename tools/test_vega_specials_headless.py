#!/usr/bin/env python3
"""Headless regression for M.Bison/Vega's special move list.

Vega routes his attacks through MUGEN helper variables, so the synthetic
command table originally emitted no matcher rules for the charge specials
(Psycho Crusher, Double Knee Press, Devil Reverse, Head Press) and the
supers.  This test drives every input and requires the corresponding runtime
state; damaging moves must also take life from the opponent.

Run after a PVSnesLib build:

    python3 tools/test_vega_specials_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_X, F_HP, F_POWER = 0x4008, 0x4000, 0x4010, 0x4030
FP2 = 0x40
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
WP, SP, WK, SK = 1, 9, 0, 8          # libretro Y/X/B/A = MUGEN x/y/a/b
HOLD = 50                            # charge prefix, in ticks
# The source's weak/strong variants share one state for these two moves.
REVERSE_W, REVERSE_S = 52, 52
HEAD_W, HEAD_S = 54, 54


def _btn(buttons):
    return set(buttons) if isinstance(buttons, (set, frozenset)) else {buttons}


def charge_back(buttons):
    return [({LEFT}, HOLD), ({RIGHT} | _btn(buttons), 3)]


def charge_down(buttons):
    return [({DOWN}, HOLD), ({UP} | _btn(buttons), 3)]


def qcf(buttons):
    return [({DOWN}, 3), ({DOWN, RIGHT}, 3), ({RIGHT}, 3),
            (_btn(buttons), 3)]


def qcb(buttons):
    return [({DOWN}, 3), ({DOWN, LEFT}, 3), ({LEFT}, 3),
            (_btn(buttons), 3)]


def super_4646(buttons):
    return [({LEFT}, HOLD), ({RIGHT}, 3), ({LEFT}, 3),
            ({RIGHT} | _btn(buttons), 3)]


CASES = [
    ("Psycho Crusher weak", charge_back(WP), 48, True),
    ("Psycho Crusher strong", charge_back(SP), 49, True),
    ("Double Knee weak", charge_back(WK), 50, True),
    ("Double Knee strong", charge_back(SK), 51, True),
    ("Devil Reverse weak", charge_down(WP), REVERSE_W, True),
    ("Devil Reverse strong", charge_down(SP), REVERSE_S, True),
    ("Head Press weak", charge_down(WK), HEAD_W, True),
    ("Head Press strong", charge_down(SK), HEAD_S, True),
    ("Vega Warp fwd P", qcf({WP, SP}), 56, False),
    ("Vega Warp fwd K", qcf({WK, SK}), 57, False),
    ("Vega Warp back P", qcb({WP, SP}), 58, False),
    ("Vega Warp back K", qcb({WK, SK}), 59, False),
    ("Mega Psycho Crusher", super_4646(WP), 85, True),
    ("Knee Press Nightmare", super_4646(WK), 86, True),
    ("Final Psycho Crusher", super_4646({WP, SP}), 87, True),
    ("MAX Knee Press Nightmare", super_4646({WK, SK}), 88, True),
]


def check(core, select_state, label, seq, sid, damaging):
    enter_fight(core, select_state, "vega", "kyo")
    core.put(F_X, 80 << 8)
    core.put(F_X + FP2, 100 << 8)
    core.put(F_POWER, 3000)
    core.step(20)
    hp0 = core.word(F_HP + FP2)
    for buttons, ticks in seq:
        core.buttons[0] = set(buttons)
        core.step(ticks)
    core.buttons[0] = set()

    seen = set()
    for _ in range(200):
        state = core.ram[F_STATE]
        if state:
            seen.add(state)
        core.step()
    hp1 = core.word(F_HP + FP2)
    assert sid in seen, f"{label}: state {sid} not entered (saw {sorted(seen)})"
    if damaging:
        assert hp1 < hp0, f"{label}: opponent took no damage"
    print(f"OK {label:24s} sid {sid:2d}"
          + (f", {hp0 - hp1} damage" if damaging else ""))


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for label, seq, sid, damaging in CASES:
            check(core, select_state, label, seq, sid, damaging)
    finally:
        core.close()
    print("PASS: Vega's special/super command list is wired end to end")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
