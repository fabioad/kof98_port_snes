#!/usr/bin/env python3
"""Record the release teaser: new COMMAND LIST + Jason/John/Lucia fights.

Scenes (one continuous take, 1080x1080 for social media):
  1. PRACTICE with Jason (P1) / John (P2): pause menu -> COMMAND LIST, scroll
     Jason's list (arrow motions), switch to John's list with RIGHT.
  2. PRACTICE with Lucia: her list.
  3. Jason vs John, CPU vs CPU (select screen + fight).
  4. Lucia vs John, CPU vs CPU.

Frames are composed with PIL (4x nearest-neighbour) and piped to
ffmpeg; the emulator audio is muxed in at the end.

    python3 tools/capture_release_video.py --output work/videos/release.mp4
"""
import argparse
import ctypes as C
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import test_command_list_headless as CL                    # noqa: E402
from calibration.headless import Core                       # noqa: E402
from capture_bout_video import CORE, av_info, frame_rgb     # noqa: E402
from test_counter_grab_headless import boot_select          # noqa: E402
from test_roster import parse_tables                        # noqa: E402
from test_ai_headless import (                              # noqa: E402
    AI_LEVEL, CPU1, CPU2, GS, LOCK1, LOCK2, SEL1, SEL2,
)

IDS = {"jason": 54, "john": 55, "lucia": 56}
SIZE = 1080
SCALE = 4

BTN_A = 8


class Recorder:
    def __init__(self, output, fps, sample_rate):
        self.fps = fps
        self.sample_rate = sample_rate
        self.chunks = []
        self.frames = 0
        self.proc = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
             "-pix_fmt", "rgb24", "-s", f"{SIZE}x{SIZE}",
             "-r", f"{fps:.4f}", "-i", "pipe:0", "-c:v", "libx264",
             "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
             str(output)], stdin=subprocess.PIPE)

    def attach(self, core):
        """Hook a fresh core: capture its audio and emit a frame per step."""
        @C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
        def audio_batch(data, count):
            if data and count:
                self.chunks.append(C.string_at(data, count * 4))
            return count
        self._audio_cb = audio_batch
        core.lib.retro_set_audio_sample_batch(audio_batch)
        core.capture_video = True
        run = core.lib.retro_run

        def step(n=1):
            for _ in range(n):
                run()
                self.emit(core)
        core.step = step

    def emit(self, core):
        if core.last_frame is None:
            return
        raw, w, h = frame_rgb(core.last_frame)
        game = Image.frombytes("RGB", (w, h), raw).resize(
            (w * SCALE, h * SCALE), Image.NEAREST)
        canvas = Image.new("RGB", (SIZE, SIZE), (10, 10, 18))
        canvas.paste(game, ((SIZE - game.width) // 2, (SIZE - game.height) // 2))
        self.proc.stdin.write(canvas.tobytes())
        self.frames += 1

    def finish(self, out):
        self.proc.stdin.close()
        if self.proc.wait() != 0:
            raise SystemExit("ffmpeg failed")
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "a.wav"
            with wave.open(str(wav), "wb") as w:
                w.setnchannels(2)
                w.setsampwidth(2)
                w.setframerate(self.sample_rate)
                w.writeframes(b"".join(self.chunks))
            dur = self.frames / self.fps
            final = Path(tmp) / "final.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(out),
                 "-i", str(wav), "-c:v", "copy", "-c:a", "aac", "-b:a",
                 "192k", "-af", f"afade=t=out:st={dur - 1.5:.2f}:d=1.5",
                 "-shortest", "-movflags", "+faststart", str(final)],
                check=True)
            shutil.move(str(final), str(out))


def hold(core, seconds, fps):
    core.step(int(seconds * fps))


def quick(core, button, fps):
    core.buttons[0] = {button}
    core.step(3)
    core.buttons[0] = set()
    core.step(5)


def scroll_list(core, fps, pages):
    """Page through the command list: bursts of DOWN, then a read pause."""
    shown = 0
    while shown < pages and core.ram[CL.CL_SEL] < core.ram[CL.CL_COUNT] - 1:
        for _ in range(11):
            if core.ram[CL.CL_SEL] >= core.ram[CL.CL_COUNT] - 1:
                break
            quick(core, CL.DOWN, fps)
        hold(core, 1.6, fps)
        shown += 1


