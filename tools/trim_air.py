#!/usr/bin/env python3
"""Trim a MUGEN .air to a frame-element budget without changing gameplay.

The SNES engine converts only a subset of each character's AIR actions, and
MUGEN exports carry hundreds of dead actions plus in-between frames the
engine never needs.  This tool rewrites an .air in place:

  * deletes actions never referenced by ``anim =``/``value =`` in any of the
    character's .cns/.cmd files (dead anims cost zero gameplay)
  * drops elements that no gameplay trigger can observe and folds their
    ticks into a kept neighbour, preserving the action's total duration

An element is never removed when any of these hold:

  * its 1-based index is <= the largest ``AnimElem``/``AnimElemTime``/``elem``
    index referenced by any statedef that can display the action (that is
    the same data build_fight.py uses for ActiveTab/PosTab/ActTab/slices)
  * it carries Clsn1 attack boxes (removing it would shorten the hit window)
  * its time is -1 (indefinite hold, emitted as 255 by the converter)
  * it is the first element of the action

Core motion actions (walk, jump, run, crouch transitions, get-up) are never
thinned at all, and no action with four or more poses is reduced below four.
Folding ticks preserves gameplay duration, but it turns a seven-pose jump
into a two-pose hold and the character visibly teleports.  Use
tools/smooth_air.py to put source frames back after a trim.

Folded ticks go to the nearest kept element without Clsn1 boxes so attack
windows never grow; survivors are capped at 254 ticks (255 is indefinite).

Usage:
  trim_air.py PATH.air [--sff FILE.sff] [--budget 655] [--apply]
  trim_air.py --batch assets/characters [--budget 655] [--apply]

Without --apply the tool only reports what it would do.  With --apply the
original file is copied to PATH.orig once before rewriting.
"""
import argparse
import glob
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FRAME_RE = re.compile(
    r"^\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)"
    r"(.*)$")
ACTION_RE = re.compile(r"^\s*\[Begin Action (-?\d+)\]", re.I)
CLSN_RE = re.compile(r"^\s*Clsn([12])(Default)?\s*:", re.I)
MAXT = 254

# anim numbers the native engine can map natively regardless of .cns
SYSTEM_ANIMS = {0, 5, 6, 10, 11, 12, 20, 21, 40, 41, 42, 43, 47, 100, 105,
                130, 131, 132, 150, 151, 152, 170, 181, 190, 195,
                3000, 3050, 3051} | set(range(5000, 6000))
# Core motion clips are never thinned.  Folding their ticks keeps the total
# duration but turns a seven-pose jump into a two-pose hold held for 28
# ticks, which is the most visible artifact of an aggressive trim.
MOTION_ANIMS = {0, 10, 11, 12, 20, 21, 40, 41, 42, 43, 47,
                100, 105, 130, 131, 132, 150, 151, 152, 190, 195,
                5120, 5300}
MIN_ACTION_FRAMES = 4
TEXT_EXT = (".cns", ".cmd", ".st", ".zss", ".inc", ".txt", ".air")
# get-hit/system block: never orphan-delete these even if unreferenced
NO_DELETE = set(range(5000, 6000)) | set(range(0, 1000))


class Elem:
    __slots__ = ("g", "n", "x", "y", "t", "tail", "raw", "pre", "atk",
                 "hurt")

    def __init__(self, m, raw):
        self.g, self.n, self.x, self.y = (int(m.group(i)) for i in (1, 2, 3, 4))
        self.t = int(m.group(5))
        self.tail = m.group(6)
        self.raw = raw
        self.pre = []          # Clsn/comment/blank lines before this frame
        self.atk = False       # carries Clsn1 boxes
        self.hurt = False


class Action:
    __slots__ = ("num", "head", "elems", "loop_idx", "tail_lines")

    def __init__(self, num, head):
        self.num = num
        self.head = head       # the [Begin Action N] line
        self.elems = []
        self.loop_idx = -1     # element index the Loopstart marker precedes
        self.tail_lines = []   # non-frame lines after the last element


