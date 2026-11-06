-- Detect forced blank crossing into the visible HUD scanlines in Mesen.
-- Use a ROM copy without an adjacent .sym (Mesen auto-import can crash).
-- KOF_HUD_LOG: output; KOF_HUD_P1/P2: IDs; KOF_HUD_SCREENSHOTS: PNG prefix;
-- KOF_HUD_STAGE: optional forced stage (matching KOF_HUD_SYMBOLS .sym);
-- KOF_HUD_FRAMES: live frames; KOF_HUD_INPUT: walk (default) or attack.
local out=assert(io.open(os.getenv('KOF_HUD_LOG') or '/tmp/kof_hud_flicker.log','w'))
local W=emu.memType.snesWorkRam
local keys,phase,age,total,live,done={},'boot',0,0,0,false
local late,visibleBlank,changes=0,0,0
local lastX=-1
local poses={}
local emptyPoseFrames=0
local screenshotPrefix=os.getenv('KOF_HUD_SCREENSHOTS')
local savedLate,savedStable=false,false
local thisLate=false
local p1=tonumber(os.getenv('KOF_HUD_P1')) or 13
local p2=tonumber(os.getenv('KOF_HUD_P2')) or 0
local limit=tonumber(os.getenv('KOF_HUD_FRAMES')) or 1200
local attack=os.getenv('KOF_HUD_INPUT')=='attack'
local function rd(a)return emu.read(a,W)end
local function wr(a,v)emu.write(a,v,W)end
local forcedStage=tonumber(os.getenv('KOF_HUD_STAGE'))
if forcedStage then
 assert(forcedStage>=0 and forcedStage<10,'invalid stage')
 local address=nil
 for line in io.lines(os.getenv('KOF_HUD_SYMBOLS') or 'kof98-snes.sym')do
  local a,n=line:match('^(%x+)%s+(%S+)$')
  if n=='CampStage' then address=tonumber(a,16)&0xFFFFFF end
 end
 assert(address,'CampStage symbol missing')
 emu.addMemoryCallback(function()wr(0x10C4,forcedStage)end,emu.callbackType.exec,address,address)
end

local function log(s)out:write(s..'\n');out:flush()end
local function finish(code,msg)
 if done then return end
 done=true;log(msg);out:close();emu.stop(code)
end
emu.addEventCallback(function()
 emu.setInput(keys,0);emu.setInput(keys,1)
end,emu.eventType.inputPolled)
emu.addMemoryCallback(function(_address,value)
 if done or phase~='fight' then return end
 local state=emu.getState()
 local line=state['ppu.scanline']
 if line>=1 and line<225 then
  thisLate=true
  if value&128==0 then late=late+1 else visibleBlank=visibleBlank+1 end
  if late+visibleBlank<=30 then
   log(string.format('VISIBLE INIDISP frame=%d line=%d pc=%02X:%04X value=%02X',
    live,line,state['cpu.k'],state['cpu.pc'],value))
  end
 end
end,emu.callbackType.write,0x2100,0x2100)
emu.addEventCallback(function()
 if done then return end
 total=total+1;age=age+1
 local gs=rd(0x1020);keys={}
 if phase=='boot' then
  keys.start=total%40<8
  if gs==6 then wr(0xF070,5)end
  if gs==5 then
   wr(0x1085,p1);wr(0x1086,p2);wr(0x108E,1);wr(0x108F,1)
   wr(0x1090,0);wr(0x1091,0);phase='launch';age=0
  end
 elseif phase=='launch' then
  if gs==1 then
   wr(0x1090,0);wr(0x1091,0)
   phase='fight';age=0;log('FIGHT '..p1..'/'..p2)
  end
 elseif phase=='fight' then
  live=live+1
  poses[rd(0x4008)*256+rd(0x400A)]=true
  if emu.readWord(0x4016,W)==0 or emu.readWord(0x4056,W)==0 then emptyPoseFrames=emptyPoseFrames+1 else emptyPoseFrames=0 end
  if emptyPoseFrames>120 then finish(1,'FAIL fighter has no displayed pose');return end
  if live%180<90 then keys.right=true else keys.left=true end
  if attack then
   -- Both pads move and attack; include quarter circles for projectile FX.
   local beat=live%120
   keys={}
   if beat<7 then keys.down=true
   elseif beat<14 then keys.down=true;keys.right=true
   elseif beat<28 then keys.right=true;keys.y=true
   elseif beat>=60 and beat<72 then keys.x=true
   elseif beat>=90 and beat<110 then keys.up=true end
  end
  if screenshotPrefix and ((thisLate and not savedLate) or (live>30 and not thisLate and not savedStable)) then
   local name=thisLate and 'late' or 'stable'
   local png=assert(io.open(screenshotPrefix..'_'..name..'.png','wb'))
   png:write(emu.takeScreenshot());png:close()
   if thisLate then savedLate=true else savedStable=true end
  end
  thisLate=false
  local x=rd(0x4000)+256*rd(0x4001)
  if x~=lastX then changes=changes+1;lastX=x end
  if gs~=1 then finish(1,'FAIL left practice fight');return end
  if live>=limit then
   local poseCount=0;for _ in pairs(poses)do poseCount=poseCount+1 end
   local active=attack and poseCount>5 or not attack and changes>10
   local ok=late==0 and visibleBlank==0 and active
   finish(ok and 0 or 1,string.format('%s frames=%d late_unblank=%d visible_blank=%d movement=%d poses=%d',
    ok and 'PASS' or 'FAIL',live,late,visibleBlank,changes,poseCount))
  end
 end
 if total>limit+6000 then finish(1,'FAIL timeout '..phase);return end
end,emu.eventType.endFrame)