def practice_scene(rec, fps, p1, p2, who, pages, show_p2):
    core = CL.boot()
    try:
        rec.attach(core)
        core.ram[CL.MSUOK] = 0
        core.ram[CL.M_ITEM] = 5
        for _ in range(30):
            CL.tap(core, CL.START)
            core.step(20)
            if core.ram[GS] == 5:
                break
        CL.wait(core, lambda: core.ram[GS] == 5, "select")
        core.ram[SEL1] = p1
        core.ram[SEL2] = p2
        core.ram[LOCK1] = 1
        core.ram[LOCK2] = 1
        core.ram[CPU1] = 0
        core.ram[CPU2] = 0
        CL.wait(core, lambda: core.ram[GS] == 1, "practice fight")
        core.step(60)
        hold(core, 1.0, fps)
        CL.press(core, CL.START)                 # pause menu
        hold(core, 1.2, fps)
        CL.press(core, CL.DOWN)
        hold(core, 0.5, fps)
        CL.press(core, CL.A)                     # COMMAND LIST
        CL.wait(core, lambda: core.ram[CL.CL_OPEN] == 1, "list open")
        hold(core, 2.2, fps)
        scroll_list(core, fps, pages)
        if show_p2:
            quick(core, CL.RIGHT, fps)
            hold(core, 2.2, fps)
            scroll_list(core, fps, pages)
        hold(core, 0.8, fps)
    finally:
        core.close()


def fight_scene(rec, fps, p1, p2, names, seconds, level):
    roster = {v["name"]: v for v in parse_tables().values()}
    core = Core(CORE, ROOT / "kof98-snes.sfc")
    try:
        boot_select(core)
        rec.attach(core)
        core.ram[CPU1] = 0
        core.ram[CPU2] = 0
        # Park the cursors on the real roster cells, let them sit on camera,
        # then lock both picks with A like a player would.
        for side, char in ((0, p1), (1, p2)):
            core.ram[0xF052 + side] = roster[char]["cell"]
        hold(core, 1.6, fps)
        for side in (0, 1):
            for _ in range(10):
                core.buttons[side] = {BTN_A}
                core.step(4)
                core.buttons[side] = set()
                core.step(8)
                if core.ram[(LOCK1, LOCK2)[side]] == 1:
                    break
            hold(core, 0.5, fps)
        core.ram[CPU1] = 1
        core.ram[CPU2] = 1
        core.ram[AI_LEVEL] = level
        hold(core, 1.0, fps)
        if core.ram[GS] == 5:
            CL.tap(core, CL.START)
        hold(core, seconds, fps)
    finally:
        core.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path,
                    default=ROOT / "work" / "videos" / "kof98_release.mp4")
    ap.add_argument("--fight-seconds", type=float, default=24.0)
    ap.add_argument("--pages", type=int, default=8)
    ap.add_argument("--level", type=int, default=8)
    ap.add_argument("--only", choices=("list", "fights"))
    ap.add_argument("--pairs", nargs="*",
                    help="fights only: p1:p2 character keys "
                         "(default jason:john lucia:john)")
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    probe = Core(CORE, ROOT / "kof98-snes.sfc")
    info = av_info(probe)
    probe.close()
    fps = info.timing.fps or 60.0988
    sr = int(round(info.timing.sample_rate or 32040))
    rec = Recorder(args.output, fps, sr)
    if args.only != "fights":
        practice_scene(rec, fps, IDS["jason"], IDS["john"], "JASON", args.pages, True)
        practice_scene(rec, fps, IDS["lucia"], IDS["john"], "LUCIA", args.pages, False)
    if args.only != "list":
        pairs = args.pairs or ["jason:john", "lucia:john"]
        for pair in pairs:
            p1, p2 = pair.split(":")
            fight_scene(rec, fps, p1, p2, pair.replace(":", "  vs  ").upper(),
                        args.fight_seconds, args.level)
    rec.finish(args.output)
    print(f"{args.output}: {rec.frames} frames, {rec.frames / fps:.1f}s")


if __name__ == "__main__":
    main()
