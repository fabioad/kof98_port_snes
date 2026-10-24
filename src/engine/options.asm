.BASE $00
.BANK 64 SLOT 0
.ORGA $0000
.SECTION "OptionsCode" FORCE
OptionsEnter:
    rep #$10
    .INDEX 16
    sep #$20
    .ACCU 8
    lda #0
    jsl OptCall_MnLoadArt                       ; title art + menu font/OBJ
    jsl OptCall_MtClear
    stz.w OPT_ITEM
    stz.w OPT_SONG
    lda DIFFICULTY
    cmp #1
    bcs +
    lda #4
    sta.w DIFFICULTY
+   cmp #9
    bcc +
    lda #8
    sta.w DIFFICULTY
+   lda.w Q_LANG
    cmp #4
    bcc +
    stz.w Q_LANG
+   jsl ApplyDifficulty
    jsr OptionsDraw
    jsl OptCall_ConsumePadEdges
    lda #GS_OPTIONS.b
    sta.b gamestate
    rtl

; Draw the OPTIONS screen.  Uses the same OAM/menu-font path as MenuDraw.
OptionsDraw:
    php
    rep #$10
    .INDEX 16
    sep #$20
    .ACCU 8
    lda #0
    sta.l $4200                         ; NMI off while drawing
    jsl OptCall_MtClear
    ; title
    lda #107
    sta.b scr0
    lda #16
    sta.b scr1
    lda #$32
    sta.b scr4
    rep #$20
    .ACCU 16
    lda #OptTitle.w
    ldy #:OptTitle
    jsr OptDrawString
    .ACCU 8                             ; OptDrawString returns A=8
    ; LEVEL label
    lda #40
    sta.b scr0
    lda #56
    sta.b scr1
    lda #0
    jsr OptSetAttr
    rep #$20
    .ACCU 16
    lda #OptLevel.w
    ldy #:OptLevel
    jsr OptDrawString
    .ACCU 8
    ; level digit
    lda #136
    sta.b scr0
    lda #56
    sta.b scr1
    lda #27
    clc
    adc.w DIFFICULTY
    sta.b scr3
    lda #0
    jsr OptSetAttr
    jsl OptCall_MtCell
    ; LANGUAGE label
    lda #40
    sta.b scr0
    lda #80
    sta.b scr1
    lda #1
    jsr OptSetAttr
    rep #$20
    .ACCU 16
    lda #OptLanguage.w
    ldy #:OptLanguage
    jsr OptDrawString
    .ACCU 8
    ; language value
    lda #136
    sta.b scr0
    lda #80
    sta.b scr1
    lda #1
    jsr OptSetAttr
    rep #$20
    .ACCU 16
    lda.w Q_LANG
    and #$00FF.w
    asl a
    tax
    lda.l OptLangPtrTab,x
    ldy #:OptEnglish
    jsr OptDrawString
    .ACCU 8
    ; SOUND TEST label
    lda #40
    sta.b scr0
    lda #104
    sta.b scr1
    lda #2
    jsr OptSetAttr
    rep #$20
    .ACCU 16
    lda #OptSound.w
    ldy #:OptSound
    jsr OptDrawString
    .ACCU 8
    ; song value
    lda #136
    sta.b scr0
    lda #104
    sta.b scr1
    lda #2
    jsr OptSetAttr
    rep #$20
    .ACCU 16
    lda.w OPT_SONG
    and #$00FF.w
    asl a
    tax
    lda.l OptSongPtrTab,x
    ldy #:OptS0
    jsr OptDrawString
    .ACCU 8
    ; EXIT label
    lda #40
    sta.b scr0
    lda #128
    sta.b scr1
    lda #3
    jsr OptSetAttr
    rep #$20
    .ACCU 16
    lda #OptExit.w
    ldy #:OptExit
    jsr OptDrawString
    .ACCU 8
    ; cursor brackets.  Keep the row Y as an immediate ladder: the old
    ; `lda.l OptRows,x` produced y=0 in the linked ROM, so both brackets
    ; were drawn at the top edge instead of on the selected row.
    lda.w OPT_ITEM
    and #$03
    cmp #0
    bne OC_cursor_row1
    lda #56
    bra OC_cursor_y
OC_cursor_row1:
    cmp #1
    bne OC_cursor_row2
    lda #80
    bra OC_cursor_y
OC_cursor_row2:
    cmp #2
    bne OC_cursor_row3
    lda #104
    bra OC_cursor_y
OC_cursor_row3:
    lda #128
OC_cursor_y:
    sta.b scr1
    lda #24
    sta.b scr0
    lda #CUR_TILE.b
    sta.b scr3
    lda #$32
    sta.b scr4
    jsl OptCall_MtCell
    sep #$20
    .ACCU 8
    lda #216
    sta.b scr0
    lda #(CUR_TILE+1).b
    sta.b scr3
    rep #$20
    .ACCU 16
    jsl OptCall_MtCell
    sep #$20
    .ACCU 8
    lda #$81.b
    sta.l $4200
    plp
    rts

