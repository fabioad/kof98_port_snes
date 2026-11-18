#!/usr/bin/env python3
"""Headless check: Kyo/Saisyu and Iori Yami Barai use the new two-frame art.

The external PNG art (tools/extract_yamibarai_art.py) is compiled by
build_fight.py into a two-page projectile clip that the engine loops while
the shot is alive.  This test fires the move on the real ROM and requires:

  * both clip frames (0 = small burst, 1 = tall burst) drawn as palette-2
    OAM cells;
  * at least 8 cells on each frame (the compiled clips hold 9 and 15);
  * the orange flame for Kyo and the violet one for Iori, measured on the
    emulator's video output.

Run after a PVSnesLib build (the .msu must sit next to the ROM):

    python3 tools/test_yamibarai_projectile_headless.py
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
SPARKS = 0x4200
OAM = 0x1800
START, A, DOWN, RIGHT = 3, 8, 5, 7
# SNES Y = MUGEN x (weak punch); SNES X = MUGEN y (strong punch).
WEAK, STRONG = 1, 9
SHOTS = ((48, WEAK, "weak"), (49, STRONG, "strong"))


def step_buttons(core, buttons, ticks=2):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def wait(core, pred, label, limit=8000):
    for _ in range(limit):
        if pred():
            return
        core.step()
    raise AssertionError(f"{label}: state={core.word(F_STATE)}")


def effect_cells(core):
    """Palette-2 OAM cells written by DrawSparks (sparks/projectiles)."""
    oam = bytes(core.ram[OAM:OAM + 512])
    return sum(1 for i in range(128) if (oam[i * 4 + 3] & 0x0E) == 4
               and oam[i * 4 + 1] < 0xF0)


def hue_pixels(core, want):
    """Count frame pixels in the orange or violet family."""
    width, height, pitch, raw, fmt = core.last_frame
    count = 0
    for y in range(80, height - 8, 2):
        row = y * pitch
        for x in range(16, width - 16, 2):
            if fmt == 1:                       # XRGB8888
                p = row + x * 4
                r, g, b = raw[p + 2], raw[p + 1], raw[p]
            else:                              # RGB565 / RGB555
                p = row + x * 2
                word = raw[p] | raw[p + 1] << 8
                if fmt == 2:
                    r, g, b = word >> 11 & 31, word >> 5 & 63, word & 31
                    r, g, b = r * 255 // 31, g * 255 // 63, b * 255 // 31
                else:
                    r, g, b = word >> 10 & 31, word >> 5 & 31, word & 31
                    r, g, b = r * 255 // 31, g * 255 // 31, b * 255 // 31
            if want == "orange":
                count += r > 150 and 60 < g < 210 and b < 110
            else:                     # violet / lavender
                count += r > 90 and b > 130 and b > g + 30 and r > g
    return count


def check_shots(core, hue):
    """Fire weak and strong Yami Barai and check the two-frame clip."""
    for sid, button, label in SHOTS:
        wait(core, lambda: core.word(F_STATE) == 0
             and core.word(0x4048) == 0, f"round start ({label})")
        core.step(40)      # let the round banner finish before input
        core.capture_video = True
        core.step()
        baseline = hue_pixels(core, hue)
        # QCF + punch; Kyo and Iori both use 236 + attack.
        for direction in ((DOWN,), (DOWN, RIGHT), (RIGHT,)):
            step_buttons(core, direction)
        step_buttons(core, {button})

        cells = {}
        peak = 0
        clip = None       # animation pointer of the spawned shot
        for _ in range(70):
            core.capture_video = True
            core.step()
            count = effect_cells(core)
            if count >= 8:
                anim = struct.unpack_from(
                    "<H", bytes(core.ram[SPARKS + 4:SPARKS + 6]))[0]
                clip = anim if clip is None else clip
                if anim == clip:
                    fidx = core.ram[SPARKS + 6]
                    cells[fidx] = max(count, cells.get(fidx, 0))
                    peak = max(peak, hue_pixels(core, hue))
            if cells and core.word(F_STATE) == 0:
                break
        core.capture_video = False
        assert cells, f"{label}: no projectile cells were drawn"
        assert {0, 1} <= set(cells), (label, sorted(cells))
        assert all(count >= 8 for count in cells.values()), (label, cells)
        assert peak > (baseline or 0) + 20, (label, hue, baseline, peak)
        print(f"PASS {label}: frames {sorted(cells)}, cells {cells}, "
              f"{hue} pixels {baseline}->{peak}")


def main():
    for p1, p2, hue in (("kyo", "iori", "orange"), ("iori", "kyo", "violet")):
        core = Core(CORE, ROM)
        try:
            enter_fight(core, boot_select(core), p1, p2)
            check_shots(core, hue)
        finally:
            core.close()
        print(f"PASS {p1} Yami Barai: two-frame {hue} burst")
    print("PASS: Kyo/Saisyu and Iori draw the new Yami Barai art")


if __name__ == "__main__":
    main()
