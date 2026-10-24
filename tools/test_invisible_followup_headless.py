#!/usr/bin/env python3
"""Regression: a heavy-d follow-up must never play an invisible hitbox clip.

Heavy D!'s Blast Upper (sid 50) and Soul Flower (sid 52) put their HitDef in
invisible kama helper states (AIR 1110/1210).  The engine has no helpers, so
it chains the main fighter into those states at the end of the launch clip.
Before the build repaired those clips, every frame of the follow-up was
sprite -1, so the character vanished while the hitbox stayed active -- on
screen only the hit spark/hitbox remained.

Run after a PVSnesLib build (the .msu must sit next to the ROM):

    python3 tools/test_invisible_followup_headless.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                       # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE = 0x4008
OAM = 0x1800
DOWN, LEFT, RIGHT, B = 5, 6, 7, 0

# sid -> command tail (the final B is Heavy D's "a": MUGEN a -> SNES B).
CASES = {
    60: ((DOWN,), (DOWN, RIGHT), (RIGHT,)),      # Blast Upper
    61: ((DOWN,), (DOWN, LEFT), (LEFT,)),        # Soul Flower
}


def fighter_cells(core):
    """P1 character cells: OBJ palette 0/1 and a visible y coordinate."""
    oam = bytes(core.ram[OAM:OAM + 512])
    return [i for i in range(128)
            if oam[i * 4 + 1] < 0xF0 and (oam[i * 4 + 3] & 0x0E) in (0, 2)]


def run_case(core, sid, motion):
    core.step(10)
    for direction in motion:
        core.buttons[0] = set(direction)
        core.step(3)
    core.buttons[0] = {B}
    core.step(3)
    core.buttons[0] = set()
    for _ in range(300):
        if core.ram[F_STATE] == sid:
            cells = fighter_cells(core)
            assert cells, f"sid {sid}: follow-up has no character cells"
            print(f"PASS sid {sid}: {len(cells)} character cells")
            return
        core.step()
    raise AssertionError(f"sid {sid} was never reached")


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select_state = boot_select(core)
        for sid, motion in CASES.items():
            enter_fight(core, select_state, "heavyd", "kyo")
            core.put(0x4000, 120 << 8)
            core.put(0x4040, 190 << 8)
            run_case(core, sid, motion)
    finally:
        core.close()


if __name__ == "__main__":
    main()
