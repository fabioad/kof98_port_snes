import sys,collections,json
from PIL import Image,ImageDraw
sys.path.insert(0,'/run/media/fabio/Dados/Fabio/kof98_port_snes/tools')
from sff import Sff
s=Sff('Robert-KOF98/Robert.sff');print('version',s.ver0,'sprites',len(s.sprites),'palettes',len(s.palettes));print(collections.Counter(v.group for v in s.sprites))
print('palette',list(enumerate(s.palettes[0][:100])))
sel=[x for x in s.sprites if x.group<5000 and x.group!=-1][::7][:120]
out=Image.new('RGB',(1000,((len(sel)+9)//10)*150),'#888888');d=ImageDraw.Draw(out)
for i,v in enumerate(sel):
 if not v.pix:continue
 f=Image.frombytes('P',(v.w,v.h),bytes(v.pix));f.putpalette([c for rgb in s.palettes[v.palidx] for c in rgb]);f.info['transparency']=0;f=f.convert('RGBA');f.thumbnail((96,125));x=i%10*100;y=i//10*150;out.paste(f,(x,y+20),f);d.text((x,y),f'{v.group},{v.number}',fill='white')
out.save('/tmp/robert_sprites.png')
