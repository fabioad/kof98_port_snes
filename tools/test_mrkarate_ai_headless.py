#!/usr/bin/env python3
"""Mr. Karate's CPU personality is always level 9 and counter-heavy.

The secret boss must keep his own AiTab (id 53) instead of falling back to
Kyo's table, advertise the top HUD level and answer a committed attack with
his own offense much more often than a normal opponent.

Run after a PVSnesLib build:

    python3 tools/test_mrkarate_ai_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from capture_pair_headless import wait, tap              # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
GS, SEL1, SEL2 = 0x1020, 0x1085, 0x1086
LOCK1, LOCK2, CPU1, CPU2 = 0x108E, 0x108F, 0x1090, 0x1091
AI_LEVEL, AI_FLAGS = 0x10EB, 0x1105
AI_DBG_THREAT, AI_DBG_COUNTER = 0x4678, 0x4687
HUDMAP = 0x4700
MK, KYO = 53, 0
WEAK_PUNCH = 1


def enter_boss_fight(core):
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    core.ram[0xF070] = 1                    # SINGLE VS
    core.step(4)
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 5, "select")
    core.ram[SEL1] = KYO
    core.ram[SEL2] = MK
    core.ram[LOCK1] = core.ram[LOCK2] = 1
    core.ram[CPU1] = 0                      # human P1 keeps the boss
    core.ram[CPU2] = 1
    core.ram[AI_LEVEL] = 1                  # prove the boss overrides it
    core.step()
    wait(core, lambda: core.ram[GS] == 1, "fight", 6000)
    core.step(120)


def main():
    core = Core(CORE, ROM)
    try:
        enter_boss_fight(core)
        assert core.ram[SEL2] == MK, f"Mr. Karate not loaded: {core.ram[SEL2]}"
        assert core.ram[AI_FLAGS] & 0x10, (
            f"Mr. Karate used another AiTab (flags={core.ram[AI_FLAGS]:#x})")
        digit = core.ram[HUDMAP + (27 * 32 + 18) * 2]
        assert digit == 8 + 27, f"HUD level digit {digit}, want LEVEL 8"

        for i in range(2400):
            if i % 30 == 0:
                core.put(0x4000, 110 << 8)
                core.put(0x4040, 140 << 8)
                core.buttons[0] = {WEAK_PUNCH}
                core.step(3)
                core.buttons[0] = set()
            core.step()
            if i % 120 == 0:                # keep the bout alive and stocked
                core.put(0x4010, 200)
                core.put(0x4050, 200)
                core.put(0x4030, 3000)
                core.put(0x4070, 3000)

        threat = core.ram[AI_DBG_THREAT]
        counter = core.ram[AI_DBG_COUNTER]
        assert threat > 0, "Mr. Karate never reacted to the attack"
        assert counter > 0, "Mr. Karate never counter-attacked"
        print(f"PASS Mr. Karate CPU: own table, HUD LEVEL 8, "
              f"{counter}/{threat} threat reads countered")
    finally:
        core.close()


if __name__ == "__main__":
    main()
