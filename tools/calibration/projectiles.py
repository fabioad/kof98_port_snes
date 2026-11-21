"""Persisted manual projectile adjustments used by the SNES generator.

Keep these explicit overrides separate from automatically inferred CNS
values.
"""

# Character name -> AIR action carrying the projectile effect artwork.
PROJECTILE_ACTIONS = {
    "kyo": 1005, "iori": 1001, "heidern": 1003, "takuma": 1001,
    "terry": 1070, "joe": 1001,
    "ryo": 3005, "athena": 1001, "kensou": 1025,
    "chin": 1901, "king": 1010, "mai": 1003, "krauser": 1025,
    "ryu": 1021, "ken": 1021, "chunli": 1010,
    # Lucky's SHOOT (state 2099) hands the basketball to helper states;
    # AIR 2101 is the 24x24 spinning ball with the attack box.
    "lucky": 2101,
    # Kyo's EX variants share the base Kyo flame clip.
    "kyonests": 1005, "kyoash": 1005,
    # Sakura's QCF+P helper (state 1020) carries the fireball in AIR 1020,
    # but the port now draws the shot with Ryu's compact fireball clip
    # (PROJECTILE_FX_ALIAS below) and uses this action only as the source
    # reference.  The old 13000/alternate 64x54 atlas distorted tiles.
    "sakura": 1021,
    # Rugal: the AIR was stripped to the firing actions (1000/1010); the
    # MUGEN projanim 1006 lives only as SFF group 1002.  build_char
    # synthesizes that action from the sprite group via projectile_air.
    # Omega98 (omegarugal98) keeps its 11-frame Gravity Smash orb (1035).
    "rugal": 1006, "omegarugal": 1035, "robert": 1055,
    # Heavy D!'s D. Magnum release (state 2105) spawns helper state 2120.
    # The helper's AIR action 2120 is the blank hitbox timeline; the actual
    # beam artwork is the 14-cel action 2113 (SFF group 2120).
    "heavyd": 2113,
    # Saisyu's fireball helper draws the shot with Explod 1025; the
    # Projectile controller's projanim 1021 is the blank launch timeline.
    "saisyu": 1025,
    # Benimaru's Raikouken is a helper with the hitdef and an Explod 1002
    # holding the electric ball.  projanim 1005 is the invisible helper body.
    "benimaru": 1002,
    # Geese's Raising Storm helper explods the ground wave as action 1053;
    # the Projectile controller points at the blank 1055 timeline.
    "geese": 1053,
    # Leona's Baltic Launcher explods the wave in state 1111 (action 1115).
    "leona": 1115,
    # Mr. Big's Ground Blaster helper body is action 1020; the Explod 1001
    # is only the muzzle flash.
    "mrbig": 1020,
    # Eiji's super helper carries the shot in its own body action 3002;
    # projanim 3004 is the blank helper timeline.
    "eiji": 3002,
    # Andy's Hishou Ken helper explods the shot as action 1157.
    "andy": 1157,
    # Daimon's Jiraishin shockwave is painted by Explod 6045.
    "daimon": 6045,
    # Ralf's only Projectile controllers (states 100000/110000) are the
    # wall-sensing helpers spawned by state 10001 (State -2); they are not
    # player shots.  Galactica Phantom's visible shockwave is Explod 11011.
    "ralf": 11011,
    # Shermie's thrown shot (state 7200) uses projanim 7220 directly.
    "shermie": 7220,
    # Yamazaki's travelling shot helper explods action 3141 for the super;
    # the regular version uses the 1216/1205 wave.
    "yamazaki": 3141,
    # Kasumi's Kasane Ate / Chou Kasane Ate helpers draw the shot on AIR
    # 1020/3020; the helper bodies have no velocity, so the native rows are
    # calibrated below as stationary shots.
    "kasumi": 1020,
}

# Some sources paint the flying projectile as one Explod per helper frame
# instead of a single Mugen animation.  Yuri's Ko'ou Ken lives in states
# 405/406: the helper itself draws the invisible action 405 and every tick
# explods 2010+animelemno(0)-1 (actions 2010..2015).  Action 10000 in the
# same SFF is a different slash effect, not the Ko'ou Ken fireball.
PROJECTILE_ACTION_SEQUENCES = {
    "yuri": (2010, 2011, 2012, 2013, 2014, 2015),
}

