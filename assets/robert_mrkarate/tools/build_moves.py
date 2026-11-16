from pathlib import Path
import re
R=Path(__file__).resolve().parents[1];D=R/'MrKarate-KOF98';S=R/'Robert-KOF98'
def sections(s):return re.split(r'(?im)(?=^\[State(?:def)?\s)',s)
# Air command access for every special and super, retaining original command names.
s=(S/'Robert.cmd').read_text(encoding='latin1');out=[]
for b in sections(s):
 v=re.search(r'(?im)^value\s*=\s*(\d+)',b)
 if v and 1000<=int(v[1])<4000 and re.search(r'(?im)^type\s*=\s*ChangeState',b):
  b=re.sub(r'(?im)^triggerall\s*=\s*statetype\s*!=\s*A[^\n]*','; MrKarate: available on the ground and in the air',b)
  # Close-range throw-special can also catch airborne targets.
  b=re.sub(r'(?im)^triggerall\s*=\s*\(p2statetype = S \|\| p2statetype = C\)[^\n]*','triggerall = p2statetype != L',b)
 out.append(b)
(D/'Robert.cmd').write_text(''.join(out),encoding='latin1')
for name in ('Robert-S.cns','Robert-H.cns'):
 s=(S/name).read_text(encoding='latin1');out=[]
 for b in sections(s):
  if re.search(r'(?im)^type\s*=\s*HitDef',b):
   # Connect using the original attack hitbox; branch to actual multi-hit follow-up.
   for key in ('damage','p1stateno','p2stateno','p2getp1state','fall','air.fall','fall.damage','numhits'):
    b=re.sub(r'(?im)^'+re.escape(key)+r'\s*=.*\n?','',b)
   b+='\ndamage = 0, 0\np1stateno = 9000\np2stateno = 9010\np2getp1state = 1\nfall = 0\nair.fall = 0\nnumhits = 1\n'
  if re.search(r'(?im)^type\s*=\s*Helper',b) and re.search(r'(?im)^name\s*=\s*"Proj"',b):
   b=re.sub(r'(?im)^stateno\s*=.*','stateno = 9300',b);b=re.sub(r'(?im)^id\s*=.*','id = 9300',b)
   b=re.sub(r'(?im)^pos\s*=.*','pos = 42, -82',b)
   for j,yy in enumerate((-82,-62,-42)):
    clone=re.sub(r'(?im)^\[State[^\]]*\]',f'[State 0, MrKarate volley {j+1}]',b)
    clone=re.sub(r'(?im)^pos\s*=.*',f'pos = {42-j*8}, {yy}',clone);out.append(clone)
   continue
  if re.search(r'(?im)^type\s*=\s*PosSet',b) and re.search(r'(?im)^y\s*=\s*0\s*$',b): b+='\ntriggerall = Pos Y >= 0\n'
  if re.search(r'(?im)^type\s*=\s*ChangeState',b):b=re.sub(r'(?im)^value\s*=\s*0\s*$',r'value = ifelse(!IsHelper && Pos Y < 0, 50, 0)',b)
  out.append(b)
 (D/name).write_text(''.join(out),encoding='latin1')
