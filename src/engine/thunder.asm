; ============================================================================
; thunder.asm — secret Mr. Karate flash card between the attract demo and the
; opening intro.  Only reached when MSU-1 is available and the demo-ending
; RNG roll picks it (see DemoToIntro in menucore.asm).
;
; The card reuses the intro's Mode-1 BG2 still machinery: art/map/palette live
; in bank 82 (gen_menu/thunder.*), tiles at VRAM word $2000 and map at $1800.
; It starts as a pure white screen (thunder flash), fades quickly to the art,
; holds, then fades slowly back to black before handing off to OpnEnter.
;
; This code lives in the free tail of bank 126 ($FC00+) so it does not
; compete with Mr. Karate's code in bank 122 or the full Fight/menu bank.
; All near helpers are reached through the MkCall_* trampolines in fight.asm.
; ============================================================================
.BASE $00
.BANK 126 SLOT 0
.ORGA $FC00
.SECTION "ThunderCode" FORCE
.IFDEF KOF_TINY
; TINY reuses bank 82's upper half for character CHR; the card stays disabled.
ThunderEnterFar:
ThunderTickFar:
    rtl
.ELSE
.IFDEF KOF_OLD
; OLD reuses bank 82's upper half for character CHR; the card stays disabled.
ThunderEnterFar:
ThunderTickFar:
    rtl
.ELSE

ThunderEnterFar:
    sep #$20
    .ACCU 8
    jsl MkCall_VoiceQueueClear
    lda #0
    sta.l NMITIMEN
    sta.l $00420C                         ; no HUD gradient HDMA on this card
    lda #ENGINE_DB.b
    pha
    plb
    stz.b huddirty
    stz.w IN_FX
    lda #$80.b
    sta.l INIDISP                         ; blank for the art upload
    jsl MkCall_MtClear
    rep #$30
    .ACCU 16
    .INDEX 16
    lda #ThunderChr.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:ThunderChr
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(ThunderChr_End-ThunderChr).w
    sta.b I_LEN
    ldx #$2000.w                          ; BG2 tile word, like the intro
    jsl MkCall_InVCopy

    lda #ThunderMap.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:ThunderMap
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #2048.w
    sta.b I_LEN
    ldx #$1800.w                          ; BG2 map word
    jsl MkCall_InVCopy

    lda #ThunderPal.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:ThunderPal
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #128.w
    sta.b I_LEN
    ldx #0
    jsl MkCall_InCgRam
    jsl MkCall_InFadeInit                 ; CGRAM all white, target = art pal
    jsl MkCall_InM1Regs

    ; Hide any OAM left over from the demo before the first visible frame.
    sep #$20
    .ACCU 8
    rep #$10
    .INDEX 16
    lda #0
    sta.l OAMADDL
    sta.l OAMADDL+1
    ldx #512.w
    lda #$F0.b
-   sta.l $2104
    dex
    bne -
    ldx #32.w
    lda #0
-   sta.l $2104
    dex
    bne -

    lda #$06.b                            ; FADE family: FightPresent's
    sta.w IN_FX                           ;   OpnApply flushes IN_FCUR in vblank
    rep #$20
    .ACCU 16
    stz.w TH_TICK
    sep #$20
    .ACCU 8
    lda #GS_THUNDER.b
    sta.b gamestate
    ; Leave INIDISP blanked for this frame.  The next vblank's present runs
    ; OpnApply (IN_FX=6) and SuperFxPresent, which enables the display at the
    ; top of the frame instead of mid-scanline, so the first visible frame is
    ; a clean full-screen white flash.
    lda #$81.b
    sta.l NMITIMEN
    rtl

ThunderTickFar:
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    rep #$20
    .ACCU 16
    lda.w TH_TICK
    inc a
    sta.w TH_TICK
    cmp #2.w                              ; keep the first presented frame pure
    bcc TH_out                            ;   white: the display is still off
    cmp #(TH_FAST_END+1).w
    bcs TH_hold
    sep #$20
    .ACCU 8
    jsl MkCall_InFadeStep                 ; four palette steps/frame: flash-in
    jsl MkCall_InFadeStep
    jsl MkCall_InFadeStep
    jsl MkCall_InFadeStep
    rep #$20
    .ACCU 16
    rtl
TH_hold:
    cmp #TH_FADE_START.w
    bcc TH_out
    bne TH_fade
    ldx #0                                ; retarget the palette at black
    txa
-   sta.w IN_FTGT,x
    inx
    inx
    cpx #128.w
    bne -
    lda.w TH_TICK
TH_fade:
    cmp #TH_DONE.w
    bcs TH_done
    sec
    sbc #TH_FADE_START.w
    and #$0003.w                          ; one step every four frames: slow-out
    bne TH_out
    sep #$20
    .ACCU 8
    jsl MkCall_InFadeStep
    rep #$20
    .ACCU 16
TH_out:
    rtl
TH_done:
    sep #$20
    .ACCU 8
    jsl MkCall_OpnEnter                   ; never returns: falls into MainLoop
    rtl

.ENDIF
.ENDIF
.ENDS
