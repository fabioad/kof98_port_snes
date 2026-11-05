#!/usr/bin/env python3
"""Chizuru voice and sound regression.

Checks that the generated VoiceTab_chizuru has all ten samples, streams each
one from the .msu file through the real voice queue, and that a wired special
(QCF+X) requests a sound through SfxPlay.

Run after a PVSnesLib build:

    python3 tools/test_chizuru_audio_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
MSU = ROOT / "kof98-snes.msu"
FP1, FP2 = 0x4000, 0x4040
F_STATE = 0x4008
VQ_HEAD, VQ_TAIL, VQ_DATA = 0x5110, 0x5112, 0x5120
VQ_BUSY, VQ_PTRIDX = 0x5180, 0x5182
VQ_POS, VQ_TOTAL, VQ_MSUOFS = 0x5186, 0x5188, 0x518A
MSU_ACTIVE = 0x015A
SFXLAST = 0x1031
DOWN, LEFT, RIGHT, X, Y = 5, 6, 7, 1, 9
QCB = (frozenset({DOWN}), frozenset({DOWN, LEFT}), frozenset({LEFT}))
QCF = (frozenset({DOWN}), frozenset({DOWN, RIGHT}), frozenset({RIGHT}))


def u32(core, addr):
    return sum(core.ram[addr + i] << (8 * i) for i in range(4))


def wait(core, predicate, label, limit=600):
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise AssertionError(label)


def queue_voice(core, ptr, index):
    tail = core.word(VQ_TAIL)
    core.ram[VQ_DATA + tail] = ptr & 0xFF
    core.ram[VQ_DATA + tail + 1] = ptr >> 8
    core.ram[VQ_DATA + tail + 2] = index
    core.ram[VQ_DATA + tail + 3] = 0
    core.ram[VQ_TAIL] = (tail + 4) & 0x3F
    core.ram[VQ_TAIL + 1] = 0


def check_voice(core, msu, ptr, index):
    previous = u32(core, VQ_MSUOFS)
    queue_voice(core, ptr, index)
    wait(core, lambda: u32(core, VQ_MSUOFS) != previous,
         f"voice {index}: stream start")
    wait(core, lambda: core.word(VQ_TOTAL) != 0
         and core.word(VQ_POS) == core.word(VQ_TOTAL),
         f"voice {index}: stream complete")
    total = core.word(VQ_TOTAL)
    offset = u32(core, VQ_MSUOFS)
    sample = msu[offset:offset + total]
    if len(sample) != total:
        raise AssertionError(f"voice {index}: offset ${offset:06X} past MSU")
    for _ in range(3):
        for base in (0x7F0000, 0x7F1800):
            start = base - 0x7E0000
            if bytes(core.ram[start:start + total]) == sample:
                return total, offset
        core.step()
    raise AssertionError(
        f"voice {index}: cache mismatch (off=${offset:06X}, len={total})")


def motion(core, steps, button):
    for direction in steps:
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = {button}
    core.step(2)
    core.buttons[0] = set()


def main():
    generated = (ROOT / "build/gen_fight/voices.inc").read_text()
    assert "VoiceTab_chizuru:" in generated
    tab = generated[generated.index("VoiceTab_chizuru:"):]
    tab = tab[:tab.index(".ENDS")]
    assert tab.count(".db 2,8,15") == 10, "expected ten Chizuru voices"

    msu = MSU.read_bytes()
    core = Core(CORE, str(ROM))
    core.capture_audio = True
    try:
        select = boot_select(core)
        enter_fight(core, select, "chizuru", "kyo")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.put(FP1, 80 << 8)
        core.put(FP2, 125 << 8)
        core.step(20)

        # QCB+X -> state 1100, which carries a voice.
        motion(core, QCB, X)
        wait(core, lambda: core.word(VQ_TOTAL) != 0, "Chizuru initial voice")
        ptr = core.word(VQ_PTRIDX)
        wait(core, lambda: core.word(VQ_POS) == core.word(VQ_TOTAL)
             and core.ram[VQ_BUSY] == 0, "Chizuru initial voice done")

        checked = 0
        for index in range(10):
            wait(core, lambda: core.ram[VQ_BUSY] == 0
                 and core.word(VQ_HEAD) == core.word(VQ_TAIL)
                 and core.ram[MSU_ACTIVE] == 0, f"voice {index} idle")
            total, offset = check_voice(core, msu, ptr, index)
            checked += 1
            print(f"OK Chizuru voice {index}: ${offset:06X} ({total} bytes)")

        # QCF+X -> state 1000; its PlaySnd must reach SfxPlay.
        wait(core, lambda: core.ram[F_STATE] == 0, "recover")
        core.ram[SFXLAST] = 0
        motion(core, QCF, X)
        sound_seen = False
        for _ in range(120):
            core.step()
            if core.ram[SFXLAST] != 0:
                sound_seen = True
                break
        assert sound_seen, "QCF+X did not request a sound"
        print("PASS Chizuru sounds and all ten voices")
    finally:
        core.close()


if __name__ == "__main__":
    main()
