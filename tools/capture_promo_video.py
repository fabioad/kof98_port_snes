#!/usr/bin/env python3
"""Record a promo clip: character select + CPU-vs-CPU fight, one take.

Boots SINGLE VS like tools/capture_bout_video.py, but keeps the versus
select screen on camera for --select-seconds while the cursors move via
real joypad taps.  Then both picks lock in, the CPU takes over at max
difficulty, and the fight plays out for the rest of --seconds.  Video is
piped as raw RGB to ffmpeg; the MSU audio stream is muxed in afterwards.

Typical use:

    python3 tools/capture_promo_video.py 28:13 --seconds 32

The output defaults to work/videos/kof98_promo_28-13.mp4.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core
from test_ai_headless import (
    AI_LEVEL, CPU1, CPU2, GS, LOCK1, LOCK2, M_ITEM, MSUOK, SEL1, SEL2,
    tap, wait,
)
from capture_bout_video import CORE, av_info, frame_rgb, word

FRAMECNT = 0x1024
RT_MSUFAIL = 0x5102
RT_OAMDROP = 0x5106

BTN_RIGHT, BTN_DOWN, BTN_LEFT, BTN_A = 7, 5, 6, 8


def boot_select(rom, core_path):
    """Title → mode menu → versus select.  Leaves both picks unlocked."""
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
    return core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pair", help="P1:P2 roster ids, e.g. 28:13")
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    parser.add_argument("--core", type=Path, default=CORE)
    parser.add_argument("--seconds", type=float, default=32.0)
    parser.add_argument("--select-seconds", type=float, default=4.0)
    parser.add_argument("--level", type=int, default=9)
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    p1, p2 = map(int, args.pair.split(":"))
    output = args.output or ROOT / "work" / "videos" / f"kof98_promo_{p1}-{p2}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)

    core = boot_select(args.rom, args.core)
    try:
        info = av_info(core)
        fps = info.timing.fps or 60.0988
        sample_rate = int(round(info.timing.sample_rate or 32040))
        total = int(round(args.seconds * fps))
        select_frames = int(round(args.select_seconds * fps))
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
            fd, name = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            Path(name).unlink()
            wav_path = Path(name)

        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", "256x224", "-r", f"{fps:.4f}", "-i", "pipe:0",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]

        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        before_msufail = word(core, RT_MSUFAIL)
        before_oamdrop = word(core, RT_OAMDROP)

        # Browse the roster for a moment, then land on the final picks.
        browse = [(select_frames // 5, lambda: tap(core, BTN_RIGHT)),
                  (select_frames * 2 // 5, lambda: tap(core, BTN_DOWN)),
                  (select_frames * 3 // 5, lambda: tap(core, BTN_RIGHT)),
                  (select_frames * 4 // 5, lambda: (tap(core, BTN_LEFT, port=1),
                                                  tap(core, BTN_LEFT, port=1)))]
        browse_i = 0
        locked = False
        fight_frames = 0
        try:
            for index in range(total):
                if not locked and browse_i < len(browse) and \
                        index == browse[browse_i][0]:
                    browse[browse_i][1]()
                    browse_i += 1
                if not locked and index >= select_frames:
                    core.ram[SEL1] = p1
                    core.ram[SEL2] = p2
                    core.ram[LOCK1] = 1
                    core.ram[LOCK2] = 1
                    core.ram[CPU1] = 1
                    core.ram[CPU2] = 1
                    core.ram[AI_LEVEL] = args.level
                    locked = True
                core.step()
                if core.last_frame is None:
                    continue
                raw, width, height = frame_rgb(core.last_frame)
                if (width, height) != (256, 224):
                    raise ValueError(f"unexpected frame size {width}x{height}")
                process.stdin.write(raw)
                if core.ram[GS] == 1:
                    fight_frames += 1
                if index and index % 300 == 0:
                    print(f"  {index}/{total} frames gs={core.ram[GS]}",
                          flush=True)
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
            with_audio = output.with_suffix(".audio.mp4")
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(output),
                 "-i", str(wav_path), "-c:v", "copy", "-c:a", "aac",
                 "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                 str(with_audio)], check=True)
            with_audio.replace(output)
            wav_path.unlink(missing_ok=True)

        sidecar = {
            "pair": [p1, p2],
            "level": args.level,
            "video_frames": total,
            "fight_frames": fight_frames,
            "fps_setting": round(fps, 4),
            "sample_rate": sample_rate,
            "audio": not args.no_audio,
            "gs_final": core.ram[GS],
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
