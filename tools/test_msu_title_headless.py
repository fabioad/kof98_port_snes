#!/usr/bin/env python3
"""Headless check: the natural end of the MSU opening must land on the same
title screen as skipping it with START.

A late video vblank used to run while TitleEnter was loading the title art,
re-assert BG2 and DMA a staged chunk over the title map/OBJ.  The result was
a periodically garbled title, most visible after the full opening played.
The prompt blinks, so the comparison masks its rows.

Run after a PVSnesLib build:

    python3 tools/test_msu_title_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import tap, wait, GS, START  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"


def boot_msu(core):
    wait(core, lambda: core.word(GS) == 14, "msu opening", 8000)
    core.step(2)
    return core.save()


def title_frame(core, snapshot, skip):
    core.load(snapshot)
    core.capture_video = True
    core.step(2)
    if skip:
        tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title", 8000)
    core.step(24)                            # same blink phase for both
    return core.last_frame


def masked_diff(a, b, y0, y1):
    width, height, pitch, raw_a, _ = a
    _, _, _, raw_b, _ = b
    diff = 0
    total = 0
    for y in range(height):
        if y0 <= y < y1:
            continue
        row = y * pitch
        for x in range(0, width * 2, 2):
            if raw_a[row + x:row + x + 2] != raw_b[row + x:row + x + 2]:
                diff += 1
            total += 1
    return diff, total


def main():
    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        snapshot = boot_msu(core)
        # 24 title frames from gs0: identical blink phase for both branches.
        natural = title_frame(core, snapshot, skip=False)
        skipped = title_frame(core, snapshot, skip=True)
        # Mask the blinking PRESS START row (y ~128-152) and credit row.
        diff, total = masked_diff(natural, skipped, 120, 210)
        if diff > total // 200:                # >0.5% of the visible area
            print(f"FAIL title differs after natural finish: "
                  f"{diff}/{total} pixels")
            return 1
        print(f"MSU title hand-off: natural and skipped title match "
              f"({diff}/{total} masked pixels differ)")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
