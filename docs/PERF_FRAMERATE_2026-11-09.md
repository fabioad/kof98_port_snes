# Perf/framerate work log (2026-11-09)

## Goal
Raise CPU-vs-CPU fight cadence toward 60 fps without graphical or gameplay
regressions.

## Baseline (pre-change, logical fps via framecnt in Snes9x headless)
- 0:1 ~52.1, 2:3 ~47.9, 4:5 ~49.7, 10:20 ~45.5, 30:40 ~45.5, 45:46 ~48.6,
  12:33 ~50.1, 7:9 ~54.0
- Profile hotspots: DF_cell ~15%, BO_fill ~8%, HpToPx ~8%, TA_row ~5%,
  WaitFightPresent ~5%, spcProcessStream+MRA_copy several %.
- Baseline re-check for the two pairs whose fight ends early inside the
  3600-frame window (2400 requested frames):
  - 45:46 = 48.82 fps, `rt_oamdrop` delta 3, worst zero-tick run 2.
  - 30:40 = 46.44 fps, `rt_oamdrop` delta 0, worst zero-tick run 2.

## Changes
- `src/engine/fast_paths.asm` (new, bank 64):
  - `DrawCellsFar`: fused cell emitter (single word read for dx|dy, biased
    scr1/scr2, folded hi-table bit accumulation, bulk OAMHI flush every 4
    cells + tail fixup).
  - `BOFillFar`: 16-byte unrolled OAMBUF `$F0` fill.
  - `HpToPxFar`/`PowToPxFar`: two-stage division (250/25, 3750/375) replacing
    per-25/375 loops.
  - `FillBarMemoFar` + `FillBarMemoResetFar`: per-slot memo of the rendered
    22-byte bar row (key: px, attr, tile group, HUDMAP ofs); hit = MVN copy
    instead of the 11-column loop.
  - `PerfVerifyReset` (KOF_PERF_VERIFY only).
- `src/engine/fight.asm`:
  - DF_cell -> `jsl DrawCellsFar`
  - BO_fill -> `jsl BOFillFar`
  - HpToPx/PowToPx -> far wrappers
  - FillBarM -> `jsl FillBarMemoFar` (+`FillBarNearT` jsl shim)
  - reset call sites; TransTab (`TA_row`/`TE_row`) early-exit on the sorted
    table.
- `src/snes/fight_bridge.asm`: PV_* verify RAM section + `FBM_CACHE` in bank
  `$7F`.
- `tools/probe_framerate_headless.py`: CPU-vs-CPU bout FPS probe + perf_verify
  counters dump.
- `tools/capture_bout_video.py` (new): CPU-vs-CPU MP4 capture with MSU audio.
- `tools/tests/test_transtab_sorted.py`, `tools/build_order.py` (+ generated
  order assets).

## Verify harness (KOF_PERF_VERIFY)
- Runs each optimized path beside a faithful copy of the original and compares
  outputs; counts mismatches in PV_*.
- Harness bugs found & fixed: missing `rep #$30` before the old-run (X8
  `cpx #512` bails); `lda [scr2],y` compare missed the `$7E` bank byte (FBM
  false mismatches); retry-once on diff (NMI may land mid-run: measured 162
  NMI entries inside calls/300 frames).
- Result: `fill_bar` 0, `hp_to_px` 0, `pow_to_px` 0 mismatches.
- `draw_cells`: residual constant-x anomaly in the captured "old" buffer on
  the first-mismatch call; the old routine was proven to compute real dxs on
  other calls, and a Python model of the original algorithm on the same ROM
  data reproduces the new output bit-exactly -> fast path semantics
  confirmed; residual attributed to harness/NMI-era interference, pending
  further isolation.

## Measured (production build, 3600 requested frames)
ROM `kof98-snes.sfc`, md5 `27e1ae5e64a5f72b26b340a452d59337`.

