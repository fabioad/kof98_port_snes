#!/usr/bin/env python3
"""Headless regression for Kyo's Aragami/Dokugami three-part rekka.

KOF98's QCF+P Aragami chain is input one part at a time: each follow-up is a
fresh QCF+P (weak or strong).  The port used to auto-chain on MoveHit and
stopped at the second part; the missing third part is the Kototsuki grab,
where Kyo lifts the opponent and drops him with a fire explosion.

Run after a PVSnesLib build:

    python3 tools/test_kyo_aragami_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_HP = 0x4008, 0x4010
F_GRAB = 0x4034                # word; bit1 = victim uses attacker sprites
FP2 = 0x40
SPARKS, SPK_SIZE, SPK_ATTR = 0x4200, 20, 15
DOWN, RIGHT = 5, 7
Y, X = 1, 9                    # SNES Y = weak punch, SNES X = strong punch

# Kyo's Aragami/Dokugami runtime sids.
PART1_W, PART1_S = 61, 66
PART2_W, PART2_S = 63, 68
PART3 = 115                    # 1630 grab, auto-chains to 116 (1631)
S_VHELD = 76
S_VTHROW = 77
S_DOWN = 10


def sample(core, seen, seen_v, grab_flags):
    """Step one frame and record states plus the victim's sprite source."""
    seen.add(core.ram[F_STATE])
    seen_v.add(core.ram[F_STATE + FP2])
    grab_flags.append(core.word(F_GRAB + FP2))


def projectile_fired(core):
    """SPK_ATTR bit7 marks a pooled shot; hit sparks do not set it."""
    return any(core.ram[SPARKS + slot * SPK_SIZE + SPK_ATTR] & 0x80
               for slot in range(2))


def qcf(core, button, hold=3):
    """One full down, down-forward, forward + punch motion."""
    for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
        core.buttons[0] = set(direction)
        core.step(hold)
    core.buttons[0] = {button}
    core.step(hold)
    core.buttons[0] = set()


def fresh_fight(core, select):
    enter_fight(core, select, "kyo", "iori")
    core.put(0x4000, 110 << 8)
    core.put(0x4040, 140 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.put(0x4030, 3000)
    core.step(20)


def wait_hit(core, hp_before, label, limit=80):
    for _ in range(limit):
        hp = core.word(F_HP + FP2)
        if hp < hp_before:
            return hp
        core.step()
    raise AssertionError(f"{label}: no contact (hp={core.word(F_HP + FP2)})")


def run_chain(core, select, first_button, second_button, third_button,
              expected):
    fresh_fight(core, select)
    first, second, third = expected
    seen = set()
    seen_v = set()
    grab_flags = []
    fired = False
    qcf(core, first_button)
    for _ in range(16):
        sample(core, seen, seen_v, grab_flags)
        fired |= projectile_fired(core)
        core.step()
    qcf(core, second_button)
    for _ in range(20):
        sample(core, seen, seen_v, grab_flags)
        fired |= projectile_fired(core)
        core.step()
    qcf(core, third_button)
    for _ in range(100):
        sample(core, seen, seen_v, grab_flags)
        fired |= projectile_fired(core)
        core.step()
    if fired:
        raise AssertionError(
            "Aragami/Dokugami is melee but spawned a travelling projectile")
    if any(grab & 0x0002 for grab in grab_flags):
        raise AssertionError(
            "held/thrown victim was drawn with the attacker's sprites "
            "(F_GRAB bit1 set)")
    for state in (first, second, third):
        if state not in seen:
            raise AssertionError(
                f"expected part {state} missing; seen={sorted(seen)}")
    if S_VHELD not in seen_v or S_VTHROW not in seen_v:
        raise AssertionError(
            f"grab did not hold/throw the victim; victim states="
            f"{sorted(seen_v)}")
    if S_DOWN not in seen_v:
        raise AssertionError(
            f"victim did not land after the fire drop; victim states="
            f"{sorted(seen_v)}")
    return core.word(F_HP + FP2)


def run_whiff(core, select):
    """No follow-up input: part 1 ends and never reaches parts 2/3."""
    fresh_fight(core, select)
    qcf(core, Y)
    hp = wait_hit(core, 200, "part 1")
    seen = set()
    for _ in range(100):
        seen.add(core.ram[F_STATE])
        if core.ram[F_STATE] == 0:
            break
        core.step()
    if seen & {PART2_W, PART2_S, PART3}:
        raise AssertionError(f"whiffed follow-up auto-chained: {sorted(seen)}")
    return hp


def main(args):
    core = Core(args.core, args.rom)
    try:
        select = boot_select(core)
        hp = run_chain(core, select, Y, X, Y, (PART1_W, PART2_S, PART3))
        print(f"PASS Kyo Aragami W->S->grab (victim hp {hp})", flush=True)
        hp = run_chain(core, select, X, Y, X, (PART1_S, PART2_W, PART3))
        print(f"PASS Kyo Dokugami S->W->grab (victim hp {hp})", flush=True)
        hp = run_whiff(core, select)
        print(f"PASS Kyo Aragami recovers without a follow-up "
              f"(victim hp {hp})", flush=True)
        print("PASS Kyo Aragami: three-part rekka, grab and fire drop",
              flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", default=str(ROOT / "kof98-snes.sfc"))
    main(parser.parse_args())