def parse_air(path):
    """Return (header_lines, [Action, ...]) preserving all raw lines."""
    actions, order = {}, []
    header, pending = [], []
    cur = None
    for raw in open(path, encoding="utf-8-sig", errors="replace"):
        line = raw.split(";", 1)[0].rstrip()
        m = ACTION_RE.match(line)
        if m:
            if cur is not None:
                cur.tail_lines = pending
            else:
                header = pending
            pending = []
            num = int(m.group(1))
            if num not in actions:
                actions[num] = Action(num, raw)
                order.append(num)
            cur = actions[num]
            continue
        stripped = line.strip()
        if cur is None:
            header.append(raw)
            continue
        if not stripped:
            pending.append(raw)
            continue
        if stripped.lower() == "loopstart":
            if cur.loop_idx < 0:
                cur.loop_idx = len(cur.elems)
            continue                        # position recomputed on write
        fm = FRAME_RE.match(raw)
        if fm:
            el = Elem(fm, raw)
            el.pre = pending
            pending = []
            cur.elems.append(el)
            continue
        cm = CLSN_RE.match(stripped)
        if cm:
            pending.append(("clsn", cm.group(1), cm.group(2), raw))
            continue
        pending.append(raw)
    if cur is not None:
        cur.tail_lines = pending
    for act in actions.values():
        for el in act.elems:
            for item in el.pre:
                if (isinstance(item, tuple) and item[0] == "clsn"
                        and item[2] is None):
                    if item[1] == "1":
                        el.atk = True
                    else:
                        el.hurt = True
    return header, [actions[n] for n in order]


def referenced_anims(cns_files):
    refd = set()
    for path in cns_files:
        body = open(path, encoding="utf-8-sig", errors="replace").read()
        for m in re.finditer(r"(?im)^\s*anim\s*=\s*(-?\d+)", body):
            refd.add(int(m.group(1)))
        for m in re.finditer(
                r"(?im)^\s*(?:value|elem)\s*=\s*(-?\d+)\s*$", body):
            refd.add(int(m.group(1)))
    return refd


def protected_index(cns_files):
    """anim number -> highest 1-based element index any trigger touches.

    A statedef's AnimElem/AnimElemTime/elem references apply to every anim
    it can display: its own ``anim =`` plus ChangeAnim/ChangeAnim2 targets.
    """
    prot = {}
    for path in cns_files:
        body = open(path, encoding="utf-8-sig", errors="replace").read()
        sdefs = re.split(r"(?i)\[statedef\s+(-?\d+)\]", body)
        for i in range(1, len(sdefs), 2):
            chunk = sdefs[i + 1]
            refs = {int(m.group(1)) for m in re.finditer(
                r"(?i)animelemtime\s*\(\s*(\d+)\s*\)", chunk)}
            refs |= {int(m.group(1)) for m in re.finditer(
                r"(?i)animelem\s*=\s*(\d+)", chunk)}
            refs |= {int(m.group(1)) for m in re.finditer(
                r"(?im)^\s*elem\s*=\s*(\d+)", chunk)}
            targets = {int(m.group(1)) for m in re.finditer(
                r"(?im)^\s*anim\s*=\s*(-?\d+)", chunk)}
            targets |= {int(m.group(1)) for m in re.finditer(
                r"(?im)^\s*value\s*=\s*(-?\d+)\s*$", chunk)}
            mx = max(refs) if refs else 0
            for a in targets:
                if mx > prot.get(a, 0):
                    prot[a] = mx
    return prot


def load_deltas(sff_path, actions):
    """(action, elem idx) -> (delta_prev, delta_next) pixel-diff, or None."""
    if not sff_path:
        return None
    try:
        import sff
        sf = sff.Sff(sff_path)
    except Exception:
        return None
    cache = {}

    def bmp(g, n):
        if (g, n) in cache:
            return cache[(g, n)]
        sp = sf.get(g, n)
        if sp is None or sp.pix is None:
            cache[(g, n)] = None
            return None
        W = 160
        cv = bytearray(W * W)
        ox, oy = 80, 140
        for yy in range(sp.h):
            for xx in range(sp.w):
                if sp.pix[yy * sp.w + xx]:
                    dx, dy = ox + xx - sp.ax, oy + yy - sp.ay
                    if 0 <= dx < W and 0 <= dy < W:
                        cv[dy * W + dx] = 1
        cache[(g, n)] = bytes(cv)
        return cache[(g, n)]

    def dl(a, b):
        if a is None or b is None:
            return 1.0
        if a == b:
            return 0.0
        return sum(x != y for x, y in zip(a, b)) / len(a)

    out = {}
    for act in actions:
        for i, el in enumerate(act.elems):
            me = bmp(el.g, el.n)
            dp = dl(me, bmp(act.elems[i - 1].g, act.elems[i - 1].n)) \
                if i else None
            dn = dl(me, bmp(act.elems[i + 1].g, act.elems[i + 1].n)) \
                if i < len(act.elems) - 1 else None
            out[(act.num, i)] = (dp, dn)
    return out