# A character may need a second, independent effect clip for one of its
# projectile rows.  Terry's Power Geyser is a stationary on-the-spot pillar
# (source helper state 3020) while his Power Wave is the travelling 1070
# flame.  Both ride the same spark slots, but the descriptor used to expose
# only one ProjFx clip per fighter, so the geyser reused the wave artwork.
# These specs compile a compact alternate clip: source action, selected
# frames/ticks, a pre-downscale for the oversized 304x224 helper sheets,
# and the sids whose ProjTab row selects it.  "release" overrides the
# engine's default third-frame launch (0-based AnimElem 7 = frame 6).
PROJECTILE_ALT_EFFECTS = {
    "terry": {
        # Source frame 3010,6 (AIR index 5) is a 92x156 flame pillar.  Fit
        # it to the 16-cell page as 48x80 (3x5 = 14 cells) and then tile the
        # middle rows once: duplicating each row next to itself makes an
        # 8-row, 48x128 pillar without adding unique tiles (still 14).  The
        # signed-byte cell offset caps a ground-anchored pillar at 128 px, so
        # this is the tallest seamless version the effect page can draw.
        "action": 3020,
        "frames": ((5, 20),),
        "pre_scale": 1,
        "squeeze_w": 48,
        "squeeze_h": 80,
        "zoom": 1,
        # Repeat the three middle rows (keep the tip and the base unique).
        # 2x each gives 1 + 6 + 1 = 8 rows and 23 cells in one frame.
        "tile_rows": {"skip_top": 1, "skip_bottom": 1, "repeat": 2},
        # The page still holds 16 unique cells; this only raises the
        # per-frame OAM cell budget so the tiled rows can be drawn.
        "max_cells": 24,
        # Draw the pillar again.  The height/width fit the 16-cell effect
        # page, and the runtime fixes keep the stationary geyser from pushing
        # the victim or running the camera to the wall.
        "invisible": False,
        "sids": (85, 86, 87),
        "release": 6,
    },
    # Geese's Raising Storm.  The source paints it with Explod 3001 (front)
    # and 3002 (back) from SFF groups 3005/3010, both already blue.  Compile
    # the front cel as the alternate projectile clip for the super rows
    # 85/86/87: squeezed to 48x80 and row-tiled to 48x128, exactly like
    # Terry's geyser, so the storm reads as a tall pillar instead of the old
    # orange FlameRise alias.  The shared projectile palette is rebuilt from
    # these pixels; PROJ_PAL_BOOST/pins keep the cyan-blue ramp.
    "geese": {
        "action": 3001,
        "frames": ((3, 20),),
        "pre_scale": 1,
        "squeeze_w": 48,
        "squeeze_h": 80,
        "zoom": 1,
        # 7 rows (1 tip + 2 middle rows doubled + 2 base rows) = 112 px.
        # 8 rows overflowed the Fight bank by 24 bytes after the second
        # horizontal copy; 7 keeps the storm tall and the ROM linking.
        "tile_rows": {"skip_top": 1, "skip_bottom": 2, "repeat": 2},
        # Draw a second copy 48 px back (centred on Geese) so the storm
        # surrounds him instead of standing only in front.  Both copies
        # reuse the same cell slots; only OAM cells double.
        "repeat_x": {"offset": -48, "copies": 2},
        "max_cells": 48,
        "invisible": False,
        "sids": (85, 86, 87),
        "release": 9,
    },
    # Athena's Phoenix Fang charge levels (3000/3050/3100).  The source
    # helper 3050 plays the visible ball on AIR 7700; 7701 is only the
    # blank Clsn1 hitbox.  Use 7700 as the alternate projectile clip.
    "athena": {
        "action": 7700,
        "frames": ((0, 4), (3, 4), (6, 6)),
        "sids": (85, 86, 87),
        "release": 2,
    },
    # Rugal's Eye Beam (1702 -> helper 1705).  The AIR 1704 was stripped
    # from the package; the beam cell is SFF group 1705 and is synthesized
    # by the `projectile_air` config.  Only the Eye Beam slot selects it.
    "rugal": {
        "action": 1704,
        "frames": ((0, 6),),
        "pre_scale": 2,
        "sids": (82,),
        "release": 3,
    },
    # Omega's Gravity Shot (state 7100) is a beam: the source Projectile
    # uses projanim 1357, while the primary ProjFx (1035) is the Gravity
    # Smash orb.  Compile the beam with a 2x pre-scale and a 12-cell cap so
    # it stays inside the effect/OAM budget instead of spilling over.
    "omegarugal": {
        "action": 1357,
        # Frame 10 is larger than the effect page after cropping; frame 6
        # already shows the beam.  Hold that frame so the one-shot alternate
        # clip does not free the projectile before it crosses the screen.
        "frames": ((3, 4), (6, 255)),
        "pre_scale": 2,
        "max_cells": 12,
        "sids": (82,),
        "release": 3,
    },
    # Kasumi's Chou Kasane Ate supers use the larger 3020 wave; the
    # regular Kasane Ate rows keep the 1020 clip.
    "kasumi": {
        "action": 3020,
        "frames": tuple((i, 5 if i == 11 else 1) for i in range(12)),
        "sids": (85, 86, 87),
        "release": 6,
    },
    # John's Flame Raid hitbox is invisible: the visible fire is the CNS
    # Explod 6040 at his feet.  Emit an empty-cell alternate clip so the
    # travelling shot keeps its full-screen hitbox without drawing a second
    # flame (the tremor/impact sells the hit instead).
    "john": {
        "action": 6040,
        "invisible": True,
        "sids": (56, 57),
        "release": 6,
    },
    # Yuki's Ai no Kusanagi (source state 3350) calls the Kyo helper
    # (state 3355, AIR 1903 / SFF group 2001).  The native engine keeps the
    # projectile hitbox but has no helper bodies, so draw Kyo as the
    # alternate ProjFx clip for sid 89.  The primary clip stays the flame
    # used by sid 88 (Naku Ko).  Squeeze the 63x82 source cel to 63x64 so
    # the Kyo frame fits the 16-cell effect page at native width; the alt
    # clip is one-shot, so a 255-tick frame holds the sprite until the shot
    # hits or reaches its TTL (two source frames would need more unique
    # tiles and force a downscale to 24x32).
    "yuki": {
        "action": 1903,
        "frames": ((1, 255),),
        "sids": (89,),
        "release": 2,
        "squeeze_w": 64,
        "squeeze_h": 64,
    },
}

