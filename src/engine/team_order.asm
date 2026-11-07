; TEAM PLAY only: choose the original trio's first, second and third fighter.
; BG3 owns this screen; portrait tiles/palettes are restored by StartFight.
.BASE $00
.BANK 64 SLOT 0
.ORGA $3000
.SECTION "TeamOrderSelect" FORCE

; Carry set when StartFight was intercepted. One READY token permits resume.
TeamOrderGate:
    php
    rep #$10
    .INDEX 16
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #2.b
    bne TOG_skip
    lda.w OR_READY
    beq TOG_new
    stz.w OR_READY
    bra TOG_skip
TOG_new:
    lda.w T_SWAP
    ora.w T_I1
    ora.w T_I2
    bne TOG_skip                       ; member changes are not a new stage
    lda.b cpu1
    and.b cpu2
    bne TOG_skip                       ; no human has an order to choose
    jsr TeamOrderEnter
    plp
    sec
    rtl
TOG_skip:
    plp
    clc
    rtl

TeamOrderEnter:
    sep #$20
    .ACCU 8
    lda #GS_TEAM_ORDER.b
    sta.b gamestate
    lda #0.b
    sta.l NMITIMEN
    sta.l HDMAEN
    stz.w T_START
    stz.w MUSIC_VALID
    stz.w OR_WAIT
    stz.w OR_READY
    stz.w OR_SIDE
    stz.w OR_CARD
    stz.w OR_COUNT
    stz.w OR_COUNT+1
    stz.w OR_CURSOR
    stz.w OR_CURSOR+1
    stz.w OR_MASK
    stz.w OR_MASK+1
    stz.w OR_ACTIVE
    lda.b cpu1
    eor #1.b
    sta.w OR_HUMAN
    lda.b cpu2
    eor #1.b
    sta.w OR_HUMAN+1
    lda #3.b
    sta.w OR_SIZE
    sta.w OR_SIZE+1
    lda.b cpu1
    beq +
    lda.w T_N2
    sta.w OR_SIZE
+   lda.b cpu2
    beq +
    lda.w T_N2
    sta.w OR_SIZE+1
+   rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0.w
TOE_copy:
    sep #$20
    .ACCU 8
    lda.w T_TEAM1,x
    sta.w OR_TEAM,x
    rep #$20
    .ACCU 16
    inx
    cpx #6.w
    bcc TOE_copy
    jsl OrderCall_Init
    sep #$20
    .ACCU 8
    lda #0.b
    sta.l HDMAEN
    sta.l $212D
    sta.l $2111                        ; BG3 horizontal/vertical scroll = 0
    sta.l $2111
    sta.l $2112
    sta.l $2112
    lda #$04.b
    sta.l TM                           ; BG3 only, no stale stage or fighters
    jsr OrderLoadPortraits
    stz.w OR_SIDE
TOE_cpu:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w OR_HUMAN,x
    bne TOE_next
    jsr OrderDefault                    ; CPU marks ready without pad input
TOE_next:
    inc.w OR_SIDE
    lda.w OR_SIDE
    cmp #2.b
    bcc TOE_cpu
    jsr OrderDraw
    lda #SONG_KOF.b
    jsl OptCall_MusPlaySong
    jsl OptCall_ConsumePadEdges
    lda #1.b
    sta.w OR_ACTIVE
    lda #$81.b
    sta.l NMITIMEN
    rts

TeamOrderTick:
    rep #$30
    .ACCU 16
    .INDEX 16
    sep #$20
    .ACCU 8
    lda.w OR_WAIT
    beq TOT_input
    dec.w OR_WAIT
    bne TOT_out
    jsr OrderCommit
    lda #1.b
    sta.w OR_READY
    stz.w OR_ACTIVE
    jsl OptCall_ConsumePadEdges
    jsl OrderCall_StartFight
    rtl
TOT_input:
    stz.w OR_SIDE
TOT_side:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w OR_HUMAN,x
    beq TOT_next
    jsr OrderInput
TOT_next:
    inc.w OR_SIDE
    lda.w OR_SIDE
    cmp #2.b
    bcc TOT_side
    lda.w OR_COUNT
    cmp #3.b
    bne TOT_draw
    lda.w OR_COUNT+1
    cmp #3.b
    bne TOT_draw
    lda #24.b
    sta.w OR_WAIT
