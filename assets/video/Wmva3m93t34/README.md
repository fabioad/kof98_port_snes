# KOF '98 opening — SNES video assets

Source: <https://www.youtube.com/watch?v=Wmva3m93t34>  
Downloaded file: `source/Wmva3m93t34.webm` (1280×720, 60 fps VP9, 55.5 s; audio discarded).

Two versions are provided:

## 1. `snes_video/Wmva3m93t34.m7vid`

A single **M7VID1** container ready for a SNES Mode-7 sequence player.

- **Resolution:** 128×112 texels. The intro's Mode-7 path displays the window at
  rest scale `0.5`, so it fills the **256×224** screen (2×).
- **Colors:** 256 per frame (8 bpp); the palette is stored pre-swapped R/B
  (`flags` bit 0) because the existing Mode-7 renderer swaps those channels.
- **Frame rate:** 8 fps, using a 7/8-tick cadence (7.5 ticks average at 60 Hz),
  so the duration is exactly **54 s**.
- **Frames:** 432.
- **Audio:** none.
- **Size:** about 3.3 MiB.

Format:

```
offset  size  contents
0       8     "M7VID1\0\0"
8       2     width  (u16 LE) = 128
10      2     height (u16 LE) = 112
12      2     fps    (u16 LE) = 8
14      2     flags  (u16 LE) bit0 = palette R/B swapped
16      4     frame_count (u32 LE)
20      4     duration_ms (u32 LE)
24      6×N   frame table: u32 data offset, u16 ticks (7 or 8)
...           N × (512-byte palette + Mode-7 pak)
```

The pak payload is the same layout used by `tools/build_intro.py` and the
intro's `InLM7` loader: `u16 ntiles, u16 cols|rows<<8, u16 map0`, then tile 0
(black), `ntiles-1` 8×8 8bpp tiles, then the `cols*rows` 1-byte cell map.
The data offsets are relative to the start of the frame-data area.

## 2. `frames/`

- 432 indexed PNGs, numbered `frame_00000.png` … `frame_00431.png`.
- **128×112**, **256 colors** (Pillow `P` mode with a 256-entry palette).
- 8 fps sampled from the 54 s cut; played at 2× to fill 256×224.
- No audio.

These are the exact frames used to build the `.m7vid`, and can also be fed to
`tools/build_intro.py`-style converters or edited/re-encoded.

## Recommended SNES FMV spec

A full 256×224 4 bpp video is too large for the MSU-1 stream at a useful frame
rate. The recommended compromise, used here, is the intro's Mode-7 window:

- **128×112 source, displayed 2× at 256×224**
- **256 colors per frame** (Mode-7 8 bpp)
- **8 fps** (7/8-tick cadence at 60 Hz)
- **No audio**

This keeps the raw stream around 63 KiB/s (the MSU path can move 1280 bytes per
vblank, ~76.8 KiB/s), leaving headroom.

## Regenerate

```sh
python3 tools/build_snes_video.py \
  --source assets/video/Wmva3m93t34/source/Wmva3m93t34.webm
```

The current intro player still runs the hand-built 16-screen presentation. The
`frames/` PNGs are `.m7pak`-compatible, and the `.m7vid` container is ready for
a sequence player; wiring that player into `InLM7` is a separate engine step.