# Characters that reuse another character's compiled projectile effect.  The
# Kyokugen trio (Ryo, Robert and Takuma) shares Yuri's Ko'ou Ken, and her
# six-cel dissolve is the most polished version, so point their ProjFx
# descriptor at her table instead of drawing the shorter/older variants.
# build_fight writes projfx_alias into each config, which also makes the
# generated descriptor reference yuriProjFxTab/yuriProjFxChr directly.
# Takuma is one of the fixed descriptors in fight.asm, so his row is updated
# there as well.
PROJECTILE_FX_ALIAS = {
    # Sakura's hadouken/super shots now use Ryu's compact fireball atlas.
    # The old Sakura-specific atlas (the 64x54 alternate cel) overflowed the
    # effect page and showed distorted tiles in the Shinkuu sequence.
    "sakura": "ryu",
    "ryo": "yuri",
    "robert": "yuri",
    "takuma": "yuri",
    # Shingo's Orochinagi is a flame wave, but its AIR only carries the
    # launch body.  Reuse Kyo's compiled flame clip instead of spawning an
    # invisible shot.
    "shingo": "kyo",
    # Saisyu's fireball (Explod 1025) is a plain flame streak.  Point the
    # runtime descriptor at Kyo's compiled Yami Barai clip so the shot reads
    # as the same ground flame, and skip compiling Saisyu's duplicate atlas.
    "saisyu": "kyo",
    # Eiji's 4-cel super shot is a plain energy orb; its own atlas does not
    # fit the remaining bank windows.  Athena's compiled orb is the closest
    # small effect and keeps the ROM linkable.
    "eiji": "athena",
    # The imported KOF98 packs store these shots as Explod/helper cels
    # rather than standalone projectile AIR actions.  Their native atlases
    # would duplicate an already-shared effect and exhaust the free ROM
    # windows, so point them at the closest compiled clip.  The per-character
    # PROJECTILE_ACTIONS rows above still document the source action.
    "benimaru": "athena",   # electric orb
    "andy": "yuri",         # Hishou Ken reuses the compiled Ko'ou Ken orb
    # Geese keeps Terry's primary ground-wave clip for the Reppuken (the
    # source action 1053 atlas would add another full page), but he compiles
    # his own blue Raising Storm alternate clip below.
    "geese": "terry",       # primary ground wave
    "leona": "terry",       # ground wave
    # Mr. Big's own Ground Blaster (action 1020) is a flame wave.  The old
    # Heavy D beam alias was a streaky horizontal beam: shrunk into the
    # 16-cell effect page its transparent gaps turned into coloured
    # speckles ("chuviscos") over the white core.
    "daimon": "terry",      # ground shockwave
    "ralf": "terry",        # Galactica shockwave
    "shermie": "athena",    # orb
    "yamazaki": "kyo",      # flame shot
}

