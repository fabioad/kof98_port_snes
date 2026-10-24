#!/usr/bin/env python3
"""Reproduce the MSU=1 survivor freeze and dump engine state."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
GS = 0x1020

def tap(c, b):
    c.buttons[0] = {b}; c.step(4); c.buttons[0] = set(); c.step(8)

c = Core(CORE, ROOT / "kof98-snes.sfc")
for _ in range(80):
    if c.ram[GS] == 6: break
    tap(c, 3)
c.ram[0x107A] = 1; c.ram[0xF070] = 4; tap(c, 3)
for _ in range(4000):
    if c.ram[GS] == 5: break
    c.step()
print("msuok seen by game:", c.ram[0x107A])
c.ram[0x10EB] = 1
c.ram[0x1085] = 0; c.ram[0x108E] = 1; c.ram[0x108F] = 1
c.ram[0x1090] = 0; c.ram[0x1091] = 1
for _ in range(8000):
    if c.ram[GS] == 1: break
    c.step()

last = c.ram[0x1024]
frozen = 0
for t in range(3000):
    c.step()
    fc = c.ram[0x1024]
    if fc == last:
        frozen += 1
        if frozen == 60:
            print(f"FROZEN at t={t} fc={fc}")
            break
    else:
        frozen = 0
        last = fc
else:
    print("no freeze in 3000 frames"); c.close(); sys.exit()

def dump(label):
    r = c.ram
    print(f"--- {label} ---")
    print(f"gs={r[0x1020]} mark4614={r[0x4614]:02X} scr4615={r[0x4615]:02X} "
          f"rng={r[0x1079]:02X} msuok={r[0x107A]}")
    print(f"p1: x={c.word(0x4000)>>8} st={r[0x4008]} anim={c.word(0x400A)} "
          f"dmareq={r[0x4018]} tilepg={r[0x4026]}")
    print(f"p2: x={c.word(0x4040)>>8} st={r[0x4048]} anim={c.word(0x404A)} "
          f"dmareq={r[0x4058]} tilepg={r[0x4066]}")
    print(f"sel1={r[0x1085]} sel2={r[0x1086]} cidx={r[0x10C1]} "
          f"gmode={r[0x10C0]}")
    print(f"msu probe 0910={c.word(0x0910):04X} 0912={c.word(0x0912):04X}")
    print(f"sfx fifo 46F8={r[0x46F8]} sfxtoken={r[0x1053] if False else r[0x1053]}")
    print(f"pausecnt={r[0x1073]} hitstun1={r[0x4028]} hitstun2={r[0x4068]}")
    print(f"rsecs={r[0x1076]} rframe={r[0x1077]} kotimer={r[0x1028]}")
    print(f"nmiflag={r[0x1020-0x1000+0x20]} vbusy={r[0x1027]}")
dump("freeze state")
for i in range(20):
    c.step()
    print("fc now", c.ram[0x1024], "gs", c.ram[GS])
c.close()
