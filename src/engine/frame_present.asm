; Vblank scheduling. Leave time for register/palette restoration before line 0.
; All entries run with DBR=$7E and D=ENGINE_DP. No MSU seek or poll is done here.
.BASE $00
.BANK 64 SLOT 0
.ORGA $4000
.SECTION "FramePresentBudget" FORCE
; A16 = bytes to transfer. C=1 if the current NTSC vblank has room.
; 160 bytes/scanline is below DMA's 170-byte theoretical rate. Three extra
; lines cover setup/counter reads; stop at line 260 to leave the final PPU
; palette/register writes before the visible picture. X/Y and DP scratch
; remain untouched, so a declined sprite retains its complete pending pose.
VblankRoom:
    rep #$20
    .ACCU 16
    pha
    sep #$20
    .ACCU 8
    lda.l $213F                         ; reset counter-read phase (SPC polls it)
    lda.l $2137                         ; timestamp before the budget calculation
    lda.l $213D
    sta.w RT_PRESENT_SCAN
    lda.l $213D
    and #1.b
    sta.w RT_PRESENT_SCAN+1
    rep #$20
    .ACCU 16
    pla
    stz.w RT_PRESENT_LINES
VR_lines:
    inc.w RT_PRESENT_LINES
    sec
    sbc #160.w
    bcs VR_lines
    lda.w RT_PRESENT_LINES
    clc
    adc #3.w
    sta.w RT_PRESENT_LINES
    lda.w RT_PRESENT_SCAN
    cmp #225.w
    bcc VR_no
    clc
    adc.w RT_PRESENT_LINES
    cmp #260.w
    bcs VR_no
    sec
    rts
VR_no:
    clc
    rts

PresentFightersFar:
    sep #$20
    .ACCU 8
    lda.w PZ_ON
    ora.w CL_OPEN
    ora.w RT_HUDFULL
    bne PF_done                         ; frozen actors; prioritize overlay DMA
    lda framecnt
    and #1.b
    bne PF_p2
    jsr PF_one
    jsr PF_two
PF_done:
    rtl
PF_p2:
    jsr PF_two
    jsr PF_one
    rtl
PF_one:
    ldx #0.w
    lda #<P1CHR
    sta scr5
    lda #>P1CHR
    sta scr5+1
    jsl PresentSpriteFar
    rts
PF_two:
    ldx #FP2OFS.w
    lda #<P2CHR
    sta scr5
    lda #>P2CHR
    sta scr5+1
    jsl PresentSpriteFar
    rts

; Sprite CHR presentation: the budget check and the kind/owner tests live
; in SprDmaFar (bank 126) so an FX-page vblank can be accounted for there.
PresentSpriteFar:
    jml SprDmaFar

HudRoomFar:
    sep #$20
    .ACCU 8
    lda gamestate
    cmp #1.b
    bne HR_full
    lda.w RT_HUDFULL
    ora.w CL_OPEN
    ora.w PZ_ON
    bne HR_full
    lda FP+F_DMAREQ
    ora FP+F_DMAREQ+FP2OFS
    bne HR_band
    lda huddirty
    and #HUD_FULL.b
    bne HR_full
HR_band:
    rep #$20
    .ACCU 16
    lda #256.w
    bra HR_room
HR_full:
    rep #$20
    .ACCU 16
    lda #2048.w
HR_room:
    jsr VblankRoom
    sep #$20
    .ACCU 8
    rtl

StageAnimPresentFar:
    rep #$20
    .ACCU 16
    lda #2560.w                         ; CPU patches include per-cell setup
    jsr VblankRoom
    bcc SAP_done
    jml StageAnimTickFar
SAP_done:
    rtl
.ENDS
