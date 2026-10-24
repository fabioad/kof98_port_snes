; ============================================================================
; menucore.asm — opening intro, title and mode menu code.
; INCLUDED INSIDE the banked "Fight" section (see fight.asm) so near jsr
; calls to engine routines work.  Ported from the sibling kof98snes project
; (asm/intro.asm + the menu flow in pvs-src/main.c) onto this engine's
; gamestate machine:
;   gs 7 = opening intro (mode-1 stills + packed mode-7 zoom windows + fade)
;   gs 0 = title ("PRESS START", idle -> replay intro)
;   gs 5 = mode menu (SINGLE PLAY / SINGLE VS / TEAM PLAY / TEAM VS /
;          SURVIVOR / PRACTICE / EXIT)
; The mode menu opens the shared select screen in fight.asm (gs 0).
; ============================================================================

; ---- new gamestates -------------------------------------------------------
.DEFINE GS_INTRO    7
.DEFINE GS_MENU     6
.DEFINE GS_MSUCHK   9
.DEFINE GS_OPTIONS  11

; OPTIONS submenu scratch.  F079/F07A are the SV_ETICK bytes, which are
; only live during the SURVIVOR ending and never overlap this screen.
.DEFINE OPT_ITEM    $F079
.DEFINE OPT_SONG    $F07A

; ---- intro/menu state (WRAM $F000+, reached via DBR=$7E like OAMBUF) -----
; NOTE: must sit above the SNESMOD stream buffer / lib BSS, which clobber the
; $6100-$65xx area while spcProcess runs
.DEFINE IN_SCR      $F000
.DEFINE IN_FX       $F001
.DEFINE IN_FDIRTY   $F002
.DEFINE IN_TICK     $F004                 ; .w
.DEFINE IN_M7HS     $F006                 ; .w h scale (8.8)
.DEFINE IN_M7DS     $F008                 ; .w v scale
.DEFINE IN_M7DHI    $F00A                 ; .w entry deltas / exit deltas
.DEFINE IN_M7DDI    $F00C
.DEFINE IN_M7DHO    $F00E
.DEFINE IN_M7DDO    $F010
.DEFINE IN_FCUR     $F080                 ; 128B fading palette (4 bands)
.DEFINE IN_FTGT     $F100                 ; 128B target palette
.DEFINE M_ITEM      $F070                 ; 0..6 -> MenuItemTab entry (6 = EXIT)
.DEFINE S_MODE      $F071                 ; mode menu selection
.DEFINE S_WAIT      $F074                 ; .w idle frames on title
.DEFINE S_BLINK     $F076                 ; PRESS START visibility phase
.DEFINE M_WHICH     $F077
.DEFINE DM_TICK     $F068                 ; .w attract-demo frames left
.DEFINE DM_ON       $F06A                 ; 1 while the title attract fight runs
.DEFINE MSU_PHASE   $F072                 ; 0 = checking, 1 = result shown
.DEFINE MSU_LEN     $F073                 ; number of blinking OBJ cells

; MSU screen credit strip: BG3 2bpp font + 32x32 map (rows 20-27 visible).
.DEFINE MSU_CRED_TILEW $7000              ; BG3 tile base (word)
.DEFINE MSU_CRED_MAPW  $7800              ; BG3 map base (word)
.DEFINE MSU_CRED_ROWS  8

.DEFINE G_MODE      $10C0                 ; 0 single VS, 1 single play, 2 team play,
                                        ;   3 team VS, 4 survivor, 5 practice
.DEFINE C_IDX       $10C1                 ; confrontation 0..6 (6 = boss)
.DEFINE C_PVP        $10C2                 ; 1 while first campaign bout is human vs human
.DEFINE C_WHARF     $10C3                 ; legacy stage-swap flag
.DEFINE C_STAGE     $10C4                 ; base stage of the confrontation
.DEFINE STAGEF      $10C5                 ; forced stage idx / $FF random
.DEFINE MATWON      $10C6                 ; confrontation outcome flag
.DEFINE T_STEP      $10C7                 ; team-select pick counter
.DEFINE T_I1        $10C8                 ; active member, player team
.DEFINE T_I2        $10C9                 ; active member, cpu team
.DEFINE T_N2        $10CA                 ; CPU team size
.DEFINE T_TEAM1     $10CB                 ; 3B player team char ids
.DEFINE T_TEAM2     $10CE                 ; 3B cpu team char ids
.DEFINE T_SWAP      $10D1                 ; bit0 P1 / bit1 P2 member swap
.DEFINE T_PICK_SIDE $10D2                 ; Team VS: 0 = P1, 1 = P2
.DEFINE CPU_USED     $10D3                 ; campaign roster history (18 bytes)
.DEFINE MUSIC_STAGE  $10E5                 ; last stage module loaded
.DEFINE MUSIC_VALID  $10E6                 ; stage music cache valid
.DEFINE T_START      $10E7                 ; delayed team fight launch
.DEFINE T_LASTFRAME  $10E8                 ; last frame counted by T_START
.DEFINE CPU_USED_COUNT $10E9               ; number of entries in CPU_USED
.DEFINE C_HUMAN_SIDE $10EA                 ; 0 = P1 carries campaign, 1 = P2

; ---- SURVIVOR route -------------------------------------------------------
; The shuffled opponent list needs 48 bytes, so it lives outside the DP
; window.  In the PVSnesLib build DBR is $7E and $8000 is WRAM; the linker
; reservation for this block lives in src/snes/fight_bridge.asm.  The plain
; WLA build keeps the same bytes in the free low-WRAM gap at $2000.
.IFDEF PVSNESLIB
.DEFINE SURV_LIST   $4F00                 ; right after the 2 KiB HUD shadow
.DEFINE SURV_COUNT  $4F30                 ; eligible opponents (byte)
.DEFINE SURV_HP     $4F31                 ; human HP carried between rounds
.DEFINE SURV_KOSP   $4F32                 ; 0 none / 1 special finish / 2 special finish with human >50% HP
.DEFINE SV_FIN      $4F33                 ; SURVIVOR ending fade-in frames
.ELSE
.DEFINE SURV_LIST   $2000
.DEFINE SURV_COUNT  $2030
.DEFINE SURV_HP     $2031
.DEFINE SURV_KOSP   $2032
.DEFINE SV_FIN      $2033
.ENDIF

; ---- endings (gs 8): still screens, BG2 $1800 / CHR $2000 like intro ----
.DEFINE GS_END      8
.DEFINE GS_SVEND    10                   ; SURVIVOR still sequence
.DEFINE SV_HOLD     600                  ; 10 s per still (130 s / 13)
.DEFINE SV_LAST_HOLD 900                 ; last still gets +5 s
.DEFINE SV_FOUT     18                   ; fast fade-out window (2 steps/frame)
.DEFINE END_COUNT   23                    ; end00-04 = ending1, 05-22 = ending2
.DEFINE END_HOLD    300                   ; frames per screen (~128 fade-in + hold + ~124 fade-out)
.DEFINE END_FOUT    132                   ; E_TICK threshold: fade-out window
; ending2 screens 6-20 are the 15 team-pair montage cards: they share the
; 3x300-frame budget of the screens they replaced, so each runs 60 frames
; with fast fades (2 InFadeStep/frame -> ~16-frame fades, black target).
.DEFINE END_PFIRST  6                     ; first montage screen index
.DEFINE END_PLAST   21                    ; one past the last montage index
.DEFINE END_PHOLD   60                    ; frames per montage card (15x60=900)
.DEFINE END_PFOUT   18                    ; montage fade-out window
.DEFINE E_SCR       $F078                 ; free gap: $F052+ is intro scratch,
.DEFINE E_TICK      $F079                 ;   $F080+ is IN_FCUR (.w countdown)
.DEFINE E_FADE      $F07B                 ; 1 = black fade-out target armed
.DEFINE E_BLACKIN   $F012                 ; 1 = next EndLoad fades in from black

