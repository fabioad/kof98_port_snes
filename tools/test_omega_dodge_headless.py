#!/usr/bin/env python3
"""Omega Rugal's Fusion evades: L rolls and the neutral dodge.

The source CMD had the ESQ_L/ESQ_F/ESQ_B [Command] blocks but no State -1
rules, and the reduced move table only carried placeholder slots 94/95/69.
Omega reuses his existing emergency-evasion clips plus a port-added
in-place 720 pose:
  * L + forward -> sid 95 / state 1010, forward clip
  * L + back    -> sid 94 / state 1011, back clip
  * Y + B       -> sid 69 / state 720 (the standard DODGE input)
  * L alone     -> neutral dodge (all characters now use this slot).

The CMD targets are also checked against the generated animation table:
state 1010 must use the forward clip, 1011 the back clip, and the neutral
dodge must not fall back to the taunt animation.

Run after a PVSnesLib build:

    python3 tools/test_omega_dodge_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
ROM = ROOT / "kof98-snes.sfc"
SYM = ROOT / "kof98-snes.sym"
F_STATE = 0x4008
F_ANIM = 0x4012
L, FWD, BACK, Y, B = 10, 7, 6, 1, 0


def symbol_offset(label):
    """Low 16 bits of a generated animation label (F_ANIM is bank-relative)."""
    for line in SYM.read_text().splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] == label:
            return int(fields[0], 16) & 0xFFFF
    raise AssertionError(f"{label} missing from {SYM.name}")


def run(directions, buttons, wanted, character="omegarugal"):
    core = Core(CORE, str(ROM))
    try:
        select = boot_select(core)
        enter_fight(core, select, character, "kyo")
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.step(30)
        held = set().union(*directions) if directions else set()
        for d in held:
            core.buttons[0] = {d}
            core.step(3)
        core.buttons[0] = held | set(buttons)
        core.step(3)
        core.buttons[0] = set()
        seen = []
        anim_at_wanted = None
        for _ in range(50):
            core.step()
            state = core.ram[F_STATE]
            if state == wanted and anim_at_wanted is None:
                anim_at_wanted = core.word(F_ANIM)
            if not seen or seen[-1] != state:
                seen.append(state)
            if state == 0 and len(seen) > 1:
                break
        return seen, anim_at_wanted
    finally:
        core.close()


def main():
    fwd_anim = symbol_offset("omegarugalAnim95")
    back_anim = symbol_offset("omegarugalAnim69")
    taunt_anim = symbol_offset("omegarugalAnim47")
    assert fwd_anim != back_anim, "forward and back clips must differ"

    seen, anim = run((frozenset({FWD}),), (L,), 95)
    assert 95 in seen, f"L+forward did not roll ({seen})"
    assert anim == fwd_anim, (
        f"L+forward used animation ${anim:04X}, expected forward ${fwd_anim:04X}")
    print("PASS Omega L+forward -> forward roll (sid 95, forward clip)")

    seen, anim = run((frozenset({BACK}),), (L,), 94)
    assert 94 in seen, f"L+back did not roll ({seen})"
    assert anim == back_anim, (
        f"L+back used animation ${anim:04X}, expected back ${back_anim:04X}")
    print("PASS Omega L+back -> back roll (sid 94, back clip)")

    seen, anim = run((), (Y, B), 69)
    assert 69 in seen, f"DODGE did not start ({seen})"
    assert anim == back_anim, (
        f"DODGE used animation ${anim:04X}, expected neutral ${back_anim:04X}")
    print("PASS Omega DODGE (Y+B) -> neutral dodge (sid 69)")

    seen, anim = run((), (L,), 69)
    assert 69 in seen, f"L alone did not dodge ({seen})"
    assert anim == back_anim, (
        f"L alone used animation ${anim:04X}, expected neutral ${back_anim:04X}")
    assert anim != taunt_anim, "L alone fell back to the taunt animation"
    print("PASS Omega L alone -> neutral dodge (sid 69, not taunt)")

    seen, _ = run((), (L,), 69, "kyo")
    assert 69 in seen, f"other characters lost the L-alone dodge ({seen})"
    print("PASS other characters use L alone -> neutral dodge (sid 69)")


if __name__ == "__main__":
    main()
