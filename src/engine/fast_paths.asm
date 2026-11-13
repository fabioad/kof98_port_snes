; Fast paths, kept out of the Fight window in bank 50.  They live in a
; FastROM bank: on ExHiROM the old home (bank 64 = $40:xxxx) is SlowROM, so
; every opcode fetch of the hottest per-frame code (DrawCells, BOFill, ...)
; cost 8 master cycles instead of 6.  Banks 31-42 ($DF-$EA) are unused in
; the MSU build; the linker places the section anywhere in bank 31.
.BASE $C0
.BANK 31 SLOT 0
.ORG 0
.SECTION "FightFastPaths" FREE

DrawCellsFar:
.IFDEF KOF_PERF_VERIFY
    jmp DCF_verify
.ENDIF
DrawCellsFastBody:
    rep #$30
    .ACCU 16
    .INDEX 16
    pei (scr0)
    pei (scr1)
    pei (scr2)
    ; scr0 bit0 = horizontal flip, bit1 = vertical flip (AIR flag "V").
    ; MUGEN mirrors the cel around its axis, so the V path negates the cel
    ; dy and sets OAM attribute bit7.  Keeping both bits here lets the cell
    ; loop pick the Y formula once per cel without extra scratch RAM.
    lda scr0
    and #$0003.w
    sta scr0
    lda scr2
    sec
    sbc #$0080.w
    sta scr2
    sep #$20
    .ACCU 8
    lda aofs
    sta scr5
    stz scr5+1
    lda scr0
    and #$02.b
    beq +
    lda scr5
    ora #$80.b                          ; OAM vertical flip
    sta scr5
+   lda scr0
    and #$01.b
    beq DCF_setup_plain
    lda scr5
    ora #$40.b
    sta scr5
    rep #$20
    .ACCU 16
    lda scr1
    clc
    adc #($0080-16).w
    sta scr1
    bra DCF_cell
DCF_setup_plain:
    rep #$20
    .ACCU 16
    lda scr1
    sec
    sbc #$0080.w
    sta scr1
    lda scr0
    and #$0002.w
    sta scr0
DCF_cell:
    cpx #512.w
    bcc DCF_in_range
    jmp DCF_over
DCF_in_range:
    lda [lptr],y
    sta scr3
    iny
    iny
    lda [lptr],y
    sta scr6
    iny
    iny
    ; vertical flip mirrors the cel about the axis: y = -dy - 16 (or -8
    ; for the 8x8 sub-cells).  Both paths add the same (-128) bias that
    ; scr2 already carries, so the OAM byte matches the horizontal path.
    lda scr0
    and #$0002.w
    bne DCF_y_vflip
    lda scr3
    xba
    and #$00FF.w
    eor #$0080.w
    clc
    adc scr2
    bra DCF_y_check
DCF_y_vflip:
    lda scr3
    xba
    and #$00FF.w
    eor #$00FF.w
    pha
    lda scr6
    bmi DCF_y_vflip8
    pla
    clc
    adc #$0071.w
    bra DCF_y_sum
DCF_y_vflip8:
    pla
    clc
    adc #$0079.w
DCF_y_sum:
    clc
    adc scr2
DCF_y_check:
    bpl DCF_y_visible
    lda #$00F0.w
DCF_y_visible:
    sep #$20
    .ACCU 8
    sta.w OAMBUF+1,x
    rep #$20
    .ACCU 16
    lda scr0
    and #$0001.w
    bne DCF_x_flip
    lda scr3
    and #$00FF.w
    eor #$0080.w
    clc
    adc scr1
    bra DCF_x_done
DCF_x_flip:
    lda scr3
    and #$00FF.w
    eor #$FF7F.w
    sec
    adc scr1
    bit scr6
    bpl DCF_x_done
    clc
    adc #8.w
DCF_x_done:
    cmp #$0100.w
    sep #$20
    .ACCU 8
    sta.w OAMBUF,x
    ror scr5+1
    lda scr6+1
    eor #$80.b
    asl a
    ror scr5+1
    rep #$20
    .ACCU 16
    lda scr6
    and #$7FFF.w
    clc
    adc pbase
    cmp #$0100.w
    sep #$20
    .ACCU 8
    sta.w OAMBUF+2,x
    lda scr5
    bcc DCF_attr_ready
    ora #$01.b
DCF_attr_ready:
    sta.w OAMBUF+3,x
    inx
    inx
    inx
    inx
    txa
    and #$0C.b
    bne DCF_cell_done
    rep #$20
    .ACCU 16
    phx
    txa
    lsr a
    lsr a
    lsr a
    lsr a
    tax
    sep #$20
    .ACCU 8
    lda scr5+1
    ora.w OAMHI-1,x
    sta.w OAMHI-1,x
    stz scr5+1
    plx
DCF_cell_done:
    dec scr4
    beq DCF_end
    rep #$20
    .ACCU 16
    jmp DCF_cell
DCF_end:
    .ACCU 8
    txa
    and #$0C.b
    beq DCF_done
DCF_partial_shift:
    lsr scr5+1
    lsr scr5+1
    clc
    adc #4.b
    cmp #16.b
    bne DCF_partial_shift
    rep #$20
    .ACCU 16
    phx
    txa
    lsr a
    lsr a
    lsr a
    lsr a
    tax
    sep #$20
    .ACCU 8
    lda scr5+1
    ora.w OAMHI,x
    sta.w OAMHI,x
    plx
    bra DCF_done
DCF_over:
    .ACCU 16
    inc.w RT_OAMDROP
DCF_done:
    rep #$30
    .ACCU 16
    .INDEX 16
    stx oamtop
    pla
    sta scr2
    pla
    sta scr1
    pla
    sta scr0
    rtl

