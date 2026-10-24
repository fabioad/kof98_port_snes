#!/usr/bin/env python3
"""Ryo's Kohou and Robert's Ryuga must knock the opponent down.

Both the weak (pad Y / MUGEN x) and strong (pad X / MUGEN y) DP+P anti-airs
have a grounded HitDef.  That HitDef used to carry only ``air.fall = 1`` in
the strong versions, so the compiled FlagsTab lacked the knockdown bit and
the victim recovered through S_HIT instead of falling to S_DOWN.

Run after a PVSnesLib build:

    python3 tools/test_ryo_robert_antiair_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
BASE, FP2 = 0x4000, 0x40
F_STATE, F_HP = 0x8, 0x10
SPARKS, SPK_SIZE, SPK_ATTR = 0x4200, 20, 15
RIGHT, DOWN, X, Y = 7, 5, 9, 1
S_DOWN = 10

# character, pad button, expected sid, label
CASES = (
    ("ryo", Y, 52, "Kohou weak"),
    ("ryo", X, 57, "Kohou strong"),
    ("robert", Y, 50, "Ryuga weak"),
    ("robert", X, 51, "Ryuga strong"),
)


def anti_air(core, select_state, name, button, sid):
    enter_fight(core, select_state, name, "kyo")
    core.put(BASE, 80 << 8)
    core.put(BASE + FP2, 125 << 8)
    core.step(10)

    hp0 = core.word(BASE + FP2 + F_HP)
    # F, D, DF + punch
    for direction in ((RIGHT,), (DOWN,), (DOWN, RIGHT)):
        core.buttons[0] = set(direction)
        core.step(3)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()

    entered = set()
    hit = down = shot = False
    for _ in range(140):
        p1 = core.ram[BASE + F_STATE]
        p2 = core.ram[BASE + FP2 + F_STATE]
        entered.add(p1)
        # SPK_ATTR bit7 marks a live projectile; hit sparks keep it clear.
        if any(core.ram[SPARKS + i * SPK_SIZE + SPK_ATTR] & 0x80
               for i in (0, 1)):
            shot = True
        if core.word(BASE + FP2 + F_HP) < hp0:
            hit = True
        if p2 == S_DOWN:
            down = True
        core.step()

    damage = hp0 - core.word(BASE + FP2 + F_HP)
    if sid not in entered:
        raise AssertionError(
            f"{name} {button}: anti-air sid {sid} never played "
            f"(states={sorted(entered)})")
    if shot:
        raise AssertionError(
            f"{name} {button}: anti-air spawned a projectile")
    if not hit:
        raise AssertionError(f"{name} {button}: anti-air did not hit")
    if not down:
        raise AssertionError(
            f"{name} {button}: victim never entered S_DOWN ({S_DOWN})")
    return damage


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for name, button, sid, label in CASES:
            damage = anti_air(core, select_state, name, button, sid)
            print(f"PASS {label}: sid {sid}, {damage} damage, knocked down",
                  flush=True)
    finally:
        core.close()
    print("PASS: Ryo/Robert anti-airs knock the opponent down")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
