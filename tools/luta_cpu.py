#!/usr/bin/env python3
"""Roda lutas CPU vs CPU com os personagens que você escolher.

Uso rápido:

    python3 tools/luta_cpu.py "luta Kyo vs Iori"
    python3 tools/luta_cpu.py "luta Terry vs Mai" --seconds 20
    python3 tools/luta_cpu.py --list
    python3 tools/luta_cpu.py "luta Mr. Karate vs Omega Rugal" --no-video

Sem argumentos, abre um prompt onde você pode digitar várias lutas:

    luta> luta Kyo vs Iori
    luta> luta Heavy D vs Blue Mary
    luta> sair

O script usa a ROM atual (`kof98-snes.sfc`) e o `.msu` que estiver ao lado
dela. Por padrão grava um MP4 em `work/videos/` com imagem e som; use
`--no-video` para só simular e ver o resultado.

Os personagens escondidos são selecionados como no jogo:
  * Omega Rugal  -> L+R sobre o Rugal
  * Kyo Nests    -> L sobre o Kyo
  * Kyo Ash      -> R sobre o Kyo
  * Mr. Karate   -> L+R sobre o Robert (precisa do .msu)

O script seleciona os dois lados como humanos e só liga o CPU depois que a
luta começa. Isso é necessário para os personagens escondidos: o próprio jogo
troca o Mr. Karate por Robert quando os dois lados já estão marcados como CPU
antes do início do combate.
"""
from __future__ import annotations

import argparse
import ctypes as C
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import wave
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from calibration.headless import Core  # noqa: E402
from capture_bout_video import av_info, frame_rgb  # noqa: E402

DEFAULT_CORE = Path("/usr/lib/x86_64-linux-gnu/libretro/snes9x_libretro.so")
DEFAULT_ROM = ROOT / "kof98-snes.sfc"
NEWTABS = ROOT / "build" / "gen_fight" / "newchars_tabs.inc"
SELDATA = ROOT / "src" / "gen_menu" / "seldata.inc"

# Endereços de WRAM usados pelo motor (ver tools/calibration/headless.py e
# tools/test_ai_headless.py).
GS = 0x1020
FRAME = 0x1024
MSUOK = 0x107A
WINS1, WINS2 = 0x1080, 0x1081
ROUNDWIN = 0x1083
SEL1, SEL2 = 0x1085, 0x1086
LOCK1, LOCK2 = 0x108E, 0x108F
CPU1, CPU2 = 0x1090, 0x1091
AI_LEVEL = 0x10EB
M_ITEM = 0xF070
SCUR1, SCUR2 = 0xF052, 0xF053
HP1, HP2 = 0x4010, 0x4050
F_CHAR = 44

# Botões do SNES no mapeamento do libretro.
BTN = {
    "B": 0, "Y": 1, "SELECT": 2, "START": 3,
    "UP": 4, "DOWN": 5, "LEFT": 6, "RIGHT": 7,
    "A": 8, "X": 9, "L": 10, "R": 11,
}

# Personagens que existem inteiramente na ROM. Os demais precisam do .msu.
ROM_SAFE = {0, 1, 2, 12, 13, 14, 15}

# Como cada personagem escondido é escolhido na tela de seleção.
# (célula do cursor, botões segurados, descrição)
HIDDEN = {
    # CJ shares John's select portrait; L+R on it picks the ported fighter.
    "cj": (51, ("L", "R"), "L+R sobre o John"),
    "omegarugal": (37, ("L", "R"), "L+R sobre o Rugal"),
    "kyonests": (3, ("L",), "L sobre o Kyo"),
    "kyoash": (3, ("R",), "R sobre o Kyo"),
    "mrkarate": (10, ("L", "R"), "L+R sobre o Robert"),
}

