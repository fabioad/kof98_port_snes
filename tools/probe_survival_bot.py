#!/usr/bin/env python3
"""Diagnostic: one survivor fight, log positions/states every 30 frames."""
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
c.ram[0x107A] = 0; c.ram[0xF070] = 4; tap(c, 3)
for _ in range(4000):
    if c.ram[GS] == 5: break
    c.step()
c.ram[0x10EB] = 1
c.ram[0x1085] = 0; c.ram[0x108E] = 1; c.ram[0x108F] = 1
c.ram[0x1090] = 0; c.ram[0x1091] = 1
for _ in range(8000):
    if c.ram[GS] == 1: break
    c.step()

ATK = (0, 1, 9, 8)
ai = 0
for t in range(3000):
    gs = c.ram[GS]
    if gs != 1:
        print(t, "GS", gs, "wins", c.ram[0x1080], c.ram[0x1081],
              "roundwin", c.ram[0x1083]); break
    px, ex = c.word(0x4000) >> 8, c.word(0x4040) >> 8
    st1, st2 = c.ram[0x4008], c.ram[0x4048]
    hp1, hp2 = c.word(0x4010), c.word(0x4050)
    if t % 30 == 0:
        print(f"t={t:4} p1x={px:3} p2x={ex:3} d={abs(ex-px):3} "
              f"s1={st1:3} s2={st2:3} hp={hp1}/{hp2} "
              f"atk={c.word(0x4024)} hs2={c.ram[0x4068]}")
    pad = set()
    dist = abs(ex - px)
    if st1 == 0:
        if dist > 42: pad = {7 if ex > px else 6}
        else:
            pad = {ATK[ai % 4]}; ai += 1
    c.buttons[0] = pad
    c.step()
c.close()
