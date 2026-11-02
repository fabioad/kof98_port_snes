#!/usr/bin/env python3
"""Headless regression for the Ryuko Ranbu family.

Ryo's and Robert's source flurries keep one HitDef and reset MUGEN's movehit
latch between contacts; Sakura's Haru Ichiban re-issues the HitDef on each
strike element.  Without ActTab op18 (MoveHitReset) only the opening punch
landed.  Each character must reach its rush state, register several contacts,
chain into the launcher state and knock the opponent down.

Run after a PVSnesLib build:

    python3 tools/test_ranbu_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    enter_fight, tap, wait, GS, START, A, B, X,
    DOWN, LEFT, RIGHT,
)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP2 = 0x40
P1_STATE, P1_X = 0x4008, 0x4000
P2_STATE, P2_HP = 0x4048, 0x4050
P1_POWER = 0x4030
DOWN_STATE = 10


def boot_select(core):
    wait(core, lambda: core.word(GS) == 14, "msu opening", 6000)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(60)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    core.ram[0xF070] = 1
    tap(core, START)
    wait(core, lambda: core.word(GS) == 5, "select")
    core.ram[0x1091] = 0
    core.step(10)
    return core.save()


def press(core, direction, frames=2):
    core.buttons[0] = set(direction)
    core.step(frames)


def qcfx2(core, button):
    for _ in range(2):
        for d in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
            press(core, d)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def halfcircle(core, button):
    for d in ((DOWN,), (DOWN, RIGHT), (RIGHT,), (DOWN, RIGHT),
              (DOWN,), (DOWN, LEFT), (LEFT,)):
        press(core, d)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def run(core, select, char, motion, rush_sid, launch_sid, hit_damage,
        min_hits, low, high):
    enter_fight(core, select, char, "kyo")
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.put(P1_X, 60 << 8)
    core.put(0x4040, 120 << 8)
    core.put(P1_POWER, 3000)
    core.step(20)
    motion(core)

    seen, drops = [], []
    last = core.word(P2_HP)
    down = False
    for _ in range(420):
        core.step()
        state = core.ram[P1_STATE]
        if not seen or seen[-1] != state:
            seen.append(state)
        hp = core.word(P2_HP)
        if hp < last:
            drops.append((state, last - hp))
            last = hp
        down |= core.ram[P2_STATE] == DOWN_STATE

    rush_hits = [d for s, d in drops if s == rush_sid]
    total = sum(d for _, d in drops)
    fails = []
    if rush_sid not in seen:
        fails.append(f"rush state {rush_sid} never reached: {seen}")
    if launch_sid not in seen:
        fails.append(f"launch state {launch_sid} never reached: {seen}")
    if len(rush_hits) < min_hits:
        fails.append(f"only {len(rush_hits)} rush contacts: {drops}")
    if any(abs(d - hit_damage) > 1 for d in rush_hits):
        fails.append(f"unexpected rush damage {rush_hits}")
    if not down:
        fails.append("victim was not knocked down")
    if not low <= total <= high:
        fails.append(f"total damage {total} outside {low}..{high}")
    return fails, drops, total, down


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    fails = []
    try:
        select = boot_select(core)
        cases = [
            # Ryo: half-circle + X, rush 3120 -> launcher 3121.
            ("ryo", halfcircle, X, 88, 89, 4, 6, 40, 100),
            # Robert: half-circle + X, flurry 3105 -> finish 3107.
            ("robert", halfcircle, X, 85, 86, 4, 6, 50, 110),
            # Sakura: double QCF + B, Haru Ichiban 3100 slices.
            ("sakura", qcfx2, B, 88, 89, 5, 4, 25, 70),
        ]
        for char, motion, button, rush, launch, dmg, hits, lo, hi in cases:
            def run_motion(c, _m=motion, _b=button):
                _m(c, _b)
            case_fails, drops, total, down = run(
                core, select, char, run_motion, rush, launch, dmg, hits,
                lo, hi)
            if case_fails:
                fails.extend(f"{char}: {f}" for f in case_fails)
            contacts = sum(1 for s, d in drops if s == rush)
            print(f"{char}: contacts={contacts} total={total} down={down}")
        if fails:
            for failure in fails:
                print("FAIL:", failure)
            return 1
        print("Ryuko Ranbu: Ryo/Robert/Sakura multi-hit, launch, knockdown OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
