#!/usr/bin/env python3
"""Yuki's Ai no Kusanagi: Kyo helper art, mirror-Kyo suppression, recovery.

The native engine has no MUGEN helper bodies, so Yuki's Kusanagi super rides
the pooled projectile slot (sid 89) with Kyo's AIR 1903 cel as the alternate
ProjFx clip.  These checks cover the three port-side rules:

  * the Kyo sprite is drawn for ordinary opponents (OAM gains its cells);
  * against Kyo / Kyo Nests / Kyo Ash the hitbox stays active but the
    duplicate Kyo body is suppressed (SPK_GRD bit1, no extra OAM cells);
  * anim 3300's source 255-tick tail no longer freezes Yuki for four
    seconds; the move returns to stand shortly after the attack.

Run after a PVSnesLib build:

    python3 tools/test_yuki_kusanagi_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_STATE = 0x4008
F_POWER = 0x4030
HP2 = 0x4050
OAMTOP = 0x102A
SPARKS = 0x4200
SPK_ANIM = 4
SPK_ATTR = 15
SPK_GRD = 18
SPK_SIZE = 20

DOWN, LEFT, RIGHT = 5, 6, 7
Y, X = 1, 9


def word(core, address):
    return core.ram[address] | core.ram[address + 1] << 8


def trigger_super(core):
    """D, B, D, F + Y+X (source SUP_AI_MAX, sid 89)."""
    core.put(F_POWER, 3000)
    core.step(4)
    for direction in ((DOWN,), (LEFT,), (DOWN,), (RIGHT,)):
        core.buttons[0] = set(direction)
        core.step(3)
    core.buttons[0] = {Y, X}
    core.step(4)
    core.buttons[0] = set()


def run_case(opponent):
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(core)
        enter_fight(core, select, "yuki", opponent)
        core.ram[0x1090] = 0             # human P1: drive the command ourselves
        core.ram[0x1091] = 0
        core.step(40)
        hp_before = word(core, HP2)
        trigger_super(core)

        pre_oam = 0
        active_oam = 0
        projectile_seen = False
        hidden = None
        recovery = None
        for tick in range(1, 220):
            core.step()
            if tick <= 90:
                pre_oam = max(pre_oam, word(core, OAMTOP))
            if 91 <= tick <= 116:
                active_oam = max(active_oam, word(core, OAMTOP))
            if word(core, SPARKS + SPK_ANIM):
                projectile_seen = True
                if hidden is None:
                    hidden = bool(word(core, SPARKS + SPK_GRD) & 0x0002)
            if core.ram[F_STATE] != 89 and tick > 10 and recovery is None:
                recovery = tick

        hp_after = word(core, HP2)
        assert projectile_seen, f"{opponent}: Kusanagi projectile never spawned"
        assert recovery is not None and 100 <= recovery <= 180, \
            f"{opponent}: recovery tick {recovery} (expected ~123)"
        assert hp_after < hp_before, \
            f"{opponent}: super did not connect ({hp_before}->{hp_after})"

        hidden_opponents = {"kyo", "kyonests", "kyoash"}
        if opponent in hidden_opponents:
            assert hidden is True, f"{opponent}: Kyo helper sprite not hidden"
            assert active_oam - pre_oam < 20, \
                (f"{opponent}: hidden helper still added OAM cells "
                 f"({pre_oam}->{active_oam})")
            print(f"PASS vs {opponent}: recovery={recovery}, "
                  f"invisible Kyo, super still hits {hp_before}->{hp_after}")
        else:
            assert hidden is False, f"{opponent}: Kyo helper sprite was hidden"
            assert active_oam - pre_oam >= 20, \
                (f"{opponent}: Kyo helper cells missing from OAM "
                 f"({pre_oam}->{active_oam})")
            print(f"PASS vs {opponent}: recovery={recovery}, "
                  f"Kyo sprite drawn (+{active_oam - pre_oam} OAM bytes), "
                  f"super hits {hp_before}->{hp_after}")
    finally:
        core.close()


def main():
    for opponent in ("mai", "kyo", "kyonests", "kyoash"):
        run_case(opponent)
    print("PASS: Yuki Kusanagi helper art, mirror-Kyo suppression and recovery")


if __name__ == "__main__":
    main()
