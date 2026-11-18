"""Metricas perceptuais: o olho enxerga a media local, nao o pixel isolado."""
import numpy as np


def gauss_blur(a, sigma):
    r = int(np.ceil(sigma * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, ((r, r), (r, r), (0, 0)), mode="edge")
    p = sum(k[i] * p[i:i + a.shape[0] + 0, :, :] for i in range(len(k))) \
        if False else _conv_axis(_conv_axis(p, k, 0), k, 1)
    return p[r:-r, r:-r] if r else p


def _conv_axis(a, k, axis):
    r = len(k) // 2
    n = a.shape[axis] - 2 * r
    out = 0
    for i, w in enumerate(k):
        sl = [slice(None)] * a.ndim
        sl[axis] = slice(i, i + n)
        out = out + w * a[tuple(sl)]
    sl = [slice(None)] * a.ndim
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r, r)
    return np.pad(out, pad, mode="edge")


def blur_rmse(lab_a, lab_b, sigma=1.2):
    """OKLab RMSE depois de um blur gaussiano (nivel que o olho percebe)."""
    d = gauss_blur(lab_a, sigma) - gauss_blur(lab_b, sigma)
    return float(np.sqrt((d ** 2).sum(-1).mean()))


def pix_rmse(lab_a, lab_b):
    return float(np.sqrt(((lab_a - lab_b) ** 2).sum(-1).mean()))


def blockiness(lab_a, lab_b):
    """Erro da media de cada bloco 4x4 (o defeito que le como 'quadrado')."""
    h, w = lab_a.shape[:2]
    a = lab_a.reshape(h // 4, 4, w // 4, 4, 3).mean((1, 3))
    b = lab_b.reshape(h // 4, 4, w // 4, 4, 3).mean((1, 3))
    return float(np.sqrt(((a - b) ** 2).sum(-1).mean()))
