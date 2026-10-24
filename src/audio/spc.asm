; SNES fighting engine SPC700 driver.
;
; The IPL loader places this image at ARAM $0200.  The driver owns voices 6
; and 7 and plays pre-encoded BRR one-shots selected by a small command port:
;   APUIO2 = voice[7] | (rolling sequence[1:0] << 5) | SFX id[4:0].
; The packed token is atomic across the CPU/APU clock boundary.  The CPU waits
; for APUIO0 to return to 0.

.MEMORYMAP
    SLOTSIZE $10000
    DEFAULTSLOT 0
    SLOT 0 $0000
.ENDME

.ROMBANKSIZE $10000
.ROMBANKS 1

.DEFINE APUIO0      $F4
.DEFINE APUIO1      $F5
.DEFINE APUIO2      $F6
.DEFINE APUIO3      $F7
.DEFINE DSPADDR     $F2
.DEFINE DSPDATA     $F3
.DEFINE TIMER0      $FA
.DEFINE COUNTER0    $FD
.DEFINE CONTROL     $F1

.DEFINE CMD_SFX     2

; BGM event opcodes (shared with the generated song stream).
.DEFINE OP_REST     $80
.DEFINE OP_INST     $81
.DEFINE OP_VOL      $82
.DEFINE OP_PAN      $83
.DEFINE OP_LOOP     $FE
.DEFINE OP_END      $FF

.INCLUDE "gen_audio/spc_ids.inc"

.ENUM $00
    cmd_arg     db
    vbit        db
    srcn        db
    vol         db
    lastseq     db
    ; music sequencer state: voices 0-5, 60 Hz timer0 ticks
    ch_wait     ds 6
    ch_dur      ds 6
    ch_vol      ds 6
    ch_inst     ds 6
    ch_pan      ds 6
    ch_op       ds 6
    ch_arg      ds 6
    ch_plo      ds 6
    ch_phi      ds 6
    ch_slo      ds 6
    ch_shi      ds 6
    playing     db
    ch          db
    kon_bits    db
    koff_bits   db
    ptr_lo      db
    ptr_hi      db
    tmp0        db
    tmp1        db
    tmp2        db
    tmp3        db
.ENDE

.BANK 0 SLOT 0
.ORGA $0200
.SECTION "SpcDriver" FORCE

SpcStart:
    CLRP
    MOV     X, #$EF
    MOV     SP, X
    ; Echo the IPL kick immediately; the 65816 loader waits for this value.
    MOV     A, APUIO0
    MOV     APUIO0, A
    CALL    !DspInit
    MOV     A, #133               ; 8000/133 ~= 60.15 Hz sequencer tick
    MOV     TIMER0, A
    MOV     A, #$01               ; timer0 on, IPL ROM unmapped
    MOV     CONTROL, A
    MOV     APUIO0, #$00
    MOV     APUIO1, #$00
    MOV     APUIO2, #$00
    MOV     APUIO3, #$00
    MOV     playing, #$00
    MOV     A, COUNTER0           ; drain any tick accumulated during init
    MOV     A, APUIO2               ; consume whatever the IPL left behind so
    MOV     lastseq, A              ; only real CPU dispatches trigger below

MainLoop:
    ; APUIO2 atomically carries id + rolling sequence.  A changed token is a
    ; complete event, including repeated plays of the same id; no second port
    ; can still contain data from the preceding event.
    MOV     A, APUIO2
    CMP     A, lastseq
    BEQ     NoCmd
    MOV     lastseq, A
    AND     A, #$1F
    MOV     cmd_arg, A
    MOV     APUIO0, #CMD_SFX         ; command echo while it is processed
    CMP     A, #SPC_MUS_PLAY
    BNE     NotPlay
    CALL    !StartSong
    BRA     CmdAck
NotPlay:
    CMP     A, #SPC_MUS_STOP
    BNE     NotStop
    MOV     playing, #$00
    MOV     A, #$3F               ; key off the six music voices only
    MOV     Y, #$5C
    CALL    !DspW
    BRA     CmdAck
NotStop:
    MOV     A, cmd_arg
    CALL    !PlaySfx
    BRA     CmdAck
CmdAck:
    MOV     APUIO0, #$00
NoCmd:
    MOV     A, COUNTER0
    BEQ     MainLoop
    MOV     tmp3, A
