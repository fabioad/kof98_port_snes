#!/usr/bin/env python3
"""gen_char_cfg.py -- mass character import for the SNES fight engine.

For each new fighter:
  1. merges the .def state files into <Key>_SNES.cns (merge_cns layout),
  2. classifies its states into SNES sids.  Two wiring styles exist:
     * trigger style (kensou/mary/billy...): [State -1] entries carry
       `command = "<name>"` triggers referencing [Command] defs;
     * ikaruga style (-KOF98 pack): no command triggers -- the [State -1]
       NAME matches the [Command] name (weak/strong in the name).
  3. writes a sanitized <Key>_SNES.cmd in the Kyo_SNES.cmd dialect, and
  4. emits tools/newroster.py with ready-made CHARS entries (msu=True).

Sid conventions mirror the hand-tuned entries:
  5-8 stand normals (x,y,a,b), 19-22 crouch, 23-26 air,
  45 run / 46 backdash / 47 taunt, 48-66 special pairs, 67 CD, 69 dodge,
  74-77 throw chain, 85-89 supers, 94-97 fusion roll/dodge/max/charge.

Usage: python3 tools/gen_char_cfg.py [char ...]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS_DIR = os.path.join(ROOT, "assets", "characters")
KOF98DATA = os.path.join(ROOT, "assets", "kof98data")
OUT_SPEC = os.path.join(ROOT, "tools", "newroster.py")
INPUT_CALIBRATION_PATH = os.path.join(
    ROOT, "assets", "calibration", "input_profiles.json")
with open(INPUT_CALIBRATION_PATH, encoding="utf-8") as _profile_file:
    INPUT_CALIBRATIONS = json.load(_profile_file)


def input_calibration(key):
    """Return the reusable command-window profile assigned to a fighter."""
    name = INPUT_CALIBRATIONS.get("assignments", {}).get(key)
    if name is None:
        return None, None
    try:
        return name, INPUT_CALIBRATIONS["profiles"][name]
    except KeyError as exc:
        raise ValueError(f"{key}: unknown input calibration profile {name!r}") from exc

# per-char manual wiring for slots the auto-extractor cannot reach:
#   "specials": [(sid, statedef, "CanonName", "motion"), ...]
#   "moves":    {sid: statedef} extra/fallback sid wiring (sys states)
OVERRIDES = {
    "king": {   # unnamed -1 entries; statedefs exist but unwired
        "specials": [(48, 1000, "QCF_X", "~D, DF, F, x"),      # Venom Strike
                     (49, 1050, "QCF_Y", "~D, DF, F, y"),
                     (50, 1100, "QCB_A", "~D, DB, B, a"),      # Trap Shot
                     (51, 1150, "QCB_B", "~D, DB, B, b"),
                     (52, 1200, "DP_A", "~F, D, DF, a"),       # Surprise Rose
                     (53, 1250, "DP_B", "~F, D, DF, b"),
                     (54, 1300, "HCB_A", "~F, DF, D, DB, B, a"),  # Tornado
                     (55, 1350, "HCB_B", "~F, DF, D, DB, B, b"),
                     (56, 1400, "RDP_X", "~B, D, DB, x"),
                     (57, 1450, "RDP_Y", "~B, D, DB, y"),
                     (85, 3000, "SUP1_X", "~D, DB, B, DB, D, DF, F, x"),
                     (86, 3100, "SUP1_Y", "~D, DB, B, DB, D, DF, F, y"),
                     (87, 3500, "SUP2", "~D, DB, B, DB, D, DF, F, a")],
        # King's jump normals are 500/510/520/530; state 600 is the standing
        # blowback.  The generic 600 fallback made every air attack play the
        # blowback animation.
        "normals": {("s", "x"): 200, ("s", "y"): 210,
                    ("s", "a"): 230, ("s", "b"): 250,
                    ("c", "x"): 300, ("c", "y"): 310,
                    ("c", "a"): 320, ("c", "b"): 330,
                    ("a", "x"): 500, ("a", "y"): 510,
                    ("a", "a"): 520, ("a", "b"): 530},
        # Source throw is forward/back + y or b, not CD.  Both buttons share
        # state 800 so the single native bind slot (75 -> 810) stays intact.
        "throws": [(800, "y", 20), (800, "b", 20)],
        "moves": {19: 300, 20: 310, 21: 320, 22: 330,  # no crouch states
                  47: 195, 74: 800},
    },
    "heavyd": {
        # Source motion list: R.S.D. QCF+P, Blast Upper QCF+K, Soul
        # Flower QCB+K, Ducking Combination QCB+P, Dancing Beat F,D,DF+P,
        # Shadow D,D+P, D. Crazy D,F,D,F+P, D. Magnum D,F,D,F+K.
        "specials": [(48, 1000, "QCF_X", "~D, DF, F, x"),      # R.S.D.
                     (49, 1050, "QCF_Y", "~D, DF, F, y"),
                     (50, 1100, "QCF_A", "~D, DF, F, a"),      # Blast Upper
                     (51, 1150, "QCF_B", "~D, DF, F, b"),
                     (52, 1200, "QCB_A", "~D, DB, B, a"),      # Soul Flower
                     (53, 1250, "QCB_B", "~D, DB, B, b"),
                     (54, 1300, "QCB_X", "~D, DB, B, x"),      # Ducking Comb.
                     (55, 1350, "QCB_Y", "~D, DB, B, y"),
                     (56, 1400, "DP_X", "~F, D, DF, x"),       # Dancing Beat
                     (57, 1450, "DP_Y", "~F, D, DF, y"),
                     (58, 1900, "DD_X", "~D, D, x"),           # Shadow
                     (59, 1950, "DD_Y", "~D, D, y"),
                     (85, 2000, "QQCF_A", "~D, F, D, F, a"),   # D. Crazy
                     (86, 2050, "QQCF_B", "~D, F, D, F, b"),
                     (87, 2105, "QQCF_X", "~D, F, D, F, x"),   # D. Magnum
                     (88, 2105, "QQCF_Y", "~D, F, D, F, y")],
        # Blast Upper and Soul Flower put the actual HitDef in a helper
        # state (1110/1210); the native engine reaches it through a
        # transition at the end of the launch animation.
        "moves": {47: 199, 60: 1110, 61: 1210},
        "anims": {88: 2106},
        "cmd_frames": {"QQCF": 30, "DD": 24},
        "cfg": {
            "extra_trans": [(50, 60, 0, 0), (51, 60, 0, 0),
                            (52, 61, 0, 0), (53, 61, 0, 0)],
            # The QQCF supers share their final press with QCF; the longer
            # motion must be tried first or R.S.D. consumes the input.
            "cmd_priority": ["QQCF_A", "QQCF_B", "QQCF_X", "QQCF_Y"],
            # State 2105 is the D. Magnum release pose and carries no
            # PowerAdd, so charge both command slots here.
            "pow_override": {87: -1000, 88: -1000},
            # Keep HeavydMeta inside one 32 KiB PVS window; the follow-up
            # clips reuse the main special artwork.
            "tween_skip_sids": [56, 57, 58, 59, 60, 61, 62, 63, 64, 65,
                                66, 85, 86, 89],
            # The source gives the double motions a 30-frame buffer; the
            # shared 18-frame default is too tight for D,F,D,F and D,D.
            "cmd_frames": {"QQCF": 30, "DD": 24},
        },
    },
    "brian": {
        # Source motions: Brian Tornado QCF+P, Hyper Tackle QCF+K,
        # Screw Body Press air QCF+P, Rocket Tackle DP+K, Brian Hammer
        # QCB+P, Supernova D,F,B+P, Galaxy Cyclone QCFx2+P, Big Bang
        # Tackle QCFx2+K.
        "specials": [(48, 1000, "QCF_X", "~D, DF, F, x"),      # Brian Tornado
                     (49, 1050, "QCF_Y", "~D, DF, F, y"),
                     (50, 1100, "QCF_A", "~D, DF, F, a"),      # Hyper Tackle
                     (51, 1150, "QCF_B", "~D, DF, F, b"),
                     (52, 1300, "DP_A", "~F, D, DF, a"),       # Rocket Tackle
                     (53, 1350, "DP_B", "~F, D, DF, b"),
                     (54, 1400, "QCB_X", "~D, DB, B, x"),      # Brian Hammer
                     (55, 1400, "QCB_Y", "~D, DB, B, y"),
                     (56, 1200, "AIR_QCF_X", "~D, DF, F, x", 4),  # Screw Press
                     (57, 1250, "AIR_QCF_Y", "~D, DF, F, y", 4),
                     (85, 3000, "SUP1", "~D, F, B, x"),        # Supernova
                     (86, 3050, "SUP2", "~D, F, B, y"),
                     (87, 3110, "SUP3", "~D, DF, F, D, DF, F, x"),  # Galaxy
                     (88, 3210, "SUP4", "~D, DF, F, D, DF, F, a")], # Big Bang
        # Root specials are wind-ups; their HitDef lives in the follow-up
        # state.  Sid 56/57 are the airborne button pair, 58-65 the hit
        # states, 66/89 the Supernova follow-up pair.
        # Ground hit states use StSpecial slots (58/60/62/64); the airborne
        # dive/tackle follow-ups use StAirSpec (61/63/65/66) so gravity and
        # the TransTab landing rows run.  89 is the strong Supernova hit.
        "moves": {58: 1010, 59: 1060, 60: 1110, 61: 1210,
                  62: 1160, 63: 1260, 64: 3005, 65: 1310,
                  66: 1360, 89: 3055},
        # The generic standard-number matcher picked 610/630/640 for the
        # wrong buttons.  Brian's source uses 200/220/210/230 standing,
        # 400/420/410/430 crouching and 600/620/610/630 airborne.
        "normals": {("s", "x"): 200, ("s", "y"): 220,
                    ("s", "a"): 210, ("s", "b"): 230,
                    ("c", "x"): 400, ("c", "y"): 420,
                    ("c", "a"): 410, ("c", "b"): 430,
                    ("a", "x"): 600, ("a", "y"): 620,
                    ("a", "a"): 610, ("a", "b"): 630},
        # The QCFx2 supers share their final press with QCF; try the longer
        # motions first so Brian Tornado/Hyper Tackle cannot swallow them.
        "cmd_frames": {"SUP": 30},
        "cfg": {
            "cmd_priority": ["SUP3", "SUP4", "SUP1", "SUP2"],
            # Sids 87/88 start directly in the active super states
            # (3110/3210), which have no PowerAdd of their own.
            "pow_override": {87: -1000, 88: -1000},
            # QCFx2 supers get the source's 30-frame input buffer.
            "cmd_frames": {"SUP": 30},
        },
        # The air command shares the ground QCF motion; the matcher
        # separates the two rules by statetype.
    },
    "andy": {
        # The Zan'eiken hit is a second state (1001/1011) entered near the
        # opponent.  Wire it as a hit follow-up so the close-range HitDef and
        # its impact spark are compiled; the engine plays it at the end of
        # the startup animation and lets the HitDef whiff when far away.
        "moves": {54: 1001, 55: 1011},
        "anims": {54: 1001, 55: 1011},
        "cfg": {"extra_trans": [(50, 54, 0, 0), (51, 55, 0, 0)]},
    },
    "chang": {
        # Air normals are 600/610/620/630 = LP/LK/HP/HK; the grounded
        # 200/210/230/240 set already matches the standard order.
        "normals": {("a", "x"): 600, ("a", "y"): 620,
                    ("a", "a"): 610, ("a", "b"): 630},
        "specials": [(48, 1000, "QCF_X", "~D, DF, F, x"),
                     (49, 1010, "QCF_Y", "~D, DF, F, y"),
                     (50, 1100, "QCB_X", "~D, DB, B, x"),
                     (51, 1150, "QCB_Y", "~D, DB, B, y"),
                     (52, 1200, "DP_A", "~F, D, DF, a"),       # Taiko Uchi
                     (53, 1210, "DP_B", "~F, D, DF, b"),
                     (54, 1300, "HCB_X", "~F, DF, D, DB, B, x"),  # Dai Hakai
                     (55, 1350, "HCB_Y", "~F, DF, D, DB, B, y"),
                     # Tekkyuu Day-Bokusatsu ends on a/b (kicks).
                     (85, 3200, "SUP1", "~D, B, D, B, a"),
                     (86, 3300, "SUP2", "~D, B, D, B, y"),
                     (87, 3500, "SUP3", "~D, DB, B, DB, D, DF, F, x")],
    },
    "choi": {
        # Light/Strong Toppa are punch supers (source 236236_x/y).  Keep the
        # shorter charge motion the native matcher can finish, but move the
        # buttons to the punch side.
        "specials": [(85, 3050, "SUP1", "~D, B, D, B, x"),
                     (86, 3060, "SUP2", "~D, B, D, B, y"),
                     (87, 3500, "SUP3", "~D, DF, F, D, DF, F, x")],
    },
    "yashiro": {
        "specials": [(48, 1100, "QCF_X", "~D, DF, F, x"),      # Jet Counter
                     (49, 1110, "QCF_Y", "~D, DF, F, y"),
                     (50, 1200, "QCB_X", "~D, DB, B, x"),      # Upper Duel
                     (51, 1210, "QCB_Y", "~D, DB, B, y"),
                     (52, 1300, "DP_A", "~F, D, DF, a"),       # Sledgehammer
                     (54, 2000, "HCB_X", "~F, DF, D, DB, B, x"),
                     (55, 2100, "HCB_Y", "~F, DF, D, DB, B, y"),
                     (85, 3000, "SUP1", "~D, DF, F, D, DF, F, x"),
                     (86, 3010, "SUP2", "~D, DF, F, D, DF, F, y"),
                     (87, 3500, "SUP3", "~D, DB, B, DB, D, DF, F, a")],
    },
    "chizuru": {  # very sparse statedefs
        "specials": [(48, 1000, "QCF_X", "~D, DF, F, x"),
                     (49, 1004, "QCF_Y", "~D, DF, F, y"),
                     (50, 1100, "QCB_X", "~D, DB, B, x"),
                     (51, 1102, "QCB_Y", "~D, DB, B, y"),
                     (52, 1200, "DP_X", "~F, D, DF, x"),
                     (54, 1300, "HCB_X", "~F, DF, D, DB, B, x"),
                     (55, 1400, "HCB_Y", "~F, DF, D, DB, B, y"),
                     (56, 1500, "RDP_X", "~B, D, DB, x"),
                     (85, 2000, "SUP1", "~D, DF, F, D, DF, F, x"),
                     (86, 2100, "SUP2", "~D, DF, F, D, DF, F, y"),
                     (87, 2200, "SUP3", "~D, B, D, B, x")],
        # 200/400/600 pick the normal animation from a `command = hold_x`
        # ChangeAnim the native engine does not evaluate.  One cloned state
        # per button gives all twelve normals their own anim and hit row.
        "normals": {("s", "x"): 200, ("s", "y"): 202,
                    ("s", "a"): 201, ("s", "b"): 203,
                    ("c", "x"): 400, ("c", "y"): 402,
                    ("c", "a"): 401, ("c", "b"): 403,
                    ("a", "x"): 600, ("a", "y"): 601,
                    ("a", "a"): 602, ("a", "b"): 603},
        "clone_states": [(200, 201, 210), (200, 202, 220), (200, 203, 230),
                         (400, 401, 410), (400, 402, 420), (400, 403, 430),
                         (600, 601, 620), (600, 602, 610), (600, 603, 630),
                         # 1000 picks anim 1000/1001 from the command; clone
                         # the strong QCF variant too.
                         (1000, 1004, 1001),
                         # 1100 picks anim 1100/1101 from the command; clone
                         # the strong QCB variant so sid 51 keeps its art.
                         (1100, 1102, 1101),
                         # 360 is also the bind pose; keep a clone for the
                         # grab attempt so both slots can coexist.
                         (360, 361, 360)],
        # Source throw: y/b + forward/back, very close.  The engine widens
        # p2bodydist by both bodies' half width, hence the roomier gate.
        "throws": [(361, "y", 20), (361, "b", 20)],
        "moves": {74: 361},
        "cfg": {
            # No p1stateno in the source: the grab state doubles as the
            # bind.  Point the throw follow-up at 360 while sid 74 uses 361.
            "throw_self_bind": 360,
            # Each cloned state carries every HitDef; pick the one whose
            # anim range matches the cloned header.
            "hitdef_by_sid": {6: 1, 7: 0, 8: 2,
                              20: 2, 21: 1, 22: 3,
                              24: 2, 25: 0, 26: 2},
            # The source has no back evade, so the back roll reuses AIR 105,
            # whose last frame is a t=-1 (255-tick) hold.  Bound it to the
            # same 27-tick duration as the forward/neutral dodge (AIR 100).
            "tail_ticks": {105: 24},
        },
    },
    "athena": {
        "specials": [(48, 1000, "QCB_X", "~D, DB, B, x"),      # Psychic Ball
                     (55, 1010, "QCB_Y", "~D, DB, B, y"),
                     (49, 1020, "DP_X", "~F, D, DF, x"),       # Psycho Sword
                     (58, 1030, "DP_Y", "~F, D, DF, y"),
                     (50, 1040, "QCB_A", "~D, DB, B, a"),      # Reflective Shield
                     (51, 1050, "QCB_B", "~D, DB, B, b"),
                     (52, 1060, "QCF_A", "~D, DF, F, a"),      # Teleport
                     (59, 1065, "QCF_B", "~D, DF, F, b"),
                     (56, 1070, "HCF_X", "~B, D, DF, F, x"),   # Psychic Grasp
                     (57, 1070, "HCF_Y", "~B, D, DF, F, y"),
                     (54, 1080, "AIR_QCB_A", "~D, DB, B, a", 4),  # aerial dive
                     (53, 1085, "AIR_QCB_B", "~D, DB, B, b", 4),
                     (85, 3000, "SUP1", "~F, DF, D, DB, B, F, DF, D, DB, B, x"),
                     (86, 3050, "SUP2", "~D, DF, F, D, DF, F, x"),
                     (87, 3100, "SUP3", "~D, DF, F, D, DF, F, a")],
        # Air DP shares the grounded Psycho Sword states; the source CMD
        # routes both postures to the same statedef.
        "extra_cmds": [(49, "AIR_DP_X", "~F, D, DF, x", 4),
                       (58, "AIR_DP_Y", "~F, D, DF, y", 4)],
        "moves": {67: 250, 74: 800, 75: 800, 96: 750},
        "cfg": {
            # Athena's SFFv1 points the body cels at palette bank 1, a
            # dark-red dim copy; palette bank 0 carries the normal
            # blue/white costume colours.
            "palette_bank": 0,
            # AIR 1001 is an 8-frame orb (SFF group 7001).  Compile every
            # cel so the Psychic Ball animates instead of showing only the
            # first and last frames.
            "projectile_all_frames": True,
        },
    },
    "yuri": {
        # ohgaki's Yuri uses Neo-Geo button order: a=LP, x=HP, b=LK, y=HK.
        # Translate her command tokens to the pack's standard MUGEN meaning
        # (x=LP, y=HP, a=LK, b=HK) so the shared Y/X/B/A pad layout and the
        # ButtonTab/cancel logic work like every other fighter.  Keep the
        # source statedef numbers; only the token names are rewritten.
        "normals": {("s", "x"): 200, ("s", "y"): 202,
                    ("s", "a"): 204, ("s", "b"): 206,
                    ("c", "x"): 220, ("c", "y"): 221,
                    ("c", "a"): 222, ("c", "b"): 223,
                    ("a", "x"): 230, ("a", "y"): 231,
                    ("a", "a"): 232, ("a", "b"): 233},
        # The source cmd uses duplicated Japanese command names, helper
        # projectiles, and var(17) MAX expressions the generic matcher cannot
        # group.  These are the real reachable player states; chain states
        # (422/435/452 and the 512/513/514 super sequence) are wired through
        # "moves" so their ChangeStates compile into TransTab.
        # Command strings below are already translated to the pack's tokens.
        "specials": [(48, 400, "QCF_X", "~D, DF, F, x"),      # Ko-Ou-Ken
                     (49, 401, "QCF_Y", "~D, DF, F, y"),
                     (50, 410, "QCB_X", "~D, DB, B, x"),      # Saiha
                     (51, 411, "QCB_Y", "~D, DB, B, y"),
                     (52, 420, "HCB_A", "~F, DF, B, a"),      # Senkai Kyaku
                     (53, 421, "HCB_B", "~F, DF, B, b"),
                     (54, 430, "DP_A", "~F, D, DF, a"),       # Kuuga
                     (55, 431, "DP_B", "~F, D, DF, b"),
                     (56, 440, "HCF_A", "~B, DB, F, a"),      # throw
                     (57, 440, "HCF_B", "~B, DB, F, b"),
                     (58, 450, "AIR_QCF_A", "~D, DF, F, a", 4),
                     (59, 451, "AIR_QCF_B", "~D, DF, F, b", 4),
                     (74, 300, "THROW_Y", "/F, y"),
                     (75, 310, "THROW_B", "/F, b"),
                     (85, 500, "SUP1_X", "~F, B, DB, DF, F, x"),
                     (87, 501, "SUP1_Y", "~F, B, DB, DF, F, y"),
                     (86, 510, "SUP2_A", "~D, DF, F, DF, B, a"),
                     # 88/89 are reserved for MAX/SDM targets in the engine;
                     # use the last free special slot for Yuri's strong DM.
                     (66, 511, "SUP2_B", "~D, DF, F, DF, B, b")],
        "moves": {60: 422, 61: 435, 62: 452,
                  63: 512, 64: 513, 65: 514,
                  67: 210, 69: 252, 74: 300, 75: 310,
                  94: 251, 95: 250, 96: 700},
        "cfg": {
            # Helper states 405/406/415/417/455/456/505/506 carry the
            # projectile HitDefs.  The native engine has a spark-slot
            # projectile, not MUGEN helpers, so launch approximations at
            # state entry: Ko-Ou-Ken travels, Saiha stays put, air Ko-Ou-Ken
            # becomes a flat shot, and SUP1 is the fast super version.
            "projs": {48: (0x0300, 14, 4), 49: (0x0400, 18, 4),
                      50: (0x0000, 14, 4), 51: (0x0000, 18, 4),
                      58: (0x0400, 12, 4), 59: (0x0600, 16, 4),
                      85: (0x0500, 22, 4), 87: (0x0600, 24, 4)},
            # Use Yuri's blue costume palette for the SNES player-one look;
            # map the compact SFF color indices to its skin, blue cloth, and
            # trouser ramps.
            "msu": True,
            "palette_act": "assets/characters/Yuri/yuri05.act",
            "palette_index_map": {
                1: 254, 2: 254, 3: 252, 4: 252, 5: 250, 6: 250,
                7: 244, 8: 243, 9: 242, 10: 237,
                11: 244, 12: 244, 13: 243, 14: 242, 15: 241, 16: 240,
                18: 237, 19: 254, 20: 252, 21: 252, 22: 250, 23: 249,
                24: 236, 25: 235, 26: 235, 27: 234, 28: 233,
                29: 236, 30: 235, 31: 234, 32: 233, 33: 232,
                34: 236, 35: 234, 36: 232,
            },
            "palette_focus_actions": [0],
            # The Saiha fan shares the compact palette indices with the
            # body (12/13/15 are the fan's pale/white face, not the shoe
            # shading).  Map those three only for the fan cel so the fan
            # is white/pale instead of dark blue/black; the body keeps the
            # costume palette.
            "palette_sprite_map": {"410,7": {12: 237, 13: 249, 15: 237}},
            # The generated dissolve cel for the standing/crouching strong
            # punch lands on a blank/offset cel (one invisible frame).
            # Keep the source animation without that tween.
            "tween_skip_sids": [6, 20],
            "idle_frame_ticks": 10,
            # trans_rules cannot express the package's separate
            # `pos Y >=0` + `vel Y >=0` landing triggers, `movecontact`, or
            # `time>70&&animtime=0`; pin the reachable chains explicitly.
            "extra_trans": [(58, 62, 1, 0), (59, 62, 1, 0),
                            (86, 63, 3, 0), (66, 63, 3, 0),
                            (64, 65, 0, 0)],
        },
    },
    "billy": {
        # Source numbering interleaves the buttons: x=200/400/600 (LP),
        # a=210/410/610 (LK), y=220/420/620 (HP), b=230/430/630 (HK).
        "normals": {("s", "x"): 200, ("s", "y"): 220,
                    ("s", "a"): 210, ("s", "b"): 230,
                    ("c", "x"): 400, ("c", "y"): 420,
                    ("c", "a"): 410, ("c", "b"): 430,
                    ("a", "x"): 600, ("a", "y"): 620,
                    ("a", "a"): 610, ("a", "b"): 630},
        # qcb_a/qcb_b and dp_a are kicks; ltp_x is the light Three Part Cane
        # punch.  Keep the other source motions untouched.
        "specials": [(48, 1100, "QCB_A", "~D, DB, B, a"),      # Counter upper
                     (49, 1110, "QCB_B", "~D, DB, B, b"),
                     (50, 1500, "DP_X", "~F, D, DF, x"),       # SenpuuKon
                     (51, 1510, "DP_Y", "~F, D, DF, y"),
                     (52, 1300, "DP_A", "~F, D, DF, a"),       # Flying Cane
                     (54, 1600, "HCB_X", "~F, DF, D, DB, B, x"),
                     (56, 1700, "QCF_X", "~D, DF, F, x"),      # Three Part Cane
                     (85, 3000, "SUP1", "~D, F, B, x"),
                     (86, 3020, "SUP2", "~D, F, B, y"),
                     (87, 3100, "SUP3", "~D, DF, F, D, DF, F, a")],
        "moves": {74: 800, 75: 800},
    },
    "lucky": {
        # fastbreak/alleyhoop/bird end on a/b (kicks) in the source; keep the
        # simplified motions but put them on the kick buttons.
        "specials": [(48, 1000, "QCF_A", "~D, DF, F, a"),      # Cyclone Break
                     (49, 1010, "QCF_B", "~D, DF, F, b"),
                     (50, 1050, "DP_A", "~F, D, DF, a"),       # Death Bound
                     (51, 1060, "DP_B", "~F, D, DF, b"),
                     (52, 1250, "DP_X", "~F, D, DF, x"),
                     # The source's ~D,D,x "shoot" motion cannot be completed
                     # by the native release-element matcher; use the free DP+kick
                     # input so the basketball is reachable.
                     (66, 2099, "SHOOT", "~F, D, DF, a"),
                     (85, 3200, "SUP1_A", "~D, F, D, F, a"),
                     (86, 3300, "SUP2_B", "~D, F, D, F, b")],
        # The auto matcher took the close variants for y/a and aliased the
        # crouch/jump kicks.  Use the far-button states so all four normals
        # per posture are distinct animations.
        "normals": {("s", "x"): 200, ("s", "y"): 240,
                    ("s", "a"): 220, ("s", "b"): 260,
                    ("c", "x"): 400, ("c", "y"): 440,
                    ("c", "a"): 420, ("c", "b"): 460,
                    ("a", "x"): 600, ("a", "y"): 640,
                    ("a", "a"): 620, ("a", "b"): 660},
        # State 310 is the strong grab with its own 311 bind animation.  Both
        # buttons share it because the native engine has a single bind slot.
        "throws": [(310, "y", 20), (310, "b", 20)],
        "moves": {74: 310},
    },
    "geese": {
        # ReversalDef counter-grab (当て身投げ): states 1400/1401/1402
        # redirect the attacker to 1411/1421 and the actor to 1410/1420.
        # Engine runtime slots 99-102 drive the actor and held victim; the
        # victim rows default to the generic hit pose.
        "moves": {99: 1410, 100: 1411, 101: 1420, 102: 1421},
        "anims": {99: 1410, 101: 1420},
        # The held-victim rows (100/102) use the shared generic hit pose;
        # leaving them out keeps the runtime fallback (5000) in charge.
        "omit_anims": [100, 102],
    },
    "chunli": {
        "cfg": {
            # xi_chunli.sff has no usable palette for the body cels: the
            # shared banks are pink/gray ramps, and the real colors live in
            # the ACT files.  The converted art stores its colours in the
            # extended 241..255 bank in reverse order (the 25x25 icon uses
            # the same reversed layout), so reverse that bank onto ACT01's
            # 16-colour block (indices 14..0: blue/white/gold/skin) before
            # SNES quantization.
            "palette_act": "assets/characters/Chunli/xi_chunli01.act",
            "palette_index_map": {241: 14, 242: 13, 243: 12, 244: 11,
                                  245: 10, 246: 9, 247: 8, 248: 7,
                                  249: 6, 250: 5, 251: 4, 252: 3,
                                  253: 2, 254: 1, 255: 0},
        },
    },
    "vega": {
        # Vega routes attacks through helper vars, so automatic command
        # analysis cannot connect its states directly.
        # The SNES command matcher models a ~40<dir> charge prefix, so the
        # source's short holds become 40-tick charges.  Both the back charge
        # (Psycho Crusher / Knee Press) and the down charge (Devil Reverse /
        # Head Press) are supported; without `~40` the parser dropped these
        # rules and the moves never appeared in the command table.
        "specials": [(48, 1000, "CHARGE_BF_X", "~40B, F, x"),
                     (49, 1010, "CHARGE_BF_Y", "~40B, F, y"),
                     (50, 1100, "CHARGE_BF_A", "~40B, F, a"),
                     (51, 1110, "CHARGE_BF_B", "~40B, F, b"),
                     (52, 1200, "CHARGE_DU_X", "~40D, U, x"),
                     (53, 1200, "CHARGE_DU_Y", "~40D, U, y"),
                     (54, 1300, "CHARGE_DU_A", "~40D, U, a"),
                     (55, 1300, "CHARGE_DU_B", "~40D, U, b"),
                     (56, 1400, "QCF_XY", "~D, DF, F, x+y"),
                     (57, 1410, "QCF_AB", "~D, DF, F, a+b"),
                     (58, 1420, "QCB_XY", "~D, DB, B, x+y"),
                     (59, 1430, "QCB_AB", "~D, DB, B, a+b"),
                     (85, 3000, "SUPER_4646_X", "~40B, F, B, F, x"),
                     (86, 3100, "SUPER_4646_A", "~40B, F, B, F, a"),
                     (87, 3050, "MAX_4646_XY", "~40B, F, B, F, x+y"),
                     (88, 3150, "MAX_4646_AB", "~40B, F, B, F, a+b")],
        # Players normally hit the final direction and button on the same
        # tick.  The native matcher consumes direction and button as separate
        # entries, so register the simultaneous forms as alternate motions.
        # Follow-up states: the root specials only show the startup pose.
        # 1001/1011 are the Psycho Crusher hit phases, 1201/1205 the Devil
        # Reverse rise/attack, 1301 the Head Press hit and 3001 the Mega
        # Psycho Crusher hit.  1202 is the shared landing recovery.
        "moves": {60: 1201, 61: 1001, 62: 1301, 63: 1011,
                  64: 1202, 66: 3001, 68: 1205, 107: 3055, 109: 3052},
        "cfg": {"invisible_anim_donor": {107: 66},
                "cmd_categories": {58: 2},
                "cmd_labels": {56: "VEGA WARP F P", 57: "VEGA WARP F K",
                               58: "VEGA WARP B P", 59: "VEGA WARP B K",
                               85: "MEGA PSYCHO CRU", 86: "KNEE PRESS NIGHT",
                               87: "FINAL PSYCHO CRU", 88: "MAX KNEE NIGHT"}},
        "extra_cmds": [(48, "CHARGE_BF_X2", "~40B, F+x", 1),
                       (49, "CHARGE_BF_Y2", "~40B, F+y", 1),
                       (50, "CHARGE_BF_A2", "~40B, F+a", 1),
                       (51, "CHARGE_BF_B2", "~40B, F+b", 1),
                       (52, "CHARGE_DU_X2", "~40D, U+x", 1),
                       (53, "CHARGE_DU_Y2", "~40D, U+y", 1),
                       (54, "CHARGE_DU_A2", "~40D, U+a", 1),
                       (55, "CHARGE_DU_B2", "~40D, U+b", 1),
                       (85, "SUPER_4646_X2", "~40B, F, B, F+x", 1),
                       (86, "SUPER_4646_A2", "~40B, F, B, F+a", 1),
                       (87, "MAX_4646_XY2", "~40B, F, B, F+x+y", 1),
                       (88, "MAX_4646_AB2", "~40B, F, B, F+a+b", 1)],
    },
    "ryu": {
        # Six super inputs share two motions, and the source triggers them
        # through Helper(99999) flags that the auto extractor cannot see.
        # 85/86 keep the Shinku Hadouken pair (QCFx2 + P), 87 is the Shinku
        # Tatsumaki (QCBx2 + K) and 88 is the MAX hadouken (QCFx2 + P+P,
        # which the engine already gates to the MAX window).
        "moves": {87: 3200, 88: 3050},
        # The source header writes the intro as "0 + (var(7) = 1);191",
        # which the statedef parser reads as anim 0 (stand).  The real
        # entrance is action 191, as the later ChangeAnim controller uses.
        "anims": {88: 3000, 92: 191},
        "specials": [(87, 3200, "MDBDB_db+a", "~D, DB, B, D, DB, B, a")],
        "extra_cmds": [(87, "MDBDB_db+b", "~D, DB, B, D, DB, B, b", 1),
                       (87, "MDBDB_db+ab", "~D, DB, B, D, DB, B, a+b", 1),
                       (88, "MDFDF_df+xy", "~D, DF, F, D, DF, F, x+y", 1)],
        "cmd_frames": {"MDFDF": 30, "MDBDB": 30},
        "cfg": {"cmd_frames": {"MDFDF": 30, "MDBDB": 30}},
    },
    "sakura": {
        # The DP (Shou'ou Ken) lands into state 1105, a recovery crouch that
        # then returns to stand on AnimTime=0.  The auto-wiring only knows
        # the attack states 1100/1110, so the landing ChangeState was dropped
        # and the fighter stayed on its air pose until the generic fallback.
        # Give 1105 the first free fast-special sid so the TransTab carries
        # the land->1105 and 1105->stand rows.
        # Sakura Otoshi (1300/1310) and the hurricane kicks (1200/1210) have
        # the same problem: their landing/recovery states were never wired,
        # so the air pose held until the generic fallback (1300's AIR ends on
        # a t=-1 hold, which the runtime plays as 255 ticks).  Wire those
        # recovery states to the remaining free fast-special sids.
        "moves": {56: 1105, 57: 1305, 58: 1201, 59: 1211},
        "anims": {56: 1105, 57: 1305, 58: 1201, 59: 1211},
    },

    "ryo": {
        # The source CMD picks the strong Ko'ou Ken with
        # `value = 1010 + ((var(10) = 1) * 50)`.  The generic extractor drops
        # that expression, so only the weak QCF+P shot was wired and QCF+strong
        # fell through to the stand strong punch.  Wire state 1010 to a free
        # special slot and give its pooled shot the usual strong-shot speed
        # and damage (the source helper picks 5 px/tick and 21 damage).
        "specials": [(61, 1010, "QCF_Y", "~D, DF, F, y")],
        "cfg": {"projs": {61: (1280, 18, 4)}},
    },

    "robert": {
        # Same var(10) strong-shot expression as Ryo: the extractor drops
        # state 1010, so QCF+strong was falling through to the normal punch.
        "specials": [(59, 1010, "QCF_Y", "~D, DF, F, y")],
        "cfg": {"projs": {58: (1024, 18, 4),
                          59: (1536, 22, 4),
                          85: (1024, 24, 4),
                          86: (1792, 30, 4)}},
        # The source CNS fires projanim 1003/1004, but this SFF has no
        # such AIR actions.  The visible Ryugeki fireball is SFF group
        # 1055 (six shrinking cels); synthesize it as AIR 1055.
        "projectile_air": {1055: [(1055, 0, 4), (1055, 1, 4),
                                  (1055, 2, 4), (1055, 3, 4),
                                  (1055, 4, 4), (1055, 5, 4)]},
        "projectile_all_frames": True,
    },
    # The next four imports use standard x/y=punch, a/b=kick tokens but
    # non-standard statedef numbering (the hard punch/kick states are
    # interleaved).  The generic matcher assumed 200/210/230/240, so pin the
    # four buttons of every posture to their real source states.
    "kensou": {
        "normals": {("s", "x"): 200, ("s", "y"): 240,
                    ("s", "a"): 230, ("s", "b"): 260,
                    ("c", "x"): 400, ("c", "y"): 440,
                    ("c", "a"): 420, ("c", "b"): 460,
                    ("a", "x"): 600, ("a", "y"): 640,
                    ("a", "a"): 630, ("a", "b"): 660},
    },
    "mai": {
        # Mai's source keeps close/far variants; use the far/neutral states
        # for the single native slot.  200/210/220/230 etc. are already in
        # punch/punch/kick/kick order.
        "normals": {("s", "x"): 200, ("s", "y"): 210,
                    ("s", "a"): 220, ("s", "b"): 230,
                    ("c", "x"): 400, ("c", "y"): 410,
                    ("c", "a"): 420, ("c", "b"): 430,
                    ("a", "x"): 600, ("a", "y"): 610,
                    ("a", "a"): 620, ("a", "b"): 630},
    },
    "shermie": {
        "normals": {("s", "x"): 200, ("s", "y"): 240,
                    ("s", "a"): 220, ("s", "b"): 260,
                    ("c", "x"): 400, ("c", "y"): 440,
                    ("c", "a"): 420, ("c", "b"): 460,
                    ("a", "x"): 600, ("a", "y"): 640,
                    ("a", "a"): 620, ("a", "b"): 660},
    },
    "chris": {
        "normals": {("s", "x"): 200, ("s", "y"): 240,
                    ("s", "a"): 220, ("s", "b"): 260,
                    ("c", "x"): 400, ("c", "y"): 440,
                    ("c", "a"): 420, ("c", "b"): 460,
                    ("a", "x"): 600, ("a", "y"): 640,
                    ("a", "a"): 630, ("a", "b"): 660},
    },
    "omega": {
        # Real Omega Rugal from assets/characters/omegarugal98.  The
        # auto-extractor only saw 7 specials/1 super because the source uses
        # unnamed [State -1] blocks; these are the 24 wired moves.
        "specials": [
            (48, 1000, "dark_a", "~F, D, DF, a"),
            (49, 1005, "dark_b", "~F, D, DF, b"),
            (50, 1020, "BR1", "~F, D, B, x"),
            (51, 1025, "BR2", "~F, D, B, y"),
            (52, 1040, "gravity1", "~D, DF, F, x"),
            (53, 1045, "gravity2", "~D, DF, F, y"),
            (54, 2000, "balia", "~D, DF, F, a"),
            (55, 2002, "balia2", "~D, DF, F, b"),
            (56, 2700, "impact", "~D, DB, B, b"),
            (57, 2899, "striker", "~D, DF, F, s"),
            (58, 7200, "tamtam", "~D, DB, B, s"),
            (59, 1070, "press", "~D, F, D, B, x"),
            (60, 1085, "press2", "~D, F, D, B, y"),
            (61, 1090, "pressmax", "~D, F, D, B, z"),
            (62, 2100, "omega", "~D, F, D, F,b"),
            (63, 2200, "omegamax", "~D, F, D, F,a+b"),
            (64, 2300, "RE", "~D, F, D, F,x"),
            (65, 2400, "REMAX", "~D, F, D, F,x+y"),
            (66, 2600, "rashomon", "~D, B, D, F,a"),
            (85, 2800, "misogi", "~F, D, B, F, D, B, b"),
            (86, 3000, "mu", "~D, B, D, B,y"),
            (87, 6000, "jibaku", "~F, B, F, B, D, F, x+y"),
            (88, 7000, "ude", "~D, F, DF,x+y"),
            (89, 8100, "gia", "~F, B, D, F, y"),
        ],
        # The source's DP motion does not complete in the native matcher;
        # keep the official command and add a working QCB alias.  The long
        # supers get F-prefixed QCFx2 aliases (jibaku works; gia/ude remain
        # MAX-only SDM input experiments).
        "extra_cmds": [
            (48, "dark_a_alt", "~D, DB, B, a", 1),
            (49, "dark_b_alt", "~D, DB, B, y", 1),
            (87, "jibaku_alt", "F, D, DF, F, D, DF, F, b", 1),
            (88, "ude_alt", "F, D, DF, F, D, DF, F, a", 1),
            (89, "gia_alt", "F, D, DF, F, D, DF, F, y", 1),
        ],
        "cfg": {
            "msu": False,                 # ROM-resident hidden boss
            "damage_scale": 0.36,         # source uses the ~1000-HP scale
            "projs": {48: (51, 6, 4), 49: (77, 6, 4),
                      52: (998, 10, 4), 53: (1638, 12, 4),
                      57: (1792, 10, 4), 62: (77, 12, 4),
                      63: (77, 18, 4), 88: (256, 10, 4)},
        },
    },
}

# sel-id order after the existing 15 (0..13 + hidden OmegaRugal=14).
ROSTER = [
    ("terry",    "Terry-KOF98",    "Terry-KOF98.def",    "TERRY"),
    ("andy",     "Andy-KOF98",     "Andy-KOF98.def",     "ANDY"),
    ("joe",      "Joe-KOF98",      "Joe-KOF98.def",      "JOE"),
    ("ryo",      "Ryo-KOF98",      "Ryo-KOF98.def",      "RYO"),
    ("robert",   "Robert-KOF98",   "Robert-KOF98.def",   "ROBERT"),
    ("yuri",     "Yuri",           "!yuri.def",          "YURI"),
    ("athena",   "Athena-98",      "Athena-98.def",      "ATHENA"),
    ("kensou",   "Kensou",         "kensou.def",         "KENSOU"),
    ("chin",     "chin-kofa",      "chin-kofa.def",      "CHIN"),
    ("king",     "KING",           "KING.def",           "KING"),
    ("mai",      "Mai-KOF98",      "K_Mai.def",          "MAI"),
    ("chizuru",  "CHIZURU",        "CHIZURU.def",        "CHIZURU"),
    ("kim",      "Kim-KOF98",      "Kim-KOF98.def",      "KIM"),
    ("chang",    "chang-kofa",     "chang-kofa.def",     "CHANG"),
    ("choi",     "choi-kofa",      "choi-kofa.def",      "CHOI"),
    ("yashiro",  "Yashiro-KOF98",  "Yashiro-KOF98.def",  "YASHIRO"),
    ("shermie",  "Shermie-KOF98",  "shermie.def",        "SHERMIE"),
    ("chris",    "Chris-KOF98",    "chris.def",          "CHRIS"),
    ("yamazaki", "Yamazaki-KOF98", "Yamazaki-KOF98.def", "YAMAZAKI"),
    ("mary",     "bluemary-kofa",  "bluemary-kofa.def",  "MARY"),
    ("billy",    "BILLY",          "BILLY.DEF",          "BILLY"),
    ("lucky",    "LUCKY",          "LUCKY.def",          "LUCKY"),
    ("heavyd",   "heavy-d-kofa",   "heavy-d-kofa.def",   "HEAVY-D"),
    ("brian",    "BRIAN",          "BRIAN.def",          "BRIAN"),
    ("geese",    "Geese-KOF98",    "Geese-KOF98.def",    "GEESE"),
    ("krauser",  "Krauser-KOF98",  "Krauser-KOF98.def",  "KRAUSER"),
    ("mrbig",    "MrBig-KOF98",    "MrBig-KOF98.def",    "MR.BIG"),
    ("eiji",     "Eiji-KOF98",     "Eiji-KOF98.def",     "EIJI"),
    ("vega",     "Vega-KOF98",     "Vega-KOF98.def",     "M.BISON"),
    ("ryu",      "Ryu-KOF98",      "Ryu-KOF98.def",      "RYU"),
    ("ken",      "Ken-KOF98",      "Ken-KOF98.def",      "KEN"),
    ("chunli",   "Chunli",         "Chunli.def",         "CHUN-LI"),
    ("sakura",   "Sakura-KOF98",   "Sakura-KOF98.def",   "SAKURA"),
]

BUTTONS = {"x": 0x4000, "y": 0x0040, "a": 0x8000, "b": 0x0080,
           "c": 0x0020, "z": 0x0010}

# base sids whose anim is a fixed mugen system state/anim number.
BASE_STATE = {
    0: 0, 1: 20, 2: 21, 3: 11, 4: 41,
    9: 5000, 10: 5050, 11: 5300, 12: 10, 13: 12, 14: 40, 15: 42,
    16: 43, 17: 47, 18: 5120,
    27: 130, 28: 131, 29: 132, 30: 150, 42: 150, 43: 151, 44: 152,
    31: 5000, 32: 5000, 33: 5000,
    34: 5010, 35: 5010, 36: 5010,
    37: 5020, 38: 5020, 39: 5020,
    40: 5030, 41: 5110, 93: 5070,
    70: 5020, 71: 5030, 72: 5050, 73: 5050,
    78: 720, 79: 720, 80: 720, 81: 720, 82: 720, 83: 720, 84: 47,
    90: 181, 91: 170, 92: 191,
}
BASE_MOVES = {90: 181, 91: 170, 92: 191, 76: 5000, 77: 5050}

# canonical ikaruga statedef numbers for the system slots.
SYS_STATE = {45: 100, 46: 105, 47: 160, 67: 250, 69: 720,
             94: 710, 95: 700, 96: 750, 97: 760, 74: 800, 75: 800}

# Per-character native system states:
#   (forward evade, backward evade, neutral dodge, blowback)
# The standard KOF98 pack uses 700/710/720/250, but custom imports keep
# the author's own numbering -- several reuse 700/710/720 for unrelated
# moves (power charge, specials), so these slots must not be inferred.
DEFAULT_SYS_STATES = (700, 710, 720, 250)
SYS_STATES = {
    "yuri":    (250, 251, 252, 210),
    "athena":  (700, 710, None, 300),   # ふっとばし = 300
    "kensou":  (750, 775, 725, 280),    # 700/710 = power charge
    "chin":    (700, 710, None, 900),   # ふっとばし = 900
    "king":    (4050, 4150, None, 600),  # 700/710 = trap/slide attacks
    "mai":     (710, 711, None, 240),   # 250 = Benitsuru no Mai
    "chizuru": (None, None, None, 240),  # no evades in the source at all
    "chang":   (900, 910, None, 940),
    "choi":    (4000, 4010, None, 500),
    "shermie": (750, 775, 725, 280),    # 700/710 = power charge
    "chris":   (750, 775, 725, 280),    # 700/710 = power charge
    "mary":    (260, 265, 250, 243),    # 250 = DODGE, 243 = CD attack
    "billy":   (250, 260, 251, 240),
    "lucky":   (700, 701, 702, 280),    # 710 = roll counter, 250 = punch
    "heavyd":  (700, 701, None, 990),
    "brian":   (900, 910, None, 240),   # 700/710 = MAX mode
    "chunli":  (900, 905, None, 910),   # 700/710/720 = SF specials
}

# Fallback animations for slots the source does not implement.  The state
# number becomes a synthetic (unused) id so each slot still has its own
# command rule; the engine only needs the anim and the sid handler.
SYS_ANIM_FALLBACK = {
    "chizuru": {95: 100, 94: 105, 69: 100},  # run / back hop / run
}
# english -1 names that pin down a slot (fallback for non-ikaruga cmds)
SYS_NAMES = {
    "taunt": 47, "power charge": 97,
    "throw": 74, "blowback attack": 67, "blowback attack ground": 67,
    "dash": 45, "run": 45, "fwd dash": 45, "back step": 46,
    "backdash": 46, "max発動": 96,
}

BASE_CMDS = [
    ("FF", "F, F", 10), ("BB", "B, B", 10),
    ("ESQ_L", "c", 4),
    ("ESQ_F", "/F, c", 8),
    ("ESQ_B", "/B, c", 8),
    ("CD", "y+b", 15), ("DODGE", "x+a", 15),
    ("CHARGE", "x+y+a+z", 6), ("MAX_ON", "x+y+a", 6),
    ("recovery", "x+a", 0),
    ("x", "x", 1), ("y", "y", 1), ("z", "z", 1),
    ("a", "a", 1), ("b", "b", 1), ("c", "c", 1),
    ("start", "s", 1),
    ("holdfwd", "/$F", 0), ("holdback", "/$B", 0),
    ("holdup", "/$U", 0), ("holddown", "/$D", 0),
    ("down_a", "/$D,a", 1), ("down_b", "/$D,b", 1),
    ("fwd", "F", 0), ("back", "B", 0), ("up", "U", 0), ("down", "D", 0),
]

BTN_ORDER = {"x": 0, "y": 1, "a": 2, "b": 3}
WEAK_BTNS = ("x", "a")
STRONG_BTNS = ("y", "b")

# standard KOF statedef numbering for normals (ikaruga + most others).
STD_NORMALS = {
    "s": {"x": 200, "y": 210, "a": 230, "b": 240},
    "c": {"x": 400, "y": 410, "a": 430, "b": 440},
    "a": {"x": 600, "y": 610, "a": 630, "b": 640},
}


def read_text(path):
    return open(path, "rb").read().decode("shift_jis", errors="replace")


def read_def(path):
    slots = {}
    txt = read_text(path)
    for line in txt.splitlines():
        m = re.match(r"\s*([A-Za-z0-9]+)\s*=\s*(.+?)\s*$", line)
        if m and not line.lstrip().startswith("["):
            slots[m.group(1).upper()] = m.group(2).split(";")[0].strip()
    m = re.search(r"localcoord\s*=\s*(\d+)", txt, re.I)
    return slots, (int(m.group(1)) if m else 320)


def find_state_file(cdir, fn):
    for cand in (cdir, KOF98DATA):
        p = os.path.join(cand, fn)
        if os.path.exists(p):
            return p
    return None


def merge_cns(cdir, slots, base):
    order = ["ST"] + [f"ST{i}" for i in range(1, 10)] + ["CNS", "STCOMMON"]
    seen, files = set(), []
    for k in order:
        fn = slots.get(k)
        if fn and fn.lower() not in seen:
            seen.add(fn.lower())
            files.append(fn)
    out = ["; Merged/sanitized CNS for the SNES port (generated)\n",
           "; Sources (precedence order): " + ", ".join(files) + "\n\n"]
    st0 = slots.get("ST")
    if st0:
        p = find_state_file(cdir, st0)
        if p:
            m = re.search(r"\[Quotes\](.*?)(?=\n\[|\Z)",
                          read_text(p), re.S | re.I)
            if m:
                out.append("[Quotes]\n" + m.group(1).strip() + "\n\n\n")
    for fn in files:
        p = find_state_file(cdir, fn)
        if not p:
            print(f"  !! missing state file {fn}")
            continue
        out.append(f"; ===== from {fn} =====\n\n"
                   + read_text(p).strip() + "\n\n")
    dest = os.path.join(cdir, f"{base}_SNES.cns")
    open(dest, "w", encoding="utf-8").write("".join(out))
    return "".join(out), f"{base}_SNES.cns"


def clone_states(txt, clones):
    """Duplicate a statedef block with a fixed `anim` header.

    Several KOF packages (Chizuru, Lucky) choose a normal's animation with
    a ChangeAnim keyed on the button command.  The native engine binds one
    animation per sid, so copy the attack state once per button and force
    the header anim.  HitDef/PosAdd/PlaySnd controllers stay intact for the
    compiler; the per-sid hit row is selected in build_fight.py.
    """
    for src, dst, anim in clones:
        m = re.search(r"(?mi)^\[statedef\s+%d\]\s*$" % src, txt)
        if not m:
            print(f"  !! clone_states: missing statedef {src}")
            continue
        nxt = re.search(r"(?mi)^\[statedef\s+", txt[m.end():])
        end = m.end() + nxt.start() if nxt else len(txt)
        block = txt[m.start():end]
        block = re.sub(r"(?mi)^\[statedef\s+%d\]" % src,
                       f"[Statedef {dst}]", block, count=1)
        # The header anim is the one before the first controller.  Replacing
        # the first `anim =` line is safe for these sources (ChangeState uses
        # `value =`, not `anim =`).
        if re.search(r"(?mi)^\s*anim\s*=", block):
            block = re.sub(r"(?mi)^\s*anim\s*=.*$",
                           f"anim = {anim}", block, count=1)
        else:
            sm = re.search(r"(?mi)^\[state\s", block)
            if sm:
                block = block[:sm.start()] + f"anim = {anim}\n" + block[sm.start():]
            else:
                block = block.rstrip() + f"\nanim = {anim}\n"
        txt = txt.rstrip() + "\n\n" + block.strip() + "\n"
    return txt


def parse_statedefs(txt):
    out = {}
    cur = None
    for raw in txt.splitlines():
        line = raw.split(";", 1)[0].strip()
        # some sources annotate the header ("[Statedef 710, Roll]")
        m = re.match(r"\[statedef\s+(-?\d+)\s*(?:,[^\]]*)?\]", line, re.I)
        if m:
            cur = int(m.group(1))
            out.setdefault(cur, {"anim": None, "type": None,
                                 "movetype": None, "hitdef": 0})
            continue
        if line.startswith("["):
            cur = None
            continue
        if cur is None or "=" not in line:
            continue
        k, v = (p.strip() for p in line.split("=", 1))
        k = k.lower()
        if k == "anim" and out[cur]["anim"] is None:
            m2 = re.match(r"-?\d+", v)
            if m2:
                out[cur]["anim"] = int(m2.group(0))
        elif k == "type":
            out[cur]["type"] = v.lower()
        elif k == "movetype":
            out[cur]["movetype"] = v.lower()
        elif k == "hitdef":
            out[cur]["hitdef"] += 1
    return out


def parse_air_ids(path):
    txt = open(path, encoding="utf-8-sig", errors="replace").read()
    return {int(n) for n in re.findall(r"\[begin\s+action\s+(\d+)\s*\]", txt, re.I)}


def synth_air(cdir, sff_name, dest_name):
    """kensou/shermie/chris ship a 1-action .air stub.  Their sff sprites
    are grouped by anim number, so rebuild a minimal .air: one action per
    group, 8 ticks per frame, full-sprite body box + attack box."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sff import Sff
    s = Sff(os.path.join(cdir, sff_name))
    groups = {}
    for sp in s.sprites:
        groups.setdefault(sp.group, []).append(sp)
    out = ["; synthetic air rebuilt from sff sprite groups\n",
           "; (source .air was a 1-action stub)\n\n"]
    # base anims the engine expects; alias missing groups to the closest
    # existing one so table fills (e.g. AnimTab sid 47) never dangle.
    ALIAS_SRC = [47, 160, 195, 12, 43, 130, 131, 132, 150, 151, 152,
                 5050, 5110, 5120]
    stand = groups.get(0) or next(iter(groups.values()))
    for g in ALIAS_SRC:
        if g not in groups:
            groups[g] = stand
    for g in sorted(groups):
        out.append(f"[Begin Action {g}]\n")
        out.append("Clsn2Default: 1\n")
        gmax = groups[g]
        x1 = min(-sp.ax for sp in gmax)
        y1 = min(-sp.ay for sp in gmax)
        x2 = max(sp.w - sp.ax for sp in gmax)
        y2 = max(sp.h - sp.ay for sp in gmax)
        out.append(f" Clsn2[0] = {x1}, {y1}, {x2}, {y2}\n")
        out.append("Clsn1Default: 1\n")
        out.append(f" Clsn1[0] = {x1}, {y1}, {x2}, {y2}\n")
        for sp in gmax:
            out.append(f"{sp.group}, {sp.number}, 0, 0, 8\n")
        out.append("\n")
    path = os.path.join(cdir, dest_name)
    open(path, "w", encoding="utf-8").write("".join(out))
    return dest_name


