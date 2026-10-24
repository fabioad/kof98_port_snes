; Normal special/super cancel gate (called with JSR from the Fight bank).
; Lives beside CancelTab in bank 50's low half, which shares the Fight
; code's CPU bank ($F2), so the call stays a near JSR.
; A(16) = 1 when the current normal may cancel into a special or super;
; X = fofs on exit.  The descriptor's CH_CANCELROW word points at a 6-byte
; row of opens for the strong normals 6, 8, 20, 22, 24 and 26.  The table is
; emitted with 0 for strong normals, so the contact check below is the only
; gate: the first connected hit can be canceled immediately.
CancelGate:
    rep #$30
    .ACCU 16
    .INDEX 16                          ; generated tables may leave WLA in X=8
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_HITDONE,x
    beq CG_no
    lda FP+F_STATE,x
    ; Light ground normals keep the old contact-only special cancel.
    cmp #5.b
    beq CG_light
    cmp #7.b
    beq CG_light
    cmp #19.b
    beq CG_light
    cmp #21.b
    beq CG_light
    cmp #6.b
    beq CG_i0
    cmp #8.b
    beq CG_i1
    cmp #20.b
    beq CG_i2
    cmp #22.b
    beq CG_i3
    cmp #24.b
    beq CG_i4
    cmp #26.b
    beq CG_i5
    bra CG_no
CG_light:
    rep #$20
    .ACCU 16
    lda #1
    rts

; The gate reaches these rows with M=1 (the comparisons above run 8-bit).
; Keep the immediates 8-bit too: a 16-bit `lda #n` here leaves a $00 byte
; that the CPU decodes as BRK, and the RTI then resumes mid-instruction --
; the strong normals (6, 8, 20, 22, 24, 26) ran off into data on contact.
CG_i0:
    sep #$20
    .ACCU 8
    lda #0
    bra CG_read
CG_i1:
    lda #1
    bra CG_read
CG_i2:
    lda #2
    bra CG_read
CG_i3:
    lda #3
    bra CG_read
CG_i4:
    lda #4
    bra CG_read
CG_i5:
    lda #5
CG_read:
    sta ct_off                        ; row index (0..5)
    rep #$20
    .ACCU 16
    ldy #CH_CANCELROW.w
    ldx #boxp
    jsr CharPtr                       ; boxp -> descriptor row pointer
    sep #$20
    .ACCU 8
    lda #:CancelTab.b                 ; rows live in the CancelData bank, not
    sta boxp+2                        ;   in the character's table bank
    rep #$20
    .ACCU 16
    lda ct_off
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    ldx fofs
    lda [boxp],y                      ; first cancelable anim element
    cmp FP+F_FRAME,x
    beq CG_yes                        ; frame >= open: window is open
    bcc CG_yes
CG_no:
    rep #$20
    .ACCU 16
    lda #0
    rts
CG_yes:
    rep #$20
    .ACCU 16
    lda #1
    rts

; Close-range normal: punch or kick, weak or strong, with a stronger bias
; when the foe is already inside the pushbox.  Kept beside CancelGate to
; leave room in the 32 KiB Fight bank.
AI_DoNormal:
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_JOY,x
    stz FP+F_JOYPR,x
    sep #$20
    .ACCU 8
    jsr AI_Rand
    and #$03
    sta AI_TMP
    lda AI_DIST
    cmp #40
    bcs +
    lda AI_TMP
    ora #$02
    sta AI_TMP
+   lda AI_TMP
    and #$01
    beq AI_normal_punch
    lda AI_TMP
    and #$02
    beq +
    lda #$80.b                          ; strong kick (A)
    bra ++
+   lda #$40.b                          ; weak kick (B)
++  ldx fofs
    sta FP+F_JOY+1,x
    sta FP+F_JOYPR+1,x
    bra AI_normal_done
AI_normal_punch:
    lda AI_TMP
    and #$02
    beq +
    lda #$80.b                          ; strong punch (X)
    bra ++
+   lda #$40.b                          ; weak punch (Y)
++  ldx fofs
    sta FP+F_JOY,x
    sta FP+F_JOYPR,x
AI_normal_done:
    lda #6
    sta AI_TMP
    jmp AI_SetTimer

; Connected grounded normal -> special/super hit-confirm.  CancelGate only
; gates human pad input; the CPU enters the follow-up directly, so it uses
; the same F_HITDONE contact signal and a level-scaled commit rate.  A short
; per-side throttle keeps a missed scan from retrying every tick.  Kept in
; the CancelData window to leave room in the 32 KiB Fight bank.
AI_ComboCheck:
    rep #$20
    .ACCU 16
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_HITDONE,x
    beq AC_no
    lda AI_LEVEL
    cmp #3
    bcc AC_no
    jsr AI_SideX
    lda AI_TIMER2,x
    bne AC_no
    lda #12
    sta AI_TIMER2,x
    lda AI_AGGR
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcs AC_no
    jsr AI_Perceive                    ; refresh distance/opponent state
    sep #$20
    .ACCU 8
    jsr AI_Rand
    and #$01
    beq AC_special
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_POWER,x
    cmp #1000.w
    bcc AC_special
    sep #$20
    .ACCU 8
    lda #2                             ; super/MAX-super table
    sta AI_SCANMODE
    bra AC_scan
AC_special:
    lda #0                             ; plain special table
    sta AI_SCANMODE
