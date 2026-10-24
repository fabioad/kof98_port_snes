#!/usr/bin/env python3
"""Restore in-between AIR frames removed by tools/trim_air.py.

trim_air.py folds dropped elements into their neighbours so gameplay keeps
the same total duration, but the visual result is a teleport: Kyo's seven
frame jump becomes a two-frame pose held for 28 ticks.  The new mechanics
increased the number of referenced actions, so the 655-element budget forced
trim_air to escalate its thinning level for every character.

This tool puts the source frames back, without touching gameplay:

  * only actions that still exist in the current .air are considered (the
    build ignores orphan actions anyway)
  * an action is restored only when the current sprite sequence is an
    ordered subsequence of the .orig sequence.  Manually edited actions
    (Sakura's entrance) do not match and stay exactly as they are
  * the restored action keeps the original element indices, so every
    AnimElem/Clsn reference in the .cns keeps pointing at the same pose
  * character CHR bank headroom is respected for the ROM-resident fighters
    (Kyo, Iori, Shingo, Terry, Rugal Omega, Benimaru, Daimon).  MSU-1
    characters have no CHR budget.
  * each action is capped at 254 elements: the runtime stores the frame
    count in a byte and 255 means "hold forever".

Usage:
  smooth_air.py [--apply] [--dry-run] [--chars kyo,iori]
"""
import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trim_air import parse_air, rebuild_action

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "gen_fight")
MAX_FRAMES = 254                 # runtime frame counter is a byte; 255 = hold
SLOT_BYTES = 32768               # one CHR half-bank
CHR_SAFETY = 256                 # keep room for alignment leftovers
# ROM fighters are currently full because build_fight used to generate one
# synthetic attack tween for every clip, with no byte budget except Kyo.
# Real restored frames replace those dissolves, so their space is available.
TWEEN_RECLAIM = 32768

# ROM-resident fighters and the number of 32 KiB CHR half-banks the linker
# map gives them (see src/engine/fight.asm and the CNAME_BANKS table in
# build_fight.py).  Keeping this here avoids trusting a partially written
# _chr.inc from an interrupted build.
ROM_CHR_BANKS = {
    "kyo": 19, "iori": 22, "terry": 17, "shingo": 19,
    "omegarugal": 18, "benimaru": 14, "daimon": 16,
}
# CHR size of the trimmed build these budgets were measured against.  Using
# max(current, baseline) keeps a rerun from counting the same free space
# twice when an interrupted build left a smaller .chr behind.
BASELINE_CHR = {
    "kyo": 621376, "iori": 710464, "terry": 535744, "shingo": 598592,
    "omegarugal": 573120, "benimaru": 452032, "daimon": 521536,
}
# Old 14-roster fighters keep their generated tables in hand-mapped fixed
# windows (fight.asm), not in the packer's larger PVS slots.  Restore their
# motion clips only: those are the visible teleports, while the attack
# clips already get a sparse-clip dissolve in build_fight.
MOTION_ONLY = {"saisyu", "heidern", "takuma", "clark", "ralf", "leona",
               "mature", "vice", "rugal"}

# Core motion clips.  Restore these first: they are the ones the player sees
# all the time.  Values are MUGEN AIR action numbers.
MOTION_ANIMS = {
    0, 5, 10, 11, 12, 20, 21, 40, 41, 42, 43, 47,
    100, 105, 130, 131, 132, 150, 151, 152, 160, 170, 181, 190, 195,
    5120, 5300,
}
# Priority inside the motion set: jumping is the most visible teleport, then
# walking/running, then the crouch/get-up transitions.
MOTION_RANK = {
    41: 0, 42: 0, 43: 0, 40: 1, 47: 1,
    1: 2, 2: 2, 20: 2, 21: 2, 100: 2, 105: 2,
    12: 3, 13: 3, 10: 3, 11: 3, 5120: 3, 5300: 3,
    0: 6, 5: 6, 130: 6, 131: 6, 132: 6, 150: 6, 151: 6, 152: 6,
    160: 6, 170: 6, 181: 6, 190: 6, 195: 6,
}


