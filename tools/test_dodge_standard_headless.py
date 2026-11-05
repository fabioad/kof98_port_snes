#!/usr/bin/env python3
"""The shared L dodge must keep the standard directions.

L+back  -> back roll (sid 94)
L+fwd   -> forward roll (sid 95)
L alone -> standing dodge (sid 69), never the taunt

The commands, states and velocities stay as they are; only the animation
sources are mapped.  The source Turn controller on the forward/back states
was being executed unconditionally by the ActTab, flipping the fighter and
inverting the input; the build drops that Turn row.  L alone now emits the
c token, so the ESQ_L rule (not start/taunt) owns it.

Run after a PVSnesLib build:

    python3 tools/test_dodge_standard_headless.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf                                  # noqa: E402
from calibration.headless import Core                     # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
SYM = ROOT / "kof98-snes.sym"
FP1, FP2 = 0x4000, 0x4040
F_STATE, F_ANIM, F_FACING = FP1 + 8, FP1 + 0x12, FP1 + 14
L, FWD, BACK = 10, 7, 6
EXPECTED = {
    "kyo": (710, 700), "terry": (710, 700), "iori": (710, 700),
    "rugal": (710, 700), "king": (4100, 4000), "yuri": (251, 250),
    "mai": (711, 710),
}
CASES = ((FWD, 95, "L+forward"), (BACK, 94, "L+back"), (None, 69, "L alone"))


def symbol_offset(label):
    for line in SYM.read_text().splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] == label:
            return int(fields[0], 16) & 0xFFFF
    raise AssertionError(f"{label} missing from {SYM.name}")


def anim_label(character, sid):
    """Resolve the generated AnimTab entry, including shared aliases."""
    text = (ROOT / "build/gen_fight" / f"{character}_spr.inc").read_text()
    match = re.search(rf"{character}AnimTab:\n(.*?)(?=\n\w)", text, re.S)
    rows = re.findall(r"\.dw (\w+)", match.group(1))
    return rows[sid]


def run(core, select, character, direction, wanted):
    enter_fight(core, select, character, "kyo")
    core.ram[0x1090] = core.ram[0x1091] = 0
    core.put(FP1, 80 << 8)
    core.put(FP2, 200 << 8)
    core.step(20)
    core.ram[F_FACING] = 1
    core.step(2)
    core.ram[F_FACING] = 1
    if direction is None:
        x0 = core.word(FP1)
        core.buttons[0] = {L}
        core.step(2)
    else:
        core.buttons[0] = {direction}
        core.step(2)
        x0 = core.word(FP1)
        core.buttons[0] = {direction, L}
        core.step(2)
    core.buttons[0] = set()
    anim = None
    for _ in range(20):
        core.step()
        if core.ram[F_STATE] == wanted and anim is None:
            anim = core.word(F_ANIM)
    # Let the short dodge finish and keep measuring displacement/facing.
    for _ in range(20):
        core.step()
    return anim, x0, core.word(FP1), core.ram[F_FACING]


def main():
    for character, (back_anim, fwd_anim) in EXPECTED.items():
        cfg = bf.CHARS[character]
        assert cfg["anims"][94] == back_anim, (
            f"{character}: back anim {cfg['anims'][94]} != {back_anim}")
        assert cfg["anims"][95] == fwd_anim, (
            f"{character}: fwd anim {cfg['anims'][95]} != {fwd_anim}")

        core = Core(CORE, ROOT / "kof98-snes.sfc")
        try:
            select = boot_select(core)
            for direction, sid, label in CASES:
                anim, x0, x1, facing = run(core, select, character,
                                           direction, sid)
                expected = symbol_offset(anim_label(character, sid))
                assert anim == expected, (
                    f"{character} {label}: anim ${anim:04X} != ${expected:04X}")
                assert facing == 1, (
                    f"{character} {label}: dodge flipped the facing ({facing})")
                if sid == 95:
                    assert x1 >= x0, (
                        f"{character} L+forward moved backward ({x0} -> {x1})")
                elif sid == 94:
                    assert x1 <= x0, (
                        f"{character} L+back moved forward ({x0} -> {x1})")
                else:
                    assert abs(x1 - x0) <= 512, (
                        f"{character} neutral dodge drifted ({x0} -> {x1})")
            print(f"PASS {character}: L+forward/back/neutral use the "
                  f"standard dodge slots")
        finally:
            core.close()


if __name__ == "__main__":
    main()