TickOne:
    CALL    !TickMusic
    DBNZ    tmp3, TickOne
    BRA     MainLoop

; cmd_arg = generated SFX id.  Voice 6 owns movement/character/announcer
; sounds; voice 7 owns contact sounds.  Class-pinning is intentional: a hit,
; guard, landing or wall impact must never re-key the swing/voice that caused
; it, allowing the attack and contact samples to overlap.
PlaySfx:
    MOV     A, cmd_arg
    CMP     A, #SFX_COUNT
    BCC     SfxIdOk
    RET
SfxIdOk:
    MOV     A, lastseq
    AND     A, #$80
    BNE     SfxVoice7

    ; Voice 6: registers $60-$67, KON bit $40.
SfxVoice6:
    MOV     Y, #$60
    MOV     A, #$70
    CALL    !DspW
    MOV     Y, #$61
    CALL    !DspW
    MOV     Y, #$62              ; pitch lo
    MOV     A, #$00
    CALL    !DspW
    MOV     Y, #$63              ; pitch hi: all clips are 8 kHz ($0400)
    MOV     A, #$04
    CALL    !DspW
    MOV     Y, #$64              ; SRCN
    MOV     A, lastseq
    AND     A, #$1F
    CALL    !DspW
    MOV     Y, #$65              ; ADSR1/ADSR2 off: GAIN one-shot envelope
    MOV     A, #$00
    CALL    !DspW
    MOV     Y, #$66
    CALL    !DspW
    MOV     Y, #$67
    MOV     A, #$7F
    CALL    !DspW
    BRA     SfxKon

    ; Voice 7: registers $70-$77, KON bit $80.
SfxVoice7:
    MOV     Y, #$70
    MOV     A, #$70
    CALL    !DspW
    MOV     Y, #$71
    CALL    !DspW
    MOV     Y, #$72
    MOV     A, #$00
    CALL    !DspW
    MOV     Y, #$73
    MOV     A, #$04
    CALL    !DspW
    MOV     Y, #$74
    MOV     A, lastseq
    AND     A, #$1F
    CALL    !DspW
    MOV     Y, #$75
    MOV     A, #$00
    CALL    !DspW
    MOV     Y, #$76
    CALL    !DspW
    MOV     Y, #$77
    MOV     A, #$7F
    CALL    !DspW
SfxKon:
    MOV     A, #$FF             ; clear ENDX latches so KON is not dropped
    MOV     Y, #$7C
    CALL    !DspW
    ; Derive the key bit from the atomic command token at the point of use.
    ; Direct-page command scratch is not stable across the music sequencer's
    ; DSP calls, which previously reduced this write to KON=0.
    MOV     A, lastseq
    AND     A, #$80
    BNE     SfxKonVoice7
    MOV     A, #$40
    BRA     SfxKonWrite
SfxKonVoice7:
    MOV     A, #$80
SfxKonWrite:
    MOV     Y, #$4C
    CALL    !DspW
    CALL    !DspWait
    MOV     A, #$00             ; release the KON latch
    MOV     Y, #$4C
    CALL    !DspW
    MOV     Y, #$5C             ; KOFF must receive zero, not the KON bit
    CALL    !DspW
    CALL    !DspWait
    MOV     A, lastseq          ; report the opened envelope on APUIO1 so the
    AND     A, #$80             ; CPU can tell a live key-on from a dropped one
    BNE     SfxEnvR7
    MOV     Y, #$68             ; voice 6 ENVX
    BRA     SfxEnvRd
SfxEnvR7:
    MOV     Y, #$78             ; voice 7 ENVX
SfxEnvRd:
    CALL    !DspR
    MOV     APUIO1, A
    MOV     A, lastseq          ; echo the consumed token (voice|seq|id) so the
    MOV     APUIO3, A           ; CPU can tell this exact dispatch completed
    RET

