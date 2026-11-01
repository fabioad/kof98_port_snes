# KOF '98 opening — SNES video assets

Source: <https://www.youtube.com/watch?v=Wmva3m93t34>  
Downloaded file: `source/Wmva3m93t34.webm` (1280×720, 60 fps VP9, 55.5 s; audio discarded).

Two video builds are kept in this directory:

| file | format | use |
| --- | --- | --- |
| `snes_video/Wmva3m93t34.m1vid` | 256×224, 4 bpp, 3 fps, 44.3 s | **new opening played by the ROM when MSU-1 is present** |
| `snes_video/Wmva3m93t34.m7vid` | 128×112, 8 bpp, 8 fps, 54 s | earlier Mode-7 reference asset (not embedded) |

The M1VID build uses the same palette pipeline as the endings: four
15-colour bands, 256×224, 4 bpp. The game's runtime file is the normal
`kof98-snes.msu`, so the SD card only needs `kof98-snes.sfc` +
`kof98-snes.msu`; there is no second runtime file.

## Runtime: M1VID1 embedded in `kof98-snes.msu`

The M1VID1 payload is appended to the game data file at offset
**`0x1BB0000`** (slice 886, 32 KiB aligned). Bytes 8-9 of the 32 KiB MSU
header keep the streamed-fighter layout CRC (`$3CDC`); bytes 10-13 carry the
video byte offset and 14-17 its length. The engine constants are generated in
`build/gen_fight/msu1_bases.inc`:

```
MSU_VIDEO_OFFSET   = $1BB0000
MSU_VIDEO_OFF0..3  = $00,$00,$BB,$01   ; 32-bit MSU seek bytes
MSU_VIDEO_SIZE     = 1497568
MSU_VIDEO_FRAMES   = 133
MSU_VIDEO_FPS      = 3
MSU_VIDEO_DATA     = 1088               ; 24 + 133*8, first frame payload
MSU_VIDEO_BASE_LO  = $0440
MSU_VIDEO_BASE_HI  = $01BB
MSU_VIDEO_TABLE_LO = $0018
MSU_VIDEO_TABLE_HI = $01BB
```

Audio stays out of the video: the opening plays the game's Cipher theme.

## M1VID1 container

```
offset  size  contents
0       8     "M1VID1\0\0"
8       2     width  (u16 LE) = 256
10      2     height (u16 LE) = 224
12      2     fps    (u16 LE) = 3
14      2     flags  (u16 LE) = 0
16      4     frame_count (u32 LE) = 133
20      4     duration_ms (u32 LE) = 44300
24      8×N   frame table: u32 data offset, u16 chr_len, u16 ticks
...           N × (CHR bytes + 2048-byte map + 128-byte palette)
```

Each frame is the output of `tools/build_endings.build_frame`: the CHR is a
set of 8×8 4 bpp tiles, the map is a 32×32 word array with the band in bits
10-12, and the palette is four 15-colour bands (colors 0-63). The data offsets
are relative to the first frame's payload.

The nominal ticks sum to **2658** (44.3 s at 60 Hz). The generator subtracts
the measured per-frame MSU staging cost (about one vblank per 12 KiB of CHR),
so the wall-clock sequence also lasts **44.3 s**; the compensated table sums
to 2557 ticks. `tools/build_intro_m1vid.py` records both values in
`manifest.json`.

## Engine path

`src/engine/msu_intro.asm` (bank 126, CPU `$3E:D300`) implements gamestate
**14**:

- `OpnEnter` branches there only when `msuok != 0` and an M1VID1 is embedded.
- `MsuIntroEnterFar` reads the 133-entry table once, sets Mode 1 / BG2-only
  (map `$1800`, 4 bpp tiles `$2000`) and loads frame 0.
- `MsuIntroTickFar` re-asserts the PPU registers every frame, advances the
  current frame's ticks, and loads the next frame under forced blank.
- START skips to the title; after the last frame the player jumps to
  `TitleEnter`.
- Without MSU-1 (`msuok == 0`) the original 16-screen ROM intro still runs
  from `InLoad`/`OpnTick` (gamestate 7).

MSU traffic is sector-aligned and double-DMA'd: `$2001 -> MsuStageBuf`, then
`MsuStageBuf + prefix -> $2118/$2119`. This is the same path the CHR streamer
validated on the SD2SNES; reading the data port at an arbitrary in-sector
offset can make its cache serve stale sectors.

## `frames/`

- 432 indexed PNGs, `frame_00000.png` … `frame_00431.png`.
- **128×112**, **256 colors** (Pillow `P` mode).
- 8 fps sampled from the 54 s cut; used by the Mode-7 `.m7vid`.

## Regenerate

```sh
# full-screen 44.3 s M1VID1 (the one embedded in the game)
python3 tools/build_intro_m1vid.py

# Mode-7 reference asset and per-frame PNGs
python3 tools/build_snes_video.py \
  --source assets/video/Wmva3m93t34/source/Wmva3m93t34.webm
python3 tools/export_snes_frames.py

# embed the M1VID1 in kof98-snes.msu and emit the engine constants
python3 tools/build_fight.py
```

`tools/build_fight.py` embeds `Wmva3m93t34.m1vid` automatically at the end of a
full `make assets` run. `tools/embed_msu_video.py` is the standalone embedder
and is idempotent: re-running it replaces the embedded copy instead of
appending a duplicate.