def parse_cmdfile(path):
    """-> (cmds {name: [motion,...]}, entries [{name,value,cmds,st,trg}])."""
    txt = read_text(path)
    cmds, entries = {}, []
    cur_cmd = cur = None
    for raw in txt.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if re.match(r"\[command\]", line, re.I):
            cur = None
            cur_cmd = {}
            continue
        m = re.match(r"\[state(?:def)?\s+-1\s*,?\s*(.*?)\]", line, re.I)
        if m:
            cur = {"name": m.group(1).strip(), "triggers": []}
            entries.append(cur)
            cur_cmd = None
            continue
        if line.startswith("["):
            cur = cur_cmd = None
            continue
        if cur_cmd is not None and "=" in line:
            k, v = (p.strip() for p in line.split("=", 1))
            cur_cmd[k.lower()] = v
            if k.lower() == "command" and "name" in cur_cmd:
                cmds.setdefault(cur_cmd["name"].strip('"'), []).append(v)
            continue
        if cur is None or "=" not in line:
            continue
        k, v = (p.strip() for p in line.split("=", 1))
        k = k.lower()
        cur[k] = v
        if k.startswith("trigger"):
            cur["triggers"].append(v)
    for e in entries:
        e["cmds"] = set()
        st = 0
        for t in e["triggers"]:
            e["cmds"].update(re.findall(r'command\s*=\s*"([^"]+)"', t))
            for op, s in re.findall(r'statetype\s*(!=|=)\s*([SCA])\b', t):
                bit = {"s": 1, "c": 2, "a": 4}[s.lower()]
                st |= bit if op == "=" else (7 & ~bit)
        e["st"] = st
        try:
            e["value_i"] = int(float(e.get("value", "-1").split(",", 1)[0]))
        except ValueError:
            e["value_i"] = -1
    return cmds, entries


