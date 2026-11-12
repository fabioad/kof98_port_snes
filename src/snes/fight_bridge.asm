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

; Private state for TEAM PLAY order selection; no campaign/input aliasing.
.RAMSECTION ".team_order_vars" BANK $7E SLOT 2 ORGA $F180 FORCE
TeamOrderVars dsb $40
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
.IFDEF KOF_TINY
; Runtime roster table for the TINY profile: CharSelTabRom/BankSelTabRom are
; copied here at boot and the ten dual-scale entries are swapped to their
; 0.90 MSU descriptors when msuok=1.  Sits in the free gap after the streaming
; block (ends at $57FF) and before VOICE_BUF at $6000.
.RAMSECTION ".tiny_sel" BANK $7E SLOT 2 ORGA $5800 FORCE
TinySelRam dsb $00C8
.ENDS
.ENDIF
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
; Opening-video staging buffer: one 512-byte sector prefix + one 4864-byte chunk.
; The seek is always aligned to a 512-byte file sector; the prefix is read
; into this buffer and skipped by the VRAM DMA source address.
.RAMSECTION ".msu_stage" BANK $7F SLOT 3 ORGA $5000 FORCE
MsuStageBuf dsb $0800
.ENDS
; Second staging buffer: both fighters can have their next CHR chunk
; prefetched during the logic phase, so the vblank only copies WRAM -> VRAM.
.RAMSECTION ".msu_stage2" BANK $7F SLOT 3 ORGA $5800 FORCE
MsuStageBuf2 dsb $0800
.ENDS
.BASE $00
.RAMSECTION ".fillbar_memo" BANK $7F SLOT 3 ORGA $6000 FORCE
FBM_CACHE dsb $0080
.ENDS
.IFDEF KOF_PERF_VERIFY
.RAMSECTION ".perf_verify" BANK $7F SLOT 3 ORGA $6100 FORCE
PV_SIGNATURE dsb 4
PV_DRAW_CALLS dsb 4
PV_DRAW_MISMATCHES dsb 4
PV_HP_CALLS dsb 4
PV_HP_MISMATCHES dsb 4
PV_POW_CALLS dsb 4
PV_POW_MISMATCHES dsb 4
PV_FB_CALLS dsb 4
PV_FB_MISMATCHES dsb 4
PV_FIRST_VALID dsb 1
PV_FIRST_TYPE dsb 1
PV_FIRST_OFFSET dsb 2
PV_FIRST_EXPECTED dsb 2
PV_FIRST_ACTUAL dsb 2
PV_FIRST_CONTEXT dsb 32
PV_TMP_OFFSET dsb 2
PV_TMP_EXPECTED dsb 2
PV_TMP_ACTUAL dsb 2
PV_DRAW_IN_A dsb 2
PV_DRAW_IN_X dsb 2
PV_DRAW_IN_Y dsb 2
PV_DRAW_SCR0 dsb 2
PV_DRAW_SCR1 dsb 2
PV_DRAW_SCR2 dsb 2
PV_DRAW_SCR3 dsb 2
PV_DRAW_SCR4 dsb 2
PV_DRAW_SCR5 dsb 2
PV_DRAW_SCR6 dsb 2
PV_DRAW_PBASE dsb 2
PV_DRAW_AOFS dsb 1
PV_DRAW_LPTR dsb 3
PV_DRAW_PRE_TOP dsb 2
PV_DRAW_PRE_DROP dsb 2
PV_DRAW_OLD_TOP dsb 2
PV_DRAW_OLD_DROP dsb 2
PV_DRAW_OLD_SCR0 dsb 2
PV_DRAW_OLD_SCR1 dsb 2
PV_DRAW_OLD_SCR2 dsb 2
PV_HP_INPUT dsb 2
PV_HP_FAST_A dsb 2
PV_HP_FAST_X dsb 2
PV_HP_OLD_A dsb 2
PV_HP_OLD_X dsb 2
PV_POW_INPUT dsb 2
PV_POW_FAST_A dsb 2
PV_POW_FAST_X dsb 2
PV_POW_OLD_A dsb 2
PV_POW_OLD_X dsb 2
PV_DRAW_PRE_OAM dsb 544
PV_DRAW_OLD_OAM dsb 544
PV_FIRST_OLD_OAM dsb 544
PV_FIRST_NEW_OAM dsb 544
PV_DBG dsb 16
PV_NMISAVE dsb 128
.ENDS
.ENDIF
.BASE $C0