; ---- intro scratch: direct-page $B0-$B9 (free in this engine's DP map) ----
.DEFINE I_SRC       $B0                   ; 3B far src pointer
.DEFINE I_PAK       $B3                   ; 3B far pak pointer
.DEFINE I_LEN       $B6                   ; 2B byte count
.DEFINE I_EA        $B8                   ; 2B scratch
.DEFINE I_EC        $F052                 ; 2B
.DEFINE I_NT        $F054
.DEFINE I_CR        $F056                 ; cols | rows<<8
.DEFINE I_MAP0      $F058
.DEFINE I_COLS      $F05A
.DEFINE I_ROWS      $F05C
.DEFINE I_CURM      $F05E
.DEFINE I_F0        $F060

.DEFINE IN_FRAMES   166                   ; 15*166 + final 168 = Cipher's 2658 ticks
.DEFINE IN_COUNT    16
.DEFINE MENU_MAPW   $1800                 ; BG1 map word (32x32)
.DEFINE MENU_TILEW  $4000                 ; BG1 tiles word
.DEFINE MENU_OBJW   $2000                 ; OBJ table0 word (font/cur) — OBSEL base aligned
.DEFINE CUR_TILE    60                    ; bracket tiles at OBJ idx 60/61

; =====================================================================
;  intro driver (port of sibling asm/intro.asm, JSR interface)
; =====================================================================

; copy I_LEN bytes from [I_SRC] to VRAM words starting at X
InVCopy:
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l $2115                           ; inc on $2118 write
    rep #$20
    .ACCU 16
    txa
    sta.l $2116
    ldy #0
-   lda.b [I_SRC],y
    sta.l $2118
    iny
    iny
    cpy.b I_LEN
    bne -
    rep #$20
    .ACCU 16
    rts

; copy I_LEN BYTES from [I_SRC] to the VRAM high-byte plane ($2119);
; caller pre-sets VMAIN/VMADD
InVCopyHi:
    sep #$20
    .ACCU 8
    ldy #0
-   lda.b [I_SRC],y
    sta.l $2119
    iny
    cpy.b I_LEN
    bne -
    rep #$20
    .ACCU 16
    rts

; write I_LEN bytes from [I_SRC] to CGRAM starting at color X
InCgRam:
    sep #$20
    .ACCU 8
    txa
    sta.l $2121
    ldy #0
-   lda.b [I_SRC],y
    sta.l $2122
    iny
    cpy.b I_LEN
    bne -
    rep #$20
    .ACCU 16
    rts

; Mode 1 regs for the still/finale screens: BG2 only, map $1800,
; tiles word $2000
InM1Regs:
    sep #$20
    .ACCU 8
    lda #$01.b
    sta.l $2105                           ; BGMODE 1
    lda #$18.b
    sta.l $2108                           ; BG2SC: map word $1800, 32x32
    lda #$20.b
    sta.l $210B                           ; BG12NBA: BG2 tiles word $2000
    lda #$02.b
    sta.l $212C                           ; TM = BG2 only
    lda #0
    sta.l $212D                           ; TS off
    lda #0
    sta.l $210D
    lda #0
    sta.l $210D                           ; BG1HOFS 0
    lda #0
    sta.l $210E
    lda #0
    sta.l $210E                           ; BG1VOFS 0
    lda #0
    sta.l $210F
    lda #0
    sta.l $210F                           ; BG2HOFS 0
    lda #0
    sta.l $2110
    lda #0
    sta.l $2110                           ; BG2VOFS 0
    rep #$20
    .ACCU 16
    rts

; Mode 7 matrix write: window pivot at the picture centre texel
; (512,472), parked at screen centre (128,112) via scroll H=384 V=360.
; Rest scale is $0080 (0.5): the 128x112-texel window then covers the
; whole 256x224 screen.
InM7Apply:
    sep #$20
    .ACCU 8
    lda #$07.b
    sta.l $2105                           ; BGMODE 7
    lda #$80.b
    sta.l $211A                           ; M7SEL: overflow black
    lda #$01.b
    sta.l $212C                           ; TM = BG1 (the M7 plane)
    lda #0
    sta.l $212D
    rep #$20
    .ACCU 16
    lda #384.w
    sep #$20
    .ACCU 8
    sta.l $210D
    xba
    sta.l $210D                           ; BG1HOFS = pivot view X
    rep #$20
    .ACCU 16
    lda #360.w
    sep #$20
    .ACCU 8
    sta.l $210E
    xba
    sta.l $210E                           ; BG1VOFS = pivot view Y
    lda #$00.b
    sta.l $211F
    lda #$02.b
    sta.l $211F                           ; M7X = 512
    lda #$D8.b
    sta.l $2120
    lda #$01.b
    sta.l $2120                           ; M7Y = 472
    rep #$20
    .ACCU 16
    lda.w IN_M7HS
    sep #$20
    .ACCU 8
    sta.l $211B
    xba
    sta.l $211B                           ; M7A = h scale (8.8)
    lda #0
    sta.l $211C
    lda #0
    sta.l $211C                           ; M7B = 0
    lda #0
    sta.l $211D
    lda #0
    sta.l $211D                           ; M7C = 0
    rep #$20
    .ACCU 16
    lda.w IN_M7DS
    sep #$20
    .ACCU 8
    sta.l $211E
    xba
    sta.l $211E                           ; M7D = v scale
    rep #$20
    .ACCU 16
    rts

; copy the 12-byte fx param record for IN_FX into the anim vars
InFxInit:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w IN_FX
    and #$00FF.w
    asl a
    asl a
    sta.b I_EA                            ; fx*4
    asl a                                 ; fx*8
    clc
    adc.b I_EA                            ; fx*12
    tax
    ldy #0
-   lda.l InFxParams,x
    sta.w IN_M7HS,y
    inx
    inx
    iny
    iny
    cpy #$000C.w
    bne -
    rts

; finale: park the target palette in IN_FTGT, start CGRAM row 0 white
InFadeInit:
    rep #$20
    .ACCU 16
    ldy #0
-   lda.b [I_SRC],y                       ; pal ptr still set from the load
    sta.w IN_FTGT,y
    iny
    iny
    cpy #128.w
    bne -
    ldx #0
    lda #$7FFF.w
-   sta.w IN_FCUR,x
    inx
    inx
    cpx #$0080.w
    bne -
    sep #$20
    .ACCU 8
    lda #$00.b
    sta.l $2121
    ldx #$0040.w
-   lda #$FF.b
    sta.l $2122
    lda #$7F.b
    sta.l $2122
    dex
    bne -
    lda #0
    sta.w IN_FDIRTY
    rep #$20
    .ACCU 16
    rts

; one step of the white->art palette fade (16 colors, 5-bit channels)
InFadeStep:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0
IFSL:
    lda.w IN_FCUR,x
    sta.b I_EA
    lda.w IN_FTGT,x
    sta.w I_EC
    lda.b I_EA                            ; red
    and #$001F.w
    sta.w I_F0
    lda.w I_EC
    and #$001F.w
    cmp.w I_F0
    beq IFgreen
    bcs IFredup
    lda.b I_EA
    dec a
    sta.b I_EA
    bra IFgreen
IFredup:
    lda.b I_EA
    inc a
    sta.b I_EA
IFgreen:
    lda.b I_EA                            ; green (bits 5..9)
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    and #$001F.w
    sta.w I_F0
    lda.w I_EC
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    and #$001F.w
    cmp.w I_F0
    beq IFblue
    bcs IFgrnup
    lda.b I_EA
    sec
    sbc #$0020.w
    sta.b I_EA
    bra IFblue
IFgrnup:
    lda.b I_EA
    clc
    adc #$0020.w
    sta.b I_EA
IFblue:
    lda.b I_EA                            ; blue (bits 10..14)
    xba
    lsr a
    lsr a
    and #$001F.w
    sta.w I_F0
    lda.w I_EC
    xba
    lsr a
    lsr a
    and #$001F.w
    cmp.w I_F0
    beq IFnext
    bcs IFbluup
    lda.b I_EA
    sec
    sbc #$0400.w
    sta.b I_EA
    bra IFnext
IFbluup:
    lda.b I_EA
    clc
    adc #$0400.w
    sta.b I_EA
IFnext:
    lda.b I_EA
    sta.w IN_FCUR,x
    inx
    inx
    cpx #$0080.w
    beq IFdone
    jmp IFSL
IFdone:
    sep #$20
    .ACCU 8
    lda #$01.b
    sta.w IN_FDIRTY
    rep #$20
    .ACCU 16
    rts

; load screen IN_SCR (0..15): force-blank upload, ends unblanked
InLoad:
    sep #$20
    .ACCU 8
    php
    lda #0
    sta.l $4200                            ; NMI off while we repack VRAM
    lda #$80.b
    sta.l $2100                            ; force blank
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.l $7E0000+IN_SCR
    and #$00FF.w
    sta.b I_EA                             ; screen index
    asl a
    sta.w I_EC                             ; screen*2 for word tables
    sep #$20
    .ACCU 8
    ldx.b I_EA
    lda.l InFxTab,x
    sta.w IN_FX
    beq InLM1                              ; NONE -> windowed Mode 1 still
    cmp #$06.b
    beq InLM1                              ; FADE -> full-frame Mode 1
    jmp InLM7

; ---- windowed / full-frame Mode 1 screen ----
InLM1:
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l InM1Chr,x
    sta.b I_SRC
    lda.l InM1Len,x
    sta.b I_LEN
    sep #$20
    .ACCU 8
    ldx.b I_EA
    lda.l InM1ChrB,x
    sta.b I_SRC+2
    ldx #$2000.w                           ; BG2 tiles word
    jsr InVCopy

    lda.b I_EA
    cmp #15.w                              ; frame 15 chr is split in two
    bne +
    rep #$20
    .ACCU 16
    lda #i15_chr2
    sta.b I_SRC
    lda #(i15_chr2_end-i15_chr2)
    sta.b I_LEN
    sep #$20
    .ACCU 8
    lda #:i15_chr2
    sta.b I_SRC+2
    ldx #$4000.w                           ; continues right after chunk A
    jsr InVCopy
+
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l InM1Map,x
    sta.b I_SRC
    sep #$20
    .ACCU 8
    ldx.b I_EA
    lda.l InM1MapB,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #2048.w
    sta.b I_LEN
    ldx #$1800.w                           ; BG2 map word
    jsr InVCopy

    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l InM1Pal,x
    sta.b I_SRC
    sep #$20
    .ACCU 8
    ldx.b I_EA
    lda.l InM1PalB,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #128.w                             ; stills all carry four
    sta.b I_LEN                            ;   16-color bands now
    ldx #0
    jsr InCgRam

    sep #$20
    .ACCU 8
    lda.w IN_FX
    cmp #$06.b
    bne +
    jsr InFadeInit                         ; I_SRC still = pal ptr
+   jsr InM1Regs
    jmp InShow

; ---- packed Mode 7 windowed screen ----
InLM7:
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l InM7Pak,x
    sta.b I_PAK
    sep #$20
    .ACCU 8
    ldx.b I_EA
    lda.l InM7PakB,x
    sta.b I_PAK+2
    rep #$20
    .ACCU 16
    ldy #0
    lda.b [I_PAK],y
    sta.w I_NT                             ; ntiles
    ldy #2
    lda.b [I_PAK],y
    sta.w I_CR                             ; cols | rows<<8
    ldy #4
    lda.b [I_PAK],y
    sta.w I_MAP0                           ; map word of cell (0,0)
    ; tiles -> high-byte plane at VMADD 0
    lda.b I_PAK
    clc
    adc #6.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda.b I_PAK+2
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda.w I_NT
    asl a
    asl a
    asl a
    asl a
    asl a
    asl a
    sta.b I_LEN                            ; ntiles*64
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l $2115                            ; inc on $2119 write
    lda #0
    sta.l $2116
    lda #0
    sta.l $2117                            ; VMADD = word 0
    jsr InVCopyHi
    ; clear the whole 128x128 map (low bytes) to tile 0 — MUST stay A8:
    ; a 16-bit store hits $2118/$2119 and inc-on-low-write would skip
    ; every other cell's low byte
    sep #$20
    .ACCU 8
    lda #0
    sta.l $2115                            ; inc on $2118 write
    lda #0
    sta.l $2116
    lda #0
    sta.l $2117
    lda #0
    rep #$10
    .INDEX 16
    ldx #$4000.w
-   sta.l $2118
    dex
    bne -
    ; window cells, one row at a time
    rep #$20
    .ACCU 16
    lda.w I_NT
    asl a
    asl a
    asl a
    asl a
    asl a
    asl a
    clc
    adc.b I_PAK
    adc #6.w
    sta.b I_SRC                            ; cells src = pak + 6 + ntiles*64
    sep #$20
    .ACCU 8
    lda.b I_PAK+2
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda.w I_CR
    and #$00FF.w
    sta.w I_COLS
    lda.w I_CR
    xba
    and #$00FF.w
    sta.w I_ROWS
    lda.w I_MAP0
    sta.w I_CURM
InLM7Row:
    sep #$20
    .ACCU 8
    lda.w I_CURM
    sta.l $2116
    lda.w I_CURM+1
    sta.l $2117
    ldy #0
-   lda.b [I_SRC],y
    sta.l $2118
    iny
    cpy.w I_COLS
    bne -
    rep #$20
    .ACCU 16
    lda.b I_SRC
    clc
    adc.w I_COLS
    sta.b I_SRC
    lda.w I_CURM
    clc
    adc #$0080.w
    sta.w I_CURM
    lda.w I_ROWS
    dec a
    sta.w I_ROWS
    bne InLM7Row
    ; 256-color palette
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l InM7Pal,x
    sta.b I_SRC
    sep #$20
    .ACCU 8
    ldx.b I_EA
    lda.l InM7PalB,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #512.w
    sta.b I_LEN
    ldx #0
    jsr InCgRam
    jsr InFxInit
    jsr InM7Apply                          ; first matrix write under blank

InShow:
    sep #$20
    .ACCU 8
    lda #$0F.b
    sta.l $2100                            ; display on
    lda #$81.b
    sta.l $4200                            ; re-arm NMI + autojoy (InLoad
                                           ;   killed it for the VRAM burst)
    rep #$20
    .ACCU 16
    plp
    rts

; ---- public entries ------------------------------------------------------

; enter the opening intro: screen 0, cipher theme, gs=GS_INTRO
OpnEnter:
    jsr VoiceQueueClear                  ; demo/intro transition: the Cipher
    sep #$20                            ;   load below keys the SPC off
    .ACCU 8
    lda #0
    sta.l NMITIMEN                         ; kill NMI before the ISR can land
    lda #$80.b
    sta.l INIDISP                          ; blank now: the last title frame
    ;                                      ;   lingers into mid-load garbage
    lda #ENGINE_DB.b                    ; defensive: callers may arrive with a
    pha                                 ;   foreign DBR; every .w var below
    plb                                 ;   lives in WRAM
    lda #0
    sta.l $7E0000+IN_SCR
    sta.l $7E0000+IN_FX
    sta.l $7E0000+IN_FDIRTY
    rep #$20
    .ACCU 16
    lda #0
    sta.l $7E0000+IN_TICK
    jsr InLoad
    sep #$20
    .ACCU 8
    lda #SONG_CIPHER.b
    jsr MusPlaySong                       ; Cipher theme under the intro
    sep #$20
    .ACCU 8
    lda #GS_INTRO.b
    sta.b gamestate
    jmp OpnDone                          ; InLoad leaves the stack skewed --
                                         ;   rts here jumps wild, so continue
                                         ;   straight into the main loop tail

; per-frame tick while the intro runs; START skips to the title
OpnTick:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR.w                       ; pad1 edges
    and #$1000.w                           ; START only
    beq +
    jmp TitleEnter
+   inc.w IN_TICK
    sep #$20
    .ACCU 8
    lda.w IN_FX
    beq OT_end                             ; NONE: still, no anim
    cmp #$06.b
    beq OT_fade
    ; M7 zoom family: entry glide ticks 0..32, exit dive ticks 128+
    rep #$20
    .ACCU 16
    lda.w IN_TICK
    cmp #33.w
    bcs OT_noin
    lda.w IN_M7HS
    clc
    adc.w IN_M7DHI
    sta.w IN_M7HS
    lda.w IN_M7DS
    clc
    adc.w IN_M7DDI
    sta.w IN_M7DS
    jmp OT_end
OT_noin:
    cmp #128.w
    bcc OT_end
    lda.w IN_M7HS
    clc
    adc.w IN_M7DHO
    sta.w IN_M7HS
    lda.w IN_M7DS
    clc
    adc.w IN_M7DDO
    sta.w IN_M7DS
    jmp OT_end
OT_fade:
    rep #$20
    .ACCU 16
    lda.w IN_TICK
    cmp #128.w
    bcs OT_end
    and #$0003.w
    bne OT_end
    jsr InFadeStep
OT_end:
    rep #$20
    .ACCU 16
    lda.w IN_SCR
    and #$00FF.w
    cmp #15.w
    bne +
    lda.w IN_TICK
    cmp #(IN_FRAMES+2).w
    bra ++
+   lda.w IN_TICK
    cmp #IN_FRAMES.w
++ 
    bcc OT_stay
    lda #0
    sta.w IN_TICK
    sep #$20
    .ACCU 8
    lda.w IN_SCR
    inc a
    sta.w IN_SCR
    cmp #IN_COUNT.b
    bcs OT_over
    jsr InLoad
OT_stay:
    rts
OT_over:
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l INIDISP                          ; blank before the handoff so no
    ;                                      ;   stale-M7 frame flashes up
    jmp TitleEnter

; boot-only MSU status screen.  The caller has already run MsuDetect and
; loaded the menu font; this screen is entered only from FightMain.
MsuScreenEnter:
    sep #$20
    .ACCU 8
    lda #0
    jsr MnLoadArt
    jsr MsuCreditsInit
    stz.w MSU_PHASE
    lda #24
    sta.w MSU_LEN
    rep #$20
    .ACCU 16
    lda #60.w
    sta.w S_WAIT
    sep #$20
    .ACCU 8
    lda #$FF.b
    sta.w S_BLINK
    jsr MsuPalette
    jsr MsuDraw
    lda #$81.b
    sta.l $4200
    lda #GS_MSUCHK.b
    sta.b gamestate
    rts

MsuScreenTick:
    sep #$20
    .ACCU 8
    lda.b framecnt
    and #$20.b
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    cmp.w S_BLINK
    beq MST_count
    sta.w S_BLINK
    jsr MsuBlink
MST_count:
    rep #$20
    .ACCU 16
    lda.w S_WAIT
    beq MST_elapsed
    dec.w S_WAIT
    rts
MST_elapsed:
    sep #$20
    .ACCU 8
    lda.w MSU_PHASE
    bne MST_intro
    lda #1
    sta.w MSU_PHASE
    lda.b msuok
    beq MST_unavailable
    lda #SFX_SELECT.b
    sta.b scr6
    lda #27
    sta.w MSU_LEN
    bra MST_play_result
MST_unavailable:
    lda #SFX_BACK.b
    sta.b scr6
    lda #26
    sta.w MSU_LEN
MST_play_result:
    lda.b scr6
    jsr SfxPlay
    rep #$20
    .ACCU 16
    lda #60.w
    sta.w S_WAIT
    sep #$20
    .ACCU 8
    jsr MsuDraw
    rts
MST_intro:
    jmp OpnEnter

; Draw the check text with the same title font and blue prompt palette.
; Six-pixel spacing keeps the longest result within the 256px screen.
MsuDraw:
    php
    sep #$20
    .ACCU 8
    lda #0
    sta.l $4200
    jsr MtClear
    rep #$20
    .ACCU 16
    lda #8.w
    sta.b scr0
    sta.b scr1
    lda #MsuCheckText.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:MsuCheckText
    sta.b scr2+2
    lda #$34.b
    sta.b scr4
    jsr MtStrDense
    sep #$20
    .ACCU 8
    lda.w MSU_PHASE
    beq MSD_done
    rep #$20
    .ACCU 16
    lda #152.w
    sta.b scr0
    lda #MsuAvailable.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:MsuAvailable
    sta.b scr2+2
    lda.b msuok
    beq MSD_no
    lda #$36.b                            ; OBJ palette 3: green
    bra MSD_color
MSD_no:
    rep #$20
    .ACCU 16
    lda #MsuUnavailable.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:MsuUnavailable
    sta.b scr2+2
    lda #$38.b                            ; OBJ palette 4: red
MSD_color:
    sta.b scr4
    jsr MtStrDense
MSD_done:
    ; The cursor-like blink matches the title prompt's half-second phase.
    sep #$20
    .ACCU 8
    lda.b framecnt
    and #$20.b
    beq MSD_show
    lda #$F0.b
    bra MSD_sety
MSD_show:
    lda #8.b
MSD_sety:
    sta.b scr5
    lda.w MSU_LEN
    asl a
    asl a
    sta.b scr6
    stz.b scr6+1
    lda.b scr5
    ldx #0
MSD_blinkloop:
    sta.w OAMBUF+1,x
    inx
    inx
    inx
    inx
    cpx.b scr6
    bcc MSD_blinkloop
    lda #$81.b
    sta.l $4200
    plp
    rts

MsuBlink:
    lda.b framecnt
    and #$20.b
    beq MSB_show
    lda #$F0.b
    bra MSB_apply
MSB_show:
    lda #8.b
MSB_apply:
    pha
    lda.w MSU_LEN
    asl a
    asl a
    sta.b scr6
    stz.b scr6+1
    pla
    ldx #0
MSB_loop:
    sta.w OAMBUF+1,x
    inx
    inx
    inx
    inx
    cpx.b scr6
    bcc MSB_loop
    rts

; 8x8 OBJ glyphs with a six-pixel horizontal advance for the status line.
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

MsuCheckText: .db 24,3,8,5,3,11,9,14,7,0,13,19,21,42,28,0,19,21,16,16,15,18,20,38,0
MsuAvailable: .db 3,25,5,19
MsuUnavailable: .db 2,14,15
; The menu/selection/ending tail lives in the free slot above the stage FX
; graphics at $7100, still inside the Fight bank, so the battle code keeps
; room below its 32 KiB limit and every near jsr/jmp continues to resolve.
.IFDEF PVSNESLIB
.ENDS
.ORGA $7100
.SECTION "FightMenuTail" FORCE

; Upload the 2bpp HUD font to BG3 and build the static credit strip on map
; rows 20-27.  Runs under forced blank and leaves the display enabled.
MsuCreditsInit:
    php
    sep #$20
    .ACCU 8
    lda #0
    sta.l $4200
    lda #$80.b
    sta.l $2100
    rep #$30
    .ACCU 16
    .INDEX 16
    ; --- font tiles -> BG3 tile base ---
    lda #HudChr.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:HudChr
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(HudChr_End-HudChr).w
    sta.b I_LEN
    ldx #MSU_CRED_TILEW.w
    jsr MnDma
    ; --- clear the 32x32 map ---
    lda #MSU_CRED_MAPW.w
    sta.l $2116
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l $2115
    rep #$20
    .ACCU 16
    lda #0
    ldx #1024.w
MCI_clear:
    sta.l $2118
    dex
    bne MCI_clear
    ; --- write the eight rows into map rows 20..27 ---
    stz.b scr6
MCI_row:
    rep #$20
    .ACCU 16
    lda.b scr6
    clc
    adc #20.w
    asl a
    asl a
    asl a
    asl a
    asl a
    clc
    adc #MSU_CRED_MAPW.w
    sta.b scr0
    lda.b scr6
    asl a
    tax
    lda.l MsuCreditTab,x
    sta.b scr2
    sep #$20
    .ACCU 8
    ldx.b scr6
    lda.l MsuCreditTabB,x
    sta.b scr2+2
    rep #$20
    .ACCU 16
    ldy #0
    lda.b [scr2],y
    and #$00FF.w
    sta.b scr5
    ; centre the row: col = (32-len)/2
    lda #32.w
    sec
    sbc.b scr5
    lsr a
    clc
    adc.b scr0
    sta.l $2116
    sep #$20
    .ACCU 8
    ldy #1
MCI_chars:
    lda.b [scr2],y
    sta.l $2118
    lda #0
    sta.l $2119
    iny
    dec.b scr5
    bne MCI_chars
    inc.b scr6
    lda.b scr6
    cmp #MSU_CRED_ROWS.b
    bne MCI_row
    ; --- BG3: tiles $7000, map $7800, no scroll ---
    sep #$20
    .ACCU 8
    lda #$07.b
    sta.l $210C                           ; BG34NBA: BG3 tiles $7000
    lda #$78.b
    sta.l $2109                           ; BG3SC: map $7800, 32x32
    lda #0
    sta.l $2111
    sta.l $2111                           ; BG3HOFS
    sta.l $2112
    sta.l $2112                           ; BG3VOFS
    lda #$0F.b
    sta.l $2100
    rep #$20
    .ACCU 16
    plp
    rts

MsuCreditTab:
    .dw MsuCredit0, MsuCredit1, MsuCredit2, MsuCredit3
    .dw MsuCredit4, MsuCredit5, MsuCredit6, MsuCredit7
MsuCreditTabB:
    .db :MsuCredit0, :MsuCredit1, :MsuCredit2, :MsuCredit3
    .db :MsuCredit4, :MsuCredit5, :MsuCredit6, :MsuCredit7

MsuPalette:
    ; OBJ palette 3 light green and palette 4 blood red.
    lda #176.b
    sta.l $2121
    lda #0.b
    sta.l $2122
    sta.l $2122
    lda #$F0.b
    sta.l $2122
    lda #$43.b
    sta.l $2122
    lda #$C8.b
    sta.l $2122
    lda #$22.b
    sta.l $2122
    lda #$F6.b
    sta.l $2122
    lda #$5F.b
    sta.l $2122
    lda #192.b
    sta.l $2121
    lda #0.b
    sta.l $2122
    sta.l $2122
    lda #$14.b
    sta.l $2122
    lda #0.b
    sta.l $2122
    lda #$0A.b
    sta.l $2122
    lda #0.b
    sta.l $2122
    lda #$5F.b
    sta.l $2122
    lda #$08.b
    sta.l $2122
    ; Keep only BG3 credits + OBJ visible over the black CGRAM backdrop.
    lda #0.b
    sta.l $2121
    sta.l $2122
    sta.l $2122
    ; BG3 palette 0: gray outline, light gray shade, white body.
    lda #1.b
    sta.l $2121
    lda #$10.b
    sta.l $2122
    lda #$42.b
    sta.l $2122
    lda #$D6.b
    sta.l $2122
    lda #$5A.b
    sta.l $2122
    lda #$FF.b
    sta.l $2122
    lda #$7F.b
    sta.l $2122
    lda #$14.b
    sta.l $212C
    lda #0.b
    sta.l $212D
    rts


.ENDIF

; called inside FightPresent (pvsnes) / FightVblank (standalone) while
; gs==GS_INTRO, after the engine's own reg writes so the intro regs win
OpnApply:
    sep #$20
    .ACCU 8
    lda.w IN_FX
    beq OpnM1                              ; NONE -> still
    cmp #$06.b
    beq OpnFade                            ; FADE -> regs + palette copy
    jsr InM7Apply
    rep #$20
    .ACCU 16
    rts
OpnM1:
    jsr InM1Regs
    rts
OpnFade:
    jsr InM1Regs
    sep #$20
    .ACCU 8
    lda.w IN_FDIRTY
    beq OpnFdone
    lda #0
    sta.w IN_FDIRTY
    lda #$00.b
    sta.l $2121                            ; CGADD 0
    ldx #0
-   lda.w IN_FCUR,x
    sta.l $2122
    inx
    cpx #$0080.w
    bne -
OpnFdone:
    rep #$20
    .ACCU 16
    rts

; ---- intro tables ----------------------------------------------------------
; fx ids: 0 NONE, 1 ZOOM, 2 BIG, 3 HST, 4 VST, 5 DEEP, 6 FADE, 7 NOUT
InFxTab:
    .db 0,2,0,3, 4,5,1,2, 3,4,5,7, 0,2,3,6

; 12-byte records: hs0 ds0 dhs_in dds_in dhs_out dds_out (.8 fixed point,
; deltas sized to land on $0080 exactly at tick 32 — rest scale is 0.5 so
; the 128x112-texel window covers the whole screen)
InFxParams:
    .dw $0000,$0000,   0,  0,  0,  0      ; NONE
    .dw $00A0,$00A0,  -1, -1,  1,  1      ; ZOOM
    .dw $0180,$0180,  -8, -8,  8,  8      ; BIG
    .dw $0300,$0080, -20,  0, 20,  0      ; HST
    .dw $0080,$0300,   0,-20,  0, 20      ; VST
    .dw $0040,$0040,   2,  2, -2, -2      ; DEEP
    .dw $0000,$0000,   0,  0,  0,  0      ; FADE
    .dw $00A0,$00A0,  -1, -1,  0,  0      ; NOUT

InM1Chr:
    .dw i0s_chr, 0, i2s_chr, 0
    .dw 0,0,0,0, 0,0,0,0, i12s_chr, 0, 0, i15_chr
InM1Map:
    .dw i0s_map, 0, i2s_map, 0
    .dw 0,0,0,0, 0,0,0,0, i12s_map, 0, 0, i15_map
InM1Pal:
    .dw i0s_pal, 0, i2s_pal, 0
    .dw 0,0,0,0, 0,0,0,0, i12s_pal, 0, 0, i15_pal
InM1Len:
    .dw (i0s_chr_end-i0s_chr), 0, (i2s_chr_end-i2s_chr), 0
    .dw 0,0,0,0, 0,0,0,0
    .dw (i12s_chr_end-i12s_chr), 0, 0, (i15_chr_end-i15_chr)
InM1ChrB:
    .db :i0s_chr, 0, :i2s_chr, 0
    .db 0,0,0,0, 0,0,0,0, :i12s_chr, 0, 0, :i15_chr
InM1MapB:
    .db :i0s_map, 0, :i2s_map, 0
    .db 0,0,0,0, 0,0,0,0, :i12s_map, 0, 0, :i15_map
InM1PalB:
    .db :i0s_pal, 0, :i2s_pal, 0
    .db 0,0,0,0, 0,0,0,0, :i12s_pal, 0, 0, :i15_pal
InM7Pak:
    .dw 0, im7_1, 0, im7_3
    .dw im7_4, im7_5, im7_6, im7_7
    .dw im7_8, im7_9, im7_10, im7_11
    .dw 0, im7_13, im7_14, 0
InM7PakB:
    .db 0, :im7_1, 0, :im7_3
    .db :im7_4, :im7_5, :im7_6, :im7_7
    .db :im7_8, :im7_9, :im7_10, :im7_11
    .db 0, :im7_13, :im7_14, 0
InM7Pal:
    .dw 0, im7p_1, 0, im7p_3
    .dw im7p_4, im7p_5, im7p_6, im7p_7
    .dw im7p_8, im7p_9, im7p_10, im7p_11
    .dw 0, im7p_13, im7p_14, 0
InM7PalB:
    .db 0, :im7p_1, 0, :im7p_3
    .db :im7p_4, :im7p_5, :im7p_6, :im7p_7
    .db :im7p_8, :im7p_9, :im7p_10, :im7p_11
    .db 0, :im7p_13, :im7p_14, 0

; =====================================================================
;  menu / title / select
; =====================================================================

; I_SRC = far src, X = dst VRAM word, I_LEN = bytes.
; CPU copy (mode-1 word writes) -- a GPDMA burst here lost data under Mesen2:
; the channel-5 transfers landed as garbage/missing while the identical CPU
; loop used by the intro (InVCopy) is reliable on every emulator.
; Call under forced blank.
MnDma:
    phx
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l $2115                           ; inc on high write
    rep #$20
    .ACCU 16
    pla                                   ; A = dst
    sta.l $2116                           ; dst word addr
    ldy #0
-   lda.b [I_SRC],y
    sta.l $2118                           ; 16-bit: fills $2118/$2119 pair
    iny
    iny
    cpy.b I_LEN
    bne -
    rts

; I_LEN bytes from [I_SRC] -> CGRAM at color X (CPU copy; pals are small)
MnCgRam:
    sep #$20
    .ACCU 8
    txa
    sta.l $2121
    ldy #0
-   lda.b [I_SRC],y
    sta.l $2122
    iny
    cpy.b I_LEN
    bne -
    rep #$20
    .ACCU 16
    rts

; A8 = which screen (0 title / 1 modes).  Force-blank upload:
; banded BG palettes, 32x32 map at word $1800, 4bpp tiles at word $4000,
; OBJ font + cursor at word $3000, menu Mode-1 regs, display on.
MnLoadArt:
    php
    sep #$20
    .ACCU 8
    sta.w M_WHICH
    stz.w M_WHICH+1                       ; high byte must be 0 for ldx.w loads
    lda #0
    sta.l $4200                           ; NMI off while we repack VRAM
    lda #$80.b
    sta.l $2100                           ; force blank
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w M_WHICH
    and #$00FF.w
    asl a
    tax
    stx.w I_EC                            ; which*2 for the .dw tables
    ; --- art palettes: band b -> colors 1+b*16 (30 bytes each) ---
    lda.l MnPalTab,x
    sta.b I_SRC
    sep #$20
    .ACCU 8
    ldx.w M_WHICH
    lda.l MnPalTabB,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #0
    sta.w I_ROWS                          ; band counter
MnPalLoop:
    lda #30.w
    sta.b I_LEN
    lda.w I_ROWS
    asl a
    asl a
    asl a
    asl a                                 ; b*16
    inc a                                 ; +1: color 0 stays transparent
    tax
    jsr MnCgRam
    rep #$20
    .ACCU 16
    lda.b I_SRC
    clc
    adc #30.w
    sta.b I_SRC
    inc.w I_ROWS
    lda.w I_ROWS
    cmp #4.w
    bcc MnPalLoop
    ; --- OBJ palettes: pal0 white text, pal1 yellow text/brackets ---
    lda #MnObjPal.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:MnObjPal
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #64.w                             ; palettes 0-1 (white, gold)
    sta.b I_LEN
    ldx #128.w                            ; OBJ pal base
    jsr MnCgRam
    ; OBJ palette 2 for the title prompt: light-blue body, blue shade,
    ; white highlight. Inline writes avoid growing the full menu asset bank.
    sep #$20
    .ACCU 8
    lda #160.b
    sta.l $2121
    lda #$00.b
    sta.l $2122
    sta.l $2122
    lda #$02.b
    sta.l $2122
    lda #$72.b
    sta.l $2122
    lda #$83.b
    sta.l $2122
    lda #$55.b
    sta.l $2122
    lda #$FF.b
    sta.l $2122
    lda #$FF.b                            ; restore the previous white highlight
    sta.l $2122
    ; --- 32x32 map -> word $1800 (28 rows) ---
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l MnMapTab,x
    sta.b I_SRC
    sep #$20
    .ACCU 8
    ldx.w M_WHICH
    lda.l MnMapTabB,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #1792.w
    sta.b I_LEN
    ldx #MENU_MAPW.w
    jsr MnDma
    ; wipe map rows 28-31 so stale cells can't peek through
    lda #(MENU_MAPW + 28*32).w
    sta.l $2116
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l $2115
    lda #0
    ldx #256.w                            ; 128 words
-   sta.l $2118
    sta.l $2119
    dex
    bne -
    ; --- tiles -> word $4000 ---
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l MnTileTab,x
    sta.b I_SRC
    lda.l MnTileLen,x
    sta.b I_LEN
    sep #$20
    .ACCU 8
    ldx.w M_WHICH
    lda.l MnTileTabB,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    ldx #MENU_TILEW.w
    jsr MnDma
    ; --- OBJ font (45 x 4bpp) at table0 idx 0 + brackets at idx 60 ---
    lda #MenuFont.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:MenuFont
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(MenuFont_End-MenuFont).w
    sta.b I_LEN
    ldx #MENU_OBJW.w
    jsr MnDma
    lda #CurTiles.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:CurTiles
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(CurTiles_End-CurTiles).w
    sta.b I_LEN
    ldx #(MENU_OBJW + CUR_TILE*16).w      ; 16 words per 4bpp tile
    jsr MnDma
    ; --- menu Mode-1 regs: BG1 art + OBJ ---
    sep #$20
    .ACCU 8
    lda #$01.b
    sta.l $2105                           ; BGMODE 1
    lda #$18.b
    sta.l $2107                           ; BG1SC: map word $1800, 32x32
    lda #$04.b
    sta.l $210B                           ; BG12NBA: BG1 tiles word $4000
    lda #$01.b
    sta.l $2101                           ; OBSEL: 8x8, table0 word $2000
    lda #$11.b
    sta.l $212C                           ; TM = BG1 + OBJ
    lda #0
    sta.l $212D
    lda #0
    sta.l $210D
    lda #0
    sta.l $210D                           ; BG1HOFS 0
    lda #0
    sta.l $210E
    lda #0
    sta.l $210E                           ; BG1VOFS 0
    lda #$0F.b
    sta.l $2100
    lda #$81.b
    sta.l $4200                           ; NMI + autojoy back on
    plp
    rts

; ---- sprite text helpers ------------------------------------------------
; clear the whole OAM shadow (128 cells y=$F0, hi table zero)
MtClear:
    rep #$20
    .ACCU 16
    lda #$F0F0.w
    ldx #0
-   sta.w OAMBUF,x
    inx
    inx
    cpx #512.w
    bne -
    ldx #0
    txa
-   sta.w OAMHI,x
    inx
    inx
    cpx #32.w
    bne -
    stz.b oamtop
    rts

; draw one len-prefixed string as 8x8 sprite cells.
; scr0.b = x px, scr1.b = y px, scr2 = far ptr to {len, tiles...},
; scr4.b = OBJ attr byte
MtStr:
    rep #$20
    .ACCU 16
    ldx.b oamtop
    ldy #0
    sep #$20
    .ACCU 8
    lda.b [scr2],y                        ; len
    sta.b scr5
    iny
-   lda.b scr0
    sta.w OAMBUF,x
    lda.b scr1
    sta.w OAMBUF+1,x
    lda.b [scr2],y
    sta.w OAMBUF+2,x                      ; tile = charset index
    lda.b scr4
    sta.w OAMBUF+3,x
    lda.b scr0
    clc
    adc #8.b
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

; one sprite cell: scr0.b=x, scr1.b=y, scr3.b=tile, scr4.b=attr
MtCell:
    rep #$20
    .ACCU 16
    ldx.b oamtop
    sep #$20
    .ACCU 8
    lda.b scr0
    sta.w OAMBUF,x
    lda.b scr1
    sta.w OAMBUF+1,x
    lda.b scr3
    sta.w OAMBUF+2,x
    lda.b scr4
    sta.w OAMBUF+3,x
    rep #$20
    .ACCU 16
    inx
    inx
    inx
    inx
    stx.b oamtop
    rts

; ---- screens --------------------------------------------------------------

; title screen: art + blinking PRESS START; START -> menu; ~22s idle
; replays the intro (matches the source attract loop)
TitleEnter:
    jsr VoiceQueueClear                  ; a fight quote must not follow us
    sep #$20                             ;   here; the title song load owns
    .ACCU 8                              ;   the SPC key-off below
    ; ShakeScroll runs from vblank in every gamestate and recomputes BG1HOFS
    ; from FP+F_X/camx.  A CPU fight (attract demo) that cuts to the intro
    ; leaves those set, so this screen used to inherit the last stage pan and
    ; the title art appeared half a screen off.  Drop the camera and the
    ; fighters' world positions before the art load resets the PPU regs.
    stz.b camx
    stz.b camx+1
    stz.b shaketmr
    rep #$20
    .ACCU 16
    stz.w FP+F_X
    stz.w FP+F_X+1
    stz.w FP+F_X+FP2OFS
    stz.w FP+F_X+FP2OFS+1
    sep #$20
    .ACCU 8
    lda #0
    jsr MnLoadArt
    jsr MtClear
    jsr TitleSprites
    sep #$20
    .ACCU 8
    lda #0
    sta.w S_WAIT
    lda #0
    sta.w S_WAIT+1
    lda #0
    sta.w S_BLINK
    stz.b nextflag
    stz.b framecnt
    stz FP+F_DMAREQ                       ; kill stale sprite uploads
    stz FP+F_DMAREQ+FP2OFS
    lda #SONG_CIPHERB.b
    jsr MusPlaySong
    ; Opening-to-title setup is synchronous and may outlast the START press.
    ; Consume edges but keep the held state so a still-held START cannot
    ; register a second press; it must be released before it counts again.
    jsr ConsumePadEdges
    stz.b gamestate                       ; gs 0 after song upload
    rts

; draw the PRESS START row (11 cells at oamtop 0..43)
TitleSprites:
    php
    sep #$20
    .ACCU 8
    lda #0
    sta.l $4200                           ; NMI off: lib ISR clobbers DP scratch
    rep #$20
    .ACCU 16
    lda #80.w
    sta.b scr0
    lda #136.w
    sta.b scr1
    lda #StrStart.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:StrStart
    sta.b scr2+2
    lda #$34.b                            ; prio3, OBJ pal2: blue text + shaded blue
    sta.b scr4
    jsr MtStr
    ; one compact credit row sits in the black strip directly below the
    ; baked-in SNK CORP OF AMERICA 1998 line.
    rep #$20
    .ACCU 16
    lda #10.w
    sta.b scr0
    lda #194.w
    sta.b scr1
    lda #TitleCredit2.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda #:TitleCredit2
    sta.b scr2+2
    lda #$34.b
    sta.b scr4
    jsr MtStr
    sep #$20
    .ACCU 8
    lda #$81.b
    sta.l $4200
    plp
    rts

; real title (gs 0 + nextflag 0); intermission/banner paths (nextflag
; 1/2) keep the old TitleTick behaviour
TitleTickNew:
    sep #$20
    .ACCU 8
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR.w                      ; pad1 edges
    sta.b scr0
    and #(JOY_ST|JOY_A|JOY_B).w
    beq TTN_nostrt
    sep #$20
    .ACCU 8
    lda #SFX_SELECT.b
    jsr SfxPlay
    jmp MenuEnter
TTN_nostrt:
    lda.b scr0                            ; any edge resets the idle timer
    bne TTN_reset
    rep #$20
    .ACCU 16
    inc.w S_WAIT                          ; one complete 16-bit tick per frame
    lda.w S_WAIT
    cmp #1330.w
    bcc TTN_wait_valid
    beq TTN_idle_done
    ; Scratch may contain an old/uninitialized value after a warm reset.
    ; Do not interpret values beyond the deadline as elapsed idle time.
    stz.w S_WAIT
    bra TTN_blink
TTN_wait_valid:
    ; Let Cipher Beta's 1329-frame sequence finish before restarting it.
    bra TTN_blink
TTN_idle_done:
    sep #$20
    .ACCU 8
    jmp DemoEnter
TTN_reset:
    rep #$20
    .ACCU 16
    stz.w S_WAIT
TTN_blink:
    ; blink at ~1 Hz: framecnt bit5 flips the text row on/off
    sep #$20
    .ACCU 8
    lda.b framecnt
    and #$20.b
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a                                 ; 0/1
    cmp.w S_BLINK
    beq TTN_out
    sta.w S_BLINK
    ldx #0                                ; toggle y on the 11 cells
-   lda.w OAMBUF+1,x
    cmp #$F0.b
    beq +
    lda #$F0.b                            ; hide
    bra ++
+   lda #136.b                            ; show at y=136
++  sta.w OAMBUF+1,x
    inx
    inx
    inx
    inx
    cpx #44.w
    bne -
TTN_out:
    rts

; ---- attract demo: title idle -> random CPU vs CPU bout -> opening intro ---
; The idle title used to cut straight to OpnEnter.  It now runs one exhibition
; fight first: both pads are AI-driven, the pair and the stage are re-rolled at
; random, and the deadline is enforced from MainLoop so a long entrance never
; stretches it.  When a fighter wins (KO or time-over), the KO fall is allowed
; to play and the demo then cuts to the opening intro just like the deadline.
; Without a valid .msu only RomFlags=1 fighters are eligible (their tiles live
; in the ROM), matching the select screen's rule and avoiding streamed garbage
; on the attract fight.
.DEFINE DEMO_FRAMES 1800                ; 30 s at 60 frames/second
.DEFINE DEMO_KOHOLD 60                  ; let the KO fall play before the reroll

DemoEnter:
    sep #$20
    .ACCU 8
    lda #1
    sta.w DM_ON
    rep #$20
    .ACCU 16
    lda #DEMO_FRAMES.w
    sta.w DM_TICK
    sep #$20
    .ACCU 8
    bra DemoSetup

; KO during the demo: let the fall play briefly, then a winner sends the demo
; to the opening intro (a draw rerolls).  The deadline clock itself lives in
; MainLoop and keeps running until OpnEnter.
DemoRestart:
    sep #$20
    .ACCU 8
DemoSetup:
    stz.b pausecnt
    stz.b shaketmr
    stz.b nextflag
    stz.b wins1
    stz.b wins2
    stz.w G_MODE                          ; free versus: random stage per bout
    stz.w FUS_VALID                       ; fresh meters for the exhibition
    lda #1
    sta.b roundno
    jsr DemoPickBoth
    lda #1
    sta.b cpu1                            ; both sides driven by the AI
    sta.b cpu2
    jsr StartFight
    rts

; sel1/sel2 <- two random eligible fighters.
DemoPickBoth:
    php
    sep #$20
    .ACCU 8
    jsr DemoPickChar
    sta.b sel1
    jsr DemoPickChar
    cmp.b sel1
    bne +
    jsr DemoPickChar                      ; avoid a mirror when the pool allows
+   sta.b sel2
    plp
    rts

; A <- random CpuPool char id.  With MSU-1 absent, skip every fighter whose
; CHR is streamed (RomFlags=0); the bounded scan falls back to Kyo, which is
; ROM-resident in every build.
DemoPickChar:
    php
    sep #$30
    .ACCU 8
    .INDEX 8
    ldy #0
DPC_try:
    lda.b rng
    inc.b rng
    eor.b framecnt
    jsr ModPool
    tax
    lda.l CpuPool,x
    sta.b scr0
    lda.b msuok
    bne DPC_ok
    ldx.b scr0
    lda.l RomFlags,x
    bne DPC_ok
    iny
    cpy #NPOOL.b
    bcc DPC_try
    lda #0                                ; fallback: Kyo
    sta.b scr0
DPC_ok:
    lda.b scr0
    plp
    rts

; mode menu ---------------------------------------------------------------
MenuEnter:
    lda #1
    jsr MnLoadArt
    lda #0
    sta.w M_ITEM
    jsl MenuDraw
    ; Screen loads can span frames while START is held. Consume edges but
    ; keep the held state so a still-held START cannot fabricate a press.
    jsr ConsumePadEdges
    lda #GS_MENU.b
    sta.b gamestate
    rts

; redraw: cleared OAM + bracket pair on the current item
; ---- MSU-1 gated rows -----------------------------------------------------
; Team Play (2) and Team VS (3) stream their character sprites from the
; .msu file, so they are dead options when MsuDetect found no MSU-1.  The
; cursor steps over them instead of stopping there (no denial sound).
; Forward: 1 -> 4 (EXIT).   Backward: 4 -> 1, 2 -> 1 (SINGLE VS).
MenuSkipLocked:
    sep #$20
    .ACCU 8
    lda.b msuok
    bne MSK_done
    lda.w M_ITEM
    cmp #2
    bcc MSK_done
    cmp #4
    bcs MSK_done
    lda #4
    sta.w M_ITEM
MSK_done:
    rep #$20
    .ACCU 16
    rts

MenuSkipLockedUp:
    sep #$20
    .ACCU 8
    lda.b msuok
    bne MSKU_done
    lda.w M_ITEM
    cmp #2
    bcc MSKU_done
    cmp #4
    bcs MSKU_done
    lda #1
    sta.w M_ITEM
MSKU_done:
    rep #$20
    .ACCU 16
    rts

MenuTick:
    rep #$30
    .ACCU 16
    .INDEX 16                            ; comparisons below use 16-bit X
    lda FP+F_JOYPR.w
    sta.b scr0
    and #JOY_UP.w
    beq MT_noup
    sep #$20
    .ACCU 8
    lda.w M_ITEM
    dec a
    bpl MT_up_step
    lda #7
MT_up_step:
    sta.w M_ITEM
    jsr MenuSkipLockedUp
    jsl MenuDraw
    sep #$20
    .ACCU 8
    lda #SFX_MOVE.b
    jsr SfxPlay
    jmp MT_done
MT_noup:
    rep #$20
    .ACCU 16
    lda.b scr0
    and #JOY_DN.w
    beq MT_nodir
    sep #$20
    .ACCU 8
    lda.w M_ITEM
    inc a
    cmp #8
    bcc MT_down_step
    lda #0
MT_down_step:
    sta.w M_ITEM
    jsr MenuSkipLocked
    jsl MenuDraw
    sep #$20
    .ACCU 8
    lda #SFX_MOVE.b
    jsr SfxPlay
    jmp MT_done
MT_nodir:
    rep #$20
    .ACCU 16
    lda.b scr0
    and #(JOY_ST|JOY_A).w
    beq MT_tryb
    sep #$20
    .ACCU 8
    rep #$20
    .ACCU 16
    lda.w M_ITEM
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    cpx #7.w
    beq MT_exititem
    cpx #6.w
    beq MT_options
    lda.l MenuItemTab,x
    bra MT_itemready
MT_exititem:
    lda #7
MT_itemready:
    cmp #7                                ; EXIT -> title
    beq MT_exit
    cmp #2                                ; Team Play / Team VS stream team
    bcc MT_allowed                        ;   sprites from the MSU-1 file,
    cmp #4                                ;   so they stay unreachable (and
    bcs MT_allowed                        ;   skipped by the cursor) without
    pha                                   ;   the MSU-1 data.  SURVIVOR and
    lda.b msuok                           ;   PRACTICE only use the ROM roster
    bne MT_allowed_pla                    ;   when MSU-1 is absent.
    pla
    jsr MenuSkipLocked
    jsl MenuDraw
    jmp MT_done
