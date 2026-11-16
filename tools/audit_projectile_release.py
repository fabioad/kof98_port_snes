#!/usr/bin/env python3
"""Audit the native projectile rows: speed, damage and launch timing.

The SNES engine spawns a shot when the fighter reaches a specific frame of
the launch animation (ProjTrySpawn in src/engine/fight.asm).  The frame is
stored in the high five bits of the ProjTab "present" byte.  When no frame is
stored the engine falls back to the third frame, which is early for most
imported KOF98 animations.

This tool compares the effective release frame of every generated ProjTab row
with the source CNS controller that actually starts the projectile:

* a direct ``type = Projectile`` controller in the root state;
* a root ``Helper`` whose child state owns a Projectile controller;
* a root ``Helper`` whose child is a travelling HitDef helper (the port
  stores those in the projectile pool as well);
* a ``ChangeState`` that enters a projectile state on an explicit AnimElem.

Only the first step in the ROOT animation is reported: the engine does not
simulate helper bodies, so the release must happen on the visible launch
animation.  Helper-internal delays are deliberately not added.

Usage:
    python3 tools/audit_projectile_release.py
    python3 tools/audit_projectile_release.py --json build/proj_audit.json
    python3 tools/audit_projectile_release.py ryu robert takuma
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_fight  # noqa: E402
from calibration.projectiles import (  # noqa: E402
    PROJECTILE_ALT_EFFECTS,
    PROJECTILE_RELEASE,
)

OUT = ROOT / "build" / "gen_fight"
DEFAULT_FRAME = 2  # ProjTrySpawn: third frame, 0-based


def _number(value):
    value = str(value).strip().strip('"')
    try:
        return int(value, 0)
    except ValueError:
        return None


def _triggers(ctrl):
    return [str(v) for k, v in ctrl.items() if k.startswith("trigger")]


def _controller_frame(ctrl):
    """Return the first AnimElem (0-based) or literal Time of a controller."""
    elems = []
    times = []
    for trig in _triggers(ctrl):
        for m in re.finditer(r"AnimElem\s*=\s*(\d+)", trig, re.I):
            elems.append(max(0, int(m.group(1)) - 1))
        for m in re.finditer(
                r"AnimElemTime\s*\(\s*(\d+)\s*\)\s*>=\s*0", trig, re.I):
            elems.append(max(0, int(m.group(1)) - 1))
        m = re.match(r"\s*Time\s*=\s*(\d+)\s*$", trig, re.I)
        if m:
            times.append(int(m.group(1)))
    if elems:
        return min(elems)
    if times:
        return max(times)
    return None


def _has_type(statedefs, state, wanted, depth=0, seen=None):
    """True when state or a helper/changestate child has a controller type."""
    if seen is None:
        seen = set()
    if state is None or state in seen or depth > 4:
        return False
    seen.add(state)
    for ctrl in statedefs.get(state, []):
        typ = ctrl.get("type", "").lower()
        if typ == wanted:
            return True
        if typ in ("helper", "changestate"):
            child = _number(ctrl.get("stateno", ctrl.get("value", "")))
            if _has_type(statedefs, child, wanted, depth + 1, seen):
                return True
    return False


def _has_hitdef_with_velocity(statedefs, state):
    """A travelling source hit helper used as a pooled shot by the port."""
    for ctrl in statedefs.get(state, []):
        typ = ctrl.get("type", "").lower()
        if typ == "hitdef":
            if any(k.lower().startswith(("p1stateno", "p2stateno"))
                   for k in ctrl):
                continue
            return True
    for ctrl in statedefs.get(state, []):
        if ctrl.get("type", "").lower() in ("helper", "changestate"):
            child = _number(ctrl.get("stateno", ctrl.get("value", "")))
            if child is not None and _has_hitdef_with_velocity(statedefs,
                                                               child):
                return True
    return False


def _has_offset_velocity(statedefs, state):
    for ctrl in statedefs.get(state, []):
        typ = ctrl.get("type", "").lower()
        if typ == "velset":
            try:
                if float(str(ctrl.get("x", "0")).strip() or 0) != 0:
                    return True
            except ValueError:
                pass
        if typ in ("helper", "changestate"):
            child = _number(ctrl.get("stateno", ctrl.get("value", "")))
            if child is not None and _has_offset_velocity(statedefs, child):
                return True
    return False


def source_release(statedefs, state):
    """Resolve the root-animation frame that starts this state's shot.

    Returns (frame, kind, target_state) or (None, None, None).  A direct
    Projectile controller is authoritative.  Otherwise the earliest helper
    that reaches a Projectile (or a travelling HitDef helper) wins.  Recovery
    ChangeStates are ignored: they have no Projectile below them.
    """
    if state is None:
        return None, None, None
    for ctrl in statedefs.get(state, []):
        if ctrl.get("type", "").lower() == "projectile":
            frame = _controller_frame(ctrl)
            return (frame if frame is not None else 0), "direct", state

    candidates = []
    for ctrl in statedefs.get(state, []):
        typ = ctrl.get("type", "").lower()
        if typ not in ("helper", "changestate"):
            continue
        child = _number(ctrl.get("stateno", ctrl.get("value", "")))
        if child is None:
            continue
        frame = _controller_frame(ctrl)
        if frame is None:
            continue
        if typ == "helper":
            if _has_type(statedefs, child, "projectile"):
                candidates.append((frame, "helper", child))
            elif (_has_type(statedefs, child, "hitdef")
                  and (_has_offset_velocity(statedefs, child)
                       or _has_hitdef_with_velocity(statedefs, child))):
                # The port stores travelling HitDef helpers and
                # Explod-drawn shots in the projectile pool too.  These
                # rows already have a ProjTab entry, so the helper is the
                # visual launch even without a Projectile controller.
                candidates.append((frame, "hit-helper", child))
        else:
            # A projectile follow-up entered from an explicit AnimElem is a
            # launch; an AnimTime=0/movecontact ChangeState is recovery.
            if (_has_type(statedefs, child, "projectile")
                    and any(re.search(r"AnimElem\s*=\s*\d+", t, re.I)
                            or re.match(r"\s*Time\s*=\s*0\s*$", t, re.I)
                            for t in _triggers(ctrl))):
                candidates.append((frame, "changestate", child))
    if not candidates:
        return None, None, None
    return min(candidates, key=lambda row: row[0])


def proj_rows(name):
    path = OUT / f"{name}_spr.inc"
    if not path.exists():
        return []
    text = path.read_text()
    m = re.search(r"^" + re.escape(name) + r"ProjTab:\s*$", text, re.M)
    if not m:
        return []
    tail = text[m.end():]
    tail = re.split(r"^\w[^ \n]*:", tail, maxsplit=1, flags=re.M)[0]
    rows = []
    for line in tail.splitlines():
        if ".db" in line:
            rows.append([int(v.strip().replace("$", "0x"), 0)
                         for v in line.split(".db", 1)[1].split(",")])
    return rows


def anim_length(name, sid):
    """Frame count of the generated animation for one runtime slot."""
    path = OUT / f"{name}_spr.inc"
    if not path.exists():
        return None
    text = path.read_text()
    m = re.search(r"^" + re.escape(name) + r"AnimTab:\s*$", text, re.M)
    if not m:
        return None
    tail = text[m.end():]
    tail = re.split(r"^\w[^ \n]*:", tail, maxsplit=1, flags=re.M)[0]
    refs = []
    for line in tail.splitlines():
        if ".dw" in line:
            mm = re.search(r"\.dw\s+(\w+)", line)
            refs.append(mm.group(1) if mm else None)
    if sid >= len(refs) or not refs[sid]:
        return None
    label = refs[sid]
    m = re.search(r"^" + re.escape(label) + r":\s*$", text, re.M)
    if not m:
        return None
    tail = text[m.end():]
    tail = re.split(r"^\w[^ \n]*:", tail, maxsplit=1, flags=re.M)[0]
    count = 0
    for line in tail.splitlines():
        if ".db" in line:
            if len(line.split(".db", 1)[1].split(",")) >= 6:
                count += 1
    return count


def state_map(name, cfg):
    mapping = {int(sid): state for sid, state in cfg.get("moves", {}).items()}
    for row in build_fight.POST_CAL_REACTIVATED.get(name, ()):
        mapping.setdefault(int(row[0]), int(row[1]))
    return mapping


def explicit_release(name, sid):
    if sid in PROJECTILE_RELEASE.get(name, {}):
        return PROJECTILE_RELEASE[name][sid], "explicit"
    spec = PROJECTILE_ALT_EFFECTS.get(name)
    if spec and sid in spec.get("sids", ()) and "release" in spec:
        return spec["release"], "alt-clip"
    return None, None


def audit(names=None):
    report = []
    for name, cfg in build_fight.CHARS.items():
        if names and name not in names:
            continue
        if not (OUT / f"{name}_spr.inc").exists():
            continue
        cns = cfg.get("cns")
        if not cns or not os.path.exists(ROOT / cns):
            continue
        parsed = build_fight.parse_cns(
            str(ROOT / cns), cfg.get("coord_scale", 1),
            cfg.get("damage_scale", 1), char=name)
        statedefs = parsed[4]
        moves = state_map(name, cfg)
        for sid, row in enumerate(proj_rows(name)):
            if len(row) != 6 or not (row[5] & 1):
                continue
            state = moves.get(sid)
            length = anim_length(name, sid)
            configured, configured_source = explicit_release(name, sid)
            # The compiled present byte is what the engine actually uses;
            # PROJECTILE_RELEASE is only the build input.  The startup
            # compaction moves the index, so never report the raw config
            # value as the runtime frame.
            if row[5] >> 3:
                release = (row[5] >> 3) - 1
                source = "present-byte"
            else:
                release = (min(DEFAULT_FRAME, length - 1) if length
                           else DEFAULT_FRAME)
                source = "default"
            src_frame, src_kind, src_state = source_release(statedefs, state)
            # The shoto fireballs compact their wind-up, so the compiled
            # release index is source_frame clamped to the kept keyframes.
            expected = src_frame
            if src_frame is not None and sid in \
                    build_fight.PROJECTILE_STARTUP_SPEEDUP.get(name, ()):
                expected = min(src_frame,
                               build_fight.PROJECTILE_STARTUP_KEEP)
            status = "ok"
            if src_frame is None:
                status = "no-source-launch"
            elif release != expected:
                status = "early" if release < expected else "late"
                if length is not None and expected >= length:
                    status = "source-out-of-anim"
            report.append({
                "char": name,
                "sid": sid,
                "state": state,
                "vx": (row[1] << 8) | row[0],
                "px_per_tick": round(((row[1] << 8) | row[0]) / 256.0, 2),
                "damage": row[2],
                "frames": length,
                "release": release,
                "configured_release": configured,
                "configured_source": configured_source,
                "expected_release": expected,
                "release_source": source,
                "source_frame": src_frame,
                "source_kind": src_kind,
                "source_state": src_state,
                "status": status,
            })
    return report


def render(rows):
    print("| Char | sid | state | vx px/t | dmg | rel | want | "
          "source | status |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for r in rows:
        source = r["source_frame"]
        if source is not None and r["expected_release"] != source:
            source = f"{source}->{r['expected_release']}"
        print(f"| {r['char']} | {r['sid']} | {r['state'] or '-'} | "
              f"{r['px_per_tick']:.2f} | {r['damage']} | {r['release']} | "
              f"{r['expected_release'] if r['expected_release'] is not None else '-'} | "
              f"{source if source is not None else '-'} | "
              f"{r['status']} |")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("chars", nargs="*", help="only audit these characters")
    ap.add_argument("--json", type=Path, help="write the full report as JSON")
    ap.add_argument("--all", action="store_true",
                    help="include rows with no source launch controller")
    args = ap.parse_args()
    rows = audit(args.chars or None)
    if not args.all:
        rows = [r for r in rows if r["status"] != "no-source-launch"]
    render(rows)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
