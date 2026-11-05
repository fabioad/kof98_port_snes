#!/usr/bin/env python3
"""Benimaru's specials and supers must connect at point-blank range.

Several imported moves put their HitDef in a follow-up state or in a
Helper (Handou Sandan 1501/1511, the Raikouken supers 3000/3010/3050) while
the command entered the intro/pose state.  The strong Raikouken also
spawned above a standing victim's hurtbox.  This regression fires every
wired special/super from 8 px away and requires real damage.

Run after a PVSnesLib build:

    python3 tools/test_benimaru_close_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
F_STATE = 0x4008
F_HP = 0x4010
F_X = 0x4000
FP2 = 0x40

DOWN, LEFT, RIGHT = 5, 6, 7
X, Y, A, B_BTN = 1, 9, 0, 8

D = frozenset({DOWN})
F = frozenset({RIGHT})
B = frozenset({LEFT})
DF = frozenset({DOWN, RIGHT})
DB = frozenset({DOWN, LEFT})
QCF = (D, DF, F)
QCB = (D, DB, B)
DP = (F, D, DF)
RDP = (B, D, DB)
QQCF = (D, DF, F, D, DF, F)
HCB2 = (F, DF, D, DB, B, F, DF, D, DB, B)
QCBHCF = (D, DB, B, DB, D, DF, F)
HCBF = (F, DF, D, DB, B, F)

# (label, motion, buttons, expected state, minimum damage)
CASES = (
    ("Raikouken weak", QCF, {X}, 48, 10),
    ("Raikouken strong", QCF, {Y}, 49, 10),
    ("Iai Geri weak", QCF, {A}, 60, 10),
    ("Iai Geri strong", QCF, {B_BTN}, 61, 10),
    ("Shinkuu Katategoma", RDP, {A}, 52, 10),
    ("Super Inazuma", DP, {A}, 54, 10),
    ("Handou Sandan weak", QCB, {A}, 58, 10),
    ("Handou Sandan strong", QCB, {B_BTN}, 59, 10),
    ("Raikouken super weak", QQCF, {X}, 85, 20),
    ("Raikouken super strong", QQCF, {Y}, 86, 20),
    ("Raikouken MAX", HCB2, {X, Y}, 87, 30),
    ("Electro Trigger", QCBHCF, {X}, 89, 10),
    ("Benimaru Collider", HCBF, {X}, 62, 10),
    ("Raiko Katategoma", QQCF, {A}, 66, 10),
    ("Electro Trigger MAX", HCB2, {X}, 88, 20),
)


def run_case(label, motion, buttons, want, min_damage, distance):
    core = Core(CORE, ROM)
    try:
        select = boot_select(core)
        enter_fight(core, select, "benimaru", "kyo")
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, (100 + distance) << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        core.put(F_X + 0x30, 4000)             # power for supers
        core.step(30)
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, (100 + distance) << 8)
        core.put(F_HP, 200)
        core.put(F_HP + FP2, 200)
        hp0 = core.word(F_HP + FP2)
        for d in motion:
            core.buttons[0] = set(d)
            core.step(3)
        core.buttons[0] = set(buttons)
        core.step(3)
        core.buttons[0] = set()
        seen = set()
        damage = 0
        for _ in range(220):
            core.step()
            seen.add(core.ram[F_STATE])
            damage = max(damage, hp0 - core.word(F_HP + FP2))
            if core.ram[F_STATE] == 0 and core.ram[F_STATE + FP2] == 0:
                break
        assert want in seen, f"{label}: state {want} never started ({seen})"
        assert damage >= min_damage, (
            f"{label} at {distance}px: only {damage} damage")
        return damage
    finally:
        core.close()


def main():
    for label, motion, buttons, want, minimum in CASES:
        damage = run_case(label, motion, buttons, want, minimum, 8)
        print(f"PASS {label:28s} point-blank {damage:3d} damage")
    # The projectile and the remapped kick must still reach at range.
    for label, motion, buttons, want in (
            ("Raikouken strong far", QCF, {Y}, 49),
            ("Handou Sandan far", QCB, {A}, 58)):
        damage = run_case(label, motion, buttons, want, 10, 80)
        print(f"PASS {label:28s} far        {damage:3d} damage")
    print("PASS Benimaru specials/supers connect at point-blank range")


if __name__ == "__main__":
    main()