.IFDEF KOF_PERF_VERIFY
DCF_verify:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    sta.l PV_DRAW_IN_A
    txa
    sta.l PV_DRAW_IN_X
    tya
    sta.l PV_DRAW_IN_Y
    lda.l PV_DRAW_CALLS
    inc a
    sta.l PV_DRAW_CALLS
    bne DCF_calls_counted
    lda.l PV_DRAW_CALLS+2
    inc a
    sta.l PV_DRAW_CALLS+2
DCF_calls_counted:
    lda #0.w
    sta.l PV_NMISAVE                    ; retry flag: transient DP clobber must
    lda scr0                            ;   survive a full old+new re-run
    sta.l PV_DRAW_SCR0
    lda scr1
    sta.l PV_DRAW_SCR1
    lda scr2
    sta.l PV_DRAW_SCR2
    lda scr3
    sta.l PV_DRAW_SCR3
    lda scr4
    sta.l PV_DRAW_SCR4
    lda scr5
    sta.l PV_DRAW_SCR5
    lda scr6
    sta.l PV_DRAW_SCR6
    lda pbase
    sta.l PV_DRAW_PBASE
    lda lptr
    sta.l PV_DRAW_LPTR
    lda oamtop
    sta.l PV_DRAW_PRE_TOP
    lda.w RT_OAMDROP
    sta.l PV_DRAW_PRE_DROP
    sep #$20
    .ACCU 8
    lda aofs
    sta.l PV_DRAW_AOFS
    lda lptr+2
    sta.l PV_DRAW_LPTR+2
    ldx #0.w
DCF_save_pre_oam:
    lda.w OAMBUF,x
    sta.l PV_DRAW_PRE_OAM,x
    inx
    cpx #512.w
    bne DCF_save_pre_oam
    ldx #0.w
DCF_save_pre_hi:
    lda.w OAMHI,x
    sta.l PV_DRAW_PRE_OAM+512,x
    inx
    cpx #32.w
    bne DCF_save_pre_hi
    plp
    rep #$30                        ; the inline cell loop ran with X16/A16;
    .ACCU 16                        ; cpx #512 bails immediately under X8
    .INDEX 16
    sep #$20
    .ACCU 8
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.l PV_DRAW_IN_X
    tax
    lda.l PV_DRAW_IN_Y
    tay
    lda.l PV_DRAW_IN_A
    jsl DrawCellsOldFar
    rep #$30
    .ACCU 16
    .INDEX 16
    lda oamtop
    sta.l PV_DRAW_OLD_TOP
    lda.w RT_OAMDROP
    sta.l PV_DRAW_OLD_DROP
    lda scr0
    sta.l PV_DRAW_OLD_SCR0
    lda scr1
    sta.l PV_DRAW_OLD_SCR1
    lda scr2
    sta.l PV_DRAW_OLD_SCR2
    sep #$20
    .ACCU 8
    ldx #0.w
DCF_save_old_oam:
    lda.w OAMBUF,x
    sta.l PV_DRAW_OLD_OAM,x
    inx
    cpx #512.w
    bne DCF_save_old_oam
    ldx #0.w
DCF_save_old_hi:
    lda.w OAMHI,x
    sta.l PV_DRAW_OLD_OAM+512,x
    inx
    cpx #32.w
    bne DCF_save_old_hi
    ldx #0.w
DCF_restore_pre_oam:
    lda.l PV_DRAW_PRE_OAM,x
    sta.w OAMBUF,x
    inx
    cpx #512.w
    bne DCF_restore_pre_oam
    ldx #0.w
DCF_restore_pre_hi:
    lda.l PV_DRAW_PRE_OAM+512,x
    sta.w OAMHI,x
    inx
    cpx #32.w
    bne DCF_restore_pre_hi
DCF_run_new:
    rep #$20
    .ACCU 16
    lda.l PV_DRAW_SCR0
    sta scr0
    lda.l PV_DRAW_SCR1
    sta scr1
    lda.l PV_DRAW_SCR2
    sta scr2
    lda.l PV_DRAW_SCR3
    sta scr3
    lda.l PV_DRAW_SCR4
    sta scr4
    lda.l PV_DRAW_SCR5
    sta scr5
    lda.l PV_DRAW_SCR6
    sta scr6
    lda.l PV_DRAW_PBASE
    sta pbase
    lda.l PV_DRAW_LPTR
    sta lptr
    lda.l PV_DRAW_PRE_TOP
    sta oamtop
    lda.l PV_DRAW_PRE_DROP
    sta.w RT_OAMDROP
    sep #$20
    .ACCU 8
    lda.l PV_DRAW_AOFS
    sta aofs
    lda.l PV_DRAW_LPTR+2
    sta lptr+2
    rep #$20
    .ACCU 16
    lda.l PV_DRAW_IN_X
    tax
    lda.l PV_DRAW_IN_Y
    tay
    lda.l PV_DRAW_IN_A
    jsl DrawCellsFastBody
    php
    pha
    phx
    phy
    sep #$20
    .ACCU 8
    ldx #0.w
DCF_compare_oam:
    lda.w OAMBUF,x
    cmp.l PV_DRAW_OLD_OAM,x
    beq DCF_oam_equal
    lda #0.b
    sta.l PV_TMP_EXPECTED+1
    sta.l PV_TMP_ACTUAL+1
    lda.w OAMBUF,x
    sta.l PV_TMP_ACTUAL
    lda.l PV_DRAW_OLD_OAM,x
    sta.l PV_TMP_EXPECTED
    rep #$20
    txa
    sta.l PV_TMP_OFFSET
    jmp DCF_mismatch
DCF_oam_equal:
    inx
    cpx #512.w
    bne DCF_compare_oam
    ldx #0.w
DCF_compare_hi:
    lda.w OAMHI,x
    cmp.l PV_DRAW_OLD_OAM+512,x
    beq DCF_hi_equal
    lda #0.b
    sta.l PV_TMP_EXPECTED+1
    sta.l PV_TMP_ACTUAL+1
    lda.w OAMHI,x
    sta.l PV_TMP_ACTUAL
    lda.l PV_DRAW_OLD_OAM+512,x
    sta.l PV_TMP_EXPECTED
    rep #$20
    txa
    clc
    adc #512.w
    sta.l PV_TMP_OFFSET
    jmp DCF_mismatch