DISPLAY = {
    "kyo": "Kyo", "iori": "Iori", "shingo": "Shingo", "rugal": "Rugal",
    "saisyu": "Saisyu", "heidern": "Heidern", "takuma": "Takuma",
    "clark": "Clark", "ralf": "Ralf", "leona": "Leona", "mature": "Mature",
    "vice": "Vice", "benimaru": "Benimaru", "daimon": "Daimon",
    "omegarugal": "Omega Rugal", "terry": "Terry", "andy": "Andy",
    "joe": "Joe", "ryo": "Ryo", "robert": "Robert", "yuri": "Yuri",
    "athena": "Athena", "kensou": "Kensou", "chin": "Chin", "king": "King",
    "mai": "Mai", "chizuru": "Chizuru", "kim": "Kim", "chang": "Chang",
    "choi": "Choi", "yashiro": "Yashiro", "shermie": "Shermie",
    "chris": "Chris", "yamazaki": "Yamazaki", "mary": "Blue Mary",
    "billy": "Billy", "lucky": "Lucky", "heavyd": "Heavy D!",
    "brian": "Brian", "geese": "Geese", "krauser": "Krauser",
    "mrbig": "Mr. Big", "eiji": "Eiji", "vega": "Vega (M. Bison)",
    "ryu": "Ryu", "ken": "Ken", "chunli": "Chun-Li", "sakura": "Sakura",
    "kasumi": "Kasumi", "duckking": "Duck King", "yuki": "Yuki",
    "kyonests": "Kyo Nests", "kyoash": "Kyo Ash", "mrkarate": "Mr. Karate",
}

# Apelidos aceitos além do nome canônico e do nome exibido.
ALIASES = {
    "kyo": ("kyo kusanagi",),
    "iori": ("iori yagami",),
    "shingo": ("shingo yabuki",),
    "rugal": ("rugal bernstein",),
    "saisyu": ("saisyu kusanagi",),
    "heidern": ("heidern",),
    "takuma": ("takuma sakazaki",),
    "clark": ("clark still",),
    "ralf": ("ralf jones",),
    "leona": ("leona heidern",),
    "mature": ("mature",),
    "vice": ("vice",),
    "benimaru": ("benimaru nikaido",),
    "daimon": ("goro daimon",),
    "omegarugal": ("omega rugal", "rugal omega", "o rugal", "orugal"),
    "terry": ("terry bogard",),
    "andy": ("andy bogard",),
    "joe": ("joe higashi",),
    "ryo": ("ryo sakazaki",),
    "robert": ("robert garcia",),
    "yuri": ("yuri sakazaki",),
    "athena": ("athena asamiya",),
    "kensou": ("sie kensou",),
    "chin": ("chin gentsai",),
    "king": ("king",),
    "mai": ("mai shiranui",),
    "chizuru": ("chizuru kagura",),
    "kim": ("kim kaphwan",),
    "chang": ("chang koehan",),
    "choi": ("choi bounge",),
    "yashiro": ("yashiro nanakase",),
    "shermie": ("shermie",),
    "chris": ("chris",),
    "yamazaki": ("ryuji yamazaki",),
    "mary": ("blue mary", "mary"),
    "billy": ("billy kane",),
    "lucky": ("lucky glauber",),
    "heavyd": ("heavy d", "heavy-d", "heavy d!", "heavyd"),
    "brian": ("brian battler",),
    "geese": ("geese howard",),
    "krauser": ("wolfgang krauser",),
    "mrbig": ("mr big", "mister big"),
    "eiji": ("eiji kisaragi",),
    "vega": ("m bison", "m. bison", "bison"),
    "ryu": ("ryu",),
    "ken": ("ken masters",),
    "chunli": ("chun li", "chun-li"),
    "sakura": ("sakura kasugano",),
    "kasumi": ("kasumi todoh",),
    "duckking": ("duck king", "duckking"),
    "yuki": ("yuki", "yuki kusanagi"),
    "kyonests": ("kyo nests", "nests kyo", "kyo ex", "kyo 99"),
    "kyoash": ("kyo ash", "ash kyo", "kyo 2003"),
    "mrkarate": ("mr karate", "mister karate", "senhor karate", "karate"),
}


class MatchError(RuntimeError):
    """Erro de nome, seleção ou execução de uma luta."""


