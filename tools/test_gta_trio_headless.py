#!/usr/bin/env python3
"""GTA tribute trio (Jason, John, Lucia): selection, normals, specials, supers.

Covers the three roster additions end to end on the real ROM:

  * each character locks on its select cell (the new row above
    Shingo/Rugal/Eiji) and enters a fight;
  * a normal attack deals damage;
  * a quarter-circle special reaches the special sids (48..66);
  * the double-motion super reaches the super sids (85..89), spending
    power, including the MAX variant (87/89) in MAX mode.

Run after a PVSnesLib build:

    python3 tools/test_gta_trio_headless.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1_STATE, P1_X, P1_POWER, P1_MAX = 0x4008, 0x4000, 0x4030, 0x403B
P2_X, P2_HP = 0x4040, 0x4050
VOICE_BUSY, VOICE_LEFT = 0x15A, 0x158
DOWN, LEFT, RIGHT = 5, 6, 7
X, Y, A, B = 9, 1, 8, 0

# MUGEN motions in pad order.  QCFx2 covers Jason/Lucia; John's source super
# is the 641236 half-circle-back + forward string.
QCF = ((DOWN,), (DOWN, RIGHT), (RIGHT,))
DP = ((RIGHT,), (DOWN,), (DOWN, RIGHT))
QCF2 = ((DOWN,), (DOWN, RIGHT), (RIGHT,),
        (DOWN,), (DOWN, RIGHT), (RIGHT,))
QCB2 = ((DOWN,), (DOWN, LEFT), (LEFT,),
        (DOWN,), (DOWN, LEFT), (LEFT,))
HCB_F = ((RIGHT,), (LEFT,), (DOWN, LEFT), (DOWN,), (DOWN, RIGHT),
         (RIGHT,))
WEAK_PUNCH, WEAK_KICK = 1, 0

SPECIAL_RANGE = range(48, 67)
SUPER_RANGE = range(85, 90)


def press(core, dirs, frames=2):
    core.buttons[0] = set(dirs)
    core.step(frames)


def motion(core, sequence, buttons):
    for dirs in sequence:
        press(core, dirs)
    core.buttons[0] = set(buttons)
    core.step(3)
    core.buttons[0] = set()


def start(select, char, opponent="geese"):
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    enter_fight(core, select, char, opponent)
    core.ram[0x1090] = 0
    core.ram[0x1091] = 0
    core.put(P1_X, 150 << 8)
    core.put(P2_X, 168 << 8)
    core.step(20)
    return core


def run_move(select, char, sequence, buttons, power=0, max_mode=0):
    core = start(select, char)
    try:
        if power:
            core.put(P1_POWER, power)
        if max_mode:
            core.ram[P1_MAX] = max_mode
        core.step(2)
        hp0 = core.word(P2_HP)
        before = core.word(P1_POWER)
        motion(core, sequence, buttons)
        seen = set()
        for _ in range(140):
            core.step()
            seen.add(core.ram[P1_STATE])
        return {"states": seen,
                "damage": hp0 - core.word(P2_HP),
                "spent": before - core.word(P1_POWER)}
    finally:
        core.close()


def voice_stream(select, char):
    """Sample the streamed-voice counter during a normal attack."""
    core = start(select, char)
    try:
        core.ram[0x1090] = 0
        core.ram[0x1091] = 0
        counters = []
        for tick in range(45):
            core.buttons[0] = {Y} if tick < 2 else set()
            core.step()
            if core.ram[VOICE_BUSY] or core.word(VOICE_LEFT):
                counters.append(core.word(VOICE_LEFT))
        return counters
    finally:
        core.close()


def main():
    probe = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        select = boot_select(probe)
    finally:
        probe.close()

    fails = []
    cases = {
        # grab: normal command-grab super (88); the MAX variant (89) uses
        # the both-button form.  Jason grabs with punches, Lucia with kicks.
        "jason": {"special": QCF, "super": QCF2,
                  "grab_seq": QCB2, "grab": (WEAK_PUNCH,),
                  "grab_max": (X, Y)},
        "john": {"special": QCF, "super": HCB_F,
                 "grab_seq": HCB_F, "grab": (WEAK_KICK,),
                 "grab_max": (A, B)},
        "lucia": {"special": QCF, "super": QCF2,
                  "grab_seq": QCB2, "grab": (WEAK_KICK,),
                  "grab_max": (A, B)},
    }
    for char, moves in cases.items():
        normal = run_move(select, char, ((RIGHT,),), (X,))
        if normal["states"] & {5, 6, 7, 8} == set() or normal["damage"] <= 0:
            fails.append(f"{char}: normal did not connect ({normal})")

        voices = voice_stream(select, char)
        if len(voices) < 4 or voices[0] <= voices[-1]:
            fails.append(f"{char}: attack voice did not stream ({voices})")

        special = run_move(select, char, moves["special"], (X,))
        if not special["states"] & set(SPECIAL_RANGE):
            fails.append(f"{char}: special state missing ({special})")
        if special["damage"] <= 0:
            fails.append(f"{char}: special did no damage ({special})")

        super_ = run_move(select, char, moves["super"], (X,), power=3000)
        if not super_["states"] & set(SUPER_RANGE):
            fails.append(f"{char}: super state missing ({super_})")
        if super_["damage"] <= 0:
            fails.append(f"{char}: super did no damage ({super_})")
        if super_["spent"] <= 0:
            fails.append(f"{char}: super spent no power ({super_})")

        maximum = run_move(select, char, moves["super"], (X, Y),
                           power=3000, max_mode=200)
        if not maximum["states"] & {87, 89}:
            fails.append(f"{char}: MAX super state missing ({maximum})")
        if maximum["damage"] <= 0:
            fails.append(f"{char}: MAX super did no damage ({maximum})")

        grab = run_move(select, char, moves["grab_seq"], moves["grab"],
                        power=3000)
        if 88 not in grab["states"]:
            fails.append(f"{char}: command grab state missing ({grab})")
        if grab["damage"] < 30:
            fails.append(f"{char}: command grab did only "
                         f"{grab['damage']} HP ({grab})")

        grab_max = run_move(select, char, moves["grab_seq"],
                            moves["grab_max"], power=3000, max_mode=200)
        if 89 not in grab_max["states"]:
            fails.append(f"{char}: MAX command grab state missing "
                         f"({grab_max})")
        if grab_max["damage"] < 40:
            fails.append(f"{char}: MAX command grab did only "
                         f"{grab_max['damage']} HP ({grab_max})")

        print(f"{char}: normal {normal['damage']} HP, "
              f"special {special['damage']} HP, "
              f"super {super_['damage']} HP, "
              f"MAX {maximum['damage']} HP, "
              f"grab {grab['damage']} HP, "
              f"MAX grab {grab_max['damage']} HP")

    # Jason's strong Cold Hook (DP + strong) must connect at point-blank
    # against a narrow hurtbox (Mai).  It used to drift past the source
    # hitbox and whiff while only the weak version connected.
    strong_core = start(select, "jason", "mai")
    try:
        strong_core.ram[0x1090] = 0
        strong_core.ram[0x1091] = 0
        strong_core.put(P1_X, 150 << 8)
        strong_core.put(P2_X, 160 << 8)
        strong_core.step(20)
        before = strong_core.word(P2_HP)
        motion(strong_core, DP, (X,))
        for _ in range(70):
            strong_core.step()
        close_damage = before - strong_core.word(P2_HP)
    finally:
        strong_core.close()
    if close_damage <= 0:
        fails.append(f"jason: strong anti-air whiffed point-blank on Mai "
                     f"({close_damage} HP)")

    if fails:
        for fail in fails:
            print("FAIL:", fail)
        return 1
    print("PASS GTA trio: Jason, John and Lucia select, fight, "
          "special, super and MAX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
