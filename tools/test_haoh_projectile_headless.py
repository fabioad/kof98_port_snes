#!/usr/bin/env python3
"""Headless regression: every Haoh Shikou Ken super must fire a shot.

The port draws the Haoh with the compact Ko'ou Ken clip: the arcade
2070/2100 blast is a 96x155 cel and does not fit the 16-cell (2 KiB) effect
page or the OAM budget.  What must not happen is the shot staying invisible:

* a release pinned to frame 0 fires under the super flash, before the palm
  pose, and usually connects before the player sees it (Yuri's old MAX
  override and Takuma's old 1500 mapping);
* Takuma's QCFx2+P was shadowed by the Ryuuko shortcut, so the super never
  reached the projectile state at all.

This test fires each Haoh variant against a distant dummy and requires the
spark to be created after the wind-up has started, to emit palette-2 OAM
cells, to travel, and to connect.

Run after a PVSnesLib build:

    python3 tools/test_haoh_projectile_headless.py
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
F_STATE = 0x4008
F_FRAME = 0x400A
F_POWER = 0x4030
P2_HP = 0x4050
SPARKS = 0x4200
SPK_SIZE = 20
OAM = 0x1800
BUTTONS = {1: 1, 2: 9, 4: 0, 8: 8, 16: 10, 32: 11, 64: 2}

WEAK, STRONG, KICK_W, KICK_S = 1, 2, 4, 8
BOTH_P = WEAK | STRONG
BOTH_K = KICK_W | KICK_S

QCB2 = [[2, 0], [10, 0], [8, 0], [2, 0], [10, 0], [8, 0]]
QCF2 = [[2, 0], [6, 0], [4, 0], [2, 0], [6, 0], [4, 0]]
# 641236+P, the parsed source command used by Ryo and Robert.
PRETZEL = [[68, 0], [8, 0], [2, 0], [4, 0]]

# char, sid, button mask, motion head, label
CASES = (
    ("yuri", 85, WEAK, QCB2, "Haoh weak"),
    ("yuri", 87, STRONG, QCB2, "Haoh strong"),
    ("yuri", 107, BOTH_P, QCF2, "MAX Haoh"),
    ("ryo", 85, WEAK, PRETZEL, "Haoh weak"),
    ("ryo", 86, STRONG, PRETZEL, "Haoh strong"),
    ("ryo", 87, BOTH_P, PRETZEL, "MAX Haoh"),
    ("robert", 109, KICK_W, QCB2, "Haoh weak"),
    ("robert", 110, KICK_S, QCB2, "Haoh strong"),
    ("robert", 111, BOTH_K, QCB2, "MAX Haoh"),
    ("takuma", 111, WEAK, QCF2, "Haoh"),
)


def dirs(bits):
    out = set()
    for bit, button in ((1, 4), (2, 5), (4, 7), (8, 6)):
        if bits & bit:
            out.add(button)
    return out


def spark(core):
    raw = bytes(core.ram[SPARKS:SPARKS + SPK_SIZE])
    return {
        "x": struct.unpack_from("<H", raw, 0)[0],
        "anim": struct.unpack_from("<H", raw, 4)[0],
        "fidx": raw[6],
    }


def effect_cells(core):
    """Palette-2 OAM cells written by DrawSparks (sparks/projectiles)."""
    oam = bytes(core.ram[OAM:OAM + 512])
    return sum(1 for i in range(128)
               if (oam[i * 4 + 3] & 0x0E) == 4 and oam[i * 4 + 1] < 0xF0)


def press(core, direction, mask):
    btns = dirs(direction & 15)
    btns |= {v for k, v in BUTTONS.items() if mask & k}
    core.buttons[0] = btns
    core.step(2)
    core.buttons[0] = set()


def check(core, sid, button, motion, label):
    core.put(0x4000, 40 << 8)
    core.put(0x4040, 200 << 8)
    core.put(F_POWER, 5000)
    core.step(3)
    for direction, mask in motion:
        press(core, direction, mask)
    press(core, 0, button)

    entered = spawned = drawn = False
    spawn_frame = None
    xs, cells = [], []
    for i in range(400):
        core.step()
        state = core.ram[F_STATE]
        entered |= state == sid
        sp = spark(core)
        count = effect_cells(core)
        if sp["anim"]:
            if not spawned:
                spawned = True
                spawn_frame = core.ram[F_FRAME]
            xs.append(sp["x"])
            cells.append(count)
            drawn |= count >= 5
        elif entered and state == 0 and i > 40:
            break
    assert entered, f"{label}: sid {sid} was never entered"
    assert spawned, f"{label}: sid {sid} entered but no projectile"
    assert drawn, f"{label}: projectile never drew OAM cells ({cells})"
    assert spawn_frame and spawn_frame > 0, (
        f"{label}: shot fired on frame 0 (under the super flash)")
    travel = max(xs) - min(xs)
    assert travel >= 20, f"{label}: shot did not travel ({travel} px)"
    assert core.word(P2_HP) < 200, f"{label}: shot did not connect"
    print(f"PASS {label} (sid {sid}): frame {spawn_frame}, "
          f"{max(cells)} cells, {travel} px, "
          f"{200 - core.word(P2_HP)} dmg")


def main():
    core = Core(CORE, ROM)
    try:
        select = boot_select(core)
        for name, sid, button, motion, label in CASES:
            enter_fight(core, select, name, "kyo")
            check(core, sid, button, motion, f"{name} {label}")
        print("PASS: all Haoh Shikou Ken supers fire a visible projectile")
    finally:
        core.close()


if __name__ == "__main__":
    main()
