#!/usr/bin/env python3
"""Headless regression for Iori's Yami Barai flaming projectile.

108 Shiki: Yami Barai (sids 48/49) is a travelling ground flame again.  The
port imports the arcade KOF'98 flame clip and recolours it with Iori's purple
ramp; the shot must spawn from the launch state, travel forward along the
floor, connect with a distant dummy and keep the source damage (14 weak /
18 strong).

Run after a PVSnesLib build:

    python3 tools/test_iori_yami_projectile_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_HP, F_X = 0x4008, 0x4010, 0x4000
FP2 = 0x40
SPARKS, SPK_SIZE, SPK_ATTR = 0x4200, 20, 15
DOWN, RIGHT = 5, 7
Y, X = 1, 9                    # SNES Y = mugen x (weak), X = mugen y (strong)
WEAK, STRONG = 48, 49


def qcf(core, button, hold=3):
    for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
        core.buttons[0] = set(direction)
        core.step(hold)
    core.buttons[0] = {button}
    core.step(hold)
    core.buttons[0] = set()


def projectile_x(core):
    """X of the pooled shot, or None.  SPK_ATTR bit7 marks a shot."""
    for slot in range(2):
        base = SPARKS + slot * SPK_SIZE
        if core.ram[base + SPK_ATTR] & 0x80:
            return core.word(base)
    return None


def run(core, select, button, sid, damage):
    enter_fight(core, select, "iori", "kyo")
    core.put(F_X, 60 << 8)
    core.put(F_X + FP2, 190 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.step(25)

    qcf(core, button)
    seen = False
    xs = []
    hit = False
    for _ in range(140):
        if core.ram[F_STATE] == sid:
            seen = True
        x = projectile_x(core)
        if x is not None:
            xs.append(x)
        if core.word(F_HP + FP2) < 200:
            hit = True
        core.step()
        if seen and not xs and core.ram[F_STATE] == 0:
            break

    if not seen:
        raise AssertionError(f"Yami Barai did not enter state {sid}")
    if not xs:
        raise AssertionError(
            f"Yami Barai sid {sid} did not spawn a travelling projectile")
    if len(xs) < 8 or xs[-1] <= xs[0]:
        raise AssertionError(
            f"Yami Barai sid {sid} shot did not travel: {xs}")
    if not hit:
        raise AssertionError(
            f"Yami Barai sid {sid} shot never reached the opponent")
    lost = 200 - core.word(F_HP + FP2)
    if lost != damage:
        raise AssertionError(
            f"Yami Barai sid {sid}: damage {lost}, expected {damage}")
    if core.ram[F_STATE + FP2] not in (0, 9):
        raise AssertionError(
            f"victim did not enter hitstun; state={core.ram[F_STATE + FP2]}")
    return lost, xs[0], xs[-1]


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select = boot_select(core)
        lost, x0, x1 = run(core, select, X, STRONG, 18)
        print(f"PASS Iori Yami Barai strong: shot {x0}->{x1}, {lost} damage",
              flush=True)
        lost, x0, x1 = run(core, select, Y, WEAK, 14)
        print(f"PASS Iori Yami Barai weak: shot {x0}->{x1}, {lost} damage",
              flush=True)
        print("PASS Iori Yami Barai: purple flame projectile travels and hits",
              flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path,
                        default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, args.rom)
