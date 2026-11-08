#!/usr/bin/env python3
"""Build the TINY profile data for kof98-snes-tiny.sfc.

The traditional build (kof98-snes.sfc / kof98-snes.msu) stays untouched.  The
TINY ROM reuses the traditional tables/MSU slice map and adds a 0.56 ROM
copy for the nine-character roster (all nine at 0.56):

    Terry, Andy, Joe, Kyo, Benimaru, Daimon, Iori, Shingo, Omega Rugal

Without MSU those nine use the ROM copies.  With MSU the eight non-Terry
characters switch to their MSU descriptors at boot; Terry always uses his
0.56 ROM copy.  Mature and Vice are MSU-only additions.  The MSU-1
layout CRC is copied from the traditional kof98-snes.msu, so renaming that
file to kof98-snes-tiny.msu is enough.

The script writes build/tiny/gen_fight/{newchars_tabs.inc,tiny_variants.inc}
and an empty gen_fight/terry_chr.inc (the traditional Terry CHR is replaced
by the eleven ROM copies).
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAD = ROOT / "build" / "gen_fight"
OUT = ROOT / "build" / "tiny" / "gen_fight"
VAR = ROOT / "build" / "tiny" / "variants" / "gen_fight"
ROM = ROOT / "kof98-snes.sfc"

CHOSEN = ["terry", "andy", "joe", "kyo", "benimaru", "daimon",
          "iori", "shingo", "omegarugal"]
# The 0.88 traditional layout leaves 143 free 32 KiB halves after the throw
# victim poses; all nine at 0.56 need 138, so the roster keeps the uniform
# 0.56 ceiling.  Override with KOF_TINY_SCALES=name:scale,...
TINY_SCALE_CAPS = {}
# The TINY roster: the nine chosen characters are selectable in both modes.
# Mature and Vice are MSU-only: their cells stay visible and selectable when
# the .msu is present, but they have no ROM copy.
MSU_ONLY_FIXED = ["mature", "vice"]
# New characters whose heavy tables are dropped from the tiny ROM.
STUB_NEW = ["ryo", "robert", "yuri", "athena", "kensou", "chin", "king",
            "mai", "chizuru", "kim", "chang", "choi", "yashiro", "shermie",
            "chris", "yamazaki", "mary", "billy", "lucky", "heavyd",
            "brian", "geese", "krauser", "mrbig", "eiji", "vega", "ryu",
            "ken", "chunli", "sakura", "kyonests", "kyoash"]
# The fixed roster order (CharSelTab ids 0..14) and the generated roster
# after it.  build_fight.py emits the same order in newchars_tabs.inc.
FIXED = ["kyo", "iori", "shingo", "rugal", "saisyu", "heidern", "takuma",
         "clark", "ralf", "leona", "mature", "vice", "benimaru", "daimon",
         "omegarugal"]
KEEP_090_FIXED = set(FIXED)
LABEL = {
    "kyo": "CharKyo", "iori": "CharIori", "shingo": "CharShingo",
    "rugal": "CharRugal", "saisyu": "CharSaisyu", "heidern": "CharHeidern",
    "takuma": "CharTakuma", "clark": "CharClark", "ralf": "CharRalf",
    "leona": "CharLeona", "mature": "CharMature", "vice": "CharVice",
    "benimaru": "CharBenimaru", "daimon": "CharDaimon",
    "omegarugal": "CharOmegaRugal", "terry": "CharTerry",
    "andy": "CharAndy", "joe": "CharJoe",
}
TINY_LABEL = {n: LABEL[n] + "Tiny05" for n in CHOSEN}
CAP = {"omegarugal": "OmegaRugal"}


def cap(name: str) -> str:
    return CAP.get(name, name[:1].upper() + name[1:])


def inc_size(path: Path) -> int:
    """Binary size of a generated .inc (same accounting as build_fight.py)."""
    total = 0
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        m = re.match(r"(?:[A-Za-z_][A-Za-z_0-9]*:\s*)?"
                     r"\.(db|dw|dl|byte|word)\b(.*)", line)
        if m:
            n = len([t for t in m.group(2).split(",") if t.strip()])
            total += n * {"db": 1, "byte": 1, "dw": 2, "word": 2,
                          "dl": 3}[m.group(1)]
    return total


def run_variants(plan: dict[str, float]) -> None:
    """Generate the ROM copies with build_fight.py's one-shot mode."""
    if VAR.exists():
        shutil.rmtree(VAR.parent)
    VAR.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "KOF_OUT_DIR": str(VAR),
        "KOF_MSU_NAME": "kof98-snes",
        "KOF_CHAR_SCALE": f"{plan.get('terry', 0.45):.2f}",
        "KOF_CHAR_SCALES": ",".join(f"{n}:{s:.2f}" for n, s in plan.items()),
        "KOF_SCALE_CAPS": "none",
        "KOF_ONLY_CHARS": ",".join(CHOSEN),
        "KOF_SKIP_MANIFEST": "1",
        "KOF_OAM_TRUNCATE": "1",
        "KOF_SPRITE_BBOX_TRUNCATE": "1",
    })
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_fight.py")],
                   cwd=ROOT, env=env, check=True,
                   stdout=subprocess.DEVNULL)


