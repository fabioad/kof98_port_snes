"""Build an auditable animation specification, reference previews and C timing tables."""
from pathlib import Path
import json, sys
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
inventory=json.loads((HERE/'source_inventory.json').read_text())
lookup={(r['stage'],r['group']):r for r in inventory}

# Target tile figures are art budgets, not measurements of converted graphics.
# A sparse BG patch has at most this many changed 8x8 cells per pose.
recipes=[
 dict(id='japan_publico',stage='JpnStreet',group=30,frames=[0,4],crop=[40,80,202,170],
      label='Público atrás dos estudantes',steps=[0,1],ticks=[36,36],phase=0,tiles=8,
      region=[344,104,40,64],gesture='Dois extremos do balanço de braços e tronco; pernas e carros estáticos.'),
 dict(id='japan_estudantes',stage='JpnStreet',group=45,frames=[0,3],crop=None,
      label='Estudantes',steps=[0,1],ticks=[30,30],phase=15,tiles=8,
      region=[384,104,64,64],gesture='Alternar postura dos braços/bolsa e um pequeno movimento da cabeça.'),
 dict(id='bazar_comerciante',stage='Mid.East',group=20,frames=[0,6],crop=[28,40,78,94],
      label='Comerciante da banca direita',steps=[0,1],ticks=[42,18],phase=0,tiles=4,
      region=[432,104,24,48],gesture='Braço em repouso e braço levantado; preservar banca e tapetes.'),
 dict(id='bazar_publico_esquerda',stage='Mid.East',group=25,frames=[0,5],crop=[128,88,200,180],
      label='Espectador da esquerda',steps=[0,1],ticks=[40,40],phase=20,tiles=4,
      region=[128,104,32,48],gesture='Movimento discreto da cabeça e do braço; mercadorias imóveis.'),
 dict(id='bazar_publico_centro',stage='Mid.East',group=30,frames=[0,3],crop=[0,88,150,180],
      label='Público central',steps=[0,1],ticks=[36,36],phase=36,tiles=8,
      region=[184,104,104,48],gesture='Dois extremos dos gestos de mãos; excluir camelo e cenário da animação.'),
 dict(id='coreia_observador',stage='Korea',group=35,frames=[13,14],crop=None,
      label='Homem atrás do parapeito',steps=[0,1],ticks=[24,24],phase=0,tiles=4,
      region=[448,112,24,24],gesture='Usar o pequeno gesto de mão do ciclo de observação; omitir entrada/saída.'),
 dict(id='china_remador',stage='China',group=15,frames=[0,10,17],crop=None,
      label='Remador',steps=[0,1,2],ticks=[24,30,24],phase=0,tiles=24,
      region=[24,120,32,48],gesture='Alcance com remo à frente, puxada com tronco baixo, recuperação com remo erguido.'),
 dict(id='coreia_gaivota',stage='Korea',group=50,frames=[0,1,2],crop=None,
      label='Gaivota compartilhada',steps=[0,1,2,1],ticks=[9,9,9,9],phase=0,tiles=4,
      region=None,gesture='Asa baixa, transição e asa alta; voltar pela transição sem armazenar uma quarta pose.')
]

def align_frames(row,selected,crop):
    sprites=[next(s for s in row['sprites'] if s['number']==number) for number in selected]
    boxes=[]
    for s in sprites:
        b=crop or s['opaque_bbox'];ax,ay=s['axis']
        boxes.append([b[0]-ax,b[1]-ay,b[2]-ax,b[3]-ay])
    bounds=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
    images=[]
    for s,b in zip(sprites,boxes):
        source=Image.open(HERE/s['reference']).convert('RGBA')
        source=source.crop(crop or s['opaque_bbox'])
        canvas=Image.new('RGBA',(bounds[2]-bounds[0],bounds[3]-bounds[1]))
        canvas.alpha_composite(source,(b[0]-bounds[0],b[1]-bounds[1]))
        images.append(canvas)
    return sprites,bounds,images

