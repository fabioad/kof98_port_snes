#!/usr/bin/env python3
"""Render a real 256x224 SNES frame from live WRAM + generated assets.

Reads the OAM shadow ($1800), HUD tilemap mirror ($4700) and fighter state
($4000/$4040) through the RetroArch remote, then composites BG1 (stage),
OBJ cells and BG3 (HUD) with the generated .chr/.pal/.map files so the
result is the actual rendered state of the emulated game, not a mockup.
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "build" / "gen_fight"
ROM = ROOT / "kof98-snes.sfc"

OAMBUF = 0x1800            # 512B low + 32B high table
HUDMAP = 0x4700            # 32x32 tilemap mirror (2B cells)
FP1, FP2 = 0x4000, 0x4040
F_META, F_TILEPG, F_TBANK, F_CHAR = 22, 27, 46, 44
P2TILEOF = 256
SEL1, SEL2 = 0x85, 0x86

# OBJ nametable base $6000 (word) -> tile 0. VRAM regions in tile units:
P2_TILE_BASE = 0x100       # P2CHR $7000
SPK1_TILE = 0xC0           # SPK1CHR $6C00, 64 tiles
SPK2_TILE = 0x1C0          # SPK2CHR $7C00, 64 tiles
F_BANK = {0xFB: "iori", 0xFF: "kyo",      # full-bank data (ORGA $0000)
          0xFD: "iori", 0xFE: "kyo"}      # legacy ORGA $8000 layout


def load_sym():
    syms = {}
    for line in (ROOT / "kof98-snes.sym").read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 8:
            syms[parts[1]] = int(parts[0], 16)
    return syms


SYMS = load_sym()


def rom_bytes(addr24, size):
    """24-bit $BB:AAAA -> file offset. HiROM: banks $C0+ are 64 KiB blocks;
    full-bank sections (ORGA $0000) use the whole block, $8000 sections the
    upper half only."""
    bank, off = (addr24 >> 16) & 0xFF, addr24 & 0xFFFF
    if bank >= 0xC0:
        if bank in F_BANK and bank not in (0xFD, 0xFE):
            pos = (bank - 0xC0) * 0x10000 + off
        else:
            pos = (bank - 0xC0) * 0x10000 + 0x8000 + (off & 0x7FFF)
    else:
        pos = (bank & 0x7F) * 0x8000 + (off & 0x7FFF)
    with ROM.open("rb") as f:
        f.seek(pos)
        return f.read(size)


def chr_tiles(data, bpp=4):
    """Decode packed SNES tiles -> list of 8x8 index arrays."""
    tsize = 8 * bpp // 8 * 8  # 32 bytes for 4bpp, 16 for 2bpp
    tiles = []
    for t in range(len(data) // tsize):
        tile = [[0] * 8 for _ in range(8)]
        base = t * tsize
        for y in range(8):
            for plane in range(bpp):
                off = base + (plane // 2) * 16 + (plane % 2) + y * 2
                byte = data[off]
                for x in range(8):
                    tile[y][7 - x] |= ((byte >> x) & 1) << plane
        tiles.append(tile)
    return tiles


def pal_colors(data):
    """BGR555 binary -> list of (r,g,b)."""
    out = []
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        out.append(((w & 31) * 8, ((w >> 5) & 31) * 8, ((w >> 10) & 31) * 8))
    return out


def load_assets():
    a = {}
    a["stage_tiles"] = chr_tiles((GEN / "stage.chr").read_bytes())
    a["stage_map"] = (GEN / "stage.map").read_bytes()
    a["stage_pal"] = pal_colors((GEN / "stage_pal.bin").read_bytes())
    a["hud_tiles"] = chr_tiles((GEN / "hud.chr").read_bytes(), bpp=2)
    a["hud_pal"] = pal_colors((GEN / "hud_pal.bin").read_bytes())
    a["spark_tiles"] = chr_tiles((GEN / "spark.chr").read_bytes())
    a["chr"] = {
        "iori": chr_tiles((GEN / "iori.chr").read_bytes()),
        "kyo": chr_tiles((GEN / "kyo.chr").read_bytes()),
    }
    a["obj_pal"] = []
    for n in ("iori_pal", "kyo_pal", "spark_pal", "iori_pal_dim",
              "kyo_pal_dim", "iori_pal_hi", "kyo_pal_hi", "wood_pal"):
        a["obj_pal"].append(pal_colors((GEN / (n + ".bin")).read_bytes()))
    return a


def draw_tile(px, tile, x0, y0, colors, hflip=False, vflip=False):
    for y in range(8):
        sy = 7 - y if vflip else y
        dy = y0 + y
        if not 0 <= dy < 224:
            continue
        row = tile[sy]
        prow = px[dy]
        for x in range(8):
            sx = 7 - x if hflip else x
            dx = x0 + x
            c = row[sx]
            if c and 0 <= dx < 256:
                prow[dx] = colors[c]


def draw_cell16(px, get_tile, T, x0, y0, colors, hflip, vflip):
    """16x16 OAM cell: subtiles T, T+1, T+16, T+17."""
    subs = ((T, 0, 0), (T + 1, 8, 0), (T + 16, 0, 8), (T + 17, 8, 8))
    for ti, ox, oy in subs:
        tile = get_tile(ti)
        if tile is None:
            continue
        sx = x0 + (15 - ox if hflip else ox)
        sy = y0 + (15 - oy if vflip else oy)
        draw_tile(px, tile, sx, sy, colors, hflip, vflip)


def sprite_meta(ra, base):
    """F_META -> (ncells, first_tile) from the ROM copy of SprData."""
    meta_ofs = ra.read_ram(base + F_META, 2)
    meta_ofs = meta_ofs[0] | meta_ofs[1] << 8
    bank = ra.read_ram(base + F_TBANK, 1)[0]
    if not meta_ofs:
        return None
    head = rom_bytes(bank << 16 | meta_ofs, 5)
    ncells = head[0]
    first_tile = head[1] | head[2] << 8
    name = F_BANK.get(bank)
    if name is None:
        return None
    return name, first_tile, ncells


def read_ram(ra, addr, size):
    """READ_CORE_RAM replies are ASCII hex over UDP; chunk to stay < 4KB."""
    out = bytearray()
    for off in range(0, size, 256):
        out += ra.read_ram(addr + off, min(256, size - off))
    return bytes(out)


def render(ra):
    a = ASSETS
    px = [[(0, 0, 0)] * 256 for _ in range(224)]

    # --- BG1: stage tilemap (64x28 world, scrolled by camx), 4bpp ---------
    # Per-stage assets: stageidx ($1087) picks which stgN.* set the engine
    # uploaded into BG1 VRAM/CGRAM.
    stg = ra.read_ram(0x1087, 1)[0]
    a["stage_tiles"] = chr_tiles(
        (GEN / "stages" / f"stg{stg}.chr").read_bytes())
    a["stage_map"] = (GEN / "stages" / f"stg{stg}.map").read_bytes()
    a["stage_pal"] = pal_colors(
        (GEN / "stages" / f"stg{stg}.pal").read_bytes())
    smap = a["stage_map"]
    camx = ra.read_ram(0x1089, 2)[0] | ra.read_ram(0x108A, 2)[0] << 8
    xoff = camx & 7
    cbase = camx >> 3
    for cy in range(28):
        for cx in range(-1, 33):
            wc = cbase + cx
            if not 0 <= wc < 64:
                continue
            ci = (wc >> 5) * 1024 + cy * 32 + (wc & 31)
            w = smap[ci * 2] | smap[ci * 2 + 1] << 8
            t = w & 0x3FF
            if t >= len(a["stage_tiles"]):
                continue
            colors = [a["stage_pal"][(w >> 10 & 7) * 16 + i] for i in range(16)]
            draw_tile(px, a["stage_tiles"][t], cx * 8 - xoff, cy * 8, colors,
                      bool(w & 0x4000), bool(w & 0x8000))

    # --- OBJ: OAM shadow ---------------------------------------------------
    oam = read_ram(ra, OAMBUF, 544)
    metas = [sprite_meta(ra, FP1), sprite_meta(ra, FP2)]
    pbases = [ra.read_ram(FP1 + F_TILEPG, 1)[0],
              ra.read_ram(FP2 + F_TILEPG, 1)[0] + P2TILEOF]

    def tile_for(T):
        """OAM tile index -> decoded 8x8 tile or None."""
        if T >= SPK2_TILE:
            return a["spark_tiles"][64 + T - SPK2_TILE] \
                if T - SPK2_TILE < 64 else None
        if T >= SPK1_TILE and T < 0x100:
            return a["spark_tiles"][T - SPK1_TILE] \
                if T - SPK1_TILE < 64 else None
        for f in (0, 1):
            if metas[f] and pbases[f] <= T < pbases[f] + 96:
                name, first_tile, _ = metas[f]
                idx = first_tile + T - pbases[f]
                return a["chr"][name][idx] \
                    if 0 <= idx < len(a["chr"][name]) else None
        return None

    order = sorted(range(128), key=lambda i: (oam[i * 4 + 3] >> 4) & 3)
    for i in order:
        x, y, tl, at = oam[i * 4:i * 4 + 4]
        if y >= 0xF0:
            continue
        hi = oam[512 + i // 4] >> ((i % 4) * 2) & 3
        if hi & 1:
            x -= 256
        T = tl | (at & 1) << 8
        pal = (at >> 1) & 7
        colors = a["obj_pal"][pal]
        if hi & 2:                              # 16x16 cell (large OBJ)
            draw_cell16(px, tile_for, T, x, y, colors,
                        bool(at & 0x40), bool(at & 0x80))
        else:                                   # 8x8 sub-cell
            draw_tile(px, tile_for(T) or [[0] * 8] * 8, x, y, colors,
                      bool(at & 0x40), bool(at & 0x80))

    # --- BG3: HUD (mode-1 high priority, 2bpp) -----------------------------
    # 2bpp tilemap palette p -> CGRAM colors p*4..p*4+3.  HudPal's 20 colors
    # are loaded at CGRAM 12-31 (palettes 3-7: text/green/yellow/red/silver).
    cgram = a["stage_pal"][:]
    cgram += [(0, 0, 0)] * 64
    cgram[12:32] = a["hud_pal"][:20]
    hud = read_ram(ra, HUDMAP, 2048)
    for cy in range(32):
        for cx in range(32):
            w = hud[(cy * 32 + cx) * 2] | hud[(cy * 32 + cx) * 2 + 1] << 8
            t = w & 0x3FF
            if t == 0 or t >= len(a["hud_tiles"]):
                continue
            pi = (w >> 10) & 7
            colors = [cgram[pi * 4 + i] for i in range(4)]
            draw_tile(px, a["hud_tiles"][t], cx * 8, cy * 8, colors,
                      bool(w & 0x4000), bool(w & 0x8000))

    img = Image.new("RGB", (256, 224))
    img.putdata([c for row in px for c in row])
    return img


ASSETS = load_assets()

if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    import test_fight_remote as t
    ra = t.RetroArch()
    if not ra.command("GET_STATUS").startswith("GET_STATUS PLAYING"):
        ra.launch("retroarch", t.CORE)
    try:
        ra.wait_ready()
        img = render(ra)
        out = sys.argv[1] if len(sys.argv) > 1 else "frame.png"
        img.save(out)
        print("saved", out)
    finally:
        ra.close()
