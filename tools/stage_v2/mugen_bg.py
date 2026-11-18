#!/usr/bin/env python3
"""Renderizador de backgrounds MUGEN (.def + .sff) para os stages KOF98.

Reproduz, tick a tick (60/s), as camadas [BG], as acoes de animacao e os
[BGCtrl] (posset/velset/posadd/Anim/SinX/SinY) usados nos dez stages, para
extrair o movimento ORIGINAL do arcade em vez de reamostrar o PNG estatico.

Uso como modulo:
    st = Stage('assets/stages/KOF98-KoreaStage')
    rgba = st.render(tick=120, camx=0)          # numpy (240, W, 4)
"""
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from sff import Sff  # noqa: E402

SCREEN_W, SCREEN_H = 320, 240


def _num(s, default=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _pair(s, default=(0.0, 0.0)):
    if s is None:
        return default
    p = [x.strip() for x in s.split(",")]
    a = _num(p[0], default[0]) if p and p[0] != "" else default[0]
    b = _num(p[1], default[1]) if len(p) > 1 and p[1] != "" else default[1]
    return a, b


def parse_def(path):
    """-> list of (section_name, {key: value}) in file order."""
    raw = open(path, "rb").read().decode("cp932", errors="ignore")
    out = []
    cur = None
    for line in raw.splitlines():
        line = line.split(";")[0].strip()
        if not line:
            continue
        m = re.match(r"^\[(.+?)\]$", line)
        if m:
            cur = (m.group(1).strip(), {}, [])
            out.append(cur)
            continue
        if cur is None:
            continue
        if "=" in line and not re.match(r"^[-\d]", line):
            k, v = line.split("=", 1)
            cur[1][k.strip().lower()] = v.strip()
        else:
            cur[2].append(line)
    return out


class Action:
    def __init__(self, lines):
        self.frames = []        # (group, number, dx, dy, ticks, flip)
        self.loopstart = 0
        for ln in lines:
            if ln.lower().startswith("loopstart"):
                self.loopstart = len(self.frames)
                continue
            p = [x.strip() for x in ln.split(",")]
            if len(p) < 5:
                continue
            try:
                g, n = int(_num(p[0])), int(_num(p[1]))
                dx, dy = int(_num(p[2])), int(_num(p[3]))
                t = int(_num(p[4]))
            except ValueError:
                continue
            flip = p[5].upper() if len(p) > 5 else ""
            self.frames.append((g, n, dx, dy, t, flip))
        self.total = sum(f[4] for f in self.frames if f[4] > 0)
        self.forever = any(f[4] < 0 for f in self.frames)

    def at(self, t):
        """frame tuple at action-local tick t (loops)."""
        if not self.frames:
            return None
        pre = sum(f[4] for f in self.frames[:self.loopstart] if f[4] > 0)
        loop = self.total - pre
        if t >= self.total and loop > 0:
            t = pre + (t - pre) % loop
        acc = 0
        for f in self.frames:
            if f[4] < 0:
                return f
            acc += f[4]
            if t < acc:
                return f
        return self.frames[-1]


class Layer:
    def __init__(self, name, kv):
        self.name = name
        self.kv = kv
        self.type = kv.get("type", "normal").lower()
        self.spriteno = tuple(int(_num(x)) for x in kv.get("spriteno", "0,0").split(","))
        self.action = int(_num(kv.get("actionno", "-1")))
        self.start = _pair(kv.get("start"))
        self.delta = _pair(kv.get("delta"), (1.0, 1.0))
        self.layerno = int(_num(kv.get("layerno", "0")))
        self.mask = int(_num(kv.get("mask", "0")))
        self.trans = kv.get("trans", "none").lower()
        self.tile = tuple(int(_num(x)) for x in kv.get("tile", "0,0").split(","))
        if len(self.tile) == 1:
            self.tile = (self.tile[0], 0)
        self.tilespacing = _pair(kv.get("tilespacing"), (0, 0))
        self.vel0 = _pair(kv.get("velocity"))
        self.sinx = [float(x) for x in kv.get("sin.x", "0,0").split(",") if x.strip()]
        self.siny = [float(x) for x in kv.get("sin.y", "0,0").split(",") if x.strip()]
        self.id = kv.get("id")
        self.reset()

    def reset(self):
        self.pos = [0.0, 0.0]
        self.vel = list(self.vel0)
        self.cur_action = self.action
        self.action_t0 = 0
        self.sinx_p = list(self.sinx)
        self.siny_p = list(self.siny)


class Stage:
    def __init__(self, base):
        self.base = base
        secs = parse_def(base + ".def")
        self.sff = Sff(base + ".sff")
        self.spr = {(s.group, s.number): s for s in self.sff.sprites}
        self.actions = {}
        self.layers = []
        self.ctrldefs = []          # {ids, loop, ctrls}
        self.info = {}
        cur_def = None
        for name, kv, lines in secs:
            low = name.lower()
            if low.startswith("begin action"):
                self.actions[int(_num(name.split()[-1]))] = Action(lines)
            elif low.startswith("bgctrldef"):
                ids = [x.strip() for x in kv.get("ctrlid", "").split(",") if x.strip()]
                cur_def = {"ids": ids, "loop": int(_num(kv.get("looptime", "-1"))),
                           "ctrls": []}
                self.ctrldefs.append(cur_def)
            elif low.startswith("bgctrl"):
                if cur_def is not None:
                    cur_def["ctrls"].append(kv)
                    if "ctrlid" in kv:
                        cur_def["ids"] = cur_def["ids"] + [
                            x.strip() for x in kv["ctrlid"].split(",")]
            elif re.match(r"^bg\b", low):
                self.layers.append(Layer(name, kv))
            elif low in ("camera", "stageinfo", "playerinfo", "bound"):
                self.info[low] = kv
        self._cache = {}

    # -- state at a tick (deterministic replay, cached incrementally) ------
    def _simulate(self, tick):
        for L in self.layers:
            L.reset()
        events = []
        for d in self.ctrldefs:
            for c in d["ctrls"]:
                events.append((int(_num(c.get("time", "0"))), d, c))
        for t in range(tick + 1):
            for d, c in [(d, c) for (tt, d, c) in events
                         if tt == (t % d["loop"] if d["loop"] > 0 else t)]:
                self._apply(d, c, t)
            for L in self.layers:
                L.pos[0] += L.vel[0]
                L.pos[1] += L.vel[1]

    def _apply(self, d, c, t):
        typ = c.get("type", "").lower()
        targets = [L for L in self.layers if L.id in d["ids"]]
        x = _num(c.get("x"), None) if "x" in c else None
        y = _num(c.get("y"), None) if "y" in c else None
        for L in targets:
            if typ == "posset":
                if x is not None:
                    L.pos[0] = x
                if y is not None:
                    L.pos[1] = y
            elif typ == "posadd":
                L.pos[0] += x or 0
                L.pos[1] += y or 0
            elif typ == "velset":
                if x is not None:
                    L.vel[0] = x
                if y is not None:
                    L.vel[1] = y
            elif typ == "veladd":
                L.vel[0] += x or 0
                L.vel[1] += y or 0
            elif typ == "anim":
                L.cur_action = int(_num(c.get("value")))
                L.action_t0 = t
            elif typ == "sinx":
                L.sinx_p = [float(v) for v in c.get("value", "0,0").split(",")]
            elif typ == "siny":
                L.siny_p = [float(v) for v in c.get("value", "0,0").split(",")]

    def _layer_sprite(self, L, tick):
        if L.type == "normal":
            return self.spr.get(L.spriteno), 0, 0, ""
        if L.type == "anim":
            a = self.actions.get(L.cur_action)
            if not a:
                return None, 0, 0, ""
            f = a.at(tick - L.action_t0)
            if not f:
                return None, 0, 0, ""
            return self.spr.get((f[0], f[1])), f[2], f[3], f[5]
        return None, 0, 0, ""

    def sprite_rgba(self, sp, mask=1):
        key = (sp.group, sp.number, mask)
        if key in self._cache:
            return self._cache[key]
        pal = self.sff.palettes[sp.palidx] if sp.palidx is not None else None
        if pal is None:
            self._cache[key] = None
            return None
        lut = np.zeros((256, 4), np.uint8)
        for i, c in enumerate(pal[:256]):
            lut[i] = (c[0], c[1], c[2], 255)
        if mask:
            lut[0, 3] = 0
        idx = np.frombuffer(sp.pix, np.uint8).reshape(sp.h, sp.w)
        out = lut[idx]
        self._cache[key] = out
        return out

    def render(self, tick=0, camx=0, camy=0, width=SCREEN_W, layers=None,
               xoff=0, only=None, world=False, force=None, skip=None,
               simulate=True):
        """Compose all layers (layerno 0 then 1).  Output (240, width, 4).

        `xoff` shifts the origin so a canvas wider than the screen can hold
        the whole world: world-x 0 is at canvas x = width/2 + xoff.
        """
        if simulate:
            self._simulate(tick)
        H = SCREEN_H
        canvas = np.zeros((H, width, 4), np.uint8)
        order = sorted(range(len(self.layers)),
                       key=lambda i: (self.layers[i].layerno, i))
        for i in order:
            L = self.layers[i]
            if only is not None and i not in only:
                continue
            if layers is not None and L.layerno not in layers:
                continue
            if skip is not None and i in skip:
                continue
            if force is not None and i in force:
                g, n, dx, dy, flip = force[i]
                sp = self.spr.get((g, n))
            else:
                sp, dx, dy, flip = self._layer_sprite(L, tick)
            if sp is None or sp.pix is None:
                continue
            img = self.sprite_rgba(sp, L.mask)
            if img is None:
                continue
            if "H" in flip:
                img = img[:, ::-1]
            if "V" in flip:
                img = img[::-1]
            sinx = 0.0
            siny = 0.0
            if len(L.sinx_p) >= 2 and L.sinx_p[1]:
                ph = L.sinx_p[2] if len(L.sinx_p) > 2 else 0
                sinx = L.sinx_p[0] * math.sin(2 * math.pi * (tick + ph) / L.sinx_p[1])
            if len(L.siny_p) >= 2 and L.siny_p[1]:
                ph = L.siny_p[2] if len(L.siny_p) > 2 else 0
                siny = L.siny_p[0] * math.sin(2 * math.pi * (tick + ph) / L.siny_p[1])
            if world:       # world-space: delta<1 layers drift with the camera
                sx = width / 2 + xoff + L.start[0] + L.pos[0] + sinx + camx * (1 - L.delta[0])
            else:
                sx = width / 2 + xoff + L.start[0] + L.pos[0] + sinx - camx * L.delta[0]
            sy = L.start[1] + L.pos[1] + siny - camy * L.delta[1]
            x0 = int(round(sx)) - sp.ax + dx
            y0 = int(round(sy)) - sp.ay + dy
            if "H" in flip:
                x0 = int(round(sx)) - (sp.w - sp.ax) + dx
            tx, ty = L.tile
            xs = [x0]
            if tx:
                step = sp.w + int(L.tilespacing[0])
                if step > 0:
                    first = x0 - ((x0 + step) // step) * step
                    xs = list(range(first, width + step, step))
            for xx in xs:
                self._blit(canvas, img, xx, y0, L.trans)
        return canvas

    @staticmethod
    def _blit(canvas, img, x0, y0, trans="none"):
        H, W = canvas.shape[:2]
        h, w = img.shape[:2]
        cx0, cy0 = max(0, x0), max(0, y0)
        cx1, cy1 = min(W, x0 + w), min(H, y0 + h)
        if cx0 >= cx1 or cy0 >= cy1:
            return
        src = img[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
        dst = canvas[cy0:cy1, cx0:cx1]
        m = src[..., 3] > 0
        if trans.startswith("add"):
            dst[m, :3] = np.minimum(255, dst[m, :3].astype(int) + src[m, :3])
            dst[m, 3] = 255
        elif trans.startswith("sub"):
            dst[m, :3] = np.maximum(0, dst[m, :3].astype(int) - src[m, :3])
            dst[m, 3] = 255
        else:
            dst[m] = src[m]


def render_world(st, tick=0, width=752, **kw):
    """Flat world composite at camera 0, holes (parallax layers that do not
    reach the world edges) filled from the camera-extreme passes."""
    base = st.render(tick, 0, width=width, world=True, **kw)
    for cam in (-108, 108, -216, 216):
        alt = st.render(tick, cam, width=width, world=True, simulate=False, **kw)
        hole = base[..., 3] == 0
        base[hole] = alt[hole]
    return base


def main():
    from PIL import Image
    base, tick, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    cam = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    st = Stage(base)
    Image.fromarray(st.render(tick, cam)).save(out)


if __name__ == "__main__":
    main()
