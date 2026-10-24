#!/usr/bin/env python3
"""Step-by-step probe of the versus select screen."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import test_fight_remote as t

W = {"gs": 0x1020, "msuok": 0x107A, "wins1": 0x1080, "sel1": 0x1085,
     "sel2": 0x1086, "lock1": 0x108E, "lock2": 0x108F, "cpu1": 0x1090,
     "cpu2": 0x1091, "mitem": 0xF070, "scur1": 0xF052, "scur2": 0xF053,
     "scput1": 0xF058, "scput2": 0xF059, "framecnt": 0x1024,
     "sfxseq": 0x1030, "sfxlast": 0x1031, "audiordy": 0x1032,
     "muson": 0xF07C, "efpending": 0x46F8,
     "spcv": 0x003C, "spcread": 0x0044, "spcwrite": 0x0045,
     "spccmd": 0x0046, "spcarg": 0x0047,
     "gmode": 0xF040, "sface1": 0xF054, "sface2": 0xF055}


def dump(ra, tag=""):
    vals = {}
    for k, a in W.items():
        try:
            vals[k] = ra.read_ram(a, 1)[0]
        except Exception as e:
            vals[k] = f"?{e}"
    print(tag, " ".join(f"{k}={v:02x}" if isinstance(v, int) else f"{k}={v}"
                        for k, v in vals.items()))


def press(ra, user, btn, settle=0.15):
    ra.button(user, btn, True); time.sleep(settle)
    ra.button(user, btn, False); time.sleep(settle)


ra = t.RetroArch()
ra.launch("retroarch", t.CORE)
try:
    ra.wait_ready()
    # to mode menu
    for _ in range(40):
        if ra.read_ram(W["gs"], 1)[0] == 6:
            break
        press(ra, 0, "START", 0.2); time.sleep(0.3)
    print("== mode menu =="); dump(ra)
    for _ in range(5):
        if ra.read_ram(W["mitem"], 1)[0] == 1:
            break
        press(ra, 0, "DOWN", 0.2)
    press(ra, 0, "START", 0.2)
    for _ in range(60):
        if ra.read_ram(W["gs"], 1)[0] == 5:
            break
        time.sleep(0.2)
    print("== select =="); dump(ra)
    time.sleep(1.0); dump(ra, "after 1s:")
    time.sleep(1.0); dump(ra, "after 2s:")

    # P1 join (cpu1 may start 1)
    print("-- p1 START --"); press(ra, 0, "START"); dump(ra)
    # P2 join
    print("-- p2 START --"); press(ra, 1, "START"); dump(ra)

    # P2 cursor -> cell 9 (ryo), lock A
    ra.command("WRITE_CORE_RAM F052 00")   # scur1 = terry cell 0
    ra.command("WRITE_CORE_RAM F053 09")   # scur2 = ryo cell 9
    time.sleep(0.3); dump(ra, "scur written:")
    print("-- p2 A --"); press(ra, 1, "A"); dump(ra)
    print("-- p1 A --"); press(ra, 0, "A"); dump(ra)
    for i in range(15):
        time.sleep(0.7); dump(ra, f"t+{i}:")
        if ra.read_ram(W["gs"], 1)[0] != 5:
            break
    print("gs now", hex(ra.read_ram(W["gs"], 1)[0]))
    for i in range(10):
        time.sleep(1.0); dump(ra, f"post{i}:")
finally:
    ra.close()
