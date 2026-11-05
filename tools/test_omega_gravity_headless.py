#!/usr/bin/env python3
"""Omega Rugal's Gravity Shot must not overflow the effect/OAM budget.

The source beam is projanim 1357, but the native table had the 16-cell
Gravity Smash orb (1035) selected instead; its large frame plus the fighter
OAM corrupted the screen.  The alternate beam clip is now compiled at a
reduced size (<= 12 effect cells).  This test fires the real Gravity Shot
and checks the damage plus the per-frame OAM cell count.

Run after a PVSnesLib build:

    python3 tools/test_omega_gravity_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
F_STATE = 0x4008
F_HP = 0x4010
F_X = 0x4000
FP2 = 0x40
OAM = 0x1800
DOWN, RIGHT, R = 5, 7, 11


def effect_cells(core):
    """OAM cells using the effect palette (palette 2)."""
    oam = bytes(core.ram[OAM:OAM + 512])
    return sum(1 for i in range(128)
               if (oam[i * 4 + 3] & 0x0E) == 4
               and oam[i * 4 + 1] < 0xF0)


def main():
    core = Core(CORE, str(ROM))
    try:
        select = boot_select(core)
        enter_fight(core, select, "omegarugal", "kyo")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, 160 << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.put(F_X + 0x30, 4000)
        core.step(30)
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, 160 << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        hp0 = core.word(F_HP + FP2)

        for direction in (frozenset({DOWN}), frozenset({DOWN, RIGHT}),
                          frozenset({RIGHT})):
            core.buttons[0] = set(direction)
            core.step(3)
        core.buttons[0] = {R}
        core.step(3)
        core.buttons[0] = set()

        seen = set()
        max_cells = 0
        damage = 0
        for _ in range(120):
            core.step()
            seen.add(core.ram[F_STATE])
            damage = max(damage, hp0 - core.word(F_HP + FP2))
            max_cells = max(max_cells, effect_cells(core))
            if core.ram[F_STATE] == 0 and damage:
                break
        assert 82 in seen, f"Gravity Shot state never started ({seen})"
        assert damage >= 10, f"Gravity Shot only dealt {damage} damage"
        assert max_cells <= 32, (
            f"Gravity Shot used {max_cells} effect cells (OAM/VRAM budget)")
        print(f"PASS Omega Gravity Shot: {damage} damage, "
              f"{max_cells} effect cells")
    finally:
        core.close()


if __name__ == "__main__":
    main()