clips=[]
for recipe in recipes:
    stage='KOF98-'+recipe['stage']+'Stage'
    row=lookup[(stage,recipe['group'])]
    sprites,bounds,images=align_frames(row,recipe['frames'],recipe['crop'])
    folder=HERE/'selected'/recipe['id'];folder.mkdir(parents=True,exist_ok=True)
    refs=[]
    for i,(s,image) in enumerate(zip(sprites,images)):
        image.save(folder/f'pose-{i}.png')
        original=Image.open(HERE/s['reference'])
        original.save(folder/f'source-{s["group"]}-{s["number"]}.png')
        frame=next(f for f in row['action'][0]['frames'] if f['group']==s['group'] and f['number']==s['number'])
        refs.append(dict(pose=i,group=s['group'],number=s['number'],source_axis=s['axis'],
            source_size=[s['width'],s['height']],source_air_offset=[frame['dx'],frame['dy']],
            source_line=frame['line'],source_ticks=frame['ticks'],source_crop=recipe['crop'],
            preview=f'selected/{recipe["id"]}/pose-{i}.png'))
    # All previews show ORIGINAL art at original scale, not converted SNES art.
    w,h=images[0].size
    sheet=Image.new('RGB',(w*len(images),h+20),(38,44,51));draw=ImageDraw.Draw(sheet)
    for i,im in enumerate(images):
        sheet.paste(im,(i*w,20),im);draw.text((i*w+2,3),f'{recipe["group"]},{recipe["frames"][i]}',fill='white')
    sheet.save(folder/'poses.png')
    animation=[]
    for step in recipe['steps']:
        bg=Image.new('RGB',(w,h),(38,44,51));bg.paste(images[step],(0,0),images[step]);animation.append(bg)
    animation[0].save(folder/'preview.gif',save_all=True,append_images=animation[1:],
        duration=[round(t*1000/60) for t in recipe['ticks']],loop=0,disposal=2)
    mode='obj_resident' if recipe['region'] is None else 'bg1_sparse_double_buffer'
    tiles=recipe['tiles'];count=len(recipe['frames'])
    target=dict(mode=mode,frame_count=count,palette='stage_bg_palette' if recipe['region'] else 'one_shared_obj_palette',
        changed_tiles_per_pose_cap=tiles,art_bytes_per_pose_cap=tiles*32,
        all_poses_rom_bytes_cap=tiles*32*count,
        resident_vram_bytes_cap=704 if mode=='obj_resident' else tiles*32*2,
        resident_payload_bytes_cap=tiles*32*(count if mode=='obj_resident' else 2),
        obj_atlas_layout=dict(pose_base_tiles=[0,2,4],row_stride_tiles=16,reserved_tile_span=22,
            used_tiles=12,unused_tiles_inside_span=10) if mode=='obj_resident' else None,
        oam_entries=1 if mode=='obj_resident' else 0,
        target_region_xywh=recipe['region'],placement_status='proposed_for_redrawn_512x224_not_pixel_matched',
        sprite_size=[16,16] if mode=='obj_resident' else None,
        sequence=[dict(pose=p,ticks60=t) for p,t in zip(recipe['steps'],recipe['ticks'])],
        start_phase_ticks60=recipe['phase'],cycle_ticks60=sum(recipe['ticks']),
        gesture=recipe['gesture'])
    clips.append(dict(id=recipe['id'],label=recipe['label'],stage=stage,
        source=dict(def_file=Path(row['def_file']).name,sff_file=Path(row['sff_file']).name,
            def_sha256=row['def_sha256'],sff_sha256=row['sff_sha256'],action=recipe['group'],
            original_action_entries=len(row['action'][0]['frames']),
            original_cycle_ticks=sum(f['ticks'] for f in row['action'][0]['frames'] if f['ticks']>0),
            bg=row['bgs'],alignment_bounds_relative_to_axis=bounds,poses=refs),target=target))

