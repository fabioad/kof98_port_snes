; Secret Robert form and flawless campaign boss route. All entry points
; preserve the engine DBR/D conventions; cinematic never runs in attract.
.DEFINE SAFE1       $7E7F12             ; trusted P1 pick (campaign/survivor)
.BASE $00
.BANK 122 SLOT 0
.ORGA $0000
.SECTION "MrKarateCode" FORCE
MkResetFar:
    sep #$20
    .ACCU 8
    rep #$10
    .INDEX 16
    ldx #9
-   stz.w MK_LOST,x
    dex
    bpl -
    stz.w MK_PICK
    rtl

; A8 candidate, X16 fighter/pad offset. Only human selections get the form;
; the side is latched so the round sanitizer can tell a real pick apart from
; a form the CPU was never allowed to choose.
MkSelectFar:
    ; Resolve CJ before recording the trusted P1 pick for campaign/Survivor.
    cmp #JOHN_ID.b
    bne MKSEL_robert
    lda.b msuok
    beq MKSEL_john
    cpx #0
    bne +
    lda.b cpu1
    bra ++
+   lda.b cpu2
++  bne MKSEL_john
    rep #$20
    .ACCU 16
    lda FP+F_JOY,x
    and #(JOY_L|JOY_R).w
    cmp #(JOY_L|JOY_R).w
    sep #$20
    .ACCU 8
    bne MKSEL_john
    lda #CJ_ID.b
    bra MKSEL_out
MKSEL_john:
    lda #JOHN_ID.b
    bra MKSEL_out
MKSEL_robert:
    cmp #ROBERT_ID.b
    bne MKSEL_out
    pha
    lda.b msuok
    beq MKSEL_base
    cpx #0
    bne +
    lda.b cpu1
    bra ++
+   lda.b cpu2
++  bne MKSEL_base
    rep #$20
    .ACCU 16
    lda FP+F_JOY,x
    and #(JOY_L|JOY_R).w
    cmp #(JOY_L|JOY_R).w
    sep #$20
    .ACCU 8
    bne MKSEL_base
    pla
    ; Record the human pick.  StartFight calls MkSanitizeFar on every round
    ; and drops Mr. Karate whenever both sides are CPU-driven (attract demo,
    ; CPU-vs-CPU harnesses); the latch preserves a form the player chose.
    lda.w MK_PICK
    cpx #0
    bne MKSEL_p2
    ora #$01
    bra MKSEL_latched
MKSEL_p2:
    ora #$02
MKSEL_latched:
    sta.w MK_PICK
    lda #MRKARATE_ID.b
    bra MKSEL_out
MKSEL_base:
    pla
MKSEL_out:
    ; A = final pick.  Keep the human P1 pick outside sel1's DP byte, which
    ; the fight/presentation path can double during a long round.  Resolve
    ; Kyo's L/R variants here too so the trusted value is the real fighter.
    cpx #0
    bne MKSEL_ret
    pha
    lda.b cpu1
    bne MKSEL_ret_pla
    pla
    cmp #KYO_BASE_ID.b
    bne MKSEL_save
    lda.b msuok
    beq MKSEL_save
    rep #$20
    .ACCU 16
    lda FP+F_JOY,x
    and #(JOY_L|JOY_R).w
    cmp #JOY_L.w
    beq MKSEL_save_nests
    cmp #JOY_R.w
    beq MKSEL_save_ash
    sep #$20
    .ACCU 8
    lda #KYO_BASE_ID.b
    bra MKSEL_save
MKSEL_save_nests:
    sep #$20
    .ACCU 8
    lda #KYO_NESTS_ID.b
    bra MKSEL_save
MKSEL_save_ash:
    sep #$20
    .ACCU 8
    lda #KYO_ASH_ID.b
MKSEL_save:
    sta.l SAFE1
MKSEL_ret:
    rtl
MKSEL_ret_pla:
    pla
    rtl

