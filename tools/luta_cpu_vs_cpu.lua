-- Mesen2 testRunner script used by tools/luta_cpu_vs_cpu.py.
--
-- Boots the current KOF98 SNES ROM, pins both selections, forces CPU vs CPU
-- and writes a machine-readable RESULT line plus an optional screenshot.
-- Configuration comes from environment variables so the Python front-end can
-- run one fight per Mesen process without editing this file.
local W = emu.memType.snesWorkRam

local function env(name, default)
    local value = os.getenv(name)
    if value == nil or value == "" then return default end
    return value
end

local logPath = assert(os.getenv("KOF_LUTA_LOG"), "KOF_LUTA_LOG missing")
local shotPath = env("KOF_LUTA_SHOT", "")
local p1 = tonumber(env("KOF_LUTA_P1", "0"))
local p2 = tonumber(env("KOF_LUTA_P2", "1"))
local level = tonumber(env("KOF_LUTA_LEVEL", "8"))
local maxFrames = tonumber(env("KOF_LUTA_MAXFRAMES", "7200"))

local out = assert(io.open(logPath, "w"))
local function log(message)
    out:write(message .. "\n")
    out:flush()
end
local function rd(address) return emu.read(address, W) end
local function rw(address) return emu.readWord(address, W) end
local function wr(address, value) emu.write(address, value, W) end

local frame = 0
local phase = "boot"
local lastGs = -1
local keys = {}
local hold = 0
local cool = 0
local done = false
local maxW1, maxW2, rounds = 0, 0, 0
local lastPng = nil

-- At least one CPU flag must be active when StartFight runs so the engine
-- latches CPU play.  The other side is enabled after the Mr. Karate sanitizer
-- has already run, otherwise the hidden form is converted back to Robert.
local earlyCpu1 = (p1 == 53) and 0 or 1
local earlyCpu2 = (p1 == 53) and 1 or 0

local function tapStart()
    if cool > 0 then return end
    keys = { start = true }
    hold = 3
    cool = 9
end

local function finish(reason)
    if done then return end
    done = true
    local hp1, hp2 = rw(0x4010), rw(0x4050)
    local winner = "draw"
    if maxW1 > maxW2 then
        winner = "p1"
    elseif maxW2 > maxW1 then
        winner = "p2"
    elseif hp1 > hp2 then
        winner = "p1"
    elseif hp2 > hp1 then
        winner = "p2"
    end
    if reason == "timeout" then winner = "timeout" end
    local shot = ""
    if shotPath ~= "" then
        local png = lastPng
        if png == nil or png == "" then png = emu.takeScreenshot() end
        if png ~= nil and png ~= "" then
            local file = assert(io.open(shotPath, "wb"))
            file:write(png)
            file:close()
            shot = shotPath
        end
    end
    log(string.format(
        "RESULT reason=%s winner=%s p1=%d p2=%d wins1=%d wins2=%d " ..
        "rounds=%d frames=%d hp1=%d hp2=%d shot=%s",
        reason, winner, p1, p2, maxW1, maxW2, rounds, frame,
        hp1, hp2, shot))
    out:close()
    emu.stop(0)
end

emu.addEventCallback(function()
    emu.setInput(keys, 0)
end, emu.eventType.inputPolled)

emu.addEventCallback(function()
    frame = frame + 1
    if hold > 0 then
        hold = hold - 1
        if hold == 0 then keys = {} end
    end
    if cool > 0 then cool = cool - 1 end

    local gs = rd(0x1020)
    if gs ~= lastGs then
        log(string.format("GS frame=%d gs=%d phase=%s", frame, gs, phase))
        lastGs = gs
    end

    if phase == "boot" then
        if gs == 6 then
            wr(0x107A, 1)                  -- MSU detected
            wr(0xF070, 1)                  -- mode menu: SINGLE VS
            phase = "menu"
            tapStart()
        elseif gs == 14 or gs == 9 or gs == 7 or gs == 0 then
            tapStart()
        end
    elseif phase == "menu" then
        if gs == 6 then
            wr(0x107A, 1)
            wr(0xF070, 1)
            tapStart()
        elseif gs == 5 then
            phase = "select"
        end
    elseif phase == "select" then
        if gs == 5 then
            -- Keep both picks pinned while the select assets settle.  The
            -- engine reads these bytes when both lock latches are set.
            wr(0x1085, p1)
            wr(0x1086, p2)
            wr(0x108E, 1)
            wr(0x108F, 1)
            wr(0x1090, earlyCpu1)
            wr(0x1091, earlyCpu2)
            wr(0x10EB, level)
        elseif gs == 4 or gs == 1 then
            wr(0x1090, 1)
            wr(0x1091, 1)
            wr(0x10EB, level)
            if gs == 4 then tapStart() end
            phase = "fightload"
        end
    elseif phase == "fightload" then
        if gs == 4 then
            wr(0x1090, 1)
            wr(0x1091, 1)
            tapStart()
        elseif gs == 1 then
            wr(0x1090, 1)
            wr(0x1091, 1)
            wr(0x10EB, level)
            phase = "fight"
            log(string.format(
                "FIGHT p1=%d p2=%d sel=%d/%d cpu=%d/%d hp=%d/%d",
                p1, p2, rd(0x1085), rd(0x1086), rd(0x1090),
                rd(0x1091), rw(0x4010), rw(0x4050)))
        end
    elseif phase == "fight" then
        -- wins can advance during the round-result screen (gs=2) and may be
        -- reset when the match returns to select, so sample it every frame.
        local w1, w2 = rd(0x1080), rd(0x1081)
        if w1 > maxW1 then
            maxW1 = w1
            rounds = math.max(rounds, maxW1 + maxW2)
            log(string.format("ROUND p1 %d-%d", maxW1, maxW2))
        end
        if w2 > maxW2 then
            maxW2 = w2
            rounds = math.max(rounds, maxW1 + maxW2)
            log(string.format("ROUND p2 %d-%d", maxW1, maxW2))
        end
        if gs == 2 and shotPath ~= "" then
            local png = emu.takeScreenshot()
            if png ~= nil and png ~= "" then lastPng = png end
        end
        if maxW1 >= 2 or maxW2 >= 2 then
            if shotPath ~= "" and lastPng == nil then
                local png = emu.takeScreenshot()
                if png ~= nil and png ~= "" then lastPng = png end
            end
            finish("match")
        elseif gs == 5 or gs == 6 then
            if rounds > 0 then finish("return") end
        end
        if frame % 600 == 0 then
            log(string.format(
                "FIGHT frame=%d gs=%d wins=%d-%d hp=%d/%d state=%d/%d",
                frame, gs, rd(0x1080), rd(0x1081), rw(0x4010),
                rw(0x4050), rd(0x4008), rd(0x4048)))
        end
    end

    if frame >= maxFrames then finish("timeout") end
end, emu.eventType.endFrame)
