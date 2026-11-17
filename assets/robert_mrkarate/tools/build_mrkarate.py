#!/usr/bin/env python3
"""Rebuild the standalone Mr. Karate from the untouched Robert source."""
import sys,io,struct,shutil,json,subprocess,collections
from pathlib import Path
import numpy as np
import wave as wavmod
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'Robert-KOF98';dst=ROOT/'MrKarate-KOF98'
sys.path.insert(0,str(ROOT/'tools'))
from sff import Sff
for p in src.iterdir():
 if p.is_file() and p.suffix.lower() in ('.cns','.cmd','.air'):shutil.copy2(p,dst/p.name)
shutil.copytree(src/'act',dst/'act',dirs_exist_ok=True)
sff=Sff(src/'Robert.sff'); pal=[list(c) for c in sff.palettes[0]]
for i,c in {12:(232,232,236),13:(184,184,192),14:(112,112,124),15:(24,24,32),240:(192,0,0),241:(128,0,8),242:(72,0,16),243:(0,0,0)}.items():pal[i]=list(c)
while len(pal)<256:pal.append([0,0,0])
# ACT stores its palette in reverse order.
(dst/'act/MrKarate.act').write_bytes(bytes(c for rgb in reversed(pal) for c in rgb))
masks=[Image.open(p).convert('RGBA') for p in sorted((ROOT/'mascaras/png').glob('*.png'))]
placements=[]; encoded=[]
# Poses where face detection cannot land the mask correctly.  The lying-down
# frame (state 5110 / AIR 5040,10) is a horizontal body: keep the Tengu mask
# resting on his chest instead of leaving the pose bare.
CHEST_MASKS={(5040,10):(32,22,6)}

def components(points):
 result=[]
 while points:
  p=points.pop();q=[p];c=[p]
  while q:
   x,y=q.pop()
   for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
    v=x+dx,y+dy
    if v in points:points.remove(v);q.append(v);c.append(v)
  result.append(c)
 return result

