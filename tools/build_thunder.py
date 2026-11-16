#!/usr/bin/env python3
"""Secret Mr. Karate flash card used between the attract demo and the intro.

The source is a 1536x1024 still.  A centred 1170x1024 crop keeps the whole
figure and maps to the SNES 256x224 frame without stretching it; build_frame
then produces the usual four-band 4bpp Mode-1 BG2 art (.chr/.map/.pal).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_endings import build_frame                    # noqa: E402

SRC = ROOT / "mr_karate.png"
DST = ROOT / "src/gen_menu/thunder"
CROP = (183, 0, 1353, 1024)                              # 1170x1024, centred


def main():
    os.makedirs(DST.parent, exist_ok=True)
    size = build_frame(str(SRC), str(DST), crop=CROP)
    print(f"thunder: {size} B of CHR")


if __name__ == "__main__":
    main()
