#!/usr/bin/env python3
"""Drive the PVSnesLib fight ROM through RetroArch's UDP interfaces."""
import argparse
import os
from pathlib import Path
import socket
import struct
import time
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "kof98-snes.sfc"
CFG = ROOT / "build" / "remote_input.cfg"
STATE = Path.home() / ".config/retroarch/states/Snes9x/kof98-snes.state"
CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
CMD_PORT = 55355
PAD_PORT = 55400

# This RetroArch build expects the legacy native remote_message layout:
# int port, int device, int index, int id, uint16 state + tail padding.
REMOTE_MSG = struct.Struct("<iiiiH2x")
RETRO_DEVICE_JOYPAD = 1
BUTTONS = {
    "B": 0, "Y": 1, "SELECT": 2, "START": 3,
    "UP": 4, "DOWN": 5, "LEFT": 6, "RIGHT": 7,
    "A": 8, "X": 9, "L": 10, "R": 11,
}

F_STATE = 8
F_FRAME = 10
F_FACING = 14
F_HP = 16
F_ANIM = 18
F_META = 22
from runtime_abi import ABI

F_DMAREQ = ABI['F_DMAREQ']
F_JOY = 32
F_JOYPR = 34
F_ATKBOX = 36
F_HURTBOX = 38
F_HTIMER = 40
F_SLIDE = 42
F_CHAR = 44
F_TBANK = 46
F_POWER = 48
F_GRAB = 52
F_OWNER = 53
F_HITVX = 54
F_HITVY = 56
F_STIME = 60
FP1 = 0x4000
FP2 = 0x4040
ENGINE = 0x1020
AUDIO = 0x1030
DBGREG = 0x4600


def u16(buf, addr):
    return struct.unpack_from("<H", buf, addr)[0]


def s16(buf, addr):
    return struct.unpack_from("<h", buf, addr)[0]


def decompress_rzip(path):
    raw = path.read_bytes()
    if not raw.startswith(b"#RZIP"):
        raise RuntimeError(f"{path} is not an RZIP savestate")
    pos = 24
    parts = []
    while pos < len(raw):
        dec = zlib.decompressobj()
        try:
            parts.append(dec.decompress(raw[pos:]))
        except zlib.error as exc:
            raise RuntimeError(f"bad RZIP chunk at {pos}") from exc
        used = len(raw) - pos - len(dec.unused_data)
        if used <= 0:
            break
        pos += used
        if not dec.unused_data:
            break
        next_zlib = dec.unused_data.find(b"\x78")
        if next_zlib < 0:
            break
        pos += next_zlib
    data = b"".join(parts)
    off = data.find(b"RAM:131072:")
    if off < 0:
        raise RuntimeError("Snes9x RAM section not found")
    return data[off + 11:off + 11 + 131072]


