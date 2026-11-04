#!/usr/bin/env python3
"""Headless regression for Chizuru's DP (anti-air).

The source DP (state 1200) only summons a clone; the rise/attack lives in
helper state 1100.  The port maps sid 52 to a shortened native clip (AIR
13000) with an explicit rise velocity and HitDef.  This test checks that the
body actually rises, the hit connects/knocks down, and the move recovers.

The input profile maps MUGEN x to SNES Y (libretro button 1); the DP is
F, D, DF, then the button (not DF+button simultaneously, which is a crouch
normal).

Run after a PVSnesLib build:

    python3 tools/test_chizuru_dp_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
B = 0x4000
F_STATE, F_Y, F_VY = B + 8, B + 2, B + 6
F_HP2 = B + 0x50
F_STATE2 = B + 0x48
FP2 = 0x40
R, D, DF, Y = 7, 5, (5, 7), 1
DP_STATE = 52


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "chizuru", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(B + 0, 80 << 8)
        core.put(B + FP2, 110 << 8)
        core.put(B + 0x10, 200)
        core.put(F_HP2, 200)
        core.step(30)

        for direction in (R, D, DF):
            core.buttons[0] = (set(direction)
                               if isinstance(direction, tuple) else {direction})
            core.step(3)
        core.buttons[0] = {Y}
        core.step(3)
        core.buttons[0] = set()

        seen = False
        peak = 0
        hit = False
        knockdown = False
        for _ in range(180):
            core.step()
            if core.ram[F_STATE] == DP_STATE:
                seen = True
            peak = max(peak, core.word(F_Y))
            if core.word(F_HP2) < 200:
                hit = True
            if core.ram[F_STATE2] in (9, 10, 18, 19):
                knockdown = True
            if seen and core.ram[F_STATE] == 0:
                break
        assert seen, "DP state 52 was never entered"
        assert peak > 40 << 8, (
            f"DP did not rise: peak height {peak / 256:.1f} px")
        assert hit, f"DP did not hit: P2 HP {core.word(F_HP2)}"
        assert knockdown, f"DP did not knock the victim down: state {core.ram[F_STATE2]}"
        assert core.ram[F_STATE] == 0, (
            f"DP did not recover: state {core.ram[F_STATE]}")
        print(
            "PASS Chizuru DP: peak %.0f px, P2 HP %d, knockdown, recovered"
            % (peak / 256.0, core.word(F_HP2)))
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, str(args.rom))
