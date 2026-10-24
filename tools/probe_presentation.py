#!/usr/bin/env python3
"""Headless presentation telemetry for the fight engine.

Boots VERSUS (P1 human, P2 idle), resets the engine telemetry block and runs
idle/walk/jump/attack, then reports upload pressure, pose age, dropped poses
and HUD DMA.  Reads only real hardware state through the Snes9x libretro core.

Usage: probe_presentation.py [--core libretro.so] [--rom kof98-snes.sfc]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from runtime_abi import ABI

START, DOWN, RIGHT, UP, A, B = 3, 5, 7, 4, 8, 0
GS, FRAME = 0x1020, 0x1024
FP1 = 0x4000


def tap(core, button, port=0):
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(8)


def wait(core, pred, label, limit=2400):
    for _ in range(limit):
        if pred():
            return
        core.step()
    raise AssertionError(
        f"{label}: gs={core.word(GS)} frame={core.word(FRAME)}")


def u32(core, addr):
    return (core.ram[addr] | core.ram[addr + 1] << 8
            | core.ram[addr + 2] << 16 | core.ram[addr + 3] << 24)


def run(core, frames, attacks=False):
    wait(core, lambda: core.word(GS) == 7, "opening")
    tap(core, START)
    wait(core, lambda: core.word(GS) == 0, "title")
    core.step(4)
    tap(core, START)
    wait(core, lambda: core.word(GS) == 6, "mode menu")
    tap(core, DOWN)                    # VERSUS
    tap(core, START)
    wait(core, lambda: core.word(GS) == 5, "select")
    core.step(10)
    for _ in range(12):
        tap(core, A)
        if core.ram[0x108E]:
            break
    for _ in range(12):
        tap(core, A, port=1)
        if core.ram[0x108F]:
            break
    assert core.ram[0x108E] and core.ram[0x108F], "select lock failed"
    wait(core, lambda: core.word(GS) == 1 and core.word(FP1 + 8) == 0,
         "fight idle")

    # Reset the engine counters once both upload queues are idle; a request
    # that straddles the reset would otherwise report a bogus age.
    for _ in range(120):
        if not core.ram[FP1 + ABI["F_DMAREQ"]] \
                and not core.ram[0x4040 + ABI["F_DMAREQ"]]:
            break
        core.step()
    core.put(ABI["TEL_CTRL"], 1)
    core.step(2)
    base_bytes = u32(core, ABI["TEL_HUD_BYTES"])
    trace = []
    for i in range(frames):
        before = u32(core, ABI["TEL_HUD_BYTES"])
        before_frames = core.word(ABI["TEL_HUD_FRAMES"])
        if i < 90:
            pass
        elif i < 150:
            core.buttons[0] = {RIGHT}
        elif i == 150:
            core.buttons[0] = set()
            tap(core, UP)
        elif attacks and i in (200, 260, 320):
            core.buttons[0] = set()
            tap(core, B)
        else:
            core.buttons[0] = set()
        core.step()
        trace.append({
            "frame": i,
            "p1req": core.ram[FP1 + ABI["F_DMAREQ"]],
            "p2req": core.ram[0x4040 + ABI["F_DMAREQ"]],
            "hud_bytes": u32(core, ABI["TEL_HUD_BYTES"]) - before,
            "hud_calls": core.word(ABI["TEL_HUD_FRAMES"]) - before_frames,
            "state": core.word(FP1 + 8),
            "fx": core.ram[0x510C],
            "tel_frames": core.word(ABI["TEL_FRAMES"]),
        })

    def u16(addr):
        return core.word(addr)

    frames_n = u16(ABI["TEL_FRAMES"])
    dma1 = u16(ABI["TEL_DMA_P1"])
    dma2 = u16(ABI["TEL_DMA_P2"])
    hud_frames = u16(ABI["TEL_HUD_FRAMES"])
    age1 = u16(ABI["TEL_AGE_SUM_P1"])
    age2 = u16(ABI["TEL_AGE_SUM_P2"])
    req1 = u16(ABI["TEL_REQS_P1"])
    req2 = u16(ABI["TEL_REQS_P2"])
    drop1 = u16(ABI["TEL_DROP_P1"])
    drop2 = u16(ABI["TEL_DROP_P2"])
    bytes_total = u32(core, ABI["TEL_HUD_BYTES"]) - base_bytes
    both = sum(1 for t in trace if t["p1req"] and t["p2req"])
    full = sum(1 for t in trace if t["hud_bytes"] >= 1024)
    bands = sum(1 for t in trace if 0 < t["hud_bytes"] < 1024)
    return {
        "frames": frames_n,
        "p1_pending_pct": round(100 * dma1 / max(1, frames_n), 1),
        "p2_pending_pct": round(100 * dma2 / max(1, frames_n), 1),
        "both_pending_pct": round(100 * both / max(1, len(trace)), 1),
        "p1_requests": req1, "p1_dropped": drop1,
        "p2_requests": req2, "p2_dropped": drop2,
        "p1_age_avg": round(age1 / max(1, dma1), 2),
        "p2_age_avg": round(age2 / max(1, dma2), 2),
        "p1_age_max": u16(ABI["TEL_AGE_MAX_P1"]),
        "p2_age_max": u16(ABI["TEL_AGE_MAX_P2"]),
        "hud_frames": hud_frames,
        "hud_bytes": bytes_total,
        "hud_bytes_per_frame": round(bytes_total / max(1, frames_n), 1),
        "hud_band_frames": bands,
        "hud_full_frames": full,
        "dmachunk": ABI["DMACHUNK"],
        "video_frames": core.video_frames,
        "msu_failures": core.word(0x5102),
        "projectile_drops": core.word(0x5104),
        "oam_drops": core.word(0x5106),
        "end_gamestate": core.word(GS),
        "end_framecnt": core.word(FRAME),
        "end_p1state": core.word(FP1 + 8),
        "end_p2state": core.word(0x4040 + 8),
        "end_p1hp": core.word(FP1 + 16),
        "end_p2hp": core.word(0x4040 + 16),
        "rt_fx": core.ram[0x510C],
        "fx_pct": round(100 * sum(1 for t in trace if t["fx"])
                        / max(1, len(trace)), 1),
        "tel_ctrl": core.word(ABI["TEL_CTRL"]),
        "sp_fixes": core.word(ABI["TEL_SPFIX"]),
        "sp_last_bad": core.word(ABI["TEL_SPLAST"]),
        "tel_resets": [trace[i]["frame"] for i in range(1, len(trace))
                       if trace[i]["tel_frames"] < trace[i - 1]["tel_frames"]],
        "hud_events": [{"frame": t["frame"], "bytes": t["hud_bytes"],
                        "calls": t["hud_calls"]}
                       for t in trace if t["hud_bytes"]],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", default="/usr/lib/x86_64-linux-gnu/libretro/"
                                     "snes9x_libretro.so")
    ap.add_argument("--rom", default=str(ROOT / "kof98-snes.sfc"))
    ap.add_argument("--frames", type=int, default=420)
    ap.add_argument("--attacks", action="store_true",
                    help="add three B attacks")
    ap.add_argument("--assert-clean", action="store_true",
                    help="exit 1 if the fight stops presenting, SP leaked, "
                         "or the round did not recover")
    args = ap.parse_args()
    core = Core(args.core, args.rom)
    try:
        report = run(core, args.frames, args.attacks)
    finally:
        core.close()
    print(json.dumps(report, indent=2))
    if args.assert_clean:
        bad = (report["end_gamestate"] != 1
               or report["end_p1state"] != 0
               or report["end_p2state"] != 0
               or report["sp_fixes"] != 0
               or report["frames"] < args.frames // 2)
        if bad:
            print("PRESENTATION STRESS FAILED", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