; A16 = string low address, Y = bank; scr0/1/4 set by caller. Returns A=8.
OptDrawString:
    rep #$20
    .ACCU 16
    sta.b scr2
    sep #$20
    .ACCU 8
    tya
    sta.b scr2+2
    jsl OptCall_MtStrDense
    rts

; A = new OPT_ITEM.  Entering SOUND TEST starts the first track; leaving
; it restores the title's cipher-beta theme.
OptSetItem:
    pha                                 ; music loading reuses DP scratch
    lda.w OPT_ITEM
    cmp #2
    bne OPS_not_on_sound
    lda 1,s
    cmp #2
    beq OPS_store
    lda #SONG_CIPHERB.b
    jsl OptCall_MusPlaySong
    bra OPS_store
OPS_not_on_sound:
    lda 1,s
    cmp #2
    bne OPS_store
    stz.w OPT_SONG
    stz.w MUSIC_VALID
    lda #0
    jsl OptCall_MusPlaySong                     ; first sound-test track = CIPHER
OPS_store:
    sep #$20
    .ACCU 8
    pla
    sta.w OPT_ITEM
    rts

OptAdjustLeft:
    sep #$20
    .ACCU 8
    lda #$FF
    sta.b scr3
    bra OptAdjust
OptAdjustRight:
    sep #$20
    .ACCU 8
    lda #1
    sta.b scr3
OptAdjust:
    lda.w OPT_ITEM
    cmp #0
    beq OAD_level
    cmp #1
    beq OAD_lang
    cmp #2
    beq OAD_song
    rts
OAD_level:
    lda.w DIFFICULTY
    clc
    adc.b scr3
    cmp #1
    bcs +
    lda #8
+   cmp #9
    bcc +
    lda #1
+   sta.w DIFFICULTY
    jsl ApplyDifficulty
    rts
OAD_lang:
    lda.w Q_LANG
    clc
    adc.b scr3
    cmp #4
    bcc +
    cmp #4
    beq ++
    lda #3
    bra +
++  lda #0
+   sta.w Q_LANG
    rts
OAD_song:
    lda.w OPT_SONG
    clc
    adc.b scr3
    cmp #17
    bcc +
    cmp #17
    beq ++
    lda #16
    bra +
++  lda #0
+   sta.w OPT_SONG
    stz.w MUSIC_VALID
    lda.w OPT_SONG
    jsl OptCall_MusPlaySong
    rts

OptionsExit:
    sep #$20
    .ACCU 8
    lda #SONG_CIPHERB.b                 ; restore the mode-menu theme
    jsl OptCall_MusPlaySong
    lda #1
    jsl OptCall_MnLoadArt                       ; modes art
    lda #6
    sta.w M_ITEM                        ; cursor back on OPTIONS
    jsl MenuDraw
    jsl OptCall_ConsumePadEdges
    lda #SFX_BACK.b
    jsl OptCall_SfxPlay
    lda #GS_MENU.b
    sta.b gamestate
    rtl

OptionsTick:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda FP+F_JOYPR.w
    sta.b scr0
    and #JOY_UP.w
    beq OT_noup
    sep #$20
    .ACCU 8
    lda.w OPT_ITEM
    dec a
    bpl +
    lda #3
+   jsr OptSetItem
    jmp OT_redraw
OT_noup:
    rep #$20
    .ACCU 16
    lda.b scr0
    and #JOY_DN.w
    beq OT_nodir
    sep #$20
    .ACCU 8
    lda.w OPT_ITEM
    inc a
    cmp #4
    bcc +
    lda #0
+   jsr OptSetItem
    jmp OT_redraw
OT_nodir:
    rep #$20
    .ACCU 16
    lda.b scr0
    and #JOY_LF.w
    beq OT_noleft
    jsr OptAdjustLeft
    jmp OT_redraw
OT_noleft:
    rep #$20
    .ACCU 16
    lda.b scr0
    and #JOY_RT.w
    beq OT_nolr
    jsr OptAdjustRight
    jmp OT_redraw
OT_nolr:
    rep #$20
    .ACCU 16
    lda.b scr0
    and #(JOY_ST|JOY_A).w
    beq OT_tryb
    sep #$20
    .ACCU 8
    lda.w OPT_ITEM
    cmp #3
    bne +
    jmp OptionsExit
+
    cmp #2
    beq OT_firstsong
    jsr OptAdjustRight
    bra OT_redraw
OT_firstsong:
    stz.w OPT_SONG
    stz.w MUSIC_VALID
    lda #0
    jsl OptCall_MusPlaySong
    bra OT_redraw
OT_tryb:
    rep #$20
    .ACCU 16
    lda.b scr0
    and #JOY_B.w
    beq OT_done
    jmp OptionsExit
OT_redraw:
    jsr OptionsDraw
    sep #$20
    .ACCU 8
    lda #SFX_MOVE.b
    jsl OptCall_SfxPlay
OT_done:
    rep #$20
    .ACCU 16
    rtl

ApplyDifficulty:
    sep #$20
    .ACCU 8
    lda DIFFICULTY
    cmp #1
    bcs +
    lda #4
+   cmp #9
    bcc +
    lda #8
+   lda DIFFICULTY
    cmp #8
    bne +
    lda #9
