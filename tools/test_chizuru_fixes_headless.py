#!/usr/bin/env python3
"""Regression for the Chizuru fixes.

Covers:
  * the QCB clone rise rises/falls like Ryu's weak/strong Shoryuken and no
    longer spends 216 ticks on the source's 30/15-tick holds;
  * the DP and RDP specials accept both the weak and the strong button;
  * the clone-dance super walks forward and lands several contacts;
  * the crouched one-hand super advances about half a screen;
  * both light and strong inputs reach the same super variants.

Run after a PVSnesLib build:

    python3 tools/test_chizuru_fixes_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_X1 = FP1
F_Y1 = FP1 + 2
F_STATE1, F_STATE2 = FP1 + 8, FP2 + 8
F_HP2 = FP2 + 0x10
F_POWER1 = FP1 + 0x30
COMBO = 0x4FC0

DOWN, RIGHT, LEFT = 5, 7, 6
X_BTN, Y_BTN, A_BTN, B_BTN = 9, 1, 8, 0
D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
DB = frozenset({DOWN, LEFT})
F = frozenset({RIGHT})
B = frozenset({LEFT})
QCF = (D, DF, F)
QCB = (D, DB, B)


def feed(core, steps, button, hold=3):
    for direction in steps:
        core.buttons[0] = set(direction)
        core.step(hold)
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()


def measure(rom, steps, button, ticks=650, hold=3):
    core = Core(CORE, rom)
    saw = []
    peak = 0
    p2 = []
    combo = 0
    try:
        select = boot_select(core)
        enter_fight(core, select, "chizuru", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(FP1, 82 << 8)
        core.put(FP2, 100 << 8)
        core.put(F_HP2, 200)
        core.put(F_POWER1, 3000)
        core.step(30)
        x0 = core.word(F_X1)
        feed(core, steps, button, hold)
        end = None
        for i in range(ticks):
            core.step()
            state = core.ram[F_STATE1]
            victim = core.ram[F_STATE2]
            if not saw or saw[-1] != state:
                saw.append(state)
            if not p2 or p2[-1] != victim:
                p2.append(victim)
            peak = max(peak, core.word(F_Y1))
            combo = max(combo, core.ram[COMBO])
            if state == 0 and len(saw) > 1 and i > 40:
                end = i
                break
        return {
            "states": saw,
            "p2": p2,
            "peak": peak / 256.0,
            "dx": (core.word(F_X1) - x0) / 256.0,
            "damage": 200 - core.word(F_HP2),
            "combo": combo,
            "end": end,
        }
    finally:
        core.close()


def main():
    rom = ROOT / "kof98-snes.sfc"

    weak = measure(rom, QCB, Y_BTN)
    strong = measure(rom, QCB, X_BTN)
    assert 50 in weak["states"], f"QCB weak state missing: {weak['states']}"
    assert 51 in strong["states"], f"QCB strong state missing: {strong['states']}"
    assert 20.0 < weak["peak"] < 45.0, (
        f"QCB weak rise {weak['peak']:.1f}px, want 20..45")
    assert 55.0 < strong["peak"] < 100.0, (
        f"QCB strong rise {strong['peak']:.1f}px, want 55..100")
    assert weak["damage"] >= 12 and strong["damage"] >= 12, (
        f"QCB damage {weak['damage']}/{strong['damage']}")
    assert weak["end"] is not None and weak["end"] < 120, (
        f"QCB weak still slow: end={weak['end']}")
    assert strong["end"] is not None and strong["end"] < 120, (
        f"QCB strong still slow: end={strong['end']}")
    print(f"PASS Chizuru QCB: weak {weak['peak']:.0f}px, "
          f"strong {strong['peak']:.0f}px, "
          f"{weak['end']}/{strong['end']} ticks")

    for label, button in (("weak", Y_BTN), ("strong", X_BTN)):
        dp = measure(rom, (F, D, DF), button)
        assert 52 in dp["states"], f"DP {label} missing: {dp['states']}"
        assert dp["peak"] > 40.0, f"DP {label} rise {dp['peak']:.1f}px"
        assert dp["damage"] >= 12, f"DP {label} damage {dp['damage']}"
        rdp = measure(rom, (B, D, DB), button)
        assert 56 in rdp["states"], f"RDP {label} missing: {rdp['states']}"
        assert rdp["damage"] >= 12, f"RDP {label} damage {rdp['damage']}"
    print("PASS Chizuru specials: DP and RDP accept weak and strong")

    dance = measure(rom, QCF + QCF, Y_BTN)
    assert 85 in dance["states"], f"dance missing: {dance['states']}"
    assert dance["dx"] >= 60.0, f"dance only moved {dance['dx']:.1f}px"
    assert dance["combo"] >= 6, f"dance combo only {dance['combo']}"
    assert dance["damage"] >= 40, f"dance damage only {dance['damage']}"
    print(f"PASS Chizuru dance: {dance['combo']} hits, "
          f"{dance['damage']} damage, {dance['dx']:.0f}px forward")

    crouch = measure(rom, QCF + QCF, X_BTN)
    assert 86 in crouch["states"], f"crouched super missing: {crouch['states']}"
    assert 105.0 <= crouch["dx"] <= 160.0, (
        f"crouched super advanced {crouch['dx']:.1f}px, want ~128")
    assert crouch["damage"] >= 40, f"crouched damage {crouch['damage']}"
    print(f"PASS Chizuru crouched super: {crouch['dx']:.0f}px, "
          f"{crouch['damage']} damage")

    hcb = (F, DF, D, DB, B)
    hcb_weak = measure(rom, hcb, Y_BTN)
    hcb_strong = measure(rom, hcb, X_BTN)
    assert 54 in hcb_weak["states"], f"HCB weak missing: {hcb_weak['states']}"
    assert 55 in hcb_strong["states"], (
        f"HCB strong missing: {hcb_strong['states']}")
    assert hcb_weak["dx"] >= 20.0, (
        f"HCB weak did not advance: {hcb_weak['dx']:.1f}px")
    assert hcb_strong["peak"] > 15.0, (
        f"HCB strong did not jump: {hcb_strong['peak']:.1f}px")
    assert hcb_weak["damage"] >= 12 and hcb_strong["damage"] >= 12, (
        f"HCB damage {hcb_weak['damage']}/{hcb_strong['damage']}")
    print(f"PASS Chizuru HCB: weak {hcb_weak['dx']:.0f}px forward, "
          f"strong jumps {hcb_strong['peak']:.0f}px")

    slow = measure(rom, QCF + QCF, Y_BTN, hold=4)
    assert 85 in slow["states"], (
        f"slow QCFx2 did not reach the dance: {slow['states']}")
    single = measure(rom, QCF, Y_BTN)
    assert 48 in single["states"] and 85 not in single["states"], (
        f"single QCF should stay the normal special: {single['states']}")
    print("PASS Chizuru dance input: 4-frame cadence and single-QCF fallback")

    light = measure(rom, QCF + QCF, B_BTN)      # MUGEN a
    heavy = measure(rom, QCF + QCF, A_BTN)      # MUGEN b
    assert 85 in light["states"], f"QCFx2+a reached {light['states']}"
    assert 86 in heavy["states"], f"QCFx2+b reached {heavy['states']}"
    assert 87 in measure(rom, QCB + QCB, Y_BTN)["states"]
    assert 87 in measure(rom, QCB + QCB, X_BTN)["states"]
    print("PASS Chizuru supers: light/strong and a/b inputs all wired")
    print("PASS Chizuru fixes")


if __name__ == "__main__":
    main()