def motion_elems(motion):
    """motion str -> (ok, elems[(dir,btn,rel)], held)."""
    elems, held, ok = [], 0, True
    for token in motion.split(","):
        token = token.strip()
        rel = False
        if token.startswith("~") and not token[1:2].isdigit():
            token = token[1:]
            rel = True
        if not token or token.startswith((">", "/", "$")) \
                or token[0].isdigit() or "~" in token:
            if token.startswith(("/", "$")):
                held += 1
                continue
            ok = False
            break
        d = b = ""
        for part in token.split("+"):
            part = part.strip()
            if part == "B" or part in "UuDdFf":
                d += part.upper()
            else:
                b += part.lower()
        if not (d or b):
            ok = False
            break
        elems.append((d, b, rel))
    return ok, elems, held


def canon_name(elems):
    names = {"D,DF,F": "QCF", "D,DB,B": "QCB", "F,D,DF": "DP",
             "B,D,DB": "RDP", "B,DB,D,DF,F": "HCF", "F,DF,D,DB,B": "HCB",
             "B,DB,D,DF,F,B": "HCBF", "D,B,F": "DBF",
             "D,DF,F,D,DF,F": "QQCF", "D,DB,B,D,DB,B": "QQCB",
             "D,DB,B,DB,D,DF,F": "QCBHCF", "D,DF,B,DF,D,DB,B": "QCFHCB",
             "F,DF,D,DB,B,F,DF,D,DB,B": "HCBHCB",
             "B,DB,D,DF,F,B,DB,D,DF,F": "HCFHCF",
             "F,DF,D,DB,B,F": "HCBF2", "F,B,F": "FBF",
             "D,F,B": "DFB", "D,F": "DF", "F,F": "FF", "B,B": "BB",
             "U": "U", "D": "D", "F": "F", "B": "B"}
    dirs = ",".join(d for d, b, r in elems if d and not b)
    btns = "+".join(sorted({b for d, b, r in elems if b}) or [""])
    base = names.get(dirs)
    if base is None:
        base = "M" + re.sub(r"[^A-Z]", "", dirs.title().replace(",", ""))
    return f"{base}_{btns}" if btns else base


