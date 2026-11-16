#!/usr/bin/env python3
"""Native Mr. Karate inputs: contact budgets, volleys, aerial recovery.

Uses real generated motions/pad inputs, not forced attack states. The engine
telemetry counts actual successful launches and contacts independently of
HUD rendering. Output includes per-move paths for diagnosing input misses.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'tools'))
import audit_specials_headless as audit
from calibration.headless import Core
from test_counter_grab_headless import boot_select, enter_fight, HIDDEN

CORE='/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so'
ACTIVE,HITS,DAMAGE,SHOTS=0xF1D0,0xF1D9,0xF1DA,0xF1DC


def run(all_moves=False):
    HIDDEN['mrkarate']={10,11}
    c=Core(CORE,ROOT/'kof98-snes.sfc')
    info=audit.character('mrkarate',ROOT/'build/gen_fight')
    rules={}
    for row in sorted(info['rules'],key=lambda r:len(r['elements'])):
        rules.setdefault(row['sid'],row)
    cases=sorted(rules) if all_moves else [50,52,58,66,85,87,109,110]
    records=[]
    try:
        sel=boot_select(c)
        enter_fight(c,sel,'mrkarate','iori')
        c.ram[0x403b]=255
        base=c.save()
        for air in (False,True):
            for sid in cases:
                if sid not in rules:continue
                rule=copy.deepcopy(rules[sid])
                if air:rule['row'][3]=4   # harness jump; ROM row stays ground-only
                result=audit.attempt(c,base,info,rule,distance=26,hold=2,
                    limit=700,power=3000,air_height=36)
                result.update(sid=sid,air=air,hits=c.ram[HITS],
                    budget_damage=c.word(DAMAGE),shots=c.word(SHOTS),
                    active=c.ram[ACTIVE],height=c.word(0x4002))
                records.append(result)
                print(json.dumps({k:result[k] for k in ('sid','air','entered','hits','budget_damage','shots','active','height','last_states','path') }),flush=True)
        out=ROOT/'build/mrkarate_regression/combat.json'
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(records,indent=2)+'\n')
        for record in records:
            assert record['game_state']==1,record
            assert not record['active'],record
            if record['hits']:
                expected=50 if record['budget_damage']>9 else 5
                assert record['hits']==expected,record
                assert record['budget_damage']==(48 if expected==50 else 9),record
            if record['entered']:
                assert record['height']==0,record
                assert record['last_states']==[0,0],record
                assert not any(record['grab_flags']),record
        assert any(r['hits']==5 for r in records),'no real special contact'
        assert any(r['hits']==50 for r in records),'no real super contact'
        assert any(r['shots']==3 for r in records),'no three-shot volley'
        assert any(r['air'] and r['entered'] for r in records),'no airborne ground cast'
        print('PASS Mr. Karate: 5/50 contacts, 9/48 HP budgets, three shots, aerial landing',flush=True)
    finally:c.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--all-moves',action='store_true')
    run(p.parse_args().all_moves)
