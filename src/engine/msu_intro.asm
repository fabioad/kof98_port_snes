; ============================================================================
; msu_intro.asm — MSU-1 full-screen opening video (gamestate 14).
;
; The M1VID1 container embedded in kof98-snes.msu holds 665 frames in the
; endings' format: 256x224, 4 bpp tiles, a 32x32 map and four 15-colour
; palette bands.  Frames are packed as
;
;     CHR (chr_len bytes) | 2048-byte map | 128-byte palette
;
; and the 8-byte table entry is { u32 offset, u16 chr_len, u16 ticks }.
;
; The player lives in ROM bank 126's free high-half tail at CPU $3E:D300.
; MsuIntroEnterFar loads the table and frame 0 once.  From then on the video
; is double-buffered: while frame N is on screen, the visible tick stages
; frame N+1 into the hidden tile/map buffer in 4864-byte chunks; the NMI hook
; (IntroNmiHandler) then performs the WRAM->VRAM DMA at the top of vblank.
; A chunk may straddle the CHR->map boundary; the consume splits it into a
; tile DMA and a map DMA instead of wasting a tick on the boundary.  When the
; frame's ticks expire, the swap (DMA palette + BG2 base) happens inside
; vblank, so the screen never goes blank between frames.  The table uses a ~15 fps
; cadence (665 frames), totalling 2658 ticks = 44.3 s at 60 Hz.
; MsuIntroTickFar only counts ticks and handles START/finish.
;
; MSU traffic is sector-aligned and double-DMA'd: $2001 -> MsuStageBuf, then
; MsuStageBuf+prefix -> $2118/$2119.  This is the same path the CHR streamer
; validated on the SD2SNES; reading the data port at an arbitrary in-sector
; offset can make its cache serve stale sectors.
; ============================================================================

; Double-buffer state.  DBR is $7E in every caller, so these are ordinary
; 16-bit WRAM addresses.  $7E8600-$7E87FF is free in the hybrid RAM map.
.DEFINE MV_ACTIVE   $8600                 ; .w 0 = A ($2000/$1800), 1 = B
.DEFINE MV_NEXT     $8602                 ; .w frame being streamed
.DEFINE MV_CHRLEFT  $8604                 ; .w bytes left in the CHR segment
.DEFINE MV_SRC0     $8606                 ; .w source low word
.DEFINE MV_SRC1     $8608                 ; .w source high word
.DEFINE MV_TOTAL    $860C                 ; .w bytes left in CHR+map
.DEFINE MV_CHR      $860E                 ; .w CHR length of the new frame
.DEFINE MV_TICKS    $8610                 ; .w display ticks of the new frame
.DEFINE MV_READY    $8612                 ; .w 1 = CHR/map/palette buffered
.DEFINE MV_PAL0     $8614                 ; .w palette source low word
.DEFINE MV_PAL1     $8616                 ; .w palette source high word
.DEFINE MV_CHRBASE  $8618                 ; .w hidden tile base word
.DEFINE MV_MAPBASE  $861A                 ; .w hidden map base word
.DEFINE MV_BGSC     $861C                 ; .w hidden BG2SC value
.DEFINE MV_NBA      $861E                 ; .w hidden BG12NBA value
.DEFINE MV_FINISH   $8620                 ; .w last frame elapsed
.DEFINE MV_LEN      $8622                 ; .w current chunk length
.DEFINE MV_VRAM     $8624                 ; .w current VRAM word address
.DEFINE MV_STAGED   $8626                 ; .w 1 = chunk ready in MsuVideoStage
.DEFINE MV_SPREFIX  $8628                 ; .w in-sector prefix of the staged chunk
.DEFINE MV_SLEN     $862A                 ; .w payload length of the staged chunk
.DEFINE MV_CHRPART  $862C                 ; .w CHR bytes inside the staged chunk
.DEFINE MV_LOCK     $862E                 ; .w 1 = visible tick is staging
.DEFINE NMI_SAVE    $7E8630               ; 6-byte NMI scratch stash
.DEFINE MV_PALBUF   $8700                 ; 128-byte palette buffer
.DEFINE MV_CHUNK    4864                 ; bytes staged during active display
.DEFINE MSU_VIDEO_POLL 65535             ; cold-start seek budget for the video

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
    ; Read the frame table (665 * 8 = 5320 bytes) into WRAM once.  A direct
    ; byte copy is enough here: it runs once and avoids the shared
    ; MsuReadAlignedFar path, whose 24-bit destination bank byte aliases the
    ; scr3 chunk counter in this DP layout.
    jsr MI_LoadTable
    jsr MI_SetRegs
    jsr MI_ResetVideo                      ; wipe the check screen's palette/maps
    rep #$20
    .ACCU 16
    stz.w IN_MFRAME
    stz.w IN_MTICK
    jsr MsuIntroLoad                       ; frame 0 -> buffer A
    rep #$20
    .ACCU 16
    stz.w MV_ACTIVE                        ; A is on screen
    stz.w MV_FINISH
    stz.w MV_STAGED                        ; no chunk is pending yet
    stz.w MV_LOCK
    lda #1.w
    jsr MI_BeginStream                     ; stream frame 1 into buffer B
    jml OpnMsuReady

