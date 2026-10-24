"""Extract original SFF references and DEF metadata; no SNES artwork conversion."""
from pathlib import Path
import sys, re, json, hashlib
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGES = HERE.parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
from sff import Sff

GROUPS = {'JpnStreet': [20,25,30,45], 'Mid.East':[20,25,30],
          'China':[15], 'Korea':[15,35,40,45,50,55], 'USAYard':[20]}

def sections(file):
    result=[]
    for line_no,line in enumerate(file.read_text(encoding='cp932').splitlines(),1):
        clean=line.split(';',1)[0].strip()
        if clean.startswith('['):
            result.append(dict(section=clean.strip('[]'),line=line_no,comment=line.partition(';')[2],values={},frames=[]))
        elif result and '=' in clean:
            key, value=clean.split('=',1)
            result[-1]['values'][key.strip().lower()]=value.strip()
        elif result and re.match(r'^-?\d+\s*,',clean):
            values=[s.strip() for s in clean.split(',')]
            if len(values)>=5:
                result[-1]['frames'].append(dict(group=int(float(values[0])),number=int(float(values[1])),
                    dx=int(float(values[2])),dy=int(float(values[3])),ticks=int(values[4]),flags=values[5:],line=line_no))
    return result

inventory=[]
for stage,groups in GROUPS.items():
    name=f'KOF98-{stage}Stage'
    file=STAGES/(name+'.def');sff_file=STAGES/(name+'.sff')
    parsed=sections(file);sff=Sff(str(sff_file))
    folder=HERE/'references'/stage;folder.mkdir(parents=True,exist_ok=True)
    for group in groups:
        sprites=[s for s in sff.sprites if s.group==group]
        frames=[]
        for s in sprites:
            image=Image.frombytes('P',(s.w,s.h),s.pix)
            image.putpalette([c for rgb in sff.palettes[s.palidx] for c in rgb])
            image.info['transparency']=0
            dest=folder/f'{group}-{s.number}.png'
            image.save(dest)
            mask=Image.frombytes('L',(s.w,s.h),bytes(255 if v else 0 for v in s.pix))
            frames.append(dict(group=group,number=s.number,width=s.w,height=s.h,
                axis=[s.ax,s.ay],opaque_bbox=mask.getbbox(),reference=str(dest.relative_to(HERE))))
        cols=min(6,len(frames));cellw=192;cellh=152
        sheet=Image.new('RGB',(cols*cellw,((len(frames)+cols-1)//cols)*cellh),(42,48,55))
        draw=ImageDraw.Draw(sheet)
        for i,f in enumerate(frames):
            im=Image.open(HERE/f['reference']).convert('RGBA')
            bbox=f['opaque_bbox']
            if bbox:im=im.crop(bbox)
            im.thumbnail((cellw-12,cellh-28),Image.Resampling.NEAREST)
            x=(i%cols)*cellw;y=(i//cols)*cellh
            sheet.paste(im,(x+6,y+22),im)
            draw.text((x+6,y+5),f'{group},{f["number"]}  {f["width"]}x{f["height"]}',fill='white')
        sheet.save(folder/f'group-{group}.png')
        action=[s for s in parsed if s['section'].lower()==f'begin action {group}']
        bgs=[s for s in parsed if s['section'].lower().startswith('bg ') and s['values'].get('actionno')==str(group)]
        inventory.append(dict(stage=name,group=group,def_file=str(file),sff_file=str(sff_file),
            def_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),sff_sha256=hashlib.sha256(sff_file.read_bytes()).hexdigest(),
            action=action,bgs=bgs,sprites=frames))
(HERE/'source_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
for item in inventory:
    print(item['stage'],item['group'],len(item['sprites']),
          [(s['number'],s['width'],s['height'],s['axis']) for s in item['sprites'][:3]])
