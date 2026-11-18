#!/usr/bin/env python3
"""Record the v2.0.2 showcase: corrected moves for Kim, Chun-Li, Heidern, Iori.

Everything runs headless through the libretro Snes9x core with scripted pad
input (the same motions the regression tests use).  Frames are scaled 3x,
captioned and piped to ffmpeg as one H.264 MP4 (no audio).

    python3 tools/capture_v202_video.py [--out work/videos/kof98_v202.mp4]
"""
import argparse
import ctypes as C
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core                              # noqa: E402
from capture_bout_video import av_info, frame_rgb                           # noqa: E402
from test_counter_grab_headless import boot_select, enter_fight    # noqa: E402
import test_command_list_headless as cl                            # noqa: E402

CORE = "/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so"
P1, P2 = 0x4000, 0x4040
STATE, HP, POWER = 0x4008, 0x4010, 0x4030
DOWN, LEFT, RIGHT = 5, 6, 7
Y, X, B, A = 1, 9, 0, 8
SCALE = 3
W, H, BAR = 256 * SCALE, 224 * SCALE, 0   # no caption bar: raw gameplay
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


class Recorder:
    def __init__(self, core, path):
        self.core = core
        self.on = False
        self.caption = ("", "")
        self.frames = 0
        self.ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
             "-pix_fmt", "rgb24", "-s", f"{W}x{H + BAR}", "-r", "60.0988",
             "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)],
            stdin=subprocess.PIPE)
        try:
            self.big = ImageFont.truetype(FONT, 26)
            self.small = ImageFont.truetype(FONT, 17)
        except OSError:
            self.big = self.small = ImageFont.load_default()
        info = av_info(core)
        self.fps = info.timing.fps or 60.0988
        self.rate = int(round(info.timing.sample_rate or 32040))
        self.audio = []          # one PCM chunk per emitted video frame
        self.pending = []
        self.hold = None         # frames of the current take (for replays)
        self.attach(core)

    def attach(self, core):
        self.core = core
        rec = self

        @C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
        def audio_batch(data, count):
            if data and count:
                rec.pending.append(C.string_at(data, count * 4))
            return count
        self._cb = audio_batch
        core.lib.retro_set_audio_sample_batch(audio_batch)
        self.raw_step = core.step
        core.capture_video = True
        core.step = self.step

    def silence(self, frames=1):
        return b"\0" * (int(round(self.rate / self.fps)) * 4) * frames

    def emit(self, img, pcm=None):
        self.ff.stdin.write(img.tobytes())
        self.audio.append(pcm if pcm is not None else self.silence())
        self.frames += 1

    def compose(self, raw, w, h):
        game = Image.frombytes("RGB", (w, h), raw).resize(
            (W, H), Image.NEAREST)
        canvas = Image.new("RGB", (W, H + BAR), (12, 12, 20))
        canvas.paste(game, (0, 0))
        if not BAR:
            return canvas
        d = ImageDraw.Draw(canvas)
        title, sub = self.caption
        d.text((14, H + 4), title, font=self.big, fill=(255, 224, 96))
        d.text((14, H + 34), sub, font=self.small, fill=(200, 200, 215))
        return canvas

    def step(self, n=1):
        for _ in range(n):
            self.pending = []
            self.raw_step(1)
            if self.on and self.core.last_frame is not None:
                raw, w, h = frame_rgb(self.core.last_frame)
                img = self.compose(raw, w, h)
                if self.hold is not None:
                    self.hold.append(img)
                self.emit(img, b"".join(self.pending))

    def slowmo(self, caption, factor=3):
        """Replay the held take at 1/factor speed (silent)."""
        old = self.caption
        self.caption = caption
        for img in self.hold or []:
            tint = self.relabel(img)
            for _ in range(factor):
                self.emit(tint, self.silence())
        self.caption = old
        self.hold = None

    def relabel(self, img):
        img = img.copy()
        d = ImageDraw.Draw(img)
        if not BAR:
            return img
        d.rectangle((0, H, W, H + BAR), fill=(12, 12, 20))
        d.text((14, H + 4), self.caption[0], font=self.big,
               fill=(255, 224, 96))
        d.text((14, H + 34), self.caption[1], font=self.small,
               fill=(200, 200, 215))
        return img

    def card(self, title, sub, seconds=2.0):
        img = Image.new("RGB", (W, H + BAR), (12, 12, 20))
        d = ImageDraw.Draw(img)
        big = ImageFont.truetype(FONT, 44) if Path(FONT).exists() else None
        d.text((W // 2, (H + BAR) // 2 - 30), title, font=big,
               fill=(255, 224, 96), anchor="mm")
        d.text((W // 2, (H + BAR) // 2 + 30), sub, font=self.big,
               fill=(220, 220, 235), anchor="mm")
        for _ in range(int(seconds * 60)):
            self.emit(img)

    def close(self, output=None):
        self.ff.stdin.close()
        code = self.ff.wait()
        if code or output is None:
            return code
        fd, name = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with wave.open(name, "wb") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(self.rate)
            wav.writeframes(b"".join(self.audio))
        tmp = str(output) + ".silent.mp4"
        os.replace(output, tmp)
        code = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", name,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
             "-movflags", "+faststart", str(output)]).returncode
        os.unlink(name)
        os.unlink(tmp)
        return code