; One MainLoop tick.  The vblank hook (MsuVideoVblank) performs the buffer
; swap and streams the next frame; this routine only counts ticks, honours
; START and handles the final hand-off.
MsuIntroTickFar:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR.w                       ; either pad's edges
    ora FP+F_JOYPR+FP2OFS.w
    and #$1000.w                           ; START only
    beq +
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l INIDISP                          ; blank before the handoff
    jml MsuTitleEnterBridge
+   lda.w MV_FINISH
    bne MIK_finish
    inc.w IN_MTICK
MIK_done:
    jsr MV_StageChunk                       ; stage the next chunk while visible
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
    ; Stay blanked.  The first gs14 vblank (FightPresentDispatch) enables
    ; the display after the check screen/PPU state has fully settled.
    rep #$20
    .ACCU 16
    rts

; Clear CGRAM and both BG2 map buffers while the display is blanked.  The
; MSU check screen leaves gray/white BG3 palettes and maps around; wiping
; them here guarantees no stale colours/tiles can peek through the first
; video frames.
MI_ResetVideo:
    sep #$20
    .ACCU 8
    rep #$10
    .INDEX 16
    lda #0
    sta.l $2121                            ; CGRAM 0
    ldx #0
-   sta.l $2122
    inx
    cpx #512.w                             ; all 256 colors
    bne -
    rep #$20
    .ACCU 16
    lda #$80.b
    sta.l $2115
    lda #$1800.w
    sta.l $2116
    lda #0
    ldx #1024.w
-   sta.l $2118
    dex
    bne -
    lda #$1C00.w
    sta.l $2116
    lda #0
    ldx #1024.w
-   sta.l $2118
    dex
    bne -
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
    ; CGRAM copy: pointer = MsuStageBuf + prefix.  Use lptr (not scr0) so
    ; scr0 keeps the advanced source word for a palette that crosses a
    ; 512-byte sector and needs a second pass.
    lda #(MsuStageBuf & $FFFF).w
    clc
    adc.b scr4
    sta.b lptr
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.b lptr+2                          ; bank byte of the 24-bit ptr
    ldy #0
MISC_copy:
    lda [lptr],y
    sta.l $2122
    iny
    cpy.b scr5
    bcc MISC_copy
    rep #$20
    .ACCU 16
    jmp MISC_loop

