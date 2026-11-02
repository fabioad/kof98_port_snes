#!/usr/bin/env python3
"""Headless regression: title -> CPU demo must replace Cipher Beta with the
demo stage module.

The title song loads a UI module and used to leave MUSIC_VALID set.  If the
random demo picked the same stage as the previous bout, StageMusic skipped
the reload: Cipher Beta kept playing and the UI winner effect stayed
selected.  The test forces the demo stage to match a stale cache entry and
checks that the stage module was loaded (UI_SFXLOAD back to 0) and that a
deferred winner voice was dropped.

Run after a PVSnesLib build:

    python3 tools/test_demo_music_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import tap, wait, GS, START  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"

S_WAIT = 0xF074
FRAMECNT = 0x1024
RNG = 0x1088
STAGEIDX = 0x1087
STAGEF = 0x10C5
MUSIC_STAGE = 0x10E5
MUSIC_VALID = 0x10E6
WINVOICE = 0x102F
UI_SFXLOAD = 0xF07E

TARGET = 6                       # valid non-boss stage
TADJ = TARGET - 1                # StagePick skips index 5


def word(core, addr):
    return core.ram[addr] | core.ram[addr + 1] << 8


def boot_title(core):
    wait(core, lambda: core.word(GS) == 14, "msu opening", 8000)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title", 8000)
    # Wait until TitleEnter has finished and the idle counter is running.
    for _ in range(600):
        if word(core, S_WAIT) > 60:
            return core.save()
        core.step()
    raise AssertionError("title idle counter never started")


def trigger(core, snapshot, predicted):
    core.load(snapshot)
    core.ram[MUSIC_STAGE] = TARGET
    core.ram[MUSIC_VALID] = 1
    core.ram[UI_SFXLOAD] = 1
    core.ram[WINVOICE] = 1
    core.put(S_WAIT, 1329)
    core.put(FRAMECNT, 0)
    core.put(RNG, TADJ ^ predicted)
    core.step(1)
    for _ in range(200):
        if core.ram[GS] in (1, 4):
            break
        core.step()
    return core.ram[STAGEIDX]


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        snapshot = boot_title(core)
        predicted = None
        for p in range(1, 25):
            if trigger(core, snapshot, p) == TARGET:
                predicted = p
                break
        if predicted is None:
            print("FAIL could not force the demo onto the stale stage")
            return 1
        stage = trigger(core, snapshot, predicted)
        core.step(30)                     # let StageMusic handshake finish
        state = {
            "gs": core.ram[GS],
            "stage": core.ram[STAGEIDX],
            "music_stage": core.ram[MUSIC_STAGE],
            "music_valid": core.ram[MUSIC_VALID],
            "ui_sfxload": core.ram[UI_SFXLOAD],
            "winvoice": core.ram[WINVOICE],
        }
        fails = []
        if stage != TARGET:
            fails.append(f"demo stage {stage} != {TARGET}")
        if state["ui_sfxload"]:
            fails.append("UI effect slots still selected (Cipher kept)")
        if not state["music_valid"] or state["music_stage"] != TARGET:
            fails.append(f"stage music cache {state}")
        if state["winvoice"]:
            fails.append("deferred winner voice survived StartFight")
        if fails:
            for failure in fails:
                print("FAIL:", failure)
            return 1
        print(f"Demo music hand-off: stage {TARGET} reloaded, "
              f"UI_SFXLOAD=0, winner voice dropped")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