MT_allowed_pla:
    pla
MT_allowed:
    sta.w S_MODE                          ; 0 = single, 1 = versus
    lda #SFX_SELECT.b
    jsr SfxPlay                           ; confirm uses the menu's select tone
    jmp MenuToSelect
MT_exit:
    lda #SFX_BACK.b
    jsr SfxPlay
    jmp TitleEnter
MT_options:
    lda #SFX_SELECT.b
    jsr SfxPlay
    jsl OptionsEnter
    jmp MT_done
MT_tryb:
    rep #$20
    .ACCU 16
    lda.b scr0
    and #JOY_B.w
    beq MT_done
    sep #$20
    .ACCU 8
    lda #SFX_BACK.b
    jsr SfxPlay
    jmp TitleEnter
MT_done:
    rts

; ---------------------------------------------------------------------------
; OPTIONS submenu: LEVEL 1..8 / LANGUAGE / SOUND TEST / EXIT.
; Drawn with the menu OBJ font over the title art; the mode menu's baked
; OPTIONS row (row 22) opens it.
; ---------------------------------------------------------------------------
; Thin far-call wrappers for the options code in bank 64.
; The drawing helpers leave A=16; preserve the options caller's widths.
OptCall_MtClear:          php
                          jsr MtClear
                          plp
                          rtl