# Add airborne state maintenance to the original -2 controller.
s=(S/'Robert-2-3.cns').read_text(encoding='latin1');extra='''
[State -2, MrKarate remember airborne cast]
type = VarSet
triggerall = !IsHelper
triggerall = StateNo = [1000,3999]
triggerall = StateNo != 1300 && StateNo != 1310
triggerall = PrevStateNo != [1000,3999]
trigger1 = Time <= 1
var(52) = Pos Y < 0

[State -2, MrKarate remember cast height]
type = VarSet
triggerall = !IsHelper
triggerall = StateNo = [1000,3999]
triggerall = var(52) = 1
triggerall = PrevStateNo != [1000,3999]
trigger1 = Time <= 1
fvar(19) = Pos Y

[State -2, MrKarate hold airborne attack height]
type = PosSet
triggerall = !IsHelper
triggerall = StateNo = [1000,3999]
triggerall = var(52) = 1
trigger1 = MoveType = A
y = fvar(19)

[State -2, MrKarate suspend airborne attack]
type = VelSet
triggerall = !IsHelper
triggerall = StateNo = [1000,3999]
triggerall = var(52) = 1
trigger1 = MoveType = A
y = 0

[State -2, MrKarate reset airborne cast]
type = VarSet
triggerall = !IsHelper
trigger1 = StateNo != [1000,3999]
var(52) = 0

[State -2, MrKarate air specials]
type = StateTypeSet
triggerall = !IsHelper
triggerall = StateNo = [1000,3999]
trigger1 = Pos Y < 0
statetype = A
physics = N

[State -2, MrKarate air gravity]
type = VelAdd
triggerall = !IsHelper
triggerall = StateNo = [1000,3999]
triggerall = StateType = A
triggerall = !var(52) || MoveType != A
trigger1 = Pos Y < 0
y = .28

[State -2, MrKarate land safely]
type = ChangeState
triggerall = !IsHelper
triggerall = StateNo = [1000,3999]
triggerall = StateType = A
triggerall = !var(52) || MoveType != A
triggerall = Time > 1
trigger1 = Pos Y >= 0 && Vel Y >= 0
value = 52
ctrl = 0

[State -2, MrKarate clear projectile lock]
type = VarSet
triggerall = !IsHelper
trigger1 = RoundState != 2
trigger2 = NumHelper(9300) = 0
var(54) = 0
'''
i=re.search(r'(?im)^\[Statedef\s+-3',s);s=s[:i.start()]+extra+s[i.start():] if i else s+extra
(D/'Robert-2-3.cns').write_text(s,encoding='latin1')
(D/'MrKarate.cns').write_text('''; MrKarate: real 5/50-hit follow-ups, with an absolute per-combo damage budget.
; Reserved formerly-unused root vars: 26=count,45=limit,46=budget,49=air,54=volley lock.
[Statedef 9000]
type = S
movetype = A
physics = N
ctrl = 0
velset = 0,0
anim = 9050
juggle = 0
sprpriority = 3

[State 9000, Hit limit]
type = VarSet
trigger1 = Time = 0
var(45) = ifelse(IsHelper, var(45), ifelse(PrevStateNo >= 3000,50,5))

[State 9000, Count starter]
type = VarSet
trigger1 = Time = 0
var(26) = 1

[State 9000, Budget]
type = VarSet
trigger1 = Time = 0 && NumTarget
var(46) = ifelse(var(45) = 50, floor(Target,LifeMax / 3.0), 60)

[State 9000, Air flag]
type = VarSet
trigger1 = Time = 0
var(49) = Pos Y < 0

[State 9000, Claim volley]
type = ParentVarSet
triggerall = IsHelper
trigger1 = Time = 0
var(54) = 1

[State 9000, Projectile combo appearance]
type = ChangeAnim
triggerall = IsHelper
trigger1 = Anim != 9051
value = 9051

[State 9000, Target bind]
type = TargetBind
trigger1 = NumTarget
pos = 38,-35

[State 9000, No push]
type = PlayerPush
trigger1 = 1
value = 0

[State 9000, First impact damage]
type = TargetLifeAdd
trigger1 = Time = 0 && NumTarget
value = -floor(var(46)*1.0/var(45))
absolute = 1
kill = 1

[State 9000, Real followup]
type = HitDef
triggerall = NumTarget
triggerall = var(26) < var(45)
trigger1 = Time % 4 = 1
attr = A, HA
hitflag = MAF
; Followup is only reached after an unguarded starter.
guardflag =
priority = 7, Hit
damage = 0,0
pausetime = 0,0
sparkno = s6002
sparkxy = 0,-45
hitsound = s1,1
ground.type = High
ground.hittime = 20
ground.velocity = 0,0
air.hittime = 20
air.velocity = 0,0
yaccel = .5
fall = 0
air.fall = 0
p2stateno = 9010
p2getp1state = 1
numhits = 1
getpower = 0,0
givepower = 0,0

[State 9000, Followup damage]
type = TargetLifeAdd
triggerall = Time > 0
trigger1 = MoveHit = 1 && NumTarget
value = -(floor(var(46)*(var(26)+1.0)/var(45))-floor(var(46)*var(26)*1.0/var(45)))
absolute = 1
kill = 1

[State 9000, Count actual impacts]
type = VarAdd
triggerall = Time > 0
trigger1 = MoveHit = 1
var(26) = 1

[State 9000, Release victim]
type = TargetState
trigger1 = var(26) >= var(45)
trigger2 = Time > 240
value = 9020

[State 9000, Release volley lock]
type = ParentVarSet
triggerall = IsHelper
trigger1 = var(26) >= var(45)
trigger2 = Time > 240 || !NumTarget
var(54) = 0

[State 9000, Remove projectile]
type = DestroySelf
triggerall = IsHelper
trigger1 = var(26) >= var(45)
trigger2 = Time > 240 || !NumTarget

[State 9000, Finish]
type = ChangeState
triggerall = !IsHelper
trigger1 = var(26) >= var(45)
trigger2 = Time > 240 || !NumTarget
value = ifelse(var(49),50,0)
ctrl = 1

[Statedef 9010]
type = A
movetype = H
physics = N
velset = 0,0
ctrl = 0

[State 9010, Hit pose]
type = ChangeAnim2
trigger1 = Time = 0
value = 9052

[State 9010, Safety release]
type = ChangeState
trigger1 = Time > 250
value = 9020

[Statedef 9020]
type = A
movetype = H
physics = N
velset = -3,-4
ctrl = 0

[State 9020, Own falling animation]
type = ChangeAnim
trigger1 = Time = 0
value = ifelse(SelfAnimExist(5050),5050,5000)
[State 9020, Gravity]
type = VelAdd
trigger1 = 1
y = .5
[State 9020, Touch down]
type = PosSet
trigger1 = Pos Y >= 0 && Vel Y > 0
y = 0
[State 9020, Restore own landing]
type = SelfState
trigger1 = Pos Y >= 0 && Vel Y > 0
value = 5100

[Statedef 9300]
type = A
movetype = A
physics = N
anim = 9051
ctrl = 0
velset = 6,0
sprpriority = 4

[State 9300, Choose budget]
type = VarSet
trigger1 = Time = 0
var(45) = ifelse(Root,StateNo >= 3000,50,5)

[State 9300, Projectile starter]
type = HitDef
trigger1 = Time = 0
attr = A, SP
hitflag = MAF
guardflag = MA
priority = 4, Hit
damage = 0,0
pausetime = 0,0
sparkno = s6002
hitsound = s1,1
guardsound = s2,1
ground.type = High
ground.hittime = 20
ground.velocity = 0,0
air.hittime = 20
air.velocity = 0,0
fall = 0
p1stateno = 9000
p2stateno = 9010
p2getp1state = 1
numhits = 1

[State 9300, Remove stray volley members]
type = DestroySelf
trigger1 = Time > 0 && Root,var(54) > 0
trigger2 = MoveGuarded
trigger3 = Time > 100
trigger4 = FrontEdgeDist < -80
''',encoding='ascii')
air=(S/'Robert.air').read_text(encoding='latin1')
air+='''
; MrKarate rapid combo: original Robert punch/kick graphics with persistent attack box.
[Begin Action 9050]
Clsn1Default: 1
 Clsn1[0] = 5,-120,90,30
Clsn2Default: 1
 Clsn2[0] = -20,-100,20,0
210,1,0,0,4
240,3,0,0,4
200,1,0,0,4
230,2,0,0,4
LoopStart
210,1,0,0,4
240,3,0,0,4
200,1,0,0,4
230,2,0,0,4

[Begin Action 9051]
Clsn1Default: 1
 Clsn1[0] = -18,-25,75,35
Clsn2Default: 1
 Clsn2[0] = -12,-18,16,18
LoopStart
1001,2,0,0,3
1001,3,0,0,3
1001,4,0,0,3

[Begin Action 9052]
Clsn2Default: 1
 Clsn2[0] = -25,-100,25,20
5000,0,0,0,-1
'''
(D/'Robert.air').write_text(air,encoding='latin1')
print('Moves rebuilt.')