def find_sff(char_dir):
    for d in glob.glob(os.path.join(char_dir, "*.def")):
        m = re.search(r"(?im)^\s*sff\s*=\s*(.+)$",
                      open(d, encoding="utf-8-sig",
                           errors="replace").read())
        if m:
            p = os.path.join(char_dir, m.group(1).strip())
            if os.path.exists(p):
                return p
    sffs = glob.glob(os.path.join(char_dir, "*.sff"))
    return max(sffs, key=os.path.getsize) if sffs else None


def plan_action(act, prot, deltas, frac):
    """Set of element indices to drop for one action (0-based)."""
    n = len(act.elems)
    if act.num in MOTION_ANIMS:
        return set()
    # Never collapse a multi-pose clip below MIN_ACTION_FRAMES: the folded
    # ticks keep gameplay timing but the result is a teleporting sprite.
    floor = min(n, MIN_ACTION_FRAMES)
    cap = min(n - max(prot, floor, 2 if n > 1 else 1), int(n * frac))
    if cap <= 0:
        return set()
    cand = []
    for i, el in enumerate(act.elems):
        if i == 0 or i < prot or el.t < 0 or el.atk:
            continue
        if deltas:
            dp, dn = deltas.get((act.num, i), (1.0, 1.0))
            score = max(dp if dp is not None else 1.0,
                        dn if dn is not None else 1.0)
        else:
            # no sprite data: prefer interior in-betweens
            score = 1.0 - abs(i - n / 2) / n
        if i and (el.g, el.n) == (act.elems[i - 1].g, act.elems[i - 1].n):
            score -= 0.5          # identical to previous: pure merge
        elif (i + 1 < n
                and (el.g, el.n) == (act.elems[i + 1].g, act.elems[i + 1].n)):
            score -= 0.25
        cand.append((score, i))
    cand.sort()
    drop = set()
    for score, i in cand:
        if len(drop) >= cap:
            break
        # short actions: never remove two neighbours in a row
        if n <= 6 and (i - 1 in drop or i + 1 in drop):
            continue
        drop.add(i)
    return drop


def apply_plan(act, drop):
    """Apply the drop set: fold ticks, rescue Clsn*Default lines.

    Returns (surviving_elems, new_loop_idx).  Mutates element tick values.
    """
    new_loop = act.loop_idx - sum(1 for i in drop if i < act.loop_idx) \
        if act.loop_idx >= 0 else -1
    out = []
    fold = 0
    rescued = []
    for i, el in enumerate(act.elems):
        if i in drop:
            fold += max(el.t, 0)
            for item in el.pre:
                if (isinstance(item, tuple) and item[0] == "clsn"
                        and item[2] is not None):
                    rescued.append(item)
            continue
        if rescued:
            el.pre = rescued + el.pre
            rescued = []
        if fold:
            # hand removed ticks to the closest previous survivor without
            # an attack box; leftover goes to this element if it is safe
            for j in range(len(out) - 1, -1, -1):
                if not out[j].atk and 0 < out[j].t < MAXT:
                    room = MAXT - out[j].t
                    add = min(fold, room)
                    out[j].t += add
                    fold -= add
                    break
            if fold and not el.atk and 0 < el.t:
                add = min(fold, MAXT - el.t)
                el.t += add
                fold -= add
            # any residual fold is lost (all survivors are atk/-1);
            # that only happens in all-attack actions, which are barely
            # thinned anyway
        out.append(el)
    # tail drops leave fold pending: top up earlier non-attack survivors
    if fold:
        for el in reversed(out):
            if not el.atk and 0 < el.t < MAXT:
                add = min(fold, MAXT - el.t)
                el.t += add
                fold -= add
                if not fold:
                    break
    return out, new_loop


