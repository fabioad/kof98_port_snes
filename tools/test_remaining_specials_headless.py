#!/usr/bin/env python3
"""Exercise repaired source command families on a frozen native ROM.

Each root must be reached by pad input, damage the opponent and recover with
both capture flags clear. A damaging unrelated command does not count.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_specials_headless as audit
from calibration.headless import Core
from remaining_specials import STRIKES, GRABS
from test_counter_grab_headless import boot_select, enter_fight


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('snapshot',type=Path)
    ap.add_argument('--chars',nargs='+')
    ap.add_argument('--out',default='repairs.json')
    args=ap.parse_args()
    p=args.snapshot; names=args.chars or list(STRIKES)
    report={'rom_sha256':audit.sha256(p/'kof98-snes.sfc'),'characters':{}}
    core=Core('/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so',p/'kof98-snes.sfc')
    try:
        select=boot_select(core)
        for name in names:
            info=audit.character(name,p/'tables')
            enter_fight(core,select,name,'kyo');core.ram[0x1090]=core.ram[0x1091]=0;core.step(24)
            base=core.save();cases=[]
            for root in sorted(set(STRIKES.get(name,{}))|set(GRABS.get(name,{}))):
                rules=[r for r in info['rules'] if info['metadata'][r['sid']]['state']==root]
                attempts=[]
                for rule in rules:
                    for setup in ({'distance':24,'input_game_ticks':True},
                                  {'distance':18,'hold':2,'keep_direction':False},
                                  {'distance':40,'hold':3,'keep_direction':True},
                                  {'distance':64,'hold':2,'keep_direction':False},
                                  {'distance':24,'combine_finish':True}):
                        result=audit.attempt(core,base,info,rule,limit=1600,complement=True,**setup)
                        status=audit.classify(result,info['metadata'][rule['sid']])
                        attempts.append(dict(status=status,result=result,rule=rule))
                        if status=='hit_and_recovered':break
                    if attempts and attempts[-1]['status']=='hit_and_recovered':break
                best=next((r for r in attempts if r['status']=='hit_and_recovered'),attempts[-1] if attempts else {'status':'missing_command'})
                case=dict(root=root,**best,attempts=attempts);cases.append(case)
                print(name,root,best['status'],best.get('result',{}).get('final_damage'),flush=True)
            report['characters'][name]=cases
            (p/args.out).write_text(json.dumps(report,indent=2)+'\n')
    finally:core.close()
    return int(any(c['status']!='hit_and_recovered' for cs in report['characters'].values() for c in cs))


if __name__=='__main__':raise SystemExit(main())