OptCall_MtStrDense:       php
                          jsr MtStrDense
                          plp
                          rtl
OptCall_MtCell:           php
                          jsr MtCell
                          plp
                          rtl
OptCall_MnLoadArt:        php
                          jsr MnLoadArt
                          plp
                          rtl
OptCall_SfxPlay:          jsr SfxPlay
                          rtl
OptCall_MusPlaySong:      jsr MusPlaySong
                          rtl
OptCall_ConsumePadEdges:  jsr ConsumePadEdges
                          rtl

; Open the same selection screen used after a match. Restore the fight
; PPU layout and HUD font, since menu art uses both VRAM regions.
MenuToSelect:
    sep #$20
    .ACCU 8
    lda.w S_MODE                          ; ids are the baked mode-menu rows:
    jsr CampReset
    lda.w S_MODE                          ;   0 play, 1 vs, 2 team play,
    cmp #1                                ;   3 team vs, 4 survivor,
    beq MTS_single_vs                     ;   5 practice
    cmp #2
    beq MTS_team
    cmp #3
    beq MTS_team_vs
    cmp #4
    beq MTS_survivor
    cmp #5
    beq MTS_practice
    lda #1                                ; Single Play campaign
    bra MTS_store
MTS_single_vs:
    stz.w G_MODE                          ; free-play single versus
    bra MTS_done
