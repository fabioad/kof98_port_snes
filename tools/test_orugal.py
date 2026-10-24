#!/usr/bin/env python3
"""Omega Rugal selection: Rugal cell + L+R -> sel id 14 (ROM-resident).
With MSU: plain A picks rugal(3); L+R+A picks omega(14).
Without MSU: plain A denied; L+R+A still picks omega(14)."""
import sys, time
sys.path.insert(0, ".")
from test_fight_remote import RetroArch, wait_for
from test_roster14 import to_select, enter_select

SEL1, SEL2, LOCK1 = 0x1085, 0x1086, 0x108E
MSUOK = 0x107A
SCUR1, SCUR2 = 0xF052, 0xF053
RUGAL_CELL = 37


def try_lock(ra, user, cur, cell, sel, lock, hold_lr):
    """Cursor to `cell`, optionally hold L+R, press A, release."""
    ra.command(f"WRITE_CORE_RAM {cur:X} {cell:02x}")
    time.sleep(0.2)
    if hold_lr:
        ra.button(user, "L", True); ra.button(user, "R", True)
        time.sleep(0.2)
    for _ in range(8):
        ra.button(user, "A", True); time.sleep(0.3)
        ra.button(user, "A", False); time.sleep(0.25)
        if ra.read_ram(lock, 1)[0]:
            break
    if hold_lr:
        ra.button(user, "L", False); ra.button(user, "R", False)
        time.sleep(0.2)
    return ra.read_ram(sel, 1)[0], ra.read_ram(lock, 1)[0]


def unlock(ra, lock):
    ra.command(f"WRITE_CORE_RAM {lock:X} 00")
    time.sleep(0.2)


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

        # P1 tries rugal with plain A
        s, l = try_lock(ra, 0, SCUR1, RUGAL_CELL, SEL1, LOCK1, False)
        print("plain A on rugal: sel", s, "lock", l)
        if msuok:
            assert s == 3 and l, "expected rugal(3) locked"
            unlock(ra, LOCK1)
        else:
            assert not l or s == 14, "expected denial without MSU"
        unlock(ra, LOCK1)

        # P1 locks rugal with L+R held -> omega
        s, l = try_lock(ra, 0, SCUR1, RUGAL_CELL, SEL1, LOCK1, True)
        print("L+R+A on rugal: sel", s, "lock", l)
        assert s == 14 and l, "expected omega rugal(14)"

        # P2 locks kyo (cell 3) to start the fight
        s2, l2 = try_lock(ra, 1, SCUR2, 3, SEL2, 0x108F, False)
        print("p2 kyo:", s2, l2)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            gs = ra.read_ram(0x1020, 1)[0]
            if gs == 1:
                break
            time.sleep(0.4)
        s1, s2 = ra.read_ram(SEL1, 1)[0], ra.read_ram(SEL2, 1)[0]
        print("fight: sel", s1, "vs", s2, "gs", gs)
        assert gs == 1 and s1 == 14, "omega rugal fight failed"
        oam = ra.read_ram(0x0434, 128)
        cells = sum(1 for i in range(0, 128, 4) if oam and (oam[i] & 0xF0) != 0xF0)
        print("oam cells onscreen-ish:", cells)
        print("PASS")
        return 0
    finally:
        ra.close()


if __name__ == "__main__":
    sys.exit(main())
