# Default (PRO), MID, HI10 and OLD builds

The default `kof98-snes.sfc` / `kof98-snes.msu` now uses the **PRO** profile:
near-full 1.0 art with a few per-character caps (Chang 0.80, Sakura 0.95,
Billy 0.85, Rugal 0.94, Chun-Li 0.99 and Omega Rugal 0.94).  The previous
default, tuned HI at a **0.88 base**, is still available as the **MID**
profile (`kof98-snes-mid.sfc` / `kof98-snes-mid.msu`).  The 0.81 layout
remains the OLD profile (`kof98-snes-old.sfc` / `kof98-snes-old.msu`).

A literal 1.0 base can be built with the MID profile using
`HI_BASE_SCALE=1.0` for comparison, but it costs more CHR/DMA traffic and
produces more sprite-packing loss on the largest poses.

## Commands

```sh
make -f Makefile.pvsnes            # default: kof98-snes.sfc/.msu (PRO scale)
make -f Makefile.pvsnes verify     # checksum + verification

make -f Makefile.pvsnes MID=1      # kof98-snes-mid.sfc/.msu (HI 0.88)
make -f Makefile.pvsnes MID=1 verify
make -f Makefile.mid               # same as MID=1
make -f Makefile.pvsnes mid        # build the MID variant
make -f Makefile.pvsnes mid-clean  # remove only the MID outputs

make -f Makefile.pvsnes HI10=1     # kof98-snes-hi.sfc/.msu (1.0 test)
make -f Makefile.hi                # same as HI10=1
make -f Makefile.pvsnes hi         # same as HI10=1
make -f Makefile.pvsnes hi-clean   # remove only the 1.0 test outputs

make -f Makefile.pvsnes OLD=1      # kof98-snes-old.sfc/.msu (0.81)
make -f Makefile.pvsnes OLD=1 verify
make -f Makefile.old               # same as OLD=1

make -f Makefile.pvsnes old        # build the 0.81 variant
make -f Makefile.pvsnes old-clean  # remove only the OLD outputs
```

From the repository root: `make pvsnes` (default PRO), `make pvsnes-mid`
(previous 0.88 default), `make pvsnes-hi` (1.0 test) and `make pvsnes-old`
(0.81), plus their `-verify` variants.

The MID profile supports `HI_BASE_SCALE`:

```sh
make -f Makefile.pvsnes MID=1 HI_BASE_SCALE=0.95
```
The dedicated 1.0 test profile is `HI10=1` / `make -f Makefile.hi`.

## Profiles and isolated artifacts

| | default (PRO) | MID=1 (HI 0.88) | HI10=1 (1.0 test) | OLD=1 (0.81) |
|---|---|---|---|---|
| ROM | `kof98-snes.sfc` | `kof98-snes-mid.sfc` | `kof98-snes-hi.sfc` | `kof98-snes-old.sfc` |
| MSU-1 | `kof98-snes.msu` | `kof98-snes-mid.msu` | `kof98-snes-hi.msu` | `kof98-snes-old.msu` |
| generated data | `build/gen_fight/` | `build/mid/gen_fight/` | `build/hi10/gen_fight/` | `build/old/gen_fight/` |
| fight object | `src/snes/fight_bridge.obj` | `build/mid/fight_bridge.obj` | `build/hi10/fight_bridge.obj` | `build/old/fight_bridge.obj` |
| linker input | `linkfile` | `build/mid/linkfile` | `build/hi10/linkfile` | `build/old/linkfile` |
| include root | `build/` | `build/mid/` | `build/hi10/` | `build/old/` |

The MID, HI10 and OLD builds never overwrite the PRO default ROM/MSU or
`build/gen_fight`.  The video manifest
(`assets/video/Wmva3m93t34/manifest.json`) is updated by the default PRO
build.  The other profiles write their own copy under their generated tree.

## Calibration

