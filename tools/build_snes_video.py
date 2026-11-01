#!/usr/bin/env python3
"""Convert a source video into SNES Mode-7 video assets.

The SNES cannot decode VP9/H.264.  This tool produces two artefacts:

  frames/            indexed PNGs, 128x112, 256 colours, 5 fps
  snes_video/*.m7vid one M7VID1 container: per-frame Mode-7 palette + pak

128x112 is the native window used by the opening intro's Mode-7 path; the
intro displays it at rest scale 0.5, i.e. 2x, filling the 256x224 screen.
The palette is stored pre-swapped R/B (flags bit0) because the existing
Mode-7 renderer swaps those channels; the PNG frames keep normal RGB.

No audio is carried into either artefact.

Usage:
  python3 tools/build_snes_video.py \
      --source assets/video/Wmva3m93t34/source/Wmva3m93t34.webm
"""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "assets/video/Wmva3m93t34"
W, H = 128, 112
COLS, ROWS = W // 8, H // 8
MAP0 = (52 << 7) | 56          # intro's Mode-7 window centre ($1A38)
FPS = 8
DURATION = 54.0                # same length as the first intro
FRAMES = int(round(DURATION * FPS))
# 60/8 = 7.5 ticks; alternate 7/8 so the total is exactly 54 s (3240 ticks).
def frame_ticks(i):
    return 7 + (i & 1)


def snes_color(c):
    r, g, b = c
    return (r * 31 // 255) | ((g * 31 // 255) << 5) | ((b * 31 // 255) << 10)


def swapped(c):
    r, g, b = c
    return snes_color((b, g, r))


def frame_to_m7(im):
    """128x112 RGB -> (indexed PNG bytes, 512B engine palette, pak bytes)."""
    q = im.convert("RGB").quantize(colors=255, method=Image.MEDIANCUT,
                                   dither=Image.NONE)
    qp = q.getpalette() or []
    ncol = len(qp) // 3
    colors = [tuple(qp[i * 3:i * 3 + 3]) for i in range(min(ncol, 255))]
    colors += [(0, 0, 0)] * (255 - len(colors))
    # Reserve index 0 for the Mode-7 black backdrop.
    lut = bytes((v + 1) & 0xFF for v in q.getdata())

    tiles = []
    seen = {bytes(64): 0}
    cells = bytearray()
    for cy in range(ROWS):
        for cx in range(COLS):
            tb = bytes(lut[(cy * 8 + y) * W + cx * 8 + x]
                       for y in range(8) for x in range(8))
            idx = seen.get(tb)
            if idx is None:
                idx = len(tiles) + 1
                seen[tb] = idx
                tiles.append(tb)
            cells.append(idx)
    if len(tiles) + 1 > 256:
        raise ValueError(f"frame needs {len(tiles) + 1} tiles (> 256)")

    # Existing .m7pak layout: header, black tile 0, unique tiles, 1-byte map.
    pak = struct.pack("<HHH", len(tiles) + 1, COLS | (ROWS << 8), MAP0)
    pak += bytes(64)
    pak += b"".join(tiles)
    pak += bytes(cells)

    pal = bytearray(struct.pack("<H", 0))          # index 0 black
    for c in colors:
        pal += struct.pack("<H", swapped(c))

    png = Image.frombytes("P", (W, H), lut)
    png.putpalette([v for c in ([(0, 0, 0)] + colors) for v in c])
    return png, bytes(pal), pak


def extract(source, tmpdir):
    tmpdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
        "-t", f"{DURATION:.3f}", "-an",
        "-vf", f"fps={FPS},scale={W}:{H}:flags=lanczos",
        "-start_number", "0", str(tmpdir / "src_%05d.png"),
    ]
    subprocess.run(cmd, check=True)
    return sorted(tmpdir.glob("src_*.png"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path,
                    default=DEFAULT_OUT / "source/Wmva3m93t34.webm")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    source = args.source.resolve()
    out = args.out.resolve()
    frames_dir = out / "frames"
    video_dir = out / "snes_video"
    tmpdir = out / "_tmp_frames"
    for d in (frames_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("frame_*.png"):
        old.unlink()

    print(f"extracting {DURATION:.0f}s at {FPS} fps ({FRAMES} frames)...")
    src_frames = extract(source, tmpdir)
    if len(src_frames) < FRAMES:
        raise SystemExit(f"only {len(src_frames)} frames extracted, "
                         f"wanted {FRAMES}")
    src_frames = src_frames[:FRAMES]

    entries = []          # (png_path, palette, pak)
    for i, path in enumerate(src_frames):
        im = Image.open(path).convert("RGB")
        png, pal, pak = frame_to_m7(im)
        png_name = frames_dir / f"frame_{i:05d}.png"
        png.save(png_name, optimize=True)
        entries.append((pal, pak))
        if (i + 1) % 25 == 0 or i + 1 == FRAMES:
            print(f"  converted {i + 1}/{FRAMES}")

    # M7VID1 container: header, 6-byte frame table, then palette+pak frames.
    header_len = 24
    table_len = FRAMES * 6
    data_start = header_len + table_len
    offsets = []
    pos = 0
    for pal, pak in entries:
        offsets.append(pos)
        pos += len(pal) + len(pak)

    out_path = video_dir / "Wmva3m93t34.m7vid"
    with open(out_path, "wb") as f:
        f.write(b"M7VID1\0\0")                     # 8 bytes
        f.write(struct.pack("<HHHH", W, H, FPS, 1))  # flags bit0 = R/B swapped
        f.write(struct.pack("<II", FRAMES,
                            int(round(DURATION * 1000))))
        for i, off in enumerate(offsets):
            f.write(struct.pack("<IH", off, frame_ticks(i)))
        for pal, pak in entries:
            f.write(pal)
            f.write(pak)

    def rel(p):
        try:
            return str(p.relative_to(ROOT))
        except ValueError:
            return str(p)

    manifest = {
        "source": rel(source),
        "source_url": "https://www.youtube.com/watch?v=Wmva3m93t34",
        "duration_seconds": DURATION,
        "fps": FPS,
        "resolution": [W, H],
        "display_resolution": "256x224 (Mode-7 rest scale 0.5 / 2x)",
        "colors": 256,
        "format": "SNES Mode-7 8bpp; intro .m7pak-compatible",
        "audio": False,
        "frame_count": FRAMES,
        "frame_ticks": "7/8 alternating",
        "duration_ticks": FRAMES * 15 // 2,
        "container": "M7VID1",
        "frames_dir": rel(frames_dir),
        "video": rel(out_path),
        "video_bytes": out_path.stat().st_size,
        "video_sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"frames: {frames_dir} ({FRAMES} PNGs, {W}x{H}, 256 colors)")
    print(f"video : {out_path} ({out_path.stat().st_size} bytes)")
    print(f"manifest: {out / 'manifest.json'}")


if __name__ == "__main__":
    main()
