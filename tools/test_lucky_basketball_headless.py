#!/usr/bin/env python3
"""Headless regression for Lucky's basketball (SHOOT) trajectory.

The source helpers (states 2100 -> 2102 -> 2107 -> 2103) give the ball a short
forward drift and then zero its horizontal speed, so it drops almost
vertically about 60 px ahead.  State 2103 is the only phase with a HitDef;
after the first ground contact the ball only bounces (cosmetic).

The old port fired the ball like a horizontal fireball at torso height.  This
test pins the source shape: spawn above the screen, ~49 px of forward drift,
then VX=0 and a vertical drop; a victim at the landing spot takes 22 damage,
and a whiff bounces backward.

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
    hp0 = core.word(victim_hp)
    shoot(core, lucky_side - 1, motion)

    base = None
    samples = []
    bounced = False
    hit = False
    for frame in range(150):
        if base is None:
            base = ball_slot(core, lucky_side == 2)
        if base is not None:
            x, y = core.word(base), core.word(base + 2)
            vx, vy = core.word(base + 8), core.word(base + 10)
            attr = core.ram[base + 15]
            samples.append((frame, x, signed16(y), vx, signed16(vy), attr))
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
    if first[2] >= 0:
        raise AssertionError(
            f"{label}: ball spawned at screen Y {first[2]}, not above the top")
    # Forward drift then a vertical drop (negative X when facing left).
    drift = max(abs(s[1] - first[1]) for s in samples)
    if not 40 <= drift <= 60:
        raise AssertionError(f"{label}: forward drift {drift}px, expected ~49")
    if not any(s[3] == 0 for s in samples if s[0] - first[0] >= 7):
        raise AssertionError(f"{label}: VX never stopped (horizontal shot)")
    max_y = max(s[2] for s in samples)

    damage = hp0 - core.word(victim_hp)
    if expect_hit:
        if not hit or damage < 20:
            raise AssertionError(
                f"{label}: victim not hit (state={core.ram[victim_state]}, "
                f"damage={damage})")
        print(f"PASS {label}: high drop + {drift}px drift + {damage} damage",
              flush=True)
    else:
        if hit or damage:
            raise AssertionError(f"{label}: ball hit a far-away victim")
        if max_y < GROUND_Y:
            raise AssertionError(f"{label}: ball never reached the floor")
        if not bounced:
            raise AssertionError(f"{label}: no ground bounce on whiff")
        ground = next(i for i, s in enumerate(samples) if s[2] >= GROUND_Y)
        if lucky_side == 1 and samples[-1][1] >= samples[ground][1]:
            raise AssertionError(f"{label}: right-facing ball did not bounce back")
        if lucky_side == 2 and samples[-1][1] <= samples[ground][1]:
            raise AssertionError(f"{label}: left-facing ball did not bounce back")
        print(f"PASS {label}: high drop + {drift}px drift + backward bounce",
              flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        # P1 Lucky, victim at the landing spot.
        case(core, select_state, "p1-hit", 1, DP_RIGHT, 166, True)
        # P1 Lucky, victim far away: the ball must bounce back, not fly on.
        case(core, select_state, "p1-whiff", 1, DP_RIGHT, 230, False)
        # P2 Lucky facing left: the drop and bounce mirror correctly.
        case(core, select_state, "p2-hit", 2, DP_LEFT, 37, True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
