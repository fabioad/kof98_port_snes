; D3: compare byte writes, word writes and mirrored MSU registers.
; Records contain the actual values supplied by this routine, not register
; readback: MSU seek registers cannot be read back through their addresses.
.DEFINE MD_METHOD $5426
MdbSeekD3:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx.w MD_IDX
    ldy.w MD_REC
    lda.l ((MsuDiagSamples & $FFFFFF)),x
    sta.b scr0
    sta.w MD_RES+28,y
    lda.l ((MsuDiagSamples & $FFFFFF)+2),x
    sta.b scr1
    sta.w MD_RES+30,y
    sep #$20
    .ACCU 8
    lda.l ((MsuDiagSamples & $FFFFFF)+7),x
    sta.w MD_METHOD
    cmp #1.b
    beq D3_word
    cmp #2.b
    beq D3_mirror
    lda.b scr0
    sta.l $002000
    lda.b scr0+1
    sta.l $002001
    lda.b scr1
    sta.l $002002
    lda.b scr1+1
    sta.l $002003
    bra D3_wait
D3_word:
    rep #$20
    .ACCU 16
    lda.b scr0
    sta.l $002000
    lda.b scr1
    sta.l $002002
    sep #$20
    .ACCU 8
    bra D3_wait
D3_mirror:
    lda.b scr0
    sta.l $802000
    lda.b scr0+1
    sta.l $802001
    lda.b scr1
    sta.l $802002
    lda.b scr1+1
    sta.l $802003
D3_wait:
    ldx #$FFFF.w
-   lda.l MSU_STAT
    bpl +
    dex
    bne -
    sec
    rts
+   clc
    rts