PROJECTILE_SOURCE_PALETTES = {
    # Iori's projectile uses the purple energy ramp stored in his fourth SFF
    # palette; the default fighter palette has black at these extended indices.
    "iori": 4,
    # Yuri's Ko'ou Ken cels use the shared fire ramp at palette 0.  Their
    # SFF palette index (1645) is a body/shadow bank with black entries
    # where the flame colours should be.
    "yuri": 0,
    # John's Mega Smash cels (SFF group 1001) carry palidx 1, which has
    # black at the effect indices 17-23; the orange/blue blast ramp lives
    # in palette 3.  Without this the compiled clip is all-transparent.
    "john": 3,
}
PROJECTILE_ZOOM = 2

# Projectile effects drawn from external PNG art instead of the fighter's SFF
# (see tools/extract_yamibarai_art.py).  Value: (ticks per frame, files in
# assets/projectiles).  Two frames at most: the build shrinks them just
# enough to fit the 16-cell effect page.  Kyo's clip also draws Saisyu,
# Shingo and Yamazaki through PROJECTILE_FX_ALIAS; Saisyu is listed so its
# old SFF flame stops contributing to the shared 15-colour projectile
# palette.  Iori is the same burst in the purple ramp of his Yami Barai.
PROJECTILE_EXTERNAL_ART = {
    "kyo": (4, ("kyo_yamibarai_a.png", "kyo_yamibarai_b.png")),
    "saisyu": (4, ("kyo_yamibarai_a.png", "kyo_yamibarai_b.png")),
    "iori": (4, ("iori_yamibarai_a.png", "iori_yamibarai_b.png")),
}

# The Ko'ou Ken cels are solid ovals (not sparse flame streaks), so the
# generic 2x upscale overflows the shared 16-cell OBJ page.  Yuri uses the
# rational resize + per-frame atlas quantizer below instead; keep her generic
# zoom at 1 so that custom path is selected.
PROJECTILE_ZOOM_BY_CHAR = {
    "yuri": 1,
    "robert": 1,
    # The basketball is already 24x24 in the source.  Doubling it would be
    # half the playfield height; keep it native so it reads as a ball.
    "lucky": 1,
    # John's blast cells are 102x39 already; the default 2x zoom overflows
    # the 16-cell effect page.
    "john": 1,
}
# Projectile effects that need a non-integer resize.  The engine fits the
# compiled 16x16-cell atlas, so these are scaled before the atlas quantizer.
# Yuri's Ko'ou Ken is enlarged 1.5x linearly (~2.25x area) to read roughly
# like Kyo's 80x96 flame; the old native size was 48x80.
PROJECTILE_RESIZE = {
    "yuri": (3, 2),
}

GROUND_PROJECTILES = {
    "terry", "kyo", "kyonests", "kyoash", "iori",
    # Restored shots that travel along the floor (or reuse a floor-wave
    # atlas): keep their spawn height at the feet so jumps can clear them.
    "andy", "daimon", "geese", "leona", "mrbig", "ralf", "shingo",
    # John's Flame Raid is a floor wave too.
    "john",
}

# Character-level fixed upper-torso spawn height.  Lucky's basketball uses
# the ballistic profile below instead; the per-shot PROJECTILE_TORSO_SIDS
# switch below still covers Geese's air shot.  The GTA trio fire from
# raised hands: the default 40 px "mid torso" spawn sat below the arms.
TORSO_PROJECTILES = {"jason", "lucia"}

# Source-verified ballistic projectiles.  The ProjFxTab header gets three
# extra bytes at offsets 5-7: spawn height above the floor, gravity in 1/16
# px/tick^2, and flags (bit0 = ballistic, bits4-7 = ticks of forward drift
# before VX is zeroed).
# Lucky's basketball is the arcade Death Bound: it leaves his hand and
# travels diagonally down/forward toward the opponent, not a vertical drop
# from the sky.  Spawn at hand height (120 px above the floor), keep a
# constant 4 px/tick forward speed and let 11/16 px/tick^2 gravity bend it
# down.  No forward-drift stop (drift=0); the pad is non-zero, so the shared
# SparkGravity path integrates the fall and the ball bounces on the floor.
# The Death Shoot (D,D+P, a separate source move) is the sky/layup toss and
# is not this projectile.
PROJECTILE_BALLISTIC = {
    "lucky": {"height": 120, "gravity": 11, "drift": 0},
}

