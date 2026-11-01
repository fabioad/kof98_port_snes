#!/usr/bin/env python3
"""Build the full-screen ending-colour intro video (M1VID1).

The source is the same KOF '98 opening already extracted under
``assets/video/Wmva3m93t34/frames``.  This tool samples 133 frames across
the first 44.3 s and converts each through the endings pipeline
(256x224, 4 bpp, four 15-colour palette bands), then packs the CHR, map and
palette into ``snes_video/Wmva3m93t34.m1vid``.

Container M1VID1:

    u8  magic[8]       "M1VID1\\0\\0"
    u16 width          256
    u16 height         224
    u16 fps            3
    u16 flags          0
    u32 frame_count    133
    u32 duration_ms    44300
    table               133 * (u32 offset, u16 chr_len, u16 ticks)
    data                chr_len bytes CHR, 2048-byte map, 128-byte palette

Frame ticks are 20 for the first 132 frames and 18 for the last, exactly
2658 ticks (44.3 s at 60 Hz).
"""
import argparse
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_endings import build_frame                  # noqa: E402

SRC = ROOT / "assets/video/Wmva3m93t34/frames"
OUT = ROOT / "assets/video/Wmva3m93t34/snes_video/Wmva3m93t34.m1vid"
W, H = 256, 224
FPS = 3
FRAMES = 133
TOTAL_TICKS = 2658
SOURCE_WINDOW = 354          # 44.3 s at the 8 fps frame export


# The player stages each frame through a 512-byte WRAM buffer, so a frame's
# load costs roughly one vblank per 12 KiB of CHR.  Subtracting that from the
# display ticks keeps the wall-clock sequence at the intended 44.3 s even
# though the nominal table sums to fewer ticks.  Calibrated with the Snes9x
# headless reference (101 frames of overhead over this sequence).
LOAD_BYTES_PER_FRAME = 12000


def frame_ticks(i, chr_len):
    base = 20 if i < FRAMES - 1 else 18
    load = (chr_len + LOAD_BYTES_PER_FRAME // 2) // LOAD_BYTES_PER_FRAME
    return max(2, base - load)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    src = sorted(args.frames.glob("frame_*.png"))
    if len(src) < SOURCE_WINDOW:
        raise SystemExit(f"need at least {SOURCE_WINDOW} source frames, "
                         f"found {len(src)}")
    src = src[:SOURCE_WINDOW]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="m1vid_"))
    table = []
    payload = bytearray()
    try:
        for i in range(FRAMES):
            idx = min(SOURCE_WINDOW - 1,
                      int(round(i * (SOURCE_WINDOW - 1) / (FRAMES - 1))))
            base = tmp / f"f{i:03d}"
            build_frame(str(src[idx]), str(base))
            chr_data = base.with_suffix(".chr").read_bytes()
            map_data = base.with_suffix(".map").read_bytes()
            pal_data = base.with_suffix(".pal").read_bytes()
            if len(map_data) != 2048 or len(pal_data) != 128:
                raise SystemExit(f"frame {i}: unexpected map/pal size "
                                 f"{len(map_data)}/{len(pal_data)}")
            table.append((len(payload), len(chr_data),
                          frame_ticks(i, len(chr_data))))
            payload += chr_data + map_data + pal_data
            if (i + 1) % 10 == 0 or i + 1 == FRAMES:
                print(f"  frame {i + 1}/{FRAMES}: {len(chr_data)}B chr")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    header = b"M1VID1\0\0"
    header += struct.pack("<HHHH", W, H, FPS, 0)
    header += struct.pack("<II", FRAMES, 44300)
    for off, chr_len, ticks in table:
        header += struct.pack("<IHH", off, chr_len, ticks)
    args.out.write_bytes(header + payload)
    print(f"wrote {args.out} ({len(header) + len(payload)} bytes, "
          f"{FRAMES} frames, {sum(t for *_x, t in table)} ticks)")

    manifest_path = ROOT / "assets/video/Wmva3m93t34/manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest["m1vid"] = {
            "file": str(args.out.relative_to(ROOT)),
            "resolution": [W, H],
            "colors": 256,
            "palette": "4 bands x 15 colors (endings pipeline)",
            "fps": FPS,
            "frame_count": FRAMES,
            "duration_seconds": 44.3,
            "ticks": sum(t for *_x, t in table),
            "nominal_ticks": TOTAL_TICKS,
            "load_compensation_ticks": TOTAL_TICKS - sum(t for *_x, t in table),
            "format": "M1VID1",
            "audio": False,
            "bytes": args.out.stat().st_size,
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
