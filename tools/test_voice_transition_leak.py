#!/usr/bin/env python3
"""Regression: a fight voice must not survive into the next screen or bout.

The shared voice ring is ticked in every gamestate.  Queue a full ring at the
match-over banner and advance: it must be empty before the select screen or the
next campaign fight starts.  Before the transition reset the last record
started playing in the new screen.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                       # noqa: E402
from capture_pair_headless import tap, wait                 # noqa: E402
from test_roster import parse_tables                        # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS = 0x1020
VQ_HEAD, VQ_TAIL, VQ_BUSY = 0x5110, 0x5112, 0x5180
VQ_DATA = 0x5120
DIGI_ACTIVE = 0x15A
WIN_TIMER = 0x007B


def to_select(core, mode):
    for _ in range(60):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    core.ram[0xF070] = mode
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 5, "select")


def start_fight(core):
    roster = parse_tables()
    core.ram[0xF053] = roster[1]["cell"]
    core.ram[0xF052] = roster[0]["cell"]
    core.ram[0x108E] = 1                    # both sides locked
    core.ram[0x108F] = 1
    wait(core, lambda: core.ram[GS] == 1, "fight")
    core.step(60)


def queue_voices(core, count=8, ptr_index=0, voice_index=0):
    core.put(VQ_HEAD, 0)
    for i in range(count):
        core.ram[VQ_DATA + i * 4] = ptr_index
        core.ram[VQ_DATA + i * 4 + 1] = 0
        core.ram[VQ_DATA + i * 4 + 2] = voice_index
        core.ram[VQ_DATA + i * 4 + 3] = 0
    core.put(VQ_TAIL, count * 4)


def finish_match(core, wins1):
    core.ram[0x1080] = wins1
    core.put(0x4050, 0)                     # P2 HP = 0
    wait(core, lambda: core.ram[GS] == 0, "match-over banner")


def assert_ring_empty(core, where):
    assert core.word(VQ_HEAD) == core.word(VQ_TAIL), (
        f"voice ring survived into {where}")
    assert core.word(VQ_BUSY) == 0, f"pending voice survived into {where}"


def check_select_transition():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        to_select(core, mode=1)             # SINGLE VS -> select after match
        start_fight(core)
        finish_match(core, wins1=1)
        queue_voices(core)
        core.put(WIN_TIMER, 419)            # next TitleTick -> select now
        wait(core, lambda: core.ram[GS] == 5, "select after banner", 300)
        assert_ring_empty(core, "select")
        for tick in range(600):
            core.step()
            assert not core.ram[DIGI_ACTIVE], (
                f"streamed fight voice started on select (frame +{tick})")
        assert_ring_empty(core, "select")
        print("PASS fight voice ring cleared on the select transition")
    finally:
        core.close()


def check_next_fight_transition():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        to_select(core, mode=0)             # SINGLE PLAY -> next foe
        start_fight(core)
        finish_match(core, wins1=1)
        queue_voices(core)
        wait(core, lambda: core.ram[GS] == 4, "next fight setup", 600)
        assert_ring_empty(core, "next fight")
        print("PASS fight voice ring cleared before the next campaign fight")
    finally:
        core.close()


def main():
    check_select_transition()
    check_next_fight_transition()


if __name__ == "__main__":
    main()