; Stage policy runs after team members have populated sel1/sel2.
MkSanitizeFar:
    sep #$20
    .ACCU 8
    ; Single Play/Survivor: the fight/presentation path can double sel1
    ; during a long round.  Restore the human's trusted pick before the
    ; descriptor is loaded; Team Play reloads sel1 from T_TEAM1 itself.
    lda.w G_MODE
    cmp #1.b
    beq MKST_restore1
    cmp #4.b
    bne MKST_after_restore1
MKST_restore1:
    lda.w C_HUMAN_SIDE
    bne MKST_after_restore1
    lda.l SAFE1
    cmp #NROSTER.b
    bcs MKST_after_restore1
    sta.b sel1
MKST_after_restore1:
    lda.b msuok
    beq MKST_strip
    lda.w MK_PICK                        ; a human selected the form: keep it
    bne MKST_clean
    lda.b cpu1
    and.b cpu2
    beq MKST_clean
MKST_strip:
    rep #$10
    .INDEX 16
    ldx #5
MKST_team_clean:
    lda.w T_TEAM1,x
    cmp #MRKARATE_ID.b
    bne +
    lda #ROBERT_ID.b
    sta.w T_TEAM1,x
+   dex
    bpl MKST_team_clean
    lda.b sel1
    cmp #MRKARATE_ID.b
    bne +
    lda #ROBERT_ID.b
    sta.b sel1
+   lda.b sel2
    cmp #MRKARATE_ID.b
    bne MKST_clean
    lda #ROBERT_ID.b
    sta.b sel2
MKST_clean:
    rtl
MkStageFar:
    sep #$20
    .ACCU 8
    lda.w MK_BOSS
    beq MKST_no
    lda #5
    sta.w STAGEF
    sec
    rtl
MKST_no:
    clc
    rtl

; Called at confrontation 6 only. Survivor intentionally has no secret route.
MkChooseBossFar:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #1
    beq +
    cmp #2
    bne MKCB_no
+   lda.b msuok
    beq MKCB_no
    lda.b cpu1
    and.b cpu2
    bne MKCB_no
    lda.w MK_LOST
    beq MKCB_yes
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0
    lda.w C_HUMAN_SIDE
    and #$00FF.w
    beq +
    ldx #FP2OFS.w
+   lda FP+F_JOY,x
    and #(JOY_L|JOY_R|JOY_A).w
    cmp #(JOY_L|JOY_R|JOY_A).w
    sep #$20
    .ACCU 8
    bne MKCB_no
MKCB_yes:
    lda #1
    sta.w MK_BOSS
    stz.w MK_SEEN
    stz.w MK_MUSIC
    lda #5
    sta.w C_STAGE
    lda.w G_MODE
    cmp #2
    beq MKCB_team
    lda.w C_HUMAN_SIDE
    bne +
    lda #MRKARATE_ID.b
    sta.b sel2
    bra MKCB_done
+   lda #MRKARATE_ID.b
    sta.b sel1
    bra MKCB_done
MKCB_team:
    lda.w C_HUMAN_SIDE
    bne +
    lda #MRKARATE_ID.b
    sta.w T_TEAM2
    sta.w T_TEAM2+1
    bra ++
+   lda #MRKARATE_ID.b
    sta.w T_TEAM1
    sta.w T_TEAM1+1
++  stz.w T_I1
    stz.w T_I2
    lda #2
    sta.w T_N2
MKCB_done:
    rep #$10
    .INDEX 16
    sec
    rtl
MKCB_no:
    rep #$10
    .INDEX 16
    clc
    rtl

; Record every lost round, including individual team members and
; continues. Carry set means this routine handled the secret solo scoring.
MkScoreFar:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #1
    beq +
    cmp #2
    bne MKSC_no
+   lda.w C_PVP
    bne MKSC_no
    lda.b roundwin
    beq +
    lda.w C_HUMAN_SIDE
    inc a
    cmp.b roundwin
    beq +
    lda #1
    sta.w MK_LOST
