-- Replay copied Mesen fight slots against a rebuilt ROM.
-- Use absolute paths for KOF_STATE, KOF_SYMBOLS and KOF_LOG.
-- KOF_RAW=1 resumes the original PC for reproducing the old ROM's failure.
-- Otherwise restart at MainLoop: code addresses move when fixing bad opcodes.
local input = assert(io.open(assert(os.getenv("KOF_STATE")), "rb"))
local save = input:read("*a")
input:close()
local out = assert(io.open(assert(os.getenv("KOF_LOG")), "w"))
local symbols = {}
for line in io.lines(assert(os.getenv("KOF_SYMBOLS"))) do
    local addr, name = line:match("^(%x+)%s+(%S+)$")
    if addr then symbols[name] = tonumber(addr, 16) end
end
local WRAM = emu.memType.snesWorkRam
local loaded, stopped = false, false
local frames, advances, unchanged, gates = 0, 0, 0, 0
local last = -1
local ring, ri = {}, 0
local trace = os.getenv("KOF_TRACE") ~= nil
local traceFrom = tonumber(os.getenv("KOF_TRACE_FROM")) or 0
local complete = false
local function log(message) out:write(message .. "\n"); out:flush() end
local function finish(code, message)
    if stopped then return end
    stopped = true
    log(message)
    emu.stop(code)
end
emu.addMemoryCallback(function(address, value)
    if not loaded then
        loaded = true
        assert(emu.loadSavestate(save))
        if not os.getenv("KOF_RAW") then
            local start = assert(symbols.MainLoop)
            log(string.format("restart=%06X", start))
            emu.setState({["cpu.pc"] = start & 0xFFFF,
                ["cpu.k"] = start >> 16, ["cpu.sp"] = 0x1FFF,
                ["cpu.d"] = 0x1000, ["cpu.dbr"] = 0x7E, ["cpu.ps"] = 0x24})
        end
        log("loaded " .. os.getenv("KOF_STATE"))
        return
    end
    if stopped then return end
    if complete and address == symbols.MainLoop then
        local recovered = os.getenv("KOF_RECOVERED")
        if advances > 1200 and recovered then
            local file = assert(io.open(recovered, "wb"))
            file:write(emu.createSavestate())
            file:close()
        end
        finish(advances > 1200 and 0 or 1, string.format(
            "%s frames=%d advances=%d cancel_calls=%d gs=%d",
            advances > 1200 and "PASS" or "FAIL", frames, advances, gates,
            emu.read(0x1020, WRAM)))
        return
    end
    if address == 0x8008 then
        local s = emu.getState()
        local sp = s["cpu.sp"]
        if trace then
            for i = 1, 80 do
                local item = ring[(ri + i - 1) % 80 + 1]
                if item then log(item) end
            end
            local file = assert(io.open(os.getenv("KOF_LOG") .. ".mss", "wb"))
            file:write(emu.createSavestate()); file:close()
        end
        finish(1, string.format("FAIL BRK/COP/IRQ frame=%d S=%04X return=%02X:%02X%02X",
            frames, sp, emu.read((sp + 4) & 0x1FFF, WRAM),
            emu.read((sp + 3) & 0x1FFF, WRAM), emu.read((sp + 2) & 0x1FFF, WRAM)))
    elseif address == symbols.CancelGate then
        gates = gates + 1
    end
    if trace and frames >= traceFrom and (value == 0x20 or value == 0x22 or value == 0x60
        or value == 0x6B or value == 0x40 or value == 0x00 or value == 0x02
        or value == 0x4C or value == 0x5C or value == 0xDC or value == 0x6C) then
        ri = ri % 80 + 1
        local s = emu.getState()
        ring[ri] = string.format("%06X %02X S=%04X P=%02X D=%04X DB=%02X",
            address, value, s["cpu.sp"], s["cpu.ps"], s["cpu.d"], s["cpu.dbr"])
    end
end, emu.callbackType.exec, 0, 0xFFFFFF)
emu.addEventCallback(function()
    if not loaded or stopped then return end
    frames = frames + 1
    local fc = emu.read(0x1024, WRAM)
    if fc == last then unchanged = unchanged + 1
    else advances = advances + 1; unchanged = 0 end
    last = fc
    if unchanged > 120 then
        finish(1, "FAIL stopped advancing")
    elseif frames >= 1800 then
        complete = true                  -- save only inside an exec callback
    end
end, emu.eventType.endFrame)
