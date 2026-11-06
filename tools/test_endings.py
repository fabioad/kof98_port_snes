#!/usr/bin/env python3
"""Defeat Omega in each campaign and verify every rendered ending card.

Use the actual KO/ending transition, not a forced gamestate. Check pixels,
clock progress, automatic card transitions and the eventual return to title.
"""
import argparse
import hashlib
from pathlib import Path

import test_boss_intro_headless as boss
import test_survivor_practice_headless as survivor
from calibration.headless import Core
from capture_pair_headless import save_frame, wait

ROOT = Path(__file__).resolve().parents[1]


def verify_cards(core, mode, output):
    state = 10 if mode == "survivor" else 8
    count = 13 if state == 10 else 23
    hashes = set()
    for screen in range(count):
        wait(core, lambda: core.ram[boss.E_SCR] == screen and core.word(0xF079) > 0,
             f"{mode} ending {screen}", 1500)
        assert core.ram[boss.GS] == state, f"{mode}: ending state corrupted"
        initial_timer = core.word(0xF079)
        # Normal cards fade over ~124 frames, montage cards in ~16 frames.
        core.step(40 if state == 10 else (30 if 6 <= screen <= 20 else 140))
        assert core.ram[boss.GS] == state, f"{mode}: renderer crashed"
        assert core.ram[boss.E_SCR] == screen, f"{mode}: unexpected card skip"
        assert core.word(0xF079) < initial_timer, f"{mode}: ending clock froze"
        assert core.last_frame, "no video output"
        w, h, pitch, raw, fmt = core.last_frame
        size = 4 if fmt == 1 else 2
        pixels = b"".join(raw[y * pitch:y * pitch + w * size] for y in range(h))
        colors = {pixels[i:i + size] for i in range(0, len(pixels), size)}
        minimum = 8 if state == 10 or 6 <= screen <= 20 else 16
        assert len(colors) > minimum, (
            f"{mode} card {screen}: only {len(colors)} colors (black/flat frame)")
        digest = hashlib.sha256(pixels).digest()
        assert digest not in hashes, f"{mode} card {screen}: repeated art"
        hashes.add(digest)
        output.mkdir(parents=True, exist_ok=True)
        save_frame(core.last_frame, output / f"{mode}_{screen:02}.png")
        print(f"PASS {mode} ending {screen:02}: {len(colors)} colors", flush=True)
        # Let the game advance itself, including the final return to title.
        wait(core, lambda: core.ram[boss.E_SCR] != screen or core.ram[boss.GS] == 0,
             f"{mode} automatic transition {screen}", 1500)
    assert core.ram[boss.GS] == 0, f"{mode}: did not return to title"
    print(f"PASS {mode}: all {count} cards and return to title", flush=True)


def run(core_path, rom, output):
    def factory(*_args):
        core = Core(core_path, rom)
        core.capture_video = True
        return core

    original_boss, original_survivor = boss.Core, survivor.Core
    boss.Core = survivor.Core = factory
    try:
        for mode, scenario in (("single", boss.single_boss_intro),
                               ("team", boss.team_boss_intro),
                               ("survivor", boss.survivor_boss_intro)):
            scenario(lambda core: verify_cards(core, mode, output))
    finally:
        boss.Core, survivor.Core = original_boss, original_survivor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=boss.CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    parser.add_argument("--output", type=Path, default=ROOT / "build/ending_regression")
    args = parser.parse_args()
    run(args.core, args.rom, args.output)
