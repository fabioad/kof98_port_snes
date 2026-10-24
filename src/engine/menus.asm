; ============================================================================
; menus.asm — menu/title/intro DATA: asset sections in the free
; half-banks (measured against the built ROM) plus the menu tables and
; sprite-text strings.  The code lives in menucore.asm, included inside
; the bank-48 "Fight" section so near jsr calls work.
; ============================================================================
.BASE $C0

.BANK 21 SLOT 0
.ORGA $0000
.SECTION "MenuArtTitle" FORCE
ArtTitleT:      .INCBIN "gen_menu/title.tiles"
ArtTitleT_End:
ArtTitleM:      .INCBIN "gen_menu/title.map"
ArtTitleP:      .INCBIN "gen_menu/title.pal"

; Title screen credit in the same 8x8 pixel font and blue OBJ palette as
; PRESS START, aligned with the SNK logo's left edge.
TitleCredit2: .db 26,16,18,15,7,18,1,13,13,9,14,7,38,0,6,1,2,9,15,0,1,4,0,29,27,29,33
.ENDS

.BANK 22 SLOT 0
.ORGA $0000
.SECTION "MenuArtModes" FORCE
ArtModesT:      .INCBIN "gen_menu/modes.tiles"
ArtModesT_End:
ArtModesM:      .INCBIN "gen_menu/modes.map"
ArtModesP:      .INCBIN "gen_menu/modes.pal"
.ENDS

.BANK 23 SLOT 0
.ORGA $0000
.SECTION "MenuFontData" FORCE
MenuFont:       .INCBIN "gen_menu/menufont.chr"
MenuFont_End:
CurTiles:       .INCBIN "gen_menu/cur.tiles"
CurTiles_End:

; ---- menu tables (bank 23 = CPU $E7 under .BASE $C0) --------------------
MenuCurRow:   .db 7, 9, 12, 14, 17, 19, 22, 24
MenuCurXl:    .db 4, 6, 5, 7, 6, 6, 7, 10
MenuCurXr:    .db 27, 26, 26, 24, 25, 25, 24, 21
; per-screen asset pointer tables
MnTileTab:
    .dw ArtTitleT, ArtModesT
MnTileTabB:
    .db :ArtTitleT, :ArtModesT
MnTileLen:
    .dw (ArtTitleT_End-ArtTitleT), (ArtModesT_End-ArtModesT)
MnMapTab:
    .dw ArtTitleM, ArtModesM
MnMapTabB:
    .db :ArtTitleM, :ArtModesM
MnPalTab:
    .dw ArtTitleP, ArtModesP
MnPalTabB:
    .db :ArtTitleP, :ArtModesP
; Menu OBJ palettes: white and gold.
MnObjPal:
    .dw $0000, $6B5A, $56B5, $7FFF
    .dw 0,0,0,0, 0,0,0,0, 0,0,0,0
    .dw $0000, $0FBF, $13FF, $2BFF
    .dw 0,0,0,0, 0,0,0,0, 0,0,$03FF,0
; Seven visible rows: the six modes plus OPTIONS; EXIT is the eighth
; cursor position, synthesized by MenuDraw.
MenuItemTab:  .db 0, 1, 2, 3, 4, 5, 6

; ---- OPTIONS submenu strings (8x8 menu font, length-prefixed) ----------
; Charset: 0 space, 1..26 A-Z, 27..36 0-9, 38 ':'.
OptTitle:      .db 7,15,16,20,9,15,14,19             ; OPTIONS
OptLevel:      .db 5,12,5,22,5,12                    ; LEVEL
OptLanguage:   .db 8,12,1,14,7,21,1,7,5              ; LANGUAGE
OptSound:      .db 10,19,15,21,14,4,0,20,5,19,20     ; SOUND TEST
OptExit:       .db 4,5,24,9,20                       ; EXIT
OptEnglish:    .db 7,5,14,7,12,9,19,8                ; ENGLISH
OptPortuguese: .db 10,16,15,18,20,21,7,21,5,19,5     ; PORTUGUESE
OptSpanish:    .db 7,19,16,1,14,9,19,8                ; SPANISH
OptFrench:     .db 6,6,18,5,14,3,8                   ; FRENCH
OptLangPtrTab: .dw OptEnglish, OptPortuguese, OptSpanish, OptFrench

