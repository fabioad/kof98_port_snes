#!/usr/bin/env python3
"""Guard cancel must not corrupt the CPU instruction stream.

Y+B / X+A while guarding enters the roll (94/95) or blowback (67) state
and spends one power stock.  The roll branch used to write 8-bit
immediates while A was 16-bit, and then popped a 16-bit stack word while
A was 8-bit; both mistakes can execute data as an opcode and freeze the
fight on the real SD2SNES (the Clark vs Ralf report).

Run after a PVSnesLib build:

    python3 tools/test_guard_cancel_headless.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                       # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
GS, FC, F_STATE, F_POWER = 0x1020, 0x1024, 0x4008, 0x4030
F_HP1, F_HP2, F_X, F_X2 = 0x4010, 0x4050, 0x4000, 0x4040
F_STATE2 = F_STATE + 0x40
# libretro ids
A, B, X, Y, LEFT = 8, 0, 9, 1, 6


def steps(core, n=1):
    for _ in range(n):
        core.step()


def wait_frames(core, n):
    """Advance n frames; fail if the fight clock stops."""
    last = core.ram[FC]
    still = 0
    for _ in range(n):
        core.step()
        fc = core.ram[FC]
        if core.ram[GS] == 1 and fc == last:
            still += 1
            assert still < 20, (
                f"fight froze: state={core.ram[F_STATE]} "
                f"power={core.word(F_POWER)}")
        else:
            still = 0
        last = fc


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "clark", "ralf")
        core.ram[0x1090] = core.ram[0x1091] = 0

        # Y+B -> guard back-roll (94/95); X+A -> guard blowback (67).
        for combo, expected in (((Y, B), 94), ((X, A), 67)):
            core.put(F_X, 110 << 8)
            core.put(F_X2, 150 << 8)
            core.put(F_HP1, 200)
            core.put(F_HP2, 200)
            core.put(F_POWER, 3000)
            core.ram[F_STATE] = 0
            core.ram[F_STATE2] = 0
            core.buttons[0] = {LEFT}
            steps(core, 3)
            core.ram[F_STATE] = 27          # stand guard hold
            steps(core, 1)
            core.buttons[0] = {LEFT, *combo}
            steps(core, 3)
            core.buttons[0] = {LEFT}
            seen = []
            for _ in range(20):
                core.step()
                seen.append(core.ram[F_STATE])
            assert expected in seen, (combo, seen)
            assert core.word(F_POWER) == 2000, core.word(F_POWER)
            wait_frames(core, 30)

        print("PASS guard cancel: Y+B back-roll and X+A blowback, "
              "one stock each, fight keeps advancing")
    finally:
        core.close()


if __name__ == "__main__":
    main()
