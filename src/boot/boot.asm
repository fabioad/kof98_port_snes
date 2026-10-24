; SNES boot ROM: solid BACKDROP color + mario.mid sequenced by the SPC700
; driver (src/neogeo_spc.asm).  8 MiB Fast ExHiROM, same layout discipline as
; the KOF '98 port: CPU bank $00 code lives in file bank 64 ($40xxxx).

.MEMORYMAP
    SLOTSIZE $10000
    DEFAULTSLOT 0
    SLOT 0 $0000
.ENDME

.ROMBANKSIZE $10000
.ROMBANKS 192

.SNESHEADER
    ID "SNES"
    NAME "SNES BOOT MARIO      "
    FASTROM
    EXHIROM
    CARTRIDGETYPE $00
    ROMSIZE $0D
    SRAMSIZE $00
    COUNTRY $01
    LICENSEECODE $00
    VERSION $00
.ENDSNES

.EMPTYFILL $00

; File bank N is CPU-visible at bank N-$C0 in the $8000-$FFFF window.
.BASE $C0

.DEFINE INIDISP     $2100
.DEFINE CGADD       $2121
.DEFINE CGDATA      $2122
.DEFINE TM          $212C
.DEFINE APUIO0      $2140
.DEFINE APUIO1      $2141
.DEFINE APUIO2      $2142
.DEFINE APUIO3      $2143
.DEFINE NMITIMEN    $4200
.DEFINE MDMAEN      $420B
.DEFINE HDMAEN      $420C

.DEFINE SPC_ENTRY   $0200
.DEFINE CMD_LOAD    4

; Backdrop color comes from the command line: -D BACKDROP_LO=.. -D BACKDROP_HI=..

; Direct-page scratch (WRAM $0010+).
.DEFINE dma_src     $10                 ; 16-bit offset of the song in its bank
.DEFINE dma_bank    $12
.DEFINE dma_len     $13                 ; 16-bit padded upload length
.DEFINE tmp0        $15                 ; 16-bit

.INCLUDE "gen/spc_size.inc"
.INCLUDE "gen_neogeo/spc_songmeta.inc"

.SNESNATIVEVECTOR
    COP    UnusedInterrupt
    BRK    UnusedInterrupt
    ABORT  UnusedInterrupt
    NMI    VblankStub
    IRQ    UnusedInterrupt
.ENDNATIVEVECTOR

.SNESEMUVECTOR
    COP    UnusedInterrupt
    ABORT  UnusedInterrupt
    NMI    UnusedInterrupt
    RESET  Reset
    IRQBRK UnusedInterrupt
.ENDEMUVECTOR

.BANK 64 SLOT 0                          ; CPU bank $00 (file $40xxxx)
.ORGA $8000
.SECTION "Boot" FORCE

Reset:
    sei                                 ; keep this byte first: the boot
    clc                                 ;  verifier checks for SEI at $408000
    xce
    rep #$38
    .ACCU 16
    .INDEX 16
    ldx #$1FFF.w
    txs
    lda #$0000.w
    tcd
    sep #$20
    .ACCU 8

    lda #$8F.b                          ; force blank while CGRAM is written
    sta INIDISP
    stz NMITIMEN
    stz MDMAEN
    stz HDMAEN

    stz CGADD                           ; palette entry 0 = backdrop
    lda #BACKDROP_LO.b
    sta CGDATA
    lda #BACKDROP_HI.b
    sta CGDATA
    stz TM                              ; no layers enabled: pure backdrop
    lda #$0F.b
    sta INIDISP                         ; backdrop color on screen

    jsr SpcUploadDriver
    jsr SpcUploadSong                   ; driver auto-starts after CMD_LOAD

    jml.l FightMain

VblankStub:
    jml.l FightVblank

; IPL ROM transfer of the driver+samples to ARAM $0200 (blargg/libSFX).
SpcUploadDriver:
    php
    sep #$20
    .ACCU 8
    rep #$10
    .INDEX 16
    ldx #$BBAA.w                        ; wait AA BB
