#!/usr/bin/env python3
"""Headless regression for the secret Mr. Karate flash card.

The card is an occasional (1 in 4) transition from the attract demo to the
opening intro, and it must only exist when the .msu file is available.  This
test forces the RNG gate and the demo deadline, then checks:

* with MSU-1: gamestate 17 appears and hands off to the opening intro;
* without MSU-1: the card never appears, even with the RNG forced.
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core                              # noqa: E402
from test_attract_demo_headless import reach_title, start_demo     # noqa: E402

GS = 0x1020
DM_TICK = 0xF068
DM_ON = 0xF06A
RNG = 0x1088
THUNDER = 17


def force_card(core):
    core.put(DM_TICK, 1)
    core.ram[RNG] = 3                 # MainLoop increments rng before the gate
    seen = set()
    for _ in range(420):
        gs = core.word(GS)
        seen.add(gs)
        if gs in (7, 14):
            break
        core.step()
    return seen


def with_msu(core_path, rom):
    core = Core(core_path, str(rom))
    try:
        reach_title(core)
        start_demo(core)
        seen = force_card(core)
        assert THUNDER in seen, f"card never appeared: states={sorted(seen)}"
        assert core.word(GS) in (7, 14), \
            f"card did not hand off to the intro: gs={core.word(GS)}"
        assert core.ram[DM_ON] == 0, "demo flag not cleared by the card"
    finally:
        core.close()


def without_msu(core_path, rom):
    with tempfile.TemporaryDirectory(prefix="kof98-thunder-") as tmp:
        bare = Path(tmp) / rom.name
        shutil.copyfile(rom, bare)
        core = Core(core_path, str(bare))
        try:
            reach_title(core)
            start_demo(core)
            seen = force_card(core)
            assert THUNDER not in seen, "card appeared without the .msu file"
            assert core.word(GS) in (7, 14), \
                f"demo did not cut straight to the intro: gs={core.word(GS)}"
        finally:
            core.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core",
                        default="/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    rom = args.rom.resolve()
    if not rom.exists():
        parser.error(f"ROM not found: {rom}")

    print("case: MSU available", flush=True)
    with_msu(args.core, rom)
    print("PASS thunder card with MSU", flush=True)
    print("case: MSU absent", flush=True)
    without_msu(args.core, rom)
    print("PASS thunder card stays off without MSU", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