MTS_team:
    lda #2
    bra MTS_store
MTS_team_vs:
    lda #3
    bra MTS_store
MTS_survivor:
    lda #4
    bra MTS_store
MTS_practice:
    lda #5
MTS_store:
    sta.w G_MODE
MTS_done:
    lda #0
    sta.b sel1
    lda #1
    sta.b sel2
    stz.b lock1                         ; select starts unlocked on both
    stz.b lock2                         ;   sides
    stz.b cpu1                          ; P1 is human in every mode
    lda.w G_MODE
    beq MTS_both_human                  ; Single VS has no CPU side
    cmp #3
    beq MTS_both_human                  ; Team VS has no CPU side
    lda #1                              ; Campaign P2 may join with START
    sta.b cpu2
    bra MTS_cpu_ready
MTS_both_human:
    stz.b cpu2
MTS_cpu_ready:
    sep #$10
    .INDEX 8
    lda.b framecnt
    clc
    adc.b rframe
-   cmp #NPOOL.b                        ; common CPUs come from CpuPool
    bcc ++
    sec
    sbc #NPOOL.b
    bra -
++  tax
    lda.l CpuPool,x
    sta.b sel2
    lda.b msuok
    bne +                               ; MSU-1: every pool char is legal
    ldx.b sel2
    lda.l RomFlags,x
    bne +
    inc.b rframe                        ; reroll an MSU-only opener
    bra MTS_cpu_ready
