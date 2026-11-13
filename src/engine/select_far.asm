; ============================================================================
; select_far.asm — P2 takeover helpers for the character select screen.
;
; They live in bank 126 (CPU $3E:E500) because the 32 KiB Fight window is
; full.  SelTick calls them with JSL; SfxPlayFar supplies the same-bank
; bridge back into the Fight bank.
; ============================================================================
.BASE $C0
.BANK 126 SLOT 0
.ORGA $E500
.SECTION "SelectHelpers" FORCE

; P1 START reclaims the P2/CPU choice in solo modes.  No-op in VS modes or
; once P2 has confirmed a fighter.
SelP1ReclaimCheck:
    sep #$20
    .ACCU 8
    lda.w M_START_SIDE
    bne SPR_no                            ; P2 started: P1 START joins, not reclaims
    lda.w G_MODE
    beq SPR_no                            ; VS: both sides are already human
    cmp #3
    beq SPR_no                            ; Team VS: both sides human
    lda.b cpu2
    bne SPR_no
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    and #JOY_ST.w
    beq SPR_no
    sep #$20
    .ACCU 8
    lda #1
    sta.b cpu2                            ; hand the P2 slot back to the CPU
    stz.b lock2
    lda.b framecnt
    clc
    adc #60.b
    sta.w SCPUT2
    lda #SFX_BACK.b
    jsl SfxPlayFar
SPR_no:
    rep #$20
    .ACCU 16
    rtl

; P2 START or a face button takes the P2/CPU choice over.  Carry set means
; the press was consumed and the caller must skip P2 movement/lock this frame.
SelP2JoinCheck:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    and #(JOY_ST|JOY_A|JOY_X|JOY_Y).w
    beq SPJ_no
    sep #$20
    .ACCU 8
    lda.b cpu2
    beq SPJ_no
    lda.b lock2
    bne SPJ_no
    stz.b cpu2
    stz.b lock2
    lda #SFX_SELECT.b
    jsl SfxPlayFar
    sec
    rtl
SPJ_no:
    clc
    rtl


; Abort a mid-flight fighter CHR stream before the select screen rebuilds
; OBJ/BG VRAM.  Called from JoinEnter; kept here so the Fight bank does not
; grow by the eight clearing stores.
JoinStreamStop:
    sep #$20
    .ACCU 8
    stz.w SP_KIND
    stz.w SP_KIND+2
    stz.w SP_COUNT
    stz.w SP_COUNT+2
    stz.w SP_LEN
    stz.w SP_DST
    stz FP+F_DMAREQ
    stz FP+F_DMAREQ+FP2OFS
    rep #$20
    .ACCU 16
    rtl

