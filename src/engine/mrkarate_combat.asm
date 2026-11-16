; Mr. Karate's native contact sequences and airborne casts. No other
; fighter changes behavior. Two hardware effect slots serve a queued volley.
.DEFINE MKC_ACTIVE  $F1D0
.DEFINE MKC_OWNER   $F1D1
.DEFINE MKC_LEFT    $F1D2
.DEFINE MKC_TOTAL   $F1D3
.DEFINE MKC_ACC     $F1D4
.DEFINE MKC_BUDGET  $F1D5
.DEFINE MKC_CLOCK   $F1D6
.DEFINE MKC_AGE     $F1D7                 ; word, bounded fail-safe
.DEFINE MKC_HITS    $F1D9
.DEFINE MKC_DAMAGE  $F1DA                ; word, actual HP removed
.DEFINE MKC_SHOTS   $F1DC                ; word, successful launches
.DEFINE MKB_KIND    $F1F0                ; two effect slots, 5 or 50
.DEFINE MKB_SERIAL  $F1F2
.DEFINE MKA_FLAG    $F200                ; fields indexed by fofs (0/$40)
.DEFINE MKA_HEIGHT  $F202                ; word, airborne cast height
.DEFINE MKQ_LEFT    $F204
.DEFINE MKQ_CD      $F205
.DEFINE MKQ_SID     $F206                ; native launch state
.DEFINE MKQ_VX      $F208
.DEFINE MKQ_DMG     $F20A
.DEFINE MKQ_GUARD   $F20C
.DEFINE MKQ_TTL     $F20E
.DEFINE MKQ_SERIAL  $F210
.DEFINE MKQ_CLAIM   $F211
.DEFINE MKQ_LATCH   $F212
.DEFINE MKW_VX     $F280
.DEFINE MKW_DMG    $F282
.DEFINE MKW_GUARD  $F284
.DEFINE MKW_FOFS   $F286
.DEFINE MKW_SID    $F288
.DEFINE MKW_SLOT   $F28A

.BASE $00
.BANK 64 SLOT 0
.ORGA $7400                         ; after CloseNormalProfiles ($73DC)
.SECTION "MrKarateCombat" FORCE
.INCLUDE "gen_fight/mrkarate_kind.inc"

MkCombatResetFar:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    phx
    ldx #0
-   stz.w MKC_ACTIVE,x
    inx
    inx
    cpx #$30.w
    bcc -
    ldx #0
-   stz.w MKA_FLAG,x
    inx
    inx
    cpx #$80.w
    bcc -
    plx
    plp
    rtl

; X16 = fighter. Carry set for the MSU form; preserves A16 and Y16.
MkIsFighter:
    pha
    sep #$20
    .ACCU 8
    lda.b msuok
    beq MKIF_no
    rep #$20
    .ACCU 16
    lda FP+F_CHAR,x
    cmp #CharMrkarate.w
    bne MKIF_no16
    pla
    sec
    rts
MKIF_no:
    rep #$20
    .ACCU 16
MKIF_no16:
    pla
    clc
    rts

; A16 = native sid -> A16 = 0, 5, 50. Preserve X/Y.
; Callers must branch on an explicit `cmp #0.w`: relying on the flag left by
; this routine silently took the native/other path at the spawn hook.
MkKind:
    phx
    cmp #119.w
    bcs MKK_none
    tax
    lda.l MkMoveKind,x
    and #$00FF.w
    plx
    rts
MKK_none:
    lda #0
    plx
    rts

; Called before EnterState commits A16. A ground cast made in the air
; holds its launch height, then returns through the ordinary jump/landing
; state machine. Knockback and KO always cancel the hold.
MkCombatEnterFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx fofs
    jsr MkIsFighter
    bcs +
    rtl