TOT_draw:
    jsr OrderDraw
TOT_out:
    rtl

; X = side, A8. B undoes one choice, START keeps the remaining source order.
OrderInput:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    beq OI_pad1
    lda FP+F_JOYPR+FP2OFS
    bra OI_pad
OI_pad1:
    lda FP+F_JOYPR
OI_pad:
    sta.w OR_KEYS
    and #JOY_B.w
    beq OI_start
    sep #$20
    .ACCU 8
    lda.w OR_COUNT,x
    bne OI_undo
    jmp OI_done
OI_undo:
    dec a
    sta.w OR_COUNT,x
    sta.b scr0
    jsr OrderSideBase                   ; Y = side*3
    rep #$20
    .ACCU 16
    lda.b scr0
    and #$00FF.w
    sta.b scr1
    tya
    clc
    adc.b scr1
    tay
    sep #$20
    .ACCU 8
    lda.w OR_SEQUENCE,y
    sta.w OR_CURSOR,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    jsr OrderBit
    eor #$FF.b
    and.w OR_MASK,x
    sta.w OR_MASK,x
    lda #SFX_BACK.b
    jsl OptCall_SfxPlay
    rts
OI_start:
    lda.w OR_KEYS
    and #JOY_ST.w
    beq OI_move
    jsr OrderDefault
    lda #SFX_SELECT.b
    jsl OptCall_SfxPlay
    rts
OI_move:
    sep #$20
    .ACCU 8
    lda.w OR_COUNT,x
    cmp #3.b
    beq OI_done
    rep #$20
    .ACCU 16
    lda.w OR_KEYS
    and #(JOY_UP|JOY_LF).w
    beq OI_forward
    sep #$20
    .ACCU 8
    lda.w OR_CURSOR,x
    bne +
    lda #3.b
+   dec a
    sta.w OR_CURSOR,x
    bra OI_confirm
OI_forward:
    lda.w OR_KEYS
    and #(JOY_DN|JOY_RT).w
    beq OI_confirm
    sep #$20
    .ACCU 8
    lda.w OR_CURSOR,x
    inc a
    cmp #3.b
    bcc +
    lda #0.b
+   sta.w OR_CURSOR,x
OI_confirm:
    rep #$20
    .ACCU 16
    lda.w OR_CURSOR,x
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    jsr OrderBit
    and.w OR_MASK,x
    beq OI_available
    rep #$20
    .ACCU 16
    lda.w OR_KEYS
    and #$0F00.w
    beq OI_done
    jmp OI_move                         ; skip already assigned cards
OI_available:
    rep #$20
    .ACCU 16
    lda.w OR_KEYS
    and #(JOY_A|JOY_X|JOY_Y).w
    beq OI_done
    sep #$20
    .ACCU 8
    jsr OrderPick
OI_done:
    sep #$20
    .ACCU 8
    rts

; Preserve the selected prefix, append each still-unused source card.
OrderDefault:
    stz.w OR_CARD
OD_loop:
    rep #$20
    .ACCU 16
    lda.w OR_CARD
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    jsr OrderBit
    and.w OR_MASK,x
    bne OD_next
    lda.w OR_CARD
    sta.w OR_CURSOR,x
    jsr OrderPick
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
OD_next:
    inc.w OR_CARD
    lda.w OR_CARD
    cmp #3.b
    bcc OD_loop
    rts

OrderPick:
    rep #$20
    .ACCU 16
    lda.w OR_CURSOR,x
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    jsr OrderBit
    and.w OR_MASK,x
    bne OP_deny
    jsr OrderBit
    ora.w OR_MASK,x
    sta.w OR_MASK,x
    lda.w OR_COUNT,x
    sta.b scr0
    jsr OrderSideBase
    rep #$20
    .ACCU 16
    lda.b scr0
    and #$00FF.w
    sta.b scr1
    tya
    clc
    adc.b scr1
    tay
    sep #$20
    .ACCU 8
    lda.w OR_CURSOR,x
    sta.w OR_SEQUENCE,y
    inc.w OR_COUNT,x
    lda.w OR_CURSOR,x
    inc a
    cmp #3.b
    bcc +
    lda #0.b
