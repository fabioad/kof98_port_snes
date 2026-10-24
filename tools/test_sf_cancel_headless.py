#!/usr/bin/env python3
"""Street Fighter crew: strong punches cancel into anti-air and fireball.

Ryu, Ken, Sakura, Ryo and Robert keep their shots in the imported character
descriptors.  CancelGate used to dereference CH_CANCELROW one time too many:
it read the word at ``F_TBANK:row_offset`` and used that as the CancelTab
offset.  The accidental byte happened to be zero for Kyo (so the fixed
characters worked) but was a code byte for the imported fighters, leaving
the gate closed.  Both the standing and crouching strong punch must now
cancel on contact into the DP anti-air and into the QCF projectile.

Run after a PVSnesLib build:

    python3 tools/test_sf_cancel_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_HITDONE = 0x4008, 0x401A
F_X, F_HP = 0x4000, 0x4010
FP2 = 0x40
X = 9                                    # libretro X -> MUGEN y (strong)
DOWN, RIGHT = 5, 7

# name, motion, posture, normal sid, expected special sid
# Posture "s" = standing strong punch (sid 6), "c" = crouching (sid 20).
CASES = (
    ("ryu", "DP", "s", 6, 51),
    ("ryu", "QCF", "s", 6, 53),
    ("ryu", "DP", "c", 20, 51),
    ("ryu", "QCF", "c", 20, 53),
    ("ken", "DP", "s", 6, 53),
    ("ken", "QCF", "s", 6, 55),
    ("ken", "DP", "c", 20, 53),
    ("ken", "QCF", "c", 20, 55),
    ("sakura", "DP", "s", 6, 49),
    ("sakura", "QCF", "s", 6, 53),
    ("sakura", "DP", "c", 20, 49),
    ("sakura", "QCF", "c", 20, 53),
    ("ryo", "DP", "s", 6, 57),
    ("ryo", "QCF", "s", 6, 61),
    ("ryo", "DP", "c", 20, 57),
    ("ryo", "QCF", "c", 20, 61),
    ("robert", "DP", "s", 6, 51),
    ("robert", "QCF", "s", 6, 59),
    ("robert", "DP", "c", 20, 51),
    ("robert", "QCF", "c", 20, 59),
)


def tap(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def start(core, select_state, name, posture):
    enter_fight(core, select_state, name, "kyo")
    core.put(F_X, 120 << 8)
    core.put(F_X + FP2, 150 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.step(10)


def cancel(core, select_state, name, motion, posture, normal_sid, target):
    start(core, select_state, name, posture)
    if posture == "c":
        core.buttons[0] = {DOWN}
        core.step(4)
        tap(core, {DOWN, X})             # standing/crouching strong punch
    else:
        tap(core, {X})

    for _ in range(40):
        if core.ram[F_HITDONE] or core.word(F_HP + FP2) < 200:
            break
        core.step()
    else:
        raise AssertionError(f"{name} {posture}: strong punch never connected")

    if core.ram[F_STATE] != normal_sid:
        raise AssertionError(
            f"{name} {posture}: expected normal {normal_sid}, "
            f"got {core.ram[F_STATE]}")

    # Hitstop skips the fighter tick (and the input ring), so buffer the
    # cancel motion after the freeze, like the Kyo regression test.
    for _ in range(40):
        if core.ram[0x1073] == 0:
            break
        core.step()
    if core.ram[F_STATE] != normal_sid:
        raise AssertionError(f"{name} {posture}: punch recovered before cancel")

    seq = ((RIGHT,), (DOWN,), (DOWN, RIGHT)) if motion == "DP" else (
        (DOWN,), (DOWN, RIGHT), (RIGHT,))
    for direction in seq:
        tap(core, direction)
    tap(core, {X})

    seen = []
    for _ in range(30):
        state = core.ram[F_STATE]
        seen.append(state)
        if state == target:
            return
        core.step()
    raise AssertionError(
        f"{name} {posture} {motion}: normal {normal_sid} did not cancel "
        f"into {target}; states={seen}")


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for name, motion, posture, normal_sid, target in CASES:
            cancel(core, select_state, name, motion, posture,
                   normal_sid, target)
            stance = "standing" if posture == "s" else "crouching"
            print(f"PASS {name:8} {stance:9} strong {normal_sid} -> "
                  f"{motion} {target}", flush=True)
    finally:
        core.close()
    print("PASS: SF strong punches cancel into anti-air and projectile")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