+   pha
    jsr MkKind
    cmp #0.w                            ; branch on the value, not on flags
    beq MKEN_other                      ;   left by a far subroutine
    sep #$20
    .ACCU 8
    stz.w MKQ_LATCH,x
    rep #$20
    .ACCU 16
    lda FP+F_Y,x
    beq MKEN_restore
    sep #$20
    .ACCU 8
    lda.w MKA_FLAG,x
    bne MKEN_restore8
    lda #1
    sta.w MKA_FLAG,x
    rep #$20
    .ACCU 16
    lda FP+F_Y,x
    sta.w MKA_HEIGHT,x
    stz FP+F_VY,x
    bra MKEN_restore
MKEN_other:
    pla
    cmp #118.w                          ; contact-loop animation
    beq MKEN_ret
    pha
    cmp #S_STAND.w
    beq MKEN_neutral
    cmp #S_CROUCH.w
    beq MKEN_neutral
    cmp #S_LAND.w
    beq MKEN_neutral
    cmp #S_HIT.w
    beq MKEN_clear
    cmp #S_DOWN.w
    beq MKEN_clear
    cmp #S_JUMP.w
    beq MKEN_clear
    bra MKEN_restore
MKEN_neutral:
    sep #$20
    .ACCU 8
    lda.w MKA_FLAG,x
    beq MKEN_restore8
    stz.w MKA_FLAG,x
    rep #$20
    .ACCU 16
    lda.w MKA_HEIGHT,x                  ; recover even after a source PosSet
    sta FP+F_Y,x
    stz FP+F_VY,x
    beq MKEN_restore
    pla
    lda #S_JUMP.w
    rtl
MKEN_clear:
    sep #$20
    .ACCU 8
    stz.w MKA_FLAG,x
MKEN_restore8:
    rep #$20
    .ACCU 16
MKEN_restore:
    pla
MKEN_ret:
    rtl

; Fallback for posture-mismatched command rows: only Mr. Karate's actual
; special/super targets become usable in the air. No airborne walk/throw.
MkAirCommandFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    phx
    phy
    ldx fofs
    jsr MkIsFighter
    bcc MKAC_no
    lda FP+F_Y,x
    beq MKAC_no
    iny
    iny
    iny
    lda [boxp],y
    and #$00FF.w
    jsr MkKind
    cmp #0.w
    beq MKAC_no
    ply
    plx
    sep #$20
    .ACCU 8
    sec
    rtl
MKAC_no:
    ply
    plx
    sep #$20
    .ACCU 8
    clc
    rtl

; Post-physics: source ground specials may set Pos Y=0 or jump. Keep the
; airborne cast steady only until its finite animation/transition ends.
MkAirRestoreFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx fofs
    sep #$20
    .ACCU 8
    lda.w MKA_FLAG,x
    beq MKAR_done
    rep #$20
    .ACCU 16
    lda FP+F_STATE,x
    and #$00FF.w
    jsr MkKind
    cmp #0.w
    beq MKAR_done16
    lda.w MKA_HEIGHT,x
    sta FP+F_Y,x
    stz FP+F_VY,x
    lda FP+F_STIME,x
    cmp #240.w
    bcc MKAR_done16
    lda #S_STAND.w                      ; EnterState redirects this to falling
    jsl MkCombat_EnterState
MKAR_done16:
    sep #$20
    .ACCU 8
MKAR_done:
    rtl

; Capture-mode fighters animate without AI, source velocity, re-armed
; HitDefs or source TargetLifeAdd. The first valid contact owns the combo.
MkFighterTickFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w MKC_ACTIVE
    and #$00FF.w
    beq MKFT_normal
    ldx fofs
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda #8
    sta FP+F_HTIMER,x
    inc FP+F_STIME,x
    txa
    sep #$20
    .ACCU 8
    cmp.w MKC_OWNER
    bne MKFT_animate
    lda FP+F_FTICK,x
    cmp #1
    bne MKFT_animate
    lda FP+F_FRAME,x
    inc a
    cmp FP+F_NFR,x
    bcc MKFT_animate
    rep #$20
    .ACCU 16
    lda #118.w
    jsl MkCombat_SetAnimSlot
    sec
    rtl
