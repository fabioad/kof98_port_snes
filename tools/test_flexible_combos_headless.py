#!/usr/bin/env python3
"""Headless regression for the normal-combo routes.

A connected normal -- light or strong -- may only cancel after the first
third of its animation into:

  * a special with either the weak or the strong button; or
  * a super with either the weak or the strong button.

Normal -> normal chains are gone: strong punch and strong kick must not cancel
into themselves or into each other.  Specials and supers keep both button
strengths.

Run after a PVSnesLib build:

    python3 tools/test_flexible_combos_headless.py
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
F_X, F_HP, F_POWER = 0x4000, 0x4010, 0x4030
FP2 = 0x40
START, A, B, X, Y = 3, 8, 0, 9, 1          # libretro ids
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7

LIGHT_PUNCH, STRONG_PUNCH = 5, 6
STRONG_NORMALS = {6, 8, 20, 22, 24, 26}
SPECIALS = set(range(48, 67))
SUPERS = set(range(85, 90))


def tap(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def start_close(core, select_state, power=None):
    enter_fight(core, select_state, "kyo", "kyo")
    core.put(F_X, 120 << 8)
    core.put(F_X + FP2, 150 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    if power is not None:
        core.put(F_POWER, power)
    core.step(10)


def connect_normal(core, button, expected_state):
    """Press a normal and wait for contact + hitstop, leaving the move live."""
    tap(core, {button})
    for _ in range(40):
        if core.ram[F_HITDONE] or core.word(F_HP + FP2) < 200:
            break
        core.step()
    else:
        raise AssertionError(f"normal {expected_state} never connected")
    for _ in range(40):
        if core.ram[0x1073] == 0:
            break
        core.step()
    if core.ram[F_STATE] != expected_state:
        raise AssertionError(
            f"normal {expected_state} recovered before the cancel test: "
            f"state={core.ram[F_STATE]}")


def buffer_qcf(core, count=1):
    for _ in range(count):
        for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
            core.buttons[0] = set(direction)
            core.step(2)
            core.buttons[0] = set()


def check_strong_self_cancel_rejected(core, select_state):
    """Strong punch must not chain into strong punch or strong kick."""
    for follow in (X, A):
        start_close(core, select_state)
        connect_normal(core, X, STRONG_PUNCH)
        for _ in range(24):
            if core.ram[F_STATE] != STRONG_PUNCH:
                break
            core.buttons[0] = {follow}
            core.step(1)
            core.buttons[0] = set()
            state = core.ram[F_STATE]
            if state in STRONG_NORMALS and state != STRONG_PUNCH:
                raise AssertionError(
                    f"strong punch canceled into strong state {state} "
                    f"(button {follow})")
            core.step(1)
    print("PASS strong punch did not cancel into strong punch/kick", flush=True)


def check_weak_followup_rejected(core, select_state):
    start_close(core, select_state)
    connect_normal(core, Y, LIGHT_PUNCH)
    for _ in range(24):
        state = core.ram[F_STATE]
        if state in STRONG_NORMALS:
            raise AssertionError(
                f"weak follow-up chained into strong state {state}")
        if state == 0:
            break
        tap(core, {Y})
        core.step(1)
    print("PASS weak follow-up stayed on the light normal", flush=True)


def check_whiff_rejected(core, select_state):
    enter_fight(core, select_state, "kyo", "kyo")
    core.put(F_X, 120 << 8)
    core.put(F_X + FP2, 230 << 8)          # out of the punch's reach
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.step(10)
    tap(core, {X})                         # strong punch, no contact
    if core.ram[F_STATE] != STRONG_PUNCH:
        raise AssertionError("whiff setup did not start the strong punch")
    for _ in range(24):
        if core.ram[F_STATE] != STRONG_PUNCH:
            break
        core.buttons[0] = {A}              # strong kick would be the old chain
        core.step(1)
        core.buttons[0] = set()
        if core.ram[F_STATE] == 8:
            raise AssertionError("whiffed strong punch chained into strong kick")
        core.step(1)
    print("PASS whiffed strong punch did not chain", flush=True)


def check_weak_special(core, select_state):
    start_close(core, select_state)
    connect_normal(core, Y, LIGHT_PUNCH)
    buffer_qcf(core)
    tap(core, {Y})                         # QCF + weak punch
    for _ in range(30):
        state = core.ram[F_STATE]
        if state in SPECIALS:
            print(f"PASS light {LIGHT_PUNCH} -> weak-button special {state}",
                  flush=True)
            return
        core.step()
    raise AssertionError(
        f"weak-button special did not cancel from light punch: "
        f"state={core.ram[F_STATE]}")


def check_strong_special(core, select_state):
    start_close(core, select_state)
    connect_normal(core, Y, LIGHT_PUNCH)
    buffer_qcf(core)
    tap(core, {X})                         # QCF + strong punch
    for _ in range(30):
        state = core.ram[F_STATE]
        if state in SPECIALS:
            print(f"PASS light {LIGHT_PUNCH} -> strong-button special {state}",
                  flush=True)
            return
        core.step()
    raise AssertionError(
        f"strong-button special did not cancel from light punch: "
        f"state={core.ram[F_STATE]}")


def check_super(core, select_state, button, label):
    start_close(core, select_state, power=1000)
    connect_normal(core, Y, LIGHT_PUNCH)
    power_before = core.word(F_POWER)
    buffer_qcf(core, count=2)
    tap(core, {button})                    # QCFx2 + weak/strong punch
    for _ in range(30):
        state = core.ram[F_STATE]
        if state in SUPERS:
            power_after = core.word(F_POWER)
            if power_before - power_after < 1000:
                raise AssertionError(
                    f"{label} super {state} did not spend a stock: "
                    f"{power_before} -> {power_after}")
            print(f"PASS light {LIGHT_PUNCH} -> {label} super {state} "
                  f"({power_before} -> {power_after} power)", flush=True)
            return
        core.step()
    raise AssertionError(
        f"{label} super did not cancel from light punch: "
        f"state={core.ram[F_STATE]}")


def check_weak_super(core, select_state):
    check_super(core, select_state, Y, "weak-button")


def check_strong_super(core, select_state):
    check_super(core, select_state, X, "strong-button")


def main(core_path, rom):
    core = Core(core_path, rom)
    failed = []
    try:
        select_state = boot_select(core)
        for name, check in (
                ("strong self-cancel", check_strong_self_cancel_rejected),
                ("weak follow-up", check_weak_followup_rejected),
                ("whiff", check_whiff_rejected),
                ("weak special", check_weak_special),
                ("strong special", check_strong_special),
                ("weak super", check_weak_super),
                ("strong super", check_strong_super)):
            try:
                check(core, select_state)
                core.buttons = [set(), set()]
                core.step(20)
            except AssertionError as exc:
                failed.append(f"{name}: {exc}")
    finally:
        core.close()
    if failed:
        raise AssertionError("; ".join(failed))
    print("PASS normal -> weak/strong special or super routes",
          flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
