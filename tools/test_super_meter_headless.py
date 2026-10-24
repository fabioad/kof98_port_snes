#!/usr/bin/env python3
"""Headless regression for super costs, MAX activation and long motions.

Checks:
  * a super does not fire with 0 meter;
  * a normal QCFx2 super spends exactly one stock;
  * Kyo's 88 is a normal 1-stock super, not a MAX slot;
  * the 30-frame motion buffer lets QCFx2 complete (the old 18-frame cap
    rejected the first half and let a DP special eat the input);
  * activating MAX spends one stock and arms the timer.

The per-character MAX mask itself is covered by
``tools/tests/test_command_list.py`` and the generated
``build/gen_fight/max_masks.inc``; this script exercises the human input
path, which needs a real emulator.

Run after a PVSnesLib build:

    python3 tools/test_super_meter_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402
from capture_pair_headless import wait                   # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_POWER, F_MAX = 0x4008, 0x4030, 0x403B
DOWN, RIGHT, LEFT = 5, 7, 6
# Physical pad -> MUGEN tokens: SNES Y = x (weak punch),
# SNES X = y (strong punch), SNES B = a (weak kick), SNES A = b (strong kick).
PUNCH_Y, PUNCH_X = 1, 9
BUTTON_B = 0


def motion(core, steps, buttons, hold=3):
    """Hold each direction `hold` ticks, then press the finish buttons."""
    for step in steps:
        core.buttons[0] = set(step)
        core.step(hold)
    core.buttons[0] = set(buttons)
    core.step(hold)
    core.buttons[0] = set()
    core.step(4)


def qcfx2(core, buttons):
    motion(core, [(DOWN,), (DOWN, RIGHT), (RIGHT,),
                  (DOWN,), (DOWN, RIGHT), (RIGHT,)], buttons)


def hcbx2(core, buttons):
    # HCB = F, DF, D, DB, B (the engine's motion table ends on back).
    motion(core, [(RIGHT,), (RIGHT, DOWN), (DOWN,),
                  (DOWN, LEFT), (LEFT,),
                  (RIGHT,), (RIGHT, DOWN), (DOWN,),
                  (DOWN, LEFT), (LEFT,)], buttons, hold=2)


def reset_positions(core, power):
    core.put(0x4000, 80 << 8)
    core.put(0x4040, 200 << 8)
    core.put(0x4010, 200)
    core.put(0x4050, 200)
    core.put(F_POWER, power)
    core.step(4)


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "kyo", "kyo")

        # 0 meter: the QCFx2 command must not enter a super.
        reset_positions(core, 0)
        qcfx2(core, {PUNCH_Y})
        assert core.ram[F_STATE] not in (85, 86), core.ram[F_STATE]
        wait(core, lambda: core.ram[F_STATE] == 0, "kyo no-meter recovery")

        # 1000 meter: the strong Saishuu Kessen Ougi spends one stock.
        reset_positions(core, 1000)
        qcfx2(core, {PUNCH_X})
        assert core.ram[F_STATE] == 86, core.ram[F_STATE]
        assert core.word(F_POWER) == 0, core.word(F_POWER)
        wait(core, lambda: core.ram[F_STATE] == 0, "kyo super recovery")

        # Kyo 88 is the second normal super (QCFx2 + both punches).
        reset_positions(core, 3000)
        qcfx2(core, {PUNCH_Y, PUNCH_X})
        assert core.ram[F_STATE] == 88, core.ram[F_STATE]
        assert core.word(F_POWER) == 2000, core.word(F_POWER)
        wait(core, lambda: core.ram[F_STATE] == 0, "kyo 88 recovery")

        # Kyo 87 is a MAX slot: with 1000 meter and no MAX it must be
        # rejected (89, the normal HCBx2 super, may fire instead).
        reset_positions(core, 1000)
        hcbx2(core, {PUNCH_Y, PUNCH_X})
        assert core.ram[F_STATE] != 87, core.ram[F_STATE]
        wait(core, lambda: core.ram[F_STATE] == 0, "kyo 87 outside MAX")

        # Fresh fight so the previous super/ring cannot affect the MAX test.
        enter_fight(core, select, "kyo", "kyo")

        # MAX activation spends one stock and arms the 240-tick timer.
        reset_positions(core, 2000)
        core.buttons[0] = {PUNCH_Y, BUTTON_B, PUNCH_X}
        core.step(2)
        core.buttons[0] = set()
        wait(core, lambda: core.ram[F_STATE] == 96, "kyo MAX", 40)
        assert core.word(F_POWER) == 1000, core.word(F_POWER)
        assert core.ram[F_MAX] >= 230, core.ram[F_MAX]
        wait(core, lambda: core.ram[F_STATE] == 0, "kyo MAX recovery")
        # The MAX input must survive CmdTry's F_HOT tick.  The old 16-bit
        # store wrote the high byte over F_MAX (offset 59), zeroing the
        # window on the first direction/button press.
        max_before = core.ram[F_MAX]
        assert max_before > 180, max_before
        hcbx2(core, {PUNCH_Y, PUNCH_X})
        assert core.ram[F_STATE] == 87, core.ram[F_STATE]
        assert core.word(F_POWER) == 0, core.word(F_POWER)
        assert core.ram[F_MAX] > 150, core.ram[F_MAX]
        print("PASS Kyo: 0-meter reject, super 1000, 88 normal, "
              "MAX 87 with timer preserved")
    finally:
        core.close()


if __name__ == "__main__":
    main()
