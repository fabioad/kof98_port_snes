#!/usr/bin/env python3
"""Headless regression for Krauser's Kaiser Wave super.

The three wired supers reuse the small Blitz Ball projectile art:
  * QCF + x     -> state 3050 / sid 85, 26 dmg
  * QCF + y     -> state 3060 / sid 86, 30 dmg
  * QCF + x+y   -> state 3070 / sid 88, MAX/quick-SDM, 34 dmg

Run with the built ROM:
    python3 tools/test_krauser_kaiser_wave_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
SPK = 20
FP2 = 0x40
F_STATE = 0x4008
F_X = 0x4000
HP1 = 0x4010
F_POWER = 0x4030
SPARKS = 0x4200
DOWN, RIGHT = 5, 7
LIGHT_P = 1      # SNES Y -> MUGEN x
STRONG_P = 9     # SNES X -> MUGEN y
BOTH_P = {LIGHT_P, STRONG_P}

# sid -> (buttons, vx, damage, guard, power left)
CASES = (
    (85, {LIGHT_P}, 0x0400, 26, 0x20, 2000),
    (86, {STRONG_P}, 0x0400, 30, 0x20, 2000),
    (88, BOTH_P, 0x0C00, 34, 0xA0, 0),
)


def press(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def qcf(core, button):
    for direction in ({DOWN}, {DOWN, RIGHT}, {RIGHT}):
        core.buttons[0] = set(direction)
        core.step(1)
    press(core, button)


def shot(core):
    for slot in (0, 1):
        base = SPARKS + slot * SPK
        if core.word(base + 4) and core.ram[base + 15] & 0x80:
            return (core.word(base + 8), core.ram[base + 12],
                    core.ram[base + 18])
    return None


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "krauser", "kyo")
        core.put(F_X, 60 << 8)
        core.put(F_X + FP2, 120 << 8)
        core.put(HP1, 200)
        core.put(HP1 + FP2, 200)
        core.put(F_POWER, 3000)
        core.step(20)
        baseline = core.save()

        for sid, button, want_vx, want_dmg, want_guard, want_power in CASES:
            core.load(baseline)
            core.buttons[0] = set()
            core.step(6)
            qcf(core, button)
            state = None
            fired = None
            for _ in range(60):
                state = core.ram[F_STATE]
                fired = shot(core)
                if state == sid and fired:
                    break
                core.step()
            assert state == sid, f"sid {sid}: state {state}"
            assert fired, f"sid {sid}: no projectile"
            vx, dmg, guard = fired
            assert (vx, dmg, guard) == (want_vx, want_dmg, want_guard), (
                f"sid {sid}: vx={vx:#06x} dmg={dmg} guard=${guard:02X}")
            hp0 = core.word(HP1 + FP2)
            for _ in range(120):
                if core.word(HP1 + FP2) < hp0:
                    break
                core.step()
            hp1 = core.word(HP1 + FP2)
            assert hp0 - hp1 == want_dmg, (
                f"sid {sid}: hp {hp0}->{hp1}, wanted -{want_dmg}")
            assert core.word(F_POWER) == want_power, (
                f"sid {sid}: power {core.word(F_POWER)}, wanted {want_power}")
            print(f"OK Kaiser Wave sid {sid}: vx=${want_vx:04X}, "
                  f"dmg={want_dmg}, power={want_power}")
    finally:
        core.close()


if __name__ == "__main__":
    main()
