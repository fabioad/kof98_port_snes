#!/usr/bin/env python3
"""Roster-14 verification: Benimaru (ROM) vs Mature (MSU) fight + no-MSU
select blocking.  Run twice: once with kof98-snes.msu present, once with it
renamed away (--nomsu expected-deny check is automatic via msuok)."""
import sys, time
sys.path.insert(0, ".")
from test_fight_remote import RetroArch, wait_for, read_fight

def to_select(ra):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        gs = ra.read_ram(0x1020, 1)[0]         # ENGINE gamestate
        if gs == 6:
            break
        ra.button(0, "START", True); time.sleep(0.2)
        ra.button(0, "START", False); time.sleep(0.5)
    else:
        raise AssertionError("mode menu never reached")
    for _ in range(4):
        if ra.read_ram(0xF070, 1)[0] == 1:
            break
        ra.button(0, "DOWN", True); time.sleep(0.2)
        ra.button(0, "DOWN", False); time.sleep(0.3)
    return  # caller writes sel before entering select

def enter_select(ra):
    ra.button(0, "START", True); time.sleep(0.2)
    ra.button(0, "START", False)
    wait_for(ra, lambda s: s["gamestate"] == 5, timeout=8)

def set_sel(ra, p1, p2):
    ra.command(f"WRITE_CORE_RAM 1085 {p1:02x}")
    ra.command(f"WRITE_CORE_RAM 1086 {p2:02x}")

def lock(ra, user, addr):
    for _ in range(8):
        ra.button(user, "A", True); time.sleep(0.3)
        ra.button(user, "A", False); time.sleep(0.25)
        if ra.read_ram(addr, 1)[0]:
            return True
    return False

def main():
    ra = RetroArch()
    try:
        if "--launch" in sys.argv:
            ra.launch("retroarch", "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
        ra.wait_ready()
        to_select(ra)
        msuok = ra.read_ram(0x107A, 1)[0]
        print("msuok:", msuok)
        # P2 = Mature (10, MSU); P1 = Benimaru (12, ROM chr).
        # sel must be written before entering the select screen: the
        # cursor cell derives from it at init.
        enter_select(ra)
        time.sleep(0.4)
        # cursors are WRAM cells; lock derives sel from the cell under it.
        # cells: 4=Benimaru 7=Mature 3=Kyo
        ra.command("WRITE_CORE_RAM F052 04")
        ra.command("WRITE_CORE_RAM F053 07")
        time.sleep(0.3)
        # P2 lock attempt on Mature: without MSU it must be denied
        locked2 = lock(ra, 1, 0x108F)
        print("p2 lock (mature):", locked2)
        if msuok == 0:
            assert not locked2, "Mature locked without MSU present"
            ra.command("WRITE_CORE_RAM F053 03")   # Kyo cell
            time.sleep(0.3)
            locked2 = lock(ra, 1, 0x108F)
            assert locked2, "Kyo lock failed without MSU"
            print("p2 lock (kyo, no msu): OK")
        else:
            assert locked2, "Mature lock failed with MSU present"
        locked1 = lock(ra, 0, 0x108E)
        assert locked1, "Benimaru lock failed"
        st = wait_for(ra, lambda s: s["gamestate"] == 1, timeout=15)
        time.sleep(2)
        s = ra.snapshot()
        c1 = ra.read_ram(0x1085, 1)[0]
        c2 = ra.read_ram(0x1086, 1)[0]
        print("fight: sel", c1, "vs", c2)
        oam = ra.read_ram(0x1800, 128)
        cells = sum(1 for i in range(0, 128, 4) if oam[i + 1] < 0xF0)
        print("oam cells onscreen-ish:", cells)
        assert c1 == 12, f"expected Benimaru(12), got {c1}"
        assert c2 == (0 if msuok == 0 else 10), f"expected Mature(10), got {c2}"
        print("PASS")
    finally:
        ra.close()

if __name__ == "__main__":
    sys.exit(main())