DCF_hi_equal:
    inx
    cpx #32.w
    bne DCF_compare_hi
    rep #$20
    .ACCU 16
    lda.l PV_DRAW_OLD_TOP
    cmp oamtop
    beq DCF_top_equal
    sta.l PV_TMP_EXPECTED
    lda oamtop
    sta.l PV_TMP_ACTUAL
    lda #$FFFE.w
    sta.l PV_TMP_OFFSET
    jmp DCF_mismatch
DCF_top_equal:
    lda.l PV_DRAW_OLD_DROP
    cmp.w RT_OAMDROP
    beq DCF_drop_equal
    sta.l PV_TMP_EXPECTED
    lda.w RT_OAMDROP
    sta.l PV_TMP_ACTUAL
    lda #$FFFC.w
    sta.l PV_TMP_OFFSET
    jmp DCF_mismatch
DCF_drop_equal:
    lda.l PV_DRAW_OLD_SCR0
    cmp scr0
    beq DCF_scr0_equal
    sta.l PV_TMP_EXPECTED
    lda scr0
    sta.l PV_TMP_ACTUAL
    lda #$FFF0.w
    sta.l PV_TMP_OFFSET
    jmp DCF_mismatch
DCF_scr0_equal:
    lda.l PV_DRAW_OLD_SCR1
    cmp scr1
    beq DCF_scr1_equal
    sta.l PV_TMP_EXPECTED
    lda scr1
    sta.l PV_TMP_ACTUAL
    lda #$FFF2.w
    sta.l PV_TMP_OFFSET
    jmp DCF_mismatch
DCF_scr1_equal:
    lda.l PV_DRAW_OLD_SCR2
    cmp scr2
    bne DCF_scr2_mismatch
    jmp DCF_after_compare
DCF_scr2_mismatch:
    sta.l PV_TMP_EXPECTED
    lda scr2
    sta.l PV_TMP_ACTUAL
    lda #$FFF4.w
    sta.l PV_TMP_OFFSET
    bra DCF_mismatch
DCF_mismatch:
    sep #$20
    .ACCU 8
    lda.l PV_NMISAVE                    ; one full retry: an NMI that lands
    bne DCF_mismatch_count              ;   mid-run can trash a DP scratch in
    lda #1.b                            ;   either implementation; a genuine
    sta.l PV_NMISAVE                    ;   logic bug survives the re-run
    jmp DCF_retry
DCF_mismatch_count:
    rep #$20
    .ACCU 16
    lda.l PV_DRAW_MISMATCHES
    inc a
    sta.l PV_DRAW_MISMATCHES
    bne DCF_mismatch_counted
    lda.l PV_DRAW_MISMATCHES+2
    inc a
    sta.l PV_DRAW_MISMATCHES+2
DCF_mismatch_counted:
    sep #$20
    .ACCU 8
    lda.l PV_FIRST_VALID
    beq DCF_save_first
    jmp DCF_after_compare
DCF_save_first:
    lda #1.b
    sta.l PV_FIRST_VALID
    lda #1.b
    sta.l PV_FIRST_TYPE
    rep #$20
    .ACCU 16
    lda.l PV_TMP_OFFSET
    sta.l PV_FIRST_OFFSET
    lda.l PV_TMP_EXPECTED
    sta.l PV_FIRST_EXPECTED
    lda.l PV_TMP_ACTUAL
    sta.l PV_FIRST_ACTUAL
    lda.l PV_DRAW_IN_A
    sta.l PV_FIRST_CONTEXT
    lda.l PV_DRAW_IN_X
    sta.l PV_FIRST_CONTEXT+2
    lda.l PV_DRAW_IN_Y
    sta.l PV_FIRST_CONTEXT+4
    lda.l PV_DRAW_SCR0
    sta.l PV_FIRST_CONTEXT+6
    lda.l PV_DRAW_SCR1
    sta.l PV_FIRST_CONTEXT+8
    lda.l PV_DRAW_SCR2
    sta.l PV_FIRST_CONTEXT+10
    lda.l PV_DRAW_SCR3
    sta.l PV_FIRST_CONTEXT+12
    lda.l PV_DRAW_SCR4
    sta.l PV_FIRST_CONTEXT+14
    lda.l PV_DRAW_SCR5
    sta.l PV_FIRST_CONTEXT+16
    lda.l PV_DRAW_SCR6
    sta.l PV_FIRST_CONTEXT+18
    lda.l PV_DRAW_PBASE
    sta.l PV_FIRST_CONTEXT+20
    lda.l PV_DRAW_PRE_TOP
    sta.l PV_FIRST_CONTEXT+22
    lda.l PV_DRAW_PRE_DROP
    sta.l PV_FIRST_CONTEXT+24
    lda.l PV_DRAW_LPTR
    sta.l PV_FIRST_CONTEXT+26
    sep #$20
    .ACCU 8
    lda.l PV_DRAW_AOFS
    sta.l PV_FIRST_CONTEXT+28
    lda.l PV_DRAW_LPTR+2
    sta.l PV_FIRST_CONTEXT+29
    ldx #0.w
DCF_snapshot_old_oam:
    lda.l PV_DRAW_OLD_OAM,x
    sta.l PV_FIRST_OLD_OAM,x
    inx
    cpx #544.w
    bne DCF_snapshot_old_oam
    ldx #0.w
DCF_snapshot_new_oam:
    lda.w OAMBUF,x
    sta.l PV_FIRST_NEW_OAM,x
    inx
    cpx #512.w
    bne DCF_snapshot_new_oam
    ldx #0.w
