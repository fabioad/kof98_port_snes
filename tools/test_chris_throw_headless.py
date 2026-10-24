#!/usr/bin/env python3
"""Chris' Step turn throw must release the victim instead of freezing.

Chris' source bind state 810 ends with a two-line landing trigger

    trigger1 = Pos Y >= 0
    trigger1 = Vel Y > 0

The build only understood the one-line form (`Vel Y > 0 && Pos Y >= 0`), so
the 810 -> 820 transition was missing from the TransTab.  The attacker sat
on the AIR trailing 255-tick hold (about 4.3 s) while the victim stayed in
S_VHELD, which looked like the fight had stopped even though the console
kept running.  StThrow also did not evaluate landing TransTab rows.

Run after a PVSnesLib build:

    python3 tools/test_chris_throw_headless.py
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                          # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE, F_X, F_HP = 0x8, 0x0, 0x10
F_GRAB = 52
FCNTR = 0x1024
X, Y = 9, 1                       # libretro X/Y -> mugen y/x (throw = x+y)
RELEASE_LIMIT = 120               # trailing hold is 255 ticks


def check_chris_throw(core, select_state):
    enter_fight(core, select_state, "chris", "kyo")
    core.put(FP1 + F_X, 130 << 8)
    core.put(FP2 + F_X, 160 << 8)
    core.put(FP1 + F_HP, 200)
    core.put(FP2 + F_HP, 200)
    core.step(10)

    core.buttons[0] = {X, Y}
    core.step(3)
    core.buttons[0] = set()

    grabbed = False
    released_at = None
    for tick in range(RELEASE_LIMIT + 1):
        core.step()
        a_state = core.ram[FP1 + F_STATE]
        v_state = core.ram[FP2 + F_STATE]
        if a_state == 75 and v_state == 76:
            grabbed = True
        if grabbed and v_state != 76:
            released_at = tick
            break
    if not grabbed:
        raise AssertionError("throw never grabbed (attacker 75, victim 76)")
    if core.ram[FP2 + F_GRAB]:
        raise AssertionError("victim stayed grabbed")
    if released_at is None:
        raise AssertionError(
            f"throw did not release within {RELEASE_LIMIT} ticks "
            f"(attacker state={core.ram[FP1 + F_STATE]}, "
            f"victim state={core.ram[FP2 + F_STATE]})")

    # Let the victim fall, get up and both fighters regain control.
    for _ in range(400):
        if (core.ram[FP1 + F_STATE] == 0
                and core.ram[FP2 + F_STATE] == 0):
            break
        core.step()
    else:
        raise AssertionError(
            f"fighters did not recover: p1={core.ram[FP1 + F_STATE]} "
            f"p2={core.ram[FP2 + F_STATE]}")

    hp = core.word(FP2 + F_HP)
    if hp > 165:
        raise AssertionError(f"throw dealt no damage (victim hp={hp})")

    fc0 = core.word(FCNTR)
    core.step(30)
    if core.word(FCNTR) == fc0:
        raise AssertionError("frame counter stopped after the throw")

    print(f"PASS Chris throw released at tick {released_at}, "
          f"victim hp={hp}", flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        check_chris_throw(core, boot_select(core))
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
