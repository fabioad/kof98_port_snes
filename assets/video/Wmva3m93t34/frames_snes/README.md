# frames_snes — per-frame SNES Mode-7 assets

Converted from `../frames` (432 indexed PNGs) with
`tools/export_snes_frames.py`.

Each source frame `frame_XXXXX.png` becomes a pair:

- `frame_XXXXX.m7pak` — Mode-7 tile/map payload
- `frame_XXXXX.m7pal` — 256-colour CGRAM palette (512 bytes)

## Format

`*.m7pak`

```
u16 ntiles          number of tiles including tile 0
u16 cols | rows<<8  16 | 14<<8 = 3600
u16 map0            $1A38 (intro Mode-7 window centre)
tile 0              64 bytes, solid black
tiles 1..ntiles-1   64 bytes each, 8x8 8bpp
cells               cols*rows = 224 bytes, one tile index each
```

`*.m7pal` is 256 BGR555 words (little-endian).  The colours are stored
**R/B-swapped** because the existing Mode-7 renderer swaps those channels;
this is the same convention as the intro's `.m7pal` files.

## Video properties

- **432 frames**
- **128×112** texels, displayed at rest scale `0.5` (2×) → **256×224**
- **256 colours per frame**
- **8 fps**, using alternating **7/8 ticks** (54 s at 60 Hz)
- **No audio**

The pair is directly consumable by the intro's `InLM7` loader: point the pak
and palette pointers at a frame, upload under forced blank, and advance the
frame every 7 or 8 vblanks.

Regenerate:

```sh
python3 tools/export_snes_frames.py
```