; Arguments for the sector-aligned MSU reader used by the voice streamer.
; Kept in the free top of WRAM next to the select scratch bytes ($7F10/$7F20
; are already used by the select screen and the voice fallback).
.RAMSECTION ".msu_read" BANK $7E SLOT 2 ORGA $7F30 FORCE
MsuReadVars dsb $10
.ENDS

; Opening-video frame table: 665 entries x 8 bytes.  Loading it once keeps the
; per-frame path to a single payload seek instead of a table seek plus a
; payload seek.  $7E8000-$7ECFFF is free in the hybrid RAM map; park the
; table at $B000, above the enlarged staging buffer.
.RAMSECTION ".msu_video_table" BANK $7E SLOT 2 ORGA $B000 FORCE
MsuVideoTable dsb 5320
.ENDS
.RAMSECTION ".msu_video_state" BANK $7E SLOT 2 ORGA $8600 FORCE
MsuVideoState dsb $0100
.ENDS
.RAMSECTION ".msu_video_pal" BANK $7E SLOT 2 ORGA $8700 FORCE
MsuVideoPal dsb $0080
.ENDS
.RAMSECTION ".msu_video_stage" BANK $7E SLOT 2 ORGA $8800 FORCE
MsuVideoStage dsb $1900
.ENDS
.DEFINE MRD_SRC $7E7F30                 ; 32-bit .msu file offset
.DEFINE MRD_DST $7E7F34                 ; 24-bit destination
.DEFINE MRD_LEN $7E7F37                 ; bytes still to read
.DEFINE MRD_POS $7E7F39                 ; bytes already copied

.INCLUDE "engine/fight.asm"
.IF MSU_VIDEO_FRAMES > 0
.INCLUDE "engine/msu_intro.asm"         ; bank-126 opening-video player
.ENDIF
.INCLUDE "engine/select_far.asm"        ; bank-126 P2 takeover helpers
.INCLUDE "engine/voice_queue.asm"       ; incremental MSU voice loader
.INCLUDE "engine/menus.asm"
.INCLUDE "engine/options.asm"
.INCLUDE "engine/team_order.asm"
.INCLUDE "engine/frame_present.asm"
.INCLUDE "engine/fast_paths.asm"
.INCLUDE "engine/msu_seek.asm"
.INCLUDE "engine/close_normals.asm"
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

; Boot MSU-check strings.  Moving these 31 bytes out of the Fight section
; leaves room for the gamestate-14 branch; MtStr walks them through a 24-bit
; pointer, so the bank byte is all that changes.  $DE00 was needed for the
; widened VoiceQueueCode block ($DA60-$DEFF), so they sit in the $EEA0 gap
; before ProjPinFar.
.BASE $C0
.BANK 126 SLOT 0
.ORGA $EEA0
.SECTION "MsuCheckStrings" FORCE
MsuCheckText: .db 24,3,8,5,3,11,9,14,7,0,13,19,21,42,28,0,19,21,16,16,15,18,20,38,0
MsuAvailable: .db 3,25,5,19
MsuUnavailable: .db 2,14,15
.ENDS

; MSU CHR staging, kept out of the full 32 KiB Fight bank.  The caller has
; already written VMADDL with the hidden-page destination and staged the
; 512-byte-aligned seek.  A16/X16 on entry and exit.
.BASE $C0
.BANK 126 SLOT 0
.ORGA $CF00
.SECTION "MsuStageCode" FORCE
; MsuStageDmaFar: vblank half.  Copies the positioned MSU sector into the
; side's WRAM staging buffer.  Must run under forced blank (FightPresent
; sets INIDISP=$8F before SprDmaFar).  Preserves Y.
MsuStageDmaFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    phy
    lda scr1
    sta.l $2181
    lda #$8008.w
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
    rep #$30
    .ACCU 16
    .INDEX 16
    ply
    jsl MsuSeekConsumedFar
    rtl

.ENDS

