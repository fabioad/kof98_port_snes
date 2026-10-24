#!/usr/bin/env python3
"""Freeze-state dump: lock kyo vs iori, wait for the stall, dump DP/WRAM."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import test_fight_remote as t
from runtime_abi import ABI
from test_roster import press, lock_side, to_select, W_SCUR1, W_SCUR2

DP = {"scr0": 0x1010, "scr1": 0x1012, "scr2": 0x1014, "scr3": 0x1016,
      "scr4": 0x1018, "scr5": 0x101A, "fofs": 0x101C, "framecnt": 0x1024,
      "huddirty": 0x1026, "kotimer": 0x1028, "tblbank": 0x102E,
      "scr6": 0x1034, "msuf": 0x103F, "lptr": 0x1040, "boxp": 0x1056,
      "cptr": 0x105A, "gs": 0x1020, "sel1": 0x1085, "sel2": 0x1086,
      "lock1": 0x108E, "lock2": 0x108F, "rng": 0x1088, "stageidx": 0x1087}
F = {"p1meta": 0x4000 + 22, "p1dmareq": 0x4000 + ABI['F_DMAREQ'],
     "p1dmapos": 0x4000 + ABI['F_DMAPOS'],
     "p1psprid": 0x4000 + ABI['F_PSPRID'], "p1tilepg": 0x4000 + 27, "p1st": 0x4000 + 8,
     "p1anim": 0x4000 + 18, "p1char": 0x4000 + 44, "p1tbank": 0x4000 + 46,
     "p2meta": 0x4040 + 22, "p2dmareq": 0x4040 + ABI['F_DMAREQ'],
     "p2dmapos": 0x4040 + ABI['F_DMAPOS'],
     "p2st": 0x4040 + 8, "p2anim": 0x4040 + 18, "p2char": 0x4040 + 44}


def u(ra, a, n=2):
    b = ra.read_ram(a, n)
    return int.from_bytes(b, "little")


ra = t.RetroArch()
ra.launch("retroarch", t.CORE)
try:
    ra.wait_ready()
    to_select(ra)
    if ra.read_ram(0x1091, 1)[0] != 0:
        press(ra, 1, "START", 0.2)
    ra.command(f"WRITE_CORE_RAM {W_SCUR2:X} 06")   # iori cell
    lock_side(ra, 1, 6, 0x108F)
    ra.command(f"WRITE_CORE_RAM {W_SCUR1:X} 03")   # kyo cell
    lock_side(ra, 0, 3, 0x108E)
    print("locked; polling for freeze...", flush=True)
    prev = None
    frozen = False
    for i in range(30):
        time.sleep(0.5)
        fc = u(ra, 0x1024, 1)
        gs = u(ra, 0x1020, 1)
        print(f"t{i}: gs={gs} fc={fc}", flush=True)
        if gs == 1:
            print("reached fight!")
            break
        if prev is not None and fc == prev:
            frozen = True
            break
        prev = fc
    if frozen:
        time.sleep(1)
        print("\n=== DP/WRAM at freeze ===")
        for k, a in DP.items():
            print(f"  {k:10s} ${a:04x} = {u(ra, a):04x}")
        for k, a in F.items():
            print(f"  {k:10s} ${a:04x} = {u(ra, a):04x}")
        print("\n=== markers $46E0-$46EE ===")
        mk = ra.read_ram(0x46E0, 24)
        names = {0xE0: "SF stage", 0xE2: "SM stage", 0xE4: "RFE idx",
                 0xE6: "SprDmaP", 0xE8: "bars/wins/camp", 0xEA: "wfv/fp",
                 0xEC: "NMI count", 0xEE: "TRAP($DE=hit)",
                 0xF0: "fr+1/+2", 0xF2: "fr+3/+4", 0xF4: "fr+5/+6",
                 0xF6: "trap SP"}
        for i in range(0, 24, 2):
            a = 0x46E0 + i
            v = mk[i] | mk[i + 1] << 8
            print(f"  ${a:04x} ({names.get(a, '?')}): {v:04x}")
        print("\n=== $7E0910-0940 (msu debug capture) ===")
        print(ra.read_ram(0x0910, 48).hex())
        print("\n=== stack $1D00-2000 scan for pushed frames ===")
        st = ra.read_ram(0x1D00, 0x300)
        run = []
        for i, b in enumerate(st):
            if b != 0x55:
                run.append((0x1D00 + i, b))
        if not run:
            print("  (all $55 - untouched)")
        else:
            lo = run[0][0] & ~0xF
            hi = (run[-1][0] | 0xF) + 1
            for a in range(lo, min(hi, 0x2000), 16):
                row = ra.read_ram(a, 16)
                hexs = ' '.join(f'{x:02x}' for x in row)
                marks = ''.join('>' if a + j in [r[0] for r in run] else ' '
                                for j in range(16))
                print(f"  ${a:04x}: {hexs}  {marks}")
            # any byte that could be a pushed PBR ($F2-ish) or PC near camp
            print("  candidates (byte==$F2 or $F0-F9):")
            for a, b in run:
                if 0xF0 <= b <= 0xF9:
                    print(f"    ${a:04x} = {b:02x}")
        print("\n=== $F000-F0FF menu blk ===")
        print(ra.read_ram(0xF000, 128).hex())
finally:
    ra.close()
