#!/usr/bin/env python3
"""Reach the mode menu, press DOWN once, record audio around it."""
import socket, struct, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "build" / "remote_input.cfg"
ROM = ROOT / "kof98-snes.sfc"
CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
CMD = ("127.0.0.1", 55355)
REMOTE_MSG = struct.Struct("<iiiiH2x")
BTN = {"START":3,"UP":4,"DOWN":5,"A":8,"B":0}

cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); cmd.settimeout(1)
pad = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(text):
    cmd.sendto(text.encode()+b"\n", CMD)
    try: return cmd.recvfrom(4096)[0].decode(errors="replace").strip()
    except socket.timeout: return ""

def send_nr(text): cmd.sendto(text.encode()+b"\n", CMD)

def press(name, hold=0.07):
    for v in (1,0):
        pad.sendto(REMOTE_MSG.pack(0,1,0,BTN[name],v), ("127.0.0.1",55400))
        time.sleep(hold)

def ram(addr, size):
    for _ in range(6):
        r = send(f"READ_CORE_RAM {addr:X} {size}")
        f = r.split()
        if len(f)==size+2:
            try: return bytes(int(x,16) for x in f[2:])
            except ValueError: pass
        time.sleep(0.02)
    return None

def gs():
    b = ram(0x1020,1); return b[0] if b else None

proc = subprocess.Popen(
    ["retroarch","-L",CORE,"--appendconfig",str(CFG),str(ROM),"-v"],
    cwd=ROOT, stdout=open("/tmp/ra_menusfx.log","w"), stderr=subprocess.STDOUT)
try:
    for _ in range(60):
        if send("GET_STATUS").startswith("GET_STATUS PLAYING"): break
        time.sleep(0.5)
    # drive to mode menu
    end=time.monotonic()+90
    while time.monotonic()<end:
        g=gs()
        if g==6: break
        if g in (0,7,9): press("START")
        time.sleep(1.0)
    print("gs=",gs())
    time.sleep(4)                        # effects reload + music settle
    send_nr("RECORDING_TOGGLE"); time.sleep(0.4)
    t0=time.monotonic(); press("DOWN")
    time.sleep(1.5)
    press("DOWN"); time.sleep(1.5)
    press("A");  time.sleep(1.5)         # confirm beep for comparison
    send_nr("RECORDING_TOGGLE"); time.sleep(1)
    print("recorded, presses at ~0.4/1.9/3.4s after toggle")
finally:
    proc.terminate()
    try: proc.wait(timeout=3)
    except subprocess.TimeoutExpired: proc.kill()