for k,s in enumerate(sff.sprites):
 pix=bytearray(s.pix or b'');p=sff.palettes[s.palidx] if s.palidx is not None else sff.palettes[0]
 # Robert's player graphics share the 16-colour source palette; effect palettes stay intact.
 player=p is not None and p[:16]==sff.palettes[0][:16] and s.group not in (9001,)
 if player and pix and (s.group,s.number) in CHEST_MASKS:
  mx,my,choice=CHEST_MASKS[(s.group,s.number)]
  m=masks[choice].copy()
  canvas=Image.new('P',(s.w,s.h),0);canvas.paste(Image.frombytes('P',(s.w,s.h),bytes(pix)),(0,0))
  for yy in range(m.height):
   for xx in range(m.width):
    r,g,b,a=m.getpixel((xx,yy))
    if a and 0<=mx+xx<canvas.width and 0<=my+yy<canvas.height:canvas.putpixel((mx+xx,my+yy),240 if r>=160 else 241 if r>=100 else 242)
  pix=bytearray(canvas.tobytes());w,h=canvas.size
  placements.append({'group':s.group,'number':s.number,'x':mx,'y':my,'variant':choice,'chest':True})
 elif player and s.group != 9000 and pix and s.w>8 and s.h>15:
  arr=np.frombuffer(bytes(pix),dtype=np.uint8).reshape(s.h,s.w)
  skin={(int(x),int(y)) for y,x in np.argwhere((arr>=1)&(arr<=5))}
  blobs=[c for c in components(skin) if len(c)>=7]
  # The face is the upper skin region with dark hair immediately above it.
  candidates=[]
  for c in blobs:
   xs=[p[0] for p in c];ys=[p[1] for p in c];x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys)
   if y0>s.h*.65 or x1-x0<3:continue
   region=arr[max(0,y0-7):y0+2,max(0,x0-3):min(s.w,x1+4)]
   hair=int(((region==15)|(region==11)).sum())
   score=y0 + abs((x0+x1)/2-s.ax)*.12 - min(hair,30)*.65
   if hair>=3:candidates.append((score,x0,y0,x1,y1))
  if candidates:
   _,x0,y0,x1,y1=min(candidates);facew=min(13,max(8,x1-x0+1));fh=13
   # Use the face's top section, excluding exposed chest from the same component.
   fx=x0+max(0,(x1-x0+1-facew)//2);fy=y0
   choice=6 if x0>s.ax+12 else (4 if x1<s.ax-12 else (s.group+s.number)%len(masks))
   m=masks[choice].copy();m.thumbnail((32,14),Image.Resampling.NEAREST)
   canvas=Image.new('P',(s.w+32,s.h+10),0);canvas.paste(Image.frombytes('P',(s.w,s.h),bytes(pix)),(0,0));draw=ImageDraw.Draw(canvas)
   # Opaque face plate underneath the source Tengu brow and nose.
   draw.polygon([(fx,fy),(fx+facew-2,fy),(fx+facew,fy+5),(fx+facew-2,fy+11),(fx+3,fy+12),(fx,fy+8)],fill=241,outline=242)
   mx=fx-1;my=fy-2
   for yy in range(m.height):
    for xx in range(m.width):
     r,g,b,a=m.getpixel((xx,yy))
     if a and 0<=mx+xx<canvas.width and 0<=my+yy<canvas.height:canvas.putpixel((mx+xx,my+yy),240 if r>=160 else 241 if r>=100 else 242)
   # Eye slit is part of the opaque mask, not the original face.
   draw.line((fx+2,fy+3,fx+5,fy+4),fill=243,width=1)
   pix=bytearray(canvas.tobytes());w,h=canvas.size
   placements.append({'group':s.group,'number':s.number,'x':fx,'y':fy,'variant':choice})
  else:w,h=s.w,s.h
 else:w,h=s.w,s.h
 palette=[list(c) for c in (pal if player else (p or pal))]
 if s.group==9000 and s.number in (0,1):
  # Portraits use their own palettes. Give the full face an opaque shaded Tengu plate.
  palette += [[0,0,0]]*(256-len(palette))
  reds=[(232,54,40),(192,16,16),(144,0,8),(88,0,16),(32,0,8),(240,220,164),(0,0,0)]
  for j,c in enumerate(reds):palette[240+j]=list(c)
  portrait=Image.frombytes('P',(w,h),bytes(pix));shape=Image.new('1',(w,h));brush=ImageDraw.Draw(shape)
  if s.number==1:
   polygon=[(22,18),(35,16),(45,19),(51,27),(54,37),(49,46),(43,52),(35,54),(28,49),(24,42),(23,36),(19,31),(19,24)]
  else:
   polygon=[(10,4),(14,3),(18,5),(19,9),(18,14),(14,17),(10,14),(9,10)]
  brush.polygon(polygon,fill=1)
  for yy in range(h):
   for xx in range(w):
    if shape.getpixel((xx,yy)):
     color=palette[portrait.getpixel((xx,yy))];lum=sum(color)/3
     level=0 if lum>195 else 1 if lum>135 else 2 if lum>75 else 3
     portrait.putpixel((xx,yy),240+level)
  dr=ImageDraw.Draw(portrait);dr.line(polygon+[polygon[0]],fill=244,width=1)
  if s.number==1:
   dr.polygon([(27,30),(21,29),(5,34),(3,37),(5,39),(25,36),(30,34)],fill=241,outline=244)
   dr.line([(7,35),(23,32),(28,33)],fill=240,width=1)
   dr.polygon([(23,25),(30,28),(35,26),(33,30),(27,31),(23,29)],fill=244)
   dr.line([(25,28),(30,29),(33,28)],fill=245,width=1);dr.point((29,29),fill=246)
   dr.line([(37,23),(45,23),(48,26)],fill=244,width=2)
   dr.line([(38,27),(43,28)],fill=245,width=1)
   dr.line([(30,44),(36,46),(44,43)],fill=244,width=1)
   dr.line([(33,48),(38,49),(43,46)],fill=240,width=1)
   # Shirt palette is independent of the in-fight palette.
   for j,c in enumerate(palette[:240]):
    rr,gg,bb=c
    if bb>rr*1.25 and bb>gg*1.12:
     lum=int(.21*rr+.72*gg+.07*bb);v=min(240,90+int(lum*1.5));palette[j]=[v,v,min(255,v+4)]
  else:
   dr.polygon([(12,8),(19,8),(24,10),(23,12),(14,11)],fill=241,outline=244)
   dr.line([(12,7),(15,8)],fill=246)
  pix=bytearray(portrait.tobytes())
  placements.append({'group':s.group,'number':s.number,'full_portrait_mask':True})
 img=Image.frombytes('P',(w,h),bytes(pix));img.putpalette([c for rgb in palette for c in rgb]);buf=io.BytesIO();img.save(buf,format='PCX');encoded.append((s,buf.getvalue()))
# SFF v1: materialize links so each pose can carry its own mask.
header=bytearray(512);header[:12]=b'ElecbyteSpr\0';header[12:16]=bytes((0,0,0,1));struct.pack_into('<4I',header,16,len(set(s.group for s,_ in encoded)),len(encoded),512,32)
stream=bytearray(header)
for i,(s,payload) in enumerate(encoded):
 nxt=len(stream)+32+len(payload) if i+1<len(encoded) else 0
 node=bytearray(32);struct.pack_into('<IIhhHHHB',node,0,nxt,len(payload),s.ax,s.ay,s.group,s.number,0,0);stream+=node+payload
(dst/'MrKarate.sff').write_bytes(stream)
(ROOT/'tools/mask_placements.json').write_text(json.dumps(placements,indent=2))
# Rename only this standalone definition, retaining original state/animation files.
definition=(src/'Robert-KOF98.def').read_text(encoding='latin1')
import re
definition=re.sub(r'(?im)^Name\s*=.*','Name = "Mr. Karate"',definition);definition=re.sub(r'(?im)^DisplayName\s*=.*','DisplayName = "Mr. Karate"',definition);definition=re.sub(r'(?im)^Pal.Defaults\s*=.*','Pal.Defaults = 1',definition)
definition=definition.replace('Robert.sff','MrKarate.sff').replace('Robert.snd','MrKarate.snd')
definition=re.sub(r'(?im)^Pal1\s*=.*','Pal1 = act/MrKarate.act',definition)
definition=definition.replace('St7      = Member.cns','St7      = Member.cns\nSt8      = MrKarate.cns')
(dst/'MrKarate.def').write_text(definition,encoding='latin1')
# SND: transform only voice group 10. Impact/projectile/UI audio is unchanged.
b=(src/'Robert.snd').read_bytes();count,offset=struct.unpack_from('<II',b,16);sounds=[]
for i in range(count):
 nxt,size,g,n=struct.unpack_from('<4I',b,offset);wave=b[offset+16:offset+16+size]
 if g==10:
  inp=ROOT/'tools/voice_input.wav';op=ROOT/'tools/voice_output.wav';inp.write_bytes(wave)
  with wavmod.open(io.BytesIO(wave)) as wav: rate=wav.getframerate()
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(inp),'-af',f'asetrate={rate}*0.74,aresample=16000,atempo=1.35135,aecho=0.7:0.5:35|71:0.23|0.13,alimiter=limit=0.85','-ac','1','-ar','16000','-c:a','pcm_s16le',str(op)],check=True)
  wave=op.read_bytes()
 sounds.append((g,n,wave));offset=nxt
snd=bytearray(b[:512]);struct.pack_into('<II',snd,16,len(sounds),512)
for i,(g,n,wave) in enumerate(sounds):
 nxt=len(snd)+16+len(wave) if i+1<len(sounds) else 0;snd+=struct.pack('<4I',nxt,len(wave),g,n)+wave
(dst/'MrKarate.snd').write_bytes(snd)
for f in ('voice_input.wav','voice_output.wav'):(ROOT/'tools'/f).unlink(missing_ok=True)
print('Built',len(encoded),'sprites;',len(placements),'masks;',len(sounds),'sounds; voices',sum(g==10 for g,n,w in sounds))
