; Incremental MSU voice loader. Kept outside the full Fight bank.
.BASE $C0
.BANK 126 SLOT 0
.ORGA $C300
.SECTION "VoiceQueueCode" FORCE

VoiceQueueAddFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w VQ_TAIL
    sta scr6
    clc
    adc #4.w
    and #$003F.w
    cmp.w VQ_HEAD
    beq VQAF_full
    ldy scr6
    lda scr4
    sta.w VQ_DATA,y
    lda scr5
    sta.w VQ_DATA+2,y
    tya
    clc
    adc #4.w
    and #$003F.w
    sta.w VQ_TAIL
    sec
    rtl
VQAF_full:
    clc
    rtl

VoiceQueueTickFar:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.l $00015A                       ; snesmod digi_active: a direct/streamed
    and #$00FF.w                        ;   voice is still on the wire.  Starting
    beq +                               ;   a second stream corrupts the SPC.
    jmp VQTF_ret
+   lda.w VQ_BUSY
    cmp #2.w
    bne VQTF_not_ready
    lda.l $7E46F8
    beq VQTF_go_play
    jmp VQTF_ret
VQTF_go_play:
    jmp VQTF_play
VQTF_not_ready:
    cmp #1.w
    bne VQTF_dequeue
    jmp VQTF_chunk
VQTF_dequeue:
    lda.w VQ_HEAD
    cmp.w VQ_TAIL
    bne +
    jmp VQTF_ret
+
    tay
    lda.w VQ_DATA,y
    sta.w VQ_PTRIDX
    lda.w VQ_DATA+2,y
    sta.w VQ_INDEX
    tya
    clc
    adc #4.w
    and #$003F.w
    sta.w VQ_HEAD
    ldx.w VQ_PTRIDX
    lda.l VoicePtrTab+5,x
    sta lptr
    sep #$20
    .ACCU 8
    lda.l VoicePtrTab+7,x
    sta lptr+2
    rep #$20
    .ACCU 16
    lda.w VQ_INDEX
    asl a
    asl a
    tay
    lda [lptr],y
    sta.w VQ_MSUOFS
    iny
    iny
    lda [lptr],y
    sta.w VQ_MSUOFS+2
    ldx.w VQ_PTRIDX
    lda.l VoicePtrTab+2,x
    sta lptr
    sep #$20
    .ACCU 8
    lda.l VoicePtrTab+4,x
    sta lptr+2
    rep #$20
    .ACCU 16
    lda.w VQ_INDEX
    asl a
    asl a
    asl a
    tay
    ldx #0
VQTF_meta:
    sep #$20
    .ACCU 8
    lda [lptr],y
    sta.w VQ_TABLE,x
    rep #$20
    .ACCU 16
    iny
    inx
    cpx #5.w
    bne VQTF_meta
    lda.w VQ_TABLE+3
    sta scr6
    asl a
    asl a
    asl a
    clc
    adc scr6
    sta.w VQ_TOTAL
    lda.w VQ_TOTAL
    bne +
    jmp VQTF_ret                       ; empty sample: never underflow VQ_COUNT
+   cmp #VQ_CACHE1.w                    ; a corrupt/out-of-range voice record
    bcc +                               ;   must not overrun the 6 KiB cache
    jmp VQTF_ret
+   stz.w VQ_POS
    lda.w VQ_SLOT
    eor #1.w
    and #1.w
    sta.w VQ_SLOT
    lda #1.w
    sta.w VQ_BUSY
VQTF_chunk:
    lda.w VQ_MSUOFS
    clc
    adc.w VQ_POS
    sta scr0
    lda.w VQ_MSUOFS+2
    adc #0.w
    sta scr2
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
    ldx #MSU_POLL_LIMIT.w
-   lda.l MSU_STAT
    bpl +
    dex
    bne -
    rep #$20
    .ACCU 16
    inc.w RT_MSUFAIL
    rtl
+   rep #$20
    .ACCU 16
    lda.w VQ_TOTAL
    sec
    sbc.w VQ_POS
    cmp #VOICE_CHUNK.w
    bcc +
    lda #VOICE_CHUNK.w
+   sta.w VQ_COUNT
    lda.w VQ_POS
    ldx.w VQ_SLOT
    beq +
    clc
    adc #VQ_CACHE1.w
+   tax
    ldy.w VQ_COUNT
    sep #$20
    .ACCU 8