; ---------------------------------------------------------------------------
; Sprite CHR upload, far half.  Kept out of the full Fight bank.
; MsuStagePrepareFar positions/polls the shared MSU port during logic.
; The actual MSU -> WRAM -> VRAM transfers stay in forced-blank vblank.
;   In:  scr0 = sector-aligned .msu offset low word
;        scr4 = .msu offset high word
;        MSU_PREFIX = in-sector prefix
;        scr3 = requested payload bytes
;        scr1 = staging buffer word address (bank $7F)
;   Out: C=1 and scr3 = clamped payload bytes when ready; C=0 while waiting.
; Fixed window between YouLoseCode ($CA6D) and SelMoveCode ($CC00); the
; Fight bank is full, so the upload helpers live in the bank-126 hole.
.BANK 126 SLOT 0
.ORGA $CA6D
.SECTION "SprUploadFar" FORCE
MsuStagePrepareFar:
    jml MsuSeekPrepareFar

; SprDmaFar: vblank half.  X = fighter offset, scr5 = base page VRAM word.
; Copies the chunk staged by SprPrepOne into the hidden ping-pong page.
SprDmaFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    stx fofs
    txa
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    tay                                 ; state offset (0/2)
    sep #$20
    .ACCU 8
    lda FP+F_DMAREQ,x
    bne SDF_req
    lda #0.b
    sta.w SP_KIND,y
    jmp SDF_ret
SDF_req:
    lda.w SP_KIND,y
    bne SDF_go
    jmp SDF_ret                         ; not staged yet: keep the old page
SDF_go:
    cmp #4.b                            ; 1 = ROM, 2 = MSU staged, 3 = commit
    bcc SDF_kind_ok
    lda #0.b                            ; stale/garbage staging state
    sta.w SP_KIND,y
    jmp SDF_ret
SDF_kind_ok:
    cmp #2.b                            ; staged MSU chunk: only the side
    bne +                               ;   that positioned the seek may
    cpy.w SP_MSUOWN                     ;   consume it
    beq +
    jmp SDF_ret
+
    cmp #3.b
    bne +
    jmp SDF_commit
+   rep #$20
    .ACCU 16
    lda.w SP_COUNT,y
    bne +
    jmp SDF_commit                      ; 0 count = 64 KiB: never DMA it
+   ; MSU source: stage the positioned sector into WRAM under forced
+    ; blank.  The direct MSU->WRAM DMA is not reliable with the PPU on.
    lda.w SP_KIND,y
    and #$00FF.w
    cmp #2.w
    bne +
    lda #(MsuStageBuf & $FFFF).w
    cpy #0.w
    beq ++
    lda #(MsuStageBuf2 & $FFFF).w
++  sta scr1
    lda.w SP_COUNT,y
    sta scr3
    lda.w SP_PREFIX,y
    sta.w MSU_PREFIX
    jsl MsuStageDmaFar
+   sep #$20
    .ACCU 8
    lda.w SP_KIND,y
    sta scr6                            ; 1 = ROM, 2 = MSU staging buffer
    ; pos = F_DMAPOS*32
    rep #$20
    .ACCU 16
    lda FP+F_DMAPOS,x
    and #$00FF.w
    asl a
    asl a
    asl a
    asl a
    asl a
    sta scr2
    ; VMADDL = hidden page base + pos/2
    lda.w SP_DST,y
    sta scr3
    lda scr2
    lsr a
    clc
    adc scr3
    sta.l VMADDL
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l VMAIN
    lda #$01.b
    sta.l $4360
    lda #$18.b
    sta.l $4361
    rep #$20
    .ACCU 16
    lda scr6
    and #$00FF.w
    cmp #2.w
    beq SDF_msu
    lda.w SP_SRC,y
    sta.l $4362
    sep #$20
    .ACCU 8
    lda.w SP_SRCBANK,y
    sta.l $4364
    bra SDF_count
SDF_msu:
    lda #(MsuStageBuf & $FFFF).w
    cpy #0.w
    beq +
    lda #(MsuStageBuf2 & $FFFF).w
+   clc
    adc.w SP_PREFIX,y
    sta.l $4362
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.l $4364
SDF_count:
    rep #$20
    .ACCU 16
    lda.w SP_COUNT,y
    sta.l $4365
    sep #$20
    .ACCU 8
    lda #$40.b
    sta.l MDMAEN                        ; channel 6: setup at $4360
    ; advance the cursor; finish (flip/commit) when the whole sprite is sent
    rep #$20
    .ACCU 16
    lda scr2
    clc
    adc.w SP_COUNT,y
    sta scr0
    ldx fofs
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    sep #$20
    .ACCU 8
    sta FP+F_DMAPOS,x
    rep #$20
    .ACCU 16
    lda scr0
    cmp.w SP_LEN,y
    bcs SDF_commit
    sep #$20
    .ACCU 8
    lda #0.b
    sta.w SP_KIND,y                     ; ask the next logic phase for chunk 2
    bra SDF_ret
