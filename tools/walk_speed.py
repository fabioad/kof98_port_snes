#!/usr/bin/env python3
"""Per-character walk speed from the MUGEN source package.

The SNES port kept a single global WALKSPD.  This helper reads the
[Velocity] section that the character was imported from (following the
same Cns/St/St0..St9 order MUGEN uses) and returns walk.fwd / walk.back
in the engine's 8.8 fixed-point (256 = 1 px/tick).

The merged *_SNES.cns used at build time may not carry [Velocity] (it
lives in Constants.cns), so the character's original .def is used to
resolve the file order.
"""
import os
import re

ENCODINGS = ("utf-8-sig", "utf-8", "cp932", "latin-1")


def _read(path):
    raw = open(path, "rb").read()
    for enc in ENCODINGS:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", "replace")


def _sections(text):
    secs = {}
    cur = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^\[([^\]]+)\]", s)
        if m:
            cur = re.sub(r"\s+", " ", m.group(1).strip().lower())
            secs.setdefault(cur, [])
            continue
        if cur is None:
            continue
        s = re.sub(r";.*$", "", s).strip()
        if s:
            secs[cur].append(s)
    return secs


def _kv(lines):
    out = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            out[re.sub(r"\s+", " ", k.strip().lower())] = v.strip()
    return out


def _resolve(expr, vel):
    """const(velocity.walk.fwd.x) / -const(...) / literal -> float."""
    e = expr.strip().rstrip(",").strip()
    if not e:
        return None

    def repl(m):
        key = re.sub(r"\s+", " ", m.group(1).strip().lower())
        axis = None
        mm = re.match(r"^(.*)\.(x|y|z)$", key)
        if mm:
            key, axis = mm.group(1).strip(), mm.group(2)
        if key.startswith("velocity."):
            key = key[len("velocity."):]
        if key not in vel:
            raise ValueError
        parts = [p for p in re.split(r"[,\s]+", vel[key].strip()) if p]
        nums = [float(p) for p in parts]
        if axis == "y":
            return repr(nums[1] if len(nums) > 1 else 0.0)
        if axis == "z":
            return repr(nums[2] if len(nums) > 2 else 0.0)
        return repr(nums[0])

    try:
        e2 = re.sub(r"const\s*\(\s*([^)]+)\s*\)", repl, e, flags=re.I)
    except (ValueError, IndexError):
        return None
    if not re.fullmatch(r"[0-9eE+\-*/().\s]+", e2):
        return None
    try:
        return float(eval(e2, {"__builtins__": {}}, {}))
    except Exception:
        return None


def _ci_path(base, rel):
    rel = rel.replace("\\", os.sep).strip().strip('"')
    p = os.path.join(base, rel)
    if os.path.exists(p):
        return p
    cur = base
    for part in rel.split(os.sep):
        if not part or part == ".":
            continue
        if part == "..":
            cur = os.path.dirname(cur)
            continue
        try:
            cand = [f for f in os.listdir(cur) if f.lower() == part.lower()]
        except OSError:
            return None
        if not cand:
            return None
        cur = os.path.join(cur, cand[0])
    return cur if os.path.exists(cur) else None


def _find_def(folder):
    """Main character .def (skip storyboards/intro/ending)."""
    cands = []
    for root, _dirs, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith(".def"):
                continue
            p = os.path.join(root, f)
            try:
                low = _read(p).lower()
            except OSError:
                continue
            has_files = "[files]" in low and "cmd" in low and "cns" in low
            scene = "[scenedef]" in low
            same = os.path.splitext(f)[0].lower() == os.path.basename(folder).lower()
            cands.append((same, has_files and not scene, not scene, -len(p), p))
    cands.sort(reverse=True)
    return cands[0][-1] if cands else None


def _load_order(def_path, base):
    files = _kv(_sections(_read(def_path)).get("files", []))
    out = []
    seq = [("stcommon", "stcommon"), ("cns", "cns"), ("st", "st")]
    seq += [(f"st{i}", f"st{i}") for i in range(1, 10)]
    for _label, key in seq:
        if key not in files:
            continue
        for piece in files[key].split(","):
            piece = piece.strip()
            if not piece:
                continue
            p = _ci_path(base, piece)
            if p:
                out.append(p)
    return out


def read_walk_speed(cns_path, coord_scale=1.0):
    """Return (fwd, back) as 8.8 signed ints, or None if not found.

    cns_path is the cfg["cns"] path (merged *_SNES.cns).  The original
    .def is looked up in the same directory.
    """
    folder = os.path.dirname(cns_path)
    def_path = _find_def(folder)
    if not def_path:
        return None

    vel = {"walk.fwd": "2.4", "walk.back": "-2.2"}
    found = False
    for p in _load_order(def_path, folder):
        secs = _sections(_read(p))
        if "velocity" not in secs:
            continue
        kv = _kv(secs["velocity"])
        for key in ("walk.fwd", "walk.back"):
            if key in kv:
                vel[key] = kv[key]
                found = True
    if not found:
        return None

    fwd = _resolve("const(velocity.walk.fwd.x)", vel)
    back = _resolve("const(velocity.walk.back.x)", vel)
    if fwd is None or back is None:
        return None
    scale = float(coord_scale) or 1.0
    return (int(round(fwd / scale * 256)) & 0xFFFF,
            int(round(back / scale * 256)) & 0xFFFF)


if __name__ == "__main__":
    import sys
    print(read_walk_speed(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 1.0))
