; ============================================================================
; msu_intro.asm — MSU-1 full-screen opening video (gamestate 14).
;
; The M1VID1 container embedded in kof98-snes.msu holds 133 frames in the
; endings' format: 256x224, 4 bpp tiles, a 32x32 map and four 15-colour
; palette bands.  Frames are packed as
;
;     CHR (chr_len bytes) | 2048-byte map | 128-byte palette
;
; and the 8-byte table entry is { u32 offset, u16 chr_len, u16 ticks }.
;
; The player lives in ROM bank 126's free high-half tail at CPU $3E:D300.
; MsuIntroEnterFar loads the table once, then MsuIntroLoad streams the first
; frame.  MsuIntroTickFar advances IN_MTICK each vblank and loads the next
; frame when the entry's tick count expires.  The generator starts from the
; nominal 2658 ticks (44.3 s) and subtracts the measured per-frame staging
; cost, so the wall-clock sequence stays at 44.3 s even though the loads run
; under forced blank.
;
; MSU traffic is sector-aligned and double-DMA'd: $2001 -> MsuStageBuf, then
; MsuStageBuf+prefix -> $2118/$2119.  This is the same path the CHR streamer
; validated on the SD2SNES; reading the data port at an arbitrary in-sector
; offset can make its cache serve stale sectors.
; ============================================================================

.BASE $C0
.BANK 126 SLOT 0
.ORGA $D300
.SECTION "MsuIntroVideo" FORCE

; A16/X16 on entry and exit (MainLoop leaves D=ENGINE_DP, DBR=$7E).
MsuIntroEnterFar:
    rep #$20
    .ACCU 16
    sep #$20
    .ACCU 8
    lda #0
    sta.l $4200                            ; NMI off during the setup
    ; Read the frame table (133 * 8 = 1064 bytes) into WRAM once.  A direct
    ; byte copy is enough here: it runs once and avoids the shared
    ; MsuReadAlignedFar path, whose 24-bit destination bank byte aliases the
    ; scr3 chunk counter in this DP layout.
    jsr MI_LoadTable
    jsr MI_SetRegs
    rep #$20
    .ACCU 16
    stz.w IN_MFRAME
    stz.w IN_MTICK
    jsr MsuIntroLoad                       ; frame 0
    jml OpnMsuReady

; One MainLoop tick.  START skips to the title; otherwise count the current
; frame's ticks and advance when the table entry expires.
MsuIntroTickFar:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR.w                       ; pad1 edges
    and #$1000.w                           ; START only
    beq +
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l INIDISP                          ; blank before the handoff
    jml MsuTitleEnterBridge
+   inc.w IN_MTICK
    lda.w IN_MTICK
    cmp.w IN_MTICKS
    bcc MIK_done
    stz.w IN_MTICK
    inc.w IN_MFRAME
    lda.w IN_MFRAME
    cmp #MSU_VIDEO_FRAMES.w
    bcs MIK_finish
    jsr MsuIntroLoad
MIK_done:
    jsr MI_SetRegs
    sep #$20
    .ACCU 8
    lda #$81.b
    sta.l $4200                            ; NMI + autojoy back on
    rep #$20
    .ACCU 16
    jml MainLoop
MIK_finish:
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l INIDISP
    jml MsuTitleEnterBridge

; ---------------------------------------------------------------------------
; Load IN_MFRAME from the MSU into BG2.  Keeps the display blanked and NMI
; off while the PPU ports are busy; the caller restores NMI after the load.
; ---------------------------------------------------------------------------
MsuIntroLoad:
    sep #$20
    .ACCU 8
    lda #0
    sta.l NMITIMEN                         ; keep the ISR off the DMA ports
    lda #$80.b
    sta.l INIDISP                          ; forced blank
    rep #$20
    .ACCU 16
    jsr MI_GetEntry                        ; IN_MCHR/IN_MTICKS + scr0/scr2
    ; CHR -> BG2 tiles ($2000 word)
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l $2115                            ; increment after $2119
    rep #$20
    .ACCU 16
    lda #$2000.w
    sta.l $2116
    lda.w IN_MCHR
    sta.b scr3
    jsr MI_StreamVram
    ; map -> BG2 map ($1800 word)
    lda #$1800.w
    sta.l $2116
    lda #2048.w
    sta.b scr3
    jsr MI_StreamVram
    ; palette -> CGRAM 0
    sep #$20
    .ACCU 8
    lda #0
    sta.l $2121
    rep #$20
    .ACCU 16
    lda #128.w
    sta.b scr3
    jsr MI_StreamCgram
    sep #$20
    .ACCU 8
    lda #$0F.b
    sta.l INIDISP                          ; display on
    rep #$20
    .ACCU 16
    rts

