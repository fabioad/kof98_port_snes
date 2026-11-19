#!/usr/bin/env python3
"""Blue Mary's special throw must launch every victim on the same arc.

A TargetState release into the generic thrown slot used to leave the flight
velocity to the victim's own 816 clip: Kyo's VelSet launches upward, Geese's
drops straight to the floor.  The port now gives airborne victims the shared
821 arc (and blocks the character-specific VelSet), so Geese, Kyo and Iori all
rise and land alike.

Run after a PVSnesLib build:

    python3 tools/test_mary_throw_height_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1_STATE, P1_X = 0x4008, 0x4000
P2_STATE, P2_Y, P2_HP = 0x4048, 0x4042, 0x4050
DOWN, LEFT, RIGHT = 5, 6, 7
Y = 1
HELD, THROWN, DOWNED, GETUP = 76, 77, 10, 18


def press(core, dirs, frames=2):
    core.buttons[0] = set(dirs)
    core.step(frames)


def typhoon(core):
    for d in ((DOWN,), (DOWN, LEFT), (LEFT,), (DOWN,), (DOWN, LEFT), (LEFT,)):
        press(core, d)
    core.buttons[0] = {Y}
    core.step(3)
    core.buttons[0] = set()


def run(victim):
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "mary", victim)
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, 150 << 8)
        core.put(0x4040, 174 << 8)
        core.step(20)
        before = core.word(P2_HP)
        typhoon(core)
        max_y = 0
        saw_hold = saw_thrown = landed = False
        for i in range(180):
            core.step()
            state = core.ram[P2_STATE]
            y = core.word(P2_Y)
            max_y = max(max_y, y >> 8)
            saw_hold |= state == HELD
            saw_thrown |= state == THROWN
            if i > 60 and state in (DOWNED, GETUP):
                landed = True
                break
        after = core.word(P2_HP)
        fails = []
        if not saw_hold:
            fails.append("victim never held")
        if not saw_thrown:
            fails.append("victim never entered the thrown slot")
        if max_y < 75:
            fails.append(f"victim only reached height {max_y} px (expected the 821 arc)")
        if not landed:
            fails.append("victim never landed")
        if before - after < 50:
            fails.append(f"throw only did {before - after} HP")
        return fails, max_y, before - after, landed
    finally:
        core.close()


def main():
    fails = []
    for victim in ("geese", "kyo", "iori"):
        case, height, damage, landed = run(victim)
        print(f"{victim}: max height {height} px, {damage} HP, landed={landed}")
        fails.extend(f"{victim}: {f}" for f in case)
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("PASS Blue Mary special throw: Geese/Kyo/Iori all launch and land together")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
