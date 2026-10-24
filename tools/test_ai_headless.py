#!/usr/bin/env python3
"""Headless smoke test for the per-character CPU personality.

Boots a single VS bout, forces CPU difficulty 9 on both sides and lets the
fighters play.  The engine's AI counters (DBGREG+120..132) must show that
the personality engaged: specials/supers, threat reads, throws, a MAX
burst, jump-in air attacks, CD blowbacks and falling anti-airs.  The same
run at level 1 must still play a few of these actions but stay clearly
sparser, proving the difficulty scaling works.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
GS = 0x1020
M_ITEM = 0xF070
MSUOK = 0x107A
SEL1 = 0x1085
SEL2 = 0x1086
LOCK1 = 0x108E
LOCK2 = 0x108F
CPU1 = 0x1090
CPU2 = 0x1091
AI_LEVEL = 0x10EB
HP1 = 0x4010
HP2 = 0x4050
POW1 = 0x4030
POW2 = 0x4070
AI_DBG_THREAT = 0x4678
AI_DBG_BLOCK = 0x4679
AI_DBG_SPEC = 0x467A
AI_DBG_THROW = 0x467B
AI_DBG_PROJ = 0x467C
AI_DBG_MAX = 0x467D
AI_DBG_PUNISH = 0x467E
AI_DBG_SUPER = 0x467F
AI_DBG_AIR = 0x4680
AI_DBG_BLOW = 0x4681
AI_DBG_AA = 0x4682
AI_DBG_AAF = 0x4683
AI_DBG_JUMP = 0x4684
AI_DBG_COMBO = 0x4686


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def wait(core, predicate, label, limit=6000):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.ram[GS]} frame={core.ram[0x1024]}")


def boot():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    return core


def start_bout(core, level, p2=1):
    core.ram[MSUOK] = 1
    core.ram[M_ITEM] = 1                # SINGLE VS (free-play select)
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 5, "versus select")
    core.ram[SEL1] = 0                  # Kyo (P1)
    core.ram[SEL2] = p2                 # CPU opponent
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.ram[CPU1] = 1
    core.ram[CPU2] = 1
    core.ram[AI_LEVEL] = level
    core.put(POW1, 3000)
    core.put(POW2, 3000)
    wait(core, lambda: core.ram[GS] in (1, 4), "fight load")
    if core.ram[GS] == 4:
        tap(core, 3)                    # skip the character intro
    wait(core, lambda: core.ram[GS] == 1, "fight")
    core.step(180)                      # let the round start settle


def run_level(level, p2=1, frames=3600, close=False):
    # 3600 frames (was 2400): the CPU now presses forward instead of idling
    # at its band edge, so the rarer branches (falling jump-in anti-air,
    # air attack) need a slightly longer window to show up in this
    # deterministic CPU-vs-CPU coverage run.
    core = boot()
    try:
        start_bout(core, level, p2)
        if close:
            core.put(0x4000, 100 << 8)
            core.put(0x4040, 140 << 8)
            core.put(0x4004, 0)
            core.put(0x4044, 0)
        min_hp = 200
        for i in range(frames):
            core.step()
            min_hp = min(min_hp, core.word(HP1), core.word(HP2))
            if i % 120 == 0:
                # keep both CPUs stocked and alive so the coverage run can
                # observe the whole toolkit instead of ending in an early KO
                core.put(POW1, 3000)
                core.put(POW2, 3000)
                core.put(HP1, 200)
                core.put(HP2, 200)
        return {
            "threat": core.ram[AI_DBG_THREAT],
            "block": core.ram[AI_DBG_BLOCK],
            "spec": core.ram[AI_DBG_SPEC],
            "throw": core.ram[AI_DBG_THROW],
            "proj": core.ram[AI_DBG_PROJ],
            "max": core.ram[AI_DBG_MAX],
            "punish": core.ram[AI_DBG_PUNISH],
            "super": core.ram[AI_DBG_SUPER],
            "air": core.ram[AI_DBG_AIR],
            "blow": core.ram[AI_DBG_BLOW],
            "aa": core.ram[AI_DBG_AA],
            "aaf": core.ram[AI_DBG_AAF],
            "jump": core.ram[AI_DBG_JUMP],
            "combo": core.ram[AI_DBG_COMBO],
            "hp1": core.word(HP1),
            "hp2": core.word(HP2),
            "min_hp": min_hp,
        }
    finally:
        core.close()


def main():
    high = run_level(9)
    print("level 9 counters:", high)
    assert high["spec"] > 0, "CPU never chose a special/super/move"
    assert high["threat"] + high["block"] > 0, "CPU never reacted"
    assert high["max"] > 0, "CPU never activated MAX at level 9"
    assert high["super"] > 0, "CPU never chose a super"
    assert high["min_hp"] < 200, "CPU never damaged the opponent"
    assert high["throw"] > 0, "CPU never attempted a throw"
    assert high["jump"] > 0, "CPU never launched a jump-in"
    assert high["air"] > 0, "CPU never pressed a jump-in air attack"
    assert high["blow"] > 0, "CPU never used the CD blowback"
    assert high["aa"] > 0, "CPU never answered a falling jump-in"
    assert high["aaf"] > 0, "CPU never answered a jump-in while falling"
    assert high["combo"] > 0, "CPU never hit-confirmed into a special/super"

    low = run_level(1)
    print("level 1 counters:", low)
    # Level 1 is intentionally sparse, not lobotomised: it should still show
    # a few of these actions, clearly fewer than the top difficulty.
    assert sum(low[k] for k in
               ("threat", "block", "spec", "throw", "proj", "max",
                "punish", "super", "air", "blow", "aa", "jump",
                "combo")) > 0, \
        "level 1 must still attempt a few actions"
    assert sum(low[k] for k in
               ("threat", "block", "spec", "throw", "proj", "max",
                "punish", "super", "air", "blow", "aa", "jump")) < \
        sum(high[k] for k in
            ("threat", "block", "spec", "throw", "proj", "max",
             "punish", "super", "air", "blow", "aa", "jump",
             "combo")), \
        "level 1 must be less active than level 9"
    print("PASS AI level 1 sparse / level 9 full toolkit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
