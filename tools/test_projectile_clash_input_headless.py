#!/usr/bin/env python3
"""Real-input projectile-clash regression.

`test_projectile_clash_headless.py` injects spark slots directly.  This
test goes through the normal command path: both fighters fire a real
projectile, the shots travel, and the engine must free both at contact
without touching either fighter.  A lone shot must still hit.

Run after a PVSnesLib build:

    python3 tools/test_projectile_clash_input_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
F_HP = 0x4010
F_X = 0x4000
FP2 = 0x40
SPARKS = 0x4200
SPK_SIZE = 20
SPK_ANIM = 4
SPK_ATTR = 15

DOWN, LEFT, RIGHT = 5, 6, 7
WEAK_P = 1                                   # SNES Y -> MUGEN x


def qcf(core, side, button):
    """QCF+button; side 0 faces right, side 1 faces left."""
    dirs = (({DOWN}, {DOWN, RIGHT}, {RIGHT}) if side == 0
            else ({DOWN}, {DOWN, LEFT}, {LEFT}))
    for d in dirs:
        core.buttons[side] = set(d)
        core.step(3)
    core.buttons[side] = {button}
    core.step(3)
    core.buttons[side] = set()


def slot(core, index):
    base = SPARKS + index * SPK_SIZE
    return core.word(base + SPK_ANIM), core.ram[base + SPK_ATTR]


def run(both):
    core = Core(CORE, ROM)
    try:
        select = boot_select(core)
        enter_fight(core, select, "iori", "iori")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(F_X, 60 << 8)
        core.put(F_X + FP2, 200 << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.step(30)
        core.put(F_X, 60 << 8)
        core.put(F_X + FP2, 200 << 8)
        hp1 = core.word(F_HP)
        hp2 = core.word(F_HP + FP2)

        qcf(core, 0, WEAK_P)
        if both:
            qcf(core, 1, WEAK_P)

        both_live = False
        clash = False
        max_dmg1 = max_dmg2 = 0
        for _ in range(120):
            core.step()
            a0, at0 = slot(core, 0)
            a1, at1 = slot(core, 1)
            live0 = bool(a0) and bool(at0 & 0x80)
            live1 = bool(a1) and bool(at1 & 0x80)
            if live0 and live1:
                both_live = True
            if both_live and not live0 and not live1:
                if core.word(F_HP + FP2) == hp2:
                    clash = True
            max_dmg1 = max(max_dmg1, hp1 - core.word(F_HP))
            max_dmg2 = max(max_dmg2, hp2 - core.word(F_HP + FP2))
        return both_live, clash, max_dmg1, max_dmg2
    finally:
        core.close()


def main():
    both_live, clash, dmg1, dmg2 = run(both=True)
    assert both_live, "the two shots never coexisted in the two slots"
    assert clash, "opposing projectiles did not cancel each other"
    assert dmg1 == 0 and dmg2 == 0, (
        f"a cancelled projectile still dealt damage ({dmg1}/{dmg2})")

    both_live, _clash, _dmg1, dmg2 = run(both=False)
    assert not both_live, "one shot occupied both slots"
    assert dmg2 > 0, "a lone projectile no longer hits the opponent"

    print("PASS projectile clash (real input): both vanish, lone shot hits")


if __name__ == "__main__":
    main()