OptS0:  .db 6,3,9,16,8,5,18                          ; CIPHER
OptS1:  .db 11,3,9,16,8,5,18,0,2,5,20,1              ; CIPHER BETA
OptS2:  .db 3,11,15,6                                ; KOF
OptS3:  .db 10,12,1,19,20,0,4,1,14,3,5               ; LAST DANCE
OptS4:  .db 6,19,21,14,19,5,20                        ; SUNSET
OptS5:  .db 6,23,9,14,14,5,18                         ; WINNER
OptS6:  .db 7,3,18,25,19,20,1,12                      ; CRYSTAL
OptS7:  .db 5,19,1,11,1                      ; ESAKA (Hero)
OptS8:  .db 3,8,9,14,1                       ; CHINA (Psycho)
OptS9:  .db 1,18,1,19,8,9                    ; ARASHI (Yagami)
OptS10: .db 19,15,21,12,0,20,15,23,14        ; SOUL TOWN (Kim)
OptS11: .db 18,21,13,2,12,9,14,7             ; RUMBLING (Ikari)
OptS12: .db 18,21,7,1,12                     ; RUGAL
OptS13: .db 6,1,9,18,25                      ; FAIRY (Women)
OptS14: .db 19,12,21,13                      ; SLUM (Wharf B)
OptS15: .db 1,18,20,6,9,7,8,20               ; ARTFIGHT (Wharf)
OptS16: .db 21,19,1,0,25,1,18,4              ; USA YARD
OptSongPtrTab:
    .dw OptS0, OptS1, OptS2, OptS3, OptS4, OptS5
    .dw OptS6, OptS7, OptS8, OptS9, OptS10, OptS11
    .dw OptS12, OptS13, OptS14, OptS15, OptS16

; MSU boot screen credit rows, drawn on BG3 as length-prefixed 8x8 tiles.
; Charset: 46 = ",", 47 = "@", 48 = '"'. Each row must fit 32 columns.
MsuCredit0: .db 29,20,8,1,14,11,19,0,6,15,18,0,9,11,1,18,21,7,1,46,0,26,5,12,7,1,4,9,19,46
MsuCredit1: .db 25,14,5,15,7,15,21,11,9,46,0,15,8,7,1,11,9,46,0,13,37,13,37,18,37,46
MsuCredit2: .db 27,1,8,21,18,15,14,46,0,12,5,47,14,46,0,13,4,11,46,0,10,21,1,14,24,15,3,46
MsuCredit3: .db 21,20,5,19,20,16,46,0,10,5,18,26,25,46,0,28,28,36,23,1,25,46
MsuCredit4: .db 28,6,5,18,22,9,3,1,14,20,5,46,0,11,1,13,18,1,14,2,5,18,14,19,20,5,9,14,46
MsuCredit5: .db 30,11,15,15,16,1,11,15,15,20,46,0,19,1,14,4,5,18,34,28,28,28,30,46,0,5,8,14,25,4,46
MsuCredit6: .db 28,13,15,21,19,5,18,46,0,8,48,46,0,22,9,3,5,46,0,2,18,1,26,15,13,2,9,5,46
MsuCredit7: .db 18,7,15,14,26,15,42,46,0,10,9,14,46,0,10,37,12,5,5
.ENDS

; ---- intro assets --------------------------------------------------------
.BANK 24 SLOT 0
.ORGA $0000
.SECTION "IntroM1a" FORCE
i0s_chr: .incbin "gen_menu/intro/intro00s.chr"
i0s_chr_end:
i0s_map: .incbin "gen_menu/intro/intro00s.map"
i0s_pal: .incbin "gen_menu/intro/intro00s.pal"
i2s_chr: .incbin "gen_menu/intro/intro02s.chr"
i2s_chr_end:
i2s_map: .incbin "gen_menu/intro/intro02s.map"
i2s_pal: .incbin "gen_menu/intro/intro02s.pal"
i12s_chr: .incbin "gen_menu/intro/intro12s.chr"
i12s_chr_end:
i12s_map: .incbin "gen_menu/intro/intro12s.map"
i12s_pal: .incbin "gen_menu/intro/intro12s.pal"
.ENDS