def btn_of(elems):
    if elems and not elems[-1][0] and elems[-1][1]:
        return elems[-1][1]
    return None


# JP name prefixes -> strength tag
JP_WEAK = "弱"
JP_STRONG = "強"
JP_MAX = "MAX"


def norm_name(name):
    """strip weak/strong/max markers so move pairs group together."""
    n = name.strip()
    n = re.sub(r"^(弱|強)\s*[／/]?\s*(弱|強)?\s*", "", n)
    n = re.sub(r"^(MAX|max)\s*", "", n)
    n = re.sub(r"[（(].*$", "", n)          # (裏)/(MOW) variants
    return n.strip()


def gen_char(key, cdir_name, defname, display):
    calibration_name, calibration = input_calibration(key)
    cdir = os.path.join(CHARS_DIR, cdir_name)
    deffile = os.path.join(cdir, defname)
    if not os.path.exists(deffile):
        cands = [f for f in os.listdir(cdir) if f.lower().endswith(".def")]
        deffile = os.path.join(cdir, cands[0])
        defname = cands[0]
        print(f"{key}: def fallback -> {defname}")
    slots, localcoord = read_def(deffile)
    base = key.capitalize() if len(key) <= 7 else key[:8].capitalize()

    merged, cns_name = merge_cns(cdir, slots, base)
    if ov_clones := OVERRIDES.get(key, {}).get("clone_states"):
        merged = clone_states(merged, ov_clones)
        open(os.path.join(cdir, cns_name), "w", encoding="utf-8").write(merged)
    stdefs = parse_statedefs(merged)
    moves = dict(BASE_MOVES)

    cmds, entries = parse_cmdfile(
        find_state_file(cdir, slots["CMD"]) or os.path.join(cdir,
                                                           slots["CMD"]))
    air_file = slots["ANIM"]
    air_path = os.path.join(cdir, air_file)
    air_ids = parse_air_ids(air_path)
    if len(air_ids) < 30:                     # stub .air -> rebuild from sff
        air_file = synth_air(cdir, slots["SPRITE"],
                             f"{base}_gen.air")
        air_ids = parse_air_ids(os.path.join(cdir, air_file))
        print(f"{key}: synthesized {air_file} "
              f"({len(air_ids)} actions from sff groups)")
    sff_rel = f"{cdir_name}/{slots['SPRITE']}"
    air_rel = f"{cdir_name}/{air_file}"

    def resolve(cname):
        for m in cmds.get(cname, []):
            ok, elems, held = motion_elems(m)
            if ok:
                return m, elems, held
        return None, None, None

    wired = {}            # sid -> mugen statedef
    spec_motion = {}      # sid -> (canon, motion str, posture)
    used_cmds = {}        # canon -> motion str
    ov = OVERRIDES.get(key, {})

    def wire(sid, state):
        if state is None or state < 0:
            return False
        wired[sid] = state
        moves[sid] = state
        return True

    def wire_motion(sid, state, motion_str, posture):
        if not wire(sid, state):
            return False
        ok, elems, _held = motion_elems(motion_str)
        cn = canon_name(elems)
        spec_motion[sid] = (cn, motion_str, posture)
        used_cmds.setdefault(cn, motion_str)
        return True

    def exists(state):
        return state in stdefs

    # ---- normals ---------------------------------------------------------
    # ikaruga/most chars: standard statedef numbers.  Check candidates in
    # order and fall back to -1-name matching for exotic layouts.
    NORM_NAMES = {
        "x": re.compile(r"light punch|jab|弱.*パンチ|パンチ.*弱", re.I),
        "y": re.compile(r"strong punch|heavy punch|強.*パンチ|パンチ.*強",
                        re.I),
        "a": re.compile(r"light kick|弱.*キック|キック.*弱", re.I),
        "b": re.compile(r"strong kick|heavy kick|強.*キック|キック.*強",
                        re.I),
    }
    normals = {}
    for posture, btns in STD_NORMALS.items():
        for btn, state in btns.items():
            cand = [state, state + 5, state + 10, state - 5]
            hit = next((c for c in cand if exists(c)
                        and stdefs[c].get("movetype") in (None, "a")), None)
            if hit is not None:
                normals[(posture, btn)] = hit
    # name matching fills gaps.  Posture comes from the entry name first
    # (stand/crouch/air wording), then statetype bits; a ground entry
    # (statetype != A) never fills a crouch slot.
    def norm_posture(e):
        nm = e["name"].lower()
        if "crouch" in nm or "しゃが" in nm:
            return {"c"}
        if "jump" in nm or "air " in nm or "空中" in nm:
            return {"a"}
        if "stand" in nm or "立ち" in nm or "近距離" in nm or "遠距離" in nm:
            return {"s"}
        st = e["st"]
        if st == 0 or st == 3:      # no flag / ground -> prefer stand
            return {"s"}
        if st == 1:
            return {"s"}
        if st == 2:
            return {"c"}
        if st == 4:
            return {"a"}
        return set()

    for e in entries:
        if e.get("type", "").lower() != "changestate" or e["value_i"] < 0 \
                or e["value_i"] >= 2000:
            continue
        nm = e["name"].lower()
        posts = norm_posture(e)
        for btn, rx in NORM_NAMES.items():
            if not rx.search(nm):
                continue
            for posture in posts:
                nkey = (posture, btn)
                if nkey not in normals:
                    normals[nkey] = e["value_i"]

    normals.update(ov.get("normals", {}))
    sid_map = {"s": 5, "c": 19, "a": 23}
    for (posture, btn), state in sorted(normals.items()):
        wire(sid_map[posture] + BTN_ORDER[btn], state)

    # ---- system states ---------------------------------------------------
    # Explicit per-character wiring comes first: the generic name/command
    # inference below cannot tell a real evade from a move that happens to
    # use one of the canonical numbers.
    sys_fwd, sys_back, sys_neutral, sys_blow = SYS_STATES.get(
        key, DEFAULT_SYS_STATES)
    virtual_anims = {}

    def native_anim(state, default):
        for cand in (stdefs.get(state, {}).get("anim"), state, default,
                     47, 0):
            if cand in air_ids:
                return cand
        return 0

    def wire_sys(sid, state, fallback_anim=None):
        """Wire a system slot, synthesising an id+anim when the source
        has no native state for it (e.g. Chizuru ships no evades)."""
        if state is not None and state >= 0 and exists(state):
            wire(sid, state)
            return True
        if fallback_anim is None:
            return False
        phantom = 19900 + sid
        used = set(stdefs) | set(moves.values())
        while phantom in used:
            phantom += 100
        wire(sid, phantom)
        virtual_anims[sid] = fallback_anim
        return True

    anim_fb = SYS_ANIM_FALLBACK.get(key, {})
    wire_sys(95, sys_fwd, anim_fb.get(95))
    wire_sys(94, sys_back, anim_fb.get(94))
    fwd_anim = None
    if sys_fwd is not None and exists(sys_fwd):
        fwd_anim = native_anim(sys_fwd, sys_fwd)
    elif 95 in virtual_anims:
        fwd_anim = virtual_anims[95]
    wire_sys(69, sys_neutral, anim_fb.get(69, fwd_anim))
    wire_sys(67, sys_blow, anim_fb.get(67))

    for e in entries:
        if e.get("type", "").lower() != "changestate" or e["value_i"] < 0:
            continue
        nl = e["name"].lower().strip()
        for pat, sid in SYS_NAMES.items():
            if nl == pat and sid not in wired:
                wire(sid, e["value_i"])
    # unnamed entries (kofa chars): infer from command names / values
    for e in entries:
        if e.get("type", "").lower() != "changestate" or e["value_i"] < 0:
            continue
        cs, csj, v = e["cmds"], " ".join(e["cmds"]).lower(), e["value_i"]
        nl = e["name"].lower()
        if 47 not in wired and cs == {"s"}:
            wire(47, v)
        if 74 not in wired and "throw" in csj:
            wire(74, v)
        if 45 not in wired and cs == {"FF"}:
            wire(45, v)
        if 46 not in wired and cs == {"BB"}:
            wire(46, v)
        if 94 not in wired and "dodge" in nl and "forward" in nl:
            wire(94, v)
        if 97 not in wired and "charge" in nl:
            wire(97, v)
        if 96 not in wired and "max" in nl and "発動" in e["name"]:
            wire(96, v)
    for sid, default in SYS_STATE.items():
        if sid not in wired and exists(default):
            wire(sid, default)

    # ---- specials & supers ----------------------------------------------
    # candidates: (norm_name, motion str, elems, posture, value)
    cand = []
    for e in entries:
        if e.get("type", "").lower() != "changestate" or e["value_i"] < 0 \
                or e["value_i"] >= 20000:
            continue
        # e["cmds"] is a set; resolve in a stable order so regenerating the
        # roster does not reshuffle special motions between runs.
        mlist = [resolve(c) for c in sorted(e["cmds"])]
        named = resolve(e["name"])           # ikaruga: state name == cmd name
        if named[0]:
            mlist.append(named)
        for mstr, elems, _held in mlist:
            if not elems or len(elems) < 2:
                continue
            if btn_of(elems) is None:
                continue
            cand.append((e, mstr, elems))

    # group by (dirs, posture, base-name): weak = x/a, strong = y/b
    groups = {}
    for e, mstr, elems in cand:
        mkey = ",".join(d for d, b, r in elems if d)
        bkey = norm_name(e["name"])
        gkey = (mkey, e["st"] or 1, bkey)
        groups.setdefault(gkey, []).append((e, mstr, elems))

    def pair_key(grp):
        """pick the entry with the fewest triggers per btn class."""
        out = {}
        for e, mstr, elems in grp:
            btn = btn_of(elems)
            cls = "w" if btn in WEAK_BTNS else ("s" if btn in STRONG_BTNS
                                                else "b")
            cur = out.get(cls)
            if cur is None or len(e["triggers"]) < cur[0]:
                out[cls] = (len(e["triggers"]), mstr, e["value_i"],
                            e["st"], e["name"])
        return out

    special_pairs = []
    supers = []
    for (mkey, st, bk), grp in groups.items():
        pair = pair_key(grp)
        weak = pair.get("w")
        strong = pair.get("s")
        both = pair.get("b")
        ndirs = mkey.count(",") + (1 if mkey else 0)
        hi = any(val[2] >= 3000 for val in (weak, strong, both)
                 if val is not None)
        ent = (mkey, st, weak, strong, both)
        if both or ndirs >= 6 or hi:
            supers.append(ent)
        else:
            special_pairs.append(ent)

    # specials fill 48..66 in pairs (weak=sid, strong=sid+1); sid 67 is the
    # reserved CD slot.  Skip groups whose states are already wired.
    sid = 48
    for mkey, st, weak, strong, _both in special_pairs:
        if sid > 66:
            break
        vals = [v for v in (weak, strong) if v]
        if vals and all(v[2] in wired.values() for v in vals):
            continue
        wrote = False
        for val, tag in ((weak, 0), (strong, 1)):
            if val is None or sid + tag > 66:
                continue
            _t, mstr, v, _s, _n = val
            wire_motion(sid + tag, v, mstr, st)
            wrote = True
        if wrote:
            sid += 2
    # supers: first group -> 85=weak, 86=strong, 87=MAX; second -> 88/89 w/s
    for gi, (mkey, st, weak, strong, both) in enumerate(supers[:2]):
        sbase = 85 if gi == 0 else 88
        for val, tag in ((weak, 0), (strong, 1), (both, 2)):
            if val is None or sbase + tag > 89:
                continue
            _t, mstr, v, _s, _n = val
            wire_motion(sbase + tag, v, mstr, st)

    # ---- manual overrides -------------------------------------------------
    for spec in ov.get("specials", []):
        osid, ostate, ocname, omotion = spec[:4]
        opost = spec[4] if len(spec) > 4 else 1
        if exists(ostate):
            spec_motion[osid] = (ocname, omotion, opost)
            used_cmds.setdefault(ocname, omotion)
            wire(osid, ostate)
    for osid, ostate in ov.get("moves", {}).items():
        if exists(ostate):
            wire(osid, ostate)
    # keep cmd-side crouch normals in sync with sid wiring (king override)
    for (pp, bb), osid in ((("c", "x"), 19), (("c", "y"), 20),
                           (("c", "a"), 21), (("c", "b"), 22)):
        if (pp, bb) not in normals and osid in wired:
            normals[(pp, bb)] = wired[osid]

    # ---- anims ------------------------------------------------------------
    def anim_for(state, default):
        for c in (stdefs.get(state, {}).get("anim"), state, default, 47, 0):
            if c in air_ids:
                return c
        return 0

    anims = {}
    for sid, state in BASE_STATE.items():
        anims[sid] = anim_for(state, state)
    for sid, state in wired.items():
        anims[sid] = anim_for(state, state)
    dodge_anim = anims.get(69) or anim_for(720, 720)
    for sid in range(98):
        if sid not in anims:
            anims[sid] = dodge_anim if 78 <= sid <= 84 else anim_for(47, 47)
    for sid, anim in virtual_anims.items():
        anims[sid] = anim
    for sid, anim in ov.get("anims", {}).items():
        anims[sid] = anim
    for sid in ov.get("omit_anims", ()):
        anims.pop(sid, None)

    # ---- _SNES.cmd --------------------------------------------------------
    cmd_name = f"{base}_SNES.cmd"
    buf = [f";\n; {cmd_name} -- synthetic command table for the SNES fight"
           " engine.\n; Generated by tools/gen_char_cfg.py.\n\n"
           ";=========================[ Command definitions ]"
           "============================\n"]
    used_names = set()
    motion_order = sorted(spec_motion.items())
    if key == "yuri":
        # The super motions end in the same F/DF/B tail as Senkai Kyaku.
        # CmdTry uses table order as priority, so emit the longer motions
        # first or the shorter special consumes the final press.
        motion_order.sort(key=lambda kv: -len(kv[1][1].split(",")))
    for osid, cn, mstr, post in ov.get("extra_cmds", []):
        motion_order.append((osid, (cn, mstr, post)))
    for _sid, (cn, mstr, _p) in motion_order:
        if cn in used_names:
            continue
        used_names.add(cn)
        # Reusable command fluency settings live in
        # assets/calibration/input_profiles.json.  Per-command prefixes let
        # each profile leave extra room for longer supers.
        if calibration:
            time = calibration["special_default_frames"]
            for prefix, frames in sorted(
                    calibration.get("special_prefix_frames", {}).items(),
                    key=lambda item: -len(item[0])):
                if cn.startswith(prefix):
                    time = frames
                    break
            for prefix, frames in ov.get("cmd_frames", {}).items():
                if cn.startswith(prefix):
                    time = frames
                    break
            buf.append(f'[Command]\nname = "{cn}"\ncommand = {mstr}\ntime = {time}\n\n')
        elif key == "yuri":
            time = 26 if cn.startswith("DBF") else 22 if cn.startswith("MBDF") else 18
            buf.append(f'[Command]\nname = "{cn}"\ncommand = {mstr}\ntime = {time}\n\n')
        else:
            buf.append(f'[Command]\nname = "{cn}"\ncommand = {mstr}\n\n')
    for n, m, t in BASE_CMDS:
        if key == "yuri":
            m, t = {"ESQ_L": ("c", 12),
                    "ESQ_F": ("/F, c", 14),
                    "ESQ_B": ("/B, c", 14),
                    "CD": ("y+b", 15), "DODGE": ("x+a", 18),
                    "recovery": ("x+a", 0),
                    "FF": ("F, F", 18), "BB": ("B, B", 18)}.get(n, (m, t))
        if calibration:
            t = calibration.get("system_command_frames", {}).get(n, t)
        buf.append(f'[Command]\nname = "{n}"\ncommand = {m}\n'
                   + (f"time = {t}\n" if t else "") + "\n")
    buf.append("[Statedef -1]\n\n")

    def entry(name, value, motion, posture, extra="trigger1 = ctrl\n"):
        buf.append(f"[State -1, {name}]\ntype = ChangeState\n"
                   f"value = {value}\n"
                   f'triggerall = command = "{motion}"\n'
                   f"triggerall = statetype {posture}\n" + extra + "\n")

    for _sid, (cn, _m, post) in motion_order:
        entry(f"special_{_sid}", wired[_sid], cn,
              "= A" if post == 4 else "!= A")
    if key in ("terry", "yuri") or (calibration and calibration.get("wire_dash")):
        for _sid, cname in ((45, "FF"), (46, "BB")):
            if _sid in wired:
                entry(f"sys_{_sid}", wired[_sid], cname, "= S")
    # 95 = forward evade (StSpecial, keeps its VelSet), 94 = backward
    # evade (StAirSpec), 69 = neutral dodge.  Yuri is no longer a special
    # case: all fighters now share the same pad layout.
    sys_entries = ((95, "ESQ_F"), (94, "ESQ_B"), (69, "ESQ_L"),
                   (96, "MAX_ON"), (97, "CHARGE"))
    for _sid, cname in sys_entries:
        if _sid in wired:
            extra = ("trigger1 = ctrl\n")
            if cname == "ESQ_L":
                # forward/back + L must roll, never fall through to the
                # neutral dodge when the direction registers first.
                extra = ('triggerall = command != "holdfwd"\n'
                         'triggerall = command != "holdback"\n' + extra)
            entry(f"sys_{_sid}", wired[_sid], cname, "= S", extra)
    if 67 in wired:
        entry("Blowback", wired[67], "CD", "= S")
    if key != "yuri":
        throw_rows = OVERRIDES.get(key, {}).get("throws")
        if throw_rows:
            for _value, _btn, _dist in throw_rows:
                buf.append(
                    f"[State -1, Throw {_btn}]\ntype = ChangeState\n"
                    f"value = {_value}\n"
                    f'triggerall = command = "{_btn}"\n'
                    "triggerall = statetype = S\n"
                    "triggerall = ctrl\n"
                    'trigger1 = command = "holdfwd"\n'
                    f"trigger1 = p2bodydist x < {_dist}\n"
                    'trigger2 = command = "holdback"\n'
                    f"trigger2 = p2bodydist x < {_dist}\n\n")
        elif 74 in wired:
            entry("Throw", wired[74], "x+y", "= S")
    if 47 in wired:
        entry("Taunt", wired[47], "start", "= S")

    # complete the 4-button normal sets (alias the nearest available state)
    for p in "sca":
        have = [b for b in BTN_ORDER if (p, b) in normals]
        for b in BTN_ORDER:
            if (p, b) not in normals:
                src = have[0] if have else None
                if src is not None:
                    normals[(p, b)] = normals[(p, src)]
    NLABEL = {("s", "x"): "Stand Light Punch", ("s", "y"): "Stand Strong Punch",
              ("s", "a"): "Stand Light Kick", ("s", "b"): "Stand Strong Kick",
              ("c", "x"): "Crouch Light Punch", ("c", "y"): "Crouch Strong Punch",
              ("c", "a"): "Crouch Light Kick", ("c", "b"): "Crouch Strong Kick",
              ("a", "x"): "Jump Light Punch", ("a", "y"): "Jump Strong Punch",
              ("a", "a"): "Jump Light Kick", ("a", "b"): "Jump Strong Kick"}
    for (p, b), nm in NLABEL.items():
        st8 = normals.get((p, b))
        if st8 is None:
            continue
        if p == "s":
            trg = ('triggerall = command != "holddown"\n'
                   'trigger1 = statetype = S\ntrigger1 = ctrl\n')
        elif p == "c":
            trg = ('triggerall = command = "holddown"\n'
                   'trigger1 = statetype = C\ntrigger1 = ctrl\n')
        else:
            trg = 'trigger1 = statetype = A\ntrigger1 = ctrl\n'
        buf.append(f"[State -1, {nm}]\ntype = ChangeState\nvalue = {st8}\n"
                   f'triggerall = command = "{b}"\n' + trg + "\n")
    open(os.path.join(cdir, cmd_name), "w", encoding="utf-8").write(
        "".join(buf))

    cfg = {
        "sff": f"assets/characters/{sff_rel}",
        "air": f"assets/characters/{air_rel}",
        "cns": f"assets/characters/{cdir_name}/{cns_name}",
        "cmd": f"assets/characters/{cdir_name}/{cmd_name}",
        "buttons": dict(BUTTONS),
        "anims": anims,
        "moves": moves,
        "coord_scale": 2 if localcoord and localcoord > 320 else 1,
        "char_scale": 0.81,
        "damage_scale": 2.0,
        "msu": True,
        "display": display,
    }
    if calibration_name:
        cfg["calibration_profile"] = calibration_name
    cfg.update(ov.get("cfg", {}))
    nspec = sum(1 for s in spec_motion if s < 85)
    nsuper = sum(1 for s in spec_motion if s >= 85)
    aliased = [f"{p}{b}" for p in "sca" for b in BTN_ORDER
               if (p, b) in normals and (p, b) not in
               [(pp, bb) for pp, bb in
                ((k[0], k[1]) for k in normals) if True]]
    print(f"{key}: base={base} normals="
          f"{'/'.join(f'{p}:{sum(1 for b in BTN_ORDER if (p,b) in normals)}' for p in 'sca')}"
          f" specials={nspec} supers={nsuper} states={len(stdefs)}"
          f" taunt={wired.get(47)} throw={wired.get(74)}"
          f" cd={wired.get(67)} max={wired.get(96)}")
    return cfg


