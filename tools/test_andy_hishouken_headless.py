#!/usr/bin/env python3
"""Headless regression for Andy's QCB+P Hishou Ken.

States 1100/1110 (sids 52/53) spawn helper 1105, a short-range palm burst
with the HitDef.  The old port wired only the QCF+c back version (sid 58),
so QCB+P played the windup with no projectile and no hitbox.

The front shot is stationary at 80 px (the source Clsn1 centre), has a 48 px
horizontal radius (source Clsn1 x=32..127) and lives for 12 ticks.  The
QCF+c back shot (sid 58) keeps its travelling 4 px/tick projectile.

Run after a PVSnesLib build:

    python3 tools/test_andy_hishouken_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                 # noqa: E402
    boot_select, enter_fight)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_X, F_HP = 0x4008, 0x4000, 0x4010
FP2 = 0x40
SPK, SPK_SIZE = 0x4200, 20
B, Y, X, L = 0, 1, 9, 10
DOWN, LEFT, RIGHT = 5, 6, 7
S_HIT = 9
QCB_RIGHT = ((DOWN,), (DOWN, LEFT), (LEFT,))
QCB_LEFT = ((DOWN,), (DOWN, RIGHT), (RIGHT,))
QCF_RIGHT = ((DOWN,), (DOWN, RIGHT), (RIGHT,))


def press(core, port, buttons, frames=3):
    core.buttons[port] = set(buttons)
    core.step(frames)
    core.buttons[port] = set()


def motion(core, port, seq, button):
    for direction in seq:
        core.buttons[port] = set(direction)
        core.step(2)
    core.step(1)
    press(core, port, {button}, 3)


def projectile(core, owner_p2):
    for slot in (0, 1):
        base = SPK + slot * SPK_SIZE
        attr = core.ram[base + 15]
        if core.word(base + 4) and (attr & 0x80):
            if bool(attr & 0x40) == owner_p2:
                return base
    return None


def hit_case(core, select_state, label, andy_side, seq, button, victim_x,
             stance_sid, expected_damage):
    if andy_side == 1:
        p1, p2 = "andy", "kyo"
        victim_state, victim_hp = F_STATE + FP2, F_HP + FP2
    else:
        p1, p2 = "kyo", "andy"
        victim_state, victim_hp = F_STATE, F_HP
    enter_fight(core, select_state, p1, p2)
    if andy_side == 1:
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, victim_x << 8)
    else:
        core.put(F_X, victim_x << 8)
        core.put(F_X + FP2, 100 << 8)
    core.step(20)
    hp0 = core.word(victim_hp)
    motion(core, andy_side - 1, seq, button)
    if core.ram[F_STATE + (andy_side - 1) * FP2] != stance_sid:
        raise AssertionError(
            f"{label}: stance {core.ram[F_STATE + (andy_side - 1) * FP2]} "
            f"!= {stance_sid}")
    for _ in range(140):
        if core.ram[victim_state] == S_HIT:
            damage = hp0 - core.word(victim_hp)
            if damage >= expected_damage - 1:
                print(f"PASS {label}: {damage} damage", flush=True)
                return
        core.step()
    raise AssertionError(
        f"{label}: no hit (victim state {core.ram[victim_state]}, "
        f"hp {hp0}->{core.word(victim_hp)})")


def whiff_case(core, select_state):
    enter_fight(core, select_state, "andy", "kyo")
    core.put(F_X, 100 << 8)
    core.put(F_X + FP2, 240 << 8)
    core.step(20)
    hp0 = core.word(F_HP + FP2)
    motion(core, 0, QCB_RIGHT, Y)
    seen = None
    first_ttl = None
    for frame in range(80):
        base = projectile(core, False)
        if base is not None and seen is None:
            seen = frame
            first_ttl = core.ram[base + 14]
            x, vx = core.word(base), core.word(base + 8)
            if not 170 <= x <= 190:
                raise AssertionError(f"p1-whiff: burst at x={x}, expected ~180")
            if vx != 0:
                raise AssertionError(f"p1-whiff: burst moves vx={vx}")
            if first_ttl > 12:
                raise AssertionError(f"p1-whiff: TTL {first_ttl}, expected <=12")
        if seen is not None and base is None and frame > seen + 10:
            break
        core.step()
    if seen is None:
        raise AssertionError("p1-whiff: QCB+P did not spawn any projectile")
    if core.word(F_HP + FP2) != hp0:
        raise AssertionError("p1-whiff: far victim took damage")
    print("PASS p1-whiff: short-range burst spawned, stayed put, expired",
          flush=True)


def back_case(core, select_state):
    enter_fight(core, select_state, "andy", "kyo")
    core.put(F_X, 100 << 8)
    core.put(F_X + FP2, 180 << 8)
    core.step(20)
    hp0 = core.word(F_HP + FP2)
    # QCF + c (back Hishou Ken, sid 58); c maps to the SNES L shoulder.
    motion(core, 0, QCF_RIGHT, L)
    if core.ram[F_STATE] != 58:
        raise AssertionError(f"back: stance {core.ram[F_STATE]} != 58")
    for _ in range(180):
        if core.ram[F_STATE + FP2] == S_HIT:
            damage = hp0 - core.word(F_HP + FP2)
            if damage >= 13:
                print(f"PASS qcf-c-back: {damage} damage", flush=True)
                return
        core.step()
    raise AssertionError("qcf-c-back: travelling projectile did not hit")


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        hit_case(core, select_state, "p1-weak", 1, QCB_RIGHT, Y, 180, 52, 26)
        hit_case(core, select_state, "p1-strong", 1, QCB_RIGHT, X, 180, 53, 28)
        whiff_case(core, select_state)
        hit_case(core, select_state, "p2-weak", 2, QCB_LEFT, Y, 20, 52, 26)
        back_case(core, select_state)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
