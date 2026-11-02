#!/usr/bin/env python3
"""Headless regression for King's move voices.

King's CNS writes PlaySnd values as ``value = 1000, 0`` (a space after the
comma).  The parser used to reject that form, so every King voice was dropped
and the moves were silent.  The two QCF specials must now queue/stream their
voice samples.

Run after a PVSnesLib build:

    python3 tools/test_king_voice_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                  # noqa: E402
    boot_select, enter_fight, X, Y, DOWN, RIGHT,
)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1_STATE, P1_X = 0x4008, 0x4000
P2_X = 0x4040
VQ_TAIL = 0x5112
DIGI_ACTIVE = 0x15A


def qcf(core, button):
    for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
        core.buttons[0] = set(direction)
        core.step(2)
    core.buttons[0] = set()
    core.step(1)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def main():
    generated = (ROOT / "build/gen_fight/voices.inc").read_text()
    assert 'VoiceTab_king:' in generated
    king_tab = generated[generated.index("VoiceTab_king:"):]
    king_tab = king_tab[:king_tab.index(".ENDS")]
    assert king_tab.count(".db 2,8,15") >= 10, "King voice table too small"

    core = Core(CORE, str(ROOT / "kof98-snes.sfc"))
    try:
        select = boot_select(core)
        failures = []
        # QCF+X reaches state 1050 and QCF+Y state 1000 (both are voiced).
        for button, expected in ((X, 49), (Y, 48)):
            enter_fight(core, select, "king", "kyo")
            core.ram[0x1090] = 0
            core.ram[0x1091] = 0
            core.put(P1_X, 70 << 8)
            core.put(P2_X, 90 << 8)
            core.step(20)
            tail0 = core.word(VQ_TAIL)
            qcf(core, button)

            seen, voiced = [], False
            for _ in range(120):
                core.step()
                state = core.ram[P1_STATE]
                if not seen or seen[-1] != state:
                    seen.append(state)
                if core.word(VQ_TAIL) != tail0 or core.ram[DIGI_ACTIVE]:
                    voiced = True
            if expected not in seen:
                failures.append(f"button {button}: state {expected} never "
                                f"reached: {seen}")
            if not voiced:
                failures.append(f"button {button}: no voice queued/streamed")
            print(f"King QCF button {button}: states={seen[:8]} "
                  f"voiced={voiced}")
        if failures:
            for failure in failures:
                print("FAIL:", failure)
            return 1
        print("King move voices: both QCF specials streamed OK")
        return 0
    finally:
        core.close()


if __name__ == "__main__":
    raise SystemExit(main())
