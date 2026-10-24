#!/usr/bin/env python3
"""Headless regression for the documented KOF input shortcuts.

Classic inputs must keep working; the shortcuts are additive:
  * DP  classic F,D,DF  / shortcut F,D,F
  * RDP classic B,D,DB  / shortcut B,D,B
  * HCBx2 classic       / shortcut F,D,B,F,D,B

The QCF/QCB two-input shortcut is intentionally NOT implemented: it is not
a documented KOF shortcut and would collide with crouching attacks.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_POWER = 0x4008, 0x4030
DOWN, RIGHT, LEFT = 5, 7, 6
# Physical pad -> MUGEN tokens: SNES Y = x (weak punch),
# SNES X = y (strong punch), SNES B = a (weak kick), SNES A = b (strong kick).
PUNCH_Y, PUNCH_X = 1, 9
KICK_W = 0


def motion(core, steps, buttons, hold=3):
    for step in steps:
        core.buttons[0] = set(step)
        core.step(hold)
    core.buttons[0] = set(buttons)
    core.step(hold)
    core.buttons[0] = set()
    core.step(6)


def fresh_fight(core, select, power, p1="kyo", p2="kyo"):
    enter_fight(core, select, p1, p2)
    core.put(0x4000, 80 << 8)
    core.put(0x4040, 200 << 8)
    core.put(0x4010, 200)
    core.put(0x4050, 200)
    core.put(F_POWER, power)
    core.step(10)


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)

        cases = [
            ("classic DP", [(RIGHT,), (DOWN,), (DOWN, RIGHT)],
             {PUNCH_Y}, 0, (50, 51)),
            ("shortcut DP", [(RIGHT,), (DOWN,), (RIGHT,)],
             {PUNCH_Y}, 0, (50, 51)),
            ("classic RDP", [(LEFT,), (DOWN,), (DOWN, LEFT)],
             {KICK_W}, 0, (58, 59)),
            ("shortcut RDP", [(LEFT,), (DOWN,), (LEFT,)],
             {KICK_W}, 0, (58, 59)),
        ]
        for label, steps, buttons, power, expected in cases:
            fresh_fight(core, select, power)
            motion(core, steps, buttons)
            st = core.ram[F_STATE]
            assert st in expected, (label, st)
            print(f"PASS {label}: state {st}")

        classic = [(RIGHT,), (RIGHT, DOWN), (DOWN,),
                   (DOWN, LEFT), (LEFT,),
                   (RIGHT,), (RIGHT, DOWN), (DOWN,),
                   (DOWN, LEFT), (LEFT,)]
        shortcut = [(RIGHT,), (DOWN,), (LEFT,),
                    (RIGHT,), (DOWN,), (LEFT,)]
        for label, steps in (("classic HCBx2", classic),
                             ("shortcut HCBx2", shortcut)):
            fresh_fight(core, select, 3000)
            motion(core, steps, {PUNCH_Y, PUNCH_X}, hold=2)
            st = core.ram[F_STATE]
            assert st == 87, (label, st)
            assert core.word(F_POWER) == 0, (label, core.word(F_POWER))
            print(f"PASS {label}: Kyo 87 Quick SDM")

        # Composed super: Iori's Ya Otome (QCBHCF+P).  The QCB portion
        # keeps its diagonal; only the HCF half loses the diagonals.
        qcbhcf_classic = [(DOWN,), (DOWN, LEFT), (LEFT,),
                          (DOWN, LEFT), (DOWN,), (DOWN, RIGHT), (RIGHT,)]
        qcbhcf_short = [(DOWN,), (DOWN, LEFT), (LEFT,),
                        (DOWN,), (RIGHT,)]
        qcbhcf_qcf = [(DOWN,), (DOWN, LEFT), (LEFT,),
                      (DOWN,), (DOWN, RIGHT), (RIGHT,)]
        qcbhcf_bdf = [(DOWN,), (DOWN, LEFT), (LEFT,),
                      (LEFT,), (DOWN,), (RIGHT,)]
        for label, steps in (("classic QCBHCF", qcbhcf_classic),
                             ("shortcut QCBHCF", qcbhcf_short),
                             ("qcb qcf QCBHCF", qcbhcf_qcf),
                             ("qcb b d f QCBHCF", qcbhcf_bdf)):
            fresh_fight(core, select, 1000, p1="iori")
            motion(core, steps, {PUNCH_Y})
            st = core.ram[F_STATE]
            assert st == 85, (label, st)
            assert core.word(F_POWER) == 0, (label, core.word(F_POWER))
            print(f"PASS {label}: Iori Ya Otome 85")

        print("PASS input shortcuts: classic and shortcut paths")
    finally:
        core.close()


if __name__ == "__main__":
    main()