MKFT_animate:
    rep #$20
    .ACCU 16
    jsl MkCombat_AnimTick
    rep #$20
    .ACCU 16
    sec
    rtl
MKFT_normal:
    clc
    rtl

; Successful melee contact, after guard/parry checks and before ordinary
; damage. Carry set when Mr. Karate's contact sequence replaces the HitDef.
MkMeleeContactFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx aofs
    jsr MkIsFighter
    bcc MKMC_no
    lda FP+F_STATE,x
    and #$00FF.w
    jsr MkKind
    cmp #0.w
    beq MKMC_no
    jsr MkContactStart
    rep #$20
    .ACCU 16
    sec
    rtl
MKMC_no:
    rep #$20
    .ACCU 16
    clc
    rtl

; Successful projectile contact, after guard. Each volley has one contact
; owner: later members cannot multiply a fifty-hit super into 150 hits.
MkProjectileContactFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    phx
    phy
    stx.w MKW_SLOT
    lda.w SPARKS+SPK_ATTR,x
    and #$0040.w
    sta aofs
    eor #FP2OFS.w
    sta vofs
    ldx aofs
    jsr MkIsFighter
    bcc MKPC_no
    ldx.w MKW_SLOT
    cpx #SPK_SIZE.w
    lda #0
    bcc +
    inc a
+   tay
    lda.w MKB_KIND,y
    and #$00FF.w
    beq MKPC_no
    pha
    sep #$20
    .ACCU 8
    lda.w MKB_SERIAL,y
    ldx aofs
    cmp.w MKQ_CLAIM,x
    beq MKPC_claimed
    sta.w MKQ_CLAIM,x
    lda.w MKC_ACTIVE
    bne MKPC_claimed
    rep #$20
    .ACCU 16
    pla
    jsr MkContactStart
    bra MKPC_consume
MKPC_claimed:
    rep #$20
    .ACCU 16
    pla
MKPC_consume:
    ldx.w MKW_SLOT
    stz.w SPARKS+SPK_ANIM,x
    rep #$30
    .ACCU 16
    .INDEX 16
    ply
    plx
    sec
    rtl
MKPC_no:
    rep #$30
    .ACCU 16
    .INDEX 16
    ply
    plx
    clc
    rtl

; A16 = 5 or 50. Begin only after actual unguarded overlap. First impact
; and each follow-up use the same fractional budget, including zero-HP
; contacts in a 48-HP/50-hit super. Never round 50 hits up to 50 damage.
MkContactStart:
    sep #$20
    .ACCU 8
    sta.w MKC_TOTAL
    sta.w MKC_LEFT
    cmp #50
    lda #9                              ; prototype 60/1000 -> 9 HP per volley
    bcc +
    lda #48.b                           ; super: 48 HP over 50 contacts (the
                                        ;   144-HP prototype's third, not
                                        ;   MAXHP/3 -- this bar is 200 HP)
+   sta.w MKC_BUDGET
    lda aofs
    sta.w MKC_OWNER
    lda #1
    sta.w MKC_ACTIVE
    stz.w MKC_ACC
    stz.w MKC_HITS
    stz.w MKC_CLOCK
    stz.b pausecnt
    rep #$20
    .ACCU 16
    stz.w MKC_DAMAGE
    stz.w MKC_AGE
    ldx aofs
    stx fofs
    stz FP+F_GRAB,x
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda #118.w
    jsl MkCombat_EnterState
    rep #$20
    .ACCU 16
    lda.w MKC_OWNER
    and #$00FF.w
    sta aofs
    eor #FP2OFS.w
    sta vofs
    jsr MkImpact
    ldx vofs
    stx fofs
    stz FP+F_GRAB,x
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda #S_HIT.w
    jsl MkCombat_EnterState
    rep #$20
    .ACCU 16
    rts

