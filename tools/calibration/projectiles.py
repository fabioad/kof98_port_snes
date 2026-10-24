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
    # Sakura's QCF+P helper (state 1020) carries the fireball in AIR 1020;
    # its own HitDef is the shot hitbox, there is no Projectile controller.
    "sakura": 1020,
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
        "action": 3020,
        # Three compact key poses keep the alternate atlas inside the small
        # free ROM windows left by the roster (the full 11-cel helper clip
        # would cost 22 KiB).  The ticks hold the peak briefly and then show
        # the dissipating tip before the one-shot slot frees itself.
        "frames": ((0, 4), (6, 12), (10, 13)),
        "pre_scale": 3,
        "zoom": 1,
        "sids": (85, 86),
        "release": 6,
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
    "andy": "kyo",          # Hishou Ken flame
    "geese": "terry",       # ground wave
    "leona": "terry",       # ground wave
    "mrbig": "heavyd",      # beam
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
}
PROJECTILE_ZOOM = 2

# The Ko'ou Ken cels are solid ovals (not sparse flame streaks), so the
# shared 16-tile OBJ page only fits them at native source size.
PROJECTILE_ZOOM_BY_CHAR = {
    "yuri": 1,
    "robert": 1,
    # The basketball is already 24x24 in the source.  Doubling it would be
    # half the playfield height; keep it native so it reads as a ball.
    "lucky": 1,
}
GROUND_PROJECTILES = {
    "terry", "kyo", "kyonests", "kyoash", "iori",
    # Restored shots that travel along the floor (or reuse a floor-wave
    # atlas): keep their spawn height at the feet so jumps can clear them.
    "andy", "daimon", "geese", "leona", "mrbig", "ralf", "shingo",
}

# Projectiles that are thrown from an airborne move (Lucky's fadeaway shot)
# keep a fixed upper-torso screen height instead of inheriting the caster's
# jump height.  Otherwise the ball spawns above a standing opponent's
# projectile hit window and flies over their head.
TORSO_PROJECTILES = {"lucky"}

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
PROJECTILE_RECOVERY = {}

# Character-level projectile calibration, in 8.8 px/tick and HUD damage.
# The source CNS is used for every other move; these rows override generic
# conversions where the imported controls had only a shared placeholder.
PROJECTILE_CALIBRATION = {
    # Ryu's QCF+P Hadouken (source states 1000/1010, sids 48/49).  The
    # generic walk did not see the controller, so both rows were empty and
    # the shot never spawned.
    "ryu": {48: (0x0300, 14), 49: (0x0400, 18)},
    "iori": {48: (0x02C0, 12), 49: (0x03C0, 16)},
    "kyo": {48: (0x0300, 14), 49: (0x0400, 18)},
    "rugal": {48: (0x0300, 16), 49: (0x0400, 20)},
    "saisyu": {48: (0x0280, 14), 49: (0x0380, 18)},
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
    # Lucky SHOOT: the basketball is a helper HitDef in state 2103, reached
    # only through 2100 -> 2101/2102 -> 2107/2103, which the one-level
    # helper walk cannot resolve.  Sid 87 is state 2100 (release pose);
    # source damage 109 on the 100-HP scale -> 22 HUD points, and the ball
    # travels forward like the other specials instead of the helper's
    # near-zero placeholder velocity.
    "lucky": {87: (0x0400, 22)},
    # Heavy D! D. Magnum: state 2105 is the release pose, helper 2120 is a
    # stationary beam with the HitDef.  Give the native shot a forward
    # speed so it reads as the travelling blast, with super-level damage.
    "heavyd": {87: (0x0400, 22), 88: (0x0500, 26)},
    # Andy's Hishou Ken (state 1150) reaches a helper whose Projectile
    # velocity is inherited from the helper VelSet; the native row needs an
    # explicit speed.
    "andy": {58: (0x0400, 14)},
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

# sid -> AIR body launch action played while the projectile effect flies.
# Effects stay separate: Iori AIR 1001 / Kyo AIR 1005 are the spark clips,
# never the fighter's body animation.
BODY_ANIMATIONS = {
    "kyo": {48: 1000, 49: 1010},
    "iori": {48: 1000, 49: 1010},
}
