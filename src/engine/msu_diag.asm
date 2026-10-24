; Optional hardware diagnostic. No hooks in production builds.
; $5400..$543F is inside the reserved $5100..$57FF streaming block.
.DEFINE MD_CPU    $5400
.DEFINE MD_VRAM   $5402
.DEFINE MD_REQ    $5404
.DEFINE MD_READY  $5406
.DEFINE MD_TO     $5408
.DEFINE MD_P1     $540A
.DEFINE MD_P2     $540C
.DEFINE MD_STAT   $540E
.DEFINE MD_POS    $5410
.DEFINE MD_LEN    $5414
.DEFINE MD_BOOT   $5416
.DEFINE MD_IDX    $5418
.DEFINE MD_VALUE  $541A
.DEFINE MD_FIELD  $541C
.DEFINE MD_DIGITS $541E
.IFDEF MSU_DIAG2
.DEFINE MD_MAPREADY $5420
.DEFINE MD_REC      $5422
.DEFINE MD_FIRST    $5424
.DEFINE MD_RES      $5440
.DEFINE MD_CPU_BUF  $7F3000
.DEFINE MD_DMA_BUF  $7F3500
.DEFINE MD_VR_BUF   $7F3A00
.DEFINE MD_MAP      $7F4400
.IFDEF MSU_DIAG3
.DEFINE MD_MAPSIZE  1280
.DEFINE MD_SAMPLE_SIZE 256
.DEFINE MD_NSAMPLES 8
.ELSE
.DEFINE MD_MAPSIZE  832
.DEFINE MD_SAMPLE_SIZE 1280
.DEFINE MD_NSAMPLES 3
.ENDIF
.DEFINE MD_MAPBANK  $7F
.ELSE
.DEFINE MD_MAP      $7E0000+HUDMAP+5*64
.DEFINE MD_MAPSIZE  256
.DEFINE MD_MAPBANK  $7E
.ENDIF

.BASE $C0
.BANK 126 SLOT 0
.ORGA $D000
.SECTION "MsuDiagnostic" FORCE

; Called with NMI disabled and forced blank, before game graphics load.
; Compare three 1280-byte samples (generated from this exact .msu), first
; through CPU reads, then through the same ch5 mode-$09 DMA as fighters.
.IFDEF MSU_DIAG2
.INCLUDE "engine/msu_diag2.asm"
.ELSE
MsuDiagBoot:
    rep #$30
    .ACCU 16
    .INDEX 16
    stz.w MD_IDX
    sep #$20
    .ACCU 8
    lda.b msuok
    bne MDB_next
    rep #$20
    .ACCU 16
    lda #$FFFF.w
    sta.w MD_CPU
    sta.w MD_VRAM
    lda #4.w
    sta.w MD_BOOT
    jmp MDB_return
MDB_next:
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
    bcc MDB_cpu
    rep #$20
    .ACCU 16
    lda #1.w
    sta.w MD_BOOT
    jmp MDB_return
MDB_cpu:
    ldy #0.w
MDB_cpu_byte:
    lda.l MSU_DATA
    cmp [lptr],y
    beq +
    rep #$20
    .ACCU 16
    inc.w MD_CPU
    sep #$20
    .ACCU 8
+   iny
    cpy #1280.w
    bne MDB_cpu_byte
    jsr MdbSeek
    bcc MDB_dma
    rep #$20
    .ACCU 16
    lda #2.w
    sta.w MD_BOOT
    jmp MDB_return
MDB_dma:
    lda #$80.b
    sta.l VMAIN
    rep #$20
    .ACCU 16
    lda #P1CHR.w
    sta.l VMADDL
    lda #$1809.w
    sta.l $4350
    lda #$2001.w
    sta.l $4352
    lda #1280.w
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #0.b
    sta.l $4354
    lda #$20.b
    sta.l MDMAEN
    rep #$20
    .ACCU 16
    lda #P1CHR.w
    sta.l VMADDL
    lda.l $2139                      ; dummy word read reloads VRAM latch
    ldy #0.w
MDB_vram_word:
    lda.l $2139
    cmp [lptr],y
    beq +
    inc.w MD_VRAM                    ; mismatching words, CPU counts bytes
+   iny
    iny
    cpy #1280.w
    bne MDB_vram_word
    lda.w MD_IDX
    clc
    adc #8.w
    sta.w MD_IDX
    cmp #24.w
    bcs MDB_return
    jmp MDB_next
MDB_return:
    sep #$20
    .ACCU 8
    rtl
.ENDIF

; Boot-only seek, long bounded wait. C=1 on timeout; A8/X16 on return.
MdbSeek:
.IFDEF MSU_DIAG3
    jmp MdbSeekD3