def postprocess(chosen: list[str]) -> None:
    """Rewrite variant labels and collect the generated binary files."""
    OUT.mkdir(parents=True, exist_ok=True)
    for name in chosen:
        for suffix in ("_spr.inc", "_meta.inc"):
            src = VAR / f"{name}{suffix}"
            txt = src.read_text()
            txt = re.sub(rf"\b{re.escape(name)}(?=[A-Z])",
                         f"{name}05", txt)
            txt = re.sub(rf"\b{name.upper()}_NSPR\b",
                         f"{name.upper()}05_NSPR", txt)
            (OUT / f"{name}05{suffix}").write_text(txt)
        spr = (OUT / f"{name}05_spr.inc").read_text()
        def blk(label, nxt):
            m = re.search(rf"^{label}:.*?(?=^{nxt}:)", spr, re.M | re.S)
            if not m:
                raise ValueError(f"{name}: missing {label} block")
            return m.group(0)
        gfx = ("; generated by tools/build_tiny.py -- 0.50 graphics tables\n"
               + blk(f"{name}05SprOfs", f"{name}05BoxTab")
               + blk(f"{name}05BoxTab", f"{name}05AnimTab")
               + blk(f"{name}05AnimTab", f"{name}05ActiveTab"))
        (OUT / f"{name}05_gfx.inc").write_text(gfx)
        shutil.copyfile(VAR / f"{name}.chr", OUT / f"{name}05.chr")
        for pal in ("_pal.bin", "_pal_dim.bin", "_pal_hi.bin"):
            shutil.copyfile(VAR / f"{name}{pal}", OUT / f"{name}05{pal}")


