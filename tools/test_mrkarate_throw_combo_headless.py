#!/usr/bin/env python3
"""Mr. Karate's close throw becomes a 15-hit Hien Shippuu Kyaku.

The throw's normal -40 HP row is replaced by the Hien Shippuu Kyaku contact
sequence: 15 real impacts using the same 40-HP budget, and the victim is
launched only after the last hit.  Run after a PVSnesLib build.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (boot_select, enter_fight,   # noqa: E402
                                        HIDDEN)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_X, F_HP, F_Y = 0x4008, 0x4000, 0x4010, 0x4002
FP2 = 0x40
MKC_HITS, MKC_ACTIVE, MKC_THROW = 0xF1D9, 0xF1D0, 0xF1DE
X, Y, RIGHT = 9, 1, 7


def main():
    HIDDEN["mrkarate"] = {10, 11}
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "mrkarate", "iori")
        core.put(F_X, 150 << 8)
        core.put(F_X + FP2, 174 << 8)
        core.step(20)

        before = core.word(F_HP + FP2)
        core.buttons[0] = {X, Y}                # port's standard close throw
        max_hits = 0
        max_y = 0
        saw_combo = False
        saw_throw = False
        for i in range(180):
            core.step()
            if i == 4:
                core.buttons[0] = set()
            if core.ram[MKC_THROW]:
                saw_throw = True
            max_hits = max(max_hits, core.ram[MKC_HITS])
            if core.ram[MKC_ACTIVE]:
                saw_combo = True
            max_y = max(max_y, core.word(F_Y + FP2))
            if i > 100 and max_hits >= 15 and core.ram[F_STATE + FP2] in (0, 10, 18):
                break

        after = core.word(F_HP + FP2)
        assert saw_throw, "the throw never reached the combo hook"
        assert saw_combo, "the Hien Shippuu Kyaku contact sequence never started"
        assert max_hits == 15, f"expected 15 impacts, got {max_hits}"
        assert before - after == 41, f"throw budget {before}->{after}, want 41"
        assert max_y > 0, "victim was never launched after the combo"
        atk = core.ram[F_STATE]
        assert atk in (0, 10, 18), f"attacker stuck in state {atk}"
        print(f"PASS Mr. Karate throw: {max_hits} Hien Shippuu impacts, "
              f"{before - after} HP (standard throw budget), launch after combo")
    finally:
        core.close()


if __name__ == "__main__":
    main()