AC_scan:
    jsr AI_ScanMove
    bcc AC_no
    lda scr3                           ; sid selected by AI_ScanMove
    jsr AI_StartMove
    inc.w AI_DBG_COMBO
    jsr AI_SideX
    stz AI_TIMER2,x
    sec
    rts
AC_no:
    clc
    rts

; FUSION generic air throw (near JSR from Fight).
AirThrowTry:
    rep #$20
    .ACCU 16
    ldx fofs
    txa
    eor #FP2OFS.w
    sta scr6                              ; victim offset
    tax
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_HIT.w
    bne +
    jmp AT_no
+
    cmp #S_DOWN.w
    bne +
    jmp AT_no
+
    cmp #S_GETUP.w
    bne +
    jmp AT_no
+
    lda FP+F_INVUL,x
    and #$00FF.w
    beq +
    jmp AT_no
+
    lda FP+F_Y,x
    bne +
    jmp AT_no                              ; victim must be airborne
+
    sta scr0
    ldx fofs
    lda FP+F_Y,x
    sec
    sbc scr0
    bpl +
    eor #$FFFF.w
    inc a
+   cmp #(40<<8).w
    bcs AT_no
    ldx fofs
    lda FP+F_X,x
    sta scr0
    ldx scr6
    lda FP+F_X,x
    sec
    sbc scr0
    bpl +
    eor #$FFFF.w
    inc a
+   cmp #(32<<8).w
    bcs AT_no
    ; --- hit: damage + slam the victim down ---
    lda FP+F_HP,x
    sec
    sbc #30.w
    bpl +
    lda #0
+   sta FP+F_HP,x
    lda fofs
    pha
    ldx scr6
    stx fofs
    lda #S_DOWN.w
    jsr EnterState
    ldx fofs
    stz FP+F_VX,x
    lda #$0300.w
    sta FP+F_VY,x
    lda #LIEDOWN.w
    sta FP+F_HTIMER,x
    sep #$20
    .ACCU 8
    lda #6.b
    sta FP+F_PFX,x
    lda #SFX_HIT_HEAVY.b
    jsr SfxPlay
    rep #$20
    .ACCU 16
    pla
    sta fofs
    tax
    lda #S_AIRTHROW.w
    jsr EnterState
    lda #ANIM_AIRT.w
    jsr SetAnimSlot
    ldx fofs
    stz FP+F_VX,x
    stz FP+F_VY,x
    rep #$20
    .ACCU 16
    sec
    rts
AT_no:
    rep #$20
    .ACCU 16
    clc
    rts


StAirThrow:                            ; 108: generic air-throw fall
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne +
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda #S_LAND.w
    jmp SetState16
+   jsr Physics
    jsr AnimTick
    jmp ClampX



BumpWord125:                            ; A signed -> A + A/4
    sta scr3
    bpl +
    eor #$FFFF.w
    inc a
    lsr a
    lsr a
    eor #$FFFF.w
    inc a
    bra ++
+   lsr a
    lsr a
++  clc
    adc scr3
    rts

CounterDraw:
    rep #$20
    .ACCU 16
    lda #((10*32+12)*2).w
    sta scr0
    lda #CounterTxt.w
    sta scr2
    sep #$20
    .ACCU 8
    lda #:CounterTxt.b
    sta scr2+2
    jsr WriteStr
    sep #$20
    .ACCU 8
    inc huddirty
    rep #$20
    .ACCU 16
    rts

CounterClear:
    rep #$20
    .ACCU 16
    ldx #((10*32+12)*2).w
    ldy #7
    lda #0
-   sta HUDMAP,x
    inx
    inx
    dey
    bne -
    sep #$20
    .ACCU 8
    inc huddirty
    rep #$20
    .ACCU 16
    rts

DizzyCheck:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_STAND.w
    beq +
    cmp #S_WALKF.w
    beq +
    cmp #S_WALKB.w
    beq +
    cmp #S_CROUCH.w
    beq +
    cmp #S_GETUP.w
    beq +
    lda #0
    bra ++
+   lda #1
++  and #$00FF.w
    beq DC_no
    sep #$20
    .ACCU 8
    lda FUS_DIZZY,x
    cmp #24.b
    bcc DC_no
    lda FUS_DIZZYT,x
    bne DC_no
    stz FUS_DIZZY,x
    lda #120.b
    sta FUS_DIZZYT,x
    rep #$20
    .ACCU 16
    lda #S_DIZZY.w
    jsr EnterState
    ldx fofs
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda #ANIM_DIZZY.w
    jsr SetAnimSlot
    rep #$20
    .ACCU 16
    rts
DC_no:
    rep #$20
    .ACCU 16
    rts

; FUSION Cover Attack: in team modes a dizzy fighter can be covered by a
; living partner.  Happy synergy always covers, neutral 50%, angry never.

; FUSION Quick MAX check (near JSR from the Fight section).
TryQuickMax:
    rep #$20
    .ACCU 16
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_MAX,x
    bne TQM_no8
    lda FP+F_HITDONE,x
    beq TQM_no8
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR,x
    and #(JOY_Y|JOY_B|JOY_X).w
    cmp #(JOY_Y|JOY_B|JOY_X).w
    bne TQM_no
    lda FP+F_POWER,x
    cmp #1000.w
    bcc TQM_no
    lda #96.w
    jsr EnterState
    rep #$20
    .ACCU 16
    sec
    rts
TQM_no8:
    rep #$20
    .ACCU 16
TQM_no:
    clc
    rts
