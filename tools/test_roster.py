#!/usr/bin/env python3
"""Roster verification: lock every CharSelTab entry on the select screen,
enter the fight, and confirm the right character loads and animates.

Versus loop: P1/P2 each pick one char per iteration, so two entries are
validated per match.  After the fighters reach gs1 with sane sprite meta
and OAM cells, the match is ended early (wins1=1 + P2 hp=0 -> KO -> match
over -> back to the select screen) and the next pair is tested.

Usage: python3 tools/test_roster.py [--launch] [--shots outdir]
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import test_fight_remote as t                      # noqa: E402
from test_menu_modes import enter_mode

SELDATA = ROOT / "src/gen_menu/seldata.inc"
NEWTABS = ROOT / "build/gen_fight/newchars_tabs.inc"

GS_SELECT = 5
GS_FIGHT = 1

# WRAM (DP base $1000 + select block $F052+)
W_GS = 0x1020
W_MSUOK = 0x107A
W_WINS1 = 0x1080
W_SEL1 = 0x1085
W_SEL2 = 0x1086
W_LOCK1 = 0x108E
W_LOCK2 = 0x108F
W_CPU2 = 0x1091
W_MITEM = 0xF070
W_SCUR1 = 0xF052
W_SCUR2 = 0xF053
W_GMODE = 0x10C0
OAM = 0x1800
FP2_HP = 0x4040 + 16


def parse_tables():
    """char id -> (name, select cell).  Order from CharSelTab, cells from
    SelChrCell; name lowercased to match build/gen_fight/<name>.* files."""
    names = []
    rows = NEWTABS.read_text().split("CharSelTab:", 1)[1].split("BankSelTab:", 1)[0]
    for line in rows.splitlines():
        if ".dw" not in line:
            continue
        for m in re.finditer(r"\bChar([A-Za-z0-9]+)\b", line.split(".dw", 1)[1]):
            names.append(m.group(1).lower())
    cells = []
    for line in SELDATA.read_text().splitlines():
        if line.startswith("SelChrCell:"):
            cells = [int(x) for x in
                     line.split(".db", 1)[1].strip().split(",")]
            break
    roster = {}
    for i, name in enumerate(names):
        roster[i] = {"name": name,
                     "cell": cells[i] if i < len(cells) else None}
    return roster


def descriptor(name):
    label = 'Char' + ('OmegaRugal' if name == 'omegarugal' else name.capitalize())
    for line in (ROOT / 'kof98-snes.symfull').read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1] == label:
            return int(fields[0], 16) & 0xFFFF
    raise ValueError('missing linked character descriptor: ' + label)


def press(ra, user, btn, settle=0.12):
    ra.button(user, btn, True)
    time.sleep(settle)
    ra.button(user, btn, False)
    time.sleep(settle)


def lock_side(ra, user, cell, lock_addr):
    """Park the side's cursor on `cell` and confirm until the lock byte
    reads 1 (UDP edges are lossy -- verify and retry)."""
    ra.command(f"WRITE_CORE_RAM {W_SCUR1 + user:X} {cell:02X}")
    for _ in range(10):
        press(ra, user, "A")
        if ra.read_ram(lock_addr, 1)[0] == 1:
            return
    raise AssertionError(f"side {user} lock never engaged")


def to_select(ra):
    """title -> mode menu -> VERSUS (item 1) -> select screen."""
    enter_mode(ra, 1)
    for _ in range(6):                        # let select assets settle
        time.sleep(0.1)


def oam_cells(ra):
    oam = ra.read_ram(OAM, 160)
    return sum(1 for i in range(0, 160, 4) if oam[i + 1] < 0xF0)


def fight_snapshot(ra):
    s = ra.snapshot()
    return {
        "sel1": ra.read_ram(W_SEL1, 1)[0],
        "sel2": ra.read_ram(W_SEL2, 1)[0],
        "p1char": s["p1"]["char"], "p2char": s["p2"]["char"],
        "p1meta": s["p1"]["frame"] and ra.read_ram(0x4000 + 22, 1)[0] or 0,
        "p1state": s["p1"]["state"], "p2state": s["p2"]["state"],
        "p1frame": s["p1"]["frame"], "p2frame": s["p2"]["frame"],
        "p1anim": s["p1"]["anim"], "p2anim": s["p2"]["anim"],
        "p1hp": s["p1"]["hp"], "p2hp": s["p2"]["hp"],
        "cells": oam_cells(ra),
    }


def idle_animation_samples(ra, users=(0, 1), duration=0.9):
    """Collect live animation element indices while both fighters stand."""
    bases = {0: t.FP1, 1: t.FP2}
    frames = {user: set() for user in users}
    metas = {user: set() for user in users}
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        for user in users:
            base = bases[user]
            state = ra.read_ram(base + t.F_STATE, 1)[0]
            if state == 0:
                frames[user].add(ra.read_ram(base + t.F_FRAME, 1)[0])
                metas[user].add(int.from_bytes(
                    ra.read_ram(base + t.F_META, 2), 'little'))
        time.sleep(0.04)
    return {user: {'frames': sorted(frames[user]), 'metas': sorted(metas[user])}
            for user in users}


def expected_idle_frame_count(name):
    import build_fight
    cfg = build_fight.CHARS.get(name)
    if not cfg or 0 not in cfg.get("anims", {}):
        return 1
    anims = build_fight.parse_air(ROOT / cfg["air"])
    frames = anims.get(cfg["anims"][0], ([], -1))[0]
    return len({(f[0], f[1]) for f in frames})


def shot(ra, outdir, tag, ids):
    """Render the live frame; teach snap_frame about MSU chars first."""
    try:
        import snap_frame as sf
    except Exception as exc:
        print(f"  shot {tag}: snap_frame unavailable ({exc})")
        return
    for base, cid in ((t.FP1, ids[0]), (t.FP2, ids[1])):
        name = ALL[cid]["name"]
        bank = ra.read_ram(base + 46, 1)[0]
        if name not in sf.ASSETS["chr"]:
            chrfile = ROOT / "build" / "gen_fight" / f"{name}.chr"
            if not chrfile.exists():
                continue
            sf.ASSETS["chr"][name] = sf.chr_tiles(chrfile.read_bytes())
        sf.F_BANK.setdefault(bank, name)
        palfile = ROOT / "build" / "gen_fight" / f"{name}_pal.bin"
        if palfile.exists():
            sf.ASSETS["obj_pal"][0 if base == t.FP1 else 1] = \
                sf.pal_colors(palfile.read_bytes())
    img = sf.render(ra)
    out = Path(outdir) / f"{tag}.png"
    img.save(out)
    print(f"  shot -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--retroarch", default="retroarch")
    ap.add_argument("--core", default=t.CORE)
    ap.add_argument("--shots", default=None,
                    help="directory for rendered frame captures")
    ap.add_argument("--only", default=None,
                    help="comma list of char ids to test instead of all")
    ap.add_argument("--animation-smoke", action="store_true",
                    help="require live stand animation frame progression for animated idle AIR actions")
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    global ALL
    ALL = parse_tables()
    ids = ([int(x) for x in args.only.split(",")] if args.only
           else [i for i in sorted(ALL) if ALL[i]["name"] != "omegarugal"])
    pairs = [(ids[i], ids[i + 1] if i + 1 < len(ids) else 0)
             for i in range(0, len(ids), 2)]

    ra = t.RetroArch()
    results = {}
    try:
        if args.launch:
            ra.launch(args.retroarch, args.core)
        ra.wait_ready()
        to_select(ra)
        msu = ra.read_ram(W_MSUOK, 1)[0]
        gmode = ra.read_ram(W_GMODE, 1)[0]
        print(f"select reached: msuok={msu} gmode={gmode} "
              f"({len(ids)} chars, {len(pairs)} matches)")

        for n, (a, b) in enumerate(pairs):
            tag = f"{n:02d}_{ALL[a]['name']}_vs_{ALL[b]['name']}"
            if ra.read_ram(W_CPU2, 1)[0] != 0:
                press(ra, 1, "START", settle=0.25)
            lock_side(ra, 1, ALL[b]["cell"], W_LOCK2)
            lock_side(ra, 0, ALL[a]["cell"], W_LOCK1)
            try:
                st = t.wait_for(ra, lambda s: s["gamestate"] == GS_FIGHT
                                and s["p1"]["state"] == 0
                                and s["p2"]["state"] == 0,
                                timeout=30)
            except AssertionError:
                print("audio reload:", ra.read_ram(0x46F8, 8).hex(),
                      "spc debug:", ra.read_ram(0x4700, 16).hex(), flush=True)
                print("transition:", {
                    "audiordy": ra.read_ram(0x1032, 1)[0],
                    "muson": ra.read_ram(0xF07C, 1)[0],
                    "stageidx": ra.read_ram(0x1087, 1)[0],
                    "locks": ra.read_ram(0x108E, 2).hex(),
                    "gamestate": ra.read_ram(0x1020, 2).hex(),
                    "frame": ra.read_ram(0x1024, 2).hex()}, flush=True)
                raise
            time.sleep(0.6)                   # sprite streams settle
            snap = fight_snapshot(ra)
            if args.animation_smoke:
                sampled = idle_animation_samples(ra)
                names = (ALL[a]["name"], ALL[b]["name"])
                counts = {names[user]: {
                    "expected": expected_idle_frame_count(names[user]),
                    "observed": len(sampled[user]['frames']),
                    "frames": sampled[user]['frames'],
                    "displayed_metas": sampled[user]['metas']}
                    for user in (0, 1)}
                snap["idle_animation"] = counts
                snap["idle_ok"] = all(
                    item["expected"] < 2 or
                    (item["observed"] >= 2 and len(item["displayed_metas"]) >= 2)
                    for item in counts.values())
            ok = (snap["sel1"] == a and snap["sel2"] == b
                  and snap["p1char"] == descriptor(ALL[a]["name"])
                  and snap["p2char"] == descriptor(ALL[b]["name"])
                  and snap["p1hp"] == 200 and snap["p2hp"] == 200
                  and snap["cells"] >= 8)
            if args.animation_smoke:
                ok = ok and snap["idle_ok"]
            results[(a, b)] = (ok, snap)
            print(f"[{n+1}/{len(pairs)}] {tag}: "
                  f"chars={snap['p1char']},{snap['p2char']} "
                  f"anims={snap['p1anim']},{snap['p2anim']} "
                  f"oam={snap['cells']} {'OK' if ok else 'FAIL'} {snap}")
            if args.shots and (n < 6 or not ok):
                Path(args.shots).mkdir(exist_ok=True)
                shot(ra, args.shots, tag, (a, b))
            # end the match: P1 already has 1 win -> this KO closes it
            ra.command(f"WRITE_CORE_RAM {W_WINS1:X} 01")
            ra.command(f"WRITE_CORE_RAM {FP2_HP:X} 00 00")
            t.wait_for(ra, lambda s: s["gamestate"] == GS_SELECT,
                       timeout=45, interval=0.15)
            time.sleep(0.4)

        # Omega Rugal: Rugal cell + L&R held swaps the pick to id 14.
        if args.only is None:
            if ra.read_ram(W_CPU2, 1)[0] != 0:
                press(ra, 1, "START", settle=0.25)
            lock_side(ra, 1, ALL[0]["cell"], W_LOCK2)
            ra.command(f"WRITE_CORE_RAM {W_SCUR1:X} {ALL[3]['cell']:02X}")
            ra.button(0, "L", True); ra.button(0, "R", True)
            time.sleep(0.2)
            press(ra, 0, "A")
            ra.button(0, "L", False); ra.button(0, "R", False)
            st = t.wait_for(ra, lambda s: s["gamestate"] == GS_FIGHT,
                            timeout=30)
            time.sleep(0.6)
            snap = fight_snapshot(ra)
            ok = (snap["sel1"] == 14
                  and snap["p1char"] == descriptor("omegarugal"))
            results[(14, 0)] = (ok, snap)
            print(f"[omegarugal] p1char={snap['p1char']} "
                  f"{'OK' if ok else 'FAIL'} {snap}")
            ra.command(f"WRITE_CORE_RAM {W_WINS1:X} 01")
            ra.command(f"WRITE_CORE_RAM {FP2_HP:X} 00 00")
            t.wait_for(ra, lambda s: s["gamestate"] == GS_SELECT,
                       timeout=45, interval=0.15)
    finally:
        ra.close()
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(json.dumps({
                "expected_ids": ids + ([14] if args.only is None else []),
                "matches": [
                    {"ids": [a, b], "names": [ALL[a]["name"], ALL[b]["name"]],
                     "passed": ok, "snapshot": snap}
                    for (a, b), (ok, snap) in results.items()],
            }, indent=2) + "\n")

    bad = {k: v for k, v in results.items() if not v[0]}
    print(f"\n== {len(results) - len(bad)}/{len(results)} matches OK ==")
    for (a, b), (_, snap) in bad.items():
        print(f"  FAIL {ALL[a]['name']} vs {ALL[b]['name']}: {snap}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