paths=[
 dict(id='passagem_0',source_action=40,start_tick60=0,start_xy=[-16,32],velocity_q4=[24,4],hflip=False),
 dict(id='passagem_1',source_action=45,start_tick60=360,start_xy=[512,96],velocity_q4=[-24,-4],hflip=True),
 dict(id='passagem_2',source_action=50,start_tick60=720,start_xy=[-16,96],velocity_q4=[24,-4],hflip=False),
 dict(id='passagem_3',source_action=55,start_tick60=1080,start_xy=[512,32],velocity_q4=[-24,4],hflip=True)
]
budgets=[]
for stage in sorted({c['stage'] for c in clips}):
    members=[c for c in clips if c['stage']==stage]
    bg=sum(c['target']['changed_tiles_per_pose_cap']*2 for c in members if c['target']['mode'].startswith('bg1'))
    budgets.append(dict(stage=stage,bg_total_tile_limit=512,bg_reserved_dynamic_tiles_cap=bg,
        bg_static_tiles_cap=512-bg,animation_graphics_rom_bytes_cap=sum(c['target']['all_poses_rom_bytes_cap'] for c in members),
        animation_vram_bytes_cap=sum(c['target']['resident_vram_bytes_cap'] for c in members),
        extra_obj_palette_bytes=32 if stage.endswith('KoreaStage') else 0))
spec=dict(version=1,status='definition_for_future_integration_no_final_chr_or_rom',tick_rate=60,
    graphics='SNES 4bpp, 32 bytes per 8x8 tile; all budget values are upper targets before art export',
    max_distinct_poses_per_clip=3,dma_policy=dict(background_art_bytes_per_vblank_cap=256,
        background_tilemap_bytes_on_commit_cap=48,commit='atomic_after_inactive_buffer_complete',
        priority='fighters_and_HUD_first; defer_environment_if_budget_unavailable'),
    clips=clips,stage_budgets=budgets,
    gull_paths=dict(shared_clip='coreia_gaivota',coordinate_space='world_512x224_top_left',
        repeat_ticks60=1440,max_simultaneous=1,lifetime_ticks60=352,
        parallax_q8=256,source_parallax_x=1.1,paths=paths),
    excluded=dict(Korea_action15='48-frame background patch with distant birds; omitted from the minimal profile',
        JpnStreet_actions20_25='Vehicles and overlapping spectators; composite static content before applying selected people patches',
        USAYard_action20='Locomotive/environment, not people',
        Spain_action20='Cat, not seagull',USAWharf_action45='Rat, not seagull'),
    docs=['https://alekmaul.github.io/pvsneslib/sprite_8h.html','https://alekmaul.github.io/pvsneslib/dma_8h.html'])
(HERE/'stage_animations.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')

header=['/* Generated by build_definitions.py; definitions only, no graphics. */',
 '#ifndef STAGE_ANIM_DATA_H','#define STAGE_ANIM_DATA_H','#include "stage_anim_clock.h"',
 '#define STAGE_ANIM_COUNT '+str(len(clips)), 'static const StageAnimDef stage_anim_defs[STAGE_ANIM_COUNT] = {']
for c in clips:
    t=c['target'];seq=t['sequence']
    rows=[f'{{{s["pose"]}, {s["ticks60"]}}}' for s in seq]+['{0, 0}']*(4-len(seq))
    header.append('    {%d, %d, %d, {%s}}, /* %s */' % (t['frame_count'],len(seq),t['start_phase_ticks60'],', '.join(rows),c['id']))
header+=['};']
for i,c in enumerate(clips): header.append(f'#define STAGE_ANIM_{c["id"].upper()} {i}')
header+=['#endif','']
(HERE/'stage_anim_data.h').write_text('\n'.join(header))
for c in clips:
    print(c['id'],[p['number'] for p in c['source']['poses']],c['target']['cycle_ticks60'])
print(json.dumps(budgets,indent=2))
