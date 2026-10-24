"""Real SNES execution via the installed Snes9x libretro core, without a GUI.

The WRAM adapter reuses tools/test_fight_remote.py's established engine layout.
This is a native normal-attack regression, not an Arcade comparison.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
import struct
import sys


class Game(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]


class Core:
    def __init__(self, library, rom):
        self.lib = C.CDLL(str(library))
        self.buttons = [set(), set()]
        self.video_frames = 0
        self.capture_video = False
        self.last_frame = None
        self.pixel_format = None
        self.capture_audio = False
        self.audio_samples = 0
        self.audio_nonzero_batches = 0
        self.directory = b'/tmp'
        def env(command, data):
            if command in (9, 31, 30):  # system/assets/save directory
                C.cast(data, C.POINTER(C.c_char_p))[0] = self.directory; return True
            if command == 10:
                self.pixel_format = C.cast(data, C.POINTER(C.c_int))[0]
                return self.pixel_format in (0,1,2)
            if command == 3: C.cast(data, C.POINTER(C.c_bool))[0] = True; return True
            if command == 17: C.cast(data, C.POINTER(C.c_bool))[0] = False; return True
            if command in (11, 16, 18): return True
            return False
        def video(data, w, h, pitch):
            self.video_frames += 1
            if self.capture_video and data:
                self.last_frame = (w, h, pitch, C.string_at(data, pitch * h),
                                   self.pixel_format)
        def audio_batch(data, n):
            if self.capture_audio and data and n:
                self.audio_samples += n
                if any(C.string_at(data, n * 4)):
                    self.audio_nonzero_batches += 1
            return n
        callbacks = [
            ('environment', C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p), env),
            ('video_refresh', C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t), video),
            ('audio_sample', C.CFUNCTYPE(None, C.c_int16, C.c_int16), lambda l,r: None),
            ('audio_sample_batch', C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t), audio_batch),
            ('input_poll', C.CFUNCTYPE(None), lambda:None),
            ('input_state', C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint),
             lambda port,device,index,button: int(port < 2 and button in self.buttons[port])),
        ]
        self.callbacks = []
        for name, typ, fn in callbacks:
            cb = typ(fn); self.callbacks.append(cb)
            setter = getattr(self.lib, 'retro_set_' + name); setter.argtypes = [typ]; setter(cb)
        self.lib.retro_init()
        self.rom = C.create_string_buffer(Path(rom).read_bytes())
        game = Game(str(rom).encode(), C.cast(self.rom,C.c_void_p), len(self.rom)-1, None)
        self.lib.retro_load_game.argtypes=[C.POINTER(Game)]; self.lib.retro_load_game.restype=C.c_bool
        if not self.lib.retro_load_game(C.byref(game)): raise ValueError('Snes9x refused ROM')
        self.lib.retro_get_memory_data.argtypes=[C.c_uint]; self.lib.retro_get_memory_data.restype=C.c_void_p
        self.lib.retro_get_memory_size.argtypes=[C.c_uint]; self.lib.retro_get_memory_size.restype=C.c_size_t
        size = self.lib.retro_get_memory_size(2)
        if size != 131072: raise ValueError(f'unexpected SNES WRAM size: {size}')
        self.ram = (C.c_ubyte * size).from_address(self.lib.retro_get_memory_data(2))
        self.lib.retro_serialize_size.restype=C.c_size_t
        for name in ('retro_serialize','retro_unserialize'):
            fn=getattr(self.lib,name); fn.argtypes=[C.c_void_p,C.c_size_t]; fn.restype=C.c_bool

    def step(self,n=1):
        for _ in range(n): self.lib.retro_run()
    def word(self,addr): return self.ram[addr] | self.ram[addr+1] << 8
    def put(self,addr,value): self.ram[addr],self.ram[addr+1] = value & 255,(value>>8)&255
    def save(self):
        b=C.create_string_buffer(self.lib.retro_serialize_size())
        if not self.lib.retro_serialize(b,len(b)): raise ValueError('serialize failed')
        return b
    def load(self,b):
        if not self.lib.retro_unserialize(b,len(b)): raise ValueError('unserialize failed')
    def close(self): self.lib.retro_unload_game(); self.lib.retro_deinit()


def smoke(core, rom, tables_dir):
    # Can also be executed as a script by the pipeline, with tools on sys.path.
    from calibration.validate import tables
    c = Core(core, rom)
    report = {'core': str(core), 'rom': str(rom), 'tests': [], 'scope': 'native normals; no Neo Geo equivalence'}
    try:
        seen=[]
        for tick in range(2400):
            gs=c.word(0x1020)
            if not seen or seen[-1]!=gs: seen.append(gs)
            if gs==5: break
            c.buttons[0] = {3} if tick % 40 < 4 else ({8} if gs==6 and tick%40<8 else set())
            c.step()
        else: raise AssertionError(f'could not reach character select: states={seen}')
        c.buttons=[set(),set()]; c.step(2)
        selection=c.save()
        # IDs follow CharSelTab in the current native adapter, not MUGEN IDs.
        for char_id,name in enumerate(('kyo','iori','shingo','rugal')):
            c.load(selection); c.buttons=[set(),set()]
            c.ram[0x1085]=char_id; c.ram[0x1086]=(char_id+1)%4
            c.ram[0x1090]=0; c.ram[0x1091]=0  # human control for both fighters
            for tick in range(900):
                c.buttons=[{8} if tick%40<3 else set(),{8} if tick%40<3 else set()]
                c.step()
                if c.word(0x1020)==1 and c.word(0x4008)==0 and c.word(0x4048)==0: break
            else: raise AssertionError(f'{name}: fight did not initialize, state={c.word(0x1020)}')
            c.buttons=[set(),set()]; c.ram[0x1090]=0; c.ram[0x1091]=0; c.step(30)
            base=c.save()
            expected=tables(Path(tables_dir)/(name+'_spr.inc'))[name+'DamageTab']
            for button,sid in ((1,5),(9,6),(0,7),(8,8)):
                c.load(base); c.buttons=[set(),set()]
                c.put(0x4000,100*256); c.put(0x4040,132*256)
                c.put(0x4010,200); c.put(0x4050,200)
                for a in range(0x4100,0x4170): c.ram[a]=0
                trace=[]
                for tick in range(150):
                    c.buttons[0]={button} if tick<2 else set(); c.step()
                    trace.append({'tick':tick, 'state':c.word(0x4008), 'element':c.word(0x400a),
                                  'hp2':c.word(0x4050), 'hitstun2':c.word(0x4068),
                                  'x2':c.word(0x4040)/256, 'atkbox':c.word(0x4024)})
                dealt=200-min(t['hp2'] for t in trace)
                if not any(t['state']==sid for t in trace): raise AssertionError(f'{name}: button failed to enter sid={sid}')
                if dealt != expected[sid]: raise AssertionError(f'{name} sid={sid}: damage={dealt}, table={expected[sid]}')
                if trace[-1]['state'] != 0: raise AssertionError(f'{name} sid={sid}: did not recover')
                report['tests'].append({'character':name,'sid':sid,'damage':dealt,'status':'passed','trace':trace})
        report.update(status='passed', video_frames=c.video_frames, boot_states=seen)
    finally: c.close()
    return report


if __name__ == '__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    p=argparse.ArgumentParser(); p.add_argument('--core',required=True); p.add_argument('--rom',required=True)
    p.add_argument('--tables',required=True); p.add_argument('--output',required=True)
    args=p.parse_args()
    result=smoke(args.core,args.rom,args.tables)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(f"Snes9x: {len(result['tests'])} native normal-attack checks passed")
