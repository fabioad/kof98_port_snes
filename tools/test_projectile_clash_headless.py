#!/usr/bin/env python3
"""Headless projectile-clash regression.

Two opposing projectiles that overlap must both leave the spark pool without
touching either fighter.  Same-side shots and cosmetic sparks must not
trigger the clash.

Run with the built ROM:
    python3 tools/test_projectile_clash_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_projectile_guard_headless import (             # noqa: E402
    F_X, HP1, SPARKS, enter_match, symbols,
)
from test_roster import parse_tables                     # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP2 = 0x40
SPK = 20
PROJ_ANIM = 4
PROJ_ATTR = 15
PROJ_BANK = 16


def put_slot(core, syms, slot, x, y, vx, attr):
    base = SPARKS + slot * SPK
    core.put(base + 0, x & 0xFFFF)
    core.put(base + 2, y & 0xFFFF)
    core.put(base + PROJ_ANIM, syms["ryuProjFxAnim"] & 0xFFFF)
    core.ram[base + 6] = 0                   # frame index
    core.ram[base + 7] = 2                   # frame ticks
    core.put(base + 8, vx & 0xFFFF)
    core.put(base + 10, 0)
    core.put(base + 12, 0)
    core.ram[base + 14] = 80                 # TTL
    core.ram[base + PROJ_ATTR] = attr
    core.ram[base + PROJ_BANK] = 117         # Ryu projectile data bank


def anim(core, slot):
    return core.word(SPARKS + slot * SPK + PROJ_ANIM)


def main(core_path, rom):
    roster = {v["name"]: {**v, "id": i}
              for i, v in parse_tables().items()}
    syms = symbols()
    core = Core(core_path, rom)
    try:
        enter_match(core, roster, "kyo", "ryu")
        baseline = core.save()

        def prepare():
            core.load(baseline)
            core.put(F_X, 60 << 8)
            core.put(F_X + FP2, 220 << 8)
            core.put(HP1, 336)
            core.put(HP1 + FP2, 336)
            core.step(2)

        # Opposing shots fired toward each other: both vanish at contact.
        prepare()
        put_slot(core, syms, 0, 120, 150, 4 * 256, 0x80)    # P1
        put_slot(core, syms, 1, 160, 150, -4 * 256, 0xC0)   # P2
        for _ in range(20):
            core.step()
            if not anim(core, 0) and not anim(core, 1):
                break
        else:
            raise AssertionError("opposing projectiles never clashed")
        assert core.word(HP1) == 336 and core.word(HP1 + FP2) == 336, (
            "projectile clash damaged a fighter")

        # Same owner: the shots pass through each other.
        prepare()
        put_slot(core, syms, 0, 120, 150, 4 * 256, 0x80)
        put_slot(core, syms, 1, 160, 150, -4 * 256, 0x80)
        for _ in range(6):
            core.step()
        assert anim(core, 0) and anim(core, 1), (
            "same-side projectiles must not cancel")

        # A cosmetic spark in the other slot must not consume a projectile.
        prepare()
        put_slot(core, syms, 0, 120, 150, 4 * 256, 0x80)
        put_slot(core, syms, 1, 122, 150, 0, 0x30)
        start_x = core.word(SPARKS)
        core.step(2)
        assert anim(core, 0), "cosmetic spark cancelled a projectile"
        assert core.word(SPARKS) > start_x, "projectile stopped after a spark"

        print("PASS projectile clash: opposing shots vanish, allies pass")
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, args.rom)