; Consume one real impact, maintain combo/hitstun, apply absolute bounded
; damage (practice keeps HP). Defensive MAX/counter scaling is bypassed.
MkImpact:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w MKC_OWNER
    and #$00FF.w
    sta aofs
    eor #FP2OFS.w
    sta vofs
    sep #$20
    .ACCU 8
    lda.w MKC_ACC
    clc
    adc.w MKC_BUDGET
    sta.w MKC_ACC
    stz.b scr0
MKI_divide:
    lda.w MKC_ACC
    cmp.w MKC_TOTAL
    bcc MKI_divided
    sec
    sbc.w MKC_TOTAL
    sta.w MKC_ACC
    inc.b scr0
    bra MKI_divide
MKI_divided:
    lda.b scr0
    rep #$20
    .ACCU 16
    and #$00FF.w
    sta scr0
    lda.w G_MODE
    and #$00FF.w
    cmp #5
    beq MKI_count
    ldx vofs
    lda FP+F_HP,x
    sec
    sbc scr0
    bcs +
    lda #0
+   sta FP+F_HP,x
    lda.w MKC_DAMAGE
    clc
    adc scr0
    sta.w MKC_DAMAGE
MKI_count:
    jsl MkCombat_ComboBump
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w MKC_OWNER
    and #$00FF.w
    sta aofs
    eor #FP2OFS.w
    sta vofs
    tax
    lda #12
    sta FP+F_HTIMER,x
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda FP+F_X,x
    xba
    and #$00FF.w
    sta scr0
    lda FP+F_Y,x
    xba
    and #$00FF.w
    sta scr1
    lda #(GROUND_Y-40).w
    sec
    sbc scr1
    sta scr1
    lda #SPARK_ANIM_HIT.w
    jsl MkCombat_SparkSpawnAt
    sep #$20
    .ACCU 8
    lda #SFX_HIT_LIGHT.b
    jsl MkCombat_SfxPlay
    sep #$20
    .ACCU 8
    inc.w MKC_HITS
    dec.w MKC_LEFT
    lda #4
    sta.w MKC_CLOCK
    rep #$20
    .ACCU 16
    rts

MkRelease:
    sep #$20
    .ACCU 8
    stz.w MKC_ACTIVE
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w MKC_OWNER
    and #$00FF.w
    sta aofs
    eor #FP2OFS.w
    sta vofs
    tax
    stx fofs
    stz FP+F_GRAB,x
    lda #S_DOWN.w
    jsl MkCombat_EnterState
    rep #$20
    .ACCU 16
    ldx vofs
    lda #-$0300.w
    sta FP+F_VY,x
    lda #30
    sta FP+F_HTIMER,x
    ldx aofs
    stx fofs
    stz FP+F_GRAB,x
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda FP+F_Y,x
    beq +
    lda #S_JUMP.w
    bra ++
+   lda #S_STAND.w
++  jsl MkCombat_EnterState
    rep #$20
    .ACCU 16
    rts

; One visit per live frame; pause/join menus run before this hook. First
; contact pins the victim without teleporting, so dodged/blocked casts fail.
MkCombatTickFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.b pausecnt
    and #$00FF.w
    beq +
    sep #$20
    .ACCU 8
    rtl
+   lda.b fofs
    pha
    jsr MkVolleyTick
    sep #$20
    .ACCU 8
    lda.w MKC_ACTIVE
    beq MKCT_done
    rep #$20
    .ACCU 16
    inc.w MKC_AGE
    lda.w MKC_OWNER
    and #$00FF.w
    tax
    lda FP+F_HP,x
    beq MKCT_release
    txa
    eor #FP2OFS.w
    tax
    lda FP+F_HP,x
    beq MKCT_release
    lda.w MKC_AGE
    cmp #240.w
    bcs MKCT_release
    sep #$20
    .ACCU 8
    lda.w MKC_CLOCK
    beq MKCT_hit
    dec.w MKC_CLOCK
    bne MKCT_done