def free_blocks(rom: bytes) -> list[tuple[int, int]]:
    """Whole free 32 KiB half-banks, plus the traditional Terry CHR run."""
    blocks: list[tuple[int, int]] = []
    for i in range(len(rom) // 0x8000):
        b = i * 0x8000
        if set(rom[b:b + 0x8000]) <= {0x00, 0xFF}:
            blocks.append((b // 0x10000, b % 0x10000))
    # TINY replaces the traditional 0.88 Terry CHR with an empty file.  It
    # occupies the high halves of WLA banks 95..115.
    for bank in range(95, 116):
        blocks.append((bank, 0x8000))
    drop = OUT / "tiny_dropped.json"
    if drop.exists():
        for bank, org in json.loads(drop.read_text()):
            blocks.append((bank, org))
    used = set()
    used_file = OUT / "tiny_used.json"
    if used_file.exists():
        used = {tuple(x) for x in json.loads(used_file.read_text())}
    # Banks 128+ belong to the standalone branch of newchars_banks.inc and
    # do not exist in the 128-bank ExHiROM.  Keep only real ROM banks.
    return sorted({(b, o) for b, o in blocks
                   if (b, o) not in used and 0 <= b < 128})


def pvs_slots() -> list[list[int]]:
    """Recreate build_fight.py's PVS_SLOTS (HI 0.88 profile)."""
    def inc(rel: str) -> int:
        return inc_size(TRAD / rel)

    def end_size(rel: str) -> int:
        return os.path.getsize(ROOT / "src" / "gen_menu" / "end" / rel)

    benimaru_end = inc("benimaru_spr.inc")
    shingo_end = inc("shingo_spr.inc")
    slots = [[47, 0, 65536],
             [61, benimaru_end, 65536 - benimaru_end],
             [62, shingo_end, 65536 - shingo_end]]
    slots += [[b, 0, 32768] for b in range(84, 118) if b != 88]
    slots += [[82, 0x4000, 0x4000], [50, 0, 0x7100],
              [48, 0x6600, 0x10000 - 0x6600]]
    slots += [[b, 0, 0x8000] for b in range(27, 43)]
    slots += [[56, 0, 0x8000],
              [63, inc("daimon_spr.inc"), 65536 - inc("daimon_spr.inc")]]
    slots += [[118, 0x6B86, 0x8000 - 0x6B86],
              [120, 0x0E20, 0x71E0], [122, 0, 0x8000]]
    omega = (inc("omegarugal_meta.inc") + 0x1FF) & ~0xFF
    end01 = ((end_size("end01.chr") + 0xFF) & ~0xFF) + 0x100
    end22 = ((end_size("end22.chr") + 0xFF) & ~0xFF) + 0x100
    slots += [[119, omega, 0x8000 - omega],
              [121, end22, 0x8000 - end22],
              [123, end01, 0x8000 - end01]]
    for bank, asset in ((118, "end04.chr"), (119, "end05.chr"),
                        (120, "end06.chr"), (121, "end07.chr"),
                        (122, "end08.chr"), (123, "end09.chr"),
                        (124, "end10.chr")):
        off = 0x8000 + ((end_size(asset) + 0xFF) & ~0xFF) + 0x100
        if 0x10000 - off > 0:
            slots.append([bank, off, 0x10000 - off])
    e3 = ((end_size("end03.chr") + 0xFF) & ~0xFF) + 0x100
    slots.append([125, e3, 0x8000 - e3])
    mp = sum(end_size(f"end{i:02d}.{ext}") for i in range(11)
             for ext in ("map", "pal"))
    mp_end = 0x8000 + ((mp + 0xFF) & ~0xFF) + 0x100
    slots.append([125, mp_end, 0x10000 - mp_end])
    # Use the original 32 KiB windows and subtract the sections the
    # traditional allocator actually placed.  Do not merge banks 27-42
    # into full 64 KiB windows: several of them still hold Chang/Lucky
    # data that crosses the half-bank boundary.
    return slots


def used_ranges() -> list[tuple[int, int, int]]:
    """Sections emitted by the tiny newchars_banks.inc (PVS branch)."""
    src = OUT / "newchars_banks.inc"
    if not src.exists():
        src = TRAD / "newchars_banks.inc"
    text = src.read_text().splitlines()
    used: list[tuple[int, int, int]] = []
    in_pvs = False
    bank = org = None
    sec_size = 0
    for line in text:
        s = line.strip()
        if s.startswith(".IFDEF PVSNESLIB"):
            in_pvs = True
            continue
        if in_pvs and s.startswith(".ELSE"):
            break
        if not in_pvs:
            continue
        if s.startswith(".BANK "):
            bank = int(s.split()[1])
        elif s.startswith(".ORGA "):
            org = int(s.split()[1].lstrip("$"), 16)
        elif s.startswith(".SECTION "):
            sec_size = 0
        elif s.startswith(".INCLUDE "):
            rel = s.split('"')[1].replace("gen_fight/", "")
            path = TRAD / rel
            if path.suffix == ".inc":
                # A few includes carry .INCBIN payloads (projectiles).
                txt = path.read_text(errors="ignore")
                incbin = sum(int(m.group(1))
                             for m in re.finditer(
                                 r"\.INCBIN\s+\"[^\"]+\".*?READ\s+(\d+)",
                                 txt))
                sec_size += incbin if incbin else inc_size(path)
            else:
                sec_size += path.stat().st_size
        elif s.startswith(".INCBIN "):
            m = re.search(r"READ\s+(\d+)", s)
            if m:
                sec_size += int(m.group(1))
        elif s == ".ENDS":
            if bank is not None and org is not None and sec_size:
                used.append((bank, org, sec_size))
            bank = org = None
            sec_size = 0
    return used


def _subtract(slots: list[list[int]],
              used: list[tuple[int, int, int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for bank, off, size in slots:
        pieces = [[bank, off, off + size]]
        for ub, uo, us in used:
            if ub != bank:
                continue
            ua, ue = uo, uo + us
            nxt = []
            for b, a, z in pieces:
                if ue <= a or ua >= z:
                    nxt.append([b, a, z])
                else:
                    if a < ua:
                        nxt.append([b, a, ua])
                    if ue < z:
                        nxt.append([b, ue, z])
            pieces = nxt
        for b, a, z in pieces:
            if z > a:
                out.append([b, a, z - a])
    return out


def _take_span(slots: list[list[int]], size: int) -> tuple[int, int] | None:
    for s in slots:
        bank, off, avail = s
        if bank in (126, 127):
            continue
        bank_end = 0x10000
        while off + size <= min(bank_end, off + avail):
            s[1] = off + size
            s[2] = avail - size
            return bank, off
    return None


def _take_block(blocks: list[tuple[int, int]],
                used: list[tuple[int, int, int]]) -> tuple[int, int] | None:
    for i, (bank, half) in enumerate(blocks):
        if bank in (126, 127):
            continue
        blocks.pop(i)
        return bank, half
    return None


def sym_used() -> list[tuple[int, int]]:
    """Used [start,end) file ranges from the traditional .symfull sections."""
    sym = ROOT / "kof98-snes.symfull"
    if not sym.exists():
        raise SystemExit("missing kof98-snes.symfull (run the traditional build)")
    starts: dict[str, int] = {}
    ends: dict[str, int] = {}
    for line in sym.read_text(errors="ignore").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        addr, name = parts
        try:
            a = int(addr, 16)
        except ValueError:
            continue
        if name.startswith("SECTIONSTART_"):
            starts[name[13:]] = a
        elif name.startswith("SECTIONEND_"):
            ends[name[11:]] = a
    out: list[tuple[int, int]] = [(0, 0x10000)]     # ROM header/vectors
    for n, a in starts.items():
        b = ends.get(n)
        if b is None or b <= a:
            continue
        if n.startswith(".") or n.startswith("TerryChr") \
                or n in ("TerryData", "TerryMeta"):
            continue
        bank = (a >> 16) & 0xFF
        off = a & 0xFFFF
        if bank >= 0xC0:
            wla = bank - 0xC0
        elif 0x40 <= bank <= 0x7D:
            wla = bank
        else:
            continue
        start = wla * 0x10000 + off
        out.append((start, start + (b - a)))
    out.sort()
    merged: list[tuple[int, int]] = []
    for a, b in out:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def sym_free_ranges() -> list[list[int]]:
    used = sym_used()
    free: list[list[int]] = []
    pos = 0
    for a, b in used:
        if a > pos:
            free.append([pos, a])
        pos = max(pos, b)
    if pos < 0x800000:
        free.append([pos, 0x800000])
    return [r for r in free if r[1] > r[0]]


def _remove(ranges: list[list[int]], lo: int, hi: int) -> None:
    out: list[list[int]] = []
    for a, b in ranges:
        if hi <= a or lo >= b:
            out.append([a, b])
            continue
        if a < lo:
            out.append([a, lo])
        if hi < b:
            out.append([hi, b])
    ranges[:] = out


def take_block(ranges: list[list[int]]) -> tuple[int, int] | None:
    for a, b in ranges:
        pos = (a + 0x7FFF) // 0x8000 * 0x8000
        while pos + 0x8000 <= b:
            if pos % 0x10000 in (0x0000, 0x8000):
                _remove(ranges, pos, pos + 0x8000)
                return pos // 0x10000, pos % 0x10000
            pos += 0x8000
    return None


def take_span(ranges: list[list[int]], size: int) -> tuple[int, int] | None:
    for a, b in ranges:
        pos = a
        while pos + size <= b:
            bank_end = (pos // 0x10000 + 1) * 0x10000
            if pos + size <= bank_end:
                _remove(ranges, pos, pos + size)
                return pos // 0x10000, pos % 0x10000
            pos = bank_end
    return None


def bank_lines_bo(bank: int, org: int) -> str:
    if bank in (126, 127) or bank >= 128:
        raise ValueError(f"block maps outside the 128-bank ROM: {bank}")
    base = "$C0" if bank < 64 else "$00"
    return f".BASE {base}\n.BANK {bank} SLOT 0\n.ORGA ${org:04X}\n"


def slice_counts(chosen: list[str]) -> dict[str, int]:
    return {n: math.ceil((OUT / f"{n}05.chr").stat().st_size / 32768)
            for n in chosen}


def data_sizes(chosen: list[str], slices: dict[str, int]) -> dict[str, int]:
    out = {}
    for n in chosen:
        out[n] = (inc_size(OUT / f"{n}05_spr.inc")
                  + 3 * 32 + 4 * slices[n])
    return out


def descriptor_block(name: str) -> str:
    """Extract the traditional descriptor text for one character."""
    if name in ("terry", "andy", "joe"):
        text = (TRAD / "newchars_desc.inc").read_text()
        label = LABEL[name]
        m = re.search(rf"^{re.escape(label)}:\n(.*?)(?=^Char\w+:\n|^;|^\.INCLUDE|^\.SECTION|^\.BASE|^\.BANK|^\.ORGA|^\.ENDS|\Z)",
                      text, re.M | re.S)
        if not m:
            raise ValueError(f"descriptor {label} not found")
        return m.group(1)
    text = (ROOT / "src" / "engine" / "fight.asm").read_text()
    label = LABEL[name]
    m = re.search(rf"^{re.escape(label)}:\n(.*?)(?=^Char\w+:\n|^;|^\.INCLUDE|^\.SECTION|^\.BASE|^\.BANK|^\.ORGA|^\.ENDS|\Z)",
                  text, re.M | re.S)
    if not m:
        raise ValueError(f"descriptor {label} not found")
    return m.group(1)


def tiny_descriptor(name: str) -> str:
    """Full 0.50 descriptor; all tables are in the 0.50 data bank."""
    lines = descriptor_block(name).splitlines()
    attr = next(i for i, line in enumerate(lines)
                if re.match(r"^\s*\.db\s+\$?[0-9A-Fa-f]+,\s*0\b", line))
    pal = next(i for i, line in enumerate(lines)
               if re.search(r"\b\w*Pal\b", line))
    out = []
    for line in lines[:attr]:
        line = re.sub(rf"\b{re.escape(name)}(?=[A-Z])", f"{name}05", line)
        line = re.sub(rf"\b{re.escape(cap(name))}(?=Pal)",
                      f"{name}05", line)
        out.append(line)
    out.append(lines[attr])
    out += [f"    .dw {name}05ChrTab", "    .db 0, 2"]
    for line in lines[pal:]:
        if re.search(r"ProjFx(Tab|Chr)\b", line):
            out.append("    .dw 0, 0")
            continue
        if re.search(r"(?:Name|QuoteTab|CmdList|CancelRow|MaxMask)\b", line):
            out.append(line)
            continue
        line = re.sub(rf"\b{re.escape(name)}(?=[A-Z])", f"{name}05", line)
        line = re.sub(rf"\b{re.escape(cap(name))}(?=Pal)",
                      f"{name}05", line)
        out.append(line)
    out = [l for l in out
           if not re.match(r"^\s*\.(IFDEF|IFNDEF|ELSE|ENDIF)\b", l)]
    return "\n".join(out) + "\n"

def parse_layout() -> dict[str, dict[str, tuple[int, int, int]]]:
    """Bank/offset/size of the traditional Data/Meta sections for the 11.

    The PVS branch is the one the TINY ROM assembles.  fight.asm selects the
    bank with .IFDEF PVSNESLIB/.ELSE *before* each .SECTION, so keep the
    first (PVS) bank and ignore the .ELSE alternative.
    """
    names = {}
    for n in CHOSEN:
        names[f"{cap(n)}Data"] = (n, "data")
        names[f"{cap(n)}Meta"] = (n, "meta")
    names["OmegaRugalTables"] = ("omegarugal", "data")
    names["OmegaRugalMeta"] = ("omegarugal", "meta")
    names["OmegarugalMeta"] = ("omegarugal", "meta")
    layout: dict[str, dict[str, tuple[int, int, int]]] = {}
    for path in (TRAD / "newchars_banks.inc", ROOT / "src" / "engine" / "fight.asm"):
        pvs = False
        pvs_bank = pvs_org = None
        sec = None
        size = 0
        for line in path.read_text(errors="ignore").splitlines():
            t = line.strip()
            if t.startswith(".IFDEF PVSNESLIB"):
                pvs = True
                continue
            if t.startswith(".ELSE"):
                pvs = False
                continue
            if t.startswith(".ENDIF"):
                pvs = True
                continue
            if t.startswith(".BANK ") and pvs:
                pvs_bank = int(t.split()[1])
            elif t.startswith(".ORGA ") and pvs:
                pvs_org = int(t.split()[1].lstrip("$"), 16)
            elif t.startswith(".SECTION "):
                sec = t.split('"')[1] if '"' in t else None
                size = 0
            elif t.startswith(".INCLUDE ") and sec:
                rel = t.split('"')[1]
                if not rel.startswith("gen_fight/"):
                    continue
                rel = rel[len("gen_fight/"):]
                p2 = TRAD / rel
                size += inc_size(p2) if p2.suffix == ".inc" else p2.stat().st_size
            elif t == ".ENDS" and sec:
                info = names.get(sec)
                if (info and pvs_bank is not None and pvs_org is not None
                        and (path.name != "newchars_banks.inc" or pvs)):
                    n, kind = info
                    layout.setdefault(n, {})[kind] = (pvs_bank, pvs_org, size)
                sec = None
                pvs_bank = pvs_org = None
    missing = [n for n in CHOSEN
               if "data" not in layout.get(n, {}) or "meta" not in layout.get(n, {})]
    if missing:
        raise ValueError(f"missing traditional layout for {missing}")
    return layout

def parse_tabs() -> tuple[list[str], list[str], str]:
    text = (TRAD / "newchars_tabs.inc").read_text()
    m = re.search(r"^CharSelTab:\s*(.*?)^BankSelTab:", text, re.M | re.S)
    if not m:
        raise ValueError("CharSelTab block not found")
    labels = re.findall(r"\bChar[A-Za-z0-9_]+\b", m.group(1))
    m = re.search(r"^BankSelTab:\s*(.*?)^AiSelTab:", text, re.M | re.S)
    if not m:
        raise ValueError("BankSelTab block not found")
    banks = re.findall(r":([A-Za-z_][A-Za-z0-9_]*)", m.group(1))
    return labels, banks, text


def fixed_halves() -> set[tuple[int, int]]:
    """32 KiB halves occupied by fixed engine sections (PVS branch)."""
    out: set[tuple[int, int]] = set()
    paths = [ROOT / "src" / "engine" / "fight.asm",
             ROOT / "src" / "engine" / "menus.asm"]
    proj = OUT / "projectiles_gfx.inc"
    if proj.exists():
        paths.append(proj)
    for path in paths:
        text = path.read_text(errors="ignore")
        # menus.asm has no PVSNESLIB conditional: all of its sections are in
        # the shipping profile.  fight.asm instead starts with .IFNDEF and
        # only later opens the .IFDEF PVSNESLIB branch.
        pvs = ".IFDEF PVSNESLIB" not in text
        bank = org = None
        sec = False
        for line in text.splitlines():
            t = line.strip()
            if t.startswith(".IFDEF PVSNESLIB"):
                pvs = True
                continue
            if t.startswith(".ELSE"):
                pvs = False
                continue
            if t.startswith(".ENDIF"):
                pvs = True
                continue
            if t.startswith(".BANK ") and pvs:
                bank = int(t.split()[1])
            elif t.startswith(".ORGA ") and pvs:
                org = int(t.split()[1].lstrip("$"), 16)
            elif t.startswith(".SECTION "):
                sec = True
            elif t == ".ENDS" and sec:
                if bank is not None and org is not None:
                    out.add((bank, org - (org % 0x8000)))
                sec = False
                bank = org = None
    return out


def half_span(bank: int, org: int, size: int) -> list[tuple[int, int]]:
    """Every 32 KiB half touched by a section that starts at org."""
    if bank is None or org is None:
        return []
    last = org + max(size, 1) - 1
    first_h = org - (org % 0x8000)
    last_h = last - (last % 0x8000)
    return [(bank, h) for h in range(first_h, min(last_h, 0x10000) + 1, 0x8000)]


def write_tiny_banks() -> None:
    """Keep the chosen/fixed sections, drop the unused new-character tables.

    The 32 characters outside the TINY roster still have descriptor labels
    (aliased to CharTinyStub) so the shared tables keep linking, but their
    sprite/metasprite/cmdlist blobs are not needed.
    """
    text = (TRAD / "newchars_banks.inc").read_text()
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    dropped: list[tuple[int, int]] = []
    kept_halves: set[tuple[int, int]] = set()
    bank = org = None
    sec = None
    block: list[str] = []
    keep = True
    sec_size = 0
    for line in lines:
        t = line.strip()
        if sec is None:
            if t.startswith(".BANK "):
                bank = int(t.split()[1])
            elif t.startswith(".ORGA "):
                org = int(t.split()[1].lstrip("$"), 16)
            elif t.startswith(".SECTION "):
                sec = t.split('"')[1] if '"' in t else None
                block = [line]
                keep = True
                sec_size = 0
                continue
            out.append(line)
            continue
        block.append(line)
        if t.startswith(".INCLUDE "):
            rel = t.split('"')[1]
            if rel.startswith("gen_fight/"):
                base = rel[len("gen_fight/"):]
                for suf in ("_spr.inc", "_meta.inc", "_cmdlist.inc"):
                    if base.endswith(suf):
                        char = base[:-len(suf)]
                        if char == "terry" or (
                                char not in CHOSEN
                                and char not in KEEP_090_FIXED):
                            keep = False
                p2 = TRAD / base
                if p2.exists():
                    sec_size += (inc_size(p2) if p2.suffix == ".inc"
                                 else p2.stat().st_size)
        elif t == ".ENDS":
            if keep:
                out.extend(block)
                kept_halves.update(half_span(bank, org, sec_size))
            else:
                dropped.extend(half_span(bank, org, sec_size))
            sec = None
            block = []
    (OUT / "newchars_banks.inc").write_text("".join(out))
    used = fixed_halves() | kept_halves
    dropped = [b for b in set(dropped) if b not in used]
    (OUT / "tiny_dropped.json").write_text(json.dumps(sorted(dropped)) + "\n")
    (OUT / "tiny_used.json").write_text(json.dumps(sorted(used)) + "\n")


def write_tiny_desc() -> None:
    """Only Andy/Joe keep their 0.88 descriptors (used with the .msu file).

    Every other mass-import character is aliased to CharTinyStub, so its
    table labels can disappear without breaking the shared voice/close-normal
    tables.
    """
    text = (TRAD / "newchars_desc.inc").read_text()
    out = ["; generated by tools/build_tiny.py -- stub descriptors\n",
           ".IFNDEF BASE4\n"]
    for n in ("andy", "joe"):
        label = LABEL[n]
        m = re.search(rf"^{re.escape(label)}:\n(.*?)(?=^Char\w+:\n|^\w+Pal:)",
                      text, re.M | re.S)
        if not m:
            raise ValueError(f"descriptor {label} not found")
        out.append(f"{label}:\n" + m.group(1))
        for pal in ("Pal", "PalDim", "PalHi"):
            p = re.search(rf"^{cap(n)}{pal}:.*$", text, re.M)
            if not p:
                raise ValueError(f"{cap(n)}{pal} not found")
            out.append(p.group(0) + "\n")
    out.append("CharTinyStub:\n    .db " + ",".join(["0"]*96) + "\n")
    out.append(".ENDIF\n")
    (OUT / "newchars_desc.inc").write_text("".join(out))



def write_tiny_seldata() -> None:
    """Keep the traditional 50-cell select map.  TinyAvailTab (checked by
    SelLockN/SLC_try) denies the cells outside the TINY roster."""
    src = ROOT / "src" / "gen_menu" / "seldata.inc"
    dst = OUT.parent / "gen_menu"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst / "seldata.inc")

def write_tiny_proj() -> None:
    shutil.copyfile(TRAD / "projectiles_gfx.inc", OUT / "projectiles_gfx.inc")



def write_tiny_projmeta() -> None:
    shutil.copyfile(TRAD / "projectiles_meta.inc", OUT / "projectiles_meta.inc")
    shutil.copyfile(TRAD / "projectiles.inc", OUT / "projectiles.inc")



def write_tiny_reflect() -> None:
    shutil.copyfile(TRAD / "reflect_tab.inc", OUT / "reflect_tab.inc")



def write_tiny_voices() -> None:
    """Add ROM voice entries for the 0.50 descriptors used without the .msu.

    Terry always runs his 0.50 copy, so his entry is repointed at that
    descriptor and uses the ROM voice table (offset 0) in both modes.  The
    other eight keep their 0.88 entries for the .msu path and gain a ROM
    fallback entry for the 0.50 descriptors.
    """
    text = (TRAD / "voices.inc").read_text()
    old = ("    .dw CharTerry, VoiceTab_terry\n"
           "    .db :VoiceTab_terry\n"
           "    .dw VoiceOfs_terry\n"
           "    .db :VoiceOfs_terry\n")
    new = ("    .dw CharTerryTiny05, VoiceTab_terry\n"
           "    .db :VoiceTab_terry\n"
           "    .dw 0\n"
           "    .db 0\n")
    if old not in text:
        raise ValueError("Terry voice entry not found")
    text = text.replace(old, new, 1)
    extra = []
    for n in CHOSEN:
        if n == "terry":
            continue
        extra.append(f"    .dw {LABEL[n]}Tiny05, VoiceTab_{n}\n"
                     f"    .db :VoiceTab_{n}\n"
                     "    .dw 0\n"
                     "    .db 0\n")
    term = "    .dw 0\n.ENDS"
    if term not in text:
        raise ValueError("VoicePtrTab terminator not found")
    text = text.replace(term, "".join(extra) + term, 1)
    (OUT / "voices.inc").write_text(text)


def write_tabs() -> None:
    labels, banks, text = parse_tabs()
    id_of = {lab: i for i, lab in enumerate(labels)}
    label_of = {v: k for k, v in LABEL.items()}
    chosen_ids = {id_of[LABEL[n]] for n in CHOSEN}
    msu_ids = {id_of[LABEL[n]] for n in MSU_ONLY_FIXED}
    rugal_id = id_of[LABEL["rugal"]]
    omega_id = id_of[LABEL["omegarugal"]]

    new_labels = list(labels)
    new_banks = list(banks)
    stub_label = {LABEL.get(n, "Char" + cap(n)) for n in STUB_NEW}
    for i, lab in enumerate(labels):
        name = label_of.get(lab)
        if name in CHOSEN:
            new_labels[i] = TINY_LABEL[name]
            new_banks[i] = f"{name}05SprOfs"
        elif lab in stub_label:
            # The stub descriptor never resolves a table bank; point it at a
            # live bank so BankSelTab still assembles after the blobs are cut.
            new_banks[i] = "terry05SprOfs"

    def sel_line(labs: list[str]) -> str:
        out = ["CharSelTabRom:\n"]
        for i in range(0, len(labs), 4):
            out.append("    .dw " + ", ".join(labs[i:i + 4]) + "\n")
        return "".join(out)

    def bank_line(bks: list[str]) -> str:
        out = ["BankSelTabRom:\n"]
        for i in range(0, len(bks), 4):
            out.append("    .db " + ", ".join(":" + b for b in bks[i:i + 4])
                       + "\n")
        return "".join(out)

    text = re.sub(r"^CharSelTab:.*?^BankSelTab:", sel_line(new_labels)
                  + "BankSelTab:", text, flags=re.M | re.S)
    text = re.sub(r"^BankSelTab:.*?^AiSelTab:", bank_line(new_banks)
                  + "AiSelTab:", text, flags=re.M | re.S)

    # RomFlags: the nine 0.50 copies plus Rugal's cell (hidden Omega input).
    m = re.search(r"^RomFlags:\s*\.db (.*)$", text, re.M)
    vals = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
    for i in range(len(vals)):
        vals[i] = 1 if (i in chosen_ids or i == rugal_id) else 0
    text = re.sub(r"^RomFlags:\s*\.db .*$",
                  "RomFlags:   .db " + ",".join(str(v) for v in vals),
                  text, flags=re.M)

    # HiddenTab: Omega, Rugal's cell (hidden input only) and every
    # non-selectable character.
    stub_ids = set(range(len(labels))) - chosen_ids - msu_ids - {rugal_id}
    m = re.search(r"^HiddenTab:\s*\.db (.*)$", text, re.M)
    hid = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
    for i in range(len(hid)):
        hid[i] = 1 if (i == omega_id or i == rugal_id or i in stub_ids) else 0
    text = re.sub(r"^HiddenTab:\s*\.db .*$",
                  "HiddenTab:  .db " + ",".join(str(v) for v in hid),
                  text, flags=re.M)

    # CPU pool: the nine chosen (minus hidden Omega) + Mature/Vice.
    pool = sorted((chosen_ids | msu_ids) - {omega_id})
    text = re.sub(r"^NPOOL = .*$", f"NPOOL = {len(pool)}", text, flags=re.M)
    text = re.sub(r"^CpuPool:.*\Z", "", text, flags=re.M | re.S)
    cpu = ["CpuPool:    .db " + ",".join(str(i) for i in pool[:20]) + "\n"]
    if len(pool) > 20:
        cpu.append("            .db " + ",".join(str(i) for i in pool[20:])
                   + "\n")
    text = text.rstrip() + "\n" + "".join(cpu)

    # Availability table checked by SelLockN/SLC_try in the tiny build.
    avail = [1 if (i in chosen_ids or i in msu_ids or i == omega_id) else 0
             for i in range(len(labels))]
    text += "\nTinyAvailTab: .db " + ",".join(str(v) for v in avail) + "\n"

    dual = ["\n; {id, 0.88 descriptor, 0.88 table bank}; $FF terminates.\n",
            "TinyDualTab:\n"]
    for n in CHOSEN:
        if n == "terry":
            continue
        dual.append(f"    .db {id_of[LABEL[n]]}\n"
                    f"    .dw {LABEL[n]}\n"
                    f"    .db :{n}SprOfs\n")
    dual.append("    .db $FF\n")

    desc = ["\n; ---- TINY 0.50 ROM descriptors ------------------------"
            "------------\n"]
    for n in CHOSEN:
        desc.append(f"{TINY_LABEL[n]}:\n" + tiny_descriptor(n) + "\n")
    (OUT / "newchars_tabs.inc").write_text("".join(dual) + text +
                                           "".join(desc))

def write_variants(chosen: list[str], slices: dict[str, int],
                   spr_blocks: dict[str, tuple[int, int]],
                   meta_blocks: dict[str, tuple[int, int]],
                   chr_blocks: dict[str, list[tuple[int, int]]]) -> None:
    """Emit the full 0.50 tables/meta and the 32 KiB CHR slices."""
    out = ["; generated by tools/build_tiny.py -- do not edit\n"]
    for n in chosen:
        db, do = spr_blocks[n]
        mb, mo = meta_blocks[n]
        out.append(f"\n; ---- {n} 0.50 ROM copy ----\n")
        out.append(bank_lines_bo(db, do))
        out.append(f'.SECTION "{cap(n)}TinyData" FORCE\n')
        out.append(f'.INCLUDE "gen_fight/{n}05_spr.inc"\n')
        out.append(f"{n}05ChrTab:\n")
        for i in range(slices[n]):
            lab = f"{n}05Chr{chr(ord('A') + i)}"
            out.append(f"    .dw {lab}\n    .db :{lab}, 0\n")
        for pal in ("", "Dim", "Hi"):
            fn = f"{n}05_pal{'' if not pal else '_' + pal.lower()}.bin"
            out.append(f'{n}05Pal{pal}: .INCBIN "gen_fight/{fn}"\n')
        out.append(".ENDS\n")
        out.append(bank_lines_bo(mb, mo))
        out.append(f'.SECTION "{cap(n)}TinyMeta" FORCE\n')
        out.append(f'.INCLUDE "gen_fight/{n}05_meta.inc"\n')
        out.append(".ENDS\n")
        for i, (bank, org) in enumerate(chr_blocks[n]):
            lab = f"{n}05Chr{chr(ord('A') + i)}"
            out.append(bank_lines_bo(bank, org))
            out.append(f'.SECTION "{cap(n)}TinyChr{chr(ord("A") + i)}" '
                       f'FORCE\n{lab}:\n')
            out.append(f'    .INCBIN "gen_fight/{n}05.chr" SKIP {i * 32768}'
                       + (" READ 32768" if i < slices[n] - 1 else "") + "\n")
            out.append(".ENDS\n")
    (OUT / "tiny_variants.inc").write_text("".join(out))

def allocate(chosen: list[str]) -> dict:
    ranges = sym_free_ranges()
    slices = slice_counts(chosen)
    sizes = data_sizes(chosen, slices)
    chr_blocks: dict[str, list[tuple[int, int]]] = {}
    for n in chosen:
        got = []
        for _ in range(slices[n]):
            b = take_block(ranges)
            if b is None:
                raise ValueError(f"not enough 32 KiB ROM blocks for {n}")
            got.append(b)
        chr_blocks[n] = got
    spr_at: dict[str, tuple[int, int]] = {}
    meta_at: dict[str, tuple[int, int]] = {}
    for n in chosen:
        got = take_span(ranges, sizes[n])
        if got is None:
            raise ValueError(f"no ROM span for {n} tables ({sizes[n]} B)")
        spr_at[n] = got
    for n in chosen:
        size = inc_size(OUT / f"{n}05_meta.inc")
        got = take_span(ranges, size)
        if got is None:
            raise ValueError(f"no ROM span for {n} meta ({size} B)")
        meta_at[n] = got
    return {"slices": slices, "chr_blocks": chr_blocks,
            "spr_at": spr_at, "meta_at": meta_at}

def main() -> int:
    if not (TRAD / "newchars_tabs.inc").exists():
        raise SystemExit("run the traditional build first (build/gen_fight)")
    if not (ROOT / "kof98-snes.sfc").exists():
        raise SystemExit("run the traditional build first (kof98-snes.sfc)")
    if not (ROOT / "kof98-snes.msu").exists():
        raise SystemExit("run the traditional build first (kof98-snes.msu)")

    base = float(os.environ.get("KOF_TINY_SCALE", "0.56"))
    plan = {n: base for n in CHOSEN}
    if base >= 0.56:
        for n, scale_cap in TINY_SCALE_CAPS.items():
            plan[n] = min(plan[n], scale_cap)
    for item in os.environ.get("KOF_TINY_SCALES", "").split(","):
        item = item.strip()
        if not item:
            continue
        n, s = item.split(":", 1)
        plan[n.strip()] = float(s)
    run_variants(plan)
    postprocess(CHOSEN)
    write_tiny_proj()
    write_tiny_projmeta()
    write_tiny_reflect()
    write_tiny_voices()
    write_tiny_banks()
    write_tiny_desc()
    write_tiny_seldata()
    write_tabs()
    slices = slice_counts(CHOSEN)
    rom = (ROOT / "kof98-snes.sfc").read_bytes()
    blocks = [(b, o) for b, o in free_blocks(rom)
              if b not in (0, 48, 126, 127)]
    spr_blocks: dict[str, tuple[int, int]] = {}
    meta_blocks: dict[str, tuple[int, int]] = {}
    pos = 0
    for n in CHOSEN:
        gsize = inc_size(OUT / f"{n}05_spr.inc") + 4 * slices[n] + 96
        msize = inc_size(OUT / f"{n}05_meta.inc")
        if gsize > 0x8000 or msize > 0x8000:
            raise SystemExit(f"{n}: 0.50 tables/meta exceed one half-bank")
        if pos + 2 > len(blocks):
            raise SystemExit("not enough halves for 0.50 tables/meta")
        spr_blocks[n] = blocks[pos]
        meta_blocks[n] = blocks[pos + 1]
        pos += 2
    chr_blocks: dict[str, list[tuple[int, int]]] = {}
    for n in CHOSEN:
        need = slices[n]
        if pos + need > len(blocks):
            raise SystemExit(f"not enough 32 KiB blocks for {n}")
        chr_blocks[n] = blocks[pos:pos + need]
        pos += need
    print(f"tiny halves: {pos}/{len(blocks)}")
    write_variants(CHOSEN, slices, spr_blocks, meta_blocks, chr_blocks)
    alias = ["; TINY: unused mass-import descriptors share one stub.\n",
             ".DEFINE CharTerry CharTerryTiny05\n"]
    for n in STUB_NEW:
        alias.append(f".DEFINE {LABEL.get(n, 'Char' + cap(n))} CharTinyStub\n")
    (OUT / "tiny_alias.inc").write_text("".join(alias))
    (OUT / "terry_chr.inc").write_text(
        "; TINY: Terry's 0.88 CHR is replaced by the 0.56 ROM copy\n")
    (OUT / "tiny.stamp").write_text("ok\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