.BANK 25 SLOT 0
.ORGA $0000
.SECTION "IntroM1b" FORCE
i15_chr: .incbin "gen_menu/intro/intro15.chr" SKIP 0 READ 16384
i15_chr_end:
.ENDS

; This intro tail uses bank 64 after the boot trampolines; vectors are at FFE0.
.BANK 64 SLOT 0
.ORGA $8010
.SECTION "IntroM1b2" FORCE
i15_chr2: .incbin "gen_menu/intro/intro15.chr" SKIP 16384
i15_chr2_end:
i15_map: .incbin "gen_menu/intro/intro15.map"
i15_pal: .incbin "gen_menu/intro/intro15.pal"
.ENDS

; Keep bank 56 free for the sixth contiguous soundbank chunk.  SNESMod
; calculates its address as soundbank base + bank number at offset zero.
.BANK 49 SLOT 0
.ORGA $0000
.SECTION "IntroM7a" FORCE
im7_1:  .incbin "gen_menu/intro/intro01.m7pak"
im7_3:  .incbin "gen_menu/intro/intro03.m7pak"
im7_4:  .incbin "gen_menu/intro/intro04.m7pak"
im7_5:  .incbin "gen_menu/intro/intro05.m7pak"
im7_6:  .incbin "gen_menu/intro/intro06.m7pak"
.ENDS

.BANK 57 SLOT 0
.ORGA $0000
.SECTION "IntroM7b" FORCE
im7_7:  .incbin "gen_menu/intro/intro07.m7pak"
im7_8:  .incbin "gen_menu/intro/intro08.m7pak"
im7_9:  .incbin "gen_menu/intro/intro09.m7pak"
.ENDS

.BANK 45 SLOT 0
.ORGA $0000
.SECTION "IntroM7c" FORCE
im7_10: .incbin "gen_menu/intro/intro10.m7pak"
im7_11: .incbin "gen_menu/intro/intro11.m7pak"
im7_13: .incbin "gen_menu/intro/intro13.m7pak"
im7_14: .incbin "gen_menu/intro/intro14.m7pak"
.ENDS

.BANK 46 SLOT 0
.ORGA $1000
.SECTION "IntroM7p" FORCE
im7p_1:  .incbin "gen_menu/intro/intro01.m7pal"
im7p_3:  .incbin "gen_menu/intro/intro03.m7pal"
im7p_4:  .incbin "gen_menu/intro/intro04.m7pal"
im7p_5:  .incbin "gen_menu/intro/intro05.m7pal"
im7p_6:  .incbin "gen_menu/intro/intro06.m7pal"
im7p_7:  .incbin "gen_menu/intro/intro07.m7pal"
im7p_8:  .incbin "gen_menu/intro/intro08.m7pal"
im7p_9:  .incbin "gen_menu/intro/intro09.m7pal"
im7p_10: .incbin "gen_menu/intro/intro10.m7pal"
im7p_11: .incbin "gen_menu/intro/intro11.m7pal"
im7p_13: .incbin "gen_menu/intro/intro13.m7pal"
im7p_14: .incbin "gen_menu/intro/intro14.m7pal"
.ENDS

; ---- ending screens: Mode-1 BG2 art, 4 banded palettes like intro15.
; end00-04 = ending1 (Rugal defeat), end05-10 = ending2 (cast/credits).
; Raw ExHiROM bank bytes can only reach $8000-$FFFF for banks 64-127, but
; the PVSnesLib low-half windows are CPU-mapped ($54-$7D).  EndData21/22
; and EndData0 uses low half 43; EndData1-3 use 120-125; EndData19/20 use the
; free upper halves of banks 46/49.  This frees upper halves 95-117 for
; Omega Rugal's ROM CHR.  Banks 84-89/110-117 keep upper-half screens.
; Bank 43 is <64: address it through the $C0 window ($EB), not $2B.
.BASE $C0
.BANK 43 SLOT 0
.ORGA $0000
.SECTION "EndData0" FORCE
e0_chr: .incbin "gen_menu/end/end00.chr"
e0_chr_end:
.ENDS

.BASE $00
.BANK 123 SLOT 0
.ORGA $0000
.SECTION "EndData1" FORCE
e1_chr: .incbin "gen_menu/end/end01.chr"
e1_chr_end:
.ENDS

