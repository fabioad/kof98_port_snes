#!/usr/bin/env python3
"""Build the full-screen ending-colour intro video (M1VID1).

The source is the same KOF '98 opening already extracted under
``assets/video/Wmva3m93t34/frames``.  This tool samples 665 frames across
the first 44.3 s (15 fps, interpolated from the 8 fps source) and converts
each through the endings pipeline (256x224, 4 bpp, four 15-colour palette
bands), then packs the CHR, map and palette into
``snes_video/Wmva3m93t34.m1vid``.

Container M1VID1:

    u8  magic[8]       "M1VID1\\0\\0"
    u16 width          256
    u16 height         224
    u16 fps            15
    u16 flags          0
    u32 frame_count    665
    u32 duration_ms    44300
    table               665 * (u32 offset, u16 chr_len, u16 ticks)
    data                chr_len bytes CHR, 2048-byte map, 128-byte palette

Frame ticks are balanced so the table totals exactly 2658 ticks (44.3 s at
60 Hz) while every frame has enough display time to stage its successor.
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
FPS = 15                           # ~15 fps, same 44.3 s duration
FRAMES = 665
TOTAL_TICKS = 2658
SOURCE_WINDOW = 354          # 44.3 s at the 8 fps frame export
# The YouTube upload places the opening inside a black 16:9 frame.  In the
# 128x112 export the content window is x=14..114, y=8..104; crop it before
# the 256x224 resize so the picture fills the SNES screen.
SOURCE_CROP = (14, 8, 114, 104)
BAND_COLORS = 15             # same 15-colour bands as the endings


CHUNK_BYTES = 4864                     # one staged chunk per tick
MAP_BYTES = 2048                       # CHR and map stream back to back


def _need(chr_len):
    # The player lets one chunk straddle the CHR->map boundary, so the map
    # rides along with the CHR tail instead of costing an extra tick.
    return (chr_len + MAP_BYTES + CHUNK_BYTES - 1) // CHUNK_BYTES


def balance_ticks(chr_lens):
    """Pick per-frame ticks that total TOTAL_TICKS and never starve the
    double-buffer streamer.  Frames need enough ticks to stage their CHR
    and map at one chunk per tick; spare ticks go to the shortest frames so
    the opening keeps the exact 44.3 s wall-clock duration.
    """
    need = [_need(c) for c in chr_lens]
    # Frame i stays on screen while frame i+1 is streamed, so its display
    # time must cover the *next* frame's payload.  Two ticks is the minimum
    # that avoids a one-frame flash; the last frame has no successor but
    # still gets the same floor.
    ticks = [max(need[i + 1], 2) for i in range(len(chr_lens) - 1)]
    ticks.append(max(need[-1], 2))
    if sum(ticks) > TOTAL_TICKS:
        raise SystemExit(
            f"15 fps needs {sum(ticks)} ticks, budget {TOTAL_TICKS}; "
            "use a larger CHUNK_BYTES or lower fps")
    # Spend the remaining ticks on the shortest frames first, so simple
    # scenes do not flash by at 60 fps while complex ones hold for longer.
    slack = TOTAL_TICKS - sum(ticks)
    order = sorted(range(len(ticks)), key=lambda i: (ticks[i], i))
    for k in range(slack):
        ticks[order[k % len(order)]] += 1
    return ticks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--colors", type=int, default=BAND_COLORS)
    ap.add_argument("--blur", type=float, default=0.0)
    ap.add_argument("--internal", default=None,
                    help="pre-scale to WxH then nearest-upscale to 256x224")
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
            # 15 fps out of an 8 fps source: blend adjacent source frames so
            # the extra frames carry real motion instead of hard duplicates.
            pos = i * (SOURCE_WINDOW - 1) / (FRAMES - 1)
            i0 = min(SOURCE_WINDOW - 1, int(pos))
            i1 = min(SOURCE_WINDOW - 1, i0 + 1)
            frac = pos - i0
            im0 = Image.open(src[i0]).convert("RGB").crop(SOURCE_CROP)
            im0 = im0.resize((W, H), Image.LANCZOS)
            if frac > 0.001:
                im1 = Image.open(src[i1]).convert("RGB").crop(SOURCE_CROP)
                im1 = im1.resize((W, H), Image.LANCZOS)
                im = Image.blend(im0, im1, frac)
            else:
                im = im0
            src_path = tmp / f"pre{i:03d}.png"
            im.save(src_path)
            base = tmp / f"f{i:03d}"
            build_frame(str(src_path), str(base), crop=None,
                        colors=args.colors, blur=args.blur)
            chr_data = base.with_suffix(".chr").read_bytes()
            map_data = base.with_suffix(".map").read_bytes()
            pal_data = base.with_suffix(".pal").read_bytes()
            if len(map_data) != 2048 or len(pal_data) != 128:
                raise SystemExit(f"frame {i}: unexpected map/pal size "
                                 f"{len(map_data)}/{len(pal_data)}")
            table.append((len(payload), len(chr_data)))
            payload += chr_data + map_data + pal_data
            if (i + 1) % 10 == 0 or i + 1 == FRAMES:
                print(f"  frame {i + 1}/{FRAMES}: {len(chr_data)}B chr")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ticks = balance_ticks([c for _, c in table])
    table = [(off, chr_len, ticks[i])
             for i, (off, chr_len) in enumerate(table)]

    header = b"M1VID1\0\0"
    header += struct.pack("<HHHH", W, H, FPS, 0)
    header += struct.pack("<II", FRAMES, 44300)
    for off, chr_len, ticks in table:
        header += struct.pack("<IHH", off, chr_len, ticks)
    args.out.write_bytes(header + payload)
    print(f"wrote {args.out} ({len(header) + len(payload)} bytes, "
          f"{FRAMES} frames, {sum(t for *_x, t in table)} ticks)")

    manifest_path = ROOT / "assets/video/Wmva3m93t34/manifest.json"
    try:
        args.out.relative_to(ROOT)
        inside_root = True
    except ValueError:
        inside_root = False
    if inside_root and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest["m1vid"] = {
            "file": str(args.out.relative_to(ROOT)),
            "resolution": [W, H],
            "colors": 256,
            "palette": "4 bands x 15 colors (endings pipeline)",
            "source_crop": list(SOURCE_CROP),
            "band_colors": args.colors,
            "blur": args.blur,
            "fps": FPS,
            "frame_count": FRAMES,
            "duration_seconds": 44.3,
            "ticks": sum(t for *_x, t in table),
            "nominal_ticks": TOTAL_TICKS,
            "format": "M1VID1",
            "audio": False,
            "bytes": args.out.stat().st_size,
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
