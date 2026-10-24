#!/usr/bin/env python3
"""Headless regression for Leona's Moon Slasher (states 48/49).

The roster config used to point both Moon Slasher states at AIR action 1010,
the Explod effect (and Riot body) timeline.  That clip has no Clsn1 attack
boxes, so the move could never hit -- and no Clsn2 hurt boxes either, which
made Leona invulnerable for the whole animation.  The real body actions are
1000/1001; 1010 is only the spinning effect spawned by the CNS Explod.

This test drives DP+P at close range and requires the move to enter states
48/49, expose attack/hurt boxes and take life from the opponent.

Run after a PVSnesLib build:

    python3 tools/test_leona_moonslasher_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (boot_select,     # noqa: E402
                                        enter_fight)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_X, F_HP = 0x4008, 0x4000, 0x4010
F_ATKBOX, F_HURTBOX = 0x4024, 0x4026
FP2 = 0x40
DOWN, RIGHT = 5, 7
LIGHT_P, STRONG_P = 1, 9
CASES = (("weak", LIGHT_P, 48), ("strong", STRONG_P, 49))


def step_buttons(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()
    core.step(ticks)


def moon_slasher(core, button):
    for direction in ((RIGHT,), (DOWN,), (DOWN, RIGHT)):
        step_buttons(core, direction)
    step_buttons(core, {button})


def check(core, select_state, label, button, sid):
    enter_fight(core, select_state, "leona", "kyo")
    core.put(F_X, 150 << 8)
    core.put(F_X + FP2, 190 << 8)
    core.step(10)
    hp0 = core.word(F_HP + FP2)
    moon_slasher(core, button)

    state = None
    atk_boxes = set()
    hurt_boxes = set()
    for _ in range(300):
        st = core.ram[F_STATE]
        if state is None and st:
            state = st
        if st == sid:
            atk_boxes.add(core.word(F_ATKBOX))
            hurt_boxes.add(core.word(F_HURTBOX))
        core.step()
        if state is not None and st == 0 and core.ram[F_STATE] == 0:
            break
    hp1 = core.word(F_HP + FP2)

    assert state == sid, f"{label}: entered state {state}, expected {sid}"
    assert any(atk_boxes), f"{label}: no Clsn1 attack box"
    assert any(hurt_boxes), f"{label}: no Clsn2 hurt box"
    assert hp1 < hp0, f"{label}: opponent took no damage"
    print(f"OK {label}: state {sid}, {hp0 - hp1} damage, "
          f"{len(atk_boxes) - (0 in atk_boxes)} attack boxes")


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for label, button, sid in CASES:
            check(core, select_state, label, button, sid)
    finally:
        core.close()
    print("PASS: Moon Slasher has hit/hurt boxes and deals damage")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
