; ============================================================================
; sel_nomsu.asm — character select without the .msu data file.
;
; Only Terry's CHR is linked into the ROM (RomFlags), so without MSU-1 the
; select screen parks both cursors on Terry and shows a blinking red notice
; in the middle of the screen on BG3:
;
;   NO MSU FILE MATCHING ROM CRC / OR NAME FOUND.
;   TIP: UNZIP OR PLACE BOTH FILES / IN THE SAME FOLDER.
;   ONLY TERRY AVAILABLE.
;
; VRAM on the select screen: BG2 chr $0000-$117F, BG1 map $1800, BG2 map
; $1C00, OBJ $2000-$3FFF, BG1 chr $4000+.  The notice uses the free gap:
; BG3 chr base $1000 with the 2bpp font at $1180 (tile 48 = glyph 0) and its
; 32x32 map at $1400.  The menu font is 4bpp with colour 3 = body and
; colour 1 = shadow; it is remapped to body = 1, everything else = 2 (black),
; so the text sits on a solid band (rows 9-17) and only uses CGRAM 1/2, which the select art never references (BG1/BG2 palette 0
; only uses colours 0 and 3-15).
;
; Lives in bank 31 next to the fast paths (the Fight window is full).
; ============================================================================
.BASE $C0
.BANK 31 SLOT 0
.ORG 0
.SECTION "SelNoMsu" FREE

.DEFINE SNM_CHRW    $1180               ; font words (BG3 chr base $1000)
.DEFINE SNM_MAPW    $1400               ; BG3 32x32 map
.DEFINE SNM_TILE0   $2030               ; tile 48 (glyph 0 = space), prio 1
.DEFINE SNM_CLEAR   $2061               ; tile 97: transparent, prio 1
.DEFINE SNM_TERRY   15                  ; the only ROM-resident fighter
.DEFINE SNM_RED     $001F
.DEFINE SNM_SHADOW  $0000

; JSL from ShowSelect under forced blank with NMI off, after the menu font is
; in VRAM and SCUR1/2 are seeded.  A8 on return; preserves the caller's P.
SelNoMsuSetupFar:
    php
    sep #$20
    .ACCU 8
    lda.b msuok
    beq +
    plp
    rtl
+   rep #$10
    .INDEX 16
    ; --- both cursors on Terry ---
    lda #SNM_TERRY.b
    sta.b sel1
    sta.b sel2
    lda.l SelChrCell+SNM_TERRY
    sta.w SCUR1
    sta.w SCUR2
    ; --- font: 4bpp planes 0/1 -> 2bpp, body 3->1, shadow 1->2 ---
    lda #$80.b
    sta.l $002115                        ; word increment after $2119
    rep #$20
    .ACCU 16
    lda #SNM_CHRW.w
    sta.l $002116
    sep #$20
    .ACCU 8
    ldx #0
SNM_tile:
    ldy #8
SNM_row:
    lda.l MenuFont+1,x                   ; plane 1
    sta.b scr0
    lda.l MenuFont,x                     ; plane 0
    and.b scr0                           ; body: both planes set
    sta.l $002118
    eor #$FF.b                           ; shadow + background -> colour 2,
    sta.l $002119                        ;   the black band behind the text
    inx
    inx
    dey
    bne SNM_row
    rep #$20
    .ACCU 16
    txa
    clc
    adc #16.w                            ; skip planes 2/3
    tax
    sep #$20
    .ACCU 8
    cpx #(MenuFont_End-MenuFont).w
    bcc SNM_tile
    ; --- tile 97 (right after the font, $1308): fully transparent ---
    rep #$20
    .ACCU 16
    lda #0
    ldx #8.w
-   sta.l $002118
    dex
    bne -
    ; --- map: transparent, a black band on rows 9-17, then the lines ---
    lda #SNM_MAPW.w
    sta.l $002116
    lda #SNM_CLEAR.w
    ldx #(9*32).w
-   sta.l $002118
    dex
    bne -
    lda #SNM_TILE0.w                     ; glyph 0: solid colour 2
    ldx #(9*32).w