DCF_snapshot_new_hi:
    lda.w OAMHI,x
    sta.l PV_FIRST_NEW_OAM+512,x
    inx
    cpx #32.w
    bne DCF_snapshot_new_hi
DCF_after_compare:
    rep #$30
    .ACCU 16
    .INDEX 16
    ply
    plx
    pla
    plp
    rtl

DCF_retry:
    rep #$30
    .ACCU 16
    .INDEX 16
    ply
    plx
    pla
    plp                             ; balance the pushes from the new run
    lda.l PV_DRAW_SCR0
    sta scr0
    lda.l PV_DRAW_SCR1
    sta scr1
    lda.l PV_DRAW_SCR2
    sta scr2
    lda.l PV_DRAW_SCR3
    sta scr3
    lda.l PV_DRAW_SCR4
    sta scr4
    lda.l PV_DRAW_SCR5
    sta scr5
    lda.l PV_DRAW_SCR6
    sta scr6
    lda.l PV_DRAW_PBASE
    sta pbase
    lda.l PV_DRAW_LPTR
    sta lptr
    lda.l PV_DRAW_PRE_TOP
    sta oamtop
    lda.l PV_DRAW_PRE_DROP
    sta.w RT_OAMDROP
    sep #$20
    .ACCU 8
    lda.l PV_DRAW_AOFS
    sta aofs
    lda.l PV_DRAW_LPTR+2
    sta lptr+2
    ldx #0.w
DCF_retry_pre_oam:
    lda.l PV_DRAW_PRE_OAM,x
    sta.w OAMBUF,x
    inx
    cpx #512.w
    bne DCF_retry_pre_oam
    ldx #0.w
DCF_retry_pre_hi:
    lda.l PV_DRAW_PRE_OAM+512,x
    sta.w OAMHI,x
    inx
    cpx #32.w
    bne DCF_retry_pre_hi
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.l PV_DRAW_IN_X
    tax
    lda.l PV_DRAW_IN_Y
    tay
    lda.l PV_DRAW_IN_A
    jsl DrawCellsOldFar
    rep #$30
    .ACCU 16
    .INDEX 16
    lda oamtop
    sta.l PV_DRAW_OLD_TOP
    lda.w RT_OAMDROP
    sta.l PV_DRAW_OLD_DROP
    lda scr0
    sta.l PV_DRAW_OLD_SCR0
    lda scr1
    sta.l PV_DRAW_OLD_SCR1
    lda scr2
    sta.l PV_DRAW_OLD_SCR2
    sep #$20
    .ACCU 8
    ldx #0.w
DCF_retry_old_oam:
    lda.w OAMBUF,x
    sta.l PV_DRAW_OLD_OAM,x
    inx
    cpx #512.w
    bne DCF_retry_old_oam
    ldx #0.w
DCF_retry_old_hi:
    lda.w OAMHI,x
    sta.l PV_DRAW_OLD_OAM+512,x
    inx
    cpx #32.w
    bne DCF_retry_old_hi
    ldx #0.w
DCF_retry_rst_oam:
    lda.l PV_DRAW_PRE_OAM,x
    sta.w OAMBUF,x
    inx
    cpx #512.w
    bne DCF_retry_rst_oam
    ldx #0.w
DCF_retry_rst_hi:
    lda.l PV_DRAW_PRE_OAM+512,x
    sta.w OAMHI,x
    inx
    cpx #32.w
    bne DCF_retry_rst_hi
    jmp DCF_run_new

DrawCellsOldFar:
DCF_old_cell:
    cpx #512.w
    bcc DCF_old_in_range
    inc.w RT_OAMDROP
    stx oamtop
    jmp DCF_old_done
DCF_old_in_range:
    rep #$20
    .ACCU 16
    tya
    clc
    adc #2
    tay
    lda [lptr],y
    sta scr6
    tya
    sec
    sbc #2
    tay
    sep #$20
    .ACCU 8
    lda [lptr],y
    sta scr3
    iny
    rep #$20
    .ACCU 16
    lda scr3
    and #$00FF.w
    bit #$0080.w
    beq DCF_old_dx_positive
    ora #$FF00.w
DCF_old_dx_positive:
    sta scr3
    lda scr0
    and #$0001.w
    beq DCF_old_dx_done
    lda scr3
    eor #$FFFF.w
    inc a
    sec
    sbc #8
    bit scr6
    bmi DCF_old_dx_done
    sec
    sbc #8
DCF_old_dx_done:
    sta scr3
    lda scr1
    clc
    adc scr3
    sta scr5
    sep #$20
    .ACCU 8
    sta.w OAMBUF,x
    lda [lptr],y
    sta scr3
    iny
    rep #$20
    .ACCU 16
    lda scr0
    and #$0002.w
    bne DCF_old_dy_vflip
    lda scr3
    xba
    and #$00FF.w
    bit #$0080.w
    beq DCF_old_dy_positive
    ora #$FF00.w
DCF_old_dy_positive:
    clc
    adc scr2
    bra DCF_old_y_done
DCF_old_dy_vflip:
    lda scr3
    xba
    and #$00FF.w
    eor #$00FF.w
    pha
    lda scr6
    bmi DCF_old_dy_vflip8
    pla
    clc
    adc #$0071.w
    bra DCF_old_dy_sum
DCF_old_dy_vflip8:
    pla
    clc
    adc #$0079.w
DCF_old_dy_sum:
    clc
    adc scr2
    sec
    sbc #$0080.w                       ; same -128 bias as the fast path
DCF_old_y_done:
    bpl DCF_old_y_visible
    lda #$00F0.w
DCF_old_y_visible:
    sep #$20
    .ACCU 8
    sta.w OAMBUF+1,x
    rep #$20
    .ACCU 16
    iny
    iny
    lda scr6
    and #$7FFF.w
    clc
    adc pbase
    sta scr3
    sep #$20
    .ACCU 8
    lda scr3
    sta.w OAMBUF+2,x
    lda aofs
    sta.w OAMBUF+3,x
    lda scr3+1
    beq DCF_old_attr_ok
    lda.w OAMBUF+3,x
    ora #$01.b
    sta.w OAMBUF+3,x