def pad(core, seq, buttons, hold=2):
    for d in seq:
        core.buttons[0] = set(d)
        core.step(hold)
    core.buttons[0] = set(seq[-1]) | set(buttons)
    core.step(2)
    core.buttons[0] = set()


QCB = [(DOWN,), (DOWN, LEFT), (LEFT,)]
DP = [(RIGHT,), (DOWN,), (DOWN, RIGHT)]


def setup(core, select, p1, p2, x1=80, x2=110, hp=300, power=3000):
    core.on_rec = False
    enter_fight(core, select, p1, p2)
    core.put(P1, x1 << 8)
    core.put(P2, x2 << 8)
    core.put(HP + 0x40, hp)
    core.put(POWER, power)
    core.step(30)


def run_clip(rec, core, select, p1, p2, title, sub, actions, tail=60,
             x2=110, track=None):
    setup(core, select, p1, p2, x2=x2)
    rec.caption = ("", "")
    rec.on = True
    core.step(40)
    path = []
    for act in actions:
        act()
        for _ in range(act.wait if hasattr(act, "wait") else 0):
            core.step()
            s = core.ram[STATE]
            if not path or path[-1] != s:
                path.append(s)
    core.step(tail)
    rec.on = False
    print(f"{title}: P1 states {path}", flush=True)


def reset():
    """Between two takes of one clip: stand them back up at close range."""
    core_ref[0].put(P1, 80 << 8)
    core_ref[0].put(P2, 110 << 8)
    core_ref[0].put(HP + 0x40, 300)
    core_ref[0].put(POWER, 3000)
    core_ref[0].step(90)


core_ref = [None]


def act(fn, wait=0):
    fn.wait = wait
    return fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "work/videos/kof98_v202.mp4"))
    ap.add_argument("--rom", default=str(ROOT / "kof98-snes.sfc"))
    args = ap.parse_args()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    core = Core(CORE, args.rom)
    core_ref[0] = core
    rec = Recorder(core, args.out)
    try:
        select = boot_select(core)

        # --- Kim -----------------------------------------------------------
        def kim_super(buttons):
            return act(lambda: pad(core, QCB * 2, buttons), 240)

        def refill():
            reset()
        run_clip(rec, core, select, "kim", "kyo", "Kim - Hou'oh Tenbu Kyaku",
                 "super completo: sequência de chutes e finalização",
                 [kim_super([A]), act(refill, 0), kim_super([A, B])],
                 tail=150)

        # --- Chun-Li vs Sakura --------------------------------------------
        run_clip(rec, core, select, "chunli", "sakura",
                 "Chun-Li vs Sakura - Spinning Bird Kick",
                 "5 impactos e derrubada (QCB+B)",
                 [act(lambda: (setattr(rec, "hold", []),
                               pad(core, QCB, [B])), 110)], tail=25)
        rec.slowmo(("", ""))

        # --- Chun-Li: Hyakuretsu em pe (B repetido) -----------------------
        def rapid():
            for _ in range(6):
                core.buttons[0] = {B}
                core.step(2)
                core.buttons[0] = set()
                core.step(4)
        run_clip(rec, core, select, "chunli", "sakura",
                 "Chun-Li - Hyakuretsu Kyaku",
                 "chutes seguidos em pé, 5 impactos (B repetido)",
                 [act(lambda: (setattr(rec, "hold", []), rapid()), 90)],
                 tail=30)
        rec.slowmo(("", ""))

        # --- Heidern -------------------------------------------------------
        run_clip(rec, core, select, "heidern", "kyo",
                 "Heidern - Neck Rolling",
                 "continuação do ataque à cabeça (DP+A / DP+B)",
                 [act(lambda: pad(core, DP, [A]), 150),
                  act(reset, 0),
                  act(lambda: pad(core, DP, [B]), 150)], tail=30)

        # --- Iori ----------------------------------------------------------
        def chain():
            pad(core, QCB, [Y])
            core.step(12)
            pad(core, QCB, [X])
            core.step(14)
            pad(core, QCB, [Y])
        run_clip(rec, core, select, "iori", "kyo",
                 "Iori - Ya Otome / Aoi Hana",
                 "3 etapas encadeadas, termina pulando e derrubando",
                 [act(chain, 130)], x2=105, tail=40)

        # --- Command List ---------------------------------------------------
        core2 = Core(CORE, args.rom)
        rec.attach(core2)
        for _ in range(80):
            if core2.ram[cl.GS] == 6:
                break
            cl.tap(core2, cl.START)
        cl.wait(core2, lambda: core2.ram[cl.GS] == 6, "mode menu")
        cl.start_practice(core2)
        rec.on = True
        core2.step(30)
        cl.open_command_list(core2)
        core2.step(50)
        for _ in range(4):
            cl.press(core2, cl.DOWN)
        core2.step(40)
        cl.press(core2, cl.A)
        core2.step(120)
        rec.on = False

    finally:
        code = rec.close(args.out)
    print(f"frames={rec.frames} ffmpeg={code} -> {args.out}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