; Prepare the stage/timers for a mid-fight join without running CampStart
; (that would discard the waiting side's character or trio).
JoinFinishPrep:
    sep #$20
    .ACCU 8
    stz.w T_START
    lda.w C_STAGE
    cmp #10.b
    bcc +
    stz.w C_STAGE
+   rep #$20
    .ACCU 16
    rtl

; OBJ palette 4 = gold title prompt.  The font glyphs use colour 3 for the
; body and colour 1 for the right/bottom shadow, so the body is the gold
; from the reference image and the shadow is the same hue, slightly darker.
; Palette 5 keeps the blue title credit.
TitlePaletteFar:
    sep #$20
    .ACCU 8
    lda #192.b
    sta.l $2121
    lda #$00.b
    sta.l $2122
    sta.l $2122
    lda #$00.b                            ; colour 1: black -- the glyph's own
    sta.l $2122                           ;   edge, matching the BG2 ring
    lda #$00.b
    sta.l $2122
    lda #$36.b                            ; colour 2: unused, same shadow
    sta.l $2122
    lda #$1A.b
    sta.l $2122
    lda #$DC.b                            ; colour 3: body 0x2ADC
    sta.l $2122
    lda #$2A.b
    sta.l $2122
    lda #208.b
    sta.l $2121
    lda #$00.b
    sta.l $2122
    sta.l $2122
    lda #$02.b
    sta.l $2122
    lda #$72.b
    sta.l $2122
    lda #$83.b
    sta.l $2122
    lda #$55.b
    sta.l $2122
    lda #$FF.b
    sta.l $2122
    sta.l $2122
    rep #$20
    .ACCU 16
    rtl

.ENDS

; P2 STARTED from the mode menu: keep Pad2 human and make P1 the CPU side
; until P1 presses START on the select screen.  Kept out of the full Fight
; bank; MenuToSelect calls it with JSL.
.BANK 84 SLOT 0
.ORGA $E700
.SECTION "MenuP2StartFar" FORCE
MenuP2StartSetup:
    sep #$20
    .ACCU 8
    lda.w M_START_SIDE
    beq MPS_done
    stz.b cpu2
    stz.b lock1
    stz.b lock2
    lda.w G_MODE
    beq MPS_done                        ; Single VS: both pads human
    cmp #3
    beq MPS_done                        ; Team VS: both pads human
    lda #1
    sta.b cpu1                          ; P1 is CPU until its START joins
    sta.w C_HUMAN_SIDE                  ; campaign follows the P2 pad
MPS_done:
    sep #$20
    .ACCU 8
    rtl
.ENDS


; MAX tags need their own bank-126 window: SelectHelpers already ends right
; before MsuChrPageClamp at $E600.  $3500 sits in the free gap between the
; ORDER portraits/counter helpers ($0000-$34FF) and the next fixed section.
.BANK 126 SLOT 0
.ORGA $F200
.SECTION "MaxTagsFar" FORCE
; Flashing MAX tag beside each POWER counter.  Lives here so the Fight bank
; only pays the JSL.  Font tile ids: M=13, A=1, X=24; $34 = gold palette.
DrawMaxTagsFar:
    php
    rep #$20
    .ACCU 16
    sep #$20
    .ACCU 8
    lda.b framecnt
    and #$10.b
    sta.b scr6
    ; P1
    lda FP+F_MAX
    beq DMT_p1off
    lda.b scr6
    beq DMT_p1off
    ldx #((22*32+4)*2).w
    lda #13
    sta.w HUDMAP,x
    lda #$34.b
    sta.w HUDMAP+1,x
    lda #1
    sta.w HUDMAP+2,x
    lda #$34.b
    sta.w HUDMAP+3,x
    lda #24
    sta.w HUDMAP+4,x
    lda #$34.b
    sta.w HUDMAP+5,x
    bra DMT_p2
DMT_p1off:
    ldx #((22*32+4)*2).w
    stz.w HUDMAP,x
    stz.w HUDMAP+1,x
    stz.w HUDMAP+2,x
    stz.w HUDMAP+3,x
    stz.w HUDMAP+4,x
    stz.w HUDMAP+5,x
DMT_p2:
    lda FP+F_MAX+FP2OFS
    beq DMT_p2off
    lda.b scr6
    beq DMT_p2off
    ldx #((22*32+26)*2).w
    lda #13
    sta.w HUDMAP,x
    lda #$34.b
    sta.w HUDMAP+1,x
    lda #1
    sta.w HUDMAP+2,x
    lda #$34.b
    sta.w HUDMAP+3,x
    lda #24
    sta.w HUDMAP+4,x
    lda #$34.b
    sta.w HUDMAP+5,x
    bra DMT_dirty
DMT_p2off:
    ldx #((22*32+26)*2).w
    stz.w HUDMAP,x
    stz.w HUDMAP+1,x
    stz.w HUDMAP+2,x
    stz.w HUDMAP+3,x
    stz.w HUDMAP+4,x
    stz.w HUDMAP+5,x
DMT_dirty:
    lda.b huddirty
    ora #HUD_POWCNT.b
    sta.b huddirty
    plp
    rtl

.ENDS


; Geyser cleanup: drop a cosmetic spark in the other slot and invalidate
; both FX pages.  Keeps the shared spark page from being drawn with the
; pillar's cells for a frame (golden flashing squares after the super).
.BANK 126 SLOT 0
.ORGA $F300
.SECTION "GeyserResidualFar" FORCE
ClearGeyserResidualFar:
    php
    phx
    rep #$20
    .ACCU 16
    txa
    eor #SPK_SIZE
    tax
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    bmi CGR_keep
    stz.w SPARKS+SPK_ANIM,x
    stz.w SPARKS+SPK_ANIM+1,x
CGR_keep:
    rep #$20
    .ACCU 16
    stz.w FX_CACHE
    stz.w FX_CACHE+2
    stz.w FX_CACHEBANK
    stz.w FX_CACHEBANK+2
    plx
    plp
    rtl
.ENDS
