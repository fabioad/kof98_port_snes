#!/usr/bin/env python3
"""Compile the stage BGM MIDI into the SPC700 song format.

Reuses the build_spc_neogeo MIDI parser/event encoder (same 3-byte
[wait][op][arg] track format and 16-byte track-offset header), but maps the
six SNES music voices onto the SPC instrument slots (dir 21-26) and trims
the source down to a bar-aligned loop window so it fits the ARAM song region.
"""

from pathlib import Path
from collections import defaultdict
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_spc_neogeo as neo

ROOT = Path(__file__).resolve().parents[1]
MIDI_PATH = ROOT / "music" / "EsakaVer3.mid"
OUT_PATH = ROOT / "build" / "gen_audio" / "spc_song.bin"

# SPC dir slots (see build_audio.py): melodic BRR loops then drums.
I_TRI, I_SQR, I_STR = 21, 22, 23
I_KICK, I_SNARE, I_HAT = 24, 25, 26

# Loop window covers the intro hook + first groove (bars 0-15, ~28s).
LOOP_BAR, LOOP_BARS = 0, 16

# Voice allocation for the six SPC music channels.  EsakaVer3: ch0 synth
# lead carries the hook (ch8 duplicates it), ch1 is a sparse whistle merged
# into the lead track, ch4 is the low bass guitar, ch5/ch3 the rhythm
# guitars, ch2 the strings pad, ch9 the drum kit.
TRACKS = [
    ("drums",  (9,),     None,  0x5C, 2),
    ("bass",   (4,),     I_TRI, 0x58, 2),
    ("lead",   (0, 1),   I_SQR, 0x50, 2),
    ("rhy1",   (5,),     I_STR, 0x3C, 1),
    ("rhy2",   (3,),     I_SQR, 0x34, 3),
    ("strings",(2,),     I_STR, 0x30, 3),
]


def spc_drum(note: int) -> int:
    if note in (35, 36, 41, 43, 45):
        return I_KICK
    if note in (38, 39, 40, 37, 42):
        return I_SNARE if note in (38, 39, 40, 37) else I_HAT
    return I_HAT


def window_events(parsed, chs, f0: int, f1: int):
    """(frame, kind, a, b) events of the MIDI channel set, window-rebased."""
    out = []
    sounding = set()
    for tick, c, kind, a, b in parsed["events"]:
        if c not in chs:
            continue
        frame = neo.midi_tick_to_frame(tick, parsed["tempos"], parsed["div"])
        if kind == "on" and frame < f0:
            sounding.add(a)
        elif kind == "off" and frame < f0:
            sounding.discard(a)
        if f0 <= frame < f1:
            out.append((frame - f0, kind, a, b))
    # Notes still sounding at the window edge get an explicit release so the
    # loop boundary does not smear into the restart.
    for frame, kind, a, b in out:
        if kind == "on":
            sounding.add(a)
        elif kind == "off":
            sounding.discard(a)
    total = f1 - f0
    for n in sounding:
        out.append((total - 1, "off", n, 0))
    out.sort()
    return out


def mono_track(evs, inst, vol, pan) -> list:
    """melodic channel -> mono (frame,kind,note,vel,_) events for emit_track."""
    sounding = []
    current = None
    out = [(0, "inst", inst, 0, 0), (0, "vol", vol, 0, 0), (0, "pan", pan * 32, 0, 0)]
    for frame, kind, a, b in evs:
        if kind == "on":
            sounding = [n for n in sounding if n != a]
            sounding.append(a)
            if a != current:
                out.append((frame, "on", a, b, 0))
                current = a
        elif kind == "off":
            sounding = [n for n in sounding if n != a]
            if a == current:
                nxt = sounding[-1] if sounding else None
                if nxt is None:
                    out.append((frame, "off", a, 0, 0))
                    current = None
                else:
                    out.append((frame, "on", nxt, 96, 0))
                    current = nxt
    if current is not None:
        last = evs[-1][0] + 8 if evs else 16
        out.append((last, "off", current, 0, 0))
    out.sort(key=lambda e: e[0])
    return out


def drum_track(evs, vol, pan) -> list:
    out = [(0, "vol", vol, 0, 0), (0, "pan", pan * 32, 0, 0)]
    for frame, kind, a, b in evs:
        if kind == "on":
            out.append((frame, "inst", spc_drum(a), 0, 0))
            out.append((frame, "on", 60, b, 0))
            out.append((frame + 8, "off", 60, 0, 0))
    out.sort(key=lambda e: e[0])
    return out


def silent_track(frames: int) -> bytes:
    # A voice with no notes still needs nonzero waits: a bare [0][LOOP][0]
    # stream would spin the SPC sequencer forever between loop fetches.
    blob = bytearray((0, neo.OP_INST, I_TRI, 0, neo.OP_VOL, 0))
    while frames > 254:
        blob += bytes((254, neo.OP_REST, 1))
        frames -= 254
    blob += bytes((frames, neo.OP_REST, 1, 0, neo.OP_LOOP, 0))
    return bytes(blob)


def build() -> bytes:
    parsed = neo.parse_midi(MIDI_PATH)
    barf = neo.midi_tick_to_frame(parsed["div"] * 4,
                                  parsed["tempos"], parsed["div"])
    f0 = LOOP_BAR * barf
    f1 = f0 + LOOP_BARS * barf
    tracks = []
    for name, chs, inst, vol, pan in TRACKS:
        evs = window_events(parsed, chs, f0, f1)
        notes = sum(1 for _, k, *_ in evs if k == "on")
        if name == "drums":
            blob = neo.emit_track(drum_track(evs, vol, pan), True)
        elif notes:
            blob = neo.emit_track(mono_track(evs, inst, vol, pan), False)
        else:
            blob = silent_track(f1 - f0)
        print(f"{name:8s} ch{chs}: {notes:4d} notes -> {len(blob)} bytes")
        tracks.append(blob)

    header = bytearray(16)
    header[0] = 6
    off = 16
    for i, t in enumerate(tracks):
        struct.pack_into("<H", header, 2 + i * 2, off)
        off += len(t)
    song = bytes(header) + b"".join(tracks)
    print(
        f"song: {len(song)} bytes, {LOOP_BARS} bars "
        f"({LOOP_BARS * barf / 60:.1f}s loop) from bar {LOOP_BAR}"
    )
    return song


if __name__ == "__main__":
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_bytes(build())