+   rep #$10
    .INDEX 16
    stz.b nextflag
    lda #SONG_KOF.b
    jsr MusPlaySong
    jsr PpuInit
    jsr LoadStaticGfx                   ; HUD font + sparks (menu art used
    jsr StagePick                       ;   the same VRAM); reload a stage
    jsr ShowSelect                      ;   backdrop, then char select (gs 5)
    sep #$20                            ; ShowSelect returns in acc16
    .ACCU 8
    lda #5
    sta.b gamestate
    rts

; ============================================================================
;  endings (gs 8): two still sequences reusing InVCopy/InCgRam/InM1Regs.
;  Screens 0-4 = ending1, 5-10 = ending2 (kof select theme). START skips.
; ============================================================================
; Load ending screen E_SCR (A=8 on entry keeps index in I_EA). Mirrors
; InLM1 without the i15 fade / m7 paths.
EndLoad:
    sep #$20
    .ACCU 8
    php
    lda #0
    sta.l $4200
    lda #$80.b
    sta.l $2100
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w E_SCR
    and #$00FF.w
    sta.b I_EA
    asl a
    sta.w I_EC
    sep #$20
    .ACCU 8
    ldx.b I_EA                            ; chr far pointer
    lda.l EndChrTabB,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l EndChrTab,x
    sta.b I_SRC
    lda.l EndChrLen,x
    sta.b I_LEN
    ldx #$2000.w
    jsr InVCopy
    sep #$20                              ; map, 2048B
    .ACCU 8
    ldx.b I_EA
    lda.l EndMPBTab,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l EndMapTab,x
    sta.b I_SRC
    lda #2048.w
    sta.b I_LEN
    ldx #$1800.w
    jsr InVCopy
    sep #$20                              ; 4-band palette at CGRAM 0
    .ACCU 8
    ldx.b I_EA
    lda.l EndMPBTab,x
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    ldx.w I_EC
    lda.l EndPalTab,x
    sta.b I_SRC
    lda #128.w
    sta.b I_LEN
    ldx #0
    jsr InCgRam
    jsr InFadeInit                        ; arm white->art fade (I_SRC = pal)
    lda.w E_BLACKIN                       ; boss hand-off: fade ending1 in
    and #$00FF.w                          ;   from black instead of white
    bne EL_black
    lda.w E_SCR                           ; montage cards fade in from
    and #$00FF.w                          ;   black, not white: re-seat
    cmp #END_PFIRST.w                     ;   IN_FCUR + CGRAM row 0 so the
    bcc EL_regs                           ;   rapid art->black->art reads
    cmp #END_PLAST.w                      ;   clean (no white strobe)
    bcs EL_regs