class RetroArch:
    def __init__(self):
        self.cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cmd.settimeout(0.25)
        self.pads = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                     socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
        self.proc = None

    def launch(self, retroarch, core):
        if self.command("GET_STATUS"):
            raise RuntimeError("a RetroArch command server is already running")
        self.proc = subprocess.Popen(
            [retroarch, "-L", core, "--appendconfig", str(CFG),
             str(ROM), "--log-file=build/ra_test.log", "-v"],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def close(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def command(self, text):
        # a timed-out request's reply can arrive late and get consumed by
        # the *next* command, so drain any stale datagrams first
        self.cmd.setblocking(False)
        try:
            while self.cmd.recvfrom(4096):
                pass
        except BlockingIOError:
            pass
        self.cmd.setblocking(True)
        self.cmd.settimeout(0.5)
        self.cmd.sendto(text.encode() + b"\n", ("127.0.0.1", CMD_PORT))
        try:
            return self.cmd.recvfrom(4096)[0].decode(errors="replace").strip()
        except socket.timeout:
            return ""

    def command_no_reply(self, text):
        """Send a command whose RetroArch handler does not reply.

        Waiting on ``command()`` for these packets adds a socket timeout to
        every frame and lets unrelated UDP replies race with later reads.
        """
        self.cmd.sendto(text.encode() + b"\n", ("127.0.0.1", CMD_PORT))

    def wait_ready(self, timeout=30):
        deadline = time.monotonic() + timeout
        playing = False
        last_fc = None
        last_move = time.monotonic()
        unpause_sent = 0
        while time.monotonic() < deadline:
            st = self.command("GET_STATUS")
            if not st.startswith("GET_STATUS PLAYING"):
                time.sleep(0.1)
                continue
            playing = True
            try:
                fc = self.read_ram(ENGINE + 4, 1)[0]
            except RuntimeError:
                continue
            if last_fc is not None and fc != last_fc:
                return                      # counter moving -> really running
            if fc != last_fc:
                last_move = time.monotonic()
            last_fc = fc
            if (time.monotonic() - last_move > 3
                    and unpause_sent < 3):
                # spawned instance sometimes boots paused while still
                # reporting PLAYING -- kick it
                self.command("PAUSE_TOGGLE")
                unpause_sent += 1
                last_move = time.monotonic()
            time.sleep(0.3)
        raise RuntimeError("RetroArch command interface did not come up"
                           if not playing else
                           "emulator loaded but never ran a frame")

    def button(self, user, name, pressed):
        port = PAD_PORT + user
        packet = REMOTE_MSG.pack(user, RETRO_DEVICE_JOYPAD, 0,
                               BUTTONS[name], int(pressed))
        self.pads[user].sendto(packet, ("127.0.0.1", port))

    def pause(self, paused):
        # PAUSE_TOGGLE travels over UDP and is occasionally dropped.  A
        # single unchecked toggle lets frame-stepped tests continue at full
        # speed, so short states can begin and end between two snapshots.
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            status = self.command("GET_STATUS")
            if not status.startswith("GET_STATUS"):
                continue
            is_paused = "PAUSED" in status
            if is_paused == paused:
                return
            self.command_no_reply("PAUSE_TOGGLE")
            time.sleep(0.05)
        raise RuntimeError(
            f"could not {'pause' if paused else 'resume'} RetroArch")

    def frame_advance(self):
        # FRAMEADVANCE is a one-way UDP command with no reply and can be
        # dropped under load.  Do not resend while the first request may
        # still be pending: queued advances make short states begin and end
        # before snapshot() gets a chance to observe them.
        prev = self.read_ram(ENGINE + 4, 1)[0]
        current = prev
        for _ in range(20):
            self.command_no_reply("FRAMEADVANCE")
            time.sleep(0.25)
            current = self.read_ram(ENGINE + 4, 1)[0]
            if current != prev:
                return self.snapshot()
        raise RuntimeError(
            "FRAMEADVANCE did not advance the core "
            f"(frame={prev}->{current}, status={self.command('GET_STATUS')!r})")

    def read_ram(self, addr, size):
        reply = ""
        # the UDP command channel is lossy -- retry a few times before
        # declaring failure
        for _ in range(5):
            reply = self.command(f"READ_CORE_RAM {addr:X} {size}")
            fields = reply.split()
            if len(fields) == size + 2 and fields[2] != "-1":
                break
            time.sleep(0.01)
        else:
            raise RuntimeError(
                f"READ_CORE_RAM failed at {addr:X}: {reply!r}")
        try:
            return bytes(int(field, 16) for field in fields[2:])
        except ValueError as exc:
            raise RuntimeError(f"bad READ_CORE_RAM reply: {reply!r}") from exc

    def snapshot(self):
        wram = bytearray(DBGREG + 128)
        wram[ENGINE:ENGINE + 16] = self.read_ram(ENGINE, 16)
        wram[AUDIO:AUDIO + 12] = self.read_ram(AUDIO, 12)
        wram[FP1:FP1 + 64] = self.read_ram(FP1, 64)
        wram[FP2:FP2 + 64] = self.read_ram(FP2, 64)
        wram[DBGREG + 120:DBGREG + 128] = self.read_ram(DBGREG + 120, 8)
        return read_fight(wram)


def read_fighter(wram, base):
    return {
        "x": u16(wram, base) / 256.0,
        "y": u16(wram, base + 2) / 256.0,
        "vx": s16(wram, base + 4) / 256.0,
        "vy": s16(wram, base + 6) / 256.0,
        "state": wram[base + F_STATE],
        "frame": u16(wram, base + F_FRAME),
        "facing": s16(wram, base + F_FACING),
        "hp": u16(wram, base + F_HP),
        "anim": u16(wram, base + F_ANIM),
        "joy": u16(wram, base + F_JOY),
        "joypr": u16(wram, base + F_JOYPR),
        "atkbox": u16(wram, base + F_ATKBOX),
        "hurtbox": u16(wram, base + F_HURTBOX),
        "htimer": u16(wram, base + F_HTIMER),
        "slide": u16(wram, base + F_SLIDE),
        "char": u16(wram, base + F_CHAR),
        "tbank": wram[base + F_TBANK],
        "power": u16(wram, base + F_POWER),
        "grab": wram[base + F_GRAB],
        "owner": wram[base + F_OWNER],
        "hitvx": s16(wram, base + F_HITVX),
        "hitvy": s16(wram, base + F_HITVY),
        "stime": u16(wram, base + F_STIME),
    }


def read_fight(wram):
    return {
        "gamestate": u16(wram, ENGINE),
        "framecnt": u16(wram, ENGINE + 4),
        "kotimer": u16(wram, ENGINE + 8),
        "oamtop": u16(wram, ENGINE + 10),
        "audio": {
            "seq": wram[AUDIO],
            "last": wram[AUDIO + 1],
            "ready": wram[AUDIO + 2],
            "done": wram[AUDIO + 3],
            "env": wram[ENGINE + 0x3B],
        },
        "p1": read_fighter(wram, FP1),
        "p2": read_fighter(wram, FP2),
        "victim_box": wram[DBGREG + 120:DBGREG + 128].hex(),
    }


def wait_for(ra, pred, timeout=10, interval=0.08):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = ra.snapshot()
        if pred(last):
            return last
        time.sleep(interval)
    raise AssertionError(f"timeout waiting for condition; last={last}")


def approach(ra, gap=48):
    state = ra.snapshot()
    p1, p2 = state["p1"], state["p2"]
    while abs(p2["x"] - p1["x"]) > gap:
        direction = "RIGHT" if p2["x"] > p1["x"] else "LEFT"
        ra.button(0, direction, True)
        time.sleep(0.08)
        state = ra.snapshot()
        p1, p2 = state["p1"], state["p2"]
    ra.button(0, "RIGHT", False)
    ra.button(0, "LEFT", False)
    s = wait_for(ra, lambda s: s["p1"]["state"] == 0 and s["p1"]["joy"] == 0,
                 timeout=2)
    # expire the walk's F entries: a buffered F,F plus the next button
    # press would otherwise complete FF_a/FF_b (real buffered-command
    # semantics) and fire the knee instead of the intended attack
    for i in range(16):
        ra.command_no_reply(f"WRITE_CORE_RAM {0x4100 + i * 3:X} 00 00 00")
    return s


def step_until(ra, pred, max_frames=120):
    """Advance one emulated frame at a time until pred(snapshot) is true.
    Wall-clock independent, so short hitstun/guardstun windows and approach
    distances are deterministic regardless of host emulation speed.
    FRAMEADVANCE leaves the emulator paused, so resume before returning."""
    last = None
    try:
        for _ in range(max_frames):
            last = ra.frame_advance()
            if pred(last):
                return last
        raise AssertionError(
            f"condition not met within {max_frames} frames; last={last}")
    finally:
        ra.pause(False)


def approach_stepped(ra, gap=48, max_frames=600):
    """Frame-stepped variant of approach(): P1 walks until the horizontal
    gap to P2 is <= gap, then releases the dpad and idles."""
    last = None
    held = None
    try:
        for _ in range(max_frames):
            last = ra.snapshot()
            p1, p2 = last["p1"], last["p2"]
            if abs(p2["x"] - p1["x"]) <= gap:
                break
            d = "RIGHT" if p2["x"] > p1["x"] else "LEFT"
            if d != held:
                if held is not None:
                    ra.button(0, held, False)
                ra.button(0, d, True)
                held = d
            last = ra.frame_advance()
        else:
            raise AssertionError(
                f"approach did not close the gap; last={last}")
        return last
    finally:
        ra.button(0, "RIGHT", False)
        ra.button(0, "LEFT", False)
        ra.pause(False)


def press_attack(ra, name, expected_state, active_frames,
                 expected_hit_sfx=None):
    state = ra.snapshot()
    old_hp = state["p2"]["hp"]
    ra.pause(True)
    ra.button(0, name, True)
    seen = {}
    first = None
    cur = state
    for _ in range(240):
        cur = ra.frame_advance()
        fighter = cur["p1"]
        if fighter["state"] == expected_state:
            if first is None:
                first = cur
            seen.setdefault(fighter["frame"], fighter["atkbox"])
        elif seen:
            break
    ra.button(0, name, False)
    ra.pause(False)
    if first is None:
        raise AssertionError(f"{name}: expected state {expected_state}, "
                             f"got {cur}")
    got_active = {frame for frame, box in seen.items() if box}
    if got_active != set(active_frames):
        raise AssertionError(f"{name}: expected AIR attack frames "
                             f"{sorted(active_frames)}, got "
                             f"{sorted(got_active)}; samples={seen}")
    after = wait_for(
        ra, lambda s: s["p1"]["state"] == 0, timeout=3)
    if expected_hit_sfx is not None:
        # knockdowns append a landing thud after the hit sfx, so `last` may
        # already be SFX_LAND(8) and seq can have grown by more than 2
        dispatched = (after["audio"]["seq"] - state["audio"]["seq"]) & 0xFF
        if (after["audio"]["ready"] != 1 or dispatched < 2 or
                after["audio"]["last"] not in (expected_hit_sfx, 8)):
            raise AssertionError(
                f"{name}: expected >=2 SFX and hit id {expected_hit_sfx}, "
                f"got {after['audio']} from {state['audio']}")
    print(f"{name} frames", seen)
    return first, after, old_hp


def run_tests(ra):
    # P2 starts as CPU; the UP press below turns it human for the scripted
    # sections.  SELECT taps toggle the cpu2 flag live to re-enable it.
    # title -> select screen: START, then lock both picks (P1 A, P2 B)
    # the boot intro sits at gs=7 until START skips it; the title then
    # opens the mode menu (gs=6) where VERSUS is item 1 (M_ITEM=$F070)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        gs = ra.read_ram(ENGINE, 1)[0]
        if gs == 6:
            break
        ra.button(0, "START", True); time.sleep(0.2)
        ra.button(0, "START", False); time.sleep(0.5)
    else:
        raise AssertionError("mode menu never reached")
    for _ in range(4):
        if ra.read_ram(0xF070, 1)[0] == 1:      # M_ITEM -> versus
            break
        ra.button(0, "DOWN", True); time.sleep(0.2)
        ra.button(0, "DOWN", False); time.sleep(0.3)
    ra.button(0, "START", True); time.sleep(0.2)
    ra.button(0, "START", False)
    wait_for(ra, lambda s: s["gamestate"] == 5, timeout=8)
    # UDP button edges are occasionally dropped on busy hosts; verify each
    # cursor/lock actually changed and retry the press until it registers.
    # new KOF98-style select: cursors are absolute WRAM $F052/$F053, pad2
    # joins as human with START, face button A locks the pick, B cancels.
    def nudge(user, btn, addr, mask=0xFF):
        for _ in range(8):
            before = ra.read_ram(addr, 1)[0] & mask
            ra.button(user, btn, True); time.sleep(0.3)
            ra.button(user, btn, False); time.sleep(0.2)
            if (ra.read_ram(addr, 1)[0] & mask) != before:
                return
        raise AssertionError(f"select input {btn} never registered")
    # order matters: P2 auto-locks ~150 frames after P1 confirms, so drive
    # P2's toggles/cursor/lock first and P1's confirm last.
    nudge(0, "RIGHT", 0xF052)          # P1 cursor cell
    if ra.read_ram(0x1091, 1)[0] != 0:  # versus may already have P2 human
        nudge(1, "START", 0x1091)      #   otherwise START joins it
    nudge(1, "LEFT", 0xF053)           # P2 cursor cell
    nudge(1, "A", 0x108F)              # P2 lock
    nudge(0, "A", 0x108E)              # P1 lock
    state = wait_for(
        ra, lambda s: s["gamestate"] == 1 and s["p2"]["joy"] == 0,
        timeout=15)
    print("initial", state)
    if state["audio"]["ready"] != 1:
        raise AssertionError(f"SPC driver did not become ready: {state['audio']}")
    if state["audio"]["seq"] < 1 or state["audio"]["last"] != 10:
        raise AssertionError("round/fight SFX commands were not dispatched: "
                             f"{state['audio']}")
    if state["p1"]["char"] == state["p2"]["char"]:
        raise AssertionError("P1/P2 did not select distinct characters")
    if state["p1"]["tbank"] == state["p2"]["tbank"]:
        raise AssertionError("P1/P2 generated tables share the same bank")
    if state["p2"]["x"] - state["p1"]["x"] < 64:
        raise AssertionError(
            f"P1/P2 spawn positions overlap: "
            f"{state['p1']['x']} / {state['p2']['x']}")

    # Landing sends one SFX_LAND after the neutral jump returns to stand.
    pre_jump_seq = state["audio"]["seq"]
    ra.button(0, "UP", True)
    wait_for(ra, lambda s: s["p1"]["state"] == 4, timeout=3)
    ra.button(0, "UP", False)
    landed = wait_for(
        ra, lambda s: s["p1"]["state"] == 0 and s["audio"]["last"] == 8,
        timeout=5)
    if landed["audio"]["seq"] != (pre_jump_seq + 1) & 0xFF:
        raise AssertionError(f"landing SFX sequence mismatch: "
                             f"{state['audio']} -> {landed['audio']}")

    # P2's first sprite upload commits F_META a few frames after the round
    # starts; poll until its OBJ palette-1 cells appear in the shadow OAM.
    attrs = []
    for _ in range(200):
        oam = ra.read_ram(0x1800, 160)
        attrs = [oam[i + 3] for i in range(0, len(oam), 4)]
        if any((attr >> 1) & 7 == 1 for attr in attrs):
            break
        ra.pause(False)
        time.sleep(0.02)
    if not any((attr >> 1) & 7 == 1 for attr in attrs):
        raise AssertionError(f"P2 did not select OBJ palette 1: {attrs}")

    # Cross P2 so FaceEachOther flips P1, then validate the mirrored AIR box.
    # The grounded pushbox blocks walking through the opponent, so teleport
    # P1 a few px past P2 instead.
    ra.button(0, "RIGHT", True)
    ra.command("WRITE_CORE_RAM 4000 00 B4")   # P1.x = 180.0, just past P2
    crossed = wait_for(ra, lambda s: s["p1"]["facing"] < 0, timeout=8)
    ra.button(0, "RIGHT", False)
    wait_for(ra, lambda s: s["p1"]["x"] >= 179, timeout=2)
    wait_for(ra, lambda s: s["p1"]["state"] == 0 and s["p1"]["joy"] == 0,
             timeout=2)
    old_hp = crossed["p2"]["hp"]
    held, after, _ = press_attack(ra, "B", 7, (3,), 4)
    if old_hp - after["p2"]["hp"] != 12:
        raise AssertionError(f"mirrored B did not apply weak-kick damage: "
                             f"{held} -> {after}")
    print("mirrored B", held, after)

    # P2 is now on the left; tap Select (cpu2 on) and require an AI hit.
    ra.button(1, "SELECT", True); time.sleep(0.25); ra.button(1, "SELECT", False)
    p1_hp = ra.snapshot()["p1"]["hp"]
    hit = wait_for(ra, lambda s: s["p1"]["hp"] < p1_hp, timeout=8,
                   interval=0.02)
    print("p2 ai hit +face", hit)
    if hit["p2"]["state"] != 7 or hit["p1"]["htimer"] == 0:
        raise AssertionError("P2 did not use the Kyo weak-kick CNS table")
    ra.button(1, "SELECT", True); time.sleep(0.25); ra.button(1, "SELECT", False)
    wait_for(ra, lambda s: s["p1"]["state"] == 0 and s["p2"]["state"] == 0,
             timeout=5)

    # Move back left until FaceEachOther restores P1's right-facing side.
    # The pushbox blocks walking back through P2, so teleport to the left.
    ra.button(0, "LEFT", True)
    ra.command("WRITE_CORE_RAM 4000 00 64")   # P1.x = 100.0, left of P2
    wait_for(ra, lambda s: s["p1"]["facing"] >= 0, timeout=8)
    ra.button(0, "LEFT", False)

    tests = (("Y", 5, 14, (3,), 4), ("X", 6, 26, (4,), 6),
             ("B", 7, 12, (3,), 4), ("A", 8, 28, (4, 5), 6))
    for name, state_id, damage, active_frames, hit_sfx in tests:
        # Without pushboxes the previous sequence can leave the fighters
        # overlapped; teleport to a fixed gap so the attack range is real.
        # Iori's normals outdamage kfm's: restore P2 HP or the loop KOs
        # the dummy before the KO/restart assertions can run.
        ra.command("WRITE_CORE_RAM 4000 00 64")   # P1.x = 100.0
        ra.command("WRITE_CORE_RAM 4040 00 96")   # P2.x = 150.0
        ra.command("WRITE_CORE_RAM 4050 C8 00")   # P2.hp = 200
        approach(ra)
        held, after, old_hp = press_attack(
            ra, name, state_id, active_frames, hit_sfx)
        got_damage = old_hp - after["p2"]["hp"]
        # hits can KO mid-sequence: damage past the remaining HP is clipped
        if got_damage != min(damage, old_hp):
            raise AssertionError(f"{name}: expected damage {damage}, "
                                 f"got {got_damage} ({old_hp} -> "
                                 f"{after['p2']['hp']})")
        print(f"{name}: state={state_id} damage={got_damage} "
              f"atk={held['p1']['atkbox']:04x} hurt={held['p1']['hurtbox']:04x}")

    # P2 is on the right now, so AI attacks in the opposite facing direction.
    ra.button(1, "SELECT", True); time.sleep(0.25); ra.button(1, "SELECT", False)
    p1_hp = ra.snapshot()["p1"]["hp"]
    hit = wait_for(ra, lambda s: s["p1"]["hp"] < p1_hp, timeout=8)
    print("p2 ai hit -face", hit)

    # sfxlast is overwritten a few ticks after the KO by the victim's
    # landing thud, so the engine latches the dispatched id at DBGREG+96
    ko = wait_for(ra, lambda s: s["gamestate"] == 2 and s["p1"]["hp"] == 0,
                  timeout=90)
    if ko["audio"]["ready"] != 1 or ra.read_ram(DBGREG + 96, 1)[0] != 11:
        raise AssertionError(f"KO SFX was not dispatched: {ko['audio']}")
    print("ko", ko)
    # Tap Select again so the AI cannot attack after the restart and
    # overwrite the round/fight SFX marker before we can read it.
    ra.button(1, "SELECT", True); time.sleep(0.25); ra.button(1, "SELECT", False)
    intermission = wait_for(
        ra, lambda s: s["gamestate"] == 0, timeout=10, interval=0.01)
    stream = ra.read_ram(FP1, 96)
    if (intermission["oamtop"] != 0 or u16(stream, F_META) != 0 or
            u16(stream, FP2 - FP1 + F_META) != 0 or
            stream[F_DMAREQ] != 0 or
            stream[FP2 - FP1 + F_DMAREQ] != 0):
        raise AssertionError(
            f"intermission retained fight OAM/stream state: "
            f"oam={intermission['oamtop']} "
            f"p1meta={u16(stream, F_META):04x} "
            f"p2meta={u16(stream, FP2 - FP1 + F_META):04x}")
    restarted = wait_for(
        ra, lambda s: s["gamestate"] == 1 and s["p1"]["hp"] == 200 and
        s["p2"]["hp"] == 200,
        timeout=20)
    if restarted["audio"]["last"] != 10:
        raise AssertionError("round restart did not dispatch round/fight SFX: "
                             f"{restarted['audio']}")
    print("restart", restarted)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true",
                    help="start a clean RetroArch/Snes9x process")
    ap.add_argument("--retroarch", default="retroarch")
    ap.add_argument("--core", default=CORE)
    args = ap.parse_args()

    ra = RetroArch()
    try:
        if args.launch:
            ra.launch(args.retroarch, args.core)
        ra.wait_ready()
        run_tests(ra)
    finally:
        ra.close()


if __name__ == "__main__":
    sys.exit(main())
