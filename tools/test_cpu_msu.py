#!/usr/bin/env python3
"""CPU must never lock an MSU char when the .msu file is missing.
Scenario: versus select, cpu2 parked on Mature's cell with the deadline
expired -> SelLockCpu should reroll to a legal cell and lock."""
import sys, time
sys.path.insert(0, ".")
from test_fight_remote import RetroArch
from test_roster14 import to_select, enter_select

SEL2, LOCK2, CPU2 = 0x1086, 0x108F, 0x1091
MSUOK = 0x107A
SCUR2 = 0xF053
SCPUT2 = 0xF059
MATURE_CELL = 7


def main():
    ra = RetroArch()
    try:
        if "--launch" in sys.argv:
            ra.launch("retroarch",
                      "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
        ra.wait_ready()
        to_select(ra)
        msuok = ra.read_ram(MSUOK, 1)[0]
        print("msuok:", msuok)
        enter_select(ra)
        time.sleep(0.4)
        # cpu2 owns P2, parked on Mature, deadline already passed
        ra.command(f"WRITE_CORE_RAM {CPU2:X} 01")
        ra.command(f"WRITE_CORE_RAM {SCUR2:X} {MATURE_CELL:02x}")
        ra.command(f"WRITE_CORE_RAM {SCPUT2:X} 00")
        locked = None
        for _ in range(60):
            time.sleep(0.2)
            if ra.read_ram(LOCK2, 1)[0]:
                locked = ra.read_ram(SEL2, 1)[0]
                break
        cur = ra.read_ram(SCUR2, 1)[0]
        dbg = ra.read_ram(0x1085, 16)
        print("cpu2 locked sel:", locked, "cursor now:", cur)
        print("gs", ra.read_ram(0x1020, 1)[0], "raw", dbg.hex())
        if msuok:
            assert locked is not None, "cpu never locked"
        else:
            assert locked is not None, "cpu never locked (softlock!)"
            assert locked != 10, "cpu locked Mature (MSU char) without MSU"
        print("PASS")
        return 0
    finally:
        ra.close()


if __name__ == "__main__":
    sys.exit(main())
