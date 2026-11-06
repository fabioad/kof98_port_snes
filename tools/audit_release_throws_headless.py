#!/usr/bin/env python3
"""Audit normal-throw capture, release, damage and recovery for the roster.

Reads inputs from the generated CmdTab/Mot tables and executes the shipping
ROM. A complete capture cycle does NOT certify the damage or visual fidelity.
Run with --hp 100 to expose TargetLifeAdd values that accidentally heal.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight
from test_roster import parse_tables
from normal_throws import PLANS

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
BUTTONS = {1: 1, 2: 9, 4: 0, 8: 8, 16: 10, 32: 11, 64: 3}
P1, P2 = 0x4000, 0x4040


def section(text, label):
    match = re.search(r"^" + re.escape(label)
                      + r":[^\n]*\n(.*?)(?=^\w[^\n]*:|\Z)",
                      text, re.M | re.S)
    return match.group(1) if match else ""


def throw_buttons(name, tables_dir):
    text = (tables_dir / f"{name}_spr.inc").read_text()
    combos = []
    for line in section(text, name + "CmdTab").splitlines():
        if ".db" not in line:
            continue
        values = [int(v.strip().replace("$", "0x"), 0)
                  for v in line.split(".db", 1)[1].split(",")]
        if len(values) != 7 or values[-1] != 74:
            continue
        motion = section(text, f"{name}Mot{values[0]}")
        tokens = re.findall(r"\.db (\d+),(\d+)", motion)
        if not tokens:
            raise ValueError(f"{name}: throw motion has no elements")
        mask = int(tokens[-1][1])
        buttons = frozenset(v for k, v in BUTTONS.items() if mask & k)
        if buttons not in combos:
            combos.append(buttons)
    return combos


def attempt(core, base, buttons, back, distance, hp, limit):
    core.load(base)
    core.buttons = [set(), set()]
    core.put(P1, 110 << 8)
    core.put(P2, (110 + distance) << 8)
    core.put(P1 + 16, 200)
    core.put(P2 + 16, hp)
    core.step(30)
    core.buttons[0] = set(buttons) | {6 if back else 7}
    states1, states2 = set(), set()
    grabbed = False
    released = recovered = None
    min_hp = max_hp = hp
    previous_hp = hp
    healing_observed = False
    for tick in range(limit):
        if tick == 3:
            core.buttons[0] = set()
        core.step()
        s1, s2 = core.ram[P1 + 8], core.ram[P2 + 8]
        states1.add(s1)
        states2.add(s2)
        held = s2 == 76 or bool(core.ram[P2 + 52] & 1)
        if held:
            grabbed = True
        if grabbed and not held and released is None:
            released = tick
        current_hp = core.word(P2 + 16)
        healing_observed |= current_hp > previous_hp
        previous_hp = current_hp
        min_hp = min(min_hp, current_hp)
        max_hp = max(max_hp, current_hp)
        if tick > 15 and s1 == 0 and s2 == 0:
            recovered = tick
            break
    return {
        "back": back, "distance": distance, "buttons": sorted(buttons),
        "grabbed": grabbed, "released": released, "recovered": recovered,
        "damage": hp - min_hp, "initial_hp": hp, "max_hp": max_hp,
        "final_hp": core.word(P2 + 16), "healed_above_initial": max_hp > hp,
        "final_damage": hp - core.word(P2 + 16),
        "healing_observed": healing_observed,
        "grab_flags_clear": not (core.ram[P1 + 52] or core.ram[P2 + 52]),
        "attacker_states": sorted(states1), "victim_states": sorted(states2),
        "cycle_complete": grabbed and released is not None and recovered is not None,
    }


def result_errors(name, result):
    """A captured victim is not a passing throw if the damage is lost later."""
    minimum = max(3, sum(hp for phase in PLANS.get(name, ())
                         for _element, hp in phase.hits))
    errors = []
    if not result.get("cycle_complete"):
        errors.append("capture/release/recovery incomplete")
    if result.get("final_damage", 0) < minimum:
        errors.append(f"final damage below {minimum} HP")
    if result.get("healing_observed"):
        errors.append("victim healed during throw")
    if not result.get("grab_flags_clear"):
        errors.append("grab flags not cleared")
    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    ap.add_argument("--tables", type=Path, default=ROOT / "build/gen_fight")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "build/release_audit_20261105/throws.json")
    ap.add_argument("--chars", nargs="+")
    ap.add_argument("--hp", type=int, default=200, choices=range(1, 201))
    ap.add_argument("--limit", type=int, default=600)
    args = ap.parse_args()
    names = args.chars or [r["name"] for r in parse_tables().values()]
    if args.limit < 1:
        ap.error("--limit must be positive")
    report = {
        "scope": "P1 normal throw vs idle Kyo; front/back; capture, damage, release, recovery",
        "limitations": "No visual equivalence, P2 input, mirrored starts or special-throw certification",
        "rom_sha256": hashlib.sha256(args.rom.read_bytes()).hexdigest(),
        "msu_sha256": (hashlib.sha256(args.rom.with_suffix('.msu').read_bytes()).hexdigest()
                       if args.rom.with_suffix('.msu').exists() else None),
        "core_sha256": hashlib.sha256(Path(args.core).read_bytes()).hexdigest(),
        "cases": [],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    core = Core(args.core, args.rom)
    try:
        select = boot_select(core)
        for name in names:
            enter_fight(core, select, name, "kyo")
            core.ram[0x1090] = core.ram[0x1091] = 0
            core.step(30)
            base = core.save()
            combos = throw_buttons(name, args.tables)
            for back in (False, True):
                attempts = []
                for distance in (25, 30, 20):
                    for buttons in combos:
                        result = attempt(core, base, buttons, back, distance,
                                         args.hp, args.limit)
                        attempts.append(result)
                        if result["cycle_complete"]:
                            break
                    if attempts and attempts[-1]["cycle_complete"]:
                        break
                result = attempts[-1] if attempts else {
                    "back": back, "cycle_complete": False,
                    "error": "No generated command targeting normal throw slot 74"}
                result = dict(result, character=name, other_attempts=attempts[:-1])
                result["errors"] = result_errors(name, result)
                report["cases"].append(result)
                args.out.write_text(json.dumps(report, indent=2) + "\n")
                status = "PASS" if not result["errors"] else "FAIL"
                print(status, name, "back" if back else "front",
                      "damage", result.get("damage"), "final HP", result.get("final_hp"),
                      "release", result.get("released"), flush=True)
    finally:
        core.close()
    print("Evidence:", args.out)
    return int(any(r["errors"] for r in report["cases"]))


if __name__ == "__main__":
    raise SystemExit(main())