+   lda.w MK_BOSS
    beq MKSC_no
    lda.w G_MODE
    cmp #1
    bne MKSC_no
    lda.b roundwin
    beq MKSC_next
    dec a
    rep #$30
    .ACCU 16
    .INDEX 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    inc.b wins1,x
    lda.b wins1,x
    cmp #2
    bcc MKSC_next
    lda.w C_HUMAN_SIDE
    inc a
    cmp.b roundwin
    bne MKSC_loss
    lda #1
    sta.w MATWON
    jsl BossEndingFar
    sec
    rtl
MKSC_loss:
    lda #2
    sta.b nextflag
    bra MKSC_show
MKSC_next:
    inc.b roundno
    lda #1
    sta.b nextflag
MKSC_show:
    jsl MkCall_ShowTitle
    sep #$20
    .ACCU 8
    sec
    rtl
MKSC_no:
    clc
    rtl

MkEndingFar:
    sep #$20
    .ACCU 8
    lda.w MK_BOSS
    sta.w MK_END
    rtl

; First setup shows a three-second still. Rebuilding the fight afterwards
; restores all VRAM/PPU state before Crystal and the entrance begin.
MkFightSetupFar:
    sep #$20
    .ACCU 8
    lda.b msuok
    beq MKFS_out
    lda.w MK_BOSS
    beq MKFS_out
    lda.w MK_SEEN
    bne MKFS_enter
    lda #1
    sta.w MK_SEEN
    sta.w MK_PHASE
    lda #GS_MK_SCENE.b
    sta.b gamestate
    rep #$20
    .ACCU 16
    lda #180.w
    sta.w MK_TICK
    jsl MkLoadStillFar
    sep #$20
    .ACCU 8
    rtl
MKFS_enter:
    lda.w MK_PHASE
    cmp #2
    bne MKFS_out
    lda #3
    sta.w MK_PHASE
    lda.w C_HUMAN_SIDE
    beq +
    lda #0
    bra ++
+   lda #FP2OFS.b
++  sta.w MK_SIDE
    rep #$30
    .ACCU 16
    .INDEX 16
    and #$00FF.w
    tax
    stx.b fofs
    lda #$F000.w                       ; 240 px above the ground: offscreen
    sta FP+F_Y,x
    lda #S_STAND.w
    jsl MkCall_EnterState
MKFS_out:
    sep #$20
    .ACCU 8
    rtl

MkVolume:
    rep #$30
    .ACCU 16
    .INDEX 16
    and #$00FF.w
    phd
    pha
    lda #0
    tcd
    jsl spcSetModuleVolume
    rep #$20
    .ACCU 16
    pla
    pld
    sep #$20
    .ACCU 8
    rts

MkSceneTickFar:
    sep #$20
    .ACCU 8
    lda.w MK_PHASE
    cmp #2
    beq MKSCENE_fade
    rep #$20
    .ACCU 16
    dec.w MK_TICK
    bne MKSCENE_out16
    sep #$20
    .ACCU 8
    lda #2
    sta.w MK_PHASE
    lda #240
    sta.w MK_VOLUME
    rtl
MKSCENE_fade:
    lda.w MK_VOLUME
    beq MKSCENE_start
    sec
    sbc #4
    sta.w MK_VOLUME
    jsr MkVolume
    rtl
MKSCENE_start:
    lda #1
    sta.w MK_MUSIC
    stz.w MUSIC_VALID
    lda.w G_MODE
    cmp #2
    bne +
    lda #1
    sta.w OR_READY                     ; resume the already chosen order
+   jsl MkCall_StartFight
    rtl
MKSCENE_out16:
    sep #$20
    .ACCU 8
    rtl

MkIntroTickFar:
    sep #$20
    .ACCU 8
    lda.w MK_PHASE
    cmp #3
    beq MKIT_enter
    jml MkNormalIntro
MKIT_enter:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w MK_SIDE
    and #$00FF.w
    tax
    stx.b fofs
    lda FP+F_Y,x
    sec
    sbc #$0200.w
    sta FP+F_Y,x
    bne MKIT_draw
    sep #$20
    .ACCU 8
    stz.w MK_PHASE
    rep #$20
    .ACCU 16
    lda #S_INTRO.w
    jsl MkCall_EnterState
