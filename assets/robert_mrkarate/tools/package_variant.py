from pathlib import Path
import shutil,re
r=Path(__file__).resolve().parents[1];src=r/'MrKarate-KOF98';dst=r/'Robert-KOF98'
mapping={p.name:'Robert-Mr-Karate-'+p.name for p in src.iterdir() if p.suffix in ('.cmd','.cns','.air')}
mapping.update({'MrKarate.sff':'Robert-Mr-Karate.sff','MrKarate.snd':'Robert-Mr-Karate.snd'})
for old,new in mapping.items():shutil.copy2(src/old,dst/new)
shutil.copy2(src/'act/MrKarate.act',dst/'act/MrKarate.act')
s=(src/'MrKarate.def').read_text(encoding='latin1')
for old,new in sorted(mapping.items(),key=lambda i:-len(i[0])):
 s=re.sub(r'(?im)(=\s*)'+re.escape(old)+r'\s*$',lambda m:m[1]+new,s)
# Keep the mask colours visible in all twelve selectable palettes.
for match in list(re.finditer(r'(?im)^(Pal\d+\s*=\s*)(act/[^\n]+)',s)):
 old=match[2].strip()
 if old=='act/MrKarate.act':continue
 data=(dst/old).read_bytes();colors=[list(data[i:i+3]) for i in range(0,768,3)][::-1]
 for i,c in {240:[192,0,0],241:[128,0,8],242:[72,0,16],243:[0,0,0]}.items():colors[i]=c
 new='act/MrKarate_'+Path(old).name
 (dst/new).write_bytes(bytes(c for rgb in colors[::-1] for c in rgb))
 s=s.replace(match[1]+match[2],match[1]+new)
(dst/'Robert-Mr-Karate.def').write_text(s,encoding='latin1')
print('Packaged Robert-KOF98/Robert-Mr-Karate.def')
