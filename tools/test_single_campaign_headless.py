#!/usr/bin/env python3
"""Exercise repeated Single Play winner banners through the real KO flow."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from capture_pair_headless import tap, wait
from test_roster import parse_tables

GS = 0x1020
FRAME = 0x1024
WINS1 = 0x1080
SEL2 = 0x1086
P2HP = 0x4050
C_IDX = 0x10C1

core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
            ROOT / "kof98-snes.sfc")
try:
    for _ in range(60):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    core.ram[0xF070] = 0                 # SINGLE PLAY
    for _ in range(30):
        tap(core, 3)                     # START confirms the mode
        for _ in range(20):
            if core.ram[GS] == 5:
                break
            core.step()
        if core.ram[GS] == 5:
            break
    wait(core, lambda: core.ram[GS] == 5, "single select")
    core.ram[0x1085] = 0
    core.ram[0x108E] = 1
    core.ram[0x108F] = 1
    core.step()
    wait(core, lambda: core.ram[GS] == 1, "battle 1", 3600)

    opponents = [core.ram[SEL2]]
    for battle in range(1, 5):
        core.ram[WINS1] = 1              # deciding round of this match
        core.put(P2HP, 0)
        wait(core, lambda: core.ram[GS] == 0, f"winner {battle}", 1200)
        wait(core, lambda: core.ram[C_IDX] == battle and
             core.ram[GS] in (1, 4), f"battle {battle + 1}", 2400)
        opponents.append(core.ram[SEL2])
        assert core.ram[SEL2] not in (3, 14), opponents
        wait(core, lambda: core.ram[GS] == 1,
             f"battle {battle + 1} ready", 2400)

    print("PASS repeated Single Play winners", opponents,
          "cidx", core.ram[C_IDX], "frame", core.ram[FRAME])
finally:
    core.close()