DspInit:
    MOV     A, #$60               ; mute + echo off, without reset bit
    MOV     Y, #$6C
    CALL    !DspW
    MOV     A, #$00               ; noise/pmon/echo off
    MOV     Y, #$3D
    CALL    !DspW
    MOV     Y, #$2D
    CALL    !DspW
    MOV     Y, #$4D
    CALL    !DspW
    MOV     Y, #$7D               ; EDL=0
    CALL    !DspW
    MOV     A, #$0F               ; sample directory page $0F00
    MOV     Y, #$5D
    CALL    !DspW
    MOV     A, #$58               ; conservative master volume headroom
    MOV     Y, #$0C
    CALL    !DspW
    MOV     Y, #$1C
    CALL    !DspW
    MOV     A, #$FF
    MOV     Y, #$5C               ; KOFF all voices
    CALL    !DspW
    CALL    !DspWait
    MOV     A, #$00               ; release the KOFF latch: while a KOFF bit
    MOV     Y, #$5C               ; stays set the DSP holds that voice keyed
    CALL    !DspW                 ; off every cycle and later KONs are lost
    MOV     A, #$FF
    MOV     Y, #$7C               ; clear stale ENDX flags
    CALL    !DspW
    MOV     A, #$00               ; unmute DSP
    MOV     Y, #$6C
    CALL    !DspW
    RET

DspWait:
    MOV     Y, #$14
DspWaitLoop:
    DBNZ    Y, DspWaitLoop
    RET

; A = value, Y = DSP register.
DspW:
    MOV     DSPADDR, Y
    MOV     X, A
    MOV     Y, #$10
DspWWait:
    DBNZ    Y, DspWWait
    MOV     A, X
    MOV     DSPDATA, A
    MOV     Y, #$10
DspWWait2:
    DBNZ    Y, DspWWait2
    RET

; Y = DSP register, returns A = value.
DspR:
    MOV     DSPADDR, Y
    MOV     Y, #$10
DspRWait:
    DBNZ    Y, DspRWait
    MOV     A, DSPDATA
    RET

; ---------------------------------------------------------------------------
; BGM sequencer: six music voices (0-5) driven by the timer0 60 Hz tick.
; Event stream per channel: [wait][op][arg], op < $80 = note (arg=duration).
; ---------------------------------------------------------------------------
StartSong:
    MOV     playing, #$01
    MOV     A, #$3F               ; silence music voices, keep SFX alive
    MOV     Y, #$5C
    CALL    !DspW
    MOV     ch, #$00
InitCh:
    MOV     X, ch
    MOV     A, #$50
    MOV     ch_vol+X, A
    MOV     A, #$00
    MOV     ch_dur+X, A
    MOV     ch_inst+X, A
    MOV     A, #$02
    MOV     ch_pan+X, A
    ; track offset = word at song+2+ch*2 (song base $DE00)
    MOV     A, ch
    ASL     A
    CLRC
    ADC     A, #$02
    MOV     ptr_lo, A
    MOV     A, #$DE
    ADC     A, #$00
    MOV     ptr_hi, A
    CALL    !ReadPtr
    MOV     tmp0, A             ; offset lo
    CALL    !IncPtr
    CALL    !ReadPtr
    MOV     tmp1, A             ; offset hi
    MOV     A, tmp0
    CLRC
    ADC     A, #$00             ; + song base lo ($00)
    MOV     X, ch
    MOV     ch_plo+X, A
    MOV     ch_slo+X, A
    MOV     A, tmp1
    ADC     A, #$DE             ; + song base hi
    MOV     ch_phi+X, A
    MOV     ch_shi+X, A
    CALL    !FetchCh
    INC     ch
    MOV     A, ch
    CMP     A, #$06
    BNE     InitCh
    RET

TickMusic:
    MOV     A, playing
    BEQ     TickDone
    MOV     kon_bits, #$00
    MOV     koff_bits, #$00
    MOV     ch, #$00
TickCh:
    MOV     X, ch
    MOV     A, ch_dur+X
    BEQ     TickWait
    DEC     A
    MOV     ch_dur+X, A
    BNE     TickWait
    ; note ended: arm the voice's KOFF bit
    MOV     A, #$01
    MOV     Y, ch
ShiftKoff:
    BEQ     StoreKoff
    ASL     A
    DEC     Y
    BRA     ShiftKoff
StoreKoff:
    OR      A, koff_bits
    MOV     koff_bits, A
TickWait:
    MOV     X, ch
    MOV     A, ch_wait+X
    BEQ     NeedApply
    DEC     A
    MOV     ch_wait+X, A
    BNE     NextCh
NeedApply:
    CALL    !ApplyCh
