#!/usr/bin/env python3
"""Headless projectile-guard regression.

Injects real projectiles into the spark pool and checks that a defender
holding back blocks guardable shots (guard-hit state 30, chip damage), while
unblockable shots and the wrong posture still connect (hit state 9).

Also verifies that cosmetic sparks (SPK_ATTR bit7 clear) never hit, now that
ProjHit is gated on the projectile flag.

Run with the built ROM:
    python3 tools/test_projectile_guard_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_roster import parse_tables                     # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
F_STATE = 0x4008
F_STIME = 0x403C
F_X = 0x4000
HP1 = 0x4010
SPARKS = 0x4200
START, UP, DOWN, LEFT, RIGHT, A, B, X, Y = 3, 4, 5, 6, 7, 8, 0, 9, 1

S_HIT = 9
S_GHIT = 30
S_CROUCH = 3


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(10)


def wait(core, predicate, label, limit=8000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(f"{label}: gs={core.word(GS)}")


def symbols():
    path = ROOT / "kof98-snes.symfull"
    if not path.exists():
        path = ROOT / "kof98-snes.sym"
    result = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) == 2:
            result[fields[1]] = int(fields[0], 16)
    return result


def enter_match(core, roster, p1, p2):
    """Enter a human-vs-human fight through the real menus.

    The old direct-RAM shortcut could land in the attract demo (gs=4), where
    the engine ignores pad input: the guard cases then saw a raw hit because
    holding back never reached F_JOY.  Reuse the menu/select flow that the
    other headless fight tests already validate.
    """
    from test_counter_grab_headless import boot_select, enter_fight
    select_state = boot_select(core)
    enter_fight(core, select_state, p1, p2)


def inject(core, syms, guard, attr=0xF0, damage=14):
    """Place an idle-adjacent P2 projectile in spark slot 0."""
    px = core.word(F_X) >> 8
    core.put(SPARKS, px + 20)
    core.put(SPARKS + 2, 150)                 # standing torso
    core.put(SPARKS + 4, syms["ryuProjFxAnim"] & 0xFFFF)
    core.ram[SPARKS + 6] = 0                  # frame index
    core.ram[SPARKS + 7] = 2                  # frame ticks
    core.put(SPARKS + 8, (-4 * 256) & 0xFFFF)  # P2 shot travelling left
    core.put(SPARKS + 10, 0)
    core.put(SPARKS + 12, damage)
    core.ram[SPARKS + 14] = 85                # TTL
    core.ram[SPARKS + 15] = attr              # bit7 hitbox, bit6 P2 owner
    core.ram[SPARKS + 16] = 117               # Ryu projectile data bank
    core.ram[SPARKS + 17] = 0
    core.ram[SPARKS + 18] = guard             # H/M/L/A mask
    core.ram[SPARKS + 19] = 0


def run_shot(core, syms, guard, held, expect_state, damage=14):
    core.buttons[0] = set(held)
    # Let crouch/guard stances settle before the shot arrives.
    core.step(8)
    core.put(HP1, 336)
    inject(core, syms, guard, damage=damage)
    hp0 = core.word(HP1)
    for _ in range(40):
        core.step()
        state = core.ram[F_STATE]
        if state in (S_HIT, S_GHIT):
            # The state byte can become visible on the frame before the HP
            # store lands (input timing shifts contact by a tick), so let
            # the damage/chip settle before sampling HP.
            core.step()
            hp1 = core.word(HP1)
            core.buttons[0] = set()
            return state, hp0 - hp1
    core.buttons[0] = set()
    raise AssertionError(f"projectile never connected (state={core.ram[F_STATE]})")


def run_case(core_path, rom, name):
    roster = {v["name"]: {**v, "id": i}
              for i, v in parse_tables().items()}
    syms = symbols()
    core = Core(core_path, rom)
    try:
        enter_match(core, roster, "kyo", "ryu")
        baseline = core.save()

        def case(guard, held, expect_state, expect_chip=None):
            core.load(baseline)
            core.buttons[0] = set()
            state, chip = run_shot(core, syms, guard, held, expect_state)
            assert state == expect_state, (
                f"{name}: guard=${guard:02X} held={held} -> state {state}, "
                f"expected {expect_state}")
            if expect_chip is not None:
                assert chip == expect_chip, (
                    f"{name}: guard=${guard:02X} chip={chip}, "
                    f"expected {expect_chip}")
            return chip

        # MA shot: back blocks, no input gets hit full damage.
        case(0xA0, {LEFT}, S_GHIT, 1)
        case(0xA0, set(), S_HIT, 14)
        # L-only: crouch blocks, standing gets hit.
        case(0x40, {LEFT, DOWN}, S_GHIT, 1)
        case(0x40, {LEFT}, S_HIT, 14)
        # H-only: standing blocks, crouching gets hit.
        case(0x10, {LEFT}, S_GHIT, 1)
        case(0x10, {LEFT, DOWN}, S_HIT, 14)
        # Explicitly unblockable: holding back still takes the full hit.
        case(0x00, {LEFT}, S_HIT, 14)

        # Cosmetic spark (bit7 clear) must never hit, even adjacent and while
        # the victim is holding back.
        core.load(baseline)
        core.buttons[0] = {LEFT}
        core.step(8)
        core.put(HP1, 336)
        inject(core, syms, 0xA0, attr=0x30, damage=14)
        for _ in range(20):
            core.step()
            assert core.ram[F_STATE] not in (S_HIT, S_GHIT), (
                "cosmetic spark entered a hit state")
        assert core.word(HP1) == 336, "cosmetic spark dealt damage"
        core.buttons[0] = set()
        print(f"PASS {name}: projectile guard masks and cosmetic-spark gate")
    finally:
        core.close()


def main(core_path, rom):
    for name in ("guard",):
        run_case(core_path, rom, name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, args.rom)
