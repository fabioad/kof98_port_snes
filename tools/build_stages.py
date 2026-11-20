#!/usr/bin/env python3
"""Convert every stage PNG in assets/stages/stages_v2/ into SNES BG1 assets
and emit the per-stage v2 animation pools/descriptors from anim/*.json.

The v2 directory is produced by tools/stage_v2/ from the arcade MUGEN source.
Static art keeps the 512x224 / 3x15-colour format consumed by emit_stage;
each stage also carries its own <=160-tile animation pool, uploaded by
StagePick (StgAnimPoolTab) instead of the old shared stage_anim.chr.

The PNGs are authored to the SNES format (512x224, three palette groups of
15 colours, <=512 unique 8x8 tiles -- see tools/stage_requant.py), so the
conversion is lossless:

  stages/stgNN.chr   4bpp tiles (deduped, <= 512 -> fits BG1CHR $0000-$1FFF)
  stages/stgNN.map   64x32-word tilemap (two 32x32 planes, 512px wide)
  stages/stgNN.pal   3x16 BGR555 entries (BG palettes 2-4 hold the art)

Pixel value in the PNG is `palette group * 15 + colour`; the group picks
BG palette 2+group.  Tiles are folded across H/V flips and across palette
groups (same pattern with other palette bits).

It also generates:

  stages_tab.inc  StageTab descriptor rows (chr/len/map/pal + 3 banks)
  stages.inc      FORCE .BANK/.SECTION blobs holding the stage data
  stage_anim.chr  every clip's pose tiles (shared dynamic tile pool 704+)
  stage_anim.inc  StgAnimTab -> per-stage clip lists + clip descriptors
  stgmods.inc     ModTab: soundbank module index per stage

Stage blobs sit in the banks listed in FREE_BANKS; each bank contributes
the CPU window $8000-$FFFF (32 KiB) so a stage takes one bank.
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sff import snes_pal, tiles4bpp

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# v2: stages rebuilt from the arcade.  The static PNGs keep the exact
# 512x224 / 3x15-colour format consumed by emit_stage; the per-stage clips
# and dynamic tile pool live under anim/.
PNG_DIR = os.path.join(ROOT, "assets/stages/stages_v2")
ANIM_DIR = os.path.join(PNG_DIR, "anim")
OUT = os.path.join(ROOT, "build/gen_fight")

MAX_TILES = 512                     # BG1CHR $0000-$1FFF = 16 KiB
STAGE_BG_PALETTE = 2                # BG3 HUD uses CGRAM colours 12-31
STAGE_NPAL = 3                      # StagePick uploads BG palettes 2-4
STAGE_NCOL = 15                     # 15 art colours + transparent per group
# Per-stage vertical placement inside the 64x32 BG1 map, in 8 px rows.  A
# positive value moves the stage art down (the fighters themselves are not
# moved).  The map is 32 rows tall and the art uses 28, so up to 4 rows fit;
# the duplicated top band sits behind the HUD.
# v2 already aligns the arcade floor to GROUND_Y.  China is the exception:
# the arcade draws BG 25 (the boat's front deck lip) on layerno 1, *in front*
# of the fighters.  The SNES port flattens every layer into BG1, which always
# renders behind the OBJ fighters, so the lip crossed behind their shins and
# they looked like they stood on the outer hull ("outside the boat").
# Two rows (16 px) put the lip just below GROUND_Y: the fighters now stand on
# the deck behind the front edge without reverting the v2 art.
STAGE_YOFS = {
    "KOF98-ChinaStage": 2,          # 16 px: front deck lip under the feet
}
# file banks >= 64 map into the CPU $00-$3D:$8000 windows under ExHiROM;
# 45-49 stay free for the SNESMOD soundbank (it wants banks < 64).
FREE_BANKS = [65, 66, 67, 68, 69, 90, 91, 92, 93, 94]

# JpnStreet stays stage 0 -- its crowd clips were tuned first.
ORDER_FIRST = ["KOF98-JpnStreetStage"]

# stage name -> music module .mid source under music/  (module idx = stage+1)
# Canonical KOF'98 stage themes.  Esaka is stage 0 (reused verbatim); the
# other nine follow the arcade team themes, keeping one song per stage.
STAGE_SONGS = {
    "KOF98-JpnStreetStage":  "EsakaVer3.mid",      # Hero Team   -- Esaka?
    "KOF98-ChinaStage":      "kof98_dora.mid",     # Psycho      -- Shin! Senritsu no Dora
    "KOF98-JpnTempleStage":  "KOF98Arashi2.mid",   # Yagami      -- Arashi no Saxophone 2
    "KOF98-KoreaStage":      "kof98_stown.mid",    # Kim         -- Soul Town
    "KOF98-Mid.EastStage":   "Rumbling.mid",       # Ikari       -- Rumbling on the City
    "KOF98-RugalStage":      "rugalomega98.mid",   # Rugal       -- The R.D.
    "KOF98-SpainStage":      "Fairy98.mid",        # Women       -- Fairy
    "KOF98-USAWharfStage":   "Ryu-ko_Final.mid",   # Art of Fight
    "KOF98-USAWharfStage-B": "KOF98Slum.mid",      # American Sports -- Slum No. 5
    "KOF98-USAYardStage":    "Kurikinton_Gomame_Guitar_Ver_.mid",  # Fatal Fury
}

# CRYSTAL is the secret SURVIVOR-ending theme (SvEndEnter -> SONG_CRYSTAL),
# so it must never be part of the stage rotation.  If a stage is ever mapped
# to it, use Art of Fight instead.
SECRET_STAGE_SONGS = {"kof00_crystal.mid"}
ART_OF_FIGHT_MIDI = "Ryu-ko_Final.mid"


def stage_song(name):
    """MIDI used by a stage, excluding the secret ending theme."""
    midi = STAGE_SONGS.get(name)
    return ART_OF_FIGHT_MIDI if midi in SECRET_STAGE_SONGS else midi


DYN_BASE = 704                      # first dynamic BG1 tile ($2C00 word)
DYN_MAX = 704 + 160                 # $2C00..$3FFF words -> 160 tiles
# v2 clip descriptors are loaded by the per-stage pool/ticker, but these
# three stages still trip the v1 ticker (black screen) on hardware/emulator.
# Keep their new static art while the descriptor/timing review is pending.
V2_ANIM_DISABLE = {
    "KOF98-JpnStreetStage",
    "KOF98-JpnTempleStage",
    "KOF98-RugalStage",
}


def _flip(tile, h, v):
    """64 raw indices (8x8 row major) -> flipped tile."""
    rows = [tile[r * 8:(r + 1) * 8] for r in range(8)]
    if h:
        rows = [r[::-1] for r in rows]
    if v:
        rows = rows[::-1]
    return b"".join(rows)


# flip bit values of a BG tilemap word (bit 15 / priority stays 0)
FLIPS = [("noflip", lambda t: t), ("h", lambda t: _flip(t, True, False)),
         ("v", lambda t: _flip(t, False, True)),
         ("hv", lambda t: _flip(t, True, True))]
FLIPBITS = [0, 0x4000, 0x8000, 0xC000]


def emit_stage(path):
    """512x224 indexed PNG -> (chr, map64x32, pal96B, pixel indices).

    Pixel value = palette group * 15 + colour; every 8x8 tile belongs to one
    group.  The group selects BG palette 2+group, so the three stage
    palettes that StagePick uploads each hold up to 15 colours.  Tiles are
    reused across H/V flips and across palette groups (same pattern, other
    palette bits), which saves room inside the 512-tile budget."""
    from PIL import Image
    img = Image.open(path)
    assert img.mode == "P" and img.size == (512, 224), \
        f"{path}: needs a 512x224 indexed PNG"
    cols = img.getcolors(1 << 24)
    assert len(cols) <= STAGE_NCOL * STAGE_NPAL, \
        f"{path}: {len(cols)} colours > {STAGE_NCOL * STAGE_NPAL}"
    sp = img.getpalette()
    rgb = [tuple(sp[i * 3:i * 3 + 3]) for i in range(STAGE_NCOL * STAGE_NPAL)]
    pal = b""
    for p in range(STAGE_NPAL):                  # BG palettes 2, 3 and 4
        # BG colour 0 is transparent, so colour c of the group sits at CGRAM
        # entry c+1 (16 entries: spare + 15 art colours)
        group = [(0, 0, 0)] + rgb[p * STAGE_NCOL:(p + 1) * STAGE_NCOL]
        group += [(0, 0, 0)] * (16 - len(group))
        pal += snes_pal(group, 16)
    raw = img.tobytes()
    pix = raw                                    # 0 = transparent, as-is

    tileset, order = {}, []
    flipset = {}                     # stored tile bytes -> tile number
    tiles = [0] * (28 * 64)
    for ty in range(28):
        for tx in range(64):
            rows = [raw[(ty * 8 + r) * 512 + tx * 8:
                        (ty * 8 + r) * 512 + tx * 8 + 8] for r in range(8)]
            grp = rows[0][0] // STAGE_NCOL
            assert all(v // STAGE_NCOL == grp for r in rows for v in r), \
                f"{path}: tile {tx},{ty} spans palette groups"
            tile = bytes(v - grp * STAGE_NCOL for r in rows for v in r)
            hit = None
            for f in range(4):    # stored tile flipped by f == this tile?
                k = FLIPS[f][1](tile)
                if k in flipset:
                    hit = (flipset[k], f)
                    break
            if hit is None:
                t4 = tiles4bpp(bytes(v + 1 for v in tile), 8, 8)[0]
                if t4 not in tileset:
                    tileset[t4] = len(order)
                    order.append(t4)
                hit = (tileset[t4], 0)
                flipset[tile] = hit[0]   # stored orientation, unflipped
            tiles[ty * 64 + tx] = (hit[0] | ((STAGE_BG_PALETTE + grp) << 10) |
                                   FLIPBITS[hit[1]])
    # Per-stage vertical placement.  The art is 28 rows; the BG1 map is 32.
    # Shift the whole image down by `yofs` rows so the deck/floor meets the
    # engine's fixed GROUND_Y, extending the first/last art rows into the
    # spare rows (the top band sits behind the HUD).
    name = os.path.splitext(os.path.basename(path))[0]
    yofs = STAGE_YOFS.get(name, 0)
    if yofs:
        assert 0 <= yofs <= 32 - 28, f"{path}: yofs {yofs} exceeds map"
        shifted = []
        for ty in range(32):
            src = min(27, max(0, ty - yofs))
            shifted.extend(tiles[src * 64:(src + 1) * 64])
        tiles = shifted
    else:
        tiles += [0] * (32 * 64 - len(tiles))    # rows 28-31 stay blank
    tilemap = struct.pack("<%dH" % len(tiles), *tiles)
    assert len(order) <= MAX_TILES, \
        f"{path}: {len(order)} tiles > BG1 budget {MAX_TILES}"
    wide = bytearray()
    for plane in (0, 1):
        for ty in range(32):
            for tx in range(32):
                wide += tilemap[(ty * 64 + plane * 32 + tx) * 2:
                                (ty * 64 + plane * 32 + tx) * 2 + 2]
    return b"".join(order), bytes(wide), pal, pix


def build_anims(stage_names):
    """Emit v2 per-stage BG1 clip descriptors.

    Each stage owns a <=160-tile pool (``anim/<stage>.pool.chr``) loaded on
    stage pick.  The tilemap words in the JSON are relative to that pool, so
    add DYN_BASE (704) to their low tile number.  Clips with more than 255
    cells are split; the engine has eight timer slots.
    """
    import json
    out = ["; generated by build_stages.py -- v2 per-stage BG1 animations",
           "STGACHR = $2C00                 ; VRAM word of dynamic tile 704"]
    stage_lists = []
    clip_id = 0
    for si, sname in enumerate(stage_names):
        path = os.path.join(ANIM_DIR, sname + ".json")
        if sname in V2_ANIM_DISABLE or not os.path.exists(path):
            stage_lists.append(0)
            continue
        spec = json.load(open(path))
        clips = spec.get("clips", [])
        if not clips:
            stage_lists.append(0)
            continue
        yofs = STAGE_YOFS.get(sname, 0)
        ptrs = []
        body = []
        for c in clips:
            cells = c["cells_ty_tx"]
            seq = c["sequence_state_ticks"]
            state_words = c["state_tilemap_words"]
            # The v2 sequence can list many 60 Hz steps while cycling through
            # only six real poses.  Collapse it to those poses and use the
            # average tick count per pose; this keeps the animation while
            # shrinking the descriptor from hundreds of KB to a few KB.
            order = []
            acc = {}
            for state, ticks in seq:
                if state not in acc:
                    order.append(state)
                    acc[state] = [0, 0]
                acc[state][0] += int(ticks)
                acc[state][1] += 1
            nposes = len(order)
            assert 0 < nposes <= 6, f"{sname}: {nposes} unique poses"
            ticks = [max(1, round(acc[state][0] / acc[state][1]))
                     for state in order]
            assert max(ticks, default=0) < 65536
            # The engine stores ncells as a byte.  Split wide clips; every
            # split runs in parallel from its own timer slot.
            for base in range(0, len(cells), 255):
                chunk = list(range(base, min(base + 255, len(cells))))
                flat = []
                for ci in chunk:
                    ty, tx = cells[ci]
                    flat.append((tx // 32) * 1024 + (ty + yofs) * 32 + tx % 32)
                    for state in order:
                        w = int(state_words[state][ci])
                        tile = (w & 0x03FF) + DYN_BASE
                        assert tile < DYN_MAX, f"{sname}: pool tile {tile}"
                        flat.append((w & 0xFC00) | tile)
                label = f"StgAnimC{clip_id}"
                body += [
                    f"{label}:                       ; {c.get('id', 'clip')} "
                    f"cells {base}..{base + len(chunk) - 1}",
                    f"    .DB {len(chunk)}, {nposes}, 0",
                    "    .DW " + ", ".join(str(v) for v in ticks),
                    "    .DW " + ", ".join(f"${w:04X}" for w in flat),
                ]
                ptrs.append(label)
                clip_id += 1
        if len(ptrs) > 8:
            raise SystemExit(
                f"{sname}: {len(ptrs)} clips exceed the engine's 8 slots")
        out.append(f"StgAnimS{si}: .DB {len(ptrs)}\n"
                   f"    .DW " + ", ".join(ptrs))
        body and out.extend(body)
        stage_lists.append(1)
    out.append("StgAnimTab: .DW " + ", ".join(
        f"StgAnimS{i}" if stage_lists[i] else "0"
        for i in range(len(stage_names))))
    open(os.path.join(OUT, "stage_anim.inc"), "w").write("\n".join(out) + "\n")
    return clip_id


def sorted_stage_paths():
    """Stage PNGs in build order: JpnStreet first, then filename order."""
    return sorted(glob.glob(os.path.join(PNG_DIR, "*.png")),
                  key=lambda p: (ORDER_FIRST.index(os.path.splitext(
                      os.path.basename(p))[0])
                      if os.path.splitext(os.path.basename(p))[0]
                      in ORDER_FIRST else len(ORDER_FIRST),
                      os.path.basename(p)))


def build():
    from PIL import Image
    out_dir = os.path.join(OUT, "stages")
    os.makedirs(out_dir, exist_ok=True)
    paths = sorted_stage_paths()
    stages = []
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            chr_b, map_b, pal_b, _pix = emit_stage(path)
        except AssertionError as exc:
            print(f"{name}: skipped ({exc})")
            continue
        pool_path = os.path.join(ANIM_DIR, name + ".pool.chr")
        if not os.path.exists(pool_path):
            print(f"{name}: skipped (missing {pool_path})")
            continue
        pool = open(pool_path, "rb").read()
        idx = len(stages)
        open(os.path.join(out_dir, f"stg{idx}.chr"), "wb").write(chr_b)
        open(os.path.join(out_dir, f"stg{idx}.map"), "wb").write(map_b)
        open(os.path.join(out_dir, f"stg{idx}.pal"), "wb").write(pal_b)
        open(os.path.join(out_dir, f"stg{idx}_anim.chr"), "wb").write(pool)
        Image.open(path).save(os.path.join(out_dir, f"stg{idx}_preview.png"))
        stages.append((name, len(chr_b) + len(map_b) + len(pal_b) + len(pool)))
        print(f"stg{idx} {name}: {len(chr_b)//32} tiles, "
              f"{len(pool)//32} anim tiles")

    nclips = build_anims([n for n, _ in stages])

    tab = ["; generated by build_stages.py -- do not edit\n",
           f".DEFINE NSTAGES {len(stages)}\n", "StageTab:\n"]
    pooltab = ["StgAnimPoolTab:\n"]
    for i in range(len(stages)):
        tab.append(f"    .dw Stg{i}Chr, Stg{i}Chr_End-Stg{i}Chr, "
                   f"Stg{i}Map, Stg{i}Pal\n"
                   f"    .db :Stg{i}Chr, :Stg{i}Map, :Stg{i}Pal, 0\n")
        pooltab.append(f"    .dw Stg{i}AnimChr, Stg{i}AnimChr_End-Stg{i}AnimChr\n"
                       f"    .db :Stg{i}AnimChr, 0\n")
    open(os.path.join(OUT, "stages_tab.inc"), "w").write(
        "".join(tab + pooltab))

    # music module index per stage (module 0 = sfx.it)
    mods = ["; generated by build_stages.py -- do not edit\n", "StageModTab:\n"]
    for i, (name, _s) in enumerate(stages):
        mods.append(f"    .db {i + 1}   ; {name} -> {stage_song(name)}\n")
    open(os.path.join(OUT, "stgmods.inc"), "w").write("".join(mods))

    # greedy bin-pack the blobs into 32 KiB ($8000-$FFFF) bank windows
    banks = []
    free = iter(FREE_BANKS)
    cur_bank, cur_size, cur_items = next(free), 0, []
    for i, (_n, size) in enumerate(stages):
        if cur_size + size > 0x8000:
            banks.append((cur_bank, cur_items))
            cur_bank, cur_size, cur_items = next(free), 0, []
        cur_items.append(i)
        cur_size += size
    banks.append((cur_bank, cur_items))
    inc = ["; generated by build_stages.py -- do not edit\n"]
    for bank, items in banks:
        inc.append(f".BANK {bank} SLOT 0\n.ORGA $8000\n"
                   f".SECTION \"StageData{bank}\" FORCE\n")
        for i in items:
            inc.append(f"Stg{i}Chr: .INCBIN \"gen_fight/stages/stg{i}.chr\"\n"
                       f"Stg{i}Chr_End:\n"
                       f"Stg{i}Map: .INCBIN \"gen_fight/stages/stg{i}.map\"\n"
                       f"Stg{i}Pal: .INCBIN \"gen_fight/stages/stg{i}.pal\"\n"
                       f"Stg{i}AnimChr: .INCBIN \"gen_fight/stages/stg{i}_anim.chr\"\n"
                       f"Stg{i}AnimChr_End:\n")
        inc.append(".ENDS\n\n")
    open(os.path.join(OUT, "stages.inc"), "w").write("".join(inc))
    print(f"{len(stages)} stages, {nclips} anim clips, "
          f"{len(banks)} bank(s): {[b for b, _ in banks]}")
    return [n for n, _ in stages]


if __name__ == "__main__":
    build()
