#!/usr/bin/env python3
"""Ralf/Clark Vulcan Punch: multi-hit hitstun with pushback, no launcher.

A grounded opponent must take every contact standing in hitstun and slide
back; the move must not force a knockdown on the fifth contact.  An airborne
opponent still takes contacts through the air-velocity branch.

Run after a PVSnesLib build:

    python3 tools/test_vulcan_punch_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_X, F_Y, F_VY, F_STATE, F_HP = 0, 2, 6, 8, 0x10
COMBO = 0x4FC0
DOWN, RIGHT = 5, 7
X_BTN, Y_BTN = 9, 1
QCF = ((DOWN,), (DOWN, RIGHT), (RIGHT,))
VULCAN_SIDS = (48, 49)
S_HIT, S_DOWN = 9, 10


def qcf(core, button):
    for direction in QCF:
        core.buttons[0] = set(direction)
        core.step(3)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()


def run(core, select_state, char, button, distance, air_height=None):
    enter_fight(core, select_state, char, "kyo")
    core.ram[0x1090] = 0                 # human P2: no AI interference
    core.ram[0x1091] = 0
    core.put(FP1 + F_X, (140 - distance // 2) << 8)
    core.put(FP2 + F_X, (140 + distance // 2) << 8)
    core.put(FP1 + F_HP, 200)
    core.put(FP2 + F_HP, 200)
    core.step(20)

    if air_height is not None:
        # Isolate the airborne branch: keep the victim suspended while the
        # punch flurry arrives, as test_air_juggle does for projectiles.
        core.ram[FP2 + F_STATE] = S_DOWN
        core.put(FP2 + F_Y, air_height << 8)
        core.put(FP2 + F_VY, 0)
        core.step(2)

    hp0 = core.word(FP2 + F_HP)
    x0 = core.word(FP2 + F_X)
    qcf(core, button)

    peak = 0
    max_y = 0
    max_x = x0
    p1_states = set()
    states = []
    for _ in range(220):
        core.step()
        if air_height is not None:
            core.put(FP2 + F_Y, air_height << 8)
            core.put(FP2 + F_VY, 0)
        peak = max(peak, core.ram[COMBO])
        p1_states.add(core.ram[FP1 + F_STATE])
        max_y = max(max_y, core.word(FP2 + F_Y) >> 8)
        max_x = max(max_x, core.word(FP2 + F_X))
        state = core.ram[FP2 + F_STATE]
        if not states or states[-1] != state:
            states.append(state)

    return dict(peak=peak, damage=hp0 - core.word(FP2 + F_HP),
                max_y=max_y, push=(max_x - x0) >> 8,
                p1_states=p1_states, states=states)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        for char in ("ralf", "clark"):
            for button, label in ((X_BTN, "weak"), (Y_BTN, "strong")):
                for distance in (24, 40, 60):
                    hit = run(core, select_state, char, button, distance)
                    if not hit["p1_states"] & set(VULCAN_SIDS):
                        raise AssertionError(
                            f"{char} {label}: Vulcan state not entered "
                            f"({sorted(hit['p1_states'])})")
                    if hit["peak"] < 4:
                        raise AssertionError(
                            f"{char} {label} at {distance}px: only "
                            f"{hit['peak']} contacts, wanted 4+")
                    if hit["damage"] < 16:
                        raise AssertionError(
                            f"{char} {label} at {distance}px: damage "
                            f"{hit['damage']}, wanted 16+")
                    if hit["max_y"] != 0:
                        raise AssertionError(
                            f"{char} {label} at {distance}px: grounded "
                            f"victim was launched to y={hit['max_y']}")
                    if S_DOWN in hit["states"]:
                        raise AssertionError(
                            f"{char} {label} at {distance}px: forced a "
                            f"knockdown ({hit['states']})")
                    if S_HIT not in hit["states"]:
                        raise AssertionError(
                            f"{char} {label} at {distance}px: victim never "
                            f"entered hitstun ({hit['states']})")
                    if hit["push"] < 40:
                        raise AssertionError(
                            f"{char} {label} at {distance}px: pushback "
                            f"{hit['push']}px, wanted 40+")

                air = run(core, select_state, char, button, 24, air_height=4)
                if air["peak"] < 1 or air["damage"] <= 0:
                    raise AssertionError(
                        f"{char} {label} airborne: combo={air['peak']} "
                        f"damage={air['damage']}")

        print("PASS Vulcan Punch: grounded victims take 4+ contacts in "
              "hitstun with 40+ px pushback and no knockdown; airborne "
              "victims still take contacts", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
