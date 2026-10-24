#!/usr/bin/env python3
"""Check that a second round starts after the announcer effect is uploaded."""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from capture_pair_headless import tap, wait
from test_roster import parse_tables

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--delay", type=int, default=0)
parser.add_argument("--match-over", action="store_true")
parser.add_argument("--auto-banner", action="store_true")
args = parser.parse_args()
roster = parse_tables()
core = Core("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so",
            ROOT / "kof98-snes.sfc")
try:
    for _ in range(60):
        if core.ram[0x1020] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[0x1020] == 6, "menu")
    core.ram[0xF070] = 1
    tap(core, 3)
    wait(core, lambda: core.ram[0x1020] == 5, "select")
    core.capture_audio = True
    core.step(args.delay)
    core.ram[0x1091] = 0
    core.ram[0xF053] = roster[1]["cell"]
    tap(core, 8, 1)
    core.ram[0xF052] = roster[0]["cell"]
    tap(core, 8, 0)
    wait(core, lambda: core.ram[0x1020] == 1, "round 1")
    wait(core, lambda: core.word(0x4008) == 0 and core.word(0x4048) == 0,
         "idle")
    core.audio_samples = 0
    core.audio_nonzero_batches = 0
    core.ram[0x73] = 12  # final hit can arrive during hit-stop
    if args.match_over:
        core.ram[0x1080] = 1  # first win already scored: this KO ends match
    core.put(0x4050, 0)
    if args.match_over:
        wait(core, lambda: core.ram[0x1020] == 0, "match-over")
        if args.auto_banner:
            wait(core, lambda: core.ram[0x1020] in (1, 4, 5),
                 "automatic post-match advance", 500)
            print("PASS final banner auto-advance")
        else:
            tap(core, 8, 0)  # A/confirm must leave the final banner
            wait(core, lambda: core.ram[0x1020] == 5, "post-match select")
            print("PASS final banner confirm")
        raise SystemExit(0)
    seen = []
    max_effect_slots = 0
    for tick in range(3600):
        state = core.ram[0x1020]
        max_effect_slots = max(max_effect_slots, core.ram[0x153])
        if not seen or seen[-1] != state:
            seen.append(state)
        if len(seen) >= 3 and seen[-3:] == [0, 4, 1]:
            assert max_effect_slots >= 6, "round voice was not loaded"
            assert core.audio_nonzero_batches, "audio output stayed silent"
            print("PASS round 2", "stage", core.ram[0x1087], "states", seen,
                  "effects_pending", core.ram[0x46F8], "ticks", tick,
                  "audio_samples", core.audio_samples,
                  "audible_batches", core.audio_nonzero_batches,
                  "loaded_effect_slots", core.ram[0x153],
                  "peak_effect_slots", max_effect_slots)
            break
        core.step()
    else:
        raise AssertionError(f"round change timed out: states={seen} "
                             f"gs={core.ram[0x1020]} "
                             f"effects_pending={core.ram[0x46F8]}")
finally:
    core.close()
