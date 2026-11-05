"""Replace only IT sample payloads/headers; musical patterns and keymaps are immutable."""
import hashlib,json,math,re,shutil,struct,subprocess,wave
from pathlib import Path
import numpy as np
from spc_export import repair
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SMCONV=Path('/run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6/devkitsnes/tools/smconv')
REF=HERE/'reference';META=json.loads((REF/'extraction.json').read_text())

def layout(d):
    o,n,s,p=struct.unpack_from('<4H',d,32);off=192+o
    ip=list(struct.unpack_from(f'<{n}I',d,off));off+=n*4
    sp=list(struct.unpack_from(f'<{s}I',d,off));off+=s*4
    pp=list(struct.unpack_from(f'<{p}I',d,off))
    return o,ip,sp,pp

def patterns(d):
    o,ip,sp,pp=layout(d)
    return d[192:192+o]+b''.join(d[p:p+8+struct.unpack_from('<H',d,p)[0]] if p else b'EMPTY' for p in pp)

def old_pcm(d,sp):
    flags=d[sp+18];length,ls,le,c5=struct.unpack_from('<4I',d,sp+48);ptr=struct.unpack_from('<I',d,sp+72)[0]
    assert not flags&12,'compressed/stereo unsupported'
    if not length:return np.zeros(0),ls,le,c5
    signed=d[sp+46]&1
    x=np.frombuffer(d, ('<i2' if signed else '<u2') if flags&2 else ('i1' if signed else 'u1'),length,ptr).astype(float)
    if not signed:x-=32768 if flags&2 else 128
    if not flags&2:x*=256
    return x,ls,le,c5

def root_octave(x,ls,le,rate,flags):
    # Match the existing sample's octave register, rather than transposing notes.
    if flags&16 and le-ls>=16:
        segment=x[ls:le]
    else:segment=x[:min(len(x),max(64,int(rate*.35)))]
    if len(segment)<16:return 0
    spec=np.abs(np.fft.rfft(segment*np.hanning(len(segment))))**2
    freq=np.fft.rfftfreq(len(segment),1/rate)
    scores=[]
    for octv in range(-3,3):
        f0=261.625565*2**octv;score=0
        for h in range(1,13):
            k=np.argmin(abs(freq-h*f0));lo=max(1,k-1);hi=min(len(spec),k+2)
            score+=float(spec[lo:hi].max(initial=0))/h
        scores.append((score,octv))
    return max(scores)[1]

def source(i):
    with wave.open(str(REF/f'sample_{i:02d}.wav'),'rb') as f:x=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)
    s=META['samples'][i]
    return x,s['loopStart'],s['loopEnd'],4000*(s['pitchScale']/256)*(0x10b0/4096)

def normalize(x,peak=.80):
    if not len(x):return b''
    x=x-np.mean(x)
    x*=peak*32767/max(1,float(abs(x).max()))
    return np.clip(np.rint(x),-32768,32767).astype('<i2').tobytes()

def drum(kind,key):
    sid=7 if kind=='kick' else 8 if kind=='tom' else 6
    x,_,_,_=source(sid)
    actual_rate={'kick':16000,'tom':18000,'snare':26000,'clap':28000,'rim':30000,'hat':32000,'openhat':26000,'crash':22000}.get(kind,26000)
    if kind in ('hat','openhat','crash','rim'):
        # Derive a short metallic noise articulation from the same Capcom snare.
        x=np.r_[0,np.diff(x)]
        duration={'hat':.032,'openhat':.085,'crash':.12,'rim':.018}[kind]
        target=int(actual_rate*duration)
        x=np.tile(x,max(1,math.ceil(target/len(x))))[:target]
        x*=np.exp(-np.arange(len(x))/(len(x)*.27))
    elif kind=='clap':x*=np.exp(-np.arange(len(x))/(len(x)*.55))
    # Fade only one-shots; leave the BRR-derived melodic loop boundaries exact.
    fade=min(64,len(x));x[-fade:]*=np.linspace(1,0,fade)
    c5=round(actual_rate/2**((key-60)/12))
    return normalize(x,.80 if kind in ('kick','snare') else .61),0,0,c5,sid,kind

KIT=[('kick',57),('kick',58),('kick',59),('rim',61),('snare',62),('clap',63),('tom',64),('hat',65),('rim',66),('openhat',67),('crash',69),('tom',76)]

