#!/usr/bin/env python3
"""Headless regression for Chun-Li's Hyakuretsu Kyaku.

The source state 1200 re-issues its HitDef on animation elements
12/16/20/24/28.  The weak 1200 clip only carries attack boxes on the first
two contacts, so the port plays the strong 1205 clip and soft-resets the hit
latch between kicks.  The engine's MoveHitFinisher then knocks the victim
down on the fifth contact, matching the rapid SNK vs Capcom Chaos sequence.

Run after a PVSnesLib build:

    python3 tools/test_chunli_hyakuretsu_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    boot_select, enter_fight, B, DOWN, LEFT,
)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1_STATE, P1_X = 0x4008, 0x4000
P2_STATE, P2_X, P2_HP = 0x4048, 0x4040, 0x4050
S_DOWN = 10


def qcb_kick(core):
    """QCB + weak kick (SNES B = MUGEN a) for a right-facing Chun-Li."""
    for direction in ((DOWN,), (DOWN, LEFT), (LEFT,)):
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = set()
    core.step(1)
    core.buttons[0] = {B}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        enter_fight(core, select, "chunli", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, 65 << 8)
        core.put(P2_X, 85 << 8)
        core.step(20)
        qcb_kick(core)

        seen, drops, down = [], [], False
        last = core.word(P2_HP)
        for _ in range(220):
            core.step()
            state = core.ram[P1_STATE]
            if not seen or seen[-1] != state:
                seen.append(state)
            hp = core.word(P2_HP)
            if hp < last:
                drops.append(last - hp)
                last = hp
            down |= core.ram[P2_STATE] == S_DOWN

        failures = []
        if 52 not in seen:
            failures.append(f"Hyakuretsu state 52 never reached: {seen}")
        if len(drops) < 5:
            failures.append(f"expected at least five contacts, got {drops}")
        if sum(drops) < 30:
            failures.append(f"multi-hit damage too low: {drops}")
        if not down:
            failures.append("victim was not knocked down")
        if failures:
            for failure in failures:
                print("FAIL:", failure)
            return 1
        print(f"Chun-Li Hyakuretsu: states={seen[:6]} hits={len(drops)} "
              f"drops={drops} knockdown={down} OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
