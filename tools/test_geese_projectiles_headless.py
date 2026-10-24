#!/usr/bin/env python3
"""Headless regression for Geese's projectiles and Raging Storm.

Checks the native ProjTab wiring introduced for Geese:
  * QCF+P (state 1000) launches a travelling ground Reppuken;
  * QCFx2+P (state 3010) launches a stationary Raging Storm shot that hits;
  * the air Shippuu Ken row advertises the per-shot torso-height flag.

Run with the built ROM:
    python3 tools/test_geese_projectiles_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402
from test_projectile_guard_headless import (             # noqa: E402
    F_STATE, F_X, HP1, SPARKS, symbols,
)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
SPK = 20
FP2 = 0x40
F_POWER = 0x4030
GROUND_Y = 190
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
LIGHT_P = 1      # SNES Y -> MUGEN x
STRONG_P = 9     # SNES X -> MUGEN y

# Native sids, not MUGEN state numbers: the engine stores the wired slot in
# F_STATE (60 = state 1000, 86 = state 3010).
S_SHOT_WEAK = 60
S_SHOT_AIR = 58
S_RAGING_STRONG = 86


def press(core, buttons, ticks=1):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def qcf(core, button):
    for direction in ({DOWN}, {DOWN, RIGHT}, {RIGHT}):
        core.buttons[0] = set(direction)
        core.step(1)
    press(core, {button}, 2)


def qcfx2(core, button):
    for _ in range(2):
        for direction in ({DOWN}, {DOWN, RIGHT}, {RIGHT}):
            core.buttons[0] = set(direction)
            core.step(1)
    press(core, {button}, 2)


def qcb(core, button):
    for direction in ({DOWN}, {DOWN, LEFT}, {LEFT}):
        core.buttons[0] = set(direction)
        core.step(1)
    press(core, {button}, 2)


def shot(core):
    """Return (slot, x, y, vx, anim, attr) for the first live hitbox."""
    for slot in (0, 1):
        base = SPARKS + slot * SPK
        anim = core.word(base + 4)
        if anim and core.ram[base + 15] & 0x80:
            return (slot, core.word(base), core.word(base + 2),
                    core.word(base + 8), anim, core.ram[base + 15])
    return None


def wait_state(core, wanted, label, limit=240):
    seen = set()
    for _ in range(limit):
        state = core.ram[F_STATE]
        seen.add(state)
        if state == wanted:
            return
        core.step()
    raise AssertionError(f"{label}: state {sorted(seen)}, wanted {wanted}")


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "geese", "kyo")
        core.put(F_X, 60 << 8)
        core.put(F_X + FP2, 200 << 8)
        core.put(HP1, 336)
        core.put(HP1 + FP2, 336)
        core.put(F_POWER, 3000)
        core.step(20)
        baseline = core.save()

        # Reppuken: a real travelling wave, not the old root HitDef-only move.
        core.load(baseline)
        qcf(core, LIGHT_P)
        wait_state(core, S_SHOT_WEAK, "Reppuken state")
        fired = None
        for _ in range(12):
            fired = shot(core)
            if fired:
                break
            core.step()
        assert fired, "Reppuken did not spawn a projectile"
        _slot, _x, y, vx, _anim, _attr = fired
        # Reppuken is a floor wave: the ProjTab height fix must keep mode 1
        # (GROUND_Y) and never lift it to the hadouken torso row.
        assert y == GROUND_Y, f"Reppuken y={y}, wanted {GROUND_Y}"
        assert vx == 0x0300, f"Reppuken vx={vx:#06x}, wanted $0300"
        hp0 = core.word(HP1 + FP2)
        for _ in range(120):
            if core.word(HP1 + FP2) < hp0:
                break
            core.step()
        hp1 = core.word(HP1 + FP2)
        assert hp1 < hp0, f"Reppuken did not connect (hp {hp0}->{hp1})"
        print(f"OK Geese Reppuken: vx=$0300, hp {hp0}->{hp1}")

        # Raging Storm spawn: keep the victim far so the stationary row stays
        # alive long enough to inspect it.
        core.load(baseline)
        core.put(F_X + FP2, 200 << 8)
        core.step(4)
        qcfx2(core, STRONG_P)
        wait_state(core, S_RAGING_STRONG, "Raging Storm state", limit=300)
        fired = None
        for _ in range(40):
            fired = shot(core)
            if fired:
                break
            core.step()
        assert fired, "Raging Storm did not spawn a stationary projectile"
        _slot, _x, _y, vx, _anim, _attr = fired
        assert vx == 0, f"Raging Storm vx={vx:#06x}, wanted stationary"
        print("OK Geese Raging Storm: stationary shot spawned")

        # Raging Storm hit: put the victim inside the stationary shot's reach.
        core.load(baseline)
        core.put(F_X + FP2, 90 << 8)
        core.put(HP1 + FP2, 336)
        core.step(4)
        qcfx2(core, STRONG_P)
        wait_state(core, S_RAGING_STRONG, "Raging Storm state", limit=300)
        hp0 = core.word(HP1 + FP2)
        for _ in range(90):
            if core.word(HP1 + FP2) < hp0:
                break
            core.step()
        hp1 = core.word(HP1 + FP2)
        assert hp1 < hp0, f"Raging Storm did not connect (hp {hp0}->{hp1})"
        print(f"OK Geese Raging Storm: hp {hp0}->{hp1}")

        # Air Shippuu Ken: the per-shot torso flag must keep the shot at a
        # fixed upper-torso height instead of the character's ground row.
        core.load(baseline)
        core.put(F_X + FP2, 200 << 8)
        core.step(4)
        core.buttons[0] = {UP}
        core.step(2)
        core.buttons[0] = set()
        core.step(10)
        qcb(core, LIGHT_P)
        wait_state(core, S_SHOT_AIR, "Shippuu Ken state")
        fired = None
        for _ in range(20):
            fired = shot(core)
            if fired:
                break
            core.step()
        assert fired, "Shippuu Ken did not spawn a projectile"
        _slot, _x, y, vx, _anim, _attr = fired
        assert y == GROUND_Y - 60, f"Shippuu Ken y={y}, wanted {GROUND_Y - 60}"
        assert vx == 0x0700, f"Shippuu Ken vx={vx:#06x}, wanted $0700"
        print(f"OK Geese Shippuu Ken: y={y}, vx=$0700")

        # Static table check for the air Shippuu Ken height flag.  This guards
        # the build bit so a later table edit cannot silently lose it.
        tab = symbols()["geeseProjTab"]
        # ExHiROM: banks $C0+ live in the lower 4 MiB of the file.
        offset = tab - 0xC00000 if tab >= 0xC00000 else tab
        rom = (ROOT / "kof98-snes.sfc").read_bytes()
        row = rom[offset + 58 * 6:offset + 58 * 6 + 6]
        assert row[5] & 0x02, f"Shippuu Ken ProjTab present=${row[5]:02X}"
        print(f"OK Geese Shippuu Ken: torso-height flag present=${row[5]:02X}")
    finally:
        core.close()


if __name__ == "__main__":
    main()