VQTF_copy:
    lda.l MSU_DATA
    sta.l $7F0000,x
    inx
    dey
    bne VQTF_copy
    rep #$20
    .ACCU 16
    lda.w VQ_POS
    clc
    adc.w VQ_COUNT
    sta.w VQ_POS
    cmp.w VQ_TOTAL
    bcs +
    jmp VQTF_ret
+   lda #2.w
    sta.w VQ_BUSY
    lda.l $7E46F8
    beq VQTF_play
    jmp VQTF_ret
VQTF_play:
    lda.w VQ_SLOT
    beq +
    lda #VQ_CACHE1.w
    bra ++
+  lda #VQ_CACHE0.w
++ sta.w VQ_TABLE+5
    sep #$20
    .ACCU 8
    lda #$7F.b
    sta.w VQ_TABLE+7
    rep #$20
    .ACCU 16
    lda #VQ_TABLE.w
    sta.l $7E0050
    sep #$20
    .ACCU 8
    lda #$7E.b
    sta.l $7E0052
    rep #$20
    .ACCU 16
    phd
    pea 0
    pea 15
    lda #0
    tcd
    jsl spcPlaySoundV
    rep #$20
    .ACCU 16
    pla
    pla
    pld
    stz.w VQ_BUSY
VQTF_ret:
    rep #$20
    .ACCU 16
    rtl

; Drop the shared ring but leave an in-flight sample alone.  StartFight uses
; this: when the next stage song loads, SpcFlushSafe pumps the current sample
; to completion before spcLoad rewrites SPC RAM, so the bout's last quote
; ends during the setup instead of starting later as a queued voice.
VoiceQueueDropFar:
    phb
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    rep #$30
    .ACCU 16
    .INDEX 16
    stz.w VQ_HEAD
    stz.w VQ_TAIL
    stz.w VQ_BUSY
    stz.w VQ_POS
    stz.w VQ_COUNT
    stz.w VQ_TOTAL
    sep #$20
    .ACCU 8
    plb
    rtl

; Clear the queue and abort an in-flight stream without touching the module.
; Use before a screen that loads its own song: the following spcLoad (CMD_LOAD)
; key offs every voice, and skipping the abort would make SpcFlushSafe wait
; for the old sample to finish.  Never queue spcPlay here -- its asynchronous
; echo can race that direct load handshake (see StageMusic).
VoiceQueueClearFar:
    phb                                 ; these .w refs are WRAM: do not trust
    sep #$20                            ;   the caller's DBR (campaign paths
    .ACCU 8                             ;   can arrive with DBR=$00)
    lda #ENGINE_DB.b
    pha
    plb
    rep #$30
    .ACCU 16
    .INDEX 16
    stz.w VQ_HEAD
    stz.w VQ_TAIL
    stz.w VQ_BUSY
    stz.w VQ_POS
    stz.w VQ_COUNT
    stz.w VQ_TOTAL
    lda.l $00015A                       ; digi_active
    and #$00FF.w
    beq VQC_out16
    sep #$20
    .ACCU 8
    lda #0
    sta.l $000158                       ; digi_remain
    sta.l $00015A                       ; digi_active
    plb
    rtl
VQC_out16:
    sep #$20
    .ACCU 8
    plb
    rtl

; Full reset for screens that keep the current module (YOU LOSE, mid-fight
; join): like VoiceQueueClearFar plus a module restart.  spcPlay's CMD_PLAY
; begins with Module_Stop (key-off all voices); without it the stream channel
; would keep reading its abandoned buffer.  The ticker runs in every gamestate
; and the ring lives in shared WRAM, so a quote queued during a bout would
; otherwise start on the select/title screen or in the next fight.
VoiceQueueResetFar:
    phb
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    rep #$30
    .ACCU 16
    .INDEX 16
    stz.w VQ_HEAD
    stz.w VQ_TAIL
    stz.w VQ_BUSY
    stz.w VQ_POS
    stz.w VQ_COUNT
    stz.w VQ_TOTAL
    lda.l $00015A
    and #$00FF.w
    beq VQR_out16
    sep #$20
    .ACCU 8
    lda #0
    sta.l $000158
    sta.l $00015A
    lda.w MUSON                         ; no module ever started: nothing to
    and #$00FF.w                        ;   key off/restart
    beq VQR_out8
    phd
    lda #0
    tcd
    pea 0                               ; CMD_PLAY starts with Module_Stop:
    jsl spcPlay                         ;   key off every voice, then restart
    rep #$20                            ;   the loaded module from the top
    .ACCU 16
    pla
    pld
    sep #$20
    .ACCU 8