# Per-sid airborne shots for characters that also have ground projectiles.
# The character-level TORSO_PROJECTILES switch above cannot express this:
# Geese's ground Reppuken must spawn at the floor, while his air Shippuu Ken
# (state 1100 / sid 58) must use the fixed upper-torso row.  The build sets
# bit1 of the ProjTab "present" byte; the engine reads it as a per-shot height
# override and does not change the character descriptor.
PROJECTILE_TORSO_SIDS = {
    "geese": {58},
}

# Recovery kept after the shot leaves the fighter's hands, in animation ticks.
# Imported launch clips spend most of their length on the follow-through pose
# (Benimaru holds the Raikouken arm for ~50 ticks after the ball is already
# flying), which feels like sluggish recovery on the SNES.  build_fight only
# rescales that tail; element indices and hit windows are preserved.
# A character may override the default with an int or a {sid: ticks} dict.
PROJECTILE_RECOVERY_TICKS = 24
PROJECTILE_RECOVERY = {
    # Takuma/Yuri compact their Ko'ou Ken wind-up and release two ticks
    # later than before; trim the same amount from the follow-through so the
    # whole special keeps its original duration.
    "takuma": {48: 20, 49: 20},
    "yuri": {48: 22, 49: 22},
}

# Per-shot forward spawn offset in pixels (multiples of 8, 0-120).  The low
# nibble of the ProjTab guard byte carries the code (px / 8); ProjSpawn uses
# it to place short-range helper shots at the palm instead of 14 px ahead.
# Codes 8-15 also select a 12-tick lifetime, so a short-range burst does not
# leave a stationary orb lingering for the normal 90-tick projectile TTL.
PROJECTILE_X_OFFSET = {
    # QCB+P Hishou Ken: the helper's Clsn1 is at x=32..127 (centre ~80), so
    # centre the burst 80 px in front of Andy.
    "andy": {52: 80, 53: 80},
    # Kikouken leaves the hands ~37 px ahead of Chun-Li.
    "chunli": {48: 40},
    # Terry's Power Geyser must erupt in front of his ground-punch sprite;
    # the engine default (14 px) hides the short pillar behind his body.
    "terry": {85: 48, 86: 48, 87: 48},
    # Kasumi's Kasane Ate helper paints the wave at its own origin but moves
    # the Clsn1 from x=60 to x=131 (source AIR 1020).  Centering the native
    # shot at 40 px with the ordinary 24 px radius only covered 16..64, so
    # the burst whiffed at the spacing where the move is actually used.
    # Codes 8-15 select the 48 px burst radius (and the source's ~10-tick
    # active window).  Use 88 px for the ground specials (40..136, covering
    # the 60..131 source box) and 72 px for the anti-air rows, which need to
    # catch a victim almost directly overhead (source box starts at x=20).
    # Both codes are odd, which keeps SPK_GRD bit0 set: the tall-pillar
    # height test that lets the anti-air version hit airborne victims.
    "kasumi": {52: 88, 53: 88, 56: 72, 57: 72,
                85: 56, 86: 56, 87: 56},
    # John's Flame Raid is a travelling floor wave now, so it must not use
    # the short-burst profile (the guard-byte low nibble >= 8 forces a
    # 12-tick lifetime).  Code 4 spawns the flame 32 px ahead with the
    # ordinary 90-tick shot lifetime, giving it full-screen reach.
    "john": {56: 32, 57: 32},
    # Raising Storm erupts in front of Geese's hands, like Terry's geyser.
    "geese": {85: 48, 86: 48, 87: 48},
}

# Per-shot release frame override (0-based source animation frame).  Used
# when the source spawns the helper later than the engine's default third
# frame.  QCB+P Hishou Ken spawns helper 1105 on anim 1100 frame 4 and on
# anim 1110 frame 5.
PROJECTILE_RELEASE = {
    "andy": {52: 4, 53: 5},
    # Kikouken's Projectile controller fires on AnimElem 7 (0-based 6);
    # the engine default third frame spawned it during the startup pose.
    "chunli": {48: 6},
    # Kasane Ate leaves the hands on AnimElem 7/8; the super root reaches
    # its follow-up around frame 6.
    # The super root clips are only 7 frames; frame 6 is already past the
    # last pose, so launch on frame 4.
    "kasumi": {52: 6, 53: 6, 56: 7, 57: 7, 85: 4, 86: 4, 87: 4},
    # Flame Raid spawns the wave on AnimElem 7 (the ground punch); the
    # compiled launch clip has 7 poses, so the punch is its last frame.
    "john": {56: 6, 57: 6},
}