.BASE $00
.BANK 124 SLOT 0
.ORGA $0000
.SECTION "EndData2" FORCE
e2_chr: .incbin "gen_menu/end/end02.chr"
e2_chr_end:
.ENDS

.BASE $00
.BANK 125 SLOT 0
.ORGA $0000
.SECTION "EndData3" FORCE
e3_chr: .incbin "gen_menu/end/end03.chr"
e3_chr_end:
.ENDS

.BANK 118 SLOT 0
.ORGA $8000
.SECTION "EndData4" FORCE
e4_chr: .incbin "gen_menu/end/end04.chr"
e4_chr_end:
.ENDS

.BANK 119 SLOT 0
.ORGA $8000
.SECTION "EndData5" FORCE
e5_chr: .incbin "gen_menu/end/end05.chr"
e5_chr_end:
.ENDS

.BANK 120 SLOT 0
.ORGA $8000
.SECTION "EndData6" FORCE
e6_chr: .incbin "gen_menu/end/end06.chr"
e6_chr_end:
.ENDS

.BANK 121 SLOT 0
.ORGA $8000
.SECTION "EndData7" FORCE
e7_chr: .incbin "gen_menu/end/end07.chr"
e7_chr_end:
.ENDS

.BANK 122 SLOT 0
.ORGA $8000
.SECTION "EndData8" FORCE
e8_chr: .incbin "gen_menu/end/end08.chr"
e8_chr_end:
.ENDS

.BANK 123 SLOT 0
.ORGA $8000
.SECTION "EndData9" FORCE
e9_chr: .incbin "gen_menu/end/end09.chr"
e9_chr_end:
.ENDS

.BANK 124 SLOT 0
.ORGA $8000
.SECTION "EndData10" FORCE
e10_chr: .incbin "gen_menu/end/end10.chr"
e10_chr_end:
.ENDS

; end11-22 = team-pair montage tail + SNK/"Thank you" cards.  Free
; EndData11-14/18 moved to low halves 18/19/20/26/16 so Shingo's
; restored AIR can occupy the high halves of banks 70-87.  Low halves of
; banks <64 are only CPU-readable through the $C0 FastROM window, so these
; four must be addressed with .BASE $C0 ($D2-$DA); .BASE $00 would point at
; the $12/$13/$14/$1A system area and corrupt the CHR upload.
.BASE $C0
.BANK 18 SLOT 0
.ORGA $0000
.SECTION "EndData11" FORCE
e11_chr: .incbin "gen_menu/end/end11.chr"
e11_chr_end:
.ENDS

.BANK 19 SLOT 0
.ORGA $0000
.SECTION "EndData12" FORCE
e12_chr: .incbin "gen_menu/end/end12.chr"
e12_chr_end:
.ENDS

.BANK 20 SLOT 0
.ORGA $0000
.SECTION "EndData13" FORCE
e13_chr: .incbin "gen_menu/end/end13.chr"
e13_chr_end:
.ENDS

.BANK 26 SLOT 0
.ORGA $0000
.SECTION "EndData14" FORCE
e14_chr: .incbin "gen_menu/end/end14.chr"
e14_chr_end:
.ENDS

.BASE $00
.BANK 88 SLOT 0
.ORGA $0000
.SECTION "EndData15" FORCE
e15_chr: .incbin "gen_menu/end/end15.chr"
e15_chr_end:
.ENDS

.BANK 89 SLOT 0
.ORGA $8000
.SECTION "EndData16" FORCE
e16_chr: .incbin "gen_menu/end/end16.chr"
e16_chr_end:
.ENDS

.BANK 89 SLOT 0
.ORGA $A8C0                         ; EndData16 ends at $A8C0 in this bank
.SECTION "EndData17" FORCE
e17_chr: .incbin "gen_menu/end/end17.chr"
e17_chr_end:
.ENDS

.BASE $00
.BANK 82 SLOT 0
.ORGA $0000                         ; free low window (Terry ends at bank 81)
.SECTION "EndData18" FORCE
e18_chr: .incbin "gen_menu/end/end18.chr"
e18_chr_end:
.ENDS

.BASE $C0
.BANK 46 SLOT 0
.ORGA $BE00                         ; after SelArt (ends ~$BDBF)
.SECTION "EndData19" FORCE
e19_chr: .incbin "gen_menu/end/end19.chr"
e19_chr_end:
.ENDS

