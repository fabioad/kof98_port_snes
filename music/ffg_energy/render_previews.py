"""Render actual smconv SPC programs with libgme's SPC700/S-DSP emulator.
No MIDI synth, SF2 render, EQ, compressor, or reverb added after emulation.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
import numpy as np
from extract_reference import GME,wav,HERE
from build_candidates import SMCONV,patterns
from spc_export import repair

def render(spc,out,seconds):
    g=GME(spc)
    try:raw=g.render(seconds)
    finally:g.close()
    x=np.frombuffer(raw,dtype='<i2').astype(np.int32)
    report=dict(seconds=seconds,rate=32000,rawPeak=int(abs(x).max()),rawRms=float(np.sqrt(np.mean(x.astype(float)**2))),rawClippedFraction=float(np.mean(abs(x)>=32767)),nonzeroFraction=float(np.mean(x!=0)))
    # Common fixed gain for both versions, not per-song loudness matching.
    pcm=np.clip(np.rint(x*.70),-32768,32767).astype('<i2').tobytes()
    result=subprocess.run(['ffmpeg','-v','error','-y','-f','s16le','-ar','32000','-ac','2','-i','pipe:0','-c:a','libmp3lame','-b:a','192k',str(out)],input=pcm,capture_output=True)
    assert result.returncode==0,result.stderr
    return report

def main():
    result=[]
    for dest in sorted((HERE/'candidates').glob('*.it')):
        seconds=12 if dest.stem=='menu_winner' else 60
        old=HERE/'before'/dest.name
        old_spc=old.with_suffix('.spc')
        subprocess.run([str(SMCONV),'-o',str(old_spc),str(old)],check=True,stdout=subprocess.DEVNULL)
        repair(old_spc,old)
        row=dict(module=dest.name,notesAndTimingIdentical=patterns(old.read_bytes())==patterns(dest.read_bytes()))
        for label,spc in [('antes',old_spc),('ffg',dest.with_suffix('.spc'))]:
            out=HERE/'previews'/f'{dest.stem}_{label}.mp3';row[label]=render(spc,out,seconds);print(dest.stem,label,row[label],flush=True)
        assert row['notesAndTimingIdentical'] and row['ffg']['rawPeak']>0 and row['antes']['rawPeak']>0 and row['ffg']['rawClippedFraction']==0
        result.append(row)
    for i in [1,2,6,13]:
        render(HERE/'reference'/f'song_{i:02d}.spc',HERE/'previews'/f'referencia_ffg_{i:02d}.mp3',45)
    (HERE/'previews/validation.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
