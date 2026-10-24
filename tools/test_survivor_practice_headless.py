#!/usr/bin/env python3
"""Exercise SURVIVOR and PRACTICE through the real menu and fight flow.

Checks:
  * menu items 4/5 map to G_MODE 4/5 (and the no-MSU cursor skips team rows);
  * SURVIVOR builds a no-repeat roster (7 ROM chars without MSU, 48 with);
  * carried HP survives a round; a special/super finish adds 50% of the
    remaining HP, and fills the bar when the human was above 50% at the blow;
  * a lost SURVIVOR round ends the run instead of restarting at 0 HP;
  * PRACTICE keeps both sides' HP untouched, holds the CPU idle, keeps both
    super meters full, and freezes the round clock.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
GS = 0x1020
FRAME = 0x1024
M_ITEM = 0xF070
MSUOK = 0x107A
G_MODE = 0x10C0
C_IDX = 0x10C1
SEL1 = 0x1085
SEL2 = 0x1086
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
HP1 = 0x4010
HP2 = 0x4050
POW1 = 0x4030
POW2 = 0x4070
RSECS = 0x1076
RFRAME = 0x1077
WINS1 = 0x1080
WINS2 = 0x1081
SURV_LIST = 0x4F00
SURV_COUNT = 0x4F30
SURV_KOSP = 0x4F32
SV_ESCR = 0xF078
SV_ETICK = 0xF079
SV_FIN = 0x4F33
C_STAGE = 0x10C4


def expected_rom_ids():
    """Read the generated RomFlags table so the test follows asset changes."""
    path = ROOT / "build/gen_fight/newchars_tabs.inc"
    if path.exists():
        match = re.search(r"RomFlags:\s*\.db\s+([0-9,\s]+)", path.read_text())
        if match:
            flags = [int(v) for v in match.group(1).split(",")]
            return {i for i, flag in enumerate(flags) if flag}
    return {0, 1, 2, 12, 13, 15}


ROM_IDS = expected_rom_ids()
PRACTICE_POOL = ROM_IDS - {3, 14}          # CpuPool excludes both bosses


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def press(core, button, port=0):
    core.buttons[port] = {button}
    core.step(10)
    core.buttons[port] = set()
    core.step(20)


def wait(core, predicate, label, limit=6000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.ram[GS]} frame={core.ram[FRAME]}")


def boot():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    return core


def open_select(core, item, msu):
    core.ram[MSUOK] = msu
    core.ram[M_ITEM] = item
    for _ in range(30):
        tap(core, 3)
        for _ in range(20):
            if core.ram[GS] == 5:
                break
            core.step()
        if core.ram[GS] == 5:
            break
    wait(core, lambda: core.ram[GS] == 5, f"select item {item}")
    return core.ram[G_MODE]


def lock_sides(core, cpu2):
    core.ram[SEL1] = 0
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.ram[CPU1] = 0
    core.ram[CPU2] = cpu2


def test_menu_navigation():
    core = boot()
    try:
        core.ram[MSUOK] = 0
        core.step(2)
        assert core.ram[M_ITEM] == 0
        press(core, 5)                    # DOWN
        assert core.ram[M_ITEM] == 1
        press(core, 5)                    # team rows skipped -> SURVIVOR
        assert core.ram[M_ITEM] == 4, core.ram[M_ITEM]
        press(core, 5)
        assert core.ram[M_ITEM] == 5, core.ram[M_ITEM]
        print("PASS menu SURVIVOR/PRACTICE rows")
    finally:
        core.close()


def test_survivor_rom_route():
    core = boot()
    try:
        assert open_select(core, 4, 0) == 4
        lock_sides(core, cpu2=1)
        wait(core, lambda: core.ram[GS] in (1, 4), "survivor fight 1")
        count = core.ram[SURV_COUNT]
        ids = [core.ram[SURV_LIST + i] for i in range(count)]
        assert count == len(ROM_IDS) and set(ids) == ROM_IDS, (count, ids)
        assert core.ram[SEL2] == ids[0]

        core.put(HP1, 30)
        core.ram[SURV_KOSP] = 1           # special finish, human <=50%
        core.ram[WINS1] = 1
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 0, "survivor banner")
        wait(core, lambda: core.ram[C_IDX] == 1 and core.ram[GS] in (1, 4),
             "survivor fight 2")
        assert core.word(HP1) == 45, hex(core.word(HP1))   # 30 + 50%
        assert core.ram[SEL2] == ids[1] and ids[1] not in ids[:1]

        wait(core, lambda: core.ram[GS] == 1, "survivor fight 2 ready")
        core.put(HP1, 30)
        core.ram[SURV_KOSP] = 0           # normal finish: no bonus
        core.ram[WINS1] = 1
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 0, "survivor banner 2")
        wait(core, lambda: core.ram[C_IDX] == 2 and core.ram[GS] in (1, 4),
             "survivor fight 3")
        assert core.word(HP1) == 30, hex(core.word(HP1))
        assert core.ram[SEL2] == ids[2] and ids[2] not in ids[:2]

        wait(core, lambda: core.ram[GS] == 1, "survivor fight 3 ready")
        core.put(HP1, 130)
        core.ram[SURV_KOSP] = 2           # special finish, human >50%
        core.ram[WINS1] = 1
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 0, "survivor banner 3")
        wait(core, lambda: core.ram[C_IDX] == 3 and core.ram[GS] in (1, 4),
             "survivor fight 4")
        assert core.word(HP1) == 200, hex(core.word(HP1))
        assert core.ram[SEL2] == ids[3] and ids[3] not in ids[:3]
        print("PASS survivor ROM route", ids)
    finally:
        core.close()


def test_survivor_full_roster():
    core = boot()
    try:
        assert open_select(core, 4, 1) == 4
        # cpu2=0 keeps this a P1-vs-P2 bout, so the list can be checked
        # without loading streamed opponents from the MSU file.
        core.ram[SEL2] = 0
        lock_sides(core, cpu2=0)
        wait(core, lambda: core.ram[GS] in (1, 4), "survivor list build")
        count = core.ram[SURV_COUNT]
        ids = [core.ram[SURV_LIST + i] for i in range(count)]
        assert count == 48 and len(set(ids)) == 48, (count, ids)
        assert min(ids) == 0 and max(ids) == 47, ids
        print("PASS survivor full roster", count)
    finally:
        core.close()


def test_survivor_loss_ends_run():
    core = boot()
    try:
        assert open_select(core, 4, 0) == 4
        lock_sides(core, cpu2=1)
        wait(core, lambda: core.ram[GS] == 1, "survivor loss fight")
        core.put(HP1, 0)
        core.put(HP2, 200)
        wait(core, lambda: core.ram[GS] == 0, "survivor loss banner")
        # A SURVIVOR defeat ends the run outright: no YOU LOSE menu, no
        # character select -- CampResolve resets and returns to PRESS START.
        wait(core, lambda: core.ram[G_MODE] == 0 and core.ram[GS] == 0,
             "survivor loss -> title")
        core.step(30)
        assert core.ram[GS] == 0, f"survivor loss gs={core.ram[GS]}"
        print("PASS survivor loss returns to title")
    finally:
        core.close()


def test_survivor_finish_tracking():
    core = boot()
    try:
        assert open_select(core, 4, 0) == 4
        lock_sides(core, cpu2=1)
        wait(core, lambda: core.ram[GS] == 1, "survivor tracking fight")
        core.ram[CPU2] = 0

        def qcf_x():
            core.put(0x4000, 100 << 8)
            core.put(0x4040, 116 << 8)
            core.buttons[0] = {5}
            core.step(3)
            core.buttons[0] = {5, 7}
            core.step(3)
            core.buttons[0] = {7}
            core.step(3)
            core.buttons[0] = {7, 9}
            core.step(4)
            core.buttons[0] = set()

        core.put(HP2, 160)
        qcf_x()
        wait(core, lambda: core.ram[SURV_KOSP] != 0, "special above 50%")
        assert core.ram[SURV_KOSP] == 2, core.ram[SURV_KOSP]

        wait(core, lambda: core.ram[0x4008] == 0 and core.ram[0x4048] == 0,
             "recover after first special")
        core.put(HP1, 60)                 # human now <=50%
        core.put(HP2, 80)
        core.ram[SURV_KOSP] = 0
        qcf_x()
        wait(core, lambda: core.ram[SURV_KOSP] != 0, "special below 50%")
        assert core.ram[SURV_KOSP] == 1, core.ram[SURV_KOSP]
        print("PASS survivor finish tracking (>50% and <=50%)")
    finally:
        core.close()


def test_survivor_ending():
    core = boot()
    try:
        assert open_select(core, 4, 1) == 4
        lock_sides(core, cpu2=1)
        wait(core, lambda: core.ram[GS] == 1, "survivor ending fight")
        count = core.ram[SURV_COUNT]
        ids = [core.ram[SURV_LIST + i] for i in range(count)]
        assert count == 48 and ids[-1] == 14, ids[-4:]

        core.ram[C_IDX] = count - 1
        core.ram[WINS1] = 1
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 10, "survivor ending gs10",
             limit=8000)
        assert core.ram[SV_ESCR] == 0
        assert core.word(SV_ETICK) == 600, core.word(SV_ETICK)

        core.capture_video = True
        core.step(60)
        frame = core.last_frame
        assert frame is not None
        raw = frame[3]
        assert sum(1 for b in raw[::101] if b) > 50, "ending screen is black"

        core.ram[SV_ETICK] = 1
        core.ram[SV_ETICK + 1] = 0
        wait(core, lambda: (core.ram[SV_ESCR] == 1 and core.ram[GS] == 10
                            and core.word(SV_ETICK) > 0),
             "survivor ending screen 1", 4000)

        for n in range(2, 13):
            core.ram[SV_ETICK] = 1
            core.ram[SV_ETICK + 1] = 0
            wait(core, lambda n=n: (core.ram[SV_ESCR] == n
                                    and core.ram[GS] == 10
                                    and core.word(SV_ETICK) > 0),
                 f"survivor ending screen {n}", 4000)
        core.step(2)
        assert core.ram[SV_ESCR] == 12
        assert core.word(SV_ETICK) >= 895, core.word(SV_ETICK)
        assert core.ram[SV_FIN] >= 29, core.ram[SV_FIN]

        core.ram[SV_ETICK] = 1
        core.ram[SV_ETICK + 1] = 0
        wait(core, lambda: core.ram[GS] == 0, "survivor ending -> title",
             6000)
        print("PASS survivor ending: 13 stills, last hold 15 s, title")
    finally:
        core.close()


def test_survivor_boss_stage():
    core = boot()
    try:
        assert open_select(core, 4, 1) == 4
        lock_sides(core, cpu2=1)
        wait(core, lambda: core.ram[GS] == 1, "survivor boss stage fight")
        count = core.ram[SURV_COUNT]
        ids = [core.ram[SURV_LIST + i] for i in range(count)]
        assert ids[-1] == 14, ids[-4:]
        assert core.ram[C_STAGE] != 5, core.ram[C_STAGE]

        # Jump to the last regular opponent, then win: the next fight is the
        # Omega Rugal boss and must use Rugal's exclusive stage.
        core.ram[C_IDX] = count - 2
        core.ram[WINS1] = 1
        core.put(HP2, 0)
        wait(core, lambda: core.ram[GS] == 0, "survivor boss stage banner")
        wait(core, lambda: core.ram[C_IDX] == count - 1
             and core.ram[GS] in (1, 4), "survivor boss stage start", 3000)
        wait(core, lambda: core.ram[GS] == 1, "survivor boss stage ready")
        assert core.ram[SEL2] == 14, core.ram[SEL2]
        assert core.ram[C_STAGE] == 5, core.ram[C_STAGE]
        print("PASS survivor boss uses stage 5")
    finally:
        core.close()


def test_practice():
    core = boot()
    try:
        assert open_select(core, 5, 0) == 5
        lock_sides(core, cpu2=1)
        wait(core, lambda: core.ram[GS] == 1, "practice fight")
        core.step(30)
        assert core.word(POW1) == 3000, hex(core.word(POW1))
        assert core.word(POW2) == 3000, hex(core.word(POW2))
        first = core.ram[SEL2]
        assert first in PRACTICE_POOL, first

        # spend both meters: both must be full again next frame
        core.put(POW1, 0)
        core.put(POW2, 0)
        core.step(2)
        assert core.word(POW1) == 3000, hex(core.word(POW1))
        assert core.word(POW2) == 3000, hex(core.word(POW2))

        # the round clock must never expire
        core.ram[RSECS] = 1
        core.ram[RFRAME] = 59
        core.step(180)
        assert core.ram[GS] == 1, core.ram[GS]
        assert core.ram[RSECS] == 1, core.ram[RSECS]

        # CPU side must remain completely idle
        core.put(0x4000, 60 << 8)
        core.put(0x4040, 180 << 8)
        cpu_x = core.word(0x4040)
        core.step(120)
        assert core.word(0x4040) == cpu_x, (hex(core.word(0x4040)),
                                            hex(cpu_x))
        assert core.ram[0x4048] == 0, core.ram[0x4048]

        # both sides are invulnerable: P1 hits the idle CPU too
        core.put(0x4000, 100 << 8)
        core.put(0x4040, 116 << 8)
        core.put(HP2, 100)
        tap(core, 9, 0)
        core.step(60)
        assert core.word(HP2) == 100, core.word(HP2)

        # drive pad 2 into P1 and confirm the human HP never drops
        core.ram[CPU2] = 0
        core.put(0x4000, 100 << 8)
        core.put(0x4040, 120 << 8)
        core.put(HP1, 100)
        for _ in range(90):
            core.ram[HP1] = 100
            core.ram[HP1 + 1] = 0
            tap(core, 1, 1)
            if core.word(HP1) != 100:
                break
        assert core.word(HP1) == 100, core.word(HP1)
        print("PASS practice: no HP loss, CPU idle, both meters full, clock frozen")
    finally:
        core.close()


if __name__ == "__main__":
    test_menu_navigation()
    test_survivor_rom_route()
    test_survivor_full_roster()
    test_survivor_loss_ends_run()
    test_survivor_finish_tracking()
    test_survivor_ending()
    test_survivor_boss_stage()
    test_practice()