@dataclass(frozen=True)
class Character:
    id: int
    key: str
    name: str
    cell: int


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("&", " e ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_roster() -> dict[int, Character]:
    if not NEWTABS.exists() or not SELDATA.exists():
        raise MatchError(
            "Tabelas do elenco não encontradas. Rode o build do jogo primeiro "
            f"({NEWTABS} e {SELDATA})."
        )
    names: list[str] = []
    rows = NEWTABS.read_text().split("CharSelTab:", 1)[1].split("BankSelTab:", 1)[0]
    for line in rows.splitlines():
        if ".dw" not in line:
            continue
        for m in re.finditer(r"\bChar([A-Za-z0-9]+)\b", line.split(".dw", 1)[1]):
            names.append(m.group(1).lower())

    cells: list[int] = []
    for line in SELDATA.read_text().splitlines():
        if line.startswith("SelChrCell:"):
            cells = [int(x) for x in line.split(".db", 1)[1].strip().split(",")]
            break

    roster: dict[int, Character] = {}
    for cid, key in enumerate(names):
        roster[cid] = Character(
            id=cid,
            key=key,
            name=DISPLAY.get(key, key.title()),
            cell=cells[cid] if cid < len(cells) else 0,
        )
    return roster


def build_aliases(roster: dict[int, Character]) -> dict[str, int]:
    aliases: dict[str, int] = {}
    for cid, ch in roster.items():
        for alias in (ch.key, ch.name, *ALIASES.get(ch.key, ())):
            aliases[normalize(alias)] = cid
    return aliases


def resolve(text: str, roster: dict[int, Character],
            aliases: dict[str, int]) -> Character:
    key = normalize(text)
    if key.isdigit():
        cid = int(key)
        if cid in roster:
            return roster[cid]
        raise MatchError(f"Não existe personagem com o ID {cid}.")
    if key in aliases:
        return roster[aliases[key]]
    close = difflib.get_close_matches(key, list(aliases), n=3, cutoff=0.55)
    hint = ""
    if close:
        hint = " Você quis dizer: " + ", ".join(
            roster[aliases[c]].name for c in close
        ) + "?"
    raise MatchError(f'Não conheço o personagem "{text.strip()}".{hint}')


def parse_match(text: str, roster: dict[int, Character],
                aliases: dict[str, int]) -> tuple[Character, Character]:
    norm = normalize(text)
    norm = re.sub(r"^(?:luta|briga|batalha|fight)\s+", "", norm)
    parts = re.split(r"\s+(?:vs|versus|contra|x)\s+", norm, maxsplit=1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise MatchError(
            'Use o formato "luta X vs Y" (ex.: "luta Kyo vs Iori").'
        )
    return resolve(parts[0], roster, aliases), resolve(parts[1], roster, aliases)


def tap(core: Core, button: int, port: int = 0) -> None:
    core.buttons[port] = {button}
    core.step(4)
    core.buttons[port] = set()
    core.step(10)


def wait(core: Core, predicate, label: str, limit: int = 12000) -> None:
    for _ in range(limit):
        if predicate():
            return
        core.step()
    raise MatchError(
        f"{label}: o jogo não chegou ao estado esperado "
        f"(gs={core.ram[GS]}, seleção={core.ram[SEL1]}/{core.ram[SEL2]})."
    )


def boot_to_select(core: Core) -> bool:
    """Abre a tela de seleção do modo SINGLE VS. Devolve msuok."""
    core.buttons = [set(), set()]
    for _ in range(160):
        if core.ram[GS] == 6:
            break
        tap(core, BTN["START"])
    wait(core, lambda: core.ram[GS] == 6, "menu de modos")
    core.step(30)                           # deixa o menu terminar de abrir
    for _ in range(4):
        core.ram[M_ITEM] = 1                # SINGLE VS
        tap(core, BTN["START"])
        for _ in range(600):
            if core.ram[GS] == 5:
                return bool(core.ram[MSUOK])
            core.step()
    raise MatchError(
        f"não consegui abrir a seleção de personagens "
        f"(gs={core.ram[GS]}, item={core.ram[M_ITEM]})."
    )


def hidden_info(ch: Character) -> tuple[int, tuple[str, ...], str]:
    return HIDDEN.get(ch.key, (ch.cell, (), "normal"))


def lock_side(core: Core, side: int, ch: Character, msuok: bool) -> None:
    """Coloca o cursor na célula certa e confirma o personagem."""
    cell, held, how = hidden_info(ch)
    if ch.id not in ROM_SAFE and not msuok:
        raise MatchError(
            f"{ch.name} precisa do arquivo .msu ao lado da ROM. "
            "Sem ele, só os personagens que já estão na ROM podem ser usados."
        )
    if ch.key in HIDDEN and ch.id not in ROM_SAFE and not msuok:
        raise MatchError(f"{ch.name} precisa do .msu para ser selecionado.")

    scur = SCUR1 if side == 0 else SCUR2
    lock = LOCK1 if side == 0 else LOCK2
    sel = SEL1 if side == 0 else SEL2
    buttons = {BTN[b] for b in held}

    for _ in range(8):
        core.ram[scur] = cell
        core.buttons[side] = set(buttons)
        core.step(4)
        core.buttons[side] = set(buttons) | {BTN["A"]}
        core.step(4)
        core.buttons[side] = set(buttons)
        core.step(4)
        core.buttons[side] = set()
        core.step(10)
        if core.ram[lock] == 1 and core.ram[sel] == ch.id:
            return
    raise MatchError(
        f"Não consegui selecionar {ch.name} ({how}). "
        "Confira se a ROM e o arquivo .msu são do mesmo build."
    )


def start_fight(core: Core, p1: Character, p2: Character, level: int,
                skip_intro: bool = True) -> None:
    """Seleciona os dois lados como humanos e liga o CPU no início da luta."""
    core.ram[CPU1] = 0
    core.ram[CPU2] = 0
    msuok = bool(core.ram[MSUOK])

    # P2 primeiro, como nos scripts de captura do projeto.
    lock_side(core, 1, p2, msuok)
    lock_side(core, 0, p1, msuok)

    wait(core, lambda: core.ram[GS] in (1, 4), "carregamento da luta")
    if core.ram[GS] == 4:
        if skip_intro:
            tap(core, BTN["START"])         # pula a apresentação
        else:
            # The caller records from here; the scripted intro states do not
            # read the AI flags, so the CPU can take over at GS 1.
            core.ram[CPU1] = 1
            core.ram[CPU2] = 1
            core.ram[AI_LEVEL] = max(1, min(9, level))
            core.buttons = [set(), set()]
            return
    wait(core, lambda: core.ram[GS] == 1, "início da luta")

    # Só agora o CPU assume. O jogo preserva os personagens escondidos
    # escolhidos como humanos, inclusive o Mr. Karate.
    core.ram[CPU1] = 1
    core.ram[CPU2] = 1
    core.ram[AI_LEVEL] = max(1, min(9, level))
    core.buttons = [set(), set()]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", normalize(text)).strip("_") or "luta"


def default_output(p1: Character, p2: Character) -> Path:
    return ROOT / "work" / "videos" / f"luta_{slug(p1.name)}_vs_{slug(p2.name)}.mp4"


def run_match(p1: Character, p2: Character, args: argparse.Namespace) -> int:
    if not args.rom.exists():
        raise MatchError(f"ROM não encontrada: {args.rom}")
    if not args.core.exists():
        raise MatchError(f"Core do Snes9x não encontrado: {args.core}")
    if not args.no_video and not shutil_which("ffmpeg"):
        raise MatchError(
            "ffmpeg não encontrado. Instale o ffmpeg ou use --no-video."
        )

    output = args.output or default_output(p1, p2)
    output.parent.mkdir(parents=True, exist_ok=True)

    core = Core(args.core, args.rom)
    try:
        msuok = boot_to_select(core)
        if not msuok and (p1.id not in ROM_SAFE or p2.id not in ROM_SAFE):
            print("  aviso: .msu ausente; personagens externos podem ser "
                  "recusados pelo jogo.", flush=True)
        start_fight(core, p1, p2, args.level,
                    skip_intro=not args.intro)

        info = av_info(core)
        fps = info.timing.fps or 60.0988
        sample_rate = int(round(info.timing.sample_rate or 32040))
        if args.seconds is not None:
            limit_frames = max(1, int(round(args.seconds * fps)))
        else:
            limit_frames = max(1, int(round(args.max_seconds * fps)))

        print(
            f"  luta: {p1.name} (P1) vs {p2.name} (P2) — "
            f"CPU nível {max(1, min(9, args.level))}, MSU={'sim' if msuok else 'não'}",
            flush=True,
        )

        if args.no_video:
            summary = _run_headless(core, p1, p2, args, limit_frames, fps)
        else:
            summary = _run_recorded(
                core, p1, p2, args, limit_frames, fps, sample_rate, output
            )

        summary.update({
            "p1": p1.name,
            "p2": p2.name,
            "ids": [p1.id, p2.id],
            "msu": msuok,
            "level": max(1, min(9, args.level)),
            "fps": round(fps, 4),
            "output": None if args.no_video else str(output),
        })
        if not args.no_video:
            output.with_suffix(".json").write_text(
                json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
            )
        _print_summary(summary, p1, p2)
        return 0
    finally:
        core.close()


def _run_headless(core: Core, p1: Character, p2: Character,
                  args: argparse.Namespace, limit_frames: int,
                  fps: float) -> dict:
    summary = _play(core, args, limit_frames, fps, write_frame=None,
                    expect=(p1, p2))
    return summary


def _run_recorded(core: Core, p1: Character, p2: Character,
                  args: argparse.Namespace, limit_frames: int,
                  fps: float, sample_rate: int, output: Path) -> dict:
    chunks: list[bytes] = []

    if not args.no_audio:
        @C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
        def audio_batch(data, count):
            if data and count:
                chunks.append(C.string_at(data, count * 4))
            return count

        core.lib.retro_set_audio_sample_batch(audio_batch)

    core.capture_video = True
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", "256x224", "-r", f"{fps:.4f}", "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write_frame() -> bool:
        if core.last_frame is None:
            return False
        raw, width, height = frame_rgb(core.last_frame)
        if (width, height) != (256, 224):
            raise MatchError(f"quadro inesperado do emulador: {width}x{height}")
        process.stdin.write(raw)
        return True

    try:
        summary = _play(core, args, limit_frames, fps, write_frame=write_frame,
                        expect=(p1, p2))
    finally:
        core.capture_video = False
        process.stdin.close()
        code = process.wait()
    if code != 0:
        raise MatchError(f"ffmpeg terminou com código {code}")

    if chunks:
        fd, name = tempfile.mkstemp(suffix=".wav", dir="/tmp/opencode")
        os.close(fd)
        wav_path = Path(name)
        try:
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
                 str(with_audio)],
                check=True,
            )
            with_audio.replace(output)
        finally:
            wav_path.unlink(missing_ok=True)

    summary["video_frames"] = summary["frames"]
    return summary