+   sta.w AI_LEVEL
    stz.w AI_LEVEL+1
    rep #$20
    .ACCU 16
    rtl

NeoToAI: .db 1, 2, 3, 4, 5, 6, 7, 9

MenuDraw:
    php
    rep #$10
    .INDEX 16
    sep #$20
    .ACCU 8
    lda #0
    sta.l $4200                           ; NMI off while drawing
    jsl OptCall_MtClear
    rep #$20
    .ACCU 16
    lda.w M_ITEM
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    cpx #7.w
    beq MD_exitrow
    lda.l MenuItemTab,x                   ; baked item id
    bra MD_row
MD_exitrow:
    lda #7
MD_row:
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l MenuCurRow,x
    asl a
    asl a
    asl a                                 ; row*8 = y px
    sta.b scr1
    lda.l MenuCurXl,x
    asl a
    asl a
    asl a                                 ; col*8 = x px
    sta.b scr0
    lda #CUR_TILE.b
    sta.b scr3
    lda #$32.b                            ; prio3, OBJ pal1 (yellow)
    sta.b scr4
    jsl OptCall_MtCell
    rep #$20
    .ACCU 16
    lda.w M_ITEM
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    cpx #7.w
    beq MD_exitrow2
    lda.l MenuItemTab,x
    bra MD_xrow
MD_exitrow2:
    lda #7
MD_xrow:
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l MenuCurXr,x
    asl a
    asl a
    asl a
    sta.b scr0
    lda #(CUR_TILE+1).b
    sta.b scr3
    jsl OptCall_MtCell
    sep #$20
    .ACCU 8
    lda #$81.b
    sta.l $4200
    plp
    rtl


; MOVED from engine/fight.asm: the Fight bank is at 32 KiB.
; Called through the MusPlaySong jml trampoline in fight.asm.
MusPlaySongFar:
    sep #$20
    .ACCU 8
    pha
    lda audiordy
    bne MPS_apu_idle
    jmp MPS_out
MPS_apu_idle:
    lda #0
    sta.l NMITIMEN                      ; NMI's spcProcess would corrupt the
    lda.l $4210                         ;   module-upload handshake; also
    rep #$30                            ;   wait out an NMI already in flight
    .ACCU 16
    .INDEX 16
    ldx #$2000
-   dex
    bne -
    phd                                 ; finish queued audio commands before
    lda #0                              ; replacing the active SNESMOD module
    tcd
    jsl SpcFlushSafe
    pld
    sep #$20
    .ACCU 8
    pla                                 ; pha was 8-bit: pop one byte only or
    rep #$20                            ;   the stack skew corrupts the rts
    .ACCU 16
    and #$00FF.w
    tax
    lda.l SongModTab,x
    and #$00FF.w
    phd                                 ; save D=ENGINE_DP; snesmod wants 0
    pha                                 ; arg1: module index
    lda #0
    tcd
    ; spcLoad replaces the previous song and driver in one handshake. A
    ; separate queued STOP can race that handshake and silence the next song.
    jsl spcLoad                         ;   its SPC RAM with the new module
    rep #$20
    .ACCU 16
    pla
    jsl SpcFlushSafe                        ; drain any stale command before PLAY
    lda #4.w                            ; reload the UI effects: select, move,
    sta.l $7E46F8                       ;   back and the winner announcer
    sep #$20                            ; byte var: STZ always stores 16 bits
    .ACCU 8                             ;   even here, so use an 8-bit STA
    lda #1                              ;   to keep the neighbouring byte
    sta.w UI_SFXLOAD
    stz.w UI_SLOT_SEL
    lda #1
    sta.w UI_SLOT_MOVE
    lda #2
    sta.w UI_SLOT_BACK
    lda #3
    sta.w UI_SLOT_WIN
    pea 0
    jsl spcPlay
    rep #$20
    .ACCU 16
    pla
    pea 150.w                           ; music under the SFX (~60%)
    jsl spcSetModuleVolume
    rep #$20
    .ACCU 16
    pla
    pld
    sep #$20
    .ACCU 8
    lda #1
    sta.w MUSON                         ; PLAY dispatched: later STOPs echo
    lda #$81.b
    sta.l NMITIMEN
    rtl
MPS_out:
    pla
    rtl

; A(8) = option row.  The selected row's text uses OBJ palette 1 (yellow,
; attribute $32); the other rows keep palette 2 (blue, $34).  The cursor
; brackets already use $32, so label/value/cursor highlight together.
OptSetAttr:
    sep #$20
    .ACCU 8
    cmp.w OPT_ITEM
    beq +
    lda #$34
    bra ++
+   lda #$32
++  sta.b scr4
    rts

.ENDS

; SFX id -> soundbank source/volume.  Lives in a low ROM bank because
; SfxPlay uses indexed long addressing (lda.l IkSfxMap+1,x); FightData's
; high bank overflows WLA's 24-bit expression calculation.
.BASE $00
.BANK 64 SLOT 0
.ORGA $2000
.SECTION "SfxMap" FORCE
.INCLUDE "gen_audio/spc_sfxmap.inc"
.ENDS