MKIT_draw:
    jsl MkCall_BuildOam
    rep #$20
    .ACCU 16
    rtl

; One fixed Mode-1 card. InVCopy/InCgRam accept the same I_SRC as EndLoad.
MkLoadStillFar:
    sep #$20
    .ACCU 8
    lda #0
    sta.l NMITIMEN
    sta.l HDMAEN
    lda #$80.b
    sta.l INIDISP
    stz.b huddirty
    rep #$30
    .ACCU 16
    .INDEX 16
    lda #MkSleepChr.w
    sta.b I_SRC
    lda #:MkSleepChr
    sta.b I_SRC+2
    lda #(MkSleepChrEnd-MkSleepChr).w
    sta.b I_LEN
    ldx #$2000.w
    jsl MkCall_InVCopy
    rep #$20
    .ACCU 16
    lda #MkSleepMap.w
    sta.b I_SRC
    lda #:MkSleepMap
    sta.b I_SRC+2
    lda #2048.w
    sta.b I_LEN
    ldx #$1800.w
    jsl MkCall_InVCopy
    rep #$20
    .ACCU 16
    lda #MkSleepPal.w
    sta.b I_SRC
    lda #:MkSleepPal
    sta.b I_SRC+2
    lda #128.w
    sta.b I_LEN
    ldx #0
    jsl MkCall_InCgRam
    jsl MkCall_InM1Regs
    sep #$20
    .ACCU 8
    lda #15
    sta.l INIDISP
    lda #$81.b
    sta.l NMITIMEN
    rtl
MkNormalIntro:
    php
    sep #$20
    .ACCU 8
    lda.w INTRO_DUCK
    bne +
    lda #1
    sta.w INTRO_DUCK
    lda #32                             ; duck the stage music under the intro
    jsr MkVolume
+   plp
    ldx #0
    jsl MkCall_KoMute
    stx fofs
    jsl MkCall_TickFighter
    ldx #FP2OFS
    jsl MkCall_KoMute
    stx fofs
    jsl MkCall_TickFighter
    jsl MkCall_TickSpark
    jsl MkCall_BuildOam
    sep #$20
    .ACCU 8
    lda.b gotime                          ; announcer already running?
    beq IT_entrance
    dec a                                 ; READY+GO still playing: keep both
    sta.b gotime                          ;   fighters idle until it finishes
    beq IT_start
    jsl MkCall_BannerTick                        ; FIGHT! logo keeps its countdown
IT_out:
    rep #$20
    .ACCU 16
    rtl
IT_entrance:
    rep #$20
    .ACCU 16
    lda FP+F_STATE
    ora FP+F_STATE+FP2OFS                 ; either one still mid-intro?
    bne IT_out
    sep #$20
    .ACCU 8
    lda #99.b                             ; clock is drawn now, but only
    sta rsecs                             ;   counts once gotime expires
    stz rframe
    jsl DrawTimer
    rep #$20                            ; FIGHT! logo across the centre
    .ACCU 16                            ;   rows; bantime clears it later
    lda #HudGo.w
    sta scr2
    lda #:HudGo.w
    sta scr2+2
    jsl BannerDrawFar
    sep #$20
    .ACCU 8
    lda #45.b
    sta.w BANTIME
    lda #1                              ; rows 9/10 lie outside the live HUD
    sta.w RT_HUDFULL                    ;   bands: the banded live-play flush
    lda huddirty                        ;   would skip the GO! logo otherwise
    ora #HUD_FULL
    sta huddirty
    lda #SFX_FIGHT.b
    jsl MkCall_SfxPlay
    lda #GO_WAIT.b
    sta.b gotime
    rep #$20
    .ACCU 16
    rtl
