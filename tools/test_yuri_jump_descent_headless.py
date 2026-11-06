#!/usr/bin/env python3
"""Yuri's three jumps share the clean final descent cel without new CHR."""
import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight
from capture_pair_headless import save_frame


def main():
    text = (ROOT/'build/gen_fight/yuri_spr.inc').read_text()
    ids = json.loads((ROOT/'build/gen_fight/yuri_sprite_ids.json').read_text())
    clean = ids['40,4']
    for sid in (4,15,16):
        match = re.search(rf'^yuriAnim{sid}:\n(.*?)(?=^\w+:|\Z)',text,re.M|re.S)
        assert match, sid
        sprites = [int(s) for s in re.findall(r'^\s*\.dw (\d+)\s*$',match[1],re.M)]
        assert sprites[-1] == clean, (sid,sprites[-1],clean)
        assert sprites[-2] == clean, (sid,'final pose is not held')
    c=Core('/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so',ROOT/'kof98-snes.sfc')
    try:
        enter_fight(c,boot_select(c),'yuri','kyo')
        c.ram[0x1090]=c.ram[0x1091]=0;c.step(30);base=c.save()
        c.capture_video=True
        out=ROOT/'build/yuri_jump_descent';out.mkdir(exist_ok=True)
        for label,keys in [('neutral',{4}),('forward',{4,7}),('back',{4,6})]:
            c.load(base);c.buttons[0]=keys
            states=set();airborne=False;landed=False
            for tick in range(100):
                c.step()
                if tick==3:c.buttons[0]=set()
                state=c.ram[0x4008];states.add(state)
                if c.word(0x4002):airborne=True
                if airborne and not c.word(0x4002) and state==0:landed=True
                if tick in (29,32,35):save_frame(c.last_frame,out/f'{label}_{tick}.png')
            assert airborne and landed, (label,states)
            print(f'PASS Yuri {label} jump: clean descent, landed; states={sorted(states)}')
    finally:c.close()

if __name__=='__main__':main()