; Read the current frame's table entry and compute its absolute MSU offset.
MI_GetEntry:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w IN_MFRAME
    asl a
    asl a
    asl a                                  ; frame * 8
    tax
    lda.w MsuVideoTable,x                  ; u32 offset, low word
    sta.w IN_MOFF0
    lda.w MsuVideoTable+2,x                ; high word
    sta.w IN_MOFF1
    lda.w MsuVideoTable+4,x                ; chr_len
    sta.w IN_MCHR
    lda.w MsuVideoTable+6,x                ; ticks
    sta.w IN_MTICKS
    lda #MSU_VIDEO_BASE_LO
    clc
    adc.w IN_MOFF0
    sta.b scr0
    lda #MSU_VIDEO_BASE_HI
    adc.w IN_MOFF1
    sta.b scr2
    rts

; ---------------------------------------------------------------------------
; Stream scr3 bytes from the 32-bit MSU offset in scr0/scr2 to the VRAM word
; address already written to VMADDL/H.  VMAIN must be $80 (mode-1 DMA).
;
; Each pass stages one 512-byte sector in MsuStageBuf, then DMAs the payload
; from stage+prefix to VRAM.  The source advances by the bytes actually read
; (scr6), not by the payload count (scr5): on a non-aligned start the two
; differ by the in-sector prefix.
; ---------------------------------------------------------------------------
MI_StreamVram:
    rep #$20
    .ACCU 16
MISV_loop:
    lda.b scr3
    bne MISV_body
    rts
MISV_body:
    ; prefix inside the 512-byte MSU sector
    lda.b scr0
    and #$01FF.w
    sta.b scr4
    ; bytes to fetch from the aligned sector: min(512, prefix+remaining)
    lda.b scr3
    clc
    adc.b scr4
    cmp #512.w
    bcc +
    lda #512.w
+   sta.b scr6
    ; payload bytes this pass: min(512-prefix, remaining)
    lda #512.w
    sec
    sbc.b scr4
    cmp.b scr3
    bcc +
    lda.b scr3
+   sta.b scr5
    ; sector-aligned seek
    lda.b scr0
    and #$FE00.w
    sta.b scr0
    jsr MI_Seek
    ; MSU -> MsuStageBuf (fixed source $00:2001)
    lda #(MsuStageBuf & $FFFF).w
    sta.l $2181
    lda #$8008.w
    sta.l $4350                            ; DMAP5 mode 0, BBAD5 $80
    lda #$2001.w
    sta.l $4352
    lda.b scr6
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$00.b
    sta.l $4354
    lda #$7F.b
    sta.l $2183
    lda #$20.b
    sta.l MDMAEN
    ; MsuStageBuf+prefix -> VRAM ($2118/$2119, A increment)
    rep #$20
    .ACCU 16
    lda #$1801.w
    sta.l $4350
    lda #(MsuStageBuf & $FFFF).w
    clc
    adc.b scr4
    sta.l $4352
    lda.b scr5
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.l $4354
    lda #$20.b
    sta.l MDMAEN
    ; advance the source (read bytes) and remaining (payload bytes)
    rep #$20
    .ACCU 16
    lda.b scr0
    clc
    adc.b scr6
    sta.b scr0
    lda.b scr2
    adc #0
    sta.b scr2
    lda.b scr3
    sec
    sbc.b scr5
    sta.b scr3
    jmp MISV_loop

