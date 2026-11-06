-- MSU animation progress and exact visible VRAM with configurable SD latency.
-- Use a ROM copy without adjacent .sym. KOF_MSU_DELAY is emulated frames per
-- seek (0 = normal, 2 = cold/contended SD). KOF_MSU_LOG, KOF_MSU_DATA select
-- output and matching .msu; KOF_MSU_P1/P2 default to Daimon/M. Bison.
local out=assert(io.open(os.getenv('KOF_MSU_LOG') or '/tmp/kof_msu_progress.log','w'))
local data=assert(io.open(os.getenv('KOF_MSU_DATA') or 'kof98-snes.msu','rb'))
local W,V,R=emu.memType.snesWorkRam,emu.memType.snesVideoRam,emu.memType.snesMemory
local delay=tonumber(os.getenv('KOF_MSU_DELAY')) or 0
local p1=tonumber(os.getenv('KOF_MSU_P1')) or 13
local p2=tonumber(os.getenv('KOF_MSU_P2')) or 43
local phase,frame,live,ready,done='boot',0,0,0,false
local keys,last,changes,stale,maxStale={}, {-1,-1},{0,0},{0,0},{0,0}
local seeks,pages,late=0,0,0
local function rd(a)return emu.read(a,W)end
local function word(a)return emu.readWord(a,W)end
local function wr(a,v)emu.write(a,v,W)end
local function log(s)out:write(s..'\n');out:flush()end
local function finish(code,msg)
 if done then return end
 done=true;log(msg);data:close();out:close();emu.stop(code)
end
local function checkPage(side,meta)
 local fp=0x4000+(side-1)*64
 -- Character descriptors share bank $3E in the native engine. Runtime
 -- pointers make this check independent of code offsets in the tested ROM.
 local desc=0x3E0000+word(fp+44)
 if emu.read(desc+23,R)&1==0 then return true end
 local record=emu.read(desc+82,R)*65536+meta
 local first,length=emu.readWord(record+1,R),emu.readWord(record+3,R)
 if length<=0 or length>3072 then finish(1,'FAIL invalid visible meta');return false end
 local slice=emu.readWord(desc+20,R)*256+emu.read(desc+22,R)
 local offset=slice*32768+first*32
 data:seek('set',offset)
 local expected=data:read(length)
 if not expected or #expected~=length then finish(1,'FAIL MSU source bounds');return false end
 local base=(side==1 and 0x6000 or 0x7000)*2+rd(fp+27)*32
 for i=0,length-1 do
  if emu.read(base+i,V)~=expected:byte(i+1) then
   finish(1,string.format('FAIL P%d mixed tiles meta=%04X byte=%d',side,meta,i));return false
  end
 end
 pages=pages+1
 return true
end
emu.addEventCallback(function()
 emu.setInput(keys,0);emu.setInput(keys,1)
end,emu.eventType.inputPolled)
emu.addMemoryCallback(function()
 if phase=='walk' then seeks=seeks+1;ready=frame+delay end
end,emu.callbackType.write,0x2003,0x2003)
emu.addMemoryCallback(function(_address,value)
 if phase=='walk' and frame<ready then return value|128 end
end,emu.callbackType.read,0x2000,0x2000)
emu.addMemoryCallback(function(_address,value)
 if phase=='walk' and value&128==0 then
  local line=emu.getState()['ppu.scanline']
  if line>=1 and line<225 then late=late+1 end
 end
end,emu.callbackType.write,0x2100,0x2100)
emu.addEventCallback(function()
 if done then return end
 frame=frame+1;keys={};local gs=rd(0x1020)
 if phase=='boot' then
  keys.start=frame%40<8;if gs==6 then wr(0xF070,5)end
  if gs==5 then
   wr(0x1085,p1);wr(0x1086,p2);wr(0x108E,1);wr(0x108F,1)
   wr(0x1090,0);wr(0x1091,0);phase='launch'
  end
 elseif phase=='launch' then
  if gs==1 then phase='warm';live=0 end
 elseif phase=='warm' then
  live=live+1
  if live>=60 then
   wr(0x1090,0);wr(0x1091,0)             -- practice initializes the opponent as CPU
   phase='walk';live=0;log('latency frames='..delay..' pair='..p1..'/'..p2)
  end
 elseif phase=='walk' then
  live=live+1
  if live%120<60 then keys.right=true else keys.left=true end
  for side=1,2 do
   local meta=word(0x4016+(side-1)*64)
   if meta~=0 and meta~=last[side] then
    changes[side]=changes[side]+1;last[side]=meta;stale[side]=0
    if not checkPage(side,meta) then return end
   elseif rd(0x4018+(side-1)*64)~=0 then stale[side]=stale[side]+1
   else stale[side]=0 end               -- an AIR hold with no upload is intentional
   maxStale[side]=math.max(maxStale[side],stale[side])
  end
  if live%60==0 then
   log(string.format('frame=%d seeks=%d changes=%d/%d stale=%d/%d pages=%d late=%d',
    live,seeks,changes[1],changes[2],stale[1],stale[2],pages,late))
  end
  if live>=360 then
   local ok=changes[1]>5 and changes[2]>5 and maxStale[1]<120 and maxStale[2]<120 and late==0
   finish(ok and 0 or 1,string.format('%s changes=%d/%d max_hold=%d/%d pages=%d seeks=%d late=%d',
    ok and 'PASS' or 'FAIL',changes[1],changes[2],maxStale[1],maxStale[2],pages,seeks,late))
  end
 end
 if frame>6000 then finish(1,'FAIL launch timeout '..phase)end
end,emu.eventType.endFrame)
