#!/usr/bin/env python3
"""Headless regression for Chun-Li's Hyakuretsu Kyaku (rapid kick, B x N).

The command is the rapid B press (cmd_extra, three presses within 50 ticks)
and it plays runtime state 57 (source 1100/1105), distinct from the Spinning
Bird Kick (state 52).  The five kick cels re-arm their HitDef on animation
elements, so the port soft-resets the hit latch between kicks
(hit_soft_resets[1100]) and the engine's MoveHitFinisher knocks the victim
down on the fifth contact only.  The state must not carry a step-in latch
(tools/build_fight.py POST_CAL_VEL): that flag became the air-blow knockdown
bit, so the first kick used to drop the victim and the other four whiffed.

Run after a PVSnesLib build:

    python3 tools/test_chunli_hyakuretsu_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    boot_select, enter_fight, B,
)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1_STATE, P1_X = 0x4008, 0x4000
P2_STATE, P2_X, P2_HP = 0x4048, 0x4040, 0x4050
S_HIT, S_DOWN = 9, 10


def rapid_kick(core, tick, taps=6, hold=2, gap=4):
    for _ in range(taps):
        core.buttons[0] = {B}
        for _ in range(hold):
            core.step()
            tick()
        core.buttons[0] = set()
        for _ in range(gap):
            core.step()
            tick()
    core.buttons[0] = set()


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        enter_fight(core, select, "chunli", "sakura")
        core.put(P1_X, 80 << 8)
        core.put(P2_X, 98 << 8)
        core.put(P2_HP, 300)
        core.step(20)

        seen, drops, stuns, downs = [], [], [0], []
        last = [core.word(P2_HP)]

        def tick():
            state = core.ram[P1_STATE]
            if not seen or seen[-1] != state:
                seen.append(state)
            hp = core.word(P2_HP)
            if hp < last[0]:
                drops.append(last[0] - hp)
                last[0] = hp
            victim = core.ram[P2_STATE]
            if victim == S_HIT:
                stuns[0] += 1
            if victim == S_DOWN:
                downs.append(len(seen))

        rapid_kick(core, tick)
        for _ in range(160):
            core.step()
            tick()

        failures = []
        if 57 not in seen:
            failures.append(f"rapid-kick state 57 never reached: {seen}")
        if len(drops) < 5:
            failures.append(f"expected five contacts, got {drops}")
        if sum(drops) < 30:
            failures.append(f"multi-hit damage too low: {drops}")
        if stuns[0] < 20:
            failures.append(
                f"victim barely stayed in hitstun ({stuns[0]} ticks)")
        # a knockdown before the fifth contact means the flurry whiffed
        if downs and len(drops) < 5:
            failures.append(
                f"victim knocked down before five contacts ({drops})")
        if not downs:
            failures.append("victim was not knocked down")
        if failures:
            for failure in failures:
                print("FAIL:", failure)
            return 1
        print(f"Chun-Li Hyakuretsu: states={seen[:4]} hits={len(drops)} "
              f"drops={drops} hitstun={stuns[0]} knockdown=True OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
