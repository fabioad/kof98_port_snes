#!/usr/bin/env python3
"""Headless regression for the shared Athena/Kensou magic burst.

The burst (2x2 ``MagicBurst`` record) belongs to the Psycho Ball / Phoenix
Fang Arrow effects.  Athena's Psycho Sword (DP+P, states 1020/1030) reuses
anim ids 1022-1024 for a sword aura; compiling those as the burst stamped a
pale square with a transparent circle on the victim's side.  The DP must
therefore never occupy a spark/explod slot with the burst, while the super
must still show it.

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
from audit_specials_headless import character, attempt    # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
SPK_SIZE = 20
P1_STATE, P1_X = 0x4008, 0x4000
P2_X, P2_HP = 0x4040, 0x4050


def psico_sword(core):
    """F, D, DF + y: the anti-air that used to stamp the burst."""
    for direction in ((RIGHT,), (DOWN,), (DOWN, RIGHT)):
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = set()
    core.step(1)
    core.buttons[0] = {Y}
    core.step(2)
    core.buttons[0] = set()


def watch_slots(core, burst, frames):
    """Step the emulator, returning (states, burst_spawned, hp_start/end)."""
    states, spawned = [], False
    hp_start = core.word(P2_HP)
    for _ in range(frames):
        core.step()
        state = core.ram[P1_STATE]
        if not states or states[-1] != state:
            states.append(state)
        for slot in range(2):
            if core.word(SPARKS + slot * SPK_SIZE + 4) == burst:
                spawned = True
    return states, spawned, hp_start, core.word(P2_HP)


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    info = character("athena", ROOT / "build" / "gen_fight")
    failures = []
    try:
        burst = symbols()["MagicBurst"] & 0xFFFF
        select = boot_select(core)
        enter_fight(core, select, "athena", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(P1_X, 70 << 8)
        core.put(P2_X, 90 << 8)
        core.step(20)
        base = core.save()

        # 1) The Psycho Sword must connect without ever showing the burst.
        psico_sword(core)
        states, spawned, hp_start, hp_end = watch_slots(core, burst, 140)
        if 49 not in states:
            failures.append(f"Psycho Sword state 49 never reached: {states}")
        if spawned:
            failures.append("MagicBurst stamp appeared on the Psycho Sword")
        if hp_end >= hp_start:
            failures.append(f"Psycho Sword did no damage "
                            f"({hp_start} -> {hp_end})")
        print(f"Psycho Sword: states={states[:8]} hp {hp_start}->{hp_end} "
              f"burst={spawned}")

        # 2) The super must still paint the burst from the shared clip.
        rule = next(r for r in info["rules"]
                    if r["sid"] == 85 and r["row"][3] == 3)
        super_states, super_spawned = [], False
        real_step = core.step

        def step(n=1):
            nonlocal super_spawned
            for _ in range(n):
                real_step(1)
                st = core.ram[P1_STATE]
                if not super_states or super_states[-1] != st:
                    super_states.append(st)
                for slot in range(2):
                    if core.word(SPARKS + slot * SPK_SIZE + 4) == burst:
                        super_spawned = True
        core.step = step
        attempt(core, base, info, rule)
        if not super_spawned:
            failures.append(
                f"Phoenix Fang Arrow never showed the burst: {super_states}")
        print(f"Phoenix Fang: states={super_states[:10]} "
              f"burst={super_spawned}")

        if failures:
            for failure in failures:
                print("FAIL:", failure)
            return 1
        print(f"Magic burst: clip=${burst:04X} OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
