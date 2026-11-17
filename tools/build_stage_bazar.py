#!/usr/bin/env python3
"""Bazar pilot: weighted architecture and sparse, real SFF gestures."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
import stage_requant as rq

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/stages/stages_png_snes'
OUT = ART / 'pilot_bazar'
NAME = 'KOF98-Mid.EastStage'
# Aligned previews, fitted to the existing crowd in the HD composition.
ACTORS = [
    ('bazar_publico_esquerda', (87, 115), (49, 62), 0, None),
    ('bazar_publico_centro', (227, 113), (47, 62), 10, (80, 0, 150, 92)),
    ('bazar_comerciante', (336, 112), (34, 37), 20, None),
]
REGIONS = [(264, 0, 400, 104, 3.), (8, 88, 112, 176, 2.)]


def clean_under_motion(rgb, union):
    """Nearest visible surround, used only where a moving silhouette uncovers it."""
    out = rgb.copy()
    ys, xs = np.where(~union)
    for y, x in zip(*np.where(union)):
        j = ((ys-y)**2 + (xs-x)**2).argmin()
        out[y, x] = rgb[ys[j], xs[j]]
    return out


def prepare(src):
    prepared = []
    composed = src.copy()
    for name, (x,y), size, phase, crop in ACTORS:
        poses = []
        for i in range(2):
            pose = Image.open(ART / f'animations/selected/{name}/pose-{i}.png').convert('RGBA')
            if crop: pose = pose.crop(crop)
            poses.append(np.asarray(pose.resize(size, Image.Resampling.NEAREST)))
        w,h = size
        box = (x//8*8, y//8*8, (x+w+7)//8*8, (y+h+7)//8*8)
        x0,y0,x1,y1 = box
        layers = []
        for pose in poses:
            layer = np.zeros((y1-y0,x1-x0,4), np.uint8)
            layer[y-y0:y-y0+h,x-x0:x-x0+w] = pose
            layers.append(layer)
        union = (layers[0][...,3] > 0) | (layers[1][...,3] > 0)
        bg = src[y0:y1,x0:x1].copy()
        clean = clean_under_motion(bg, union)
        frames = []
        for layer in layers:
            frame = bg.copy()
            frame[union] = clean[union]
            mask = layer[...,3] > 0
            frame[mask] = layer[...,:3][mask]
            frames.append(frame)
        composed[y0:y1,x0:x1] = frames[0]
        prepared.append((name,box,phase,np.array(frames)))
    return composed, prepared


def quantize(frames, pal_rgb):
    lab = rq.srgb_to_oklab(frames)
    pals = rq.srgb_to_oklab(pal_rgb)
    n,h,w,_ = frames.shape
    idx = np.zeros((n,h,w),np.uint8)
    for y in range(0,h,8):
        for x in range(0,w,8):
            b = lab[:,y:y+8,x:x+8]
            d = ((b[:,:,:,None,None,:]-pals[None,None,None])**2).sum(-1)
            g = d.min(-1).sum((0,1,2)).argmin()
            idx[:,y:y+8,x:x+8] = g*15 + d[...,g,:].argmin(-1)
    cells = [(x//8,y//8) for y in range(0,h,8) for x in range(0,w,8)
             if np.any(idx[0,y:y+8,x:x+8] != idx[1,y:y+8,x:x+8])]
    return idx, cells


def main():
    OUT.mkdir(exist_ok=True)
    src, _ = rq.load_source(NAME)
    composed, prepared = prepare(src)
    lab = rq.srgb_to_oklab(composed)
    pal_lab,pal_rgb,_ = rq.design_palettes(rq.tiles_of(lab))
    patches = [(name,box,phase,*quantize(frames,pal_rgb)) for name,box,phase,frames in prepared]
    count = sum(len(cells) for _,_,_,_,cells in patches)
    print('Changed cells:', [(name,len(cells)) for name,_,_,_,cells in patches],flush=True)
    assert count <= 36, f'{count*2+88} resident tiles exceeds shared 160'
    assert all(0 < len(cells) <= 16 for *_,cells in patches), 'per-commit CPU budget'
    weights = np.ones((28,64),np.float32)
    for x0,y0,x1,y1,w in REGIONS:
        weights[y0//8:y1//8,x0//8:x1//8] = w
    for _,(x0,y0,x1,y1),_,_,_ in patches:
        weights[y0//8:y1//8,x0//8:x1//8] = 3
    # Reclaim patterns made unused when pose-0 cells replace the reduced
    # background. Keep the best fitting result if the tile count oscillates.
    budget = 512-count
    best = None
    attempted = set()
    for _ in range(4):
        if budget in attempted: break
        attempted.add(budget)
        med,arg,cost = rq.reduce_tiles(rq.tiles_of(lab),pal_lab,k=budget,weights=weights.ravel())
        candidate = rq.compose(med,arg,pal_rgb)
        for _,box,_,idx,cells in patches:
            for x,y in cells:
                tile=Image.fromarray(idx[0,y*8:y*8+8,x*8:x*8+8],'P')
                tile.putpalette(candidate.getpalette())
                candidate.paste(tile,(box[0]+x*8,box[1]+y*8))
        used=rq.count_tiles(candidate)
        print(f'Background budget {budget}: {used} final tiles',flush=True)
        if used<=512 and (best is None or cost<best[0]):best=(cost,candidate)
        if used==512:break
        budget=min(512,max(1,budget+512-used))
    assert best is not None
    final = best[1]
    specs = {}
    for name,box,phase,idx,cells in patches:
        x0,y0,x1,y1 = box
        for x,y in cells:
            tile = Image.fromarray(idx[0,y*8:y*8+8,x*8:x*8+8], 'P')
            tile.putpalette(final.getpalette())
            final.paste(tile,(x0+x*8,y0+y*8))
        paths=[]
        for p in range(2):
            patch=Image.fromarray(idx[p],'P');patch.putpalette(final.getpalette())
            path=f'pilot_bazar/{name}-{p}.png';patch.save(ART/path);paths.append(path)
        specs[name] = dict(target_region_xywh=[x0,y0,x1-x0,y1-y0],
            resident_patch_files=paths,resident_patch_cells=cells,
            frame_count=2,changed_tiles_per_pose_cap=len(cells),
            art_bytes_per_pose_cap=len(cells)*32,all_poses_rom_bytes_cap=len(cells)*64,
            resident_vram_bytes_cap=len(cells)*64,resident_payload_bytes_cap=len(cells)*64,
            sequence=[dict(pose=0,ticks60=30),dict(pose=1,ticks60=30)],
            start_phase_ticks60=phase,cycle_ticks60=60,
            placement_status='pilot_aligned_sff_sparse_gestures')
    n=rq.count_tiles(final);assert n<=512,n
    final.save(ART/f'{NAME}.png')
    (OUT/'targets.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2)+'\n')
    specpath=ART/'animations/stage_animations.json'
    spec=json.loads(specpath.read_text())
    for clip in spec['clips']:
        if clip['id'] in specs:clip['target'].update(specs[clip['id']])
    specpath.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    frames=[]
    for tick in range(60):
        f=final.copy()
        for name,box,phase,idx,cells in patches:
            p=((tick+phase)//30)%2
            for x,y in cells:
                tile=Image.fromarray(idx[p,y*8:y*8+8,x*8:x*8+8],'P');tile.putpalette(final.getpalette())
                f.paste(tile,(box[0]+x*8,box[1]+y*8))
        frames.append(f.convert('RGB'))
    frames[0].save(OUT/'preview.gif',save_all=True,append_images=frames[1:],
                   duration=[20,10,20]*20,loop=0)
    valid=np.ones((224,512),bool);priority=np.zeros_like(valid)
    for _,(x0,y0,x1,y1),_,_,_ in patches:valid[y0:y1,x0:x1]=False
    for x0,y0,x1,y1,_ in REGIONS:priority[y0:y1,x0:x1]=True
    ref=rq.srgb_to_oklab(src);errors={}
    for label,im in [('before',Image.open(OUT/'before.png')),('after',final)]:
        err=((rq.srgb_to_oklab(np.asarray(im.convert('RGB')))-ref)**2).sum(-1)
        errors[label]={k:float(np.sqrt(err[m].mean())) for k,m in [('without_actors',valid),('architecture',priority & valid)]}
    report=dict(stage=NAME,static_tiles=n,animated_cells=count,dynamic_tiles=count*2,
                shared_dynamic_tiles=88+count*2,priority_regions=REGIONS,errors=errors)
    (OUT/'metrics.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)


if __name__=='__main__': main()
