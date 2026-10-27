#!/usr/bin/env python3
"""Headless regression for Yamazaki's Sadomazo (tongue) reversal.

Yamazaki's counter stance (states 1100/1110) must turn an incoming hit into
the follow-up state 1101 (runtime slot 103), and the follow-up must deal its
real damage.  The strong-punch case pins the counter-hit path: the victim is
still in its attack animation when 1101 connects, and CounterDraw->WriteStr
used to clobber the attacker-state scratch used to index the damage table,
so the reversal dealt 1 point instead of the full hit.

Run after a PVSnesLib build:

    python3 tools/test_yamazaki_reversal_headless.py
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
# libretro pad ids
B, Y, A, X = 0, 1, 8, 9
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
# MUGEN a = SNES B, b = SNES A (weak/strong kick buttons on this port).
MOTION_RIGHT = ((LEFT,), (LEFT, DOWN), (DOWN,), (DOWN, RIGHT), (RIGHT,))
MOTION_LEFT = ((RIGHT,), (RIGHT, DOWN), (DOWN,), (DOWN, LEFT), (LEFT,))
REVERSAL_SID = 103
MIN_DAMAGE = 20          # full hit is 26; counter hit is 32


def press(core, port, buttons, frames=3):
    core.buttons[port] = set(buttons)
    core.step(frames)
    core.buttons[port] = set()


def stance(core, port, button, motion):
    for direction in motion:
        core.buttons[port] = set(direction)
        core.step(2)
    core.buttons[port] = set()
    core.step(2)
    press(core, port, {button}, 3)
    core.step(6)


def watch(core, attacker_hp, frames=280):
    """Run the fight, returning (reversal seen, hp lost by the attacker)."""
    hp0 = core.word(attacker_hp)
    seen = False
    for _ in range(frames):
        if (core.ram[F_STATE] == REVERSAL_SID
                or core.ram[F_STATE + FP2] == REVERSAL_SID):
            seen = True
        core.step()
    return seen, hp0 - core.word(attacker_hp)


def case(core, select_state, label, yamazaki_side, button, stance_sid,
         attack):
    port = yamazaki_side - 1         # 1 = P1, 2 = P2
    if port == 0:                   # Yamazaki is P1, facing right
        p1, p2 = "yamazaki", "kyo"
        motion, attack_port, hp = MOTION_RIGHT, 1, F_HP + FP2
    else:                           # Yamazaki is P2, facing left
        p1, p2 = "kyo", "yamazaki"
        motion, attack_port, hp = MOTION_LEFT, 0, F_HP
    enter_fight(core, select_state, p1, p2)
    core.put(F_X, 150 << 8)
    core.put(F_X + FP2, 174 << 8)
    core.step(20)
    stance(core, port, button, motion)
    if core.ram[F_STATE + port * FP2] != stance_sid:
        raise AssertionError(
            f"{label}: stance {core.ram[F_STATE + port * FP2]} "
            f"!= {stance_sid}")
    # Arm the counter, then let the opponent attack.
    core.step(6)
    attack(core, attack_port)
    reversed_ok, damage = watch(core, hp)
    if not reversed_ok:
        raise AssertionError(f"{label}: reversal did not trigger")
    if damage < MIN_DAMAGE:
        raise AssertionError(
            f"{label}: follow-up dealt only {damage} damage "
            f"(expected >= {MIN_DAMAGE})")
    print(f"PASS {label}: reversal + {damage} damage", flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)

        def punch(core, port):
            press(core, port, {Y}, 3)        # MUGEN x

        def strong_punch(core, port):
            press(core, port, {X}, 3)        # MUGEN y

        def jump_in(core, port):
            core.buttons[port] = {UP}
            core.step(2)
            core.buttons[port] = set()
            core.step(20)
            press(core, port, {Y}, 3)

        # Yamazaki as P2 (CPU/opponent side), strong Sadomazo vs a punch.
        case(core, select_state, "p2-strong/counter-hit", 2, A, 49,
             strong_punch)
        # Weak Sadomazo on the P1 side.
        case(core, select_state, "p1-weak/normal", 1, B, 48, punch)
        # Airborne attacker: the RevTab posture mask must accept jump-ins.
        case(core, select_state, "p2-strong/jump-in", 2, A, 49, jump_in)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