def char_name(air_path):
    """assets/characters/Kyo-KOF98/Kyo.air -> kyo"""
    return os.path.basename(os.path.dirname(air_path)).lower()


def load_build_config():
    """Import build_fight lazily: it exposes CHARS with the msu flag/paths."""
    import build_fight
    return build_fight


def chr_headroom(name):
    """Return the free bytes in a ROM character's CHR bank run."""
    chr_path = os.path.join(OUT, f"{name}.chr")
    banks = ROM_CHR_BANKS.get(name)
    if not banks or not os.path.exists(chr_path):
        return 0
    used = os.path.getsize(chr_path)
    used = max(used, BASELINE_CHR.get(name, 0))
    return max(0, banks * SLOT_BYTES - used - CHR_SAFETY)


def sprite_cells(sprite):
    """Upper-bound packed size of one SFF sprite (16x16 cell page)."""
    if sprite.pix is None or not sprite.w or not sprite.h:
        return 0
    cols = (sprite.w + 15) // 16
    rows = (sprite.h + 15) // 16
    n = 0
    for cy in range(rows):
        for cx in range(cols):
            for yy in range(cy * 16, min((cy + 1) * 16, sprite.h)):
                row = sprite.pix[yy * sprite.w + cx * 16:
                               yy * sprite.w + min((cx + 1) * 16, sprite.w)]
                if any(row):
                    n += 1
                    break
    return min(3072, n * 4 * 32)


def action_sprites(act):
    return [(e.g, e.n) for e in act.elems]


def is_subsequence(cur, org):
    it = iter(org)
    return all(x in it for x in cur)


def restore_file(path, budget, sff, apply, wanted_anims=None,
                 motion_only=False):
    """Restore eligible actions of one .air.  Returns a report dict."""
    orig_path = path + ".orig"
    header, current = parse_air(path)
    _, source = parse_air(orig_path)
    src = {a.num: a for a in source}
    cur = {a.num: a for a in current}
    if wanted_anims is not None:
        # build_char only compiles cfg["anims"]; restoring orphan or unused
        # actions would bloat the file without changing a single sprite.
        current = [a for a in current if a.num in wanted_anims]

    # Sprites already present anywhere in the current file are free: the
    # build compiles each unique cel once, regardless of which action uses it.
    available = set()
    for act in current:
        available.update(action_sprites(act))

    candidates = []
    for act in current:
        o = src.get(act.num)
        if o is None or len(o.elems) <= len(act.elems):
            continue
        if len(o.elems) > MAX_FRAMES:
            continue
        if not is_subsequence(action_sprites(act), action_sprites(o)):
            continue
        if motion_only and act.num not in MOTION_ANIMS:
            continue
        new = [s for s in dict.fromkeys(action_sprites(o)) if s not in available]
        if sff is not None:
            cost = sum(sprite_cells(sff[s]) for s in new if s in sff)
        else:
            cost = 3072 * len(new)
        rank = MOTION_RANK.get(act.num, 5)
        if act.num not in MOTION_ANIMS:
            rank = 8
        candidates.append((rank, cost, -(len(o.elems) - len(act.elems)),
                           act.num, o, new))

    candidates.sort(key=lambda c: (c[0], c[1], c[2], c[3]))
    chosen, spent = set(), 0
    for rank, cost, _gain, num, o, new in candidates:
        if budget is not None and spent + cost > budget:
            continue
        chosen.add(num)
        spent += cost
        available.update(new)

    report = {"path": path, "restored": [], "skipped": 0, "bytes": spent,
              "frames": sum(len(src[n].elems) - len(cur[n].elems)
                            for n in chosen)}
    if not apply or not chosen:
        report["restored"] = sorted(chosen)
        report["skipped"] = len(candidates) - len(chosen)
        return report

    # Replace only the chosen action blocks; leave the rest of the file
    # byte-for-byte untouched.
    text = open(path, encoding="utf-8-sig", errors="replace").read()
    blocks = list(re.finditer(r"(?im)^\s*\[begin\s+action\s+(\d+)\s*\]",
                              text))
    out = [text[:blocks[0].start()]] if blocks else [text]
    for i, m in enumerate(blocks):
        end = blocks[i + 1].start() if i + 1 < len(blocks) else len(text)
        num = int(m.group(1))
        if num in chosen:
            o = src[num]
            out.append("".join(rebuild_action(o, o.elems, o.loop_idx)))
            if not out[-1].endswith("\n"):
                out[-1] += "\n"
            report["restored"].append(num)
        else:
            out.append(text[m.start():end])
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("".join(out))
    report["restored"].sort()
    return report