MKCT_hit:
    jsr MkImpact
    sep #$20
    .ACCU 8
    lda.w MKC_LEFT
    bne MKCT_done
MKCT_release:
    jsr MkRelease
MKCT_done:
    rep #$30
    .ACCU 16
    .INDEX 16
    pla
    sta fofs
    sep #$20
    .ACCU 8
    rtl

; Preserve the native caller's vx, damage/sound and guard row. A queued
; member reuses the launch row even after the fighter has recovered.
MkProjectileSpawnFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx fofs
    jsr MkIsFighter
    bcs MKPS_karate
    jml MkNativeProjSpawnFar
MKPS_karate:
    lda scr0
    sta.w MKW_VX
    lda scr1
    sta.w MKW_DMG
    lda scr3
    sta.w MKW_GUARD
    lda fofs
    sta.w MKW_FOFS
    lda FP+F_STATE,x
    and #$00FF.w
    sta.w MKW_SID
    jsr MkKind
    cmp #0.w
    beq MKPS_normal
    sep #$20
    .ACCU 8
    lda.w MKQ_LATCH,x
    bne MKPS_duplicate
    lda #1
    sta.w MKQ_LATCH,x
    inc.w MKQ_SERIAL,x
    lda.w MKQ_SERIAL,x
    bne +
    inc.w MKQ_SERIAL,x                  ; serial zero means no claim
+   lda #0
    sta.w MKQ_CLAIM,x
    lda #3
    sta.w MKQ_LEFT,x
    lda #0
    sta.w MKQ_CD,x
    rep #$20
    .ACCU 16
    lda #240.w
    sta.w MKQ_TTL,x
    lda.w MKW_SID
    sta.w MKQ_SID,x
    lda.w MKW_VX
    sta.w MKQ_VX,x
    lda.w MKW_DMG
    sta.w MKQ_DMG,x
    lda.w MKW_GUARD
    sta.w MKQ_GUARD,x
    jsr MkLaunchQueued
    rtl
MKPS_duplicate:
    rep #$20
    .ACCU 16
    clc
    rtl
MKPS_normal:
    lda.w MKW_VX
    sta scr0
    lda.w MKW_DMG
    sta scr1
    lda.w MKW_GUARD
    sta scr3
    jml MkNativeProjSpawnFar

; X16 = side. Failed allocation keeps the member pending and retries; a
; full slot is never evicted. At most two actual projectiles exist at once.
MkLaunchQueued:
    rep #$30
    .ACCU 16
    .INDEX 16
    stx fofs
    phx
    lda FP+F_STATE,x
    pha
    lda.w MKQ_SID,x
    sta FP+F_STATE,x
    lda.w MKQ_VX,x
    sta scr0
    lda.w MKQ_DMG,x
    sta scr1
    lda.w MKQ_GUARD,x
    sta scr3
    jsl MkNativeProjSpawnFar
    php
    stx.w MKW_SLOT
    rep #$30
    .ACCU 16
    .INDEX 16
    plp
    bcc MKL_failed
    pla
    ldx fofs
    sta FP+F_STATE,x
    plx
    inc.w MKC_SHOTS
    sep #$20
    .ACCU 8
    dec.w MKQ_LEFT,x
    lda #12
    sta.w MKQ_CD,x
    rep #$20
    .ACCU 16
    lda.w MKQ_SID,x
    jsr MkKind
    pha
    lda.w MKQ_SERIAL,x
    and #$00FF.w
    pha
    lda FP+F_Y,x
    xba
    and #$00FF.w
    sta scr2
    ldx.w MKW_SLOT
    ; The contact controller owns all repeats; disable generic super pins.
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    and #$FE.b
    sta.w SPARKS+SPK_ATTR,x
    rep #$20
    .ACCU 16
    lda #0
    cpx #SPK_SIZE.w
    bcc +
    inc a