def main():
    sel = sys.argv[1:] or [k for k, _d, _f, _n in ROSTER]
    specs = {}
    for key, cdir, deff, disp in ROSTER:
        if key not in sel:
            continue
        try:
            specs[key] = gen_char(key, cdir, deff, disp)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"{key}: FAILED {e}")
    out = ["# generated by tools/gen_char_cfg.py -- do not edit\n",
           "NEW_CHARS = {\n"]
    for key, cdir, deff, disp in ROSTER:
        if key not in specs:
            continue
        cfg = specs[key]
        out.append(f"    {key!r}: {{\n")
        for k, v in cfg.items():
            if k in ("anims", "moves"):
                items = ",".join(f"{a}:{b}" for a, b in sorted(v.items()))
                out.append(f"        {k!r}: {{{items}}},\n")
            elif k == "buttons":
                items = ",".join(f"{a!r}:{b}" for a, b in v.items())
                out.append(f"        {k!r}: {{{items}}},\n")
            else:
                out.append(f"        {k!r}: {v!r},\n")
        out.append("    },\n")
    # Kyo KOF'98 EX variants: build_fight.py clones the hand-tuned base Kyo
    # config and only needs these entries for the hidden roster ids used by
    # the select screen (L/R on the Kyo cell).
    out.append(
        "    # Kyo EX variants (full configs cloned from base Kyo in "
        "build_fight.py).\n"
        "    'kyonests': {\n"
        "        'sff': 'assets/characters/Kyo-KOF98/Nests/Kyo.sff',\n"
        "        'anims': {}, 'moves': {}, 'msu': True, 'hidden': True,\n"
        "        'display': 'KYO',\n"
        "    },\n"
        "    'kyoash': {\n"
        "        'sff': 'assets/characters/Kyo-KOF98/Ash/Kyo.sff',\n"
        "        'anims': {}, 'moves': {}, 'msu': True, 'hidden': True,\n"
        "        'display': 'KYO',\n"
        "    },\n")
    out.append("}\n")
    open(OUT_SPEC, "w").write("".join(out))
    print(f"\n{OUT_SPEC}: {len(specs)} chars")


if __name__ == "__main__":
    main()
