#!/usr/bin/env python3
"""Headless regression for the Chin fixes.

Covers:
  * DP weak (state 1450) lands through 1402 and recovers promptly;
  * DP strong (1400 -> 1401 -> 1402) is reachable with the strong punch;
  * the QCFx2 Zake FireBall weak/strong supers use the 85-89 multi-contact
    path (five hits, ~45 HP) and spend one stock;
  * the CD blowback no longer spends 1000 power nor flashes/darkens the
    screen like a super.

Run after a PVSnesLib build:

    python3 tools/test_chin_fixes_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                          # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE, F_X, F_Y = 8, 0, 2
HP2 = FP2 + 0x10
POW1 = FP1 + 0x30
SPARKS = 0x4200
SPK_SIZE = 20
SUPERFX = 0x51F0
DOWN, RIGHT = 5, 7
D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
QCF = (D, DF, F)
DP = (F, D, DF)
WEAK, STRONG = 1, 9          # libretro Y = mugen x; X = mugen y


def feed(core, seq, button, hold=3):
    for direction in seq:
        core.buttons[0] = set(direction)
        core.step(hold)
    core.buttons[0] = ({button} if isinstance(button, int) else set(button))
    core.step(3)
    core.buttons[0] = set()


def run(seq, button, p2x, ticks=220):
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "chin", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(FP1, 100 << 8)
        core.put(FP2, p2x << 8)
        core.put(HP2, 200)
        core.put(POW1, 3000)
        core.step(30)
        feed(core, seq, button)

        states = []
        peak_y = 0
        hp_min = 200
        power_min = 3000
        shots = 0
        superfx = 0
        elapsed = 0
        for tick in range(ticks):
            core.step()
            state = core.ram[FP1 + F_STATE]
            if not states or states[-1] != state:
                states.append(state)
            peak_y = max(peak_y, core.word(FP1 + F_Y))
            hp_min = min(hp_min, core.word(HP2))
            power_min = min(power_min, core.word(POW1))
            shots = max(shots, sum(
                1 for slot in range(2)
                if core.ram[SPARKS + slot * SPK_SIZE + 15]))
            superfx = max(superfx, core.ram[SUPERFX])
            elapsed = tick
            if state == 0 and len(states) > 1 and tick > 20:
                break
        return {
            "states": states,
            "ticks": elapsed,
            "peak_y": peak_y / 256.0,
            "damage": 200 - hp_min,
            "power": power_min,
            "shots": shots,
            "superfx": superfx,
        }
    finally:
        core.close()


def main(core_path, rom):
    global CORE
    CORE = core_path

    weak_dp = run(DP, WEAK, 120)
    assert 66 in weak_dp["states"], f"DP weak missing: {weak_dp['states']}"
    assert 53 in weak_dp["states"], (
        f"DP weak did not land through 1402: {weak_dp['states']}")
    assert weak_dp["peak_y"] > 10, f"DP weak did not leave ground: {weak_dp}"
    assert weak_dp["ticks"] < 120, (
        f"DP weak recovery still slow: {weak_dp['ticks']} ticks")
    print(f"PASS Chin DP weak: lands in {weak_dp['ticks']} ticks, "
          f"peak {weak_dp['peak_y']:.0f}px, {weak_dp['damage']} HP")

    strong_dp = run(DP, STRONG, 120)
    assert 54 in strong_dp["states"], (
        f"DP strong (1400/54) missing: {strong_dp['states']}")
    assert 57 in strong_dp["states"] and 53 in strong_dp["states"], (
        f"DP strong chain incomplete: {strong_dp['states']}")
    assert strong_dp["ticks"] < 160, (
        f"DP strong recovery too long: {strong_dp['ticks']} ticks")
    assert strong_dp["damage"] >= weak_dp["damage"], (
        f"DP strong damage {strong_dp['damage']} < weak {weak_dp['damage']}")
    print(f"PASS Chin DP strong: states={strong_dp['states']}, "
          f"{strong_dp['damage']} HP, {strong_dp['ticks']} ticks")

    for tag, button, expected in (("weak", WEAK, 85), ("strong", STRONG, 86)):
        sup = run(QCF + QCF, button, 190)
        assert expected in sup["states"], (
            f"Chin super {tag} did not reach {expected}: {sup['states']}")
        assert sup["power"] <= 2000, (
            f"Chin super {tag} did not spend 1000 power: {sup['power']}")
        assert sup["shots"] >= 1, f"Chin super {tag} spawned no shot"
        assert sup["superfx"] > 0, f"Chin super {tag} had no super flash"
        assert sup["damage"] >= 40, (
            f"Chin super {tag} only did {sup['damage']} HP; the multi-hit "
            f"sequence is incomplete")
        print(f"PASS Chin super {tag}: states={sup['states']}, "
              f"{sup['damage']} HP, {sup['shots']} shot(s)")

    cd = run((), {STRONG, 8}, 120)       # X+A = mugen y+b
    assert 67 in cd["states"], f"CD blowback missing: {cd['states']}"
    assert cd["power"] == 3000, (
        f"CD blowback spent power like a super: {cd['power']}")
    assert cd["superfx"] == 0, (
        f"CD blowback darkened the screen (superfx={cd['superfx']})")
    assert cd["damage"] > 0, "CD blowback did no damage"
    print(f"PASS Chin CD blowback: {cd['damage']} HP, power {cd['power']}, "
          f"no super flash")

    print("PASS Chin fixes")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
