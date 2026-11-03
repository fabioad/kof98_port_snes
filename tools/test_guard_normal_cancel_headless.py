#!/usr/bin/env python3
"""Guard hold may be cut by a normal, but guard-hit (blockstun) may not.

In the arcade, holding back is only a guard *pose*: if the opponent's move
does not connect, pressing a normal leaves the pose and the attack comes
out.  Once a move connects, the victim is in S_GHIT and the current block
behaviour stays (only the existing Y+B / X+A guard cancels work there).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                       # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
F_STATE = 0x4008
F_HTIMER = 0x4028
F_STATE2 = F_STATE + 0x40
F_X, F_X2 = 0x4000, 0x4040
A, B, X, Y, LEFT, DOWN = 8, 0, 9, 1, 6, 5
NORMALS = set(range(5, 9))              # S_PUNCH..S_SKICK
CROUCH_NORMALS = set(range(19, 23))     # S_CPUNCH..S_CSKICK


def reset_pose(core, state, held):
    core.put(F_X, 110 << 8)
    core.put(F_X2, 220 << 8)             # out of normal range: no hitstop
    core.put(0x4050, 200)                # full HP for the dummy
    core.ram[F_STATE] = 0
    core.ram[F_STATE2] = 0
    core.buttons[0] = set(held)
    core.step(3)
    core.ram[F_STATE] = state
    core.step(1)


def press_and_sample(core, button, held=(LEFT,), frames=5):
    core.buttons[0] = set(held) | {button}
    core.step(3)
    core.buttons[0] = set(held)
    seen = []
    for _ in range(frames):
        core.step()
        seen.append(core.ram[F_STATE])
    return seen


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        enter_fight(core, select, "kyo", "iori")
        core.ram[0x1090] = core.ram[0x1091] = 0

        for name, button in (("A", A), ("B", B), ("X", X), ("Y", Y)):
            reset_pose(core, 27, (LEFT,))
            seen = press_and_sample(core, button)
            assert NORMALS & set(seen), f"stand guard + {name}: {seen}"
            print(f"PASS stand guard + {name} -> normal {NORMALS & set(seen)}")

        reset_pose(core, 28, (LEFT, DOWN))
        seen = press_and_sample(core, A, held=(LEFT, DOWN))
        assert CROUCH_NORMALS & set(seen), f"crouch guard + A: {seen}"
        print("PASS crouch guard + A -> crouching normal")

        # Blockstun: the normal must not cut the guard-hit flinch.
        reset_pose(core, 30, (LEFT,))
        core.ram[F_HTIMER] = 20
        seen = press_and_sample(core, A)
        assert all(s == 30 for s in seen), \
            f"guard-hit was cancelled by a normal: {seen}"
        assert core.ram[F_HTIMER] > 0
        print("PASS guard-hit + A keeps the current blockstun")
    finally:
        core.close()


if __name__ == "__main__":
    main()