def _play(core: Core, args: argparse.Namespace, limit_frames: int,
          fps: float, write_frame, expect: tuple[Character, Character]) -> dict:
    """Avança o emulador, opcionalmente gravando, e acompanha o placar."""
    frames = 0
    fight_frames = 0
    kos = 0
    last_gs = -1
    saw_fight = False
    finish_frames = 0
    max_wins = (0, 0)
    last_roundwin = 0
    round_no = 0

    while frames < limit_frames:
        core.step()
        frames += 1
        if write_frame is not None and not write_frame():
            continue

        gs = core.ram[GS]
        # Cada round é remontado pelo motor.  Confere que ele manteve os
        # personagens pedidos; sem o latch da seleção secreta, o sanitizador
        # devolvia o Mr. Karate como Robert a partir do round 2.
        if gs == 1 and last_gs != 1:
            round_no += 1
            want = (expect[0].id, expect[1].id)
            got = (core.ram[SEL1], core.ram[SEL2])
            if got != want:
                raise MatchError(
                    f"round {round_no}: o jogo trocou a seleção "
                    f"{want[0]}/{want[1]} -> {got[0]}/{got[1]} "
                    f"({expect[0].name} vs {expect[1].name})."
                )
        if gs == 1:
            saw_fight = True
            fight_frames += 1
        if gs == 2 and last_gs != 2:
            kos += 1
            last_roundwin = core.ram[ROUNDWIN]
        last_gs = gs

        w1, w2 = core.ram[WINS1], core.ram[WINS2]
        max_wins = (max(max_wins[0], w1), max(max_wins[1], w2))

        # Partida em modo versus termina quando um lado chega a 2 vitórias
        # e o jogo volta à seleção. Dá alguns segundos para o K.O. aparecer.
        if saw_fight and (w1 >= 2 or w2 >= 2):
            finish_frames += 1
        if args.seconds is None and saw_fight:
            if gs == 5 or finish_frames > int(3 * fps):
                break

        if frames % int(10 * fps) == 0:
            print(f"  {frames / fps:5.1f}s  placar {max_wins[0]}x{max_wins[1]}"
                  f"  gs={gs}", flush=True)

    winner = None
    if max_wins[0] > max_wins[1]:
        winner = 1
    elif max_wins[1] > max_wins[0]:
        winner = 2

    return {
        "frames": frames,
        "fight_frames": fight_frames,
        "seconds": round(frames / fps, 3),
        "fight_seconds": round(fight_frames / fps, 3),
        "wins": list(max_wins),
        "winner": winner,
        "kos": kos,
        "last_roundwin": last_roundwin,
        "finished": finish_frames > 0 or (saw_fight and core.ram[GS] == 5),
        "gs_final": core.ram[GS],
    }


