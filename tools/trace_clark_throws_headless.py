#!/usr/bin/env python3
"""Per-tick trace of Clark's grabs: attacker and held/thrown victim.

For every Clark grab (normal, specials, supers, MAX) this feeds the command
and logs, each tick: attacker state/frame/x/y/facing, victim
state/frame/anim/x/y and the victim offset relative to the attacker
(facing-relative dx, dy up = positive).  It then flags the motion defects
users report:

  * jump   -- victim moved more than --jump px in one tick while bound;
  * plateau-- victim stayed at the same bound offset for > --plateau ticks
              while the attacker animation kept advancing;
  * pose   -- victim animation frame never changed during a bound phase;
  * drop   -- victim left the bound slot while the attacker still owns a
              grab state.

Usage:
    python3 tools/trace_clark_throws_headless.py [--victim kyo] [--p2]
        [--x 110] [--json out.json] [--case "Ultra Argentine weak"]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                    # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight  # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040
F_X, F_Y, F_VX, F_VY, F_STATE, F_FRAME = 0, 2, 4, 6, 8, 10
F_FACING, F_HP, F_ANIM, F_GRAB, F_POWER = 14, 16, 18, 52, 48

UP, DOWN, LEFT, RIGHT = 4, 5, 6, 7
Y, X, PHYS_B, PHYS_A, L = 1, 9, 0, 8, 10      # MUGEN y/x/a/b and C

HELD_STATES = {76, 100, 102}


def dirs(fwd_right):
    f, b = (RIGHT, LEFT) if fwd_right else (LEFT, RIGHT)
    return {
        "F": frozenset({f}), "B": frozenset({b}), "D": frozenset({DOWN}),
        "DF": frozenset({DOWN, f}), "DB": frozenset({DOWN, b}),
    }


def motion(names, fwd_right):
    d = dirs(fwd_right)
    return tuple(d[n] for n in names.split())


HCF = "B DB D DF F"
HCB = "F DF D DB B"
DP = "F D DF"

# name, motion, buttons, gap (px), normal throw?
CASES = (
    ("Normal throw", "F", {Y}, 20, True),
    ("Mount Tackle weak", HCF, {X}, 30, False),
    ("Super Argentine weak", HCF, {PHYS_B}, 22, False),
    ("Frankensteiner weak", DP, {PHYS_B}, 30, False),
    ("Napalm Stretch weak", DP, {X}, 30, False),
    ("Ultra Argentine weak", HCB + " " + HCB, {X}, 18, False),
    ("Ultra Argentine MAX", HCB + " " + HCB, {X, Y}, 18, False),
    ("Running Three weak", HCF + " " + HCF, {PHYS_B}, 60, False),
    ("Running Three strong", HCF + " " + HCF, {PHYS_A}, 60, False),
    ("Running Three MAX", HCF + " " + HCF, {L}, 60, False),
)


def s16(v):
    return v - 0x10000 if v & 0x8000 else v


def snap(core, base):
    return {
        "state": core.ram[base + F_STATE],
        "frame": core.ram[base + F_FRAME],
        "anim": core.word(base + F_ANIM),
        "nfr": core.ram[base + 20],
        "ftick": core.ram[base + 12],
        "x": core.word(base + F_X) / 256.0,
        "y": s16(core.word(base + F_Y)) / 256.0,
        "vx": s16(core.word(base + F_VX)) / 256.0,
        "vy": s16(core.word(base + F_VY)) / 256.0,
        "facing": 1 if s16(core.word(base + F_FACING)) >= 0 else -1,
        "grab": core.ram[base + F_GRAB],
        "hp": core.word(base + F_HP),
    }


def run_case(core, base, case, p2side, x0, limit):
    label, mot, buttons, gap, _normal = case
    att, vic = (P2, P1) if p2side else (P1, P2)
    pad = 1 if p2side else 0
    core.load(base)
    core.buttons = [set(), set()]
    if p2side:
        core.put(P2 + F_X, x0 << 8)
        core.put(P1 + F_X, (x0 - gap) << 8)
    else:
        core.put(P1 + F_X, x0 << 8)
        core.put(P2 + F_X, (x0 + gap) << 8)
    core.put(att + F_POWER, 3000)
    core.put(P1 + F_HP, 200)
    core.put(P2 + F_HP, 200)
    core.step(20)
    fwd_right = snap(core, att)["facing"] > 0
    steps = motion(mot, fwd_right)
    for tok in steps:
        core.buttons[pad] = set(tok)
        core.step(2)
    core.buttons[pad] = set(steps[-1]) | set(buttons)
    core.step(2)
    core.buttons[pad] = set()
    rows = []
    grabbed = False
    for t in range(limit):
        core.step()
        a, v = snap(core, att), snap(core, vic)
        held = v["state"] in HELD_STATES
        grabbed |= held
        rows.append({
            "t": t, "a": a, "v": v, "held": held,
            "dx": round((v["x"] - a["x"]) * a["facing"], 2),
            "dy": round(v["y"] - a["y"], 2),
        })
        if grabbed and t > 20 and a["state"] == 0 and v["state"] in (0, 10, 12):
            break
    return rows


def analyse(rows, jump, plateau):
    issues = []
    bound = [r for r in rows if r["held"]]
    if not bound:
        return ["no grab"], {}
    prev = None
    run = 0
    for r in rows:
        if prev is not None and r["held"] and prev["held"]:
            ddx = abs(r["v"]["x"] - prev["v"]["x"])
            ddy = abs(r["v"]["y"] - prev["v"]["y"])
            if ddx > jump or ddy > jump:
                issues.append(
                    f"t{r['t']}: jump dx={r['v']['x'] - prev['v']['x']:+.0f} "
                    f"dy={r['v']['y'] - prev['v']['y']:+.0f} "
                    f"(att st{r['a']['state']} fr{r['a']['frame']})")
            same = (r["dx"], r["dy"]) == (prev["dx"], prev["dy"])
            if same and r["dy"] > 0:
                run += 1
                if run == plateau + 1:
                    issues.append(
                        f"t{r['t']}: plateau at dy={r['dy']:+.0f} "
                        f"for >{plateau} ticks (att st{r['a']['state']})")
            else:
                run = 0
        if prev is not None and prev["held"] and not r["held"]:
            issues.append(f"t{r['t']}: release -> victim st{r['v']['state']} "
                          f"vx={r['v']['vx']:+.2f} vy={r['v']['vy']:+.2f} "
                          f"(att st{r['a']['state']} fr{r['a']['frame']})")
        prev = r
    # Pose per attacker state while bound.
    poses = {}
    for r in bound:
        poses.setdefault(r["a"]["state"], set()).add(
            (r["v"]["anim"], r["v"]["frame"]))
    peak = max(r["dy"] for r in bound)
    summary = {
        "bound_ticks": len(bound),
        "peak_dy": peak,
        "victim_poses_per_attacker_state": {k: len(v) for k, v in poses.items()},
        "victim_anims": sorted({r["v"]["anim"] for r in bound}),
        "attacker_states": sorted({r["a"]["state"] for r in rows}),
        "victim_states": sorted({r["v"]["state"] for r in rows}),
        "damage": rows[0]["v"]["hp"] - rows[-1]["v"]["hp"],
    }
    return issues, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    ap.add_argument("--victim", default="kyo")
    ap.add_argument("--p2", action="store_true", help="Clark on P2")
    ap.add_argument("--x", type=int, default=110)
    ap.add_argument("--case", action="append")
    ap.add_argument("--jump", type=float, default=24.0)
    ap.add_argument("--plateau", type=int, default=12)
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--rows", action="store_true", help="print every tick")
    args = ap.parse_args()
    core = Core(CORE, args.rom)
    report = {}
    try:
        sel = boot_select(core)
        p1, p2 = ((args.victim, "clark") if args.p2
                  else ("clark", args.victim))
        enter_fight(core, sel, p1, p2)
        core.ram[0x1090] = core.ram[0x1091] = 0
        core.step(20)
        base = core.save()
        for case in CASES:
            if args.case and case[0] not in args.case:
                continue
            rows = run_case(core, base, case, args.p2, args.x, args.limit)
            issues, summary = analyse(rows, args.jump, args.plateau)
            report[case[0]] = {"summary": summary, "issues": issues,
                               "rows": rows}
            print(f"== {case[0]}  {json.dumps(summary)}")
            for i in issues:
                print("   ", i)
            if args.rows:
                for r in rows:
                    a, v = r["a"], r["v"]
                    print(f"   t{r['t']:3d} A st{a['state']:3d} fr{a['frame']:2d} "
                          f"x{a['x']:6.1f} y{a['y']:5.1f} f{a['facing']:+d} | "
                          f"V st{v['state']:3d} an{v['anim']:5d} fr{v['frame']:2d} "
                          f"x{v['x']:6.1f} y{v['y']:5.1f} g{v['grab']} "
                          f"| dx{r['dx']:+6.1f} dy{r['dy']:+6.1f}")
    finally:
        core.close()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
