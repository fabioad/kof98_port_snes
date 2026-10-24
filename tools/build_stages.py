#!/usr/bin/env python3
"""Convert every stage PNG in assets/stages/stages_png_snes/ into SNES BG1
assets and emit the per-stage animation tables described by
assets/stages/stages_png_snes/animations/stage_animations.json.

The PNGs are already authored to the SNES format (512x224, <=15 colours,
<=512 unique 8x8 tiles), so conversion is lossless:

  stages/stgNN.chr   4bpp tiles (deduped, <= 512 -> fits BG1CHR $0000-$1FFF)
  stages/stgNN.map   64x32-word tilemap (two 32x32 planes, 512px wide)
  stages/stgNN.pal   3x16 BGR555 entries (BG palette 2 holds the art colours)

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
PNG_DIR = os.path.join(ROOT, "assets/stages/stages_png_snes")
ANIM_JSON = os.path.join(PNG_DIR, "animations/stage_animations.json")
OUT = os.path.join(ROOT, "build/gen_fight")

MAX_TILES = 512                     # BG1CHR $0000-$1FFF = 16 KiB
STAGE_BG_PALETTE = 2                # BG3 HUD uses CGRAM colours 12-31
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


def emit_stage(path):
    """512x224 mode-P PNG -> (chr, map64x32, pal96B, pixel indices)."""
    from PIL import Image
    img = Image.open(path)
    assert img.mode == "P" and img.size == (512, 224), \
        f"{path}: needs a 512x224 indexed PNG"
    cols = img.getcolors(1 << 24)
    assert len(cols) <= 15, f"{path}: {len(cols)} colours > 15"
    sp = img.getpalette()
    pal = [(0, 0, 0)] + [tuple(sp[i * 3:i * 3 + 3]) for i in range(len(cols))]
    pal += [(0, 0, 0)] * (16 - len(pal))
    pix = bytes(b + 1 for b in img.tobytes())

    tiles = tiles4bpp(pix, 512, 224)[0]
    tileset, order, tilemap = {}, [], bytearray()
    for i in range(28 * 64):
        t = tiles[i * 32:(i + 1) * 32]
        if t not in tileset:
            tileset[t] = len(order)
            order.append(t)
        tilemap += struct.pack("<H", tileset[t] | (STAGE_BG_PALETTE << 10))
    assert len(order) <= MAX_TILES, \
        f"{path}: {len(order)} tiles > BG1 budget {MAX_TILES}"
    wide = bytearray()
    for plane in (0, 1):
        for ty in range(32):
            if ty < 28:
                for tx in range(32):
                    wide += tilemap[(ty * 64 + plane * 32 + tx) * 2:
                                    (ty * 64 + plane * 32 + tx) * 2 + 2]
            else:
                wide += b"\x00" * 64
    return (b"".join(order), bytes(wide),
            b"".join(snes_pal(p, 16) for p in
                     (pal, [(0, 0, 0)] * 16, [(0, 0, 0)] * 16)), pix)


def build_anims(stage_names, pix_by_stage):
    """Sparse BG1 crowd/pose patches per stage, from stage_animations.json.

    Every pose of every clip is resident in the shared dynamic pool
    (tile index 704+), so a commit is a tilemap write only.  Pose k of a
    cell re-samples the source k px higher -- a gentle bob that stands in
    for the MUGEN gestures.  Format:

      StgAnimTab: .DW S0..S{n}            ; one list ptr per stage (0=none)
      Si: .DB nclips ; .DW clip ptrs
      clip: .DB ncells, nposes, phase
            .DW ticks[nposes]
            .DW mapidx, tileP0..tilePn    ; per cell
    """
    import json
    spec = json.load(open(ANIM_JSON))
    chr_out = bytearray()
    asm = ["; generated: per-stage BG1 animation patches (resident poses)",
           "STGACHR = $2C00                 ; VRAM word of dynamic tile 704",
           'StgAnimChr: .INCBIN "gen_fight/stage_anim.chr"',
           "StgAnimChr_End:"]
    tile_no = DYN_BASE
    stage_lists = []
    clip_id = 0
    for si, sname in enumerate(stage_names):
        clips = [c for c in spec["clips"] if c["stage"] == sname
                 and c["target"].get("mode") == "bg1_sparse_double_buffer"]
        if not clips:
            stage_lists.append(0)
            continue
        ptrs = [f"StgAnimC{clip_id + k}" for k in range(len(clips))]
        asm.append(f"StgAnimS{si}: .DB {len(clips)}\n"
                   f"    .DW " + ", ".join(ptrs))
        body = []
        for c in clips:
            t = c["target"]
            rx, ry, rw, rh = t["target_region_xywh"]
            cap = t["changed_tiles_per_pose_cap"]
            nposes = t["frame_count"]
            ticks = [s["ticks60"] for s in t["sequence"]]
            assert len(ticks) == nposes and max(ticks) < 65536
            phase = t.get("start_phase_ticks60", 0)
            pix = pix_by_stage[sname]
            cells = []
            for ty in range(ry // 8, (ry + rh) // 8):
                for tx in range(rx // 8, (rx + rw) // 8):
                    if (ty * 8 - ry) >= rh * 2 // 3:
                        continue            # upper rows move; floor static
                    vals = [pix[(ty * 8 + r) * 512 + tx * 8 + c]
                            for r in range(8) for c in range(8)]
                    mode = max(set(vals), key=vals.count)
                    cells.append((sum(v != mode for v in vals), tx, ty))
            cells = sorted(cells, reverse=True)[:cap]
            cells.sort(key=lambda s: (s[2], s[1]))
            entries = []
            for _, tx, ty in cells:
                for pose in range(nposes):
                    y0 = max(ty * 8 - pose, 0)
                    chr_out += tiles4bpp(b"".join(
                        bytes(pix[(y0 + r) * 512 + tx * 8:
                                  (y0 + r) * 512 + tx * 8 + 8])
                        for r in range(8)), 8, 8)[0]
                mapidx = (tx // 32) * 1024 + ty * 32 + tx % 32
                entries.append([mapidx] +
                               [(tile_no + p) | (STAGE_BG_PALETTE << 10)
                                for p in range(nposes)])
                tile_no += nposes
            flat = [w for e in entries for w in e]
            body += [f"StgAnimC{clip_id}:                       ; {c['id']}",
                     f"    .DB {len(cells)}, {nposes}, {phase}",
                     "    .DW " + ", ".join(str(v) for v in ticks),
                     "    .DW " + ", ".join(f"${w:04X}" for w in flat)]
            clip_id += 1
        asm += body
        stage_lists.append(1)
    asm.append("StgAnimTab: .DW " +
               ", ".join(f"StgAnimS{i}" if stage_lists[i] else "0"
                         for i in range(len(stage_names))))
    assert tile_no <= DYN_MAX, "stage anim tiles overflow dynamic range"
    open(os.path.join(OUT, "stage_anim.chr"), "wb").write(bytes(chr_out))
    open(os.path.join(OUT, "stage_anim.inc"), "w").write("\n".join(asm) + "\n")
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
    stages, pix_by_stage = [], {}
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            chr_b, map_b, pal_b, pix = emit_stage(path)
        except AssertionError as exc:
            print(f"{name}: skipped ({exc})")
            continue
        idx = len(stages)
        open(os.path.join(out_dir, f"stg{idx}.chr"), "wb").write(chr_b)
        open(os.path.join(out_dir, f"stg{idx}.map"), "wb").write(map_b)
        open(os.path.join(out_dir, f"stg{idx}.pal"), "wb").write(pal_b)
        Image.open(path).save(os.path.join(out_dir, f"stg{idx}_preview.png"))
        stages.append((name, len(chr_b) + len(map_b) + len(pal_b)))
        pix_by_stage[name] = pix
        print(f"stg{idx} {name}: {len(chr_b)//32} tiles")

    nclips = build_anims([n for n, _ in stages], pix_by_stage)

    tab = ["; generated by build_stages.py -- do not edit\n",
           f".DEFINE NSTAGES {len(stages)}\n", "StageTab:\n"]
    for i in range(len(stages)):
        tab.append(f"    .dw Stg{i}Chr, Stg{i}Chr_End-Stg{i}Chr, "
                   f"Stg{i}Map, Stg{i}Pal\n"
                   f"    .db :Stg{i}Chr, :Stg{i}Map, :Stg{i}Pal, 0\n")
    open(os.path.join(OUT, "stages_tab.inc"), "w").write("".join(tab))

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
                       f"Stg{i}Pal: .INCBIN \"gen_fight/stages/stg{i}.pal\"\n")
        inc.append(".ENDS\n\n")
    open(os.path.join(OUT, "stages.inc"), "w").write("".join(inc))
    print(f"{len(stages)} stages, {nclips} anim clips, "
          f"{len(banks)} bank(s): {[b for b, _ in banks]}")
    return [n for n, _ in stages]


if __name__ == "__main__":
    build()
