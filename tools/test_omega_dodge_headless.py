#!/usr/bin/env python3
"""Omega Rugal's Fusion evades: L rolls and the neutral dodge.

The source CMD had the ESQ_L/ESQ_F/ESQ_B [Command] blocks but no State -1
rules, and the reduced move table only carried placeholder slots 94/95/69.
Omega now reuses his existing emergency-evasion clips (1010/1011) plus a
port-added in-place 720 pose:
  * L + forward -> sid 95 / state 1010
  * L + back    -> sid 94 / state 1011
  * Y + B       -> sid 69 / state 720 (the standard DODGE input)
  * L alone     -> taunt, exactly like every character.

Run after a PVSnesLib build:

    python3 tools/test_omega_dodge_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
F_STATE = 0x4008
L, FWD, BACK, Y, B = 10, 7, 6, 1, 0


def run(directions, buttons, wanted):
    core = Core(CORE, str(ROM))
    try:
        select = boot_select(core)
        enter_fight(core, select, "omegarugal", "kyo")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.step(30)
        held = set().union(*directions) if directions else set()
        for d in held:
            core.buttons[0] = {d}
            core.step(3)
        core.buttons[0] = held | set(buttons)
        core.step(3)
        core.buttons[0] = set()
        seen = []
        for _ in range(50):
            core.step()
            state = core.ram[F_STATE]
            if not seen or seen[-1] != state:
                seen.append(state)
            if state == 0 and len(seen) > 1:
                break
        return seen
    finally:
        core.close()


def main():
    seen = run((frozenset({FWD}),), (L,), 95)
    assert 95 in seen, f"L+forward did not roll ({seen})"
    print("PASS Omega L+forward -> forward roll (sid 95)")

    seen = run((frozenset({BACK}),), (L,), 94)
    assert 94 in seen, f"L+back did not roll ({seen})"
    print("PASS Omega L+back -> back roll (sid 94)")

    seen = run((), (Y, B), 69)
    assert 69 in seen, f"DODGE did not start ({seen})"
    print("PASS Omega DODGE (Y+B) -> neutral dodge (sid 69)")

    seen = run((), (L,), 47)
    assert 47 in seen, f"L alone did not taunt ({seen})"
    print("PASS Omega L alone -> taunt, like all characters")


if __name__ == "__main__":
    main()
