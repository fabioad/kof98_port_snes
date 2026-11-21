#!/usr/bin/env python3
"""Extract the Yami Barai flame art used by the Kyo/Saisyu/Iori projectiles.

Inputs (not stored in the repo; download them first):
  * the KOF'98 "108 Shiki Yami Barai" animation (WebP/GIF, 18 frames) -> Kyo
    and Saisyu;
  * the KOF XV Iori Yami Barai still, used only as the colour reference for
    Iori's purple version.

Outputs, in assets/projectiles/ (committed, read by tools/build_fight.py):
  kyo_yamibarai_a.png / kyo_yamibarai_b.png     tall burst, flat burst
  iori_yamibarai_a.png / iori_yamibarai_b.png   same shapes, purple ramp

Usage:
  python3 -I tools/extract_yamibarai_art.py KYO_ANIM IORI_STILL [OUT_DIR]
"""
import os
import sys

import numpy as np
from PIL import Image

# (animation frame, left, right, top, bottom) of the flame, inclusive.  The
# bursts travel right of Kyo's body in the later frames, so a plain crop
# removes the fighter completely.  Two consecutive frames of the source
# eruption (small burst, then the tall one) keep the GIF's own flicker: the
# engine holds the last frame, so the shot settles on the big flame.
KYO_FRAMES = {"a": (12, 112, 229, 0, 119),    # small burst
              "b": (13, 112, 229, 0, 119)}    # tall burst
IORI_FLAME_X = 123                            # flame starts right of Iori


def lum(rgb):
    return rgb[..., 0] * 0.30 + rgb[..., 1] * 0.59 + rgb[..., 2] * 0.11


def tight_crop(im):
    box = im.getchannel("A").point(lambda v: 255 if v else 0).getbbox()
    return im.crop(box)


def extract_kyo(anim_path):
    anim = Image.open(anim_path)
    out = {}
    for key, (idx, x0, x1, y0, y1) in KYO_FRAMES.items():
        anim.seek(idx)
        im = anim.convert("RGBA").crop((x0, y0, x1, y1))
        out[key] = tight_crop(im)
    return out


def iori_ramp(still_path):
    """Opaque flame pixels of the Iori still, sorted by luminance."""
    im = np.array(Image.open(still_path).convert("RGBA"))
    flame = im[:, IORI_FLAME_X:]
    px = flame[flame[..., 3] > 200][:, :3].astype(np.float32)
    # Drop the near-black backdrop/shadow so it does not become the ramp's
    # darkest entry.
    px = px[lum(px) > 25]
    return px[np.argsort(lum(px))]


def recolor_purple(frames, ramp):
    """Histogram-match the Kyo flame luminance onto the Iori purple ramp."""
    all_lum = np.concatenate([
        lum(np.array(f)[..., :3].astype(np.float32))[np.array(f)[..., 3] > 0]
        for f in frames.values()])
    all_lum.sort()
    out = {}
    for key, f in frames.items():
        a = np.array(f).astype(np.float32)
        mask = a[..., 3] > 0
        l = lum(a[..., :3])
        pct = np.searchsorted(all_lum, l, side="left") / max(1, len(all_lum))
        pos = np.clip((pct * (len(ramp) - 1)).astype(int), 0, len(ramp) - 1)
        rgb = ramp[pos]
        res = np.zeros_like(a)
        res[..., :3] = np.where(mask[..., None], rgb, 0)
        res[..., 3] = a[..., 3]
        out[key] = Image.fromarray(res.astype(np.uint8), "RGBA")
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    out_dir = argv[3] if len(argv) > 3 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "assets",
        "projectiles")
    os.makedirs(out_dir, exist_ok=True)
    kyo = extract_kyo(argv[1])
    iori = recolor_purple(kyo, iori_ramp(argv[2]))
    for key in kyo:
        kyo[key].save(os.path.join(out_dir, f"kyo_yamibarai_{key}.png"))
        iori[key].save(os.path.join(out_dir, f"iori_yamibarai_{key}.png"))
        print(key, kyo[key].size)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
