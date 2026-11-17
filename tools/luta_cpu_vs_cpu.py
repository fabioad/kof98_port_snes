#!/usr/bin/env python3
"""Run CPU-vs-CPU fights on the current ROM by typing "luta X vs Y".

The front-end resolves roster names, refreshes the ROM copy and launches the
Mesen2 testRunner (tools/luta_cpu_vs_cpu.lua).  Each fight reports the winner,
round score and saves a screenshot under work/lutas/.

Examples:
    python3 tools/luta_cpu_vs_cpu.py
    > luta Terry vs Kyo
    > luta Mr. Karate vs Omega Rugal
    > sair

    python3 tools/luta_cpu_vs_cpu.py "luta Sakura vs Iori"
    python3 tools/luta_cpu_vs_cpu.py --list
"""
from __future__ import annotations

import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

try:
    from test_roster import parse_tables
except Exception as exc:  # pragma: no cover - friendly message for a fresh tree
    raise SystemExit(
        f"nao consegui ler as tabelas do roster ({exc}).\n"
        "Gere os assets com: make -f Makefile.pvsnes assets"
    )


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", text.lower())


ALIASES = {
    "mrkarate": "mrkarate",
    "mrcarate": "mrkarate",
    "misterkarate": "mrkarate",
    "mestrekarate": "mrkarate",
    "omegarugal": "omegarugal",
    "rugalomega": "omegarugal",
    "bluemary": "mary",
    "mrbig": "mrbig",
    "heavyd": "heavyd",
    "duckking": "duckking",
    "chunli": "chunli",
    "kyonests": "kyonests",
    "kyoash": "kyoash",
}


def roster_maps():
    roster = parse_tables()
    by_name: dict[str, int] = {}
    names: dict[int, str] = {}
    for cid, row in roster.items():
        name = row["name"]
        names[cid] = name
        by_name[normalize(name)] = cid

    # Add display names authored in newroster.py (MR. KARATE, OMEGA RUGAL,
    # CHUN-LI, ...).  Canonical build names always win; variants that share a
    # display name (Kyo/Ash/Kyo Nests) are not allowed to shadow "kyo".
    try:
        from newroster import NEW_CHARS
        display_ids: dict[str, set[int]] = {}
        for cid, row in roster.items():
            cfg = NEW_CHARS.get(row["name"])
            if not isinstance(cfg, dict):
                continue
            display = cfg.get("display")
            if display:
                display_ids.setdefault(normalize(display), set()).add(cid)
        for display, ids in display_ids.items():
            if display not in by_name and len(ids) == 1:
                by_name[display] = next(iter(ids))
    except Exception:
        pass

    for alias, target in ALIASES.items():
        if target in by_name:
            by_name.setdefault(alias, by_name[target])
    return roster, by_name, names


def resolve(name: str, by_name: dict[str, int], names: dict[int, str]) -> int:
    key = normalize(name)
    if key in by_name and by_name[key] is not None:
        return by_name[key]
    choices = sorted(k for k, v in by_name.items() if v is not None)
    close = difflib.get_close_matches(key, choices, n=4, cutoff=0.55)
    hint = ""
    if close:
        hint = "\n  Voce quis dizer: " + ", ".join(
            names.get(by_name[c], c) for c in close)
    raise SystemExit(f"personagem desconhecido: {name!r}{hint}")


