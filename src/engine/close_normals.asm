; Proximity normals reuse the existing state, animation, boxes and CHR.
; Private per-side words use side index 0/2, independently of pose streaming.
.BASE $00
.BANK 64 SLOT 0
.ORGA $5000
.SECTION "CloseNormalCode" FORCE
CloseNormalInitFar:
    stz.w CN_PROFILE
    stz.w CN_PROFILE+2
    stz.w CN_LEFT
    stz.w CN_LEFT+2
    stz.w CN_WAIT
    stz.w CN_WAIT+2
    rtl

CloseNormalEnterFar:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    pha
    phx
    phy
    ldx fofs
    txa
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    tay
    lda #0.w
    sta.w CN_PROFILE,y
    sta.w CN_LEFT,y
    sta.w CN_WAIT,y
    lda FP+F_STATE,x
    and #$00FF.w
    sec
    sbc #5.w
    cmp #4.w
    bcs CNE_done
    lda FP+F_Y,x
    bne CNE_done
    txa
    eor #FP2OFS.w
    tax
    lda FP+F_Y,x
    bne CNE_done
    lda FP+F_X,x
    ldx fofs
    sec
    sbc FP+F_X,x
    bpl +
    eor #$FFFF.w
    inc a
+   cmp #$2801.w                      ; 40 px between fighter origins
    bcs CNE_done
    lda FP+F_CHAR,x
    ldx #0.w
CNE_find:
    cmp.l CloseNormalDirectory,x
    beq CNE_found
    pha
    lda.l CloseNormalDirectory,x
    beq CNE_missing
    pla
    inx
    inx
    inx
    inx
    bra CNE_find
CNE_missing:
    pla
    bra CNE_done
CNE_found:
    lda.l CloseNormalDirectory+2,x
    sta cptr
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    sec
    sbc #5.w
    asl a
    asl a
    asl a
    asl a
    asl a
    clc
    adc cptr
    sta cptr
    sep #$20
    .ACCU 8
    lda #:CloseNormalData
    sta cptr+2
    rep #$20
    .ACCU 16
    phy
    ldy #0.w
    lda [cptr],y
    beq CNE_disabled
    ldy #2.w
    lda [cptr],y
    ply
    sta.w CN_LEFT,y
    lda cptr
    sta.w CN_PROFILE,y
    bra CNE_done
CNE_disabled:
    ply
CNE_done:
    ply
    plx
    pla
    plp
    rtl

; Called once per unpaused fighter tick, never once per collision pass.
; A contact holds the existing active pose long enough for a distinct hit.
CloseNormalTickFar:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    pha
    phx
    phy
    ldx fofs
    txa
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    tay
    lda.w CN_PROFILE,y
    beq CNT_done
    lda FP+F_STATE,x
    and #$00FF.w
    sec
    sbc #5.w
    cmp #4.w
    bcc CNT_active
    lda #0.w
    sta.w CN_PROFILE,y
    sta.w CN_LEFT,y
    sta.w CN_WAIT,y
    bra CNT_done
CNT_active:
    lda.w CN_LEFT,y
    beq CNT_done
    lda FP+F_HITDONE,x
    and #$00FF.w
    beq CNT_done
    lda.w CN_WAIT,y
    bne CNT_wait
    lda #4.w
    sta.w CN_WAIT,y
    sep #$20
    .ACCU 8
    lda FP+F_FTICK,x
    cmp #6.b
    bcs CNT_done
    lda #6.b
    sta FP+F_FTICK,x
    bra CNT_done
CNT_wait:
    dec a
    sta.w CN_WAIT,y
    bne CNT_done
    lda.w CN_LEFT,y
    dec a
    sta.w CN_LEFT,y
    sep #$20
    .ACCU 8
    stz FP+F_HITDONE,x
CNT_done:
    rep #$30
    .ACCU 16
    .INDEX 16
    ply
    plx
    pla
    plp
    rtl

; CharPtr's X is the output DP pointer; Y is the descriptor field.
; Adjust its base for the caller's original sid * record-size indexing.
; All other descriptor fields (especially animation/CHR/events) stay shared.
CloseNormalPtrFar:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    pha
    phx
    phy
    phx
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    sec
    sbc #5.w
    cmp #4.w
    bcs CNP_none
    txa
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    tax
    lda.w CN_PROFILE,x
    beq CNP_none
    sta cptr
    cpy #94.w
    bcs CNP_none
    tya
    tax
    lda.l CNFields,x
    cmp #$FFFF.w
    beq CNP_none
    pha                                 ; high byte = stride, low = field offset
    and #$00FF.w
    clc
    adc cptr
    sta cptr
    ; Intermediate contacts retain the target; the last uses source pushback.
    ; The low byte of CNFields is the profile word offset: 12 = HitVel,
    ; 20 = guard velocity.  (The high byte is the field stride.)
    lda 0,s
    and #$00FF.w
    cmp #12.w
    beq CNP_push
    cmp #20.w
    bne CNP_stride
CNP_push:
    phx
    ldx fofs
    txa
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    tax
    lda.w CN_LEFT,x
    beq +
    lda #CNZeroVel.w
    sta cptr
+   plx
CNP_stride:
    pla
    xba
    and #$00FF.w
    tay
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
CNP_sub:
    pha
    lda cptr
    sec
    sbc 1,s
    sta cptr
    pla
    dey
    bne CNP_sub
    plx
    lda cptr
    sta 0,x
    sep #$20
    .ACCU 8
    lda #:CloseNormalData
    sta 2,x
    bra CNP_done
CNP_none:
    plx
CNP_done:
    rep #$30
    .ACCU 16
    .INDEX 16
    ply
    plx
    pla
    plp
    rtl
; CNP_sub subtracts stride*(state-5) from the zero pointer; keep enough
; zero padding before CNZeroVel for the widest field (8 bytes * 3).
CNZeroPad: .dsb 32,0
CNZeroVel: .dw 0,0,0,0
CNFields:
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $0204
    .dw $0206
    .dw $0208
    .dw $080C
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $021A
    .dw $0614
    .dw $020A
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $011C
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
    .dw $FFFF
.ENDS
.ORGA $5800
.SECTION "CloseNormalProfiles" FORCE
.INCLUDE "gen_fight/close_normals.inc"
.ENDS