def refresh_profile(name, rel, path):
    """Refresh the calibrated .air input hash after a visual-only rewrite.

    The profiles in assets/calibration pin every input file.  Restoring
    in-between frames changes no combat value, but it does change the .air
    bytes.  Refuse to touch a profile that carries an animation correction:
    such a correction is indexed by element and would need recalibration.
    """
    profile = os.path.join(ROOT, "assets", "calibration", name + ".json")
    if not os.path.exists(profile):
        return False
    data = json.load(open(profile, encoding="utf-8"))
    if any(c.get("kind") == "animation" for c in data.get("corrections", ())):
        raise SystemExit(f"{name}: profile has element-indexed animation "
                         f"corrections; recalibrate instead of patching")
    if rel not in data.get("inputs", {}):
        return False
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    data["inputs"][rel] = h.hexdigest()
    with open(profile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    return True


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="rewrite the .air files (default: dry run)")
    ap.add_argument("--chars", help="comma separated character directory "
                                    "names (default: every .air with .orig)")
    args = ap.parse_args()

    bf = load_build_config()
    only = ({c.strip().lower() for c in args.chars.split(",")}
            if args.chars else None)

    # air path -> (character build name, ROM resident?, compiled anim numbers)
    paths = {}
    for name, cfg in bf.CHARS.items():
        air = cfg.get("air")
        if not air:
            continue
        rel = os.path.relpath(os.path.join(ROOT, air), ROOT)
        anims = frozenset(cfg.get("anims", {}).values())
        paths.setdefault(rel, (name, not cfg.get("msu"), anims))

    total_frames = 0
    for rel, (name, rom, wanted_anims) in sorted(paths.items()):
        if only and char_name(rel) not in only and name not in only:
            continue
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path + ".orig"):
            continue
        budget = chr_headroom(name) + TWEEN_RECLAIM if rom else None
        sprites = None
        try:
            from sff import Sff
            sffcfg = bf.CHARS[name]
            sprites = {(s.group, s.number): s
                       for s in Sff(os.path.join(ROOT, sffcfg["sff"])).sprites}
        except Exception:
            sprites = None
        rep = restore_file(path, budget, sprites, args.apply,
                           wanted_anims=wanted_anims,
                           motion_only=name in MOTION_ONLY)
        if not rep["restored"]:
            continue
        total_frames += rep["frames"]
        tag = "ROM" if rom else "MSU"
        print(f"{name:12s} {tag:3s} restore {len(rep['restored']):3d} actions"
              f", budget {'inf' if budget is None else budget}"
              f", spent ~{rep['bytes']}B")
        if rep["skipped"]:
            print(f"             skipped {rep['skipped']} actions that do not "
                  "fit the CHR budget (or were edited manually)")
        if args.apply:
            print("             actions " + ",".join(map(str, rep["restored"])))
            if refresh_profile(name, rel, path):
                print("             calibration .air hash refreshed")
    print(f"{'applied' if args.apply else 'dry-run'}: "
          f"{total_frames} restored frames, {len(paths)} character AIRs")


if __name__ == "__main__":
    main()
