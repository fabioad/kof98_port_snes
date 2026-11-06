"""Compile missing special phases into bounded native timelines.

Keep command identities and source cels; flatten internal source state changes
so variants do not consume a different runtime slot for every intermediate pose.
Grab damage remains conditional on a real capture and uses held-victim slots.
"""
import re
import json
import os
from pathlib import Path

# root: (source phases, native damage). Helpers are handled by copying their
# HitDef onto the actor's animation, as elsewhere in the native port.
STRIKES = {
 'iori': {3200: ((3200,3210),32)},
 'shingo': {3050: ((3050,3051),48),3150: ((3150,),42)},
 'rugal': {},
 'omegarugal': {1025:((1025,1026,1030),20),2800:((2800,2801,2803),42),
               3000:((3000,),40),6000:((6000,),48)},
 'saisyu': {1200:((1200,1201),18),1210:((1210,1211),22),3150:((3150,3160,3165),48)},
 'heidern': {3010:((3010,3011),38),3050:((3050,3051),48),
             1200:((1200,1201),22),1210:((1210,1211),26)},
 'leona': {1200:((1200,),18),1201:((1201,),22),1400:((1400,),18),1401:((1401,),22),
           3150:((3150,3151,3152),42)},
 'mature': {1100:((1100,1110,1120),22),1320:((1320,1310),24),1420:((1310,),22)},
 'vice': {3100:((3100,3110,3020),34),3200:((3200,3210,3220),44)},
 'daimon': {},
 'king': {1300:((1300,1310),22),1350:((1350,1360),26)},
 'kim': {3100:((3100,3105),34),3110:((3110,3105),38),3120:((3120,3125),48)},
 'chang': {1000:((1000,),18),1010:((1010,),22),1350:((1300,1310),24),3500:((3500,3510),48)},
 'choi': {3050:((3050,3051),40),3060:((3060,3061),44)},
 'yashiro': {2000:((2000,),20),2100:((2100,),24),3000:((3000,3001,3002),38),
             3010:((3010,3001,3002),44),3500:((3500,3501,3502),48)},
 'shermie': {7000:((7000,7010),20),7050:((7050,7060),24),8050:((8050,8060),48)},
 'chris': {1200:((1200,1210),22),1250:((1250,1260),26),1400:((1400,1410,1420),24),
           1450:((1450,1460,1470),30),2150:((2150,2155),34),2250:((2250,2260,2270),44),
           7100:((7100,7110),24),7150:((7150,7160),28),8150:((8150,8160),48),8155:((8155,8160),48)},
 'mrbig': {1300:((1300,1301),20),1310:((1310,1311,1312),28),
           3200:((3200,3201,3202),38),3210:((3210,3201,3202),44)},
}
# Root command -> (capture HitDef source, held source sequence, damage).
GRABS = {
 'rugal': {1400:(1400,(1402,),24),1410:(1410,(1402,),28),
           3000:(3000,(3002,),38),3010:(3010,(3002,),42),
           3200:(3200,(3202,3203),38),3210:(3210,(3202,3203),42),
           3250:(3250,(3251,3203),48),3150:(3150,(3152,3153,3154,3105),48)},
 'omegarugal': {1070:(1071,(1074,1075,1076),38),1085:(1086,(1074,1075,1076),42),
                1090:(1091,(1094,1095,1096),48),2400:(2401,(2402,2403),38),
                2600:(2600,(2601,),24),2700:(2700,(2701,),30)},
 'heidern': {1300:(1300,(1310,1311,1312),24)},
 'daimon': {1200:(1200,(1210,),26),1300:(1300,(1310,),26),
            1500:(1505,(1520,),26),1510:(1505,(1520,),30),
            1700:(1700,(1710,),28),3000:(3000,(3010,),42)},
 'shermie': {1400:(1405,(1420,1425),26),1450:(1455,(1470,1475),30)},
}
# Explicit actions for source header expressions/helper-only attack states.
ACTIONS = {('shingo',3150):3151,('chang',1350):1300,
           ('choi',3051):3051,('choi',3061):3051,
           ('shermie',1475):1425,('shermie',1420):1420,
           ('mature',1420):1310,('yashiro',3502):3502}
