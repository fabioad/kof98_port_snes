#!/usr/bin/env python3
"""Measure FightTick cadence in single VS CPU-vs-CPU bouts via Snes9x."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from test_ai_headless import (
    AI_LEVEL, CPU1, CPU2, GS, LOCK1, LOCK2, M_ITEM, MSUOK, SEL1, SEL2,
    tap, wait,
)

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
ABI = json.loads((ROOT / "assets" / "runtime_abi.json").read_text())
FRAMECNT = 0x1024
RT_MSUFAIL = 0x5102
RT_OAMDROP = 0x5106
PV_BASE = 0x16100
PV_FIRST_OLD_OAM = 0x4CE
PV_FIRST_NEW_OAM = 0x6EE
PV_COUNTERS = {
    "draw_cells": 0x04,
    "draw_cells_mismatches": 0x08,
    "hp_to_px": 0x0C,
    "hp_to_px_mismatches": 0x10,
    "pow_to_px": 0x14,
    "pow_to_px_mismatches": 0x18,
    "fill_bar": 0x1C,
    "fill_bar_mismatches": 0x20,
}
PV_TYPES = {1: "draw_cells", 2: "hp_to_px", 3: "pow_to_px", 4: "fill_bar"}


def word(core, address):
    return core.ram[address] | core.ram[address + 1] << 8


def counter_snapshot(core):
    addresses = {
        "tel_spfix": ABI["TEL_SPFIX"],
        "rt_oamdrop": RT_OAMDROP,
        "rt_msufail": RT_MSUFAIL,
    }
    return {name: word(core, address) for name, address in addresses.items()}


def counter_delta(before, after):
    return {name: (after[name] - value) & 0xFFFF
            for name, value in before.items()}


def perf_verify_snapshot(core):
    if bytes(core.ram[PV_BASE:PV_BASE + 4]) != b"PV01":
        return None
    counts = {
        name: int.from_bytes(core.ram[PV_BASE + offset:PV_BASE + offset + 4],
                             "little")
        for name, offset in PV_COUNTERS.items()
    }
    first = None
    if core.ram[PV_BASE + 0x24]:
        offset = word(core, PV_BASE + 0x26)
        first = {
            "type": PV_TYPES.get(core.ram[PV_BASE + 0x25], "unknown"),
            "offset": offset,
            "expected": word(core, PV_BASE + 0x28),
            "actual": word(core, PV_BASE + 0x2A),
            "context": bytes(core.ram[PV_BASE + 0x2C:PV_BASE + 0x4C]).hex(),
        }
        if core.ram[PV_BASE + 0x25] == 1 and offset < 544:
            first["oam_expected"] = bytes(
                core.ram[PV_BASE + PV_FIRST_OLD_OAM + offset:
                         PV_BASE + PV_FIRST_OLD_OAM + offset + 4]).hex()
            first["oam_actual"] = bytes(
                core.ram[PV_BASE + PV_FIRST_NEW_OAM + offset:
                         PV_BASE + PV_FIRST_NEW_OAM + offset + 4]).hex()
    return {"counts": counts, "first_mismatch": first}


def bout(rom, p1, p2, frames, level=8, core_path=CORE):
    core = Core(core_path, rom)
    try:
        for _ in range(80):
            if core.ram[GS] == 6:
                break
            tap(core, 3)
        wait(core, lambda: core.ram[GS] == 6, "mode menu")
        core.ram[MSUOK] = 1
        core.ram[M_ITEM] = 1
        tap(core, 3)
        wait(core, lambda: core.ram[GS] == 5, "versus select")
        core.ram[SEL1] = p1
        core.ram[SEL2] = p2
        core.ram[LOCK1] = 1
        core.ram[LOCK2] = 1
        core.ram[CPU1] = 1
        core.ram[CPU2] = 1
        core.ram[AI_LEVEL] = level
        wait(core, lambda: core.ram[GS] in (1, 4), "fight load")
        if core.ram[GS] == 4:
            tap(core, 3)
        wait(core, lambda: core.ram[GS] == 1, "fight")
        core.step(120)

        before = counter_snapshot(core)
        before_frame = core.ram[FRAMECNT]
        histogram = {}
        fight_video_frames = 0
        ticks = 0
        zero_run = 0
        worst_zero_run = 0
        for _ in range(frames):
            core.step()
            now = core.ram[FRAMECNT]
            delta = (now - before_frame) & 0xFF
            before_frame = now
            if core.ram[GS] != 1:
                zero_run = 0
                continue
            fight_video_frames += 1
            ticks += delta
            histogram[delta] = histogram.get(delta, 0) + 1
            zero_run = zero_run + 1 if delta == 0 else 0
            worst_zero_run = max(worst_zero_run, zero_run)

        after = counter_snapshot(core)
        result = {
            "p1": p1,
            "p2": p2,
            "level": level,
            "requested_video_frames": frames,
            "fight_video_frames": fight_video_frames,
            "ticks": ticks,
            "fps": round(60.0988 * ticks / max(1, fight_video_frames), 4),
            "histogram": dict(sorted(histogram.items())),
            "worst_zero_tick_run": worst_zero_run,
            "gs_final": core.ram[GS],
            "counters": {
                "before": before,
                "after": after,
                "delta": counter_delta(before, after),
            },
        }
        verify = perf_verify_snapshot(core)
        if verify is not None:
            result["perf_verify"] = verify
        return result
    finally:
        core.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    parser.add_argument("--core", type=Path, default=CORE)
    parser.add_argument("--frames", type=int, default=3600)
    parser.add_argument("--min-fps", type=float)
    parser.add_argument("pairs", nargs="*", default=["0:1"])
    args = parser.parse_args()

    failed = False
    for pair in args.pairs:
        try:
            p1, p2 = map(int, pair.split(":"))
            result = bout(args.rom, p1, p2, args.frames, core_path=args.core)
            if args.min_fps is not None and result["fps"] < args.min_fps:
                failed = True
                result["below_min_fps"] = args.min_fps
        except Exception as error:
            failed = True
            try:
                p1, p2 = map(int, pair.split(":"))
            except ValueError:
                p1, p2 = None, None
            result = {"p1": p1, "p2": p2, "error": str(error)}
        print(json.dumps(result, sort_keys=True), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