.ELSE
    sep #$20
    .ACCU 8
    ldx.w MD_IDX
    lda.l ((MsuDiagSamples & $FFFFFF)),x
    sta.l $2000
    lda.l ((MsuDiagSamples & $FFFFFF)+1),x
    sta.l $2001
    lda.l ((MsuDiagSamples & $FFFFFF)+2),x
    sta.l $2002
    lda.l ((MsuDiagSamples & $FFFFFF)+3),x
    sta.l $2003
    ldx #$FFFF.w
-   lda.l MSU_STAT
    bpl +
    dex
    bne -
    sec
    rts
+   clc
    rts
.ENDIF

; Preserve the production 1024-poll loop. Collect status only after it,
; using the last value read (STA changes no flags). C=1 on timeout.
MsuDiagSpriteWait:
    ldx #MSU_POLL_LIMIT.w
-   lda.l MSU_STAT
    bpl MDW_ready
    dex
    bne -
    sta.w MD_STAT
    rep #$20
    .ACCU 16
    inc.w MD_REQ
    inc.w MD_TO
    inc.w RT_MSUFAIL
    jsr MdwPosition
    sep #$20
    .ACCU 8
    sec
    rtl
MDW_ready:
    sta.w MD_STAT
    rep #$20
    .ACCU 16
    inc.w MD_REQ
    inc.w MD_READY
    jsr MdwPosition
    sep #$20
    .ACCU 8
    clc
    rtl
MdwPosition:
    lda.b scr0
    sta.w MD_POS
    lda.b scr4
    sta.w MD_POS+2
    lda.b scr3
    sta.w MD_LEN
    rts

MsuDiagTransferred:
    rep #$20
    .ACCU 16
    ldx.b fofs
    bne MDT_p2
    inc.w MD_P1
    bra MDT_done
MDT_p2:
    inc.w MD_P2
MDT_done:
    sep #$20
    .ACCU 8
    rtl

; Draw at most every 16 presentations. Private map upload (256 bytes)
; does not depend on FlushHud, which can be skipped while sprites wait.
MsuDiagOverlay:
    sep #$20
    .ACCU 8
    lda.b gamestate
    cmp #1.b
    beq +
    rtl
+
    lda.b framecnt
    and #15.b
    beq +
    rtl
+
    rep #$30
    .ACCU 16
    .INDEX 16
.IFDEF MSU_DIAG2
    lda.w MD_MAPREADY
    beq +
    lda #MSU_DIAG_LIVE_FIELD.w
    sta.w MD_FIELD
    bra MDO_field
+   inc.w MD_MAPREADY
.ENDIF
    ldx #0.w
-   lda.l ((MsuDiagTemplate & $FFFFFF)),x
    sta.l MD_MAP,x
    inx
    inx
    cpx #MD_MAPSIZE.w
    bne -
    stz.w MD_FIELD
MDO_field:
    ldx.w MD_FIELD
    lda.l ((MsuDiagFields & $FFFFFF)),x
    tay
    lda.w $0000,y
    sta.w MD_VALUE
    lda.l ((MsuDiagFields & $FFFFFF)+2),x
    tax
    lda #4.w
    sta.w MD_DIGITS
MDO_digit:
    lda.w MD_VALUE
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    phx
    tax
    lda.l ((MsuDiagHex & $FFFFFF)),x
    plx
    and #$00FF.w
    ora #$3C00.w
    sta.l MD_MAP,x
    inx
    inx
    lda.w MD_VALUE
    asl a
    asl a
    asl a
    asl a
    sta.w MD_VALUE
    dec.w MD_DIGITS
    bne MDO_digit
    lda.w MD_FIELD
    clc
    adc #4.w
    sta.w MD_FIELD
    cmp #(MsuDiagFieldsEnd-MsuDiagFields).w
    bcc MDO_field
    lda #(BG3MAP+5*32).w
    sta.l VMADDL
    lda #$1801.w
    sta.l $4340
    lda #(MD_MAP & $FFFF).w
    sta.l $4342
    lda #MD_MAPSIZE.w
    sta.l $4345
    sep #$20
    .ACCU 8
    lda #MD_MAPBANK.b
    sta.l $4344
    lda #$80.b
    sta.l VMAIN
    lda #$10.b
    sta.l MDMAEN
MDO_ret:
    sep #$20
    .ACCU 8
    rtl

.IFDEF MSU_DIAG3
.INCLUDE "engine/msu_diag3.asm"
.IFDEF MSU_DIAG4
.INCLUDE "engine/msu_diag4.asm"
.INCLUDE "msu_diag4/generated.inc"
.ELSE
.INCLUDE "msu_diag3/generated.inc"
.ENDIF
.ELSE
.IFDEF MSU_DIAG2
.INCLUDE "msu_diag2/generated.inc"
.ELSE
.INCLUDE "msu_diag/generated.inc"
.ENDIF
.ENDIF
.ENDS
