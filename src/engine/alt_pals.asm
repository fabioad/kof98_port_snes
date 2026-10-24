; P2 mirror-match palette upload.  This lives in the AltPals section (bank
; 124) so neither the Fight code bank nor FightData grows.  LoadCharPals
; reaches it with jsl.  AltPalRow is a 9-byte row per char id:
;   +0 base ptr, +2 base bank + next ptr low, ... (3-byte entries).
UpCharPalsAltFar:
    rep #$20
    .ACCU 16
    lda sel2
    and #$00FF.w
    sta scr4
    asl a                               ; sel * 2
    asl a                               ; sel * 4
    asl a                               ; sel * 8
    clc
    adc scr4                            ; sel * 9
    sta scr4                            ; AltPalRow offset
    ldx #0
    lda #144.w                          ; P2 OBJ palette 1
    jsr AltPalUpFar
    ldx #3
    lda #192.w                          ; P2 OBJ palette 4 (dim)
    jsr AltPalUpFar
    ldx #6
    lda #224.w                          ; P2 OBJ palette 6 (flash)
    jsr AltPalUpFar
    rep #$20
    .ACCU 16
    rtl

; A(16) = CGRAM base, X = row offset (0 base / 3 dim / 6 hi),
; scr4 = char id*9.  Uploads one 32-byte OBJ palette.
AltPalUpFar:
    sep #$20
    .ACCU 8
    sta.l CGADD
    rep #$20
    .ACCU 16
    txa
    clc
    adc scr4
    tax
    lda.l AltPalRow,x
    sta lptr
    inx
    inx
    lda.l AltPalRow,x
    and #$00FF.w
    sta lptr+2
    ldy #0
-   lda [lptr],y
    sep #$20
    .ACCU 8
    sta.l CGDATA
    xba
    sta.l CGDATA
    rep #$20
    .ACCU 16
    iny
    iny
    cpy #32.w
    bne -
    rep #$20
    .ACCU 16
    rts

; Pad bit -> facing-relative direction.  JoyRelDir reads these with lda.l.
PadDirR:
    .db 0,4,8,12, 2,6,10,14, 1,5,9,13, 3,7,11,15
PadDirL:
    .db 0,8,4,12, 2,10,6,14, 1,9,5,13, 3,11,7,15
