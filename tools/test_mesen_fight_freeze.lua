-- Replay a frozen fight from a copied Mesen state. Run from the repo root:
-- KOF_FREEZE_STATE=/path/to/slot.mss mesen --testRunner \
--   /path/to/repo/tools/test_mesen_fight_freeze.lua /tmp/rom.sfc --timeout=60
-- KOF_FREEZE_REPLAY=evade starts a state captured immediately before AI_evade.
-- KOF_FREEZE_RECOVERED optionally names a new state to save after 60 frames.
-- The input state is never overwritten. Use symbols from the tested ROM.
local statePath = assert(os.getenv("KOF_FREEZE_STATE"), "set KOF_FREEZE_STATE")
local symPath = os.getenv("KOF_FREEZE_SYMBOLS") or
    ((os.getenv("PWD") or ".") .. "/kof98-snes.sym")
local outputPath = os.getenv("KOF_FREEZE_LOG") or "/tmp/kof_fight_freeze.log"
local out = assert(io.open(outputPath, "w"))
local symbols = {}
for line in io.lines(symPath) do
    local address, name = line:match("^(%x+)%s+(%S+)$")
    if address then symbols[name] = tonumber(address, 16) end
end
local start = assert(symbols.MainLoop)
if os.getenv("KOF_FREEZE_REPLAY") == "evade" then
    start = assert(symbols.AI_evade)
end
local input = assert(io.open(statePath, "rb"))
local save = input:read("*a")
input:close()
local loaded, stopped, recovered = false, false, false
local frames, advances, evades, unchanged = 0, 0, 0, 0
local lastFrame = -1
local WRAM = emu.memType.snesWorkRam
local function log(message) out:write(message .. "\n"); out:flush() end
local function finish(code, message)
    if stopped then return end
    stopped = true
    log(message)
    emu.stop(code)
end
emu.addMemoryCallback(function()
    if loaded then return end
    loaded = true
    assert(emu.loadSavestate(save))
    local registers = { ["cpu.pc"] = start & 0xFFFF, ["cpu.k"] = start >> 16 }
    if os.getenv("KOF_FREEZE_REPLAY") ~= "evade" then
        -- The original slot already has S=$2002 before NMI and has lost
        -- its return address. Restart at the top-level frame boundary.
        registers["cpu.sp"] = 0x1FFF
        registers["cpu.d"] = 0x1000
        registers["cpu.dbr"] = 0x7E
        registers["cpu.ps"] = 0x24
    end
    emu.setState(registers)
    -- Loading redirects the current opcode fetch after its exec callback.
    if os.getenv("KOF_FREEZE_REPLAY") == "evade" then evades = 1 end
    log("loaded " .. statePath)
end, emu.callbackType.exec, 0x8000, 0x8000)
emu.addMemoryCallback(function()
    if not loaded or stopped then return end
    local s = emu.getState()
    local file = assert(io.open(outputPath .. ".mss", "wb"))
    file:write(emu.createSavestate())
    file:close()
    local sp = s["cpu.sp"]
    local frame = {}
    for i = 1, 4 do frame[i] = emu.read((sp + i) & 0x1FFF, WRAM) end
    log(string.format("interrupt return=%02X:%02X%02X P=%02X",
        frame[4], frame[3], frame[2], frame[1]))
    finish(1, string.format("FAIL BRK/COP/IRQ frame=%d S=%04X", frames, s["cpu.sp"]))
end, emu.callbackType.exec, 0x8008, 0x8008)
emu.addMemoryCallback(function()
    if loaded and not stopped then evades = evades + 1 end
end, emu.callbackType.exec, assert(symbols.AI_evade), symbols.AI_evade)
emu.addMemoryCallback(function()
    local path = os.getenv("KOF_FREEZE_RECOVERED")
    if not loaded or stopped or recovered or frames < 60 or not path then return end
    recovered = true
    local file = assert(io.open(path, "wb"))
    file:write(emu.createSavestate())
    file:close()
    log("recovered state " .. path)
end, emu.callbackType.exec, assert(symbols.MainLoop), symbols.MainLoop)
emu.addEventCallback(function()
    if not loaded or stopped then return end
    frames = frames + 1
    local fc = emu.read(0x1024, WRAM)
    local gs = emu.read(0x1020, WRAM)
    if fc ~= lastFrame then advances = advances + 1; unchanged = 0
    else unchanged = unchanged + 1 end
    lastFrame = fc
    if gs == 1 and unchanged > 120 then
        finish(1, "FAIL fight stopped advancing at frame " .. frames)
    elseif frames >= 1800 then
        local passed = evades > 0 and advances > 300
        finish(passed and 0 or 1, string.format(
            "%s frames=%d advances=%d evades=%d gs=%d",
            passed and "PASS" or "FAIL", frames, advances, evades, gs))
    elseif frames % 300 == 0 then
        log(string.format("frames=%d advances=%d evades=%d gs=%d", frames, advances, evades, gs))
    end
end, emu.eventType.endFrame)
