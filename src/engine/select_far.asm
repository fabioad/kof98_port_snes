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
    lda.w G_MODE
    beq SPR_no                            ; VS: both sides are already human
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
    lda #$36.b                            ; colour 1: shadow 0x1A36
    sta.l $2122
    lda #$1A.b
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