# Source-aligned release frames (audit 2026-11-15).
#
# The engine used to spawn every unlisted shot on the launch clip's third
# frame.  Imported KOF98 animations usually reach the actual throw much
# later, so the fireball appeared while the fighter was still winding up.
# These rows use the root animation frame where the source CNS starts the
# projectile (direct controller, projectile helper, or a travelling HitDef
# helper the port stores in the shared shot pool).  Helper-internal delays
# are not added: the port does not render helper bodies, so the visible
# launch is the root helper/controller.
#
# Regenerate the evidence with:
#     python3 tools/audit_projectile_release.py
#
# Kept separate from the older per-character rows above so the origin of
# each value (manual fix vs. source audit) stays clear.
_PROJECTILE_RELEASE_AUDIT = {
    "iori": {48: 3, 49: 3},
    "kyo": {48: 4, 49: 4},
    "kyonests": {48: 4, 49: 4},
    "kyoash": {48: 4, 49: 4},
    "saisyu": {48: 4, 49: 4},
    "heidern": {48: 5, 49: 5},
    "takuma": {48: 5, 49: 5},
    "daimon": {58: 4},
    # Power Wave / Power Geyser helpers leave the hands on element 7.
    "terry": {58: 6, 59: 6, 60: 6},
    # Hishou Ken travelling versions (QCF+c and the air follow-up).
    "andy": {58: 3, 63: 3},
    # Hurricane Upper, Slash Kick and Screw Upper.
    "joe": {60: 6, 62: 6, 65: 6, 107: 5},
    # Ko'ou Ken (ground, EX, air and Haoh Shikou Ken).
    "ryo": {60: 3, 61: 4, 64: 6, 85: 5, 86: 5, 87: 6, 107: 5,
            109: 3, 110: 3},
    # Ryuu Geki Ken and the three Haoh Shikou Ken variants.
    "robert": {58: 5, 59: 5, 60: 5, 109: 7, 110: 7, 111: 7},
    "chin": {85: 1, 86: 1, 87: 1, 111: 3},
    "choi": {88: 7},
    # Yamazaki's travelling super shot is drawn by helper 3141.
    "yamazaki": {85: 11},
    # Reppuken / Shippuu Ken helpers and the Raging Storm pillar.
    "geese": {58: 3, 60: 4, 62: 4, 65: 4, 85: 9, 86: 9, 87: 9},
    # Kaiser Wave helpers.
    "krauser": {54: 3, 55: 3, 56: 3, 57: 3},
    # Ground Blaster helper.
    "mrbig": {54: 6, 55: 6},
    # Eiji's super shot leaves the helper on element 9.
    "eiji": {85: 8, 86: 8, 87: 8},
    # Hadouken and Shinkuu Hadouken helpers (all start on element 5).
    "ryu": {48: 4, 49: 4, 52: 4, 53: 4, 85: 4, 86: 4, 88: 4},
    "ken": {54: 4, 55: 4},
    # Sakura's Hadouken helper.
    "sakura": {52: 4, 53: 4},
    # Yuri's Ko'ou Ken helpers.  The air shot (450/451) already launches on
    # frame 2; the ground and super versions wait for the palm thrust.
    # The MAX Haoh (sid 107) used to be pinned to frame 0, which fired the
    # shot during the super freeze/dim, before the palm pose.  It follows
    # the other Haoh variants (source helper 555 at AnimElem 8).
    "yuri": {48: 6, 49: 6, 50: 8, 51: 8, 85: 7, 87: 7, 107: 7},
    # Psycho Ball (direct Projectile on AnimElem 6).
    "athena": {48: 5, 55: 5},
    # Raikouken helpers and their super variants.
    "benimaru": {48: 5, 49: 4, 85: 6, 86: 5, 87: 5},
    # Kensou's Psycho Ball helpers.
    "kensou": {56: 3, 57: 3},
    # Venom Strike / Double Strike (direct Projectile on AnimElem 4).
    "king": {48: 3, 49: 3},
    # Shermie's thrown shot: direct Projectile on AnimElem 10/15.
    "shermie": {58: 9, 59: 14},
    # D. Magnum's beam is drawn from element 11; the native shot follows it.
    "heavyd": {87: 10, 88: 10},
    # Rugal's 1550 helper creates the shot on entry.
    "rugal": {61: 0},
    # Omega Rugal's fireball helpers leave on element 4; the 2899 follow-up
    # starts its helper on entry.
    "omegarugal": {48: 3, 49: 3, 57: 0},
    # Billy's super shot controller fires on element 12; 6000 on element 4.
    "billy": {64: 11, 66: 11, 107: 11, 110: 3},
    # Yuki's Kusanagi helper (3355) starts on AnimElem 6.
    "yuki": {89: 5},
}
for _char, _rows in _PROJECTILE_RELEASE_AUDIT.items():
    PROJECTILE_RELEASE.setdefault(_char, {}).update(_rows)

