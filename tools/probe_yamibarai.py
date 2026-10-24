#!/usr/bin/env python3
"""Capture P1 body-anim/frame progression for Kyo/Iori Yami Barai.

Locks P1 on the requested character, fires the ~40B,F+punch charge move
(sid 48 weak X / sid 49 strong Y), and samples (state, anim, frame) while
the move runs so the AIR action driving the body can be identified.
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import test_fight_remote as t
from test_roster import parse_tables, lock_side, to_select, W_CPU2

PADS = ("LEFT", "RIGHT", "DOWN", "UP", "X", "Y", "A", "B")


def reset(ra):
    for b in PADS:
        ra.button(0, b, False)
    ra.command("WRITE_CORE_RAM 4000 00 50")   # P1.x = 80
    ra.command("WRITE_CORE_RAM 4040 00 E0")   # P2.x = 224
    ra.command("WRITE_CORE_RAM 4050 C8 00")   # P2.hp = 200
    time.sleep(0.4)


def fire(ra, punch):
    """~40B charge, then F then punch (the port's Yami Barai motion).

    The F edge must land in the input ring BEFORE the punch press -- if
    the punch packet wins the UDP race the ring sees dir+x on the B
    entry and only the normal-punch rule can match.
    """
    ra.button(0, "LEFT", True)
    time.sleep(1.0)
    ra.button(0, "RIGHT", True)
    time.sleep(0.10)
    ra.button(0, "LEFT", False)
    ra.button(0, punch, True)
    time.sleep(0.15)
    ra.button(0, punch, False)
    ra.button(0, "RIGHT", False)


def qcf(ra, punch):
    """~D, DF, F+punch (Iori's QCF motion, 15-tick window)."""
    ra.button(0, "DOWN", True)
    time.sleep(0.05)
    ra.button(0, "RIGHT", True)
    time.sleep(0.05)
    ra.button(0, "DOWN", False)
    time.sleep(0.02)
    ra.button(0, punch, True)
    time.sleep(0.12)
    ra.button(0, punch, False)
    for b in ("DOWN", "RIGHT"):
        ra.button(0, b, False)


def sample(ra, sid, frames=50):
    out = []
    entered = False
    for _ in range(frames):
        s = ra.snapshot()
        f = s["p1"]
        if f["state"] == sid:
            entered = True
            if not out or out[-1] != (f["anim"], f["frame"]):
                out.append((f["anim"], f["frame"]))
        elif entered and f["state"] == 0 and len(out) > 2:
            break
        time.sleep(0.05)
    return entered, out


def fire_and_log(ra, tag, punch, sid, motion):
    for attempt in range(10):
        reset(ra)
        motion(ra, punch)
        entered, out = sample(ra, sid)
        if entered:
            break
    print(f"{tag}: entered sid {sid}: {entered} (attempt {attempt + 1})")
    for i, (anim, frame) in enumerate(out):
        print(f"  s{i:02d} anim={anim} frame={frame}")
    print(f"{tag}: {len(out)} distinct (anim,frame) samples")
    return entered, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("char", choices=["kyo", "iori"])
    ap.add_argument("--retroarch", default="retroarch")
    ap.add_argument("--core", default=t.CORE)
    args = ap.parse_args()

    roster = parse_tables()
    p1 = next(i for i, r in roster.items() if r["name"] == args.char)
    p2 = next(i for i, r in roster.items()
              if r["name"] not in (args.char, "shingo"))

    ra = t.RetroArch()
    try:
        ra.launch(args.retroarch, args.core)
        ra.wait_ready()
        to_select(ra)
        lock_side(ra, 1, roster[p2]["cell"], 0x108F)
        lock_side(ra, 0, roster[p1]["cell"], 0x108E)
        t.wait_for(ra, lambda s: s["gamestate"] == 1, timeout=20)
        ra.command(f"WRITE_CORE_RAM {W_CPU2:X} 00")   # P2 dummy stays idle
        state = t.wait_for(ra, lambda s: s["p1"]["state"] == 0, timeout=10)
        print(f"P1={args.char} P2={roster[p2]['name']}")
        # retropad X -> mugen x (weak punch), retropad A -> mugen y (strong)
        motion, tag = (fire, "~B,F") if args.char == "kyo" else (qcf, "QCF")
        ok1 = fire_and_log(ra, f"{args.char} {tag}+x (weak)", "X", 48, motion)
        ok2 = fire_and_log(ra, f"{args.char} {tag}+y (strong)", "A", 49, motion)
        if not (ok1[0] and ok2[0]):
            raise SystemExit(1)
    finally:
        ra.close()


if __name__ == "__main__":
    sys.exit(main())