; ---------------------------------------------------------------------------
; Stream scr3 bytes from scr0/scr2 to CGRAM, starting at the CGADD the caller
; already wrote.  The palette is only 128 bytes, but the loop handles a
; sector crossing.
; ---------------------------------------------------------------------------
MI_StreamCgram:
    rep #$20
    .ACCU 16
MISC_loop:
    lda.b scr3
    bne MISC_body
    rts
MISC_body:
    lda.b scr0
    and #$01FF.w
    sta.b scr4
    lda.b scr3
    clc
    adc.b scr4
    cmp #512.w
    bcc +
    lda #512.w
+   sta.b scr6
    lda #512.w
    sec
    sbc.b scr4
    cmp.b scr3
    bcc +
    lda.b scr3
+   sta.b scr5
    lda.b scr0
    and #$FE00.w
    sta.b scr0
    jsr MI_Seek
    ; MSU -> MsuStageBuf
    lda #(MsuStageBuf & $FFFF).w
    sta.l $2181
    lda #$8008.w
    sta.l $4350
    lda #$2001.w
    sta.l $4352
    lda.b scr6
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$00.b
    sta.l $4354
    lda #$7F.b
    sta.l $2183
    lda #$20.b
    sta.l MDMAEN
    ; advance the source before reusing scr0 as the WRAM pointer
    rep #$20
    .ACCU 16
    lda.b scr0
    clc
    adc.b scr6
    sta.b scr0
    lda.b scr2
    adc #0
    sta.b scr2
    lda.b scr3
    sec
    sbc.b scr5
    sta.b scr3
    ; CGRAM copy: pointer = MsuStageBuf + prefix
    lda #(MsuStageBuf & $FFFF).w
    clc
    adc.b scr4
    sta.b scr0
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.b scr1                            ; bank byte of the 24-bit ptr
    ldy #0
MISC_copy:
    lda [scr0],y
    sta.l $2122
    iny
    cpy.b scr5
    bcc MISC_copy
    rep #$20
    .ACCU 16
    jmp MISC_loop

; Re-assert the Mode 1/BG2-only setup.  Other front-end ticks (and the
; library NMI) may touch the PPU registers while the video is running.
MI_SetRegs:
    sep #$20
    .ACCU 8
    lda #$01.b
    sta.l $2105                            ; BGMODE 1
    lda #$18.b
    sta.l $2108                            ; BG2SC: map word $1800, 32x32
    lda #$20.b
    sta.l $210B                            ; BG12NBA: BG2 tiles word $2000
    lda #$02.b
    sta.l $212C                            ; TM = BG2 only
    lda #0
    sta.l $212D                            ; TS off
    sta.l $210F
    sta.l $210F                            ; BG2HOFS 0
    sta.l $2110
    sta.l $2110                            ; BG2VOFS 0
    rep #$20
    .ACCU 16
    rts

; Copy the M1VID1 frame table into MsuVideoTable.  A16 on entry and exit.
MI_LoadTable:
    rep #$20
    .ACCU 16
    lda #MSU_VIDEO_TABLE_LO
    sta.b scr0
    lda #MSU_VIDEO_TABLE_HI
    sta.b scr2
    jsr MI_Seek
    rep #$20
    .ACCU 16
    lda #(MsuVideoTable & $FFFF)
    sta.b scr0
    sep #$20
    .ACCU 8
    lda #$7E.b
    sta.b scr1                            ; bank byte at scr0+2
    ldy #0
-   lda.l $2001
    sta [scr0],y
    iny
    cpy #(MSU_VIDEO_FRAMES * 8)
    bcc -
    rep #$20
    .ACCU 16
    rts

; Wait for the pending MSU seek.  Bounded like the CHR streamer; if the
; board never answers the DMA simply transfers stale bytes rather than
; hanging the intro.
MI_Seek:
    rep #$30
    .ACCU 16
    .INDEX 16
    sep #$20
    .ACCU 8
    lda.b scr0
    sta.l $2000
    lda.b scr0+1
    sta.l $2001
    lda.b scr2
    sta.l $2002
    lda.b scr2+1
    sta.l $2003
    ldx #MSU_POLL_LIMIT.w
-   lda.l $2000
    bpl +
    dex
    bne -
+   rep #$20
    .ACCU 16
    rts

.ENDS