The PRO and MID profiles do **not** edit any character `char_scale` field in
the configuration or in `assets/calibration/*.json`.  `KOF_CHAR_SCALE` and
`KOF_SCALE_CAPS` are builder-level overrides applied only while scaling
fighter sprites and collision boxes; the config hash and all 19 verified
profiles stay valid.

The larger cell grids no longer fit the legacy 0.81 table windows, so the HI
generator splits every fighter's `SprData` blob into a packed `_meta.inc` bank
(the descriptor's `CH_MBANK` resolves automatically) and places the victory
quote strings after the compact tables.

The larger metas also need more ROM than the 0.81 layout.  To keep the 8 MiB
image viable, the HI-family profiles stream Iori, Kyo, Shingo, Omega Rugal and
Benimaru from the .msu file as well (Terry stays in ROM because his poses
stream slowly, and moves to the banks Omega vacated).  The cast is unchanged;
only the CHR storage split differs from the OLD profile.

## 1.0 test profile (HI10)

`HI10=1` (or `make -f Makefile.hi`) builds the full 1.0 art for hardware
comparison.  It is deliberately **not** the PRO default: it keeps every
fighter at 1.0 except Billy (0.88 structural cap, because his 1.0 metasprite
blob exceeds the engine's 64 KiB `CH_MBANK`).  The OAM/DMA truncation
fallbacks stay enabled, so the build completes even on the oversized poses;
expect more visible packing loss and slowdown than the PRO/MID builds.

The 1.0 profile includes the hardware MSU-CHR upload/HUD fixes from
`ec0690e` (vblank staging, one MSU seek per frame, `DMACHUNK=1536`).

Artifacts: `kof98-snes-hi.sfc` + `kof98-snes-hi.msu`, in
`build/hi10/gen_fight/`.  The PRO/MID trees and manifest are not touched.

### Streaming / HUD fixes in the 1.0 profile

- Projectile/FX pages upload the full 2 KiB page.  The earlier "used tiles
  only" experiment left stale tiles behind and caused shuffled tiles/palettes,
  so it was reverted.
- Both fighter CHR chunks are uploaded every frame, as in the original
  uploader.  Alternating sides or deferring a side on FX frames kept a pose
  in flight long enough for the next animation request to arrive; the staging
  state then mixed with the new pose and produced more mixed/invisible tiles.
  The full 2 KiB FX page is still uploaded on its own.
- While the 2 KiB HUD repaint is deferred by fighter streaming, the engine
  refreshes the small CHALLENGER/name band (row 1) separately, removing the
  lifebar-label flicker.
- `StagePick` now aborts any in-flight DMA and clears the FX staging state
  before reloading a stage; this removes the first-round stage corruption that
  disappeared on the next round.
- The 1.0 test profile caps Billy and Sakura 0.90 (structural), Chang 0.78,
  Robert/Ralf/Clark/Ryo/Joe 0.92, Saisyu 0.93, Shingo/Kyo/Rugal/Omega Rugal
  0.95, Benimaru 0.94 and Iori 0.93.  All female fighters use 0.94 except
  Sakura (0.90).  The remaining fighters stay 1.0.

The PRO and MID artifacts are not rebuilt by this profile.  The heaviest
MSU-vs-MSU pairs are still the first candidates for real-hardware pacing
checks.

## Default profile (PRO)

The default build (plain `make`, `make -f Makefile.pvsnes` or
`make pvsnes`) uses the PRO scale.  Every fighter uses the full 1.0 art
except:

| Character | Scale |
|---|---|
| Chang | 0.80 |
| Sakura | 0.95 |
| Billy | 0.85 |
| Rugal | 0.94 |
| Chun-Li | 0.99 |
| Omega Rugal | 0.94 |

Artifacts: `kof98-snes.sfc` + `kof98-snes.msu`, generated in
`build/gen_fight/` with `src/snes/fight_bridge.obj` and `linkfile`.  The MID,
HI10 and OLD trees are not touched.

The scale caps are builder-level overrides (`KOF_SCALE_CAPS=pro`); no
character cfg or `assets/calibration/*.json` value changes, so the calibration
hashes stay valid.  The OAM/DMA truncation fallbacks stay enabled, as in HI10.

Billy at 0.85 uses 53,062 bytes of `SprData` and keeps every staged
throw-victim held pose.  His hard ceiling is 0.88 (63,054 bytes): 0.89 grows
to 65,683 bytes, already past the engine's 64 KiB `CH_MBANK` window, and
0.90–0.95 reach 70–80 KiB.

Rugal uses 0.94 by request to match Omega Rugal; at 1.0 his blob would fit
(47,652 bytes), so this one is a design choice rather than a structural cap.

Chun-Li and Omega Rugal cannot reach 1.0: their blobs would be 70,851 and
72,325 bytes.  0.99 (65,466 bytes) and 0.94 (65,142 bytes) are the largest
values that fit, and Omega Rugal at 0.94 still keeps most held poses.  Sakura
at 0.95 (26,133 bytes) and Chang at 0.80 (64,844 bytes) keep their held poses.

## Per-character caps (MID)

MID uses the **0.88 base** plus one structural cap: Chang at **0.86**
(65,560 bytes at 0.87 and 65,816 at 0.88; 0.86 is the largest verified value
that fits the 64 KiB `CH_MBANK`).  Every other fighter stays at 0.88.

The optional `KOF_SCALE_CAPS=full` aesthetic map (not used by the shipped
MID or PRO profiles) is:

| Character | Scale |
|---|---|
| Billy | 0.88 |
| Chang | 0.82 |
| Omega Rugal | 0.92 |
| Rugal | 0.93 |
| Mr. Big | 0.92 |
| Brian | 0.92 |
| Terry | 0.92 |
| Daimon | 0.93 |
| Yashiro | 0.93 |
| Yamazaki | 0.93 |
| Krauser | 0.93 |
| Geese | 0.93 |

Rugal and Omega Rugal keep the full 3072-byte DMA window in HI (the OLD build
uses 2560), which removes the dropped-cell artifacts on their largest poses.

## Current artifact

The default PRO build:

- `kof98-snes.sfc`: 8 MiB image with ~2.9 MB free.
- `kof98-snes.msu`: ~56 MB.
- Chun-Li 0.99 and Omega Rugal 0.94 are the only structural caps needed by
  the 64 KiB `CH_MBANK` window; the other PRO caps are deliberate.
- No `dma_cap_cell`, `oam_cell_truncate` or `sprite_bbox_crop` events remain.
- ROM-resident CHR descriptors carry the high-half offset (`$8000`) for
  HI's bank layout; this fixes Terry's tiles (the table bank stays the same).
- HI meta sections carry a 16-byte pad before `SprData`, so the first
  sprite's `F_META` offset is never zero (zero is the engine's "no sprite"
  sentinel).  This fixes Terry's missing first idle frame.

The MID build (`kof98-snes-mid.sfc` / `.msu`) keeps the previous 0.88
artifact: 8 MiB ROM with ~4 MB free and a ~48 MB MSU file.

## Known runtime risks

- OAM/64-cell budget: the packed page still holds at most 64 cells and 96
  tiles.  Extremely large poses lose a few low-coverage cells; the loss is
  recorded in `build/gen_fight/art_loss.json` (`quadrant`).
- VRAM/DMA: the MID 0.88 profile is within a few percent of the 0.81 build's
  CHR/DMA load; the PRO 1.0 base is heavier.
- Gameplay: scale changes sprite placement and hit boxes, not velocities or
  timing.  Reach and hit feel differ from the OLD build; this is a
  demonstration profile, not a competitive ruleset.
- MSU-1: the default data file is larger and streams 52 fighters; test on
  SD2SNES/FXPak and real hardware, not only in an emulator.

## Backup / rollback

Before the HI split was added, the current artifacts and configuration were
saved in `backup/pre-hi-20261103/` (ROM, MSU, symbols, generated fight data,
source archive and the modified Makefiles).  The commit is recorded in
`backup/pre-hi-20261103/HEAD.txt`.
