#!/usr/bin/env python3
"""Record a CPU-vs-CPU versus bout from the Snes9x libretro core.

Boots SINGLE VS, forces both sides to CPU, lets the AI play, and captures
every video refresh plus the MSU audio stream.  Frames are piped as raw
RGB to ffmpeg, so no PNG sequence is written to disk; the soundtrack is
written to a temporary WAV and muxed into the final MP4.

Typical use:

    python3 tools/capture_bout_video.py 0:1 --seconds 30

The output defaults to work/videos/kof98_cpu_0-1.mp4.  A JSON sidecar with
the measured framerate and runtime counters is written next to it.
"""
import argparse
import ctypes as C
import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from test_ai_headless import (
    AI_LEVEL, CPU1, CPU2, GS, LOCK1, LOCK2, M_ITEM, MSUOK, SEL1, SEL2,
    tap, wait,
)

CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
FRAMECNT = 0x1024
RT_MSUFAIL = 0x5102
RT_OAMDROP = 0x5106


class GameGeometry(C.Structure):
    _fields_ = [
        ("base_width", C.c_uint), ("base_height", C.c_uint),
        ("max_width", C.c_uint), ("max_height", C.c_uint),
        ("aspect_ratio", C.c_float),
    ]


class SystemTiming(C.Structure):
    _fields_ = [("fps", C.c_double), ("sample_rate", C.c_double)]


class SystemAvInfo(C.Structure):
    _fields_ = [("geometry", GameGeometry), ("timing", SystemTiming)]


def av_info(core):
    info = SystemAvInfo()
    fn = core.lib.retro_get_system_av_info
    fn.argtypes = [C.POINTER(SystemAvInfo)]
    fn(C.byref(info))
    return info


def frame_rgb(frame):
    """Convert a libretro frame to packed RGB24.

    Snes9x pads each scanline to the core's max_width (512 px), so the
    pitch is usually larger than width*bpp; PIL's raw decoder skips that
    padding when we pass the real pitch and a width-sized image.
    """
    width, height, pitch, raw, fmt = frame
    if fmt == 1:                       # RETRO_PIXEL_FORMAT_XRGB8888
        mode = "BGRX"
    elif fmt == 2:                     # RETRO_PIXEL_FORMAT_RGB565
        mode = "BGR;16"
    else:                              # RETRO_PIXEL_FORMAT_0RGB1555
        mode = "BGR;15"
    image = Image.frombytes("RGB", (width, height), raw, "raw", mode, pitch)
    return image.tobytes(), width, height


def word(core, address):
    return core.ram[address] | core.ram[address + 1] << 8


def boot_bout(rom, p1, p2, level, core_path, idle):
    core = Core(core_path, rom)
    for _ in range(80):
        if core.ram[GS] == 6:
            break
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 6, "mode menu")
    core.ram[MSUOK] = 1
    core.ram[M_ITEM] = 1
    tap(core, 3)
    wait(core, lambda: core.ram[GS] == 5, "versus select")
    core.ram[SEL1] = p1
    core.ram[SEL2] = p2
    core.ram[LOCK1] = 1
    core.ram[LOCK2] = 1
    core.ram[CPU1] = 1
    core.ram[CPU2] = 1
    core.ram[AI_LEVEL] = level
    wait(core, lambda: core.ram[GS] in (1, 4), "fight load")
    if core.ram[GS] == 4:
        tap(core, 3)
    wait(core, lambda: core.ram[GS] == 1, "fight")
    core.step(idle)
    return core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pair", help="P1:P2 roster ids, e.g. 0:1")
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    parser.add_argument("--core", type=Path, default=CORE)
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--level", type=int, default=8)
    parser.add_argument("--idle", type=int, default=120,
                        help="frames to let the round settle before capture")
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    p1, p2 = map(int, args.pair.split(":"))
    output = args.output or ROOT / "work" / "videos" / f"kof98_cpu_{p1}-{p2}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)

    core = boot_bout(args.rom, p1, p2, args.level, args.core, args.idle)
    try:
        info = av_info(core)
        fps = info.timing.fps or 60.0988
        sample_rate = int(round(info.timing.sample_rate or 32040))
        frames = int(round(args.seconds * fps))
        chunks = []

        @C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
        def audio_batch(data, count):
            if data and count:
                chunks.append(C.string_at(data, count * 4))
            return count

        core.lib.retro_set_audio_sample_batch(audio_batch)
        core.capture_video = True

        wav_path = None
        if not args.no_audio:
            fd, name = tempfile.mkstemp(suffix=".wav", dir="/tmp/opencode")
            os.close(fd)
            Path(name).unlink()
            wav_path = Path(name)

        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", "256x224", "-r", f"{fps:.4f}", "-i", "pipe:0",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]

        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        before_frame = core.ram[FRAMECNT]
        prev_frame = before_frame
        before_msufail = word(core, RT_MSUFAIL)
        before_oamdrop = word(core, RT_OAMDROP)
        ticks = 0
        fight_frames = 0
        try:
            for index in range(frames):
                core.step()
                raw, width, height = frame_rgb(core.last_frame)
                if (width, height) != (256, 224):
                    raise ValueError(f"unexpected frame size {width}x{height}")
                process.stdin.write(raw)
                now = core.ram[FRAMECNT]
                delta = (now - prev_frame) & 0xFF
                prev_frame = now
                # Count logic ticks only during the fight: the KO/attract
                # transition rewrites framecnt and would inflate the sum.
                if core.ram[GS] == 1 and delta <= 4:
                    ticks += delta
                    fight_frames += 1
                if index and index % 300 == 0:
                    print(f"  {index}/{frames} frames", flush=True)
        finally:
            core.capture_video = False
            process.stdin.close()
            code = process.wait()
        if code != 0:
            raise SystemExit(f"ffmpeg failed with exit code {code}")

        if wav_path:
            with wave.open(str(wav_path), "wb") as wav:
                wav.setnchannels(2)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                wav.writeframes(b"".join(chunks))
            # ffmpeg already ran; remux the audio now that the WAV is complete.
            with_audio = output.with_suffix(".audio.mp4")
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(output),
                 "-i", str(wav_path), "-c:v", "copy", "-c:a", "aac",
                 "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                 str(with_audio)], check=True)
            with_audio.replace(output)
            wav_path.unlink(missing_ok=True)

        gs = core.ram[GS]
        sidecar = {
            "pair": [p1, p2],
            "level": args.level,
            "requested_frames": frames,
            "video_frames": frames,
            "fight_frames": fight_frames,
            "fps_setting": round(fps, 4),
            "ticks": ticks,
            "logic_fps": round(fps * ticks / max(1, fight_frames), 4),
            "sample_rate": sample_rate,
            "audio": not args.no_audio,
            "gs_final": gs,
            "rt_msufail_delta": (word(core, RT_MSUFAIL) - before_msufail) & 0xFFFF,
            "rt_oamdrop_delta": (word(core, RT_OAMDROP) - before_oamdrop) & 0xFFFF,
            "output": str(output),
        }
        output.with_suffix(".json").write_text(
            json.dumps(sidecar, indent=2) + "\n")
        print(json.dumps(sidecar, indent=2))
    finally:
        core.close()


if __name__ == "__main__":
    main()