# Character-level projectile calibration, in 8.8 px/tick and HUD damage.
# The source CNS is used for every other move; these rows override generic
# conversions where the imported controls had only a shared placeholder.
PROJECTILE_CALIBRATION = {
    # Ryu's QCF+P Hadouken (source states 1000/1010, sids 48/49).  The
    # generic walk did not see the controller, so both rows were empty and
    # the shot never spawned.
    "ryu": {48: (0x0300, 14), 49: (0x0400, 18)},
    # Kikouken: source damage 40 (vs Ryu's 18); the generic import derived
    # only 8 HUD from the formula, leaving the strongest fireball weaker
    # than a Hadouken.  Keep the source speed and give it a commensurate
    # HUD value.
    "chunli": {48: (0x0300, 24)},
    # Iori's Yami Barai uses the imported arcade flame clip recoloured with
    # his purple ramp; same speed/damage as Kyo's fire.
    "iori": {48: (0x0300, 14), 49: (0x0400, 18)},
    "kyo": {48: (0x0300, 14), 49: (0x0400, 18)},
    "rugal": {48: (0x0300, 16), 49: (0x0400, 20)},
    # Saisyu's Yami Barai uses the same compiled clip as Kyo
    # (PROJECTILE_FX_ALIAS below), so it must also use Kyo's speed/damage.
    # The old 0x0280/0x0380 rows made his flame visibly slower than Kyo's.
    "saisyu": {48: (0x0300, 14), 49: (0x0400, 18)},
    "heidern": {48: (0x0400, 14), 49: (0x0500, 18)},
    "takuma": {48: (0x0280, 16), 49: (0x0380, 20)},
    "benimaru": {48: (0x0300, 14), 49: (0x0400, 18),
                 50: (0x0400, 16), 51: (0x0500, 20)},
    # Sakura's QCF+P helper has a HitDef but no Projectile controller or
    # VelSet, so the native table had no row at all.  The source values are
    # 13/17 on the ~100-HP scale; use the same HUD values as Ryu's shot and
    # the helper's intended forward speed.  Sids 52/53 are states 1000/1010
    # (hadouken); 48/49 are the DP and must stay projectile-free.
    "sakura": {52: (0x0400, 14), 53: (0x0700, 18)},
    # Lucky Death Bound: sid 87 is state 2100 (release pose).  The ball
    # leaves the hand at 4 px/tick forward; the ballistic profile above adds
    # the downward curve.  Source damage 109 on the 100-HP scale -> 22 HUD.
    "lucky": {87: (0x0400, 22)},
    # Heavy D! D. Magnum: state 2105 is the release pose, helper 2120 is a
    # stationary beam with the HitDef.  Give the native shot a forward
    # speed so it reads as the travelling blast, with super-level damage.
    "heavyd": {87: (0x0400, 22), 88: (0x0500, 26)},
    # Andy's QCB+P Hishou Ken (states 1100/1110, sids 52/53) is the
    # short-range palm burst: stationary at the 80 px spawn offset, damage
    # 13/14 on the source's 100-HP scale -> 26/28 HUD points.  The QCF+c back
    # version (state 1150, sid 58) is the travelling shot.
    "andy": {52: (0x0000, 26), 53: (0x0000, 28), 58: (0x0400, 14)},
    # Daimon's Jiraishin shockwave is the source state-300 projectile; its
    # velocity is also inherited, so use a slow forward wave.
    "daimon": {58: (0x0200, 14)},
    # Shermie's state 7200 shot is stationary in the source (the engine
    # skips zero-velocity projectiles); state 7300 travels at 4 px/tick.
    "shermie": {58: (0x0100, 20), 59: (0x0400, 12)},
    # Yamazaki's state 1215/3140 helpers use inherited VelSet velocities.
    "yamazaki": {58: (0x0800, 8), 85: (0x0C00, 20)},
    # Leona's Baltic Launcher: the weak state 1100 was not detected because
    # its projectile is a follow-up HitDef, and the derived strong row only
    # carried the source's 120-damage expression.  Give both buttons the
    # same forward speed/damage scale as the other ground waves.
    "leona": {50: (0x0280, 14), 51: (0x0380, 18)},
    # Mr. Big's Ground Blaster helper only exposes a placeholder velocity in
    # the imported CNS; use the same forward wave scale as the other shots.
    "mrbig": {54: (0x0300, 14), 55: (0x0400, 18)},
}

