-- Run a ROM copy without an adjacent .sym (Mesen's auto-import can crash).
-- mesen --testRunner /absolute/tools/test_mesen_pause_soak.lua /tmp/rom.sfc --timeout=1800
-- KOF_PAUSE_SYMBOLS: matching symbols; KOF_PAUSE_LOG: output; KOF_PAUSE_FRAMES:
-- paused frames per stage (default 25200); KOF_PAUSE_FIRST/LAST_STAGE: 0..9.
local out=assert(io.open(os.getenv('KOF_PAUSE_LOG') or '/tmp/kof_pause_mesen.log','w'))
local symbols={}
for line in io.lines(os.getenv('KOF_PAUSE_SYMBOLS') or 'kof98-snes.sym') do
 local address,name=line:match('^(%x+)%s+(%S+)$')
 if address then symbols[name]=tonumber(address,16) end
end
local W,A=emu.memType.snesWorkRam,emu.memType.spcRam
local limit=tonumber(os.getenv('KOF_PAUSE_FRAMES')) or 25200
local lastStage=tonumber(os.getenv('KOF_PAUSE_LAST_STAGE')) or 9
local frame,phase,age,stage=0,'boot',0,tonumber(os.getenv('KOF_PAUSE_FIRST_STAGE')) or 0
local paused,still,cpuStill,lastFc,lastSong=0,0,0,-1,-1
local done,keys=false,{}
local startX=0
local function rd(a) return emu.read(a,W) end
local function wr(a,v) emu.write(a,v,W) end
local function log(s) out:write(s..'\n');out:flush() end
local function finish(code,msg)
 if done then return end
 done=true
 log(msg)
 log('audiordy='..rd(0x1032)..' spcDP='..emu.read(0x18,A)..','..emu.read(0x19,A)..','..emu.read(0x1A,A)..' driver='..emu.read(0x400,A)..','..emu.read(0x401,A))
 if code~=0 then
  for k,v in pairs(emu.getState()) do
   if k:match('^cpu%.') or k=='spc.pc' then log(k..'='..tostring(v)) end
  end
 end
 out:close();emu.stop(code)
end
emu.addEventCallback(function() emu.setInput(keys,0) end,emu.eventType.inputPolled)
emu.addMemoryCallback(function()
 -- Force the selected stage at its normal loading entry; the rest of
 -- StartFight loads the real PPU resources and the matching SPC module.
 wr(0x10C4,stage)
end,emu.callbackType.exec,assert(symbols.CampStage),symbols.CampStage)
emu.addEventCallback(function()
 if done then return end
 frame=frame+1;age=age+1
 local gs=rd(0x1020)
 local input={}
 if phase=='boot' then
  input.start=frame%40<8
  if gs==6 then wr(0xF070,0) end
  if gs==5 then
   wr(0x1085,13);wr(0x1086,16)
   wr(0x108E,1);wr(0x108F,1);wr(0x1090,0);wr(0x1091,0)
   phase='launch';age=0
  end
 elseif phase=='launch' then
  if gs==1 then
   assert(rd(0x1087)==stage,'wrong stage')
   phase='ready';age=0;log('BEGIN stage '..stage)
  end
 elseif phase=='ready' then
  if age>=60 and age<68 then input.start=true end
  if rd(0x4FB0)==1 then
   phase='paused';age=0;paused=0;still=0;cpuStill=0;lastFc=-1;lastSong=-1
  end
 elseif phase=='paused' then
  paused=paused+1
  local fc=rd(0x1024)
  if fc==lastFc then cpuStill=cpuStill+1 else cpuStill=0 end
  lastFc=fc
  local song=emu.read(0x19,A)+emu.read(0x1A,A)*256
  if song==lastSong then still=still+1 else still=0 end
  lastSong=song
  if paused%600==0 then
   log(string.format('stage=%d paused=%d gs=%d fc=%d cpuStill=%d song=%04X songStill=%d',stage,paused,gs,fc,cpuStill,song,still))
  end
  if cpuStill>180 or still>900 or gs~=1 or rd(0x4FB0)~=1 then
   finish(1,'FAIL stalled stage '..stage);return
  end
  if paused>=limit then phase='resume';age=0 end
 elseif phase=='resume' then
  input.start=age<8
  if rd(0x4FB0)==0 then
   phase='move';age=0;startX=rd(0x4000)+256*rd(0x4001)
  end
 elseif phase=='move' then
  input.right=true
  if age>=60 then
   if gs~=1 or rd(0x4000)+256*rd(0x4001)==startX then
    finish(1,'FAIL resume stage '..stage);return
   end
   log('PASS stage '..stage..': pause music advances, resume movement')
   if stage==lastStage then finish(0,'PASS all stages');return end
   stage=stage+1;phase='launch';age=0
   wr(0x1084,1);wr(0x1082,2);wr(0x1024,59);wr(0x10E6,0);wr(0x1020,0)
   input={}
  end
 end
 keys=input
 if age>6000 and phase~='paused' then finish(1,'FAIL timeout phase '..phase) end
end,emu.eventType.endFrame)
