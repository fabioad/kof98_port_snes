#!/usr/bin/env python3
"""Sakura's light anti-air knocks down; the strong one is a five-hit combo.

The light Shou'ou Ken (MUGEN 1100, sid 48) used to carry only ``air.fall``,
so a grounded opponent recovered through S_HIT instead of falling to
S_DOWN.  The strong version (MUGEN 1110, sid 49) has three HitDefs but the
native table kept a single row, so it landed once.  It is now sliced over
five runtime sids (49, 60, 61, 62, 63) and the damage is distributed so the
whole combo removes exactly the same 26 HP as a normal strong punch.

Run after a PVSnesLib build:

    python3 tools/test_sakura_antiair_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_X, F_STATE, F_HP = 0, 8, 16
COMBO = 0x4FC0
DOWN, RIGHT = 5, 7
X, Y = 9, 1                              # SNES X -> MUGEN y; Y -> MUGEN x
S_DOWN = 10
LIGHT_ANTIAIR = 48
STRONG_ANTIAIR = 49
STRONG_SLICES = (60, 61, 62, 63)


def press(core, buttons, ticks=3):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def start_fight(core, select_state):
    enter_fight(core, select_state, "sakura", "kyo")
    core.put(FP1 + F_X, 130 << 8)
    core.put(FP2 + F_X, 165 << 8)
    core.step(10)


def dp_punch(core, button):
    # DP motion: F, D, DF + punch (MUGEN ~F, D, DF, x/y).
    for direction in ({RIGHT}, {DOWN}, {DOWN, RIGHT}):
        core.buttons[0] = set(direction)
        core.step(3)
    press(core, {button})


def collect(core, ticks, hp0):
    states = []
    peak_combo = 0
    down_ticks = 0
    damage = 0
    for _ in range(ticks):
        p1 = core.ram[FP1 + F_STATE]
        p2 = core.ram[FP2 + F_STATE]
        if not states or states[-1] != p1:
            states.append(p1)
        peak_combo = max(peak_combo, core.ram[COMBO])
        if p2 == S_DOWN:
            down_ticks += 1
        damage = max(damage, hp0 - core.word(FP2 + F_HP))
        core.step()
    return states, peak_combo, down_ticks, damage


def normal_strong_damage(core, select_state):
    start_fight(core, select_state)
    hp0 = core.word(FP2 + F_HP)
    press(core, {X})
    _, _, _, damage = collect(core, 150, hp0)
    if damage <= 0:
        raise AssertionError("normal strong punch did not connect")
    return damage


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        strong_budget = normal_strong_damage(core, select_state)

        # --- weak Shou'ou Ken: must knock the opponent down -----------------
        start_fight(core, select_state)
        hp0 = core.word(FP2 + F_HP)
        dp_punch(core, Y)
        states, _, down_ticks, damage = collect(core, 400, hp0)
        if LIGHT_ANTIAIR not in states:
            raise AssertionError(
                f"light anti-air sid {LIGHT_ANTIAIR} never played: {states}")
        if down_ticks < 20:
            raise AssertionError(
                f"light anti-air did not knock down ({down_ticks} down ticks)")
        if damage <= 0:
            raise AssertionError("light anti-air did not connect")
        print(f"PASS weak Shou'ou Ken: states={states}, "
              f"knockdown={down_ticks}t, damage={damage}", flush=True)

        # --- strong Shou'ou Ken: exactly five contacts ----------------------
        start_fight(core, select_state)
        hp0 = core.word(FP2 + F_HP)
        dp_punch(core, X)
        states, peak_combo, down_ticks, damage = collect(
            core, 500, hp0)
        if STRONG_ANTIAIR not in states:
            raise AssertionError(
                f"strong anti-air sid {STRONG_ANTIAIR} never played: {states}")
        for sid in STRONG_SLICES:
            if sid not in states:
                raise AssertionError(
                    f"strong anti-air slice {sid} never played: {states}")
        if peak_combo != 5:
            raise AssertionError(
                f"combo counter peaked at {peak_combo}, expected 5")
        if down_ticks < 20:
            raise AssertionError(
                f"strong anti-air did not knock down ({down_ticks} down ticks)")
        if damage != strong_budget:
            raise AssertionError(
                f"strong anti-air dealt {damage} damage, expected the "
                f"normal strong punch budget ({strong_budget})")
        if core.ram[FP1 + F_STATE] or core.ram[FP2 + F_STATE]:
            raise AssertionError(
                f"fighters did not recover: p1={core.ram[FP1 + F_STATE]} "
                f"p2={core.ram[FP2 + F_STATE]}")
        print(f"PASS strong Shou'ou Ken: states={states}, "
              f"combo={peak_combo}, knockdown={down_ticks}t, "
              f"damage={damage}", flush=True)
    finally:
        core.close()
    print("PASS: Sakura anti-airs (light knockdown / strong 5-hit combo)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
