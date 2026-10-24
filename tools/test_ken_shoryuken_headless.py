#!/usr/bin/env python3
"""Ken's strong Shoryuken registers three hits and finishes in a knockdown.

The source state 1110 carries three HitDefs (uppercut, rising uppercut and
launcher).  The native tables used to keep a single row, so the move landed
once and never dropped the victim.  It is now split over three runtime sids
and the final hit carries fall=1; total damage stays at the single-hit
strong-special value instead of tripling.

Run after a PVSnesLib build:

    python3 tools/test_ken_shoryuken_headless.py
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
STRONG_P = 9                             # SNES X -> MUGEN y
S_DOWN = 10
SHORYUKEN, HIT2, HIT3 = 53, 58, 59


def press(core, buttons, ticks=3):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "ken", "kyo")
        core.put(FP1 + F_X, 130 << 8)
        core.put(FP2 + F_X, 160 << 8)
        core.step(10)

        hp0 = core.word(FP2 + F_HP)
        # DP + strong punch (MUGEN: ~F, D, DF, y).
        for direction in ({RIGHT}, {DOWN}, {DOWN, RIGHT}):
            core.buttons[0] = set(direction)
            core.step(2)
        press(core, {STRONG_P})

        states = []
        peak_combo = 0
        knockdown = False
        down_ticks = 0
        for _ in range(500):
            p1 = core.ram[FP1 + F_STATE]
            p2 = core.ram[FP2 + F_STATE]
            if not states or states[-1] != p1:
                states.append(p1)
            peak_combo = max(peak_combo, core.ram[COMBO])
            if p2 == S_DOWN:
                knockdown = True
                down_ticks += 1
            core.step()
            if (p1 == 0 and p2 == 0 and knockdown
                    and core.ram[FP2 + F_STATE] == 0):
                break

        if SHORYUKEN not in states:
            raise AssertionError(
                f"strong Shoryuken state {SHORYUKEN} never played: {states}")
        for sid in (HIT2, HIT3):
            if sid not in states:
                raise AssertionError(
                    f"Shoryuken hit slice {sid} never played: {states}")
        if peak_combo != 3:
            raise AssertionError(
                f"combo counter peaked at {peak_combo}, expected 3")
        if not knockdown:
            raise AssertionError(
                f"victim never reached the knockdown state {S_DOWN}: {states}")
        if down_ticks < 20:
            raise AssertionError(
                f"victim left the knockdown pose too quickly ({down_ticks}t)")

        damage = hp0 - core.word(FP2 + F_HP)
        if not 0 < damage <= 30:
            raise AssertionError(
                f"three-hit Shoryuken dealt {damage} damage; "
                "it must stay at the strong-special budget (<=30)")
        if core.ram[FP1 + F_STATE] or core.ram[FP2 + F_STATE]:
            raise AssertionError(
                f"fighters did not recover: p1={core.ram[FP1 + F_STATE]} "
                f"p2={core.ram[FP2 + F_STATE]}")
        print(f"PASS strong Shoryuken: states={states}, "
              f"combo={peak_combo}, knockdown={down_ticks}t, "
              f"damage={damage}", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
