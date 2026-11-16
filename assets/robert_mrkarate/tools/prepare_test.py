from pathlib import Path
import shutil,re
r=Path(__file__).resolve().parents[1];t=r/'ikemen-test';d=t/'chars/Robert-KOF98'
shutil.copytree(r/'Robert-KOF98',d,dirs_exist_ok=True)
# Position/setup states are confined to the test install.
p=d/'Robert-Mr-Karate-MrKarate.cns';s=p.read_text()
for i,(state,y) in enumerate([(1100, 0), (1200, 0), (1400, 0), (3100, 0), (3000, 0), (1000, 0), (1200, -25), (1000, -25), (3200, 0), (1500, -25), (1100, -25), (1250, -25), (1400, -25), (1600, -25), (1300, -25), (1050, -25), (1010, -25), (1110, -25), (1210, -25), (1260, -25), (1450, -25), (1510, -25), (1610, -25), (1310, -25), (3020, 0), (3120, 0), (3220, 0)]):
 s+=f'''\n[Statedef {99000+i}]
type = S
physics = N
movetype = I
ctrl = 0
velset = 0,0
facep2 = 1
[State 0, position]
type = PosSet
trigger1 = Time = 0
x = EnemyNear,Pos X - 42
y = {y}
[State 0, enter move]
type = ChangeState
trigger1 = Time = 1
value = {state}
'''
p.write_text(s)
p=t/'chars/kfm/kfm.cns';shutil.copy2(Path('/run/media/fabio/Dados/Fabio/Ikemen_GO-dev-linux/chars/kfm/kfm.cns'),p);s=p.read_text();s+='\n[Statedef 99099]\ntype = S\nphysics = N\nvelset = 0,0\n[State 0, reset]\ntype = PosSet\ntrigger1 = 1\nx = 60\ny = 0\n[State 0, stand]\ntype = ChangeState\ntrigger1 = Time = 1\nvalue = 0\nctrl = 1\n';p.write_text(s)
p=t/'save/config.ini';s=p.read_text();s=re.sub(r'(?im)^Lua\s*=.*','Lua = dofile("tests/runtime.lua")',s);s=re.sub(r'(?im)^ScreenshotFolder\s*=.*','ScreenshotFolder = screenshots/',s);p.write_text(s)