def rebuild_action(act, elems, loop_idx):
    lines = [act.head]
    wrote_loop = False
    for i, el in enumerate(elems):
        if not wrote_loop and loop_idx == i:
            lines.append("Loopstart\n")
            wrote_loop = True
        for item in el.pre:
            if isinstance(item, tuple):
                lines.append(item[3])
            elif isinstance(item, str):
                lines.append(item)
        lines.append(f"{el.g},{el.n},{el.x},{el.y},{el.t}{el.tail}\n")
    if not wrote_loop and 0 <= loop_idx <= len(elems):
        lines.append("Loopstart\n")
    lines += [l for l in act.tail_lines]
    return lines


def trim(path, sff_path, cns_files, budget, apply, keep_extra, levels):
    header, actions = parse_air(path)
    total = sum(len(a.elems) for a in actions)
    refd = referenced_anims(cns_files) | SYSTEM_ANIMS | keep_extra
    prot = protected_index(cns_files)
    deltas = load_deltas(sff_path, actions)

    kept, deleted = [], []
    for act in actions:
        if act.num in NO_DELETE or act.num in refd:
            kept.append(act)
        else:
            deleted.append(act)

    plans, used = {}, 0
    frac = levels[0]
    for frac in levels:
        plans = {a.num: plan_action(a, prot.get(a.num, 0), deltas, frac)
                 for a in kept}
        used = sum(len(a.elems) - len(plans[a.num]) for a in kept)
        if used <= budget:
            break

    report = {"path": path, "actions": len(actions), "elements": total,
              "orphans": [(a.num, len(a.elems)) for a in deleted],
              "kept_actions": len(kept), "after": used, "level": frac,
              "dropped": {a.num: len(plans[a.num])
                          for a in kept if plans[a.num]}}

    if apply:
        out = list(header)
        for act in kept:
            elems, new_loop = apply_plan(act, plans[act.num])
            out += rebuild_action(act, elems, new_loop)
        bak = path + ".orig"
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(out)
    return report


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("air", nargs="?", help=".air file to trim")
    ap.add_argument("--batch", metavar="DIR",
                    help="trim every <char>/*.air under DIR (skips _* dirs)")
    ap.add_argument("--sff", help=".sff for visual-delta scoring "
                                  "(auto-detected per character)")
    ap.add_argument("--budget", type=int, default=655)
    ap.add_argument("--level", type=float, default=None,
                    help="fixed removal fraction per action (0-1). "
                         "Default: escalate 0.25->1.0 until under budget")
    ap.add_argument("--keep", nargs="*", type=int, default=[],
                    help="extra anim numbers to preserve")
    ap.add_argument("--refs", nargs="*", default=None,
                    help="use only these .cns/.cmd files as the reference "
                         "set instead of globbing the char dir")
    ap.add_argument("--apply", action="store_true",
                    help="rewrite files in place (backs up to .orig first)")
    args = ap.parse_args()

    targets = []
    if args.batch:
        for d in sorted(os.listdir(args.batch)):
            p = os.path.join(args.batch, d)
            if not os.path.isdir(p) or d.startswith("_") or d == "stages":
                continue
            for f in sorted(glob.glob(os.path.join(p, "*.air"))):
                targets.append((f, p))
    elif args.air:
        targets.append((args.air,
                        os.path.dirname(os.path.abspath(args.air))))
    else:
        ap.error("give an .air file or --batch DIR")

    for path, cdir in targets:
        if args.refs is not None:
            cns = args.refs
        else:
            cns = [f for f in glob.glob(os.path.join(cdir, "**", "*"),
                                        recursive=True)
                   if f.lower().endswith(TEXT_EXT)
                   and not f.endswith(".orig")]
        sff = args.sff or find_sff(cdir)
        levels = ([args.level] if args.level is not None
                  else (0.25, 0.40, 0.60, 0.80, 1.0))
        r = trim(path, sff, cns, args.budget, args.apply, set(args.keep),
                 levels)
        orph = sum(c for _, c in r["orphans"])
        print(f"{r['path']}")
        print(f"  actions {r['actions']} -> {r['kept_actions']} "
              f"(orphans deleted: {len(r['orphans'])} acts / {orph} elems)")
        print(f"  elements {r['elements']} -> {r['after']} "
              f"(thin level {r['level']}, budget {args.budget})")
        if r["after"] > args.budget:
            print(f"  !! {r['after'] - args.budget} over budget -- "
                  f"choose which referenced specials to drop with --keep")
        drops = ", ".join(f"{a}:-{c}" for a, c in
                          sorted(r["dropped"].items()))
        if drops:
            print(f"  elements removed per action: {drops}")


if __name__ == "__main__":
    main()
