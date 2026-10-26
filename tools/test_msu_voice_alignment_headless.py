#!/usr/bin/env python3
"""Sector-aligned MSU voice streaming regression.

The SD2SNES data cache is refilled from 512-byte sectors.  The CHR loader
already aligns every MSU read to a sector, but the voice streamer used to
read 512-byte chunks from arbitrary file offsets, so a chunk could start at
a non-zero in-sector pointer (or cross the cache page) and stall the console
while music kept playing.

This test streams every Clark voice through the queue and compares the cache
bytes with the source ``.msu`` file, including odd and multi-chunk samples.

Run after a PVSnesLib build:

    python3 tools/test_msu_voice_alignment_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                          # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
VQ_HEAD, VQ_TAIL, VQ_DATA = 0x5110, 0x5112, 0x5120
VQ_BUSY, VQ_PTRIDX = 0x5180, 0x5182
VQ_POS, VQ_TOTAL, VQ_MSUOFS = 0x5186, 0x5188, 0x518A
MSU_ACTIVE = 0x015A


def u16(core, addr):
    return core.word(addr)


def u32(core, addr):
    return sum(core.ram[addr + i] << (8 * i) for i in range(4))


def wait(core, predicate, label, limit=400):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(
        f"{label}: busy={core.ram[VQ_BUSY]} pos={u16(core, VQ_POS)} "
        f"total={u16(core, VQ_TOTAL)}")


def check(core, msu, ptr, index):
    # The queue is a four-byte ring record: VoicePtrTab offset + voice index.
    tail = u16(core, VQ_TAIL)
    core.ram[VQ_DATA + tail] = ptr & 0xFF
    core.ram[VQ_DATA + tail + 1] = ptr >> 8
    core.ram[VQ_DATA + tail + 2] = index
    core.ram[VQ_DATA + tail + 3] = 0
    core.ram[VQ_TAIL] = (tail + 4) & 0x3F
    core.ram[VQ_TAIL + 1] = 0

    wait(core, lambda: u16(core, VQ_TOTAL) != 0
         and u16(core, VQ_POS) == u16(core, VQ_TOTAL),
         f"voice {index} stream")
    total = u16(core, VQ_TOTAL)
    off = u32(core, VQ_MSUOFS)
    sample = msu[off:off + total]
    if len(sample) != total:
        raise AssertionError(f"voice {index}: offset ${off:06X} past MSU end")
    for _ in range(3):
        for base in (0x7F0000, 0x7F1800):
            start = base - 0x7E0000
            if bytes(core.ram[start:start + total]) == sample:
                return total, off
        core.step()
    raise AssertionError(f"voice {index}: cache mismatch (off=${off:06X}, "
                         f"len={total})")


def main(core_path, rom, msu_path):
    msu = msu_path.read_bytes()
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "ralf", "clark")
        core.put(FP1, 90 << 8)
        core.put(FP2, 200 << 8)
        core.step(10)

        # P2 light punch enters Clark state 5, whose ActTab requests a voice.
        # Its queue record gives us the VoicePtrTab offset for Clark.
        core.buttons[1] = {1}
        core.step(3)
        core.buttons[1] = set()
        wait(core, lambda: u16(core, VQ_TOTAL) != 0, "Clark voice")
        ptr = u16(core, VQ_PTRIDX)
        wait(core, lambda: u16(core, VQ_POS) == u16(core, VQ_TOTAL)
             and core.ram[VQ_BUSY] == 0, "Clark voice done")

        checked = 0
        for index in range(21):
            wait(core, lambda: core.ram[VQ_BUSY] == 0
                 and u16(core, VQ_HEAD) == u16(core, VQ_TAIL)
                 and core.ram[MSU_ACTIVE] == 0, f"voice {index} idle")
            total, off = check(core, msu, ptr, index)
            checked += 1
            print(f"OK voice {index}: ${off:06X} ({total} bytes)", flush=True)
        print(f"PASS {checked} aligned MSU voices", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    ap.add_argument("--msu", type=Path, default=ROOT / "kof98-snes.msu")
    args = ap.parse_args()
    main(args.core, args.rom, args.msu)
