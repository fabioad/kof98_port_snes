#!/usr/bin/env python3
"""Headless regression for ReversalDef counter-grabs.

A counter stance must turn the opponent's hit into a throw: the parrying
fighter enters the actor slot (99/101), the incoming attacker enters the
held-victim slot (100/102), and (except for Heidern's drain follow-up, which
is not wired yet) the victim loses life.

Run after a PVSnesLib build:

    python3 tools/test_counter_grab_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_roster import parse_tables                     # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS, F_STATE, F_X, F_HP = 0x1020, 0x4008, 0x4000, 0x4010
FP2 = 0x40
START, A, B, X, Y = 3, 8, 0, 9, 1
UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7

# name -> (stance sid, counter button, direction tail, low slot, crouch hit)
CASES = {
    "geese": (51, A, ((RIGHT,), (RIGHT, DOWN), (DOWN,), (DOWN, LEFT),
                      (LEFT,)), False, False),
    "mary": (50, B, ((DOWN,), (DOWN, LEFT), (LEFT,)), False, False),
    "mary_low": (51, A, ((DOWN,), (DOWN, LEFT), (LEFT,)), True, True),
    "heidern": (55, B, ((RIGHT,), (RIGHT, DOWN), (DOWN,), (DOWN, LEFT),
                        (LEFT,)), False, False),
    "takuma": (56, Y, ((RIGHT,), (RIGHT, DOWN), (DOWN,), (DOWN, LEFT),
                       (LEFT,)), False, False),
}
ACTOR = {False: (99, 100), True: (101, 102)}


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def wait(core, pred, label, limit=8000):
    for _ in range(limit):
        if pred():
            return
        core.step()
    raise AssertionError(f"{label}: gs={core.word(GS)}")


def boot_select(core):
    wait(core, lambda: core.word(GS) == 7, "opening")
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(60)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    core.ram[0xF070] = 1
    tap(core, START)
    wait(core, lambda: core.word(GS) == 5, "select")
    core.ram[0x1091] = 0
    core.step(10)
    return core.save()


def enter_fight(core, select_state, p1, p2):
    roster = {v["name"]: v for v in parse_tables().values()}
    core.load(select_state)
    core.buttons = [set(), set()]
    core.step(4)
    for side, char, lock in ((0, p1, 0x108E), (1, p2, 0x108F)):
        core.ram[0xF052 + side] = roster[char]["cell"]
        for _ in range(10):
            core.step(4)
            tap(core, A, side)
            if core.ram[lock] == 1:
                break
        else:
            raise AssertionError(f"side {side + 1} did not lock")
    tap(core, START)
    wait(core, lambda: core.word(GS) == 1, "fight live")
    wait(core, lambda: core.ram[F_STATE] == 0 and
         core.ram[F_STATE + FP2] == 0, "idle")
    core.step(40)


def main(core_path, rom):
    core = Core(core_path, rom)
    failed = []
    try:
        select_state = boot_select(core)
        for name, (stance, button, seq, low, crouch) in CASES.items():
            p1 = "mary" if name == "mary_low" else name
            enter_fight(core, select_state, p1, "kyo")
            core.put(F_X, 150 << 8)
            core.put(F_X + FP2, 190 << 8)
            core.step(10)

            for d in seq:
                core.buttons[0] = set(d)
                core.step(2)
            core.buttons[0] = set()
            for _ in range(30):            # let crouch->stand finish
                if core.ram[F_STATE] == 0:
                    break
                core.step()
            core.buttons[0] = {button}
            core.step(3)
            core.buttons[0] = set()
            if core.ram[F_STATE] != stance:
                failed.append(f"{name}: stance {core.ram[F_STATE]} != {stance}")
                continue

            # Attack only after the reversal stance is confirmed.  Pressing
            # both pads together let a fast jab connect before the counter
            # was armed, so the test saw a normal hit instead of the grab.
            if crouch:
                core.buttons[1] = {DOWN}
                core.step(4)
                core.buttons[1] = {DOWN, Y}
                core.step(3)
            else:
                core.buttons[1] = {Y}
                core.step(3)
            core.buttons[1] = set()

            actor, victim = ACTOR[low]
            hp0 = core.word(F_HP + FP2)
            grabbed = False
            for _ in range(200):
                if (core.ram[F_STATE] == actor
                        and core.ram[F_STATE + FP2] == victim):
                    grabbed = True
                core.step()
            hp1 = core.word(F_HP + FP2)
            if not grabbed:
                failed.append(f"{name}: no counter-grab")
            elif name not in ("heidern", "mary_low") and hp1 >= hp0:
                failed.append(f"{name}: held victim took no damage")
            else:
                print(f"PASS {name}: grab + {hp0 - hp1} damage", flush=True)
            core.buttons = [set(), set()]
            core.step(20)
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
