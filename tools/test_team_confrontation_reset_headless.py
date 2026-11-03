#!/usr/bin/env python3
"""Headless regression: a new Team Play confrontation must fully reset.

Winning a trio leaves T_SWAP set from the last member KO.  StartFight used
to take the partial TeamSwap path on the next confrontation, keeping the
survivor's low HP/position, so the player's life bar started only partly
filled.  CampNext/CampResolve now clear T_SWAP and the next trio starts at
full health.

Run after a PVSnesLib build:

    python3 tools/test_team_confrontation_reset_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from capture_pair_headless import wait                    # noqa: E402
from test_midfight_join_headless import (start_team, GS, CPU1, CPU2)  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_HP, F_POWER, F_X = 0x4010, 0x4030, 0x4000
FP2 = 0x40
C_IDX = 0x10C1
T_SWAP = 0x10D1
MAXHP = 200


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        start_team(core)
        core.ram[CPU1] = 0
        core.ram[CPU2] = 0
        core.step(30)
        core.put(F_HP, 40)                 # survivor starts badly hurt
        core.put(F_POWER, 3000)            # and with a full meter
        core.step(5)
        for member in range(3):
            core.put(F_HP + FP2, 0)
            wait(core, lambda: core.word(GS) == 2, "ko", 600)
            wait(core, lambda: core.word(GS) == 1, "next fight", 8000)
            core.step(30)
            if member < 2:
                # Member swaps keep the survivor's HP (with TeamRecover).
                continue
            assert core.ram[C_IDX] == 1, \
                f"new confrontation not reached: C_IDX={core.ram[C_IDX]}"
            assert core.ram[T_SWAP] == 0, \
                f"stale T_SWAP={core.ram[T_SWAP]} leaked into the new trio"
            assert core.word(F_HP) == MAXHP, (
                "player life was not restored for the next trio: "
                f"HP={core.word(F_HP)}")
            assert core.word(F_HP + FP2) == MAXHP
            assert core.word(F_X) == 80 << 8, (
                f"player did not spawn at home: x={core.word(F_X) / 256:.1f}")
            assert core.word(F_POWER) == 3000, (
                "power meter should carry into the next confrontation: "
                f"{core.word(F_POWER)}")
        print("PASS Team Play: next trio starts at full HP, T_SWAP cleared")
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, str(args.rom))
