#!/usr/bin/env python3
"""Projectiles must leave early and link from a connected cr.HP.

Ryu's QCF+P Hadouken used to spawn on the penultimate animation frame; the
imported anim has long recovery frames, so the shot appeared ~35-40 ticks
after the special started and could never connect while the opponent was
still in cr.HP hitstun.  It now spawns on the third frame, and projectiles
may hit a victim that is still in S_HIT (but still not a knocked-down foe).
"""
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
F_STATE, FP2 = 0x4008, 0x40
F_X = 0x4000
HP2 = 0x4050
SPARKS = 0x4200
GROUND_Y = 190
DOWN, RIGHT = 5, 7
STRONG_P = 9    # SNES X -> MUGEN y (strong punch)
LIGHT_P = 1     # SNES Y -> MUGEN x (light punch)


def press(core, buttons, ticks=1):
    core.buttons[0] = set(buttons)
    core.step(ticks)
    core.buttons[0] = set()


def qcf_p(core):
    for d in ({DOWN}, {DOWN, RIGHT}, {RIGHT}):
        core.buttons[0] = set(d)
        core.step(1)
    press(core, {LIGHT_P}, 2)


def main():
    core = Core(CORE, ROM)
    try:
        sel = boot_select(core)

        # 1) release timing: third frame of the special, not the penultimate
        enter_fight(core, sel, "ryu", "kyo")
        core.put(F_X, 80 << 8)
        core.put(F_X + FP2, 200 << 8)
        core.step(20)
        qcf_p(core)
        shot = None
        shot_y = None
        for f in range(40):
            anim = struct.unpack_from("<H", core.ram, SPARKS + 4)[0]
            if anim and (core.ram[SPARKS + 15] & 0x80):
                shot = f
                shot_y = struct.unpack_from("<H", core.ram, SPARKS + 2)[0]
                break
            core.step()
        assert shot is not None, "QCF+P did not spawn a projectile"
        # The ProjFxTab header stores the spawn-height mode after both anim
        # pointers; reading the pointer byte instead put every primary shot
        # at the floor, so the hadouken travelled below the fighters' waists.
        assert shot_y == GROUND_Y - 40, f"Hadouken y={shot_y}, wanted {GROUND_Y - 40}"
        # qcf_p itself spends five frames on the motion/button
        assert shot <= 12, f"projectile took {shot}+5 frames (want <= 17)"
        print(f"OK Ryu Hadouken: shot {shot} frames after the input, "
              f"y={shot_y}")

        # 2) cr.HP -> shot link: the shot must add a second hit
        enter_fight(core, sel, "ryu", "kyo")
        core.put(F_X, 100 << 8)
        core.put(F_X + FP2, 140 << 8)
        core.step(20)
        hp0 = core.word(HP2)
        core.buttons[0] = {DOWN}
        core.step(4)
        press(core, {DOWN, STRONG_P}, 2)
        for _ in range(20):
            if core.word(HP2) != hp0:
                break
            core.step()
        hp1 = core.word(HP2)
        assert hp1 < hp0, "cr.HP did not connect"
        for _ in range(4):
            qcf_p(core)
            core.step(2)
        for _ in range(40):
            if core.word(HP2) < hp1:
                break
            core.step()
        hp2 = core.word(HP2)
        assert hp2 < hp1, f"shot did not link (hp {hp0}->{hp1}->{hp2})"
        print(f"OK cr.HP link: hp {hp0}->{hp1}->{hp2}")
        print("PASS fast projectile + cr.HP link")
    finally:
        core.close()


if __name__ == "__main__":
    main()