DCF_old_attr_ok:
    lda scr0
    and #$02.b
    beq +
    lda.w OAMBUF+3,x
    ora #$80.b                          ; OAM vertical flip
    sta.w OAMBUF+3,x
+   lda scr0
    and #$01.b
    beq DCF_old_flip_done
    lda.w OAMBUF+3,x
    ora #$40.b
    sta.w OAMBUF+3,x
DCF_old_flip_done:
    rep #$20
    .ACCU 16
    phx
    txa
    lsr a
    lsr a
    sta scr3
    and #$0003.w
    asl a
    tax
    lda #$0000.w
    bit scr6
    bmi DCF_old_size_ready
    lda #$0002.w
DCF_old_size_ready:
    phy
    ldy scr5
    bpl DCF_old_x_positive
    ora #$0001.w
DCF_old_x_positive:
    cpy #256.w
    bcc DCF_old_x_in_range
    ora #$0001.w
DCF_old_x_in_range:
    cpx #0
    beq DCF_old_shift_done
DCF_old_shift:
    asl a
    dex
    bne DCF_old_shift
DCF_old_shift_done:
    sta scr5
    lda scr3
    lsr a
    lsr a
    tax
    sep #$20
    .ACCU 8
    lda scr5
    ora.w OAMHI,x
    sta.w OAMHI,x
    rep #$20
    .ACCU 16
    ply
    plx
    inx
    inx
    inx
    inx
    sep #$20
    .ACCU 8
    dec scr4
    rep #$20
    .ACCU 16
    beq DCF_old_finish
    jmp DCF_old_cell
DCF_old_finish:
    stx oamtop
DCF_old_done:
    rtl
.ENDIF

BOFillFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx oamtop
    lda #$F0F0.w
BOF_head:
    cpx #512.w
    bcs BOF_done
    txa
    and #$000F.w
    beq BOF_bulk
    lda #$F0F0.w
    sta.w OAMBUF,x
    inx
    inx
    bra BOF_head
BOF_bulk:
    lda #$F0F0.w
    sta.w OAMBUF,x
    sta.w OAMBUF+2,x
    sta.w OAMBUF+4,x
    sta.w OAMBUF+6,x
    sta.w OAMBUF+8,x
    sta.w OAMBUF+10,x
    sta.w OAMBUF+12,x
    sta.w OAMBUF+14,x
    txa
    clc
    adc #16.w
    tax
    cpx #512.w
    bcc BOF_bulk
BOF_done:
    rtl

HpToPxFar:
    .ACCU 16
    .INDEX 16
.IFDEF KOF_PERF_VERIFY
    sta.l PV_HP_INPUT
    lda.l PV_HP_CALLS
    inc a
    sta.l PV_HP_CALLS
    bne HPT_calls_counted
    lda.l PV_HP_CALLS+2
    inc a
    sta.l PV_HP_CALLS+2
HPT_calls_counted:
    lda.l PV_HP_INPUT
.ENDIF
    and #$00FF.w
    sta scr1
    asl a
    asl a
    asl a
    clc
    adc scr1
    adc scr1
    adc scr1
    ldx #0.w
HPT_hundreds:
    cmp #250.w
    bcc HPT_tens_start
    sbc #250.w
    inx
    bra HPT_hundreds
HPT_tens_start:
    stx scr1
    ldx #0.w
HPT_tens:
    cmp #25.w
    bcc HPT_result
    sbc #25.w
    inx
    bra HPT_tens
HPT_result:
    lda scr1
    asl a
    sta scr1
    asl a
    asl a
    clc
    adc scr1
    stx scr1
    clc
    adc scr1
    tax
.IFDEF KOF_PERF_VERIFY
    sta.l PV_HP_FAST_A
    txa
    sta.l PV_HP_FAST_X
    lda.l PV_HP_INPUT
    jsr HPT_old
    sta.l PV_HP_OLD_A
    txa
    sta.l PV_HP_OLD_X
    lda.l PV_HP_FAST_A
    cmp.l PV_HP_OLD_A
    beq HPT_compare_x
    lda.l PV_HP_OLD_A
    sta.l PV_TMP_EXPECTED
    lda.l PV_HP_FAST_A
    sta.l PV_TMP_ACTUAL
    lda #0.w
    sta.l PV_TMP_OFFSET
    jmp HPT_mismatch
HPT_compare_x:
    lda.l PV_HP_FAST_X
    cmp.l PV_HP_OLD_X
    bne HPT_x_mismatch
    jmp HPT_compare_done
HPT_x_mismatch:
    lda.l PV_HP_OLD_X
    sta.l PV_TMP_EXPECTED
    lda.l PV_HP_FAST_X
    sta.l PV_TMP_ACTUAL
    lda #1.w
    sta.l PV_TMP_OFFSET
HPT_mismatch:
    rep #$20
    .ACCU 16
    lda.l PV_HP_MISMATCHES
    inc a
    sta.l PV_HP_MISMATCHES
    bne HPT_mismatch_counted
    lda.l PV_HP_MISMATCHES+2
    inc a
    sta.l PV_HP_MISMATCHES+2
HPT_mismatch_counted:
    sep #$20
    .ACCU 8
    lda.l PV_FIRST_VALID
    bne HPT_compare_done
    lda #1.b
    sta.l PV_FIRST_VALID
    lda #2.b
    sta.l PV_FIRST_TYPE
    rep #$20
    .ACCU 16
    lda.l PV_TMP_OFFSET
    sta.l PV_FIRST_OFFSET
    lda.l PV_TMP_EXPECTED
    sta.l PV_FIRST_EXPECTED
    lda.l PV_TMP_ACTUAL
    sta.l PV_FIRST_ACTUAL
    lda.l PV_HP_INPUT
    sta.l PV_FIRST_CONTEXT
    lda.l PV_HP_OLD_A
    sta.l PV_FIRST_CONTEXT+2
    lda.l PV_HP_FAST_A
    sta.l PV_FIRST_CONTEXT+4
    lda.l PV_HP_OLD_X
    sta.l PV_FIRST_CONTEXT+6
    lda.l PV_HP_FAST_X
    sta.l PV_FIRST_CONTEXT+8
