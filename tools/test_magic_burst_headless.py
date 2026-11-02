#!/usr/bin/env python3
"""Headless regression for the shared Athena/Kensou magic burst.

Athena's Psycho Ball states emit Explods 1022/1023/1024 (and the supers use
7000/7100); all of them were previously skipped because the clips were not in
the shared spark atlas.  They now map to the 2x2 ``MagicBurst`` record.

Run after a PVSnesLib build:

    python3 tools/test_magic_burst_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    boot_select, enter_fight, Y, DOWN, RIGHT,
)
from test_projectile_guard_headless import SPARKS, symbols  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
SPK_SIZE = 20
P1_STATE, P1_X = 0x4008, 0x4000
P2_X, P2_HP = 0x4040, 0x4050


def double_qcf(core, button):
    for _ in range(2):
        for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
            core.buttons[0] = set(direction)
            core.step(2)
    core.buttons[0] = set()
    core.step(1)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        burst = symbols()["MagicBurst"] & 0xFFFF
        select = boot_select(core)
        enter_fight(core, select, "athena", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, 70 << 8)
        core.put(P2_X, 90 << 8)
        core.step(20)
        double_qcf(core, Y)

        seen, spawned, hp_start = [], False, core.word(P2_HP)
        for _ in range(70):
            core.step()
            state = core.ram[P1_STATE]
            if not seen or seen[-1] != state:
                seen.append(state)
            for slot in range(2):
                base = SPARKS + slot * SPK_SIZE
                if core.word(base + 4) == burst:
                    spawned = True
        hp_end = core.word(P2_HP)
        failures = []
        if 49 not in seen:
            failures.append(f"Athena Psycho Ball state 49 never reached: "
                            f"{seen}")
        if not spawned:
            failures.append("MagicBurst never occupied a spark/explod slot")
        if hp_end >= hp_start:
            failures.append(f"Psycho Ball did no damage "
                            f"({hp_start} -> {hp_end})")
        if failures:
            for failure in failures:
                print("FAIL:", failure)
            return 1
        print(f"Magic burst: states={seen[:8]} hp {hp_start}->{hp_end} "
              f"clip=${burst:04X} OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
