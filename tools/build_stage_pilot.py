#!/usr/bin/env python3
"""Reproduce the China pilot: weighted details + three aligned SFF poses.

The 16 cells under the rower are reserved in the static 512-tile budget.
Animation uses the existing 48 resident tiles, with no extra runtime DMA.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
import stage_requant as rq

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/stages/stages_png_snes'
OUT = ART / 'pilot_china'
NAME = 'KOF98-ChinaStage'
BOX = (328, 112, 360, 144)
REGIONS = [(56, 40, 248, 136, 4.0)]  # temple roofs, columns and facade


def make_patches(base, pal_rgb):
    """Common palette per cell across all poses avoids background flashing."""
    rgb = []
    for i in range(3):
        pose = Image.open(ART / f'animations/selected/china_remador/pose-{i}.png').convert('RGBA')
        # Source previews already share the same SFF-axis-aligned canvas.
        pose.thumbnail((32, 32), Image.Resampling.NEAREST)
        patch = base.crop(BOX).convert('RGBA')
        patch.alpha_composite(pose, ((32 - pose.width) // 2, 32 - pose.height))
        rgb.append(np.asarray(patch.convert('RGB')))
    lab = rq.srgb_to_oklab(np.array(rgb))
    pals = rq.srgb_to_oklab(pal_rgb)
    indexed = np.zeros((3, 32, 32), np.uint8)
    for y in range(0, 32, 8):
        for x in range(0, 32, 8):
            block = lab[:, y:y+8, x:x+8]
            d = ((block[:, :, :, None, None, :] - pals[None, None, None]) ** 2).sum(-1)
            group = d.min(-1).sum((0, 1, 2)).argmin()
            indexed[:, y:y+8, x:x+8] = group * 15 + d[..., group, :].argmin(-1)
    result = []
    for data in indexed:
        im = Image.fromarray(data, 'P')
        im.putpalette(base.getpalette())
        result.append(im)
    return result


def main():
    OUT.mkdir(exist_ok=True)
    src, _ = rq.load_source(NAME)
    lab = rq.srgb_to_oklab(src)
    lab_t = rq.tiles_of(lab)
    weights = np.ones((28, 64), np.float32)
    for x0, y0, x1, y1, weight in REGIONS:
        weights[y0//8:y1//8, x0//8:x1//8] = weight
    pal_lab, pal_rgb, _ = rq.design_palettes(lab_t)
    # This source leaves repeated dark entries in group 1. Give those slots
    # to the real actor's blue clothing/skin, without taking a fourth palette.
    actor_pixels = []
    for i in range(3):
        rgba = np.asarray(Image.open(ART / f'animations/selected/china_remador/pose-{i}.png').convert('RGBA'))
        actor_pixels.append(rgba[..., :3][rgba[..., 3] > 0])
    actor_lab = rq.srgb_to_oklab(np.concatenate(actor_pixels))
    pal_rgb[1, :6] = pal_rgb[0, [0, 2, 4, 6, 8, 10]]
    pal_lab[1, :6] = rq.srgb_to_oklab(pal_rgb[1, :6])
    pal_rgb[1, 6:], pal_lab[1, 6:] = rq.snap555(rq.kmeans(actor_lab, 9))
    med, arg, _ = rq.reduce_tiles(lab_t, pal_lab, k=496, weights=weights.ravel())
    base = rq.compose(med, arg, pal_rgb)
    patches = make_patches(base, pal_rgb)
    final = base.copy()
    final.paste(patches[0], BOX)
    count = rq.count_tiles(final)
    assert count <= 512, count
    final.save(ART / f'{NAME}.png')
    for i, patch in enumerate(patches):
        patch.save(OUT / f'pose-{i}.png')
    frames = []
    for patch in patches:
        frame = final.copy()
        frame.paste(patch, BOX)
        frames.append(frame.convert('RGB'))
    frames[0].save(OUT / 'preview.gif', save_all=True, append_images=frames[1:],
                   duration=[400, 500, 400], loop=0)
    report = {'stage': NAME, 'static_tiles': count, 'reserved_static_cells': 16,
              'dynamic_tiles': 48, 'region_xywh': [BOX[0], BOX[1], 32, 32],
              'priority_regions_xyxy_weight': REGIONS, 'poses': [0, 10, 17],
              'source_group': 15, 'ticks': [24, 30, 24], 'errors': {}}
    # Exclude the new actor when comparing the unchanged source composition.
    valid = np.ones((224, 512), bool)
    valid[BOX[1]:BOX[3], BOX[0]:BOX[2]] = False
    temple = np.zeros_like(valid)
    temple[40:136, 56:248] = True
    for label, im in [('before', Image.open(OUT / 'before.png')), ('after', final)]:
        err = ((rq.srgb_to_oklab(np.asarray(im.convert('RGB'))) - lab) ** 2).sum(-1)
        report['errors'][label] = {k: float(np.sqrt(err[m].mean()))
                                   for k, m in [('whole_without_actor', valid), ('temple', temple)]}
    (OUT / 'metrics.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
