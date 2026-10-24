; D2 is included inside MsuDiagnostic's bank/section. Boot runs in forced
; blank with NMI disabled. Buffers are reserved explicitly in fight_bridge.
; Each result record is 32 bytes: C/M/V byte-error counts; E/C/M/V first
; four bytes (display order); first mismatching offsets C/M/V; spare words.
MsuDiagBoot:
    rep #$30
    .ACCU 16
    .INDEX 16
    stz.w MD_IDX
    stz.w MD_REC
    ldx #0.w
    lda #$FFFF.w
-   sta.w MD_RES,x
    inx
    inx
    cpx #(MD_NSAMPLES*32).w
    bne -
    sep #$20
    .ACCU 8
    lda.b msuok
    bne D2_next
    rep #$20
    .ACCU 16
    lda #4.w
    sta.w MD_BOOT
    sep #$20
    .ACCU 8
    rtl
D2_next:
    rep #$20
    .ACCU 16
    ldx.w MD_IDX
    lda.l ((MsuDiagSamples & $FFFFFF)+4),x
    sta.b lptr
    sep #$20
    .ACCU 8
    lda.l ((MsuDiagSamples & $FFFFFF)+6),x
    sta.b lptr+2
    jsr MdbSeek
    bcc D2_cpu
    rep #$20
    .ACCU 16
    lda.w MD_BOOT
    ora #1.w
    sta.w MD_BOOT
    jmp D2_try_dma
D2_cpu:
    ; Capture first, compare afterwards. No ROM data comparisons interleave
    ; MSU reads, and all 1280 received bytes remain available in WRAM.
    ldx #0.w
-   lda.l MSU_DATA
    sta.l MD_CPU_BUF,x
    inx
    cpx #MD_SAMPLE_SIZE.w
    bne -
    rep #$20
    .ACCU 16
    lda #(MD_CPU_BUF & $FFFF).w
    jsr D2_compare
    ldx.w MD_REC
    sta.w MD_RES,x
    clc
    adc.w MD_CPU
    sta.w MD_CPU
    lda.w MD_FIRST
    sta.w MD_RES+22,x
D2_try_dma:
    jsr MdbSeek
    bcc D2_dma
    rep #$20
    .ACCU 16
    lda.w MD_BOOT
    ora #2.w
    sta.w MD_BOOT
    jmp D2_record
D2_dma:
    ; MSU -> WRAM, through $2180 (fixed-source mode 0).
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
    lda #(MD_DMA_BUF & $FFFF).w
    jsr D2_compare
    ldx.w MD_REC
    sta.w MD_RES+2,x
    lda.w MD_FIRST
    sta.w MD_RES+24,x
.IFNDEF MSU_DIAG4
    ; Upload exactly that captured WRAM buffer, then read VRAM back.
    lda #P1CHR.w
    sta.l VMADDL
    lda #$1801.w
    sta.l $4350
    lda #(MD_DMA_BUF & $FFFF).w
    sta.l $4352
    lda #MD_SAMPLE_SIZE.w
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.l $4354
    lda #$80.b
    sta.l VMAIN
    lda #$20.b
    sta.l MDMAEN
    rep #$20
    .ACCU 16
    lda #P1CHR.w
    sta.l VMADDL
    lda.l $2139                       ; dummy word read, as in D1
    ldx #0.w
-   lda.l $2139
    sta.l MD_VR_BUF,x
    inx
    inx
    cpx #MD_SAMPLE_SIZE.w
    bne -
    lda #(MD_VR_BUF & $FFFF).w
    jsr D2_compare
    ldx.w MD_REC
    sta.w MD_RES+4,x
    clc
    adc.w MD_VRAM
    sta.w MD_VRAM
    lda.w MD_FIRST
    sta.w MD_RES+26,x
.ENDIF
D2_record:
    rep #$20
    .ACCU 16
    ldx.w MD_REC
    ldy #0.w
    lda [lptr],y
    xba
    sta.w MD_RES+6,x
    iny
    iny
    lda [lptr],y
    xba
    sta.w MD_RES+8,x
    ; Timed-out paths keep FFFF counts; their byte displays are invalid.
    lda.w MD_RES,x
    cmp #$FFFF.w
    beq D2_no_cpu_bytes
    lda.l MD_CPU_BUF
    xba
    sta.w MD_RES+10,x
    lda.l MD_CPU_BUF+2
    xba
    sta.w MD_RES+12,x
D2_no_cpu_bytes:
    lda.w MD_RES+2,x
    cmp #$FFFF.w
    beq D2_no_dma_bytes
    lda.l MD_DMA_BUF
    xba
    sta.w MD_RES+14,x
    lda.l MD_DMA_BUF+2
    xba
    sta.w MD_RES+16,x
.IFNDEF MSU_DIAG4
    lda.l MD_VR_BUF
    xba
    sta.w MD_RES+18,x
    lda.l MD_VR_BUF+2
    xba
    sta.w MD_RES+20,x
.ENDIF
D2_no_dma_bytes:
    lda.w MD_REC
    clc
    adc #32.w
    sta.w MD_REC
    lda.w MD_IDX
    clc
    adc #8.w
    sta.w MD_IDX
    cmp #(MD_NSAMPLES*8).w
    bcs D2_done
    jmp D2_next
D2_done:
.IFDEF MSU_DIAG4
    jsr D4Sequential
.ENDIF
    sep #$20
    .ACCU 8
    rtl

; A16 = low word of buffer in $7F; lptr = expected sample in ROM.
; Returns A16 = differing bytes; MD_FIRST = first offset, FFFF if identical.
D2_compare:
    sta.b sptr
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.b sptr+2
    rep #$20
    .ACCU 16
    stz.w MD_VALUE
    lda #$FFFF.w
    sta.w MD_FIRST
    sep #$20
    .ACCU 8
    ldy #0.w
D2_cmp_byte:
    lda [sptr],y
    cmp [lptr],y
    beq D2_cmp_next
    rep #$20
    .ACCU 16
    inc.w MD_VALUE
    lda.w MD_FIRST
    cmp #$FFFF.w
    bne +
    tya
    sta.w MD_FIRST
+   sep #$20
    .ACCU 8
D2_cmp_next:
    iny
    cpy #MD_SAMPLE_SIZE.w
    bne D2_cmp_byte
    rep #$20
    .ACCU 16
    lda.w MD_VALUE
    rts

; Live sprites use the same two-stage route tested at boot. scr0/2/3/4
; survive, and VMADD already points to the hidden fighter page.
MsuDiagStagedUpload:
    rep #$20
    .ACCU 16
    lda #(MD_DMA_BUF & $FFFF).w
    sta.l $2181
    lda #$8008.w
    sta.l $4350
    lda #$2001.w
    sta.l $4352
    lda.w MSU_PREFIX
    clc
    adc.b scr3
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
    lda #$1801.w
    sta.l $4350
    lda #(MD_DMA_BUF & $FFFF).w
    clc
    adc.w MSU_PREFIX
    sta.l $4352
    lda.b scr3
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.l $4354
    lda #$80.b
    sta.l VMAIN
    lda #$20.b
    sta.l MDMAEN
    jsl MsuDiagTransferred
    rep #$20
    .ACCU 16
    lda.b scr0
    sta.l $7E0910
    lda.b scr4
    sta.l $7E0912
    rtl