| Pair  | Baseline | New    | Delta  | Zero ticks | OAM drops |
|-------|----------|--------|--------|------------|-----------|
| 0:1   | 52.1     | 59.07  | +6.97  | 47 / 2744  | 0         |
| 2:3   | 47.9     | 57.71  | +9.81  | 109 / 2747 | 0         |
| 4:5   | 49.7     | 58.57  | +8.87  | 67 / 2636  | 0         |
| 10:20 | 45.5     | 58.56  | +13.06 | 81 / 3173  | 0         |
| 30:40 | 45.5     | 53.34* | +7.84  | 215 / 1913 | 0         |
| 45:46 | 48.6     | 56.72  | +8.12  | 135 / 2400 | 2         |
| 12:33 | 50.1     | 57.79  | +7.69  | 122 / 3171 | 0         |
| 7:9   | 54.0     | 59.38  | +5.38  | 38 / 3173  | 0         |

- `Zero ticks` = video frames where the logic counter did not advance, out of
  the fight frames observed; the histogram only ever contained 0 and 1, and
  the worst consecutive zero-tick run was **1** for every pair (baseline had
  runs of 2).
- `*30:40`: the bout ended at 1913 fight frames, so the window is shorter.
  Re-measured baseline for the same pair over 2400 requested frames = 46.44.
- `45:46` OAM drops are not new: baseline reported 3 in the same pair
  (2400-frame re-check); the optimized build reports 2.
- `rt_msufail` and `tel_spfix` stayed 0 for every pair.
- Verify build is intentionally much slower (dual-run + instrumentation); do
  not use it for fps numbers.

## Regression suite
- `python3 -m pytest tools/tests -q`
  -> **312 passed, 5504 subtests passed** (24 s).
- Passing headless checks on the optimized ROM:
  - `test_counter_banner_headless.py` — counter banner glyphs + expiry
  - `test_team_order_headless.py` — 17 checks (order, undo, CPU, stages)
  - `test_ai_headless.py` — AI level 1 sparse / level 9 full toolkit
  - `test_fight_pause_soak_headless.py --minutes 1 --stages 0` — pause soak
- Six boot/visual tests fail **identically on the pre-change ROM** (verified by
  rebuilding `HEAD` fight sources): `test_hud_bands_headless`,
  `test_super_meter_headless`, `test_round_timer_headless`,
  `test_ko_banner_headless`, `test_round_voice_headless` and
  `test_projectile_render`. They are stale w.r.t. the MSU opening video
  (gamestate 14) and the projectile attribute (now `$34`, test expects
  `$04`), not perf regressions. They should be refreshed separately.

## Video capture
- `tools/capture_bout_video.py 0:1 --seconds 30`
- Output: `work/videos/kof98_cpu_kyo-vs-iori_2026-11-09.mp4`
  (git-ignored work tree), plus a `.json` sidecar.
- 1803 frames @ 60.0988 Hz, MSU audio muxed at 32040 Hz; fight window =
  1532 frames, 1507 logic ticks -> **59.12 fps**, `rt_msufail` 0,
  `rt_oamdrop` 0.
- Additional captures (same settings):
  - `kof98_cpu_mai-vs-eiji_2026-11-09.mp4` (ids 25:42) — 1376 fight
    frames, **59.14 fps**, 0 `msufail`/`oamdrop`.
  - `kof98_cpu_duckking-vs-yuki_2026-11-09.mp4` (ids 49:50) — 1609 fight
    frames, **57.90 fps**, 0 `msufail`/`oamdrop`.
- The tool handles Snes9x's padded stride: the core reports 256x224 but pads
  each scanline to its 512-px max width (pitch 1024). Decoding must pass the
  real pitch to PIL and keep the 256-px width.

## Repro
```sh
# production build
make -f Makefile.pvsnes kof98-snes.sfc

# fps matrix
python3 tools/probe_framerate_headless.py --rom kof98-snes.sfc --frames 3600 \
  0:1 2:3 4:5 10:20 30:40 45:46 12:33 7:9

# verify build (slow; never use for fps)
make -f Makefile.pvsnes PERF_VERIFY=1 kof98-snes-verify.sfc

# python regression suite
python3 -m pytest tools/tests -q

# CPU-vs-CPU capture
python3 tools/capture_bout_video.py 0:1 --seconds 30
```

## Follow-ups
- Isolate the residual `draw_cells` verify anomaly (old-buffer first call).
- Refresh the six stale headless tests listed above (gamestate 14 / attr `$34`).
- Optional: shave the remaining 30:40 / 45:46 overhead (streamed fighter CHR
  and effect-heavy frames) to bring the worst pair above 55.