EL_black:
    stz.w E_BLACKIN
    ldx #0
    txa
-   sta.w IN_FCUR,x
    inx
    inx
    cpx #$0080.w
    bne -
    sep #$20                              ; display is still force-blanked,
    .ACCU 8                               ;   so push black over the white
    lda #$00.b                            ;   row InFadeInit just wrote
    sta.l $2121
    ldx #$0040.w
-   sta.l $2122
    sta.l $2122
    dex
    bne -
    rep #$20
    .ACCU 16
EL_regs:
    jsr InM1Regs
    sep #$20
    .ACCU 8
    lda #$06.b                            ; FADE fx id -> OpnFade flush
    sta.w IN_FX
    stz.w E_FADE
    rep #$20
    .ACCU 16
    stz.w IN_TICK                         ; fade clock reset
    jmp InShow                            ; display on + NMI re-arm + plp

; Entered via jmp from the match-over title tick on a campaign clear.
EndEnter:
    jsr VoiceQueueClear                  ; endings replace the fight audio
    .ACCU 8
    lda #0
    sta.l NMITIMEN
    lda #ENGINE_DB.b
    pha
    plb
    lda #0
    sta.w E_SCR
    jsr EndLoad
    sep #$20
    .ACCU 8
    lda #SONG_LDANCE.b                    ; ending1 theme
    jsr MusPlaySong
    sep #$20
    .ACCU 8
    lda #GS_END.b
    sta.b gamestate
    rep #$20
    .ACCU 16
    lda #END_HOLD.w
    sta.w E_TICK
    sep #$20
    .ACCU 8
    jmp MainLoop

EndTick:
    rep #$20
    .ACCU 16
    inc.w IN_TICK                         ; fade clock for this screen
    lda FP+F_JOYPR.w
    and #JOY_ST.w
    bne ET_adv                            ; START skips the current screen
    lda.w E_TICK
    dec a
    sta.w E_TICK
    beq ET_adv
    sta.w I_EC                            ; scratch: remaining ticks
    lda.w E_SCR                           ; pick this screen's fade-out
    and #$00FF.w                          ;   window (montage = tight)
    cmp #END_PFIRST.w
    bcc +
    cmp #END_PLAST.w
    bcs +
    lda #END_PFOUT.w
    bra ++
+   lda #END_FOUT.w                       ; last ~2s: arm the black target once
++  cmp.w I_EC
    bcs ET_fadeout                        ; E_TICK <= window -> fade-out arm
    bra ET_step                           ; E_TICK > window -> hold window
ET_fadeout:
    sep #$20
    .ACCU 8
    lda.w E_FADE
    bne ET_steplab
    lda #1
    sta.w E_FADE
    rep #$20
    .ACCU 16
    ldx #0
    txa
-   sta.w IN_FTGT,x                       ; fade-out: walk IN_FCUR to black
    inx
    inx
    cpx #$0080.w
    bne -
ET_steplab:
    rep #$20
    .ACCU 16
ET_step:
    lda.w E_SCR                           ; montage cards step the fade
    and #$00FF.w                          ;   twice per frame (~16-frame
    cmp #END_PFIRST.w                     ;   fades inside the 60-frame
    bcc +                                 ;   slot); normal screens keep
    cmp #END_PLAST.w                      ;   the 1-step/4-frames pace
    bcs +
    jsr InFadeStep
    jsr InFadeStep
    rts
+   lda.w IN_TICK
    and #$0003.w
    bne +
    jsr InFadeStep                        ; 1 step every 4 frames (~124 ticks)
+   rts
ET_adv:
    sep #$20
    .ACCU 8
    lda.w E_SCR
    inc a
    sta.w E_SCR
    cmp #END_COUNT.b
    bcc ++
    jsr CampReset                         ; clear campaign/team state
    jmp TitleEnter                        ; -> gs 0, "PRESS START"
++  cmp #5
    bne +
    lda #SONG_SUNSET.b                    ; ending2 theme
    jsr MusPlaySong
    sep #$20
    .ACCU 8
    lda.w E_SCR
+   jsr EndLoad                           ; returns in plp'd width (acc16)
    rep #$20
    .ACCU 16
    lda.w E_SCR                           ; montage cards get a 60-frame
    and #$00FF.w                          ;   slot; everything else 300
    cmp #END_PFIRST.w
    bcc +
    cmp #END_PLAST.w
    bcs +
    lda #END_PHOLD.w
    bra ++
+   lda #END_HOLD.w
++  sta.w E_TICK
    rts

; ============================================================================
;  SURVIVOR ending (gs 10)
;  13 stills streamed from kof98-snes.msu.  130 s / 13 = 10 s per still;
;  the last still gets 15 s.  Fades are fast (2 palette steps/frame); the
;  final still fades in at 1 step/frame.  Afterwards returns to the title.
; ============================================================================
.INCLUDE "gen_fight/survival_msu_defs.inc"

SvEndEnter:
    jsr VoiceQueueClear                  ; survival stills replace the fight
    .ACCU 8
    lda #0
    sta.l NMITIMEN
    lda #ENGINE_DB.b
    pha
    plb
    lda.b msuok
    beq SV_fallback
    stz.w E_SCR
    jsr SvEndLoad
    sep #$20
    .ACCU 8
    lda #SONG_CRYSTAL.b
    jsr MusPlaySong
    sep #$20
    .ACCU 8
    lda #GS_SVEND.b
    sta.b gamestate
    rep #$20
    .ACCU 16
    lda #SV_HOLD.w
    sta.w E_TICK
    sep #$20
    .ACCU 8
    jmp MainLoop
SV_fallback:
    jmp EndEnter                          ; no MSU-1: use the normal ending

; A(16) = VRAM word address, X(16) = byte count.  The MSU-1 data port
; advances its own 4 GB pointer.  CPU-copy in 16-bit VRAM writes: the ending
; loads under forced blank, so the extra ~0.3 s per still is invisible and
; this avoids any DMA/mode-1 B-bus quirks.
SvDmaVram:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    sta.l VMADDL
    txa
    lsr a
    sta.b scr4
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l VMAIN
SVD_loop:
    lda.l MSU_DATA
    sta.b scr5
    lda.l MSU_DATA
    sta.b scr5+1
    rep #$20
    .ACCU 16
    lda.b scr5
    sta.l $2118
    dec.b scr4
    sep #$20
    .ACCU 8
    bne SVD_loop
    plp
    rts

; Load E_SCR from the MSU-1 file and arm the fade.  Returns via InShow's
; plp/rts, exactly like EndLoad.
SvEndLoad:
    sep #$20
    .ACCU 8
    php
    lda #0
    sta.l $4200
    lda #$80.b
    sta.l $2100
    rep #$30
    .ACCU 16
    .INDEX 16
    lda #SurvivalEndOfs
    sta.b lptr
    sep #$20
    .ACCU 8
    lda #:SurvivalEndOfs
    sta.b lptr+2
    rep #$20
    .ACCU 16
    lda.w E_SCR
    and #$00FF.w
    asl a
    asl a
    tay
    sep #$20
    .ACCU 8
    lda [lptr],y
    sta.l MSU_STAT
    iny
    lda [lptr],y
    sta.l MSU_DATA
    iny
    lda [lptr],y
    sta.l $2002
    iny
    lda [lptr],y
    sta.l $2003
    ldx #$FFFF.w