IT_start:
    lda #0
    sta.w T_ENTERFLAG                    ; entrance finished: camera free
    lda #1.b                              ; GO over -> round is live
    sta gamestate
    php
    sep #$20
    .ACCU 8
    lda #240                            ; restore the stage music for the bout
    jsr MkVolume
    lda #0
    sta.w INTRO_DUCK
    plp
    rep #$20
    .ACCU 16
    rtl


MkCampStageFar:
    jsl MkStageFar
    bcc +
    rtl
+
    sep #$20
    .ACCU 8
    lda.w G_MODE
    beq CS_vs
    cmp #1
    beq CS_force
    cmp #2
    beq CS_force
    cmp #3
    beq CS_force
    cmp #4
    beq CS_force
    cmp #5
    beq CS_force
CS_random:
    lda #$FF.b                            ; free/versus: StagePick stays random
    sta.w STAGEF
    rtl
CS_vs:
    lda.b roundno
    cmp #1.b
    beq CS_random                         ; choose a fresh stage for the match
    lda.b stageidx
    sta.w STAGEF                          ; Single VS keeps it for every round
    rtl
CS_force:
    lda.w C_STAGE                         ; fixed for all rounds/members
    sta.w STAGEF
    rtl


MkEndRouteFar:
    sep #$20
    .ACCU 8
    lda.w MK_END
    beq +
    jml SvEndEnter
+   rtl

MkCampPickStageFar:
    sep #$20
    .ACCU 8
    inc rng
    lda.b rng
    eor.b framecnt
    jsl MkCall_ModStg
    cmp #5
    beq MkCampPickStageFar                     ; Rugal's stage is boss-only
    sta.w C_STAGE
    rtl

MkBossEndingFar:
    jsl MkEndingFar
    sep #$20
    .ACCU 8
    lda #1
    sta.w E_BLACKIN
    stz.b nextflag
    lda #15
    sta.b fadelevel
    lda #GS_BOSS_FADE.b
    sta.b gamestate
    rtl



; HitOne's downed-victim gate, called with vofs set.  Returns scr5=1 when
; the hit must be refused.  CJ's crouching strong punch may juggle an
; airborne S_DOWN victim launched by his crouching strong kick.
; Crouch-cancel selector for StCrouchAtk.  Returns 1 for CJ's connected
; crouching strong punch -> long jump, 2 for the connected crouching strong
; kick -> crouching strong punch (trip juggle), 0 otherwise.
CrouchCancelFar:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx fofs
    lda FP+F_CHAR,x
    cmp #CharCj.w
    bne CCH_no
    lda FP+F_HITDONE,x
    and #$00FF.w
    beq CCH_no
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_CSPUNCH.w
    bne CCH_chk
    lda FP+F_JOY,x
    and #(JOY_UP).w
    beq CCH_no
    lda #1.w
    bra CCH_out
CCH_chk:
    cmp #S_CSKICK.w
    bne CCH_no
    lda FP+F_JOY,x
    and #(JOY_X).w
    beq CCH_no
    lda #2.w
    bra CCH_out
CCH_no:
    lda #0.w
CCH_out:
    plp
    rtl

DownedGateFar:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx vofs
    lda FP+F_GRAB,x
    and #$00FF.w
    bne DG_block
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_DOWN.w
    bne DG_getup
    lda FP+F_Y,x
    beq DG_block
    ldx aofs
    lda FP+F_CHAR,x
    cmp #CharCj.w
    bne DG_block
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_CSPUNCH.w
    bne DG_block
    bra DG_allow
DG_getup:
    cmp #S_GETUP.w
    beq DG_block
DG_allow:
    sep #$20
    .ACCU 8
    stz scr5
    plp
    rtl
DG_block:
    sep #$20
    .ACCU 8
    lda #1
    sta scr5
    plp
    rtl

MkSleepChr: .INCBIN "gen_fight/mrkarate_sleep.chr"
MkSleepChrEnd:
MkSleepMap: .INCBIN "gen_fight/mrkarate_sleep.map"
MkSleepPal: .INCBIN "gen_fight/mrkarate_sleep.pal"
.ENDS
