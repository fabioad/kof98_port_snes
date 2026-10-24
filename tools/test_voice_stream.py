#!/usr/bin/env python3
"""Check streamed character voices during a real select-to-fight transition."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from capture_pair_headless import tap, wait
from test_roster import parse_tables


def to_select(core):
    for _ in range(60):
        if core.ram[0x1020] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[0x1020] == 6, "menu")
    core.ram[0xF070] = 1
    tap(core, 3)
    wait(core, lambda: core.ram[0x1020] == 5, "select")
    core.ram[0x1091] = 0


def main():
    generated = (ROOT / "build/gen_fight/voices.inc").read_text()
    assert generated.count('.SECTION "VoiceTab_') == 42
    assert ".DEFINE VOICE_CHAR_COUNT 42" in generated

    roster = parse_tables()
    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        to_select(core)
        core.ram[0xF053] = roster[1]["cell"]
        tap(core, 8, 1)
        core.ram[0xF052] = roster[0]["cell"]
        tap(core, 8, 0)

        states = []
        streams = []
        for _ in range(500):
            core.step()
            state = core.ram[0x1020]
            if not states or states[-1] != state:
                states.append(state)
            if core.ram[0x15A]:
                streams.append(core.word(0x158))
        assert states[:3] == [5, 4, 1], states
        assert len(streams) > 2 and streams[0] > streams[-1], streams
        print(f"PASS: states={states[:3]}, voice frames={len(streams)}, "
              f"BRR blocks={streams[0]}->{streams[-1]}")
    finally:
        core.close()

    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        to_select(core)
        core.ram[0xF053] = roster[0]["cell"]
        tap(core, 8, 1)
        core.ram[0xF052] = roster[15]["cell"]  # Terry: first MSU fighter
        tap(core, 8, 0)
        wait(core, lambda: core.ram[0x1020] == 1, "Terry fight", 1200)
        wait(core, lambda: core.word(0x4008) == 0 and
             core.word(0x4048) == 0, "idle", 1000)
        core.ram[0x1090] = core.ram[0x1091] = 0
        voice_frames = []
        for tick in range(40):
            core.buttons[0] = {1} if tick < 3 else set()
            core.step()
            if core.ram[0x15A]:
                voice_frames.append(core.word(0x158))
        assert voice_frames and voice_frames[0] > voice_frames[-1]
        print(f"PASS: Terry attack voice streamed for {len(voice_frames)} frames")
    finally:
        core.close()


if __name__ == "__main__":
    main()