HIT_SOURCES = {('leona',1200):1210,('leona',1201):1211,
               ('leona',1400):1450,('leona',1401):1455,
               ('chang',1000):1005,('chang',1010):1005,
               ('omegarugal',3000):3002,('omegarugal',6000):6004}


def repair(name,cfg,anims,air,moves,headers,states,binds,acts,posadds):
    if name not in STRIKES and name not in GRABS:
        return []
    # 78..84 dispatch as defensive/block states in the native engine. Source
    # MAX attacks imported there must move to an actual attacking slot.
    for sid,root in list(cfg['moves'].items()):
        if not 78 <= sid <= 84 or root not in (set(STRIKES.get(name,{})) | set(GRABS.get(name,{}))):
            continue
        other=next((s for s,st in cfg['moves'].items() if st==root and not 78<=s<=84),None)
        if other is None:
            other=next((s for s in list(range(48,67))+[68]+list(range(114,106,-1)) if s not in cfg['moves']),None)
            if other is None:raise ValueError(f'{name}: no attack slot for {root}')
            cfg['moves'][other]=root;anims[other]=anims[sid]
            cfg.setdefault('anims',{})[other]=anims[sid]
        del cfg['moves'][sid]
    if name=='rugal':
        # MAX Screamer is flattened below; only its private old chain is
        # retired. The normal Screamer's 103..106 chain remains intact.
        for old in (107,108,109):
            cfg['moves'].pop(old,None)
        cfg['extra_trans']=[t for t in cfg.get('extra_trans',[]) if t[0] not in (107,108,109)]
    changed=[]; counter=0
    source_headers={st:dict(h) for st,h in headers.items()}
    source_states=dict(states)
    def finish(root):
        # Retain the source power metadata used to distinguish MAX/SDM in
        # the command list and MAX-mode descriptor; discard old branches.
        return [c for c in source_states.get(root,())
                if c.get('type','').lower()=='poweradd'] + [
            {'type':'ChangeState','value':'0','triggers':['AnimTime = 0'],
             'trigger_groups':['trigger1']}]

    def action(st, fallback):
        explicit=ACTIONS.get((name,st))
        expr=source_headers.get(st,{}).get('anim','')
        try: anum=explicit if explicit is not None else int(expr)
        except ValueError:
            # AIR numbers at the front of expressions refer to the body's
            # own action; never evaluate arbitrary source code.
            m=re.match(r'^\s*(\d+)',expr)
            anum=int(m[1]) if m else fallback
        return anum if anum in air and air[anum][0] else fallback

    def timeline(phases,resident,held=False):
        frames=[]; windows=[]; sound=[]; offensive=None
        for st in phases:
            anum=action(st,resident)
            source=list(air[anum][0])
            # Indefinite MUGEN holds require a source ChangeState. The
            # flattened sequence has an explicit exit, so bound those holds.
            for local,f in enumerate(source):
                g,n,x,y,t,flip,atk,hurt=f
                if g<0: continue
                frame=(g,n,x,y,max(1,min(8,t if t>0 else 4)),flip,atk,hurt)
                if atk and offensive is None:offensive=len(frames)
                frames.append(frame)
                if held:
                    ws=[(dx,dy) for lo,hi,dx,dy in binds.get(st,()) if lo<=local<=hi]
                    windows.append(ws[-1] if ws else (windows[-1] if windows else (24,0)))
            if len(frames)>120:
                raise ValueError(f'{name} {phases}: special timeline exceeds native element budget')
        if not frames:raise ValueError(f'{name}: empty special {phases}')
        return frames,windows,offensive

    def install(sid,root,phases,damage,held=False):
        nonlocal counter
        resident=anims[sid];frames,windows,hit=timeline(phases,resident,held)
        anum=65100+counter;counter+=1
        if anum in air:raise ValueError('special synthetic action collision')
        if not held and hit is None:
            # Helper-only attacks use the actor's own visible strike pose.
            hit=max(0,len(frames)-2)
            f=frames[hit];frames[hit]=(*f[:6],[(-12,-100,70,0)],f[7])
        air[anum]=(frames,-1);anims[sid]=cfg.setdefault('anims',{})[sid]=anum
        cfg.get('slices',{}).pop(sid,None);cfg.get('frame_cap',{}).pop(sid,None)
        cfg.get('state_vel',{}).pop(sid,None)
        # Flattening owns the source phases now; stale transitions must not
        # jump back into an old/incomplete runtime sequence.
        cfg.setdefault('trans_drop',[]).append((sid,0))
        cfg['extra_trans']=[t for t in cfg.get('extra_trans',[]) if t[0]!=sid]
        cfg['extra_trans'].append((sid,0,0,0))
        cfg.get('slice_hits',{}).pop(sid,None)
        states[root]=finish(root)
        headers[root]=dict(headers.get(root,{}),anim=str(anum),velset='0,0')
        posadds[root]=[]
        acts[root]=[(0,5,0,0),(0,15,0,0)]
        if held:
            # Single impact replaces source life expressions on a 1000/1500
            # life bar. It can only execute with a successfully held victim.
            impact=max(0,len(frames)-2)
            acts[root]+=[(impact,3,-damage,0)]
            binds[root]=[(i,i,dx,dy) for i,(dx,dy) in enumerate(windows)]
            row={'active':0,'damage':0,'gdamage':0,'p2state':255,'throw':0}
        else:
            source=HIT_SOURCES.get((name,root))
            candidates=[source] if source else list(reversed(phases))
            row=next((dict(moves[st]) for st in candidates if st in moves),{})
            row.update(active=hit+1,damage=damage,gdamage=2,fall=1,
                       p1mugen=-1,p2state=255,throw=0,gvx=512,gvy=-1024)
        cfg.setdefault('hitdef_override',{})[sid]=row
        cfg.setdefault('slice_damage',{})[sid]=0 if held else damage
        # Do not retain source flurry resets or full-width super projectiles
        # after replacing the timeline; otherwise the first hit duplicates.
        cfg.get('movehit_reset',{}).pop(root,None)
        changed.append((sid,root,phases))

    for root,(phases,damage) in STRIKES.get(name,{}).items():
        for sid,st in list(cfg['moves'].items()):
            if st==root:
                install(sid,root,phases,damage)
    shared={}
    shared_damage={}
    for root,(capture,phases,damage) in GRABS.get(name,{}).items():
        roots=[sid for sid,st in cfg['moves'].items() if st==root and sid not in shared.values()]
        if not roots:continue
        # Allocate from the high end, leaving 103..106 available to reversal
        # wiring. No existing special/counter/throw slot may be replaced.
        key=phases
        if key not in shared:
            slot=next((s for s in list(range(114,102,-1))+[68,66,65,64,63,62,61,60] if s not in cfg['moves']),None)
            if slot is None:raise ValueError(f'{name}: no free held-special slot for {root}')
            synth=22000+counter
            cfg['moves'][slot]=synth;anims[slot]=anims[roots[0]]
            install(slot,synth,phases,damage,True);shared[key]=slot;shared_damage[key]=damage
        slot=shared[key];synth=cfg['moves'][slot]
        for sid in roots:
            # Retain the source capture animation and configure its actual
            # HitDef rather than inflicting damage on a whiff.
            if capture!=root:
                a=action(capture,anims[sid]);anims[sid]=cfg['anims'][sid]=a
            row=dict(moves.get(capture,{}))
            extra=max(0,damage-shared_damage[key])
            capture_damage=extra+1 if extra else 0
            row.update(active=1,damage=capture_damage,gdamage=0,throw=1,p2state=76,p1mugen=synth)
            cfg.setdefault('hitdef_override',{})[sid]=row
            cfg.setdefault('slice_damage',{})[sid]=capture_damage
            a=anims[sid];fs,loop=air[a];fs=list(fs)
            if fs:
                f=fs[0];fs[0]=(*f[:6],[(-8,-105,45,0)],f[7]);air[a]=(fs,loop)
            states[root]=finish(root)
            cfg['extra_trans']=[t for t in cfg.get('extra_trans',[]) if t[0]!=sid]
    # The source also exposed hold phases as standalone commands. Route
    # them through the capture root, preserving the damage precondition.
    if name=='daimon':cfg.setdefault('cmd_remap',{}).update({3010:3000,3160:3100})
    output=os.environ.get('KOF_OUT_DIR')
    if output:
        Path(output,f'{name}_remaining_specials.json').write_text(json.dumps({
            'moves':cfg['moves'],'repairs':changed},indent=2)+'\n')
    return changed