SVL_wait:
    lda.l MSU_STAT
    bpl SVL_ready
    dex
    bne SVL_wait
SVL_ready:
    lda.l MSU_DATA                       ; 8-byte block header
    sta.b scr0
    lda.l MSU_DATA
    sta.b scr0+1
    lda.l MSU_DATA
    sta.b scr1
    lda.l MSU_DATA
    sta.b scr1+1
    lda.l MSU_DATA
    sta.b scr2
    lda.l MSU_DATA
    sta.b scr2+1
    lda.l MSU_DATA
    lda.l MSU_DATA
    rep #$20
    .ACCU 16
    lda #$2000.w
    ldx scr0
    jsr SvDmaVram
    rep #$20
    .ACCU 16
    lda #$1800.w
    ldx scr1
    jsr SvDmaVram
    sep #$20                              ; palette -> IN_FTGT
    .ACCU 8
    rep #$10
    .INDEX 16
    ldx #0
-   lda.l MSU_DATA
    sta.w IN_FTGT,x
    inx
    cpx #128.w
    bne -
    rep #$20
    .ACCU 16
    lda #IN_FTGT
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #$7E.b
    sta.b I_SRC+2
    jsr InFadeInit
    jsr InM1Regs
    sep #$20
    .ACCU 8
    lda #$06.b
    sta.w IN_FX
    stz.w E_FADE
    rep #$20
    .ACCU 16
    stz.w IN_TICK
    sep #$20
    .ACCU 8
    lda.w E_SCR
    cmp #(SURVIVAL_END_COUNT-1).b
    beq +
    lda #16.b                             ; 2 steps/frame: ~16 frames
    bra ++
+   lda #31.b                             ; last still: 1 step/frame
++  sta.w SV_FIN
    jmp InShow

SvEndTick:
    rep #$20
    .ACCU 16
    sep #$20
    .ACCU 8
    lda.w SV_FIN
    beq SVE_timer
    dec a
    sta.w SV_FIN
    lda.w E_SCR
    cmp #(SURVIVAL_END_COUNT-1).b
    beq SVE_fin_last
    jsr InFadeStep
    jsr InFadeStep
    bra SVE_timer
SVE_fin_last:
    jsr InFadeStep
SVE_timer:
    rep #$20
    .ACCU 16
    lda.w E_TICK
    dec a
    sta.w E_TICK
    beq SVE_advance
    cmp #SV_FOUT.w
    bcs SVE_hold
    sep #$20
    .ACCU 8
    lda.w E_FADE
    bne +
    lda #1
    sta.w E_FADE
    rep #$20
    .ACCU 16
    ldx #0
    txa
-   sta.w IN_FTGT,x                       ; fade-out target: black
    inx
    inx
    cpx #$0080.w
    bne -
+   jsr InFadeStep
    jsr InFadeStep
SVE_hold:
    rep #$20
    .ACCU 16
    rts
SVE_advance:
    sep #$20
    .ACCU 8
    lda.w E_SCR
    inc a
    sta.w E_SCR
    cmp #SURVIVAL_END_COUNT.b
    bcc +
    jsr CampReset
    jmp TitleEnter
+   jsr SvEndLoad
    sep #$20
    .ACCU 8
    lda.w E_SCR
    cmp #(SURVIVAL_END_COUNT-1).b
    beq ++
    rep #$20
    .ACCU 16
    lda #SV_HOLD.w
    sta.w E_TICK
    bra +++
++  rep #$20
    .ACCU 16
    lda #SV_LAST_HOLD.w
    sta.w E_TICK
+++ sep #$20
    .ACCU 8
    rts

; ---- attract-demo helpers (FightMenuTail: same bank, near calls) ----------
; MainLoop calls this once per frame while the demo runs.  Zeroing the clock
; cuts straight into the opening intro.
DemoClock:
    sep #$20
    .ACCU 8
    lda.w DM_ON
    beq DC_out
    ; START or A on either pad leaves the exhibition immediately and returns
    ; to PRESS START.  MainLoop calls this before the gamestate tick, so these
    ; are still the real pad edges -- AiDrive overwrites them later.
    rep #$20
    .ACCU 16
    lda.w FP+F_JOYPR
    ora.w FP+F_JOYPR+FP2OFS
    and #(JOY_ST|JOY_A).w
    bne DC_skip
    dec.w DM_TICK
    bne +
    sep #$20
    .ACCU 8
    stz.w DM_ON
    jmp OpnEnter
+   sep #$20
    .ACCU 8
DC_out:
    rts
DC_skip:
    sep #$20
    .ACCU 8
    stz.w DM_ON
    jmp TitleEnter

; Tail of KoTick: after the KO fall has played, leave the exhibition.  A
; decided round (roundwin 1/2) returns to the opening intro; a draw keeps the
; old reroll behaviour.  DM_TICK still runs in MainLoop as the deadline.
DemoKoTick:
    sep #$20
    .ACCU 8
    lda.w DM_ON
    beq DK_out
    lda.b kotimer
    cmp #(KO_TIME-DEMO_KOHOLD)
    bcs DK_out
    lda.b roundwin
    bne DK_winner
    jmp DemoRestart
DK_winner:
    stz.w DM_ON
    jmp OpnEnter
DK_out:
    rts

; A -> A mod NPOOL, acc8 in/out.
ModPool:
-   cmp #NPOOL.b
    bcc +
    sec
    sbc #NPOOL.b
    bra -
+   rts

; A -> A mod NSTAGES, acc8 in/out.
ModStg:
-   cmp #NSTAGES.b
    bcc +
    sbc #NSTAGES.b
    bra -
+   rts

; ---- clamped horizontal movement -----------------------------------------
; A(16) = signed 8.8 delta, X = fighter offset.  Adds the delta to F_X and
; saturates at the stage bounds.  A plain 16-bit add wraps when a cornered
; fighter is pushed past the wall (24 - 25 px = $FFFF); ClampX then read the
; wrapped value as past the far wall and teleported the victim to the
; opposite corner.  The carry/borrow flags tell which way the add left the
; stage: a positive delta that carries, or a negative delta that does not,
; wrapped and is clamped to the near wall.  X is preserved.
AddXClamped:
    rep #$20
    .ACCU 16
    sta xdelta
    lda FP+F_X,x
    clc
    adc xdelta
    sta FP+F_X,x
    bcs AX_high_wrap
    lda xdelta
    bmi AX_low                             ; negative delta borrowed past 0
    lda FP+F_X,x                           ; normal positive step: high clamp
    cmp #STAGE_R<<8.w
    bcc AX_done
AX_high:
    lda #STAGE_R<<8.w
    sta FP+F_X,x
    bra AX_done
AX_high_wrap:                              ; carry out of bit 15
    lda xdelta
    bmi AX_done                            ; negative delta: no borrow, in range
    bra AX_high                            ; positive delta wrapped past 65535
AX_low:
    lda #STAGE_L<<8.w
    sta FP+F_X,x
AX_done:
    rts

; ---- stage-bound X clamp -------------------------------------------------
; Shared by every state handler; lives here (same CPU bank) so the battle
; section stays under its 32 KiB limit.
ClampX:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_X,x
    cmp #STAGE_L<<8.w
    bcs +
    lda #STAGE_L<<8.w
+   cmp #STAGE_R<<8.w
    bcc ++
    lda #STAGE_R<<8.w
++  sta FP+F_X,x
    rts

; ---- VelSet-driven move velocity -----------------------------------------
; X = fofs on entry; returns with X = fofs, acc16.  FlagsTab bit12 marks a
; move whose CNS VelSet (ActTab op5) owns F_VX.  Every other attack state
; pins it to zero so the fighter does not drift out of a neutral pose.
PinVXUnlessVelSet:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    sta scr4
    ldy #CH_FLAGS
    ldx #boxp
    jsr CharPtr
    ldy scr4
    lda [boxp],y
    and #$1000.w
    bne +
    ldx fofs
    stz FP+F_VX,x
    rts
+   ldx fofs
    rts

; ---- KO knockdown helpers ------------------------------------------------
; The melee HitCheck path sends a finishing blow through HO_ko, but HP can
; also reach zero from a projectile or a scripted TargetLifeAdd.  Those used
; to leave the victim in S_HIT (or an air state) that recovered into S_STAND,
; so the defeated fighter stood through the whole KO banner.  These helpers
; put a zero-HP fighter in the KO lie pose and keep it there.  They live in
; the tail because the battle section is at its 32 KiB limit.

; fofs = victim, acc16.  Enter the KO lie state without touching velocity
; (safe while the body is still falling).
KO_DownState:
    rep #$20
    .ACCU 16
    lda #S_DOWN.w
    jsr EnterState
    ldx fofs
    lda #LIEDOWN.w
    sta FP+F_HTIMER,x
    rts

; fofs = victim, acc16.  Finishing-blow entry: cap the pushback, keep at
; least the minimum upward launch, then enter the KO lie state.
KO_ForceDown:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_VY,x
    cmp #KOVY.w
    bmi +
    lda #KOVY.w
    sta FP+F_VY,x
+   lda FP+F_VX,x
    bmi KOFD_left
    cmp #KOVXMAX.w
    bcc KOFD_down
    lda #KOVXMAX.w
    bra KOFD_store
KOFD_left:
    cmp #-KOVXMAX.w
    bpl KOFD_down
    lda #-KOVXMAX.w
KOFD_store:
    sta FP+F_VX,x
KOFD_down:
    jmp KO_DownState

; X = fighter offset during the KO banner.  Safety net: any zero-HP fighter
; that is not already down (or owned by a scripted throw chain) is parked in
; the lie pose.  S_LOSE is the time-over pose, which deliberately stands.
KoHoldDown:
    rep #$20
    .ACCU 16
    lda FP+F_HP,x
    bne KHD_out
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_DOWN.w
    beq KHD_out
    cmp #S_LOSE.w
    beq KHD_out
    cmp #S_VSHAKE.w                       ; 70-77 victim/throw chain: its own
    bcc KHD_go                            ;   script ends in a down state
    cmp #(S_VTHROW+1).w
    bcc KHD_out
KHD_go:
    stx fofs
    jmp KO_DownState
KHD_out:
    rts
