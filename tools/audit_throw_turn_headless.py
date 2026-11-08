#!/usr/bin/env python3
"""Roster-wide throw victim position/orientation audit.

For every roster entry this performs the normal throw front and back and
checks:

* the victim is launched in the direction the thrower faces;
* entries whose source victim state carries a ``Turn`` flip the victim on
  the mapped frame (TargetState entry frame + AnimElem - 1).

The Turn list is derived from the source CNS, not hardcoded, so the audit
stays honest when the roster or source packages change.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight
from test_roster import parse_tables
from audit_release_throws_headless import throw_buttons

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040


def s16(value):
    """Sign-extend a 16-bit emulator word."""
    return value - 0x10000 if value & 0x8000 else value


def source_turns(names):
    """name -> [(victim state, absolute bind frame), ...]."""
    import build_fight as bf

    out = {}
    for name in names:
        cfg = bf.CHARS.get(name)
        if cfg is None:
            continue
        vals = bf.parse_cns(
            bf.asset_path(cfg["cns"]), 1, cfg.get("damage_scale", 1),
            char=name, char_scale=bf.char_scale_for(name, cfg))
        moves, _posadds, _powadds, _headers, statedefs, _binds, acts = vals[:7]
        attempt = cfg.get("moves", {}).get(74)
        row = moves.get(attempt)
        if not row or not row.get("throw"):
            continue
        p1 = row.get("p1mugen", -1)
        if p1 < 0:
            continue
        own = acts.get(p1, ())
        targets = []
        for ctrl in statedefs.get(p1, ()):
            if ctrl.get("type", "").lower() != "targetstate":
                continue
            raw = ctrl.get("value", "").split(",")[0].strip()
            try:
                targets.append(int(float(raw)))
            except ValueError:
                pass
        rows = []
        for state in targets:
            entry = 0
            for frame, op, arg, _cond in own:
                if op == 4 and arg == state:
                    entry = int(frame)
                    break
            for ctrl in statedefs.get(state, ()):
                if ctrl.get("type", "").lower() != "turn":
                    continue
                for trigger in ctrl.get("triggers", ()):
                    m = re.search(r"\banimelem\s*=\s*(\d+)", trigger, re.I)
                    if m:
                        rows.append((state, entry + int(m.group(1)) - 1))
                        break
        if rows:
            out[name] = rows
    return out


def attempt(core, base, buttons, back, distance, limit):
    core.load(base)
    core.buttons = [set(), set()]
    core.put(P1, 110 << 8)
    core.put(P2, (110 + distance) << 8)
    core.put(P1 + 16, 200)
    core.put(P2 + 16, 200)
    core.step(30)
    core.buttons[0] = set(buttons) | {6 if back else 7}

    grab = release = None
    x_grab = None
    facing = None
    changes = []
    att_facing_release = None
    vx_release = None
    face_release = None
    for tick in range(limit):
        if tick == 3:
            core.buttons[0] = set()
        core.step()
        s2 = core.ram[P2 + 8]
        held = s2 == 76 or bool(core.ram[P2 + 52] & 1)
        if held and grab is None:
            grab = tick
            x_grab = core.word(P2)
            facing = core.word(P2 + 14)
        if held:
            now = core.word(P2 + 14)
            if now != facing:
                changes.append((core.ram[P1 + 10], now))
                facing = now
        if grab is not None and not held and release is None:
            release = tick
            att_facing_release = core.word(P1 + 14)
            vx_release = core.word(P2 + 4)
            face_release = core.word(P2 + 14)
            x_release = core.word(P2)
        if release is not None and tick > release + 12:
            break
    if grab is None or release is None:
        return None
    return {
        "buttons": sorted(buttons),
        "back": back,
        "distance": distance,
        "grab": grab,
        "release": release,
        "dx": (x_release - x_grab) / 256.0,
        "attacker_facing": s16(att_facing_release),
        "victim_facing": s16(face_release),
        "vx": s16(vx_release) / 256.0,
        "facing_changes": [(frame, s16(face)) for frame, face in changes],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", default=CORE)
    ap.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    ap.add_argument("--tables", type=Path, default=ROOT / "build/gen_fight")
    ap.add_argument("--chars", nargs="+")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "build/throw_turn_roster_audit.json")
    ap.add_argument("--limit", type=int, default=280)
    args = ap.parse_args()

    roster = {r["name"] for r in parse_tables().values()}
    names = args.chars or sorted(roster)
    turns = source_turns(names)
    core = Core(args.core, args.rom)
    report = {"rom": str(args.rom), "cases": [], "failures": []}
    try:
        select = boot_select(core)
        for name in names:
            try:
                enter_fight(core, select, name, "kyo")
            except AssertionError as exc:
                report["failures"].append(f"{name}: select {exc}")
                print("FAIL", name, "select", exc, flush=True)
                continue
            core.ram[0x1090] = core.ram[0x1091] = 0
            core.step(30)
            base = core.save()
            combos = throw_buttons(name, args.tables) or [frozenset()]
            for back in (False, True):
                result = None
                for distance in (25, 30, 20):
                    for buttons in combos:
                        result = attempt(core, base, buttons, back, distance,
                                         args.limit)
                        if result is not None:
                            break
                    if result is not None:
                        break
                if result is None:
                    report["failures"].append(f"{name}: no {'back' if back else 'front'} throw")
                    print("FAIL", name, "back" if back else "front",
                          "no throw", flush=True)
                    continue
                dx = result["dx"]
                # The launch velocity is the throw direction.  Net dx also
                # includes the bind's repositioning during the hold and can
                # point the other way for cross-body throws.
                throw_dir = (1 if result["vx"] > 0
                             else -1 if result["vx"] < 0 else 0)
                dir_ok = throw_dir != 0 and throw_dir == (
                    1 if result["attacker_facing"] > 0 else -1)
                expected = turns.get(name, ())
                turn_ok = None
                turn_seen = None
                if expected:
                    want_frames = {f for _st, f in expected}
                    seen = [f for f, _face in result["facing_changes"]]
                    turn_seen = result["facing_changes"]
                    turn_ok = (any(abs(f - want) <= 1
                                   for f in seen for want in want_frames)
                               and result["victim_facing"] == throw_dir)
                entry = dict(result, character=name, throw_dir=throw_dir,
                             dir_ok=dir_ok, expected_turns=expected,
                             turn_ok=turn_ok)
                report["cases"].append(entry)
                if not dir_ok or turn_ok is False:
                    msg = (f"{name} {'back' if back else 'front'}: "
                           f"dx={dx:+.1f} vx={result['vx']:+.1f} "
                           f"att_face={result['attacker_facing']} "
                           f"vic_face={result['victim_facing']} "
                           f"changes={result['facing_changes']} "
                           f"expected={expected}")
                    report["failures"].append(msg)
                    print("FAIL", msg, flush=True)
                else:
                    print("PASS", name, "back" if back else "front",
                          f"dx={dx:+.1f}", "turn" if turn_ok else "-",
                          flush=True)
    finally:
        core.close()
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print("failures:", len(report["failures"]), "evidence:", args.out)
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
