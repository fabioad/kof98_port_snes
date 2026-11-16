#!/usr/bin/env python3
"""Headless regression for Iori's Aoi Hana (QCB+P three-part rekka).

KOF98's Aoi Hana is a three-part rekka: each follow-up is a fresh QCB+P
(weak or strong).  Parts 1 and 2 must keep the victim in hitstun; only the
third jumping double-palm knocks down.  The source auto-chain rows used to
knock the victim down on the first contact, so the third part never landed
in the port.

Run after a PVSnesLib build:

    python3 tools/test_iori_aoi_hana_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_HITDONE, F_HP = 0x4008, 0x401A, 0x4010
FP2 = 0x40
START = 3
DOWN, LEFT = 5, 6
Y, X = 1, 9                    # SNES Y = weak punch, SNES X = strong punch

# Iori's Aoi Hana runtime sids.
PART1_W, PART1_S = 61, 66
PART2_W, PART2_S = 63, 68
PART3_W, PART3_S = 62, 64
S_DOWN = 10


def qcb(core, button, hold=2):
    """One full down, down-back, back + punch motion."""
    for direction in ((DOWN,), (DOWN, LEFT), (LEFT,)):
        core.buttons[0] = set(direction)
        core.step(hold)
    core.buttons[0] = {button}
    core.step(hold)
    core.buttons[0] = set()


def fresh_fight(core, select):
    enter_fight(core, select, "iori", "kyo")
    core.put(0x4000, 120 << 8)
    core.put(0x4040, 150 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.put(0x4030, 3000)
    core.step(10)


def wait_hit(core, hp_before, label, limit=80):
    # Use actual HP loss, not F_HITDONE: the flag can survive the state
    # handoff on the same tick and made the next part look connected early.
    for _ in range(limit):
        hp = core.word(F_HP + FP2)
        if hp < hp_before:
            return hp
        core.step()
    raise AssertionError(f"{label}: no contact (hp={core.word(F_HP + FP2)})")


def wait_state(core, states, label, limit=80):
    for _ in range(limit):
        if core.ram[F_STATE] in states:
            return
        core.step()
    raise AssertionError(f"{label}: states={core.ram[F_STATE]} not in {states}")


def run_chain(core, select, first_button, second_button, third_button,
              expected):
    fresh_fight(core, select)
    first, second, third = expected
    seen = set()
    seen_v = set()
    qcb(core, first_button)
    for tick in range(120):
        seen.add(core.ram[F_STATE])
        seen_v.add(core.ram[F_STATE + FP2])
        if tick == 12:
            qcb(core, second_button)
        elif tick == 28:
            qcb(core, third_button)
        core.step()
    for state in (first, second, third):
        if state not in seen:
            raise AssertionError(
                f"expected part {state} missing; seen={sorted(seen)}")
    if S_DOWN not in seen_v:
        raise AssertionError(
            f"third part did not knock down; victim states={sorted(seen_v)}")
    return core.word(F_HP + FP2)


def run_whiff(core, select):
    """No follow-up input: part 1 ends and never reaches parts 2/3."""
    fresh_fight(core, select)
    qcb(core, Y)
    wait_state(core, {PART1_W}, "part 1")
    wait_hit(core, 200, "part 1")
    seen = set()
    for _ in range(90):
        seen.add(core.ram[F_STATE])
        if core.ram[F_STATE] == 0:
            break
        core.step()
    if seen & {PART2_W, PART2_S, PART3_W, PART3_S}:
        raise AssertionError(f"whiffed follow-up auto-chained: {sorted(seen)}")


def main(args):
    core = Core(args.core, args.rom)
    try:
        select = boot_select(core)
        # Weak -> strong -> weak.
        hp = run_chain(core, select, Y, X, Y, (PART1_W, PART2_S, PART3_W))
        print(f"PASS Iori Aoi Hana W->S->W (victim hp {hp})", flush=True)
        # Strong -> weak -> strong.
        hp = run_chain(core, select, X, Y, X, (PART1_S, PART2_W, PART3_S))
        print(f"PASS Iori Aoi Hana S->W->S (victim hp {hp})", flush=True)
        run_whiff(core, select)
        print("PASS Iori Aoi Hana recovers when the follow-up is not input",
              flush=True)
        print("PASS Iori Aoi Hana: three-part rekka and knockdown", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", default=str(ROOT / "kof98-snes.sfc"))
    main(parser.parse_args())