def replace_one(src,dest):
    d=bytearray(src.read_bytes());o,ips,sps,pps=layout(d);original_patterns=patterns(d);original_instruments=[bytes(d[p:p+554]) for p in ips]
    roles={}
    for ip in ips:
        name=d[ip+32:ip+58].split(b'\0')[0].decode('latin1').lower()
        ids=sorted({d[ip+65+n*2] for n in range(120)}-{0})
        for k,sid in enumerate(ids):roles.setdefault(sid,(name,k))
    # Reserve S-DSP mixer headroom before emulation, rather than hiding clipping in MP3.
    d[48]=max(1,round(d[48]*.75))
    changes=[]
    for sid,sp in enumerate(sps,1):
        x,ls,le,c5=old_pcm(d,sp)
        if not len(x):continue
        name,k=roles.get(sid,('unknown',0));flags=d[sp+18]
        if '909 kit' in name:
            if k>=len(KIT):continue
            new,loop,loopend,newc5,refid,role=drum(*KIT[k])
        elif any(n in name for n in ['hat','snare','kick','cymbal','tom']):
            role='openhat' if 'open' in name else 'hat' if 'hat' in name else 'kick' if 'kick' in name else 'tom' if 'tom' in name else 'snare'
            # Fixed remap in existing IT instruments: find the played sample key.
            keys=[d[ip+64+n*2] for ip in ips for n in range(120) if d[ip+65+n*2]==sid]
            key=max(set(keys),key=keys.count) if keys else 60
            new,loop,loopend,newc5,refid,role=drum(role,key)
        else:
            refid=4 if ('bass' in name or ' bs' in name) else 3 if 'pad' in name or 'string' in name else 2 if 'piano' in name else 12 if 'santur' in name else 9 if 'arp' in name else 0 if 'lead' in name else 1
            xx,loop,loopend,rate=source(refid);octave=root_octave(x,ls,le,c5,flags)
            newc5=round(rate*2**octave);new=normalize(xx,.76);role=name
        # Append new PCM so every pattern and instrument pointer stays in place.
        ptr=len(d);d.extend(new)
        d[sp+18]=3|(16 if loopend>loop else 0);d[sp+46]=1
        struct.pack_into('<4I',d,sp+48,len(new)//2,loop,loopend,newc5)
        struct.pack_into('<2I',d,sp+64,0,0);struct.pack_into('<I',d,sp+72,ptr)
        # Retain sample/global volumes, envelopes, keymaps, channel pan and effects.
        label=('FFG '+role)[:25].encode('ascii','replace');d[sp+20:sp+46]=label.ljust(26,b'\0')
        changes.append(dict(sample=sid,role=role,referenceSample=refid,c5Speed=newc5,loop=[loop,loopend],pcmBytes=len(new)))
    assert patterns(d)==original_patterns
    assert all(d[p:p+554]==v for p,v in zip(ips,original_instruments))
    dest.write_bytes(d)
    r=subprocess.run([str(SMCONV),'-V','-o',str(dest.with_suffix('.spc')),str(dest)],capture_output=True,text=True)
    report=r.stdout+r.stderr;(dest.with_suffix('.smconv.log')).write_text(report)
    m=re.search(r'Total:\s*\[\s*(\d+) bytes\]',report)
    assert r.returncode==0 and m and 'module is too big' not in report.lower(),report
    size=int(m.group(1));assert size<=44500,(dest,size)
    placement=repair(dest.with_suffix('.spc'),dest)
    return dict(module=dest.name,source=str(src.relative_to(ROOT)),beforeSha256=hashlib.sha256(src.read_bytes()).hexdigest(),patternSha256=hashlib.sha256(original_patterns).hexdigest(),patternsAndInstrumentsIdentical=True,aramBytes=size,globalVolume=d[48],spcPlacement=placement,changes=changes)

def main():
    result=[]
    files=sorted((ROOT/'build/gen_audio/it').glob('stg*.it'))+sorted((ROOT/'assets/audio/menu').glob('*.it'))
    for src in files:
        label=src.name if src.name.startswith('stg') else 'menu_'+src.name
        backup=HERE/'before'/label
        dest=HERE/'candidates'/label
        if backup.exists():
            # After integration the active file is the approved candidate.
            # Always regenerate from the immutable pre-FFG baseline.
            approved=ROOT/'assets/audio/ffg'/label
            allowed=[backup.read_bytes()]
            if approved.exists():allowed.append(approved.read_bytes())
            assert src.read_bytes() in allowed,'Active module changed outside the reviewed profile'
        else:shutil.copy2(src,backup)
        row=replace_one(backup,dest)
        row['source']=str(src.relative_to(ROOT))
        result.append(row);print(label,row['aramBytes'],'ARAM bytes',len(row['changes']),'new samples',flush=True)
    (HERE/'candidates/manifest.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