; ---------------------------------------------------------------------------
; Prepare the hidden buffer for frame A.  Reads its table entry, computes the
; CHR/map/palette addresses and selects the buffer that is not on screen.
; A16 = frame index, returns A16.
; ---------------------------------------------------------------------------
MI_BeginStream:
    rep #$30
    .ACCU 16
    .INDEX 16
    sta.w MV_NEXT
    asl a
    asl a
    asl a                                  ; frame * 8
    tax
    lda.w MsuVideoTable,x                  ; offset low word
    sta.b scr0
    lda.w MsuVideoTable+2,x                ; offset high word
    sta.b scr2
    lda #MSU_VIDEO_BASE_LO
    clc
    adc.b scr0
    sta.w MV_SRC0
    lda #MSU_VIDEO_BASE_HI
    adc.b scr2
    sta.w MV_SRC1
    lda.w MsuVideoTable+4,x                ; chr_len
    sta.w MV_CHR
    lda.w MsuVideoTable+6,x                ; ticks
    sta.w MV_TICKS
    lda.w MV_CHR
    sta.w MV_CHRLEFT
    clc
    adc #2048.w
    sta.w MV_TOTAL
    ; palette source = frame base + chr_len + 2048
    lda.w MV_SRC0
    clc
    adc.w MV_CHR
    sta.b scr0
    lda.w MV_SRC1
    adc #0
    sta.b scr2
    lda.b scr0
    clc
    adc #2048.w
    sta.w MV_PAL0
    lda.b scr2
    adc #0
    sta.w MV_PAL1
    stz.w MV_READY
    ; target the buffer that is not active
    lda.w MV_ACTIVE
    bne MIB_targetA
    lda #$5000.w
    sta.w MV_CHRBASE
    lda #$1C00.w
    sta.w MV_MAPBASE
    lda #$1C.w
    sta.w MV_BGSC
    lda #$50.w
    sta.w MV_NBA
    bra MIB_target_done
MIB_targetA:
    lda #$2000.w
    sta.w MV_CHRBASE
    lda #$1800.w
    sta.w MV_MAPBASE
    lda #$18.w
    sta.w MV_BGSC
    lda #$20.w
    sta.w MV_NBA
MIB_target_done:
    lda.w MV_CHRBASE
    sta.w MV_VRAM
    rts

; ---------------------------------------------------------------------------
; Read the 128-byte palette at MV_PAL0/1 into MV_PALBUF and mark the stream
; ready.  Runs inside a vblank; 128 CPU reads are cheap.
; ---------------------------------------------------------------------------
MI_ReadPalette:
    rep #$30
    .ACCU 16
    .INDEX 16
    ; Read prefix+128 bytes from the aligned sector into MsuStageBuf, then
    ; copy the 128-byte payload.  Direct reads at a non-zero in-sector offset
    ; can make the SD2SNES cache serve stale sectors.
    lda.w MV_PAL0
    and #$01FF.w
    sta.w MSU_PREFIX
    lda.w MV_PAL0
    and #$FE00.w
    sta.b scr0
    lda.w MV_PAL1
    sta.b scr2
    jsr MI_Seek
    lda.w MSU_PREFIX
    clc
    adc #128.w
    sta.w MV_LEN
    lda #(MsuStageBuf & $FFFF).w
    sta.l $2181
    lda #$8008.w
    sta.l $4350
    lda #$2001.w
    sta.l $4352
    lda.w MV_LEN
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$00.b
    sta.l $4354
    lda #$7F.b
    sta.l $2183
    lda #$20.b
    sta.l MDMAEN
    ; copy the palette out of stage+prefix
    rep #$20
    .ACCU 16
    lda #(MsuStageBuf & $FFFF).w
    clc
    adc.w MSU_PREFIX
    sta.b scr0
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.b scr1
    ldy #0
-   lda [scr0],y
    sta.w MV_PALBUF,y
    iny
    cpy #128.w
    bcc -
    rep #$20
    .ACCU 16
    lda #1.w
    sta.w MV_READY
    rts

