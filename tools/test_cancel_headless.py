#!/usr/bin/env python3
"""Headless regression: a connected strong normal cancels into a special.

Kyo's standing strong punch (sid 6) opens its MUGEN var(1) cancel window
at animation element 4.  Once the punch connects, a QCF+Y motion during
that window must enter Dokugami (sid 66) instead of finishing the punch.

Run after a PVSnesLib build:

    python3 tools/test_cancel_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_FRAME, F_HITDONE = 0x4008, 0x400A, 0x401A
F_X, F_HP = 0x4000, 0x4010
FP2 = 0x40
Y = 9                                    # libretro X -> MUGEN y (strong)
DOWN, RIGHT = 5, 7
SPUNCH, CANCEL = 6, (66,)


def step_buttons(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def buffer_cancel_motion(core):
    """QCF+Y: D, DF, F, then Y.  Kept in the input ring until the gate opens."""
    for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
        step_buttons(core, direction)
    step_buttons(core, {Y})


def check_connected_cancel(core, select_state):
    enter_fight(core, select_state, "kyo", "kyo")
    core.put(F_X, 120 << 8)
    core.put(F_X + FP2, 150 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.step(10)

    step_buttons(core, {Y})               # standing strong punch
    for _ in range(30):
        if core.ram[F_HITDONE] or core.word(F_HP + FP2) < 200:
            break
        core.step()
    else:
        raise AssertionError("strong punch never connected")

    # Hitstop skips the fighter tick (and its input ring), so wait for
    # the freeze to end before buffering the cancel motion.
    for _ in range(40):
        if core.ram[0x1073] == 0:
            break
        core.step()
    if core.ram[F_STATE] != SPUNCH:
        raise AssertionError(f"punch recovered before cancel: "
                             f"state={core.ram[F_STATE]}")

    frame_at_cancel = core.word(F_FRAME)
    buffer_cancel_motion(core)

    seen = []
    for _ in range(30):
        state = core.ram[F_STATE]
        seen.append(state)
        if state in CANCEL:
            break
        core.step()
    if core.ram[F_STATE] not in CANCEL:
        raise AssertionError(f"cancel did not enter Dokugami: states={seen}")
    print(f"PASS strong punch {SPUNCH} -> Dokugami "
          f"{core.ram[F_STATE]} from frame {frame_at_cancel}", flush=True)


def check_whiff_no_cancel(core, select_state):
    """A whiffed strong normal must not open the cancel gate."""
    enter_fight(core, select_state, "kyo", "kyo")
    core.put(F_X, 120 << 8)
    core.put(F_X + FP2, 220 << 8)         # out of the punch's reach
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.step(10)

    step_buttons(core, {Y})               # standing strong punch, no contact
    if core.ram[F_STATE] != SPUNCH:
        raise AssertionError(f"whiff setup did not start the punch: "
                             f"state={core.ram[F_STATE]}")
    buffer_cancel_motion(core)

    seen = []
    for _ in range(30):
        state = core.ram[F_STATE]
        seen.append(state)
        if state in CANCEL:
            raise AssertionError(
                f"whiffed strong canceled before recovering: states={seen}")
        if core.ram[F_HITDONE]:
            raise AssertionError(f"whiffed punch reported contact: "
                                 f"states={seen}")
        if state != SPUNCH:
            break                         # recovery: a fresh special is legal
        core.step()
    print(f"PASS whiffed strong {SPUNCH} did not cancel (states={seen})",
          flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    failed = []
    try:
        select_state = boot_select(core)
        for name, check in (("connected", check_connected_cancel),
                            ("whiff", check_whiff_no_cancel)):
            try:
                check(core, select_state)
            except AssertionError as exc:
                failed.append(f"{name}: {exc}")
    finally:
        core.close()
    if failed:
        raise AssertionError("; ".join(failed))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
