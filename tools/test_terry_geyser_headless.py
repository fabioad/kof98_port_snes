#!/usr/bin/env python3
"""Power Geyser is a hitbox-only move now.

The spark object must still exist so the tall column hits and the ProjTab
damage/guard applies, but Terry's alternate geyser clip must contain a
zero-cell frame so DrawSparks draws nothing.

Run after a PVSnesLib build:

    python3 tools/test_terry_geyser_headless.py
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                          # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
FP1, FP2 = 0x4000, 0x4040
F_STATE = 8
HP2 = FP2 + 0x10
POW1 = FP1 + 0x30
SPARKS = 0x4200
SPK_SIZE = 20
DOWN, RIGHT, LEFT = 5, 7, 6
D = frozenset({DOWN})
B = frozenset({LEFT})
F = frozenset({RIGHT})
WEAK, STRONG = 1, 9


def feed(core, buttons):
    for direction in (D, B, F):
        core.buttons[0] = set(direction)
        core.step(3)
    core.buttons[0] = ({buttons} if isinstance(buttons, int)
                       else set(buttons))
    core.step(3)
    core.buttons[0] = set()


def run(buttons, expected_state, expected_damage, expected_power):
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "terry", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(FP1, 100 << 8)
        core.put(FP2, 130 << 8)
        core.put(HP2, 200)
        core.put(POW1, 3000)
        core.step(30)
        feed(core, buttons)

        states = []
        hp_min = 200
        power_min = 3000
        shots = 0
        tall = False
        for tick in range(180):
            core.step()
            state = core.ram[FP1 + F_STATE]
            if not states or states[-1] != state:
                states.append(state)
            hp_min = min(hp_min, core.word(HP2))
            power_min = min(power_min, core.word(POW1))
            for slot in range(2):
                base = SPARKS + slot * SPK_SIZE
                if core.ram[base + 4] or core.ram[base + 5]:
                    shots += 1
                    if core.ram[base + 18] & 0x01:
                        tall = True
            if state == 0 and len(states) > 1 and tick > 20:
                break
    finally:
        core.close()
    damage = 200 - hp_min
    assert expected_state in states, (
        f"geyser state {expected_state} missing: {states}")
    assert damage == expected_damage, (
        f"geyser damage {damage}, want {expected_damage}")
    assert power_min == expected_power, (
        f"geyser power {power_min}, want {expected_power}")
    assert shots > 0, "geyser spark/hitbox never existed"
    assert tall, "geyser hitbox lost its tall SPK_GRD column"
    return states, damage


def check_invisible_clip():
    meta = (ROOT / "build/gen_fight/projectiles_meta.inc").read_text()
    m = re.search(r"terryProjFx2F0:\s*\.db\s+1,0\b", meta)
    assert m, (
        "terryProjFx2F0 should have ticks=1, ncells=0 (invisible geyser)")
    print("PASS Power Geyser: alternate clip has zero drawable cells")


def main(core_path, rom):
    global CORE, ROM
    CORE = core_path
    ROM = rom
    check_invisible_clip()
    for tag, buttons, state, damage, power in (
            ("weak", WEAK, 85, 25, 2000),
            ("strong", STRONG, 86, 30, 2000),
            ("MAX", {WEAK, STRONG}, 87, 50, 0)):
        states, got = run(buttons, state, damage, power)
        print(f"PASS Power Geyser {tag}: {got} HP, states={states[:4]}, "
              f"power {power}")
    print("PASS Power Geyser: hitbox active, no drawn projectile")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