HPT_compare_done:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.l PV_HP_FAST_X
    tax
    lda.l PV_HP_FAST_A
.ENDIF
    rtl
.IFDEF KOF_PERF_VERIFY
HPT_old:
    and #$00FF.w
    sta scr1
    asl a
    asl a
    asl a
    clc
    adc scr1
    adc scr1
    adc scr1
    ldx #0.w
HPT_old_loop:
    cmp #25.w
    bcc HPT_old_done
    sec
    sbc #25.w
    inx
    bra HPT_old_loop
HPT_old_done:
    txa
    rts
.ENDIF

PowToPxFar:
    .ACCU 16
    .INDEX 16
.IFDEF KOF_PERF_VERIFY
    sta.l PV_POW_INPUT
    lda.l PV_POW_CALLS
    inc a
    sta.l PV_POW_CALLS
    bne PTP_calls_counted
    lda.l PV_POW_CALLS+2
    inc a
    sta.l PV_POW_CALLS+2
PTP_calls_counted:
    lda.l PV_POW_INPUT
.ENDIF
    sta scr1
    asl a
    asl a
    asl a
    clc
    adc scr1
    adc scr1
    adc scr1
    ldx #0.w
PTP_thousands:
    cmp #3750.w
    bcc PTP_hundreds_start
    sbc #3750.w
    inx
    bra PTP_thousands
PTP_hundreds_start:
    stx scr1
    ldx #0.w
PTP_hundreds:
    cmp #375.w
    bcc PTP_result
    sbc #375.w
    inx
    bra PTP_hundreds
PTP_result:
    lda scr1
    asl a
    sta scr1
    asl a
    asl a
    clc
    adc scr1
    stx scr1
    clc
    adc scr1
    tax
.IFDEF KOF_PERF_VERIFY
    sta.l PV_POW_FAST_A
    txa
    sta.l PV_POW_FAST_X
    lda.l PV_POW_INPUT
    jsr PTP_old
    sta.l PV_POW_OLD_A
    txa
    sta.l PV_POW_OLD_X
    lda.l PV_POW_FAST_A
    cmp.l PV_POW_OLD_A
    beq PTP_compare_x
    lda.l PV_POW_OLD_A
    sta.l PV_TMP_EXPECTED
    lda.l PV_POW_FAST_A
    sta.l PV_TMP_ACTUAL
    lda #0.w
    sta.l PV_TMP_OFFSET
    jmp PTP_mismatch
PTP_compare_x:
    lda.l PV_POW_FAST_X
    cmp.l PV_POW_OLD_X
    bne PTP_x_mismatch
    jmp PTP_compare_done
PTP_x_mismatch:
    lda.l PV_POW_OLD_X
    sta.l PV_TMP_EXPECTED
    lda.l PV_POW_FAST_X
    sta.l PV_TMP_ACTUAL
    lda #1.w
    sta.l PV_TMP_OFFSET
PTP_mismatch:
    rep #$20
    .ACCU 16
    lda.l PV_POW_MISMATCHES
    inc a
    sta.l PV_POW_MISMATCHES
    bne PTP_mismatch_counted
    lda.l PV_POW_MISMATCHES+2
    inc a
    sta.l PV_POW_MISMATCHES+2
PTP_mismatch_counted:
    sep #$20
    .ACCU 8
    lda.l PV_FIRST_VALID
    bne PTP_compare_done
    lda #1.b
    sta.l PV_FIRST_VALID
    lda #3.b
    sta.l PV_FIRST_TYPE
    rep #$20
    .ACCU 16
    lda.l PV_TMP_OFFSET
    sta.l PV_FIRST_OFFSET
    lda.l PV_TMP_EXPECTED
    sta.l PV_FIRST_EXPECTED
    lda.l PV_TMP_ACTUAL
    sta.l PV_FIRST_ACTUAL
    lda.l PV_POW_INPUT
    sta.l PV_FIRST_CONTEXT
    lda.l PV_POW_OLD_A
    sta.l PV_FIRST_CONTEXT+2
    lda.l PV_POW_FAST_A
    sta.l PV_FIRST_CONTEXT+4
    lda.l PV_POW_OLD_X
    sta.l PV_FIRST_CONTEXT+6
    lda.l PV_POW_FAST_X
    sta.l PV_FIRST_CONTEXT+8
PTP_compare_done:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.l PV_POW_FAST_X
    tax
    lda.l PV_POW_FAST_A
.ENDIF
    rtl
.IFDEF KOF_PERF_VERIFY
PTP_old:
    sta scr1
    asl a
    asl a
    asl a
    clc
    adc scr1
    adc scr1
    adc scr1
    ldx #0.w
PTP_old_loop:
    cmp #375.w
    bcc PTP_old_done
    sec
    sbc #375.w
    inx
    bra PTP_old_loop
PTP_old_done:
    txa
    rts
.ENDIF

FillBarMemoFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    pei (scr0)
    pei (scr1)
    pei (scr2)
.IFDEF KOF_PERF_VERIFY
    lda.l PV_FB_CALLS
    inc a
    sta.l PV_FB_CALLS
    bne FBM_calls_counted
    lda.l PV_FB_CALLS+2
    inc a
    sta.l PV_FB_CALLS+2
FBM_calls_counted:
.ENDIF
    stx scr0
    sty scr1
    tyx
    sep #$20
    .ACCU 8
    lda.l FBM_CACHE+3,x
    bne FBM_valid
    jmp FBM_miss
