#!/usr/bin/env python3
"""Super and MAX hits use the source's bigger impact sparks.

The arcade changes the hit spark with the attack: s6001 for a normal hit,
+3 during MAX (s6004) and the s6002 family for supers.  The port keeps the
generic spark for normals and now picks SparkSuper / SparkMax from the
attacker's live chain (PowTab cost <= -1000) and F_MAX byte.  Projectiles
remember the launch tier in SPK_GRD bits 1-2 so a shot that outlives the
caster's super state still lands with the right spark.

Run after a PVSnesLib build:

    python3 tools/test_super_sparks_headless.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import (                 # noqa: E402
    boot_select, enter_fight, DOWN, RIGHT, X)

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
F_X, F_HP, F_POWER, F_MAX = 0x4000, 0x4010, 0x4030, 0x403B
F_STATE = 0x4008
FP2 = 0x40
SPARKS, SPK_SIZE = 0x4200, 20
SPK_ANIM = 4
WEAK_PUNCH = 1                            # libretro Y -> MUGEN x
SPARK_NAMES = ("SparkHit", "SparkSuper", "SparkMax")


def symbols():
    path = ROOT / "kof98-snes.symfull"
    if not path.exists():
        path = ROOT / "kof98-snes.sym"
    result = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) == 2:
            result[fields[1]] = int(fields[0], 16) & 0xFFFF
    return result


def live_spark(core, syms):
    """Return the name of a live hit/guard spark, or None."""
    by_addr = {syms[name]: name for name in SPARK_NAMES}
    for slot in range(2):
        base = SPARKS + slot * SPK_SIZE
        anim = core.word(base + SPK_ANIM)
        if anim in by_addr:
            return by_addr[anim]
    return None


def press(core, buttons, frames=2):
    core.buttons[0] = set(buttons)
    core.step(frames)
    core.buttons[0] = set()


def motion(core, seq, button):
    for direction in seq:
        press(core, direction, 2)
    core.buttons[0] = set(button)
    core.step(3)
    core.buttons[0] = set()
    core.step(1)


def clear_sparks(core):
    for slot in range(2):
        core.put(SPARKS + slot * SPK_SIZE + SPK_ANIM, 0)
    core.step(2)


def reset_positions(core):
    clear_sparks(core)
    # Let hitstun/knockback finish first: setting X before the victim is
    # idle lets the carried velocity push it out of the next punch's reach.
    for _ in range(120):
        if core.ram[F_STATE] == 0 and core.ram[F_STATE + FP2] == 0:
            break
        core.step()
    core.put(F_X, 90 << 8)
    core.put(F_X + FP2, 122 << 8)
    core.put(F_HP, 200)
    core.put(F_HP + FP2, 200)
    core.ram[F_MAX] = 0
    core.put(F_POWER, 0)
    core.step(6)


def wait_spark(core, syms, label, limit=240):
    for _ in range(limit):
        seen = live_spark(core, syms)
        if seen is not None:
            return seen
        core.step()
    raise AssertionError(f"{label}: no hit spark appeared")


def check_normal(core, syms):
    reset_positions(core)
    press(core, {WEAK_PUNCH})
    seen = wait_spark(core, syms, "normal hit")
    assert seen == "SparkHit", f"normal hit used {seen}, expected SparkHit"
    print("PASS normal hit -> SparkHit", flush=True)


def check_max(core, syms):
    reset_positions(core)
    core.ram[F_MAX] = 120                 # live MAX window
    core.step(1)
    press(core, {WEAK_PUNCH})
    seen = wait_spark(core, syms, "MAX hit")
    assert seen == "SparkMax", f"MAX hit used {seen}, expected SparkMax"
    core.ram[F_MAX] = 0
    print("PASS MAX hit -> SparkMax", flush=True)


def check_super(core, syms):
    reset_positions(core)
    core.put(F_POWER, 3000)
    core.step(5)
    # Kyo's QCFx2 + strong punch (Orochinagi).  The flame is a projectile,
    # so this also exercises the launch-tier bits read by SpawnProjImpact.
    motion(core, ((DOWN,), (DOWN, RIGHT), (RIGHT,),
                  (DOWN,), (DOWN, RIGHT), (RIGHT,)), (X,))
    seen = wait_spark(core, syms, "super hit", limit=360)
    assert seen == "SparkSuper", f"super hit used {seen}, expected SparkSuper"
    print("PASS super hit -> SparkSuper", flush=True)


def main(core_path, rom):
    core = Core(core_path, rom)
    syms = symbols()
    for name in SPARK_NAMES:
        if name not in syms:
            raise SystemExit(f"{name} missing from the symbol file; "
                             "run tools/build_fight.py first")
    failed = []
    try:
        select_state = boot_select(core)
        enter_fight(core, select_state, "kyo", "iori")
        for name, check in (("normal", check_normal),
                            ("max", check_max),
                            ("super", check_super)):
            try:
                check(core, syms)
            except AssertionError as exc:
                failed.append(f"{name}: {exc}")
    finally:
        core.close()
    if failed:
        raise AssertionError("; ".join(failed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", default=CORE)
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    args = parser.parse_args()
    main(args.core, args.rom)
