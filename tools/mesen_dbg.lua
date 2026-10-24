-- Mesen debug overlay: reads the KOF98 debug registers and draws them
-- on screen every frame. Load via Tools > Debug > Lua Script.
-- Marker map:
--   $4614 (M): $30 select->fight, $40 StartFight, $41 pals ok,
--              $42 EnterState ok, $43 CampStage ok, $44 StagePick ok,
--              $45 StageMusic ok, $50 TeamSwap
--   $4615 (S): $11 opening, $12 title, $13 menu, $14 endings
--   GS = gamestate (0 title/intermission, 5 select, 4 intro, 1 fight,
--                    2 ko, 6 menu, 7 opening, 8 endings)

local function memtype()
    local ok, t = pcall(function() return emu.memType.snesMemory end)
    if ok and t ~= nil then return t end
    ok, t = pcall(function() return emu.memType.cpuMemory end)
    if ok and t ~= nil then return t end
    return emu.memType.debuggerMemory
end
local MT = memtype()

local function rd(a)
    local ok, v = pcall(function() return emu.read(a, MT) end)
    if ok then return v end
    return -1
end

local function draw()
    local gs  = rd(0x7E1020)
    local m   = rd(0x7E4614)
    local scr = rd(0x7E4615)
    local fc  = rd(0x7E1024)
    local g   = rd(0x7EF040)
    local txt = string.format(
        "GS=%02X M=%02X S=%02X FC=%02X GM=%d",
        gs < 0 and 255 or gs,
        m < 0 and 255 or m,
        scr < 0 and 255 or scr,
        fc < 0 and 255 or fc,
        g < 0 and 255 or g)
    local ok = pcall(function()
        emu.drawString(4, 4, txt, 0xFFFFFF, 0xFF000000)
    end)
    if not ok then
        pcall(function() emu.drawText(4, 4, txt, 0xFFFFFF, 0xFF000000) end)
    end
end

emu.addEventCallback(draw, emu.eventType.endFrame)
