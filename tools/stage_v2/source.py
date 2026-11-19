"""Fonte do arcade -> imagem 512x224 em luz linear para a reducao SNES."""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mugen_bg as mb  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
STAGES = os.path.join(ROOT, "assets/stages")
W_WORLD = 752          # camera +-216 + tela de 320
OUT_W, OUT_H = 512, 224
GROUND_ROW = 190       # fight.asm GROUND_Y: linha de arte onde ficam os pes
GROUND_CANVAS = {"KOF98-ChinaStage": 208}   # deck: BG10 y=232 + dummy -24
DEFAULT_GROUND = 218   # zoffset do .def


def srgb_to_lin(a):
    a = a / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055) * 255.0


def crop_rows(name, world):
    """(240,752,4) -> 224 linhas com o chao do arcade em GROUND_ROW."""
    y0 = GROUND_CANVAS.get(name, DEFAULT_GROUND) - GROUND_ROW
    h = world.shape[0]
    rows = np.arange(y0, y0 + OUT_H)
    rows = np.where(rows >= h, 2 * (h - 1) - rows, rows)     # espelha o piso
    return world[np.clip(rows, 0, h - 1)]


def downscale(rgb_lin, w=OUT_W, h=OUT_H):
    """Lanczos em luz linear (suave, sem serrilhado) -> (h,w,3) float."""
    out = np.empty((h, w, 3), np.float32)
    for c in range(3):
        im = Image.fromarray(rgb_lin[..., c].astype(np.float32), "F")
        out[..., c] = np.asarray(im.resize((w, h), Image.LANCZOS))
    return np.clip(out, 0, 1)


def arcade_rgb(world_rgba):
    """RGBA 752x224 -> sRGB 512x224 float 0..255."""
    rgb = srgb_to_lin(world_rgba[..., :3].astype(np.float64))
    return lin_to_srgb(downscale(rgb)).astype(np.float32)


def bilateral_lab(lab, radius=3, sigma_s=1.6, sigma_r=0.045, iters=1):
    """Filtro bilateral em OKLab: apaga ruido de textura (que gasta tiles e
    cores) mas preserva contornos.  lab (H,W,3) float32."""
    out = lab.astype(np.float32)
    H, W, _ = out.shape
    for _ in range(iters):
        p = np.pad(out, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
        acc = np.zeros_like(out)
        wsum = np.zeros((H, W, 1), np.float32)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                ws = np.exp(-(dx * dx + dy * dy) / (2 * sigma_s ** 2))
                nb = p[radius + dy:radius + dy + H, radius + dx:radius + dx + W]
                d2 = ((nb - out) ** 2).sum(-1, keepdims=True)
                w = ws * np.exp(-d2 / (2 * sigma_r ** 2))
                acc += w * nb
                wsum += w
        out = acc / wsum
    return out
