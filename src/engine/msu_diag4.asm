; D4 compares direct seeks against ONE sequential stream from byte zero.
; Direct CPU/DMA capture and snapshot storage are shared with D2; the
; per-record +4/+18/+26 fields now hold sequential results, not VRAM.
.DEFINE MD_SEQ_POS  $5428
.DEFINE MD_SEQ_DONE $542C

D4Sequential:
    rep #$30
    .ACCU 16
    .INDEX 16
    stz.w MD_SEQ_POS
    stz.w MD_SEQ_POS+2
    stz.w MD_SEQ_DONE
    stz.w MD_IDX
    stz.w MD_REC
    sep #$20
    .ACCU 8
    lda #0.b
    sta.l $2000
    sta.l $2001
    sta.l $2002
    sta.l $2003
    jsr D4Wait
    bcc D4_chunk
    rep #$20
    .ACCU 16
    lda.w MD_BOOT
    ora #8.w
    sta.w MD_BOOT
    rts
D4_chunk:
    ; No seeks here. Check status before each 256-byte DMA, then drain
    ; the next bytes to WRAM. Previous discarded blocks need no storage.
    jsr D4Wait
    bcc D4_dma
    rep #$20
    .ACCU 16
    lda.w MD_BOOT
    ora #16.w
    sta.w MD_BOOT
    rts
D4_dma:
    rep #$20
    .ACCU 16
    lda #(MD_DMA_BUF & $FFFF).w
    sta.l $2181
    lda #$8008.w
    sta.l $4350
    lda #$2001.w
    sta.l $4352
    lda #MD_SAMPLE_SIZE.w
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #1.b
    sta.l $2183
    lda #0.b
    sta.l $4354
    lda #$20.b
    sta.l MDMAEN
    rep #$20
    .ACCU 16
    ldx.w MD_IDX
    lda.l ((MsuDiagSamples & $FFFFFF)),x
    cmp.w MD_SEQ_POS
    bne D4_advance
    lda.l ((MsuDiagSamples & $FFFFFF)+2),x
    cmp.w MD_SEQ_POS+2
    bne D4_advance
    lda.l ((MsuDiagSamples & $FFFFFF)+4),x
    sta.b lptr
    sep #$20
    .ACCU 8
    lda.l ((MsuDiagSamples & $FFFFFF)+6),x
    sta.b lptr+2
    rep #$20
    .ACCU 16
    lda #(MD_DMA_BUF & $FFFF).w
    jsr D2_compare
    ldx.w MD_REC
    sta.w MD_RES+4,x
    clc
    adc.w MD_VRAM                     ; aggregate sequential errors in D4
    sta.w MD_VRAM
    lda.w MD_FIRST
    sta.w MD_RES+26,x
    lda.l MD_DMA_BUF
    xba
    sta.w MD_RES+18,x
    lda.l MD_DMA_BUF+2
    xba
    sta.w MD_RES+20,x
    inc.w MD_SEQ_DONE
    lda.w MD_REC
    clc
    adc #32.w
    sta.w MD_REC
    lda.w MD_IDX
    clc
    adc #8.w
    sta.w MD_IDX
    cmp #(MD_NSAMPLES*8).w
    bcs D4_done
D4_advance:
    lda.w MD_SEQ_POS
    clc
    adc #MD_SAMPLE_SIZE.w
    sta.w MD_SEQ_POS
    lda.w MD_SEQ_POS+2
    adc #0.w
    sta.w MD_SEQ_POS+2
    lda.w MD_SEQ_POS
    and #$0FFF.w
    bne D4_resume
    ; Let the real SD controller refill its ring buffer. This fixed pause
    ; every 4 KiB is a test condition, not a guaranteed hardware deadline.
    ldx #$0400.w
-   dex
    bne -
D4_resume:
    sep #$20
    .ACCU 8
    jmp D4_chunk
D4_done:
    ; MD_SEQ_POS is the start of the final sampled block ($00800000).
    rts

D4Wait:
    sep #$20
    .ACCU 8
    ldx #$FFFF.w
-   lda.l MSU_STAT
    bpl +
    dex
    bne -
    sec
    rts
+   clc
    rts