+   tay
    sep #$20
    .ACCU 8
    lda #0
    sta.w RT_PROJHITS,y
    rep #$20
    .ACCU 16
    pla
    sep #$20
    .ACCU 8
    sta.w MKB_SERIAL,y
    rep #$20
    .ACCU 16
    pla
    sep #$20
    .ACCU 8
    sta.w MKB_KIND,y
    rep #$20
    .ACCU 16
    lda scr2
    beq +
    lda #(GROUND_Y-40).w
    sec
    sbc scr2
    sta.w SPARKS+2,x                    ; cast height follows the aerial user
+   sec
    rts
MKL_failed:
    rep #$30
    .ACCU 16
    .INDEX 16
    pla
    ldx fofs
    sta FP+F_STATE,x
    plx
    sep #$20
    .ACCU 8
    lda #3
    sta.w MKQ_CD,x
    rep #$20
    .ACCU 16
    clc
    rts

MkVolleyTick:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0
    jsr MKVT_side
    ldx #FP2OFS.w
    jsr MKVT_side
    rep #$20
    .ACCU 16
    rts
MKVT_side:
    sep #$20
    .ACCU 8
    lda.w MKQ_LEFT,x
    beq MKVT_done
    rep #$20
    .ACCU 16
    lda FP+F_HP,x
    beq MKVT_clear
    lda.w MKQ_TTL,x
    beq MKVT_clear
    dec.w MKQ_TTL,x
    sep #$20
    .ACCU 8
    lda.w MKQ_CD,x
    beq MKVT_launch
    dec.w MKQ_CD,x
    bne MKVT_done
MKVT_launch:
    jsr MkLaunchQueued
    rep #$20
    .ACCU 16
    rts
MKVT_clear:
    sep #$20
    .ACCU 8
    stz.w MKQ_LEFT,x
MKVT_done:
    rep #$20
    .ACCU 16
    rts
.ENDS
.ORGA $5300                         ; gap after CloseNormalCode ($5249)
.SECTION "MrKarateProjectile" FORCE
MkNativeProjSpawnFar:
    rep #$20
    .ACCU 16
    ldx #0
    lda.w SPARKS+SPK_ANIM,x
    beq +
    ldx #SPK_SIZE
    lda.w SPARKS+SPK_ANIM,x
    beq +
    ; A projectile may evict a cosmetic spark, but never another active
    ; projectile. This prevents a hitbox from silently disappearing.
    ldx #0
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    bpl PS_slot
    ldx #SPK_SIZE
    lda.w SPARKS+SPK_ATTR,x
    bpl PS_slot
    rep #$20
    .ACCU 16
    inc.w RT_PROJDROP
    clc
    rtl
PS_slot:
    rep #$20
    .ACCU 16
+   ldy fofs
    lda FP+F_X,y                        ; positions are 8.8 fixed point
    pha
    lda FP+F_FACING,y
    bmi +                               ; left-facing: spawn left of caster
    pla
    clc
    adc #14<<8.w
    bra ++
+   pla
    sec
    sbc #14<<8.w
++  xba                                ; sparks are stored in screen pixels
    and #$00FF.w
    sta.w SPARKS,x
    lda FP+F_Y,y                        ; convert world height to screen Y
    xba
    and #$00FF.w
    sta scr2
    lda #GROUND_Y.w
    sec
    sbc scr2
    sec
    sbc #40.w                           ; mid torso, ~40px above the floor
    sta.w SPARKS+2,x
    rep #$20
    .ACCU 16
    phx
    ldx #sptr.w
    ldy #CH_PROJFXTAB.w
    jsl MkCombat_CharPtr                         ; char-specific anim pointer table
    plx                                 ; restore spark slot base
    sep #$20
    .ACCU 8
    lda #:ProjFxGlobal
    sta sptr+2
    rep #$20
    .ACCU 16
    lda.w RT_PROJAIR                    ; per-shot override (air Shippuu Ken)
    and #$00FF.w
    beq PS_readmode
    lda #2.w
    bra PS_havemode
