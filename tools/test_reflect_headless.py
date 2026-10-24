#!/usr/bin/env python3
"""Headless projectile-reflection regression.

Every character with a reflection window in ReflectTab must reverse an
incoming projectile: the owner bit flips to the reflector and VX changes
sign.  The test injects a real P2 projectile into the shield box, so it does
not depend on projectile timing, and verifies the bounce in the live engine.

Cases:
  athena - QCB+B enters Reflective Shield (sid 51); DP+P is Psycho Sword
  rugal  - Dark Barrier (sid 54); the state window is pinned because the
           command recognizer is covered by the roster/move tests.
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
SPARKS = 0x4200
START, A, B, D, R, L = 3, 8, 0, 5, 7, 6

CASES = {
    # name: (target state, motion before the attack button, attack button)
    # Athena's QCB+K is the Reflective Shield; QCB+P is the Psychic Ball
    # and DP+P is now the Psycho Sword.
    "athena": (51, ({D}, {D, L}, {L}), A),
    "rugal": (54, None, A),
}


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
    path = ROOT / "kof98-snes.sym"
    if not path.exists():
        path = ROOT / "kof98-snes.symfull"
    result = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) == 2:
            result[fields[1]] = int(fields[0], 16)
    return result


def enter_match(core, roster, p1, p2="ryu"):
    wait(core, lambda: core.word(GS) == 7, "opening")
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(60)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    core.ram[0xF070] = 1
    tap(core, START)
    wait(core, lambda: core.word(GS) == 5, "select")
    # The headless loader starts the match from the selection bytes; this is
    # the same path used by calibration/headless.py and avoids cursor timing.
    core.ram[0x1085] = roster[p1]["id"]
    core.ram[0x1086] = roster[p2]["id"]
    core.ram[0x108E] = 1
    core.ram[0x108F] = 1
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.step(10)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 1, "fight live")
    wait(core, lambda: core.ram[F_STATE] == 0 and
         core.ram[F_STATE + 0x40] == 0, "idle")


def enter_special(core, directions, state, button):
    for direction in directions:
        core.buttons[0] = direction
        core.step(2)
    core.buttons[0] = directions[-1] | {button}
    core.step(3)
    core.buttons[0] = set()
    wait(core, lambda: core.ram[F_STATE] == state, f"state {state}")


def run_case(core_path, rom, roster, name):
    state, directions, button = CASES[name]
    syms = symbols()
    core = Core(core_path, rom)
    try:
        enter_match(core, roster, name)
        if directions is None:
            core.ram[F_STATE] = state
            core.put(F_STIME, 20)
        else:
            enter_special(core, directions, state, button)

        ax = core.word(F_X) >> 8
        core.put(SPARKS, ax + 70)         # inside the shield before it moves
        core.put(SPARKS + 2, 150)
        core.put(SPARKS + 4, syms["ryuProjFxAnim"] & 0xFFFF)
        core.ram[SPARKS + 6] = 0          # frame index
        core.ram[SPARKS + 7] = 2          # frame ticks
        core.put(SPARKS + 8, 0xFC00)      # -4.0 px/tick, owned by P2
        core.put(SPARKS + 10, 0)
        core.put(SPARKS + 12, 14)         # damage
        core.ram[SPARKS + 14] = 85        # TTL
        core.ram[SPARKS + 15] = 0xF0      # projectile | P2 owner | special | left
        core.ram[SPARKS + 16] = 117       # Ryu projectile data bank

        for _ in range(300):
            if directions is None:
                # Keep the window active while the injected projectile
                # crosses it; command entry is not what this test measures.
                core.ram[F_STATE] = state
                core.put(F_STIME, 20)
            attr = core.ram[SPARKS + 15]
            vx = core.word(SPARKS + 8)
            if not (attr & 0x40) and vx > 0:
                print(f"PASS {name} reflected attr=${attr:02X} vx={vx}")
                return
            if core.word(SPARKS + 4) == 0:
                raise AssertionError(f"{name}: projectile was consumed, "
                                     "not reflected")
            core.step()
        raise AssertionError(f"{name}: projectile never reflected")
    finally:
        core.close()


def main(core_path, rom, cases):
    roster = {v["name"]: {**v, "id": i}
              for i, v in parse_tables().items()}
    for name in cases:
        if name not in roster:
            raise AssertionError(f"{name} is not in the roster")
        run_case(core_path, rom, roster, name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    parser.add_argument("--case", choices=sorted(CASES), action="append",
                        help="run only this reflector (default: all)")
    args = parser.parse_args()
    main(args.core, args.rom, args.case or sorted(CASES))