; ---------------------------------------------------------------------------
; Swap the hidden buffer on screen: copy its palette to CGRAM, program the
; new BG2 base, advance IN_MFRAME and start streaming the following frame.
; Called from the vblank hook, so none of this is visible.
; ---------------------------------------------------------------------------
MI_SwapBuffers:
    sep #$20
    .ACCU 8
    lda #0
    sta.l $2121                            ; CGRAM 0
    ; 128-byte palette via GPDMA ch6.  The CPU loop this replaces spent
    ; most of the vblank window on CGRAM writes and pushed the swap into
    ; the visible area, blacking out the top scanlines.
    rep #$20
    .ACCU 16
    lda #$2200.w                        ; mode 0, BBAD6 $22 (CGDATA)
    sta.l $4360
    lda #(MV_PALBUF & $FFFF).w
    sta.l $4362
    sep #$20
    .ACCU 8
    lda #$7E.b
    sta.l $4364
    lda #128.b
    sta.l $4365
    stz $4366
    lda #$40.b                            ; channel 6
    sta.l MDMAEN
    lda.w MV_BGSC
    sta.l $2108                            ; BG2SC
    lda.w MV_NBA
    sta.l $210B                            ; BG12NBA
    lda #$01.b
    sta.l $2105                            ; BGMODE 1
    lda #$02.b
    sta.l $212C                            ; TM = BG2
    rep #$20
    .ACCU 16
    lda.w MV_NEXT
    sta.w IN_MFRAME
    lda.w MV_TICKS
    sta.w IN_MTICKS
    stz.w IN_MTICK
    lda.w MV_ACTIVE
    eor #1.w
    sta.w MV_ACTIVE
    lda.w IN_MFRAME
    inc a
    cmp #MSU_VIDEO_FRAMES.w
    bcs MISB_no_next
    jsr MI_BeginStream
    bra MISB_done
MISB_no_next:
    stz.w MV_READY
    stz.w MV_TOTAL
MISB_done:
    rts

; ---------------------------------------------------------------------------
; Vblank hook for gamestate 14, called at the top of vblank by
; FightPresentDispatch.  It re-asserts the PPU mode, performs a due buffer
; swap, and streams at most MV_CHUNK bytes into the hidden VRAM buffer.
; ---------------------------------------------------------------------------
MsuVideoVblank:
    ; Keep BG2 on the active buffer even if the library ISR touched the PPU.
    sep #$20
    .ACCU 8
    lda #$01.b
    sta.l $2105                            ; BGMODE 1
    lda #$02.b
    sta.l $212C                            ; TM = BG2 only
    lda #0
    sta.l $212D                            ; TS off
    sta.l $210F
    sta.l $210F                            ; BG2HOFS 0
    sta.l $2110
    sta.l $2110                            ; BG2VOFS 0
    lda.w MV_ACTIVE
    bne MVV_activeB
    lda #$18.b
    sta.l $2108
    lda #$20.b
    sta.l $210B
    bra MVV_regs_done
MVV_activeB:
    lda #$1C.b
    sta.l $2108
    lda #$50.b
    sta.l $210B
MVV_regs_done:
    rep #$20
    .ACCU 16
    ; Consume one pre-staged chunk (WRAM -> VRAM only; the MSU read ran
    ; during the visible part of the previous frame).
    lda.w MV_STAGED
    beq MVV_check_swap
    jsr MV_ConsumeChunk
MVV_check_swap:
    ; A swap is due when the tick counter has reached the frame's ticks.
    lda.w IN_MTICK
    cmp.w IN_MTICKS
    bcc MVV_out
    lda.w IN_MFRAME
    cmp #(MSU_VIDEO_FRAMES - 1).w
    bcs MVV_finish
    lda.w MV_READY
    beq MVV_out
    jsr MI_SwapBuffers
    bra MVV_out
MVV_finish:
    lda #1.w
    sta.w MV_FINISH
MVV_out:
    rep #$20
    .ACCU 16
    rtl

; ---------------------------------------------------------------------------
; Copy the staged chunk from MsuVideoStage to VRAM.  Called from the vblank
; hook, so the forced blank around the DMA is invisible.
; ---------------------------------------------------------------------------
MV_ConsumeChunk:
    rep #$20
    .ACCU 16
    sep #$20
    .ACCU 8
    lda #$8F.b
    sta.l INIDISP                          ; blank during the VRAM DMAs
    lda #$80.b
    sta.l $2115                            ; increment after $2119
    rep #$20
    .ACCU 16
    lda #$1801.w
    sta.l $4350                            ; mode 1, BBAD5 $2118
    sep #$20
    .ACCU 8
    lda #$7E.b
    sta.l $4354
    rep #$20
    .ACCU 16
    ; A chunk may cross the CHR -> map boundary.  Split the VRAM DMA
    ; into a CHR part and a map part; the staged bytes are contiguous.
    lda.w MV_SLEN
    cmp.w MV_CHRLEFT
    bcc +
    lda.w MV_CHRLEFT
