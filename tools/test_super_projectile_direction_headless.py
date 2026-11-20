#!/usr/bin/env python3
"""Regression: a multi-hit super projectile must push the victim away.

Ryu's Shinku Hadouken latches onto the victim after the first contact and
ProjPinIfMultiFar zeroes the shot's VX, so the per-contact pushback and the
final launch used to fall back to "right" for every hit.  With the caster on
the right (facing left) that pulled the victim into him instead of throwing
him away.

Run after a PVSnesLib build:

    python3 tools/test_super_projectile_direction_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                       # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040
DOWN, LEFT, RIGHT = 5, 6, 7
STRONG_P = 9
DOWN_STATE = 10


def motion(core, facing_right):
    forward = RIGHT if facing_right else LEFT
    for direction in ({DOWN}, {DOWN, forward}, {forward},
                      {DOWN}, {DOWN, forward}, {forward}):
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = {STRONG_P}
    core.step(3)
    core.buttons[0] = set()


def run(core, select, caster_x, victim_x):
    enter_fight(core, select, "ryu", "ken")
    core.ram[0x1090] = core.ram[0x1091] = 0
    core.put(P1, caster_x << 8)
    core.put(P2, victim_x << 8)
    core.put(P1 + 16, 336)
    core.put(P2 + 16, 336)
    core.put(P1 + 48, 3000)                    # one super stock
    core.step(20)

    motion(core, facing_right=caster_x < victim_x)

    hp0 = core.word(P2 + 16)
    first_x = later_x = last_x = None
    since_hit = 0
    down = False
    for _ in range(140):
        core.step()
        hp = core.word(P2 + 16)
        x = core.word(P2) >> 8
        if hp < hp0:
            if first_x is None:
                first_x = x
            last_x = x
            if later_x is None:
                since_hit += 1
                if since_hit >= 15:
                    later_x = x
        down |= core.ram[P2 + 8] == DOWN_STATE
    return hp0 - core.word(P2 + 16), first_x, later_x, last_x, down


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        fails = []

        # Caster on the right, facing left: the victim (also on the left)
        # must travel left, away from him.
        dmg, first, later, last, down = run(core, select, 200, 140)
        if first is None or later is None or later > first - 15:
            fails.append(f"right side: victim did not move left "
                         f"(first={first} later={later})")
        if dmg == 0 or not down:
            fails.append(f"right side: dmg={dmg} down={down}")
        elif last is not None and last > first:
            fails.append(f"right side: victim ended closer to the caster "
                         f"({first}->{last})")

        # Caster on the left: unchanged behaviour, the victim flies right.
        dmg, first, later, last, down = run(core, select, 100, 160)
        if first is None or later is None or later < first + 15:
            fails.append(f"left side: victim did not move right "
                         f"(first={first} later={later})")
        if dmg == 0 or not down:
            fails.append(f"left side: dmg={dmg} down={down}")
        elif last is not None and last < first:
            fails.append(f"left side: victim ended closer to the caster "
                         f"({first}->{last})")

        if fails:
            for failure in fails:
                print("FAIL:", failure)
            return 1
        print("PASS super projectile direction: right-side caster throws the "
              "victim left, left-side caster throws right")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