+   sta.w OR_CURSOR,x
    lda.w OR_COUNT,x
    cmp #3.b
    bcs OP_selected
OP_seek:
    rep #$20
    .ACCU 16
    lda.w OR_CURSOR,x
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    jsr OrderBit
    and.w OR_MASK,x
    beq OP_selected
    lda.w OR_CURSOR,x
    inc a
    cmp #3.b
    bcc +
    lda #0.b
+   sta.w OR_CURSOR,x
    bra OP_seek
OP_selected:
    lda #SFX_SELECT.b
    jsl OptCall_SfxPlay
    rts
OP_deny:
    lda #SFX_BACK.b
    jsl OptCall_SfxPlay
    rts

; Y = side*3, X preserved, A16 on return.
OrderSideBase:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    sta.b scr6
    asl a
    clc
    adc.b scr6
    tay
    rts

OrderCommit:
    stz.w OR_SIDE
OC_side:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w OR_HUMAN,x
    beq OC_next
    jsr OrderSideBase
    sty.b scr4                         ; source/destination side base
    ldx #0.w
OC_member:
    txa
    clc
    adc.b scr4
    tay
    sep #$20
    .ACCU 8
    lda.w OR_SEQUENCE,y
    rep #$20
    .ACCU 16
    and #$00FF.w
    clc
    adc.b scr4
    tay
    sep #$20
    .ACCU 8
    lda.w OR_TEAM,y
    sta.b scr0
    rep #$20
    .ACCU 16
    txa
    clc
    adc.b scr4
    tay
    sep #$20
    .ACCU 8
    lda.b scr0
    sta.w T_TEAM1,y
    rep #$20
    .ACCU 16
    inx
    cpx #3.w
    bcc OC_member
OC_next:
    sep #$20
    .ACCU 8
    inc.w OR_SIDE
    lda.w OR_SIDE
    cmp #2.b
    bcc OC_side
    stz.w T_I1
    stz.w T_I2
    rts

; Portraits are six independent 2bpp palettes, UI text uses palettes 6/7.
OrderLoadPortraits:
    stz.w OR_SIDE
OL_side:
    stz.w OR_CARD
OL_card:
    jsr OrderCardIndex
    rep #$20
    .ACCU 16
    lda.w OR_TEAM,y
    and #$00FF.w
    cmp #PORTRAIT_COUNT.w
    bcc +
    lda #0.w
+   asl a
    tax
    lda.w OR_SIDE
    and #$00FF.w
    beq OL_face1
    lda.l OrderPortraitOfsP2,x
    bra OL_face
OL_face1:
    lda.l OrderPortraitOfs,x
OL_face:
    clc
    adc #OrderPortraits.w
    sta.b scr0
    lda #256.w
    sta.b scr1
    lda.w OR_INDEX
    and #$00FF.w
    asl a
    asl a
    asl a
    asl a                              ; portrait slot*16 tiles
    asl a
    asl a
    asl a                              ; *8 -> words
    clc
    adc #(BG3CHR+512*8).w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:OrderPortraits
    jsl VrDmaFar
    jsr OrderCardIndex
    rep #$20
    .ACCU 16
    lda.w OR_TEAM,y
    and #$00FF.w
    cmp #PORTRAIT_COUNT.w
    bcc +
    lda #0.w
+   asl a
    asl a
    asl a
    clc
    adc #OrderPortraitPal.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:OrderPortraitPal
    sta.b scr2+2
    lda.w OR_INDEX
    asl a
    asl a
    sta.l CGADD
    rep #$20
    .ACCU 16
    ldy #0.w
OL_palette:
    lda [scr2],y
    sep #$20
    .ACCU 8
    sta.l CGDATA
    xba
    sta.l CGDATA
    rep #$20
    .ACCU 16
    iny
    iny
    cpy #8.w
    bcc OL_palette
    sep #$20
    .ACCU 8
    inc.w OR_CARD
    lda.w OR_CARD
    cmp #3.b
    bcs OL_cards_done
    jmp OL_card