SDF_commit:
    sep #$20
    .ACCU 8
    lda.w SP_KIND,y
    cmp #2.b
    bne SDF_flip
    rep #$20
    .ACCU 16
    tya
    eor #2.w
    sta.w MS_SEEK_NEXT                  ; finish a pose before serving the other
    sep #$20
    .ACCU 8
SDF_flip:
    lda FP+F_TILEPG,x
    eor #$60.b
    sta FP+F_TILEPG,x                   ; newly-uploaded page becomes visible
    stz FP+F_DMAREQ,x
    lda FP+F_QFR,x                      ; ThrowBind follows what the screen
    sta FP+F_SHOWN,x                    ;   shows, not the ticking F_FRAME
    lda FP+F_PXOFF,x
    sta FP+F_XOFF,x
    lda FP+F_PYOFF,x
    sta FP+F_YOFF,x
    lda FP+F_PFLAGS,x
    sta FP+F_FLAGS,x
    lda #0.b
    sta.w SP_KIND,y
    rep #$20
    .ACCU 16
    lda.w SP_META,y
    sta FP+F_META,x
    lda FP+F_PATKBOX,x
    sta FP+F_ATKBOX,x
    lda FP+F_PHURTBOX,x
    sta FP+F_HURTBOX,x
SDF_ret:
    sep #$20                            ; callers continue in 8-bit A
    .ACCU 8
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
    rep #$20
    .ACCU 16
    stz.w MS_PORT_VALID                  ; voice reads reposition the shared port
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
    ; prefix + payload must stay inside one 8 KiB MSU cache page here too:
    ; a voice chunk that starts in the final sector of a page crossed the
    ; boundary and could leave the CPU spinning on MSU_DATA.  The loop below
    ; advances MRD_POS by the clamped count, so the rest is read next.
    jsl MsuChrPageClamp
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
    ; Keep the port on the CPU data path: interleaving MSU DMA consumers
    ; leaves the SD2SNES cache serving stale CHR sectors on some cards.
    sep #$20
    .ACCU 8
    ldx.w MSU_PREFIX
    beq MRA_payload
MRA_skip_prefix:
    lda.l MSU_DATA
    dex
    bne MRA_skip_prefix
MRA_payload:
    rep #$20
    .ACCU 16
    lda.l MRD_DST
    clc
    adc.l MRD_POS
    sta scr0
    sep #$20
    .ACCU 8
    lda.l MRD_DST+2
    sta scr0+2
    ldy #0
MRA_copy_payload:
    lda.l MSU_DATA
    sta [scr0],y
    iny
    cpy scr3
    bcc MRA_copy_payload
    rep #$20
    .ACCU 16
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

; Clamp a staged MSU read so prefix + payload stays inside one 8 KiB
; data-cache page.  The seek itself is already aligned down to a 512-byte
; sector, but prefix + payload can still straddle the page end; on the
; SD2SNES that can leave the MSU data port (and the CPU/DMA waiting on it)
; stalled while the audio keeps playing.  The failure is deterministic for
; chunks that sit at the end of a page: Ralf's idle tile chunk was the
; known CHR case, and several streamed voice samples (Ralf 34/36, Daimon
; 0/4/11/18) have the same layout.  Both MsuStageUploadFar and
; MsuReadAlignedFar call this routine; each advances its cursor by the
; clamped scr3, so the next read resumes on the next page.
; In: scr0 = sector-aligned seek address, MSU_PREFIX = in-sector offset,
;     scr3 = requested payload bytes.  Out: scr3 possibly shortened.
; A16 on entry and exit; direct page is the engine's.
.BASE $C0
.BANK 126 SLOT 0
.ORGA $E600                          ; free window after SelectHelpers
.SECTION "MsuChrPageClamp" FORCE
MsuChrPageClamp:
    rep #$20
    .ACCU 16
    lda scr0
    and #$1FFF.w
    eor #$1FFF.w
    inc a                               ; bytes left in this 8 KiB page
    sec
    sbc.w MSU_PREFIX
    bcc +
    cmp scr3
    bcs +
    sta scr3
+   rtl
.ENDS
