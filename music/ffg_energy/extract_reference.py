"""Extract the local Final Fight Guy ROM through Snes9x's actual APU state.
No downloaded soundtrack or replacement notes. Playback stub selects resident songs.
"""
import ctypes as C
import hashlib,json,re,struct,sys,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from calibration.headless import Core
HERE=Path(__file__).resolve().parent
REF=HERE/'reference'
CORE='/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so'
ROM=ROOT/'music/examples/Final Fight Guy (Japan).sfc'

def state_apu(state):
    pos=state.index(b'SND:');n=int(state[pos+4:pos+10]);snd=state[pos+11:pos+11+n]
    assert len(snd)==66560
    # Snes9x bapu SMP state: 64K RAM + 41 little-endian 32-bit fields.
    regs=struct.unpack_from('<41I',snd,65536)
    return bytearray(snd[:65536]),bytearray(snd[65700:65828]),regs

def spc_file(ram,dsp,regs,track=None):
    out=bytearray(66048);out[:33]=b'SNES-SPC700 Sound File Data v0.30';out[33:37]=bytes([26,26,27,30])
    pc=regs[3];a,x,y,sp=regs[5],regs[6],regs[7],regs[4]
    psw=sum(bool(regs[8+i])<<(7-i) for i in range(8))
    if track is not None:
        # Driver routine $03e0 loads an ID from A. Silence command polling
        # after selection because an SPC file has no 65816 host handshake.
        # Only unused $ff00 RAM and the host-poll RET are patched.
        ram=bytearray(ram);ram[0x3c8]=0x6f;ram[0xff00:0xff09]=bytes([0xe8,track,0x3f,0xe0,3,0x5f,0x28,3]);pc=0xff00
    struct.pack_into('<H',out,0x25,pc);out[0x27:0x2c]=bytes([a,x,y,psw,sp]);out[0x100:0x10100]=ram;out[0x10100:0x10180]=dsp
    out[0x102:0x104]=ram[2:4]
    return out

class GME:
    def __init__(self,path,rate=32000):
        self.rate=rate;self.lib=C.CDLL('libgme.so.0');self.ptr=C.c_void_p()
        self.lib.gme_open_file.argtypes=[C.c_char_p,C.POINTER(C.c_void_p),C.c_int];self.lib.gme_open_file.restype=C.c_char_p
        self.lib.gme_start_track.argtypes=[C.c_void_p,C.c_int];self.lib.gme_start_track.restype=C.c_char_p
        self.lib.gme_play.argtypes=[C.c_void_p,C.c_int,C.POINTER(C.c_int16)];self.lib.gme_play.restype=C.c_char_p
        self.lib.gme_delete.argtypes=[C.c_void_p]
        for err in [self.lib.gme_open_file(str(path).encode(),C.byref(self.ptr),rate),self.lib.gme_start_track(self.ptr,0)]:
            if err:raise RuntimeError(err.decode())
        self.lib.gme_ignore_silence.argtypes=[C.c_void_p,C.c_int];self.lib.gme_ignore_silence(self.ptr,1)
    def render(self,seconds):
        result=[]
        for sec in range(seconds):
            b=(C.c_int16*(self.rate*2))();err=self.lib.gme_play(self.ptr,len(b),b)
            if err:raise RuntimeError(err.decode())
            result.append(C.string_at(b,len(b)*2))
        return b''.join(result)
    def close(self):self.lib.gme_delete(self.ptr)

def wav(path,pcm,rate=32000):
    with wave.open(str(path),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm)

def decode_brr(ram,start):
    out=[];p1=p2=0;pos=start;blob=bytearray()
    while pos+9<=65536:
        block=ram[pos:pos+9];blob+=block;h=block[0];shift=h>>4;fil=h&12
        for b in block[1:]:
            for nib in [b>>4,b&15]:
                n=nib if nib<8 else nib-16;s=(n<<shift)>>1 if shift<=12 else (n&~2047)
                q2=p2>>1
                if fil>=8:
                    s+=p1-q2
                    if fil==8:s+=(q2>>4)+((-3*p1)>>6)
                    else:s+=((-13*p1)>>7)+((3*q2)>>4)
                elif fil:s+=(p1>>1)+((-p1)>>5)
                s=max(-32768,min(32767,s));s=((s*2+32768)&65535)-32768
                out.append(s);p2,p1=p1,s
        pos+=9
        if h&1:return np.asarray(out,dtype='<i2'),bytes(blob),bool(h&2)
    raise ValueError('unterminated BRR')

def main():
    REF.mkdir(exist_ok=True,parents=True)
    core=Core(CORE,ROM)
    try:core.step(600);state=core.save().raw
    finally:core.close()
    ram,dsp,regs=state_apu(state)
    (REF/'apu_ram.bin').write_bytes(ram);(REF/'apu_dsp.bin').write_bytes(dsp);(REF/'runtime.spc').write_bytes(spc_file(ram,dsp,regs))
    assert ram[0x3f2:0x3f5]==bytes.fromhex('1c5df5') and ram[0xa2d:0xa30]==bytes.fromhex('8d06cf')
    assert dsp[0x5d]==0x48
    tracks=[]
    # These IDs have eight valid resident track pointers and music priority 0.
    for i in range(1,80):
        p=int.from_bytes(ram[0xe02+i*2:0xe04+i*2],'big')
        if not p or ram[p]!=0:continue
        ptrs=[int.from_bytes(ram[p+1+j*2:p+3+j*2],'big') for j in range(8)]
        if not all(0xe00<=x<0x4800 for x in ptrs):continue
        file=REF/f'song_{i:02d}.spc';file.write_bytes(spc_file(ram,dsp,regs,i));g=GME(file);pcm=g.render(5);g.close()
        peak=int(np.abs(np.frombuffer(pcm,dtype='<i2').astype(np.int32)).max())
        tracks.append(dict(id=i,header=hex(p),pointers=ptrs,file=file.name,testPeak=peak))
    samples=[]
    for i in range(28):
        start,loop=struct.unpack_from('<HH',ram,0x4800+i*4);pcm,brr,looping=decode_brr(ram,start)
        (REF/f'sample_{i:02d}.brr').write_bytes(brr)
        with wave.open(str(REF/f'sample_{i:02d}.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(32000);f.writeframes(pcm.tobytes())
        srcn,a1,a2,gain=ram[0x4a00+i*6:0x4a04+i*6];pitch=int.from_bytes(ram[0x4a04+i*6:0x4a06+i*6],'big',signed=True)
        samples.append(dict(id=i,address=hex(start),romOffsets=[hex(m.start()) for m in re.finditer(re.escape(brr),ROM.read_bytes())],brrBytes=len(brr),pcmLength=len(pcm),loopStart=(loop-start)//9*16,loopEnd=len(pcm),looping=looping,adsr1=hex(a1),adsr2=hex(a2),gain=hex(gain),pitchScale=pitch,source=srcn))
    report=dict(rom=str(ROM.relative_to(ROOT)),romSha256=hashlib.sha256(ROM.read_bytes()).hexdigest(),core=CORE,songTable='0x0e02',instrumentTable='0x4a00',sampleDirectory='0x4800',tracks=tracks,samples=samples)
    (REF/'extraction.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Extracted',len(tracks),'music sequences and',len(samples),'BRR samples; peaks',[t['testPeak'] for t in tracks])
if __name__=='__main__':main()