-   sta.l $002118
    dex
    bne -
    lda #SNM_CLEAR.w
    ldx #(14*32).w
-   sta.l $002118
    dex
    bne -
    ldx #0
SNM_line:
    lda.l SelNoMsuText,x
    beq SNM_text_done
    sta.l $002116                        ; VRAM word of the first cell
    inx
    inx
    lda.l SelNoMsuText,x
    and #$00FF.w
    tay                                  ; length
    inx
-   lda.l SelNoMsuText,x
    and #$00FF.w
    clc
    adc #SNM_TILE0.w
    sta.l $002118
    inx
    dey
    bne -
    bra SNM_line
SNM_text_done:
    ; --- colours: CGRAM 1 red body, 2 dark shadow ---
    sep #$20
    .ACCU 8
    lda #1.b
    sta.l $002121
    lda #<SNM_RED
    sta.l $002122
    lda #>SNM_RED
    sta.l $002122
    lda #<SNM_SHADOW
    sta.l $002122
    lda #>SNM_SHADOW
    sta.l $002122
    ; --- BG3 on top of everything (mode 1 BG3 priority + tile prio) ---
    lda #$09.b
    sta.l $002105                        ; BGMODE 1, BG3 high priority
    lda #((SNM_MAPW>>10)<<2).b
    sta.l $002109                        ; BG3SC: $1400, 32x32
    lda #$01.b
    sta.l $00210C                        ; BG34NBA: BG3 chr $1000
    lda #0
    sta.l $002111
    sta.l $002111                        ; BG3HOFS 0
    sta.l $002112
    sta.l $002112                        ; BG3VOFS 0
    sta.l $002130                        ; no colour math / windows left
    sta.l $002131                        ;   over by the last fight
    sta.l $00212E
    sta.l $00212F
    lda #$17.b
    sta.l $00212C                        ; TM = BG1 + BG2 + BG3 + OBJ
    plp
    rtl

; JSL from the vblank tick on the select screen (gs 5), A8.  Blinks the
; notice with the title prompt's 32-frame phase and hides it under the pause
; menu.  Leaves TM alone when the .msu is present.
SelNoMsuBlinkFar:
    php
    sep #$20
    .ACCU 8
    lda.b msuok
    bne SNB_out
    lda.w PZ_ON
    bne SNB_hide
    lda.b framecnt
    and #$20.b
    bne SNB_hide
    lda #$17.b                           ; BG1 + BG2 + BG3 + OBJ
    bra SNB_set
SNB_hide:
    lda #$13.b                           ; BG1 + BG2 + OBJ
SNB_set:
    sta.l $00212C
SNB_out:
    plp
    rtl

; .dw VRAM word, .db length, menufont indices (0 space, 1-26 A-Z, 37 ".", 38 ":").
; Rows 10-16 of 28: centered on the screen, 8 px cells.
SelNoMsuText:
    .dw $1542                       ; row 10: NO MSU FILE MATCHING ROM CRC
    .db 28,14,15,0,13,19,21,0,6,9,12,5,0,13,1,20,3,8,9,14,7,0,18,15,13,0,3,18,3
    .dw $1569                       ; row 11: OR NAME FOUND.
    .db 14,15,18,0,14,1,13,5,0,6,15,21,14,4,37
    .dw $15A1                       ; row 13: TIP: UNZIP OR PLACE BOTH FILES
    .db 30,20,9,16,38,0,21,14,26,9,16,0,15,18,0,16,12,1,3,5,0,2,15,20,8,0,6,9,12,5,19
    .dw $15C6                       ; row 14: IN THE SAME FOLDER.
    .db 19,9,14,0,20,8,5,0,19,1,13,5,0,6,15,12,4,5,18,37
    .dw $1605                       ; row 16: ONLY TERRY AVAILABLE.
    .db 21,15,14,12,25,0,20,5,18,18,25,0,1,22,1,9,12,1,2,12,5,37
    .dw 0

.ENDS