# Shots that knock the victim down like a sweep (crouching strong kick) on a
# clean hit.  The ProjTab row has no free flag bit, so the build marks the
# row's damage byte with $80 (damage itself is capped below 128) and ProjHit
# reads that bit to switch the victim to the trip-fall knockdown instead of
# the ordinary 8-tick hitstun.
PROJECTILE_KNOCKDOWN = {
    # John's Flame Raid (states 1400/1410): floor wave that trips on contact.
    "john": (56, 57),
}

# sid -> AIR body launch action played while the projectile effect flies.
# Effects stay separate: Iori AIR 1001 / Kyo AIR 1005 are the spark clips,
# never the fighter's body animation.
BODY_ANIMATIONS = {
    "kyo": {48: 1000, 49: 1010},
    "iori": {48: 1000, 49: 1010},
}

# --- arcade Yami Barai flame (hand import) -------------------------------
# The KOF98 packs only carry a sparse two-frame wisp for the 108 Shiki
# projectile: the compiled clip shrinks to three tiles after the release
# frame, which reads as a faint flicker on the SNES.  The arcade move uses a
# wide, bright ground flame, so this clip is imported from the standard
# KOF'98 rip (fightersgeneration "kyo98-projectile.gif") instead of the SFF
# artwork.  The GIF frames show Kyo plus the travelling flame; each sampled
# frame is cropped from the listed left edge so only the flame is kept, then
# scaled, quantised to the shared OBJ colour ramp and packed into the usual
# 16-cell effect page.  Kyo and Saisyu (FX alias) share the fire ramp; Iori
# gets the same shapes recoloured with his purple Yami Barai palette.
#
# The flame is sampled from frame 7 on, where it has fully left Kyo's hand
# and reads as the travelling shot.  Frames alternate tall/low in the source
# animation, which is exactly the arcade flicker the loop reproduces.
PROJECTILE_GIF_CLIPS = {
    "gif": "assets/fx/kyo98-projectile.gif",
    # (gif frame, left crop edge[, top crop edge]).  The first two frames
    # still carry the ember chain trailing from Kyo's hand above the flame,
    # so they also clip the top rows.
    "frames": ((7, 74, 46), (8, 76, 80), (9, 95), (10, 96), (11, 115),
               (12, 116), (13, 135), (14, 136), (15, 155)),
    # The port scales fighter art to 0.81; 0.9 keeps the flame dominant
    # without overflowing the 16-cell page (15 cells max after packing).
    "scale": 0.9,
    # 3 ticks per source frame keeps the arcade's 60 ms cadence (the engine
    # clamps projectile frames to 2 ticks minimum).
    "ticks": 3,
    # Source tone -> shared OBJ palette colour.  The palette indices are
    # resolved at build time against gen_fight/spark_pal.bin, so the flame
    # follows the compiled palette instead of hard-coding slot numbers.
    "ramps": {
        # Pale yellow core, then the arcade orange ramp down to the shadow.
        "kyo": (((248, 216, 160), (246, 230, 156)),
                ((240, 168, 56), (246, 180, 98)),
                ((216, 104, 8), (238, 115, 24)),
                ((184, 80, 0), (156, 49, 16)),
                ((144, 104, 72), (180, 98, 32))),
        # Iori's Yami Barai is a purple flame (KOF XV reference): white-hot
        # core, light purple, purple body, deep purple shadow.
        "iori": (((248, 216, 160), (246, 246, 246)),
                 ((240, 168, 56), (197, 106, 255)),
                 ((216, 104, 8), (115, 74, 230)),
                 ((184, 80, 0), (41, 32, 65)),
                 ((144, 104, 72), (41, 32, 65))),
    },
}
# Characters whose compiled ProjFx is replaced by the imported flame.  Kyo's
# clip is shared by Saisyu through PROJECTILE_FX_ALIAS.
PROJECTILE_GIF_USERS = ("kyo", "iori")