NextCh:
    INC     ch
    MOV     A, ch
    CMP     A, #$06
    BNE     TickCh
    ; Mask retiring bits of voices that key on this same tick: simultaneous
    ; KON+KOFF on a voice drops the key-on on real S-DSPs.
    MOV     A, kon_bits
    EOR     A, #$FF
    AND     A, koff_bits
    BEQ     DoKon
    MOV     Y, #$5C
    CALL    !DspW
DoKon:
    MOV     A, kon_bits
    BEQ     TickDone
    MOV     A, #$FF             ; clear ENDX latches so KON is not dropped
    MOV     Y, #$7C
    CALL    !DspW
    MOV     A, kon_bits
    MOV     Y, #$4C
    CALL    !DspW
    CALL    !DspWait
    MOV     A, #$00             ; release the KON/KOFF latches
    MOV     Y, #$4C
    CALL    !DspW
    MOV     Y, #$5C
    CALL    !DspW
TickDone:
    RET

ApplyCh:
    MOV     X, ch
ApplyLoop:
    MOV     A, ch_wait+X
    BNE     ApplyRet
    MOV     A, ch_op+X
    CMP     A, #OP_LOOP
    BEQ     DoLoop
    CMP     A, #OP_INST
    BEQ     DoInst
    CMP     A, #OP_VOL
    BEQ     DoVol
    CMP     A, #OP_PAN
    BEQ     DoPan
    CMP     A, #OP_REST
    BEQ     DoRest
    CMP     A, #OP_END
    BEQ     DoEnd
    ; note 0-127
    CALL    !VoiceOn
    MOV     X, ch
    MOV     A, ch_arg+X
    MOV     ch_dur+X, A
    CALL    !FetchCh
    RET
DoInst:
    MOV     A, ch_arg+X
    MOV     ch_inst+X, A
    CALL    !FetchCh
    MOV     X, ch
    BRA     ApplyLoop
DoVol:
    MOV     A, ch_arg+X
    MOV     ch_vol+X, A
    CALL    !FetchCh
    MOV     X, ch
    BRA     ApplyLoop
DoPan:
    MOV     A, ch_arg+X
    MOV     ch_pan+X, A
    CALL    !FetchCh
    MOV     X, ch
    BRA     ApplyLoop
DoRest:
    MOV     A, ch_arg+X
    MOV     ch_dur+X, A
    CALL    !FetchCh
    RET
DoEnd:
    CALL    !FetchCh
    MOV     X, ch
    BRA     ApplyLoop
DoLoop:
    MOV     X, ch
    MOV     A, ch_slo+X
    MOV     ch_plo+X, A
    MOV     A, ch_shi+X
    MOV     ch_phi+X, A
    CALL    !FetchCh
    MOV     X, ch
    BRA     ApplyLoop
ApplyRet:
    RET

FetchCh:
    MOV     X, ch
    MOV     A, ch_plo+X
    MOV     ptr_lo, A
    MOV     A, ch_phi+X
    MOV     ptr_hi, A
    CALL    !ReadPtr
    MOV     X, ch
    MOV     ch_wait+X, A
    CALL    !IncPtr
    CALL    !ReadPtr
    MOV     X, ch
    MOV     ch_op+X, A
    CALL    !IncPtr
    CALL    !ReadPtr
    MOV     X, ch
    MOV     ch_arg+X, A
    CALL    !IncPtr
    MOV     X, ch
    MOV     A, ptr_lo
    MOV     ch_plo+X, A
    MOV     A, ptr_hi
    MOV     ch_phi+X, A
    RET

ReadPtr:
    MOV     X, #$00
    MOV     A, [ptr_lo+X]
    RET

IncPtr:
    INC     ptr_lo
    BNE     IncPtrDone
    INC     ptr_hi
IncPtrDone:
    RET

