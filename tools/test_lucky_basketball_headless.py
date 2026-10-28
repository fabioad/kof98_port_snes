#!/usr/bin/env python3
"""Headless regression for Lucky's Death Bound basketball.

The arcade Death Bound leaves Lucky's hand and travels diagonally down and
forward toward the opponent (the A version is higher, the C version lower).
It is not a vertical drop from the sky: the source's sky/layup ball belongs to
the separate Death Shoot (D,D+P).

This port's basketball row (sid 87, state 2100) now spawns at hand height
(120 px above the floor), moves 4 px/tick forward and curves down at
11/16 px/tick^2.  It hits a victim about 60 px ahead for 22 damage and bounces
on the floor on a whiff.

Run after a PVSnesLib build:

    python3 tools/test_lucky_basketball_headless.py
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
B = 0
DOWN, LEFT, RIGHT = 5, 6, 7
S_HIT = 9
GROUND_Y = 190
BALL_DAMAGE = 22
# ~F, D, DF, a (a = SNES B on this port).
DP_RIGHT = ((RIGHT,), (DOWN,), (DOWN, RIGHT), (RIGHT,))
DP_LEFT = ((LEFT,), (DOWN,), (DOWN, LEFT), (LEFT,))


def press(core, port, buttons, frames=3):
    core.buttons[port] = set(buttons)
    core.step(frames)
    core.buttons[port] = set()


def shoot(core, port, motion):
    for direction in motion:
        core.buttons[port] = set(direction)
        core.step(2)
    core.step(1)
    press(core, port, {B}, 3)


def ball_slot(core, owner_p2):
    for slot in (0, 1):
        base = SPK + slot * SPK_SIZE
        attr = core.ram[base + 15]
        if not core.word(base + 4) or not (attr & 0x80):
            continue
        if bool(attr & 0x40) != owner_p2:
            continue
        return base
    return None


def signed16(value):
    return value - 0x10000 if value & 0x8000 else value


def case(core, select_state, label, lucky_side, motion, victim_x,
         expect_hit):
    if lucky_side == 1:
        p1, p2 = "lucky", "kyo"
        victim_state, victim_hp = F_STATE + FP2, F_HP + FP2
    else:
        p1, p2 = "kyo", "lucky"
        victim_state, victim_hp = F_STATE, F_HP
    enter_fight(core, select_state, p1, p2)
    if lucky_side == 1:
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, victim_x << 8)
    else:
        core.put(F_X, victim_x << 8)
        core.put(F_X + FP2, 100 << 8)
    core.step(20)
    if not expect_hit:
        # The corner clamps the victim inside the ball's reach; make him
        # invulnerable so the projectile passes through and we can test the
        # floor bounce on a clean whiff.
        core.ram[F_X + (FP2 if lucky_side == 1 else 0) + 62] = 0xFF
    hp0 = core.word(victim_hp)
    shoot(core, lucky_side - 1, motion)

    samples = []
    bounced = False
    hit = False
    for frame in range(150):
        base = ball_slot(core, lucky_side == 2)
        if base is not None:
            x, y = core.word(base), core.word(base + 2)
            vx = signed16(core.word(base + 8))
            vy = signed16(core.word(base + 10))
            attr = core.ram[base + 15]
            samples.append((frame, x, signed16(y), vx, vy, attr))
            if (len(samples) > 1 and samples[-2][2] >= GROUND_Y
                    and signed16(y) < GROUND_Y and signed16(vy) < 0):
                bounced = True
        if core.ram[victim_state] == S_HIT and core.word(victim_hp) < hp0:
            hit = True
            break
        core.step()

    if not samples:
        raise AssertionError(f"{label}: no projectile spawned")
    first = samples[0]
    # The ball must leave the hand area, not appear above the screen.
    if not 50 <= first[2] <= 150:
        raise AssertionError(
            f"{label}: ball spawned at screen Y {first[2]}, "
            f"expected hand height (~120)")
    # Forward and downward: no vertical drop, no horizontal fireball.
    if lucky_side == 1:
        forward = max(s[1] for s in samples) - first[1]
        if first[3] <= 0 or forward < 20:
            raise AssertionError(
                f"{label}: ball did not move forward (vx={first[3]}, "
                f"dx={forward})")
    else:
        forward = first[1] - min(s[1] for s in samples)
        if first[3] >= 0 or forward < 20:
            raise AssertionError(
                f"{label}: ball did not move forward (vx={first[3]}, "
                f"dx={forward})")
    if expect_hit and samples[-1][2] <= first[2]:
        raise AssertionError(f"{label}: ball did not descend")

    damage = hp0 - core.word(victim_hp)
    if expect_hit:
        if not hit or damage < 20:
            raise AssertionError(
                f"{label}: victim not hit (state={core.ram[victim_state]}, "
                f"damage={damage})")
        print(f"PASS {label}: diagonal hand shot + {damage} damage",
              flush=True)
    else:
        if hit or damage:
            raise AssertionError(f"{label}: ball hit a far-away victim")
        if max(s[2] for s in samples) < GROUND_Y:
            raise AssertionError(f"{label}: ball never reached the floor")
        if not bounced:
            raise AssertionError(f"{label}: no ground bounce on whiff")
        ground = next(i for i, s in enumerate(samples) if s[2] >= GROUND_Y)
        if lucky_side == 1 and samples[-1][1] >= samples[ground][1]:
            raise AssertionError(f"{label}: right-facing ball did not bounce back")
        if lucky_side == 2 and samples[-1][1] <= samples[ground][1]:
            raise AssertionError(f"{label}: left-facing ball did not bounce back")
        print(f"PASS {label}: diagonal hand shot + floor bounce", flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        # P1 Lucky, victim at the landing spot.
        case(core, select_state, "p1-hit", 1, DP_RIGHT, 166, True)
        # P1 Lucky, victim far away: the ball must land and bounce, not fly on.
        case(core, select_state, "p1-whiff", 1, DP_RIGHT, 232, False)
        # P2 Lucky facing left: the diagonal and bounce mirror correctly.
        case(core, select_state, "p2-hit", 2, DP_LEFT, 20, True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
