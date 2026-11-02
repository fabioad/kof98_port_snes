#!/usr/bin/env python3
"""Regression: Geese's Raging Storm matches the KOF98 arcade move.

KOF98's Raging Storm is a single-hit, untechable anti-air pillar in front of
Geese: it hits airborne opponents, is blockable (chip only), costs 1000
meter, and must not use the engine's generic five-contact super projectile.

Run after a PVSnesLib build:

    python3 tools/test_geese_raging_storm_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import enter_fight, tap, wait  # noqa: E402
from test_geese_projectiles_headless import (             # noqa: E402
    CORE, F_POWER, FP2, HP1, F_STATE, S_RAGING_STRONG,
    STRONG_P, RIGHT, UP, qcfx2, wait_state,
)

GS = 0x1020
START = 3
DOWN_STATE = 10
GUARD_STATES = {27, 28, 30, 31, 79, 81}


def boot_select(core):
    """Skip the MSU opening (gs14) and stop on the character select."""
    wait(core, lambda: core.word(GS) == 14, "msu opening", 4000)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(60)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    core.ram[0xF070] = 1                       # SINGLE VS
    tap(core, START)
    wait(core, lambda: core.word(GS) == 5, "select")
    core.ram[0x1091] = 0
    core.step(10)
    return core.save()


def start(core, select_state, p2x=140):
    enter_fight(core, select_state, "geese", "kyo")
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.put(0x4000, 60 << 8)
    core.put(0x4040, p2x << 8)
    core.put(0x4010, 336)
    core.put(0x4050, 336)
    core.put(F_POWER, 3000)
    core.step(20)
    hp0 = core.word(HP1 + FP2)
    qcfx2(core, STRONG_P)
    wait_state(core, S_RAGING_STRONG, "Raging Storm state", limit=300)
    return hp0


def collect(core, frames=120, hold=None, start_jump=False):
    if start_jump:
        core.buttons[1] = {UP}
        core.step(2)
        core.buttons[1] = set()
    hp0 = core.word(HP1 + FP2)
    drops = []
    last = hp0
    down = guard = air = False
    for _ in range(frames):
        if hold:
            core.buttons[1] = set(hold)
        core.step()
        hp = core.word(HP1 + FP2)
        if hp < last:
            drops.append(last - hp)
            last = hp
        state = core.ram[F_STATE + FP2]
        down |= state == DOWN_STATE
        guard |= state in GUARD_STATES
        air |= core.word(HP1 + FP2 - 0x10) != 0
    core.buttons[1] = set()
    return hp0 - last, drops, down, guard, air


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        fails = []

        # Ground: exactly one 38-damage hit, untechable knockdown.
        start(core, select)
        loss, drops, down, guard, _ = collect(core)
        if drops != [38] or not down or guard:
            fails.append(f"ground: drops={drops} down={down} guard={guard}")

        # Block: guard stance, chip only, no knockdown, meter still paid.
        start(core, select)
        loss, drops, down, guard, _ = collect(core, hold=(RIGHT,))
        if not guard or down or not (0 < loss <= 4):
            fails.append(
                f"block: guard={guard} down={down} loss={loss}")
        if core.word(F_POWER) != 2000:
            fails.append(f"block meter={core.word(F_POWER)}, wanted 2000")

        # Air: the tall pillar must catch a jump (KOF98 anti-air).
        start(core, select)
        loss, drops, down, guard, air = collect(core, start_jump=True)
        if not air or loss != 38 or not down:
            fails.append(
                f"air: airborne={air} loss={loss} down={down}")

        if fails:
            for failure in fails:
                print("FAIL:", failure)
            return 1
        print("Geese Raging Storm: 1 hit / 38 dmg / knockdown, "
              "blockable chip, anti-air OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