+   sta.w MV_CHRPART
    beq MVC_map
    ; CHR part -> tile page
    lda.w MV_VRAM
    sta.l $2116
    lda #(MsuVideoStage & $FFFF).w
    clc
    adc.w MV_SPREFIX
    sta.l $4352
    lda.w MV_CHRPART
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$20.b
    sta.l MDMAEN
    rep #$20
    .ACCU 16
    lda.w MV_CHRPART
    lsr a
    clc
    adc.w MV_VRAM
    sta.w MV_VRAM
    lda.w MV_SRC0
    clc
    adc.w MV_CHRPART
    sta.w MV_SRC0
    lda.w MV_SRC1
    adc #0
    sta.w MV_SRC1
    lda.w MV_CHRLEFT
    sec
    sbc.w MV_CHRPART
    sta.w MV_CHRLEFT
    lda.w MV_TOTAL
    sec
    sbc.w MV_CHRPART
    sta.w MV_TOTAL
    lda.w MV_CHRLEFT
    bne MVC_finish
    lda.w MV_MAPBASE                       ; CHR done: next bytes are the map
    sta.w MV_VRAM
MVC_map:
    ; map part -> map page
    lda.w MV_SLEN
    sec
    sbc.w MV_CHRPART
    beq MVC_finish
    sta.w MV_LEN
    lda.w MV_VRAM
    sta.l $2116
    lda #(MsuVideoStage & $FFFF).w
    clc
    adc.w MV_SPREFIX
    clc
    adc.w MV_CHRPART
    sta.l $4352
    lda.w MV_LEN
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$20.b
    sta.l MDMAEN
    rep #$20
    .ACCU 16
    lda.w MV_LEN
    lsr a
    clc
    adc.w MV_VRAM
    sta.w MV_VRAM
    lda.w MV_SRC0
    clc
    adc.w MV_LEN
    sta.w MV_SRC0
    lda.w MV_SRC1
    adc #0
    sta.w MV_SRC1
    lda.w MV_TOTAL
    sec
    sbc.w MV_LEN
    sta.w MV_TOTAL
MVC_finish:
    stz.w MV_STAGED
    rep #$20
    .ACCU 16
    rts

; ---------------------------------------------------------------------------
; Stage one chunk from the MSU into MsuVideoStage.  Called from the tick,
; i.e. during the visible part of the frame, so the MSU read/DMA never eats
; into vblank.  When the last map chunk is staged, the palette is read into
; MV_PALBUF in the same pass, ready for the vblank swap.
; ---------------------------------------------------------------------------
MV_StageChunk:
    rep #$20
    .ACCU 16
    lda.w MV_STAGED
    bne MVS_out
    lda.w MV_READY
    bne MVS_out
    lda.w MV_TOTAL
    beq MVS_out
    lda #1.w
    sta.w MV_LOCK                          ; the NMI hook must not touch MV_*
    lda.w MV_TOTAL
    cmp #MV_CHUNK.w
    bcc +
    lda #MV_CHUNK.w
+   sta.w MV_SLEN
    ; sector-aligned seek
    lda.w MV_SRC0
    and #$01FF.w
    sta.w MV_SPREFIX
    lda.w MV_SRC0
    and #$FE00.w
    sta.b scr0
    lda.w MV_SRC1
    sta.b scr2
    jsr MI_Seek
    ; MSU -> MsuVideoStage (channel 4, fixed source $00:2001)
    lda #(MsuVideoStage & $FFFF).w
    sta.l $2181
    lda #$8008.w
    sta.l $4340
    lda #$2001.w
    sta.l $4342
    lda.w MV_SPREFIX
    clc
    adc.w MV_SLEN
    sta.l $4345
    sep #$20
    .ACCU 8
    lda #$00.b
    sta.l $4344
    lda #$7E.b
    sta.l $2183
    lda #$10.b                            ; channel 4
    sta.l MDMAEN
    rep #$20
    .ACCU 16
    lda #1.w
    sta.w MV_STAGED
    ; If this chunk completes the CHR+map payload, read the palette now.
    lda.w MV_SLEN
    cmp.w MV_TOTAL
    bne MVS_out
    jsr MI_ReadPalette
