#!/usr/bin/env python3
"""Projectile cancels must be true combos from a strong normal.

A connected standing or crouching strong punch must cancel into the
character's projectile and the shot must land while the victim is still in
hitstun, so the combo counter reaches 2.  This covers the shoto-style QCF+P
fighters (Ryu, Ken, Sakura, Ryo, Robert, Takuma and Yuri) with both the weak
and the strong projectile button.

The shot must also leave on the third frame and sit at the caster's torso
height, not at the floor.

Run after a PVSnesLib build:

    python3 tools/test_projectile_speed_combo_headless.py
"""
import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE, F_HITDONE = 0x4008, 0x401A
F_X, F_HP = 0x4000, 0x4010
FP2 = 0x40
COMBO = 0x4FC0
SPARKS = 0x4200
GROUND_Y = 190
DOWN, RIGHT = 5, 7
STRONG_P = 9    # SNES X -> MUGEN y (strong punch)
LIGHT_P = 1     # SNES Y -> MUGEN x (light punch)

SHOTOS = ("ryu", "ken", "sakura", "ryo", "robert", "takuma", "yuri")


def press(core, buttons, ticks=1):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def qcf_p(core, button):
    for direction in ({DOWN}, {DOWN, RIGHT}, {RIGHT}):
        core.buttons[0] = set(direction)
        core.step(3)
    press(core, {button}, 2)


def connect_strong_punch(core, crouch):
    hp0 = core.word(F_HP + FP2)
    if crouch:
        core.buttons[0] = {DOWN}
        core.step(4)
        press(core, {DOWN, STRONG_P}, 2)
    else:
        press(core, {STRONG_P}, 2)
    for _ in range(20):
        if core.ram[F_STATE] in (6, 20) and core.word(F_HP + FP2) < hp0:
            break
        core.step()
    else:
        return None, None
    hp1 = core.word(F_HP + FP2)
    for _ in range(40):
        if core.ram[0x1073] == 0:
            break
        core.step()
    return hp0, hp1


def check_shot_combo(core, select_state, name, crouch, button, label):
    enter_fight(core, select_state, name, "kyo")
    core.put(F_X, 100 << 8)
    core.put(F_X + FP2, 135 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.step(20)
    hp0, hp1 = connect_strong_punch(core, crouch)
    if hp0 is None:
        raise AssertionError(f"{name} {'crouch' if crouch else 'stand'}: "
                             "strong punch did not connect")
    qcf_p(core, button)
    peak = 0
    landed = False
    for _ in range(90):
        core.step()
        peak = max(peak, core.ram[COMBO])
        if core.word(F_HP + FP2) < hp1:
            landed = True
    if not landed:
        raise AssertionError(f"{name} {'crouch' if crouch else 'stand'} "
                             f"{label}: projectile did not hit")
    if peak < 2:
        raise AssertionError(
            f"{name} {'crouch' if crouch else 'stand'} {label}: shot hit "
            f"after hitstun (combo peak {peak})")
    print(f"PASS {name:8} {'crouch' if crouch else 'stand':6} {label}: "
          f"strong punch -> shot = {peak} HITS", flush=True)


def check_hitstop_buffer(core, select_state):
    """A motion entered while the hit is frozen must still cancel."""
    enter_fight(core, select_state, "ryu", "kyo")
    core.put(F_X, 100 << 8)
    core.put(F_X + FP2, 135 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.step(20)
    hp0 = core.word(F_HP + FP2)
    press(core, {STRONG_P}, 2)
    for _ in range(20):
        if core.ram[F_STATE] == 6 and core.word(F_HP + FP2) < hp0:
            break
        core.step()
    else:
        raise AssertionError("hitstop-buffer: strong punch did not connect")
    if core.ram[0x1073] == 0:
        raise AssertionError("hitstop-buffer: hitstop already over")
    qcf_p(core, LIGHT_P)              # entirely inside the hitstop
    peak = 0
    landed = False
    for _ in range(90):
        core.step()
        peak = max(peak, core.ram[COMBO])
        if core.word(F_HP + FP2) < hp0:
            landed = True
    if not landed or peak < 2:
        raise AssertionError(
            f"hitstop-buffer: combo peak {peak}, landed={landed}")
    print(f"PASS motion buffered during hitstop: {peak} HITS", flush=True)


def check_release_timing(core, select_state):
    enter_fight(core, select_state, "ryu", "kyo")
    core.put(F_X, 80 << 8)
    core.put(F_X + FP2, 200 << 8)
    core.step(20)
    qcf_p(core, LIGHT_P)
    shot = None
    shot_y = None
    for frame in range(40):
        anim = struct.unpack_from("<H", core.ram, SPARKS + 4)[0]
        if anim and (core.ram[SPARKS + 15] & 0x80):
            shot = frame
            shot_y = struct.unpack_from("<H", core.ram, SPARKS + 2)[0]
            break
        core.step()
    if shot is None:
        raise AssertionError("QCF+P did not spawn a projectile")
    if shot_y != GROUND_Y - 40:
        raise AssertionError(
            f"Hadouken y={shot_y}, wanted {GROUND_Y - 40}")
    # qcf_p itself spends eleven frames on the motion/button
    if shot > 18:
        raise AssertionError(
            f"projectile took {shot}+11 frames (want <= 29)")
    print(f"PASS Ryu Hadouken: shot {shot} frames after the input, "
          f"y={shot_y}", flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    try:
        select_state = boot_select(core)
        check_hitstop_buffer(core, select_state)
        check_release_timing(core, select_state)
        for name in SHOTOS:
            for crouch in (False, True):
                for button, label in ((LIGHT_P, "weak shot"),
                                      (STRONG_P, "strong shot")):
                    check_shot_combo(core, select_state, name, crouch,
                                     button, label)
                    core.buttons = [set(), set()]
                    core.step(20)
        print("PASS every projectile shoto links strong punch into a shot",
              flush=True)
    finally:
        core.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