FBM_valid:
    lda scr5
    cmp.l FBM_CACHE+0,x
    beq FBM_key_px_ok
    jmp FBM_miss
FBM_key_px_ok:
    lda scr6
    cmp.l FBM_CACHE+1,x
    beq FBM_key_attr_ok
    jmp FBM_miss
FBM_key_attr_ok:
    lda scr3
    cmp.l FBM_CACHE+2,x
    beq FBM_key_group_ok
    jmp FBM_miss
FBM_key_group_ok:
    rep #$20
    .ACCU 16
    lda scr0
    cmp.l FBM_CACHE+4,x
    beq FBM_hit
    jmp FBM_miss
FBM_hit:
.IFDEF KOF_PERF_VERIFY
    ldx scr0
    jsl FillBarNearT
    phx
    jsr FBM_rowstart
    sta scr2
    sep #$20
    .ACCU 8
    lda #$7E.b                        ; HUDMAP lives in bank $7E
    sta scr2+2
    rep #$20
    .ACCU 16
    ldx scr1
    ldy #0.w
    sep #$20
    .ACCU 8
FBM_verify_row:
    lda [scr2],y
    cmp.l FBM_CACHE+6,x
    beq FBM_verify_equal
    sta.l PV_TMP_ACTUAL
    lda.l FBM_CACHE+6,x
    sta.l PV_TMP_EXPECTED
    lda #0.b
    sta.l PV_TMP_ACTUAL+1
    sta.l PV_TMP_EXPECTED+1
    rep #$20
    .ACCU 16
    tya
    sta.l PV_TMP_OFFSET
    jmp FBM_verify_mismatch
FBM_verify_equal:
    iny
    inx
    cpy #22.w
    bne FBM_verify_row
    bra FBM_verify_done
FBM_verify_mismatch:
    lda.l PV_FB_MISMATCHES
    inc a
    sta.l PV_FB_MISMATCHES
    bne FBM_verify_counted
    lda.l PV_FB_MISMATCHES+2
    inc a
    sta.l PV_FB_MISMATCHES+2
FBM_verify_counted:
    sep #$20
    .ACCU 8
    lda.l PV_FIRST_VALID
    bne FBM_verify_done
    lda #1.b
    sta.l PV_FIRST_VALID
    lda #4.b
    sta.l PV_FIRST_TYPE
    rep #$20
    .ACCU 16
    lda.l PV_TMP_OFFSET
    sta.l PV_FIRST_OFFSET
    lda.l PV_TMP_EXPECTED
    sta.l PV_FIRST_EXPECTED
    lda.l PV_TMP_ACTUAL
    sta.l PV_FIRST_ACTUAL
    ldx scr1
    lda.l FBM_CACHE+0,x
    and #$00FF.w
    sta.l PV_FIRST_CONTEXT
    lda.l FBM_CACHE+1,x
    and #$00FF.w
    sta.l PV_FIRST_CONTEXT+2
    lda.l FBM_CACHE+2,x
    and #$00FF.w
    sta.l PV_FIRST_CONTEXT+4
    lda.l FBM_CACHE+4,x
    sta.l PV_FIRST_CONTEXT+6
    lda scr0
    sta.l PV_FIRST_CONTEXT+8
    lda scr1
    sta.l PV_FIRST_CONTEXT+10
FBM_verify_done:
    rep #$30
    .ACCU 16
    .INDEX 16
    plx
    ldy #11.w
    jmp FBM_out
.ELSE
    ; WLA-DX uses source-bank, destination-bank operand order for MVN.
    jsr FBM_rowstart
    tay
    lda scr1
    clc
    adc #((FBM_CACHE+6)&$FFFF).w
    tax
    lda #21.w
    mvn $7F,$7E
    rep #$30
    .ACCU 16
    .INDEX 16
    lda scr6
    and #$0040.w
    bne FBM_cached_x_flip
    lda scr0
    clc
    adc #22.w
    tax
    bra FBM_cached_x_done
FBM_cached_x_flip:
    lda scr0
    sec
    sbc #22.w
    tax
FBM_cached_x_done:
    ldy #11.w
    jmp FBM_cached_result
.ENDIF
FBM_miss:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx scr1
    sep #$20
    .ACCU 8
    lda #0.b
    sta.l FBM_CACHE+3,x
    lda scr5
    sta.l FBM_CACHE+0,x
    lda scr6
    sta.l FBM_CACHE+1,x
    lda scr3
    sta.l FBM_CACHE+2,x
    rep #$20
    .ACCU 16
    lda scr0
    sta.l FBM_CACHE+4,x
    ldx scr0
    jsl FillBarNearT
    phx
    jsr FBM_rowstart
    tax
    lda scr1
    clc
    adc #((FBM_CACHE+6)&$FFFF).w
    tay
    lda #21.w
    mvn $7E,$7F
    sep #$20
    .ACCU 8
    lda #$7E.b
    pha
    plb
    ldx scr1
    lda #1.b
    sta.l FBM_CACHE+3,x
    plx
    rep #$30
    .ACCU 16
    .INDEX 16
    ldy #11.w
    jmp FBM_out
FBM_cached_result:
    sep #$20
    .ACCU 8
    lda scr5
    sec
    sbc #80.b
    bcs FBM_last_width_ready
    lda #0.b
FBM_last_width_ready:
    cmp #8.b
    bcc FBM_last_width_store
    lda #8.b
FBM_last_width_store:
    sta scr4
    lda scr5
    sec
    sbc #88.b
    bcs FBM_remaining_ready
    lda #0.b
FBM_remaining_ready:
    sta scr5
    rep #$30
    .ACCU 16
    .INDEX 16
FBM_out:
    pla
    sta scr2
    pla
    sta scr1
    pla
    sta scr0
    rtl