OL_cards_done:
    inc.w OR_SIDE
    lda.w OR_SIDE
    cmp #2.b
    bcs OL_sides_done
    jmp OL_side
OL_sides_done:
    lda #24.b
    sta.l CGADD
    rep #$20
    .ACCU 16
    ldx #0.w
OL_ui_palette:
    lda.l OrderPalette,x
    sep #$20
    .ACCU 8
    sta.l CGDATA
    xba
    sta.l CGDATA
    rep #$20
    .ACCU 16
    inx
    inx
    cpx #32.w
    bcc OL_ui_palette
    sep #$20
    .ACCU 8
    lda #0.b
    sta.l CGADD
    lda #$21.b
    sta.l CGDATA
    lda #$10.b
    sta.l CGDATA
    rts

OrderCardIndex:
    jsr OrderSideBase
    tya
    clc
    adc.w OR_CARD                       ; mask byte: do not read OR_INDEX
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    tya
    sta.w OR_INDEX
    rts

OrderDraw:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0.w
    lda #$3800.w
OD_clear:
    sta.w HUDMAP,x
    inx
    inx
    cpx #2048.w
    bcc OD_clear
    sta.w OR_ATTR
    sep #$20
    .ACCU 8
    lda #32.b
    sta.w OR_LIMIT
    ; ---- arcade-style frame: title band + blue/red side panels ----------
    ; Title strip behind ORDER SELECT (palette 6, steel blue fill).
    rep #$20
    .ACCU 16
    lda #((1*32+4)*2).w
    sta.w OR_POS
    lda #24.w
    sta.b scr0
    lda #2.w
    sta.b scr1
    lda #(FONT_SOLID|$3800).w
    sta scr2
    jsr OrderFill
    ; P1 header (palette 8, blue) and P2 header (palette 9, red).
    lda #((5*32+2)*2).w
    sta.w OR_POS
    lda #13.w
    sta.b scr0
    lda #1.w
    sta.b scr1
    lda #(FONT_SOLID|$4000).w
    sta scr2
    jsr OrderFill
    lda #((5*32+17)*2).w
    sta.w OR_POS
    lda #13.w
    sta.b scr0
    lda #1.w
    sta.b scr1
    lda #(FONT_SOLID|$4400).w
    sta scr2
    jsr OrderFill
    ; Thin side borders around each trio.
    lda #((5*32+1)*2).w
    sta.w OR_POS
    lda #1.w
    sta.b scr0
    lda #19.w
    sta.b scr1
    lda #(FONT_SOLID|$4000).w
    sta scr2
    jsr OrderFill
    lda #((5*32+15)*2).w
    sta.w OR_POS
    jsr OrderFill
    lda #((5*32+16)*2).w
    sta.w OR_POS
    lda #(FONT_SOLID|$4400).w
    sta scr2
    jsr OrderFill
    lda #((5*32+30)*2).w
    sta.w OR_POS
    jsr OrderFill
    ; Bottom rail under both trios.
    lda #((23*32+1)*2).w
    sta.w OR_POS
    lda #15.w
    sta.b scr0
    lda #1.w
    sta.b scr1
    lda #(FONT_SOLID|$4000).w
    sta scr2
    jsr OrderFill
    lda #((23*32+16)*2).w
    sta.w OR_POS
    lda #(FONT_SOLID|$4400).w
    sta scr2
    jsr OrderFill
    rep #$20
    .ACCU 16
    lda #((2*32+10)*2).w
    sta.w OR_POS
    lda #OrderTitle.w
    jsr OrderLocalText
    lda #((4*32+12)*2).w
    sta.w OR_POS
    lda #OrderStage.w
    jsr OrderLocalText
    lda.w C_IDX
    and #$00FF.w
    clc
    adc #28.w                           ; charset '1' + confrontation
    ora #$3800.w
    sta.w HUDMAP+((4*32+18)*2)
    lda #((24*32+3)*2).w
    sta.w OR_POS
    lda #OrderHint.w
    jsr OrderLocalText
    lda #((26*32+7)*2).w
    sta.w OR_POS
    lda #OrderStart.w
    jsr OrderLocalText
    sep #$20
    .ACCU 8
    stz.w OR_SIDE
