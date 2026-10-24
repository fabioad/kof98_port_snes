#!/usr/bin/env python3
"""Regression: a KO'd fighter must lie on the floor, never stand.

A melee finishing blow already entered S_DOWN, but a projectile (or any
scripted TargetLifeAdd) could zero the loser's HP while it was in S_HIT;
hitstun then expired into S_STAND and the defeated fighter stood through
the whole KO banner.  This checks the projectile KO path and the KoTick
safety net that parks a zero-HP fighter in the lie pose.

Run after a PVSnesLib build:

    python3 tools/test_ko_lie_headless.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"

GS = 0x1020
FP, FP2 = 0x4000, 0x40
F_X, F_Y, F_STATE, F_HP = 0, 2, 8, 16
P2 = FP + FP2
S_STAND, S_DOWN = 0, 10
DOWN, RIGHT = 5, 7
LIGHT_P, STRONG_P = 1, 9    # SNES Y -> MUGEN x, SNES X -> MUGEN y


def press(core, buttons, ticks=1):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def qcf_p(core):
    for d in ({DOWN}, {DOWN, RIGHT}, {RIGHT}):
        core.buttons[0] = set(d)
        core.step(1)
    press(core, {LIGHT_P}, 2)


def wait(core, pred, label, limit=2000):
    for _ in range(limit):
        if pred():
            return
        core.step()
    raise AssertionError(f"{label}: gs={core.word(GS)} "
                         f"st={core.ram[P2 + F_STATE]} "
                         f"hp={core.word(P2 + F_HP)}")


def loser_lands(core, limit=120):
    """Wait for the KO'd P2 to be lying on the floor (S_DOWN, y == 0)."""
    for _ in range(limit):
        if core.ram[P2 + F_STATE] == S_DOWN and core.word(P2 + F_Y) == 0:
            return
        core.step()
    raise AssertionError(
        f"loser never landed: st={core.ram[P2 + F_STATE]} "
        f"y={core.word(P2 + F_Y)}")


def assert_stays_lie(core, ticks):
    for _ in range(ticks):
        st = core.ram[P2 + F_STATE]
        assert st != S_STAND, "KO'd fighter recovered to S_STAND"
        core.step()
    assert core.ram[P2 + F_STATE] == S_DOWN, \
        f"loser left S_DOWN: {core.ram[P2 + F_STATE]}"


def projectile_ko(core, sel):
    """Ryu's Hadouken must knock the one-HP opponent down."""
    enter_fight(core, sel, "ryu", "kyo")
    core.put(FP + F_X, 100 << 8)
    core.put(P2 + F_X, 150 << 8)
    core.step(20)
    core.put(P2 + F_HP, 1)
    qcf_p(core)
    wait(core, lambda: core.word(GS) == 2, "projectile KO", limit=200)
    assert core.word(P2 + F_HP) == 0
    loser_lands(core)
    assert_stays_lie(core, 60)
    print("OK projectile KO: loser lies down and stays down")


def watchdog(core, sel):
    """Zero HP + a state that would stand: KoTick must re-seat the body."""
    enter_fight(core, sel, "yuri", "kyo")
    core.put(FP + F_X, 70 << 8)
    core.put(P2 + F_X, 110 << 8)
    core.put(FP + F_HP, 200)
    core.put(P2 + F_HP, 1)
    core.step(20)
    core.buttons[0] = {STRONG_P}
    core.step(3)
    core.buttons[0] = set()
    wait(core, lambda: core.word(GS) == 2, "melee KO")
    loser_lands(core)
    # Simulate a stray state that recovered into the stand pose.
    core.ram[P2 + F_STATE] = S_STAND
    core.step(2)
    assert core.ram[P2 + F_STATE] == S_DOWN, \
        "watchdog left the KO'd fighter standing"
    assert_stays_lie(core, 60)
    print("OK KoTick watchdog: a standing zero-HP fighter is put back down")


def main(core_path=CORE, rom=ROM):
    core = Core(core_path, rom)
    try:
        sel = boot_select(core)
        projectile_ko(core, sel)
        watchdog(core, sel)
        print("PASS KO loser lies on the floor")
    finally:
        core.close()


if __name__ == "__main__":
    main()
