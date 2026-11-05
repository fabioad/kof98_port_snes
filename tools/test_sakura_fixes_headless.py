#!/usr/bin/env python3
"""Headless regression for the Sakura fixes.

Covers:
  * forward + strong punch now performs the throw (state 800 -> 810) and the
    choke holds the victim inside Sakura's reach;
  * Sakura Otoshi's jump-in complement (x/y during the rise -> 1320/1325);
  * Shinkuu Hadouken (QCFx2 + punch -> 3000/3010) launches a real projectile;
  * Shun Goku Satsu on strong kick (QCF+b -> 3300/3305/3306), 15-hit combo,
    black cinematic screen and the back-turned finale (no taunt).

Run after a PVSnesLib build:

    python3 tools/test_sakura_fixes_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE1, F_STATE2 = FP1 + 8, FP2 + 8
F_NFR1 = FP1 + 20
F_HP2 = FP2 + 0x10
F_POWER = FP1 + 0x30
COMBO = 0x4FC0
SPARKS = 0x4200
SPK_SIZE = 20
SPK_ANIM = 4

DOWN, RIGHT = 5, 7
Y, X, B_BTN, A_BTN = 1, 9, 0, 8
D = frozenset({DOWN})
DF = frozenset({DOWN, RIGHT})
F = frozenset({RIGHT})
QCF = (D, DF, F)
DP = (F, D, DF)
VHELD = 76
THROW = 75
SGS_FINISH = 113
TAUNT = 47


def press(core, buttons, ticks=3):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def motion(core, steps, button, keep_last=False):
    last = set()
    for direction in steps:
        core.buttons[0] = set(direction)
        last = set(direction)
        core.step(2)
    core.buttons[0] = (last if keep_last else set()) | set(button)
    core.step(3)
    core.buttons[0] = set()


def brightness(core, box=(32, 32, 224, 190)):
    w, h, pitch, data, fmt = core.last_frame
    x0, y0, x1, y1 = box
    total = 0
    count = 0
    step = 4 if fmt == 1 else 2
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            off = y * pitch + x * step
            value = int.from_bytes(data[off:off + step], "little")
            if fmt == 1:
                r, g, b = (value >> 16) & 255, (value >> 8) & 255, value & 255
            elif fmt == 2:
                r = ((value >> 11) & 31) * 255 // 31
                g = ((value >> 5) & 63) * 255 // 63
                b = (value & 31) * 255 // 31
            else:
                r = ((value >> 10) & 31) * 255 // 31
                g = ((value >> 5) & 31) * 255 // 31
                b = (value & 31) * 255 // 31
            total += r + g + b
            count += 1
    return total / (3 * count)


def start(core, select_state):
    enter_fight(core, select_state, "sakura", "kyo")
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.put(FP1, 82 << 8)
    core.put(FP2, 100 << 8)
    core.put(F_HP2, 200)
    core.put(F_POWER, 3000)
    core.step(20)
    core.put(FP1, 82 << 8)
    core.put(FP2, 100 << 8)
    core.put(F_POWER, 3000)
    core.step(20)


def collect(core, ticks):
    states = []
    p2 = []
    hp_min = core.word(F_HP2)
    combo = 0
    finish_frames = set()
    for _ in range(ticks):
        core.step()
        s1 = core.ram[F_STATE1]
        s2 = core.ram[F_STATE2]
        if not states or states[-1] != s1:
            states.append(s1)
        if not p2 or p2[-1] != s2:
            p2.append(s2)
        if s1 == SGS_FINISH:
            finish_frames.add(core.ram[F_NFR1])
        hp_min = min(hp_min, core.word(F_HP2))
        combo = max(combo, core.ram[COMBO])
    return states, p2, hp_min, combo, finish_frames


def main():
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select_state = boot_select(core)

        # --- forward + strong punch throw ----------------------------------
        start(core, select_state)
        hp0 = core.word(F_HP2)
        motion(core, (F,), {X}, keep_last=True)
        states, p2, hp_min, _, _ = collect(core, 120)
        assert THROW in states, f"throw bind state never played: {states}"
        assert VHELD in p2, f"victim was not held during the throw: {p2}"
        assert hp0 - hp_min >= 5, (
            f"throw dealt only {hp0 - hp_min} damage")
        print(f"PASS Sakura throw: states={states[:6]}, "
              f"damage={hp0 - hp_min}")

        # Re-run and sample the choke spacing: the victim must sit inside
        # Sakura's reaching arm (about 10 px), not at the grab distance.
        start(core, select_state)
        motion(core, (F,), {X}, keep_last=True)
        gaps = []
        held = []
        for _ in range(110):
            core.step()
            if core.ram[F_STATE1] == THROW and core.ram[F_STATE2] == VHELD:
                gap = abs(core.word(FP2) - core.word(FP1)) / 256.0
                gaps.append(gap)
        assert gaps, "throw/choke states were never sampled"
        assert min(gaps) >= 6 and max(gaps) <= 14, (
            f"choke spacing out of range: {min(gaps):.1f}..{max(gaps):.1f}px")
        print(f"PASS Sakura choke: victim centred at "
              f"{sum(gaps) / len(gaps):.1f}px")

        # --- Shinkuu Hadouken projectile ------------------------------------
        start(core, select_state)
        core.put(FP1, 60 << 8)
        core.put(FP2, 200 << 8)
        core.put(F_HP2, 200)
        core.put(F_POWER, 3000)
        core.step(10)
        hp0 = core.word(F_HP2)
        for _ in range(2):                  # QCF x2
            for direction in QCF:
                core.buttons[0] = set(direction)
                core.step(3)
        core.buttons[0] = {X}               # strong punch -> 3010 (sid 86)
        core.step(3)
        core.buttons[0] = set()
        states = []
        shot = False
        hp_min = hp0
        for _ in range(150):
            core.step()
            state = core.ram[F_STATE1]
            if not states or states[-1] != state:
                states.append(state)
            if any(core.ram[SPARKS + k * SPK_SIZE + 15] & 0x80
                   for k in range(2)):
                shot = True
            hp_min = min(hp_min, core.word(F_HP2))
        assert 85 in states or 86 in states, (
            f"Shinkuu Hadouken state never played: {states}")
        assert shot, f"Shinkuu Hadouken launched no projectile: {states}"
        assert hp0 - hp_min == 34, (
            f"Shinkuu Hadouken should be one 34 HP contact, "
            f"got {hp0 - hp_min}")
        print(f"PASS Sakura Shinkuu Hadouken: states={states[:6]}, "
              f"damage={hp0 - hp_min}")

        # --- Sakura Otoshi jump-in complement -------------------------------
        start(core, select_state)
        hp0 = core.word(F_HP2)
        motion(core, DP, {B_BTN})
        core.step(12)
        press(core, {Y})
        states, p2, hp_min, _, _ = collect(core, 180)
        assert 65 in states, f"Otoshi air follow-up never played: {states}"
        assert 66 in states, f"Otoshi landing state never played: {states}"
        assert hp0 - hp_min >= 4, (
            f"Otoshi follow-up dealt only {hp0 - hp_min} damage")
        print(f"PASS Sakura Otoshi complement: states={states[:8]}, "
              f"damage={hp0 - hp_min}")

        # --- Shun Goku Satsu on strong kick ---------------------------------
        start(core, select_state)
        hp0 = core.word(F_HP2)
        core.capture_video = True
        core.step(2)
        before = brightness(core)
        motion(core, QCF, {A_BTN})
        pre = []
        for _ in range(120):
            core.step()
            state = core.ram[F_STATE1]
            if not pre or pre[-1] != state:
                pre.append(state)
            if state == 112:
                break
        assert core.ram[F_STATE1] == 112, (
            f"Shun Goku Satsu never reached 3305: {core.ram[F_STATE1]}")
        core.step(8)
        during = brightness(core)
        states, p2, hp_min, combo, finish_frames = collect(core, 220)
        merged = []
        for state in pre + states:
            if not merged or merged[-1] != state:
                merged.append(state)
        states = merged
        core.step(2)
        after = brightness(core)
        assert 114 in states, f"SGS root never played: {states}"
        assert 113 in states, f"SGS finisher never played: {states}"
        assert TAUNT not in states, f"SGS still drops into the taunt: {states}"
        assert finish_frames == {1}, (
            "SGS finale must hold the single back-turned cel, "
            f"finisher frames={sorted(finish_frames)}")
        assert VHELD in p2, f"victim was not held during the SGS: {p2}"
        assert hp0 - hp_min >= 45, (
            f"SGS dealt only {hp0 - hp_min} damage")
        assert combo == 15, f"SGS combo peaked at {combo}, expected 15"
        assert during < 2.0, f"cinematic screen was not black ({during:.1f})"
        assert before > 10.0 and after > 10.0, (
            f"screen did not return after the cinematic "
            f"({before:.1f} -> {during:.1f} -> {after:.1f})")
        print(f"PASS Sakura Shun Goku Satsu (strong kick): states={states}, "
              f"combo={combo}, damage={hp0 - hp_min}, "
              f"brightness={before:.0f}/{during:.0f}/{after:.0f}")
    finally:
        core.close()
    print("PASS Sakura: throw, Otoshi complement and Shun Goku Satsu")


if __name__ == "__main__":
    main()