def find_mesen(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists():
            return path
        raise SystemExit(f"Mesen nao encontrado em {path}")
    found = shutil.which("mesen") or shutil.which("Mesen")
    if found:
        return Path(found)
    fallback = Path.home() / ".local/bin/mesen"
    if fallback.exists():
        return fallback
    raise SystemExit("Mesen nao encontrado; use --mesen /caminho/do/mesen")


def prepare_temp_rom(rom: Path, msu: Path, temp_dir: Path) -> Path:
    temp_dir.mkdir(parents=True, exist_ok=True)
    target = temp_dir / "kof98-snes.sfc"
    shutil.copyfile(rom, target)
    msu_target = temp_dir / "kof98-snes.msu"
    if msu_target.is_symlink() or msu_target.exists():
        msu_target.unlink()
    if msu.exists():
        os.symlink(msu.resolve(), msu_target)
    return target


def parse_result(log: Path) -> dict[str, str] | None:
    if not log.exists():
        return None
    for line in log.read_text(errors="replace").splitlines():
        if not line.startswith("RESULT "):
            continue
        fields: dict[str, str] = {}
        for part in line[len("RESULT "):].split():
            if "=" in part:
                key, value = part.split("=", 1)
                fields[key] = value
        return fields
    return None


def parse_command(line: str) -> tuple[str, str] | None:
    text = line.strip()
    if not text:
        return None
    if text.lower().startswith("luta "):
        text = text[5:].strip()
    match = re.split(r"\s+(?:vs\.?|x|contra)\s+", text, maxsplit=1,
                     flags=re.IGNORECASE)
    if len(match) != 2:
        return None
    left, right = (part.strip() for part in match)
    if not left or not right:
        return None
    return left, right


def run_fight(p1_name: str, p2_name: str, p1: int, p2: int,
              args: argparse.Namespace, mesen: Path) -> bool:
    slug = f"{normalize(p1_name)}_vs_{normalize(p2_name)}"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / "work" / "lutas"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / f"{slug}_{stamp}.log"
    shot_path = out_dir / f"{slug}_{stamp}.png"

    temp_dir = Path("/tmp/opencode/luta_mesen")
    rom_copy = prepare_temp_rom(args.rom, args.msu, temp_dir)

    env = os.environ.copy()
    env.update({
        "KOF_LUTA_LOG": str(log_path),
        "KOF_LUTA_SHOT": "" if args.no_shot else str(shot_path),
        "KOF_LUTA_P1": str(p1),
        "KOF_LUTA_P2": str(p2),
        "KOF_LUTA_LEVEL": str(args.level),
        "KOF_LUTA_MAXFRAMES": str(int(args.seconds * 60.0988)),
    })
    timeout = max(30, int(args.seconds) + 30)
    cmd = [
        str(mesen), "--testRunner", str(ROOT / "tools" / "luta_cpu_vs_cpu.lua"),
        str(rom_copy), f"--timeout={timeout}",
    ]
    stdout_log = log_path.with_suffix(".mesen.log")
    print(f"  {p1_name} vs {p2_name}: rodando no Mesen ({args.seconds:.0f}s max)...",
          flush=True)
    result = None
    for attempt in (1, 2):
        with stdout_log.open("w") as handle:
            try:
                subprocess.run(cmd, env=env, stdout=handle,
                               stderr=subprocess.STDOUT, timeout=timeout + 20,
                               check=False)
            except subprocess.TimeoutExpired:
                print("  aviso: Mesen excedeu o tempo limite", flush=True)
        result = parse_result(log_path)
        if result:
            break
        if attempt == 1:
            print("  aviso: Mesen nao gravou resultado; tentando novamente...",
                  flush=True)
            time.sleep(1)

    if not result:
        print(f"  FALHOU: sem resultado. Veja {stdout_log}", flush=True)
        return False

    winner = result.get("winner", "draw")
    if winner == "p1":
        winner_name = p1_name
    elif winner == "p2":
        winner_name = p2_name
    elif winner == "timeout":
        winner_name = "tempo esgotado"
    else:
        winner_name = "empate"

    wins = f"{result.get('wins1', '0')}-{result.get('wins2', '0')}"
    frames = result.get("frames", "?")
    hp = f"{result.get('hp1', '?')}/{result.get('hp2', '?')}"
    print(f"  Vencedor: {winner_name}  ({wins} rounds, {frames} frames, HP {hp})",
          flush=True)
    shot = result.get("shot", "")
    if shot:
        print(f"  Screenshot: {shot}", flush=True)
    print(f"  Log: {log_path}", flush=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lutas CPU vs CPU na ROM atual, com Mesen.")
    parser.add_argument("command", nargs="?",
                        help='comando unico, ex.: "luta Terry vs Kyo"')
    parser.add_argument("--rom", type=Path, default=ROOT / "kof98-snes.sfc")
    parser.add_argument("--msu", type=Path, default=ROOT / "kof98-snes.msu")
    parser.add_argument("--mesen", default=None)
    parser.add_argument("--level", type=int, default=8,
                        help="nivel da IA (1..8; Mr. Karate usa 9 interno)")
    parser.add_argument("--seconds", type=float, default=120.0,
                        help="duracao maxima de cada luta")
    parser.add_argument("--no-shot", action="store_true",
                        help="nao salvar screenshot")
    parser.add_argument("--list", action="store_true",
                        help="listar personagens disponiveis")
    args = parser.parse_args()

    if not args.rom.exists():
        raise SystemExit(f"ROM nao encontrada: {args.rom}")
    if not args.msu.exists():
        print(f"aviso: {args.msu} nao existe; personagens MSU podem falhar",
              flush=True)
    mesen = find_mesen(args.mesen)
    _, by_name, names = roster_maps()

    if args.list:
        print("Personagens disponiveis:")
        for cid in sorted(names):
            print(f"  {cid:>3}  {names[cid]}")
        return 0

    def one(line: str) -> bool:
        parsed = parse_command(line)
        if not parsed:
            print("  Formato: luta X vs Y   (ex.: luta Terry vs Kyo)")
            return False
        p1_name, p2_name = parsed
        p1 = resolve(p1_name, by_name, names)
        p2 = resolve(p2_name, by_name, names)
        return run_fight(p1_name, p2_name, p1, p2, args, mesen)

    if args.command:
        return 0 if one(args.command) else 1

    print("KOF98 SNES - lutas CPU vs CPU pelo Mesen")
    print('Digite "luta X vs Y" (ex.: luta Terry vs Kyo), "lista" ou "sair".')
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        low = line.lower()
        if low in ("sair", "exit", "quit"):
            break
        if low in ("ajuda", "help", "?"):
            print('  luta X vs Y   agenda uma luta')
            print("  lista         mostra os personagens")
            print("  sair          encerra")
            continue
        if low in ("lista", "list", "personagens"):
            for cid in sorted(names):
                print(f"  {cid:>3}  {names[cid]}")
            continue
        one(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