MVS_out:
    stz.w MV_LOCK
    rep #$20
    .ACCU 16
    rts

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

; Copy the M1VID1 frame table into MsuVideoTable.  The table starts at
; video_off+24, i.e. at a non-zero in-sector offset; direct reads there can
; make the SD2SNES cache serve the wrong sector and corrupt the first frame
; entries.  Read from the aligned sector into MsuStageBuf, then copy the
; requested window.
MI_LoadTable:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda #MSU_VIDEO_TABLE_LO
    and #$01FF.w
    sta.w MSU_PREFIX
    lda #MSU_VIDEO_TABLE_LO
    and #$FE00.w
    sta.b scr0
    lda #MSU_VIDEO_TABLE_HI
    sta.b scr2
    jsr MI_Seek
    lda.w MSU_PREFIX
    clc
    adc #(MSU_VIDEO_FRAMES * 8).w
    sta.w MV_LEN
    lda #(MsuStageBuf & $FFFF).w
    sta.l $2181
    lda #$8008.w
    sta.l $4350
    lda #$2001.w
    sta.l $4352
    lda.w MV_LEN
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$00.b
    sta.l $4354
    lda #$7F.b
    sta.l $2183
    lda #$20.b
    sta.l MDMAEN
    rep #$20
    .ACCU 16
    lda #(MsuStageBuf & $FFFF).w
    clc
    adc.w MSU_PREFIX
    sta.b scr0
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.b scr1                            ; bank byte at scr0+2
    ldy #0
-   lda [scr0],y
    sta.w MsuVideoTable,y
    iny
    cpy #(MSU_VIDEO_FRAMES * 8).w
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
    ldx #MSU_VIDEO_POLL.w
-   lda.l $2000
    bpl +
    dex
    bne -
+   rep #$20
    .ACCU 16
    rts


; ---------------------------------------------------------------------------
; PVSnesLib NMI hook.  The library ISR transfers OAM and then jumps here
; before scanning the pads.  Running the video consume/swap at this point
; gives the VRAM DMA the full vblank window; doing it after WaitForVBlank
; left only part of vblank and blanked the top scanlines on some frames.
; Non-video states fall through to the library's consoleVblank unchanged.
; ---------------------------------------------------------------------------
IntroNmiHandler:
    rep #$30
    .ACCU 16
    .INDEX 16
    pha
    phx
    phy
    phd
    phb
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    rep #$20
    .ACCU 16
    lda #ENGINE_DP.w
    tcd
    sep #$20
    .ACCU 8
    lda gamestate
    cmp #GS_INTRO_MSU.b
    beq IntroNmi_video
    rep #$30
    .ACCU 16
    plb
    pld
    ply
    plx
    pla
    jml consoleVblank
IntroNmi_video:
    ldx #$05.w                            ; preserve scr0..scr2 for the tick
-   lda $10.b,x
    sta.l NMI_SAVE,x
    dex
    bpl -
    lda.w MV_LOCK                         ; visible tick is mid-update: skip
    bne IntroNmi_restore
    rep #$20
    .ACCU 16
    jsl MsuVideoVblank
    sep #$20
    .ACCU 8
    lda #$0F.b
    sta.l INIDISP
IntroNmi_restore:
    ldx #$05.w
-   lda.l NMI_SAVE,x
    sta $10.b,x
    dex
    bpl -
    rep #$30
    .ACCU 16
    plb
    pld
    ply
    plx
    pla
    rtl

.ENDS
