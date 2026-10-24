#!/usr/bin/env python3
"""Exercise a full versus round change, including the announcer upload."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import test_fight_remote as t
from test_roster import lock_side, press, to_select


def wait_state(ra, target, timeout):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = ra.read_ram(0x1020, 1)[0]
        if last == target:
            return
        time.sleep(0.1)
    raise AssertionError(
        f"wait gs={target} timed out: gs={last}, "
        f"frame={ra.read_ram(0x1024, 1)[0]}, "
        f"effects_pending={ra.read_ram(0x46F8, 1)[0]}")


ra = t.RetroArch()
ra.launch("retroarch", t.CORE)
try:
    ra.wait_ready()
    to_select(ra)
    if ra.read_ram(0x1091, 1)[0]:
        press(ra, 1, "START")
    lock_side(ra, 1, 6, 0x108F)  # Iori
    lock_side(ra, 0, 3, 0x108E)  # Kyo
    wait_state(ra, 1, 30)
    print("round 1 reached", flush=True)
    ra.command("WRITE_CORE_RAM 4050 00 00")  # P2 HP = 0
    wait_state(ra, 0, 30)
    print("intermission reached", flush=True)
    wait_state(ra, 4, 40)
    wait_state(ra, 1, 40)
    print("round 2 reached; audio seq=", ra.read_ram(0x1032, 1)[0],
          "effects_pending=", ra.read_ram(0x46F8, 1)[0], flush=True)
finally:
    ra.close()