.BANK 49 SLOT 0
.ORGA $9800                         ; after IntroM7a
.SECTION "EndData20" FORCE
e20_chr: .incbin "gen_menu/end/end20.chr"
e20_chr_end:
.ENDS

.BASE $00
.BANK 120 SLOT 0
.ORGA $0000
.SECTION "EndData21" FORCE
e21_chr: .incbin "gen_menu/end/end21.chr"
e21_chr_end:
.ENDS

.BASE $00
.BANK 121 SLOT 0
.ORGA $0000
.SECTION "EndData22" FORCE
e22_chr: .incbin "gen_menu/end/end22.chr"
e22_chr_end:
.ENDS

.BANK 125 SLOT 0
.ORGA $8000
.SECTION "EndDataMP" FORCE
e0_map: .incbin "gen_menu/end/end00.map"
e0_pal: .incbin "gen_menu/end/end00.pal"
e1_map: .incbin "gen_menu/end/end01.map"
e1_pal: .incbin "gen_menu/end/end01.pal"
e2_map: .incbin "gen_menu/end/end02.map"
e2_pal: .incbin "gen_menu/end/end02.pal"
e3_map: .incbin "gen_menu/end/end03.map"
e3_pal: .incbin "gen_menu/end/end03.pal"
e4_map: .incbin "gen_menu/end/end04.map"
e4_pal: .incbin "gen_menu/end/end04.pal"
e5_map: .incbin "gen_menu/end/end05.map"
e5_pal: .incbin "gen_menu/end/end05.pal"
e6_map: .incbin "gen_menu/end/end06.map"
e6_pal: .incbin "gen_menu/end/end06.pal"
e7_map: .incbin "gen_menu/end/end07.map"
e7_pal: .incbin "gen_menu/end/end07.pal"
e8_map: .incbin "gen_menu/end/end08.map"
e8_pal: .incbin "gen_menu/end/end08.pal"
e9_map: .incbin "gen_menu/end/end09.map"
e9_pal: .incbin "gen_menu/end/end09.pal"
e10_map: .incbin "gen_menu/end/end10.map"
e10_pal: .incbin "gen_menu/end/end10.pal"

; per-screen pointer tables, indexed by ending screen 0-22
EndChrTab:
    .dw e0_chr, e1_chr, e2_chr, e3_chr, e4_chr, e5_chr
    .dw e6_chr, e7_chr, e8_chr, e9_chr, e10_chr, e11_chr
    .dw e12_chr, e13_chr, e14_chr, e15_chr, e16_chr, e17_chr
    .dw e18_chr, e19_chr, e20_chr, e21_chr, e22_chr
EndChrLen:
    .dw (e0_chr_end-e0_chr), (e1_chr_end-e1_chr), (e2_chr_end-e2_chr)
    .dw (e3_chr_end-e3_chr), (e4_chr_end-e4_chr), (e5_chr_end-e5_chr)
    .dw (e6_chr_end-e6_chr), (e7_chr_end-e7_chr), (e8_chr_end-e8_chr)
    .dw (e9_chr_end-e9_chr), (e10_chr_end-e10_chr), (e11_chr_end-e11_chr)
    .dw (e12_chr_end-e12_chr), (e13_chr_end-e13_chr), (e14_chr_end-e14_chr)
    .dw (e15_chr_end-e15_chr), (e16_chr_end-e16_chr), (e17_chr_end-e17_chr)
    .dw (e18_chr_end-e18_chr), (e19_chr_end-e19_chr), (e20_chr_end-e20_chr)
    .dw (e21_chr_end-e21_chr), (e22_chr_end-e22_chr)
EndChrTabB:
    .db :e0_chr, :e1_chr, :e2_chr, :e3_chr, :e4_chr, :e5_chr
    .db :e6_chr, :e7_chr, :e8_chr, :e9_chr, :e10_chr, :e11_chr
    .db :e12_chr, :e13_chr, :e14_chr, :e15_chr, :e16_chr, :e17_chr
    .db :e18_chr, :e19_chr, :e20_chr, :e21_chr, :e22_chr
