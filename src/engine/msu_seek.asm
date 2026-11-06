; Keep a cold SD seek alive across frame boundaries. Reissuing $2003 before
; the previous seek is ready can repeatedly restart the cartridge cache.
.BASE $00
.BANK 64 SLOT 0
.ORGA $4800
.SECTION "MsuPendingSeek" FORCE
MsuSeekPrepareFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    jsl MsuChrPageClamp
    lda.w MS_SEEK_STATE
    beq MSS_start
    ; A team member/state reset may invalidate a saved request. Reuse a seek
    ; only if owner, aligned file offset and complete geometry still match.
    lda.w SP_SIDE
    cmp.w MS_SEEK_SIDE
    bne MSS_start
    lda scr0
    cmp.w MS_SEEK_SOURCE
    bne MSS_start
    lda scr4
    cmp.w MS_SEEK_SOURCE+2
    bne MSS_start
    lda scr3
    cmp.w MS_SEEK_COUNT
    bne MSS_start
    lda.w MSU_PREFIX
    cmp.w MS_SEEK_PREFIX
    beq MSS_poll
MSS_start:
    lda.w SP_SIDE
    sta.w MS_SEEK_SIDE
    lda scr0
    sta.w MS_SEEK_SOURCE
    lda scr4
    sta.w MS_SEEK_SOURCE+2
    lda scr3
    sta.w MS_SEEK_COUNT
    lda.w MSU_PREFIX
    sta.w MS_SEEK_PREFIX
    sta.w MS_SEEK_READ_PREFIX
    clc
    adc scr0
    sta.w MS_SEEK_GOAL
    lda scr4
    adc #0.w
    sta.w MS_SEEK_GOAL+2
    stz.w MS_SEEK_WAITS
    lda #1.w
    sta.w MS_SEEK_STATE
    ; The next chunk of this pose often starts exactly at the current read
    ; pointer. Continue within the same 8 KiB cache page without a new seek
    ; or re-reading its sector prefix. Voices/transitions invalidate this.
    lda.w MS_PORT_VALID
    beq MSS_seek
    lda.w MS_SEEK_GOAL
    and #$1FFF.w
    beq MSS_seek                        ; refill a new cache page via aligned seek
    lda.w MS_SEEK_GOAL
    cmp.w MS_PORT_NEXT
    bne MSS_seek
    lda.w MS_SEEK_GOAL+2
    cmp.w MS_PORT_NEXT+2
    bne MSS_seek
    stz.w MS_SEEK_READ_PREFIX
    bra MSS_poll
MSS_seek:
    stz.w MS_PORT_VALID
    sep #$20
    .ACCU 8
    lda scr0
    sta.l MSU_STAT
    lda scr0+1
    sta.l MSU_DATA
    lda scr4
    sta.l $2002
    lda scr4+1
    sta.l $2003
MSS_poll:
    sep #$20
    .ACCU 8
    ldx #MSU_POLL_LIMIT.w
MSS_wait:
    lda.l MSU_STAT
    bpl MSS_ready
    dex
    bne MSS_wait
    rep #$20
    .ACCU 16
    inc.w RT_MSUFAIL
    inc.w MS_SEEK_WAITS
    lda.w MS_SEEK_WAITS
    cmp #120.w
    bcc MSS_later
    lda.w MS_SEEK_SIDE
    eor #2.w
    sta.w MS_SEEK_NEXT
    stz.w MS_SEEK_STATE                  ; bounded recovery for an absent device
MSS_later:
    clc
    rtl
MSS_ready:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda #2.w
    sta.w MS_SEEK_STATE                  ; don't let voices steal an unconsumed seek
    lda.w MS_SEEK_READ_PREFIX
    sta.w MSU_PREFIX
    sec
    rtl

MsuSeekConsumedFar:
    rep #$20
    .ACCU 16
    lda.w MS_SEEK_GOAL
    clc
    adc.w MS_SEEK_COUNT
    sta.w MS_PORT_NEXT
    lda.w MS_SEEK_GOAL+2
    adc #0.w
    sta.w MS_PORT_NEXT+2
    lda #1.w
    sta.w MS_PORT_VALID
    stz.w MS_SEEK_STATE
    rtl
.ENDS
