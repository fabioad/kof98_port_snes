#!/usr/bin/env python3
"""Generic air throw: strong punch/kick while airborne, weak stays air normal.

The FUSION air throw used the weak buttons (SNES B/Y).  It now follows the
ground throw convention: SNES A/X (strong) near an airborne opponent deals
30 damage and slams it down; weak B/Y still runs the normal air attack.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_X, F_Y, F_VX, F_VY = 0, 2, 4, 6
F_STATE, F_HP, F_INVUL = 8, 16, 62
S_JUMP, S_DOWN, S_AIRTHROW = 4, 10, 44
STRONG = {"X": 9, "A": 8}                 # libretro X/A = mugen y/b
WEAK = {"Y": 1, "B": 0}                   # libretro Y/B = mugen x/a


def trial(button, victim_air=True, char="mai"):
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, char, "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(FP1 + F_X, 100 << 8)
        core.put(FP2 + F_X, 115 << 8)
        core.put(FP1 + F_Y, 30 << 8)
        core.put(FP1 + F_VX, 0)
        core.put(FP1 + F_VY, 0)
        core.put(FP2 + F_Y, (30 if victim_air else 0) << 8)
        core.put(FP1 + F_HP, 200)
        core.put(FP2 + F_HP, 200)
        core.ram[FP1 + F_STATE] = S_JUMP
        core.ram[FP2 + F_STATE] = S_JUMP if victim_air else 0
        core.ram[FP1 + F_INVUL] = 0
        core.ram[FP2 + F_INVUL] = 0
        core.step(1)
        core.buttons[0] = {button}
        core.step(3)
        core.buttons[0] = set()
        airthrow = False
        for _ in range(24):
            core.step()
            airthrow |= core.ram[FP1 + F_STATE] == S_AIRTHROW
        return core.word(FP2 + F_HP), core.ram[FP2 + F_STATE], airthrow
    finally:
        core.close()


def main():
    for name, button in STRONG.items():
        hp, state, airthrow = trial(button)
        assert hp == 170, f"strong {name}: victim HP {hp}"
        assert state == S_DOWN, f"strong {name}: victim state {state}"
        assert airthrow, f"strong {name}: attacker never entered S_AIRTHROW"
        print(f"PASS air throw strong {name}: -30 HP, knockdown")
    for name, button in WEAK.items():
        hp, _state, airthrow = trial(button)
        assert not airthrow, f"weak {name}: weak button triggered the throw"
        assert hp != 170, f"weak {name}: weak button used the throw damage"
        print(f"PASS weak {name}: normal air attack, no air throw")
    hp, state, airthrow = trial(STRONG["X"], victim_air=False)
    assert not airthrow and hp != 170, (
        f"strong vs grounded: airthrow={airthrow} hp={hp} state={state}")
    print("PASS strong vs grounded: normal air attack, no air throw")


if __name__ == "__main__":
    main()