EndMapTab:
    .dw e0_map, e1_map, e2_map, e3_map, e4_map, e5_map
    .dw e6_map, e7_map, e8_map, e9_map, e10_map, e11_map
    .dw e12_map, e13_map, e14_map, e15_map, e16_map, e17_map
    .dw e18_map, e19_map, e20_map, e21_map, e22_map
EndPalTab:
    .dw e0_pal, e1_pal, e2_pal, e3_pal, e4_pal, e5_pal
    .dw e6_pal, e7_pal, e8_pal, e9_pal, e10_pal, e11_pal
    .dw e12_pal, e13_pal, e14_pal, e15_pal, e16_pal, e17_pal
    .dw e18_pal, e19_pal, e20_pal, e21_pal, e22_pal
EndMPBTab:
    .db :e0_map, :e1_map, :e2_map, :e3_map, :e4_map, :e5_map
    .db :e6_map, :e7_map, :e8_map, :e9_map, :e10_map, :e11_map
    .db :e12_map, :e13_map, :e14_map, :e15_map, :e16_map, :e17_map
    .db :e18_map, :e19_map, :e20_map, :e21_map, :e22_map
.ENDS

; end11-22 map/pal: bank 125's upper half ran out of room. Use bank 48's
; low half; its upper half is now free (MatureData moved to bank 83).
.BASE $C0
.BANK 48 SLOT 0
.ORGA $0000
.SECTION "EndDataMP2" FORCE
e11_map: .incbin "gen_menu/end/end11.map"
e11_pal: .incbin "gen_menu/end/end11.pal"
e12_map: .incbin "gen_menu/end/end12.map"
e12_pal: .incbin "gen_menu/end/end12.pal"
e13_map: .incbin "gen_menu/end/end13.map"
e13_pal: .incbin "gen_menu/end/end13.pal"
e14_map: .incbin "gen_menu/end/end14.map"
e14_pal: .incbin "gen_menu/end/end14.pal"
e15_map: .incbin "gen_menu/end/end15.map"
e15_pal: .incbin "gen_menu/end/end15.pal"
e16_map: .incbin "gen_menu/end/end16.map"
e16_pal: .incbin "gen_menu/end/end16.pal"
e17_map: .incbin "gen_menu/end/end17.map"
e17_pal: .incbin "gen_menu/end/end17.pal"
e18_map: .incbin "gen_menu/end/end18.map"
e18_pal: .incbin "gen_menu/end/end18.pal"
e19_map: .incbin "gen_menu/end/end19.map"
e19_pal: .incbin "gen_menu/end/end19.pal"
e20_map: .incbin "gen_menu/end/end20.map"
e20_pal: .incbin "gen_menu/end/end20.pal"
e21_map: .incbin "gen_menu/end/end21.map"
e21_pal: .incbin "gen_menu/end/end21.pal"
e22_map: .incbin "gen_menu/end/end22.map"
e22_pal: .incbin "gen_menu/end/end22.pal"
.ENDS

; ---- KOF98 character-select screen ----------------------------------------
; Select tables live in the CPU-mapped low window of bank 118 (same
; .BASE $00 scheme as the mass-import data), so lda.l reaches them
; reliably.  SelArt in bank 46 crosses $8000 and cannot hold the table.
.BASE $00
.BANK 118 SLOT 0
.ORGA $0000
.SECTION "SelData" FORCE
.INCLUDE "gen_menu/seldata.inc"
.ENDS

; Converted by tools/build_select.py: bg anim frame 0,44 of Select.sff
; (blue beams + 39-cell grid + STAGE SELECT bar) quantized to a 4bpp BG1
; tilemap, char icons baked into occupied cells, big portraits emitted as
; runtime-patched face windows, and the system.sff cursor brackets packed
; into OBJ ring tiles.
.BASE $C0
.BANK 46 SLOT 0
.ORGA $3000                         ; IntroM7p owns $1000-~$2A00 of this bank
.SECTION "SelArt" FORCE
SelChr:         .INCBIN "gen_menu/select.chr"
SelChr_End:
SelMap:         .INCBIN "gen_menu/select.map"
SelMap_End:
SelPal:         .INCBIN "gen_menu/select.pal"
SelPal_End:
SelObjChr:      .INCBIN "gen_menu/selobj.chr"
SelObjChr_End:
SelObjPal:      .INCBIN "gen_menu/selobj.pal"
SelObjPal_End:
.ENDS
