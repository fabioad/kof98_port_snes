# Calibration And Release Checks

The canonical entry point is `tools/calibrate_batch.py`. It includes the
ROM fighters and the MSU fighters; `--all` also includes hidden Omega Rugal.
Source packages without a native roster entry are not silently imported.

## Reproduce

```sh
make pvsnes
python3 tools/calibrate_batch.py --all --apply --output build/calibration/release-candidate
python3 tools/test_menu_modes.py --repeat 2 --output build/calibration/release-candidate/menu-modes.json
python3 tools/test_roster.py --launch --animation-smoke --json-output build/calibration/release-candidate/roster-runtime.json
python3 tools/test_projectile_render.py
python3 -m unittest discover -s tools/tests -v
PYTHONPATH=tools python3 -m calibration.snapshot build/calibration/release-candidate
```

Run emulator commands sequentially: they share the RetroArch UDP command
and input ports. Leave any interactive emulator owned by the player alone.
The projectile renderer test uses an instrumented temporary ROM; menu and
roster tests use the actual game ROM. Neither substitutes for hardware tests.

## What Is Calibrated

- Canonical MUGEN definitions are resolved to roster entries, including
  packages whose filenames differ from the roster key.
- Only unambiguous source-backed scalar HitDef changes and supported AIR
  timing corrections are applied by the existing conservative comparator.
- Profiles retain configuration and input hashes. Stale profiles fail closed.
- The staged generator rebuilds the complete character, projectile, voice
  and MSU-offset bundle. Skipped fighters reject publication.
- ROM assembly, checksum verification and calibration regressions complete
  before the transaction publishes the generated bundle and matching ROM/MSU.
- MSU remains the storage path for imported fighters, including Yuri.
  Terry retains the existing explicit ROM exception.

The journal in `build/calibration/run-*/transaction` preserves the proposal,
previous content and hashes. A batch can successfully apply safe corrections
but still exit with `needs_repair` because unresolved catalog errors remain.
Do not treat this exit as proof that the calibration transaction failed.

## Reading The Inventory

Each character has `catalog.json` and `animations.md`. The JSON includes
every animation slot, native state, resolved AIR action, command definitions,
source sprite references, source durations, emitted animation records,
combat fields and projectile configuration.

Counts refer to native slots, not distinct named Arcade moves. Follow-ups,
weak/strong variants, victim states and shared animations can occupy separate
slots. An entry in the catalog does not prove that every conditional command
or helper chain is executable in the port.

AIR elements, unique source images and emitted ROM elements are different
measurements. A 255-tick record is treated as a hold, not a measured recovery
duration. Collision-box elements alone do not establish startup, active,
recovery, cancel windows or practical anti-air performance.

Cold-upload lower bounds describe the existing byte budgets, not observed
frame rates. A repeated sprite can reuse an upload; seeks, two fighters and
voices can add cost. Do not stretch all move timings to these bounds: that
would hide the streaming problem by slowing gameplay.

## Release Blockers

The final catalog and runtime JSON are evidence, not a release certificate.
Require all of the following before tagging a release:

- No unresolved sprite references on reachable moves, or explicit reviewed
  documentation of intentional transparent elements.
- No playable slot accidentally mapped to helper/effect-only artwork.
- Faithful AIR data for packages currently reconstructed from SFF groups;
  synthetic timings and full-sprite boxes are approximations.
- Actual displayed sprite progression, not just changing state/frame counters.
- Each normal, command special, super and follow-up exercised in combat,
  including resource checks, cancel paths and weak/strong variants.
- Projectile artwork, launch timing, trajectory, contact, guard, damage,
  expiration, simultaneous effects and stationary attacks checked in game.
- Single/team campaign, team swaps, versus, winner, endings and return paths
  verified without frame-counter stalls.
- Audio gaps and missing SND references resolved or explicitly accepted.
- Long sessions and physical SNES-compatible hardware validation.

The current automatic roster smoke covers selection, fight entry, idle
counter/display progression and return to select. It does not validate every
special or super. The renderer harness verifies specific OAM/VRAM/contact
cases, not all moves of every fighter.