; Start note on music voice `ch`: SRCN=ch_inst, pitch from PitchTab
; (melodic) or PercPTab (inst >= INST_PERC), vol/pan applied.
VoiceOn:
    MOV     A, ch
    ASL     A
    ASL     A
    ASL     A
    ASL     A
    MOV     tmp2, A             ; v*16
    MOV     A, tmp2
    CLRC
    ADC     A, #$04             ; SRCN
    MOV     Y, A
    MOV     X, ch
    MOV     A, ch_inst+X
    CALL    !DspW
    ; ADSR: melodic loops get a soft pluck; percussion uses GAIN one-shot
    MOV     X, ch
    MOV     A, ch_inst+X
    CMP     A, #INST_PERC
    BCS     PercAdsr
    MOV     A, tmp2
    CLRC
    ADC     A, #$05             ; ADSR1
    MOV     Y, A
    MOV     A, #$8F
    CALL    !DspW
    MOV     A, tmp2
    CLRC
    ADC     A, #$06             ; ADSR2
    MOV     Y, A
    MOV     A, #$E8
    CALL    !DspW
    BRA     SetPitch
PercAdsr:
    MOV     A, tmp2
    CLRC
    ADC     A, #$05             ; ADSR1 = 0 -> GAIN mode
    MOV     Y, A
    MOV     A, #$00
    CALL    !DspW
    MOV     A, tmp2
    CLRC
    ADC     A, #$07             ; GAIN
    MOV     Y, A
    MOV     A, #$7F
    CALL    !DspW
SetPitch:
    MOV     X, ch
    MOV     A, ch_inst+X
    CMP     A, #INST_PERC
    BCS     PercPUse
    MOV     A, ch_op+X          ; MIDI note -> DSP pitch
    ASL     A
    MOV     Y, A
    MOV     A, !PitchTab+Y
    MOV     tmp0, A
    INC     Y
    MOV     A, !PitchTab+Y
    MOV     tmp1, A
    BRA     WritePitch
PercPUse:
    SETC
    SBC     A, #INST_PERC       ; per-instrument fixed rate
    ASL     A
    MOV     Y, A
    MOV     A, !PercPTab+Y
    MOV     tmp0, A
    INC     Y
    MOV     A, !PercPTab+Y
    MOV     tmp1, A
WritePitch:
    MOV     A, tmp2
    CLRC
    ADC     A, #$02             ; pitch lo
    MOV     Y, A
    MOV     A, tmp0
    CALL    !DspW
    MOV     A, tmp2
    CLRC
    ADC     A, #$03             ; pitch hi
    MOV     Y, A
    MOV     A, tmp1
    CALL    !DspW
    ; volume L/R with gentle pan separation
    MOV     X, ch
    MOV     A, ch_vol+X
    LSR     A
    MOV     tmp0, A
    MOV     A, ch_pan+X
    CMP     A, #$01
    BEQ     PanLeft
    CMP     A, #$03
    BEQ     PanRight
PanCenter:
    MOV     A, tmp2
    MOV     Y, A                ; VOLL
    MOV     A, tmp0
    CALL    !DspW
    MOV     A, tmp2
    INC     A
    MOV     Y, A                ; VOLR
    MOV     A, tmp0
    CALL    !DspW
    BRA     PanDone
PanLeft:
    MOV     A, tmp2
    MOV     Y, A
    MOV     A, tmp0
    CALL    !DspW
    MOV     A, tmp2
    INC     A
    MOV     Y, A
    MOV     A, tmp0
    LSR     A
    CALL    !DspW
    BRA     PanDone
PanRight:
    MOV     A, tmp2
    MOV     Y, A
    MOV     A, tmp0
    LSR     A
    CALL    !DspW
    MOV     A, tmp2
    INC     A
    MOV     Y, A
    MOV     A, tmp0
    CALL    !DspW
PanDone:
    MOV     A, #$01             ; arm this voice's KON bit
    MOV     Y, ch
KonShift:
    BEQ     KonStore
    ASL     A
    DEC     Y
    BRA     KonShift
KonStore:
    OR      A, kon_bits
    MOV     kon_bits, A
    RET

PitchTab:
    .INCBIN "gen_audio/spc_pitch.bin"

.INCLUDE "gen_audio/spc_perc.inc"
.INCLUDE "gen_audio/spc_tables.inc"
.ENDS

.ORGA $0F00
.SECTION "SpcDir" FORCE
    .INCBIN "gen_audio/spc_dir.bin"
.ENDS

.ORGA $1000
.SECTION "SpcBrr" FORCE
    .INCBIN "gen_audio/spc_brr.bin"
.ENDS

.ORGA $DE00
.SECTION "SpcSong" FORCE
    .INCBIN "gen_audio/spc_song.bin"
.ENDS