def _print_summary(summary: dict, p1: Character, p2: Character) -> None:
    w1, w2 = summary["wins"]
    if summary["winner"] == 1:
        result = f"{p1.name} venceu"
    elif summary["winner"] == 2:
        result = f"{p2.name} venceu"
    else:
        result = "sem vencedor (empate ou tempo esgotado)"
    print(
        f"  resultado: {p1.name} {w1} x {w2} {p2.name} — {result}",
        flush=True,
    )
    if summary["output"]:
        print(f"  vídeo: {summary['output']}", flush=True)
    else:
        print("  modo sem vídeo (--no-video)", flush=True)


def shutil_which(name: str) -> str | None:
    from shutil import which
    return which(name)


def print_roster(roster: dict[int, Character]) -> None:
    print("Personagens disponíveis (use o nome ou o ID):\n")
    print(f"{'ID':>3}  {'Nome':<16}  Seleção")
    print(f"{'---':>3}  {'-' * 16}  -------")
    for cid in sorted(roster):
        ch = roster[cid]
        how = HIDDEN.get(ch.key, (None, (), "normal"))[2]
        print(f"{cid:>3}  {ch.name:<16}  {how}")
    print(
        "\nDica: o script aceita acentos, maiúsculas e apelidos "
        "(ex.: \"blue mary\", \"heavy d\", \"m bison\")."
    )


