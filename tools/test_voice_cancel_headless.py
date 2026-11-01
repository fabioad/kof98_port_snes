#!/usr/bin/env python3
"""P1 move voices cancel on a new attack; P2 voices are left alone.

The test seeds the voice queue with one P1 and one P2 record, makes P1 start
another normal, and checks:

  * the P1 record is marked cancelled and an in-flight P1 stream is stopped;
  * the P2 record and in-flight P2 stream stay untouched.

Run after a PVSnesLib build:

    python3 tools/test_voice_cancel_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_X, F_HP = 0x4008, 0x4000, 0x4010
FP2 = 0x40
VQ_HEAD, VQ_TAIL, VQ_DATA = 0x5110, 0x5112, 0x5120
VQ_BUSY, VQ_CUR_SIDE = 0x5180, 0x5194
VQ_AUDIO_READY = 0x46F8
DIGI_ACTIVE, DIGI_REMAIN = 0x15A, 0x158
CPU1, CPU2 = 0x1090, 0x1091
STRONG_P, STRONG_K = 9, 8


def press(core, button, ticks=1, port=0):
    core.buttons[port] = {button}
    core.step(ticks)
    core.buttons[port] = set()


def put_word(core, address, value):
    core.ram[address] = value & 0xFF
    core.ram[address + 1] = (value >> 8) & 0xFF


def get_word(core, address):
    return core.ram[address] | (core.ram[address + 1] << 8)


def seed_voice_queue(core, current_side):
    put_word(core, VQ_HEAD, 0)
    put_word(core, VQ_TAIL, 8)
    put_word(core, VQ_DATA, 0)
    put_word(core, VQ_DATA + 2, 0x0001)      # P1 record
    put_word(core, VQ_DATA + 4, 0)
    put_word(core, VQ_DATA + 6, 0x0102)      # P2 record
    put_word(core, VQ_BUSY, 2)
    core.ram[VQ_AUDIO_READY] = 1            # don't start fetching a record
    core.ram[DIGI_ACTIVE] = 1
    core.ram[DIGI_REMAIN] = 1
    core.ram[VQ_CUR_SIDE] = current_side


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "ryu", "kyo")
        core.put(F_X, 60 << 8)
        core.put(F_X + FP2, 220 << 8)       # out of range: no contact hitstop
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.step(180)

        # 1) P1 pad: P1's old voice is cancelled, P2's record is untouched.
        core.ram[CPU1] = 0
        core.ram[CPU2] = 0
        seed_voice_queue(core, current_side=0)
        press(core, STRONG_P, 1, port=0)
        rec1 = get_word(core, VQ_DATA + 2)
        rec2 = get_word(core, VQ_DATA + 6)
        if rec1 & 0xFF != 0xFF:
            raise AssertionError(f"P1 record not cancelled: ${rec1:04X}")
        if rec2 & 0xFF != 0x02:
            raise AssertionError(f"P2 record was touched: ${rec2:04X}")
        if core.ram[DIGI_ACTIVE]:
            raise AssertionError("P1 in-flight stream was not stopped")
        print("PASS P1 pad cancelled its previous voice", flush=True)

        # 2) P2 pad with P1 as CPU: P2's old voice is cancelled.
        enter_fight(core, select_state, "ryu", "kyo")
        core.put(F_X, 60 << 8)
        core.put(F_X + FP2, 220 << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.step(180)
        core.ram[CPU1] = 1
        core.ram[CPU2] = 0
        seed_voice_queue(core, current_side=1)
        press(core, STRONG_P, 1, port=1)
        rec1 = get_word(core, VQ_DATA + 2)
        rec2 = get_word(core, VQ_DATA + 6)
        if rec2 & 0xFF != 0xFF:
            raise AssertionError(f"P2 record not cancelled: ${rec2:04X}")
        if rec1 & 0xFF != 0x01:
            raise AssertionError(f"P1 record was touched: ${rec1:04X}")
        if core.ram[DIGI_ACTIVE]:
            raise AssertionError("P2 in-flight stream was not stopped")
        print("PASS P2 pad cancelled its previous voice", flush=True)

        # 3) CPU P2: P2's voice must survive a P1 pad move.
        enter_fight(core, select_state, "ryu", "kyo")
        core.put(F_X, 60 << 8)
        core.put(F_X + FP2, 220 << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.step(180)
        core.ram[CPU1] = 0
        core.ram[CPU2] = 1
        seed_voice_queue(core, current_side=1)
        press(core, STRONG_K, 1, port=0)
        rec1 = get_word(core, VQ_DATA + 2)
        rec2 = get_word(core, VQ_DATA + 6)
        if rec1 & 0xFF != 0xFF:
            raise AssertionError(f"P1 record not cancelled: ${rec1:04X}")
        if rec2 & 0xFF != 0x02:
            raise AssertionError(f"CPU P2 record was touched: ${rec2:04X}")
        if not core.ram[DIGI_ACTIVE]:
            raise AssertionError("CPU P2 in-flight stream was stopped")
        print("PASS CPU P2 voice was left untouched", flush=True)
        print("PASS voice cancellation is side-aware", flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
