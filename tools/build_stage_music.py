#!/usr/bin/env python3
"""Build one SNESMOD .it module per stage song.

Each stage's source MIDI (tools/build_stages.py:STAGE_SONGS) is split into
per-channel MIDI files, the duplicates are dropped, and the three densest
melodic channels are kept -- highest average pitch as lead, lowest as bass,
the remaining one as harmony -- plus drums.  Each channel is bound to one of
the instruments in assets/audio/esaka/instruments/ by a small General-MIDI
program heuristic, and midi2tracker assembles the arrangement into
build/gen_audio/it/.

Module order in the soundbank is the stage order (module 0 = sfx.it,
module i+1 = stage i).
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stages

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MUSIC = os.path.join(ROOT, "music")
INSTR = os.path.join(ROOT, "assets/audio/esaka/instruments")
OUT = os.path.join(ROOT, "build/gen_audio/it")

# smconv budget per module is ~58.5 KB of ARAM.  Songs whose reduced PCM
# still overflows get a deeper resample here (default is TARGET_RATE=5500).
# KOF98BlueMarysBlues converted at the default rate totaled 65584 bytes --
# the SPC transfer wrapped past the top of ARAM, scribbled the driver and
# froze the console inside spcLoad's echo wait.
PCM_RATE = {
    # This track has long samples across several instruments.  At the default
    # 5500 Hz it exceeds SNESMOD's 58,573-byte ARAM ceiling and spcLoad hangs.
    # Keep both of the largest modules below 47 KB to leave room for effects
    # and round voices loaded after the stage music.
    "kof98_dora.mid": 3000,
    # Esaka-style reduction (3 melodic voices + drums) still leaves these
    # four near the 44.5 KB runtime ceiling at 5500 Hz; 3 kHz keeps every
    # stage module at or below the 36 KB Esaka reference.
    "KOF98Arashi2.mid": 3000,
    "Fairy98.mid": 3000,
    "Ryu-ko_Final.mid": 3000,
    "Kurikinton_Gomame_Guitar_Ver_.mid": 3000,
    # Survivor ending: long, layered MIDI.  Keep it below the ARAM ceiling
    # without making the piano/strings too dull.
    "kof00_crystal.mid": 2000,
}
MIDI2TRACKER = os.path.expanduser("~/.local/bin/midi2tracker")


def stage_order():
    # Use the exact same order as build_stages.build(): the stage index is
    # also the soundbank module offset (module = stage + 1).  Sorting the
    # extension-stripped names here would reorder *Stage* vs *Stage-B* and
    # shift the music mapping by one.
    paths = build_stages.sorted_stage_paths()
    out = []
    for i, path in enumerate(paths):
        name = os.path.splitext(os.path.basename(path))[0]
        if build_stages.stage_song(name) is not None:
            out.append((i, name))
    return out


def gm_instrument(prog, drums):
    """GM program -> one of the instruments we already ship."""
    if drums:
        return "909_kit.iti"
    if 32 <= prog <= 39:
        return "bass_closer.iti"      # bass
    if prog <= 7:
        return "house_piano.iti"      # piano/keys
    if 24 <= prog <= 31:
        return "saw_stab.iti"         # guitars
    if 48 <= prog <= 55 or 88 <= prog <= 99:
        return "euro_pad.iti"         # strings/pads/fx
    if 80 <= prog <= 87:
        return "trance_arp.iti"       # synth leads
    if 56 <= prog <= 79:
        return "eurobeat_lead.iti"    # brass/reed/pipes -> lead
    return "saw_stab.iti"             # default melodic


def split_channels(mid_path, workdir):
    """Return {channel: mid_path} -- one single-channel file each."""
    import mido
    src = mido.MidiFile(mid_path)
    meta = []                        # (absolute tick, merged order, message)
    chan_msgs = {}
    chan_prog = {}
    # MIDI format 1 stores each track's deltas relative to that track.  They
    # cannot be concatenated directly: doing so shifts every later track by
    # the accumulated duration of the earlier one.  Merge first so mido
    # orders events globally and recalculates their deltas, then retain each
    # event's absolute tick while making the per-channel files.
    tick = 0
    for order, msg in enumerate(mido.merge_tracks(src.tracks)):
        tick += msg.time
        if msg.is_meta:
            if msg.type in ("set_tempo", "time_signature", "key_signature"):
                meta.append((tick, order, msg))
            continue
        ch = getattr(msg, "channel", None)
        if ch is None:
            continue
        chan_msgs.setdefault(ch, []).append((tick, order, msg))
        if msg.type == "program_change" and ch not in chan_prog:
            chan_prog[ch] = msg.program
    out = {}
    for ch, msgs in chan_msgs.items():
        if not any(m.type == "note_on" and m.velocity for _t, _o, m in msgs):
            continue
        f = mido.MidiFile(ticks_per_beat=src.ticks_per_beat)
        tr = mido.MidiTrack()
        timeline = [(t, order, msg.copy()) for t, order, msg in meta]
        timeline.extend((t, order, msg.copy()) for t, order, msg in msgs)
        timeline.sort(key=lambda item: (item[0], item[1]))
        prev_tick = 0
        for abs_tick, _order, msg in timeline:
            msg.time = abs_tick - prev_tick
            tr.append(msg)
            prev_tick = abs_tick
        tr.append(mido.MetaMessage("end_of_track", time=0))
        f.tracks.append(tr)
        p = os.path.join(workdir, f"ch{ch:02d}.mid")
        f.save(p)
        out[ch] = (p, chan_prog.get(ch, 0))
    return out


def build_module(midi_name, out_it):
    """One stage song -> .it via channel split + auto instrument map.

    midi_name may be a bare name under music/ or an absolute/relative path.
    """
    midi_path = (midi_name if os.path.isabs(midi_name)
                 else os.path.join(MUSIC, midi_name))
    midi_base = os.path.basename(midi_path)
    with tempfile.TemporaryDirectory() as wd:
        parts = split_channels(midi_path, wd)
        lines = ["name: stage", "settings:",
                 "  rows_per_beat: 4", "  allocation: packed",
                 "tracks:"]
        # SNESMOD hard cap: 8 channels per module.  Esaka recipe: drums
        # (2 channels) + three melodic voices (lead 2, harmony 1, bass 1).
        import mido
        stats = {}
        for ch, (path, _p) in parts.items():
            mf = mido.MidiFile(path)
            notes = [m.note for tr in mf.tracks for m in tr
                     if m.type == "note_on" and m.velocity]
            if notes:
                stats[ch] = (len(notes), sum(notes) / len(notes),
                             tuple(sorted(notes)))
        drums = 9 if 9 in stats else None
        # Duplicate channels (same note set, different program) waste a
        # voice: Arashi has three copies of its main riff, Fairy two.
        unique, seen = [], set()
        for ch in sorted(c for c in stats if c != 9):
            sig = stats[ch][2]
            if sig in seen:
                continue
            seen.add(sig)
            unique.append(ch)
        top = sorted(unique, key=lambda c: -stats[c][0])[:3]
        by_pitch = sorted(top, key=lambda c: stats[c][1])
        lead = by_pitch[-1] if by_pitch else None
        keep = set(top)
        if drums is not None:
            keep.add(drums)
        parts = {c: v for c, v in parts.items() if c in keep}
        for ch in sorted(parts):
            path, prog = parts[ch]
            iti = gm_instrument(prog, ch == 9)
            n = 2 if (ch == 9 or ch == lead) else 1
            lines.append(f"  {path}:")
            lines.append(f"    instrument_file: {INSTR}/{iti}")
            lines.append(f"    channels: {n}")
        yaml_path = os.path.join(wd, "arranjo.yaml")
        open(yaml_path, "w").write("\n".join(lines) + "\n")
        r = subprocess.run([MIDI2TRACKER, yaml_path, out_it,
                            "--channels", "8"],
                           capture_output=True, text=True, cwd=wd)
        if r.returncode != 0:
            raise RuntimeError(f"{midi_base}: midi2tracker: {r.stderr}")
    # shrink PCM so the module fits ARAM (snesmod converts to BRR)
    import it_reduce
    it_reduce.reduce_it(out_it, out_it + ".tmp",
                        PCM_RATE.get(midi_base, it_reduce.TARGET_RATE))
    os.replace(out_it + ".tmp", out_it)
    return r


def main():
    os.makedirs(OUT, exist_ok=True)
    mods = ["sfx.it placeholder"]          # module 0 is the sfx bank
    for idx, name in stage_order():
        midi = build_stages.stage_song(name)
        out_it = os.path.join(OUT, f"stg{idx}.it")
        try:
            build_module(midi, out_it)
        except Exception as exc:
            print(f"stg{idx} {name}: midi2tracker failed ({exc}); "
                  "using the in-tree MIDI-to-IT converter")
            subprocess.run([
                sys.executable,
                os.path.join(ROOT, "tools/mid2it.py"),
                os.path.join(MUSIC, midi),
                os.path.join(ROOT, "assets/audio/menu/cipher_beta.it"),
                out_it,
            ], check=True)
        print(f"stg{idx} {name}: {midi} -> {os.path.getsize(out_it)}B")
        mods.append(out_it)
    print(f"{len(mods)-1} stage modules written to {OUT}")


if __name__ == "__main__":
    main()