FBM_rowstart:
    lda scr6
    and #$0040.w
    beq FBM_plain_row
    lda scr0
    sec
    sbc #20.w
    bra FBM_row_offset
FBM_plain_row:
    lda scr0
FBM_row_offset:
    clc
    adc #HUDMAP.w
    rts

FillBarMemoResetFar:
    rep #$20
    .ACCU 16
    lda #0.w
    sta.l FBM_CACHE+3
    sta.l FBM_CACHE+35
    sta.l FBM_CACHE+67
    sta.l FBM_CACHE+99
    rtl

.IFDEF KOF_PERF_VERIFY
PerfVerifyReset:
    php
    rep #$20
    .ACCU 16
    lda.l PV_SIGNATURE
    cmp #$5650.w
    bne PVR_initialize
    lda.l PV_SIGNATURE+2
    cmp #$3130.w
    beq PVR_done
PVR_initialize:
    lda #0.w
    sta.l PV_DRAW_CALLS
    sta.l PV_DRAW_CALLS+2
    sta.l PV_DRAW_MISMATCHES
    sta.l PV_DRAW_MISMATCHES+2
    sta.l PV_HP_CALLS
    sta.l PV_HP_CALLS+2
    sta.l PV_HP_MISMATCHES
    sta.l PV_HP_MISMATCHES+2
    sta.l PV_POW_CALLS
    sta.l PV_POW_CALLS+2
    sta.l PV_POW_MISMATCHES
    sta.l PV_POW_MISMATCHES+2
    sta.l PV_FB_CALLS
    sta.l PV_FB_CALLS+2
    sta.l PV_FB_MISMATCHES
    sta.l PV_FB_MISMATCHES+2
    sta.l PV_TMP_OFFSET
    sta.l PV_TMP_EXPECTED
    sta.l PV_TMP_ACTUAL
    lda #$5650.w
    sta.l PV_SIGNATURE
    lda #$3130.w
    sta.l PV_SIGNATURE+2
    sep #$20
    .ACCU 8
    lda #0.b
    sta.l PV_FIRST_VALID
    sta.l PV_FIRST_TYPE
PVR_done:
    plp
    rtl
.ENDIF

.ENDS

; ---------------------------------------------------------------------------
; MSU -> WRAM byte copy for MsuReadAlignedFar (streamed voices).  The port
; stays on the CPU data path (see MRA_ready), but the old one-byte loop ran
; from SlowROM bank $3E at ~160 master cycles per byte, so a 512-byte voice
; chunk plus its sector prefix took up to ~95 scanlines.  Here the prefix
; skip is unrolled x8 and the payload x16 with long stores into bank $7F.
; In:  A8/X16, D = engine DP, MSU_PREFIX = bytes to discard,
;      scr0 = 24-bit destination, scr3 = payload bytes.
; Out: A8/X16.  scr0/scr3 preserved; X/Y clobbered.
.SECTION "MsuCopyFast" FREE
MsuCopyFar:
    .ACCU 8
    .INDEX 16
    ldx.w MSU_PREFIX
MCF_skip8:
    cpx #8.w
    bcc MCF_skip1
    lda.l MSU_DATA
    lda.l MSU_DATA
    lda.l MSU_DATA
    lda.l MSU_DATA
    lda.l MSU_DATA
    lda.l MSU_DATA
    lda.l MSU_DATA
    lda.l MSU_DATA
    rep #$20
    .ACCU 16
    txa
    sec
    sbc #8.w
    tax
    sep #$20
    .ACCU 8
    bra MCF_skip8
MCF_skip1:
    cpx #0.w
    beq MCF_payload
    lda.l MSU_DATA
    dex
    bra MCF_skip1
MCF_payload:
    lda scr0+2
    cmp #$7F.b
    beq +
    jmp MCF_generic                     ; only the voice cache bank is unrolled
+   ldx scr0
    rep #$20
    .ACCU 16
    lda scr3
    lsr a
    lsr a
    lsr a
    lsr a
    bne +
    jmp MCF_tail
+   tay                                 ; Y = 16-byte blocks
    sep #$20
    .ACCU 8
MCF_block:
    lda.l MSU_DATA
    sta.l $7F0000,x
    lda.l MSU_DATA
    sta.l $7F0001,x
    lda.l MSU_DATA
    sta.l $7F0002,x
    lda.l MSU_DATA
    sta.l $7F0003,x
    lda.l MSU_DATA
    sta.l $7F0004,x
    lda.l MSU_DATA
    sta.l $7F0005,x
    lda.l MSU_DATA
    sta.l $7F0006,x
    lda.l MSU_DATA
    sta.l $7F0007,x
    lda.l MSU_DATA
    sta.l $7F0008,x
    lda.l MSU_DATA
    sta.l $7F0009,x
    lda.l MSU_DATA
    sta.l $7F000A,x
    lda.l MSU_DATA
    sta.l $7F000B,x
    lda.l MSU_DATA
    sta.l $7F000C,x
    lda.l MSU_DATA
    sta.l $7F000D,x
    lda.l MSU_DATA
    sta.l $7F000E,x
    lda.l MSU_DATA
    sta.l $7F000F,x
    rep #$21
    .ACCU 16
    txa
    adc #16.w
    tax
    sep #$20
    .ACCU 8
    dey
    beq MCF_tail
    jmp MCF_block                       ; the 16-byte body is beyond bne range
MCF_tail:
    rep #$20
    .ACCU 16
    lda scr3
    and #$000F.w
    tay
    sep #$20
    .ACCU 8
    cpy #0.w
    beq MCF_done
MCF_tail1:
    lda.l MSU_DATA
    sta.l $7F0000,x
    inx
    dey
    bne MCF_tail1
MCF_done:
    rtl
MCF_generic:
    ldy #0.w
MCF_gen1:
    cpy scr3
    bcs MCF_done
    lda.l MSU_DATA
    sta [scr0],y
    iny
    bra MCF_gen1
.ENDS
