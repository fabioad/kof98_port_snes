#!/usr/bin/env python3
"""Exercise OPTIONS through real menu input, including its text and settings."""
import argparse
from pathlib import Path

from calibration.headless import Core
from test_start_transition import tap as tap_input, wait_for

ROOT = Path(__file__).resolve().parents[1]
CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
GS, ITEM, OPT, SONG = 0x1020, 0xF070, 0xF079, 0xF07A
LEVEL, AI, LANG, MODE = 0x10ED, 0x10EB, 0xF07F, 0x10C0
START, UP, DOWN, LEFT, RIGHT, A, B = 3, 4, 5, 6, 7, 8, 0


def tap(core, button):
    tap_input(core, button)
    # A sound-test song replaces the SPC module across several video frames.
    # Wait for normal game ticks before sending another controller edge.
    for _ in range(2):
        frame = core.ram[0x1024]
        wait_for(core, lambda: core.ram[0x1024] != frame, "input settled")


def label(core, text, y):
    cells = {(core.ram[a], core.ram[a + 1]): core.ram[a + 2]
             for a in range(0x1800, 0x1A00, 4)}
    for i, ch in enumerate(text):
        tile = ord(ch) - ord('A') + 1 if ch != ' ' else 0
        assert cells.get((40 + 6 * i, y)) == tile, f"missing {text} glyph {i}"


def cursor(core):
    """Return the two bracket cells (x, y, tile) emitted by OptionsDraw."""
    left = right = None
    for a in range(0x1800, 0x1A00, 4):
        x, y, tile = core.ram[a], core.ram[a + 1], core.ram[a + 2]
        if tile == 60:
            left = (x, y)
        elif tile == 61:
            right = (x, y)
    return left, right


def run(library, rom):
    core = Core(library, rom)
    try:
        wait_for(core, lambda: core.word(GS) == 7, "opening")
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 0, "title")
        core.step(4)
        tap(core, START)
        wait_for(core, lambda: core.word(GS) == 6, "mode menu")
        menu = core.save()
        # Wrap through EXIT to OPTIONS without writing the menu selection.
        tap(core, UP)
        assert core.ram[ITEM] == 7, "menu did not wrap to EXIT"
        tap(core, UP)
        assert core.ram[ITEM] == 6, "cursor did not reach OPTIONS"
        mode = core.ram[MODE]
        tap(core, START)
        assert core.word(GS) == 11, f"OPTIONS opened gs={core.word(GS)}"
        assert core.ram[MODE] == mode, "OPTIONS changed the play mode"
        assert core.ram[OPT] == 0, "OPTIONS did not select LEVEL"
        for text, y in (("LEVEL", 56), ("LANGUAGE", 80),
                        ("SOUND TEST", 104), ("EXIT", 128)):
            label(core, text, y)
        assert cursor(core) == ((24, 56), (216, 56)), (
            f"cursor not on LEVEL: {cursor(core)}")
        print("PASS OPTIONS opens its four correctly drawn settings", flush=True)

        initial = core.ram[LEVEL]
        for _ in range(8):
            before = core.ram[LEVEL]
            tap(core, RIGHT)
            assert core.ram[LEVEL] == before % 8 + 1
            assert core.ram[AI] == (9 if core.ram[LEVEL] == 8 else core.ram[LEVEL])
            assert core.word(GS) == 11
        assert core.ram[LEVEL] == initial
        tap(core, LEFT)
        assert core.ram[LEVEL] == (initial - 2) % 8 + 1
        tap(core, RIGHT)
        print("PASS LEVEL wraps 1..8 and updates CPU difficulty", flush=True)

        tap(core, DOWN)
        assert core.ram[OPT] == 1
        assert cursor(core) == ((24, 80), (216, 80)), (
            f"cursor not on LANGUAGE: {cursor(core)}")
        initial_lang = core.ram[LANG]
        for _ in range(4):
            before = core.ram[LANG]
            tap(core, RIGHT)
            assert core.ram[LANG] == (before + 1) % 4
        tap(core, LEFT)
        assert core.ram[LANG] == (initial_lang - 1) % 4
        tap(core, RIGHT)
        print("PASS LANGUAGE cycles all four languages", flush=True)

        tap(core, DOWN)
        wait_for(core, lambda: core.ram[OPT] == 2, "sound-test module loaded")
        assert core.ram[OPT] == 2, f"SOUND TEST selected row {core.ram[OPT]}"
        assert cursor(core) == ((24, 104), (216, 104)), (
            f"cursor not on SOUND TEST: {cursor(core)}")
        assert core.ram[SONG] == 0
        core.capture_audio = True
        core.step(120)
        assert core.audio_nonzero_batches > 0, "SOUND TEST produced no audio"
        tap(core, RIGHT)
        assert core.ram[SONG] == 1
        tap(core, LEFT)
        assert core.ram[SONG] == 0
        tap(core, LEFT)
        assert core.ram[SONG] == 16
        tap(core, START)
        assert core.ram[SONG] == 0, "START did not restart the first song"
        print("PASS SOUND TEST plays audio, changes tracks and wraps", flush=True)

        tap(core, DOWN)
        assert core.ram[OPT] == 3, f"EXIT selected row {core.ram[OPT]}"
        assert cursor(core) == ((24, 128), (216, 128)), (
            f"cursor not on EXIT: {cursor(core)}")
        tap(core, START)
        assert core.word(GS) == 6 and core.ram[ITEM] == 6
        tap(core, A)
        assert core.word(GS) == 11, "A did not reopen OPTIONS"
        assert cursor(core) == ((24, 56), (216, 56)), (
            f"cursor not reset to LEVEL: {cursor(core)}")
        assert core.ram[LEVEL] == initial and core.ram[LANG] == initial_lang
        tap(core, B)
        assert core.word(GS) == 6 and core.ram[ITEM] == 6
        print("PASS EXIT/B return to OPTIONS in the menu; settings persist", flush=True)

        for item, mode in enumerate((1, 0, 2, 3, 4, 5)):
            core.load(menu)
            core.buttons = [set(), set()]
            for _ in range(item):
                tap(core, DOWN)
            assert core.ram[ITEM] == item
            tap(core, START)
            wait_for(core, lambda: core.word(GS) == 5, f"mode {item} select")
            assert core.ram[MODE] == mode, f"item {item} opened mode {core.ram[MODE]}"
        print("PASS all six play modes still open their own selection", flush=True)
        core.load(menu)
        core.buttons = [set(), set()]
        tap(core, UP)
        tap(core, START)
        assert core.word(GS) == 0, "main-menu EXIT did not return to title"
        print("PASS main-menu EXIT returns to the title", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    run(args.core, args.rom)
