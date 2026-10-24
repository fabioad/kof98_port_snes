#!/usr/bin/env python3
"""Choi's Zujou Sashi throw must no longer drain most of the life bar.

Choi sits on the opponent's head and stabs eight times (MUGEN state 810).
The source values (-24 per stab, a ~1500-HP MUGEN bar) were copied verbatim
into the port's 200-HP bar, so the throw removed 192 HP -- 96% of a full
life bar -- and looked like an energy drain.

The per-stab value is now -8: eight stabs remove 64 HP, one third of the old
total, which keeps the throw strong without making it a one-hit kill.

Run after a PVSnesLib build:

    python3 tools/test_choi_throw_headless.py
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                          # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE, F_X, F_HP = 0x8, 0x0, 0x10
F_GRAB = 52
FCNTR = 0x1024
X, Y = 9, 1                       # libretro X/Y -> mugen y/x (throw = x+y)
RELEASE_LIMIT = 180               # eight stabs plus recovery

# Old drain was 192 HP (8 x 24) on the 200-HP bar.  A third lands near 64;
# allow the whole 50..80 band so combo decay/tuning tweaks do not break it.
MIN_DAMAGE, MAX_DAMAGE = 50, 80


def check_choi_throw(core, select_state):
    enter_fight(core, select_state, "choi", "kyo")
    core.put(FP1 + F_X, 130 << 8)
    core.put(FP2 + F_X, 160 << 8)
    core.put(FP1 + F_HP, 200)
    core.put(FP2 + F_HP, 200)
    core.step(10)

    core.buttons[0] = {X, Y}
    core.step(3)
    core.buttons[0] = set()

    grabbed = False
    released_at = None
    for tick in range(RELEASE_LIMIT + 1):
        core.step()
        a_state = core.ram[FP1 + F_STATE]
        v_state = core.ram[FP2 + F_STATE]
        if a_state == 75 and v_state == 76:
            grabbed = True
        if grabbed and v_state != 76:
            released_at = tick
            break
    if not grabbed:
        raise AssertionError("throw never grabbed (attacker 75, victim 76)")
    if core.ram[FP2 + F_GRAB]:
        raise AssertionError("victim stayed grabbed")
    if released_at is None:
        raise AssertionError(
            f"throw did not release within {RELEASE_LIMIT} ticks "
            f"(attacker state={core.ram[FP1 + F_STATE]}, "
            f"victim state={core.ram[FP2 + F_STATE]})")

    for _ in range(400):
        if (core.ram[FP1 + F_STATE] == 0
                and core.ram[FP2 + F_STATE] == 0):
            break
        core.step()
    else:
        raise AssertionError(
            f"fighters did not recover: p1={core.ram[FP1 + F_STATE]} "
            f"p2={core.ram[FP2 + F_STATE]}")

    hp = core.word(FP2 + F_HP)
    damage = 200 - hp
    if not MIN_DAMAGE <= damage <= MAX_DAMAGE:
        raise AssertionError(
            f"throw drained {damage} HP (victim hp={hp}); expected "
            f"{MIN_DAMAGE}..{MAX_DAMAGE} after the one-third reduction")

    print(f"PASS Choi throw released at tick {released_at}, "
          f"victim hp={hp} (drained {damage} HP)", flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        check_choi_throw(core, boot_select(core))
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