PS_readmode:
    ; ProjFxTab header: .dw primary anim, .dw alternate anim, .db height.
    ; The height byte is always at offset 4; reading offset 2 here would
    ; pick the low byte of the second anim pointer (non-zero), which sent
    ; every primary shot to the floor (hadouken at GROUND_Y instead of the
    ; caster's torso).  Ground rows keep mode 1 and are unaffected.
    ldy #4
    lda [sptr],y                        ; spawn-height mode
    and #$00FF.w                        ;   0 = caster torso, 1 = floor,
PS_havemode:
    beq +                               ;   2 = fixed upper torso (air shots)
    cmp #2.w
    bne PS_ground
    lda #(GROUND_Y-60).w                ; airborne throw: keep the ball at a
    sta.w SPARKS+2,x                    ;   height a standing victim can hit
    bra +
PS_ground:
    lda #GROUND_Y.w
    sta.w SPARKS+2,x
+
    sep #$20
    .ACCU 8
    lda #90.b                           ; normal projectile lifetime
    sta.w SPARKS+SPK_TTL,x
    rep #$20
    .ACCU 16
    jsl ProjBallisticSetup              ; per-shot offset / high-drop profile
    ldy #0
    lda.w RT_PROJFX2                    ; 0 = primary ProjFxAnim,
    and #$0001.w                        ; 1 = the alternate geyser clip
    beq +
    ldy #2
+   lda [sptr],y
    sta.w SPARKS+SPK_ANIM,x
    ; Yuki's Kusanagi super (sid 89) draws Kyo in the alternate clip.  Against
    ; Kyo himself that would duplicate the opponent, so fall back to the
    ; primary clip -- the visible shot the super used to draw -- instead of
    ; hiding it.  Hitbox, damage and guard are untouched.
    ldy fofs
    lda FP+F_STATE,y
    and #$00FF.w
    cmp #89
    bne PS_kyo_done
    lda FP+F_CHAR,y
    cmp #CharYuki
    bne PS_kyo_done
    lda fofs
    eor #FP2OFS.w
    tay
    lda FP+F_CHAR,y
    cmp #CharKyo
    beq PS_kyo_primary
    cmp #CharKyonests
    beq PS_kyo_primary
    cmp #CharKyoash
    bne PS_kyo_done
PS_kyo_primary:
    ldy #0
    lda [sptr]
    sta.w SPARKS+SPK_ANIM,x
PS_kyo_done:
    sep #$20
    .ACCU 8
    lda #:ProjFxGlobal
    sta.w SPARKS+SPK_BANK,x
    rep #$20
    .ACCU 16
    lda scr0                            ; vx magnitude -> signed by facing
    ldy fofs
    lda FP+F_FACING,y
    bmi +
    lda scr0
    bra ++
+   lda scr0
    eor #$FFFF.w
    inc a
++  sta.w SPARKS+SPK_VX,x
    lda scr1                            ; dmg byte -> SPK_AY low
    and #$00FF.w
    sta.w SPARKS+SPK_AY,x
    sep #$20
    .ACCU 8
    lda scr1+1                          ; launch state's HitDef sound
    sta.w SPARKS+SPK_AY+1,x
    lda scr3                            ; per-shot guard mask (H/M/L/A<<4)
    sta.w SPARKS+SPK_GRD,x
    stz.w SPARKS+SPK_FIDX,x             ; begin at frame 0
    rep #$20
    .ACCU 16
    jsl ProjVyFixFar                    ; default vy=0; Benimaru strong arcs
    lda.w SPARKS+SPK_ANIM,x             ; anim rec: byte0 = nframes
    sta sptr
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_BANK,x
    sta sptr+2
    rep #$20
    .ACCU 16
    ldy #1                              ; first frame pointer -> ticks
    lda [sptr],y
    sta sptr
    sep #$20
    .ACCU 8
    lda [sptr]
    sta.w SPARKS+SPK_FTIM,x
    lda #$80.b                          ; projectile flag; OAM palette is per side
    ldy fofs
    cpy #FP2OFS.w                       ; Y remains 16-bit even with acc8
    bne +
    ora #$40.b                          ; owner = P2
+   sta.w SPARKS+SPK_ATTR,x
    sep #$20
    .ACCU 8
    lda.w RT_PROJFX2
    and #$01.b
    beq +
    lda.w SPARKS+SPK_ATTR,x
    ora #$08.b                          ; bit3 = one-shot clip (no loop)
    sta.w SPARKS+SPK_ATTR,x
+   ldy fofs
    lda FP+F_FACING+1,y                 ; bit4: projectile art faces left
    bpl +
    lda.w SPARKS+SPK_ATTR,x
    ora #$10.b
    sta.w SPARKS+SPK_ATTR,x
+   ldy fofs
    lda FP+F_STATE,y                     ; remember whether the launch state
    jsl MkCombat_IsSpecialState                    ;   was a special/super (survivor)
    bcc PTS_idx0                          ; not a special: single-hit setup
    lda.w SPARKS+SPK_ATTR,x
    ora #$20.b                           ; bit5 = special/super projectile
    sta.w SPARKS+SPK_ATTR,x
    stz scr3                             ; spark slot -> 0/1 table index
    cpx #SPK_SIZE
    bcc PTS_idx0
    lda #1
    sta scr3
PTS_idx0:
    ldy scr3
    lda #0                               ; single-hit by default
    sta.w RT_PROJHITS,y
    sta.w RT_PROJCD,y
    sta.w RT_PROJHIT,x                   ; no contact yet: let the shot fly
    ldy fofs
    lda FP+F_STATE,y
    cmp #S_SUPPER.b                      ; 85..89 = super projectile:
    bcc PTS_notmulti                     ;   five sequential hits
    cmp #90.b
    bcs PTS_notmulti
    lda #5
    ldy scr3
    sta.w RT_PROJHITS,y
    ; Geese's Raging Storm is a single-hit tall anti-air pillar in KOF98,
    ; not the generic five-contact super projectile.  SPK_GRD bit0 marks
    ; the tall hitbox (the guard bits themselves live in 4-7).
    rep #$20
    .ACCU 16
    ldy fofs
    lda FP+F_CHAR,y
    cmp #CharGeese
    bne PTS_notstorm
    sep #$20
    .ACCU 8
    lda FP+F_STATE,y
    cmp #85
    beq PTS_storm
    cmp #86
    beq PTS_storm
PTS_notstorm:
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    ora #$01.b                        ; multi-hit shot: exempt from the
    sta.w SPARKS+SPK_ATTR,x           ;   one-proj-per-fall cap
    bra PTS_sakura_check
PTS_storm:
    lda #1
    ldy scr3
    sta.w RT_PROJHITS,y
    lda.w SPARKS+SPK_GRD,x
    ora #$01.b
    sta.w SPARKS+SPK_GRD,x
PTS_sakura_check:
    ; Sakura's Shinkuu travels far, so it lands 8 contacts (9 HP each)
    ; instead of the generic five-contact super sequence.
    rep #$20
    .ACCU 16
    ldy fofs
    lda FP+F_CHAR,y
    cmp #CharSakura
    bne PTS_notmulti
    sep #$20
    .ACCU 8
    lda FP+F_STATE,y
    cmp #85
    beq PTS_sak_many
    cmp #86
    beq PTS_sak_many
    cmp #87
    beq PTS_sak_many
    bra PTS_notmulti
PTS_sak_many:
    lda #8
    ldy scr3
    sta.w RT_PROJHITS,y
PTS_notmulti:
+   rep #$20
    .ACCU 16
    sec
    rtl

.ENDS