VQR_out8:
    plb
    rtl
VQR_out16:
    sep #$20
    .ACCU 8
    plb
    rtl

StageMusicFar:
    sep #$20
    .ACCU 8
    lda.w MUSIC_VALID
    beq SMF_changed
    lda.w MUSIC_STAGE
    cmp.b stageidx
    bne SMF_changed
    jmp SMF_out
SMF_changed:
    lda audiordy
    bne SMF_apu_idle
    jmp SMF_out
SMF_apu_idle:
    lda #0
    sta.l NMITIMEN
    lda.l $4210
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #$2000
-   dex
    bne -
    phd
    lda #0
    tcd
    jsl SpcFlushSafe
    sep #$20
    .ACCU 8
    lda.l $7E0000+ENGINE_DP+stageidx     ; absolute: D=0 here, and stageidx is
    rep #$20                            ;   a DP offset (reading $0087 loaded
    .ACCU 16                            ;   the wrong module, sometimes CRYSTAL)
    and #$00FF.w
    tax
    lda.l StageModTab,x
    and #$00FF.w
    pha
    jsl spcLoad
    rep #$20
    .ACCU 16
    pla
    jsl SpcFlushSafe
    lda #8.w                            ; 5 combat effects + 3 menu blips
    sta.l $7E46F8                       ;   (see FightFxSrc in fight.asm)
    sep #$20                            ; byte var: STA is 8-bit here; STZ
    .ACCU 8                             ;   always writes a 16-bit zero
    lda #0
    sta.w UI_SFXLOAD
    pea 0
    jsl spcPlay
    rep #$20
    .ACCU 16
    pla
    pea 150.w
    jsl spcSetModuleVolume
    rep #$20
    .ACCU 16
    pla
    pld
    sep #$20
    .ACCU 8
    lda.b stageidx
    sta.w MUSIC_STAGE
    lda #1
    sta.w MUSIC_VALID
    sta.w MUSON
    lda #$81.b
    sta.l NMITIMEN
SMF_out:
    sep #$20
    .ACCU 8
    rtl

VoicePlayFar:
    php                                ; preserve the caller's M/X flags
    rep #$10                           ; PHX/PLX must always be 16-bit
    sep #$20
    .ACCU 8
    .INDEX 16
    sta.l $7E7F20                      ; save the local voice index outside
    pha                                ;   the stack: PHX width depends on the
    phx                                ;   caller's index flag, so a fixed
    lda audiordy                       ;   stack offset is unsafe
    bne +
    rep #$10
    plx
    pla
    plp
    rtl
+   ldx fofs
    phd
    rep #$20
    .ACCU 16
    lda FP+F_CHAR,x
    sta scr5
    ldx #0
VPF_scan:
    lda.l VoicePtrTab,x
    beq VPF_out
    cmp scr5
    beq VPF_got
    txa
    clc
    adc #8.w
    tax
    bra VPF_scan
VPF_got:
    stx scr4
    lda.l VoicePtrTab+5,x
    beq VPF_rom
    lda msuok
    and #$00FF.w
    beq VPF_out
    lda.l $7E7F20                      ; saved local voice index
    and #$00FF.w
    sta scr5
    jsl VoiceQueueAddFar
    bra VPF_out
VPF_rom:
    lda.l $00015A                       ; a direct ROM voice must not cut into
    and #$00FF.w                        ;   an active streamed voice
    beq +
    jmp VPF_out
+   lda.w VQ_BUSY
    bne VPF_out
    lda.w VQ_HEAD
    cmp.w VQ_TAIL
    bne VPF_out                        ; queued voice has priority
    lda.l $7E7F20                      ; same saved index (ROM voice path)
    and #$00FF.w
    sta scr5
    ldx scr4
    lda.l VoicePtrTab+2,x
    sta.l $7E0050
    sep #$20
    .ACCU 8
    lda.l VoicePtrTab+4,x
    sta.l $7E0052
    rep #$20
    .ACCU 16
    lda scr5
    pha
    lda #15.w
    pha
    lda #0
    tcd
    jsl spcPlaySoundV
    rep #$20
    .ACCU 16
    pla
    pla
VPF_out:
    pld
    sep #$20
    .ACCU 8
    rep #$10
    plx
    pla
    plp
    rtl

.ENDS