SpcWaitIpl:
    cpx APUIO0
    bne SpcWaitIpl
    lda #<SPC_ENTRY
    sta APUIO2
    lda #>SPC_ENTRY
    sta APUIO3
    lda #$CC.b
    sta APUIO1
    sta APUIO0
SpcWaitCc:
    cmp APUIO0
    bne SpcWaitCc
    ldx #0
SpcCopy:
    lda.l SpcBoot,x
    sta APUIO1
    txa
    sta APUIO0
SpcWaitY:
    cmp APUIO0
    bne SpcWaitY
    inx
    cpx #SPC_BOOT_SIZE.w
    bne SpcCopy
    lda #<SPC_ENTRY                     ; execute at $0200
    sta APUIO2
    lda #>SPC_ENTRY
    sta APUIO3
    stz APUIO1
    lda APUIO0
    inc a
    inc a
    bne SpcKick
    inc a
SpcKick:
    sta APUIO0
SpcWaitRun:
    cmp APUIO0
    bne SpcWaitRun
    ldx #0                              ; driver zeroes port0 when idle
SpcWaitReady:
    lda APUIO0
    beq SpcReady
    dex
    bne SpcWaitReady
SpcReady:
    stz APUIO0                          ; drop the IPL kick byte
    plp
    rts

; Upload song_mario.bin through CMD_LOAD; the driver runs StartSong when the
; copy completes, so no PLAY command is needed afterwards.
SpcUploadSong:
    php
    sep #$20
    .ACCU 8
    rep #$10
    .INDEX 16
    rep #$20
    .ACCU 16
    lda #SongMario.w
    sta.b dma_src
    lda #SONG_MARIO_BYTES.w             ; already padded to a multiple of 3
    sta.b dma_len
    sep #$20
    .ACCU 8
    lda #:SongMario.b
    sta.b dma_bank

    lda.b dma_len
    sta APUIO2
    lda.b dma_len+1
    sta APUIO3
    ldx #$FFFF.w
SpcULIdle:
    lda APUIO0
    beq SpcULSend
    dex
    bne SpcULIdle
    plp
    rts
SpcULSend:
    lda.b dma_len                       ; re-assert length with the command,
    sta APUIO2                          ;  idle polls can clobber io2/io3
    lda.b dma_len+1
    sta APUIO3
    lda #CMD_LOAD.b
    sta APUIO0
    ldx #$FFFF.w
SpcULEcho:
    cmp APUIO0
    beq SpcULGo
    dex
    bne SpcULEcho
    plp
    rts
SpcULGo:
    phb
    lda.b dma_bank
    pha
    plb                                 ; DB = song bank for (dma_src),y
    ldy #0
SpcULCopy:
    tya
    sta.b tmp0
    lda (dma_src),y                     ; 3 bytes per handshake group
    sta.l APUIO1
    iny
    lda (dma_src),y
    sta.l APUIO2
    iny
    lda (dma_src),y
    sta.l APUIO3
    iny
    lda.b tmp0
    sta.l APUIO0
    ldx #$FFFF.w
SpcULWait:
    cmp.l APUIO0
    beq SpcULNext
    dex
    bne SpcULWait
    plb
    plp
    rts
SpcULNext:
    rep #$20
    .ACCU 16
    tya
    cmp.b dma_len
    sep #$20
    .ACCU 8
    bcc SpcULCopy
    plb
    ldx #$FFFF.w
SpcULDone:
    lda APUIO0                          ; driver acks with io0=0, song playing
    beq SpcULOk
    dex
    bne SpcULDone
    plp
    rts
SpcULOk:
    stz APUIO0
    plp
    rts

UnusedInterrupt:
    rti

.ENDS

.BANK 65 SLOT 0                          ; CPU bank $01 (file $41xxxx)
.ORGA $8000
.SECTION "SpcBoot" FORCE
SpcBoot: .INCBIN "gen/spc_boot.bin"
.ENDS

.BANK 66 SLOT 0                          ; CPU bank $02 (file $42xxxx)
.ORGA $8000
.SECTION "SongMario" FORCE
SongMario: .INCBIN "gen_neogeo/song_mario.bin"
.ENDS
