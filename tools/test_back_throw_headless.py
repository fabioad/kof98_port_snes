#!/usr/bin/env python3
"""Street Fighter II-style back throw for every fighter with a normal throw.

Holding back + the throw button at grab time now turns both fighters around:
the same throw animation plays mirrored and the victim is carried to the
opposite side, then keeps sliding horizontally away from the thrower.  This
test covers a normal holdfwd/back throw, a forward-only source command
(Yuri's THROW_Y), an x+y throw (Ryu) and a grappler (King).

Run after a PVSnesLib build:

    python3 tools/test_back_throw_headless.py
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                          # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
FP1, FP2 = 0x4000, 0x4040
F_STATE, F_X, F_Y, F_VX, F_FACING, F_HP = 8, 0, 2, 4, 14, 0x10
F_TFLAGS = 51
F_GRAB = 52
BACK_BIT = 0x20
LEFT, RIGHT = 6, 7

# libretro X = mugen y (strong punch); Y = mugen x.  Ryu/Terry/Robert use the
# source's x+y throw, the rest use a single strong punch.
CHAR_BUTTONS = {
    "yuri": (9,),
    "iori": (9,),
    "king": (9,),
    "benimaru": (9,),
    "ryu": (9, 1),
    "chizuru": (9,),
}


def run_throw(core_path, rom, char, back, p1x=100, p2x=125):
    """Return a dict describing one throw attempt.

    p1x < p2x means P1 starts on the left and faces right.  The mirrored case
    passes p1x > p2x and still uses `back=True` (the held direction is away
    from the foe).
    """
    core = Core(core_path, rom)
    try:
        select = boot_select(core)
        enter_fight(core, select, char, "kyo")
        core.ram[0x1090] = 0                  # both pads human: no CPU AI
        core.ram[0x1091] = 0
        core.put(FP1, p1x << 8)
        core.put(FP2, p2x << 8)
        core.put(FP2 + F_HP, 200)
        core.step(30)

        # P1 starts left of P2, so back is LEFT; mirrored, back is RIGHT.
        hold = RIGHT if back and p1x > p2x else LEFT if back else \
            LEFT if p1x > p2x else RIGHT
        core.buttons[0] = {hold, *CHAR_BUTTONS[char]}
        core.step(3)
        core.buttons[0] = set()

        grabbed = False
        released = None
        facing = None
        flag_at_grab = None
        x_at_grab = None
        x_at_release = None
        vx_at_release = None
        x_after = None
        a_release = None
        a_after = None
        y_peak = 0
        dmg_peak = 0
        for tick in range(180):
            core.step()
            s1 = core.ram[FP1 + F_STATE]
            s2 = core.ram[FP2 + F_STATE]
            if s1 == 75 and s2 == 76 and not grabbed:
                grabbed = True
                facing = core.word(FP1 + F_FACING)
                if facing & 0x8000:
                    facing -= 0x10000
                flag_at_grab = core.ram[FP1 + F_TFLAGS]
                x_at_grab = core.word(FP1) / 256.0
            if grabbed and s2 != 76 and released is None:
                released = tick
                x_at_release = core.word(FP2) / 256.0
                vx = core.word(FP2 + F_VX)
                if vx & 0x8000:
                    vx -= 0x10000
                vx_at_release = vx / 256.0
            if released is not None and tick == released + 20:
                x_after = core.word(FP2) / 256.0
                a_after = core.word(FP1) / 256.0
            if released is not None and released == tick:
                a_release = core.word(FP1) / 256.0
            if released is not None:
                y_peak = max(y_peak, core.word(FP2 + F_Y) / 256.0)
            dmg_peak = max(dmg_peak, 200 - core.word(FP2 + F_HP))
        return {
            "grabbed": grabbed,
            "released": released,
            "facing": facing,
            "flag_at_grab": flag_at_grab,
            "flag_after": core.ram[FP1 + F_TFLAGS],
            "x_grab": x_at_grab,
            "x_release": x_at_release,
            "vx_release": vx_at_release,
            "x_after": x_after,
            "a_release": a_release,
            "a_after": a_after,
            "y_peak": y_peak,
            "damage": dmg_peak,
        }
    finally:
        core.close()


def check_char(core_path, rom, char):
    fwd = run_throw(core_path, rom, char, back=False)
    back = run_throw(core_path, rom, char, back=True)
    mirror = run_throw(core_path, rom, char, back=True, p1x=150, p2x=125)

    for tag, r in (("forward", fwd), ("back", back), ("mirror", mirror)):
        assert r["grabbed"], f"{char} {tag}: throw never grabbed"
        assert r["released"] is not None, f"{char} {tag}: victim never released"
        assert r["x_after"] is not None, f"{char} {tag}: no post-release sample"

    # Forward throw: attacker keeps its facing, victim stays in front.
    assert fwd["facing"] == 1, f"{char} forward facing {fwd['facing']}"
    assert fwd["flag_at_grab"] & BACK_BIT == 0, \
        f"{char} forward throw marked as a back throw"
    assert fwd["x_release"] > fwd["x_grab"], \
        f"{char} forward victim did not stay in front ({fwd})"
    assert fwd["vx_release"] > 1.0, \
        f"{char} forward throw did not launch the victim away ({fwd})"
    assert fwd["y_peak"] > 4.0, \
        f"{char} forward victim never went airborne ({fwd})"

    # Back throw: both turned, victim crosses to the other side and slides.
    assert back["facing"] == -1, f"{char} back facing {back['facing']}"
    assert back["flag_at_grab"] & BACK_BIT, \
        f"{char} back throw did not set the direction flag"
    assert back["x_release"] < back["x_grab"], \
        f"{char} back victim did not cross behind ({back})"
    assert back["vx_release"] < -0.1, \
        f"{char} back victim did not move away ({back})"
    # A throw released near the wall now bounces instead of sticking, so
    # require visible horizontal travel and a legal on-screen landing.
    assert abs(back["x_after"] - back["x_release"]) > 1.0, \
        f"{char} back victim did not slide horizontally ({back})"
    assert 24.0 <= back["x_after"] <= 232.0, \
        f"{char} back victim left the stage ({back})"
    assert back["y_peak"] > 4.0, \
        f"{char} back victim never went airborne ({back})"
    assert back["flag_after"] & BACK_BIT == 0, \
        f"{char} back-throw flag leaked after release"

    # Mirrored back throw: the same geometry reflected around the attacker.
    assert mirror["facing"] == 1, f"{char} mirror facing {mirror['facing']}"
    assert mirror["flag_at_grab"] & BACK_BIT, \
        f"{char} mirror throw did not set the direction flag"
    assert mirror["x_release"] > mirror["x_grab"], \
        f"{char} mirror victim did not cross behind ({mirror})"
    assert mirror["vx_release"] > 0.1, \
        f"{char} mirror victim did not move away ({mirror})"
    assert abs(mirror["x_after"] - mirror["x_release"]) > 1.0, \
        f"{char} mirror victim did not slide horizontally ({mirror})"
    assert 24.0 <= mirror["x_after"] <= 232.0, \
        f"{char} mirror victim left the stage ({mirror})"

    # Same animation and damage in both directions.
    assert back["damage"] == fwd["damage"], (
        f"{char} back throw damage {back['damage']} != forward "
        f"{fwd['damage']}")
    assert mirror["damage"] == fwd["damage"], (
        f"{char} mirrored damage {mirror['damage']} != forward "
        f"{fwd['damage']}")

    print(f"PASS {char}: forward {fwd['damage']} HP; back +{back['damage']} HP "
          f"({back['x_release']:.0f}->{back['x_after']:.0f}px), "
          f"mirror {mirror['x_release']:.0f}->{mirror['x_after']:.0f}px",
          flush=True)


def check_chizuru(core_path, rom):
    """Chizuru's source grab uses a zero TargetBind and moves the attacker;
    the deferred wrong-side re-seat must still put the victim behind her."""
    fwd = run_throw(core_path, rom, "chizuru", back=False)
    back = run_throw(core_path, rom, "chizuru", back=True)
    mirror = run_throw(core_path, rom, "chizuru", back=True, p1x=150, p2x=125)
    for tag, r in (("forward", fwd), ("back", back), ("mirror", mirror)):
        assert r["grabbed"], f"chizuru {tag}: throw never grabbed"
        assert r["released"] is not None, f"chizuru {tag}: no release"
    # The zero bind is corrected two ticks after release, so compare the
    # settled position (release + 20) with the attacker's position.
    assert back["x_after"] < back["a_after"], (
        f"chizuru back victim not behind: {back}")
    assert back["x_after"] < back["x_release"], (
        f"chizuru back victim did not keep sliding: {back}")
    assert mirror["x_after"] > mirror["a_after"], (
        f"chizuru mirror victim not behind: {mirror}")
    assert mirror["x_after"] > mirror["x_release"], (
        f"chizuru mirror victim did not keep sliding: {mirror}")
    assert back["damage"] == fwd["damage"] == mirror["damage"], (
        f"chizuru damage mismatch: {fwd['damage']}/"
        f"{back['damage']}/{mirror['damage']}")
    print(f"PASS chizuru zero-bind grab: back behind at "
          f"{back['x_release']:.0f}px, mirror at {mirror['x_release']:.0f}px",
          flush=True)


def main(core_path, rom):
    for char in ("yuri", "iori", "king", "benimaru", "ryu"):
        check_char(core_path, rom, char)
    check_chizuru(core_path, rom)
    print("PASS all sampled fighters: SF2-style back throw")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = ap.parse_args()
    main(args.core, args.rom)