OD_side:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    tax
    asl a
    asl a
    asl a
    asl a                              ; side*16 columns
    clc
    adc #3.w
    clc
    adc #(6*32).w
    asl a
    sta.w OR_POS
    sep #$20
    .ACCU 8
    lda.w OR_HUMAN,x
    beq OD_cpu_title
    rep #$20
    .ACCU 16
    lda #OrderPlayer.w
    jsr OrderLocalText
    bra OD_player_num
OD_cpu_title:
    rep #$20
    .ACCU 16
    lda #OrderCpu.w
    jsr OrderLocalText
OD_player_num:
    lda.w OR_SIDE
    and #$00FF.w
    clc
    adc #28.w
    ora #$3800.w
    ldx.w OR_POS
    sta.w HUDMAP+14,x
    sep #$20
    .ACCU 8
    stz.w OR_CARD
OD_card:
    jsr OrderCardIndex
    rep #$20
    .ACCU 16
    lda.w OR_CARD
    and #$00FF.w
    sta.b scr0
    asl a
    asl a
    clc
    adc.b scr0                         ; card*5 rows
    clc
    adc #8.w
    asl a
    asl a
    asl a
    asl a
    asl a
    asl a                              ; row*64 byte HUD offset
    sta.b scr0
    lda.w OR_SIDE
    and #$00FF.w
    asl a
    asl a
    asl a
    asl a
    clc
    adc #2.w
    asl a
    clc
    adc.b scr0
    sta.w OR_ROWPOS
    lda.w OR_SIDE
    and #$00FF.w
    tax
    lda.w OR_CARD
    and #$00FF.w
    sep #$20
    .ACCU 8
    cmp.w OR_SIZE,x
    bcs OD_empty
    jsr OrderDrawPortrait
    jsr OrderDrawName
    jsr OrderDrawRank
OD_empty:
    sep #$20
    .ACCU 8
    inc.w OR_CARD
    lda.w OR_CARD
    cmp #3.b
    bcs OD_cards_done
    jmp OD_card
OD_cards_done:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    tax
    asl a
    asl a
    asl a
    asl a
    clc
    adc #(22*32+4).w
    asl a
    sta.w OR_POS
    lda #$3800.w
    sta.w OR_ATTR
    sep #$20
    .ACCU 8
    lda.w OR_HUMAN,x
    beq OD_fixed
    lda.w OR_COUNT,x
    cmp #3.b
    beq OD_ready
    rep #$20
    .ACCU 16
    lda #OrderChoose.w
    bra OD_status
OD_ready:
    rep #$20
    .ACCU 16
    lda #$3C00.w
    sta.w OR_ATTR
    lda #OrderReady.w
    bra OD_status
OD_fixed:
    rep #$20
    .ACCU 16
    lda #OrderFixed.w
OD_status:
    jsr OrderLocalText
    sep #$20
    .ACCU 8
    inc.w OR_SIDE
    lda.w OR_SIDE
    cmp #2.b
    bcs OD_sides_done
    jmp OD_side
OD_sides_done:
    rts

; Fill a HUDMAP rectangle: OR_POS = start byte offset, scr0 = width (tiles),
; scr1 = height (rows), scr2 = tile|palette|priority word.  Used only by the
; ORDER SELECT frame, before text/portraits are placed.
OrderFill:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx.w OR_POS
    sep #$20
    .ACCU 8
    lda.b scr0
    asl a
    sta.b scr4                          ; width in bytes
    lda #64
    sec
    sbc.b scr4
    sta.b scr5                          ; advance to the next row
    stz.b scr5+1
    lda.b scr1
    sta.b scr6
OF_row:
    lda.b scr0
    sta.b scr3
OF_col:
    lda.b scr2
    sta.w HUDMAP,x
    lda.b scr2+1
    sta.w HUDMAP+1,x
    inx
    inx
    dec.b scr3
    bne OF_col
    rep #$20
    .ACCU 16
    txa
    clc
    adc scr5
    tax
    sep #$20
    .ACCU 8
    dec.b scr6
    bne OF_row
    rep #$30
    .ACCU 16
    .INDEX 16
    rts

