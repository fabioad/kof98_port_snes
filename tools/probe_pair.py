#!/usr/bin/env python3
"""Bisect the MSU-char fight hang: try char pairs and see where gs stops."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import test_fight_remote as t
from test_roster import (parse_tables, press, lock_side, to_select,
                         W_GS, W_CPU2, W_SCUR1, W_SCUR2, GS_SELECT)

W = {"gs": 0x1020, "sel1": 0x1085, "sel2": 0x1086, "lock1": 0x108E,
     "lock2": 0x108F, "cpu1": 0x1090, "cpu2": 0x1091, "fc": 0x1024,
     "kotimer": 0x1028, "dmareq1": 0x4000 + 24, "dmareq2": 0x4040 + 24,
     "dmapos1": 0x4000 + 25, "dmapos2": 0x4040 + 25,
     "meta1": 0x4000 + 22, "meta2": 0x4040 + 22,
     "st1": 0x4000 + 8, "st2": 0x4040 + 8, "dbg": 0x4698}
WINS1, FP2HP = 0x1080, 0x4050


def dump(ra, tag=""):
    out = {}
    for k, a in W.items():
        try:
            v = ra.read_ram(a, 2 if k.startswith("meta") else 1)
            out[k] = v[0] | (v[1] << 8 if len(v) > 1 else 0)
        except Exception as e:
            out[k] = str(e)
    print(tag, " ".join(f"{k}={v:02x}" if isinstance(v, int) else f"{k}={v}"
                        for k, v in out.items()), flush=True)


def attempt(ra, roster, a, b):
    if ra.read_ram(W["cpu2"], 1)[0] != 0:
        press(ra, 1, "START", 0.2)
    ca, cb = roster[a]["cell"], roster[b]["cell"]
    ra.command(f"WRITE_CORE_RAM {W_SCUR2:X} {cb:02X}")
    lock_side(ra, 1, cb, 0x108F)
    ra.command(f"WRITE_CORE_RAM {W_SCUR1:X} {ca:02X}")
    lock_side(ra, 0, ca, 0x108E)
    print(f"locked {roster[a]['name']}({a}) vs {roster[b]['name']}({b})")
    prev = None
    for i in range(40):
        time.sleep(0.5)
        dump(ra, f"  t{i}:")
        gs = ra.read_ram(W["gs"], 1)[0]
        fc = ra.read_ram(W["fc"], 1)[0]
        if gs == 1:
            return True
        if prev is not None and fc == prev:
            print("  !! framecnt frozen")
            return False
        prev = fc
    return False


roster = parse_tables()
ra = t.RetroArch()
ra.launch("retroarch", t.CORE)
try:
    ra.wait_ready()
    to_select(ra)
    for pair in [(0, 1), (15, 0), (0, 18), (15, 18)]:
        ok = attempt(ra, roster, *pair)
        print(f"pair {pair}: {'FIGHT' if ok else 'HANG'}", flush=True)
        if not ok:
            break
        ra.command(f"WRITE_CORE_RAM {WINS1:X} 01")
        ra.command(f"WRITE_CORE_RAM {FP2HP:X} 00 00")
        t.wait_for(ra, lambda s: s["gamestate"] == GS_SELECT,
                   timeout=45, interval=0.15)
        time.sleep(0.5)
finally:
    ra.close()
