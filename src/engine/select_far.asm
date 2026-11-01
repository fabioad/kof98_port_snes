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


; OBJ palette 4 = light-orange title prompt (dark-orange outline, white
; highlight); palette 5 = blue title credit, matching the previous look.
; Kept out of the menu tail so bank 50 has room for FightHelperTail.
TitlePaletteFar:
    sep #$20
    .ACCU 8
    lda #192.b
    sta.l $2121
    lda #$00.b
    sta.l $2122
    sta.l $2122
    lda #$FF.b
    sta.l $2122
    lda #$26.b
    sta.l $2122
    lda #$57.b
    sta.l $2122
    lda #$01.b
    sta.l $2122
    lda #$FF.b
    sta.l $2122
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