OrderDrawPortrait:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w OR_INDEX
    and #$00FF.w
    sta.b scr0
    asl a
    asl a
    asl a
    asl a                              ; slot*16 tiles
    clc
    adc #512.w
    sta.w OR_TILE
    lda.w OR_INDEX
    and #$00FF.w
    xba
    asl a
    asl a
    ora #$2000.w
    sta.b scr2
    ldx.w OR_ROWPOS
    ldy #4.w
ODP_row:
    lda #4.w
    sta.b scr0
ODP_col:
    lda.w OR_TILE
    ora.b scr2
    sta.w HUDMAP,x
    inc.w OR_TILE
    inx
    inx
    dec.b scr0
    bne ODP_col
    txa
    clc
    adc #56.w
    tax
    dey
    bne ODP_row
    rts

OrderDrawName:
    jsr OrderCardIndex
    rep #$20
    .ACCU 16
    lda.w OR_TEAM,y
    and #$00FF.w
    asl a
    tax
    lda.l CharSelTab,x
    sta.b scr2
    sep #$20
    .ACCU 8
    lda.b tblbank
    sta.b scr2+2
    rep #$20
    .ACCU 16
    ldy #CH_NAME.w
    lda [scr2],y
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:ioriName
    sta.b scr2+2
    lda #9.b
    sta.w OR_LIMIT
    rep #$20
    .ACCU 16
    lda #$3800.w
    sta.w OR_ATTR
    lda.w OR_ROWPOS
    clc
    adc #8.w
    sta.w OR_POS
    jsr OrderText
    sep #$20
    .ACCU 8
    lda #32.b
    sta.w OR_LIMIT
    rts

OrderDrawRank:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    tax
    lda.w OR_ROWPOS
    clc
    adc #72.w                          ; below the name, next to portrait
    sta.w OR_POS
    lda #$3800.w
    sta.w OR_ATTR
    jsr OrderSideBase
    sty.b scr4
    lda.w OR_COUNT,x
    and #$00FF.w
    sta.b scr5
    ldx #0.w
ODR_scan:
    cpx.b scr5
    bcs ODR_unpicked
    txa
    clc
    adc.b scr4
    tay
    sep #$20
    .ACCU 8
    lda.w OR_SEQUENCE,y
    cmp.w OR_CARD
    beq ODR_rank
    rep #$20
    .ACCU 16
    inx
    bra ODR_scan
ODR_rank:
    rep #$20
    .ACCU 16
    txa
    clc
    adc #28.w
    ora #$3C00.w
    ldx.w OR_POS
    sta.w HUDMAP,x
    rts
ODR_unpicked:
    rep #$20
    .ACCU 16
    lda.w OR_SIDE
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w OR_HUMAN,x
    beq ODR_out
    lda.w OR_CURSOR,x
    cmp.w OR_CARD
    bne ODR_out
    rep #$20
    .ACCU 16
    lda #$3C00.w
    sta.w OR_ATTR
    lda #OrderPickText.w
    jsr OrderLocalText
ODR_out:
    rts

; A16 = length-prefixed string in this bank, OR_POS = HUD byte address.
OrderLocalText:
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:OrderTitle
    sta.b scr2+2
    jsr OrderText
    rep #$20
    .ACCU 16
    rts
OrderText:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx.w OR_POS
    ldy #0.w
    sep #$20
    .ACCU 8
    lda [scr2],y
    cmp.w OR_LIMIT
    bcc +
    lda.w OR_LIMIT
+   sta.b scr0
    beq OTXT_out
    iny
OTXT_loop:
    lda [scr2],y
    sta.w HUDMAP,x
    lda.w OR_ATTR+1
    sta.w HUDMAP+1,x
    inx
    inx
    iny
    dec.b scr0
    bne OTXT_loop
OTXT_out:
    rep #$20
    .ACCU 16
    rts

