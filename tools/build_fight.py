#!/usr/bin/env python3
"""Build SNES fight data from MUGEN/Ikemen-format assets.

Generates into build/gen_fight/:
  <char>.chr     4bpp tile stream for every referenced character sprite
  <char>_pal.bin sprite palette (BGR555, index 0 = transparent)
  <char>_spr.inc metasprites, AIR boxes, animations, CNS/CMD tables, name
  stage.chr      BG 4bpp tiles, stage.map 32x28 tilemap, stage_pal.bin
"""
import os
import copy
import glob
import json
import re
import statistics
import struct
import sys
import unicodedata
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sff import Sff, Sprite, snes_pal, tiles4bpp
from runtime_abi import ABI as RUNTIME_ABI, emit as emit_runtime_abi
from calibration.projectiles import (PROJECTILE_ACTIONS,
                                     PROJECTILE_ACTION_SEQUENCES,
                                     PROJECTILE_SOURCE_PALETTES,
                                     PROJECTILE_ZOOM, GROUND_PROJECTILES,
                                     TORSO_PROJECTILES,
                                     PROJECTILE_TORSO_SIDS,
                                     PROJECTILE_ZOOM_BY_CHAR,
                                     PROJECTILE_CALIBRATION,
                                     PROJECTILE_RECOVERY,
                                     PROJECTILE_RECOVERY_TICKS,
                                     PROJECTILE_FX_ALIAS,
                                     PROJECTILE_ALT_EFFECTS,
                                     BODY_ANIMATIONS as
                                     PROJECTILE_BODY_ANIMATIONS)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "gen_fight")

# (name, chr-bytes) pairs appended to kof98-snes.msu at 32 KiB alignment;
# emitted as msu1_bases.inc + the data file at the end of the build.  Keyed by
# name: skipped characters may reuse an older CHR blob, and the layout must
# stay in roster order either way or every slice index shifts.
MSU_BLOBS = {}

# Fixed ROM banks for characters whose CHR stays in the ROM (descriptors in
# fight.asm reference <Name>Chr directly).  Streamed characters use the MSU
# slice path instead; their "_chr.inc" only carries a comment.
CNAME_BANKS = {
    "iori": ("Iori", 2, 71, "$8000"),
    "kyo": ("Kyo", 26, 95, "$8000"),
    "terry": ("Terry", 65, 65, "$0000"),
    "shingo": ("Shingo", 70, 70, "$8000"),
    "omegarugal": ("ORugal", 95, 95, "$8000"),
    # saisyu/leona: $0000 low halves of banks <64 (full 64K
    # window at $C0+N; CH_CHR=$0000).  the rest live in the
    # extended ExHiROM region (WLA banks 128+, :ref=$40+ at
    # $8000) -> file 8-12 MiB, the SD2SNES 96 Mbit map.
    "saisyu": ("Saisyu", 2, 2, "$0000"),
    "leona": ("Leona", 27, 27, "$0000"),
    "clark": ("Clark", 128, 128, "$8000"),
    "ralf": ("Ralf", 141, 141, "$8000"),
    "takuma": ("Takuma", 158, 158, "$8000"),
    "heidern": ("Heidern", 171, 171, "$8000"),
    "mature": ("Mature", 206, 206, "$8000"),
    "vice": ("Vice", 227, 227, "$8000"),
    # Yuri's large fight sprites use direct ROM DMA to avoid
    # the 192-byte-per-vblank MSU stream path stalling moves.
    "yuri": ("Yuri", 96, 96, "$0000"),
    # benimaru/daimon: 8 MiB ROM, low halves of banks <64
    # ($C0+N:$0000 window, CH_CHR=$0000) -- 19-slice runs
    "benimaru": ("Benimaru", 2, 2, "$0000"),
    "daimon": ("Daimon", 27, 27, "$0000"),
}
PROJECTILE_BLOBS = {}
PROJECTILE_TABLES = {}
# Optional second ProjFx clip per fighter (see PROJECTILE_ALT_EFFECTS).
# PROJECTILE_ALT_SIDS names the ProjTab rows that select it.
PROJECTILE_BLOBS2 = {}
PROJECTILE_TABLES2 = {}
PROJECTILE_ALT_SIDS = {}
PROJECTILE_ALT_RELEASE = {}
PROJECTILE_PALETTE = [(0, 0, 0)]
PROJECTILE_PALETTE_IDX = {(0, 0, 0): 0}
ART_LOSS = []

# Per-character normal special-cancel opens.  Each descriptor gets a word
# pointing at a six-byte row (strong sids in CANCEL_STRONG_ORDER) inside the
# shared CancelData bank, so tight per-character table banks do not grow.
CANCEL_OPENS = {}

# Generated per-character CPU AI move tables (see ai_move_table below).
AI_COUNTS = {}
AI_TABLES = []
AI_F_PROJ = 0x01
AI_F_AA = 0x02
AI_F_RUSH = 0x04
AI_F_SUPER = 0x08
AI_F_THROW = 0x10
AI_F_MAX = 0x20

# Per-character CPU personality flags (AiTab header byte 11).
AI_PF_PRESSURE = 0x01                   # advance after knockdowns/on block
AI_PF_METER = 0x02                      # spend a stock on a MAX burst
AI_PF_ADAPT = 0x04                      # punish hitstun and whiff recovery
AI_PF_ZONER = 0x08                      # hold the preferred range

# AiTab header extension: zone_lo, zone_hi, anti_air, throw, mixup, flags.
# Aggression/defense reuse the existing header bytes; they are now authored
# per character instead of only derived from the move kit.  Values are
# 0..255 and get scaled by the runtime difficulty (level 1 = classic AI,
# level 9 = the full personality at full strength).
#
#                 zone       aggr def  aa throw mix flags
AI_TUNING = {
    "kyo":        (30,  80, 225, 180, 220, 120, 235,
                   AI_PF_PRESSURE | AI_PF_METER | AI_PF_ADAPT),
    "kyonests":   (30,  80, 225, 180, 220, 120, 235,
                   AI_PF_PRESSURE | AI_PF_METER | AI_PF_ADAPT),
    "kyoash":     (30,  80, 225, 180, 220, 120, 235,
                   AI_PF_PRESSURE | AI_PF_METER | AI_PF_ADAPT),
    "iori":       (32,  84, 230, 190, 230,  90, 220,
                   AI_PF_PRESSURE | AI_PF_METER | AI_PF_ADAPT),
    "shingo":     (36,  90, 195, 165, 180,  80, 190,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "rugal":      (50, 160, 225, 220, 200, 160, 190,
                   AI_PF_PRESSURE | AI_PF_METER | AI_PF_ADAPT |
                   AI_PF_ZONER),
    # Omega's specials are meter-hungry boss moves; at 0 meter a wide
    # zoner band would make him stand at mid-screen blocking forever.
    # Keep the boss aggressive and let normals carry the no-meter phase.
    "omegarugal": (10,  70, 250, 230, 240, 230, 240,
                   AI_PF_PRESSURE | AI_PF_METER | AI_PF_ADAPT),
    "saisyu":     (80, 160, 210, 210, 190,  50, 150,
                   AI_PF_METER | AI_PF_ZONER),
    "heidern":    (50, 130, 210, 215, 190, 160, 150,
                   AI_PF_METER | AI_PF_ADAPT | AI_PF_ZONER),
    "takuma":     (90, 180, 205, 200, 200,  40, 140,
                   AI_PF_METER | AI_PF_ZONER),
    "clark":      (10,  44, 205, 215, 140, 250, 100, AI_PF_PRESSURE),
    "ralf":       (30,  84, 220, 195, 190, 120, 190,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "leona":      (28,  72, 210, 180, 200, 100, 230,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "mature":     (28,  72, 215, 175, 200,  80, 240,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "vice":       (12,  50, 205, 200, 170, 230, 130, AI_PF_PRESSURE),
    "benimaru":   (50, 120, 215, 200, 210,  70, 190,
                   AI_PF_METER | AI_PF_ADAPT),
    "daimon":     (10,  42, 200, 220, 150, 255,  80, AI_PF_PRESSURE),
    "terry":      (60, 130, 210, 200, 190,  60, 160,
                   AI_PF_METER | AI_PF_ADAPT | AI_PF_ZONER),
    "andy":       (30,  80, 210, 180, 200,  80, 200,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "joe":        (90, 170, 195, 200, 190,  30, 130,
                   AI_PF_METER | AI_PF_ZONER),
    "ryo":        (50, 110, 210, 215, 200,  90, 150,
                   AI_PF_METER | AI_PF_ADAPT),
    "robert":     (80, 150, 205, 195, 180,  40, 160,
                   AI_PF_METER | AI_PF_ZONER),
    "yuri":       (30,  76, 205, 170, 190,  90, 210,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "athena":     (100, 190, 210, 220, 150,  30, 140,
                   AI_PF_METER | AI_PF_ZONER),
    "kensou":     (55, 120, 195, 195, 180,  70, 160,
                   AI_PF_ADAPT | AI_PF_ZONER),
    "chin":       (70, 150, 185, 185, 160,  80, 180,
                   AI_PF_ADAPT | AI_PF_ZONER),
    "king":       (100, 190, 210, 215, 180,  40, 120, AI_PF_ZONER),
    "mai":        (32,  84, 215, 180, 200, 100, 220,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "chizuru":    (90, 170, 205, 210, 170,  40, 140,
                   AI_PF_METER | AI_PF_ADAPT | AI_PF_ZONER),
    "kim":        (30,  80, 215, 190, 210, 120, 200,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "chang":      (12,  50, 185, 200, 120, 250,  80, AI_PF_PRESSURE),
    "choi":       (28,  76, 195, 160, 170,  70, 240,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "yashiro":    (32,  84, 215, 190, 200, 110, 190, AI_PF_PRESSURE),
    "shermie":    (14,  52, 195, 210, 150, 240, 110, AI_PF_PRESSURE),
    "chris":      (30,  80, 215, 180, 190,  90, 210,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "yamazaki":   (20,  70, 205, 195, 170, 170, 160,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "mary":       (20,  64, 215, 185, 190, 200, 180,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "billy":      (90, 180, 195, 205, 180,  40, 120, AI_PF_ZONER),
    "lucky":      (90, 170, 190, 195, 170,  50, 130, AI_PF_ZONER),
    "heavyd":     (50, 120, 195, 200, 180,  90, 140, AI_PF_ADAPT),
    "brian":      (40, 100, 200, 205, 170, 120, 150, AI_PF_PRESSURE),
    "geese":      (50, 160, 235, 225, 220, 140, 200,
                   AI_PF_PRESSURE | AI_PF_METER | AI_PF_ADAPT |
                   AI_PF_ZONER),
    "krauser":    (60, 180, 235, 230, 210, 120, 180,
                   AI_PF_PRESSURE | AI_PF_METER | AI_PF_ADAPT |
                   AI_PF_ZONER),
    "mrbig":      (80, 170, 210, 205, 180,  80, 160, AI_PF_ZONER),
    "eiji":       (28,  76, 210, 175, 190,  90, 230,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "vega":       (24,  70, 215, 170, 200, 100, 240,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "ryu":        (70, 150, 225, 220, 210,  60, 170,
                   AI_PF_METER | AI_PF_ADAPT | AI_PF_ZONER),
    "ken":        (40, 100, 215, 190, 200,  80, 200,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
    "chunli":     (60, 140, 210, 195, 190,  90, 220,
                   AI_PF_ADAPT | AI_PF_ZONER),
    "sakura":     (32,  80, 205, 175, 190,  90, 210,
                   AI_PF_PRESSURE | AI_PF_ADAPT),
}

# Style fallbacks for a roster entry added without an AI_TUNING row.
AI_STYLE_PROFILE = {
    0: (44, 104, 190, 200, 180,  70, 150, AI_PF_ADAPT),
    1: (96, 180, 190, 210, 160,  40, 110,
        AI_PF_ADAPT | AI_PF_ZONER),
    2: (28,  72, 200, 170, 190, 100, 200,
        AI_PF_PRESSURE | AI_PF_ADAPT),
    3: (10,  44, 180, 190, 140, 240,  90, AI_PF_PRESSURE),
}

CHARS = {
    # Iori Yagami (KOF'98).  localcoord=320 matches the engine space, so no
    # coordinate scaling.  Iori_SNES.cns is a merged/sanitized copy of all
    # the char's state files; Iori_SNES.cmd rewrites the ikaruga-style
    # command wiring in kfm.cmd dialect for the native matcher.
    "iori": {
        "sff": "assets/characters/Iori-KOF98/Iori.sff",
        "air": "assets/characters/Iori-KOF98/Iori.air",
        "cns": "assets/characters/Iori-KOF98/Iori_SNES.cns",
        "cmd": "assets/characters/Iori-KOF98/Iori_SNES.cmd",
        # MUGEN command button -> requested SNES pad mask
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        # state id -> mugen anim number
        "anims": {
            0: 0,     # stand
            1: 20,    # walk fwd
            2: 21,    # walk back
            3: 11,    # crouch
            4: 41,    # jump neutral
            5: 200,   # punch
            6: 210,   # strong punch
            7: 230,   # kick
            8: 240,   # strong kick
            9: 5000,  # hit
            10: 5050, # knocked down (falling through the air)
            11: 5300, # dizzy/win pose-ish
            12: 10,   # stand -> crouch transition
            13: 12,   # crouch -> stand transition
            14: 40,   # jump takeoff
            15: 42,   # jump forward
            16: 43,   # jump back
            17: 47,   # land
            18: 5120, # rise from lying down
            19: 400,  # crouch punch
            20: 410,  # crouch strong punch
            21: 430,  # crouch kick
            22: 440,  # crouch strong kick (sweep, trips)
            23: 600,  # air punch
            24: 610,  # air strong punch
            25: 630,  # air kick
            26: 640,  # air strong kick
            27: 130,  # stand guard (S_GUARD)
            28: 131,  # crouch guard (S_CGUARD)
            29: 132,  # air guard (S_AGUARD)
            30: 150,  # guard hit (S_GHIT)
            # get-hit anim slots (AnimTab indices, not real states) --
            # shared anims: KOF hit reactions differ only cosmetically
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030,                       # air hit / back hit
            41: 5110,                       # lying down
            93: 5070,                       # trip fall (sweep knockdown)
            # guard-hit variants picked by SetAnimSlot
            42: 150, 43: 151, 44: 152,
            # command-driven states wired through the motion matcher
            45: 100,  # run forward (FF)
            46: 43,   # backdash: jump-back pose (anim 105's sprites don't
                      #   fit the IoriData bank; 43 is already loaded)
            47: 5300, # taunt shares the dizzy pose
            **PROJECTILE_BODY_ANIMATIONS["iori"],
                              # Yami Barai weak/strong (QCF+x/y): the body
                              #   launch anims; the flame itself is the AIR
                              #   1001 effect clip rendered from the spark pool
            50: 1100, 51: 1110, # Oniyaki weak/strong (DP+x/y; the AIR's
                              #   1101/1102 are the flame Explod clips)
            52: 1300, 53: 310,  # 52 = Yumebiki 6A first hit (F_X); the
                              #   group-100 sprites now ride the bank;
                              #   53 = Goufu In (F+B overhead)
            54: 1502, 55: 1502, # Tsumakushi weak/strong hit phase (QCF+a/b)
            56: 1305, 57: 1306, # Kototsuki grab/slam (chained from 65)
            58: 1400, 59: 1400, # Kuzukaze command throw
            # 60-66: Aoi Hana rekka chain + Kototsuki entry -- root hits sit
            #   on StAirSpec sids so TransTab kind-3 (MoveHit) chains fire;
            #   whiffed first hits recover to stand instead of committing
            60: 315,  61: 1200, 62: 1202, 63: 1201, 64: 1212,
            65: 1300, 66: 1210,
            67: 250,              # Blowback Attack (CD, ground)
            68: 1211,             # Aoi Hana strong mid-hit (StAirSpec)
            69: 720,              # attack dodge (x+a)
            94: 710,              # FUSION fwd/back roll (L+dir)
            95: 700,              # FUSION extra dodge (L)
            98: 1301,             # Yumebiki second hit
            96: 750,              # FUSION MAX burst (Y+B+X, costs stock)
            97: 760,              # FUSION manual charge (hold R+Y+B+X)
            # attacker-owned victim poses (kfm fast-palm chain): reuse
            # ordinary get-hit anims
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            # throw: attempt + bind seq (attacker), victim held and thrown
            # flight render the victim's own get-hit anims
            74: 800, 75: 1305, 76: 5000, 77: 5050,
            #   75 reuses the Kototsuki grab anim (already loaded via 56)
            #   so the throw costs zero new sprites
            # parry slots unused by Iori (78-84); keep valid anims
            78: 720, 79: 720, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            # supers: Ya Otome weak/strong + finisher slice, then the
            # 211-shiki finisher and Saku Tsumakushi MAX -- the last two
            # reuse already-converted anims so they cost no chr space
            85: 3000, 86: 3010, 87: 3020, 88: 1102, 89: 1502,
            # real win pose (anim 181) and lose pose (mugen 170); intro is
            # the real anim 191 -- its trailing t=-1 hold is stripped at
            # emit so AnimTime=0 exits to stand
            90: 181, 91: 170, 92: 191,
        },
        # internal state id -> CNS Statedef used by the native engine
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1100, 51: 1110,
                  52: 1300, 98: 1301, 53: 310, 54: 1501, 55: 1511,
                  56: 1305, 57: 1306, 58: 1400, 59: 1400,
                  60: 315, 61: 1200, 62: 1202, 63: 1201, 64: 1212,
                  65: 1300, 66: 1210, 68: 1211,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  85: 3000, 86: 3010, 87: 3020, 88: 3210, 89: 3200,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        # SF2-SNES proportions: artwork, AIR offsets and clsn boxes at 75%;
        # physics, positions and timing unchanged
        "char_scale": 0.81,
        # KOF HitDefs carry ~5-19 raw damage on a MUGEN ~103-HP scale;
        # x2 lands normals at ~6-15% and supers at ~30% of the 200-HP bar
        "damage_scale": 2.0,
        # FUSION: Yamibarai fires a spark-pool projectile
        # (sid -> vx px/tick 8.8, dmg, SparkAnim idx)
        "projs": {48: (0x0300, 14, 4), 49: (0x0400, 18, 4)},
        # FUSION: MAX burst spends one 1000 stock (the mugen
        #   statedef PowerAdd is var-gated and does not extract)
        "pow_override": {96: -1000},
        # sids 50/51 ride StAirSpec: kind-1 lands into S_LAND on descent,
        # kind-0 frees a move that never left the ground
        "extra_trans": [(50, 17, 1, 0), (50, 0, 0, 0),
                        (51, 17, 1, 0), (51, 0, 0, 0)],
        "display": "IORI",
    },
    # Kyo Kusanagi (KOF'98).  localcoord=320 matches the engine space, so no
    # coordinate scaling.  Kyo_SNES.cns is a merged/sanitized copy of all the
    # char's state files; Kyo_SNES.cmd rewrites the ikaruga-style command
    # wiring in kfm.cmd dialect for the native matcher.
    "kyo": {
        "sff": "assets/characters/Kyo-KOF98/Kyo.sff",
        "air": "assets/characters/Kyo-KOF98/Kyo.air",
        "cns": "assets/characters/Kyo-KOF98/Kyo_SNES.cns",
        "cmd": "assets/characters/Kyo-KOF98/Kyo_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 20, 3: 11, 4: 42,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300,
            12: 10, 13: 12, 14: 40, 15: 42, 16: 42,
            17: 47, 18: 5120,   # real get-up anim (trip->lie->rise)
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 131, 30: 150,
            # get-hit anim slots (AnimTab indices, not real states) --
            # shared anims: KOF hit reactions differ only cosmetically
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110,   # ANIM_LIE: real lying-on-ground frame
            93: 5070,             # trip fall (sweep knockdown)
            42: 150, 43: 150, 44: 150,
            45: 100, 46: 105, 47: 5300,  # taunt shows the dizzy pose
                                         #   (anim 160 cut for bank space)
            **PROJECTILE_BODY_ANIMATIONS["kyo"],
                              # Yami Barai weak/strong (QCF+x/y): the body
                              #   launch anims; the flame itself is the AIR
                              #   1005 effect clip rendered from the spark pool
            50: 1100, 51: 1110,   # Oniyaki weak/strong (DP+x/y)
            52: 1300, 53: 1310,   # 910-shiki weak/strong (QCB+x/y)
            54: 1200, 55: 1210,   # 75-shiki Kai weak/strong (QCF+a/b)
            56: 1500, 57: 1500,   # Oboro Guruma weak/strong (DP+a/b;
                                  #   strong reuses the weak anim: sprites
                                  #   do not fit the KyoData bank)
            58: 1800, 59: 1810,   # R.E.D. Kick weak/strong (RDP+a/b)
            # 60-68: Aragami/Dokugami rekka chains -- rekka roots and mid
            #   hits sit on StAirSpec sids so TransTab kind-3 (MoveHit)
            #   chains hit-confirm into the next stage; whiffs recover
            60: 5050, 61: 1600, 62: 1610, 63: 1605, 64: 1720,
            65: 5050, 66: 1700, 68: 1710,
            67: 250,              # Blowback Attack (CD, ground)
            69: 720,              # attack dodge (x+a)
            94: 710,              # FUSION fwd/back roll (L+dir)
            95: 700,              # FUSION extra dodge (L)
            96: 750,              # FUSION MAX burst (Y+B+X, costs stock)
            97: 760,              # FUSION manual charge (hold R+Y+B+X)
            # attacker-owned victim poses (kfm fast-palm/upper chain): the
            # 8200s throw-victim sprites exceed the 64-cell OBJ limit, so the
            # slots reuse ordinary get-hit anims
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            # throw: attempt + bind seq (attacker), victim held (815) and
            # thrown flight (816 -> victim's own fall anim)
            74: 800, 75: 826, 76: 815, 77: 5050,
            #   75 uses action 826: a 2-frame throw fake built from the
            #   already-loaded punch/blowback groups (Kyo.air)
            # parry slots unused by Kyo (78-84); keep valid anims
            78: 720, 79: 720, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            # supers: Mushiki weak/strong, MAX Mushiki, Chou Hissatsu
            # (the '99 blast's sprites were dropped for table-bank space
            # and the Orochinagi line is helper-driven -- unwired)
            85: 3200, 86: 3210, 87: 3500, 88: 3500, 89: 3500,
            # real win pose (anim 183 -- a KOF98 alt win variant; the 181
            # sprites do not fit the table bank); lose shows the dizzy
            # anim; intro is the real anim 191 (hold stripped at emit)
            90: 183, 91: 5300, 92: 191,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010,
                  50: 1100, 51: 1110,
                  52: 1300, 53: 1310, 54: 1200, 55: 1210,
                  56: 1500, 57: 1510, 58: 1800, 59: 1810,
                  61: 1600, 62: 1610, 63: 1605, 64: 1720,
                  66: 1700, 68: 1710,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  85: 3200, 86: 3210, 87: 3550, 88: 3305, 89: 3500,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        # SF2-SNES proportions: artwork, AIR offsets and clsn boxes at 75%;
        # physics, positions and timing unchanged
        "char_scale": 0.81,
        # win pose sliced to the glove-adjust + hold: elems 2-5 of anim 183
        # (arm flourish) free ~3 sprites so the real get-up 5120 fits
        "slices": {90: (183, 2, 5), 92: (191, 0, 4)},
        # KOF HitDefs carry ~5-19 raw damage on a MUGEN ~103-HP scale;
        # x2 lands normals at ~6-15% and supers at ~30% of the 200-HP bar
        "damage_scale": 2.0,
        # Yami Barai weak/strong: compact flame projectile in the shared spark pool
        "projs": {48: (0x0300, 14, 4), 49: (0x0400, 18, 4)},
        # FUSION: MAX burst spends one 1000 stock (the mugen
        #   statedef PowerAdd is var-gated and does not extract)
        "pow_override": {96: -1000},
        # sids 50/51 ride StAirSpec: kind-1 lands into S_LAND on descent,
        # kind-0 frees a move that never left the ground
        "extra_trans": [(50, 17, 1, 0), (50, 0, 0, 0),
                        (51, 17, 1, 0), (51, 0, 0, 0)],
        "display": "KYO",
    },
    # Shingo Yabuki (KOF'98).  Same merged/sanitized CNS + synthetic cmd
    # pipeline as Iori/Kyo (tools/merge_cns.py + Shingo_SNES.cmd).
    "shingo": {
        "sff": "assets/characters/Shingo-KOF98/Shingo.sff",
        "air": "assets/characters/Shingo-KOF98/Shingo.air",
        "cns": "assets/characters/Shingo-KOF98/Shingo_SNES.cns",
        "cmd": "assets/characters/Shingo-KOF98/Shingo_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300,
            12: 10, 13: 12, 14: 40, 15: 42, 16: 43,
            17: 47, 18: 5120,
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 132, 30: 150,
            # get-hit anim slots (AnimTab indices, not real states) --
            # shared anims: KOF hit reactions differ only cosmetically
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110,
            93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 5300,  # taunt shows the dizzy pose
            # specials: Aragami/Dokugami (QCF+p), Oniyaki mid (DP+p),
            # Goufu You cmd normal, Hiji Otoshi (QCF+k), Nie Togi (DP+k),
            # Oboroguruma mid (QCB+k), Shingo Kick (HCB+k)
            48: 1000, 49: 1010,
            50: 1100, 51: 1110,
            52: 5050, 53: 300,
            54: 1500, 55: 1510,
            56: 5050, 57: 5050,
            58: 1400, 59: 1400,
            60: 1200, 61: 1210, 62: 1300, 63: 1310,
            64: 5050, 65: 5050, 66: 5050, 68: 5050,
            67: 250,
            69: 720,
            94: 710, 95: 700,   # FUSION roll (L+dir) / extra dodge (L)
            96: 750, 97: 760,   # MAX burst / manual charge
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 250, 76: 5000, 77: 5050,
            #   75 = blowback anim as a zero-cost throw fake
            # MAX supers ride the spare parry slots (3050/3150 share the
            # base anims 3000/3150 -- no separate AIR actions)
            78: 3150, 79: 3000, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            # supers: Kakehourin weak/strong + MAX, Burning Shingo w/s
            # (strong/MAX reuse anim 3000 like their statedefs do)
            85: 3000, 86: 3000, 87: 3000, 88: 3100, 89: 3110,
            90: 181, 91: 170, 92: 191,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1100, 51: 1110,
                  53: 300, 54: 1500, 55: 1510,
                  58: 1400, 59: 1400,
                  60: 1200, 61: 1210, 62: 1300, 63: 1310,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  78: 3150, 79: 3050,
                  85: 3000, 86: 3010, 87: 3050, 88: 3100, 89: 3110,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "damage_scale": 2.0,
        # FUSION: MAX burst spends one 1000 stock (the mugen
        #   statedef PowerAdd is var-gated and does not extract)
        "pow_override": {96: -1000},
        # sids 50/51 ride StAirSpec: kind-1 lands into S_LAND on descent,
        # kind-0 frees a move that never left the ground
        "extra_trans": [(50, 17, 1, 0), (50, 0, 0, 0),
                        (51, 17, 1, 0), (51, 0, 0, 0)],
        "display": "SHINGO",
    },
    # Rugal Bernstein (KOF'98, boss).
    "rugal": {
        "sff": "assets/characters/Rugal-KOF98/Rugal.sff",
        "air": "assets/characters/Rugal-KOF98/Rugal.air",
        "cns": "assets/characters/Rugal-KOF98/Rugal_SNES.cns",
        "cmd": "assets/characters/Rugal-KOF98/Rugal_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300,
            12: 10, 13: 12, 14: 40, 15: 42, 16: 43,
            17: 47, 18: 5120,
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110,
            93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 5300,
            # specials: Reppuken (QCF+p), Genocide Cutter (DP+k),
            # Double Tomahawk cmd normal, Dark Barrier (QCF+k),
            # God Press (QCB+p), Gravity Smash + Vanishing Rush (QCB/HCB+k),
            # Kaiser Wave (HCBF+p)
            48: 1000, 49: 1010,
            50: 1200, 51: 1210,
            52: 300, 53: 300,             # 305 reuses anim 300 per statedef
            54: 1300, 55: 1310,
            56: 5050, 57: 5050,
            58: 1400, 59: 1410,
            60: 1500, 61: 1550, 62: 1600, 63: 1610,
            64: 1100, 65: 1100, 66: 5050, 68: 5050,
            67: 250,
            69: 720,
            94: 710, 95: 700,   # FUSION roll (L+dir) / extra dodge (L)
            96: 750, 97: 760,   # MAX burst / manual charge
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 250, 76: 5000, 77: 5050,
            #   75 = blowback anim as a zero-cost throw fake
            # MAX supers + Excursion ride the spare parry slots
            78: 3150, 79: 3200, 80: 3210, 81: 3250,
            82: 720, 83: 720, 84: 47,
            # supers: Gigantic Pressure w/s + MAX, Dead End Screamer w/s
            85: 3000, 86: 3010, 87: 3050, 88: 3100, 89: 3110,
            90: 181, 91: 170, 92: 190,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1200, 51: 1210,
                  52: 305, 53: 300, 54: 1300, 55: 1310,
                  58: 1400, 59: 1410,
                  60: 1500, 61: 1550, 62: 1600, 63: 1610,
                  64: 1100, 65: 1110,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  78: 3150, 79: 3200, 80: 3210, 81: 3250,
                  85: 3000, 86: 3010, 87: 3050, 88: 3100, 89: 3110,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "max_dma": 2560,
        "damage_scale": 2.0,
        # FUSION: Reppuken + Kaiser Wave projectiles (same spark-pool scheme)
        # Reppuken 48/49; Kaiser Wave 64/65 (helper 1105's Projectile).
        "projs": {48: (0x0300, 16, 4), 49: (0x0400, 20, 4),
                  64: (0x0400, 24, 4), 65: (0x0C00, 32, 4)},
        # AIR only ships the firing actions; synthesize the MUGEN 1006
        # projectile action from the SFF's Kaiser Wave group (1002).
        "projectile_air": {1006: [(1002, 0, 4), (1002, 1, 4),
                                  (1002, 2, 4), (1002, 3, 4)]},
        # FUSION: MAX burst spends one 1000 stock (the mugen
        #   statedef PowerAdd is var-gated and does not extract)
        "pow_override": {96: -1000},
        # sids 50/51 ride StAirSpec: kind-1 lands into S_LAND on descent,
        # kind-0 frees a move that never left the ground
        "extra_trans": [(50, 17, 1, 0), (50, 0, 0, 0),
                        (51, 17, 1, 0), (51, 0, 0, 0)],
        "msu": True,
        "display": "RUGAL",
    },
    # Omega Rugal: same cmd/cns/air as Rugal (OmegaRugal.def), shirtless
    # sprites from OmegaRugal.sff.  Lives in the main ROM on the banks
    # Rugal vacated; the select screen swaps him in when L+R is held on
    # the Rugal cell (works with or without MSU).
    # Real Omega Rugal (omegarugal98 assets): shirtless body, own
    # AIR/CNS/CMD.  Kept ROM-resident so the hidden boss still works
    # without the MSU-1 data file.
    "omegarugal": {
        'sff': 'assets/characters/omegarugal98/omegarugal98.sff',
        'air': 'assets/characters/omegarugal98/omegarugal98.air',
        'cns': 'assets/characters/omegarugal98/Omega_SNES.cns',
        'cmd': 'assets/characters/omegarugal98/Omega_SNES.cmd',
        "buttons": {'x': 16384, 'y': 64, 'a': 32768, 'b': 128, 'c': 32, 'z': 16},
        "anims": {
            0: 0,
            1: 20,
            2: 21,
            3: 11,
            4: 41,
            9: 5000,
            10: 5050,
            11: 5300,
            12: 10,
            13: 12,
            14: 40,
            15: 42,
            16: 43,
            17: 47,
            18: 5120,
            27: 130,
            28: 131,
            29: 132,
            30: 150,
            42: 150,
            43: 150,
            44: 152,
            31: 5000,
            32: 5000,
            33: 5000,
            34: 5010,
            35: 5010,
            36: 5010,
            37: 5020,
            38: 5020,
            39: 5020,
            40: 5030,
            41: 5110,
            93: 5070,
            70: 5020,
            71: 5030,
            72: 5050,
            73: 5050,
            78: 47,
            79: 47,
            80: 47,
            81: 47,
            82: 47,
            83: 47,
            84: 47,
            90: 180,
            91: 47,
            92: 190,
            25: 630,
            26: 640,
            23: 600,
            24: 610,
            21: 430,
            22: 440,
            19: 400,
            20: 410,
            7: 230,
            8: 240,
            5: 200,
            6: 210,
            47: 195,
            45: 100,
            46: 105,
            74: 800,
            75: 800,
            48: 1000,
            50: 1020,
            51: 1025,
            52: 1030,
            53: 1030,
            54: 1060,
            55: 1060,
            85: 1300,
            49: 1000,
            56: 1216,
            57: 195,
            58: 195,
            59: 1040,
            60: 1040,
            61: 1040,
            62: 1070,
            63: 1070,
            64: 1090,
            65: 1090,
            66: 809,
            86: 1331,
            87: 1346,
            88: 1350,
            89: 8100,
            67: 47,
            68: 47,
            69: 47,
            76: 47,
            77: 47,
            94: 47,
            95: 47,
            96: 47,
            97: 47,
        },
        "moves": {
            90: 181,
            91: 170,
            92: 191,
            76: 5000,
            77: 5050,
            25: 630,
            26: 640,
            23: 600,
            24: 610,
            21: 430,
            22: 440,
            19: 400,
            20: 410,
            7: 230,
            8: 240,
            5: 200,
            6: 210,
            47: 195,
            45: 100,
            46: 105,
            74: 800,
            75: 800,
            48: 1000,
            50: 1020,
            51: 1025,
            52: 1040,
            53: 1045,
            54: 2000,
            55: 2002,
            85: 2800,
            49: 1005,
            56: 2700,
            57: 2899,
            58: 7200,
            59: 1070,
            60: 1085,
            61: 1090,
            62: 2100,
            63: 2200,
            64: 2300,
            65: 2400,
            66: 2600,
            86: 3000,
            87: 6000,
            88: 7000,
            89: 8100,
        },
        "coord_scale": 1,
        "char_scale": 0.81,
        "max_dma": 2560,
        "damage_scale": 0.36,
        "projs": {48: (51, 6, 4), 49: (77, 6, 4),
                  52: (998, 10, 4), 53: (1638, 12, 4),
                  57: (1792, 10, 4), 62: (77, 12, 4),
                  63: (77, 18, 4), 88: (256, 10, 4)},
        # ROM-resident so Omega remains the hidden boss even without the
        # MSU-1 data file.  His CHR fits in the high halves of banks 95-117.
        "display": "O.RUGAL",
    },
    "saisyu": {
        "sff": "assets/characters/Saisyu-KOF98/Saisyu.sff",
        "air": "assets/characters/Saisyu-KOF98/Saisyu.air",
        "cns": "assets/characters/Saisyu-KOF98/Saisyu_SNES.cns",
        "cmd": "assets/characters/Saisyu-KOF98/Saisyu_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 160,
            48: 1000, 49: 1010,  # Yami Barai weak/strong
            50: 1100, 51: 1110,  # Oniyaki weak/strong
            52: 1200, 53: 1210,  # Kamukakari weak/strong
            54: 1300, 55: 1310,  # Nata Guruma weak/strong
            56: 1400, 57: 1410,  # Enju weak/strong            # Tsumugari MAX
            67: 250, 69: 720,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 720, 79: 720, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            85: 3000, 86: 3000,   # Orochinagi w/s/MAX             # Tsumugari w/s
            90: 181, 91: 170, 92: 191,
            94: 710, 95: 700, 96: 750, 97: 760,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1100, 51: 1110,
                  52: 1200, 53: 1210, 54: 1300, 55: 1310,
                  56: 1400, 57: 1410, 
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  85: 3000, 86: 3010, 87: 3050,  89: 3110,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "msu": True,
        "damage_scale": 2.0,
        "projs": {48: (0x0300, 14, 4), 49: (0x0400, 18, 4)},
        "pow_override": {96: -1000},
        "extra_trans": [(50, 17, 1, 0), (50, 0, 0, 0),
                        (51, 17, 1, 0), (51, 0, 0, 0)],
        "display": "SAISYU",
    },
    "heidern": {
        "sff": "assets/characters/Heidern-KOF98/Heidern.sff",
        "air": "assets/characters/Heidern-KOF98/Heidern.air",
        "cns": "assets/characters/Heidern-KOF98/Heidern_SNES.cns",
        "cmd": "assets/characters/Heidern-KOF98/Heidern_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 160,
            48: 1000, 49: 1010,  # Cross Cutter weak/strong
            50: 1100, 51: 1110,  # Moon Slasher weak/strong
            52: 1200, 53: 1200,  # Neck Rolling weak/strong
            54: 1300,            # Storm Bringer
            55: 1400, 56: 1410,  # Killing Bringer weak/strong
            58: 3150,            # Heidern End MAX
            67: 250, 69: 720,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 720, 79: 720, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            85: 3000, 86: 3000, 87: 3000,  # Final Bringer w/s/MAX
            88: 3100, 89: 3110,            # Heidern End w/s
            90: 181, 91: 170, 92: 191,
            94: 710, 95: 700, 96: 750, 97: 760,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1100, 51: 1110,
                  52: 1200, 53: 1210, 54: 1300,
                  55: 1400, 56: 1410, 58: 3150,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  85: 3000, 86: 3010, 87: 3050, 88: 3100, 89: 3110,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "msu": True,
        "damage_scale": 2.0,
        "projs": {48: (0x0300, 14, 4), 49: (0x0400, 18, 4)},
        "pow_override": {96: -1000},
        "extra_trans": [(50, 17, 1, 0), (50, 0, 0, 0),
                        (51, 17, 1, 0), (51, 0, 0, 0)],
        "display": "HEIDERN",
    },
    "takuma": {
        "sff": "assets/characters/Takuma-KOF98/Takuma.sff",
        "air": "assets/characters/Takuma-KOF98/Takuma.air",
        "cns": "assets/characters/Takuma-KOF98/Takuma_SNES.cns",
        "cmd": "assets/characters/Takuma-KOF98/Takuma_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 160,
            48: 1000, 49: 1010,  # Ko-Ou-Ken weak/strong
            50: 1100, 51: 1110,  # Hien Shippuu Kyaku weak/strong
            52: 1200, 53: 1210,  # Zanretsuken weak/strong
            54: 1300, 55: 1310,  # Shouran Kyaku weak/strong
            56: 1700,            # Mouko Burai Gan
            # Shouran Kyaku follow-ups: 60 = grab attempt (1305),
            # 62 = landing recovery (1321), 101 = the held multi-kick
            # sequence (1320).  Slot 101 already exists for the shared
            # counter-grab tables, so the character table keeps its size.
            60: 1305, 62: 1321, 101: 1320,
            58: 3210,            # Ryuuko Ranbu MAX
            67: 250, 69: 720,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 720, 79: 720, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            85: 3000, 86: 3010, 87: 3020,  # Haoh Shikou Ken w/s/MAX
            88: 3100, 89: 3100,            # Ryuuko Ranbu w/s
            90: 181, 91: 170, 92: 191,
            94: 710, 95: 700, 96: 750, 97: 760,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1100, 51: 1110,
                  52: 1200, 53: 1210, 54: 1300, 55: 1310,
                  56: 1700, 58: 3220,
                  60: 1305, 62: 1321, 101: 1320,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  85: 3000, 86: 3010, 87: 3020, 88: 3100, 89: 3120,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "msu": True,
        "damage_scale": 2.0,
        "projs": {48: (0x0300, 14, 4), 49: (0x0400, 18, 4)},
        "pow_override": {96: -1000},
        "extra_trans": [(50, 17, 1, 0), (50, 0, 0, 0),
                        (51, 17, 1, 0), (51, 0, 0, 0)],
        "display": "TAKUMA",
    },
    "clark": {
        "sff": "assets/characters/Clark-KOF98/Clark.sff",
        "air": "assets/characters/Clark-KOF98/Clark.air",
        "cns": "assets/characters/Clark-KOF98/Clark_SNES.cns",
        "cmd": "assets/characters/Clark-KOF98/Clark_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 160,
            48: 1000, 49: 1010,  # Vulcan Punch weak/strong
            50: 1100, 51: 1110,  # Gatling Attack weak/strong
            52: 1200, 53: 1210,  # Mount Tackle weak/strong
            54: 1300, 55: 1310,  # Super Argentine weak/strong
            56: 1400, 57: 1410,  # Frankensteiner weak/strong
            58: 1500, 59: 1510,  # Napalm Stretch weak/strong
            60: 3100,            # Running Three MAX
            67: 250, 69: 720,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 720, 79: 720, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            85: 3000, 86: 3010, 87: 3000,  # Ultra Argentine w/s/MAX
            88: 3100, 89: 3110,            # Running Three w/s
            90: 181, 91: 170, 92: 191,
            94: 710, 95: 700, 96: 750, 97: 760,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1100, 51: 1110,
                  52: 1200, 53: 1210, 54: 1300, 55: 1310,
                  56: 1400, 57: 1410, 58: 1500, 59: 1510,
                  60: 3150,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  85: 3000, 86: 3010, 87: 3050, 88: 3100, 89: 3110,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "msu": True,
        "damage_scale": 2.0,
        "pow_override": {96: -1000},
        "display": "CLARK",
    },
    "ralf": {
        "sff": "assets/characters/Ralf-KOF98/ralf.sff",
        "air": "assets/characters/Ralf-KOF98/ralf.air",
        "cns": "assets/characters/Ralf-KOF98/Ralf_SNES.cns",
        "cmd": "assets/characters/Ralf-KOF98/Ralf_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 202, 7: 204, 8: 206,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 220, 20: 221, 21: 222, 22: 223,
            23: 230, 24: 231, 25: 232, 26: 233,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 195,
            48: 400, 49: 401,    # Vulcan Punch weak/strong
            50: 420, 51: 421,    # Gatling Attack weak/strong
            52: 440, 53: 441,    # Ralf Kick weak/strong
            54: 455,             # air dive
            58: 521, 59: 550, 60: 570,  # extra supers / MAXes
            67: 210, 69: 250,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 300, 75: 300, 76: 5000, 77: 5050,
            78: 251, 79: 251, 80: 251, 81: 251,
            82: 251, 83: 251, 84: 47,
            85: 500, 86: 501,            # Galactica Phantom w/s 88: 510,            # running super w/s                     # QQCF super
            90: 181, 91: 170, 92: 191,
            94: 251, 95: 250, 96: 700, 97: 700,
        },
        "moves": {5: 200, 6: 202, 7: 204, 8: 206,
                  19: 220, 20: 221, 21: 222, 22: 223,
                  23: 230, 24: 231, 25: 232, 26: 233,
                  45: 100, 46: 105, 47: 195,
                  48: 400, 49: 401, 50: 420, 51: 421,
                  52: 440, 53: 441, 54: 455,
                  58: 521, 59: 550, 60: 570,
                  67: 210, 69: 19969, 94: 251, 95: 250, 96: 700,
                  74: 300, 75: 301, 76: 302, 77: 313,
                  85: 500, 86: 501, 87: 510, 88: 511, 89: 520,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "msu": True,
        "damage_scale": 2.0,
        "pow_override": {96: -1000},
        "extra_trans": [(54, 17, 1, 0), (54, 0, 0, 0)],
        "display": "RALF",
    },
    "leona": {
        "sff": "assets/characters/Leona-KOF98/98Leona.sff",
        "air": "assets/characters/Leona-KOF98/98Leona.air",
        "cns": "assets/characters/Leona-KOF98/98Leona_SNES.cns",
        "cmd": "assets/characters/Leona-KOF98/98Leona_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            # Leona's source interleaves the states: x=LP, a=LK, y=HP,
            # b=HK (200/210/220/230 etc.).
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 220, 7: 210, 8: 230,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 400, 20: 420, 21: 410, 22: 430,
            23: 600, 24: 620, 25: 610, 26: 630,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5040, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 195,
            48: 1000, 49: 1001,  # Moon Slasher weak/strong (body, not FX 1010)
            50: 1100, 51: 1101,  # Baltic Launcher weak/strong
            52: 1200, 53: 1201,  # X-Caliber (air) weak/strong
            54: 1400, 55: 1401,  # Grand Saber weak/strong
            56: 1500, 57: 1510,  # Earring Bomb weak/strong
            58: 4020,            # V-Slasher MAX (air)
            67: 240, 69: 310,
            70: 5020, 71: 5040, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 47, 79: 47, 80: 47, 81: 47,
            82: 47, 83: 47, 84: 47,
            85: 4000, 86: 4000,  # V-Slasher w/s (air)
            87: 3100, 88: 3150,  # Rebel Spark w/s
            89: 3300,            # Grateful Dead
            90: 181, 91: 170, 92: 191,
            94: 360, 95: 350, 96: 910, 97: 910,
        },
        "moves": {5: 200, 6: 220, 7: 210, 8: 230,
                  19: 400, 20: 420, 21: 410, 22: 430,
                  23: 600, 24: 620, 25: 610, 26: 630,
                  45: 100, 46: 105, 47: 195,
                  48: 1000, 49: 1001, 50: 1100, 51: 1101,
                  52: 1200, 53: 1201, 54: 1400, 55: 1401,
                  56: 1500, 57: 1510, 58: 3250,
                  67: 240, 69: 310, 94: 360, 95: 350, 96: 910,
                  74: 800, 75: 810, 76: 810, 77: 810,
                  85: 3000, 86: 3001, 87: 3100, 88: 3150, 89: 3300,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.78,
        "msu": True,
        "damage_scale": 2.0,
        "extra_trans": [(52, 17, 1, 0), (52, 0, 0, 0),
                        (53, 17, 1, 0), (53, 0, 0, 0),
                        (85, 17, 1, 0), (85, 0, 0, 0),
                        (86, 17, 1, 0), (86, 0, 0, 0)],
        "display": "LEONA",
    },
    "mature": {
        "sff": "assets/characters/Mature-KOF98/Mature.sff",
        "air": "assets/characters/Mature-KOF98/Mature.air",
        "cns": "assets/characters/Mature-KOF98/Mature_SNES.cns",
        "cmd": "assets/characters/Mature-KOF98/Mature_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 220, 8: 230,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 400, 20: 410, 21: 420, 22: 430,
            23: 600, 24: 610, 25: 620, 26: 630,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 199,
            48: 1000, 49: 1020,  # Ebony Tears weak/strong
            50: 1100, 51: 1100,  # Death Blow weak/strong (AIR 1120 absent)
            52: 1200,            # Metal Massacre
            54: 1300, 55: 1320,  # Despair weak/strong
            56: 1400, 57: 1410,  # Sacrilege weak/strong
            67: 115, 69: 110,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 703, 79: 703, 80: 703, 81: 703,
            82: 703, 83: 703, 84: 47,
            85: 3000, 86: 3010,  # Heaven's Gate w/s
            87: 3500, 88: 3600,  # Nocturnal Rites w/s
            90: 181, 91: 170, 92: 191,
            94: 111, 95: 110, 96: 199, 97: 199,
        },
        "moves": {5: 200, 6: 210, 7: 220, 8: 230,
                  19: 400, 20: 410, 21: 420, 22: 430,
                  23: 600, 24: 610, 25: 620, 26: 630,
                  45: 100, 46: 105, 47: 199,
                  48: 1000, 49: 1020, 50: 1100, 51: 1120,
                  52: 1200, 54: 1300, 55: 1320,
                  56: 1400, 57: 1420,
                  67: 115, 69: 19969, 94: 111, 95: 110,
                  74: 800, 75: 800, 76: 815, 77: 816,
                  85: 3000, 86: 3010, 87: 3500, 88: 3600,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "msu": True,
        "damage_scale": 2.0,
        "display": "MATURE",
    },
    "vice": {
        "sff": "assets/characters/Vice-KOF98/Vice.sff",
        "air": "assets/characters/Vice-KOF98/Vice.air",
        "cns": "assets/characters/Vice-KOF98/Vice_SNES.cns",
        "cmd": "assets/characters/Vice-KOF98/Vice_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 220, 8: 230,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 300, 20: 310, 21: 320, 22: 330,
            23: 500, 24: 510, 25: 520, 26: 530,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 195,
            48: 1200, 49: 1250,  # Deicide Slayer weak/strong
            50: 1300, 51: 1350,  # Mayhem weak/strong
            52: 1400, 53: 1410,  # Black Out weak/strong
            54: 1500, 55: 1510,  # Gore Fest weak/strong
            58: 3000,            # Withering Surface MAX (state 3200)
            67: 600, 69: 4000,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 4100, 79: 4100, 80: 4100, 81: 4100,
            82: 4100, 83: 4100, 84: 47,
            85: 3000, 86: 3000,  # Withering Surface w/s
            87: 3000,            # Withering Surface strong (state 3100)
            88: 3300, 89: 3300,  # Negative Gain w/s
            90: 181, 91: 175, 92: 191,
            94: 4100, 95: 4000, 96: 195, 97: 195,
        },
        "moves": {5: 200, 6: 210, 7: 220, 8: 230,
                  19: 300, 20: 310, 21: 320, 22: 330,
                  23: 500, 24: 510, 25: 520, 26: 530,
                  45: 100, 46: 105, 47: 195,
                  48: 1200, 49: 1250, 50: 1300, 51: 1350,
                  52: 1400, 53: 1410, 54: 1500, 55: 1510,
                  58: 3200,
                  67: 600, 69: 19969, 94: 4150, 95: 4050,
                  74: 800, 75: 810, 76: 810, 77: 810,
                  85: 3000, 86: 3010, 87: 3100, 88: 3300, 89: 3400,
                  90: 181, 91: 175, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "msu": True,
        "damage_scale": 2.0,
        "display": "VICE",
    },
    "benimaru": {
        "sff": "assets/characters/Benimaru-KOF98/Benimaru.sff",
        "air": "assets/characters/Benimaru-KOF98/Benimaru.air",
        "cns": "assets/characters/Benimaru-KOF98/Benimaru_SNES.cns",
        "cmd": "assets/characters/Benimaru-KOF98/Benimaru_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 160,
            48: 1000, 49: 1010,  # Raikouken weak/strong
            50: 1100, 51: 1110,  # Kuuchuu Raikouken weak/strong
            52: 1200, 53: 1210,  # Shinkuu Katategoma weak/strong
            54: 1400, 55: 1410,  # Super Inazuma weak/strong
            56: 1500, 57: 1501,  # Handou Sandan weak/strong
            67: 250, 69: 720,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 720, 79: 720, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            85: 3000, 86: 3010,   # Raikouken super w/s
            90: 181, 91: 170, 92: 191,
            94: 710, 95: 700, 96: 750, 97: 760,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1100, 51: 1110,
                  52: 1200, 53: 1210, 54: 1400, 55: 1410,
                  56: 1500, 57: 1510,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  85: 3000, 86: 3010, 87: 3050, 89: 3100,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "damage_scale": 2.0,
        "projs": {48: (0x0300, 14, 4), 49: (0x0400, 18, 4),
                  50: (0x0300, 14, 4), 51: (0x0400, 18, 4)},
        "pow_override": {96: -1000},
        "extra_trans": [(50, 17, 1, 0), (50, 0, 0, 0),
                        (51, 17, 1, 0), (51, 0, 0, 0)],
        "display": "BENIMARU",
    },
    "daimon": {
        "sff": "assets/characters/Daimon-KOF98/Daimon.sff",
        "air": "assets/characters/Daimon-KOF98/Daimon.air",
        "cns": "assets/characters/Daimon-KOF98/Daimon_SNES.cns",
        "cmd": "assets/characters/Daimon-KOF98/Daimon_SNES.cmd",
        "buttons": {"x": 0x4000, "y": 0x0040,
                    "a": 0x8000, "b": 0x0080,
                    "c": 0x0020, "z": 0x0010},
        "anims": {
            0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
            5: 200, 6: 210, 7: 230, 8: 240,
            9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12,
            14: 40, 15: 42, 16: 43, 17: 47, 18: 5120,
            19: 400, 20: 410, 21: 430, 22: 440,
            23: 600, 24: 610, 25: 630, 26: 640,
            27: 130, 28: 131, 29: 132, 30: 150,
            31: 5000, 32: 5000, 33: 5000,
            34: 5010, 35: 5010, 36: 5010,
            37: 5020, 38: 5020, 39: 5020,
            40: 5030, 41: 5110, 93: 5070,
            42: 150, 43: 151, 44: 152,
            45: 100, 46: 105, 47: 160,
            48: 1000, 49: 1010,  # Jiraishin weak/strong
            50: 1100, 51: 1110,  # Chou Ukemi weak/strong
            52: 1200, 53: 1300,  # Kumo Tsukami / Kirikabu Gaeshi
            54: 1500, 55: 1500,  # Ura Nage weak/strong
            56: 1700, 57: 1710,  # Chou Oosotogari weak/strong
            67: 250, 69: 720,
            70: 5020, 71: 5030, 72: 5050, 73: 5050,
            74: 800, 75: 800, 76: 5000, 77: 5050,
            78: 720, 79: 720, 80: 720, 81: 720,
            82: 720, 83: 720, 84: 47,
            85: 3000, 86: 3010,   # Jigoku Gokuraku w/s
            90: 181, 91: 170, 92: 191,
            94: 710, 95: 700, 96: 755, 97: 760,
        },
        "moves": {5: 200, 6: 210, 7: 230, 8: 240,
                  19: 400, 20: 410, 21: 430, 22: 440,
                  23: 600, 24: 610, 25: 630, 26: 640,
                  45: 100, 46: 105, 47: 160,
                  48: 1000, 49: 1010, 50: 1100, 51: 1110,
                  52: 1200, 53: 1300, 54: 1500, 55: 1510,
                  56: 1700, 57: 1700,
                  67: 250, 69: 720, 94: 710, 95: 700, 96: 750, 97: 760,
                  74: 800, 75: 810, 76: 815, 77: 816,
                  85: 3000, 86: 3010, 87: 3050, 89: 3100,
                  90: 181, 91: 170, 92: 191},
        "coord_scale": 1,
        "char_scale": 0.81,
        "damage_scale": 2.0,
        "pow_override": {96: -1000},
        "display": "DAIMON",
    },
}

# Keep generated and hand-maintained character configs on the requested
# SNES face-button layout: Y=weak punch, X=strong punch, B=weak kick,
# A=strong kick.  The fight engine's JOY_* constants use these same labels.
for _cfg in CHARS.values():
    _cfg["buttons"].update({"x": 0x4000, "y": 0x0040,
                            "a": 0x8000, "b": 0x0080})

# 8 MiB fallback build: KOF_BASE4=1 drops the extra chars back to the
# original roster (Kyo/Iori/Shingo/Rugal).  Default build: 14 chars --
# kyo/iori/shingo/rugal/benimaru/daimon in the 8 MiB ROM at 0.85,
# the other eight streamed from kof98-snes.msu.
if os.environ.get("KOF_BASE4"):
    for _c in ("saisyu", "heidern", "takuma", "clark",
               "ralf", "leona", "mature", "vice",
               "benimaru", "daimon", "omegarugal"):
        del CHARS[_c]

# ROM budget: keep each new char to a single super pair (sids 85/86) --
# the second supers and MAX variants (58, 87-89) are unwired; their states
# stay in the _SNES.cmd but get no sid, so the matcher skips them.
# Mature and Vice are the exception: their second supers/MAX variants are
# calibrated and wired below, so keep 58/87-89 for them.
for _c in ("saisyu", "heidern", "takuma", "clark",
           "ralf", "leona", "mature", "vice",
           "benimaru", "daimon"):
    if _c not in CHARS or _c in ("mature", "vice"):
        continue
    keep = {60, 62} if _c == "takuma" else set()
    for _sid in (58, 59, 60, 61, 62, 63, 64, 65, 66, 87, 88, 89):
        if _sid in keep:                 # Shouran Kyaku follow-ups
            continue
        CHARS[_c]["moves"].pop(_sid, None)
        CHARS[_c]["anims"].pop(_sid, None)

# The new chars leave unused sids (rekka slots, 68, trimmed supers, ...)
# without an anim entry; AnimTab is a dense table, so fill the holes with
# the land anim, which exists in every one of these .air files.
for _c in ("saisyu", "heidern", "takuma", "clark",
           "ralf", "leona", "mature", "vice",
           "benimaru", "daimon"):
    if _c not in CHARS:
        continue
    for _sid in range(98):
        CHARS[_c]["anims"].setdefault(_sid, 47)

# --- projectile reflectors -------------------------------------------------
# (sid, start_tick, end_tick, x0, y0, x1, y1) in fighter-relative pixels.
# The box is forward-relative (mirrored by facing); y is relative to the
# fighter's feet.  end=255 means no cut-off.  The runtime scans this table
# before a projectile hit, so every character with a reflection window is
# data, not a special case in the engine.
# False positives from the helper/ChangeState projectile heuristic.  Keep
# the move itself, but drop the invisible travelling shot the generator
# inferred from a follow-up dash HitDef.
PROJECTILE_EXCLUDE = {
    # Zan'eiken's close-range HitDefs are melee, not travelling shots.  The
    # follow-up states (1001/1011 and their 1005/1015 chain) were being
    # compiled as invisible projectiles by the HitDef heuristic.
    "andy": (50, 51, 54, 55),
    # Nocturnal Rites (3500/3600) is a melee rush.  Its 3501/3601 follow-up
    # HitDefs carry a dash velocity but no p1/p2 bind, so the same heuristic
    # invented a travelling flame projectile; keep the move, drop the shot.
    "mature": (87, 88),
    # Heavy D!'s moving specials chain into hit states with a VelSet; the
    # heuristic turned R.S.D., Ducking Combination and D. Crazy into bogus
    # fireballs.  Only D. Magnum (87/88, calibrated in projectiles.py) is a
    # real projectile.
    "heavyd": tuple(s for s in range(48, 87)) + (89,),
    # Brian has no projectile at all: every special/super is melee or a
    # throw.  Keep the follow-up HitDefs from becoming travelling shots.
    "brian": tuple(range(48, 90)),
    # Billy's wired DP follow-ups (1505/1525) are spinning-staff melee
    # states.  The heuristic turned their dash HitDefs into invisible shots.
    "billy": (50, 53),
    # Benimaru's Handou Sandan follow-ups are melee; only the Raikouken
    # states (48-51, explicit rows) throw the electric ball.
    "benimaru": (56, 57),
    # Choi, Kim, Mary, Vega and Yashiro have no travelling projectile in
    # their wired move set.  Their follow-up HitDefs/dashes were being
    # compiled as invisible shots.
    "choi": (50, 51, 86),
    "kim": (53, 85, 86),
    "mary": (54, 55, 87),
    "vega": (48, 49, 52, 53, 85, 86),
    "yashiro": (48, 49, 85, 86),
    # Chris' Glider/Hunting moves are dives and rushes; their wind Explods
    # are not projectiles.
    "chris": (50, 55, 56, 57, 58, 59),
    # Leona: keep the Baltic Launcher (50/51) and drop X-Caliber, Grand
    # Saber and V-Slasher follow-up dashes.
    "leona": (52, 53, 54, 55, 85, 86),
    # Mr. Big: keep Ground Blaster (54/55); the rest are stick pokes and
    # the melee super.
    "mrbig": (48, 49, 52, 85, 86),
    # Eiji: keep the super shot (85/86); special_52/53 are teleport/dash
    # follow-ups.
    "eiji": (52, 53),
    # Geese: 53 (state 1210) is the HCB+P dash whose follow-up HitDef was
    # inferred as a travelling shot; the move itself is melee.  The air
    # Shippuu Ken (58/state 1100) is a real helper projectile (1103) and must
    # stay wired.  Keep the EX Reppuken (62/state 1050).
    "geese": (53, 54, 57),
    # Robert's Ryuga anti-airs (states 1100/1110) chain into the airborne
    # follow-ups 1101/1111, whose HitDef inherits the jump VelSet (2,-6 and
    # 6,-8.5).  The heuristic read those follow-ups as travelling shots, so
    # both DP+P moves spawned an invisible projectile on top of the kick.
    "robert": (50, 51),
}

REFLECTORS = {
    # Athena's ground Reflective Shields (states 1040/1050): the source
    # HitOverride helper sits at +30,-75 and lives for the whole state.
    "athena": [(50, 0, 255, 8, -105, 76, -10),
               (51, 0, 255, 8, -105, 76, -10)],
    # Rugal's Dark Barrier (states 1300/1310) spawns a reflection helper at
    # +72,-56.  It appears on tick 11 (weak) / 14 (strong) and disappears
    # when the state ends on tick 27 / 46.
    "rugal": [(54, 11, 27, 48, -100, 96, -12),
              (55, 14, 46, 48, -100, 96, -12)],
}

# --- mass MSU import ------------------------------------------------------
# Generated spec from tools/gen_char_cfg.py (tools/newroster.py).  All of
# these stream tiles from kof98-snes.msu; only the tables live in ROM.
# Supers dropped by the ROM diet below can be restored after calibration:
# the generated command table already carries their [State -1] entries, and
# re-adding them after apply_profile keeps existing profile hashes valid.
POST_CAL_SUPERS = {}
# Source packages whose state names are too generic/absent for the automatic
# MAX/SDM detection.  Values are the sid slots (85-89) that need the MAX
# window; every other super is an ordinary 1-stock move.
MAX_SIDS_OVERRIDE = {
    # Omega Rugal's ude/gia inputs are the source's MAX-only experiments;
    # jibaku (87) stays a normal super.
    "omegarugal": (88, 89),
    # Ryu's 88 is the explicit MAX hadouken.  87 is wired as the normal
    # QCBx2 kick super even though the source state has the SDM cost shape.
    "ryu": (88,),
}
# name -> byte mask, bit0 = sid85 ... bit4 = sid89.
MAX_MASKS = {}


def max_sid_mask(sids):
    mask = 0
    for sid in sids:
        if 85 <= sid <= 89:
            mask |= 1 << (sid - 85)
    return mask & 0x1F


POST_CAL_SUPER_CHARS = {
    "chin", "chunli", "geese", "joe", "ken",
    "krauser", "mai", "mary", "yamazaki",
}
# Time-over loser pose fallbacks for imports whose anim 170 is missing.
POST_CAL_LOSE_ANIM = {"joe": 5300, "omegarugal": 5300, "yamazaki": 5300}
# Those fallbacks reuse an animation that another sid already emits; give
# sid 91 its own AnimTab body so the 255-tick hold survives deduplication.
POSE_UNIQUE_ANIM_SIDS = {_n: (91,) for _n in POST_CAL_LOSE_ANIM}
try:
    from newroster import NEW_CHARS
except ImportError:
    NEW_CHARS = {}
for _c, _cfg in NEW_CHARS.items():
    if os.environ.get("KOF_BASE4") or _c in CHARS:
        continue
    # same ROM diet as the other new chars: drop MAX/second supers.
    # Yuri's package has distinct weak/strong super states (500/501 and
    # 510/511), so keep her 87 slot; sid 66 carries the strong second DM
    # because 88/89 are the engine's MAX/SDM slots.  The extra tables are
    # small and the sprites are already streamed from MSU-1.
    # Ryu keeps 87 (super tatsumaki) and 88 (MAX hadouken); only the unused
    # 89 slot is dropped.
    if _c == "ryu":
        _drop = (89,)
    elif _c == "yuri":
        _drop = (88, 89)
    elif _c == "lucky":
        # Keep 87 for the follow-up fadeaway state 2100.  The basketball is
        # a helper HitDef there, not a Projectile controller, so the native
        # row is added in PROJECTILE_CALIBRATION below.
        _drop = (88, 89)
    elif _c == "heavyd":
        # 87/88 are D. Magnum weak/strong (state 2105 + projectile 2120).
        # Dropping them was why Heavy D! had no projectile at all.
        _drop = ()
    elif _c == "brian":
        # 87/88 are the direct Galaxy Cyclone / Big Bang Tackle hit states
        # and 89 is the strong Supernova follow-up (3055).
        _drop = ()
    elif _c == "vega":
        # Final Psycho Crusher (3050) and MAX Knee Press Nightmare (3150)
        # are part of Vega's move list; 89 is unused.
        _drop = (89,)
    else:
        _drop = (87, 88, 89)
    _saved_supers = {}
    for _sid in _drop:
        if _c in POST_CAL_SUPER_CHARS and _sid in _cfg["moves"]:
            _saved_supers[_sid] = (_cfg["moves"][_sid],
                                   _cfg["anims"].get(_sid))
        _cfg["moves"].pop(_sid, None)
        _cfg["anims"].pop(_sid, None)
    if _saved_supers:
        POST_CAL_SUPERS[_c] = _saved_supers
    for _sid in range(98):
        _cfg["anims"].setdefault(_sid, 47)
    CHARS[_c] = _cfg

# --- restored projectile moves --------------------------------------------
# A few imported fighters keep their travelling shot in a helper state that
# the generic one-level projectile walk cannot reach (or whose command entry
# was dropped by the ROM diet).  Wire the real source state on a free special
# slot so the projectile art in PROJECTILE_ACTIONS has something to launch.
# The matching [State -1] rules live in each character's _SNES.cmd on the free
# C button.
EXTRA_PROJECTILE_MOVES = {
    # Hishou Ken.
    "andy": {58: 1150},
    # Jiraishin shockwave.
    "daimon": {58: 300},
    # Light/strong thrown shot.
    "shermie": {58: 7200, 59: 7300},
    # Travelling shot and its super.
    "yamazaki": {58: 1215, 85: 3140},
}
for _c, _extra in EXTRA_PROJECTILE_MOVES.items():
    if _c not in CHARS:
        continue
    for _sid, _state in _extra.items():
        CHARS[_c]["moves"][_sid] = _state
        CHARS[_c]["anims"][_sid] = _state
    for _sid in range(98):
        CHARS[_c]["anims"].setdefault(_sid, 47)

# Share Yuri's six-cel Ko'ou Ken with the rest of the Kyokugen team.  The
# alias skips compiling their shorter/older effect atlases and points the
# runtime descriptor (and verify_chars) at Yuri's generated ProjFx table.
for _c, _src in PROJECTILE_FX_ALIAS.items():
    if _c in CHARS and _src in CHARS:
        CHARS[_c]["projfx_alias"] = _src

# Lucky's SHOOT special (state 2099, wired on sid 66) follows up with the
# fadeaway shot state 2100.  The basketball lives in helper states 2101/
# 2102/2103 (an anim+HitDef, not a Projectile controller), so wire state
# 2100 on sid 87 and let PROJECTILE_CALIBRATION spawn the native projectile
# at that animation's release.  The source exits to landing state 1066,
# which is not a runtime sid: land into stand instead of freezing on the
# hold frame.
if "lucky" in CHARS:
    CHARS["lucky"]["moves"][87] = 2100
    CHARS["lucky"]["anims"][87] = 2100
    CHARS["lucky"].setdefault("extra_trans", []).append((87, 0, 1, 0))
    # DP+kick also completes the existing DP special; try the SHOOT rule
    # first so the basketball wins the input.
    CHARS["lucky"]["cmd_priority"] = ["SHOOT"]
    CHARS["lucky"]["cmd_labels"] = {66: "BASKETBALL"}
    # The command-list button labels are globally inverted; show the input
    # the pad actually needs for the new move: forward, down, down-forward, Y.
    CHARS["lucky"]["cmd_text"] = {66: "DP+Y"}

# Blue Mary: restore the multi-phase specials and give the grab follow-ups a
# runtime state.  The generated import only wired the root statedefs, so every
# ChangeState that waited for an animation element was dropped (TransTab only
# carries anim-end, landing, command and MoveHit rules).  The fighter then sat
# on the AIR trailing 255-tick hold -- roughly 4.2 seconds of recovery -- while
# Vertical Arrow never left the ground and Goodnight's throw follow-up never
# played.  Slots 107+ are free: all roster entries stop at 102 and 103-106 are
# the ReversalDef follow-ups.
if "mary" in CHARS:
    _mary = CHARS["mary"]
    _mary["moves"].update({107: 1101, 108: 1111, 109: 1305,
                           110: 1910, 111: 4010})
    # Reuse the throw cels already resident from the counter-grab states
    # instead of importing the source-only 1305/1910/4010 sequences.  The
    # follow-up logic (target binds, damage and frame events) comes from the
    # statedef tables, so the drawn cels are interchangeable.
    _mary["anims"].update({107: 1111, 108: 1111, 109: 1505,
                           110: 1505, 111: 1525})
    # Both Vertical Arrow air states launch through a `Time = [0,5]` VelSet
    # controller, which the native extractor cannot represent.  Apply the
    # source launch velocity on state entry instead.
    _mary["state_vel"] = {107: (3.6, -5.4), 108: (4.7, -7.5)}
    # The 1110 startup clip ends with a t=255 hold.  Trim it so the animation
    # reaches its end and TransEnd hands over to the air phase (107/108).
    _mary["tail_ticks"] = {1110: 1}
    # The import's intro pose at element 17 is a wide double cel; the current
    # presenter stalls on it (global freeze, independent of these states).
    # End the intro on the preceding pose so the round can start.
    _mary["frame_cap"] = {92: 16}
    _mary.setdefault("extra_trans", []).extend([
        (54, 107, 0, 0), (55, 108, 0, 0),    # Vertical Arrow -> air phase
        (107, 17, 1, 0), (108, 17, 1, 0),    # Vertical Arrow air -> land
        (59, 17, 1, 0), (60, 17, 1, 0),      # Spinfall -> land
        (56, 17, 1, 0), (57, 17, 1, 0),      # Spider attempt -> land
        (49, 17, 1, 0),                     # Typhoon whiff -> land
    ])

# Ken: the strong Shoryuken (MUGEN state 1110, sid 53) is a three-HitDef
# sequence (ground uppercut, rising uppercut, launcher with fall=1).  The
# generated row kept only one HitDef, so the move landed once and never
# knocked down.  Split the AIR 1110 timeline into three runtime sids the
# same way the generated supers split their animations; each slice gets its
# own HitDef row and the anim-end chain reaches the next one.  Damage is
# spread over the three contacts so the total stays at the single-hit strong
# special value instead of tripling it.
if "ken" in CHARS:
    _ken = CHARS["ken"]
    _ken["moves"].update({58: 1110, 59: 1110, 60: 1111})
    _ken["anims"].update({53: 1110, 58: 1110, 59: 1110, 60: 1111})
    _ken["slices"] = {
        53: (1110, 0, 4),       # startup + first uppercut (HitDef 0)
        58: (1110, 5, 5),       # rising uppercut (HitDef 1)
        59: (1110, 6, 18),      # airborne launcher + recovery hold
    }
    _ken["slice_hits"] = {53: (0, 58), 58: (1, 59), 59: (2, 60)}
    _ken["slice_damage"] = {53: 8, 58: 8, 59: 8}

# Sakura: the strong Shou'ou Ken (MUGEN state 1110, sid 49) also carries
# three HitDefs, and the native tables kept only the first one.  Split the
# AIR 1110 timeline into five runtime sids so the anti-air registers five
# separate contacts.  The first two slices reuse the low hit, the middle two
# the rising hit and the last slice keeps the source launcher (fall=1).
# Damage is spread over the five slices so the whole combo totals the same
# 26 points as Sakura's normal strong punch (sid 6) instead of tripling the
# single-hit special.  Each slice gets an entry velocity because EnterState
# applies the source header's velset=0,0; without it the fighter would stop
# moving forward between the hit slices.
if "sakura" in CHARS:
    _sakura = CHARS["sakura"]
    _sakura["moves"].update({60: 1110, 61: 1110, 62: 1110, 63: 1110})
    _sakura["anims"].update({60: 1110, 61: 1110, 62: 1110, 63: 1110})
    _sakura["slices"] = {
        49: (1110, 0, 3),      # startup + first grounded hit
        60: (1110, 3, 4),      # second contact (replays the first hit cel)
        61: (1110, 5, 5),      # third contact (rising hit)
        62: (1110, 5, 6),      # fourth contact (replays the rising hit cel)
        63: (1110, 7, 13),     # launcher + recovery/landing hold
    }
    _sakura["slice_hits"] = {49: (0, 60), 60: (0, 61),
                             61: (1, 62), 62: (1, 63), 63: (2, 56)}
    # Raw values account for the engine's KOF combo decay (by the time of
    # each hit the counter already reads 0/1/2/3/4): the five contacts
    # remove exactly the 26 HP a normal strong punch costs in one hit.
    _sakura["slice_damage"] = {49: 6, 60: 5, 61: 5, 62: 5, 63: 6}
    _sakura["state_vel"] = {60: (6, 0), 61: (6, 0),
                            62: (6, 0), 63: (8, -10)}
    _sakura.setdefault("extra_trans", []).append((63, 56, 1, 0))

# ReversalDef counter-grab follow-ups (p1stateno/p2stateno) share four
# runtime slots: 99/100 for the high/mid counter (actor/held opponent) and
# 101/102 for the low counter.  Wiring both MUGEN states into "moves" makes
# RevTab carry the victim sid and lets the actor's TargetState/TargetLifeAdd
# rows resolve at build time.  Without this a ReversalDef only parries: the
# opponent gets the blocked pose instead of being grabbed and thrown.
# Each row is (p1 follow-up state, p2 held state, actor animation).
# Daimon (1400) and Krauser (1600) also carry a source counter stance, but
# their QCB+X stance never reached the port's command table, so it is not
# listed here until that stance gets a runtime slot.
COUNTER_GRAB_STATES = {
    "geese":   {"hi": (1410, 1411, 1410), "lo": (1420, 1421, 1420)},
    "heidern": {"hi": (1420, 1430, 1420)},
    "mary":    {"hi": (1505, 1510, 1505)},
    "takuma":  {"hi": (1705, 1706, 1705)},
}
# Added after calibration.native.apply_profile: Mary's profile was verified
# with slots 99/100 only, and its config hash must stay unchanged.  New
# slots do not touch any calibrated HitDef, so wiring them afterwards is safe.
COUNTER_GRAB_POST_CAL = {
    "mary": {"lo": (1525, 1530, 1525)},
}
_COUNTER_GRAB_SLOTS = {"hi": (99, 100), "lo": (101, 102)}


def wire_counter_grabs(cfg, rows):
    for _height, (_p1, _p2, _anim) in rows.items():
        _asid, _vsid = _COUNTER_GRAB_SLOTS[_height]
        cfg["moves"].setdefault(_asid, _p1)
        cfg["moves"].setdefault(_vsid, _p2)
        cfg["anims"].setdefault(_asid, _anim)


# ReversalDef states that only have p1stateno (a counter-attack, no p2 held
# state) need their follow-up wired as a runtime state too.  Without a slot
# the RevTab row carries $FF and the engine used to jump to state 255 when
# the parry connected.  These four slots dispatch through StSpecial in
# StateTab, exactly like a regular ground special.
REVERSAL_ACTOR_SLOTS = (103, 104, 105, 106)


def wire_reversal_followups(cfg, anims, air, cns_headers, cns_statedefs,
                            cns_reversals):
    """Map reachable ReversalDef p1stateno states onto free runtime sids."""
    state_to_sid = {}
    for sid, state in sorted(cfg.get("moves", {}).items()):
        state_to_sid.setdefault(state, sid)
    wired = {}
    for stance, (_win, actor_state, _cls, _victim) in sorted(
            cns_reversals.items()):
        if stance not in state_to_sid or actor_state < 0:
            continue                       # stance not reachable in the port
        if actor_state in state_to_sid:
            continue                       # follow-up already has a state
        hdr = cns_headers.get(actor_state)
        if not hdr or actor_state not in cns_statedefs:
            continue
        # U/L are helper/spawn states (Chizuru's clone counter); they have no
        # fighter pose and must not become the player's state.
        if (hdr.get("type") or "S").strip().upper() not in ("S", "C"):
            continue
        try:
            anum = int(hdr.get("anim", "-1"))
        except (TypeError, ValueError):
            continue
        if anum not in air:
            continue
        slot = next((s for s in REVERSAL_ACTOR_SLOTS
                     if s not in cfg.get("moves", {})), None)
        if slot is None:
            print(f"{cfg.get('display', '?')}: no free ReversalDef "
                  f"follow-up slot for state {actor_state}")
            break
        cfg.setdefault("moves", {})[slot] = actor_state
        cfg.setdefault("anims", {})[slot] = anum
        anims[slot] = anum
        state_to_sid[actor_state] = slot
        wired[stance] = slot
    return wired


for _c, _rows in COUNTER_GRAB_STATES.items():
    if _c in CHARS:
        wire_counter_grabs(CHARS[_c], _rows)

# --- Kyo KOF'98 EX variants ------------------------------------------------
# Nests and Ash share the base Kyo moveset/CNS/CMD; only their SFF, AIR and
# default ACT palette differ.  Clone the hand-tuned Kyo tables so every
# special, super, projectile, throw and chain stays identical, and stream the
# variant's tiles from the MSU-1 file.  They are hidden roster entries: the
# select screen reaches them with L/R on the Kyo cell.
_KYO_VARIANTS = {
    "kyonests": {
        "sff": "assets/characters/Kyo-KOF98/Nests/Kyo.sff",
        "air": "assets/characters/Kyo-KOF98/Nests/Kyo.air",
        "palette_act": "assets/characters/Kyo-KOF98/Nests/act/act01.act",
        "display": "KYO",
    },
    "kyoash": {
        "sff": "assets/characters/Kyo-KOF98/Ash/Kyo.sff",
        "air": "assets/characters/Kyo-KOF98/Ash/Kyo.air",
        "palette_act": "assets/characters/Kyo-KOF98/Ash/act/act01.act",
        "display": "KYO",
    },
}
for _key, _ov in _KYO_VARIANTS.items():
    _cfg = copy.deepcopy(CHARS["kyo"])
    _cfg.update(_ov)
    _cfg["cns"] = "assets/characters/Kyo-KOF98/Kyo_SNES.cns"
    _cfg["cmd"] = "assets/characters/Kyo-KOF98/Kyo_SNES.cmd"
    _cfg["msu"] = True
    _cfg["hidden"] = True
    # The variant's flame effect is the same asset as base Kyo's; share the
    # generated ProjFx tables/graphics instead of spending two more 4 KiB
    # ROM windows on identical atlases.
    _cfg["projfx_alias"] = "kyo"
    CHARS[_key] = _cfg

if "terry" in CHARS:
    # Terry's 2.8 KB poses take ~15 VBlanks via the MSU byte port, longer
    # than a normal attack. Keep his CHR in ROM for the regular DMA path.
    CHARS["terry"]["msu"] = False
    CHARS["terry"]["projs"] = {
        58: (0x0300, 22, 4),  # weak Power Wave (state 1000)
        59: (0x0400, 26, 4),  # strong Power Wave (state 1010)
        # Power Geyser (states 3000/3010) is the source's stationary helper
        # pillar, not a travelling shot.  vx=0 keeps it in front of Terry;
        # bits 2/3-7 of the generated present byte select the geyser clip and
        # delay it to AnimElem 7 (the ground punch).
        85: (0x0000, 26, 4, 2),
        86: (0x0000, 30, 4, 2),
    }

CELL = 16
# Old-roster fighters whose generated tables live in hand-mapped fixed
# windows (fight.asm).  Their metasprite blob is split into _meta.inc so the
# restored AIR frames do not push the table section past that window; the
# descriptor already resolves CH_MBANK through the SprData label.
SPLIT_OLD = ("vice", "mature", "leona", "ralf")
CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:!?'-/+>,@\""

# Victory-quote languages.  The first item is the JSON file name, the second
# the runtime/label tag.  Q_LANG indexes this list, so keep the order stable
# (0 = English, 1 = Portuguese, 2 = Spanish, 3 = French).
QUOTE_LANGS = (("en", "en"), ("pt-BR", "pt"), ("es", "es"), ("fr", "fr"))
QUOTE_DIR = os.path.join(ROOT, "assets", "data", "quotes")
_QUOTE_DB = None
# Unique quote strings collected while build_char runs.  Each language gets
# its own generated include so the packer can drop them into free windows;
# QuoteTab entries are 24-bit far pointers (.dl) into these sections.
QUOTE_STRINGS = {tag: [] for _fname, tag in QUOTE_LANGS}
# Per-character 16-pair tables (4 languages x 4 quotes, 24-bit far pointers).
# They live in one shared section so tight character banks only keep their
# gameplay tables; the descriptor's CH_QUOTE field holds the low address.
QUOTE_TABLES = []
# Per-character 7-8 byte name strings.  They also live in the shared tables
# bank; select/HUD name draws override the descriptor bank after CharPtr.
CHAR_NAMES = []

# Sid 97 is a universal charge, even when the original character has no
# state 760.  None keeps a real charge action; an index freezes one selected
# neutral/power-up pose instead of playing a roll, taunt or stand fallback.
CHARGE_ANIMS = {
    "ralf": (700, 0), "leona": (910, 0),
    "mature": (199, 4), "vice": (700, 0),
    "athena": (911, None), "kensou": (700, None),
    "shermie": (700, None), "chris": (700, None),
    "billy": (3101, None), "lucky": (704, None),
    "chin": (911, 0), "king": (195, 0), "mai": (195, 0),
    "chizuru": (195, 0), "chang": (900, 0),
    "choi": (195, 0), "mary": (195, 0),
    "heavyd": (199, 5), "brian": (195, 6), "yuri": (195, 0),
}


def charge_frames(name, air, default_action):
    action, element = CHARGE_ANIMS.get(name, (default_action, None))
    frames, loopstart = air[action]
    if element is not None:
        frames, loopstart = [frames[element]], 0
    # Charging cannot hit, even when its stance borrows a combat action.
    frames = [(g, n, x, y, 255 if len(frames) == 1 else t,
               flip, [], hurt) for g, n, x, y, t, flip, _atk, hurt
              in frames]
    return frames, loopstart

# MUGEN custom states are remapped into the compact byte-sized runtime state
# space. These four form the fast-palm victim chain (1025 -> 1028).
VICTIM_STATE_IDS = {1025: 70, 1026: 71, 1027: 72, 1028: 73,
                    820: 76, 821: 77,
                    # Kyo throw victims: held pose -> S_VHELD, thrown flight
                    # -> S_VTHROW (815/816 from the C throw, 825/826 from D)
                    815: 76, 816: 77, 825: 76, 826: 77,
                    # Iori Kuzukaze (1400) victims swap to held/thrown too
                    1410: 76, 1420: 77}

# Runtime SFX ids -- kept in sync with the SAMPLES order in
# tools/build_audio.py (spc_ids.inc is generated from that list).
CHAR_VOICES = {}                        # name -> {(snd group,item): voice id}
VOICE_BASE = 40                         # op7 arg >= this -> streamed voice

SND_TO_SFX = {                          # character .snd (group,item) -> id
    (0, 0): 0, (0, 1): 1, (0, 4): 1,   # weak / strong punch swish
    (1, 1): 14,                         # grab whiff
    (800, 0): 15,                       # throw slam
    (100, 0): 16,                       # dash whoosh
    (40, 0): 8,                         # landing
}
HIT_SND = {0: 4, 1: 5, 2: 6, 3: 18, 4: 19}   # common.snd group 5 -> id
# PlaySnd's F prefix selects the common sound bank (not fight.snd).  The
# announcer clips are dispatched directly by the round system.
COMMON_SND = {(5, 0): 4, (5, 1): 5, (5, 2): 6, (5, 3): 18,
              (5, 4): 19, (6, 0): 7, (7, 0): 20}


def div_coord(v, scale):
    if scale == 1:
        return v
    if v % scale:
        raise ValueError(f"coordinate {v} is not divisible by {scale}")
    return v // scale


def scale_air_frames(frames, scale):
    if scale == 1:
        return frames
    out = []
    for g, n, x, y, t, flip, atk, hurt in frames:
        out.append((g, n, div_coord(x, scale), div_coord(y, scale),
                    t, flip,
                    [tuple(div_coord(v, scale) for v in box)
                     for box in atk],
                    [tuple(div_coord(v, scale) for v in box)
                     for box in hurt]))
    return out


def scale_sprite(s, scale):
    if scale == 1 or s is None or s.pix is None:
        return s
    ns = Sprite()
    ns.group, ns.number = s.group, s.number
    ns.w = (s.w + scale - 1) // scale
    ns.h = (s.h + scale - 1) // scale
    ns.ax = div_coord(s.ax, scale)
    ns.ay = div_coord(s.ay, scale)
    ns.palidx = s.palidx
    ns.link = s.link
    pix = bytearray(ns.w * ns.h)
    for oy in range(ns.h):
        for ox in range(ns.w):
            counts = {}
            for sy in range(oy * scale, min((oy + 1) * scale, s.h)):
                row = sy * s.w
                for sx in range(ox * scale,
                                min((ox + 1) * scale, s.w)):
                    v = s.pix[row + sx]
                    counts[v] = counts.get(v, 0) + 1
            opaque = [(count, idx) for idx, count in counts.items() if idx]
            pix[oy * ns.w + ox] = max(opaque)[1] if opaque else 0
    ns.pix = bytes(pix)
    return ns


def scale_air_frames_f(frames, f):
    """Fractional char_scale: sprite placement + clsn boxes shrink with the
    artwork; velocities, positions and timing stay untouched."""
    if f == 1.0:
        return frames
    out = []
    for g, n, x, y, t, flip, atk, hurt in frames:
        out.append((g, n, int(round(x * f)), int(round(y * f)),
                    t, flip,
                    [tuple(int(round(v * f)) for v in box) for box in atk],
                    [tuple(int(round(v * f)) for v in box) for box in hurt]))
    return out


def scale_sprite_f(s, f):
    """Fractional downscale of the indexed pixels (nearest keeps palette
    indices valid) plus anchor rescale."""
    if f == 1.0 or s is None or s.pix is None:
        return s
    from PIL import Image
    ns = Sprite()
    ns.group, ns.number = s.group, s.number
    ns.w = max(1, int(round(s.w * f)))
    ns.h = max(1, int(round(s.h * f)))
    ns.ax = int(round(s.ax * f))
    ns.ay = int(round(s.ay * f))
    ns.palidx = s.palidx
    ns.link = s.link
    im = Image.frombytes("P", (s.w, s.h), s.pix)
    ns.pix = im.resize((ns.w, ns.h), Image.NEAREST).tobytes()
    return ns


def parse_air(path):
    # .air comments may be Shift-JIS / Latin-1; only ASCII tokens matter
    with open(path, encoding="utf-8-sig", errors="replace") as src:
        txt = src.read()
    anims = {}
    parts = re.split(r"\[begin\s+action\s+(\d+)\s*\]", txt, flags=re.I)
    frame_re = re.compile(
        r"(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*(?:,\s*(\S+))?")
    clsn_re = re.compile(r"clsn([12])(default)?\s*:\s*(\d+)", re.I)
    box_re = re.compile(
        r"clsn([12])(?:default)?\s*\[\d+\]\s*=\s*"
        r"(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)",
        re.I)

    for i in range(1, len(parts), 2):
        num = int(parts[i])
        frames = []
        loopstart = 0
        default_clsn1 = []
        default_clsn2 = []
        frame_clsn1 = None
        frame_clsn2 = None
        lines = iter(parts[i + 1].splitlines())
        pending_kind = None
        pending_default = False
        pending_count = 0
        pending_boxes = []

        for raw in lines:
            line = raw.split(";", 1)[0].strip()
            if not line:
                continue
            if line.lower() == "loopstart":
                loopstart = len(frames)
                continue
            if line.startswith("["):
                break

            m = clsn_re.match(line)
            if m:
                pending_kind = int(m.group(1))
                pending_default = bool(m.group(2))
                pending_count = int(m.group(3))
                pending_boxes = []
                if pending_count == 0:
                    if pending_default:
                        if pending_kind == 1:
                            default_clsn1 = []
                        else:
                            default_clsn2 = []
                    elif pending_kind == 1:
                        frame_clsn1 = []
                    else:
                        frame_clsn2 = []
                    pending_kind = None
                continue

            m = box_re.match(line)
            if m and pending_kind == int(m.group(1)):
                x1, y1, x2, y2 = map(int, m.groups()[1:])
                pending_boxes.append((min(x1, x2), min(y1, y2),
                                    max(x1, x2), max(y1, y2)))
                if len(pending_boxes) == pending_count:
                    if pending_default:
                        if pending_kind == 1:
                            default_clsn1 = list(pending_boxes)
                        else:
                            default_clsn2 = list(pending_boxes)
                    elif pending_kind == 1:
                        frame_clsn1 = list(pending_boxes)
                    else:
                        frame_clsn2 = list(pending_boxes)
                    pending_kind = None
                continue

            m = frame_re.match(line)
            if m:
                g, n, x, y, t, flip = m.groups()
                atk = frame_clsn1 if frame_clsn1 is not None else default_clsn1
                hurt = frame_clsn2 if frame_clsn2 is not None else default_clsn2
                frames.append((int(g), int(n), int(x), int(y),
                               255 if int(t) < 0 else max(1, int(t)),
                               flip or "", list(atk), list(hurt)))
                frame_clsn1 = frame_clsn2 = None
        # Some AIRs append a duplicate placeholder action after the real
        # animation (King repeats action 0 as -1,-1).  Keep the usable one.
        if (num in anims and any(g >= 0 and n >= 0 for g, n, *_ in anims[num][0])
                and not any(g >= 0 and n >= 0 for g, n, *_ in frames)):
            continue
        anims[num] = (frames, loopstart)
    return anims


def resolve_import_anims(cfg, air):
    """Replace missing attack actions in imported chars with nearby real art.

    The roster generator uses action 47 when a statedef's action is absent.
    In many AIRs 47 is just a single stand/landing pose, even though the
    character has other attack sprites in the same move-number range.
    """
    anims = dict(cfg["anims"])
    for sid, state in cfg["moves"].items():
        if not (5 <= sid <= 8 or 19 <= sid <= 26 or
                48 <= sid <= 68 or 85 <= sid <= 89):
            continue
        if anims.get(sid) != 47 or state == 47:
            continue
        if 200 <= state < 700:
            candidates = (a for a in air if 200 <= a < 700
                          and abs(a - state) <= 30)
        elif state >= 1000:
            candidates = (a for a in air if a >= 1000
                          and abs(a - state) <= 100)
        else:
            continue
        candidates = [a for a in candidates
                      if len({(g, n) for g, n, *_ in air[a][0]
                              if g >= 0 and n >= 0}) >= 2]
        if candidates:
            anims[sid] = min(candidates, key=lambda a: (
                abs(a - state), -len(air[a][0]), a))
    return anims


def repair_invisible_move_anims(name, cfg, anims, air):
    """Give move states whose AIR action draws no sprite a visible body.

    A few imports put a special's HitDef in an invisible helper timeline
    (Heavy D!'s Blast Upper and Soul Flower: every frame is sprite ``-1``
    plus Clsn1).  The SNES engine has no helpers, so it chains the main
    fighter into that state at the end of the launch animation.  Playing
    the helper's action on the fighter made the character disappear for
    the active frames -- only the hitbox/hit spark remained on screen.

    Keep the helper clip's ticks and collision boxes (so the move still
    hits with the source timing) but draw the last pose of the visible
    state that chains into it.  The parent animation has just ended when
    the transition fires, so that hold pose is the closest match to what
    the arcade game shows while the helper finishes the attack.
    """
    def drawable(frames):
        return bool(frames) and any(g >= 0 and n >= 0 for g, n, *_ in frames)

    # A transition row (from, to, anim-end) names the visible parent clip.
    donors = {}
    for row in cfg.get("extra_trans", ()):
        fsid, tsid, kind, _arg = row
        if kind == 0 and tsid != fsid:
            donors.setdefault(tsid, fsid)
    donors.update(cfg.get("invisible_anim_donor", {}))

    used = set(air)
    repaired = []
    for sid, anum in sorted(anims.items()):
        clip = air.get(anum)
        if clip is None or drawable(clip[0]):
            continue
        if sid not in cfg.get("moves", {}) or sid in cfg.get("slices", {}):
            continue
        donor = None
        donor_sid = donors.get(sid)
        if donor_sid is not None and donor_sid in anims:
            candidate = air.get(anims[donor_sid])
            if candidate is not None and drawable(candidate[0]):
                donor = candidate[0]
        if donor is None:
            # No transition recorded (e.g. a wiring added later): use the
            # closest visible action so the fighter can never turn into an
            # invisible hitbox.
            close = [(abs(a - anum), -len(clip[0]), a) for a, c in air.items()
                     if drawable(c[0]) and a != anum]
            if close:
                donor = air[min(close)[2]][0]
        if donor is None:
            continue
        pose = next((f for f in reversed(donor)
                     if f[0] >= 0 and f[1] >= 0), None)
        if pose is None:
            continue
        new_num = -1 - sid
        while new_num in used:
            new_num -= 1
        used.add(new_num)
        air[new_num] = (
            [(pose[0], pose[1], pose[2], pose[3], f[4], pose[5], f[6], f[7])
             for f in clip[0]], clip[1])
        anims[sid] = new_num
        repaired.append((sid, anum, new_num))
    if repaired:
        print(f"{name}: drawable pose for {len(repaired)} invisible move "
              f"clips: {repaired}")
    return repaired


def kof_damage(expr, varvals=None):
    """Pull a plain base damage out of a `damage =` field.

    Plain numbers pass through unchanged.  KOF-authored chars compute
    damage as ``floor((ifelse(var(6),C,B)-var(21))*fvar(7))`` where the
    counter-hit branch C and combo dampeners var(21)/fvar(7) cannot be
    evaluated at build time -- the SNES engine stores a single byte, so
    the false branch B (the non-counter base) is the right value.  Forms
    like ``floor((N-var(21))*fvar(7))`` and ``floor(N*fvar(7))`` reduce
    to their leading constant.  ``var(25)``-style indirection resolves
    through ``varvals`` (the statedef's VarSet constants).
    """
    expr = expr.strip()
    m = re.match(r"-?\d+(?:\.\d+)?", expr)
    if m:
        return float(m.group(0))
    # mask variable reads first so `var(25)` cannot leak its index into
    # the numeric patterns below
    masked = re.sub(r"(?:sysvar|fvar|var)\s*\([^)]*\)", "0", expr, flags=re.I)
    # KOF HitDefs often nest Ifelse(hitcount...): evaluating the first
    # hit (hitcount=0, random=0) picks the non-counter base branch instead
    # of a combo-damage divisor or the outer minimum.  Brian's Screw Body
    # Press and Big Bang Tackle were collapsing to 1-2 points before this.
    # Only take this path for hitcount expressions so unrelated movelists
    # (notably Kyo's var(23) SDM scaling) keep their established values.
    if re.search(r"\bhitcount\b", expr, re.I):
        eval_expr = re.sub(r"fvar\s*\([^)]*\)", "1", expr, flags=re.I)
        def _var_value(m):
            idx = m.group(1)
            return str(varvals.get(idx, 0)) if varvals else "0"
        eval_expr = re.sub(r"(?:sysvar|var)\s*\(\s*(\d+)\s*\)",
                           _var_value, eval_expr, flags=re.I)
        try:
            from calibration.mugen import evaluate, Unsupported
            return float(evaluate(eval_expr, {'hitcount': 0, 'random': 0}))
        except (Unsupported, ValueError, TypeError, ZeroDivisionError):
            pass
    m = re.search(r"ifelse\(([^)]*)\)", masked, re.I)
    if m:
        nums = re.findall(r"-?\d+(?:\.\d+)?", m.group(1))
        if nums:
            return float(nums[-1])
    for pat in (r"\(\s*(-?\d+(?:\.\d+)?)",
                r"floor\s*\(\s*(-?\d+(?:\.\d+)?)"):
        m = re.search(pat, masked, re.I)
        if m and float(m.group(1)):
            return float(m.group(1))
    if varvals:
        vals = [varvals[n] for n in
                re.findall(r"var\s*\(\s*(\d+)", expr)
                if n in varvals and varvals[n]]
        if vals:
            return min(vals)
    return 0.0


def _plain_int(value):
    """Parse a plain MUGEN integer; expressions return None."""
    text = str(value or "").strip()
    m = re.fullmatch(r"[+-]?\s*\d+", text)
    return int(text.replace(" ", "")) if m else None


def state_power_base(headers, statedefs, state):
    """Cost that still applies while the MAX window is active.

    The source gates the extra -1000/-2000 PowerAdd with `var(40) = 0`
    (the arcade MAX flag).  The port uses F_MAX for that flag, so the
    var(40)-gated part is the *outside-MAX* surcharge, not the base cost.
    SuperPause and PowerAdd controllers can both carry the value.
    """
    base = 0
    header = _plain_int(headers.get(state, {}).get("poweradd", "0"))
    if header is not None:
        base += header
    for ctrl in statedefs.get(state, ()):
        if any(re.search(r"\bvar\s*\(\s*40\s*\)", t)
               for t in ctrl.get("triggers", ())):
            continue
        delta = _plain_int(ctrl.get("poweradd", ""))
        if delta is None:
            if ctrl.get("type", "").strip().lower() != "poweradd":
                continue
            delta = _plain_int(ctrl.get("value", ""))
        if delta is not None and delta < 0:
            base += delta
    return base


def _state_comment(path, state):
    """Comment/name block immediately around `[Statedef state]`."""
    key = (path, state)
    if key in _STATE_COMMENT_CACHE:
        return _STATE_COMMENT_CACHE[key]
    text = ""
    try:
        lines = open(path, encoding="utf-8-sig",
                     errors="replace").read().splitlines()
    except OSError:
        lines = []
    for i, line in enumerate(lines):
        if re.match(rf"\[statedef\s+{state}\]", line, re.I):
            pre = [x.strip() for x in lines[:i]
                   if x.strip().startswith((";", "//"))][-2:]
            post = [x.strip() for x in lines[i + 1:i + 4]
                    if x.strip().startswith((";", "//"))][:2]
            text = " ".join(pre + post)
            break
    _STATE_COMMENT_CACHE[key] = text
    return text


_STATE_COMMENT_CACHE = {}


def state_is_max(cns_path, headers, statedefs, state):
    """True when a wired 85-89 slot is a MAX/SDM version."""
    text = _state_comment(cns_path, state).upper()
    if "MAX" in text or "SDM" in text:
        return True
    header = _plain_int(headers.get(state, {}).get("poweradd", "0"))
    if header is None or header >= 0:
        return False
    for ctrl in statedefs.get(state, ()):
        if ctrl.get("type", "").strip().lower() != "poweradd":
            continue
        delta = _plain_int(ctrl.get("value", ""))
        if delta is None or delta >= 0:
            continue
        if any(re.search(r"\bvar\s*\(\s*40\s*\)", t)
               for t in ctrl.get("triggers", ())):
            return True
    return False


def parse_cns(path, coord_scale=1, damage_scale=1, char=None):
    """Return the small HitDef subset needed by the native fight engine.

    ``char`` selects per-character Explod anim overrides (for source anim ids
    that are reused by several packages); native calibration callers can omit
    it because they never compile Explod rows.
    """
    statedefs = {}
    headers = {}                             # statedef -> header fields
    powadds = {}                             # statedef -> power delta
    current_state = None
    current_ctrl = None
    for raw in open(path, encoding="utf-8-sig"):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"\[statedef\s+(-?\d+)\]", line, re.I)
        if m:
            current_state = int(m.group(1))
            statedefs.setdefault(current_state, [])
            headers[current_state] = {}
            current_ctrl = None
            continue
        m = re.match(r"\[state\b[^\]]*\]", line, re.I)
        if m:
            # MUGEN attaches a controller to the enclosing Statedef; the
            # number in "[State N, name]" is only a label (ikaruga's files
            # carry stale numbers from copy-pasted blocks).  Some imports
            # (Heavy D) use letter labels such as "[State a]" and
            # "[State explod]"; those still start a new controller.  Failing
            # to open one there let the following controller overwrite the
            # previous HitDef, so moves silently lost their hitbox.
            # State -1/-2/-3 sections work because their controllers belong
            # to that same statedef section.
            current_ctrl = {"triggers": []}
            if current_state is not None:
                statedefs.setdefault(current_state, []).append(current_ctrl)
            continue
        if "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        key = key.lower()
        if key == "poweradd" and current_state is not None:
            # header pseudo-controller and PowerAdd state controllers both
            # net to a per-state delta; the engine applies it on entry
            try:
                powadds[current_state] = (powadds.get(current_state, 0)
                                          + int(float(value)))
            except ValueError:
                pass
        if current_ctrl is not None:
            current_ctrl[key] = value
            if key.startswith("trigger"):
                current_ctrl["triggers"].append(value)
                # Keep the source trigger index alongside the expression:
                # repeated triggerN lines are ANDed, while trigger1/trigger2
                # are ORed.  trans_rules needs the grouping for split
                # landing rules (`trigger1 = Pos Y >= 0` + `Vel Y > 0`).
                current_ctrl.setdefault("trigger_groups", []).append(key)
        elif current_state is not None:
            headers[current_state][key] = value

    # PowerAdd controllers are the normal way MUGEN states pay for a super.
    # Sum simple negative controller values; expressions stay out and are
    # handled by a per-character `pow_override`.
    for state, ctrls in statedefs.items():
        for ctrl in ctrls:
            if ctrl.get("type", "").strip().lower() != "poweradd":
                continue
            delta = _plain_int(ctrl.get("value", ""))
            if delta is not None and delta < 0:
                powadds[state] = powadds.get(state, 0) + delta

    def hitdef_row(hitdef, varvals=None):
        def first_number(key, default=0):
            m = re.match(r"(-?\d+(?:\.\d+)?)",
                         hitdef.get(key, "").strip())
            return float(m.group(1)) if m else default

        def number_pair(key):
            m = re.match(
                r"(-?\d*\.?\d+)\s*(?:,\s*(-?\d*\.?\d+))?",
                hitdef.get(key, "").strip())
            if not m:
                return (0.0, 0.0)
            return (float(m.group(1)),
                    float(m.group(2)) if m.group(2) is not None else 0.0)

        gvel = number_pair("ground.velocity")
        avel = number_pair("air.velocity")
        gtype = hitdef.get("ground.type", "").strip().lower()
        fall = (hitdef.get("fall", "0").strip().startswith("1")
                or gtype == "trip")
        # MUGEN animtype -> get-hit anim variant. Light/Medium/Heavy pick
        # the base+0..2 frame set; Back/Up/DiagUp/etc force the 5030 pose.
        animtype = {"light": 0, "medium": 1, "med": 1, "heavy": 2,
                    "hard": 2, "back": 3, "up": 4, "diagup": 5,
                    "twirl": 5, "none": 0}.get(
            hitdef.get("animtype", "light").strip().lower(), 2)
        low = int(gtype == "low")
        # guardflag letters -> bitmask H=1,M=2,L=4,A=8 (which blocking
        # postures can stop this hit)
        guard = 0
        for i, letter in enumerate("hmla"):
            if letter in hitdef.get("guardflag", "").strip().lower():
                guard |= 1 << i
        # chip damage is the optional second component of damage = n, chip;
        # the comma must sit at paren depth 0 (ifelse() args contain commas)
        _dmg_expr = hitdef.get("damage", "")
        _depth = 0
        _split = len(_dmg_expr)
        for _i, _ch in enumerate(_dmg_expr):
            if _ch == "(":
                _depth += 1
            elif _ch == ")":
                _depth -= 1
            elif _ch == "," and _depth == 0:
                _split = _i
                break
        _dmg_parts = (_dmg_expr[:_split], _dmg_expr[_split + 1:])
        dmg = (int(round(kof_damage(_dmg_parts[0], varvals)
                        * damage_scale)),
               int(round(kof_damage(_dmg_parts[1], varvals)
                        * damage_scale))
               if len(_dmg_parts) > 1 else 0)
        gdvel = number_pair("guard.velocity")
        agvel = number_pair("airguard.velocity")
        def expr_pair(key):
            # KOF-style values bury the second component behind a
            # parenthesized expression ("11+(Helper(...),var(0)),13"), so
            # split on the comma at paren depth 0 like the damage field.
            raw = hitdef.get(key, "").strip()
            depth = 0
            for i, ch in enumerate(raw):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == "," and depth == 0:
                    def lead(s):
                        m = re.match(r"(-?\d+(?:\.\d+)?)", s.strip())
                        return float(m.group(1)) if m else 0.0
                    return (lead(raw[:i]), lead(raw[i + 1:]))
            return (first_number(key), 0.0)

        pause = expr_pair("pausetime")
        gpause = expr_pair("guard.pausetime")
        p2state = int(first_number("p2stateno", -1))
        p1state = int(first_number("p1stateno", -1))
        # attr second field carrying T (S,NT / A,NT ...) = throw HitDef:
        # bypasses guard, hits only victims not already in a hit state
        attr = hitdef.get("attr", "")
        throw = bool(re.search(r",\s*\w*t\b", attr, re.I))

        active = 1
        for trigger in hitdef["triggers"]:
            m = re.search(r"\banimelem\s*=\s*(\d+)", trigger, re.I)
            if m:
                active = int(m.group(1))
                break
            # KOF-style chars gate the HitDef with an element window:
            # `AnimElemTime(N) >= 0 && AnimElemTime(M) < 0` fires on 1-based
            # element N -- use the window start like `animelem = N`.
            m = re.search(r"animelemtime\s*\(\s*(\d+)\s*\)\s*>?=?\s*0",
                          trigger, re.I)
            if m:
                active = int(m.group(1))
                break
        return {
            "active": active,
            "damage": dmg[0],
            "hittime": int(first_number("ground.hittime", 8)),
            "slidetime": int(first_number("ground.slidetime", 4)),
            # 8.8 fixed point; x magnitudes, y keeps the screen-space sign
            "gvx": int(round(abs(gvel[0] or 1.5) / coord_scale * 256)),
            "gvy": int(round(gvel[1] / coord_scale * 256)),
            "avx": int(round(abs(avel[0] or gvel[0] or 1.5)
                             / coord_scale * 256)),
            "avy": int(round(avel[1] / coord_scale * 256)),
            "fall": int(fall),
            "trip": int(gtype == "trip"),
            "animtype": animtype,
            "low": low,
            "guard": guard,
            "gdamage": dmg[1],
            # guard pushback: ground x magnitude (falls back to the hit's
            # ground.velocity), then air x,y
            "grvx": int(round(abs(gdvel[0] or gvel[0] or 2)
                              / coord_scale * 256)),
            "agvx": int(round(abs(agvel[0] or 1.5) / coord_scale * 256)),
            "agvy": int(round(agvel[1] / coord_scale * 256)),
            # throw HitDefs with p2stateno commented out still bind the
            # victim: the mugen chars redirect through TargetState inside
            # the attacker's bind state (810) -- S_VHELD is the placeholder
            "p2state": VICTIM_STATE_IDS.get(p2state, 76 if throw else 0xFF),
            "p2pause": max(0, min(255, int(pause[1]))),
            # attacker-side hitstop: global freeze ticks on contact
            "p1pause": max(0, min(60, int(pause[0]))),
            "p1gpause": max(0, min(60, int(gpause[0] or pause[0]))),
            "p1mugen": p1state,
            "throw": int(throw),
            # HitDef envshake (supers): packed (ampl<<5)|ticks, applied by the
            # engine when the hit connects
            "eshake": ((max(0, min(int(first_number("envshake.ampl",
                                            first_number("fall.envshake.ampl"))),
                                   7)) << 5) |
                       max(0, min(int(first_number("envshake.time",
                                            first_number("fall.envshake.time"))),
                                  31))),
        }

    moves = {}
    hitdef_lists = {}                          # state -> all HitDef rows
    hitsnds = {}                               # state -> runtime hit sfx id
    for state, ctrls in statedefs.items():
        hitdefs = [c for c in ctrls
                   if c.get("type", "").lower() == "hitdef"]
        if not hitdefs:
            continue
        # VarSet constants backing `damage = ...var(N)...` expressions;
        # variants differ by var(10), so the weakest is the base damage
        varvals = {}
        for c in ctrls:
            for k, v in c.items():
                mv = re.match(r"var\((\d+)\)", k)
                if mv:
                    d = kof_damage(v)
                    if d:
                        varvals[mv.group(1)] = min(
                            d, varvals.get(mv.group(1), d))
        hitdef_lists[state] = [hitdef_row(c, varvals) for c in hitdefs]
        hs = hitdefs[0].get("hitsound", "").strip()
        at = hitdefs[0].get("animtype", "").strip().lower()
        # KOF HitDefs often write hitsound as an expression
        # (S444,IfElse(...)); keep the bank/group but fall back to the
        # common bank by strength.  -1 means the move is intentionally silent.
        m = re.match(r"([fFsS]?)\s*(-?\d+)\s*,\s*([^\s,]+)", hs)
        if m:
            bank = m.group(1).lower()
            group = int(m.group(2))
            item = m.group(3)
            if group < 0:
                hitsnds[state] = 0xFF
            elif bank == "" and group == 5 and item.isdigit():
                hitsnds[state] = HIT_SND.get(int(item), 0xFF)
            elif bank == "f" and item.isdigit():
                hitsnds[state] = COMMON_SND.get((group, int(item)), 0xFF)
            else:
                # char.snd hit ids are not in the fixed audio bank; pick the
                # generic common.snd hit by the HitDef's declared strength
                hitsnds[state] = {"light": 4, "medium": 5}.get(at, 6)
        # multi-hitdef states (launcher + follow-up hits): keep the hit that
        # knocks down/launches, else the first one
        hitdef = next((c for c in hitdefs
                       if c.get("fall", "0").strip().startswith("1")
                       or c.get("air.fall", "0").strip().startswith("1")
                       or c.get("ground.type", "").strip().lower() == "trip"),
                      hitdefs[0])
        moves[state] = hitdef_row(hitdef, varvals)

    # ReversalDef (Kung Fu Blocking parry / counter-grab): state ->
    # (window ticks, mugen blocked state, class, mugen victim state).  The
    # cancelling ReversalDef's Time trigger supplies the window; p1stateno
    # is the reversal actor's follow-up and p2stateno (counter-grabs such as
    # Geese/Daimon/Heidern) is the opponent's held state.
    reversals = {}
    for state, ctrls in statedefs.items():
        armed = stop = 0
        blocked = -1
        victim = -1
        cls = 0
        for c in ctrls:
            ctype = c.get("type", "").lower()
            if ctype == "reversaldef":
                attr = c.get("reversal.attr", "").strip()
                dst = c.get("p1stateno", "-1")
                vdst = c.get("p2stateno", "-1")
            elif ctype == "hitoverride":
                attr = c.get("attr", "").strip()
                dst = c.get("stateno", "-1")
                vdst = "-1"
            else:
                continue
            if not attr or attr == ",":
                # empty attr = cancel row: its Time trigger(s) close the
                # armed window (Time = 8 cancels, Time < 5 limits too)
                for t in c["triggers"]:
                    m = re.search(r"time\s*[<=]+\s*(\d+)", t, re.I)
                    if m:
                        stop = max(stop, int(m.group(1)))
                continue
            try:
                dst = int(float(dst.split(",")[0]))
            except ValueError:
                continue
            try:
                vdst = int(float(vdst.split(",")[0]))
            except ValueError:
                vdst = -1
            if blocked < 0:
                blocked = dst
            if victim < 0:
                victim = vdst
            for t in c["triggers"]:
                m = re.search(r"time\s*<\s*(\d+)", t, re.I)
                if m:
                    stop = max(stop, int(m.group(1)))
            try:
                stop = max(stop, int(float(c.get("time", "0")
                                         .split(",")[0])))
            except ValueError:
                pass
            # allowed attacker postures (same bits as ct_post): the first
            # attr token lists statetype letters S/C/A
            for letter in attr.split(",")[0].upper():
                if letter == "S":
                    cls |= 1
                elif letter == "C":
                    cls |= 2
                elif letter == "A":
                    cls |= 4
        if blocked >= 0:
            reversals[state] = (stop or 8, blocked, cls or 5, victim)

    # PosAdd controllers -> per-state (anim elem, dx) timeline applied on the
    # tick the element becomes current.  var(*)-conditioned PosAdds (throw's
    # holdfwd move) are elem-actions instead -- they carry a condition flag.
    posadds = {}
    for state, ctrls in statedefs.items():
        for ctrl in ctrls:
            if ctrl.get("type", "").lower() != "posadd":
                continue
            if any("var(" in t.lower() for t in ctrl["triggers"]):
                continue
            m = re.match(r"(-?\d+(?:\.\d+)?)", ctrl.get("x", "0").strip())
            dx = int(round(float(m.group(1)) / coord_scale)) if m else 0
            if not dx:
                continue
            for trigger in ctrl["triggers"]:
                em = re.search(r"\banimelem\s*=\s*(\d+)", trigger, re.I)
                if em:
                    posadds.setdefault(state, []).append(
                        (int(em.group(1)) - 1, dx))
    for state in posadds:
        posadds[state] = sorted(set(posadds[state]))

    def elem_window(triggers):
        """Trigger list -> inclusive 0-based frame window for TargetBind."""
        lo, hi = 0, 254
        for x in triggers:
            m = re.search(r"animelemtime\((\d+)\)\s*>=\s*0", x, re.I)
            if m:
                lo = max(lo, int(m.group(1)) - 1)
            m = re.search(r"animelemtime\((\d+)\)\s*<\s*0", x, re.I)
            if m:
                hi = min(hi, int(m.group(1)) - 2)
            m = re.search(r"\banimelem\s*=\s*(\d+)", x, re.I)
            if m:
                lo = hi = int(m.group(1)) - 1
        return lo, hi

    # TargetBind -> per-state (lo,hi,dx,dy) windows; elem-gated actor/target
    # controllers -> (frame, op, arg, cond) action rows.  cond bit0 gates
    # var(2) (throw's holdfwd variant); bit1 preserves Random<=500 voices.
    binds = {}
    acts = {}
    exprows = []                             # compiled Explod rows
    snds = {}                                # state -> [(triggers, sfx id)]
    for state, ctrls in statedefs.items():
        for ctrl in ctrls:
            ctype = ctrl.get("type", "").lower()
            trig = ctrl["triggers"]
            cond = int(any("var(" in t.lower() for t in trig))
            frame = None
            for x in trig:
                em = re.search(r"\banimelem\s*=\s*(\d+)", x, re.I)
                if em:
                    frame = int(em.group(1)) - 1
                    break
                # `time = 0` fires on the state-entry tick -> frame 0
                # (throw's TargetState 815 binds through this)
                if re.match(r"\s*time\s*=\s*0\s*$", x, re.I):
                    frame = 0
                    break
                tm = re.match(r"\s*time\s*=\s*(\d+)\s*$", x, re.I)
                if tm:
                    frame = 0x80 | int(tm.group(1))
                    break
            if ctype == "pause":
                # Pause at state-entry -> global freeze op (blocked poses
                # use `trigger1 = Time = 0`; anim-elem pauses fall through)
                if any(re.match(r"time\s*=\s*0\s*$", t, re.I)
                       for t in trig):
                    tparam = ctrl.get("time", "0").split(",")[0]
                    acts.setdefault(state, []).append(
                        (0, 6, int(float(tparam)) & 0xFF, 0))
                continue
            if ctype == "superpause":
                # SuperPause at an anim elem -> global freeze (mugen
                # default time = 30); the poweradd rides PowTab instead
                tparam = ctrl.get("time", "30").split(",")[0]
                ticks = int(float(tparam)) or 30
                for x in trig:
                    for em in re.finditer(r"\banimelem\s*=\s*(\d+)",
                                          x, re.I):
                        acts.setdefault(state, []).append(
                            (int(em.group(1)) - 1, 6, ticks & 0xFF, 0))
                continue
            if ctype == "targetbind":
                pos = ctrl.get("pos", "0,0")
                m = re.match(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)",
                             pos.strip())
                dx, dy = ((int(round(float(m.group(1)) / coord_scale)),
                           int(round(float(m.group(2)) / coord_scale)))
                          if m else (0, 0))
                lo, hi = elem_window(trig)
                binds.setdefault(state, []).append((lo, hi, dx, dy))
            elif ctype == "playsnd":
                # AnimElem/Time triggers are resolved to frame rows by the
                # caller (which owns the anim durations); keep the raw
                # trigger list and the mapped runtime sfx id.
                v = ctrl.get("value", "").strip()
                m = re.match(r"([fFsS]?)", v)
                bank = m.group(1).lower()
                rest = v[m.end():]
                # Split on the first comma outside parentheses, then take
                # the leading constant of each side.  KOF chars write the
                # sample as an expression, e.g. Ryu's
                # `s10+(var(8)*10),10`: the voice bank/group is still 10
                # (var(8)=0 in the port), but a plain `\d+,\d+` match
                # rejected it and dropped every normal/special grunt.
                depth = 0
                split = None
                for i, ch in enumerate(rest):
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                    elif ch == "," and depth == 0:
                        split = i
                        break
                gm = re.match(r"(-?\d+)", rest)
                im = (re.match(r"(-?\d+)", rest[split + 1:])
                      if split is not None else None)
                if gm and im:
                    pair = (int(gm.group(1)), int(im.group(1)))
                    sfxid = (SND_TO_SFX.get(pair)
                             if bank in ("", "s")
                             else COMMON_SND.get(pair))
                    if sfxid is not None:
                        snds.setdefault(state, []).append((trig, sfxid))
                    elif bank in ("", "s"):
                        # unmapped char-bank sample: keep the (group,item)
                        # pair so the caller can route it to a per-char
                        # streamed voice id instead of dropping it
                        snds.setdefault(state, []).append((trig, pair))
            elif ctype == "palfx":
                # color flash on the fast/EX moves: op8 arg = flash ticks
                tparam = ctrl.get("time", "20").split(",")[0]
                acts.setdefault(state, []).append(
                    (0x80, 8, int(float(tparam or 20)) & 0xFF, 0))
            elif ctype == "afterimage":
                # ghost trail: op9 latches the flag for the rest of the
                # state; the engine's per-slot ttl gives the mugen decay
                acts.setdefault(state, []).append(
                    (frame if frame is not None else 0x80, 9, 1, 0))
            elif ctype == "envshake":
                # op10 arg packs (ampl << 5) | ticks; freq is folded into a
                # fixed alternate-frames oscillation in the presenter
                tt = int(float(ctrl.get("time", "8").split(",")[0] or 8))
                amp = int(float(ctrl.get("ampl", "4").split(",")[0] or 4))
                acts.setdefault(state, []).append(
                    (frame if frame is not None else 0x80, 10,
                     ((min(amp, 7) << 5) | min(tt, 31)) & 0xFF, 0))
            elif ctype == "nothitby":
                # op11 arg = invuln ticks; mugen time <= 1 (constant refresh
                # or one-symbolic-tick) becomes "for the whole state"
                try:
                    tt = int(float(ctrl.get("time", "-1").split(",")[0] or -1))
                except ValueError:
                    tt = -1
                arg = tt if 1 < tt < 0xFF else 0xFF
                acts.setdefault(state, []).append(
                    (frame if frame is not None else 0x80, 11, arg, 0))
            elif ctype == "posfreeze":
                # op13 arg1 = latch the x-freeze until the window's end elem
                acts.setdefault(state, []).append((0x80, 13, 1, 0))
                for x in trig:
                    m = re.search(r"animelemtime\((\d+)\)\s*<\s*0",
                                  x, re.I)
                    if m:
                        acts.setdefault(state, []).append(
                            (int(m.group(1)) - 1, 13, 0, 0))
            elif ctype == "explod":
                # op14: arg = row index into the char's ExpTab.  Compiled
                # clips are the intro's wood pieces and the Oniyaki flame
                # pillar/crest; fightfx anims (Fxx) are skipped.  Triggers:
                # RoundState!=0 -> state-entry, AnimElemTime(n)=1 or a bare
                # AnimElem = n[,= m] -> frame n-1.
                m = re.match(r"([fF]?)\s*(\d+)", ctrl.get("anim", "").strip())
                if not m or m.group(1):
                    continue
                label = EXPLOD_ANIM_BY_CHAR.get(char, {}).get(
                    int(m.group(2)))
                if label is None:
                    label = EXPLOD_ANIM.get(int(m.group(2)))
                if label is None:
                    continue

                def pair(key, scale=1.0):
                    mm = re.match(
                        r"(-?\d*\.?\d+)\s*,\s*(-?\d*\.?\d+)",
                        ctrl.get(key, "0,0").strip())
                    if not mm:
                        return 0, 0
                    return (int(round(float(mm.group(1)) / coord_scale
                                        * scale)),
                            int(round(float(mm.group(2)) / coord_scale
                                        * scale)))

                xoff, yoff = pair("pos")
                vx, vy = pair("velocity", 256.0)
                _ax, ay = pair("accel", 256.0)
                rem = int(float(ctrl.get("removetime", "0")
                                .split(",")[0] or 0))
                trig_b = 0x80                       # RoundState != 0 -> entry
                for x in trig:
                    m2 = re.search(r"animelemtime\((\d+)\)\s*=\s*1", x, re.I)
                    if not m2:
                        m2 = re.search(r"animelem\s*=\s*(\d+)", x, re.I)
                    if m2:
                        trig_b = int(m2.group(1)) - 1
                acts.setdefault(state, []).append(
                    (trig_b, 14, len(exprows), 0))
                exprows.append((EXPLODS_IDX[label], xoff, yoff,
                                vx, vy, ay, rem & 0xFF, EXPLODS[label][3]))
            elif ctype == "changeanim" and any(
                    "movecontact" in t.lower() for t in trig):
                # "switch to elem N on hit contact" -> op12: when the HitDef
                # has already connected, jump the frame cursor to arg
                tgt = int(float(ctrl.get("elem", "0").split(",")[0] or 0)) - 1
                wstart = None
                for x in trig:
                    m = re.search(r"animelemtime\((\d+)\)\s*>\s*0", x, re.I)
                    if m:
                        wstart = int(m.group(1)) - 1
                if 0 <= tgt < 0x80 and wstart is not None:
                    acts.setdefault(state, []).append(
                        (wstart, 12, tgt, 0))
            elif ctype == "velmul":
                # VelMul x -> op16 (arm per-tick Q8 damping) so a move keeps
                # MUGEN's exponential slowdown instead of sliding at the
                # initial VelSet speed for the whole action.  A bounded
                # AnimElemTime(M) < 0 window also emits op17 to disarm it.
                # Only mapped move states: victim/common states already use
                # the engine's own hit-slide friction.  Runs before the
                # `frame is None` guard because AnimElemTime triggers do not
                # produce a plain element index.
                if state not in moves:
                    continue
                xv = ctrl.get("x")
                if xv is None:
                    continue
                m = re.match(r"(\d*\.?\d+)", xv.strip())
                if not m:
                    continue                  # expression -> skip
                mult = float(m.group(1))
                if not 0.0 < mult < 1.0:
                    continue
                q8 = max(1, min(255, int(round(mult * 256))))
                frm = None
                for x in trig:
                    em = re.search(r"\banimelem\s*=\s*(\d+)", x, re.I)
                    if em:
                        frm = int(em.group(1)) - 1
                        break
                    mt = re.search(r"\banimelemtime\s*\(\s*(\d+)\s*\)"
                                   r"\s*>=?\s*\d+", x, re.I)
                    if mt:
                        frm = int(mt.group(1)) - 1
                        break
                    if re.match(r"\s*1\s*$", x):
                        frm = 0
                        break
                    tm = re.match(r"\s*time\s*=\s*(\d+)\s*$", x, re.I)
                    if tm:
                        frm = 0x80 | int(tm.group(1))
                        break
                if frm is None:
                    continue
                acts.setdefault(state, []).append((frm, 16, q8, cond))
                for x in trig:
                    mm = re.search(r"\banimelemtime\s*\(\s*(\d+)\s*\)"
                                   r"\s*<\s*0", x, re.I)
                    if mm:
                        stop = int(mm.group(1)) - 1
                        if stop > 0:
                            acts.setdefault(state, []).append(
                                (stop, 17, 0, cond))
            elif frame is None:
                continue
            elif ctype == "turn":
                acts.setdefault(state, []).append((frame, 0, 0, cond))
            elif ctype == "posadd":
                if not cond:
                    continue                  # plain posadds already in PosTab
                m = re.match(r"(-?\d+(?:\.\d+)?)", ctrl.get("x", "0"))
                dx = int(round(float(m.group(1)) / coord_scale)) if m else 0
                if dx:
                    acts.setdefault(state, []).append((frame, 1, dx, cond))
            elif ctype == "targetfacing":
                m = re.match(r"(-?\d+(?:\.\d+)?)",
                             ctrl.get("value", "1"))
                if not m:
                    continue                  # expression -> skip
                arg = int(float(m.group(1)))
                acts.setdefault(state, []).append((frame, 2, arg, cond))
            elif ctype == "targetlifeadd":
                raw = ctrl.get("value", "0")
                m = re.match(r"(-?\d+(?:\.\d+)?)", raw)
                if m:
                    arg = int(float(m.group(1)))
                else:
                    # `IfElse((Var(1)), strong, normal)` selects the MAX-mode
                    # damage variant; Var(1) is zero outside MAX, so keep the
                    # normal branch.  The engine still applies its own MAX
                    # bonus when the attacker is powered up.
                    m = re.match(
                        r"ifelse\s*\(\s*\(?\s*var\s*\(\s*\d+\s*\)\s*\)?\s*,"
                        r"\s*-?\d+(?:\.\d+)?\s*,\s*(-?\d+(?:\.\d+)?)\s*\)\s*$",
                        raw, re.I)
                    if not m:
                        # KOF throw/counter damage is authored as
                        # -floor((((N-var(21))*fvar(7))*fvar(0))*attack/100).
                        # The combo scalar var(21) is zero at throw start; keep
                        # the base N and apply the same 2x HP-scale conversion as
                        # HitDefs.  Other expressions remain unported.
                        m = re.match(
                            r"-floor\(\(\(\((\d+)\s*-\s*(?:var\(21\)|ifelse\()",
                            raw, re.I)
                        if not m:
                            # Yuri's throws spell the same HP-scaled damage as
                            # ceil(N*attack*-0.01); keep the base N.
                            m = re.match(
                                r"ceil\(\s*(\d+)\s*\*.*?\*\s*-\s*0?\.01\s*\)",
                                raw, re.I)
                        if not m:
                            continue
                        arg = -int(round(int(m.group(1)) * damage_scale))
                    else:
                        arg = int(float(m.group(1)))
                if not arg:
                    continue
                # A single controller may list several elements
                # (`AnimElem = 3 || AnimElem = 5 || ...`).  Each one is a
                # separate hit of the throw sequence, so emit one row per
                # element; keeping only the first turned Takuma's six-kick
                # Shouran Kyaku into a single-damage throw.
                elem_frames = []
                for x in trig:
                    elem_frames += [int(em.group(1)) - 1 for em in
                                    re.finditer(r"\banimelem\s*=\s*(\d+)",
                                                x, re.I)]
                if elem_frames:
                    for fr in sorted(set(elem_frames)):
                        acts.setdefault(state, []).append((fr, 3, arg, cond))
                elif frame is not None:
                    acts.setdefault(state, []).append((frame, 3, arg, cond))
            elif ctype == "targetstate":
                m = re.match(r"(-?\d+(?:\.\d+)?)",
                             ctrl.get("value", "0"))
                if not m:
                    continue                  # expression -> skip
                arg = int(float(m.group(1)))
                acts.setdefault(state, []).append((frame, 4, arg, cond))
            elif ctype == "velset":
                # AnimElem- and exact Time-triggered VelSet -> op5
                # velset.x (px/frame, signed, facing-relative) + op15
                # velset.y (quarter-px/frame, screen-space, negative =
                # rising). Each trigger produces one row per axis.
                for x in trig:
                    frames = [int(em.group(1)) - 1 for em in
                              re.finditer(r"\banimelem\s*=\s*(\d+)", x, re.I)]
                    frames += [0x80 | int(tm.group(1)) for tm in
                               re.finditer(r"\btime\s*=\s*(\d+)\b", x, re.I)]
                    for fr in frames:
                        xv = ctrl.get("x")
                        if xv is not None:
                            m = re.match(r"(-?\d+(?:\.\d+)?)", xv)
                            if not m:
                                # System dodges spell the normal speed in an
                                # ifelse(): e.g. Ralf/Clark
                                #   ifelse((PrevStateNo=100 || var(16)=1),7.5,5)
                                #   ifelse(var(16)=1,-7.5,-5)
                                # The condition selects a powered-up/extra
                                # dodge; use the else branch for the normal
                                # ESQ_F/ESQ_B path instead of dropping the
                                # velocity and leaving the roll stationary.
                                if not re.search(
                                        r"prevstateno|var\s*\(\s*16\s*\)",
                                        xv, re.I):
                                    continue  # jump/gethit expression
                                m = re.search(
                                    r",\s*(-?\d+(?:\.\d+)?)\s*,"
                                    r"\s*(-?\d+(?:\.\d+)?)\s*\)\s*$",
                                    xv)
                                if not m:
                                    continue  # complex expression -> skip
                                vx = int(round(float(m.group(2))
                                               / coord_scale))
                            else:
                                vx = int(round(float(m.group(1))
                                               / coord_scale))
                            acts.setdefault(state, []).append(
                                (fr, 5, vx & 0xFF, cond))
                        yv = ctrl.get("y")
                        if yv is not None:
                            m = re.match(r"(-?\d+(?:\.\d+)?)", yv)
                            if not m:
                                continue      # expression -> skip
                            vy = int(round(float(m.group(1)) * 4))
                            acts.setdefault(state, []).append(
                                (fr, 15, vy & 0xFF, cond))
    for state in binds:
        binds[state].sort()
    for state in acts:
        acts[state].sort()

    # hitdefpersist states carry no HitDef of their own -- inherit the move
    # row from whichever state ChangeStates into them
    for state, ctrls in statedefs.items():
        if state in moves or                 headers.get(state, {}).get("hitdefpersist", "0") != "1":
            continue
        for donor, dctrls in statedefs.items():
            if donor not in moves:
                continue
            for c in dctrls:
                if c.get("type", "").lower() == "changestate" and                         c.get("value", "").split(",")[0].strip() == str(state):
                    moves[state] = dict(moves[donor])
                    break
            if state in moves:
                break
    return (moves, posadds, powadds, headers, statedefs, binds, acts,
            reversals, hitdef_lists, snds, hitsnds, exprows)


def parse_cmd(path, buttons, move_ids):
    """Extract one-button attacks from CMD State -1 entries.

    Returns {"stand": [...], "crouch": [...], "air": [...]} of
    (pad_mask, internal_state_id) pairs.  Crouch attacks are the entries
    that require "holddown"; air attacks trigger on statetype A.
    """
    entries = []
    entry = None
    for raw in open(path, encoding="utf-8-sig"):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if re.match(r"\[command\]", line, re.I):
            entry = None
            continue
        if re.match(r"\[state(?:def)?\s+-1\b", line, re.I):
            entry = {"triggers": []}
            entries.append(entry)
            continue
        if entry is None or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        key = key.lower()
        entry[key] = value
        if key.startswith("trigger"):
            entry["triggers"].append(value)

    # first-wins: sliced states (one mugen state -> several sids) resolve
    # to the first slice sid
    state_to_sid = {}
    for _sid, _state in move_ids.items():
        state_to_sid.setdefault(_state, _sid)
    out = {"stand": [], "crouch": [], "air": []}
    for entry in entries:
        if entry.get("type", "").lower() != "changestate":
            continue
        try:
            state = int(float(entry.get("value", "-1").split(",", 1)[0]))
        except ValueError:
            continue
        sid = state_to_sid.get(state)
        if sid is None:
            continue
        triggers = entry["triggers"]
        required = set()
        rejected = set()
        st_s = st_a = False
        for trigger in triggers:
            required.update(re.findall(r'command\s*=\s*"([^"]+)"',
                                       trigger, re.I))
            rejected.update(re.findall(r'command\s*!=\s*"([^"]+)"',
                                       trigger, re.I))
            if re.search(r"statetype\s*=\s*S", trigger, re.I):
                st_s = True
            if re.search(r"statetype\s*=\s*A", trigger, re.I):
                st_a = True
        if "holddown" in required:
            cls = "crouch"
        elif st_a:
            cls = "air"
        elif st_s and "holddown" in rejected:
            cls = "stand"
        else:
            continue
        names = required - {"holddown"}
        if len(names) != 1:
            continue
        command = next(iter(names))
        if command in buttons:
            out[cls].append((buttons[command], sid))
    attack_btns = {k: v for k, v in buttons.items() if k in "xyab"}
    for cls, rows in out.items():
        if len(rows) != len(attack_btns):
            raise SystemExit(f"CMD {cls} attack mapping incomplete: {rows}")
    return out


# ---- command/motion extraction ------------------------------------------
# The SNES engine keeps a per-fighter ring of (facing-relative direction
# nibble, newly pressed buttons) and runs a backward matcher over generated
# tables.  Direction bits are facing-relative: U=1 D=2 F=4 B=8 (diagonals
# OR their cardinals).  Button bits: x=1 y=2 a=4 b=8 c=16 z=32 s=64.
DIR_TOK = {"u": 1, "d": 2, "f": 4, "b": 8,
           "uf": 5, "ub": 9, "df": 6, "db": 10}
BTN_TOK = {"x": 1, "y": 2, "a": 4, "b": 8, "c": 16, "z": 32, "s": 64}
HOLD_CMD = {"holdup": 1, "holddown": 2, "holdfwd": 4, "holdback": 8}

# Normal-attack slots that the cancel gate covers.  Strong punches/kicks
# open their special-cancel window by the middle of the animation; light
# normals keep the source's own var(1) window (or cancel on contact when
# the source has no window at all).
CANCEL_NORMAL_SIDS = tuple(range(5, 27))
CANCEL_STRONG_ORDER = (6, 8, 20, 22, 24, 26)
CANCEL_STRONG_SIDS = frozenset(CANCEL_STRONG_ORDER)


def dir_token(part):
    """MUGEN case convention: uppercase B is the back direction while
    lowercase b is the b button.  Other direction symbols are
    case-insensitive."""
    if part == "b":
        return 0
    return DIR_TOK.get(part.lower(), 0)


def btn_token(part):
    """Lowercase-only for b (uppercase B means the back direction); the
    remaining button names are case-insensitive."""
    if part == "B":
        return 0
    return BTN_TOK.get(part.lower(), 0)


def parse_command_defs(path):
    """[Command] blocks -> {name: (held_dirs, [(dir, btn), ...], window)}.

    held_dirs collects /-prefixed (hold) direction tokens; the element list
    keeps the press sequence.  A command we cannot model ($ wildcards, >
    ordering, ~NN charge holds) is stored with elems=None so rule
    extraction can still fold it into held-dir conditions.
    """
    cmds = {}
    name = None
    cmd_time = 15
    in_cmd = False
    last_def = None
    for raw in open(path, encoding="utf-8-sig"):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            in_cmd = bool(re.match(r"\[command\]", line, re.I))
            name = None
            cmd_time = 15
            last_def = None
            continue
        if not in_cmd or "=" not in line:
            continue
        key, value = (p.strip() for p in line.split("=", 1))
        key = key.lower()
        if key in ("time", "command.time"):
            cmd_time = int(float(value))
            if last_def in cmds:
                held, elems, _ = cmds[last_def]
                cmds[last_def] = (held, elems, cmd_time)
            continue
        if key == "name":
            name = value.strip('"')
            continue
        if key != "command" or name is None:
            continue
        held = 0
        elems = []
        ok = True
        for token in value.split(","):
            token = token.strip()
            rel = False
            charge = re.match(r"^~(\d+)([a-z]+)$", token, re.I)
            if charge:
                charge_frames = int(charge.group(1))
                token = charge.group(2)
            else:
                charge_frames = 0
            if token.startswith("~") and not token[1:2].isdigit():
                token = token[1:]
                rel = True                    # ~D/~F: dir-release element
            if not token or token.startswith((">", "/", "$")) or \
                    token[0].isdigit() or "~" in token:
                if token.startswith(("/", "$")):
                    # /F or $F: direction held, not pressed ($F also covers
                    # the diagonals -- a looser hold is close enough)
                    body = token[1:].lstrip("$")
                    held |= dir_token(body)
                    continue
                ok = False
                break
            d = b = 0
            for part in token.split("+"):
                dt = dir_token(part)
                bt = btn_token(part)
                if dt and not bt:
                    d |= dt
                elif bt and not dt:
                    b |= bt
                elif dt and bt:
                    ok = False                # genuinely ambiguous symbol
                else:
                    ok = False
            if not ok or (d == 0 and b == 0):
                ok = False
                break
            if rel:
                if b or not d:
                    ok = False                # ~button releases unsupported
                    break
                d |= 0x40                     # release flag on the dir byte
            if charge_frames:
                # The runtime charge matcher models a ~40<dir> prefix: any
                # single held direction at least 40 ticks before the finisher
                # (back for Psycho Crusher/Knee Press, down for Head Press/
                # Devil Reverse).  Bit 5 marks the charged element.
                if b or not d or charge_frames != 40:
                    ok = False
                    break
                d |= 0x20
            elems.append((d, b))
        if ok and name is not None:
            if name in cmds:
                # same-name defs are alternative inputs (e.g. x vs y
                # finishers): register as separate motions name#2.. so each
                # produces its own matcher rule (the matcher's button test
                # is a superset check -- OR-ing btn bits would not work)
                i = 2
                while f"{name}#{i}" in cmds:
                    i += 1
                last_def = f"{name}#{i}"
                cmds[last_def] = (held, elems, cmd_time)
            else:
                last_def = name
                cmds[last_def] = (held, elems, cmd_time)
    return cmds


def apply_input_calibration(cmddefs, profile):
    """Apply the shared command windows to any character's CMD table."""
    if not profile:
        return
    system = profile.get("system_command_frames", {})
    prefixes = profile.get("special_prefix_frames", {})
    ordinary = {
        "FF", "BB", "ESQ_L", "ESQ_L_PAIR", "ESQ_F", "ESQ_F_PAIR",
        "ESQ_B", "ESQ_B_PAIR", "DODGE", "CD", "CHARGE", "MAX_ON",
        "RECOVERY", "THROW", "TAUNT", "X", "Y", "A", "B", "C",
        "Z", "START", "HOLDFWD", "HOLDBACK", "HOLDUP", "HOLDDOWN",
        "DOWN_A", "DOWN_B", "FWD", "BACK", "UP", "DOWN",
    }
    for name, (held, elems, window) in list(cmddefs.items()):
        base = name.split("#", 1)[0]
        upper = base.upper()
        if base in system:
            window = system[base]
        elif upper not in ordinary:
            window = profile["special_default_frames"]
            for prefix, frames in sorted(prefixes.items(),
                                         key=lambda item: -len(item[0])):
                if upper.startswith(prefix.upper()):
                    window = frames
                    break
        cmddefs[name] = (held, elems, window)


def apply_button_calibration(cfg, buttons):
    """Apply a SNES button layout from the input calibrator.

    Keys are MUGEN command buttons (x/y/a/b/c/z/s); values are SNES labels
    (A/B/X/Y/L/R/START) or raw JOY_* masks.  The global CHARS layout is only a
    default: entries here let one fighter diverge without touching the engine.
    """
    for key, value in (buttons or {}).items():
        if key not in BTN_TOK:
            raise ValueError(
                f"input calibration: unknown command button {key!r}")
        mask = value if isinstance(value, int) else SNES_BTN_MASK.get(
            str(value).strip().upper())
        if not mask:
            raise ValueError(
                f"input calibration: invalid SNES button {value!r} for {key!r}")
        cfg.setdefault("buttons", {})[key] = mask


def button_layout(data, name):
    """Merge the calibrator's default button layout with a fighter's override."""
    layout = data.get("buttons") or {}
    buttons = dict(layout.get("default") or {})
    buttons.update((layout.get("characters") or {}).get(name) or {})
    return buttons


def resolve_input_calibration(name, cfg):
    """Load the timing profile and button layout assigned to a fighter."""
    path = os.path.join(ROOT, "assets", "calibration", "input_profiles.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    apply_button_calibration(cfg, button_layout(data, name))
    profile_name = (cfg.get("calibration_profile") or
                    data.get("assignments", {}).get(name))
    return data.get("profiles", {}).get(profile_name) if profile_name else None


def parse_neg1(path):
    """[State -1] blocks -> [{"name", "type", "value", "triggers"}].

    The block label is the move name authored by the source CMD (e.g.
    "[State -1, Oniyaki (weak)]").  build_command_list() keeps it so the
    PRACTICE command list can show a friendly label instead of the internal
    state number.
    """
    entries = []
    entry = None
    for raw in open(path, encoding="utf-8-sig"):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"\[state(?:def)?\s+-1\b\s*,?\s*([^\]]*)\]", line,
                     re.I)
        if m:
            entry = {"name": m.group(1).strip(), "triggers": []}
            entries.append(entry)
            continue
        if line.startswith("["):
            entry = None
            continue
        if entry is None or "=" not in line:
            continue
        key, value = (p.strip() for p in line.split("=", 1))
        key = key.lower()
        entry[key] = value
        if key.startswith("trigger"):
            entry["triggers"].append((key, value))
    return entries


def motion_rank(rule, cmddefs):
    """Sort key shared by the first and the post-shortcut rule sorts."""
    rec = cmddefs.get(rule["motion"])
    if not rec or not rec[1]:
        return (0, 0)
    bits = 0
    for _dir, btn in rec[1]:
        bits |= btn or 0
    return (len(rec[1]), bin(bits).count("1"))


# KOF's documented motion shortcuts (KOF'98/99/2002):
#   HCF = B, D, F              (diagonals optional)
#   HCB = F, D, B
#   DP  = F, D, F              (classic F, D, DF still accepted)
#   RDP = B, D, B              (classic B, D, DB still accepted)
# QCF/QCB keep their diagonals: a two-input 2,3+P / 2,1+P would collide
# with crouching attacks and is not a documented KOF shortcut.
_SHORTCUT_HALF = (
    ((8, 10, 2, 6, 4), (8, 2, 4)),      # HCF
    ((4, 6, 2, 10, 8), (4, 2, 8)),      # HCB
)
_SHORTCUT_DP = (
    ((4, 2, 6), (4, 2, 4)),             # DP
    ((8, 2, 10), (8, 2, 8)),            # RDP
)


def _dir_meta(d):
    return d & 0xF0


def shortcut_elems(elems):
    """Return the documented shortcut for a motion, or None.

    Half-circle diagonals are optional everywhere the half-circle appears
    (HCF/HCB, including their x2 and combined super forms).  DP/RDP are
    shortened only when the whole command is the DP/RDP itself, so a
    forward+QCF input does not acquire an accidental extra rule.
    """
    if not elems:
        return None
    dirs = [d & 0x0F for d, _b in elems]
    # CMD files often put the button in a final (0, button) element; strip
    # those button-only tails before deciding whether this is a pure DP/RDP.
    core_dirs = list(dirs)
    while core_dirs and core_dirs[-1] == 0:
        core_dirs.pop()
    if core_dirs in ([4, 2, 6], [8, 2, 10]):
        patterns = _SHORTCUT_DP
    else:
        patterns = _SHORTCUT_HALF
    patterns = sorted(patterns, key=lambda item: -len(item[0]))
    out = []
    changed = False
    i = 0
    while i < len(elems):
        matched = False
        for pat, short in patterns:
            if dirs[i:i + len(pat)] != list(pat):
                continue
            # An interior button or charge/release flag cannot be dropped.
            if any(elems[i + k][1] or _dir_meta(elems[i + k][0])
                   for k in range(1, len(pat) - 1)):
                continue
            first_d, first_b = elems[i]
            last_d, last_b = elems[i + len(pat) - 1]
            for j, sd in enumerate(short):
                if j == 0:
                    out.append((sd | _dir_meta(first_d), first_b))
                elif j == len(short) - 1:
                    out.append((sd | _dir_meta(last_d), last_b))
                else:
                    out.append((sd, 0))
            i += len(pat)
            changed = True
            matched = True
            break
        if matched:
            continue
        out.append(elems[i])
        i += 1
    return out if changed else None


def apply_half_circle_shortcuts(cmddefs):
    """Replace HCF/HCB records with their diagonal-free matcher form.

    The classic input still matches because the matcher may skip the extra
    diagonal entries.  DP/RDP are kept classic here: their shortcut ends in
    F/B instead of DF/DB, so both variants need their own rule.
    """
    for name, (held, elems, window) in list(cmddefs.items()):
        if not elems:
            continue
        dirs = [d & 0x0F for d, _b in elems]
        core_dirs = list(dirs)
        while core_dirs and core_dirs[-1] == 0:
            core_dirs.pop()
        if core_dirs in ([4, 2, 6], [8, 2, 10]):
            continue
        short = shortcut_elems(elems)
        if short:
            cmddefs[name] = (held, short, window)


def add_shortcut_rules(rules, cmddefs):
    """Append shortcut matcher rules without adding command-list rows."""
    out = []
    short_names = {}
    seen = set()
    for rule in rules:
        out.append(rule)
        rec = cmddefs.get(rule["motion"])
        if not rec or not rec[1]:
            continue
        short = shortcut_elems(rec[1])
        if not short:
            continue
        key = (rule["motion"], tuple(short))
        name = short_names.get(key)
        if name is None:
            base = rule["motion"] + "#SC"
            name = base
            n = 2
            while name in cmddefs:
                name = f"{base}{n}"
                n += 1
            cmddefs[name] = (rec[0], short, rec[2])
            short_names[key] = name
        dedup = (rule["state"], name, rule["held"], rule["nheld"],
                 rule["posture"], rule["dist"], rule["nstate"])
        if dedup in seen:
            continue
        seen.add(dedup)
        nr = dict(rule)
        nr["motion"] = name
        nr["shortcut"] = True
        out.append(nr)
    return out


def cmd_rules(path, cmddefs, wired):
    """State -1 entries -> ordered matcher rules for wired states.

    wired maps MUGEN state -> internal state id.  Each emitted rule:
    {"motion": command name, "held": int, "nheld": int,
     "posture": int bitmask S=1 C=2 A=4, "state": internal sid}
    A triggerall+triggerN group is skipped when it needs something the
    matcher cannot evaluate (power, p2*, stateno, time, movecontact...).
    """
    entries = parse_neg1(path)

    cmd_re = re.compile(r'command\s*(=|!=)\s*"([^"]+)"', re.I)
    st_re = re.compile(r'state(?:type)?\s*(=|!=)\s*([sca])\b', re.I)
    ok_re = re.compile(
        r"^(command\s*(=|!=)\s*\"[^\"]+\"|ctrl(\s*=\s*1)?|"
        r"statetype\s*(=|!=)\s*[sca]\b|var\(1\)|power\s*>=\s*\d+|"
        r"1)\s*$", re.I)
    drop_re = re.compile(
        r"p2\w*\s*(=|<|>|!=)|stateno|movecontact|time\s*[<>=]|"
        r"hitdefattr|anim\s*=|roundstate|numhelper|trigger\d", re.I)

    dist_re = re.compile(r"p2bodydist\s+x\s*<\s*(\d+)", re.I)
    p2ok_re = re.compile(r"^\(?\s*p2(statetype|movetype)\b", re.I)
    nstate_re = re.compile(r"^stateno\s*!=\s*(\d+)\s*$", re.I)
    rules = []
    for entry in entries:
        if entry.get("type", "").lower() != "changestate":
            continue
        try:
            mstate = int(float(entry.get("value", "-1").split(",", 1)[0]))
        except ValueError:
            continue
        sid = wired.get(mstate)
        if sid is None:
            continue
        base = [v for k, v in entry["triggers"] if k == "triggerall"]
        groups = {}
        for k, v in entry["triggers"]:
            if k == "triggerall":
                continue
            m = re.match(r"trigger(\d+)", k)
            groups.setdefault(int(m.group(1)) if m else 1, []).append(v)
        for conds in [base + g for g in groups.values()] or [base]:
            held = nheld = posture = 0
            dist = vgate = nstate = 0
            motions = []
            bad = False
            for line in conds:
                m = dist_re.search(line)
                if m:
                    # body distance counts edge-to-edge; our gate compares
                    # center x -- widen by ~both half widths (30px)
                    dist = min(127, int(m.group(1)) + 30)
                    vgate = 1
                    continue
                if p2ok_re.match(line):
                    # p2statetype S/C and p2movetype != H collapse into the
                    # throw gate: victim grounded and out of hitstun
                    vgate = 1
                    continue
                m = nstate_re.match(line)
                if m:
                    ns = wired.get(int(m.group(1)))
                    if ns is None:
                        bad = True
                        break
                    nstate = ns
                    continue
                if "||" in line or drop_re.search(line):
                    bad = True
                    break
                if not ok_re.match(line):
                    bad = True
                    break
                for op, cname in cmd_re.findall(line):
                    if cname in HOLD_CMD:
                        if op == "=":
                            held |= HOLD_CMD[cname]
                        else:
                            nheld |= HOLD_CMD[cname]
                    elif cname in cmddefs and cmddefs[cname][1] is not None:
                        if op == "!=":
                            bad = True
                            break
                        # same-name alternate defs (cname#2..) are extra
                        # motions for the same target
                        v = 0
                        while True:
                            mname = cname if v == 0 else f"{cname}#{v + 1}"
                            if mname not in cmddefs:
                                break
                            motions.append(mname)
                            v += 1
                    elif cname in BTN_TOK:
                        if op == "!=":
                            bad = True
                            break
                        # raw button name ("y"): synthesize a one-element
                        # motion so proximity commands like the throw work
                        cmddefs.setdefault(
                            cname, (0, [(0, BTN_TOK[cname])], 15))
                        motions.append(cname)
                    else:
                        bad = True
                        break
                if bad:
                    break
                for op, st in st_re.findall(line):
                    bit = {"s": 1, "c": 2, "a": 4}[st.lower()]
                    posture = posture | bit if op == "=" else posture
                    if op == "!=":
                        posture |= 7 & ~bit
            if bad or not motions:
                continue
            if re.search(r"var\(1\)", " ".join(conds)):
                posture |= 3  # combo condition: grounded with control
            for motion in motions:
                rules.append({"motion": motion, "held": held,
                              "nheld": nheld, "posture": posture or 7,
                              "dist": dist | (vgate << 7), "nstate": nstate,
                              "state": sid, "mstate": mstate,
                              "label": entry.get("name", "")})

    # CmdTry scans the table from the newest press backwards and keeps the
    # first rule that completes.  A shorter motion is a subsequence of its
    # own super tail (QCFx2+x also completes QCF+x, and even DP+x), so the
    # longer motions must be tried first.  Combined-button rules (x+y)
    # likewise have to precede their single-button halves.  Stable sort
    # keeps the generated order among equally specific rules.
    rules.sort(key=lambda rule: motion_rank(rule, cmddefs), reverse=True)
    return rules


# ---- PRACTICE command list ------------------------------------------------
# Every fighter gets a compact, self-contained command list in its own
# generated-data bank.  A row is {sid, category, name, command}; the runtime
# uses the sid to mark the row when P1/P2 actually enters that move.
#
# Categories are deliberately coarse: the practice submenu uses them as a
# colour-coded tag and the detail line spells them out.
# Characters with a hand-written descriptor in fight.asm.  Their descriptor
# resolves the command list through F_TBANK; the mass-import descriptors get
# an explicit 24-bit pointer because their lists are packed into free tails.
CMD_POOL_ROWS = {}
FIXED_CMD_LIST = {
    "iori", "kyo", "rugal", "omegarugal", "saisyu", "heidern",
    "takuma", "clark", "ralf", "leona", "mature", "vice", "benimaru",
    "daimon",
}

CMD_CATEGORIES = (
    ("NRM", "NORMAL"),
    ("CMD", "COMMAND"),
    ("SPC", "SPECIAL"),
    ("SUP", "SUPER"),
    ("MAX", "MAX"),
    ("THR", "THROW"),
    ("SYS", "SYSTEM"),
)
CMD_CAT_NORMAL, CMD_CAT_COMMAND, CMD_CAT_SPECIAL, CMD_CAT_SUPER, \
    CMD_CAT_MAX, CMD_CAT_THROW, CMD_CAT_SYSTEM = range(len(CMD_CATEGORIES))

# SNES pad labels keyed by the JOY_* masks used in the per-character cfg.
# $4219/$4218 layout: A=$0080, B=$8000, X=$0040, Y=$4000.
SNES_BTN_TEXT = {0x0080: "A", 0x8000: "B", 0x0040: "X", 0x4000: "Y",
                 0x0020: "L", 0x0010: "R", 0x1000: "START"}
SNES_BTN_MASK = {v: k for k, v in SNES_BTN_TEXT.items()}
DIR_TEXT = {1: "U", 2: "D", 4: "F", 8: "B",
            5: "UF", 6: "DF", 9: "UB", 10: "DB"}
MOTION_TEXT = {
    ("D", "DF", "F"): "QCF",
    ("D", "DB", "B"): "QCB",
    ("F", "D", "DF"): "DP",
    ("B", "D", "DB"): "RDP",
    ("B", "DB", "D", "DF", "F"): "HCF",
    ("F", "DF", "D", "DB", "B"): "HCB",
    ("B", "DB", "D", "DF", "F", "B"): "HCBF",
    ("D", "B", "F"): "DBF",
    ("D", "DF", "F", "D", "DF", "F"): "QCFx2",
    ("D", "DB", "B", "D", "DB", "B"): "QCBx2",
    ("D", "DB", "B", "DB", "D", "DF", "F"): "QCBHCF",
    ("D", "DF", "F", "D", "DB", "B"): "QCFHCB",
    ("F", "DF", "D", "DB", "B", "F", "DF", "D", "DB", "B"): "HCBx2",
    ("B", "DB", "D", "DF", "F", "B", "DB", "D", "DF", "F"): "HCFx2",
    ("F", "DF", "D", "DB", "B", "F"): "HCBF2",
    ("D", "DF", "F", "DF", "D", "DB", "B"): "QCF,HCB",
    ("D", "DF", "F", "DF", "B"): "QCF,DB",
    ("DF", "B", "DF", "B"): "DFBx2",
    ("DB", "DB"): "DBx2",
    ("DF", "DF"): "DFx2",
    ("F", "D", "DF", "F", "D", "DF", "F"): "DP,QCF",
    ("F", "B", "DB", "D", "DF", "F"): "F,HCF",
    ("F", "B", "F"): "F,B,F",
    ("F", "F"): "F,F",
    ("B", "B"): "B,B",
    ("D", "F"): "DF",
}
# Physical pad action for the L/R system moves.  PushHist (fight.asm) reroutes
# the shoulder buttons into the legacy MUGEN tokens used by the CMD files
# (L -> c, R -> y|b, L+R -> s), so the command list must show the button the
# player actually presses instead of those internal tokens.
PHYSICAL_SYS_CMD = {
    47: "L+R",      # taunt
    67: "R",        # blowback
    69: "L",        # neutral dodge
    94: "L + BACK",  # back roll
    95: "L + FWD",   # forward roll
}
# CMD block labels that are boilerplate rather than a move name.
GENERIC_CMD_LABELS = re.compile(
    r"^(label|varset|var\d*|displaytoclipboard|reset|count|condition\d*|"
    r"special_?\d+|sys_?\d+|state\d*|\d+|.*helper.*|.*check.*|"
    r".*no state.*|.*reset.*|.*count.*)$", re.I)


def _read_text_any(path):
    data = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis", "latin1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin1", errors="replace")


def _source_cmd_path(cfg):
    """Original MUGEN CMD next to the sanitized <Char>_SNES.cmd, if any."""
    snes = os.path.join(ROOT, cfg["cmd"])
    cdir = os.path.dirname(snes)
    if not os.path.isdir(cdir):
        return None
    candidates = []
    for deff in sorted(glob.glob(os.path.join(cdir, "*.def"))):
        try:
            text = _read_text_any(deff)
        except OSError:
            continue
        m = re.search(r"^\s*cmd\s*=\s*(.+?)\s*$", text, re.I | re.M)
        if m:
            p = os.path.join(cdir, m.group(1).split(";", 1)[0].strip())
            if os.path.exists(p):
                candidates.append(p)
    for p in sorted(glob.glob(os.path.join(cdir, "*.cmd"))):
        if "_SNES" not in os.path.basename(p):
            candidates.append(p)
    return candidates[0] if candidates else None


def _state_labels(path):
    """[State -1, name] label(s) per MUGEN statedef value."""
    out = {}
    if not path or not os.path.exists(path):
        return out
    text = _read_text_any(path)
    blocks = re.split(r"(?=\[State\s+-1\b)", text, flags=re.I)
    for block in blocks:
        m = re.match(r"\[State\s+-1\b\s*,?\s*([^\]]*)\]", block, re.I)
        if not m:
            continue
        label = m.group(1).strip()
        vm = re.search(r"^\s*value\s*=\s*(-?\d+)", block, re.I | re.M)
        if not vm:
            continue
        out.setdefault(int(vm.group(1)), []).append(label)
    return out


def _readme_moves(cfg):
    """English move names from <char>/txt/ReadMe(ENG).txt (best effort)."""
    snes = os.path.join(ROOT, cfg["cmd"])
    cdir = os.path.dirname(snes)
    paths = []
    for root, _dirs, files in os.walk(cdir):
        for f in files:
            low = f.lower()
            if "readme" in low and "eng" in low and low.endswith(".txt"):
                paths.append(os.path.join(root, f))
    out = []
    for path in sorted(paths)[:1]:
        try:
            text = _read_text_any(path)
        except OSError:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            m = re.match(r"^(.{3,48}?)\s+-\s+(.+)$", line)
            if not m:
                continue
            name, command = m.group(1).strip(), m.group(2).strip()
            # Case matters: uppercase B/D/F/U are directions, lowercase
            # x/y/a/b/z/c/s are buttons.  Uppercasing the whole line would
            # turn the button "b" into a back direction.
            dirs = re.findall(r"\b(?:DB|DF|UB|UF|D|U|F|B)\b", command)
            if not dirs:
                continue
            btns = set(re.findall(r"(?<![A-Za-z])[xyzabcs](?![A-Za-z])",
                                  command))
            if not btns:
                continue
            cls = ("punch" if btns & {"x", "y"} else "") + \
                  ("kick" if btns & {"a", "b"} else "")
            out.append((name, tuple(dirs), cls or "any"))
    return out


def _snes_button(cfg, bits):
    labels = []
    for name in ("x", "y", "a", "b", "c", "z", "s"):
        if bits & BTN_TOK[name]:
            mask = cfg.get("buttons", {}).get(name)
            labels.append(SNES_BTN_TEXT.get(
                mask, "START" if name == "s" else name.upper()))
    return "+".join(labels) if labels else "?"


def _dir_bits_text(bits):
    return DIR_TEXT.get(bits & 0x0F, "?")


def _motion_text(dirs):
    if not dirs:
        return ""
    key = tuple(dirs)
    if key in MOTION_TEXT:
        return MOTION_TEXT[key]
    return ",".join(dirs)


def _motion_text_compact(dirs):
    if not dirs:
        return ""
    key = tuple(dirs)
    if key in MOTION_TEXT:
        return MOTION_TEXT[key]
    # Unknown motion: no commas/spaces so the button still fits the HUD.
    return "".join(dirs)


def _short_motion(dirs):
    """Longest known prefix of a raw motion, used when the full one won't
    fit next to the button.  Exact matches are handled by _motion_text."""
    for n in range(len(dirs) - 1, 2, -1):
        name = MOTION_TEXT.get(tuple(dirs[:n]))
        if name:
            return name
    return None


def _command_text(rec, cfg, limit=11):
    """(held, elems, window) -> command notation.

    Try the readable form first ('QCF + Y'); if it does not fit the 11-cell
    HUD field, fall back to a compact form ('QCF+Y', 'CHG BF+Y', 'HLD D+U+Y').
    The old code truncated the whole string, cutting off exactly the button.
    """
    if not rec or rec[1] is None:
        return "?"
    held, elems, _window = rec
    hd = [DIR_TEXT[b] for b in (1, 2, 4, 8) if held & b] if held else []
    dirs = []
    btns = []
    charged = False
    for d, b in elems:
        dd = d & 0x0F
        if d & 0x20:
            charged = True
        if dd:
            dirs.append(_dir_bits_text(dd))
        if b:
            btns.append(_snes_button(cfg, b))
    # Drop repeats from multi-element definitions; the display only needs
    # the physical button(s) once.
    uniq = []
    for b in btns:
        if b not in uniq:
            uniq.append(b)
    button_text = "+".join(uniq)

    def build(compact, motion=None):
        parts = []
        if hd:
            parts.append(("HLD " if compact else "HOLD ") + "/".join(hd))
        mt = motion
        if mt is None:
            mt = (_motion_text_compact(dirs) if compact
                  else _motion_text(dirs))
        if charged and mt:
            mt = ("CHG " if compact else "CHARGE ") + mt
        elif charged:
            mt = "CHG" if compact else "CHARGE"
        if mt:
            parts.append(mt)
        sep = "+" if compact else " + "
        if button_text:
            parts.append(button_text)
        return sep.join(parts) if parts else "?"

    pretty = build(False)
    if len(pretty) <= limit:
        return pretty
    compact = build(True)
    if len(compact) <= limit:
        return compact
    short = _short_motion(dirs)
    if short:
        return build(True, ("CHG " + short) if charged else short)
    return compact


def _clean_move_label(label):
    """ROM font cannot draw Japanese; keep ASCII labels only."""
    label = (label or "").strip()
    if not label or GENERIC_CMD_LABELS.match(label):
        return ""
    if any(ord(c) > 0x7E for c in label):
        return ""
    return label


def _sanitize_hud_text(text, limit):
    text = unicodedata.normalize("NFKD", text or "")
    text = text.upper().replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    out = [c if c in CHARSET else " " for c in text]
    s = re.sub(r"\s+", " ", "".join(out)).strip()[:limit].rstrip()
    return s.rstrip(" +,-/").rstrip()


def _fit_command(text, limit=11):
    """Fit a command into the HUD field without cutting off its button.

    The previous code sliced the whole string at 11 cells, so long motions
    (CHARGE ..., raw direction lists) lost the trailing '+Y'/'+X' and the
    list showed no button at all.  Preserve the complete button suffix
    (including combined presses like B+A) and trim the motion instead.
    """
    s = _sanitize_hud_text(text, 64)
    if len(s) <= limit:
        return s
    buttons = set(SNES_BTN_TEXT.values())
    tokens = [p.strip() for p in s.split('+')]
    # Trailing run of physical button tokens: '+Y', '+Y+X', '+B+A', ...
    i = len(tokens)
    while i > 0 and tokens[i - 1] in buttons:
        i -= 1
    if i < len(tokens):
        suffix = '+' + '+'.join(tokens[i:])
        head = '+'.join(tokens[:i])
        # The hold/charge keyword is useful but not essential; dropping it
        # keeps the direction and both buttons on combined-button moves.
        if head.startswith(('HLD ', 'CHG ')):
            short_head = head.split(' ', 1)[1]
            if short_head and len(short_head) + len(suffix) <= limit:
                return short_head + suffix
        room = limit - len(suffix)
        if room >= 1:
            head = head[:room].rstrip(' +,-/')
            if head:
                return head + suffix
        return suffix[-limit:].lstrip('+')
    return s[:limit].rstrip(' +,-/')


def _move_category(sid, label, rec, max_sids=()):
    if sid in (5, 6, 7, 8, 19, 20, 21, 22, 23, 24, 25, 26):
        return CMD_CAT_NORMAL
    if sid == 67:
        return CMD_CAT_COMMAND
    if sid == 74:
        return CMD_CAT_THROW
    if sid in (85, 86, 87, 88, 89):
        return CMD_CAT_MAX if sid in max_sids else CMD_CAT_SUPER
    if sid == 58:
        buttons = 0
        if rec and rec[1]:
            for _d, b in rec[1]:
                buttons |= b
        is_max = "max" in (label or "").lower() or \
            bin(buttons).count("1") > 1
        return CMD_CAT_MAX if is_max else CMD_CAT_SPECIAL
    if sid == 96:
        return CMD_CAT_MAX
    if sid in (45, 46, 47, 69, 94, 95, 97):
        return CMD_CAT_SYSTEM
    if 48 <= sid <= 66:
        return CMD_CAT_SPECIAL
    if 78 <= sid <= 84:
        return CMD_CAT_SYSTEM
    return CMD_CAT_SPECIAL


def _readme_label(cfg, rec, sid, source_label):
    """Match a ReadMe command to a special/super row (motion + button)."""
    if sid not in (67,) and not (48 <= sid <= 89):
        return ""
    if not rec or not rec[1]:
        return ""
    dirs = []
    btn_bits = 0
    for d, b in rec[1]:
        dd = d & 0x0F
        if dd:
            dirs.append(DIR_TEXT[dd])
        btn_bits |= b
    cls = ""
    if btn_bits & (BTN_TOK["x"] | BTN_TOK["y"]):
        cls += "punch"
    if btn_bits & (BTN_TOK["a"] | BTN_TOK["b"]):
        cls += "kick"
    cls = cls or "any"
    all_matches = [(nm, rcls) for nm, rdirs, rcls in _readme_moves(cfg)
                   if rdirs == tuple(dirs)]
    exact = [nm for nm, rcls in all_matches if rcls == cls]
    loose = [nm for nm, rcls in all_matches
             if rcls in ("any", "punchkick")]
    if not exact and not loose:
        return ""
    # Exact punch/kick matches come first; a ReadMe that lists "x or y"
    # is a wildcard only when there is no exact button-class line.
    names = sorted(set(exact or loose), key=lambda s: (-len(s), s))
    name = names[0]
    # Weak/strong pairs share an input line in most ReadMes.
    strength = ""
    for b in (BTN_TOK["y"], BTN_TOK["b"]):
        if btn_bits & b:
            strength = "STRONG"
    for b in (BTN_TOK["x"], BTN_TOK["a"]):
        if btn_bits & b:
            strength = "WEAK" if not strength else strength
    if strength and "max" not in name.lower():
        suffix = " WEAK" if strength == "WEAK" else " STRONG"
        if len(name) + len(suffix) > 16:
            suffix = " W" if strength == "WEAK" else " S"
        name = f"{name}{suffix}"
    return name


def build_command_list(name, cfg, button_rows, rules, cmddefs, max_sids=()):
    """Rows for the PRACTICE command submenu, sorted for display.

    Each row: {"sid", "cat", "name", "cmd"}.  Names come from the sanitized
    CMD labels, the original MUGEN CMD, the English ReadMe, or a readable
    category fallback -- so every roster slot is usable even when the source
    has neither an ASCII label nor a ReadMe.
    """
    rows = {}
    # Standard normals are table-driven (ButtonTab) and do not appear in the
    # CMD State -1 block for most imports.
    inv = {}
    for k, v in cfg.get("buttons", {}).items():
        inv.setdefault(v, k)
    normal_defs = (
        ("stand", "STAND", ""),
        ("crouch", "CROUCH", "D + "),
        ("air", "JUMP", "AIR + "),
    )
    for cls, prefix, dpref in normal_defs:
        for mask, sid in button_rows.get(cls, []):
            mbtn = inv.get(mask)
            if mbtn not in BTN_TOK:
                continue
            tag = {"x": "LP", "y": "HP", "a": "LK", "b": "HK"}.get(mbtn, "?")
            cmd = dpref + _snes_button(cfg, BTN_TOK[mbtn])
            rows.setdefault(sid, {
                "sid": sid, "cat": CMD_CAT_NORMAL,
                "name": f"{prefix} {tag}", "cmd": cmd,
                "order": 0,
            })

    source = _state_labels(_source_cmd_path(cfg))
    for r in rules:
        if r.get("shortcut"):
            continue
        sid = r["state"]
        if sid in rows:
            continue
        motion = r["motion"]
        rec = cmddefs.get(motion)
        label = _clean_move_label(r.get("label"))
        if not label:
            for cand in source.get(r.get("mstate", -1), []):
                label = _clean_move_label(cand)
                if label:
                    break
        if not label:
            label = _clean_move_label(_readme_label(cfg, rec, sid, label))
        cat = cfg.get("cmd_categories", {}).get(
            sid, _move_category(sid, label, rec, max_sids))
        if not label:
            fallback = {
                45: "RUN FWD", 46: "BACK DASH", 47: "TAUNT",
                67: "BLOWBACK", 69: "DODGE", 74: "THROW",
                94: "ROLL BACK", 95: "ROLL FWD", 96: "MAX MODE",
                97: "CHARGE",
            }
            label = fallback.get(sid, CMD_CATEGORIES[cat][1])
        label = cfg.get("cmd_labels", {}).get(sid, label)
        rows[sid] = {
            "sid": sid, "cat": cat,
            "name": _sanitize_hud_text(label, 16),
            "cmd": _fit_command(
                cfg.get("cmd_text", {}).get(sid)
                or PHYSICAL_SYS_CMD.get(sid)
                or _command_text(rec, cfg), 11),
            "order": 1,
        }

    # Display order: normals first, then command/specials, supers, MAX,
    # throw and system; within a category keep the internal slot order.
    cat_rank = {
        CMD_CAT_NORMAL: 0, CMD_CAT_COMMAND: 1, CMD_CAT_SPECIAL: 2,
        CMD_CAT_SUPER: 3, CMD_CAT_MAX: 4, CMD_CAT_THROW: 5,
        CMD_CAT_SYSTEM: 6,
    }
    out = [r for r in rows.values() if r["name"] and r["cmd"]]
    out.sort(key=lambda r: (cat_rank.get(r["cat"], 9), r["sid"]))
    # The WRAM "seen" arrays and the on-screen pager are sized for 48 rows.
    out = out[:48]
    for r in out:
        r["name"] = _sanitize_hud_text(r["name"], 16)
        r["cmd"] = _fit_command(r["cmd"], 11)
    return out


def emit_command_list(name, rows, inc):
    """Append strings + table to a character's _spr.inc buffer."""
    for i, row in enumerate(rows):
        nids = [CHARSET.index(c) for c in row["name"]]
        cids = [CHARSET.index(c) for c in row["cmd"]]
        inc.append(f"{name}CmdName{i}: .db {len(nids)}," +
                   ",".join(str(v) for v in nids) + "\n")
        inc.append(f"{name}CmdKey{i}: .db {len(cids)}," +
                   ",".join(str(v) for v in cids) + "\n")
    inc.append(f"{name}CmdList:\n")
    inc.append(f"    .db {len(rows)}\n")
    for i, row in enumerate(rows):
        inc.append(f"    .db {row['sid']},{row['cat']}\n")
        inc.append(f"    .dw {name}CmdName{i},{name}CmdKey{i}\n")


def emit_command_pool():
    """Deduplicated string pool + per-character tables for mass imports.

    The PVSnesLib build allocates one compact section instead of one small
    block per fighter; repeated normal/system names and command strings are
    stored once.  The standalone build still uses the per-character files.
    """
    string_ids = {}
    strings = []

    def string_label(text):
        if text not in string_ids:
            label = f"CmdPool{len(strings)}"
            string_ids[text] = label
            strings.append((label, text))
        return string_ids[text]

    out = ["; generated by build_fight.py -- PRACTICE command lists\n"]
    for name in sorted(CMD_POOL_ROWS):
        rows = CMD_POOL_ROWS[name]
        out.append(f"{name}CmdList:\n    .db {len(rows)}\n")
        for row in rows:
            nlab = string_label(row["name"])
            clab = string_label(row["cmd"])
            out.append(f"    .db {row['sid']},{row['cat']}\n"
                       f"    .dw {nlab},{clab}\n")
    for label, text in strings:
        ids = [CHARSET.index(c) for c in text]
        out.append(f"{label}: .db {len(ids)}," +
                   ",".join(str(v) for v in ids) + "\n")
    # A character skipped this run (stale calibration, missing asset) still
    # has descriptors pointing at <name>CmdList.  Give it an empty list so
    # the ROM links; the practice command screen is informational only.
    # Check every roster entry, not just NEW_CHARS: Shingo is a fixed
    # descriptor but its table belongs in this pool.
    for name in sorted(CHARS):
        if name in CMD_POOL_ROWS or name in FIXED_CMD_LIST:
            continue
        out.append(f"{name}CmdList:\n    .db 0\n")
    open(os.path.join(OUT, "cmdlist_pool.inc"), "w").write("".join(out))


LAND_SID = 17                           # S_LAND: grounded recovery -> stand


def trans_rules(statedefs, headers, state_to_sid, buttons, state_to_sids=None):
    """ChangeState controllers inside wired statedefs -> TransTab rows.

    (from_sid, to_sid, kind, arg):
      kind 0 = on anim end            (AnimTime = 0)
      kind 1 = land when falling      (Vel Y > 0 && Pos Y >= -arg)
      kind 2 = air follow-up press    (Command = "<btn>" [|| "<btn>"] and
                                       Vel y < 0; arg = pad mask)
      kind 3 = on hit connect         (MoveHit -- super success poses)
      kind 4 = distance gate          (|p2.x - p1.x| <= arg.lo px and
                                       current frame >= arg.hi -- running
                                       grabs such as Shouran Kyaku)
    A lone `time > N` guard next to kind 1/2 is ignored (the ring only
    carries fresh presses anyway).  Controllers needing other trigger
    forms are skipped.

    A landing ChangeState whose target has no runtime slot (Ryo 1501,
    Robert 1301, King 1110...) still needs to fire: the source target is a
    grounded recovery pose (type=S, movetype=I), so it maps onto S_LAND.
    Without the row the fighter froze on the anim's trailing -1 hold for
    the 255-tick fallback -- the long recovery Ryo/Robert showed after
    their dive specials.
    """
    vel = re.compile(r"vel\s*y\s*(<|>)\s*(-?\d+(?:\.\d+)?)", re.I)
    cmd = re.compile(r'command\s*=\s*"([^"]+)"', re.I)
    land = re.compile(r"pos\s*y\s*>=\s*(-?\d+(?:\.\d+)?)", re.I)
    # MUGEN trigger groups: repeated `triggerN` lines are ANDed.  Imports
    # commonly spell the landing rule as two lines
    #   trigger1 = Pos Y >= 0
    #   trigger1 = Vel Y > 0
    # instead of the one-line form, so combine them by source trigger index.
    land_line = re.compile(r"^pos\s*y\s*>=\s*(-?\d+(?:\.\d+)?)", re.I)
    # Distance-gated ChangeState (Shouran Kyaku and other running grabs):
    # `P2bodydist X <= N` paired with an animation-element start.  Encoded as
    # kind 4, arg low byte = centre distance, high byte = first frame.
    p2dist = re.compile(r"p2bodydist\s+x\s*<=\s*(\d+)", re.I)
    elemtime_ge = re.compile(
        r"animelemtime\s*\(\s*(\d+)\s*\)\s*>=\s*(-?\d+(?:\.\d+)?)", re.I)
    elem_eq = re.compile(r"^\s*animelem\s*=\s*(\d+)\s*$", re.I)
    # Window guards such as `AnimElem = 5,> 0` or `AnimElemTime(5) > 0`
    # accompany a landing/ChangeState rule.  They do not define the rule and
    # must not mark the controller as unsupported: dropping it left Choi
    # (1500/1510 -> 1505) and other rising anti-airs on the animation's
    # 255-tick trailing hold after touching the floor.
    elem_window = re.compile(
        r"^\s*animelem\s*=\s*\d+\s*,\s*[<>]=?\s*-?\d+(?:\.\d+)?\s*$",
        re.I)
    elemtime_window = re.compile(
        r"^\s*animelemtime\s*\(\s*\d+\s*\)\s*[<>]\s*"
        r"-?\d+(?:\.\d+)?\s*$", re.I)
    if state_to_sids is None:
        state_to_sids = {st: [sid] for st, sid in state_to_sid.items()}
    rows = []
    for mstate, ctrls in statedefs.items():
        from_sids = state_to_sids.get(mstate)
        if not from_sids:
            continue
        def emit(to_sid, kind, arg):
            # A MUGEN state can own several runtime sids: slices and
            # alternate/MAX versions.  The old first-sid-only mapping left
            # the MAX/duplicate versions without landing rows, so a rising
            # anti-air on those sids stayed on its 255-tick hold after
            # touching the floor.
            for fsid in from_sids:
                rows.append((fsid, to_sid, kind, arg))
        for c in ctrls:
            if c.get("type", "").lower() != "changestate":
                continue
            try:
                mto = int(float(c.get("value", "-1").split(",", 1)[0]))
            except ValueError:
                continue
            to_sid = state_to_sid.get(mto)
            land_recovery = False
            if to_sid is None:
                # ChangeStates into native engine states (stand, walk...)
                # that are not wired in cfg["moves"]: sid 0 is the only
                # one a wired statedef legitimately targets (intro end)
                if mto == 0:
                    to_sid = 0
                else:
                    hdr = headers.get(mto, {})
                    if (hdr.get("type", "").strip().upper() == "S"
                            and hdr.get("movetype", "").strip().upper()
                            == "I"):
                        # Unwired landing recovery pose: resolve to S_LAND
                        # once the trigger is confirmed as a landing rule.
                        land_recovery = True
                    else:
                        continue
            trigs = c.get("triggers", [])
            trig_groups = c.get("trigger_groups", [])
            kind = arg = None
            dist = None
            elem_frame = 0
            rising = falling = False
            land_groups = {}
            fall_groups = set()
            names = []
            bad = False
            for ti, trig in enumerate(trigs):
                t = trig.strip()
                tgroup = (trig_groups[ti].lower()
                          if ti < len(trig_groups) else "")
                # `AnimTime = 0` and `!Animtime` are the same exit: the
                # animation has reached its last tick.  Several imports
                # (Brian) only use the latter, which used to leave their
                # root special without a link to the active hit state.
                if re.match(r"^(?:!\s*animtime|animtime\s*=\s*0)$", t,
                            re.I):
                    if kind is None:
                        kind = 0
                        arg = 0
                    continue
                if re.match(r"^movehit\b", t, re.I):
                    if kind is None:
                        kind = 3
                        arg = 0
                    continue
                if re.match(r"^time\s*>\s*\d+$", t, re.I):
                    continue                     # entry-tick guard: drop
                found = cmd.findall(t)
                if found:
                    for nm in found:
                        if nm not in buttons:
                            bad = True
                    names.extend(found)          # separate triggers = OR
                    continue
                dm = p2dist.search(t)
                if dm:
                    dist = int(dm.group(1))
                    continue
                em = elemtime_ge.search(t)
                if em:
                    # F_FRAME is the element index; start the gate at the
                    # element's first tick (one tick early for `>= 1`).
                    elem_frame = max(0, int(em.group(1)) - 1)
                    continue
                ee = elem_eq.match(t)
                if ee:
                    elem_frame = max(0, int(ee.group(1)) - 1)
                    continue
                if elem_window.match(t) or elemtime_window.match(t):
                    continue                  # window guard, not a rule
                m = vel.search(t)
                if m:
                    if m.group(1) == "<":
                        rising = True
                    else:
                        falling = True
                        if tgroup:
                            fall_groups.add(tgroup)
                    lm = land.search(t)
                    if falling and lm:
                        kind = 1
                        arg = int(round(-float(lm.group(1))))
                    continue
                lm = land_line.match(t)
                if lm:
                    # Standalone `Pos Y >= N` -- only useful together with a
                    # falling line in the same trigger group (see above).
                    land_groups[tgroup] = float(lm.group(1))
                    continue
                bad = True
            if kind is None and falling:
                for g, y in land_groups.items():
                    if g == "triggerall" or g in fall_groups:
                        kind = 1
                        arg = int(round(-y))
                        break
            if bad:
                continue
            if kind is None and dist is not None:
                # Distance-gated ChangeState (running grab).  The engine
                # compares centre X, so widen the source body distance by
                # roughly both fighters' half widths (same +30 used by the
                # command matcher).
                kind = 4
                arg = (min(127, dist + 30) |
                       (min(255, elem_frame) << 8))
            if land_recovery:
                # Only the landing rule can use the generic recovery pose;
                # an anim-end/press rule pointing at it is a different path.
                if kind != 1:
                    continue
                to_sid = LAND_SID
            if kind is None and names and rising:
                # `command = "a"` || `command = "b"` is an OR across
                # triggers: emit one kind-2 row per button so either
                # fresh press fires the follow-up.
                for nm in names:
                    if nm not in buttons:
                        continue
                    emit(to_sid, 2, buttons[nm])
                continue
            if kind is None:
                continue
            emit(to_sid, kind, arg)
    return rows


def chain_rules(path, buttons, move_ids):
    """State -1 entries -> normal-attack chain rows.

    Each row is (from_sid, to_sid, held_dirs, pad_mask, t_norm, t_hit) and
    fires while the fighter is in from_sid when the pad bit was just
    pressed, the held_dirs are held, and either the state frame has
    reached t_norm or a hit made contact and the frame reached t_hit.
    Times are stored as the first frame number that satisfies the trigger
    (``time > 5`` -> 6); $FF disables a clock.  Only trigger groups that
    reference mappable ``stateno = N`` conditions produce rows -- the
    plain "from ctrl" groups are already covered by the button tables.
    """
    wired = {}
    for _s, _m in move_ids.items():
        wired.setdefault(_m, _s)         # first slice sid wins
    rows = []
    for entry in parse_neg1(path):
        if entry.get("type", "").lower() != "changestate":
            continue
        try:
            mstate = int(float(entry.get("value", "-1").split(",", 1)[0]))
        except ValueError:
            continue
        to_sid = wired.get(mstate)
        if to_sid is None or not 5 <= to_sid <= 26:
            continue                          # chains only target normals
        base = [v for k, v in entry["triggers"] if k == "triggerall"]
        groups = {}
        for k, v in entry["triggers"]:
            if k == "triggerall":
                continue
            m = re.match(r"trigger(\d+)", k)
            groups.setdefault(int(m.group(1)) if m else 1, []).append(v)
        names = re.findall(r'command\s*=\s*"([^"]+)"', " ".join(base), re.I)
        btns = [b for b in names if b in buttons]
        if len(btns) != 1:
            continue
        pad = buttons[btns[0]]
        held = 0
        for cname in names:
            if cname in HOLD_CMD:
                held |= HOLD_CMD[cname]
        for conds in [base + g for g in groups.values()]:
            txt = " ".join(conds)
            if re.search(r"stateno\s*(?:!=|=\s*\[)", txt):
                continue                      # ranges/exclusions too complex
            froms = [int(n) for n in
                     re.findall(r"stateno\s*=\s*(\d+)", txt)]
            from_sids = [wired[n] for n in froms if n in wired]
            if not from_sids or len(from_sids) != len(froms):
                continue                      # unmapped stateno ref -> skip
            if not all(5 <= s <= 26 for s in from_sids):
                continue                      # only chains out of normals
            m = re.search(r"movecontact\s*&&\s*\btime\s*>\s*(\d+)", txt)
            if m:
                t_hit = int(m.group(1)) + 1
            elif "movecontact" in txt:
                t_hit = 0
            else:
                t_hit = 0xFF
            rest = re.sub(r"movecontact\s*&&\s*\btime\s*>\s*\d+", "", txt)
            tn = [int(n) + 1 for n in
                  re.findall(r"\btime\s*>\s*(\d+)", rest)]
            tn += [int(n) for n in
                   re.findall(r"(?:\btime|statetime)\s*>=\s*(\d+)", rest)]
            t_norm = min(tn) if tn else 0xFF
            if t_norm == 0xFF and t_hit == 0xFF:
                continue
            for fsid in from_sids:
                if fsid == to_sid:
                    continue                      # same-normal loops are infinite
                rows.append((fsid, to_sid, held, pad, t_norm, t_hit))
    return rows


def cancel_windows(path, move_ids, anim_len):
    """State -1 ``[Combo]`` VarSets -> per-normal special-cancel opens.

    KOF98's CMD/CNS defines the cancel window as ``var(1) = 1`` while a
    normal is in its cancelable animation elements; the CMD's special and
    super entries then fire on that variable.  The native engine evaluates
    the connection separately (F_HITDONE), so this table only needs the
    first element where a connected normal may cancel.

    Returns ``(sid, open_elem)`` rows for the normal slots (5..26).  The
    window runs to the animation's end, which keeps late hit-confirms
    usable instead of freezing on a one-element source window.  CancelGate
    already requires F_HITDONE, so opening strong normals at element 0 means
    the first connected hit can cancel immediately into a special or super
    (KOF98 hit-confirm timing).  Light normals without a source var(1) block
    keep the old contact-only behaviour.
    """
    state_to_sid = {}
    for sid, mstate in move_ids.items():
        state_to_sid.setdefault(mstate, sid)
    mugen = {}
    if os.path.exists(path):
        for entry in parse_neg1(path):
            if entry.get("type", "").lower() != "varset":
                continue
            if entry.get("var(1)", "0").strip() != "1":
                continue
            for key, trig in entry["triggers"]:
                if key == "triggerall":
                    continue
                ms = re.search(r"\bstateno\s*=\s*(\d+)\b", trig, re.I)
                if not ms:
                    continue
                sid = state_to_sid.get(int(ms.group(1)))
                if sid not in CANCEL_NORMAL_SIDS:
                    continue
                open_elem = None
                has_window = False
                for k, op, _val in re.findall(
                        r"AnimElemTime\s*\(\s*(\d+)\s*\)\s*([<>]=?)\s*(-?\d+)",
                        trig, re.I):
                    k = int(k)
                    if op in (">", ">="):
                        # Any lower bound starts inside element k.  Element
                        # durations are not needed for a 1-based -> 0-based
                        # conversion of the opening point.
                        cand = max(0, k - 1)
                        open_elem = (cand if open_elem is None
                                     else min(open_elem, cand))
                    elif op in ("<", "<="):
                        has_window = True
                if open_elem is None and has_window:
                    open_elem = 0
                if open_elem is not None:
                    mugen[sid] = min(mugen.get(sid, open_elem), open_elem)
    rows = []
    for sid in CANCEL_NORMAL_SIDS:
        strong = sid in CANCEL_STRONG_SIDS
        if strong:
            # Contact is the only gate that matters: once the normal hits or
            # is blocked, CancelGate lets the player route into a special or
            # super on the same frame.  Do not wait for the source var(1)
            # window or the middle of the animation.
            open_elem = 0
        elif sid in mugen:
            open_elem = mugen[sid]
        else:
            open_elem = 0
        rows.append((sid, max(0, min(0xFE, open_elem))))
    return rows


def ai_move_table(name, rules, move_ids, pow_costs, max_sids, projs, cfg):
    """Build the per-character CPU move table.

    The runtime chooses a wired special/super and enters its state directly,
    so this table only needs the sid, a useful distance window and a few
    behaviour flags.  Personality bytes are derived from the character's
    actual kit: projectile-heavy kits keep space, dragon punches anti-air,
    command grabs close in, and rush specials drive aggression.
    """
    rows = []
    seen = set()
    for rule in rules:
        if rule.get("shortcut"):
            continue
        sid = rule["state"]
        if sid in seen:
            continue
        if not (48 <= sid <= 66 or 74 <= sid <= 75 or 85 <= sid <= 89):
            continue
        motion = rule["motion"].split("#", 1)[0].upper()
        flags = 0
        # Stationary shots (vx == 0) are still projectiles: presence in the
        # ProjTab, not velocity, is what tells the AI to keep its distance.
        is_proj = sid in projs
        if is_proj:
            flags |= AI_F_PROJ
        if motion.startswith("DP"):
            flags |= AI_F_AA
        elif motion.startswith(("RDP", "HCB", "HCF", "FBF")):
            flags |= AI_F_RUSH
        elif ("QCF" in motion or "QCB" in motion) and not is_proj:
            flags |= AI_F_RUSH
        if sid >= 85:
            flags |= AI_F_SUPER
        if sid in (74, 75):
            flags |= AI_F_THROW
        if sid in max_sids:
            flags |= AI_F_MAX
        delta = pow_costs.get(sid, 0)
        cost100 = min(255, (max(0, -delta) + 99) // 100)
        if flags & AI_F_PROJ:
            lo, hi = 64, 255
        elif flags & AI_F_AA:
            lo, hi = 0, 72
        elif flags & AI_F_THROW:
            lo, hi = 0, 45
        elif flags & AI_F_SUPER:
            lo, hi = 24, 200
        elif flags & AI_F_RUSH:
            lo, hi = 0, 140
        else:
            lo, hi = 0, 140
        if rule.get("dist"):
            # rule["dist"] packs the p2bodydist gate in bit7.  Only the
            # low 7 bits are a distance; bit7 just says the source checks
            # the victim's posture (the throw gate).
            gate = rule["dist"]
            if flags & AI_F_THROW:
                hi = gate & 0x7F
                if not hi:
                    hi = 45             # posture-only throw command
                hi = max(lo, hi)
            elif gate & 0x7F:
                hi = min(255, max(lo, gate & 0x7F))
        if flags & AI_F_SUPER:
            # the AI never fires a super for free, even when the source
            # state's poweradd is zero (Kyo 85/86)
            cost100 = max(cost100, 10)
        weight = 3 if flags & (AI_F_PROJ | AI_F_AA | AI_F_THROW) else 2
        rows.append((sid, lo, hi, flags, cost100, weight))
        seen.add(sid)
    # Keep the most character-defining options when a kit has more than
    # eight wired moves: supers and throws first, then anti-airs, zoning
    # projectiles and rush specials.  This guarantees that every character
    # with a throw can actually use it without growing the ROM table.
    def _prio(row):
        f = row[3]
        if f & AI_F_SUPER:
            return 0
        if f & AI_F_THROW:
            return 1
        if f & AI_F_AA:
            return 2
        if f & AI_F_PROJ:
            return 3
        return 4
    rows.sort(key=lambda row: (_prio(row), row[0]))
    rows = rows[:8]

    proj_n = sum(1 for r in rows if r[3] & AI_F_PROJ)
    aa_n = sum(1 for r in rows if r[3] & AI_F_AA)
    rush_n = sum(1 for r in rows if r[3] & AI_F_RUSH)
    throw_n = sum(1 for r in rows if r[3] & AI_F_THROW)
    super_n = sum(1 for r in rows if r[3] & AI_F_SUPER)
    if throw_n and rush_n >= 2:
        style, spec = 3, 128
    elif proj_n >= 2 or (proj_n and rush_n == 0):
        style, spec = 1, 176
    elif aa_n + rush_n >= 2:
        style, spec = 2, 144
    else:
        style, spec = 0, 112
    spec = min(255, spec + 8 * len(rows))
    super_rate = min(255, 64 + 24 * super_n)

    # Personality profile.  AI_TUNING is the hand-authored per-character
    # layer; a character added without a row still gets a sensible style
    # default.  Kyo's table is the runtime fallback for unknown ids.
    zlo, zhi, aggr, deff, aa, throw_r, mix, pflags = AI_TUNING.get(
        name, AI_STYLE_PROFILE[style])
    if 96 not in cfg.get("moves", {}):
        pflags &= ~AI_PF_METER          # kit has no FUSION MAX burst
    if not throw_n:
        throw_r = 0
    if not super_n:
        super_rate = 0
    zlo = max(0, min(200, int(zlo)))
    zhi = max(zlo + 8, min(255, int(zhi)))
    # The authored profile also owns the spacing style.  Kit heuristics are
    # only a fallback for characters without an AI_TUNING row.
    if pflags & AI_PF_ZONER:
        style = 1
    elif throw_r >= 200 and zhi <= 60:
        style = 3
    elif (pflags & AI_PF_PRESSURE) or zhi <= 100:
        style = 2
    else:
        style = 0
    profile = (zlo, zhi, min(255, int(aa)), min(255, int(throw_r)),
               min(255, int(mix)), int(pflags) & 0xFF)
    AI_COUNTS[name] = len(rows)
    return (style, min(255, int(aggr)), min(255, int(deff)), spec,
            super_rate, rows, profile)


def guard_flag_mask(text, default=""):
    """MUGEN guardflag letters -> engine mask (H=1, M=2, L=4, A=8).

    The runtime stores the mask shifted into bits 4-7, exactly like the
    HitDef FlagsTab.  An empty/unknown value returns 0, i.e. unblockable.
    """
    letters = (text if text is not None else default).strip().lower()
    mask = 0
    for i, letter in enumerate("hmla"):
        if letter in letters:
            mask |= 1 << i
    return mask


def projectile_rules(statedefs, headers, move_ids, damage_scale):
    """Build native projectile rows for mapped moves with CNS projectiles.

    The engine represents projectiles in its shared moving-spark pool. A
    source move may create one directly or through a helper; follow one helper
    level so those common KOF patterns work without character-specific code.
    Character config rows remain available to tune moves whose CNS values are
    conditional or expressed through helper variables.

    Each row is (vx 8.8, HUD damage, effect anim, guard mask).  The guard
    mask is the same H/M/L/A bitmask used by HitDef FlagsTab.  Most KOF
    projectiles omit neither field and use MUGEN's "MA" default; an explicit
    empty guardflag, a throw attr or `guard.dist = 0` marks the shot
    unblockable.
    """
    def number(value):
        if value is None:
            return None
        m = re.match(r"\s*(-?\d+(?:\.\d+)?)", str(value))
        return float(m.group(1)) if m else None

    def helper_speed(state):
        # Projectile helpers commonly inherit their velocity from a VelSet
        # controller while the Projectile controller says "Vel X, Vel Y".
        for ctrl in statedefs.get(state, []):
            if ctrl.get("type", "").lower() == "velset":
                speed = number(ctrl.get("x"))
                if speed is not None and speed != 0:
                    return abs(speed)
        velset = headers.get(state, {}).get("velset", "")
        return abs(number(velset) or 0)

    def trigger_frame(ctrl):
        """Release frame (0-based) from a Helper/Projectile trigger."""
        for trig in ctrl.get("triggers", []):
            m = re.search(r"\banimelem\s*=\s*(\d+)", trig, re.I)
            if m:
                return max(0, int(m.group(1)) - 1)
            m = re.search(
                r"\banimelemtime\s*\(\s*(\d+)\s*\)\s*>?=?\s*0", trig, re.I)
            if m:
                return max(0, int(m.group(1)) - 1)
            m = re.match(r"\s*time\s*=\s*(\d+)\s*$", trig, re.I)
            if m:
                return int(m.group(1))
        return None

    out = {}
    for sid, root_state in move_ids.items():
        candidates = [root_state]
        seen = {root_state}
        release_for = {root_state: None}
        # Some chars create a visual helper that creates another helper,
        # where the last helper owns the actual Projectile controller.
        for source_state in candidates:
            for ctrl in statedefs.get(source_state, []):
                typ = ctrl.get("type", "").lower()
                if typ == "helper":
                    child = number(ctrl.get("stateno"))
                elif typ == "hitdef":
                    # Super HitDefs often hand off to a cinematic p1 state
                    # that owns the actual projectile (Omega's 2100->2101->
                    # 2103 chain).  p2stateno is the victim, never follow it.
                    child = number(ctrl.get("p1stateno"))
                    if child is not None and not (1000 <= child < 5000):
                        child = None
                elif typ == "changestate":
                    # Moves such as Gravity Smash fire their projectile from
                    # a follow-up state (the release/fire state), not the
                    # input state itself.  Follow the same-move chain once.
                    child = number(ctrl.get("value"))
                    if child is not None and not (1000 <= child < 5000):
                        child = None
                else:
                    continue
                if child is not None and int(child) not in seen:
                    seen.add(int(child))
                    candidates.append(int(child))
                    release_for.setdefault(int(child), trigger_frame(ctrl))
        for source_state in candidates:
            source_ctrls = statedefs.get(source_state, [])
            attacks = [c for c in source_ctrls
                       if c.get("type", "").lower() == "projectile"]
            if not attacks and source_state != root_state:
                # A few packages implement their travelling shot as a
                # moving helper with HitDef instead of a Projectile
                # controller. Treat that helper as the same pooled shot.
                # Throw/grab follow-ups also carry HitDefs, but their
                # p1stateno/p2stateno binding and dash VelSet would turn
                # them into bogus 30 px/frame "projectiles" (Omega's BR,
                # God Press and Rugal Excursion chains), so skip those.
                attacks = [c for c in source_ctrls
                           if c.get("type", "").lower() == "hitdef"
                           and not any(k.lower().startswith(("p1stateno",
                                                             "p2stateno"))
                                       for k in c)]
            for ctrl in attacks:
                speed = number(ctrl.get("velocity"))
                if speed is None and source_state != root_state:
                    speed = helper_speed(source_state)
                if speed is None or speed == 0:
                    continue                    # reflectors/held projectiles
                raw_damage = number(ctrl.get("damage"))
                # Source damage uses the MUGEN ~100-HP scale, while this
                # engine's spark slot stores whole SNES HUD damage points.
                dmg = max(1, min(40, round((raw_damage or 70) *
                                           damage_scale / 10)))
                release = release_for.get(source_state)
                if release is None:
                    release = trigger_frame(ctrl)
                # Guard is per shot: the source guardflag selects which
                # postures stop it.  A missing key keeps MUGEN's "MA"
                # default (blockable high or low); an explicit empty value
                # or a literal guard.dist = 0 marks it unblockable.  A
                # throw attr bypasses guard just like a throw HitDef.
                gflag = ctrl.get("guardflag")
                guard = (guard_flag_mask(gflag, default="ma")
                         if gflag is None else guard_flag_mask(gflag))
                gdist = ctrl.get("guard.dist")
                if gdist is not None:
                    gd = number(gdist)
                    if gd is not None and gd <= 0:
                        guard = 0
                if re.search(r",\s*\w*t\b", ctrl.get("attr", ""), re.I):
                    guard = 0
                # The native engine fires every projectile on the launch
                # clip's third frame (see ProjTrySpawn); the parsed source
                # release frame is kept only as documentation/debug data.
                out[sid] = (round(abs(speed) * 256), dmg, 4, guard)
                break
            if sid in out:
                break
    return out


def cap_projectile_recovery(frames, release, cap):
    """Shorten the follow-through tail of a projectile launch animation.

    Imported clips keep their full MUGEN recovery, so the fighter can stand
    in the throw pose for dozens of ticks after the shot has already left
    (Benimaru's Raikouken is the clearest case).  Only the tick counts after
    ``release`` are rescaled; every element survives so AnimElem/ActTab
    indices, hitboxes and sprite references still line up.
    """
    if not frames or cap <= 0:
        return frames
    release = max(0, min(int(release), len(frames) - 1))
    tail = frames[release + 1:]
    if not tail:
        return frames
    # 255 is an intentional hold (air shots wait for the landing row) and a
    # tail hitbox is gameplay, not recovery: leave both animations alone.
    if any(f[4] == 255 for f in frames):
        return frames
    if any(f[6] for f in tail):
        return frames
    weights = [max(1, int(f[4])) for f in tail]
    total = sum(weights)
    target = max(int(cap), len(tail))    # at least one tick per pose
    if total <= target:
        return frames
    scaled = [max(1, round(w * target / total)) for w in weights]
    while sum(scaled) > target:          # rounding drift -> longest pose
        i = max((j for j, n in enumerate(scaled) if n > 1),
                key=lambda j: scaled[j], default=None)
        if i is None:
            break
        scaled[i] -= 1
    while sum(scaled) < target:
        i = max(range(len(scaled)), key=lambda j: weights[j])
        scaled[i] += 1
    out = [(*f[:4], n, *f[5:]) for f, n in zip(tail, scaled)]
    return frames[:release + 1] + out


DAMAGE_NORMAL_SIDS = (5, 6, 7, 8,
                      19, 20, 21, 22, 23, 24, 25, 26)
# Ground normals (and the standing blowback) cannot be air-guarded in KOF98;
# specials, supers, projectiles and air normals can.  FlagsTab bit13 carries
# that distinction to GuardCheck.
AIR_GUARD_DENY_SIDS = frozenset((5, 6, 7, 8, 19, 20, 21, 22, 67))
# The imported HitDefs use the 320 px arcade/Neo-Geo stage.  On the 208 px
# SNES playfield (fight.asm STAGE_L/STAGE_R) their heavy normals slide the
# victim 178-230 px in one hit -- from mid-screen straight into the wall.
# Keep every normal's ground/air hit and guard pushback at one third of
# the screen.
STAGE_L = 24
STAGE_R = 232
NORMAL_PUSH_LIMIT = (STAGE_R - STAGE_L) // 3        # 69 px
_KYO_DAMAGE_PROFILE = None


def limit_normal_pushback(rows):
    """Clamp normal-attack pushback to one third of the SNES playfield.

    Velocities are 8.8 fixed-point px/tick.  A grounded victim keeps
    ``gvx``/``grvx`` for ``min(hittime, slidetime)`` ticks; an airborne one
    keeps ``avx``/``agvx`` for the whole ``slidetime``.  The cap is therefore
    per state and per window: a longer slide gets a lower per-tick velocity,
    keeping the total travel below NORMAL_PUSH_LIMIT.  Specials and supers
    are left untouched.
    """
    for sid in DAMAGE_NORMAL_SIDS:
        if sid >= len(rows):
            continue
        row = rows[sid]
        hit = row.get("hittime", 0)
        slide = row.get("slidetime", 0)
        if slide <= 0:
            continue
        windows = {"gvx": min(hit, slide), "grvx": min(hit, slide),
                   "avx": slide, "agvx": slide}
        changes = {}
        for key, window in windows.items():
            if window <= 0:
                continue
            cap = (NORMAL_PUSH_LIMIT * 256) // window
            if row.get(key, 0) > cap:
                changes[key] = cap
        if changes:
            row = dict(row)
            row.update(changes)
            rows[sid] = row


def damage_profile(rows):
    """Median normal-hit damage and maximum damage from runtime move rows."""
    vals = [rows[sid].get("damage", 0)
            for sid in DAMAGE_NORMAL_SIDS
            if sid < len(rows) and rows[sid].get("damage", 0) > 0]
    return (statistics.median(vals) if vals else 0,
            max((row.get("damage", 0) for row in rows), default=0))


def kyo_damage_profile():
    """Kyo is the reference/fallback damage profile for imported fighters."""
    global _KYO_DAMAGE_PROFILE
    if _KYO_DAMAGE_PROFILE is None:
        cfg = CHARS["kyo"]
        cns = parse_cns(os.path.join(ROOT, cfg["cns"]),
                        cfg.get("coord_scale", 1),
                        cfg.get("damage_scale", 1))
        moves = cns[0]
        move_ids = cfg.get("moves", {})
        rows = [moves.get(move_ids.get(sid, -1), {})
                for sid in range(max(move_ids, default=0) + 1)]
        _KYO_DAMAGE_PROFILE = damage_profile(rows)
    return _KYO_DAMAGE_PROFILE


def load_quote_db():
    """Load the per-language victory-quote JSON files (cached)."""
    global _QUOTE_DB
    if _QUOTE_DB is None:
        _QUOTE_DB = {}
        for fname, tag in QUOTE_LANGS:
            path = os.path.join(QUOTE_DIR, fname + ".json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            _QUOTE_DB[tag] = {k: v for k, v in data.items()
                              if not k.startswith("_")}
    return _QUOTE_DB


def normalize_quote(text):
    """Fold a translated quote into the 8x8 HUD font's character set.

    The KOF lifebar font only carries ASCII letters, digits and a handful of
    punctuation marks.  Accented translations are kept in the JSON source;
    they are transliterated here (á -> A, ç -> C, ...) so Portuguese, Spanish
    and French render without extra font tiles.
    """
    for src, dst in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'),
                     ("\u201d", '"'), ("\u2013", "-"), ("\u2014", "-"),
                     ("\u2026", "...")):
        text = text.replace(src, dst)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace(",", " ")
    text = "".join(c if c in CHARSET else " " for c in text)
    return re.sub(r"\s+", " ", text).strip()


def wrap_quote(text, width=30, max_lines=2):
    """Word-wrap a normalized quote; None when it cannot fit the HUD."""
    lines, cur = [], ""
    for word in text.split():
        if len(word) > width:
            return None
        cand = (cur + " " + word).strip()
        if len(cand) <= width:
            cur = cand
        else:
            lines.append(cur)
            cur = word
            if len(lines) >= max_lines:
                return None
    lines.append(cur)
    return lines if len(lines) <= max_lines else None


def legacy_quote_lines(name, cfg):
    """Fallback: first [Quotes] / [en.Quotes] block in the merged CNS."""
    path = os.path.join(ROOT, cfg.get("cns", ""))
    try:
        text = open(path, encoding="latin-1").read()
    except OSError:
        return []
    section = re.search(r'^\[(?:en\.)?Quotes\]\s*\n(.*?)(?=^\[|\Z)',
                        text, re.M | re.S | re.I)
    body = section.group(1) if section else ""
    out = []
    for m in re.finditer(r'^victory\d+\s*=\s*"([^"]+)"', body,
                         re.M | re.I):
        lines = wrap_quote(normalize_quote(m.group(1)))
        if lines:
            out.append(lines)
    return out


def wire_throw_chain(name, cfg, anims, air, cns_moves, cns_headers):
    """Wire the source throw bind + victim poses for every fighter.

    The roster tables predate the throw audit: most rows point sid 74/75 at
    the grab stance and leave sid 76/77 on the stand/hit placeholder, so the
    attacker never enters the bind animation and a thrown fighter stands
    still.  Prefer the animations already present in the source AIR:
      * 75 = the p1 bind state's own anim (custom fakes such as Kyo's 826
        and Iori's 1305 are kept);
      * 76 = a held pose (815 -> 820 -> 825);
      * 77 = a thrown pose (816 -> 821 -> the generic fall 5050).
    Characters without those actions keep their current placeholders.
    """
    throws = [(st, row) for st, row in cns_moves.items()
              if row.get("throw")]
    if not throws:
        return
    attempt = cfg.get("moves", {}).get(74)
    row = cns_moves.get(attempt)
    if row is None or not row.get("throw"):
        attempt = throws[0][0]
        cfg.setdefault("moves", {})[74] = attempt
        try:
            a = int(cns_headers.get(attempt, {}).get("anim", "-1"))
        except (TypeError, ValueError):
            a = -1
        if a in air:
            cfg.setdefault("anims", {})[74] = a
            anims[74] = a
        row = cns_moves[attempt]
    try:
        attempt_anim = int(cns_headers.get(attempt, {}).get("anim", "-1"))
    except (TypeError, ValueError):
        attempt_anim = -1
    raw_attempt_anim = attempt_anim
    if raw_attempt_anim not in air:
        raw_attempt_anim = cfg.get("anims", {}).get(74, -1)
    # Chizuru's mind throw uses a 15-frame gesture with no bind.  Keep its
    # first-frame Clsn1 (the grab window) but render the timeline with that
    # single cel so the fixed-bank budget stays intact.
    _aa = cfg.get("anims", {}).get(74)
    if _aa in air and len(air[_aa][0]) > 3:
        frames, loop = air[_aa]
        af = frames[0]
        air[65002] = ([(af[0], af[1], af[2], af[3], f[4], af[5], *af[6:])
                       for f in frames], loop)
        cfg.setdefault("anims", {})[74] = 65002
        anims[74] = 65002
        attempt_anim = 65002
    p1 = row.get("p1mugen", -1)
    self_bind = cfg.get("throw_self_bind")
    if p1 < 0 and self_bind is not None:
        p1 = self_bind
        row["p1mugen"] = p1
    try:
        bind_anim = int(cns_headers.get(p1, {}).get("anim", "-1"))
    except (TypeError, ValueError):
        bind_anim = -1
    if p1 == self_bind and bind_anim not in air and raw_attempt_anim in air:
        bind_anim = raw_attempt_anim
    if p1 < 0 or bind_anim not in air or not air[bind_anim][0]:
        # Athena/Chin/Leona's command throw HitDef has no p1stateno, but the
        # source package has another bind state with real art.  Borrow that
        # bind (the HitDef/victim state stay untouched) so the attacker still
        # performs a throw animation.
        for st2, row2 in throws:
            p1b = row2.get("p1mugen", -1)
            try:
                ab = int(cns_headers.get(p1b, {}).get("anim", "-1"))
            except (TypeError, ValueError):
                ab = -1
            if p1b >= 0 and ab in air and air[ab][0]:
                row["p1mugen"] = p1b
                p1, bind_anim = p1b, ab
                break
    if p1 >= 0 and bind_anim in air and air[bind_anim][0]:
        cfg.setdefault("moves", {})[75] = p1
        cur = cfg.setdefault("anims", {}).get(75)
        # Keep authored custom bind cels (Kyo 826, Iori 1305, Yuri 311).
        if cur in (None, attempt_anim, 47, 250, 300, 5000, 5050) \
                or cur not in air:
            # Keep the source timeline (Bind/Act rows use frame numbers) but
            # render it with three key poses; a 12-25 frame bind does not fit
            # the per-character metasprite bank on top of the victim pose.
            frames, loop = air[bind_anim]
            if not cfg.get("msu") and attempt_anim in air:
                # Fixed ROM CHR banks (Daimon/Kyo/Terry...) have no room for
                # new bind cels.  Reuse the grab-stance sprite for every bind
                # frame so the controller/damage timeline still runs.
                af = air[attempt_anim][0][0]
                air[65001] = ([(af[0], af[1], af[2], af[3], f[4],
                                af[5], *af[6:]) for f in frames], loop)
                bind_anim = 65001
            elif len(frames) > 3:
                picks = (frames[0], frames[len(frames) // 2], frames[-1])
                compact = []
                for i, f in enumerate(frames):
                    src = picks[min(i * len(picks) // len(frames),
                                    len(picks) - 1)]
                    compact.append((src[0], src[1], f[2], f[3], f[4],
                                    src[5], *f[6:]))
                air[65001] = (compact, loop)
                bind_anim = 65001
            cfg["anims"][75] = bind_anim
            anims[75] = bind_anim
        else:
            anims[75] = cur
    def first(*actions):
        for a in actions:
            if a in air and air[a][0]:
                return a
        return None
    # Victim poses: keep authored custom cels (Kyo 815, Yuri 303/313);
    # everyone else uses the already-resident hit/fall art.  Importing the
    # per-character 815/820/821 sequences for all 50 fighters does not fit
    # the metasprite/table bank windows, so the generic reaction is the
    # budget-safe fallback.
    if cfg["anims"].get(76) in (None, 47, 250, 300, 5000, 5050):
        cfg["anims"][76] = 5000 if 5000 in air else 47
        anims[76] = cfg["anims"][76]
    if cfg["anims"].get(77) in (None, 47, 250, 300, 5000, 5050):
        cfg["anims"][77] = 5050 if 5050 in air else 47
        anims[77] = cfg["anims"][77]


def _clean_def_path(value):
    """Strip MUGEN .def comments/quotes from a path or value."""
    return value.split(";", 1)[0].strip().strip('"').strip()


def _find_char_def(sff_rel):
    """Return (def_path, text) for the .def that owns sff_rel.

    Packs often ship several .def files in the same folder (normal, EX,
    alternate costume, ...).  The Sprite= entry is authoritative, so match
    the resolved path before falling back to a basename match.
    """
    sff_abs = os.path.abspath(os.path.join(ROOT, sff_rel))
    roots = []
    d = os.path.dirname(sff_abs)
    for _ in range(3):
        if d not in roots:
            roots.append(d)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    best = None
    for root in roots:
        try:
            names = os.listdir(root)
        except OSError:
            continue
        for fname in names:
            if not fname.lower().endswith(".def"):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, encoding="latin-1") as f:
                    text = f.read()
            except OSError:
                continue
            m = re.search(r"(?im)^\s*Sprite\s*=\s*(.+?)\s*$", text)
            if not m:
                continue
            sprite = _clean_def_path(m.group(1)).replace("\\", "/")
            full = os.path.abspath(os.path.normpath(
                os.path.join(root, sprite)))
            if full == sff_abs:
                score = 3
            elif (os.path.basename(full).lower()
                  == os.path.basename(sff_abs).lower()
                  and os.path.dirname(full) == os.path.dirname(sff_abs)):
                score = 2
            else:
                continue
            if best is None or score > best[0]:
                best = (score, path, text)
    return (best[1], best[2]) if best else (None, None)


def _parse_def_palettes(text):
    """Return ({pal_number: path}, [Pal.Defaults numbers])."""
    pals = {}
    for m in re.finditer(r"(?im)^\s*Pal(\d+)\s*=\s*(.+?)\s*$", text):
        path = _clean_def_path(m.group(2)).replace("\\", "/")
        if path:
            pals[int(m.group(1))] = path
    defaults = []
    m = re.search(r"(?im)^\s*Pal\.Defaults\s*=\s*(.+?)\s*$", text)
    if m:
        defaults = [int(x) for x in
                    re.findall(r"\d+", _clean_def_path(m.group(1)))]
    return pals, defaults


def resolve_p2_candidates(name, cfg):
    """Return (base_act, [p2_act, ...]) for mirror-match colours.

    The base palette is the one already selected by the build (Pal.Defaults,
    or cfg["palette_act"]).  Candidates are the remaining entries in the
    pack's Pal1..PalN list (in cycle order), plus any ACT files the .def did
    not list.  build_char samples them and keeps the first one that is
    visually distinguishable from the base.
    """
    override = cfg.get("palette_act_p2")
    if override:
        return cfg.get("palette_act"), [override]

    def_path, text = _find_char_def(cfg["sff"])
    if not text:
        return cfg.get("palette_act"), []
    pals, defaults = _parse_def_palettes(text)
    if not pals:
        return cfg.get("palette_act"), []

    keys = sorted(pals)
    base_num = None
    base = cfg.get("palette_act")
    if base:
        base_name = os.path.basename(base.replace("\\", "/")).lower()
        for num, path in pals.items():
            if os.path.basename(path).lower() == base_name:
                base_num = num
                break
    if base_num is None:
        for num in defaults:
            if num in pals:
                base_num = num
                break
    if base_num is None:
        base_num = keys[0]

    def_dir = os.path.dirname(def_path)

    def resolved(num):
        return os.path.abspath(os.path.normpath(
            os.path.join(def_dir, pals[num])))

    if base_num in pals:
        base_path = resolved(base_num)
    elif base:
        base_path = os.path.abspath(os.path.join(ROOT, base))
    else:
        base_num = keys[0]
        base_path = resolved(base_num)

    ordered = []
    if base_num in keys:
        pos = keys.index(base_num)
        ordered = keys[pos + 1:] + keys[:pos]
    else:
        ordered = keys

    candidates = []
    seen = {os.path.normpath(base_path)}
    for num in ordered:
        path = resolved(num)
        key = os.path.normpath(path)
        if key in seen or not os.path.exists(path):
            continue
        seen.add(key)
        candidates.append(path)

    # Packs like Mature list only Pal1 in the .def even though the folder
    # carries a full Mature00..Mature12 set.  Append every unlisted ACT.
    acts = sorted(glob.glob(os.path.join(def_dir, "*.act")))
    acts += sorted(glob.glob(os.path.join(def_dir, "**", "*.act"),
                             recursive=True))
    for cand in acts:
        cand = os.path.abspath(cand)
        key = os.path.normpath(cand)
        if key in seen or not os.path.exists(cand):
            continue
        seen.add(key)
        candidates.append(cand)

    return (base if base else base_path), candidates


def resolve_p2_palette(name, cfg):
    """Convenience wrapper: the base palette and the first alternate."""
    base, candidates = resolve_p2_candidates(name, cfg)
    return base, (candidates[0] if candidates else None)


def _shift_palette(pal, degrees=140):
    """Hue-rotate a palette.  Fallback for mirrors with no source ACT."""
    import colorsys
    out = [pal[0]]
    for r, g, b in pal[1:]:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        h = (h + degrees / 360) % 1.0
        nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
        out.append((int(nr * 255), int(ng * 255), int(nb * 255)))
    return out


def build_char(name, cfg, global_pal=None):
    coord_scale = cfg.get("coord_scale", 1)
    char_scale = cfg.get("char_scale", 1.0)
    sff = Sff(os.path.join(ROOT, cfg["sff"]))
    # Some SFFv1 imports point the body cels at a shadow/alternate palette
    # bank (e.g. Athena ships palette 1 as a dark-red dim copy while palette
    # 0 carries the normal blue/white colours).  Force the intended bank
    # before any sprite, tween or projectile reads s.palidx.
    palette_bank = cfg.get("palette_bank")
    if palette_bank is not None:
        for sprite in sff.sprites:
            sprite.palidx = palette_bank
    air = parse_air(os.path.join(ROOT, cfg["air"]))
    # A few imported clips end a phase with a trailing t=255 "hold until the
    # next ChangeState" element.  When the caller only needs a short recovery
    # (or an anim-end hand-over), replace that hold with a bounded tick count.
    for anum, ticks in (cfg.get("tail_ticks") or {}).items():
        if anum not in air or not air[anum][0]:
            continue
        frames, loopstart = air[anum]
        g, n, x, y, _t, flip, atk, hurt = frames[-1]
        air[anum] = (frames[:-1] +
                     [(g, n, x, y, max(1, min(255, int(ticks))),
                       flip, atk, hurt)], loopstart)
    # Imported projectiles sometimes reference a MUGEN action that was
    # stripped from the AIR even though the SFF still carries its sprites
    # (Rugal/Omega projanim 1006 -> SFF group 1002).  Synthesize the action
    # so projectile_effect can compile the effect artwork.
    for anum, entries in cfg.get("projectile_air", {}).items():
        if anum in air:
            continue
        air[anum] = ([(g, n, 0, 0, max(1, int(t)), "", [], [])
                      for g, n, t in entries], 0)
    anims = resolve_import_anims(cfg, air) if name in NEW_CHARS else cfg["anims"]
    anims = dict(anims)
    # Counter-grab runtime slots (RevTab p2stateno): every fighter can be the
    # victim of a reversal throw, so all tables need a valid held-pose entry
    # at 100/102.  The reversal actor overrides 99/101 with its own follow-up
    # animation in its roster row.  98 stays Iori's Yumebiki second hit.
    # Extended follow-up slots can leave holes above 102 (Mary's 107-111), so
    # fill the dense AnimTab range up to the highest wired sid.
    for _sid in range(98, max(max(cfg.get("moves", {0})), 102) + 1):
        anims.setdefault(_sid, 5000)
    # Only mapped but animation-less slots need a fallback.  Adding every
    # reversal-follow-up slot regardless of whether the fighter maps it made
    # Mature's generated table overflow its fixed ROM window.
    for _sid in cfg.get("moves", {}):
        anims.setdefault(_sid, 5000)
    # FUSION dizzy/air-throw states reuse existing animation slots (11/44)
    # so the shared tables do not grow an extra sid per fighter.
    charge = CHARGE_ANIMS.get(name)
    if charge:
        anims[97] = charge[0]
    repaired = [(sid, cfg["anims"][sid], anims[sid])
                for sid in cfg["anims"] if anims.get(sid) != cfg["anims"][sid]]
    if repaired:
        print(f"{name}: replaced {len(repaired)} stand-pose move actions: "
              f"{repaired}")
    (cns_moves, cns_posadds, cns_powadds, cns_headers,
     cns_statedefs, cns_binds, cns_acts,
     cns_reversals, cns_hitdef_lists,
     cns_snds, cns_hitsnds, cns_exprows) = parse_cns(
        os.path.join(ROOT, cfg["cns"]), coord_scale,
        cfg.get("damage_scale", 1), char=name)

    # Optional verified calibration, preserving the existing native table ABI.
    # Stale source hashes or changed manual values fail closed at build time.
    from calibration.native import apply_profile
    apply_profile(ROOT, name, cfg, cns_moves, air)
    wire_throw_chain(name, cfg, anims, air, cns_moves, cns_headers)
    if name in COUNTER_GRAB_POST_CAL:
        _rows = COUNTER_GRAB_POST_CAL[name]
        wire_counter_grabs(cfg, _rows)
        # AnimTab/CHR were resolved from this local dict before calibration;
        # keep it in sync with the newly wired actor slots.
        for _height, (_p1, _p2, _anim) in _rows.items():
            anims[_COUNTER_GRAB_SLOTS[_height][0]] = _anim

    # Restore supers that the ROM diet dropped for imported characters.
    # apply_profile already validated the (reduced) config hash, and none of
    # the restored sids touch a calibrated HitDef.
    for _sid, (_state, _anim) in POST_CAL_SUPERS.get(name, {}).items():
        cfg["moves"].setdefault(_sid, _state)
        cfg["anims"][_sid] = _anim
        anims[_sid] = _anim

    # Which super slots are MAX/SDM versions?  Stored in a descriptor byte
    # (CH_MAXMASK) so the matcher no longer guesses from the sid number.
    if "max_sids" in cfg:
        _max_sids = set(cfg["max_sids"])
    elif name in MAX_SIDS_OVERRIDE:
        _max_sids = set(MAX_SIDS_OVERRIDE[name])
    else:
        _max_sids = set()
        for _sid in (85, 86, 87, 88, 89):
            _state = cfg.get("moves", {}).get(_sid)
            if _state is None:
                continue
            if state_is_max(cfg["cns"], cns_headers, cns_statedefs,
                            _state):
                _max_sids.add(_sid)
    _max_sids = {x for x in _max_sids if x in cfg.get("moves", {})}
    cfg["_max_sids"] = _max_sids
    MAX_MASKS[name] = max_sid_mask(_max_sids)

    # A few imports have no AIR 170 (time-over loser pose); use their dizzy
    # pose instead of falling back to the anim 47 landing placeholder.
    if name in POST_CAL_LOSE_ANIM and anims.get(91) == 47:
        anims[91] = POST_CAL_LOSE_ANIM[name]
        cfg["anims"][91] = anims[91]

    # ReversalDef counter-attacks (Yamazaki/Kyo/Shingo/Billy): give the
    # p1stateno follow-up a real runtime sid so RevCheck never returns $FF.
    wire_reversal_followups(cfg, anims, air, cns_headers, cns_statedefs,
                            cns_reversals)

    # PlaySnd controllers -> op7 action rows.  Element triggers use the
    # 0-based animation element.  State-time triggers carry bit7 and retain
    # their exact tick; folding Time=N into the containing element made a
    # sound scheduled late in a long element play several ticks too early.
    voices = {}
    used_states = set(cfg.get("moves", {}).values())
    for state, entries in cns_snds.items():
        durs = []
        loopstart = -1
        try:
            anum = int(cns_headers.get(state, {}).get("anim", "-1"))
            anim_frames, loopstart = air.get(anum, ([], -1))
            durs = [f[4] for f in anim_frames]
        except (ValueError, TypeError):
            pass
        for trig, sfxid in entries:
            is_voice = isinstance(sfxid, tuple)
            voice_random = (isinstance(sfxid, tuple) and any(
                re.search(r"\brandom\s*<=\s*500\b", t, re.I)
                for t in trig))
            if isinstance(sfxid, tuple):
                # char .snd sample without a bank mapping -> streamed voice.
                # Only states wired to a sid can fire it.
                if state not in used_states or len(voices) >= 200:
                    continue
                if sfxid not in voices:
                    voices[sfxid] = len(voices)
                sfxid = 40 + voices[sfxid]
            frames = [int(e.group(1)) - 1
                      for t in trig
                      for e in [re.search(r"\banimelem\s*=\s*(\d+)",
                                          t, re.I)]
                      if e]
            times = [int(e.group(1))
                     for t in trig
                     for e in [re.match(r"time\s*=\s*(\d+)\s*$", t, re.I)]
                     if e]
            # MUGEN accepts arithmetic in Time triggers. Preserve simple
            # integer sums so the event fires once at the intended state tick.
            times += [sum(map(int, e.groups()))
                      for t in trig
                      for e in [re.fullmatch(
                          r"\s*time\s*=\s*(\d+)\s*\+\s*(\d+)\s*",
                          t, re.I)] if e]
            for t in trig:
                e = re.search(r"animelemtime\((\d+)\)\s*=\s*(-?\d+)",
                              t, re.I)
                if not e or not durs:
                    continue
                elem = int(e.group(1)) - 1
                if 0 <= elem < len(durs):
                    times.append(sum(max(1, d) for d in durs[:elem])
                                 + int(e.group(2)))
            for frame in frames:
                if is_voice and loopstart >= 0 and frame >= loopstart:
                    # AnimElem actions inside an animation's loop are replayed
                    # every time that element comes around. Voices are one-shot
                    # events, so schedule them at the matching state tick.
                    tick = sum(max(1, d) for d in durs[:frame])
                    if tick < 0x7F:
                        times.append(tick)
                    elif frame < 0x7F:
                        # State-time triggers only carry seven bits.  Long
                        # supers (Ralf's Galactica Phantom weak runs 182
                        # ticks) used to lose their voice silently.  Keep an
                        # element trigger as a fallback: the move does not
                        # loop, so it still fires once.
                        cns_acts.setdefault(state, []).append(
                            (frame, 7, sfxid, 2 if voice_random else 0))
                else:
                    cns_acts.setdefault(state, []).append(
                        (frame, 7, sfxid, 2 if voice_random else 0))
            for tick in times:
                if 0 <= tick < 0x7F:
                    cns_acts.setdefault(state, []).append(
                        (0x80 | tick, 7, sfxid,
                         2 if voice_random else 0))
    if voices:
        CHAR_VOICES[name] = voices
    # KOF98 forward dash and directional evasions do not use afterimage
    # trails.  Their source CNS files sometimes enable AfterImage in these
    # states; omit those controllers to keep their SNES animations lighter.
    for state in (100, 250, 251, 710):
        cns_acts[state] = [row for row in cns_acts.get(state, ())
                           if row[1] != 9]
    for state in cns_acts:
        cns_acts[state].sort()
    # Resolve the calibrator before parse_cmd so a per-character button
    # override reaches ButtonTab and the command-list labels too.
    calibration = resolve_input_calibration(name, cfg)
    button_rows = parse_cmd(os.path.join(ROOT, cfg["cmd"]),
                            cfg["buttons"], cfg["moves"])

    # ProjTab rows are needed both for the animation pass below (recovery
    # trim) and for the emitted table, so resolve them before anim_tables.
    projs = projectile_rules(cns_statedefs, cns_headers, cfg["moves"],
                             cfg.get("damage_scale", 1))
    for _sid in PROJECTILE_EXCLUDE.get(name, ()):
        projs.pop(_sid, None)
    for sid, row in cfg.get("projs", {}).items():   # calibrated rows win
        row = tuple(row)
        old = projs.get(sid, (0, 0, 0, 0x0A))
        # A 3-tuple keeps the source-derived guard mask; the optional 4th
        # element pins it (0 = unblockable) for hand-tuned shots.
        guard = row[3] if len(row) > 3 else old[3]
        projs[sid] = (row[0], row[1], row[2], guard)
    for sid, vals in PROJECTILE_CALIBRATION.get(name, {}).items():
        vx, dmg = vals[:2]
        old = projs.get(sid, (0, 0, 0, 0x0A))
        projs[sid] = (vx, dmg, old[2], old[3])

    repair_invisible_move_anims(name, cfg, anims, air)

    wanted = set()
    anim_tables = {}
    for sid, anum in anims.items():
        frames, loopstart = air[anum]
        if sid == 97:
            frames, loopstart = charge_frames(name, air, anum)
        frames = scale_air_frames(frames, coord_scale)
        frames = scale_air_frames_f(frames, char_scale)
        if sid == 92:
            # the mugen intro anim ends on a t=-1 hold (parse_air maps it
            # to 255) and statedef 191 exits on AnimElemTime -- a trigger
            # the native engine does not evaluate.  Drop the hold and force
            # a one-shot clip: Omega98's AIR 191 declares Loopstart=0, which
            # otherwise makes the intro loop forever and stalls gs4.
            while frames and frames[-1][4] == 255:
                frames.pop()
            loopstart = -1
        if sid in (90, 91) and frames and frames[-1][4] != 255:
            # win/lose poses must hold their last frame until the round
            # restarts -- AnimTime=0 would drop the fighter back to stand.
            # Append a copy of the final frame as a 255-tick hold.
            last = frames[-1]
            frames = frames + [(last[0], last[1], last[2], last[3], 255,
                                last[5], last[6], last[7])]
        if sid in cfg.get("slices", ()):
            # one mugen state split over several sids (super 3000): this sid
            # plays only elems lo..hi of the shared anim
            _anim, lo, hi = cfg["slices"][sid]
            assert _anim == anum
            frames = frames[lo:hi if hi is None else hi + 1]
            loopstart = 0
        anim_tables[sid] = (frames, loopstart)
        for g, n, *_ in frames:
            wanted.add((g, n))

    # Imported projectile specials keep the source's long follow-through.
    # Rescale only the tail after the release frame (ProjTrySpawn fires on
    # element 3) so the fighter can act again without changing startup or
    # the shot's flight.  Skip airborne clips (they end on landing), the
    # landing-placeholder anim 47 and any animation shared with a normal
    # state -- shortening those would affect movement or recovery poses.
    recovery = PROJECTILE_RECOVERY.get(name, PROJECTILE_RECOVERY_TICKS)
    anim_sharing = {}
    for sid, anum in anims.items():
        anim_sharing.setdefault(anum, []).append(sid)
    seen_anims = set()
    for sid in projs:
        anum = anims.get(sid)
        if anum is None or anum in seen_anims or anum not in air:
            continue
        seen_anims.add(anum)
        sids = [s for s in anim_sharing.get(anum, ()) if s in anim_tables]
        if not sids or any(s not in projs for s in sids):
            continue
        if any(s in cfg.get("slices", ()) for s in sids):
            continue
        states = [cfg["moves"].get(s) for s in sids]
        headers = [cns_headers.get(st, {}) for st in states]
        if any(h.get("type", "").strip().upper() == "A" for h in headers):
            continue
        cap = recovery.get(sid, PROJECTILE_RECOVERY_TICKS) \
            if isinstance(recovery, dict) else recovery
        frames, loopstart = anim_tables[sids[0]]
        release = min(2, len(frames) - 1)
        capped = cap_projectile_recovery(frames, release, cap)
        if capped is not frames:
            for s in sids:
                anim_tables[s] = (capped, loopstart)
    blank = None

    def sprite_or_blank(key):
        """MUGEN tolerates missing sprite references (blank frame); decode
        failures and absent group,number pairs get a transparent 8x8."""
        nonlocal blank
        s = scale_sprite_f(
            scale_sprite(sff.get(*key), coord_scale), char_scale)
        if s is not None and s.pix is not None:
            return s
        if blank is None:
            blank = Sprite()
            blank.group = blank.number = -1
            blank.w = blank.h = 8
            blank.ax = blank.ay = 0
            blank.link = 0
            blank.palidx = None
            blank.pix = bytes(64)
        return blank

    sprites = {key: sprite_or_blank(key) for key in wanted}

    # Optional ACT palette reference: map each per-sprite PCX color onto the
    # nearest color from the character's declared default palette before the
    # 15-color SNES quantization. This keeps a character's colors consistent
    # even when its SFF stores a different palette in every sprite.
    palette_ref = None
    if cfg.get("palette_act"):
        with open(os.path.join(ROOT, cfg["palette_act"]), "rb") as f:
            raw_pal = f.read()
        if len(raw_pal) < 768:
            raise ValueError(f"invalid ACT palette: {cfg['palette_act']}")
        palette_ref = [tuple(raw_pal[i:i + 3]) for i in range(0, 768, 3)]
        palette_colors = [c for c in palette_ref if any(c)]

    # Mirror matches: sample the pack's alternate ACT entries and keep the
    # first one that is visually distinct from the base palette.  Tiles are
    # shared, so only the 16 CGRAM words change.
    _, p2_acts = resolve_p2_candidates(name, cfg)
    alt_candidates = []
    for p2_act in p2_acts:
        try:
            with open(p2_act if os.path.isabs(p2_act)
                      else os.path.join(ROOT, p2_act), "rb") as f:
                raw_alt = f.read()
        except OSError:
            continue
        if len(raw_alt) >= 768:
            alt_candidates.append([tuple(raw_alt[i:i + 3])
                                   for i in range(0, 768, 3)])

    palette_color_cache = {}
    alt_index_cache = {}
    base_index_map = cfg.get("palette_index_map", {})
    sprite_maps = cfg.get("palette_sprite_map", {})

    def sprite_index_map(key):
        extra = (sprite_maps.get(key)
                 or sprite_maps.get(f"{key[0]},{key[1]}"))
        return {**base_index_map, **extra} if extra else base_index_map

    def mapped_color(index, color, index_map=None):
        if palette_ref is None:
            return color
        index_map = base_index_map if index_map is None else index_map
        target = index_map.get(index)
        if target is not None and target < len(palette_ref):
            return palette_ref[target]
        # Some MUGEN palettes keep the active sprite colors in a remapped
        # palette bank (Yuri's starts at ACT index 146). Respect that index
        # layout: RGB-nearest matching collapses her white/green costume to
        # muddy browns because the embedded PCX palette itself is damaged.
        offset = cfg.get("palette_index_offset")
        if offset is not None and index + offset < len(palette_ref):
            return palette_ref[index + offset]
        if color not in palette_color_cache:
            palette_color_cache[color] = min(
                palette_colors,
                key=lambda c: sum((c[i] - color[i]) ** 2
                                  for i in range(3)))
        return palette_color_cache[color]

    def act_target(index, color, index_map=None):
        """ACT slot corresponding to an SFF pixel index.

        The packs store ACT entries in reverse order relative to the SFF
        pixel indices (act[255-index] is the matching colour); characters
        with an explicit palette_index_map reuse that map.
        """
        index_map = base_index_map if index_map is None else index_map
        target = index_map.get(index)
        if target is None:
            offset = cfg.get("palette_index_offset")
            if offset is not None:
                target = index + offset
        if target is None and palette_ref is not None:
            if color not in alt_index_cache:
                alt_index_cache[color] = min(
                    range(len(palette_ref)),
                    key=lambda i: sum((palette_ref[i][ch] - color[ch]) ** 2
                                      for ch in range(3)))
            target = alt_index_cache[color]
        if target is None:
            target = 255 - index
        if 0 <= target < 256:
            return target
        return None

    # original colour -> {ACT slot: pixel weight}
    src_targets = {}

    # global 15-colour palette (union, deterministic order).  Characters
    # whose sprites exceed 15 unique colours are median-cut quantized: each
    # original colour maps to its bucket's weighted centroid.
    remap_color = None
    if global_pal is None:
        colors = []
        seen = set()
        hist = {}
        for key in sorted(wanted):
            s = sprites[key]
            smap = sprite_index_map(key)
            pal = sff.palettes[s.palidx] if s.palidx is not None else []
            for idx in sorted(set(s.pix)):
                if idx == 0:
                    continue
                c = mapped_color(idx, pal[idx] if idx < len(pal)
                                 else (0, 0, 0), smap)
                if c not in seen:
                    seen.add(c)
                    colors.append(c)
            for idx in s.pix:
                if idx == 0:
                    continue
                c = mapped_color(idx, pal[idx] if idx < len(pal)
                                 else (0, 0, 0), smap)
                hist[c] = hist.get(c, 0) + 1
                target = act_target(idx, c, smap)
                if target is not None:
                    votes = src_targets.setdefault(c, {})
                    votes[target] = votes.get(target, 0) + 1
        all_hist = hist
        focus_actions = cfg.get("palette_focus_actions", ())
        if focus_actions:
            focused = {}
            for action in focus_actions:
                for g, n, *_ in air.get(action, ([], -1))[0]:
                    s = sprites.get((g, n))
                    if s is None:
                        continue
                    smap = sprite_index_map((g, n))
                    pal = sff.palettes[s.palidx] if s.palidx is not None else []
                    for idx in s.pix:
                        if idx == 0:
                            continue
                        c = mapped_color(idx, pal[idx] if idx < len(pal)
                                         else (0, 0, 0), smap)
                        focused[c] = focused.get(c, 0) + 1
            if focused:
                hist = focused
                colors = sorted(focused)
        if len(colors) > 15:
            # weighted median cut: split the widest-range bucket at the
            # pixel-count median until 15 buckets remain
            buckets = [sorted(hist)]
            while len(buckets) < 15:
                def spread(bucket):
                    return max(max(c[i] for c in bucket)
                               - min(c[i] for c in bucket)
                               for i in range(3))
                bucket = max(buckets, key=spread)
                if spread(bucket) == 0:
                    break                    # nothing left worth splitting
                buckets.remove(bucket)
                ch = max(range(3),
                         key=lambda i: max(c[i] for c in bucket)
                         - min(c[i] for c in bucket))
                bucket.sort(key=lambda c: c[ch])
                total = sum(hist[c] for c in bucket)
                acc, i = 0, 0
                while i < len(bucket) - 1 and acc < total / 2:
                    acc += hist[bucket[i]]
                    i += 1
                buckets += [bucket[:i], bucket[i:]]
            colors = []
            remap_color = {}
            for bucket in buckets:
                total = sum(hist[c] for c in bucket)
                cent = tuple(sum(c[i] * hist[c] for c in bucket) // total
                             for i in range(3))
                for c in bucket:
                    remap_color[c] = len(colors) + 1
                colors.append(cent)
            if focus_actions:
                # Preserve idle colors in the hardware palette, then map
                # every other action/effect to its nearest idle color.
                remap_color = {
                    c: min(range(1, len(colors) + 1),
                           key=lambda i: sum((colors[i - 1][ch] - c[ch]) ** 2
                                             for ch in range(3)))
                    for c in all_hist
                }
        elif focus_actions:
            # The idle set may use fewer than 15 colors. Keep all of them and
            # map non-idle colors by RGB distance instead of dropping them.
            remap_color = {
                c: min(range(1, len(colors) + 1),
                       key=lambda i: sum((colors[i - 1][ch] - c[ch]) ** 2
                                         for ch in range(3)))
                for c in all_hist
            }
        global_pal = [(0, 0, 0)] + colors
    palidx = remap_color if remap_color is not None else \
        {c: i for i, c in enumerate(global_pal)}

    # P2 mirror palette: keep every tile index stable and only swap the
    # colour behind it.  Pick the most frequent alternate colour for each
    # hardware slot; slots with no source keep the P1 colour.
    def build_alt_pal(alt_ref):
        alt_votes = {}
        for c, counts in src_targets.items():
            slot = palidx.get(c)
            if not slot:
                continue
            bucket = alt_votes.setdefault(slot, {})
            for target, weight in counts.items():
                if target >= len(alt_ref):
                    continue
                alt = alt_ref[target]
                if alt in ((255, 0, 255), (248, 0, 248), (252, 2, 252)):
                    continue
                bucket[alt] = bucket.get(alt, 0) + weight
        out = [(0, 0, 0)]
        for i in range(1, len(global_pal)):
            bucket = alt_votes.get(i)
            out.append(max(bucket, key=bucket.get)
                       if bucket else global_pal[i])
        return out

    def mirror_score(pal):
        diffs = [sum(abs(x - y) for x, y in zip(ca, cb))
                 for ca, cb in zip(pal, global_pal)]
        return (sum(d > 60 for d in diffs), max(diffs), sum(diffs))

    alt_pal = None
    best = None
    for alt_ref in alt_candidates:
        cand = build_alt_pal(alt_ref)
        score = mirror_score(cand)
        # Keep the source palette order: the first clearly different
        # alternate wins.  Otherwise use the most different candidate.
        if score[0] >= 3 and score[1] >= 120:
            alt_pal = cand
            break
        if best is None or score > best[0]:
            best = (score, cand)
    if alt_pal is None and best is not None:
        alt_pal = best[1]
    if alt_pal is None or len(alt_pal) != len(global_pal) \
            or mirror_score(alt_pal)[1] < 60:
        alt_pal = _shift_palette(global_pal, 140)

    # Add palette-safe dissolve/morph cels to clips that still have too few
    # poses after the AIR restoration pass.  The blend is rasterized into the
    # character's 4bpp palette, so it remains ordinary metasprite data at
    # runtime.  We only interpolate where AIR keeps the same attack/hurt-box
    # presence on both sides; hit timing therefore stays attached to the
    # original active frames instead of gaining or losing an active tick at a
    # transition.  Clips with five or more real poses are left alone: the
    # restored source frames are sharper than a dissolve and the SNES upload
    # path already needs one or two vblanks per pose.
    attack_sids = (set(range(5, 9)) | set(range(19, 27)) |
                   set(range(48, 69)) | {67, 68, 98} |
                   set(range(74, 76)) | set(range(85, 90)))
    attack_sids.intersection_update(cfg.get("moves", {}), anim_tables)
    motion_sids = {0, 1, 2, 3, 4, 12, 13, 14, 15, 16, 17, 18,
                   27, 28, 29, 45, 46}
    motion_sids.intersection_update(anim_tables)
    tween_sids = attack_sids | motion_sids
    TWEEN_TARGET = 5                # clips below five poses get a dissolve
    bayer8 = (
        (0, 48, 12, 60, 3, 51, 15, 63),
        (32, 16, 44, 28, 35, 19, 47, 31),
        (8, 56, 4, 52, 11, 59, 7, 55),
        (40, 24, 36, 20, 43, 27, 39, 23),
        (2, 50, 14, 62, 1, 49, 13, 61),
        (34, 18, 46, 30, 33, 17, 45, 29),
        (10, 58, 6, 54, 9, 57, 5, 53),
        (42, 26, 38, 22, 41, 25, 37, 21),
    )
    synthetic = {}
    tweened_sids = set()
    tween_group = -32768
    next_synthetic = 0
    tween_bytes_estimate = 0
    # ROM-resident fighters use their CHR space for restored source frames;
    # synthetic dissolves would compete with them for the same bank.  Omega
    # Rugal has no .orig to restore from, so it keeps a small tween budget.
    if not cfg.get("msu"):
        tween_bytes_budget = 32768 if name == "omegarugal" else 0
    else:
        tween_bytes_budget = None

    def source_palette_index(sprite, source_index, smap=None):
        if not source_index:
            return 0
        srcpal = (sff.palettes[sprite.palidx]
                  if sprite.palidx is not None else [])
        color = srcpal[source_index] if source_index < len(srcpal) else (0, 0, 0)
        return palidx.get(mapped_color(source_index, color, smap), 0)

    def blend_index(a, b, amount):
        if len(global_pal) <= 1:
            return 0
        ca = global_pal[a] if a < len(global_pal) else (0, 0, 0)
        cb = global_pal[b] if b < len(global_pal) else ca
        color = tuple(round(ca[ch] * (1 - amount) + cb[ch] * amount)
                      for ch in range(3))
        return min(range(1, len(global_pal)),
                   key=lambda idx: sum((global_pal[idx][ch] - color[ch]) ** 2
                                       for ch in range(3)))

    def add_tween(left_frame, right_frame, amount=0.5):
        nonlocal next_synthetic, tween_bytes_estimate
        lg, ln, lx, ly, lt, lf, latk, lhurt = left_frame
        rg, rn, rx, ry, rt, rf, ratk, rhurt = right_frame
        if lt == 255 or bool(latk) != bool(ratk) \
                or bool(lhurt) != bool(rhurt):
            return None
        sa, sb = sprites[(lg, ln)], sprites[(rg, rn)]
        if sa.pix is None or sb.pix is None:
            return None
        ax, ay = lx - sa.ax, ly - sa.ay
        bx, by = rx - sb.ax, ry - sb.ay
        if (lg, ln, ax, ay) == (rg, rn, bx, by):
            return None
        x0, y0 = min(ax, bx), min(ay, by)
        x1, y1 = max(ax + sa.w, bx + sb.w), max(ay + sa.h, by + sb.h)
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0 or w * h > 262144:
            return None
        estimated_bytes = min(
            3072, ((w + 15) // 16) * ((h + 15) // 16) * 128)
        if (tween_bytes_budget is not None and
                tween_bytes_estimate + estimated_bytes > tween_bytes_budget):
            return None
        apal = [source_palette_index(sa, i, sprite_index_map((lg, ln)))
                for i in range(256)]
        bpal = [source_palette_index(sb, i, sprite_index_map((rg, rn)))
                for i in range(256)]
        pixels = bytearray(w * h)
        for py in range(h):
            world_y = y0 + py
            sy_a, sy_b = world_y - ay, world_y - by
            for px in range(w):
                world_x = x0 + px
                sx_a, sx_b = world_x - ax, world_x - bx
                ai = (sa.pix[sy_a * sa.w + sx_a]
                      if 0 <= sx_a < sa.w and 0 <= sy_a < sa.h else 0)
                bi = (sb.pix[sy_b * sb.w + sx_b]
                      if 0 <= sx_b < sb.w and 0 <= sy_b < sb.h else 0)
                ac, bc = apal[ai], bpal[bi]
                threshold = (bayer8[py & 7][px & 7] + 0.5) / 64
                if ac and bc:
                    pixels[py * w + px] = blend_index(ac, bc, amount)
                elif bc and threshold < amount:
                    pixels[py * w + px] = bc
                elif ac and threshold >= amount:
                    pixels[py * w + px] = ac
        key = (tween_group, next_synthetic)
        next_synthetic += 1
        cel = Sprite()
        cel.group, cel.number = key
        cel.w, cel.h, cel.ax, cel.ay = w, h, 0, 0
        cel.palidx, cel.link, cel.pix = None, 0, bytes(pixels)
        synthetic[key] = cel
        tween_bytes_estimate += estimated_bytes
        # Reuse the source frame's rectangles. Their presence matches the
        # destination frame (checked above), and reusing them keeps the
        # one-byte runtime box IDs within their existing table budget.
        atk = latk if latk else []
        hurt = lhurt if lhurt else []
        return (key[0], key[1], x0, y0, 1, '', atk, hurt)

    # Process each unique AIR action once and share its generated timeline
    # across the slots that reference that same action. Sliced supers get
    # their own pass.
    clip_groups = {}
    for sid in sorted(tween_sids):
        if sid in cfg.get("tween_skip_sids", ()):
            # The dissolve cel is not always drawable (e.g. Yuri's strong
            # punch tweens land on a blank/offset cel).  Keep the source
            # timing instead of inserting a one-frame hole.
            continue
        anum = anims[sid]
        clip_key = (anum, sid if sid in cfg.get('slices', {}) else None)
        clip_groups.setdefault(clip_key, []).append(sid)
    for (anum, slice_sid), sids in clip_groups.items():
        sid = sids[0]
        frames, loopstart = anim_tables[sid]
        nfr = len(frames)
        if nfr < 2 or nfr >= TWEEN_TARGET:
            continue
        center = (nfr - 1) / 2
        gaps = sorted(range(1, nfr),
                      key=lambda i: (abs((i - 0.5) - center), i))
        if nfr == 2:
            # A single source pair (common on imported jumps) gets a
            # two-step dissolve: 1/3 and 2/3 of the way to the next pose.
            specs = [(1, 1 / 3), (1, 2 / 3)]
        else:
            specs = [(gaps[0], 0.5)]
        by_gap = {}
        for gap, amount in specs:
            by_gap.setdefault(gap, []).append(amount)
        expanded = []
        added = 0
        for i, frame in enumerate(frames):
            for amount in sorted(by_gap.get(i, ())):
                candidate = add_tween(frames[i - 1], frame, amount)
                if candidate is None:
                    continue
                # Borrow one display tick from the preceding pose when
                # possible, keeping the clip's overall duration stable.
                prev = expanded[-1]
                if prev[4] > 1 and prev[4] != 255:
                    expanded[-1] = (*prev[:4], prev[4] - 1, *prev[5:])
                expanded.append(candidate)
                added += 1
            expanded.append(frame)
        if added:
            tweened_sids.update(sids)
            for grouped_sid in sids:
                anim_tables[grouped_sid] = (expanded, loopstart)
            # Source cels have already passed palette construction.  Tween
            # cels are in global palette indices and must not be remapped.
            sprites.update(synthetic)
            wanted.update(synthetic)

    if synthetic:
        print(f"{name}: {len(synthetic)} tween cels (~{tween_bytes_estimate} B)")

    move_ids = cfg.get("moves", {})
    proj_fx = None if cfg.get("projfx_alias") else projectile_effect(
        name, cfg, sff, air, cns_statedefs, cns_headers, move_ids,
        palidx, global_pal, mapped_color)
    alt_spec = PROJECTILE_ALT_EFFECTS.get(name)
    proj_fx_alt = None
    if alt_spec is not None and not cfg.get("projfx_alias"):
        proj_fx_alt = projectile_effect_alt(name, sff, air, alt_spec)
    # A clip with no drawable cells still costs a 2 KiB CHR page.  Empty
    # inferred/invalid clips are exactly the invisible projectiles this
    # generator is trying to avoid; fall back to the shared zero-byte
    # placeholder instead of spending a bank window on nothing.
    if proj_fx is not None and not any(cells for _ticks, cells in proj_fx[1]):
        proj_fx = None
    if proj_fx_alt is not None and not any(cells for _ticks, cells
                                           in proj_fx_alt[1]):
        proj_fx_alt = None

    tiles = bytearray()
    spr_meta = []     # bytes: ncells, (dx,dy,tilelo,tilehi)*n  + axis in header
    spr_ids = {}
    spr_upload_bytes = {}
    spr_shift = {}
    headers = []      # (ax, ay, meta offset)
    max_cells = 0
    max_dma = 0
    for key in sorted(wanted):
        s = sprites[key]
        spr_ids[key] = len(spr_ids)
        remap = [0] * 256
        if key in synthetic:
            # Synthetic tween cels already contain indices in global_pal.
            remap = list(range(256))
            srcpal = global_pal
        else:
            srcpal = sff.palettes[s.palidx] if s.palidx is not None else []
        # SFF color index 0 is transparency.  Keep it mapped to hardware
        # palette entry 0 instead of matching its RGB value to an opaque
        # color in the character's reduced SNES palette; otherwise unused
        # pixels become solid rectangles behind the metasprite.
        remap[0] = 0
        smap = sprite_index_map(key)
        for i, c in enumerate(srcpal[1:], start=1):
            remap[i] = palidx.get(mapped_color(i, c, smap), 0)
        # 16x16 cells; emit 4 tiles per non-empty cell
        cols = (s.w + CELL - 1) // CELL
        rows = (s.h + CELL - 1) // CELL
        cells = []
        cell_tiles = []
        for cy in range(rows):
            for cx in range(cols):
                # any non-transparent pixel in this cell?
                any_px = False
                for yy in range(cy * CELL, min((cy + 1) * CELL, s.h)):
                    row = s.pix[yy * s.w + cx * CELL:
                                yy * s.w + min((cx + 1) * CELL, s.w)]
                    if any(b and remap[b] for b in row):
                        any_px = True
                        break
                if not any_px:
                    continue
                # build a padded 16x16 indexed block
                block = bytearray(CELL * CELL)
                for yy in range(CELL):
                    sy = cy * CELL + yy
                    if sy >= s.h:
                        break
                    for xx in range(CELL):
                        sx = cx * CELL + xx
                        if sx < s.w:
                            block[yy * CELL + xx] = remap[s.pix[sy * s.w + sx]]
                t, _, _ = tiles4bpp(block, CELL, CELL)
                cells.append((cx * CELL - s.ax, cy * CELL - s.ay, 0))
                cell_tiles.append(t)
        # Cell dx/dy are signed bytes and dy+15 must also fit; sprites whose
        # axis sits far from the art (e.g. launcher rise frames) shift the
        # whole cell grid in 16px steps, compensated back in the frame's
        # xoff/yoff at AnimTab emission.
        if cells:
            sx = sy = 0
            while min(c[0] for c in cells) + sx < -128:
                sx += 16
            while max(c[0] + CELL for c in cells) + sx > 128:
                sx -= 16
            while min(c[1] for c in cells) + sy < -128:
                sy += 16
            while max(c[1] + CELL for c in cells) + sy > 128:
                sy -= 16
            if sx or sy:
                cells = [(dx + sx, dy + sy, 0) for dx, dy, _ in cells]
            spr_shift[key] = (sx, sy)
        if len(cells) > 64:
            raise SystemExit(f"{name} {key}: {len(cells)} OBJ cells exceed 64")
        # Dedup identical 16x16 cells. A ping-pong OBJ page is 96 tiles:
        # each unique 16x16 cell costs a fixed 4-tile quad slot (24 slots),
        # while 8x8 sub-cells cost a single tile in any free slot. Sprites
        # needing more than 24 unique big cells split their least-covered
        # cells into non-empty 8x8 quadrants until the page fits; the meta
        # tile word's bit15 marks an 8x8 cell.
        cov = [sum(1 for b in t if b) for t in cell_tiles]
        big = [len({t for t in cell_tiles}) <= 24] * len(cells)
        dropq = [set() for _ in cells]          # quadrants suppressed

        def quad_parts(i):
            t = cell_tiles[i]
            return [(q, t[q * 32:(q + 1) * 32]) for q in range(4)
                    if q not in dropq[i] and any(t[q * 32:(q + 1) * 32])]

        def footprint():
            ub = {cell_tiles[i] for i, b in enumerate(big) if b}
            us = {qt for i, b in enumerate(big) if not b
                  for _, qt in quad_parts(i)}
            nc = sum(1 for b in big if b) + sum(
                len(quad_parts(i)) for i, b in enumerate(big) if not b)
            return len(ub) * 4 + len(us), len(ub), nc

        if not all(big) and not cfg.get("msu"):
            # ROM-resident tile banks are fixed at two banks per fighter, so
            # keep the original, more conservative packing there.  Only the
            # streamed MSU characters can afford the extra unique tiles that
            # the cell-promotion pass adds.
            while True:
                cost, nb, nc = footprint()
                if cost <= 96 and nb <= 24 and nc <= 64:
                    break
                cand = [i for i, b in enumerate(big) if b]
                if cand and nc <= 64:
                    big[min(cand, key=lambda i: (cov[i], i))] = False
                    continue
                parts = [(i, q, sum(1 for b in qt if b))
                         for i in range(len(cells))
                         for q, qt in quad_parts(i)]
                if not parts:
                    break
                i, q, lost = min(parts, key=lambda p: (p[2], p[0], p[1]))
                dropq[i].add(q)
                ART_LOSS.append({'character': name, 'sprite': list(key),
                                 'kind': 'quadrant', 'opaque_pixels': lost})
        if not all(big) and cfg.get("msu"):
            # Phase 1: fit the 96-tile page.  Split cells are cheaper in
            # tiles, so drop the least-covered quadrants until the unique
            # tile budget fits.
            while True:
                cost, nb, nc = footprint()
                if cost <= 96:
                    break
                parts = [(i, q, sum(1 for b in qt if b))
                         for i in range(len(cells))
                         for q, qt in quad_parts(i)]
                if not parts:
                    break
                i, q, lost = min(parts, key=lambda p: (p[2], p[0], p[1]))
                dropq[i].add(q)
                ART_LOSS.append({'character': name, 'sprite': list(key),
                                 'kind': 'quadrant', 'opaque_pixels': lost})
            # Phase 2: fit the 64-OAM-cell cap.  Promote split cells back to
            # a single 16x16 cell: up to four quadrants become one OAM entry,
            # so the artwork stays on the page instead of being thrown away.
            # A 4-quadrant cell costs no extra tiles (4 tiles either way) and
            # saves three cells; 3-quadrant cells cost one tile and save two;
            # 2-quadrant cells cost two tiles and save one.  Without this
            # pass, large imports such as Chang stayed split forever, lost
            # half their art to the 64-cell cap and still left 32 tiles of
            # the page unused.
            while True:
                cost, nb, nc = footprint()
                if nc <= 64 and nb <= 24:
                    break
                best = None
                for i, b in enumerate(big):
                    if b:
                        continue
                    parts = quad_parts(i)
                    if len(parts) < 2:
                        continue
                    ub = {cell_tiles[j] for j, bj in enumerate(big) if bj}
                    ub.add(cell_tiles[i])
                    us = {qt for j, bj in enumerate(big)
                          if not bj and j != i
                          for _, qt in quad_parts(j)}
                    ncost = len(ub) * 4 + len(us)
                    nnc = nc - (len(parts) - 1)
                    if ncost > 96 or len(ub) > 24:
                        continue
                    saved = len(parts) - 1
                    extra = ncost - cost
                    score = (extra / saved, -cov[i], i)
                    if best is None or score < best[0]:
                        best = (score, i)
                if best is not None:
                    big[best[1]] = True
                    continue
                # No promotion fits: free a tile by dropping the least
                # covered quadrant, then retry (the cell cap still needs to
                # be met, so dropping one cell is unavoidable here).
                parts = [(i, q, sum(1 for b in qt if b))
                         for i in range(len(cells))
                         for q, qt in quad_parts(i)]
                if parts:
                    i, q, lost = min(parts,
                                     key=lambda p: (p[2], p[0], p[1]))
                    dropq[i].add(q)
                    ART_LOSS.append({'character': name,
                                     'sprite': list(key),
                                     'kind': 'quadrant',
                                     'opaque_pixels': lost})
                else:
                    # All remaining cells are 16x16.  Drop the least
                    # covered one whole; splitting it would only raise the
                    # OAM cell count again.
                    cand = [(cov[i], i) for i, b in enumerate(big) if b]
                    if not cand:
                        break
                    lost, i = min(cand)
                    big[i] = False
                    dropq[i] = {0, 1, 2, 3}
                    ART_LOSS.append({'character': name,
                                     'sprite': list(key),
                                     'kind': 'cell',
                                     'opaque_pixels': lost})
        # quad slots in first-appearance order; 8x8 tiles fill the singles
        # left over inside the 96-tile page.  Characters with a per-frame DMA
        # cap get their highest-coverage art in the low slots, so the cap
        # below removes the least visible cells first.
        dma_cap = cfg.get("max_dma")
        big_idx = {}
        if dma_cap:
            big_cov = {}
            for i, b in enumerate(big):
                if b:
                    t = cell_tiles[i]
                    big_cov[t] = max(big_cov.get(t, 0), cov[i])
            for t, _ in sorted(big_cov.items(),
                               key=lambda kv: (-kv[1], kv[0])):
                big_idx[t] = len(big_idx)
        else:
            for i, b in enumerate(big):
                if b and cell_tiles[i] not in big_idx:
                    big_idx[cell_tiles[i]] = len(big_idx)
        used_idx = set()
        for i in big_idx.values():
            ti = (i % 8) * 2 + (i // 8) * 32
            used_idx.update((ti, ti + 1, ti + 16, ti + 17))
        free_it = iter(x for x in range(96) if x not in used_idx)
        small_idx = {}
        if dma_cap:
            small_cov = {}
            for i, b in enumerate(big):
                if not b:
                    for _, qt in quad_parts(i):
                        small_cov[qt] = max(
                            small_cov.get(qt, 0), sum(1 for x in qt if x))
            for qt, _ in sorted(small_cov.items(),
                                key=lambda kv: (-kv[1], kv[0])):
                small_idx[qt] = next(free_it)
        else:
            for i, b in enumerate(big):
                if b:
                    continue
                for _, qt in quad_parts(i):
                    if qt not in small_idx:
                        small_idx[qt] = next(free_it)
        max_idx = max(used_idx | set(small_idx.values()), default=-1)
        packed = bytearray((max_idx + 1) * 32)
        bank_used = len(tiles) % 32768
        if bank_used + len(packed) > 32768:
            tiles += bytes(32768 - bank_used)
        first_tile = len(tiles) // 32
        packed_cells = []
        for i, b in enumerate(big):
            dx, dy, _ = cells[i]
            if b:
                j = big_idx[cell_tiles[i]]
                ti = (j % 8) * 2 + (j // 8) * 32
                t = cell_tiles[i]
                packed[ti * 32:(ti + 2) * 32] = t[:64]
                packed[(ti + 16) * 32:(ti + 18) * 32] = t[64:]
                packed_cells.append((dx, dy, ti))
            else:
                for q, qt in quad_parts(i):
                    si = small_idx[qt]
                    packed[si * 32:(si + 1) * 32] = qt
                    packed_cells.append((dx + (q % 2) * 8,
                                         dy + (q // 2) * 8, si | 0x8000))
        if dma_cap:
            # A 16x16 cell costs four tiles in the 2x2 OBJ layout.  Keep only
            # cells whose complete tile span fits in the capped page.  The
            # meta table is rebuilt from the surviving cells below, so no OAM
            # entry points at truncated tile data.
            cap_tiles = dma_cap // 32
            def cell_tile_span(ti):
                base = ti & 0x7fff
                if ti & 0x8000:
                    return (base,)
                return (base, base + 1, base + 16, base + 17)
            before_cap = list(packed_cells)
            kept = [c for c in packed_cells
                    if all(t < cap_tiles for t in cell_tile_span(c[2]))]
            if not kept:
                raise SystemExit(
                    f"{name} {key}: max_dma cap drops every OBJ cell")
            packed_cells = kept
            for cell in before_cap:
                if cell not in kept:
                    ART_LOSS.append({'character': name, 'sprite': list(key),
                                     'kind': 'dma_cap_cell',
                                     'opaque_pixels': None})
            max_idx = max(max(cell_tile_span(c[2])) for c in packed_cells)
            packed = packed[:(max_idx + 1) * 32]
        tiles += packed
        spr_upload_bytes[key] = len(packed)
        cells = packed_cells
        if len(cells) > 64:
            raise SystemExit(f"{name} {key}: {len(cells)} OBJ cells exceed 64")
        max_cells = max(max_cells, len(cells))
        max_dma = max(max_dma, len(packed))
        headers.append((s.ax, s.ay))
        if cells:
            minx = min(c[0] for c in cells)
            miny = min(c[1] for c in cells)
            maxx = max(c[0] + (8 if c[2] & 0x8000 else CELL) for c in cells)
            maxy = max(c[1] + (8 if c[2] & 0x8000 else CELL) for c in cells)
        else:
            minx = miny = maxx = maxy = 0
        meta = bytearray([len(cells)])
        meta += struct.pack("<HH", first_tile, len(packed))
        meta += struct.pack("<bbBB", minx, miny,
                            maxx - minx, maxy - miny)
        for dx, dy, ti in cells:
            meta += struct.pack("<bbH", dx, dy, ti)
        spr_meta.append(bytes(meta))

    # Optional per-sid frame cap (OAM-heavy source poses).  Applied before the
    # upload budget so the surviving frames still get their minimum ticks.
    for _sid, _cap in (cfg.get("frame_cap") or {}).items():
        if _sid in anim_tables:
            _frames, _loop = anim_tables[_sid]
            anim_tables[_sid] = (_frames[:max(1, int(_cap))], _loop)

    # Give every cel enough time for its upload slice.  Both the ROM and the
    # MSU-1 paths stream at most DMACHUNK bytes per vblank, and SprDmaP holds
    # the displayed frame until the queued sprite finishes.  Real AIR frames
    # can be just as heavy as synthetic tweens, so apply the upload-aware
    # minimum to all of them: otherwise a 3 KiB startup pose with a 1-tick
    # AIR frame visibly freezes (Joe's stand HK / 41236 specials are examples).
    # Keep in sync with .DEFINE DMACHUNK in src/engine/fight.asm.
    upload_budget = RUNTIME_ABI["DMACHUNK"]
    for sid, (frames, loopstart) in list(anim_tables.items()):
        adjusted = []
        for frame in frames:
            upload = spr_upload_bytes.get((frame[0], frame[1]), 0)
            need = (upload + upload_budget - 1) // upload_budget
            ticks = max(frame[4], need)
            adjusted.append((*frame[:4], min(255, ticks), *frame[5:]))
        anim_tables[sid] = (adjusted, loopstart)

    # AIR Clsn1/Clsn2 boxes, reduced to one attack and one hurt rectangle per
    # animation element. Multiple MUGEN boxes are unioned so the runtime stays
    # a single 16-bit AABB test; box records are deduplicated.
    box_records = []
    box_ids = {(): 0}
    frame_boxes = {}

    def get_box_id(boxes):
        if not boxes:
            return 0
        cl = lambda v: max(-128, min(127, v))
        rec = tuple(cl(v) for v in
                    (min(b[0] for b in boxes), min(b[1] for b in boxes),
                     max(b[2] for b in boxes), max(b[3] for b in boxes)))
        if rec not in box_ids:
            if len(box_records) >= 255:
                # The animation frame stores attack/hurt box ids in one byte
                # each.  Billy has 266 distinct AIR rectangles, so fold the
                # overflow variants onto the closest existing record instead
                # of emitting ids the runtime cannot address.
                near = min(range(1, len(box_records) + 1),
                           key=lambda i: sum(abs(a - b) for a, b in
                                            zip(box_records[i - 1], rec)))
                box_ids[rec] = near
                return near
            box_ids[rec] = len(box_records) + 1
            box_records.append(rec)
        return box_ids[rec]

    for sid, (frames, _loopstart) in anim_tables.items():
        for i, frame in enumerate(frames):
            frame_boxes[(sid, i)] = (get_box_id(frame[6]),
                                     get_box_id(frame[7]))

    inc = []
    inc.append(f"; generated by build_fight.py -- {name} sprites\n")
    inc.append(f"{name.upper()}_NSPR = {len(spr_ids)}\n")
    if proj_fx:
        _proj_action, proj_frames, proj_chr = proj_fx
    else:
        proj_chr = bytes([0])
        proj_frames = [(1, [])]
    inc.append(f"{name}SprOfs:\n")
    ofs = 0
    for meta in spr_meta:
        inc.append(f"    .dw {name}SprData+{ofs}\n")
        ofs += len(meta)
    inc.append(f"{name}SprData:\n")
    for meta in spr_meta:
        inc.append("    .db " + ",".join(f"${b:02X}" for b in meta) + "\n")
    if not cfg.get("projfx_alias"):
        PROJECTILE_BLOBS[name] = proj_chr
        PROJECTILE_TABLES[name] = proj_frames
        if proj_fx_alt is not None:
            PROJECTILE_BLOBS2[name] = proj_fx_alt[2]
            PROJECTILE_TABLES2[name] = proj_fx_alt[1]
            PROJECTILE_ALT_SIDS[name] = set(alt_spec.get("sids", ()))
            PROJECTILE_ALT_RELEASE[name] = {
                sid: int(alt_spec.get("release", 2))
                for sid in PROJECTILE_ALT_SIDS[name]}

    # Box IDs index 16-bit record pointers in this table. ID 0 is no box.
    inc.append(f"{name}BoxTab:\n    .dw 0\n")
    for i, rec in enumerate(box_records, 1):
        inc.append(f"    .dw {name}Box{i}\n")
    for i, rec in enumerate(box_records, 1):
        inc.append(f"{name}Box{i}:\n    .db " +
                   ",".join(f"${v & 0xFF:02X}" for v in rec) + "\n")

    # anim frames: dw sprid, db ticks,xoff,yoff,flags,atkbox,hurtbox (8 bytes)
    # state ids that resolve to the same MUGEN anim share one data body --
    # except sliced sids, which each emit their own slice of the anim.
    inc.append(f"{name}AnimTab:\n")
    nsid = max(anim_tables) + 1
    slices = cfg.get("slices", {})
    anum_label = {}
    for sid in range(nsid):
        anum = anims[sid]
        key = ((anum, sid) if (sid in slices or (sid == 97 and charge)
               or sid in POSE_UNIQUE_ANIM_SIDS.get(name, ())) else
               (anum, "tween") if sid in tweened_sids else anum)
        if key not in anum_label:
            anum_label[key] = f"{name}Anim{sid}"
        inc.append(f"    .dw {anum_label[key]}\n")
    emitted = set()
    for sid in range(nsid):
        anum = anims[sid]
        key = ((anum, sid) if (sid in slices or (sid == 97 and charge)
               or sid in POSE_UNIQUE_ANIM_SIDS.get(name, ())) else
               (anum, "tween") if sid in tweened_sids else anum)
        if key in emitted:
            continue
        emitted.add(key)
        frames, loopstart = anim_tables[sid]
        inc.append(f"{name}Anim{sid}:\n    .db {len(frames)},{loopstart}\n")
        for i, (g, n, x, y, t, flip, _atk, _hurt) in enumerate(frames):
            if sid == 0 and cfg.get("idle_frame_ticks"):
                t = max(t, cfg["idle_frame_ticks"])
            if sid == 0 and cfg.get("idle_frame_scale"):
                t = max(1, round(t * cfg["idle_frame_scale"]))
            flags = ("H" in flip and 1 or 0) | ("V" in flip and 2 or 0)
            atk_id, hurt_id = frame_boxes[(sid, i)]
            sx, sy = spr_shift.get((g, n), (0, 0))
            inc.append(f"    .dw {spr_ids[(g, n)]}\n"
                       f"    .db {min(t, 255)},{(x - sx) & 0xFF},"
                       f"{(y - sy) & 0xFF},"
                       f"{flags},{atk_id},{hurt_id}\n")

    move_ids = cfg.get("moves", {})
    persist = set(cfg.get("persist", ()))   # hitdefpersist sids (flag bit2)
    empty_move = {"active": 0, "damage": 0, "hittime": 0,
                  "slidetime": 0, "gvx": 0, "gvy": 0, "avx": 0, "avy": 0,
                  "fall": 0, "trip": 0, "animtype": 0, "low": 0, "guard": 0,
                  "gdamage": 0, "grvx": 0, "agvx": 0, "agvy": 0,
                  "p2state": 0xFF, "p2pause": 0, "p1pause": 0, "p1gpause": 0,
                  "p1mugen": -1, "throw": 0}
    move_rows = [cns_moves.get(move_ids.get(sid, -1), empty_move)
                 for sid in range(nsid)]
    # sliced sids pick their own HitDef row out of the shared statedef and
    # shift the active frame into the slice's local timeline
    for sid, (hidx, _nxt) in cfg.get("slice_hits", {}).items():
        lst = cns_hitdef_lists.get(move_ids.get(sid, -1))
        if lst and hidx < len(lst):
            row = dict(lst[hidx])
            row["active"] = max(0, row["active"] - slices[sid][1])
            move_rows[sid] = row
    # Cloned normal states carry every HitDef of the source; pick the row
    # whose anim/strength matches the cloned header instead of the first.
    for sid, hidx in cfg.get("hitdef_by_sid", {}).items():
        lst = cns_hitdef_lists.get(move_ids.get(sid, -1))
        if lst and 0 <= hidx < len(lst):
            move_rows[sid] = dict(lst[hidx])
    # AIR trimming shifts the HitDef's animelem start: the engine activates
    # hits only on frames >= active-1, so when no surviving frame at/after
    # that index carries an atkbox the move whiffs forever.  Re-anchor the
    # window to the first clsn-bearing frame.
    for sid, move in enumerate(move_rows):
        if move["active"] <= 0 or sid not in anim_tables:
            continue
        nfr = len(anim_tables[sid][0])
        start = move["active"] - 1
        atk_idx = [i for i in range(nfr)
                   if frame_boxes.get((sid, i), (0, 0))[0]]
        if atk_idx and atk_idx[-1] < start:
            move["active"] = atk_idx[0] + 1
    # Source-specific damage normalisation.  Imported characters whose CNS
    # was authored on another life scale (Chun-Li/XI uses 1500 HP) carry
    # fixed HitDef values that the KOF98 2.0 factor over-amplifies.  The
    # scale is applied after calibration and before DamageTab emission, so
    # hitboxes/timings stay untouched; per-state entries cover the
    # multi-hit supers that would otherwise remove a whole bar.
    dmg_scale_default = cfg.get("damage_tab_scale")
    dmg_scale_by_state = dict(cfg.get("damage_tab_scale_by_state", {}))
    # Automatic Kyo-relative normalization for imports whose source used a
    # different life/damage scale.  Kyo is also the fallback reference when
    # no explicit damage_tab_scale is present.  Only fighters whose normal
    # median is more than 2x Kyo's are touched; the per-state cap keeps a
    # single super from crossing Kyo's maximum while leaving multi-hit
    # supers proportional.
    if (dmg_scale_default is None and not dmg_scale_by_state
            and name not in ("kyo", "kyonests", "kyoash", "omegarugal")):
        kyo_med, kyo_max = kyo_damage_profile()
        med, mx = damage_profile(move_rows)
        if kyo_med and med > kyo_med * 2:
            factor = max(0.05, min(1.0, kyo_med / med))
            cap = kyo_max * 1.25
            for sid, row in enumerate(move_rows):
                dmg = row.get("damage", 0)
                if dmg and dmg * factor > cap:
                    dmg_scale_by_state[sid] = cap / dmg
            dmg_scale_default = factor
            print(f"{name}: damage normalized x{factor:.3f} "
                  f"(normal {med:.1f} -> {kyo_med:.1f}, "
                  f"max {mx} -> {min(mx * factor, cap):.0f})")
    if dmg_scale_default is not None or dmg_scale_by_state:
        for sid in range(len(move_rows)):
            factor = dmg_scale_by_state.get(
                sid, 1.0 if dmg_scale_default is None else dmg_scale_default)
            if factor == 1.0:
                continue
            row = dict(move_rows[sid])
            for key in ("damage", "gdamage"):
                value = row.get(key, 0)
                if value:
                    row[key] = max(1, int(round(value * factor)))
            move_rows[sid] = row
    # Cap normal pushback after the source/calibration values are final so
    # every fighter -- Yuri included -- stays within the same screen budget.
    limit_normal_pushback(move_rows)
    # Explicit per-slice damage (e.g. a source state whose HitDefs are split
    # across several runtime sids).  Applied after normalization so the
    # requested total is exact and the source CNS stays untouched.
    for sid, dmg in cfg.get("slice_damage", {}).items():
        if 0 <= sid < len(move_rows):
            row = dict(move_rows[sid])
            row["damage"] = int(dmg)
            move_rows[sid] = row
    # first-wins: one mugen state mapped to several sids (slices) resolves
    # to the first slice for command/state lookups
    state_to_sid = {}
    for _sid, _st in move_ids.items():
        state_to_sid.setdefault(_st, _sid)
    for label, key in (("ActiveTab", "active"), ("DamageTab", "damage"),
                       ("HitTimeTab", "hittime"),
                       ("SlideTab", "slidetime"),
                       ("GDmgTab", "gdamage")):
        inc.append(f"{name}{label}:\n")
        for move in move_rows:
            inc.append(f"    .dw {move[key]}\n")
    # HitVel records are 8 bytes/state: ground vx,vy then air vx,vy.
    inc.append(f"{name}HitVelTab:\n")
    for move in move_rows:
        inc.append(f"    .dw ${move['gvx'] & 0xFFFF:04X},"
                   f"${move['gvy'] & 0xFFFF:04X},"
                   f"${move['avx'] & 0xFFFF:04X},"
                   f"${move['avy'] & 0xFFFF:04X}\n")
    # GuardVel records are 6 bytes/state: guard ground gx then air gx,gy.
    inc.append(f"{name}GVelTab:\n")
    for move in move_rows:
        inc.append(f"    .dw ${move['grvx'] & 0xFFFF:04X},"
                   f"${move['agvx'] & 0xFFFF:04X},"
                   f"${move['agvy'] & 0xFFFF:04X}\n")
    # bit0 = knockdown (HitDef fall=1 or ground.type=Trip)
    # bit1 = low hit (ground.type=Low)
    # bit2 = hitdefpersist (persist sids)
    # bit3 = throw HitDef (attr ...T): bypasses guard, needs a throwable
    #        victim, spawns no spark
    # bits 4-7 = guardflag H/M/L/A (blocking postures that stop the hit)
    # bits 8-10 = MUGEN animtype (0 light, 1 medium, 2 heavy, >=3 -> 5030)
    # bit 11 = trip (ground.type=Trip): falls with the 5070 crumple anim
    # bit 12 = state owns horizontal velocity through a non-zero VelSet
    #          (ActTab op5): StSpecial must not pin F_VX to zero
    vel_states = {state for state, rows in cns_acts.items()
                  if any(op == 5 and arg != 0
                         for _f, op, arg, _c in rows)}
    inc.append(f"{name}FlagsTab:\n")
    for sid, move in enumerate(move_rows):
        flags = (move["fall"] | move["low"] << 1 | move["throw"] << 3 |
                 move["guard"] << 4 | move["animtype"] << 8 |
                 move["trip"] << 11)
        if sid in persist:
            flags |= 4                     # bit2 = hitdefpersist
        if move_ids.get(sid) in vel_states:
            flags |= 0x1000                # bit12 = VelSet-driven movement
        if sid in AIR_GUARD_DENY_SIDS:
            flags |= 0x2000                # bit13 = ground normal: no air guard
        # bits14-15 = juggle cost tier.  MUGEN's StateDef `juggle` is the
        # source's juggle-point requirement; group it into four tiers so the
        # flag word stays 16-bit.  Any real attack with juggle=0 costs 1, so
        # repeated relaunches cannot loop forever.
        try:
            juggle = int(float(cns_headers.get(
                move_ids.get(sid, -1), {}).get("juggle", "0") or 0))
        except (TypeError, ValueError):
            juggle = 0
        tier = 3 if juggle >= 12 else 2 if juggle >= 6 else \
            1 if juggle >= 1 else 0
        if tier == 0 and move.get("active", 0) > 0:
            tier = 1
        flags |= (tier & 3) << 14
        if sid in cfg.get("slice_no_fall", ()):
            # Mid-combo slices: keep the victim in hitstun so the next
            # contact can connect.  The source marks intermediate hits with
            # fall=1, but the native victim would go straight to S_DOWN and
            # become unhittable, dropping the final launcher.
            flags &= ~1
        inc.append(f"    .dw {flags}\n")
    # TargetTab records (4 bytes): {runtime p2 state, victim hit-pause,
    # runtime p1 state on hit ($FF = stay), flags}.  flags bit0 = victim
    # keeps its own sprite data (throw: ChangeAnim2 timings are compiled
    # per-character, so bit1 of F_GRAB stays clear).
    inc.append(f"{name}TargetTab:\n")
    for move in move_rows:
        p1 = state_to_sid.get(move.get("p1mugen", -1), 0xFF)
        inc.append(f"    .db ${move['p2state']:02X},{move['p2pause']},"
                   f"${p1:02X},{move['throw']}\n")
    inc.append(f"{name}ButtonTab:\n")
    for mask, sid in button_rows["stand"]:
        inc.append(f"    .dw ${mask:04X},{sid}\n")
    inc.append(f"{name}ButtonTabEnd:\n")
    inc.append(f"{name}CButtonTab:\n")
    for mask, sid in button_rows["crouch"]:
        inc.append(f"    .dw ${mask:04X},{sid}\n")
    inc.append(f"{name}CButtonTabEnd:\n")
    inc.append(f"{name}AButtonTab:\n")
    for mask, sid in button_rows["air"]:
        inc.append(f"    .dw ${mask:04X},{sid}\n")
    inc.append(f"{name}AButtonTabEnd:\n")

    # command matcher tables.  CmdTab rows (5 bytes each, $FF terminator):
    # motion idx, held dirs, forbidden held dirs, posture mask, state.
    # MotTab points at motion records: .db nelem,window then (dir,btn)
    # element bytes in input order.
    cmddefs = parse_command_defs(os.path.join(ROOT, cfg["cmd"]))
    # MUGEN allows literal button combos as command names in State -1
    # triggers (Terry/Athena/KOF98 throw "x+y") without a [Command] block.
    # The native matcher only knows named commands, so synthesize their
    # button definition or the throw rule is silently dropped.
    _cmd_text = open(os.path.join(ROOT, cfg["cmd"]), encoding="utf-8-sig",
                     errors="replace").read()
    for _cname in re.findall(r'command\s*=\s*"([^"]+)"', _cmd_text):
        if _cname in cmddefs or "+" not in _cname:
            continue
        _bits = 0
        for _part in _cname.split("+"):
            _bt = btn_token(_part)
            if not _bt:
                _bits = 0
                break
            _bits |= _bt
        if _bits:
            cmddefs[_cname] = (0, [(0, _bits)], 15)
    apply_input_calibration(cmddefs, calibration)
    # Per-character command-window overrides: long double-motion supers
    # need a wider buffer than the shared special default.
    for cname, (held, elems, window) in list(cmddefs.items()):
        for prefix, frames in (cfg.get("cmd_frames") or {}).items():
            if cname.upper().startswith(prefix.upper()):
                cmddefs[cname] = (held, elems, frames)
                break
    wired = {}
    for _sid, _mu in move_ids.items():
        wired.setdefault(_mu, _sid)            # first slice sid wins
    # Keep the classic records for the PRACTICE command list; the matcher
    # uses the diagonal-free HCF/HCB forms plus DP/RDP shortcut rules.
    display_defs = dict(cmddefs)
    apply_half_circle_shortcuts(cmddefs)
    rules = cmd_rules(os.path.join(ROOT, cfg["cmd"]), cmddefs, wired)
    rules = add_shortcut_rules(rules, cmddefs)
    rules.sort(key=lambda rule: motion_rank(rule, cmddefs), reverse=True)
    # Explicit priority for commands whose motion is a subset of another
    # rule's tail (Lucky's SHOOT = DP+kick also completes the DP special).
    # Stable sort keeps the per-length order among the remaining rules.
    for _motion in reversed(cfg.get("cmd_priority", ())):
        rules.sort(key=lambda r: r["motion"].split("#", 1)[0] != _motion)
    # System slots are wired explicitly per character.  When a source state
    # is shared with a normal/air move (e.g. Billy's CD state 240 is also
    # his stand strong kick), state->sid first-wins maps the command to the
    # lower slot.  Pin the system command back to its own slot so L / L+dir
    # / R always enter the evade and blowback states.
    sys_cmd_sids = {"ESQ_F": 95, "ESQ_B": 94, "ESQ_L": 69, "CD": 67}
    for r in rules:
        if r["state"] == 74:
            continue                      # close-range throw shares "CD"
        sid = sys_cmd_sids.get(r["motion"].split("#", 1)[0])
        if sid is not None and sid in move_ids:
            r["state"] = sid
    if calibration and calibration.get("wire_dash"):
        for sid, motion in ((45, "FF"), (46, "BB")):
            if sid not in move_ids or motion not in cmddefs:
                continue
            if any(rule["state"] == sid for rule in rules):
                continue
            rules.append({"motion": motion, "held": 0, "nheld": 0,
                          "posture": 1, "dist": 0, "nstate": 0,
                          "state": sid})
    # x+y is both the CD blowback and the close throw in the source CMD;
    # MUGEN resolves them by trigger order.  The native matcher scans rows in
    # order, so put the throw first and gate it by range; the blowback row
    # still fires when the opponent is farther away.
    for r in rules:
        if r["state"] == 74 and r["dist"] == 0:
            r["dist"] = 40
            r["vgate"] = 1
    rules.sort(key=lambda r: r["state"] != 74)
    mot_ids = {}
    for r in rules:
        if r["motion"] not in mot_ids:
            mot_ids[r["motion"]] = len(mot_ids)
    inc.append(f"{name}MotTab:\n")
    for i in range(len(mot_ids)):
        inc.append(f"    .dw {name}Mot{i}\n")
    for cname, i in mot_ids.items():
        _held, elems, win = cmddefs[cname]
        inc.append(f"{name}Mot{i}: .db {len(elems)},{min(win + 3, 31)}\n")
        for d, b in elems:
            inc.append(f"    .db {d},{b}\n")
    inc.append(f"{name}CmdTab:\n")
    for r in rules:
        held = r["held"] | cmddefs[r["motion"]][0]
        inc.append(f"    .db {mot_ids[r['motion']]},{held},"
                   f"{r['nheld']},{r['posture']},{r['dist']},"
                   f"{r['nstate']},{r['state']}\n")
    inc.append("    .db $FF\n")

    # normal-attack chain/cancel rules.  ChainTab rows (7 bytes each, $FF
    # terminator): from sid, to sid, held dirs, t_norm, t_hit, pad mask
    # (16-bit).  Fires when in from_sid with the pad bit just pressed and
    # either frame >= t_norm or (hitcontact and frame >= t_hit).
    chains = chain_rules(os.path.join(ROOT, cfg["cmd"]),
                         cfg["buttons"], cfg["moves"])
    inc.append(f"{name}ChainTab:\n")
    for fsid, tsid, held, pad, tn, th in chains:
        inc.append(f"    .db {fsid},{tsid},{held},{tn},{th}\n")
        inc.append(f"    .dw ${pad:04X}\n")
    inc.append("    .db $FF\n")

    # Special/super cancel gate.  The descriptor carries a pointer to this
    # character's six strong-normal opens.  CancelGate additionally requires
    # F_HITDONE, so only a connected strong normal opens the window.  Opens
    # come from the character's MUGEN var(1) Combo windows, capped at the
    # middle element; strong normals without a source window fall back to
    # exactly half.
    CANCEL_OPENS[name] = cancel_windows(
        os.path.join(ROOT, cfg["cns"]), cfg["moves"],
        {sid: len(anim_tables[sid][0])
         for sid in range(nsid) if sid in anim_tables})

    # PowTab[sid] = signed word power delta applied on state entry
    # (statedef-header poweradd plus PowerAdd controllers, summed).
    # Negative deltas are spends and double as the `power >=` cmd gate.
    # Only the first slice of a split state pays the cost.
    inc.append(f"{name}PowTab:\n")
    pow_ovr = cfg.get("pow_override", {})
    max_sids = cfg.get("_max_sids", set())
    pow_costs = {}
    cmd_sids = {r["state"] for r in rules}
    for sid in range(nsid):
        _state = move_ids.get(sid, -1)
        d = pow_ovr.get(sid, cns_powadds.get(_state, 0))
        if sid in max_sids:
            # PowTab stores the cost that still applies inside MAX; CmdTry
            # adds the remainder to reach 3000 outside MAX.
            d = state_power_base(cns_headers, cns_statedefs, _state)
        if sid == 96:
            d = -1000  # MAX burst always costs one stock
        elif sid in (69, 94, 95, 97):
            # System dodge/evades are always free.
            d = 0
        elif 85 <= sid <= 89 and sid in cmd_sids and d > -1000:
            # Every reachable super costs at least one stock.  Follow-up
            # slices often carry no PowerAdd of their own.
            d = -1000
        if sid in slices:
            anum = slices[sid][0]
            first = min(s for s, spec in slices.items() if spec[0] == anum)
            if sid != first:
                d = 0
        pow_costs[sid] = d
        inc.append(f"    .dw {d}\n")

    # ProjTab[sid] = 6B: vx 8.8, damage, hit sound, guard mask, present.
    # The old release-frame byte was never used at runtime (ProjTrySpawn fires
    # on the third launch frame), so it now carries H/M/L/A<<4.
    # Presence is separate from velocity so stationary projectiles are valid.
    # Present bits: 0 = exists, 1 = upper-torso height, 2 = alternate ProjFx,
    # 3-7 = 1-based release frame (0 = engine default third frame).
    # Artwork comes from the active character's compact clip in ProjFxGlobal.
    inc.append(f"{name}ProjTab:\n")
    for sid in range(nsid):
        vx, dmg, _anim, guard = projs.get(sid, (0, 0, 0, 0))
        # Presence, not velocity, decides whether a shot exists: stationary
        # supers (Geese's Raging Storm) still need their launch HitDef sound.
        hit_sfx = cns_hitsnds.get(move_ids.get(sid, -1), 5) \
            if sid in projs else 0
        present = int(sid in projs)
        if sid in PROJECTILE_TORSO_SIDS.get(name, ()):
            present |= 0x02             # per-shot upper-torso spawn height
        if sid in PROJECTILE_ALT_SIDS.get(name, ()):
            present |= 0x04             # select the alternate ProjFx clip
        release = PROJECTILE_ALT_RELEASE.get(name, {}).get(sid)
        if release is not None:
            # Bits 3-7 carry a 1-based release frame (0 = engine default).
            present |= ((release + 1) & 0x1F) << 3
        inc.append(f"    .db ${vx&0xFF:02X},${vx>>8:02X},{dmg},{hit_sfx},"
                   f"${(guard & 0x0F) << 4:02X},{present}\n")

    # AiTab: header (count, style, aggression, defense, special rate,
    # super rate, preferred range, anti-air/throw/mixup rates, personality
    # flags) followed by 6-byte move rows: sid, min px, max px, flags,
    # cost/100, weight.  The first six bytes keep the original ABI; the
    # profile extension is appended so the runtime can scale a character's
    # personality with the difficulty level.
    (ai_style, ai_aggr, ai_def, ai_spec, ai_super, ai_rows,
     ai_prof) = ai_move_table(
        name, rules, move_ids, pow_costs, max_sids, projs, cfg)
    zlo, zhi, aa_r, throw_r, mix_r, pflags = ai_prof
    AI_TABLES.append(f"{name}AiTab:\n")
    AI_TABLES.append(f"    .db {len(ai_rows)},{ai_style},{ai_aggr},{ai_def},"
                     f"{ai_spec},{ai_super}\n")
    AI_TABLES.append(f"    .db {zlo},{zhi},{aa_r},{throw_r},{mix_r},"
                     f"{pflags}\n")
    for sid, lo, hi, flags, cost100, weight in ai_rows:
        AI_TABLES.append(
            f"    .db {sid},{lo},{hi},${flags:02X},{cost100},{weight}\n")

    # TransTab: intra-state ChangeState rows (5 bytes, $FF terminator):
    #   .db from_sid, to_sid, kind ; .dw arg.  kind 0 anim-end, 1 land at
    #   y<=arg px while falling, 2 air follow-up on pad arg while rising,
    #   3 MoveHit.  Sliced states chain through synthetic kind-0 rows.
    state_to_sids = {}
    for sid, mstate in move_ids.items():
        state_to_sids.setdefault(mstate, []).append(sid)
    trows = trans_rules(cns_statedefs, cns_headers, state_to_sid,
                        cfg["buttons"], state_to_sids)
    # a sliced sid's statedef-derived "anim end -> stand" row is the
    # ORIGINAL mugen state's end-of-move; each slice exits through its
    # chain row instead.  TransEnd takes the first kind-0 match and
    # trows is sorted by (from,to), so a leftover (87,0) row would win
    # over (87,88) and kill the chain.
    trows = [r for r in trows
             if not (r[0] in slices and r[1] == 0 and r[2] == 0)]
    for sid, (_hi, nxt) in cfg.get("slice_hits", {}).items():
        trows.append((sid, nxt, 0, 0))
    # a sid whose only rows are "live" (kind>=1) would freeze on its last
    # frame when the trigger never fires; give 85 the mugen anim-end exit
    have_k0 = {r[0] for r in trows if r[2] == 0}
    have_live = {r[0] for r in trows if r[2] >= 1}
    for sid in have_live - have_k0:
        trows.append((sid, 0, 0, 0))
    for row in cfg.get("extra_trans", ()):
        trows.append(tuple(row))
    # TransEnd returns the FIRST kind-0 row for a from_sid, so the generic
    # "anim end -> stand" recovery row must sort after real chain targets
    # (else 53->0 shadows 53->60 and a follow-up never fires).
    trows.sort(key=lambda r: (r[0], r[1] == 0, r[1], r[2], r[3]))
    inc.append(f"{name}TransTab:\n")
    for fsid, tsid, kind, arg in trows:
        inc.append(f"    .db {fsid},{tsid},{kind}\n")
        inc.append(f"    .dw ${arg & 0xFFFF:04X}\n")
    inc.append("    .db $FF\n")

    # EVelTab: sparse statedef `velset` applied on state entry, 5-byte rows
    # (.db sid, .dw vx, vy; vx is facing-relative).  vy is screen-space
    # (negative = rising).  $FF terminates.  `state_vel` supplies entry
    # velocities for imported states whose source uses a Time=[a,b] VelSet
    # controller (which the extractor cannot represent).
    inc.append(f"{name}EVelTab:\n")
    state_vel = cfg.get("state_vel", {})
    for sid in range(nsid):
        if sid in state_vel:
            vx, vy = state_vel[sid]
            vx = int(round(vx / coord_scale * 256))
            vy = int(round(vy / coord_scale * 256))
            inc.append(f"    .db {sid}\n")
            inc.append(f"    .dw ${vx & 0xFFFF:04X},${vy & 0xFFFF:04X}\n")
            continue
        mstate = move_ids.get(sid, -1)
        vs = cns_headers.get(mstate, {}).get("velset")
        if vs is None:
            continue
        parts = [p.strip() for p in vs.split(",")]
        if len(parts) < 2:
            continue
        try:
            vx = int(round(float(parts[0]) / coord_scale * 256))
            vy = int(round(float(parts[1]) / coord_scale * 256))
        except ValueError:
            continue
        inc.append(f"    .db {sid}\n")
        inc.append(f"    .dw ${vx & 0xFFFF:04X},${vy & 0xFFFF:04X}\n")
    inc.append("    .db $FF\n")

    def _slice_rows(d, sid):
        """Frame-indexed timeline rows for sid, windowed and shifted into
        the slice's local frames when sid is an anim slice.  Exact state-time
        rows (trigger bit7) are not frames: they stay with the first slice."""
        rows = d.get(move_ids.get(sid, -1), ())
        if sid in slices:
            _a, lo, hi = slices[sid]
            hi = 999 if hi is None else hi
            rows = [(f - lo, *rest) if not (f & 0x80) else (f, *rest)
                    for f, *rest in rows
                    if (f & 0x80 and lo == 0)
                    or (not (f & 0x80) and lo <= f <= hi)]
        return rows

    # PosAdd timeline: PosTab[sid] -> {elem.b, dx.b}* terminated by $FF.
    inc.append(f"{name}PosTab:\n")
    for sid in range(nsid):
        rows = _slice_rows(cns_posadds, sid)
        inc.append(f"    .dw {name}Pos{sid}\n" if rows else "    .dw 0\n")
    for sid in range(nsid):
        rows = _slice_rows(cns_posadds, sid)
        if rows:
            inc.append(f"{name}Pos{sid}:\n")
            for elem, dx in rows:
                inc.append(f"    .db {elem},{dx & 0xFF}\n")
            inc.append("    .db $FF\n")

    # TargetBind windows: BindTab[sid] -> {lo.b, hi.b, dx.s8, dy.s8}*,
    # $FF terminated.  dy is mugen-space (negative = up).
    inc.append(f"{name}BindTab:\n")
    for sid in range(nsid):
        rows = cns_binds.get(move_ids.get(sid, -1))
        inc.append(f"    .dw {name}Bind{sid}\n" if rows else "    .dw 0\n")
    for sid in range(nsid):
        rows = cns_binds.get(move_ids.get(sid, -1))
        if rows:
            inc.append(f"{name}Bind{sid}:\n")
            for lo, hi, dx, dy in rows:
                inc.append(f"    .db {lo},{hi},{dx & 0xFF},{dy & 0xFF}\n")
            inc.append("    .db $FF\n")

    # Actions: ActTab[sid] -> {trigger.b, op.b, arg.b, cond.b}*, $FF.
    # trigger bit7 selects exact state time; clear values select anim elems.
    # op 0=turn self, 1=posadd x (facing-relative), 2=target facing *=arg,
    # 3=target life add, 4=target state (mugen state, resolved here),
    # 5=velset x (px/frame, facing-relative), 6=global pause ticks,
    # 7=playsnd (arg = runtime sfx id), 16=velmul x (arg = Q8 factor),
    # 17=clear velmul.
    # cond bit0 = only when the F_TFLAGS fwd bit was set at grab time.
    inc.append(f"{name}ActTab:\n")
    act_sids = {}
    for sid in range(nsid):
        rows = _slice_rows(cns_acts, sid)
        out = []
        for frame, op, arg, cond in (rows or ()):
            if op == 4:
                arg = VICTIM_STATE_IDS.get(arg, state_to_sid.get(arg, 0xFF))
                if arg == 0xFF:
                    continue
            out.append((frame, op, arg, cond))
        act_sids[sid] = out
        inc.append(f"    .dw {name}Act{sid}\n" if out else "    .dw 0\n")
    for sid in range(nsid):
        if act_sids[sid]:
            inc.append(f"{name}Act{sid}:\n")
            for frame, op, arg, cond in act_sids[sid]:
                inc.append(f"    .db {frame},{op},{arg & 0xFF},{cond}\n")
            inc.append("    .db $FF\n")

    # Per-state HitDef hitsound: byte = runtime sfx id, $FF = silent.
    inc.append(f"{name}HitSndTab:\n")
    for sid in range(nsid):
        if sid in cfg.get("hitdef_by_sid", {}):
            # cloned normals: the chosen HitDef may be stronger than the
            # first one in the source state.
            at = move_rows[sid].get("animtype", 2)
            snd = {0: 4, 1: 5}.get(at, 6)
        else:
            snd = cns_hitsnds.get(move_ids.get(sid, -1), 0xFF)
        inc.append("    .db $%02X\n" % snd)

    # Per-state HitDef pausetime (.db): attacker hitstop ticks, applied as
    # the global freeze on contact.  guard.pausetime folds into pausetime --
    # the sources are within ~2 ticks of each other on every HitDef here.
    inc.append(f"{name}PauseTab:\n")
    for sid in range(nsid):
        mv = move_rows[sid]
        inc.append("    .db %d\n" % (mv.get("p1gpause", 0)
                                     if mv.get("guard") else
                                     mv.get("p1pause", 0)))

    # Per-state HitDef envshake byte ((ampl<<5)|ticks, 0 = none); the engine
    # starts a screen shake when the state's HitDef connects.
    inc.append(f"{name}ShakeTab:\n")
    for sid in range(nsid):
        inc.append("    .db $%02X\n" % move_rows[sid].get("eshake", 0))

    # Reversal windows (Kung Fu Blocking parry / counter-grab):
    # RevTab[sid] -> 4-byte row {window.b, blocked sid.b, posture mask.b,
    # victim sid.b (0xFF = parry only)} or 0.  The mask uses ct_post bits
    # (S=1 C=2 A=4) for allowed attacker postures.
    inc.append(f"{name}RevTab:\n")
    for sid in range(nsid):
        rev = cns_reversals.get(move_ids.get(sid, -1))
        inc.append(f"    .dw {name}Rev{sid}\n" if rev else "    .dw 0\n")
    for sid in range(nsid):
        rev = cns_reversals.get(move_ids.get(sid, -1))
        if rev:
            win, bmugen, cls, vmugen = rev
            bsid = state_to_sid.get(bmugen, 0xFF)
            vsid = state_to_sid.get(vmugen, 0xFF) if vmugen >= 0 else 0xFF
            inc.append(f"{name}Rev{sid}:\n")
            inc.append(f"    .db {win},{bsid},{cls},{vsid}\n")

    # Compiled Explod rows (16B each): anim idx into SparkAnimTab, ttl,
    # OAM attr, anchor (bit0: y rel. to ground), xoff/yoff px, vx/vy/ay
    # in 8.8 fixed point.  Reached from ActTab op14 rows.
    inc.append(f"{name}ExpTab:\n")
    for anim, xoff, yoff, vx, vy, ay, ttl, attr in cns_exprows:
        inc.append(f"    .db {anim},{ttl},{attr},1\n")
        inc.append(f"    .dw {xoff & 0xFFFF},{yoff & 0xFFFF},"
                   f"{vx & 0xFFFF},{vy & 0xFFFF},{ay & 0xFFFF},0\n")
    print(f"{name}: {len(rules)} matcher rules, {len(mot_ids)} motions")
    display = cfg.get("display", name.upper())
    name_ids = [CHARSET.index(c) for c in display]
    CHAR_NAMES.append(f"{name}Name: .db {len(name_ids)}," +
                      ",".join(str(i) for i in name_ids) + "\n")

    # PRACTICE command list: names/commands/categories for every input the
    # engine can execute.  Strings stay in this character's F_TBANK window;
    # the descriptor points at the header through CH_CMDLIST.
    cmd_rows = build_command_list(name, cfg, button_rows, rules, display_defs,
                                  cfg.get("_max_sids", ()))
    # The fixed 15 descriptors live in FightData and address their generated
    # data through F_TBANK, so their small command list can stay beside the
    # other tables.  Mass-import blocks are allocated separately: adding
    # ~1 KiB per fighter to the already-tight 64 KiB windows pushed the
    # largest metasprite blobs out of the map.
    if name in FIXED_CMD_LIST:
        emit_command_list(name, cmd_rows, inc)
    else:
        cmd_inc = []
        emit_command_list(name, cmd_rows, cmd_inc)
        open(os.path.join(OUT, f"{name}_cmdlist.inc"), "w").write(
            "; generated by build_fight.py -- PRACTICE command list\n" +
            "".join(cmd_inc))
        CMD_POOL_ROWS[name] = cmd_rows
    print(f"{name}: {len(cmd_rows)} command-list rows")

    # Victory quotes: four HUD pairs per language, word-wrapped into <= 2
    # rows of 30 glyphs.  The QuoteTab is language-major:
    #   Q_LANG*32 + (framecnt>>3 & 3)*4 -> pair offset (two .dw pointers).
    # Sources live in assets/data/quotes/*.json; the CNS [Quotes] block is
    # only a fallback for characters not yet in the database.
    quote_db = load_quote_db()
    lang_quotes = {}
    for fname, tag in QUOTE_LANGS:
        raw = quote_db[tag].get(name) or quote_db["en"].get(name) or []
        quotes = []
        for text in raw:
            lines = wrap_quote(normalize_quote(text))
            if lines:
                quotes.append(lines)
            else:
                print(f"{name}: quote skipped ({tag}): {text!r}")
        if not quotes:
            quotes = legacy_quote_lines(name, cfg)
        quotes = quotes[:4]
        while len(quotes) < 4:
            quotes.append(quotes[-1] if quotes else ["", ""])
        lang_quotes[tag] = quotes
    pair_tab = {}
    for fname, tag in QUOTE_LANGS:
        # identical padded slots share one stored pair; QuoteTab rows alias
        pair_idx = {}
        for qi, lines in enumerate(lang_quotes[tag]):
            pair_idx.setdefault(tuple(lines + [""] * (2 - len(lines))), qi)
        pair_tab[tag] = pair_idx
        for lines, ui in pair_idx.items():
            for li, s in enumerate(lines):
                ids = [CHARSET.index(c) for c in s]
                QUOTE_STRINGS[tag].append(
                    f"{name}Q{tag}{ui}{'ab'[li]}: .db {len(ids)}" +
                    (("," + ",".join(str(i) for i in ids)) if ids else "")
                    + "\n")
    QUOTE_TABLES.append(f"{name}QuoteTab:\n")
    for fname, tag in QUOTE_LANGS:
        pair_idx = pair_tab[tag]
        for lines in lang_quotes[tag]:
            ui = pair_idx[tuple(lines + [""] * (2 - len(lines)))]
            QUOTE_TABLES.append(f"    .dl {name}Q{tag}{ui}a\n"
                                f"    .dl {name}Q{tag}{ui}b\n")

    def shade_pal(data, mul, lift):
        """15-bit palette -> scaled copy: each channel * mul/256 + lift*rem."""
        out = bytearray()
        for i in range(0, len(data), 2):
            c = data[i] | (data[i + 1] << 8)
            r = (c & 31) * mul // 256 + (31 - (c & 31)) * lift // 256
            g = ((c >> 5) & 31) * mul // 256 + \
                (31 - ((c >> 5) & 31)) * lift // 256
            b = ((c >> 10) & 31) * mul // 256 + \
                (31 - ((c >> 10) & 31)) * lift // 256
            nc = min(r, 31) | (min(g, 31) << 5) | (min(b, 31) << 10)
            out += bytes((nc & 0xFF, nc >> 8))
        return out

    base_pal = snes_pal(global_pal, 16)
    alt_base_pal = snes_pal(alt_pal, 16)
    open(os.path.join(OUT, f"{name}.chr"), "wb").write(tiles)
    # chr is sliced into contiguous aligned 32 KiB half-banks; emit exactly
    # ceil(size/32K) sections so sprite tile fetch (CH_CHRBANK + tile>>10)
    # stays contiguous while tail banks stay free for other content
    nbanks = (len(tiles) + 32767) // 32768
    # chr is sliced into contiguous aligned 32 KiB half-banks; each char
    # owns a run of file banks (see the memory map in fight.asm).
    # Chars flagged "msu" leave the ROM entirely: their chr blob is
    # appended to kof98-snes.msu (32 KiB-aligned) and the descriptor's
    # CH_CHRBANK field carries a slice index instead of a CPU bank byte.
    if cfg.get("msu"):
        MSU_BLOBS[name] = bytes(tiles)
        open(os.path.join(OUT, f"{name}_chr.inc"), "w").write(
            f"; {name}: chr lives in kof98-snes.msu (MSU-1 data file)\n")
    else:
        cname, bank0, bank0x, orga = CNAME_BANKS[name]
        out_lines = []
        for i in range(nbanks):
            letter = chr(ord('A') + i)
            pvs_bank = bank0 + i
            pvs_orga = orga
            # Iori's final partial bank collides with TakumaData in bank 23.
            out_lines.append(
                f".IFDEF PVSNESLIB\n.BANK {pvs_bank} SLOT 0\n.ELSE\n"
                f".BANK {bank0x + i} SLOT 0\n.ENDIF\n.ORGA {pvs_orga}\n"
                f".SECTION \"{cname}Chr{letter}\" FORCE\n\n"
                + (f"{cname}Chr:\n" if i == 0 else "")
                + f"    .INCBIN \"gen_fight/{name}.chr\" SKIP {i * 32768}"
                + (" READ 32768" if i < nbanks - 1 else "") + "\n"
                + (f"{cname}Chr_End:\n" if i == nbanks - 1 else "")
                + ".ENDS\n\n")
        open(os.path.join(OUT, f"{name}_chr.inc"),
             "w").write("".join(out_lines))
    open(os.path.join(OUT, f"{name}_pal.bin"), "wb").write(base_pal)
    # OBJ palettes 3/5 (dim ghost, bright PalFX flash) per character
    open(os.path.join(OUT, f"{name}_pal_dim.bin"), "wb").write(
        shade_pal(base_pal, 140, 0))
    open(os.path.join(OUT, f"{name}_pal_hi.bin"), "wb").write(
        shade_pal(base_pal, 160, 160))
    # P2 mirror-match palettes use the next ACT colour of the same pack.
    open(os.path.join(OUT, f"{name}_pal_p2.bin"), "wb").write(alt_base_pal)
    open(os.path.join(OUT, f"{name}_pal_p2_dim.bin"), "wb").write(
        shade_pal(alt_base_pal, 140, 0))
    open(os.path.join(OUT, f"{name}_pal_p2_hi.bin"), "wb").write(
        shade_pal(alt_base_pal, 160, 160))
    open(os.path.join(OUT, f"{name}_spr.inc"), "w").write("".join(inc))
    # Mass-import chars also get their SprData blob split into _meta.inc so
    # the bulky metasprite cells can sit in a second bank (CH_MBANK) while
    # the index/state tables stay in F_TBANK.  SprOfs must remain here: the
    # engine fetches it via CharPtr(CH_SPROFS) at the table bank.
    if name in NEW_CHARS or name in ("omegarugal", "rugal") \
            or name in SPLIT_OLD:
        spr_part, meta_part, in_meta = [], [], False
        for line in inc:
            if line.startswith(f"{name}SprData:"):
                in_meta = True
            elif in_meta and re.match(r"^\S", line):
                in_meta = False
            (meta_part if in_meta else spr_part).append(line)
        open(os.path.join(OUT, f"{name}_spr.inc"), "w").write(
            "".join(spr_part))
        open(os.path.join(OUT, f"{name}_meta.inc"), "w").write(
            "; generated by build_fight.py -- metasprite blob\n" +
            "".join(meta_part))
    print(f"{name}: {len(spr_ids)} sprites, {len(tiles) // 32} tiles "
          f"({len(tiles)} bytes), palette {len(global_pal) - 1} colors, "
          f"max {max_cells} cells/{max_dma} DMA bytes")


# --- hit sparks -----------------------------------------------------------
# Two spare 64-tile OBJ regions live at the tail of each 96-tile ping-pong
# pair: tile indices 192-255 (VRAM $6C00) and 448-511 ($7C00).  Spark tiles
# Each live effect slot owns a full page of sixteen 16x16 cells. Static
# sparks/explods share one atlas; enlarged projectile frames stream into
# the same page as needed. Both pages use identical tile offsets.
SPARK_SLOTS = ([192 + 2 * k for k in range(8)] +
               [224 + 2 * k for k in range(8)])

# anim label -> (SFF path, AIR path, action, downscale, frame indices).
# Kyo-N.cns uses s6001 for regular HitDefs; this generic impact is shared by
# every fighter.  Guard and character-specific Explods retain their sources.
SPARK_ANIMS = {
    "SparkHit":   ("assets/characters/Kyo-KOF98/Kyo.sff",
                   "assets/characters/Kyo-KOF98/Kyo.air",
                   6001, 3, [2]),
    "SparkGuard": ("assets/data/fightfx.sff",
                   "assets/data/fightfx.air",
                   40, 3, [3]),
}

# Explod effects compiled from the char SFFs: the intro's flying wood pieces.
# anim label -> (sff path, scale, [(group,num,ticks)], attr byte)
# attr $3E = OBJ palette 7 + priority 3 (own palette, WoodPal); empty frames
# (group -1) animate the flicker of the breaking chunk.
WOOD_SCALE = 4
EXPLODS = {
    "WoodA": ("assets/characters/_excluded/kfm/kfm.sff", WOOD_SCALE,
              [(191, 3, 8), (191, 0, 8)],
              0x3E),
    "WoodB": ("assets/characters/_excluded/kfm/kfm.sff", WOOD_SCALE,
              [(192, 0, 5), (192, 1, 8), (-1, 0, 1)],
              0x3E),
    # Oniyaki flame pillar + crest (Kyo 1120/1121, Iori 1101/1102 -- the
    # sprite sheets are identical between the two chars).  The full clips
    # blow the 32-slot cell pool, so each effect uses one prominent frame at
    # 1/3 scale for the rise and 1/2 scale for the crest. The clips change
    # from pillar to crest at the original timing; the generic hit spark drops
    # one redundant middle frame to make room in the shared tile pool.
    "FlameRise": ("assets/characters/Kyo-KOF98/Kyo.sff", 3,
                  [(1105, 3, 14)],
                  0x3E),
    "FlameTop": ("assets/characters/Kyo-KOF98/Kyo.sff", 2,
                 [(1110, 3, 12)],
                 0x3E),
}
# mugen explod anim id -> compiled clip label.  Kyo's flames ride AIR
# actions 1120/1121; Iori's (identical art) ride 1101/1102.
EXPLOD_ANIM = {191: "WoodA", 192: "WoodB",
               1120: "FlameRise", 1121: "FlameTop",
               1101: "FlameRise", 1102: "FlameTop"}
# Per-character overrides for source anim ids that collide across packages.
# Geese's Raging Storm paints its pillar with Explod 3001/3002.  Reuse the
# already-compiled flame pillar/crest clips so the super has a visible
# vertical effect without adding another atlas to the shared 32-cell pool.
EXPLOD_ANIM_BY_CHAR = {
    "geese": {3001: "FlameRise", 3002: "FlameTop"},
}
EXPLODS_IDX = {label: i for i, label in enumerate(
    list(SPARK_ANIMS) + list(EXPLODS))}

# Verified source AIR clips for characters whose converted CNS lost ProjAnim.
# Others are resolved from their Projectile controllers first.
def spark_sprite(s, scale):
    """Downscale by integer factor keeping the axis like scale_sprite(),
    but tolerating non-divisible axes."""
    if scale == 1:
        return s
    ns = Sprite()
    ns.group, ns.number = s.group, s.number
    ns.w = (s.w + scale - 1) // scale
    ns.h = (s.h + scale - 1) // scale
    ns.ax = -(-s.ax // scale)
    ns.ay = -(-s.ay // scale)
    ns.palidx = s.palidx
    ns.link = s.link
    pix = bytearray(ns.w * ns.h)
    for oy in range(ns.h):
        for ox in range(ns.w):
            counts = {}
            for sy in range(oy * scale, min((oy + 1) * scale, s.h)):
                row = sy * s.w
                for sx in range(ox * scale,
                                min((ox + 1) * scale, s.w)):
                    v = s.pix[row + sx]
                    counts[v] = counts.get(v, 0) + 1
            opaque = [(c, i) for i, c in counts.items() if i]
            pix[oy * ns.w + ox] = max(opaque)[1] if opaque else 0
    ns.pix = bytes(pix)
    return ns


def projectile_source_color(sff, spr, idx, char_name=None):
    """Read MUGEN's auxiliary effect palette for extended sprite indices."""
    palettes = sff.palettes
    source_idx = PROJECTILE_SOURCE_PALETTES.get(char_name, spr.palidx)
    srcpal = palettes[source_idx] if source_idx is not None \
        and source_idx < len(palettes) else []
    color = srcpal[idx] if idx < len(srcpal) else (0, 0, 0)
    # Several KOF SFFs store magic art in indices 16..255, while their
    # fighter palette only defines entries 0..15. Palette 2 carries the
    # matching effect ramp; reading the body palette here made every
    # projectile black or a character-color approximation.
    if idx >= 16 and color in ((0, 0, 0), (248, 0, 248)) \
            and len(palettes) > 2 and idx < len(palettes[2]):
        effect_color = palettes[2][idx]
        if effect_color != (0, 0, 0) and effect_color != (248, 0, 248):
            color = effect_color
    return color


def upscale_projectile(spr, factor=2):
    """Nearest-neighbour enlargement for tiny source energy sprites."""
    enlarged = Sprite()
    enlarged.group, enlarged.number = spr.group, spr.number
    enlarged.w, enlarged.h = spr.w * factor, spr.h * factor
    enlarged.ax, enlarged.ay = spr.ax * factor, spr.ay * factor
    enlarged.palidx, enlarged.link = spr.palidx, spr.link
    enlarged.pix = bytes(spr.pix[(y // factor) * spr.w + (x // factor)]
                         for y in range(enlarged.h)
                         for x in range(enlarged.w))
    return enlarged


def projectile_action_candidates(cfg, statedefs, move_ids):
    """Return projectile animations, preferring source-verified AIR actions."""
    candidates = []
    for _sid, state in sorted(move_ids.items()):
        todo = [state]
        seen = {state}
        while todo:
            source_state = todo.pop(0)
            for ctrl in statedefs.get(source_state, []):
                typ = ctrl.get("type", "").lower()
                if typ == "projectile":
                    raw = ctrl.get("projanim") or ctrl.get("anim")
                    match = re.search(r"-?\d+", str(raw or ""))
                    if match:
                        candidates.append(int(match.group()))
                elif typ == "helper":
                    match = re.search(r"\d+", str(ctrl.get("stateno", "")))
                    if match and int(match.group()) not in seen:
                        child = int(match.group())
                        seen.add(child)
                        todo.append(child)
    inferred = candidates
    candidates = []
    name = next((key for key, value in CHARS.items() if value is cfg), None)
    # Prefer the character's verified source action over animation IDs
    # inferred from converted CNS.  Some MUGEN projectile controllers point
    # at a firing/owner animation (and generic command-state traversal can
    # encounter that animation first), which renders fighter fragments as
    # the projectile.  The explicit rows below were checked against each
    # character's AIR/SFF artwork.
    if name in PROJECTILE_ACTIONS:
        candidates.append(PROJECTILE_ACTIONS[name])
    candidates.extend(cfg.get("projectile_anims", ()))
    candidates.extend(inferred)
    return list(dict.fromkeys(candidates))


def crop_projectile_sprite(spr):
    """Discard transparent canvas around an effect before applying size limits.

    Terry and Joe store their real projectiles on 304x224 transparent sheets;
    the visible art, rather than that canvas, determines the OBJ budget.
    """
    if spr is None or not spr.pix:
        return spr
    xs, ys = [], []
    for i, value in enumerate(spr.pix):
        if value:
            xs.append(i % spr.w)
            ys.append(i // spr.w)
    if not xs:
        return spr
    left, top = max(0, min(xs) - 1), max(0, min(ys) - 1)
    right = min(spr.w, max(xs) + 2)
    bottom = min(spr.h, max(ys) + 2)
    if right - left > 192 or bottom - top > 128:
        return spr
    clipped = Sprite()
    clipped.group, clipped.number = spr.group, spr.number
    clipped.w, clipped.h = right - left, bottom - top
    clipped.ax, clipped.ay = spr.ax - left, spr.ay - top
    clipped.palidx, clipped.link = spr.palidx, spr.link
    clipped.pix = bytes(spr.pix[y * spr.w + x]
                        for y in range(top, bottom)
                        for x in range(left, right))
    return clipped


def projectile_remap_index(sff, spr, idx, name):
    """Map a source SFF palette index onto the shared OBJ effect palette."""
    if idx == 0:
        return 0
    c = projectile_source_color(sff, spr, idx, name)
    # Projectile energy art has its own shared OBJ palette. Mapping these
    # colors through the fighter's body palette turns flames and orbs into
    # mottled skin/costume colors (the "dirt" look seen in game).
    got = PROJECTILE_PALETTE_IDX.get(c)
    if got is not None:
        return got
    return min(range(1, len(PROJECTILE_PALETTE)),
               key=lambda i: sum((PROJECTILE_PALETTE[i][ch] - c[ch]) ** 2
                                 for ch in range(3)))


def projectile_collect_usable(sff, air, actions):
    """Return usable (action, frame index, frame, cropped sprite) rows."""
    out = []
    for anum in actions:
        if anum not in air:
            continue
        for fi, frame in enumerate(air[anum][0]):
            g, n = frame[0], frame[1]
            try:
                source = sff.get(g, n)
            except (KeyError, IndexError):
                continue
            if source is None:
                continue
            spr = crop_projectile_sprite(source)
            if (spr is None or spr.w <= 0 or spr.h <= 0
                    or spr.w > 192 or spr.h > 128 or not any(spr.pix)):
                continue
            out.append((anum, fi, frame, spr))
    return out


def projectile_effect_sequence(name, cfg, sff, air, actions):
    """Compile a multi-action source effect (one Explod anim per tick).

    The port's clip format already stores an arbitrary frame count; unlike
    the single-action path we keep every source frame and give each frame
    its own 16-tile page.  Yuri's Ko'ou Ken needs this because one helper
    state explods actions 2010..2015 in sequence instead of playing a
    single AIR action.
    """
    usable = projectile_collect_usable(sff, air, actions)
    if not usable:
        return None
    zoom = PROJECTILE_ZOOM_BY_CHAR.get(name, PROJECTILE_ZOOM)
    originals = []
    for _anum, _fi, frame, spr in usable:
        _g, _n, xoff, yoff, ticks, _flip, _ab, _hb = frame
        original = upscale_projectile(spr, zoom) if zoom != 1 else spr
        originals.append((original, xoff, yoff, max(1, min(255, ticks))))

    fitted = None
    for scale in range(1, 17):
        out = []
        ok = True
        for original, xoff, yoff, ticks in originals:
            spr = spark_sprite(original, scale)
            cell_pixels = {}
            source_cells = []
            cols = (spr.w + CELL - 1) // CELL
            rows = (spr.h + CELL - 1) // CELL
            for cy in range(rows):
                for cx in range(cols):
                    block = bytearray(CELL * CELL)
                    any_px = False
                    for yy in range(CELL):
                        sy = cy * CELL + yy
                        if sy >= spr.h:
                            break
                        for xx in range(CELL):
                            sx = cx * CELL + xx
                            if sx >= spr.w:
                                continue
                            v = projectile_remap_index(
                                sff, spr, spr.pix[sy * spr.w + sx], name)
                            block[yy * CELL + xx] = v
                            any_px |= bool(v)
                    if not any_px:
                        continue
                    quad = tiles4bpp(block, CELL, CELL)[0]
                    slot = cell_pixels.setdefault(bytes(quad), len(cell_pixels))
                    cell_pixels[slot] = bytes(block)
                    source_cells.append(
                        (cx * CELL - spr.w // 2 + xoff // scale,
                         cy * CELL - spr.h // 2 + yoff // scale, slot))
            if not source_cells:
                ok = False
                break
            bottom = max((dy + i // CELL + 1
                          for dx, dy, slot in source_cells
                          for i, value in enumerate(cell_pixels[slot])
                          if value), default=0)
            yshift = bottom * zoom if name in GROUND_PROJECTILES else 0
            atlas = {}
            cells = []
            for dx, dy, slot in source_cells:
                pix = cell_pixels[slot]
                for by in range(zoom):
                    for bx in range(zoom):
                        block = bytes(
                            pix[(by * CELL + y) // zoom * CELL
                                + (bx * CELL + x) // zoom]
                            for y in range(CELL) for x in range(CELL))
                        if not any(block):
                            continue
                        quad = tiles4bpp(block, CELL, CELL)[0]
                        idx = atlas.setdefault(quad, len(atlas))
                        cells.append((dx * zoom + bx * CELL,
                                      dy * zoom + by * CELL - yshift, idx))
            if not cells or len(atlas) > len(SPARK_SLOTS):
                ok = False
                break
            out.append((ticks, cells, atlas))
        if ok:
            fitted = out
            break
    if fitted is None:
        raise ValueError(f"{name}: projectile sequence does not fit the "
                         f"{len(SPARK_SLOTS)}-tile OBJ page")

    zoom_frames = []
    chr_data = bytearray()
    for ticks, cells, atlas in fitted:
        page = bytearray(2048)
        for quad, idx in atlas.items():
            offset = (SPARK_SLOTS[idx] - 192) * 32
            page[offset:offset + 64] = quad[:64]
            page[offset + 512:offset + 576] = quad[64:]
        chr_data += page
        zoom_frames.append((ticks, cells))
    return actions, zoom_frames, bytes(chr_data)


def projectile_effect(name, cfg, sff, air, statedefs, headers, move_ids,
                      palidx, global_pal, mapped_color):
    """Compile source AIR frames into the eight-cell OBJ cache per side."""
    sequence = PROJECTILE_ACTION_SEQUENCES.get(name)
    if sequence is not None:
        return projectile_effect_sequence(name, cfg, sff, air, sequence)

    candidates = projectile_action_candidates(cfg, statedefs, move_ids)
    # The verified per-character action may hold the whole effect in one
    # cel (Ryu/Ken's hadouken: AIR 1021 has one real fireball frame plus a
    # sparse sparkle frame whose visible box exceeds the OBJ limit).
    # Accept that single frame for an explicit action; inferred candidates
    # still need two frames so a firing pose is never mistaken for the shot.
    verified = set(cfg.get("projectile_anims", ()))
    if name in PROJECTILE_ACTIONS:
        verified.add(PROJECTILE_ACTIONS[name])

    action = None
    frames = None
    all_frames = bool(cfg.get("projectile_all_frames"))
    for anum in candidates:
        if anum not in air:
            continue
        frs = air[anum][0]
        usable = []
        for fi, frame in enumerate(frs):
            g, n = frame[0], frame[1]
            try:
                source = sff.get(g, n)
            except (KeyError, IndexError):
                continue
            if source is None:
                continue
            spr = crop_projectile_sprite(source)
            if spr is None or spr.w <= 0 or spr.h <= 0 or spr.w > 192 or spr.h > 128:
                continue
            if not any(spr.pix):
                continue
            usable.append(fi)
        if len(usable) >= 2 or (anum in verified and usable):
            action = anum
            frames = usable if all_frames else [usable[0], usable[-1]]
            break
    if action is None:
        return None

    zoom = PROJECTILE_ZOOM_BY_CHAR.get(name, PROJECTILE_ZOOM)

    def remap_index(spr, idx):
        return projectile_remap_index(sff, spr, idx, name)

    source_frames = air[action][0]
    originals = []
    for fi in frames:
        g, n, xoff, yoff, ticks, _flip, _ab, _hb = source_frames[fi]
        original = upscale_projectile(crop_projectile_sprite(sff.get(g, n)),
                                      zoom)
        originals.append((original, xoff, yoff, ticks))

    # Fit the complete animation at one scale. Fitting each frame separately
    # let the first consume the cache and forced later frames to shrink or
    # repeat tile zero. Rebuild all frames until their distinct tiles fit.
    scale = 1
    while True:
        all_cells = {}
        cell_pixels = {}
        out_frames = []
        for original, xoff, yoff, ticks in originals:
            spr = spark_sprite(original, scale)
            cells = []
            cols = (spr.w + CELL - 1) // CELL
            rows = (spr.h + CELL - 1) // CELL
            for cy in range(rows):
                for cx in range(cols):
                    block = bytearray(CELL * CELL)
                    any_px = False
                    for yy in range(CELL):
                        sy = cy * CELL + yy
                        if sy >= spr.h:
                            break
                        for xx in range(CELL):
                            sx = cx * CELL + xx
                            if sx >= spr.w:
                                continue
                            v = remap_index(spr, spr.pix[sy * spr.w + sx])
                            block[yy * CELL + xx] = v
                            any_px |= bool(v)
                    if any_px:
                        quad = tiles4bpp(block, CELL, CELL)[0]
                        key = bytes(quad)
                        slot = all_cells.setdefault(key, len(all_cells))
                        cell_pixels[slot] = bytes(block)
                        # The moving spark is spawned at torso height, while
                        # MUGEN's projectile animation is anchored near the
                        # floor. Centering the extracted effect on the launch
                        # point avoids sending Kyo's fireball above the HUD.
                        cells.append((cx * CELL - spr.w // 2 + xoff // scale,
                                      cy * CELL - spr.h // 2 + yoff // scale,
                                      slot))
            out_frames.append((max(1, min(255, ticks)), cells))
        if len(all_cells) <= 8 and all(len(cells) <= 8
                                      for _ticks, cells in out_frames):
            break
        scale += 1

    # Enlarge the fitted pixels exactly 2x, without shrinking them back to
    # the old clip budget. Each live effect slot streams a complete 2 KiB
    # frame page, shared with ordinary sparks when that slot is reused.
    zoom_frames = []
    chr_data = bytearray()
    for ticks, source_cells in out_frames:
        bottom = max(dy + i // CELL + 1
                     for dx, dy, slot in source_cells
                     for i, value in enumerate(cell_pixels[slot]) if value)
        yshift = bottom * zoom if name in GROUND_PROJECTILES else 0
        atlas = {}
        cells = []
        for dx, dy, slot in source_cells:
            pix = cell_pixels[slot]
            for by in range(zoom):
                for bx in range(zoom):
                    block = bytes(pix[(by * CELL + y) // zoom * CELL
                                      + (bx * CELL + x) // zoom]
                                  for y in range(CELL) for x in range(CELL))
                    if not any(block):
                        continue
                    quad = tiles4bpp(block, CELL, CELL)[0]
                    idx = atlas.setdefault(quad, len(atlas))
                    cells.append((dx * zoom + bx * CELL,
                                  dy * zoom + by * CELL - yshift, idx))
        if len(atlas) > 16:
            raise ValueError(f"{name}: {zoom}x frame exceeds its 16-cell "
                             f"VRAM page")
        page = bytearray(2048)
        for quad, idx in atlas.items():
            offset = (SPARK_SLOTS[idx] - 192) * 32
            page[offset:offset + 64] = quad[:64]
            page[offset + 512:offset + 576] = quad[64:]
        chr_data += page
        zoom_frames.append((ticks, cells))
    return action, zoom_frames, bytes(chr_data)


def projectile_effect_alt(name, sff, air, spec):
    """Compile a second, explicitly selected projectile effect clip.

    ``spec`` comes from PROJECTILE_ALT_EFFECTS.  The source helper sheets can
    be larger than the 192x128 source-cell cap, so ``pre_scale`` shrinks them
    before cropping.  The fitted frames still obey the same 16-cell OBJ page
    budget; ``zoom`` is kept at 1 for large pillars so the whole animation
    fits without exceeding a page.
    """
    action = spec["action"]
    if action not in air:
        return None
    pre_scale = max(1, int(spec.get("pre_scale", 1)))
    zoom = max(1, int(spec.get("zoom", 1)))
    max_cells = int(spec.get("max_cells", len(SPARK_SLOTS)))
    source_frames = air[action][0]
    originals = []
    for fi, ticks in spec["frames"]:
        if fi < 0 or fi >= len(source_frames):
            continue
        g, n, xoff, yoff, _ticks, _flip, _atk, _hurt = source_frames[fi]
        try:
            source = sff.get(g, n)
        except (KeyError, IndexError):
            continue
        if source is None:
            continue
        if pre_scale != 1:
            source = spark_sprite(source, pre_scale)
        spr = crop_projectile_sprite(source)
        if (spr is None or spr.w <= 0 or spr.h <= 0
                or spr.w > 192 or spr.h > 128 or not any(spr.pix)):
            continue
        originals.append((spr, xoff, yoff,
                          max(1, min(255, int(ticks)))))

    if not originals:
        return None

    scale = 1
    while True:
        all_cells = {}
        cell_pixels = {}
        out_frames = []
        for original, xoff, yoff, ticks in originals:
            spr = spark_sprite(original, scale)
            cells = []
            cols = (spr.w + CELL - 1) // CELL
            rows = (spr.h + CELL - 1) // CELL
            for cy in range(rows):
                for cx in range(cols):
                    block = bytearray(CELL * CELL)
                    any_px = False
                    for yy in range(CELL):
                        sy = cy * CELL + yy
                        if sy >= spr.h:
                            break
                        for xx in range(CELL):
                            sx = cx * CELL + xx
                            if sx >= spr.w:
                                continue
                            v = projectile_remap_index(
                                sff, spr, spr.pix[sy * spr.w + sx], name)
                            block[yy * CELL + xx] = v
                            any_px |= bool(v)
                    if not any_px:
                        continue
                    quad = tiles4bpp(block, CELL, CELL)[0]
                    key = bytes(quad)
                    slot = all_cells.setdefault(key, len(all_cells))
                    cell_pixels[slot] = bytes(block)
                    # Source offsets are still in the full-resolution space.
                    cells.append((cx * CELL - spr.w // 2
                                  + xoff // (pre_scale * scale),
                                  cy * CELL - spr.h // 2
                                  + yoff // (pre_scale * scale), slot))
            out_frames.append((ticks, cells))
        if (len(all_cells) <= max_cells
                and all(len(cells) <= max_cells
                        for _ticks, cells in out_frames)):
            break
        scale += 1
        if scale > 16:
            raise ValueError(f"{name}: alternate projectile effect does not "
                             f"fit the {max_cells}-cell OBJ page")

    zoom_frames = []
    chr_data = bytearray()
    for ticks, source_cells in out_frames:
        bottom = max((dy + i // CELL + 1
                      for dx, dy, slot in source_cells
                      for i, value in enumerate(cell_pixels[slot]) if value),
                     default=0)
        yshift = bottom * zoom if name in GROUND_PROJECTILES else 0
        atlas = {}
        cells = []
        for dx, dy, slot in source_cells:
            pix = cell_pixels[slot]
            for by in range(zoom):
                for bx in range(zoom):
                    block = bytes(
                        pix[(by * CELL + y) // zoom * CELL
                            + (bx * CELL + x) // zoom]
                        for y in range(CELL) for x in range(CELL))
                    if not any(block):
                        continue
                    quad = tiles4bpp(block, CELL, CELL)[0]
                    idx = atlas.setdefault(quad, len(atlas))
                    cells.append((dx * zoom + bx * CELL,
                                  dy * zoom + by * CELL - yshift, idx))
        if len(atlas) > len(SPARK_SLOTS):
            raise ValueError(f"{name}: alternate projectile frame exceeds "
                             f"its {len(SPARK_SLOTS)}-cell VRAM page")
        page = bytearray(2048)
        for quad, idx in atlas.items():
            offset = (SPARK_SLOTS[idx] - 192) * 32
            page[offset:offset + 64] = quad[:64]
            page[offset + 512:offset + 576] = quad[64:]
        chr_data += page
        zoom_frames.append((ticks, cells))
    return action, zoom_frames, bytes(chr_data)


def build_spark():
    """Emit spark.chr (tiles placed at fixed OBJ indices), spark.inc
    (animation cell tables) and spark_pal.bin from the generic impact and
    guard sprites.  Explods ride the same pipeline with their own palette."""
    sff_cache = {}
    air_cache = {}

    def spark_source(sff_rel, air_rel):
        if sff_rel not in sff_cache:
            sff_cache[sff_rel] = Sff(os.path.join(ROOT, sff_rel))
        if air_rel not in air_cache:
            air_cache[air_rel] = parse_air(os.path.join(ROOT, air_rel))
        return sff_cache[sff_rel], air_cache[air_rel]

    # Palette 2 is shared by impact sparks and all character projectiles.
    # Build it from the actual effect pixels across the roster so each source
    # keeps its energy hue instead of inheriting the fighter's body palette.
    color_hist = {}
    for _label, (sff_rel, air_rel, anum, scale, idxs) in SPARK_ANIMS.items():
        sff, air = spark_source(sff_rel, air_rel)
        frames, _loop = air[anum]
        for fi in idxs:
            g, n, x, y, t, flip, _a, _h = frames[fi]
            s = spark_sprite(sff.get(g, n), scale)
            for idx in sorted(set(s.pix)):
                if idx == 0:
                    continue
                c = projectile_source_color(sff, s, idx, _label)
                color_hist[c] = color_hist.get(c, 0) + s.pix.count(idx)

    # Sample the source frames from each verified projectile effect,
    # matching the clip compiler's frame selection. Weight projectile
    # pixels above the generic hit spark so palette slots preserve magic hues.
    for name, cfg in CHARS.items():
        if not cfg.get("sff") or not cfg.get("air") or not cfg.get("cns"):
            continue
        sff, air = spark_source(cfg["sff"], cfg["air"])
        sequence = PROJECTILE_ACTION_SEQUENCES.get(name)
        if sequence is not None:
            selected = projectile_collect_usable(sff, air, sequence)
        else:
            cns = parse_cns(os.path.join(ROOT, cfg["cns"]),
                            cfg.get("coord_scale", 1),
                            cfg.get("damage_scale", 1))
            statedefs = cns[4]
            actions = projectile_action_candidates(cfg, statedefs,
                                                   cfg.get("moves", {}))
            selected = None
            for action in actions:
                usable = projectile_collect_usable(sff, air, [action])
                if len(usable) >= 2:
                    selected = [usable[0], usable[-1]]
                    break
        if not selected:
            continue
        for _action, _fi, _frame, spr in selected:
            for idx in set(spr.pix):
                if not idx:
                    continue
                c = projectile_source_color(sff, spr, idx, name)
                color_hist[c] = color_hist.get(c, 0) + spr.pix.count(idx) * 4

    # Weighted median cut to the 15 opaque SNES OBJ colors. Deterministic
    # ordering keeps generated ROMs reproducible.
    buckets = [sorted(color_hist)] if color_hist else []
    while len(buckets) < 15:
        def spread(bucket):
            return max(max(c[i] for c in bucket) - min(c[i] for c in bucket)
                       for i in range(3)) if bucket else 0
        bucket = max(buckets, key=spread, default=[])
        if len(bucket) < 2 or spread(bucket) == 0:
            break
        buckets.remove(bucket)
        ch = max(range(3), key=lambda i: max(c[i] for c in bucket)
                 - min(c[i] for c in bucket))
        bucket.sort(key=lambda c: c[ch])
        total = sum(color_hist[c] for c in bucket)
        acc, split = 0, 0
        while split < len(bucket) - 1 and acc < total / 2:
            acc += color_hist[bucket[split]]
            split += 1
        buckets.extend((bucket[:split], bucket[split:]))
    colors = []
    for bucket in buckets:
        total = sum(color_hist[c] for c in bucket)
        colors.append(tuple(sum(c[i] * color_hist[c] for c in bucket) // total
                            for i in range(3)))
    pal = [(0, 0, 0)] + colors
    palidx = {c: i for i, c in enumerate(pal)}
    def shared_color_index(color):
        exact = palidx.get(color)
        if exact is not None:
            return exact
        return min(range(1, len(pal)),
                   key=lambda i: sum((pal[i][ch] - color[ch]) ** 2
                                     for ch in range(3)))
    global PROJECTILE_PALETTE, PROJECTILE_PALETTE_IDX
    PROJECTILE_PALETTE = pal
    PROJECTILE_PALETTE_IDX = palidx

    # wood palette comes from the kfm sheet: collect the colours the (already
    # downscaled) wood sprites actually use
    # explod sprites share one OBJ palette (attr $3E): keep the 15 most
    # used colours and remap the rest to their nearest kept neighbour.
    counts = {}
    for _label, (sff_rel, scale, frs, _a) in EXPLODS.items():
        csff = Sff(os.path.join(ROOT, sff_rel))
        for g, n, _t in frs:
            if g < 0:
                continue
            s = spark_sprite(csff.get(g, n), scale)
            srcpal = csff.palettes[s.palidx]
            for idx in set(s.pix):
                if idx == 0:
                    continue
                c = srcpal[idx] if idx < len(srcpal) else (0, 0, 0)
                counts[c] = counts.get(c, 0) + sum(
                    1 for v in s.pix if v == idx)
    wood_pal = [(0, 0, 0)]
    wood_pal += sorted(counts, key=lambda c: -counts[c])[:15]
    wood_remap = {}

    def nearest(c):
        if c in wood_remap:
            return wood_remap[c]
        best = min(range(1, len(wood_pal)),
                   key=lambda i: sum((a - b) ** 2
                                     for a, b in zip(c, wood_pal[i])))
        wood_remap[c] = best
        return best

    wpidx = {c: (wood_pal.index(c) if c in wood_pal else nearest(c))
             for c in counts}

    # collect all cells as 4bpp tile quads, dedup into the slot pool
    pool = {}            # tile quad bytes -> slot index
    anims = {}

    def sprite_cells(s, remap):
        cells = []
        cols = (s.w + CELL - 1) // CELL
        rows = (s.h + CELL - 1) // CELL
        for cy in range(rows):
            for cx in range(cols):
                block = bytearray(CELL * CELL)
                any_px = False
                for yy in range(CELL):
                    sy = cy * CELL + yy
                    if sy >= s.h:
                        break
                    for xx in range(CELL):
                        sx = cx * CELL + xx
                        if sx < s.w:
                            v = remap[s.pix[sy * s.w + sx]]
                            block[yy * CELL + xx] = v
                            if v:
                                any_px = True
                if not any_px:
                    continue
                quad = tiles4bpp(block, CELL, CELL)[0]
                if quad not in pool:
                    if len(pool) >= len(SPARK_SLOTS):
                        raise SystemExit(
                            f"spark: cell pool exceeds {len(SPARK_SLOTS)} slots")
                    pool[quad] = len(pool)
                cells.append((cx * CELL - s.ax, cy * CELL - s.ay,
                              SPARK_SLOTS[pool[quad]]))
        return cells

    for label, (sff_rel, air_rel, anum, scale, idxs) in SPARK_ANIMS.items():
        sff, air = spark_source(sff_rel, air_rel)
        frames, _loop = air[anum]
        out_frames = []
        for fi in idxs:
            g, n, x, y, t, flip, _a, _h = frames[fi]
            s = spark_sprite(sff.get(g, n), scale)
            remap = [0] * 256
            srcpal = sff.palettes[s.palidx] if s.palidx is not None else []
            for i, c in enumerate(srcpal):
                remap[i] = 0 if i == 0 else shared_color_index(c)
            out_frames.append((t, sprite_cells(s, remap)))
        anims[label] = out_frames

    wood_attrs = {}
    for label, (sff_rel, scale, frs, attr) in EXPLODS.items():
        csff = Sff(os.path.join(ROOT, sff_rel))
        out_frames = []
        for g, n, t in frs:
            if g < 0:
                out_frames.append((t, []))
                continue
            s = spark_sprite(csff.get(g, n), scale)
            remap = [0] * 256
            srcpal = csff.palettes[s.palidx]
            for i, c in enumerate(srcpal):
                remap[i] = wpidx.get(c, 0)
            out_frames.append((t, sprite_cells(s, remap)))
        anims[label] = out_frames
        wood_attrs[label] = attr

    # tile buffer covering both zones: pool slot -> tile quad bytes
    chrbuf = bytearray(128 * 32)
    for quad, slot in pool.items():
        ti = SPARK_SLOTS[slot]
        base = ti - 192
        chrbuf[base * 32:(base + 2) * 32] = quad[:64]
        chrbuf[(base + 16) * 32:(base + 18) * 32] = quad[64:]
    chrbuf[2048:] = chrbuf[:2048]

    inc = ["; generated by build_fight.py -- shared hit sparks + explods\n",
           "SparkAnimTab:\n"]
    for label in list(SPARK_ANIMS) + list(EXPLODS):
        inc.append(f"    .dw {label}\n")
    for label, frames in anims.items():
        inc.append(f"{label}:\n    .db {len(frames)}\n")
        for i in range(len(frames)):
            inc.append(f"    .dw {label}f{i}\n")
        for i, (t, cells) in enumerate(frames):
            inc.append(f"{label}f{i}:\n    .db {t},{len(cells)}\n")
            for dx, dy, ti in cells:
                inc.append(f"    .db {dx & 0xFF},{dy & 0xFF}\n"
                           f"    .dw ${ti:04X}\n")

    open(os.path.join(OUT, "spark.chr"), "wb").write(chrbuf)
    open(os.path.join(OUT, "spark_pal.bin"), "wb").write(snes_pal(pal, 16))
    open(os.path.join(OUT, "wood_pal.bin"), "wb").write(
        snes_pal(wood_pal, 16))
    open(os.path.join(OUT, "spark.inc"), "w").write("".join(inc))
    print(f"spark: {len(pool)}/{len(SPARK_SLOTS)} cells, "
          f"{sum(len(f) for f in anims.values())} "
          f"frames, shared magic palette {len(pal) - 1} colors, "
          f"wood palette {len(wood_pal) - 1} colors")


def tiles2bpp(pix, w, h):
    tw, th = (w + 7) // 8, (h + 7) // 8
    out = bytearray()
    for ty in range(th):
        for tx in range(tw):
            for row in range(8):
                y = ty * 8 + row
                lo = hi = 0
                for x in range(8):
                    px = pix[y * w + tx * 8 + x] if y < h and tx * 8 + x < w else 0
                    lo |= (px & 1) << (7 - x)
                    hi |= (px >> 1 & 1) << (7 - x)
                out += bytes((lo, hi))
    return bytes(out)


def _sff_imgs(path, keys=None):
    """{(group, number): PIL RGBA} — indexed (pix+pal) and PNG (fmt>=10)."""
    import io
    from PIL import Image
    d = open(path, 'rb').read()
    (so, ns, _po, _np, lo, _d, to) = struct.unpack_from('<7I', d, 0x24)
    sff = Sff(path)
    out = {}
    for i, spr in enumerate(sff.sprites):
        key = (spr.group, spr.number)
        if key in out or (keys is not None and key not in keys):
            continue
        if spr.pix:
            pal = (sff.palettes[spr.palidx]
                   if spr.palidx < len(sff.palettes) and
                   sff.palettes[spr.palidx] else None)
            im = Image.frombytes('P', (spr.w, spr.h), spr.pix)
            if pal:
                im.putpalette([c for rgb in pal[:256] for c in rgb])
            out[key] = im.convert('RGBA')
            continue
        o = so + i * 28
        (_g, _n, w, h, _ax, _ay, _l, fmt, _dep, ofs, size, _p,
         flags) = struct.unpack_from('<hhHHhhHBBIIHH', d, o)
        if size and fmt >= 10:
            base = to if flags & 1 else lo
            try:
                out[key] = Image.open(io.BytesIO(
                    d[base + ofs + 4:base + ofs + size])).convert('RGBA')
            except Exception:
                pass
    return out


def _q(px):
    """RGBA -> 2bpp index: transparent/dark/mid/bright."""
    r, g, b, a = px
    if a < 96:
        return 0
    lum = (r * 77 + g * 150 + b * 29) >> 8
    return 1 if lum < 70 else (2 if lum < 175 else 3)


def _bar_strip(imgs, layers, w=96, h=8):
    """Composite fight.sff bar layers scaled to the 12-tile HUD strip."""
    from PIL import Image
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for key in layers:
        im = imgs[key].resize((w, h), Image.LANCZOS)
        base = Image.alpha_composite(base, im)
    return base


def _bar_tiles(imgs, bg_key, mid_key, fill_key, top_key, w=96):
    """27 tile cells for one bar: full/empty caps and pixel clip variants."""
    from PIL import Image
    h = 8
    top = imgs[top_key].resize((w, h), Image.LANCZOS)
    lay = [imgs[k].resize((w, h), Image.LANCZOS) for k in
           (bg_key, mid_key) if k]
    # Empty gauge cells must be opaque: a transparent background lets the
    # stage show through as "missing tiles" once HP/power drains.
    empty = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    for im in lay:
        empty = Image.alpha_composite(empty, im)
    full = Image.alpha_composite(
        empty, imgs[fill_key].resize((w, h), Image.LANCZOS))
    empty = Image.alpha_composite(empty, top)
    full = Image.alpha_composite(full, top)
    ep, fp = empty.load(), full.load()

    def cell(x0, clip=None):
        out = bytearray(64)
        for y in range(8):
            for x in range(8):
                px = fp[x0 + x, y] if clip is None or x < clip else \
                    ep[x0 + x, y]
                idx = _q(px)
                out[y * 8 + x] = idx
        return bytes(out)

    end = w - 8
    cells = [cell(0), cell(8), cell(end), cell(0, 0), cell(8, 0), cell(end, 0)]
    cells += [cell(8, c) for c in range(1, 8)]
    cells += [cell(0, c) for c in range(1, 8)]
    cells += [cell(end, c) for c in range(1, 8)]
    return cells


def _fnt_v1(path):
    """MUGEN FNT v1 -> {ch: PIL RGBA}: PCX strip + [Map] x,width entries."""
    import io
    from PIL import Image
    d = open(path, 'rb').read()
    pcxstart, pcxsize, txtstart, txtsize = \
        struct.unpack_from("<4I", d, 16)
    pimg = Image.open(io.BytesIO(d[pcxstart:pcxstart + pcxsize]))
    bgcol = tuple(pimg.getpalette()[pimg.getpixel((0, 0)) * 3:
                                  pimg.getpixel((0, 0)) * 3 + 3])
    strip = pimg.convert('RGBA')
    sect = d[txtstart:txtstart + txtsize].decode('ascii', errors='replace')
    glyphs = {}
    for line in sect.splitlines():
        parts = line.split()
        if len(parts) == 3 and len(parts[0]) == 1 and \
                parts[1].isdigit() and parts[2].isdigit():
            ch, x, w = parts[0], int(parts[1]), int(parts[2])
            glyphs[ch] = strip.crop((x, 0, x + w, strip.height))
    # font strips key transparency on the corner background colour
    for im in glyphs.values():
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                if px[x, y][:3] == bgcol:
                    px[x, y] = (0, 0, 0, 0)
    return glyphs


def _mugen_def(path):
    """Read the active key/value entries and embedded AIR action frames."""
    sections = {}
    actions = {}
    section = None
    for raw in open(path, encoding='utf-8-sig'):
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        if line.startswith('[') and ']' in line:
            section = line[1:line.index(']')].strip().lower()
            sections.setdefault(section, {})
            continue
        if section is None:
            continue
        if section.startswith('begin action '):
            fields = [part.strip() for part in line.split(',')]
            if len(fields) >= 2 and all(part.lstrip('-').isdigit()
                                        for part in fields[:2]):
                actions.setdefault(int(section.split()[-1]), []).append(
                    tuple(map(int, fields[:2])))
        elif '=' in line:
            key, value = line.split('=', 1)
            sections[section][key.strip().lower()] = value.strip()
    return sections, actions


def _def_sprite(section, key):
    return tuple(int(x.strip()) for x in section[key].split(',')[:2])


def _fnt_v2_sff(path):
    sections, _ = _mugen_def(path)
    return os.path.join(os.path.dirname(path),
                        sections['def']['file'].strip('"'))


def _lifebar_backdrop(imgs, tiles, top_keys, bottom_keys):
    """Compile the two 640x480 fight.def halves into BG3 tilemap strips.

    fight.sff uses full-canvas PNGs.  The active 1P/2P frames occupy the
    upper 120 source rows and the power frames occupy rows 394..462.  Keep
    their transparent pixels so the stage remains visible around the HUD.
    """
    from PIL import Image

    def strip(groups, y0, y1, rows):
        canvas = Image.new('RGBA', (256, rows * 8), (0, 0, 0, 0))
        for side, key in enumerate(groups):
            im = imgs[key].crop((0, y0, 320, y1))
            im = im.resize((128, rows * 8), Image.LANCZOS)
            canvas.alpha_composite(im, (side * 128, 0))
        return canvas

    strips = (strip(top_keys, 10, 130, 7),
              strip(bottom_keys, 399, 467, 4))
    pool = {bytes(tiles[i:i + 16]): i // 16
            for i in range(0, len(tiles), 16)}
    maps = []
    for area, im in enumerate(strips):
        px = im.load()
        words = []
        for ty in range(im.height // 8):
            for tx in range(32):
                cell = bytearray(64)
                for y in range(8):
                    for x in range(8):
                        r, g, b, a = px[tx * 8 + x, ty * 8 + y]
                        if a < 96:
                            v = 0
                        elif max(r, g, b) < 70:
                            v = 1                 # black frame/outline
                        elif min(r, g, b) > 185:
                            v = 3                 # silver/white highlight
                        else:
                            v = 2                 # blue/red/orange field
                        cell[y * 8 + x] = v
                if not any(cell):
                    words.append(0)
                    continue
                raw = tiles2bpp(bytes(cell), 8, 8)
                tile = pool.get(raw)
                if tile is None:
                    tile = len(tiles) // 16
                    pool[raw] = tile
                    tiles.extend(raw)
                pal = 7 if area else (3 if tx < 16 else 6)
                words.append(tile | (((0x20 | pal * 4) & 0xFC) << 8))
        maps.append(words)
    return maps


def build_portraits():
    """Build 24x24 2bpp HUD portraits from the select-cell icons.

    Each portrait uses a per-character 3-colour palette (plus transparent
    index 0), copied to CGRAM 0/4 at fight start.  The cells stay exactly
    inside the 3x3 face windows of the lifebar.
    """
    from build_select import ROSTER, sprite_rgb
    from PIL import Image
    data = bytearray()
    paldata = bytearray()
    table = []
    table_p2 = []
    for entry in ROSTER:
        rel = entry[0]
        path = os.path.join(ROOT, "assets/characters", rel)
        try:
            im, _ = sprite_rgb(Sff(path), 9000, 0)
            im = im.convert("RGBA").resize((24, 24), Image.LANCZOS)
        except Exception:
            im = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        # Quantise only the opaque face pixels; transparent pixels become
        # tile index 0 so the red/blue window shows through.
        rgb = Image.new("RGB", (24, 24), (128, 128, 128))
        rgb.paste(im, (0, 0), im)
        q = rgb.quantize(colors=3, method=Image.MEDIANCUT,
                         dither=Image.NONE)
        qp = q.getpalette()
        cols = [tuple(qp[i * 3:i * 3 + 3]) for i in range(3)]
        pal = [(0, 0, 0)] + cols
        for r, g, b in pal:
            c = (r * 31 // 255) | ((g * 31 // 255) << 5) \
                | ((b * 31 // 255) << 10)
            paldata += struct.pack("<H", c)
        vals = []
        alpha = im.split()[3]
        for y in range(24):
            for x in range(24):
                if alpha.getpixel((x, y)) < 96:
                    vals.append(0)
                else:
                    vals.append(q.getpixel((x, y)) + 1)
        table.append(len(data))
        data += tiles2bpp(bytes(vals), 24, 24)
        # P2 uses the same art mirrored horizontally.
        mirrored = [vals[y * 24 + (23 - x)]
                    for y in range(24) for x in range(24)]
        table_p2.append(len(data))
        data += tiles2bpp(bytes(mirrored), 24, 24)
    open(os.path.join(OUT, "portraits.chr"), "wb").write(data)
    open(os.path.join(OUT, "portrait_pal.bin"), "wb").write(paldata)
    inc = ["; generated by tools/build_fight.py -- do not edit\n",
           f"PORTRAIT_COUNT = {len(table)}\n",
           "PortraitOfs:\n"]
    for i in range(0, len(table), 8):
        inc.append("    .dw " + ",".join(str(v) for v in table[i:i + 8])
                   + "\n")
    inc.append("PortraitOfsP2:\n")
    for i in range(0, len(table_p2), 8):
        inc.append("    .dw " + ",".join(str(v) for v in table_p2[i:i + 8])
                   + "\n")
    open(os.path.join(OUT, "portraits.inc"), "w").write("".join(inc))
    print(f"hud portraits: {len(table)} chars, {len(data)}B + {len(paldata)}B pal")


def build_hud():
    """SNES fight HUD sourced from Lifebar/fight.def and its SFF/FNT files."""
    from PIL import Image
    tiles = bytearray()
    lb_dir = os.path.join(ROOT, "assets/kof98data/Lifebar")
    definition, actions = _mugen_def(os.path.join(lb_dir, "fight.def"))
    files = definition['files']
    life_def = definition['lifebar']
    power_def = definition['powerbar']
    round_def = definition['round']
    win_def = definition['winicon']
    life_bg = (_def_sprite(life_def, 'p1.bg1.spr'),
               _def_sprite(life_def, 'p2.bg1.spr'))
    life_fill = _def_sprite(life_def, 'p1.front.spr')
    power_bg = (_def_sprite(power_def, 'p1.bg1.spr'),
                _def_sprite(power_def, 'p2.bg1.spr'))
    power_fill = _def_sprite(power_def, 'p1.front.spr')
    win_icon = _def_sprite(win_def, 'p1.bg0.spr')
    round_key = (int(round_def['round1.anim']), 4)
    go_key = (int(round_def['fight.anim']), 34)
    ko_key = (int(round_def['ko.anim']), 6)
    for key in (round_key, go_key, ko_key):
        if key not in actions[key[0]]:
            raise ValueError(f"fight.def action {key[0]} lacks frame {key}")

    # --- small font: KOF99DM 8x8 (Stage.fnt = Life Names Simul.fnt) ------
    fnt = _fnt_v1(os.path.join(lb_dir, files['font7']))
    for ch in CHARSET:
        cell = bytearray(64)
        spr = fnt.get(ch) or fnt.get(ch.lower()) or fnt.get(ch.upper())
        if spr:
            im = spr
            if im.width != 8:
                im = im.resize((8, im.height), Image.LANCZOS)
            pix = im.load()
            for y in range(min(8, im.height)):
                for x in range(8):
                    if _q(pix[x, y]) >= 2:
                        cell[y * 8 + x] = 3
        # The KOF99DM strip has a blank @ entry; draw a compact one so the
        # MSU credits can spell "LE@N".
        if ch == '@' and not any(cell):
            for x, y in ((2, 1), (3, 1), (4, 1),
                         (1, 2), (5, 2),
                         (1, 3), (3, 3), (5, 3),
                         (1, 4), (3, 4), (5, 4),
                         (1, 5), (3, 5), (4, 5), (5, 5),
                         (1, 6), (2, 7), (3, 7), (4, 7)):
                cell[y * 8 + x] = 3
        # dark outline around every lit pixel
        for y in range(8):
            for x in range(8):
                if cell[y * 8 + x]:
                    continue
                for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 8 and 0 <= yy < 8 and \
                            cell[yy * 8 + xx] == 3:
                        cell[y * 8 + x] = 1
                        break
        tiles += tiles2bpp(bytes(cell), 8, 8)

    # --- big font: KOF98 name font (Name.fnt = Life Names.fnt) ----------
    # Letters/punct come from the 690x15 variable-width PCX strip; the
    # digits come from the timer font (Time.sff) for the KOF98 clock look.
    # Every glyph is squeezed into an 8x16 cell -> a pair of 8x8 tiles.
    nfont = _fnt_v1(os.path.join(lb_dir, files['font1']))
    tdig = _sff_imgs(_fnt_v2_sff(os.path.join(lb_dir, files['font2'])))
    BIGSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.!'- "
    big_base = len(tiles) // 16
    big_ids = {}
    for ch in BIGSET:
        cell = bytearray(128)
        spr = tdig.get((0, ord(ch))) if ch.isdigit() else nfont.get(ch)
        if spr:
            im = spr.copy()
            if ch.isalnum():                # fill the 8x15 cell, squashing
                nw, nh = 8, 15              #   wide KOF98 glyphs into caps
            else:                           # punctuation keeps its aspect
                k = min(8.0 / im.width, 15.0 / im.height, 1.0)
                nw, nh = max(1, round(im.width * k)), \
                    max(1, round(im.height * k))
            if (nw, nh) != im.size:
                im = im.resize((nw, nh), Image.LANCZOS)
            px = im.load()
            ox = (8 - nw) // 2
            oy = 16 - nh
            for y in range(im.height):
                for x in range(im.width):
                    cell[(oy + y) * 8 + ox + x] = _q(px[x, y])
        # outline grows the dark border one pixel
        for y in range(16):
            for x in range(8):
                if cell[y * 8 + x]:
                    continue
                for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 8 and 0 <= yy < 16 and \
                            cell[yy * 8 + xx] >= 2:
                        cell[y * 8 + x] = 1
                        break
        big_ids[ch] = len(tiles) // 16
        tiles += tiles2bpp(bytes(cell[:64]), 8, 8)
        tiles += tiles2bpp(bytes(cell[64:]), 8, 8)

    # fight.def embeds the AIR actions.  The held frames are ROUND, GO!, KO.
    keys = {round_key, go_key, ko_key, life_fill, power_fill,
            win_icon, *life_bg, *power_bg}
    fspr = _sff_imgs(os.path.join(lb_dir, files['sff']), keys)
    logo_blocks = {}

    def logo_cells(key, cols, rows=2, c0=0, c1=None):
        """Rasterise an SFF sprite into a `rows x cols` grid of 8x8 tile
        ids, emitting tiles only for columns [c0, c1)."""
        nonlocal tiles
        im = fspr[key]
        bb = im.getbbox()
        im = im.crop(bb) if bb else im
        im = im.resize((cols * 8, rows * 8 - 1), Image.LANCZOS)
        canvas = Image.new('RGBA', (cols * 8, rows * 8), (0, 0, 0, 0))
        canvas.paste(im, (0, rows * 8 - 1 - im.height), im)
        px = canvas.load()
        grid = [[0] * cols for _ in range(rows)]
        for ty in range(rows):
            for tx in range(cols):
                if c1 is not None and not (c0 <= tx < c1):
                    continue
                cell = bytearray(64)
                for y in range(8):
                    for x in range(8):
                        cell[y * 8 + x] = _q(px[tx * 8 + x, ty * 8 + y])
                grid[ty][tx] = len(tiles) // 16
                tiles += tiles2bpp(bytes(cell), 8, 8)
        return grid

    # The round sprite embeds a trailing "1"; only its first 6 columns
    # ("ROUND") are emitted and the real round number is drawn separately
    # with the BIGD tiles, so later rounds show the right digit.
    rgrid = logo_cells(round_key, 8, c0=0, c1=6)
    logo_blocks["RoundLogo"] = (6, 2,
                                rgrid[0][0:6] + rgrid[1][0:6])
    for label, key, cols in (("KoLogo", ko_key, 6),
                             ("FgLogo", go_key, 8)):
        g = logo_cells(key, cols)
        logo_blocks[label] = (cols, 2, g[0] + g[1])

    # Each dynamic tile includes its empty frame.  It must replace the BG3
    # static-map cell at every health value, including zero.
    blank = Image.new('RGBA', (88, 8), (0, 0, 0, 0))
    life_base = fspr[life_bg[0]].crop((68, 44, 286, 62)).resize((88, 8), Image.LANCZOS)
    life = fspr[life_fill].crop((68, 44, 286, 62)).resize((88, 8), Image.LANCZOS)
    power_base = fspr[power_bg[0]].crop((32, 433, 235, 451)).resize((88, 8), Image.LANCZOS)
    power = fspr[power_fill].crop((32, 435, 235, 454)).resize((88, 8), Image.LANCZOS)
    bars = {(0, 0): life_base, (0, 1): life,
            (0, 2): power_base, (0, 3): power, (0, 4): blank}
    lb_base = len(tiles) // 16
    for cell in _bar_tiles(bars, (0, 0), None, (0, 1), (0, 4), w=88):
        tiles += tiles2bpp(cell, 8, 8)
    pb_base = len(tiles) // 16
    for cell in _bar_tiles(bars, (0, 2), None, (0, 3), (0, 4), w=88):
        tiles += tiles2bpp(cell, 8, 8)

    # Opaque fill for drained gauge middles: index 1 in the HUD palettes.
    blank_bar = len(tiles) // 16
    # 2bpp solid index 1: low plane all ones, high plane zero.
    tiles += bytes((0xFF, 0x00)) * 8

    # Round-win icon, group 120 in the [WinIcon] section.
    pip = len(tiles) // 16
    icon = fspr[win_icon].resize((8, 8), Image.LANCZOS)
    cell = bytearray(_q(icon.getpixel((x, y)))
                     for y in range(8) for x in range(8))
    tiles += tiles2bpp(bytes(cell), 8, 8)

    # The two stock counters use their own FNT v2 SFF art, as fight.def does.
    pow_ids = {}
    for side in (1, 2):
        digits = _sff_imgs(_fnt_v2_sff(os.path.join(
            lb_dir, files[f'font{side + 2}'])),
            {(0, ord(ch)) for ch in "0123"})
        pow_ids[side] = len(tiles) // 16
        for ch in "0123":
            im = digits[0, ord(ch)]
            im = im.crop(im.getbbox()).resize((8, 15), Image.LANCZOS)
            canvas = Image.new('RGBA', (8, 16), (0, 0, 0, 0))
            canvas.alpha_composite(im, (0, 1))
            values = bytes(_q(canvas.getpixel((x, y)))
                           for y in range(16) for x in range(8))
            tiles += tiles2bpp(values[:64], 8, 8)
            tiles += tiles2bpp(values[64:], 8, 8)

    # In Combo.def, ASCII A is the "HITS" suffix used by [Combo] in fight.def.
    combo = _sff_imgs(_fnt_v2_sff(os.path.join(lb_dir, files['font6'])),
                      {(0, ord('A'))})[0, ord('A')]
    combo = combo.resize((32, 8), Image.LANCZOS)
    combo_ids = []
    for tx in range(4):
        cell = bytes(_q(combo.getpixel((tx * 8 + x, y)))
                     for y in range(8) for x in range(8))
        combo_ids.append(len(tiles) // 16)
        tiles += tiles2bpp(cell, 8, 8)

    topmap, bottommap = _lifebar_backdrop(fspr, tiles, life_bg, power_bg)
    portrait_base = len(tiles) // 16
    tiles += bytes(16) * 18                 # reserve 3x3 tiles per side
    # BG3 tiles are DMA'd to VRAM word $2000 (BG3CHR); dynamic stage-anim
    # tiles begin at word $2C00 (STGACHR).  The $C00 words in between hold
    # 6144 bytes = 384 2bpp tiles, so hud.chr must not exceed that or it
    # would overwrite the crowd/pose animation tiles.
    if len(tiles) // 16 > 384:
        raise ValueError("lifebar exceeds BG3's 384 tile VRAM region "
                         "($2000-$2BFF, before STGACHR=$2C00)")
    open(os.path.join(OUT, "hud.chr"), "wb").write(tiles)

    strs = {
        "StrTitle": "FIGHTING ENGINE",
        "StrStart": "PRESS START",
        "StrKfm": "IORI",
        "StrKO": "K.O.",
        "StrTime": "TIME",
        "StrDraw": "DRAW",
        "StrRound": "ROUND ",
        "StrWins": "WINS",
        "StrP1": "1P:",
        "StrP2": "2P:",
        "StrLevel": "LEVEL",
        "StrSelHint": "SELECT",
        "Str1P": "1P",
        "Str2P": "2P",
        "StrK720": "KYO",
        "StrShingo": "SHINGO",
        "StrRugal": "RUGAL",
        "StrSaisyu": "SAISYU",
        "StrHeidern": "HEIDERN",
        "StrTakuma": "TAKUMA",
        "StrClark": "CLARK",
        "StrRalf": "RALF",
        "StrLeona": "LEONA",
        "StrMature": "MATURE",
        "StrVice": "VICE",
        "StrBenimaru": "BENIMARU",
        "StrDaimon": "DAIMON",
        "StrORugal": "O.RUGAL",
    }
    for _k in NEW_CHARS:
        if _k in CHARS:
            strs["Str" + _k[0].upper() + _k[1:]] = \
                CHARS[_k].get("display", _k.upper())
    # PRACTICE command-list tags: three-letter row tag + full category name
    # for the selected-move detail line.
    for _i, (_short, _full) in enumerate(CMD_CATEGORIES):
        strs[f"CmdCatShort{_i}"] = _short
        strs[f"CmdCat{_i}"] = _full
    strs["CmdListTitle"] = "COMMAND LIST"
    strs["CmdListSide1"] = "P1"
    strs["CmdListSide2"] = "P2"
    strs["CmdListLegend"] = "NRM CMD SPC SUP MAX THR SYS"
    strs["CmdListHelp"] = "UP/DN L/R SIDE  START EXIT"
    inc = []
    inc.append(f"PORTRAIT_P1 = {portrait_base}\n"
               f"PORTRAIT_P2 = {portrait_base + 9}\n")
    for label, s in strs.items():
        ids = [CHARSET.index(c) for c in s]
        inc.append(f"{label}: .db {len(ids)}," +
                   ",".join(str(i) for i in ids) + "\n")
    # Runtime indexes these by row category / short tag.
    inc.append("CmdCatTab: .dw " +
               ",".join(f"CmdCat{i}" for i in range(len(CMD_CATEGORIES))) +
               "\n")
    inc.append("CmdCatShortTab: .dw " +
               ",".join(f"CmdCatShort{i}"
                        for i in range(len(CMD_CATEGORIES))) + "\n")
    inc.append(f"CMD_CUR_TILE = {CHARSET.index('>')}\n"
               f"CMD_USED_TILE = {CHARSET.index('+')}\n")
    bstrs = {
        "BStrKO": "K.O.",
        "BStrTime": "TIME OVER",
        "BStrRound": "ROUND ",
        "BStrTitle": "FIGHTING ENGINE",
        "BStrWins": "WINS",
        "BStrDraw": "DRAW",
        "BStrPause": "PAUSE",
        "BStrContinue": "CONTINUE",
        "BStrCommand": "COMMAND LIST",
        "BStrExit": "EXIT",
        "BStrYouLose": "YOU LOSE",
        "BStrSelectFighter": "SELECT FIGHTER",
        "BStrKfm": "IORI",
        "BStrK720": "KYO",
        "BStrShingo": "SHINGO",
        "BStrRugal": "RUGAL",
        "BStrSaisyu": "SAISYU",
        "BStrHeidern": "HEIDERN",
        "BStrTakuma": "TAKUMA",
        "BStrClark": "CLARK",
        "BStrRalf": "RALF",
        "BStrLeona": "LEONA",
        "BStrMature": "MATURE",
        "BStrVice": "VICE",
        "BStrBenimaru": "BENIMARU",
        "BStrDaimon": "DAIMON",
        "BStrORugal": "OMEGA",
        "BStrSel": "SELECT",
    }
    for _k in NEW_CHARS:
        if _k in CHARS:
            bstrs["BStr" + _k[0].upper() + _k[1:]] = \
                CHARS[_k].get("display", _k.upper())
    for label, s in bstrs.items():
        ids = [big_ids[c] for c in s]
        inc.append(f"{label}: .db {len(ids)}," +
                   ",".join(str(i) for i in ids) + "\n")
    for label, (cols, rows, ids) in logo_blocks.items():
        inc.append(f"{label}: .db {cols},{rows}," +
                   ",".join(str(i) for i in ids) + "\n")
    inc.append("ComboHits: .db 4," +
               ",".join(str(i) for i in combo_ids) + "\n")
    # FUSION counter-hit banner.  Uses the shared big font so it costs tiles
    # already emitted for names/quotes.
    inc.append("CounterTxt: .db 7," +
               ",".join(str(big_ids[c]) for c in "COUNTER") + "\n")
    for label, words in (("HudTopMap", topmap),
                         ("HudBottomMap", bottommap)):
        inc.append(f"{label}:\n")
        for i in range(0, len(words), 8):
            inc.append("    .dw " + ",".join(
                f"${word:04X}" for word in words[i:i + 8]) + "\n")
    inc.append(f"BIGD0 = {big_ids['0']}\n"
               f"LB_BAR = {lb_base}\n"
               f"PB_BAR = {pb_base}\n"
               f"PIP = {pip}\n"
               f"P1POW0 = {pow_ids[1]}\n"
               f"P2POW0 = {pow_ids[2]}\n"
               f"BLANK_BAR = {blank_bar}\n"
               f"ATT_TXT = $2C\n"
               f"ATT_YEL = $34\n"
               f"ATT_GRN = $30\n"
               f"ATT_RED = $38\n"
               f"ATT_SIL = $3C\n"
               f"FONT_BASE = 0\n")
    open(os.path.join(OUT, "hud.inc"), "w").write("".join(inc))

    pals = [
        # pal3 P1 frame and white text
        (0, 0, 0), (12, 16, 44), (32, 70, 245), (255, 255, 255),
        # pal4 lifebar green
        (0, 0, 0), (12, 16, 12), (40, 160, 48), (170, 255, 170),
        # pal5 lifebar yellow + big-font gold
        (0, 0, 0), (20, 14, 4), (190, 140, 20), (255, 240, 150),
        # pal6 P2 frame and critical life
        (0, 0, 0), (28, 8, 8), (220, 32, 22), (255, 245, 245),
        # pal7 power bar and counters
        (0, 0, 0), (20, 16, 20), (246, 91, 8), (255, 246, 201),
    ]
    open(os.path.join(OUT, "hud_pal.bin"), "wb").write(snes_pal(pals, 20))
    print(f"hud: {len(CHARSET)} + {len(BIGSET)}x2 font tiles, "
          f"{len(tiles) // 16} tiles total")


def _inc_size(fname):
    """assembled byte size of a generated .inc (counts data directives)."""
    import re
    total = 0
    for line in open(os.path.join(OUT, fname), errors="replace"):
        line = line.split(";")[0].strip()
        m = re.match(r"(?:[A-Za-z_][A-Za-z_0-9]*:\s*)?\.(db|dw|dl|byte|word)\b(.*)", line)
        if m:
            n = len([t for t in m.group(2).split(",") if t.strip()])
            total += n * {"db": 1, "byte": 1, "dw": 2, "word": 2, "dl": 3}[m.group(1)]
    return total


def emit_newchars_inc(new_keys, msu_slices):
    """Emit newchars_{tabs,desc,banks}.inc consumed by fight.asm for the
    mass MSU import.  Always runs so stale files never linger; under
    KOF_BASE4 the files carry only the BASE4-visible rows."""
    cap = lambda k: k[0].upper() + k[1:]
    # Roster order used by CharSelTab / AltPalRow (ids 0-3, fixed 4-14, then
    # the mass-imported ids 15+).
    alt_roster = ["kyo", "iori", "shingo", "rugal",
                  "saisyu", "heidern", "takuma", "clark",
                  "ralf", "leona", "mature", "vice",
                  "benimaru", "daimon", "omegarugal"] + list(new_keys)
    alt_label = {"omegarugal": "OmegaRugal"}

    # Quote strings are shared by every character and live in their own
    # per-language sections so tight per-character banks only carry the
    # 96-byte QuoteTab.  Labels are resolved as 24-bit pointers by the
    # assembler, so the packer is free to place the sections anywhere.
    qstr_files = []
    for fname, tag in QUOTE_LANGS:
        rel = f"quote_strings_{tag}.inc"
        with open(os.path.join(OUT, rel), "w") as f:
            f.write(f"; generated by tools/build_fight.py -- {tag} quotes\n")
            f.write("".join(QUOTE_STRINGS[tag]))
        qstr_files.append((tag, rel))
    with open(os.path.join(OUT, "quote_tables.inc"), "w") as f:
        f.write("; generated by tools/build_fight.py -- victory quote tables\n")
        f.write("".join(QUOTE_TABLES))
    with open(os.path.join(OUT, "char_names.inc"), "w") as f:
        f.write("; generated by tools/build_fight.py -- char name strings\n")
        f.write("".join(CHAR_NAMES))

    def ai_label(k):
        # Kyo is the generic fallback: his EX variants and any character
        # without a generated move table inherit his CPU personality.
        return "kyoAiTab" if (k in ("kyonests", "kyoash")
                              or not AI_COUNTS.get(k)) else f"{k}AiTab"

    # ---- newchars_tabs.inc: replaces the CharSelTab..StrCpu block ----
    # (old rows kept verbatim; new ids = 15.. in NEW_CHARS order, id 14
    # stays the hidden Omega Rugal)
    t = ["; generated by tools/build_fight.py -- do not edit\n",
         "CharSelTab: .dw CharKyo, CharIori, CharShingo, CharRugal\n",
         ".IFNDEF BASE4\n",
         "            .dw CharSaisyu, CharHeidern, CharTakuma, CharClark\n",
         "            .dw CharRalf, CharLeona, CharMature, CharVice\n",
         "            .dw CharBenimaru, CharDaimon, CharOmegaRugal\n"]
    for i in range(0, len(new_keys), 4):
        t.append("            .dw " + ", ".join(
            "Char" + cap(k) for k in new_keys[i:i + 4]) + "\n")
    t += [".ENDIF\n",
          "BankSelTab: .db :kyoSprOfs, :ioriSprOfs, :shingoSprOfs,"
          " :rugalSprOfs\n",
          ".IFNDEF BASE4\n",
          "            .db :saisyuSprOfs, :heidernSprOfs, :takumaSprOfs,"
          " :clarkSprOfs\n",
          "            .db :ralfSprOfs, :leonaSprOfs, :matureSprOfs,"
          " :viceSprOfs\n",
          "            .db :benimaruSprOfs, :daimonSprOfs,"
          " :omegarugalSprOfs\n"]
    for i in range(0, len(new_keys), 4):
        t.append("            .db " + ", ".join(
            f":{k}SprOfs" for k in new_keys[i:i + 4]) + "\n")
    t += [".ENDIF\n",
          "AiSelTab: .dw kyoAiTab, ioriAiTab, shingoAiTab, rugalAiTab\n",
          ".IFNDEF BASE4\n",
          "            .dw saisyuAiTab, heidernAiTab, takumaAiTab,"
          " clarkAiTab\n",
          "            .dw ralfAiTab, leonaAiTab, matureAiTab, viceAiTab\n",
          "            .dw benimaruAiTab, daimonAiTab, omegarugalAiTab\n"]
    for i in range(0, len(new_keys), 4):
        t.append("            .dw " + ", ".join(
            ai_label(k) for k in new_keys[i:i + 4]) + "\n")
    t += [".ENDIF\n",
          "AiSelBank: .db :kyoAiTab, :ioriAiTab, :shingoAiTab,"
          " :rugalAiTab\n",
          ".IFNDEF BASE4\n",
          "            .db :saisyuAiTab, :heidernAiTab, :takumaAiTab,"
          " :clarkAiTab\n",
          "            .db :ralfAiTab, :leonaAiTab, :matureAiTab,"
          " :viceAiTab\n",
          "            .db :benimaruAiTab, :daimonAiTab,"
          " :omegarugalAiTab\n"]
    for i in range(0, len(new_keys), 4):
        t.append("            .db " + ", ".join(
            ":" + ai_label(k) for k in new_keys[i:i + 4]) + "\n")
    t += [".ENDIF\n",
          "SelBStrTab: .dw BStrK720, BStrKfm, BStrShingo, BStrRugal\n",
          ".IFNDEF BASE4\n",
          "            .dw BStrSaisyu, BStrHeidern, BStrTakuma, BStrClark\n",
          "            .dw BStrRalf, BStrLeona, BStrMature, BStrVice\n",
          "            .dw BStrBenimaru, BStrDaimon, BStrORugal\n"]
    for i in range(0, len(new_keys), 4):
        t.append("            .dw " + ", ".join(
            "BStr" + cap(k) for k in new_keys[i:i + 4]) + "\n")
    t += [".ENDIF\n",
          "SelStrTab:  .dw StrK720, StrKfm, StrShingo, StrRugal\n",
          ".IFNDEF BASE4\n",
          "            .dw StrSaisyu, StrHeidern, StrTakuma, StrClark\n",
          "            .dw StrRalf, StrLeona, StrMature, StrVice\n",
          "            .dw StrBenimaru, StrDaimon, StrORugal\n"]
    for i in range(0, len(new_keys), 4):
        t.append("            .dw " + ", ".join(
            "Str" + cap(k) for k in new_keys[i:i + 4]) + "\n")
    # CPU random-pick pool: every selectable common char.  Rugal (id 3)
    # and hidden Omega Rugal (id 14) are campaign bosses only, and the Kyo
    # EX variants are select-only extras (L/R on Kyo).
    # BASE4 keeps the historic 0-2 pick (only 4 descriptors exist there)
    pool = ([i for i in range(14) if i != 3] +
            [15 + j for j, k in enumerate(new_keys)
             if not CHARS.get(k, {}).get("hidden")]) \
        if new_keys else [0, 1, 2]
    nroster = (15 + len(new_keys)) if new_keys else 4
    fixed_names = ["kyo", "iori", "shingo", "rugal", "saisyu", "heidern",
                   "takuma", "clark", "ralf", "leona", "mature", "vice",
                   "benimaru", "daimon", "omegarugal"]
    idname = {i: fixed_names[i] for i in range(15)}
    for i, k in enumerate(new_keys, start=15):
        idname[i] = k
    rom_flags = [0 if idname.get(i) in msu_slices else 1
                 for i in range(nroster)]
    hidden = [1 if CHARS.get(idname.get(i), {}).get("hidden") else 0
              for i in range(nroster)]
    new_ids = {k: 15 + i for i, k in enumerate(new_keys)}
    t += [".ENDIF\n",
          "SelCols:    .db 1, 9, 17, 25\n",
          "StrCpu:     .db 3,3,16,21\n",
          f"NPOOL = {len(pool)}\n",
          f"NROSTER = {nroster}\n",
          "KYO_BASE_ID = 0\n",
          f"KYO_NESTS_ID = {new_ids.get('kyonests', 0)}\n",
          f"KYO_ASH_ID = {new_ids.get('kyoash', 0)}\n",
          "RomFlags:   .db " + ",".join(str(f) for f in rom_flags) + "\n",
          "HiddenTab:  .db " + ",".join(str(h) for h in hidden) + "\n",
          "CpuPool:    .db " + ",".join(str(i) for i in pool[:20]) + "\n",
          *(["            .db " + ",".join(str(i) for i in pool[20:]) + "\n"]
            if len(pool) > 20 else [])]
    # Projectile reflection windows.  Rows compare the victim's descriptor
    # pointer, so the table stays independent of roster order.  The engine
    # scans it before a projectile hit lands.  Keep it in the Fight bank
    # (24-bit reachable) rather than FightData, whose high bank makes WLA
    # reject indexed long addressing such as ReflectTab+2,x.
    reflect = ["ReflectTab:\n"]
    for _name, _rows in REFLECTORS.items():
        if _name not in CHARS:
            continue
        _c = cap(_name)
        for _sid, _start, _end, _x0, _y0, _x1, _y1 in _rows:
            reflect.append(f"    .dw Char{_c}\n"
                           f"    .db {_sid},{_start},{_end},"
                           f"{_x0 & 0xFF},{_y0 & 0xFF},"
                           f"{_x1 & 0xFF},{_y1 & 0xFF}\n")
    reflect.append("    .dw $FFFF\n")
    open(os.path.join(OUT, "reflect_tab.inc"), "w").write("".join(reflect))
    # Normal special-cancel opens.  Each row is six bytes, one open element
    # for each strong sid in CANCEL_STRONG_ORDER.  The descriptor's
    # CH_CANCELROW word points at the row; the table and CancelGate share
    # bank 50's low window.
    cancel = ["; generated by tools/build_fight.py -- do not edit\n",
              "CancelTab:\n"]
    for k in CHARS:
        rows = CANCEL_OPENS.get(k)
        if not rows:
            continue
        opens = dict(rows)
        cancel.append(f"{k}CancelRow:\n")
        cancel.append("    .db " + ",".join(
            str(opens[sid]) for sid in CANCEL_STRONG_ORDER) + "\n")
    open(os.path.join(OUT, "cancel_tab.inc"), "w").write("".join(cancel))
    open(os.path.join(OUT, "newchars_tabs.inc"), "w").write("".join(t))

    # ---- newchars_desc.inc: descriptors + pals (inside Fight section) --
    d = ["; generated by tools/build_fight.py -- do not edit\n",
         ".IFNDEF BASE4\n"]
    for k in new_keys:
        C = cap(k)
        pfx = CHARS[k].get("projfx_alias", k)
        if k in msu_slices:
            sl = msu_slices[k]
            chr_fields = [f"    .dw {sl >> 8}\n",
                          f"    .db {sl & 0xFF}, 1\n"]
        else:
            # ExHiROM's $01:0000 mirror is CPU RAM/I/O.  The same lower
            # half of file bank 65 is readable as ROM at $41:0000.
            chr_fields = ["    .dw 0\n", f"    .db (:{C}Chr+$40), 0\n"]
        d += [f"Char{C}:\n",
              f"    .dw {k}SprOfs, {k}BoxTab, {k}AnimTab\n",
              f"    .dw {k}ActiveTab, {k}DamageTab, {k}HitTimeTab\n",
              f"    .dw {k}SlideTab, {k}HitVelTab, {k}ButtonTab\n",
              "    .db $30, 0\n",
              *chr_fields,
              f"    .dw {C}Pal\n",
              f"    .db :{C}Pal, 0\n",
              f"    .dw {k}Name\n",
              f"    .dw {k}CButtonTab, {k}AButtonTab, {k}FlagsTab\n",
              f"    .dw {k}GVelTab, {k}GDmgTab\n",
              f"    .dw {k}CmdTab, {k}MotTab, {k}PosTab\n",
              f"    .dw {k}ChainTab\n",
              f"    .dw {k}PowTab\n",
              f"    .dw {k}TransTab, {k}EVelTab\n",
              f"    .dw {k}TargetTab\n",
              f"    .dw {k}BindTab, {k}ActTab, {k}RevTab\n",
              f"    .dw {k}HitSndTab\n",
              f"    .dw {k}ShakeTab\n",
              f"    .dw {k}QuoteTab\n",
              f"    .dw {k}ExpTab\n",
              f"    .dw {k}PauseTab\n",
              f"    .dw {C}PalDim\n",
              f"    .db :{C}PalDim, 0\n",
              f"    .dw {C}PalHi\n",
              f"    .db :{C}PalHi, 0\n",
              f"    .dw {k}ProjTab\n",
              f"    .db :{k}SprData, 0\n",
              f"    .dw {pfx}ProjFxTab, {pfx}ProjFxChr\n",
              f"    .dw {k}CmdList\n",
              f"    .db :{k}CmdList, {MAX_MASKS.get(k, 0)}\n",
              f"    .dw {k}CancelRow\n"]
    for k in new_keys:
        C = cap(k)
        d += [f"{C}Pal: .INCBIN \"gen_fight/{k}_pal.bin\"\n",
              f"{C}PalDim: .INCBIN \"gen_fight/{k}_pal_dim.bin\"\n",
              f"{C}PalHi: .INCBIN \"gen_fight/{k}_pal_hi.bin\"\n"]
    d.append(".ENDIF\n")
    open(os.path.join(OUT, "newchars_desc.inc"), "w").write("".join(d))
    mm = ["; generated by tools/build_fight.py -- do not edit\n"]
    # Fixed descriptors live in fight.asm outside the BASE4 guard, so their
    # constants must exist even when KOF_BASE4 removed the character from
    # CHARS.  Generated descriptors use the numeric mask directly.
    fixed_desc = ("iori", "kyo", "shingo", "rugal", "omegarugal", "saisyu",
                  "heidern", "takuma", "clark", "ralf", "leona", "mature",
                  "vice", "benimaru", "daimon")
    for k in sorted(set(CHARS) | set(fixed_desc)):
        mm.append(f"{k}MaxMask = {MAX_MASKS.get(k, 0)}\n")
    open(os.path.join(OUT, "max_masks.inc"), "w").write("".join(mm))

    # ---- alt_pals.inc: P2 mirror palettes -------------------------------
    # Kept out of FightData: its tail already holds YouLoseCode.  PVS bank
    # 124's low window carries EndData2 up to $6A80; the remaining 5.5 KiB
    # tail is free and fits 50 palette triples.  The standalone map uses a
    # different bank, and the AltPalRow table stays in FightData.
    a = ["; generated by tools/build_fight.py -- do not edit\n",
         ".IFDEF PVSNESLIB\n",
         ".BASE $00\n",
         ".BANK 124 SLOT 0\n",
         ".ORGA $6A80\n",
         ".ELSE\n",
         ".BASE $00\n",
         ".BANK 119 SLOT 0\n",
         ".ORGA $0000\n",
         ".ENDIF\n",
         '.SECTION "AltPals" FORCE\n',
         "; 9-byte rows: three pointer+bank entries, no padding.\n",
         "AltPalRow:\n"]
    for _k in alt_roster:
        _c = alt_label.get(_k, cap(_k))
        a += [f"    .dw {_c}PalP2\n", f"    .db :{_c}PalP2\n",
              f"    .dw {_c}PalP2Dim\n", f"    .db :{_c}PalP2Dim\n",
              f"    .dw {_c}PalP2Hi\n", f"    .db :{_c}PalP2Hi\n"]
    for _k in alt_roster:
        _c = alt_label.get(_k, cap(_k))
        a += [f"{_c}PalP2: .INCBIN \"gen_fight/{_k}_pal_p2.bin\"\n",
              f"{_c}PalP2Dim: .INCBIN \"gen_fight/{_k}_pal_p2_dim.bin\"\n",
              f"{_c}PalP2Hi: .INCBIN \"gen_fight/{_k}_pal_p2_hi.bin\"\n"]
    a.append('.INCLUDE "engine/alt_pals.asm"\n')
    a.append(".ENDS\n")
    # The include starts with .BASE $00 to reach bank 124's low window.  Do
    # not leak that state: fight.asm links its 64 KiB data banks (Iori/Kyo/
    # Shingo/Rugal) right after this include and they need the ROM window.
    a.append(".BASE $C0\n")
    open(os.path.join(OUT, "alt_pals.inc"), "w").write("".join(a))
    alt_size = 9 * len(alt_roster) + 96 * len(alt_roster) + 192
    end02 = os.path.getsize(os.path.join(
        ROOT, "src/gen_menu/end/end02.chr"))
    if end02 + alt_size > 0x8000:
        raise ValueError(f"alt palettes overlap bank 124's EndData2 window: "
                         f"{end02:#x} + {alt_size} > 0x8000")

    # ---- newchars_banks.inc: bank windows + empty chr placeholders ----
    # Full CPU banks $40-$7D map the upper 4 MiB of ExHiROM. Their low
    # halves are ROM too, unlike the RAM/I/O mirrors at $00-$3D:0000.
    # Terry CHR occupies low halves 65-81; 82/83 hold Omega/Takuma tables.
    # Banks 84-125 therefore provide independent 32 KiB windows below the
    # fixed stage/menu/CHR assets in their upper halves. Emit BASE $00 for
    # these sections so :label resolves to CPU $54-$7D, rather than $14-$3D.
    # Generated tables/metas that exceed 32 KiB use the full HiROM bank 47,
    # the dynamically measured tails after BenimaruData/ShingoData, or the
    # bank 48 tail registered below.
    benimaru_end = _inc_size("benimaru_spr.inc")
    shingo_end = _inc_size("shingo_spr.inc")
    PVS_SLOTS = [(47, 0, 65536),
                 (61, benimaru_end, 65536 - benimaru_end),
                 (62, shingo_end, 65536 - shingo_end)]
    # Bank 88 carries EndData15 in the lower half and ShingoChrS in the
    # upper half.  A generated section there makes the linker reject
    # ShingoChrS once the allocation order changes, so leave the bank to
    # the fixed sections.
    PVS_SLOTS += [(bank, 0, 32768)
                  for bank in range(84, 118) if bank != 88]
    # Bank 82 is otherwise unused in the PVS build: its low half starts
    # after EndData18 (13 KiB) and its upper half is free.  Small overflow
    # tables/projectile atlases use these tail windows.
    PVS_SLOTS += [(82, 0x4000, 0x4000)]
    # Bank 50's low half is free below the Fight code, but $7100-$751C is
    # reserved for FightMenuTail (menucore.asm).  Keep generated data below
    # that tail or the linker cannot place the section.
    PVS_SLOTS += [(50, 0x0000, 0x7100)]
    # Bank 48 ($F0) carries EndDataMP2 at $0000-$6600.  The rest of the
    # 64 KiB window is free and is the only remaining slot large enough for
    # a 33-34 KiB generated table/meta blob (Heavyd/Billy/Mrbig).
    PVS_SLOTS += [(48, 0x6600, 0x10000 - 0x6600)]
    # Bank 56's low half is empty in the hybrid map; its full 32 KiB window
    # keeps 12 KiB projectile atlases from fragmenting the upper banks.
    PVS_SLOTS += [(56, 0x0000, 0x8000)]
    # Daimon's tables occupy the low part of bank 63; the tail is still ROM
    # and gives the 12 KiB projectile atlases a window that does not depend
    # on the per-character table packing above.
    daimon_end = _inc_size("daimon_spr.inc")
    PVS_SLOTS += [(63, daimon_end, 65536 - daimon_end)]
    # Never allocate file banks 126/127: ExHiROM maps them to CPU $7E/$7F,
    # which are WRAM, so data placed there is unreachable (projectile tables
    # and Chris' generated tables used to land in that hole).  The ending
    # banks below still have usable ROM windows once their fixed stills are
    # placed; keep these ranges in sync with the map from wlalink -v.
    # Bank 118's $401A-$6B85 area is occupied by Omega's generated tables;
    # only the tail after the packed projectile atlases is really free.
    PVS_SLOTS += [(118, 0x6B86, 0x8000 - 0x6B86),
                  (120, 0x0E20, 0x71E0), (122, 0x0000, 0x8000)]

    def pvs_bank(bank):
        if bank in (126, 127):
            raise ValueError(f"bank {bank} maps to WRAM on ExHiROM")
        return f".BASE ${0 if bank >= 64 else 0xC0:02X}\n.BANK {bank} SLOT 0\n"

    def qstr_pvs():
        out = []
        for tag, rel in qstr_files:
            qb, qo = pvs_qstr[tag]
            out += [pvs_bank(qb), f".ORGA ${qo:04X}\n",
                    f'.SECTION "QuoteStr{cap(tag)}" FORCE\n',
                    f'.INCLUDE "gen_fight/{rel}"\n', '.ENDS\n']
        out += [pvs_bank(58), ".ORGA $C000\n",
                '.SECTION "SharedTables" FORCE\n',
                '.INCLUDE "gen_fight/quote_tables.inc"\n',
                '.INCLUDE "gen_fight/char_names.inc"\n',
                '.INCLUDE "gen_fight/survival_msu.inc"\n', '.ENDS\n']
        return out

    def qstr_standalone():
        out = [".BANK 52 SLOT 0\n", ".ORGA $0000\n",
               '.SECTION "QuoteStrings" FORCE\n']
        out += [f'.INCLUDE "gen_fight/{rel}"\n' for _tag, rel in qstr_files]
        out += [".ENDS\n", ".BANK 52 SLOT 0\n", ".ORGA $8000\n",
                '.SECTION "SharedTables" FORCE\n',
                '.INCLUDE "gen_fight/quote_tables.inc"\n',
                '.INCLUDE "gen_fight/char_names.inc"\n',
                '.INCLUDE "gen_fight/survival_msu.inc"\n', '.ENDS\n']
        return out

    # Each new char ships two pieces: _spr.inc (state/gameplay tables plus
    # the SprOfs index, addressed at F_TBANK) and _meta.inc (the bulky
    # SprData metasprite cells, addressed at the descriptor's CH_MBANK byte).
    # Pack metas and tables together, largest first. Separate passes can leave
    # enough total bytes but fragment the short contiguous windows.
    meta_sz = {k: _inc_size(k + "_meta.inc") for k in new_keys}
    old_split = [k for k in SPLIT_OLD if k in CHARS]
    meta_sz.update({k: _inc_size(k + "_meta.inc") for k in old_split})
    tab_sz = {k: _inc_size(k + "_spr.inc") for k in new_keys}
    free = [[s[0], s[1], s[2]] for s in PVS_SLOTS]
    # Raw data sections need no alignment; leave a small readable map gap.
    pvs_guard = 0
    cancel_size = 6 * len(CANCEL_OPENS)

    def grab(sz_map, guard=None, prefer_max_slot=None, defer_no_fit=False):
        guard = pvs_guard if guard is None else guard
        alloc = {}
        for k in sorted(sz_map, key=lambda k: -sz_map[k]):
            candidates = [slot for slot in free
                          if sz_map[k] <= slot[2] - guard]
            if prefer_max_slot is not None:
                compact = [slot for slot in candidates
                           if slot[2] <= prefer_max_slot]
                if compact:
                    candidates = compact
            if not candidates:
                if defer_no_fit:
                    continue
                raise ValueError(f"{k}: no free PVS bank window for "
                                 f"{sz_map[k]} bytes")
            # Best-fit prevents a medium section from wasting a large span
            # and leaving only fragments too small for later tables.
            slot = min(candidates, key=lambda candidate: candidate[2])
            alloc[k] = (slot[0], slot[1])
            slot[1] += sz_map[k] + guard
            slot[2] -= sz_map[k] + guard
        return alloc
    # Animation records share one bank; 2x frame pages are scattered into
    # free ROM windows and carry their own bank byte for DMA.
    proj_order = [k for k in CHARS if k in PROJECTILE_BLOBS]
    proj_blob = bytearray()
    proj_offsets = {}
    proj_lengths = {}
    proj_length1 = {}
    proj_length2 = {}
    for k in proj_order:
        payload = PROJECTILE_BLOBS[k]
        payload2 = PROJECTILE_BLOBS2.get(k, b"")
        proj_offsets[k] = len(proj_blob)
        proj_length1[k] = len(payload)
        proj_length2[k] = len(payload2)
        proj_lengths[k] = len(payload) + len(payload2)
        proj_blob += payload + payload2
    open(os.path.join(OUT, "projectiles.bin"), "wb").write(proj_blob)
    proj_meta = []
    for k in proj_order:
        frames = PROJECTILE_TABLES[k]
        frames2 = PROJECTILE_TABLES2.get(k)
        second = f"{k}ProjFxAnim" if frames2 is None else f"{k}ProjFx2Anim"
        # ProjFxTab header: primary anim, alternate anim, then the spawn
        # height byte at offset 4.  ProjSpawn reads the height from offset 4
        # regardless of which clip is selected; keep this layout in sync.
        proj_meta.append(f"{k}ProjFxTab: .dw {k}ProjFxAnim, {second}\n")
        spawn_row = 2 if k in TORSO_PROJECTILES else int(k in GROUND_PROJECTILES)
        proj_meta.append(f"    .db {spawn_row}\n")
        proj_meta.append(f"{k}ProjFxAnim: .db {len(frames)}\n")
        for fi in range(len(frames)):
            proj_meta.append(f"    .dw {k}ProjFxF{fi}\n")
        if frames2 is not None:
            proj_meta.append(f"{k}ProjFx2Anim: .db {len(frames2)}\n")
            for fi in range(len(frames2)):
                proj_meta.append(f"    .dw {k}ProjFx2F{fi}\n")
        for fi, (ticks, cells) in enumerate(frames):
            proj_meta.append(f"{k}ProjFxF{fi}: .db {ticks},{len(cells)}\n")
            proj_meta.append(f"    .dw {k}ProjFxChr+{fi * 2048}\n"
                             f"    .db :{k}ProjFxChr\n")
            for dx, dy, slot in cells:
                proj_meta.append(f"    .db {dx & 0xFF},{dy & 0xFF}\n"
                f"    .dw ${SPARK_SLOTS[slot]:04X}\n")
        if frames2 is not None:
            for fi, (ticks, cells) in enumerate(frames2):
                proj_meta.append(f"{k}ProjFx2F{fi}: .db {ticks},{len(cells)}\n")
                proj_meta.append(f"    .dw {k}ProjFx2Chr+{fi * 2048}\n"
                                 f"    .db :{k}ProjFx2Chr\n")
                for dx, dy, slot in cells:
                    proj_meta.append(f"    .db {dx & 0xFF},{dy & 0xFF}\n"
                    f"    .dw ${SPARK_SLOTS[slot]:04X}\n")
    open(os.path.join(OUT, "projectiles_meta.inc"), "w").write(
        "".join(proj_meta))
    proj_inc = ["ProjFxGlobal:\n", '.INCLUDE "gen_fight/projectiles_meta.inc"\n']
    open(os.path.join(OUT, "projectiles.inc"), "w").write(
        "".join(proj_inc))
    proj_size = _inc_size("projectiles_meta.inc")
    # The cancel table is small but the Fight bank is already tight; give
    # it the low half of the Fight bank's own ROM window (the map's
    # PVS_SLOTS already proves it free).  A near JSR reaches CancelGate.
    pvs_cancel = None
    for idx, slot in enumerate(free):
        # Bank 50's low half shares the Fight code's CPU bank ($F2), so a
        # plain JSR from the hit path reaches CancelGate without a bank
        # switch.  Reserve the window before grab() can split it.
        if slot[0] == 50 and slot[1] == 0 and slot[2] >= cancel_size:
            pvs_cancel = (50, 0)
            # The command gate and its table are far smaller than the 32 KiB
            # window.  Keep the tail available for generated character
            # tables instead of dropping the whole slot from the pool.
            used = max(0x1000, (cancel_size + 0x0FFF) & ~0x0FFF)
            if used < slot[2]:
                slot[1] += used
                slot[2] -= used
            else:
                free.pop(idx)
            break
    if pvs_cancel is None:
        pvs_cancel = grab({"__cancel": cancel_size}, guard=0)["__cancel"]
    if pvs_cancel[0] != 50:
        raise ValueError("CancelData must stay in the Fight bank (near JSR)")
    cancel_data = ["; generated by tools/build_fight.py -- do not edit\n",
                   ".IFDEF PVSNESLIB\n", pvs_bank(pvs_cancel[0]),
                   f".ORGA ${pvs_cancel[1]:04X}\n",
                   ".ELSE\n", ".BANK 50 SLOT 0\n", ".ORGA $0000\n",
                   ".ENDIF\n",
                   '.SECTION "CancelData" FORCE\n',
                   '.INCLUDE "gen_fight/cancel_tab.inc"\n',
                   '.INCLUDE "engine/cancel_gate.asm"\n',
                   ".ENDS\n"]
    open(os.path.join(OUT, "cancel_data.inc"), "w").write(
        "".join(cancel_data))
    # Reserve the PRACTICE command pool before smaller allocations fragment
    # the only windows that can hold this contiguous block.
    cmd_keys = [k for k in new_keys if k not in FIXED_CMD_LIST]
    cmdpool_sz = _inc_size("cmdlist_pool.inc")
    pvs_cmdpool = (grab({"__cmdpool": cmdpool_sz}, guard=0)["__cmdpool"]
                   if cmdpool_sz else None)
    # Allocate the per-character sections (metas + gameplay tables) first:
    # they are by far the largest blocks and need the big contiguous windows.
    # The small/fixed projectile atlases and the AI table fit in the leftover
    # fragments afterwards.  Allocating the small pieces first fragmented the
    # last 10 KiB window and left a character table with nowhere to go.
    combined_sizes = ({("meta", k): size for k, size in meta_sz.items()} |
                      {("table", k): size for k, size in tab_sz.items()})
    combined_alloc = grab(combined_sizes)
    pvs_meta = {k: combined_alloc[("meta", k)] for k in meta_sz}
    pvs_tab = {k: combined_alloc[("table", k)] for k in tab_sz}
    # Projectile atlases are a fixed 4 KiB each and must be contiguous; the
    # AI table avoids the per-character section banks so a 30K table never
    # pushes Vice/Kyo's shared bank 60 over its 32K window.
    pvs_projgfx = grab(proj_lengths, guard=16)
    pvs_ai = grab({"__ai": _inc_size("ai_tables.inc")})["__ai"]
    # The shared projectile descriptor table is small; allocate it after the
    # 64 KiB Chang meta section has claimed the full-window slot.
    proj_slot = max((slot for slot in free
                     if proj_size <= slot[2] - pvs_guard),
                    key=lambda slot: slot[2])
    pvs_proj = (proj_slot[0], proj_slot[1])
    proj_slot[1] += proj_size + pvs_guard
    proj_slot[2] -= proj_size + pvs_guard
    # Quote strings live in fixed readable tails of the already-occupied
    # banks: Rugal's low half (bank 44) carries EN+FR, Iori's bank 58 carries
    # PT and Heidern's bank 59 carries ES.  The assertions keep the constants
    # honest if a character's generated tables grow later.
    qstr_sz = {tag: _inc_size(rel) for tag, rel in qstr_files}
    assert _inc_size("kyo_spr.inc") <= 0x9000      # ViceData starts there
    assert _inc_size("vice_spr.inc") <= 0x7000     # remainder of bank 60
    # MatureData uses the free tail of sound bank 55 ($794C-$FFFF).
    assert _inc_size("mature_spr.inc") <= 0x10000 - 0x794C
    assert _inc_size("rugal_spr.inc") <= 0x3000
    assert 0x3000 + qstr_sz["en"] <= 0x5000
    assert 0x5000 + qstr_sz["fr"] <= 0x8000
    assert _inc_size("iori_spr.inc") <= 0x9000
    assert 0x9000 + qstr_sz["pt"] <= 0x10000
    assert _inc_size("heidern_spr.inc") <= 0xA000
    assert 0xA000 + qstr_sz["es"] <= 0x10000
    qtab_sz = (_inc_size("quote_tables.inc") +
               _inc_size("char_names.inc") +
               _inc_size("survival_msu.inc"))
    assert 0xC000 + qtab_sz <= 0x10000            # PVS bank 58
    assert sum(qstr_sz.values()) <= 0x8000        # standalone bank 52
    assert 0x8000 + qtab_sz <= 0x10000
    pvs_qstr = {"en": (44, 0x3000), "fr": (44, 0x5000),
                "pt": (58, 0x9000), "es": (59, 0xA000)}
    gfx_inc = ["; per-frame 2x projectile atlases\n.IFDEF PVSNESLIB\n"]
    for k in proj_order:
        bk, org = pvs_projgfx[k]
        gfx_inc += [pvs_bank(bk), f".ORGA ${org:04X}\n",
                    f'.SECTION "{k}ProjGfx" FORCE\n',
                    f"{k}ProjFxChr:\n",
                    f'    .INCBIN "gen_fight/projectiles.bin" '
                    f'SKIP {proj_offsets[k]} READ {proj_length1[k]}\n']
        if k in PROJECTILE_BLOBS2:
            gfx_inc += [
                f"{k}ProjFx2Chr:\n",
                f'    .INCBIN "gen_fight/projectiles.bin" '
                f'SKIP {proj_offsets[k] + proj_length1[k]} '
                f'READ {proj_length2[k]}\n']
        gfx_inc.append(".ENDS\n")
    # PVSnesLib build uses the fixed-bank FORCE sections above.  The
    # standalone ExHiROM branch duplicated every ProjFxChr label when WLA
    # parsed both sides; the shipping ROM is PVS-only, so emit just the
    # PVS branch.
    gfx_inc.append(".ENDIF\n")
    open(os.path.join(OUT, "projectiles_gfx.inc"), "w").write("".join(gfx_inc))
    b = ["; generated by tools/build_fight.py -- do not edit\n",
         ".IFNDEF BASE4\n",
         "; mass-import tables.  PVSNESLIB scatters them across the free\n",
         "; spans of the 8 MiB map (see PVS_SLOTS in build_fight.py),\n",
         "; with SprData cells in a separate section (CH_MBANK-resolved);\n",
         "; the standalone map gives each char two banks (128+)\n",
         ".IFDEF PVSNESLIB\n"]
    for k in new_keys:
        C = cap(k)
        for suffix, alloc in (("Data", pvs_tab), ("Meta", pvs_meta)):
            bk, org = alloc[k]
            inc = "_spr.inc" if suffix == "Data" else "_meta.inc"
            b += [pvs_bank(bk), f".ORGA ${org:04X}\n",
                  f".SECTION \"{C}{suffix}\" FORCE\n",
                  f".INCLUDE \"gen_fight/{k}{inc}\"\n", ".ENDS\n"]
    # Restored-frame metas for the old-roster fighters.  Their descriptors
    # already point CH_MBANK at <name>SprData, so moving that label into a
    # packed bank only changes the bank byte.
    for k in old_split:
        C = cap(k)
        bk, org = pvs_meta[k]
        b += [pvs_bank(bk), f".ORGA ${org:04X}\n",
              f".SECTION \"{C}Meta\" FORCE\n",
              f".INCLUDE \"gen_fight/{k}_meta.inc\"\n", ".ENDS\n"]
    if pvs_cmdpool:
        bk, org = pvs_cmdpool
        b += [pvs_bank(bk), f".ORGA ${org:04X}\n",
              '.SECTION "CmdListPool" FORCE\n',
              '.INCLUDE "gen_fight/cmdlist_pool.inc"\n', '.ENDS\n']
    bk, org = pvs_proj
    b += [pvs_bank(bk), f".ORGA ${org:04X}\n",
          '.SECTION "ProjFxGlobal" FORCE\n',
          '.INCLUDE "gen_fight/projectiles.inc"\n', '.ENDS\n']
    b += [pvs_bank(pvs_ai[0]), f".ORGA ${pvs_ai[1]:04X}\n",
          '.SECTION "AiTables" FORCE\n',
          '.INCLUDE "gen_fight/ai_tables.inc"\n', '.ENDS\n']
    b += qstr_pvs()
    b.append(".BASE $C0\n.ELSE\n")
    for i, k in enumerate(new_keys):
        C = cap(k)
        cmd_inc = (f".INCLUDE \"gen_fight/{k}_cmdlist.inc\"\n"
                   if k in cmd_keys else "")
        b += [f".BANK {128 + 2 * i} SLOT 0\n", ".ORGA $0000\n",
              f".SECTION \"{C}Data\" FORCE\n",
              f".INCLUDE \"gen_fight/{k}_spr.inc\"\n", cmd_inc, ".ENDS\n",
              f".BANK {129 + 2 * i} SLOT 0\n", ".ORGA $0000\n",
              f".SECTION \"{C}Meta\" FORCE\n",
              f".INCLUDE \"gen_fight/{k}_meta.inc\"\n", ".ENDS\n"]
    for i, k in enumerate(old_split):
        C = cap(k)
        b += [f".BANK {128 + 2 * len(new_keys) + i} SLOT 0\n", ".ORGA $0000\n",
              f".SECTION \"{C}Meta\" FORCE\n",
              f".INCLUDE \"gen_fight/{k}_meta.inc\"\n", ".ENDS\n"]
    b += [".BANK 47 SLOT 0\n", ".ORGA $0000\n",
          '.SECTION "ProjFxGlobal" FORCE\n',
          '.INCLUDE "gen_fight/projectiles.inc"\n', '.ENDS\n']
    b += [".BANK 51 SLOT 0\n", ".ORGA $0000\n",
          '.SECTION "AiTables" FORCE\n',
          '.INCLUDE "gen_fight/ai_tables.inc"\n', '.ENDS\n']
    b += qstr_standalone()
    b.append(".ENDIF\n")
    for k in new_keys:
        b.append(f".INCLUDE \"gen_fight/{k}_chr.inc\"\n")
    b.append(".ENDIF\n")
    b.append(".IFDEF BASE4\n.IFDEF PVSNESLIB\n")
    b += [pvs_bank(pvs_proj[0]),
          f".ORGA ${pvs_proj[1]:04X}\n",
          '.SECTION "ProjFxGlobal" FORCE\n',
          '.INCLUDE "gen_fight/projectiles.inc"\n', '.ENDS\n']
    b += [pvs_bank(pvs_ai[0]), f".ORGA ${pvs_ai[1]:04X}\n",
          '.SECTION "AiTables" FORCE\n',
          '.INCLUDE "gen_fight/ai_tables.inc"\n', '.ENDS\n']
    b += qstr_pvs()
    b += [".BASE $C0\n.ELSE\n.BANK 47 SLOT 0\n.ORGA $0000\n",
          '.SECTION "ProjFxGlobal" FORCE\n',
          '.INCLUDE "gen_fight/projectiles.inc"\n', '.ENDS\n',
          ".BANK 51 SLOT 0\n.ORGA $0000\n",
          '.SECTION "AiTables" FORCE\n',
          '.INCLUDE "gen_fight/ai_tables.inc"\n', '.ENDS\n']
    b += qstr_standalone()
    b += [".ENDIF\n"]
    b.append(".ENDIF\n")
    b.append('.INCLUDE "gen_fight/projectiles_gfx.inc"\n')
    open(os.path.join(OUT, "newchars_banks.inc"), "w").write("".join(b))


def emit_voices(msu, rom_voice_chars):
    """Per-char .snd samples -> ROM tables and MSU-1 voice data.

    Characters whose CHR is linked into the ROM (the same set that becomes
    RomFlags=1) stay selectable without the .msu file, so their voices are
    kept in ROM as well.  Terry also needs ROM voices to avoid the MSU copy
    blocking the main loop.  All other characters remain in MSU-1.
    """
    from build_spc_neogeo import (encode_brr, load_mugen_snd,
                                  load_wav_mono_bytes, resample_mono)
    id_order = ["kyo", "iori", "shingo", "rugal", "saisyu", "heidern",
                "takuma", "clark", "ralf", "leona", "mature", "vice",
                "benimaru", "daimon", "omegarugal", *NEW_CHARS]
    L = [f"; generated char voice tables (ROM BRR or .msu offsets)\n",
         f".DEFINE VOICE_BASE {VOICE_BASE}\n",
         f".DEFINE VOICE_CHAR_COUNT {len(id_order)}\n"]
    ptrs = {}
    cache = {}

    def snd_of(name):
        d = os.path.join(ROOT, os.path.dirname(CHARS[name]["cns"]))
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(".snd"):
                return os.path.join(d, f)
        return None

    voice_banks = "SEMISUPERFREE BANKS 11-63"
    total = 0
    missing = []
    for name in id_order:
        voices = CHAR_VOICES.get(name)
        snd = voices and snd_of(name)
        if not snd:
            continue
        if snd not in cache:
            from pathlib import Path
            cache[snd] = load_mugen_snd(Path(snd))
        items = []
        for pair, vid in sorted(voices.items(), key=lambda kv: kv[1]):
            raw = cache[snd].get(pair)
            if raw is None:
                missing.append((name, pair))
                items.append(encode_brr([0] * 16, loop=False))
                continue
            pcm, rate = load_wav_mono_bytes(raw)
            pcm = resample_mono(pcm, rate, 4000)
            while pcm and abs(pcm[0]) < 600:
                pcm.pop(0)
            while pcm and abs(pcm[-1]) < 600:
                pcm.pop()
            pcm = pcm[:6000]
            peak = max((abs(v) for v in pcm), default=1) or 1
            pcm = [int(v * 30000 / peak) for v in pcm]
            items.append(encode_brr(pcm or [0] * 16, loop=False))
        tab_label = f"VoiceTab_{name}"
        ofs_label = f"VoiceOfs_{name}"
        # ROM-CHR fighters (RomFlags=1) are selectable with no .msu file,
        # so their samples must not be MSU-only: link them into the ROM.
        # Terry is already in this set and also benefits from skipping the
        # MSU-to-WRAM copy during a fight.
        rom_voice = name in rom_voice_chars
        ptrs[name] = (tab_label, None if rom_voice else ofs_label)
        L.append(f'.SECTION "{tab_label}" {voice_banks}\n{tab_label}:\n')
        for vid, brr in enumerate(items):
            # SNESMOD's spcPlaySoundV uses the table's PITCH field, where
            # each step is 2 kHz. The BRR voices above are encoded from 4 kHz
            # PCM, so pitch 2 preserves their intended duration and tone.
            L.append(f"    .db 2,8,15\n    .dw {len(brr) // 9}\n"
                     + (f"    .dw V_{name}_{vid}\n"
                        f"    .db :V_{name}_{vid}\n" if rom_voice
                        else "    .dw (VOICE_BUF & $FFFF)\n    .db $7E\n"))
        L.append(".ENDS\n")
        if rom_voice:
            for vid, brr in enumerate(items):
                label = f"V_{name}_{vid}"
                path = os.path.join(OUT, "voice", label + ".brr")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as output:
                    output.write(brr)
                L.append(f'.SECTION "{label}" {voice_banks}\n'
                         f'{label}: .INCBIN "gen_fight/voice/{label}.brr"\n'
                         ".ENDS\n")
        else:
            L.append(f'.SECTION "{ofs_label}" {voice_banks}\n{ofs_label}:\n')
            for brr in items:
                off = len(msu)
                b4 = ", ".join(str((off >> s) & 0xFF)
                               for s in (0, 8, 16, 24))
                L.append(f"    .db {b4}\n")
                msu += brr
            L.append(".ENDS\n")
        for brr in items:
            total += len(brr)
    # F_CHAR stores the 16-bit descriptor pointer, not the roster index, so
    # the runtime maps desc -> (voice table, offset table), 8 B/entry.
    L.append(f'.SECTION "VoicePtrs" {voice_banks}\nVoicePtrTab:\n')
    for name in id_order:
        t = ptrs.get(name)
        if t:
            cname = {"omegarugal": "OmegaRugal"}.get(name, name.capitalize())
            L.append(f"    .dw Char{cname}, {t[0]}\n"
                     f"    .db :{t[0]}\n"
                     + (f"    .dw {t[1]}\n    .db :{t[1]}\n"
                        if t[1] else "    .dw 0\n    .db 0\n"))
    L.append("    .dw 0\n")                    # terminator
    L.append(".ENDS\n")
    open(os.path.join(OUT, "voices.inc"), "w").write("".join(L))
    print(f"voices: {sum(len(v) for v in CHAR_VOICES.values())} samples, "
          f"{total} bytes BRR (msu stream)")
    if missing:
        print(f"voices: {len(missing)} missing .snd entries: {missing}")
    return msu


def emit_survival_ending(msu):
    """Pack the 13 SURVIVOR stills into 32 KiB MSU blocks.

    Each block: 8-byte header (chr/map/pal lengths) followed by the 4bpp
    chr, the 32x32 map and the 128-byte banded palette.  The runtime seeks
    to these file offsets and DMAs the chr/map straight to VRAM.
    """
    src = os.path.join(ROOT, "assets/survival_ending")
    if not os.path.isdir(src):
        return msu, 0
    files = sorted(f for f in os.listdir(src)
                   if re.fullmatch(r"\d{2}\.png", f))
    if not files:
        return msu, 0
    from build_endings import build_frame
    dst = os.path.join(OUT, "survival")
    os.makedirs(dst, exist_ok=True)
    offsets = []
    for i, name in enumerate(files):
        base = os.path.join(dst, f"sv{i:02d}")
        build_frame(os.path.join(src, name), base)
        chr_b = open(base + ".chr", "rb").read()
        map_b = open(base + ".map", "rb").read()
        pal_b = open(base + ".pal", "rb").read()
        block = (struct.pack("<HHHH", len(chr_b), len(map_b),
                             len(pal_b), 0) + chr_b + map_b + pal_b)
        if len(block) > 32768:
            raise ValueError(f"survival ending {name}: {len(block)}B > 32 KiB")
        msu += b"\0" * ((-len(msu)) % 32768)
        offsets.append(len(msu))
        msu += block + b"\0" * (32768 - len(block))
    inc = [f"; generated by tools/build_fight.py -- do not edit\n" +
           f"SURVIVAL_END_COUNT = {len(offsets)}\n"]
    open(os.path.join(OUT, "survival_msu_defs.inc"), "w").write(
        "".join(inc))
    inc = ["; generated by tools/build_fight.py -- do not edit\n",
           "SurvivalEndOfs:\n"]
    for off in offsets:
        inc.append("    .db " + ",".join(str(b) for b in
                                         off.to_bytes(4, "little")) + "\n")
    open(os.path.join(OUT, "survival_msu.inc"), "w").write("".join(inc))
    print(f"survival ending: {len(offsets)} stills -> {sum(1 for _ in offsets) * 32} KiB")
    return msu, len(offsets)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    emit_runtime_abi(ROOT)
    import build_stages
    build_stages.build()
    build_hud()
    build_portraits()
    build_spark()
    skipped = []
    for name, cfg in CHARS.items():
        try:
            build_char(name, cfg)
        except Exception as e:
            # roster WIP: chars still missing wired assets are skipped so
            # the fight ROM can keep building off the playable cast
            if os.environ.get("KOF_TRACE"):
                import traceback
                traceback.print_exc()
            print(f"{name}: SKIPPED ({type(e).__name__}: {e})")
            skipped.append(name)
    # A skipped character can still have a good CHR blob from the previous
    # build (only the tables failed to regenerate).  Streamed characters reuse
    # it through the MSU path; ROM characters must still emit their chr
    # sections at the fixed CNAME_BANKS banks, or descriptors such as
    # CharShingo reference an undefined ShingoChr label.
    for name in skipped:
        chr_path = os.path.join(OUT, f"{name}.chr")
        if not os.path.exists(chr_path) or not os.path.getsize(chr_path):
            continue
        blob = open(chr_path, "rb").read()
        cfg = CHARS.get(name, {})
        if not cfg.get("msu") and name in CNAME_BANKS:
            cname, bank0, bank0x, orga = CNAME_BANKS[name]
            nbanks = (len(blob) + 32767) // 32768
            out_lines = []
            for i in range(nbanks):
                letter = chr(ord("A") + i)
                out_lines.append(
                    f".IFDEF PVSNESLIB\n.BANK {bank0 + i} SLOT 0\n.ELSE\n"
                    f".BANK {bank0x + i} SLOT 0\n.ENDIF\n.ORGA {orga}\n"
                    f".SECTION \"{cname}Chr{letter}\" FORCE\n\n"
                    + (f"{cname}Chr:\n" if i == 0 else "")
                    + f"    .INCBIN \"gen_fight/{name}.chr\" SKIP {i * 32768}"
                    + (" READ 32768" if i < nbanks - 1 else "") + "\n"
                    + (f"{cname}Chr_End:\n" if i == nbanks - 1 else "")
                    + ".ENDS\n\n")
            open(os.path.join(OUT, f"{name}_chr.inc"),
                 "w").write("".join(out_lines))
            print(f"{name}: reusing previous ROM CHR ({len(blob)} bytes)")
        else:
            MSU_BLOBS[name] = blob
            open(os.path.join(OUT, f"{name}_chr.inc"), "w").write(
                f"; {name}: chr lives in kof98-snes.msu (MSU-1 data file)\n")
            print(f"{name}: reusing previous CHR via MSU ({len(blob)} bytes)")
    with open(os.path.join(OUT, "art_loss.json"), "w") as f:
        json.dump({'events': ART_LOSS}, f, indent=2)
    # MSU-1 data file: a 32 KiB header block carrying the "KOF98MSU"
    # signature (probed by MsuDetect at boot to confirm both the port and
    # the right data file), then chr blobs at 32 KiB alignment addressed
    # by slice index (file offset >> 15) in CH_CHRBANK.
    msu = bytearray(b"KOF98MSU\0")
    defs = ["; MSU-1 chr slice indices into kof98-snes.msu\n",
            "; (each unit = 32 KiB; seek = (slice + tilebase>>10) * 32768\n",
            ";  + (tilebase&1023)*32 + pos)\n"]
    msu_slices = {}
    roster_order = {name: i for i, name in enumerate(CHARS)}
    ordered_blobs = sorted(
        MSU_BLOBS.items(),
        key=lambda kv: roster_order.get(kv[0], len(roster_order)))
    for name, blob in ordered_blobs:
        pad = (-len(msu)) % 32768
        msu += b"\0" * pad
        msu_slices[name] = len(msu) // 32768
        defs.append(f"MSU_{name.upper()}_SLICE = {msu_slices[name]}\n")
        msu += blob
    # RomFlags is computed as "not in msu_slices" (see emit_newchars_inc);
    # keep the voice storage decision on the same set.
    msu = emit_voices(msu, set(CHARS) - set(msu_slices))
    msu, sv_count = emit_survival_ending(msu)
    # Version the data-file layout.  Every streamed character's CHR offset
    # lives in the ROM as a 32 KiB slice index, so a .msu generated by a
    # different build silently feeds the wrong tiles into the OBJ pages
    # (the fighter turns into garbage boxes for the whole match).  Store a
    # CRC of the slice map + blob sizes in bytes 8-9 of the 32 KiB header;
    # MsuDetect compares it with the value linked into the ROM.
    layout_src = "|".join(
        f"{blob_name}:{msu_slices[blob_name]}:{len(blob)}"
        for blob_name, blob in ordered_blobs)
    layout_src += f"|size:{len(msu)}"
    layout = zlib.crc32(layout_src.encode("ascii")) & 0xFFFF
    if layout == 0:
        layout = 0x5A5A
    if len(msu) >= 10:
        msu[8] = layout & 0xFF
        msu[9] = layout >> 8
    if MSU_BLOBS or sv_count:
        defs.append(f"MSU_LAYOUT = ${layout:04X}\n")
        # Write through a temp file and rename: an emulator running during a
        # rebuild keeps this file open, and truncating it in place makes
        # sprite CHR reads past the new EOF return $FF (solid palette-15
        # "hitbox" blocks).  The rename swaps the inode instead.
        msu_path = os.path.join(OUT, "kof98-snes.msu")
        tmp_path = msu_path + ".tmp"
        with open(tmp_path, "wb") as f:
            f.write(msu)
        os.replace(tmp_path, msu_path)
        with open(msu_path, "rb") as f:
            head = f.read(10)
        assert head[:8] == b"KOF98MSU" \
            and head[8] | head[9] << 8 == layout, "MSU header layout mismatch"
        open(os.path.join(OUT, "msu1_bases.inc"), "w").write("".join(defs))
        print(f"msu1data: {len(MSU_BLOBS)} chars, {len(msu)} bytes, "
              f"layout ${layout:04X}")
    else:
        open(os.path.join(OUT, "msu1_bases.inc"), "w").write(
            "MSU_LAYOUT = $FFFF\n")
    open(os.path.join(OUT, "ai_tables.inc"), "w").write("".join(AI_TABLES))
    emit_command_pool()
    emit_newchars_inc([k for k in NEW_CHARS if k in CHARS], msu_slices)