def interactive(roster: dict[int, Character], aliases: dict[str, int],
                args: argparse.Namespace) -> int:
    print('Digite "luta X vs Y" para rodar uma luta, "lista" para ver o elenco')
    print('ou "sair" para terminar.')
    while True:
        try:
            line = input("luta> ").strip()
        except EOFError:
            print()
            return 0
        if not line:
            continue
        if line.lower() in {"sair", "exit", "quit"}:
            return 0
        if line.lower() in {"lista", "list", "elenco", "chars"}:
            print_roster(roster)
            continue
        try:
            p1, p2 = parse_match(line, roster, aliases)
            run_match(p1, p2, args)
        except MatchError as exc:
            print(f"  erro: {exc}", flush=True)
        except KeyboardInterrupt:
            print("\n  interrompido.", flush=True)
            return 130


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Roda uma luta CPU vs CPU na ROM atual do port.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Exemplos:\n'
               '  python3 tools/luta_cpu.py "luta Kyo vs Iori"\n'
               '  python3 tools/luta_cpu.py "luta Terry vs Mai" --seconds 20\n'
               '  python3 tools/luta_cpu.py --list',
    )
    parser.add_argument("match", nargs="?",
                        help='texto no formato "luta X vs Y"')
    parser.add_argument("--list", action="store_true",
                        help="lista os personagens e como escolhê-los")
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM,
                        help="ROM a usar (padrão: kof98-snes.sfc)")
    parser.add_argument("--core", type=Path, default=DEFAULT_CORE,
                        help="core libretro do Snes9x")
    parser.add_argument("--seconds", type=float, default=None,
                        help="grava exatamente N segundos (padrão: até acabar)")
    parser.add_argument("--max-seconds", type=float, default=150.0,
                        help="limite de segurança quando não há --seconds")
    parser.add_argument("--level", type=int, default=8,
                        help="nível da IA, 1 a 9 (padrão: 8)")
    parser.add_argument("--intro", action="store_true",
                        help="grava também a apresentação dos lutadores")
    parser.add_argument("--no-video", action="store_true",
                        help="não grava MP4; só simula e mostra o resultado")
    parser.add_argument("--no-audio", action="store_true",
                        help="grava o vídeo sem som")
    parser.add_argument("--output", type=Path,
                        help="caminho do MP4 de saída")
    args = parser.parse_args()

    try:
        roster = load_roster()
        aliases = build_aliases(roster)
    except MatchError as exc:
        parser.error(str(exc))
        return 2

    if args.list:
        print_roster(roster)
        return 0
    if args.match is None:
        return interactive(roster, aliases, args)

    try:
        p1, p2 = parse_match(args.match, roster, aliases)
        return run_match(p1, p2, args)
    except MatchError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrompido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
