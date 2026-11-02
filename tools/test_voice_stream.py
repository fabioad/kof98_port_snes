#!/usr/bin/env python3
"""Check streamed character voices during a real select-to-fight transition."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight
from test_roster import parse_tables


def main():
    generated = (ROOT / "build/gen_fight/voices.inc").read_text()
    count = generated.count('.SECTION "VoiceTab_')
    assert count >= 42, count
    assert f".DEFINE VOICE_CHAR_COUNT {count}" in generated

    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "kyo", "iori")

        states = []
        for _ in range(500):
            core.step()
            state = core.ram[0x1020]
            if not states or states[-1] != state:
                states.append(state)
        assert 1 in states, states
        print(f"PASS: select-to-fight transition states={states[:4]}")
    finally:
        core.close()

    core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
                ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "terry", "kyo")
        for _ in range(1000):
            core.step()
            if core.word(0x4008) == 0 and core.word(0x4048) == 0:
                break
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