; Called only in vblank by FightPresentDispatch, not the battle renderer.
TeamOrderPresent:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    sep #$20
    .ACCU 8
    lda #$8F.b
    sta.l INIDISP
    lda #$80.b
    sta.l VMAIN
    rep #$20
    .ACCU 16
    lda #BG3MAP.w
    sta.l VMADDL
    lda #HUDMAP.w
    sta.l $4362
    lda #2048.w
    sta.l $4365
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    sta.l $4364
    lda #1.b
    sta.l $4360
    lda #$18.b
    sta.l $4361
    lda #$40.b
    sta.l MDMAEN
    lda #$04.b
    sta.l TM
    lda #0.b
    sta.l $212D
    lda #$0F.b
    sta.l INIDISP
    inc.b framecnt
    plp
    rtl

; A8 = 1 << Y (Y=0..2), preserve the side index X.
OrderBit:
    phx
    tyx
    lda #1.b
    cpx #0.w
    beq OB_done
OB_shift:
    asl a
    dex
    bne OB_shift
OB_done:
    plx
    rts

OrderReady: .db 5,18,5,1,4,25
OrderChoose: .db 6,3,8,15,15,19,5
OrderFixed: .db 5,6,9,24,5,4
OrderBits: .db 1,2,4
OrderPalette: .dw $0000,$7FFF,$4210,$6318, $0000,$03FF,$7FFF,$4210
              .dw $0000,$03FF,$03FF,$0010, $0000,$001F,$001F,$0010
OrderTitle: .db 12,15,18,4,5,18,0,19,5,12,5,3,20
OrderStage: .db 5,19,20,1,7,5
OrderPlayer: .db 6,16,12,1,25,5,18
OrderCpu: .db 3,3,16,21
OrderPickText: .db 6,45,0,16,9,3,11
OrderHint: .db 27,1,38,0,16,9,3,11,0,0,2,38,0,21,14,4,15,0,0,4,9,18,38,0,13,15,22,5
OrderStart: .db 18,19,20,1,18,20,38,0,11,5,5,16,0,15,18,4,5,18,0,0
.ENDS

; Same CPU bank as Fight, in its free low-ROM window. Near calls remain
; valid without growing the full $8000..$FFFF battle section.
.BASE $C0
.BANK 50 SLOT 0
.ORGA $7040
.SECTION "TeamOrderNear" FORCE
; MainLoop's per-vblank presentation entry.  Gamestate 14 owns the PPU setup
; and streams the opening video; every other state keeps the fight path.
FightPresentDispatch:
    sep #$20
    .ACCU 8
    lda gamestate
    cmp #GS_TEAM_ORDER.b
    bne +
    jsl TeamOrderPresent
    rts
+   sep #$20
    .ACCU 8
    lda gamestate
    cmp #GS_INTRO_MSU.b
    bne +
    ; MsuVideoVblank runs from IntroNmiHandler at the top of the NMI, so the
    ; VRAM DMA gets the whole vblank window.  Only the frame counter is left.
    sep #$20
    .ACCU 8
    lda #$0F.b
    sta.l INIDISP
    inc.w framecnt
    rts
+   lda gamestate
    cmp #0.b
    bne +
    jsl TitlePaletteFar                   ; rewrite CGRAM inside vblank
+   jsr FightPresent
    rts


; Same-bank bridges used by the far ORDER SELECT screen.
OrderCall_Init:
    jsr VoiceQueueDrop
    stz.b winvoice
    stz.b sfxtoken
    jsr ResetSuperFx
    jsr PpuInit
    jsr LoadStaticGfx
    rtl
OrderCall_StartFight:
    jsr StartFight
    rtl

; Keep the near label in the Fight bank, below its full high-code window.
MtStrDense:
    rep #$20
    .ACCU 16
    ldx.b oamtop
    ldy #0
    sep #$20
    .ACCU 8
    lda.b [scr2],y
    sta.b scr5
    iny
-   lda.b scr0
    sta.w OAMBUF,x
    lda.b scr1
    sta.w OAMBUF+1,x
    lda.b [scr2],y
    sta.w OAMBUF+2,x
    lda.b scr4
    sta.w OAMBUF+3,x
    lda.b scr0
    clc
    adc #6.b
    sta.b scr0
    inx
    inx
    inx
    inx
    iny
    dec.b scr5
    bne -
    rep #$20
    .ACCU 16
    stx.b oamtop
    rts


.ENDS
