.INCLUDE "hdr.asm"

.DEFINE PVSNESLIB 1

; Keep the engine's direct-page scratch away from 816-tcc's imaginary
; registers and PVSnesLib's own low-RAM allocations.
.RAMSECTION ".fight_dp" BANK 0 SLOT 1 ORGA $1000 FORCE
FightDirectPage dsb $E9
.ENDS

; The original engine used the bank-$00 WRAM mirror.  In the hybrid build the
; fighter state, OAM shadow and HUD tilemap live in an explicitly reserved
; area of bank $7E.
.RAMSECTION ".fight_ram" BANK $7E SLOT 2 ORGA $4000 FORCE
FightRam dsb $0F00
.ENDS

; intro/title/menu/select state + scratch (see engine/menucore.asm).
.RAMSECTION ".menu_vars" BANK $7E SLOT 2 ORGA $F000 FORCE
MenuVarsRam dsb $180
.ENDS

; SURVIVOR opponent order + carried HP live in the menu-vars window above.
; PRACTICE command-list state follows them in the same free page.
.RAMSECTION ".fight_cmdlist" BANK $7E SLOT 2 ORGA $4F40 FORCE
FightCommandListRam dsb $80
.ENDS

; P1/P2 combo counters; must not alias campaign/team vars at $10C0+.
.RAMSECTION ".fight_combo" BANK $7E SLOT 2 ORGA $4FC0 FORCE
FightComboRam dsb $82
.ENDS

; Bounded MSU voice queue/cache metadata and runtime telemetry.
.RAMSECTION ".fight_streaming" BANK $7E SLOT 2 ORGA $5100 FORCE
FightStreamingRam dsb $0700
.ENDS
; Per-side AI jump-in state.  Sits in the free gap between the combo
; counters and the streaming queue, away from the C stack/stream buffer.
.RAMSECTION ".fight_ai" BANK $7E SLOT 2 ORGA $5042 FORCE
FightAiRam dsb $10
.ENDS
; FUSION juggle/dizzy/MAX/carry state.  The engine addresses it at $5052;
; keep the reservation adjacent so the free 0xAE-byte gap is not reused.
.RAMSECTION ".fight_fusion" BANK $7E SLOT 2 ORGA $5052 FORCE
FightFusionRam dsb $80
.ENDS
.RAMSECTION ".oam_cache" BANK $7E SLOT 2 ORGA $3800 FORCE
OamCacheRam dsb $0800
.ENDS
.RAMSECTION ".fight_stream_cache" BANK $7F SLOT 3 ORGA $0000 FORCE
FightStreamingCache dsb $3000
.ENDS
; MSU CHR staging buffer: one 512-byte sector prefix + one 1280-byte chunk.
; The seek is always aligned to a 512-byte file sector; the prefix is read
; into this buffer and skipped by the VRAM DMA source address.
.RAMSECTION ".msu_stage" BANK $7F SLOT 3 ORGA $5000 FORCE
MsuStageBuf dsb $0800
.ENDS

; Arguments for the sector-aligned MSU reader used by the voice streamer.
; Kept in the free top of WRAM next to the select scratch bytes ($7F10/$7F20
; are already used by the select screen and the voice fallback).
.RAMSECTION ".msu_read" BANK $7E SLOT 2 ORGA $7F30 FORCE
MsuReadVars dsb $10
.ENDS
.DEFINE MRD_SRC $7E7F30                 ; 32-bit .msu file offset
.DEFINE MRD_DST $7E7F34                 ; 24-bit destination
.DEFINE MRD_LEN $7E7F37                 ; bytes still to read
.DEFINE MRD_POS $7E7F39                 ; bytes already copied

.INCLUDE "engine/fight.asm"
.INCLUDE "engine/voice_queue.asm"       ; incremental MSU voice loader
.INCLUDE "engine/menus.asm"
.INCLUDE "engine/options.asm"
.IFDEF MSU_DIAG
.IFDEF MSU_DIAG2
.RAMSECTION ".msu_diag_buffers" BANK $7F SLOT 3 ORGA $3000 FORCE
.IFDEF MSU_DIAG3
MsuDiagBuffers dsb $1900
.ELSE
MsuDiagBuffers dsb $1800
.ENDIF
.ENDS
.ENDIF
.INCLUDE "engine/msu_diag.asm"
.ENDIF

