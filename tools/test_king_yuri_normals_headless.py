#!/usr/bin/env python3
"""King and Yuri ground-normal animation mapping.

King's source pack has close and far standing normals.  The port used a
mix (light kick = close strong kick, strong kick = far light punch), so the
kicks looked completely different from every other character.  King now
uses the four far animations (250/260/270/280); Yuri's source states
200/202/204/206 are the close weak punch / strong punch / weak kick /
strong kick and are mapped accordingly.

Run after a PVSnesLib build:

    python3 tools/test_king_yuri_normals_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight as bf                                  # noqa: E402
from calibration.headless import Core                     # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
SYM = ROOT / "kof98-snes.sym"
F_STATE, F_ANIM = 0x4008, 0x4012
# libretro SNES ids: Y=1 (MUGEN x), X=9 (y), B=0 (a), A=8 (b).
BUTTONS = ((1, 5, "weak punch"), (9, 6, "strong punch"),
           (0, 7, "weak kick"), (8, 8, "strong kick"))
EXPECTED = {
    "king": {5: 250, 6: 260, 7: 270, 8: 280},
    "yuri": {5: 200, 6: 202, 7: 204, 8: 206},
}


def symbol_offset(label):
    for line in SYM.read_text().splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] == label:
            return int(fields[0], 16) & 0xFFFF
    raise AssertionError(f"{label} missing from {SYM.name}")


def main():
    for character, mapping in EXPECTED.items():
        cfg = bf.CHARS[character]
        for sid, anim in mapping.items():
            assert cfg["anims"][sid] == anim, (
                f"{character} sid {sid}: anim {cfg['anims'][sid]} != {anim}")
            assert cfg["moves"][sid] == anim, (
                f"{character} sid {sid}: state {cfg['moves'][sid]} != {anim}")

        core = Core(CORE, ROOT / "kof98-snes.sfc")
        try:
            select = boot_select(core)
            enter_fight(core, select, character, "kyo")
            core.ram[0x1090] = core.ram[0x1091] = 0
            core.step(20)
            for button, sid, label in BUTTONS:
                core.buttons[0] = {button}
                core.step(2)
                core.buttons[0] = set()
                state = core.ram[F_STATE]
                anim = core.word(F_ANIM)
                expected = symbol_offset(f"{character}Anim{sid}")
                assert state == sid, (
                    f"{character} {label}: sid {state} != {sid}")
                assert anim == expected, (
                    f"{character} {label}: anim ${anim:04X} != ${expected:04X}")
                core.step(40)
            print(f"PASS {character}: ground normals use the correct "
                  f"animations ({mapping})")
        finally:
            core.close()


if __name__ == "__main__":
    main()