; MSU CHR staging, kept out of the full 32 KiB Fight bank.  The caller has
; already written VMADDL with the hidden-page destination and staged the
; 512-byte-aligned seek.  A16/X16 on entry and exit.
.BASE $C0
.BANK 126 SLOT 0
.ORGA $CF00
.SECTION "MsuStageCode" FORCE
MsuStageUploadFar:
    rep #$20
    .ACCU 16
    ; Both DMAs below write through the PPU ports ($2181 WMDATA and
    ; $2118/$2119 VRAM).  On the SD2SNES those transfers are not reliable
    ; while the display is rendering, so blank around them.  The caller has
    ; already waited for the SD sector with the screen on.
    sep #$20
    .ACCU 8
    lda #$8F.b
    sta.l INIDISP
    rep #$20
    .ACCU 16
    ; 1) MSU -> WRAM: sector prefix + payload from the fixed data port.
    lda #(MsuStageBuf & $FFFF).w
    sta.l $2181
    lda #$8008.w                        ; mode 0, fixed A source -> WMDATA
    sta.l $4350
    lda #$2001.w
    sta.l $4352
    lda.w MSU_PREFIX
    clc
    adc scr3
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.l $2183
    lda #$00.b
    sta.l $4354
    lda #$20.b
    sta.l MDMAEN
    ; 2) WRAM -> VRAM: skip the prefix, write only the requested payload.
    lda #$80.b
    sta.l VMAIN
    rep #$20
    .ACCU 16
    lda #$1801.w                        ; mode 1: alternate $2118/$2119
    sta.l $4350
    lda #(MsuStageBuf & $FFFF).w
    clc
    adc.w MSU_PREFIX
    sta.l $4352
    lda scr3
    sta.l $4355
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.l $4354
    lda #$20.b
    sta.l MDMAEN
    ; Restore the display after the VRAM write.
    lda #$0F.b
    sta.l INIDISP
    rep #$20
    .ACCU 16
    rtl
.ENDS

; Sector-aligned MSU reader for streamed voices.  The CHR path was already
; aligned to 512 bytes because the SD2SNES data cache is refilled per sector;
; the voice streamer still read 512-byte chunks from arbitrary offsets, so a
; chunk could start at a non-zero in-sector pointer (or cross a cache page)
; and stall the console inside the byte-copy loop.  Keep every MSU read on a
; sector boundary and copy only the payload out of the staging buffer.
;
; In:  MRD_SRC = 32-bit .msu offset
;      MRD_DST = 24-bit destination
;      MRD_LEN = number of bytes
; Out: C=1 when everything was copied, C=0 after an MSU timeout (nothing is
;      advanced by the caller, so it can retry on the next frame).
; A16/X16 on exit.
.BANK 126 SLOT 0
.ORGA $CF80
.SECTION "MsuAlignedRead" FORCE
MsuReadAlignedFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    sep #$20
    .ACCU 8
    lda #0
    sta.l MRD_POS
    sta.l MRD_POS+1
    rep #$20
    .ACCU 16
MRA_loop:
    lda.l MRD_POS
    cmp.l MRD_LEN
    bcc MRA_more
    jmp MRA_done
MRA_more:
    ; count = min(512, remaining)
    lda.l MRD_LEN
    sec
    sbc.l MRD_POS
    cmp #VOICE_CHUNK.w
    bcc +
    lda #VOICE_CHUNK.w
+   sta scr3
    ; 32-bit source offset for this chunk
    lda.l MRD_SRC
    clc
    adc.l MRD_POS
    sta scr0
    lda.l MRD_SRC+2
    adc #0.w
    sta scr2
    ; align the seek down to a 512-byte sector
    lda scr0
    and #$01FF.w
    sta.w MSU_PREFIX
    lda scr0
    and #$FE00.w
    sta scr0
    sep #$20
    .ACCU 8
    lda scr0
    sta.l MSU_STAT
    lda scr0+1
    sta.l MSU_DATA
    lda scr2
    sta.l $2002
    lda scr2+1
    sta.l $2003
    ldx #MSU_POLL_LIMIT.w               ; bounded: caller retries next frame
MRA_poll:
    lda.l MSU_STAT
    bpl MRA_ready
    dex
    bne MRA_poll
    rep #$30
    .ACCU 16
    .INDEX 16
    clc
    rtl
MRA_ready:
    ; MSU -> WRAM through the CPU data port.  Do not use a second MSU DMA
    ; here: the CHR uploader owns the DMA/cache path, and interleaving two
    ; MSU DMA consumers left the SD2SNES cache serving stale CHR sectors on
    ; some cards (MSU fighters showed garbled tiles again).  A voice chunk
    ; is only 512 bytes, so the CPU copy is cheap enough.
    rep #$20
    .ACCU 16
    lda #(MsuStageBuf & $FFFF).w
    sta scr0
    lda.w MSU_PREFIX
    clc
    adc scr3
    sta scr5                            ; prefix + payload bytes
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta scr0+2
    ldy #0
MRA_copy_in:
    lda.l MSU_DATA
    sta [scr0],y
    iny
    cpy scr5
    bcc MRA_copy_in
    ; copy only the requested payload, skipping the sector prefix
    rep #$20
    .ACCU 16
    lda #(MsuStageBuf & $FFFF).w
    clc
    adc.w MSU_PREFIX
    sta scr0
    lda.l MRD_DST
    clc
    adc.l MRD_POS
    sta scr2
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta scr0+2
    lda.l MRD_DST+2
    sta scr2+2
    rep #$20
    .ACCU 16
    ldy #0
MRA_copy:
    lda [scr0],y
    sta [scr2],y
    iny
    cpy scr3
    bcc MRA_copy
    lda.l MRD_POS
    clc
    adc scr3
    sta.l MRD_POS
    jmp MRA_loop
MRA_done:
    rep #$30
    .ACCU 16
    .INDEX 16
    sec
    rtl
.ENDS
