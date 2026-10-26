; SNES Fighting Engine (65816) -- fighting engine (65816).
; Mode 1: BG1 = stage tilemap, BG3 = HUD text/lifebars, OBJ = two fighters.
; Sprite tiles stream to VRAM on animation frame changes (one transfer per
; fighter change, synchronized with VBlank).
;
; The standalone build keeps DB at $00 and uses the low-WRAM mirror.  The
; PVSnesLib build keeps DB at $7E and moves the large buffers out of the
; library/compiler low-RAM workspace; hardware registers use long addresses.
; ROM tables (data bank) are read through 24-bit dp pointers (`lda [ptr],y`)
; or `lda.l label,x`. Fighter fields are indexed with X via FP+F_*,x; FP is
; $0300 in the standalone build and $4000 in the PVSnesLib build.

.IFNDEF PVSNESLIB
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

.BASE $C0
.ENDIF

.DEFINE INIDISP     $002100
.DEFINE OBSEL       $002101
.DEFINE OAMADDL     $002102
.DEFINE BGMODE      $002105
.DEFINE BG1SC       $002107
.DEFINE BG3SC       $002109
.DEFINE BG12NBA     $00210B
.DEFINE BG34NBA     $00210C
.DEFINE BG1HOFS     $00210D
.DEFINE BG1VOFS     $00210E
.DEFINE VMAIN       $002115
.DEFINE VMADDL      $002116
.DEFINE VMDATAL     $002118
.DEFINE CGADD       $002121
.DEFINE CGDATA      $002122
.DEFINE TM          $00212C
.DEFINE NMITIMEN    $004200
.DEFINE JOY1L       $004218
.DEFINE JOY2L       $00421A
.DEFINE APUIO0      $002140
.DEFINE APUIO1      $002141
.DEFINE APUIO2      $002142
.DEFINE APUIO3      $002143
.DEFINE DMAP0       $004300
.DEFINE BBAD0       $004301
.DEFINE A1T0L       $004302
.DEFINE A1B0        $004304
.DEFINE DAS0L       $004305
.DEFINE MDMAEN      $00420B

.DEFINE BG1MAP      $4000
.DEFINE BG1CHR      $0000
.DEFINE BG3MAP      $5000               ; BG1's 64x32 map spans $4000-$4FFF
.DEFINE BG3CHR      $2000
.DEFINE P1CHR       $6000
.DEFINE P2CHR       $7000
.DEFINE P2TILEOF    256
.DEFINE PGOF        $0600               ; ping-pong page: +96 OBJ tiles
.DEFINE SPK1CHR     $6C00               ; 64 OBJ tiles for live effect slot 0
.DEFINE SPK2CHR     $7C00               ; 64 OBJ tiles for live effect slot 1
.INCLUDE "gen_fight/runtime_abi.inc"
                                        ; DMACHUNK is shared with Python probes.
                                        ; 1536-byte bursts wipe VRAM during
                                        ; large super frames (the transfer
                                        ; outruns the forced-blank window by
                                        ; a scanline on some cores); 1280
                                        ; keeps the last chunk in the window.

.DEFINE GROUND_Y    190
.DEFINE STAGE_L     24
.DEFINE STAGE_R     232
.DEFINE BODY_SEP    $1800               ; 24 px (8.8): body pushbox width
.DEFINE TEAM_SPAWN_SEP 96               ; newcomer gap on a team member swap
.DEFINE WALKSPD     $0140
.DEFINE RUNSPD      $04A0               ; kfm run.fwd = 4.6 px/tick
.DEFINE DASHSPD     $0480               ; kfm run.back x = -4.5
.DEFINE DASHVY      $FC33               ; kfm run.back y = -3.8 (hop)
.DEFINE JUMPVY      $F79A               ; -8.4 px/tick (kfm velocity.jump.neu y)
.DEFINE HOPVY       $F980               ; -6.5 px/tick for a tapped-up hop
.DEFINE HYPERHOPVY  $F8B0               ; -7.3 px/tick: fast hyper hop
.DEFINE HIGHJUMPVY  $F580               ; -10.5 px/tick for D,U or a run jump
.DEFINE JUMPVXF     $0280               ;  2.5 px/tick (jump.fwd, facing-relative)
.DEFINE JUMPVXB     $028D               ;  2.55 px/tick (jump.back, facing-relative)
.DEFINE HYPERHOPVXF $0340               ; 3.25 px/tick: further than a hop
.DEFINE HYPERHOPVXB $0348               ; 3.28 px/tick: further than a hop
.DEFINE HIGHJUMPVXF $03C0               ; 1.5 * jump.fwd
.DEFINE HIGHJUMPVXB $03D4               ; 1.5 * jump.back (rounded)
.DEFINE GRAV        $0071               ;  0.44 px/tick^2 (kfm yaccel)
.DEFINE VBOUNCEGRAV $005A               ;  0.35 px/tick^2 (state 1028)
.DEFINE KOVY        $FB00               ; -5.0 px/tick: minimum KO upward launch
.DEFINE KOVXMAX     $0400               ;  4.0 px/tick: cap on KO pushback
.DEFINE DOWNFRI     $0020               ;  0.125 px/tick^2 slide friction on floor
.DEFINE LIEDOWN     60                  ; ticks knocked down before get-up
.DEFINE MAXHP       200
.DEFINE BAR_TILES   12
.DEFINE KO_TIME     240
; Victory-quote language selected by the OPTIONS screen.
; 0 = English, 1 = Portuguese (BR), 2 = Spanish, 3 = French.
; Engine RAM.  UI_SFXLOAD lives at $F07E, so every store to that byte must
; be an 8-bit STA: STZ always writes 16 bits and would also clear Q_LANG.
.DEFINE Q_LANG      $F07F

.DEFINE S_STAND     0
.DEFINE S_WALKF     1
.DEFINE S_WALKB     2
.DEFINE S_CROUCH    3
.DEFINE S_JUMP      4
.DEFINE S_PUNCH     5
.DEFINE S_SPUNCH    6
.DEFINE S_KICK      7
.DEFINE S_SKICK     8
.DEFINE S_HIT       9
.DEFINE S_DOWN      10
.DEFINE S_WIN       11
.DEFINE S_CDOWN     12                  ; stand->crouch transition (anim 10)
.DEFINE S_CUP       13                  ; crouch->stand transition (anim 12)
.DEFINE S_JSTART    14                  ; jump takeoff squat (anim 40)
.DEFINE S_JUMPF     15                  ; air, moving forward (anim 42)
.DEFINE S_JUMPB     16                  ; air, moving back (anim 43)
.DEFINE S_LAND      17                  ; touch-down recovery (anim 47)
.DEFINE S_GETUP     18                  ; rise from lying down (anim 5120)
.DEFINE S_CPUNCH    19                  ; crouching light punch  (state 400)
.DEFINE S_CSPUNCH   20                  ; crouching strong punch (state 410)
.DEFINE S_CKICK     21                  ; crouching light kick   (state 430)
.DEFINE S_CSKICK    22                  ; crouching strong kick  (state 440, trip)
.DEFINE S_APUNCH    23                  ; jumping light punch    (state 600)
.DEFINE S_ASPUNCH   24                  ; jumping strong punch   (state 610)
.DEFINE S_AKICK     25                  ; jumping light kick     (state 630)
.DEFINE S_ASKICK    26                  ; jumping strong kick    (state 640)
.DEFINE S_GUARD     27                  ; stand guard hold       (anim 130)
.DEFINE S_CGUARD    28                  ; crouch guard hold      (anim 131)
.DEFINE S_AGUARD    29                  ; air guard / air guard-hit
.DEFINE S_GHIT      30                  ; guard-hit flinch + pushback
.DEFINE S_RUNF      45                  ; run forward  (FF, anim 100)
.DEFINE S_BACKD     46                  ; backdash     (BB, anim 105)
.DEFINE S_TAUNT     47                  ; taunt        (start, anim 195)
.DEFINE S_SPECIAL   48                  ; special moves 48-55 (states 1000+)
.DEFINE S_LASTSP    55
.DEFINE S_FASTSP    56                  ; fast variants 56-59 (-330 power)
.DEFINE S_KNEE      60                  ; Kung Fu Knee family 60-69 (1050+)
.DEFINE S_VSHAKE    70                  ; attacker-owned victim state 1025
.DEFINE S_VFLY      71                  ; HitVelSet flight (1026)
.DEFINE S_VWALL     72                  ; wall freeze / ChangeAnim2 (1027)
.DEFINE S_VBOUNCE   73                  ; self-animation wall bounce (1028)
.DEFINE S_THROW     74                  ; throw attempt HitDef (mugen 800)
.DEFINE S_TSEQ      75                  ; throw bind sequence (810)
.DEFINE S_VHELD     76                  ; bound victim (820)
.DEFINE S_VTHROW    77                  ; thrown victim flight (821)
; ReversalDef counter-grab runtime slots (Geese/Daimon/Heidern/etc.):
; 99/101 = actor follow-up, 100/102 = held opponent.  98 stays Iori's
; Yumebiki second hit; these slots sit outside the classic 0-98 table.
.DEFINE S_CGRAB_HI  99
.DEFINE S_CGRAB_HIV 100
.DEFINE S_CGRAB_LO  101
.DEFINE S_CGRAB_LOV 102
.DEFINE S_BLOCK     78                  ; stand parry stance (1300)
.DEFINE S_BHIT      79                  ; stand blocked freeze (1310)
.DEFINE S_BLOCKC    80                  ; crouch parry stance (1320)
.DEFINE S_BHITC     81                  ; crouch blocked (1330)
.DEFINE S_BLAND     84                  ; air-parry landing (1351)
.DEFINE S_SUPPER    85                  ; Smash Kung Fu Upper (3050)
.DEFINE S_SPOSE     86                  ; upper success pose (3051)
                                        ; 87-89 = Triple Kung Fu Palm slices
.DEFINE S_WPOSE     90                  ; win pose (mugen 181)
.DEFINE S_LOSE      91                  ; time-over lose pose (mugen 170)
.DEFINE S_INTRO     92                  ; intro (mugen 191)
                                        ; 103-106 = ReversalDef counter
.DEFINE S_REVACT    103                 ;   follow-ups (Yamazaki, Kyo,
.DEFINE S_REVACT_LAST 106               ;   Shingo, Billy); dispatched as
                                        ;   ordinary ground specials
.DEFINE S_EXT_LAST 111                  ; 107-111 = imported extended
                                        ;   follow-ups (Blue Mary); treated as
                                        ;   specials by HitOne/AI/survivor
.DEFINE S_EXT_GRAB 109                  ; 109-111 = throw/grab follow-ups:
                                        ;   StVictimHeld keeps the victim
                                        ;   bound while the owner is here
.DEFINE S_DIZZY     11                  ; FUSION dizzy/stun (reuses S_WIN slot)
.DEFINE S_AIRTHROW  44                  ; FUSION air-throw (reuses spare AnimTab slot)

.DEFINE F_X         0
.DEFINE F_Y         2
.DEFINE F_VX        4
.DEFINE F_VY        6
.DEFINE F_STATE     8
.DEFINE F_FRAME     10
.DEFINE F_FTICK     12
.DEFINE F_FACING    14
.DEFINE F_HP        16
.DEFINE F_ANIM      18
.DEFINE F_NFR       20
.DEFINE F_LOOP      21
.DEFINE F_META      22
.DEFINE F_DMAREQ    24                  ; keep in sync with runtime_abi.json
.DEFINE F_DMAPOS    25
.DEFINE F_HITDONE   26
.DEFINE F_TILEPG    27                  ; displayed OBJ tile page: 0 or $60
.DEFINE F_XOFF      28
.DEFINE F_YOFF      29
.DEFINE F_FLAGS     30
.DEFINE F_HIST      31                  ; command ring: next write index 0-15
.DEFINE F_LASTCT    50                  ; tick of last consumed command input
.DEFINE F_JOY       32
.DEFINE F_JOYPR     34
.DEFINE F_ATKBOX    36
.DEFINE F_HURTBOX   38
.DEFINE F_HTIMER    40
.DEFINE F_SLIDE     42                  ; low byte: jump direction; high: jump type
.DEFINE F_CHAR      44
.DEFINE F_TBANK     46                  ; low byte: generated-data bank
.DEFINE F_PSPRID    47                  ; keep in sync with runtime_abi.json
.DEFINE F_PSPRID_H  F_PSPRID+$80        ; high byte in the spare fighter-page tail
; Frame geometry is committed together with the tiles.  The animation keeps
; ticking while a big sprite streams in, so writing F_XOFF/F_YOFF/F_FLAGS
; immediately would draw the *previous* metasprite (F_META) at the next
; frame's offsets -- the pose visibly jumps until the upload finishes.
.DEFINE F_PXOFF     F_PSPRID+$81        ; pending frame xoff/yoff/flags,
.DEFINE F_PYOFF     F_PSPRID+$82        ;   copied to the live bytes by
.DEFINE F_PFLAGS    F_PSPRID+$83        ;   SprDmaP's commit step
.DEFINE F_VMUL      F_PSPRID+$84        ; Q8 VelMul x factor; 0 = inactive
.DEFINE F_POWER     48                  ; word: 0..3000 power meter
.DEFINE F_GRAB      52                  ; bit0 custom victim; bit1 attacker anim source
.DEFINE F_OWNER     53                  ; attacker fighter offset (0/$40)
.DEFINE F_TFLAGS    51                  ; bit0: throw entered via holdfwd
                                        ; bit1: state entered this tick
                                        ; bit2: afterimage trail on
                                        ; bit3: PosFreeze latch
.DEFINE F_HITVX     54                  ; HitVelSet velocity saved at impact
.DEFINE F_HITVY     56
.DEFINE F_HOT       58                  ; ticks of live command input: PushHist
.DEFINE F_MAX       59                  ; FUSION: MAX-mode timer (ticks left)
                                        ;   re-arms on an edge/press; CmdTry
                                        ;   early-outs at 0 (no scan while a
                                        ;   direction is just held)
.DEFINE F_STIME     60                  ; exact ticks since EnterState (word)
.DEFINE F_INVUL     62                  ; NotHitBy ticks left; $FF = whole state
.DEFINE F_PFX       63                  ; PalFX bright-flash ticks remaining
.DEFINE F_LASTSCAN  186                 ; CmdTry: ring head already scanned
.DEFINE F_LASTSTATE 187                 ; CmdTry: state at that scan
.DEFINE ct_cut      $53                 ; CmdTry: ring age cap (frames)
.DEFINE F_PROJDONE  180                 ; spare tail byte; must not alias F_MAX
.DEFINE F_PATKBOX   182                 ; collision geometry queued with tiles
.DEFINE F_PHURTBOX  184
                                        ; F_TFLAGS bit2 = afterimage trail on
                                        ; F_TFLAGS bit3 = PosFreeze latch

; Character descriptor offsets (all pointers are 16-bit in F_TBANK)
.DEFINE CH_SPROFS   0
.DEFINE CH_BOXTAB   2
.DEFINE CH_ANIMTAB  4
.DEFINE CH_ACTIVE   6
.DEFINE CH_DAMAGE   8
.DEFINE CH_HTTIME   10
.DEFINE CH_SLIDE    12
.DEFINE CH_HITVEL   14
.DEFINE CH_BUTTONS  16
.DEFINE CH_OAMATTR  18
.DEFINE CH_CHR      20
.DEFINE CH_CHRBANK  22
.DEFINE CH_CHRFLAG  23                  ; chr source flags: bit0 = MSU-1 file
.DEFINE CH_PAL      24
.DEFINE CH_PALBANK  26
.DEFINE CH_NAME     28
.DEFINE CH_CBTN     30                  ; crouching button->state table
.DEFINE CH_ABTN     32                  ; air button->state table
.DEFINE CH_FLAGS    34                  ; per-state flags (bit0 = knockdown,
                                        ; bit12 = VelSet-driven movement)
.DEFINE CH_GVEL     36                  ; per-state guard pushback table
.DEFINE CH_GDMG     38                  ; per-state chip damage table
.DEFINE CH_CMDTAB   40                  ; command rules (motion,held,nheld,post,st)
.DEFINE CH_MOTTAB   42                  ; motion record pointer table
.DEFINE CH_POSTAB   44                  ; per-state PosAdd timeline pointers
.DEFINE CH_CHAINTAB 46                  ; normal-attack chain/cancel rules
.DEFINE CH_POWTAB   48                  ; per-state power delta table (.dw)
.DEFINE CH_TRANSTAB 50                  ; intra-state ChangeState rules
.DEFINE CH_EVELTAB  52                  ; per-state entry velset (.dw vx,vy)
.DEFINE CH_TARGETTAB 54                 ; HitDef target/victim pause/p1/flags (.db x4)
.DEFINE CH_BINDTAB  56                  ; TargetBind windows per state
.DEFINE CH_ACTTAB   58                  ; elem-gated action table per state
.DEFINE CH_REVTAB   60                  ; parry/reversal windows per state
.DEFINE CH_HITSND   62                  ; per-state HitDef hitsound id
.DEFINE CH_SHAKE    64                  ; per-state HitDef envshake byte
.DEFINE CH_QUOTE    66                  ; victory quote pair table
.DEFINE CH_EXPTAB   68                  ; compiled Explod rows (16B each)
.DEFINE CH_P1PAUSE  70                  ; HitDef pausetime (.db/sid)
.DEFINE CH_PALDIM   72                  ; OBJ pal+3 ghost copy (.dw/.db)
.DEFINE CH_PALHI    76                  ; OBJ pal+5 PalFX flash (.dw/.db + pad)
.DEFINE CH_PROJTAB  80                  ; projectile launch rows (.db x4/sid)
                                        ;   vx.w, dmg.b, hitsnd.b; spawn
                                        ;   timing is the launch anim end
.DEFINE CH_MBANK    82                  ; metasprite data bank (SprOfs entries
                                        ;   point into it; tables stay F_TBANK)
.DEFINE CH_PROJFXTAB 84                 ; per-char projectile animation table
.DEFINE CH_PROJFXCHR 86                 ; compact projectile cells in ProjFxGlobal
.DEFINE CH_CMDLIST   88                 ; PRACTICE command list header
.DEFINE CH_CMDLISTBANK 90               ; 0 = F_TBANK, else explicit bank
.DEFINE CH_CANCELROW 92                 ; 6 strong-normal cancel opens in
                                        ;   the CancelData bank (.db each)
.DEFINE CH_MAXMASK   91                 ; bit0..bit4 = sids 85..89 are MAX/SDM
                                        ;   (byte uses the padding after
                                        ;   CH_CMDLISTBANK; layout unchanged)

.IFDEF PVSNESLIB
.DEFINE ENGINE_DP   $1000
.DEFINE ENGINE_DB   $7E
.DEFINE FP          $4000                ; +ofs: FP1=$4000, FP2=$4040
.DEFINE OAMBUF      $1800                ; private shadow; PVSnesLib owns oamMemory
.DEFINE OAMHI       OAMBUF+512           ; 512-byte low table + 32-byte high table
.DEFINE HUDMAP      $4700
.ELSE
.DEFINE ENGINE_DP   $0000
.DEFINE ENGINE_DB   $00
.DEFINE FP          $0300                ; +ofs: FP1=$0300, FP2=$0330
.DEFINE OAMBUF      $0400
.DEFINE OAMHI       OAMBUF+512
.DEFINE HUDMAP      $0A00
.ENDIF
.DEFINE FP2OFS      $40
.IFDEF PVSNESLIB
.DEFINE OAMC1       $3800
.DEFINE OAMC2       $3A00
.DEFINE OAMC_TMP    $3C00
.DEFINE OAMC_PTR    $3C10
.DEFINE OAMC_START  $3C13
.ENDIF

.DEFINE JOY_B       $8000
.DEFINE JOY_Y       $4000
.DEFINE JOY_ST      $1000
.DEFINE JOY_UP      $0800
.DEFINE JOY_DN      $0400
.DEFINE JOY_LF      $0200
.DEFINE JOY_RT      $0100
.DEFINE JOY_A       $0080
.DEFINE JOY_SE      $2000
.DEFINE JOY_X       $0040
.DEFINE JOY_L       $0020
.DEFINE JOY_R       $0010

.DEFINE scr0        $10
.DEFINE scr1        $12
.DEFINE scr2        $14
.DEFINE scr3        $16
.DEFINE scr4        $18
.DEFINE scr5        $1A
.DEFINE scr6        $34
.DEFINE selcand     $7E7F10             ; select cursor candidate (WRAM, outside DP blast)
.DEFINE selfallback $7E7F11             ; cursor wrapped with no legal cell in direction
.DEFINE qtab        $B0                 ; 3-byte QuoteTab pointer (far)
.DEFINE qrow        $B3                 ; 3-byte second quote row pointer
.DEFINE msuf        $3F                 ; chr src flags for pending sprite
.DEFINE MSU_STAT    $002000             ; MSU-1 status/read-flags reg
.DEFINE MSU_DATA    $002001             ; MSU-1 sequential data byte
; Bytes between the 512-byte-aligned sector and the requested CHR chunk.
; Unused diag word at $543E (MD_RES starts at $5440).
.DEFINE MSU_PREFIX  $543E

; Generated MSU-1 slice constants are used by tables below, so define them
; before those tables are assembled.
.INCLUDE "gen_fight/msu1_bases.inc"
.DEFINE pbase       $36                 ; displayed OBJ tile base for cells
.DEFINE rev_vsid    $37                 ; RevCheck: counter-grab victim sid
.DEFINE rev_bsid    $3E                 ; RevCheck: counter-grab actor sid
.DEFINE sptr        $38                 ; 3-byte spark-anim pointer (tblbank)
.DEFINE sfxtoken    $3B                 ; free byte between sptr and sidx
.DEFINE gotime      $29                 ; READY+GO frames left: IntroTick holds
                                        ;   the round start until it reaches 0
.DEFINE sfxenv      $3D                 ; DSP ENVX sampled after last KON
.DEFINE sidx        $3C                 ; spark slot loop offset
.DEFINE VOICE_BUF   $7E6000             ; MSU-streamed voice sample target

; get-hit AnimTab slots (generated; not real states)
.DEFINE ANIM_HIT_HI 31                     ; stand hit high, base+animtype
.DEFINE ANIM_HIT_LO 34                     ; stand hit low
.DEFINE ANIM_HIT_CR 37                     ; crouch hit
.DEFINE ANIM_HIT_AIR 40                    ; air hit (mugen anim 5030)
.DEFINE ANIM_LIE     41                    ; lying down (mugen anim 5110)
.DEFINE ANIM_GHIT_HI 42                    ; stand guard-hit (mugen anim 150)
.DEFINE ANIM_GHIT_CR 43                    ; crouch guard-hit (151)
.DEFINE ANIM_AGUARD  29                    ; air guard / air guard-hit
.DEFINE ANIM_DIZZY   11                    ; FUSION dizzy pose (mugen 5300)
.DEFINE ANIM_AIRT    23                    ; FUSION air-throw attempt (air punch)
.DEFINE ANIM_TRIP    93                    ; trip fall, ground.type=Trip (5070)
.DEFINE fofs        $1C
.DEFINE vofs        $1E
.DEFINE gamestate   $20
.DEFINE GS_YOULOSE  12                 ; campaign defeat menu (YOU LOSE).  Must
                                        ;   stay distinct from GS_MENU (6):
                                        ;   MainLoop dispatches each to its own
                                        ;   tick, and reusing 6 left YouLoseTick
                                        ;   unreachable (frozen cursor).
.DEFINE GS_BOSS_FADE 13                ; final KO -> black -> ending1
.DEFINE nmiflag     $22
.DEFINE framecnt    $24
.DEFINE WIN_TIMER   $7B                 ; 16-bit winner-screen frame counter
                                        ;   (free pad in the DP $78-$7F tail;
                                        ;   must not alias AI_LEVEL/DIFFICULTY)
.DEFINE xdelta      $7D                    ; AddXClamped scratch (same free pad)
.DEFINE huddirty    $26
.DEFINE stagehold   $27                 ; 1 = flush the rebuilt HUD in StagePick
.DEFINE winvoice    $2F                 ; 1 = defer the winner voice until the
                                        ;   winner module's effects are loaded
.DEFINE kotimer     $28
.DEFINE oamtop      $2A
.DEFINE vbusy       $2C
.DEFINE sfxseq      $30
.DEFINE sfxlast     $31
.DEFINE audiordy    $32
.DEFINE sfxdone     $33                    ; id[4:0] + seq[6:5] + voice[7]
.DEFINE tblbank     $2E
.DEFINE DBGREG      $4600
.DEFINE DBGREG_L    $7E4600
.IFDEF PVSNESLIB
.DEFINE SPARKS      $4200               ; 2 spark/explod slots x 20 bytes
.ELSE
.DEFINE SPARKS      $06B0               ; standalone: free WRAM after GHBUF
.ENDIF
                                        ;   x.w,y.w,animptr.w(tblbank,0=free),
                                        ;   fidx.b,ftim.b,vx.w,vy.w,ay.w,
                                        ;   ttl.b(0=anim end frees),attr.b,
                                        ;   bank.w,guard.b+pad
.DEFINE SPK_ANIM    4                   ; anim record ptr; 0 = slot free
.DEFINE SPK_FIDX    6
.DEFINE SPK_FTIM    7
.DEFINE SPK_VX      8                   ; 8.8 fixed-point velocity/accel
.DEFINE SPK_VY      10
.DEFINE SPK_AY      12
.DEFINE SPK_TTL     14
.DEFINE SPK_ATTR    15
.DEFINE SPK_BANK    16                  ; fighter table bank for projectile clip
.DEFINE SPK_GRD     18                  ; guard mask, H/M/L/A in bits 4-7
.DEFINE SPK_SIZE    20
.IFDEF PVSNESLIB
.DEFINE FX_CACHE    $4230               ; frame pointer cached in each 2 KiB FX page
.DEFINE FX_CACHEBANK $4234              ; ROM bank is part of the cache key
.ELSE
.DEFINE FX_CACHE    $06F0
.DEFINE FX_CACHEBANK $06F4
.ENDIF
.DEFINE CMDHIST_L   $7E4100             ; per-fighter input ring: 16 entries x
                                        ;   3 bytes (dir,btn,tick); P2 at +$40

; PRACTICE command-list submenu state.  PVSnesLib reserves this block in
; fight_bridge.asm; the standalone build keeps it in the free low-WRAM gap
; between the NMI save area and the 2 KiB HUD shadow.
.IFDEF PVSNESLIB
.DEFINE CL_VARS     $4F40
.ELSE
.DEFINE CL_VARS     $0800
.ENDIF
.DEFINE CL_OPEN     CL_VARS+0           ; 1 while the submenu owns the screen
.DEFINE CL_SIDE     CL_VARS+1           ; 0 = P1 list, 1 = P2 list
.DEFINE CL_SEL      CL_VARS+2           ; selected row
.DEFINE CL_TOP      CL_VARS+3           ; first visible row
.DEFINE CL_COUNT    CL_VARS+4           ; rows in the active list
.DEFINE CL_LAST1    CL_VARS+5           ; last move sid each side entered
.DEFINE CL_LAST2    CL_VARS+6
.DEFINE CL_TMP      CL_VARS+7
.DEFINE CL_LASTT1   CL_VARS+8           ; frame stamp (word) for the flash
.DEFINE CL_LASTT2   CL_VARS+10
.DEFINE CL_ROW      CL_VARS+12           ; list loop counter
.DEFINE CL_IDX      CL_VARS+13           ; absolute row index
.DEFINE CL_ROWBASE  CL_VARS+14           ; word: HUDMAP offset of the row
.DEFINE CL_SEEN1    CL_VARS+$10         ; 48 bytes: rows P1 has executed
.DEFINE CL_SEEN2    CL_VARS+$40         ; 48 bytes: rows P2 has executed
.DEFINE JOIN_ACTIVE CL_VARS+$72         ; 1 = select opened by START mid-fight
.DEFINE JOIN_SIDE   CL_VARS+$73         ; 0 = P1 joined, 1 = P2 joined
.DEFINE CL_FROM_PAUSE CL_VARS+$74       ; command list was opened by PAUSE
.DEFINE PZ_SIDE     CL_VARS+$75         ; pad that opened the pause menu
.DEFINE UI_SLOT_SEL CL_VARS+$76         ; effect slots of the UI sounds
.DEFINE UI_SLOT_MOVE CL_VARS+$77
.DEFINE UI_SLOT_BACK CL_VARS+$78
.DEFINE UI_SLOT_WIN CL_VARS+$79          ; winner-screen announcer
.DEFINE UI_SLOT_ROW $7E4FBB             ; word: UiSrc row being reloaded
.DEFINE UI_SLOT_NEW $7E4FBE             ; word: slot returned by spcLoadEffect
                                        ;   (kept clear of ROW's high byte)
; Pause menu (SELECT during a fight): lives in the free tail of the
; PRACTICE command-list block ($4FB0 in the hybrid build, $0870 standalone).
.DEFINE PZ_ON      CL_VARS+$70         ; 1 while the fight is paused
.DEFINE PZ_SEL     CL_VARS+$71         ; 0 = CONTINUE, 1 = EXIT
; YOU LOSE screen (single/team campaign defeat).  The two bytes sit between
; the UI slot list and UI_SLOT_NEW's word, which is safe: the screen does not
; load effects.
.DEFINE YL_SEL     CL_VARS+$7A         ; 0 CONTINUE / 1 SELECT FIGHTER / 2 EXIT
.DEFINE YL_REPICK  CL_VARS+$7D         ; 1 = character select resumes the bout
.DEFINE ct_row      $60                 ; CmdTry scratch: CmdTab row offset
.DEFINE ct_dir      $62                 ; current facing-relative dir nibble
.DEFINE ct_post     $63                 ; current posture bit (S=1 C=2 A=4)
.DEFINE ct_ei       $64                 ; element byte offset into motion rec
.DEFINE ct_j        $65                 ; ring scan cursor (entry index)
.DEFINE ct_scan     $66                 ; entries scanned for current element
.DEFINE ct_ts0      $67                 ; tick of the newest matched element
.DEFINE ct_win      $68                 ; motion window
.DEFINE ct_cancel   $52                 ; 1 = CmdTry is a hit-cancel scan
.DEFINE ct_rel      $6F                 ; released-dir mask for ~X elements
.DEFINE ct_tmp      $69
.DEFINE ct_edir     $6A                 ; ring entry dir/btn/tick under test
.DEFINE ct_ebtn     $6B
.DEFINE ct_ets      $6C
.DEFINE ct_nelem    $6D                 ; motion element count *2
.DEFINE ct_off      $6E
.DEFINE histp       $70                 ; 3-byte ptr to this fighter's ring
.DEFINE pausecnt    $73                 ; global freeze (Pause/SuperPause):
                                        ;   FightTick stalls while nonzero
.DEFINE shaketmr    $74                 ; EnvShake ticks remaining
.DEFINE shakeamp    $75                 ; EnvShake amplitude (px)
.DEFINE rsecs       $76                 ; round timer seconds
.DEFINE rframe      $77                 ; round timer frame counter (0-59)
.DEFINE gk          $78                 ; ghost-slot loop counter (word: $78-79)
.DEFINE wins1       $80                 ; round wins / best-of-3
.DEFINE wins2       $81
.DEFINE roundno     $82                 ; 1..3
.DEFINE roundwin    $83                 ; last round: 0 draw, 1 P1, 2 P2
.DEFINE nextflag    $84                 ; 0 fresh title, 1 intermission,
                                        ;   2 match-over banner
.DEFINE sel1        $85                 ; title char pick: 0 KFM, 1 KYO
.DEFINE sel2        $86
; Combo counters are indexed by fighter offset (0/$40).  Keep them out of
; DP $10C0+ in the hybrid build: campaign/team vars live there, and the old
; $8B/$CB location aliased T_TEAM1[0]/[2] (ComboTick erased the waiting trio).
.IFDEF PVSNESLIB
.DEFINE COMBO_BASE  $4FC0
.ELSE
.DEFINE COMBO_BASE  $0880
.ENDIF
.DEFINE combohit    COMBO_BASE
.DEFINE combotmr    COMBO_BASE+$41
; --- FUSION mechanics (all indexed by fofs: +0 P1, +$40 P2) ----------------
.IFDEF PVSNESLIB
.DEFINE FUSION_BASE $5052              ; free gap before the streaming queue
.ELSE
.DEFINE FUSION_BASE $2200              ; standalone WRAM tail
.ENDIF
.DEFINE FUS_JUGGLE  FUSION_BASE+0      ; word: juggle points left
.DEFINE FUS_DIZZY   FUSION_BASE+2      ; byte: dizzy accumulator
.DEFINE FUS_DIZZYT  FUSION_BASE+3      ; byte: dizzy state timer
.DEFINE FUS_CARRY   FUSION_BASE+4      ; word: meter carried to next member
.DEFINE FUS_SYN     FUSION_BASE+6      ; byte: 0 angry / 1 neutral / 2 happy
.DEFINE FUS_COVER   FUSION_BASE+7      ; byte: cover-attack cooldown
.DEFINE FUS_CTR     FUSION_BASE+8      ; word: current hit is a counter
.DEFINE FUS_FLASH   FUSION_BASE+10     ; byte: COUNTER banner ticks
.DEFINE FUS_VALID   FUSION_BASE+11     ; byte: synergy/carry initialized
.DEFINE FUS_TMP     FUSION_BASE+12     ; word: AddPower scratch
.DEFINE sdmaside    COMBO_BASE+$80    ; sprite-DMA arbiter for the current
                                        ;   vblank: 0 = free, 1 = only P1,
                                        ;   2 = only P2 (set when both sides
                                        ;   stream tiles in the same frame;
                                        ;   reserved but unused combo slot)
.DEFINE lock1       $8E                 ; select-screen confirm latches
.DEFINE lock2       $8F
.DEFINE cpu1        $90                 ; 1 = CPU drives P1 (select toggle)
.DEFINE cpu2        $91                 ; 1 = CPU drives P2 (default)
.DEFINE AI_LEVEL    $10EB               ; 1..9 internal CPU difficulty
.DEFINE DIFFICULTY  $10ED               ; 1..8 Neo-Geo style options level
.DEFINE AI_TIMER1   $10EE               ; per-side action commit timer
.DEFINE AI_TIMER2   $10EF
.DEFINE AI_HOLD1    $10F0               ; 0 idle, 1 back/block, 2 forward
.DEFINE AI_HOLD2    $10F1
.DEFINE AI_SIDE     $10F2               ; 0 = P1, 1 = P2 during AI_one
.DEFINE AI_SCANMODE $10F3               ; move-table filter (0 special, 1 AA...)
.DEFINE AI_CNT      $10F4               ; table header cache
.DEFINE AI_STYLE    $10F5
.DEFINE AI_AGGR     $10F6
.DEFINE AI_DEF      $10F7
.DEFINE AI_SPEC     $10F8
.DEFINE AI_SUPER    $10F9
.DEFINE AI_DIST     $10FA               ; word, pixels
.DEFINE AI_OPPST    $10FC
.DEFINE AI_OPPY     $10FD               ; nonzero when the foe is airborne
.DEFINE AI_OPPATT   $10FE               ; nonzero when the foe is attacking
.DEFINE AI_TMP      $10FF
.DEFINE AI_ZLO      $1100               ; preferred spacing band (px)
.DEFINE AI_ZHI      $1101
.DEFINE AI_AA       $1102               ; profile rates: anti-air, throw,
.DEFINE AI_THROW    $1103               ;   mixup/evade
.DEFINE AI_MIX      $1104
.DEFINE AI_FLAGS    $1105               ; AI_PF_* personality bits
.DEFINE AI_PDIST    $1106               ; word: low = distance, high = guard mask
.DEFINE AI_OPPGRD   $1108               ; foe is guarding
.DEFINE AI_OPPHIT   $1109               ; foe is in hitstun/recovery
.DEFINE AI_OPPDOWN  $110A               ; foe is down/getting up
.IFDEF PVSNESLIB
; Reserved by fight_bridge.asm between the combo counters and streaming queue.
.DEFINE AI_OPPFALL  $5042               ; foe is airborne and falling
.DEFINE AI_JUMP     $5044               ; 2 bytes, per side: jump-in flags
.DEFINE AI_AIRT     $5046               ; 2 bytes, per side: air-attack delay
.DEFINE AI_JUMPCD   $5048               ; 2 bytes, per side: jump-in cooldown
.DEFINE AI_OFFCD    $504A               ; 2 bytes, per side: offense cooldown
.ELSE
.DEFINE AI_OPPFALL  $4E00               ; standalone WRAM, below SURV_LIST
.DEFINE AI_JUMP     $4E02
.DEFINE AI_AIRT     $4E04
.DEFINE AI_JUMPCD   $4E06
.DEFINE AI_OFFCD    $4E08
.ENDIF
.DEFINE AI_J_FWD    $01                 ; AI_JUMP bit0: forward jump-in
.DEFINE AI_J_ATK    $02                 ; AI_JUMP bit1: attack while airborne
.DEFINE AI_F_PROJ   $01                 ; generated AiTab move flags
.DEFINE AI_F_AA     $02
.DEFINE AI_F_RUSH   $04
.DEFINE AI_F_SUPER  $08
.DEFINE AI_F_THROW  $10
.DEFINE AI_F_MAX    $20
.DEFINE AI_PF_PRESSURE $01              ; AiTab personality flags
.DEFINE AI_PF_METER $02
.DEFINE AI_PF_ADAPT $04
.DEFINE AI_PF_ZONER $08
.DEFINE AI_DBG_THREAT DBGREG+120        ; headless AI coverage counters
.DEFINE AI_DBG_BLOCK  DBGREG+121
.DEFINE AI_DBG_SPEC   DBGREG+122
.DEFINE AI_DBG_THROW  DBGREG+123
.DEFINE AI_DBG_PROJ   DBGREG+124
.DEFINE AI_DBG_MAX    DBGREG+125
.DEFINE AI_DBG_PUNISH DBGREG+126
.DEFINE AI_DBG_SUPER  DBGREG+127
.DEFINE AI_DBG_AIR    DBGREG+128        ; jump-in air attack pressed
.DEFINE AI_DBG_BLOW   DBGREG+129        ; CD blowback started
.DEFINE AI_DBG_AA     DBGREG+130        ; anti-air answer fired
.DEFINE AI_DBG_AAF    DBGREG+131        ; anti-air fired on a falling jump-in
.DEFINE AI_DBG_JUMP   DBGREG+132        ; jump-in actually launched
.DEFINE AI_DBG_PBLOCK DBGREG+133        ; projectile blocked instead of dodged
.DEFINE AI_DBG_COMBO  DBGREG+134        ; connected normal canceled into special/super
.DEFINE sintro      $8C                 ; 1 = skip intro (later round / solo)
.DEFINE fadelevel   $8D                 ; 15..0 final-boss fade-out brightness
.DEFINE msuok       $7A                 ; 1 = MSU-1 data port is present
; select-screen state: lives in the $F052+ menu scratch (dead while gs5
; runs -- the intro only touches it during its own loads)
.DEFINE SCUR1       $F052               ; cursor cell index, P1/P2
.DEFINE SCUR2       $F053
.DEFINE SFACE1      $F054               ; char under P1 cursor ($FF init)
.DEFINE SFACE2      $F055
.DEFINE SCPUT1      $F058               ; cpu auto-lock deadline (framecnt)
.DEFINE SCPUT2      $F059
.DEFINE MUSON       $F07C               ; nonzero once a PLAY has been queued:
.DEFINE UI_SFXLOAD  $F07E               ; menu clips active (UI module or pause)
.DEFINE BANTIME     $F057               ; FIGHT! logo frames-left countdown
                                        ;   STOP on a never-started driver gets
                                        ;   no port1 echo back and spcLoad's
                                        ;   handshake then hangs forever
.DEFINE animT       $94                 ; stage-anim timers: 8 words $94-$A3
.DEFINE animP       $A4                 ; stage-anim poses:  8 bytes $A4-$AB
.DEFINE sacnt       $AC                 ; StageAnimTick clip counter (word)
.DEFINE saofs       $AE                 ; StageAnimTick clip-ptr offset (word)
.DEFINE stageidx    $87                 ; last random stage loaded
.DEFINE rng         $88                 ; free-running entropy for stage pick
.DEFINE camx        $89                 ; stage camera x, pixels (word)
.DEFINE hudband     $8B                 ; next live HUD band to flush (round-robin)
.IFDEF PVSNESLIB
.DEFINE GHBUF       $4300               ; afterimage slots, 2x12B per fighter
.ELSE
.DEFINE GHBUF       $0680               ; standalone: free WRAM below HUDMAP
.DEFINE NmiDpSave   $0700               ; NMI scratch-reg stash (96 bytes)
.ENDIF
                                        ;   x.w y.w meta.w tilepg flip xoff
                                        ;   yoff ttl pad; P2 slots at +GHP2
.DEFINE GHP2        24

; Runtime streaming/telemetry block reserved by fight_bridge.asm.
.DEFINE RT_HUDFULL  $5100               ; force next HUD transfer to be complete
.DEFINE RT_MSUFAIL  $5102               ; bounded-seek failures
.DEFINE RT_PROJDROP $5104               ; projectile rejected: two gameplay slots
.DEFINE RT_PROJAIR  $510E               ; per-shot torso-height override (ProjTab bit1)
.DEFINE RT_PROJREL  $51E0               ; per-shot release frame (ProjTab bits 3-7)
.DEFINE RT_PROJFX2  $51E2               ; per-shot alternate ProjFx clip (bit2)
.DEFINE RT_OAMDROP  $5106               ; cells culled after OAM reaches 128
.DEFINE RT_GHOSTGEN $5108               ; generation for P1a/P1b/P2a/P2b
.DEFINE RT_FXUPLOAD $510C               ; cosmetic FX pages per presentation
                                        ;   (projectiles may also use the 2nd)
; HUD dirty bands (huddirty is a bitmask during live play).  FlushHud sends
; at most one band per presentation: life first, then power/combo/timer.
.DEFINE HUD_TOP1    $01                 ; row 1: names / team pips
.DEFINE HUD_LIFE    $02                 ; row 2: life bars + timer top
.DEFINE HUD_TIMER   $04                 ; row 3: timer bottom
.DEFINE HUD_TOP4    $08                 ; row 4: spare top row
.DEFINE HUD_COMBO   $10                 ; row 11: "n HITS"
.DEFINE HUD_POWCNT  $20                 ; rows 22-23: power level counters
.DEFINE HUD_POWER   $40                 ; row 25: power bars
.DEFINE HUD_FULL    $80                 ; all 2048 bytes (overlays/setup)
.DEFINE VQ_HEAD     $5110               ; word offsets in 16-entry ring
.DEFINE VQ_TAIL     $5112
.DEFINE VQ_DATA     $5120               ; 16 records: ptr-index.w, voice-index.w
.DEFINE VQ_BUSY     $5180
.DEFINE VQ_PTRIDX   $5182
.DEFINE VQ_INDEX    $5184
.DEFINE VQ_POS      $5186
.DEFINE VQ_TOTAL    $5188
.DEFINE VQ_MSUOFS   $518A               ; 32-bit offset
.DEFINE VQ_SLOT     $518E               ; cache slot 0/1
.DEFINE VQ_LASTSLOT $5190
.DEFINE VQ_COUNT    $5192               ; bytes copied during this tick
.DEFINE VQ_TABLE    $51A0               ; mutable 8-byte SNESMOD sample record
.DEFINE VQ_CACHE0   $0000               ; bank $7F, 6 KiB per slot
.DEFINE VQ_CACHE1   $1800

.DEFINE lptr        $40                  ; 3-byte long pointer
.DEFINE box0        $44                  ; 8 bytes: victim x0,y0,x1,y1
.DEFINE box1        $4C                  ; 8 bytes: attacker x0,y0,x1,y1
.DEFINE aofs        $54                  ; HitOne attacker offset
.DEFINE boxp        $56                  ; 3-byte generated-data pointer
.DEFINE cptr        $5A                  ; 3-byte character descriptor pointer

.INCLUDE "gen_audio/spc_ids.inc"
.INCLUDE "gen_fight/voices.inc"
.DEFINE MOD_ESAKA   1                     ; soundbank module index (sfx.it=0)
.DEFINE NUMSEL      4                     ; selectable fighters
; frontend song ids -> soundbank modules (MusPlaySong): after the 10
; stage modules (1..10) come cipher(11), cipher beta(12), kof(13),
; lastdance(14), sunset(15), winner(16), crystal(17).
.DEFINE SONG_CIPHER   0                   ; opening intro theme
.DEFINE SONG_CIPHERB  1                   ; title idle theme
.DEFINE SONG_KOF      2                   ; character-select theme
.DEFINE SONG_LDANCE   3                   ; ending1 theme (kof02 last dance rugal)
.DEFINE SONG_SUNSET   4                   ; ending2 theme (kof94 sunset)
.DEFINE SONG_WIN      5                   ; final winner screen (W.mid)
.DEFINE SONG_CRYSTAL  6                   ; SURVIVOR ending (kof00_crystal.mid)
.DEFINE VOICE_SELECT  7                   ; common_00062: select-screen entry
; SFX_FIGHT plays source 5 of sfx.it: common_00063 (READY) + common_00073
; (GO) concatenated by tools/build_sfx_it.py.  The clip is 7454 samples at
; 4 kHz (~1.864 s), plus one frame for the snesmod fifo to reach the SPC.
.DEFINE GO_WAIT     113

; Normal special-cancel openings (six element bytes per character, addressed
; through the descriptor's CH_CANCELROW word).  The table and CancelGate get
; their own window in bank 50's low half, keeping the 32 KiB Fight bank below
; its limit while sharing the code's CPU bank.
.INCLUDE "gen_fight/cancel_data.inc"

.IFDEF PVSNESLIB
.BANK 50 SLOT 0
.ELSE
.BANK 70 SLOT 0
.ENDIF
.ORGA $8000
.SECTION "Fight" FORCE
; Projectile-reflector rows live in this 24-bit bank; FightData's high bank
; makes WLA reject the indexed long access used by ProjReflect.
.INCLUDE "gen_fight/reflect_tab.inc"
.INCLUDE "gen_fight/max_masks.inc"

FightMain:
    rep #$38
    .ACCU 16
    .INDEX 16
.IFNDEF PVSNESLIB
    ldx #$1FFF.w
    txs
.ENDIF
    lda #ENGINE_DP.w
    tcd
    stz.b gamestate                     ; deterministic engine state
    stz.b nmiflag
    stz.b framecnt
    stz.b huddirty
    stz.b stagehold
    stz.b kotimer
    stz.b oamtop
    stz.b vbusy
    jsr TelReset
    stz.b sfxseq
    stz.b sfxlast
    stz.b audiordy
    stz.b sfxdone
    stz.b sfxtoken
    stz.b gotime                          ; no announcer wait at power-on
    stz.b pausecnt                        ; byte: $74 is shaketmr, cleared below
    stz.b shaketmr
    stz.b shakeamp
    stz.b wins1                           ; fresh match state ($80-81 pair)
    stz.b roundwin                        ;   ($83-84: roundwin + nextflag)
    stz.b sel1                            ;   ($85-86: sel1 + sel2)
    stz.b cpu1                            ;   P1 human by default
    stz.w JOIN_ACTIVE                     ; no mid-fight join pending
    stz.w JOIN_SIDE
    stz.w DM_ON                           ; attract demo off at power-on
    stz.b msuok                           ;   MSU-1 presence, set by MsuDetect
.IFDEF PVSNESLIB
    sep #$20
    .ACCU 8
    lda #0
    sta.l $7E0000+Q_LANG                  ;   English quotes at power-on
    rep #$20
    .ACCU 16
.ELSE
    stz.w Q_LANG
.ENDIF
    lda #1
    sta.b roundno                         ;   ($82,$83=0)
    sta.b sel2                            ;   ($86=1: default KYO vs IORI)
    sta.b cpu2                            ;   P2 CPU by default
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    lda #0
    sta.b hudband                       ; live HUD band cursor
    lda #4
    sta.w AI_LEVEL                      ; default CPU difficulty (1..9)
    stz.w AI_LEVEL+1
    sta.w DIFFICULTY                    ; Neo-Geo style OPTIONS level (1..8)
    rep #$20
    .ACCU 16
    stz.w AI_OPPFALL                    ; per-side jump-in state starts clean
    stz.w AI_JUMP
    stz.w AI_AIRT
    stz.w AI_JUMPCD
    stz.w AI_OFFCD
    sep #$20
    .ACCU 8
    lda #1
    sta.w MUSON                         ; BootAudio runs module 1 muted; stop it on first song change
    jsr CmdListReset                      ; fresh PRACTICE usage log
    jsr CampReset                         ; campaign/team vars + STAGEF
    jsr MsuDetect                         ; probe $2002-2007 for "S-MSU1"
    lda #:CharIori                         ; descriptors + spark/hud tables
    sta tblbank                           ;   (char tables live in F_TBANK)
    rep #$20
    .ACCU 16
    ldx #0
    txa
-   sta.l DBGREG_L,x                    ; zero debug counters
    inx
    inx
    cpx #144.w
    bne -
    ; BootAudio already loaded the initial SFX bank.  This scheduler counter
    ; lives outside the engine's cleared debug range and must start at zero;
    ; a stale value makes the first CHECKING MSU SUPPORT frames try to reload
    ; arbitrary SPC effects before the screen timer can advance.
    lda #0
    sta.l $7E46F8
    sep #$20                            ; byte var: keep Q_LANG intact
    .ACCU 8
    sta.w UI_SFXLOAD
    rep #$20
    .ACCU 16
    ldx #0
-   sta.w $5100,x                       ; streaming queue + telemetry
    inx
    inx
    cpx #$0700.w
    bne -
    sep #$20
    .ACCU 8
    lda #$FF.b
    sta.w VQ_LASTSLOT
    rep #$20
    .ACCU 16
    ldx #0
    txa
-   sta FP,x                            ; zero fighter state $0300-$037F
    inx
    inx
    cpx #$80.w
    bne -
.IFDEF PVSNESLIB
    ldx #$100.w
-   sta.w $4000,x                       ; cmd hist, sparks and ghost slots
    inx                               ;   must start free -- a garbage
    inx                               ;   meta pointer would make DrawGhost
    cpx #$400.w                       ;   spew cells across WRAM
    bne -
.ELSE
    ldx #0
-   sta.w GHBUF,x                       ; ghost slots start free -- a garbage
    inx                               ;   meta pointer would make DrawGhost
    cpx #48.w                         ;   spew cells across WRAM
    bne -
.ENDIF
    sep #$20
    .ACCU 8
    jsr PpuInit
.IFDEF MSU_DIAG
    jsl MsuDiagBoot
.ENDIF
    jsr LoadStaticGfx
    jsr StagePick                         ; stage for the select backdrop
    inc.b audiordy                      ; BootAudio (C) already ran SNESMOD
    lda #1                              ; SAFE AUDIO: BootAudio loaded all
    sta.w UI_SFXLOAD                    ;   effects once; UI set is slots 5/6/7
    lda #5
    sta.w UI_SLOT_SEL
    lda #6
    sta.w UI_SLOT_MOVE
    lda #7
    sta.w UI_SLOT_BACK
    jsr MsuScreenEnter                  ; one-time boot check, then intro
OpnDone:
    lda #$81.b                          ; NMI on — wai needs it to wake
    sta.l NMITIMEN
MainLoop:
    ; The NMI ISR and the C audio calls can leave or underflow S inside the
    ; direct-page window.  gs itself lives in WRAM and can already be
    ; corrupted by that overflow, so a conditional reset is not a safe guard.
    ; Restore S unconditionally before WaitForVBlank can push an NMI frame.
    rep #$30
    .ACCU 16
    .INDEX 16
    tsc
    cmp #$1C00.w                        ; valid stack window: $1C00-$1FFF
    bcc ML_top_bad
    cmp #$2000.w
    bcs ML_top_bad
    bra ML_top_ok
ML_top_bad:
    inc.w TEL_SPFIX                     ; telemetry: leaked/corrupted S
    sta.w TEL_SPLAST
ML_top_ok:
    ldx #$1FFF.w
    txs
.IFDEF PVSNESLIB
    jsl WaitForVBlank
    rep #$20
    .ACCU 16
    lda #ENGINE_DP.w
    tcd
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    rep #$20
    .ACCU 16
    jsr FightPresent
    sep #$20
    .ACCU 8
    rep #$20
    .ACCU 16
    .ELSE
    wai
    lda nmiflag
    bne +
        jmp MainLoop
    + 
    stz nmiflag
.ENDIF
    sep #$20
    .ACCU 8
    inc rng                             ; entropy for the stage picker
    jsr ReadPads
    phd                                 ; pump the snesmod message fifo every
    rep #$20                            ;   frame in every gamestate (its
    .ACCU 16                            ;   zeropage needs D=0)
    lda #0
    tcd
    jsl spcProcess
    jsl FxDrainFar                      ; one pending effect load per frame,
                                        ;   after spcProcess; the far routine
                                        ;   also records the real slots
ML_reload_done:
    pld
    sep #$20
    .ACCU 8
    lda.l $7E46F8                       ; wait for sources 0..6, 12, 13
    bne ML_audio_ready                  ; before allocating another effect
    lda.b sfxtoken                      ; ShowSelect queues its voice until
    beq ML_audio_ready                  ; stable slots 7/8 are restored
    stz.b sfxtoken
    lda #VOICE_SELECT.b
    jsr RoundVoice
ML_audio_ready:
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b                      ; snesmod may leave DBR elsewhere;
    pha                                   ;   .w refs below need $7E
    plb
    ; voice queue tick is scheduled after audio reloads below
    jsr VoiceQueueTick
    sep #$20
    .ACCU 8
    jsr DemoClock                          ; attract-demo 30 s deadline (tail)
    lda gamestate
    cmp #9.b
    bne ML_not_msuchk
    jsr MsuScreenTick
    jmp MainLoop
ML_not_msuchk:
    lda gamestate
    cmp #1
    beq ML_sp_ok
    cmp #2
    beq ML_sp_ok
    cmp #4
    bne ML_sp_next
ML_sp_ok:
    rep #$30
    ldx #$1FFF.w
    txs                                 ; fight top-level frame: reset leaked SP
    sep #$20
    lda gamestate
ML_sp_next:
    cmp #1
    beq +
    cmp #2
    beq ++
    cmp #4
    beq +++
    cmp #5
    beq ++++
    cmp #6
    beq +++++
    cmp #7
    beq ++++++
    cmp #8
    beq ++++++++
    cmp #10.b
    beq ML_svend
    cmp #11.b
    beq ML_options
    cmp #GS_YOULOSE.b
    beq ML_youlose
    cmp #GS_BOSS_FADE.b
    beq ML_bossfade
    lda nextflag                        ; gs0 splits: imported title when the
    beq +++++++                         ;   mode-menu flow owns it, legacy
    jsr TitleTick                       ;   intermission/banner tick otherwise
    jmp MainLoop
+++++++ jsr TitleTickNew
    jmp MainLoop
+    jsr FightTick
    jmp MainLoop
++    jsr KoTick
    jmp MainLoop
+++    jsr IntroTick
    jmp MainLoop
++++
    jsr SelTick
    jmp MainLoop
+++++
    jsr MenuTick                          ; mode menu (menucore)
    jmp MainLoop
++++++
    jsr OpnTick                           ; opening intro (menucore)
    jmp MainLoop
++++++++
    jsr EndTick                           ; endings (menucore)
    jmp MainLoop
ML_svend:
    jsr SvEndTick                         ; SURVIVOR still sequence
    jmp MainLoop
ML_options:
    jsl OptionsTick                       ; OPTIONS submenu
    jmp MainLoop
ML_youlose:
    jsl YouLoseTick                       ; campaign defeat menu
    jmp MainLoop
ML_bossfade:
    jsl BossFadeTickFar                   ; Omega KO -> ending1
    jmp MainLoop

; ---------------------------------------------------------------------------
PpuInit:
    .ACCU 8
    lda #0.b                            ; no NMI while reloading VRAM/CGRAM
    sta.l NMITIMEN
    lda #$8F.b
    sta.l INIDISP
    lda #$09.b                            ; mode 1 + BG3 high priority (HUD)
    sta.l BGMODE
    lda #$03.b                            ; OBJ sizes 8x8 small / 16x16 large
    sta.l OBSEL
    lda #(BG1MAP>>10<<2|1).b            ; 64x32 map: stage scrolls L/R 512px
    sta.l BG1SC
    lda #(BG3MAP>>10<<2).b
    sta.l BG3SC
    lda #(BG1CHR>>12).b
    sta.l BG12NBA
    lda #(BG3CHR>>12).b
    sta.l BG34NBA
    lda #32                             ; BG palettes 2-4: stage regions are
    sta.l CGADD                         ;   uploaded per pick by StagePick;
    jsr ClearCgram96                    ;   black them out until then
    lda #0                              ; backdrop color forced to black
    sta.l CGADD
    sta.l CGDATA
    sta.l CGDATA
    lda #12                            ; 2bpp HUD palettes 3-7 -> CGRAM 12-31
    sta.l CGADD                         ;   (tilemap pal bits address pal*4)
    lda #<HudPal
    sta scr0
    lda #>HudPal
    sta scr0+1
    lda #40                             ; 5 pals: text/green/yellow/red/silver
    sta scr1
    stz scr1+1
    lda #:HudPal
    sta scr3
    jsr CgDma
    lda #160                            ; OBJ palette 2: hit sparks
    sta.l CGADD
    lda #<SparkPal
    sta scr0
    lda #>SparkPal
    sta scr0+1
    lda #32
    sta scr1
    stz scr1+1
    lda #:SparkPal
    sta scr3
    jsr CgDma
    lda #240                            ; OBJ palette 7: intro wood explods
    sta.l CGADD
    lda #<WoodPal
    sta scr0
    lda #>WoodPal
    sta scr0+1
    lda #32
    sta scr1
    stz scr1+1
    lda #:WoodPal
    sta scr3
    jsr CgDma
    rep #$20
    .ACCU 16
    ldx #0
    lda #$F0F0.w
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
    cpx #32
    bne -
    sep #$20
    .ACCU 8
    rts

ClearCgram96:                           ; zero 48 colours at current CGADD
    sep #$20                            ;   (acc8, index16 in -- preserved)
    .ACCU 8
    ldx #96.w
    lda #0.b
-   sta.l CGDATA
    dex
    bne -
    rts

CgDma:                                  ; scr0 src, scr3 src bank, scr1 len
    lda scr0
    sta lptr
    lda scr0+1
    sta lptr+1
    lda scr3
    sta lptr+2
    rep #$20
    .ACCU 16
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
    cpy scr1
    bne -
    sep #$20
    .ACCU 8
    rts

; A(8) = generated SFX id.  Routes through IkSfxMap to a SNESMOD soundbank
; source and queues spcEffect(pitch=1, source, vol*16+8); the music commands
; map to spcPlay/spcStop.  Messages dispatch from the fifo in spcProcess,
; which FightTick pumps once per frame.
SfxPlay:
    php
    rep #$30                            ; 16-bit pushes so pops can use the
    .ACCU 16                            ;   same width (plp restores caller
    .INDEX 16                           ;   flags afterwards)
    pha
    phx
    phy
    phd
    sep #$20
    .ACCU 8
    sta sfxlast
    lda audiordy
    bne SfxAudioReady
    jmp SfxDoneD                        ; restore saved direct page on early exit
SfxAudioReady:
    lda sfxlast
    cmp #SFX_SELECT.b
    beq SfxWaitMenuEffects
    cmp #SFX_MOVE.b
    beq SfxWaitMenuEffects
    cmp #SFX_BACK.b
    bne SfxDispatch
SfxWaitMenuEffects:
    rep #$20
    .ACCU 16
    lda.l $7E46F8
    beq SfxMenuReady
    jmp SfxDoneD                        ; skip until the UI slots are restored
SfxMenuReady:
    sep #$20
    .ACCU 8
    lda sfxlast
    cmp #SFX_BACK.b
    beq SfxBlipBack
    cmp #SFX_SELECT.b
    beq SfxBlipLight
    cmp #SFX_MOVE.b
    bne SfxDispatch
SfxBlipLight:
    lda.l $7E0000+UI_SFXLOAD             ; the pause menu raises this flag (its
    bne SfxDispatch                     ;   stage module preloads the menu
    lda #SFX_HIT_LIGHT.b                ;   clips); join-select still has no
    sta sfxlast                         ;   menu slots: use combat blips
    bra SfxDispatch
SfxBlipBack:
    lda.l $7E0000+UI_SFXLOAD
    bne SfxDispatch
    lda #SFX_HIT_MED.b
    sta sfxlast
SfxDispatch:
    inc.b sfxseq                        ; dispatch counter (test/debug hook)
    rep #$30
    .ACCU 16
    .INDEX 16
    lda sfxlast
    and #$00FF.w
    tay                                 ; preserve the byte id as a clean word;
                                        ; $32 beside sfxlast is audiordy
    cmp #SPC_MUS_PLAY.w
    beq SfxMusPlay
    cmp #SPC_MUS_STOP.w
    bne +
    jmp SfxMusStop
+
    ; On UI modules the menu/winner effects live in the slots returned by
    ; UiLoadSounds, not in the fixed boot slots.  Compare the ids explicitly:
    ; the old "id - SFX_SELECT" index silently read past the slots when the
    ; accumulator reaching this point was not the plain menu id.
    lda.l $7E0000+UI_SFXLOAD
    and #$00FF.w                        ; byte var: mask the high byte
    beq SfxMap
    tya
    cmp #SFX_SELECT.w
    beq SfxUiSelect
    cmp #SFX_MOVE.w
    beq SfxUiMove
    cmp #SFX_BACK.w
    beq SfxUiBack
    cmp #SFX_WIN.w
    beq SfxUiWin
    bra SfxMap
SfxUiSelect:
    lda.l $7E0000+UI_SLOT_SEL
    bra SfxUiUse
SfxUiMove:
    lda.l $7E0000+UI_SLOT_MOVE
    bra SfxUiUse
SfxUiBack:
    lda.l $7E0000+UI_SLOT_BACK
    bra SfxUiUse
SfxUiWin:
    lda.l $7E0000+UI_SLOT_WIN
SfxUiUse:
    and #$00FF.w
    tay
    lda #$00E8.w                        ; volume 14, centre pan
    bra SfxEffect
SfxMap:
    tya
    ; id -> IkSfxMap[id*2]: .db source, .db volume nibble
    asl a
    tax
    lda.l IkSfxMap,x
    and #$00FF.w
    tay                             ; Y = preloaded effect-directory slot
    lda.l IkSfxMap+1,x
    and #$000F.w
    asl a
    asl a
    asl a
    asl a
    ora #$0008.w                    ; volpan = vol*16 + center pan
SfxEffect:
    pha                             ; arg3
    tya
    phy                             ; arg2: source index
    pea 1                           ; arg1: pitch 1 = 4 kHz
    lda #0
    tcd                             ; pvsneslib audio code expects D=0
    jsl spcEffect
    bra SfxPop
SfxMusPlay:
    lda #0
    tcd
    pea 0
    jsl spcPlay
    rep #$20
    .ACCU 16
    pla                               ; drop pea 0 (interrupt-safe)
    lda #1                            ; a module is now playing: STOP echoes
    sta.w MUSON
    bra SfxDoneD
SfxMusStop:
    lda #0
    tcd
    lda.w MUSON                       ; STOP on a never-started driver hangs
    and #$00FF.w                      ;   the next handshake -- skip it
    beq SMS_out
    jsl spcStop
    stz.w MUSON                       ; stz writes a byte pair here -- $F07D
SMS_out:                              ;   is free padding, keep it that way
    bra SfxDoneD
SfxPop:
    rep #$20
    .ACCU 16
    pla
    pla
    pla
SfxDoneD:
    pld
SfxDone:
    rep #$30                            ; pops match the 16-bit pushes; plp
    .ACCU 16                            ;   then restores the caller's flags
    .INDEX 16
    ply
    plx
    pla
    plp
    rts

VrDma:
    sta scr3
    lda scr3
    sta lptr+2
    lda scr0
    sta lptr
    lda scr0+1
    sta lptr+1
    lda #$80.b
    sta.l VMAIN
    rep #$20
    .ACCU 16
    lda scr2
    sta.l VMADDL
    ldy #0
-   lda [lptr],y
    sta.l VMDATAL
    iny
    iny
    cpy scr1
    bne -
    sep #$20
    .ACCU 8
    rts

; Copy the selected 3x3 portrait tiles into the two reserved BG3 slots.
LoadPortraits:
    rep #$20
    .ACCU 16
    lda sel1
    and #$00FF.w
    asl a
    tax
    lda.l PortraitOfs,x
    sta scr0
    lda #Portraits.w
    clc
    adc scr0
    sta scr0
    lda #144.w
    sta scr1
    lda #(BG3CHR + PORTRAIT_P1*8).w
    sta scr2
    sep #$20
    .ACCU 8
    lda #:Portraits
    jsr VrDma
    rep #$20
    .ACCU 16
    lda sel2
    and #$00FF.w
    asl a
    tax
    lda.l PortraitOfsP2,x
    sta scr0
    lda #Portraits.w
    clc
    adc scr0
    sta scr0
    lda #144.w
    sta scr1
    lda #(BG3CHR + PORTRAIT_P2*8).w
    sta scr2
    sep #$20
    .ACCU 8
    lda #:Portraits
    jsr VrDma
    rep #$20
    .ACCU 16
    ; P1 portrait palette -> CGRAM 0..3
    lda sel1
    and #$00FF.w
    asl a
    asl a
    asl a
    sta scr0
    lda #PortraitPal.w
    clc
    adc scr0
    sta scr0
    lda #8
    sta scr1
    sep #$20
    .ACCU 8
    lda #0
    sta.l CGADD
    lda #:PortraitPal
    sta scr3
    jsr CgDma
    rep #$20
    .ACCU 16
    ; P2 portrait palette -> CGRAM 4..7
    lda sel2
    and #$00FF.w
    asl a
    asl a
    asl a
    sta scr0
    lda #PortraitPal.w
    clc
    adc scr0
    sta scr0
    lda #8
    sta scr1
    sep #$20
    .ACCU 8
    lda #4
    sta.l CGADD
    lda #:PortraitPal
    sta scr3
    jsr CgDma
    rep #$20
    .ACCU 16
    rts

; Point the 3x3 red/blue face-window cells at the portrait tiles.
PortraitMap:
    rep #$20
    .ACCU 16
    lda #((1*32+0)*2).w
    sta scr0
    lda #PORTRAIT_P1.w
    sta scr1
    lda #$2000.w                          ; BG3 palette 0 (P1)
    sta scr2
    ldy #3
PM_p1_row:
    ldx scr0
    lda #3
    sta scr3
PM_p1_col:
    lda scr1
    ora scr2
    sta HUDMAP,x
    inx
    inx
    inc scr1
    dec scr3
    bne PM_p1_col
    lda scr0
    clc
    adc #(32*2).w
    sta scr0
    dey
    bne PM_p1_row
    lda #((1*32+29)*2).w
    sta scr0
    lda #PORTRAIT_P2.w
    sta scr1
    lda #$2400.w                          ; BG3 palette 1 (P2)
    sta scr2
    ldy #3
PM_p2_row:
    ldx scr0
    lda #3
    sta scr3
PM_p2_col:
    lda scr1
    ora scr2
    sta HUDMAP,x
    inx
    inx
    inc scr1
    dec scr3
    bne PM_p2_col
    lda scr0
    clc
    adc #(32*2).w
    sta scr0
    dey
    bne PM_p2_row
    rep #$20
    .ACCU 16
    rts

LoadStaticGfx:
    rep #$20
    .ACCU 16
    lda #HudChr
    sta scr0
    lda #HudChr_End-HudChr
    sta scr1
    lda #BG3CHR
    sta scr2
    sep #$20
    .ACCU 8
    lda #:HudChr
    jsr VrDma
    rep #$20
    .ACCU 16
    ; crowd-anim pose tiles -> dynamic BG1 slots ($2C00, above the font)
    lda #StgAnimChr
    sta scr0
    lda #StgAnimChr_End-StgAnimChr
    sta scr1
    lda #STGACHR
    sta scr2
    sep #$20
    .ACCU 8
    lda #:StgAnimChr
    jsr VrDma
    ; anim state is reinitialised per stage in StagePick (animT/animP)
    rep #$20
    .ACCU 16
    ; Effect pages are uploaded by FxPrepareBoth under forced blank.  The
    ; old unconditional static-spark copy ran after it and overwrote the
    ; streamed projectile atlas, so projectiles showed the spark page.
    ldx #0
    txa
-   sta HUDMAP,x
    inx
    inx
    cpx #2048.w
    bne -
    jsr FlushHud
    sep #$20
    .ACCU 8
    rts

FlushHud:
    sep #$20
    .ACCU 8
    lda gamestate
    cmp #1.b
    bne FlushHudFullNear
    lda.w RT_HUDFULL
    bne FlushHudFullNear
    lda.w CL_OPEN
    bne FlushHudFullNear
    lda.w PZ_ON
    bne FlushHudFullNear
    lda huddirty
    bne +
    rts
+   and #HUD_FULL
    beq FlushHudLive
    jmp FlushHudFull
FlushHudFullNear:
    jmp FlushHudFull
FlushHudLive:
    rep #$20
    .ACCU 16
    inc.w TEL_HUD_FRAMES
    sep #$20
    .ACCU 8
    rep #$10
    .INDEX 16
    lda.b hudband                        ; resume after the last band sent:
    cmp #(5*7).b                         ;   a band that is dirty every frame
    bcc FHB_start                        ;   (LIFE during damage/chip) must not
    lda #0                               ;   starve TIMER/POWER/COMBO
    sta.b hudband
FHB_start:
    rep #$20                             ; form the index in 16-bit A: TAX
    .ACCU 16                             ;   while A is 8-bit lets the stale
    lda.b hudband                        ;   B/high byte leak into X and the
    and #$00FF.w                         ;   table read runs off HudBandTab
    tax
    sep #$20
    .ACCU 8
    ldy #6                               ; 5 bands + the table terminator
FlushHudBand:
    lda.l HudBandTab,x
    beq FHB_wrap
    and huddirty
    bne FHB_send
FHB_advance:
    inx
    inx
    inx
    inx
    inx
    inx
    inx
    cpx #(5*7).w                        ; X is 16-bit throughout FlushHudLive
    bcc FHB_adv_ok
    ldx #0
FHB_adv_ok:
    dey
    bne FlushHudBand
    rts
FHB_wrap:
    ldx #0
    dey
    bne FlushHudBand
    rts
FHB_send:
    sta scr4
    lda huddirty
    eor scr4
    sta huddirty
    txa                                  ; next frame starts at the following
    clc                                  ;   band
    adc #7
    cmp #(5*7).b
    bcc FHB_next_ok
    lda #0
FHB_next_ok:
    sta.b hudband
    rep #$20
    .ACCU 16
    lda.l HudBandTab+1,x
    clc
    adc #HUDMAP.w
    sta scr0
    lda.l HudBandTab+3,x
    clc
    adc #BG3MAP.w
    sta scr1
    lda.l HudBandTab+5,x
    sta scr2
    jsr FlushHudRange
    rts
FlushHudDone:
    rts

FlushHudFull:
    sep #$20
    .ACCU 8
    stz.w RT_HUDFULL
    stz.b huddirty
    rep #$20
    .ACCU 16
    inc.w TEL_HUD_FRAMES
    lda #HUDMAP.w
    sta scr0
    lda #BG3MAP.w
    sta scr1
    lda #2048.w
    sta scr2
FlushHudRange:
    rep #$20
    .ACCU 16
    lda.w TEL_HUD_BYTES
    clc
    adc scr2
    sta.w TEL_HUD_BYTES
    lda.w TEL_HUD_BYTES+2
    adc #0
    sta.w TEL_HUD_BYTES+2
    lda scr1
    sta.l VMADDL
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l VMAIN
    lda #$01.b                          ; mode 1: word writes to $2118/$2119
    sta.l $4360
    lda #$18.b
    sta.l $4361
    rep #$20
    .ACCU 16
    lda scr0
    sta.l $4362
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    sta.l $4364
    rep #$20
    .ACCU 16
    lda scr2
    sta.l $4365
    sep #$20
    .ACCU 8
    lda #$40.b
    sta.l MDMAEN                        ; fire ch6
    rts

; mask, HUDMAP row*64, BG3MAP row*32 words, byte count (little-endian)
HudBandTab:
    .db HUD_LIFE,                  $80, $00, $40, $00, $40, $00
    .db HUD_POWER,                 $40, $06, $20, $03, $40, $00
    .db HUD_POWCNT,                $80, $05, $C0, $02, $80, $00
    .db HUD_TIMER,                 $80, $00, $40, $00, $80, $00
    .db HUD_COMBO,                 $C0, $02, $60, $01, $40, $00
    .db 0


; ---------------------------------------------------------------------------
; Random stage picker: idx = (rng ^ framecnt) mod NSTAGES, then the chosen
; stage's chr/map/pal are uploaded to BG1 VRAM + CGRAM under forced blank.
; StageTab rows are 12 bytes: .dw chr, chrlen, map, pal / .db 3 banks, pad.
StagePick:
    sep #$20
    .ACCU 8
    lda #0.b                          ; uploads take several vblanks; an NMI
    sta.l NMITIMEN                        ;   landing mid-VrDma steals VMADD/CGADD
    lda.l $4210                         ;   landing mid-VrDma steals VMADD/CGADD
                                        ;   and scatters the map/pal writes
    lda.w STAGEF                          ; campaign may pin a stage
    bpl SP_set
    lda rng
    eor framecnt
SP_mod:
    cmp #(NSTAGES-1).b                    ; random picks exclude Rugal's stage
    bcc SP_skipboss
    sbc #(NSTAGES-1).b
    bra SP_mod
SP_skipboss:
    cmp #5.b                              ;   (boss-only), so map 0..N-2 to
    bcc SP_set                            ;   0..4,6..N-1
    inc a
SP_set:
    sta stageidx
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl
    asl                                 ; idx*4
    sta scr6
    asl                                 ; idx*8
    adc scr6                            ; idx*12 -> table offset
    sta scr6
    sep #$20
    .ACCU 8
    lda #$8F.b                          ; force blank for the VRAM reload
    sta.l INIDISP
    rep #$20                            ; drop the previous screen's OAM cells:
    .ACCU 16                            ;   their tiles are about to be replaced
    jsr MtClear                         ;   by stage graphics
    sep #$20
    .ACCU 8
    ; VrDma clobbers lptr, so rebuild the StageTab pointer before each read
    rep #$20
    .ACCU 16
    lda #StageTab
    clc
    adc scr6
    sta lptr
    sep #$20
    .ACCU 8
    lda #:StageTab
    sta lptr+2
    rep #$20
    .ACCU 16
    ldy #2
    lda [lptr],y                        ; chr byte count
    sta scr1
    dey
    dey
    lda [lptr],y                        ; chr offset
    sta scr0
    lda #BG1CHR
    sta scr2
    ldy #8
    sep #$20
    .ACCU 8
    lda [lptr],y                        ; chr bank
    jsr VrDma
    rep #$20
    .ACCU 16
    lda #StageTab
    clc
    adc scr6
    sta lptr
    sep #$20
    .ACCU 8
    lda #:StageTab
    sta lptr+2
    rep #$20
    .ACCU 16
    ldy #4
    lda [lptr],y                        ; map offset
    sta scr0
    lda #4096.w                         ; 64x32 word map (2 planes)
    sta scr1
    lda #BG1MAP
    sta scr2
    ldy #9
    sep #$20
    .ACCU 8
    lda [lptr],y                        ; map bank
    jsr VrDma
    lda #32                             ; BG palettes 2-4; HUD owns 12-31
    sta.l CGADD
    rep #$20
    .ACCU 16
    lda #StageTab
    clc
    adc scr6
    sta lptr
    sep #$20
    .ACCU 8
    lda #:StageTab
    sta lptr+2
    rep #$20
    .ACCU 16
    ldy #6
    lda [lptr],y                        ; pal offset
    sta scr0
    lda #96.w                           ; 3 pals x 16 colors x 2 bytes
    sta scr1
    ldy #10
    sep #$20
    .ACCU 8
    lda [lptr],y                        ; pal bank
    sta scr3
    jsr CgDma
    jsr StageAnimInit                     ; reset clip clocks for this stage
    jsr PushOamShadow                     ; hardware OAM <- cleared shadow
    lda.b stagehold                       ; StartFight rebuilt the HUD map, so
    beq SP_show                           ;   upload it now while the display is
    lda #1                                ;   still blank: the first frame the
    sta.w RT_HUDFULL                      ;   stage appears must not show the
    jsr FlushHud                          ;   old HUD map or leftover sprites
SP_show:
    lda #$0F.b
    sta.l INIDISP
    lda #$81.b                            ; WaitForVBlank sleeps in a WAI loop
    sta.l NMITIMEN                        ;   that only the NMI can wake
    stz.b stagehold                       ; one-shot hold
    rts

; OAM shadow -> hardware OAM via GPDMA ch6.  Shared by the vblank presenter
; and StagePick: the previous screen leaves its sprites in hardware OAM and
; StagePick turns the display on again before the main loop can present, so
; the cleared shadow must be pushed there too.
PushOamShadow:
    sep #$20
    .ACCU 8
    lda #0
    sta.l OAMADDL
    sta.l OAMADDL+1
    sta.l $4360                           ; mode 0: bytes to a single reg
    lda #$04.b
    sta.l $4361                           ; -> $2104 OAMDATA
    rep #$20
    .ACCU 16
    lda #OAMBUF.w
    sta.l $4362
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    sta.l $4364                           ; OAMBUF bank
    rep #$20
    .ACCU 16
    lda #544.w
    sta.l $4365
    sep #$20
    .ACCU 8
    lda #$40.b
    sta.l MDMAEN                          ; fire ch6
    rts

; scr0 = HUDMAP byte ofs, scr2 = 24-bit string pointer
WriteStrData:
    sep #$20
    .ACCU 8
    lda tblbank
    sta scr2+2
WriteStr:
    sep #$20
    .ACCU 8
    ldy #0
    lda [scr2],y
    sta scr4
    iny
    rep #$20
    .ACCU 16
    lda scr0
    tax
    sep #$20
    .ACCU 8
-   lda [scr2],y
    sta HUDMAP,x
    lda #$2C.b
    sta HUDMAP+1,x
    iny
    inx
    inx
    dec scr4
    bne -
    rep #$20
    .ACCU 16
    rts

; scr0 = top-row HUDMAP byte ofs, scr2 = 24-bit string pointer (.db len,
; top-half tile ids).  Writes the 8x16 big glyphs: tile at row r, tile+1 at
; row r+1, both in the gold announce palette.
WriteStrBigData:
    sep #$20
    .ACCU 8
    lda tblbank
    sta scr2+2
WriteStrBig:
    sep #$20
    .ACCU 8
    ldy #0
    lda [scr2],y
    sta scr4
    iny
    rep #$20
    .ACCU 16
    lda scr0
    tax
    sep #$20
    .ACCU 8
-   lda [scr2],y
    sta HUDMAP,x
    inc a
    sta HUDMAP+64,x                     ; bottom half on the row below
    lda #ATT_YEL.b
    sta HUDMAP+1,x
    sta HUDMAP+65,x
    iny
    inx
    inx
    dec scr4
    bne -
    rep #$20
    .ACCU 16
    rts

; scr0 = HUDMAP byte ofs of the top-left cell, scr2 = 24-bit pointer to a
; tile block (.db w,h then w*h tile ids, row major).  Each cell gets the
; gold announce attribute.  Used for the real K.O. and FIGHT! logos.
WriteBlock:
    sep #$20
    .ACCU 8
    lda tblbank
    sta scr2+2
    rep #$20
    .ACCU 16
    lda [scr2]                          ; word read: w low, h high
    sta scr4                            ; w -> scr4; h byte lands at scr4+1
    sep #$20
    .ACCU 8
    lda scr4+1
    and #$1F.b                          ; stray pointers must not spew rows
    beq WB_bail                         ;   outside the 32x32 HUD map
    sta scr5                            ; scr5 = h
    lda scr4
    and #$1F.b
    beq WB_bail
    sta scr4                            ; scr4 = w
    rep #$20
    .ACCU 16
    ldy #2
WB_row:
    ldx scr0
    sep #$20
    .ACCU 8
    lda scr4
    sta scr6
-   lda [scr2],y
    sta HUDMAP,x
    lda #ATT_YEL.b
    sta HUDMAP+1,x
    iny
    inx
    inx
    dec scr6
    bne -
    rep #$20
    .ACCU 16
    lda scr0
    clc
    adc #64.w                           ; next HUD row
    sta scr0
    ; scr5 holds the 8-bit height: decrement it in 8-bit mode.  A 16-bit
    ; DEC here folded the stale high byte into the counter and made a 2-row
    ; logo scribble dozens of rows (and past HUDMAP) whenever scr5+1 was
    ; left non-zero by an earlier routine -- the garbled "spinning" column
    ; over the loser after the K.O.
    sep #$20
    .ACCU 8
    dec scr5
    bne WB_row
WB_bail:
    rep #$20
    .ACCU 16
    rts

; FIGHT! logo countdown shared by FightTick and the IntroTick announcer wait.
; A = 8-bit on entry and exit; clears the banner when the countdown expires.
BannerTick:
    lda.w BANTIME
    beq BT_out
    dec a
    sta.w BANTIME
    bne BT_out
    rep #$20
    .ACCU 16
    jsr ClearBanner
    sep #$20
    .ACCU 8
    lda huddirty
    ora #HUD_FULL
    sta huddirty
BT_out:
    rts

; FIGHT! logo cells: clear the 8x2 block drawn at round start (row 9,
; cols 12-19).  Called by FightTick when bantime reaches zero.
ClearBanner:
    rep #$20
    .ACCU 16
    ldx #((9*32+12)*2).w
    sep #$20
    .ACCU 8
    lda #0
-   sta HUDMAP,x
    sta HUDMAP+1,x
    inx
    inx
    cpx #((9*32+20)*2).w
    bne -
    ldx #((10*32+12)*2).w
-   sta HUDMAP,x
    sta HUDMAP+1,x
    inx
    inx
    cpx #((10*32+20)*2).w
    bne -
    rep #$20
    .ACCU 16
    lda #1
    sta.w RT_HUDFULL                    ; rows 9/10 lie outside the live HUD bands
    rts

ShowTitle:
    .ACCU 8
    stz.b winvoice                      ; drop a deferred voice from the last
    lda #$15.b                          ; BG1 stage + BG3 HUD + OBJ
    sta.l TM
    rep #$20
    .ACCU 16
    stz.w WIN_TIMER
    ldx #0
    txa
-   sta HUDMAP,x                        ; clear whole HUD map
    inx
    inx
    cpx #2048.w
    bne -
    sep #$20
    .ACCU 8
    lda nextflag
    cmp #1
    bne ST_title
    rep #$20                            ; round intermission: "ROUND n"
    .ACCU 16                            ;   shared "ROUND" text...
    lda #((9*32+12)*2).w
    sta scr0
    lda #RoundLogo.w
    sta scr2
    jsr WriteBlock
    rep #$20
    .ACCU 16
    ldx #((9*32+18)*2).w                  ; digit follows the ROUND text
    sep #$20
    .ACCU 8
    lda roundno
    asl a
    clc
    adc #BIGD0.b
    sta HUDMAP,x
    inc a
    sta HUDMAP+64,x
    lda #ATT_YEL.b
    sta HUDMAP+1,x
    sta HUDMAP+65,x
    bra ST_select
ST_title:
    sep #$20
    .ACCU 8
    lda nextflag                        ; match-over screen skips the title
    cmp #2                              ;   so "<name> WINS" stands alone
    beq ST_quote
    rep #$20
    .ACCU 16
    lda #((9*32+10)*2).w
    sta scr0
    lda #BStrTitle.w
    sta scr2
    jsr WriteStrBigData
ST_quote:
    sep #$20
    .ACCU 8
    lda nextflag
    cmp #2
    bne ST_select
    jsr DrawBanner                      ; match over: "<name> WINS"/"DRAW"
ST_select:
    ; The title/round intermission does not run FightTick, so explicitly
    ; retire every fight object.  Otherwise the final KO OAM (sometimes just
    ; one spark cell) remains on screen until the next round starts.
    ; F_META/SPK_ANIM are words: this runs with 8-bit A, so clear the high
    ; byte too or DrawFighter reads a stale $XX00 pointer and paints a
    ; garbage metasprite over the ROUND screen.
    stz FP+F_META
    stz FP+F_META+1
    stz FP+F_META+FP2OFS
    stz FP+F_META+FP2OFS+1
    stz.w SPARKS+SPK_ANIM
    stz.w SPARKS+SPK_ANIM+1
    stz.w SPARKS+SPK_ANIM+SPK_SIZE
    stz.w SPARKS+SPK_ANIM+SPK_SIZE+1
    jsr ClearGhosts                     ; drop afterimage trail slots too
    jsr BuildOam
    sep #$20
    .ACCU 8
    stz FP+F_DMAREQ
    stz FP+F_DMAREQ+FP2OFS
    stz framecnt                        ; make the intermission exactly 60 frames
    stz pausecnt                        ;   and never carry a freeze over
    stz shaketmr                        ;   ($74: an old word clear of $73/$74)
    stz gamestate
    stz combohit                        ; drop any counter still on screen
    stz combohit+FP2OFS
    stz combotmr
    stz combotmr+FP2OFS
    lda huddirty
    ora #HUD_FULL
    sta huddirty
    lda nextflag                          ; announcer only on round change;
    cmp #1                                ;   the boot/match-over title is
    beq ST_round_voice
    cmp #2
    beq ST_winner_audio
    rts
ST_winner_audio:
    lda #SONG_WIN.b
    jsr MusPlaySong                       ; start converted W.mid at Winner entry
    lda #1
    sta.b winvoice                        ; TitleTick plays it once the winner
    rts                                   ;   module's effects are loaded
ST_round_voice:
    lda wins1                             ; match point -> "FINAL ROUND"
    cmp #1
    beq ST_finalrd
    lda wins2
    cmp #1
    beq ST_finalrd
    lda roundno                           ; else voice index = roundno-1
    dec a
    cmp #9
    bcc ++
    lda #8
++  bra ST_rdplay
ST_finalrd:
    lda #8
ST_rdplay:
    jsr RoundVoice
    rts

; (SelNameTab removed: .l loads resolve the code bank wrong; sel*<Str strings
;  are branched on directly in DrawSelect/DrawBanner)

; "1P:"/<name> and "2P:"/<name> select rows.  Called from ShowTitle and on
; every pad toggle so the rows always reflect sel1/sel2.
; ---------------------------------------------------------------------------
; Character select (gamestate 5) -- KOF98-style screen built by
; tools/build_select.py: BG1 carries the beams art + 47-cell grid with the
; roster icons baked in, and OBJ ring sprites mark each side's cursor
; (the portrait windows were dropped for the 41-char roster; the area now
; holds extra cells).  START joins a CPU side, B hands it back / undoes
; its pick -- arcade semantics; the move/confirm/cancel sounds match the
; mode menu.
ShowSelect:
    jsr VoiceQueueReset                  ; drop the previous bout's quotes
    sep #$20
    .ACCU 8
    lda #0
    sta.l NMITIMEN                        ; VRAM repack -> NMI off
    lda #$80.b
    sta.l INIDISP                         ; force blank
    rep #$20
    .ACCU 16
    ; --- palettes: art + cell pals + initial face pals (8 BG pals) ---
    lda #SelPal.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:SelPal
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(SelPal_End-SelPal).w
    sta.b I_LEN
    ldx #0
    jsr MnCgRam
    ; OBJ pals: menu font white/yellow -> 128, cursor ramps -> 160
    lda #MnObjPal.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:MnObjPal
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #128.w
    sta.b I_LEN
    ldx #128.w
    jsr MnCgRam
    lda #SelObjPal.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:SelObjPal
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(SelObjPal_End-SelObjPal).w
    sta.b I_LEN
    ldx #160.w
    jsr MnCgRam
    ; --- BG1 map + tiles ---
    lda #SelMap.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:SelMap
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(SelMap_End-SelMap).w
    sta.b I_LEN
    ldx #MENU_MAPW.w
    jsr MnDma
    lda #SelChr.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:SelChr
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(SelChr_End-SelChr).w
    sta.b I_LEN
    ldx #MENU_TILEW.w
    jsr MnDma
    ; --- OBJ chr: menu font at idx0, cursor ring at SEL_CUR_TILE ---
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
    lda #SelObjChr.w
    sta.b I_SRC
    sep #$20
    .ACCU 8
    lda #:SelObjChr
    sta.b I_SRC+2
    rep #$20
    .ACCU 16
    lda #(SelObjChr_End-SelObjChr).w
    sta.b I_LEN
    ldx #(MENU_OBJW + SEL_CUR_TILE*16).w
    jsr MnDma
    ; --- mode1 regs: BG1 map $1800 / chr $4000, OBJ base $2000, 8+32 ---
    sep #$20
    .ACCU 8
    lda #$01.b
    sta.l $2105                           ; BGMODE 1
    lda #$18.b
    sta.l $2107                           ; BG1SC: map word $1800, 32x32
    lda #$04.b
    sta.l $210B                           ; BG12NBA: BG1 tiles word $4000
    lda #$01.b
    sta.l $2101                           ; OBSEL: 8x8/32x32, table0 $2000
    lda #$11.b
    sta.l $212C                           ; TM = BG1 + OBJ
    lda #0
    sta.l $212D
    sta.l $210D
    sta.l $210D
    sta.l $210E
    sta.l $210E                           ; BG1 scroll 0,0
    ; FightPresent calls ShakeScroll from vblank even outside a fight.  Clear
    ; the last fighters' world positions and camera so the next vblank does
    ; not overwrite this select screen's zero scroll with the old fight pan.
    rep #$20
    .ACCU 16
    stz FP+F_X
    stz FP+F_X+FP2OFS
    stz.b camx                          ; DP vars: .w would hit $7E0089/$0074,
    stz.b shaketmr                      ;   i.e. snesmod's spc_fifo in page 0
    sep #$20
    .ACCU 8
    ; --- select state ---
    stz.b lock1
    stz.b lock2
    stz.b framecnt
    stz FP+F_META                         ; retire fight OAM leftovers
    stz FP+F_META+1
    stz FP+F_META+FP2OFS
    stz FP+F_META+FP2OFS+1
    stz.w SPARKS+SPK_ANIM
    stz.w SPARKS+SPK_ANIM+1
    stz.w SPARKS+SPK_ANIM+SPK_SIZE
    stz.w SPARKS+SPK_ANIM+SPK_SIZE+1
    jsr ClearGhosts
    rep #$20
    .ACCU 16
    lda.b sel1                            ; cursor on the side's pick cell
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelChrCell,x
    sta.w SCUR1
    rep #$20
    .ACCU 16
    lda.b sel2
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelChrCell,x
    sta.w SCUR2
    lda #$FF.b
    sta.w SFACE1
    sta.w SFACE2
    lda #90.b
    sta.w SCPUT1
    lda #150.b
    sta.w SCPUT2
    jsr SelFaceSync                       ; name anchors off the seeded cells
    jsr MtClear
    jsr SelDrawOam
    sep #$20
    .ACCU 8
    lda #$81.b
    sta.l NMITIMEN
    lda #$0F.b
    sta.l INIDISP
    lda #1
    sta.b sfxtoken                       ; play after menu effects reload
    rep #$20
    .ACCU 16
    rts

; ---------------------------------------------------------------------------
; Cursor helpers
; ---------------------------------------------------------------------------
; X = side (0/1): copy the cursor cell's pixel pos into scr0/scr1.
SDO_cellxy:
    sep #$20
    .ACCU 8
    lda.w SCUR1,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellX,x
    sta.b scr0
    lda.l SelCellY,x
    sta.b scr1
    sep #$20
    .ACCU 8
    rts

; emit the 8-tile cursor ring: scr0.b=x scr1.b=y scr5.b=OBJ attr
SelRingOam:
    rep #$20
    .ACCU 16
    stz.b scr6                            ; tile counter
SR_loop:
    rep #$20
    .ACCU 16
    ldx.b scr6
    sep #$20
    .ACCU 8
    lda.b scr0
    clc
    adc.l SelRingX,x
    ldy.b oamtop
    sta.w OAMBUF,y
    lda.b scr1
    clc
    adc.l SelRingY,x
    sta.w OAMBUF+1,y
    lda.l SelRingMap,x
    sta.w OAMBUF+2,y
    lda.b scr5
    sta.w OAMBUF+3,y
    tya
    clc
    adc #4.b
    sta.b oamtop
    inc.b scr6
    lda.b scr6
    cmp #8.b
    bne SR_loop
    sep #$20
    .ACCU 8
    rts

; locked-side center fill tile: scr0/scr1 hold the ring origin
SelFillOam:
    sep #$20
    .ACCU 8
    lda.b scr0
    clc
    adc #8.b
    sta.b scr0
    lda.b scr1
    clc
    adc #8.b
    sta.b scr1
    lda #SEL_FILL_TILE.b
    sta.b scr3
    jsr MtCell
    sep #$20
    .ACCU 8
    rts

; tag string left/above the ring: scr0/scr1 = cell pixel pos, scr2=str ptr
; (caller's bank byte already in scr2+2)
SelTagOam:
    sep #$20
    .ACCU 8
    lda.b scr1
    sec
    sbc #10.b
    sta.b scr1
    lda #$30.b                            ; prio3, OBJ pal0 (white)
    sta.b scr4
    jsr MtStr
    sep #$20
    .ACCU 8
    rts

; ---------------------------------------------------------------------------
; Per-frame OAM emit for the select screen: cursor rings (+locked fill),
; "1P"/"2P" tags, face-window names, team-mode pick marks.
; ---------------------------------------------------------------------------
SelDrawOam:
    rep #$20
    .ACCU 16
    stz.b oamtop
    ; ---------- P1 ring ----------
    sep #$20
    .ACCU 8
    lda.b cpu1
    bne SDO_cur2                          ; CPU side: no ring
    lda.b lock1
    bne +                                 ; locked: steady ring
    lda.b framecnt
    and #$10.b
    bne SDO_cur2                          ; blink off-phase
+   ldx #0
    jsr SDO_cellxy
    lda #$34.b                            ; prio3, OBJ pal2 (blue)
    sta.b scr5
    jsr SelRingOam
    sep #$20
    .ACCU 8
    lda.b lock1
    beq +
    lda.b scr5
    sta.b scr4
    jsr SelFillOam                        ; locked: dim the cell center
+   sep #$20
    .ACCU 8
    ldx #0
    jsr SDO_cellxy
    rep #$20
    .ACCU 16
    lda #Str1P.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda tblbank.b
    sta.b scr2+2
    jsr SelTagOam
SDO_cur2:
    ; ---------- P2 ring ----------
    sep #$20
    .ACCU 8
    lda.b cpu2
    beq SDO_p2human
    ; CPU side: show the ring while P1 steers the foe pick (solo campaign)
    lda.w G_MODE
    cmp #1
    beq SDO_ringchk
    cmp #4
    beq SDO_ringchk
    cmp #5
    bne SDO_team
SDO_ringchk:
    lda.b lock1
    beq SDO_team
    lda.b lock2
    bne SDO_team
    bra SDO_p2ring
SDO_p2human:
    lda.b lock2
    bne SDO_p2ring                        ; locked: steady ring
    lda.b framecnt
    and #$10.b
    bne SDO_team                          ; blink off-phase
SDO_p2ring:
+   ldx #1
    jsr SDO_cellxy
    lda #$36.b                            ; prio3, OBJ pal3 (red)
    sta.b scr5
    jsr SelRingOam
    sep #$20
    .ACCU 8
    lda.b lock2
    beq +
    lda.b scr5
    sta.b scr4
    jsr SelFillOam
+   sep #$20
    .ACCU 8
    ldx #1
    jsr SDO_cellxy
    sep #$20
    .ACCU 8
    lda.b scr0
    clc
    adc #8.b
    sta.b scr0                            ; "2P" tag shifted right
    rep #$20
    .ACCU 16
    lda #Str2P.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda tblbank.b
    sta.b scr2+2
    jsr SelTagOam
SDO_team:
    ; ---------- team pick marks (fill the picked cells) ----------
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #2
    beq SDO_team_mode
    jmp SDO_faces
SDO_team_mode:
    rep #$20
    .ACCU 16
    stz.b scr6                            ; pick slot (word -- idx16 loads
    sep #$20                              ;   scr6+1 alongside scr6)
    .ACCU 8
    lda.w JOIN_ACTIVE                     ; P2 joined mid-fight: P1's trio is
    beq SDO_tm                            ;   preserved, so T_STEP belongs to
    lda.w JOIN_SIDE                       ;   P2 and must not mark P1's cells
    beq SDO_tm
    jmp SDO_tm2_begin
SDO_tm:
    sep #$20
    .ACCU 8
    lda.b scr6
    cmp.w T_STEP
    bcs SDO_tm2_begin
    ldy.b scr6
    lda.w T_TEAM1,y                       ; picked char -> its cell
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelChrCell,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellX,x
    clc
    adc #8.b
    sta.b scr0
    lda.l SelCellY,x
    clc
    adc #8.b
    sta.b scr1
    lda #SEL_FILL_TILE.b
    sta.b scr3
    lda #$34.b
    sta.b scr4
    jsr MtCell
    rep #$20
    .ACCU 16
    inc.b scr6
    bra SDO_tm
SDO_tm2_begin:
    sep #$20
    .ACCU 8
    lda.w T_PICK_SIDE
    beq SDO_faces
    rep #$20
    .ACCU 16
    stz.b scr6
SDO_tm2:
    sep #$20
    .ACCU 8
    lda.b scr6
    cmp.w T_STEP
    bcs SDO_faces
    ldy.b scr6
    lda.w T_TEAM2,y
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelChrCell,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellX,x
    clc
    adc #8.b
    sta.b scr0
    lda.l SelCellY,x
    clc
    adc #8.b
    sta.b scr1
    lda #SEL_FILL_TILE.b
    sta.b scr3
    lda #$36.b
    sta.b scr4
    jsr MtCell
    rep #$20
    .ACCU 16
    inc.b scr6
    bra SDO_tm2
SDO_faces:
    ; ---------- face-window names ----------
    rep #$20
    .ACCU 16
    stz.b scr6                            ; side loop
SDO_floop:
    sep #$20
    .ACCU 8
    ldx.b scr6
    lda.w SFACE1,x                        ; char shown in this face window
    bmi SDO_fnext
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    tax
    lda.l SelStrTab,x
    sta.b scr2
    sep #$20
    .ACCU 8
    lda tblbank.b
    sta.b scr2+2
    ; centered under the 48px window: x = winx + (48 - len*8)/2
    lda.b [scr2]                          ; name length
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    asl a
    asl a                                 ; len*8
    sta.b scr4
    lda #48.w
    sec
    sbc.b scr4
    lsr a                                 ; (48-len*8)/2
    clc
    adc #(SEL_FACEL*8).w
    ldy.b scr6
    beq +
    clc
    adc #((SEL_FACER-SEL_FACEL)*8).w
+   sta.b scr0
    sep #$20
    .ACCU 8
    lda #SEL_NAMEY.b
    sta.b scr1
    ldx.b scr6                            ; locked -> yellow name
    lda.b lock1,x
    beq +
    lda #$32.b
    bra ++
+   lda #$30.b
++  sta.b scr4
    jsr MtStr
SDO_fnext:
    rep #$20
    .ACCU 16
    inc.b scr6
    lda.b scr6
    cmp #2.w
    beq +
    jmp SDO_floop
+   ; ---------- CPU difficulty readout (bottom, centred) ----------
    ; "LEVEL X" is 7 cells (56 px); x=100 centres it exactly in 256 px.
    ; Draw the digit first so the variable-length string cannot clobber it.
    ; Show the OPTIONS scale (1..8), not the internal AI level (8 -> 9).
    lda DIFFICULTY
    clc
    adc #27
    sta.b scr3
    lda #148
    sta.b scr0
    lda #212
    sta.b scr1
    lda #$30.b
    sta.b scr4
    jsr MtCell
    rep #$20
    .ACCU 16
    lda #StrLevel.w
    sta.b scr2
    sep #$20
    .ACCU 8
    lda tblbank.b
    sta.b scr2+2
    lda #100
    sta.b scr0
    lda #212
    sta.b scr1
    lda #$30.b
    sta.b scr4
    jsr MtStr
    ; ---------- hide the rest of the used OAM range ----------
    rep #$20
    .ACCU 16
    ldx.b oamtop
    sep #$20
    .ACCU 8
-   cpx #192.w
    bcs +
    lda #$F0.b
    sta.w OAMBUF+1,x
    inx
    inx
    inx
    inx
    bra -
+   sep #$20
    .ACCU 8
    rts

; ---------------------------------------------------------------------------
; Cursor move: X = side (0/1), A16 = joy edges for that pad.  The code lives
; in a separate bank so the already-full Fight section has room for the
; select-screen MSU gating; this stub keeps the original jsr call sites.
; ---------------------------------------------------------------------------
SelMove:
    jsl SelMoveFar
    rts

; Same-bank trampoline for the far cursor routine.
SfxPlayFar:
    jsr SfxPlay
    rtl

; probe the MSU-1 port once at boot: seek to 0 and read back the
; "KOF98MSU" signature that heads the data file.  This validates both
; the cartridge port and the presence of the right .msu file; without
; it msuok stays 0 and the external-chr cells refuse to lock.
MsuDetect:
    sep #$20
    .ACCU 8
    stz.b msuok
    lda #0
    sta.l $2000                         ; seek offset 0
    sta.l $2001
    sta.l $2002
    sta.l $2003
    ldx #$FFFF.w                        ; bounded wait for the seek
-   lda.l $2000
    bpl +
    dex
    bne -
    rts                                 ; no port: msuok stays 0
+   rep #$20
    .ACCU 16
    lda #MsuSig.w
    sta cptr
    sep #$20
    .ACCU 8
    lda #:MsuSig
    sta cptr+2
    ldy #0
-   lda.l $2001                         ; sequential data byte
    cmp [cptr],y
    bne MD_no
    iny
    cpy #10                             ; signature + 16-bit layout CRC
    bne -
    lda #1
    sta.b msuok
MD_no:
    rts
.IFNDEF MSU_LAYOUT
.DEFINE MSU_LAYOUT $FFFF                ; stale/partial generated data: never
                                        ;   accept the .msu at boot
.ENDIF
MsuSig: .byte "KOF98MSU"
        .dw MSU_LAYOUT

; A = char id -> A = descriptor CH_CHRFLAG byte.  Clobbers X, Y, cptr.
CharFlags:
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    tax
    lda.l CharSelTab,x
    sta cptr
    sep #$20
    .ACCU 8
    lda tblbank.b
    sta cptr+2
    ldy #CH_CHRFLAG
    lda [cptr],y
    rts

; lock the side's pick: selN = char under the cursor.  X = side (0/1).
SelLockN:
    sep #$20
    .ACCU 8
    stx.b scr6
SL_cell:
    ldx.b scr6
    lda.w SCUR1,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    bpl +
    jmp SL_denied                         ; $FF: empty cell can't lock
+   sta.b scr5                            ; candidate char id
    ; Hidden Omega Rugal: L+R held on the Rugal cell selects id 14.  This
    ; is ROM-resident, so it works with or without the MSU file.  With MSU
    ; absent the cell stays on the cursor path (see SelMoveFar) but a plain
    ; A press is denied: the normal Rugal form needs streamed CHR.
    lda.b scr5
    cmp #3.b
    bne SL_not_rugal
    rep #$20
    .ACCU 16
    lda.b scr6
    and #$00FF.w
    beq +
    lda #FP2OFS.w
+   tax
    lda FP+F_JOY,x                        ; held buttons (not edges)
    and #(JOY_L|JOY_R).w
    cmp #(JOY_L|JOY_R).w
    sep #$20
    .ACCU 8
    bne SL_not_rugal
    lda #14.b
    sta.b scr5
SL_not_rugal:
    ; Kyo EX variants: L = Nests, R = Ash.  Only on the Kyo cell and only
    ; with the MSU data file present; otherwise the normal Kyo pick stands.
    lda.b scr5
    cmp #KYO_BASE_ID.b
    bne SL_ckmsu
    lda.b msuok
    beq SL_ckmsu
    rep #$20
    .ACCU 16
    lda.b scr6
    and #$00FF.w
    beq +
    lda #FP2OFS.w
    tax
    bra ++
+   ldx #0
++  lda FP+F_JOY,x
    and #(JOY_L|JOY_R).w
    sep #$20
    .ACCU 8
    cmp #JOY_L.b
    bne +
    lda #KYO_NESTS_ID.b
    sta.b scr5
    bra SL_ckmsu
+   cmp #JOY_R.b
    bne SL_ckmsu
    lda #KYO_ASH_ID.b
    sta.b scr5
SL_ckmsu:
    ; ROM-resident hidden Omega must lock with or without the MSU file.
    lda.b scr5
    cmp #14.b
    beq SL_ok
    ; MSU-gated chr (CH_CHRFLAG bit0) can't lock without the cartridge
    lda.b msuok
    bne SL_ok
    lda.b scr5
    jsr CharFlags
    and #$01.b
    bne SL_denied                         ; external chr + no MSU -> deny
SL_ok:
    ldx.b scr6
    lda.b scr5
    sta.b sel1,x                          ; sel1/sel2 are adjacent DP bytes
    lda #1
    sta.b lock1,x
    lda #SFX_SELECT.b
    jsr SfxPlay
    sep #$20
    .ACCU 8
    rts
SL_denied:
    lda #SFX_BACK.b
    jsr SfxPlay
    sep #$20
    .ACCU 8
    rts

; CPU auto-lock: X = side (0/1).  Without MSU a CPU cursor parked on an
; MSU-gated char would be denied forever, so hop to a random legal cell
; first, then lock.
SelLockCpu:
    sep #$20
    .ACCU 8
    stx.b scr5                            ; side
    lda.w G_MODE
    cmp #1
    beq SLC_solo
    cmp #4
    beq SLC_solo
    cmp #5
    bne SLC_regular
SLC_solo:
    lda.b scr5
    beq SLC_regular                       ; campaign P2 keeps its CpuPool pick
    lda #1
    sta.b lock2
    rts
SLC_regular:
    lda.b msuok
    bne SLC_go                            ; msu present -> anything legal
SLC_try:
    ldx.b scr5
    lda.w SCUR1,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    bmi SLC_roll                          ; empty cell -> reroll
    jsr CharFlags                         ; flag bit0; clobbers X,Y,cptr
    and #$01.b
    beq SLC_go
SLC_roll:
    inc.b rng                           ; each attempt must differ, else an
    lda.b rng                           ;   MSU/empty landing loops forever
    clc
    adc.b framecnt
-   cmp #SEL_NCELLS.b
    bcc +
    sec
    sbc #SEL_NCELLS.b
    bra -
+   ldx.b scr5
    sta.w SCUR1,x
    bra SLC_try
SLC_go:
    ldx.b scr5
    jsr SelLockN
    rts

; names follow the cursors: track which char each side's cursor sits on
; (SFACE1/2 feeds the OBJ name row in SelDrawOam).
SelFaceSync:
    rep #$20
    .ACCU 16
    stz.b scr4                            ; side
SFS_loop:
    sep #$20
    .ACCU 8
    ldx.b scr4
    lda.w SCUR1,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    bpl +
    ldx.b scr4
    lda.w SFACE1,x                        ; empty cell: keep the last char
    bra SFS_cmp
+   cmp #3.b                              ; Rugal cell
    bne SFS_cmp
    lda.b msuok
    bne SFS_keep_rugal                    ; with MSU: normal Rugal name
    lda #14.b                             ; without MSU: the cell is Omega
    bra SFS_cmp
SFS_keep_rugal:
    lda #3.b
SFS_cmp:
    ldx.b scr4
    cmp.w SFACE1,x
    beq SFS_next
    sta.w SFACE1,x
SFS_next:
    rep #$20
    .ACCU 16
    inc.b scr4
    lda.b scr4
    cmp #2.w
    bne SFS_loop
    sep #$20
    .ACCU 8
    rts

; SELECT on the select screen cycles the OPTIONS difficulty 1..8 (P1 pad).
; ApplyDifficulty maps 8 to the internal AI level 9.
SelLevelTick:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    and #JOY_SE.w
    beq +
    sep #$20
    .ACCU 8
    lda DIFFICULTY
    inc a
    cmp #9
    bcc ++
    lda #1
++  sta DIFFICULTY
    jsl ApplyDifficulty
    sep #$20
    .ACCU 8
    lda #SFX_MOVE.b
    jsr SfxPlay
+   sep #$20
    .ACCU 8
    rts

SelTick:
    sep #$20
    .ACCU 8
    jsr SelLevelTick
    lda.w G_MODE
    cmp #2
    bne +
    jmp TeamSelTick                       ; 3-pick team selection owns the pad
+   lda.w G_MODE
    cmp #3
    bne +
    jmp TeamVsSelTick                     ; both sides choose three fighters
+   ; ---------- START: join the P1 side ----------
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    and #JOY_ST.w
    beq ST_nostart1
    sep #$20
    .ACCU 8
    lda.b cpu1
    beq ST_nostart1
    stz.b cpu1
    stz.b lock1                           ; joining always un-locks
    lda #SFX_SELECT.b
    jsr SfxPlay
ST_nostart1:
    ; ---------- B: undo pick / hand P1 back to CPU ----------
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    and #JOY_B.w
    beq ST_nob1
    sep #$20
    .ACCU 8
    lda.b cpu1
    bne ST_nob1
    lda.w JOIN_ACTIVE
    beq ST_b1_ok
    lda.w JOIN_SIDE
    bne ST_nob1                           ; P1 waits while P2 joins
ST_b1_ok:
    lda.b lock1
    beq +
    stz.b lock1                           ; undo the pick, stay human
    bra ST_back1
    lda.w G_MODE
    beq ST_nob1                           ; VS controls never hand off to CPU
    lda #1                                ; still choosing -> back to CPU
    sta.b cpu1
    lda.b framecnt
    clc
    adc #60.b
    sta.w SCPUT1                          ; CPU locks ~1s after taking over
ST_back1:
    lda #SFX_BACK.b
    jsr SfxPlay
ST_nob1:
    ; ---------- P1 move: own cursor, or the foe's after locking ----------
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    and #$0F00.w
    beq ST_nop1move
    sep #$20
    .ACCU 8
    lda.b lock1
    beq +
    lda.w G_MODE                          ; locked P1 in solo campaign steers
    cmp #1                                ;   the CPU opponent's cell
    beq ST_steerfoe
    cmp #4
    beq ST_steerfoe
    cmp #5
    bne ST_nop1move
ST_steerfoe:
    lda.b cpu2                            ; P1 only steers this cursor before
    beq ST_nop1move                       ;   P2 joins the campaign
    lda.b lock2
    bne ST_nop1move
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    ldx #1
    jsr SelMove
    bra ST_nop1move
+   lda.b cpu1
    bne ST_nop1move
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    ldx #0
    jsr SelMove
ST_nop1move:
    ; ---------- P1 lock (face buttons; B cancels, START joins) ----------
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    and #(JOY_A|JOY_X|JOY_Y).w
    beq ST_nolock1
    sep #$20
    .ACCU 8
    lda.b cpu1
    bne ST_nolock1
    lda.b lock1
    bne ST_nolock1
    ldx #0
    jsr SelLockN
ST_nolock1:
    ; ---------- P2 pad: joins campaign or versus mode ----------
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #2
    bne ST_pad2_ready
    jmp ST_cpuflow                        ; Team Play owns Pad2 in TeamSelTick
ST_pad2_ready:
ST_pad2:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    and #JOY_ST.w
    beq ST_nostart2
    sep #$20
    .ACCU 8
    lda.b cpu2
    beq ST_nostart2
    stz.b cpu2
    stz.b lock2
    lda #SFX_SELECT.b
    jsr SfxPlay
ST_nostart2:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    and #JOY_B.w
    beq ST_nob2
    sep #$20
    .ACCU 8
    lda.b cpu2
    bne ST_nob2
    lda.w JOIN_ACTIVE
    beq ST_b2_ok
    lda.w JOIN_SIDE
    beq ST_nob2                           ; P2 waits while P1 joins
ST_b2_ok:
    lda.b lock2
    beq +
    stz.b lock2
    bra ST_back2
    lda.w G_MODE
    beq ST_nob2                           ; VS controls never hand off to CPU
    lda #1
    sta.b cpu2
    lda.b framecnt
    clc
    adc #60.b
    sta.w SCPUT2
ST_back2:
    lda #SFX_BACK.b
    jsr SfxPlay
ST_nob2:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    and #$0F00.w
    beq +
    sep #$20
    .ACCU 8
    lda.b cpu2
    bne +
    lda.b lock2
    bne +
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    ldx #1
    jsr SelMove
+   rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    and #(JOY_A|JOY_X|JOY_Y).w
    beq ST_cpuflow
    sep #$20
    .ACCU 8
    lda.b cpu2
    bne ST_cpuflow
    lda.b lock2
    bne ST_cpuflow
    ldx #1
    jsr SelLockN
ST_cpuflow:
    ; ---------- CPU sides auto-lock at their deadlines ----------
    sep #$20
    .ACCU 8
    lda.b cpu1
    beq +
    lda.b lock1
    bne +
    lda.b framecnt
    cmp.w SCPUT1
    bcc +
    ldx #0
    jsr SelLockCpu
+   lda.b cpu2
    beq ++
    lda.w G_MODE                          ; versus waits for Pad2 START
    beq ++
    cmp #3
    beq ++
    lda.b lock2
    bne ++
    lda.b framecnt
    cmp.w SCPUT2
    bcc ++
    ldx #1
    jsr SelLockCpu
++  jsr SelFaceSync                       ; names follow the cursors
    ; ---------- both locked -> fight ----------
    lda.b lock1
    beq ST_refresh
    lda.b lock2
    beq ST_refresh
    lda.w JOIN_ACTIVE
    beq +
    jsr JoinFinish                        ; mid-fight join: preserve the
    rts                                   ;   waiting side's pick and restart
+   lda.w YL_REPICK                       ; YOU LOSE re-pick: campaign continues
    beq +
    jsl YouLoseRepickDone
    rts
+   lda.w G_MODE                          ; campaign modes begin via CampStart
    beq +
    jsr CampStart
+   jsr StartFight
    rts
ST_refresh:
    jsr SelDrawOam
    rts

; ---------------------------------------------------------------------------
; Mid-fight join (Single Play / Team Play).  START on a CPU-driven pad opens
; the character select for that side; the side already fighting keeps its
; current pick (single) or trio (team) and waits locked.  Both modes restart
; the confrontation with full health once the newcomer confirms.
; ---------------------------------------------------------------------------
FightJoinCheck:
    sep #$20
    .ACCU 8
    lda.b pausecnt
    bne FJC_no
    lda.w G_MODE
    cmp #1
    beq FJC_mode
    cmp #2
    bne FJC_no
FJC_mode:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    and #JOY_ST.w
    beq FJC_p2
    sep #$20
    .ACCU 8
    lda.b cpu1
    beq FJC_p2
    stz.w JOIN_SIDE
    bra FJC_enter
FJC_p2:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    and #JOY_ST.w
    beq FJC_no
    sep #$20
    .ACCU 8
    lda.b cpu2
    beq FJC_no
    lda #1
    sta.w JOIN_SIDE
FJC_enter:
    jsr JoinEnter
    sec
    rts
FJC_no:
    sep #$20
    .ACCU 8
    clc
    rts

JoinEnter:
    sep #$20
    .ACCU 8
    lda #1
    sta.w JOIN_ACTIVE
    lda.w JOIN_SIDE
    bne JE_cpu2
    stz.b cpu1                            ; the joining pad takes P1 back
    bra JE_cpu_done
JE_cpu2:
    stz.b cpu2
JE_cpu_done:
    lda.w G_MODE
    cmp #2
    beq JE_team
    bra JE_audio

JE_team:
    lda.w JOIN_SIDE
    sta.w T_PICK_SIDE                     ; the newcomer picks the trio
    stz.w T_STEP
    stz.w T_START
    stz.w T_LASTFRAME
    rep #$20                              ; seed both cursors/faces from the
    .ACCU 16                              ;   members currently in the fight
    lda.w T_I1
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w T_TEAM1,x
    sta.b sel1
    rep #$20
    .ACCU 16
    lda.w T_I2
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w T_TEAM2,x
    sta.b sel2

JE_audio:
    ; Keep the stage module playing while the joiner picks.  Swapping to the
    ; select theme here forces StartFight to reload the stage module right
    ; after the pick; on SNESMOD that second spcLoad can hang waiting for the
    ; APU and leave the join stuck on the select screen.  MUSIC_VALID stays
    ; set, so StartFight's StageMusic is a no-op for the same stage.
    jsr ShowSelect
    sep #$20                              ; the side already fighting waits
    .ACCU 8                               ;   locked; the newcomer is free
    lda.w JOIN_SIDE
    bne JE_lock1
    lda #1
    sta.b lock2
    stz.b lock1
    bra JE_locked
JE_lock1:
    lda #1
    sta.b lock1
    stz.b lock2
JE_locked:
    rep #$20
    .ACCU 16
    lda #5
    sta.b gamestate
    rts

; Selection finished for a mid-fight join: keep the waiting side's character
; or trio, give the newcomer its fresh pick, and restart the bout at full HP.
JoinFinish:
    sep #$20
    .ACCU 8
    stz.w JOIN_ACTIVE
    stz.b cpu1
    stz.b cpu2
    stz.b lock1
    stz.b lock2
    stz.b wins1
    stz.b wins2
    stz.b nextflag
    stz.b pausecnt
    stz.b shaketmr
    lda #1
    sta.b roundno
    sta.w C_PVP                           ; winner continues the campaign
    stz.w MATWON
    stz.w C_WHARF
    stz.w T_SWAP
    lda.w JOIN_SIDE
    eor #1
    sta.w C_HUMAN_SIDE                    ; the waiting side carries on
    lda.w G_MODE
    cmp #2
    bne JF_single
    stz.w T_I1                            ; both trios start from member 1
    stz.w T_I2
    lda #3
    sta.w T_N2
JF_single:
    jsr StartFight
    rts

; TEAM VS selection: P1 chooses three fighters, then P2 chooses three.
; Both sides are human from the start; the shared cursor rings and cell data
; are reused.
TeamVsSelTick:
    sep #$20
    .ACCU 8
    lda.w T_START
    beq TVS_normal
    lda.b framecnt
    cmp.w T_LASTFRAME
    beq TVS_wait
    sta.w T_LASTFRAME
    dec.w T_START
    bne TVS_wait
    jsr StartFight
    rts
TVS_wait:
    rts
TVS_normal:
TVS_side:
    sep #$20
    .ACCU 8
    lda.w T_PICK_SIDE
    sta.b scr5
    beq TVS_p1
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    bra TVS_input
TVS_p1:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
TVS_input:
    sta.b scr4
    and #$0F00.w
    beq TVS_confirm
    lda.b scr4
    ldx.b scr5
    jsr SelMove
TVS_confirm:
    rep #$20
    .ACCU 16
    lda.b scr4
    and #(JOY_A|JOY_X|JOY_Y).w
    bne TVS_confirm_pick
    jmp TVS_cancel
TVS_confirm_pick:
    sep #$20
    .ACCU 8
    lda.w T_STEP
    cmp #3
    bcc TVS_have_slot
    jmp TVS_draw
TVS_have_slot:
    ldx.b scr5
    lda.w SCUR1,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    bpl TVS_candidate_ok
    jmp TVS_deny
TVS_candidate_ok:
    sta.b scr0
    ; Hidden Omega Rugal: L+R on the Rugal cell selects the ROM-resident
    ; omega form, exactly like Team Play.  Plain A still follows the MSU
    ; gate below, so normal Rugal stays unavailable without the data file.
    lda.b scr0
    cmp #3.b
    bne TVS_candidate_msu
    rep #$20
    .ACCU 16
    lda.b scr5                            ; side (0/1)
    and #$00FF.w
    beq +
    lda #FP2OFS.w
+   tax
    lda FP+F_JOY,x
    and #(JOY_L|JOY_R).w
    cmp #(JOY_L|JOY_R).w
    sep #$20
    .ACCU 8
    bne TVS_candidate_msu
    lda #14.b
    sta.b scr0
TVS_candidate_msu:
    lda.b msuok
    bne TVS_dup
    lda.b scr0
    jsr CharFlags
    and #$01.b
    beq TVS_dup
    jmp TVS_deny
TVS_dup:
    lda.w T_STEP
    sta.b scr6
    stz.b scr6+1
    rep #$20
    .ACCU 16
    ldy #0
TVS_dup_loop:
    cpy.b scr6
    bcs TVS_store
    sep #$20
    .ACCU 8
    lda.b scr5
    beq TVS_dup_p1
    lda.w T_TEAM2,y
    bra TVS_dup_cmp
TVS_dup_p1:
    lda.w T_TEAM1,y
TVS_dup_cmp:
    cmp.b scr0
    bne TVS_dup_next
    jmp TVS_deny
TVS_dup_next:
    rep #$20
    .ACCU 16
    iny
    bra TVS_dup_loop
TVS_store:
    sep #$20
    .ACCU 8
    lda.b scr5
    beq TVS_store_p1
    ldy.w T_STEP
    lda.b scr0
    sta.w T_TEAM2,y
    bra TVS_store_done
TVS_store_p1:
    ldy.w T_STEP
    lda.b scr0
    sta.w T_TEAM1,y
TVS_store_done:
    inc.w T_STEP
    lda.w T_STEP
    cmp #3
    bcs TVS_full_team
    lda #SFX_SELECT.b
    jsr SfxPlay
    jmp TVS_draw
TVS_full_team:
    lda.b scr5
    bne TVS_p2_full
    lda #SFX_SELECT.b
    jsr SfxPlay
    lda #1
    sta.w T_PICK_SIDE
    stz.w T_STEP
    lda #1
    sta.b lock1
    bra TVS_draw
TVS_p2_full:
TVS_done:
    lda #1
    sta.b lock2
    stz.w T_SWAP
    stz.w T_I1
    stz.w T_I2
    lda #3
    sta.w T_N2
    stz.b wins1
    stz.b wins2
    lda #1
    sta.b roundno
    stz.b nextflag
    lda #8
    sta.w T_START
    lda.b framecnt
    sta.w T_LASTFRAME
    rts
TVS_deny:
    lda #SFX_BACK.b
    jsr SfxPlay
    bra TVS_draw
TVS_cancel:
    rep #$20
    .ACCU 16
    lda.b scr4
    and #JOY_B.w
    beq TVS_draw
    sep #$20
    .ACCU 8
    lda.w T_STEP
    beq TVS_draw
    dec.w T_STEP
TVS_draw:
    jsr SelFaceSync
    jsr SelDrawOam
    rts

; Match-over banner at row 8: the wins leader's name + "WINS", or "DRAW".
DrawBanner:
    sep #$20
    .ACCU 8
    lda wins1
    cmp wins2
    bne +
    jmp DB_draw
+   sep #$20                            ; lda/sta keep the carry from cmp
    .ACCU 8
    bcc +
    lda sel1
    bra ++
+   lda sel2
++  rep #$20                            ; "<name> WINS" centred as a unit:
    .ACCU 16                            ;   col = (32 - (len+5)) / 2
    and #$00FF.w
    asl a
    tax
    lda.l SelBStrTab,x
    sta scr2
    sep #$20
    .ACCU 8
    lda tblbank
    sta scr2+2
    ldy #0
    lda [scr2],y                        ; name length
    rep #$20
    .ACCU 16
    and #$00FF.w
    sta scr6                            ; namelen
    clc
    adc #5.w                            ; + " WINS"
    sta scr5
    lda #32.w
    sec
    sbc scr5
    lsr a
    sta scr5                            ; start col
    clc
    adc #(8*32).w
    asl a
    sta scr0
    jsr WriteStrBigData
    rep #$20                            ; WINS one cell past the name
    .ACCU 16
    lda scr5
    clc
    adc scr6
    ina
    adc #(8*32).w
    asl a
    sta scr0
    lda #BStrWins.w
    sta scr2
    jsr WriteStrBigData
    ; winner's victory quote: two centred rows picked by framecnt>>3 and
    ; Q_LANG.  fofs selects the winning fighter's descriptor, whose CH_QUOTE
    ; field holds the low address inside the shared QuoteTables bank.
    sep #$20
    .ACCU 8
    lda wins1
    cmp wins2
    bcc +
    stz fofs
    bra ++
+   lda #FP2OFS.b
    sta fofs
++  ldy #CH_QUOTE
    ldx #scr2
    jsr CharPtr                         ; scr2 = QuoteTab low address
    ; QuoteTab lives in the shared QuoteTables bank; CharPtr returned
    ; the low address from the descriptor, so replace its bank byte.
    sep #$20
    .ACCU 8
    lda.b #:ioriQuoteTab
    sta scr2+2
    rep #$20
    .ACCU 16
    lda framecnt
    lsr a
    lsr a
    lsr a
    and #$0003.w
    sta scr6
    asl a
    clc
    adc scr6
    asl a                               ; quote slot offset (x6)
    sta scr6
    sep #$20
    .ACCU 8
    lda.w Q_LANG
    and #$03.b
    rep #$20
    .ACCU 16
    and #$0003.w
    asl a
    asl a
    asl a                               ; language * 8
    sta scr5
    asl a
    clc
    adc scr5                            ; language block: 4 pairs x 6 bytes
    clc
    adc scr6
    tay
    ; Copy the table pointer before scr2 is reused for the string.
    lda scr2
    sta qtab
    sep #$20
    .ACCU 8
    lda scr2+2
    sta qtab+2
    lda [qtab],y                        ; row A: 24-bit far pointer
    sta scr2
    iny
    lda [qtab],y
    sta scr2+1
    iny
    lda [qtab],y
    sta scr2+2
    iny
    lda [qtab],y                        ; row B: keep for the second call
    sta qrow
    iny
    lda [qtab],y
    sta qrow+1
    iny
    lda [qtab],y
    sta qrow+2
    rep #$20
    .ACCU 16
    lda #12.w
    jsr DrawQuoteRow
    sep #$20
    .ACCU 8
    lda qrow
    sta scr2
    lda qrow+1
    sta scr2+1
    lda qrow+2
    sta scr2+2
    rep #$20
    .ACCU 16
    lda #14.w
    jsr DrawQuoteRow
    rts
; A = HUD row, scr2 = quote string (24-bit far pointer into a quote bank).
; Centres the row; empty strings (len 0) are skipped.
DrawQuoteRow:
    asl a
    asl a
    asl a
    asl a
    asl a                               ; scr5 = row*32 cells
    sta scr5
    ldy #0
    sep #$20
    .ACCU 8
    lda [scr2],y                        ; len byte
    beq DQ_out
    sta scr4
    stz scr4+1
    rep #$20
    .ACCU 16
    lda #32.w
    sec
    sbc scr4
    lsr a                               ; x = (32-len)/2 cells
    clc
    adc scr5
    asl a                               ; cell index -> map byte offset
    sta scr0
    jsr WriteStr                        ; scr2 already carries the bank
    rep #$20
    .ACCU 16
    rts
DQ_out:
    rep #$20
    .ACCU 16
    rts
DB_draw:
    rep #$20
    .ACCU 16
    lda #((8*32+14)*2).w
    sta scr0
    lda #BStrDraw.w
    sta scr2
    jsr WriteStrBigData
    rts

TitleTick:
    sep #$20
    .ACCU 8
    lda nextflag
    bne +                                 ; real title screen (menucore):
    jmp TitleTickNew                      ;   PRESS START -> mode menu
+   cmp #1                                ; intermission ignores pad input;
    bne TT_check_winner
    jmp TT_auto                           ;   select is a real-title thing
TT_check_winner:
    cmp #2                                ; match-over/intermediate victory:
    bne TT_auto
    lda.b winvoice                        ; the winner module's effects load a
    beq +                                 ;   few frames after the song swap
    lda.l $7E46F8
    bne +
    stz.b winvoice
    lda.w UI_SFXLOAD
    beq +
    lda #SFX_WIN.b
    jsr SfxPlay
+   rep #$20
    .ACCU 16
    inc.w WIN_TIMER
TT_win_timer:
    rep #$20
    .ACCU 16
    lda.w WIN_TIMER
    cmp #420.w                            ; seven seconds at 60 frames/second
    bcc TT_win_wait
    sep #$20
    .ACCU 8
    jmp TT_start
TT_win_wait:
    sep #$20
    .ACCU 8
    rts
TT_auto:
    sep #$20
    .ACCU 8
    lda framecnt                        ; auto-enter fight at frame 60
    cmp #60
    bne TT_out
TT_start:
    sep #$20
    .ACCU 8
    lda nextflag
    cmp #1
    beq TT_go                           ; intermission -> keep the score
    lda.w G_MODE                        ; only campaign modes resolve a route
    cmp #1
    beq TT_campaign
    cmp #2
    beq TT_campaign
    cmp #4
    beq TT_campaign
    cmp #5
    beq TT_campaign
    bra TT_free
TT_campaign:
    jsr CampResolve
    rts
TT_free:
    stz wins1                           ; fresh match
    stz wins2
    lda #1
    sta roundno
    stz.w T_STEP
    stz.w T_PICK_SIDE
    stz.w T_START
    stz.w T_LASTFRAME
    stz.w T_I1
    stz.w T_I2
    stz.w T_SWAP
    stz.b cpu1
    lda.w G_MODE
    beq TT_free_vs
    cmp #3
    beq TT_free_vs
    lda #1                              ; campaigns return with optional P2
    sta.b cpu2
    bra TT_free_cpu_ready
TT_free_vs:
    stz.b cpu2                          ; VS returns with both human pads
TT_free_cpu_ready:
    lda #SONG_KOF.b                     ; the select theme returns with the
    jsr MusPlaySong                     ;   screen (single VS / team VS);
    stz.w MUSIC_VALID                   ;   ShowSelect queues the matching
    stz nextflag                        ;   "select" voice behind it
    jsr ShowSelect                      ; -> character select (gs 5)
    rep #$20                            ;   (ShowSelect returns acc16; keep
    .ACCU 16                            ;    lda #5 word-sized)
    lda #5
    sta gamestate
    rts
TT_go:
    stz nextflag
    jsr StartFight
TT_out:
    rts

; ---------------------------------------------------------------------------
StartFight:
    jsr VoiceQueueDrop                   ; no queued quote may follow us;
    sep #$20                             ;   StageMusic finishes an active one
    .ACCU 8                              ;   before rewriting SPC RAM
    lda #0
    sta.b hudband                       ; select-screen scratch shares $8B:
    rep #$10                            ;   start the live flush at a valid band
    .INDEX 16
    lda.w G_MODE
    cmp #2
    bcc SF_not_team
    cmp #4
    bcs SF_full
    lda.w T_SWAP                          ; team member-out: partial reset,
    beq SF_full                           ;   not a fresh confrontation
    jmp TeamSwap                          ;   (TeamSwap clears T_SWAP)
SF_not_team:
SF_full:
    jsr PpuInit                          ; select screen changed BG/OBJ bases
    jsr LoadStaticGfx                    ; restore HUD, sparks and static tiles
    rep #$20
    .ACCU 16
    lda #80<<8.w
    sta FP+F_X
    lda #176<<8.w
    sta FP+F_X+FP2OFS
    stz FP+F_Y
    stz FP+F_Y+FP2OFS
    stz FP+F_VX
    stz FP+F_VX+FP2OFS
    stz FP+F_VY
    stz FP+F_VY+FP2OFS
    stz FP+F_GRAB
    stz FP+F_GRAB+FP2OFS
    stz FP+F_HITVX
    stz FP+F_HITVX+FP2OFS
    stz FP+F_HITVY
    stz FP+F_HITVY+FP2OFS
    stz FP+F_META
    stz FP+F_META+FP2OFS
    sep #$20
    .ACCU 8
    stz FP+F_TFLAGS
    stz FP+F_TFLAGS+FP2OFS
    stz FP+F_DMAREQ
    stz FP+F_DMAREQ+FP2OFS
    stz FP+F_DMAPOS
    stz FP+F_DMAPOS+FP2OFS
    stz FP+F_TILEPG
    stz FP+F_TILEPG+FP2OFS
    stz FP+F_MAX
    stz FP+F_MAX+FP2OFS
    lda #$FF.b                          ; invalid sentinel: force first sprite upload
    sta FP+F_PSPRID
    sta FP+F_PSPRID+FP2OFS
    sta FP+F_PSPRID_H
    sta FP+F_PSPRID_H+FP2OFS
    stz FP+F_PXOFF
    stz FP+F_PXOFF+FP2OFS
    stz FP+F_PYOFF
    stz FP+F_PYOFF+FP2OFS
    stz FP+F_PFLAGS
    stz FP+F_PFLAGS+FP2OFS
    stz FP+F_VMUL
    stz FP+F_VMUL+FP2OFS
    stz FP+F_HIST                       ; empty command rings
    stz FP+F_HIST+FP2OFS
    stz FP+F_LASTCT
    stz FP+F_LASTCT+FP2OFS
    stz combohit                        ; fresh confrontation: drop any count
    stz combohit+FP2OFS                 ;   left in WRAM (the select screen
    stz combotmr                        ;   bypasses ShowTitle/ST_select, so
    stz combotmr+FP2OFS                 ;   the first round would draw garbage)
    rep #$20
    .ACCU 16
    stz.w SPARKS+SPK_ANIM               ; clear both hit-spark slots
    stz.w SPARKS+SPK_ANIM+SPK_SIZE
    ldx #0                              ; drop leftover afterimage slots
-   stz.w GHBUF+4,x
    inx
    inx
    cpx #48.w
    bne -
    lda #0
    ldx #112                            ; clear both 48-entry rings at fofs
                                        ;   stride: $4100 + {0,$40} + 48B
    -   sta.l CMDHIST_L,x
    dex
    dex
    bpl -
    lda #1                              ; P1 faces right (mugen facing is +/-1;
    sta FP+F_FACING                     ;   a 0 would draw right but break
    lda #$FFFF.w                        ;   the facing-relative helpers)
    sta FP+F_FACING+FP2OFS
    lda #MAXHP.w
    sta FP+F_HP
    sta FP+F_HP+FP2OFS
    ; FUSION: meters carry between rounds and team members.  The first round
    ; of a match starts empty; CampReset invalidates the carry otherwise.
    sep #$20
    .ACCU 8
    lda FUS_VALID
    bne SF_carry
    lda #1
    sta FUS_VALID
    lda rng                               ; FUSION team synergy 0/1/2
    inc rng
    and #$03
    cmp #3
    bne +
    lda #2
+   sta FUS_SYN
    lda rng
    inc rng
    and #$03
    cmp #3
    bne +
    lda #2
+   sta FUS_SYN+FP2OFS
    rep #$20
    .ACCU 16
    stz FUS_CARRY
    stz FUS_CARRY+FP2OFS
SF_carry:
    rep #$20
    .ACCU 16
    lda FUS_CARRY
    sta FP+F_POWER
    lda FUS_CARRY+FP2OFS
    sta FP+F_POWER+FP2OFS
    lda #30.w                             ; fresh juggle budget per round
    sta FUS_JUGGLE
    sta FUS_JUGGLE+FP2OFS
    stz FUS_CTR
    sep #$20
    .ACCU 8
    stz FUS_DIZZY
    stz FUS_DIZZY+FP2OFS
    stz FUS_DIZZYT
    stz FUS_DIZZYT+FP2OFS
    stz FUS_COVER
    stz FUS_COVER+FP2OFS
    stz FUS_FLASH
    rep #$20
    .ACCU 16
    jsr CampInitHP                        ; survivor carry / practice setup
    sep #$20                            ; team play: active members pick sels
    .ACCU 8
    lda.w G_MODE
    cmp #2
    bcc +
    cmp #4
    bcs +
    rep #$20                            ; load byte vars via acc16 so the
    .ACCU 16                            ;   index16 tax can't see A's stale
    lda.w T_I1                          ;   high byte (T_I1,T_I2 are bytes)
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w T_TEAM1,x
    sta.b sel1
    rep #$20
    .ACCU 16
    lda.w T_I2
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w T_TEAM2,x
    sta.b sel2
+   rep #$20                            ; sel -> descriptor + table bank
    .ACCU 16                            ;   (0 KYO, 1 IORI, 2 SHINGO, 3 RUGAL)
    lda sel1
    and #$00FF.w
    asl a
    tax
    lda.l CharSelTab,x
    sta FP+F_CHAR
    txa
    lsr a
    tax
    sep #$20
    .ACCU 8
    lda.l BankSelTab,x
    sta FP+F_TBANK
    rep #$20
    .ACCU 16
    lda sel2                            ; same pick for player 2
    and #$00FF.w
    asl a
    tax
    lda.l CharSelTab,x
    sta FP+F_CHAR+FP2OFS
    txa
    lsr a
    tax
    sep #$20
    .ACCU 8
    lda.l BankSelTab,x
    sta FP+F_TBANK+FP2OFS
    jsr LoadPortraits                   ; photos of the active team members
    jsr LoadCharPals                    ; per-side OBJ palettes (0/3/5, 1/4/6)
    jsr ProjFxLoadBoth                  ; invalidate streamed effect pages
    ldx #0
    txa
-   sta HUDMAP,x
    inx
    inx
    cpx #2048.w
    bne -
    ; fight.def: the two 320-pixel lifebar halves and the bottom power
    ; frames are pre-scaled into the generated BG3 maps.
    ldx #0
-   lda.l HudTopMap,x
    sta HUDMAP,x
    inx
    inx
    cpx #(7*32*2).w
    bne -
    jsr PortraitMap
    ldx #0
-   lda.l HudBottomMap,x
    sta HUDMAP+(23*32*2),x
    inx
    inx
    cpx #(4*32*2).w
    bne -
    lda #((4*32+5)*2).w
    sta scr0
    ldx #0
    stx fofs
    ldy #CH_NAME
    ldx #scr2
    jsr NamePtr
    jsr WriteStr
    lda #((4*32+23)*2).w
    sta scr0
    ldx #FP2OFS
    stx fofs
    ldy #CH_NAME
    ldx #scr2
    jsr NamePtr
    jsr WriteStr
    jsr DrawBars
    jsr DrawWins                          ; round-win pips under the names
    jsr DrawLevel                         ; small LEVEL n at the bottom
    jsr CampStage                       ; campaign stage rules -> STAGEF
    lda #1                              ; StagePick must upload the rebuilt
    sta.b stagehold                     ;   HUD map before it shows the stage
    jsr StagePick                       ; random stage: chr+map+pal+anim init
    sep #$20                            ; StagePick returns with A in 8-bit mode
    .ACCU 8
    jsr StageMusic                      ; load + queue that stage's module
    ; Load the stage music before EnterState can enqueue an intro voice.
    ; Otherwise spcFlush may wait on the just-queued voice command forever.
    rep #$20
    .ACCU 16
    stz scr6
    stz scr6+1
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #2.b
    beq SF_intro
    cmp #3.b
    beq SF_intro
    lda.b roundno
    cmp #1.b
    beq SF_intro
    inc scr6
SF_intro:
    rep #$20
    .ACCU 16
    lda scr6                            ; keep the flag across EnterState: its
    sta.b sintro                        ; anim upload uses scr6 as scratch
    ldx #0
    stx fofs
    lda.b sintro
    beq SF_p1_intro
    lda #S_STAND.w
    bra SF_p1_state
SF_p1_intro:
    lda #S_INTRO.w
SF_p1_state:
    jsr EnterState
    ldx #FP2OFS
    stx fofs
    lda.b sintro
    beq SF_p2_intro
    lda #S_STAND.w
    bra SF_p2_state
SF_p2_intro:
    lda #S_INTRO.w
SF_p2_state:
    jsr EnterState
    sep #$20
    .ACCU 8
    lda #$15.b                          ; BG1 stage + BG3 HUD + OBJ
    sta.l TM
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #1.b
    beq SF_gs_solo
    cmp #4.b
    beq SF_gs_solo
    cmp #5.b
    beq SF_gs_solo
    bra SF_gs_intro
SF_gs_solo:
    lda.b roundno
    cmp #1.b
    beq SF_gs_intro
    lda #1                                ; later solo rounds start now
    bra SF_gs_store
SF_gs_intro:
    lda #4                                ; -> IntroTick until both stand
SF_gs_store:
    sta gamestate
    ; Every round starts at 99.  Later solo/campaign rounds skip IntroTick
    ; (gamestate 4), which used to be the only place that reset the clock,
    ; so round 2 inherited the seconds left from round 1.  Reset it here,
    ; at round setup only -- never in FightTick, or the clock never counts.
    sep #$20
    .ACCU 8
    lda #99.b
    sta rsecs
    lda #0
    sta rframe
    lda gamestate
    cmp #1.b
    bne +
    rep #$10                            ; DrawTimer indexes HUDMAP with X16
    .INDEX 16
    jsr DrawTimer
    sep #$20
    .ACCU 8
+   lda huddirty
    ora #HUD_FULL
    sta huddirty
    rts

DrawBars:
    rep #$20
    .ACCU 16
    lda FP+F_HP
    jsr HpToPx
    sta scr5
    sep #$20
    .ACCU 8
    lda FP+F_HP                         ; green >50%, yellow >25%, else red
    ldy #ATT_GRN.w
    cmp #101.b
    bcs +
    ldy #ATT_YEL.w
    cmp #51.b
    bcs +
    ldy #ATT_RED.w
+   sty scr6
    lda #LB_BAR.b
    sta scr3
    rep #$20
    .ACCU 16
    ldx #((2*32+3)*2).w
    jsr FillBar
    rep #$20
    .ACCU 16
    lda FP+F_HP+FP2OFS
    jsr HpToPx
    sta scr5
    sep #$20
    .ACCU 8
    lda FP+F_HP+FP2OFS
    ldy #ATT_GRN.w
    cmp #101.b
    bcs +
    ldy #ATT_YEL.w
    cmp #51.b
    bcs +
    ldy #ATT_RED.w
+   tya
    ora #$40.b                          ; hflip: P2 bar drains toward center
    sta scr6
    lda #LB_BAR.b
    sta scr3
    rep #$20
    .ACCU 16
    ldx #((2*32+28)*2).w
    jsr FillBar
    rep #$20                            ; power bars on the row below the
    .ACCU 16                            ;   life bars
    lda FP+F_POWER
    jsr PowToPx
    sta scr5
    sep #$20
    .ACCU 8
    lda FP+F_MAX
    beq +
    lda #ATT_YEL.b
    bra ++
+   lda #ATT_SIL.b
++  sta scr6
    lda #PB_BAR.b
    sta scr3
    rep #$20
    .ACCU 16
    ldx #((25*32+1)*2).w
    jsr FillBar
    rep #$20
    .ACCU 16
    lda FP+F_POWER+FP2OFS
    jsr PowToPx
    sta scr5
    sep #$20
    .ACCU 8
    lda FP+F_MAX+FP2OFS
    beq +
    lda #(ATT_YEL|$40).b
    bra ++
+   lda #(ATT_SIL|$40).b
++  sta scr6
    lda #PB_BAR.b
    sta scr3
    rep #$20
    .ACCU 16
    ldx #((25*32+30)*2).w
    jsr FillBar
    jsr DrawPowerCounters
    ; Dirty-band selection: only mark the rows whose source values changed.
    ; DrawBars runs every tick, so this is cheap and keeps HP responsive even
    ; when no other HUD event fires.
    sep #$20
    .ACCU 8
    lda FP+F_HP
    cmp.w TEL_HP1
    beq +
    sta.w TEL_HP1
    lda huddirty
    ora #HUD_LIFE
    sta huddirty
+   lda FP+F_HP+FP2OFS
    cmp.w TEL_HP2
    beq +
    sta.w TEL_HP2
    lda huddirty
    ora #HUD_LIFE
    sta huddirty
+   rep #$20
    .ACCU 16
    lda FP+F_POWER
    cmp.w TEL_POW1
    beq +
    sta.w TEL_POW1
    sep #$20
    .ACCU 8
    lda huddirty
    ora #HUD_POWCNT|HUD_POWER
    sta huddirty
    rep #$20
    .ACCU 16
+   lda FP+F_POWER+FP2OFS
    cmp.w TEL_POW2
    beq +
    sta.w TEL_POW2
    sep #$20
    .ACCU 8
    lda huddirty
    ora #HUD_POWCNT|HUD_POWER
    sta huddirty
    rep #$20
    .ACCU 16
+   sep #$20
    .ACCU 8
    lda FP+F_MAX
    cmp.w TEL_MAX1
    beq +
    sta.w TEL_MAX1
    lda huddirty
    ora #HUD_POWER
    sta huddirty
+   lda FP+F_MAX+FP2OFS
    cmp.w TEL_MAX2
    beq +
    sta.w TEL_MAX2
    lda huddirty
    ora #HUD_POWER
    sta huddirty
+   rep #$20
    .ACCU 16
    rts

DrawWins:                               ; fight.def [WinIcon], beneath names
    rep #$20
    .ACCU 16
    ldx #((5*32+3)*2).w
    sep #$20
    .ACCU 8
    lda wins1
    beq ++
-   pha
    lda #PIP.b
    sta HUDMAP,x
    lda #ATT_YEL.b
    sta HUDMAP+1,x
    inx
    inx
    inx
    inx
    pla
    dec a
    bne -
++  rep #$20
    .ACCU 16
    ldx #((5*32+28)*2).w
    sep #$20
    .ACCU 8
    lda wins2
    beq ++
-   pha
    lda #PIP.b
    sta HUDMAP,x
    lda #ATT_YEL.b
    sta HUDMAP+1,x
    inx
    inx
    inx
    inx
    pla
    dec a
    bne -
++  rep #$20
    .ACCU 16
    rts

; Small "LEVEL n" at the bottom centre of the fight HUD (BG3, row 27).
DrawLevel:
    rep #$20
    .ACCU 16
    lda #((27*32+12)*2).w               ; 7 cells = 56 px -> x=96..151
    sta scr0
    lda #StrLevel.w
    sta scr2
    sep #$20
    .ACCU 8
    lda #:StrLevel
    sta scr2+2
    jsr WriteStr
    rep #$20
    .ACCU 16
    ldx #((27*32+18)*2).w               ; space at col 17, digit at col 18
    sep #$20
    .ACCU 8
    lda.w DIFFICULTY                    ; OPTIONS scale (1..8), not AI 1..9
    clc
    adc #27                             ; charset: '0' is tile 27
    sta HUDMAP,x
    lda #ATT_TXT.b
    sta HUDMAP+1,x
    rep #$20
    .ACCU 16
    rts

; A(16) = hp 0..MAXHP -> A = filled px 0..88 (hp*11/25)
HpToPx:
    and #$00FF.w
    sta scr1
    asl a
    asl a
    asl a                               ; hp*8
    clc
    adc scr1                            ; hp*9
    adc scr1                            ; hp*10
    adc scr1                            ; hp*11
    ldx #0
-   cmp #25.w
    bcc +
    sec
    sbc #25.w
    inx
    bra -
+   txa
    rts

; A(16) = power 0..3000 -> A = filled px 0..88 (power*11/375)
PowToPx:
    sta scr1
    asl a
    asl a                               ; power*4
    asl a                               ; power*8
    clc
    adc scr1
    adc scr1
    adc scr1                            ; power*11 <= 33000
    ldx #0
-   cmp #375.w
    bcc +
    sec
    sbc #375.w
    inx
    bra -
+   txa
    rts

; Pixel-granular 11-column bar.  scr5(8) = filled px left; scr6 = palette
; attr (bit6 set -> draw mirrored right-to-left, P2 side); scr3(8) = tile
; group base (LB_BAR/PB_BAR); X = HUDMAP byte ofs of the first column.
; Tile roles inside a group: 0 capL-full,1 fill,2 capR-full, 3 capL-empty,
; 4 empty,5 capR-empty, 6..12 edge1-7, 13..19 capL-edge1-7, 20..26
; capR-edge1-7.
FillBar:
    sep #$20
    .ACCU 8
    ldy #0
FB_col:
    lda scr5
    cmp #8
    bcc +
    lda #8.b
+   sta scr4                            ; this column's fill width
    lda scr5
    sec
    sbc scr4
    sta scr5
    lda scr4
    beq FB_empty
    cmp #8
    bne FB_edge
    cpy #0
    beq +
    cpy #10
    beq ++
    lda #1.b
    bra FB_put
+   lda #0.b
    bra FB_put
++  lda #2.b
    bra FB_put
FB_empty:
    cpy #0
    beq +
    cpy #10
    beq ++
    ; Drained middle: opaque tile + dark palette (no stage/hatch bleeding)
    lda #BLANK_BAR.b
    sta HUDMAP,x
    lda scr6
    and #$40.b
    ora #ATT_SIL.b
    sta HUDMAP+1,x
    jmp FB_after_put
+   lda #3.b
    bra FB_put
++  lda #5.b
    bra FB_put
FB_edge:
    cpy #0
    beq +
    cpy #10
    beq ++
    lda #6.b
    bra +++
+   lda #13.b
    bra +++
++  lda #20.b
+++ dec a
    clc
    adc scr4                            ; role base-1 + clip width
FB_put:
    clc
    adc scr3                            ; -> tile id in the group
    sta HUDMAP,x
    lda scr6
    sta HUDMAP+1,x
FB_after_put:
    bit scr6                            ; V = hflip bit -> mirrored side
    bvs +
    inx
    inx
    bra ++
+   dex
    dex
++  iny
    cpy #11
    beq +
    jmp FB_col
+   rep #$20
    .ACCU 16
    rts

; The two FNT v2 power fonts provide the stock digits.  They are kept
; separate because their SFF glyphs are positioned and styled per side.
DrawPowerCounters:
    rep #$20
    .ACCU 16
    lda FP+F_POWER
    ldy #0
-   cmp #1000.w
    bcc +
    sec
    sbc #1000.w
    iny
    cpy #3
    bne -
+   tya
    asl a
    clc
    adc #P1POW0.w
    sta scr0
    ldx #((22*32+2)*2).w
    sep #$20
    .ACCU 8
    lda scr0
    sta HUDMAP,x
    inc a
    sta HUDMAP+64,x
    lda #ATT_SIL.b
    sta HUDMAP+1,x
    sta HUDMAP+65,x
    rep #$20
    .ACCU 16
    lda FP+F_POWER+FP2OFS
    ldy #0
-   cmp #1000.w
    bcc +
    sec
    sbc #1000.w
    iny
    cpy #3
    bne -
+   tya
    asl a
    clc
    adc #P2POW0.w
    sta scr0
    ldx #((22*32+29)*2).w
    sep #$20
    .ACCU 8
    lda scr0
    sta HUDMAP,x
    inc a
    sta HUDMAP+64,x
    lda #ATT_SIL.b
    sta HUDMAP+1,x
    sta HUDMAP+65,x
    rep #$20
    .ACCU 16
    rts

; Return X = fighter whose generated data/graphics own the current state.
; ChangeAnim2 victim states keep their position/state in `fofs`, but source
; animation, boxes and tiles from the attacker recorded in F_OWNER.
DataFighterX:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_GRAB,x
    and #$0002.w
    beq +
    lda FP+F_OWNER,x
    and #$00FF.w
    tax
+   rts

; Y = character descriptor field, X = destination 24-bit dp pointer.
; Descriptor bank is tblbank; the generated data bank comes from F_TBANK.
; Upload the picked chars' OBJ palettes per side: P1 -> CGADD 128/176/208
; (palette 0 base / 3 dim / 5 flash), P2 -> 144/192/224 (1/4/6).  Spark
; palette 2 and wood palette 7 are shared and stay from boot.  The CharX
; descriptors carry CH_PAL/CH_PALDIM/CH_PALHI pointers for this.
LoadCharPals:
    sep #$20
    .ACCU 8
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    lda sel1
    and #$00FF.w
    asl a
    tax
    lda.l CharSelTab,x
    sta cptr
    ldx #0
    jsr UpCharPals
    ; Mirror match: both sides picked the same character.  Give P2 the
    ; pack's alternate ACT palette instead of duplicating P1's colours.
    sep #$20
    .ACCU 8
    lda sel1
    cmp sel2
    beq LCP_alt
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    lda sel2
    and #$00FF.w
    asl a
    tax
    lda.l CharSelTab,x
    sta cptr
    ldx #1
    jsr UpCharPals
    rep #$20
    .ACCU 16
    rts
LCP_alt:
    rep #$20
    .ACCU 16
    jsl UpCharPalsAltFar
    rts

; Invalidate the two effect-slot pages after a fight/member change.
ProjFxLoadBoth:
    rep #$20
    .ACCU 16
    stz.w FX_CACHE
    stz.w FX_CACHE+2
    stz.w FX_CACHEBANK
    stz.w FX_CACHEBANK+2
    rts

; Each live spark slot owns one full 2 KiB OBJ page. Projectiles stream
; their enlarged frame; ordinary effects restore the shared static page.
; Upload only when a frame changes. Called under forced blank before OAM.
FxPrepareBoth:
    rep #$30
    .ACCU 16
    .INDEX 16
    stz sidx
    stz.w RT_FXUPLOAD
FXP_slot:
    lda sidx
    beq +
    lda #2.w
+   sta gk
    ldx sidx
    lda.w SPARKS+SPK_ANIM,x
    bne +
    jmp FXP_next
+   sta sptr
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    bmi FXP_projectile
    rep #$20
    .ACCU 16
    lda #$FFFF.w                        ; sentinel: shared sparks/explods
    sta scr6
    lda #(:SparkChr & $FF).w
    sta scr3
    ldy gk
    lda scr6
    cmp.w FX_CACHE,y
    bne +
    lda.w FX_CACHEBANK,y
    and #$00FF.w
    cmp scr3
    bne +
    jmp FXP_next
+   lda #SparkChr.w
    sta scr0
    sep #$20
    .ACCU 8
    lda #:SparkChr
    sta scr3
    bra FXP_upload
FXP_projectile:
    lda.w SPARKS+SPK_BANK,x
    sta sptr+2
    sta scr3
    stz scr3+1
    lda.w SPARKS+SPK_FIDX,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    inc a
    tay
    lda [sptr],y                        ; current frame record
    sta sptr
    sta scr6
    ldy #1
    lda [sptr],y
    and #$00FF.w
    bne +
    jmp FXP_next                        ; empty/missing projectile frame
+   ldy gk
    ldy #2
    lda [sptr],y                        ; per-frame atlas pointer
    sta scr0
    ldy #4
    lda [sptr],y
    and #$00FF.w
    sta scr3                            ; atlas ROM bank
    ldy gk
    lda scr6
    cmp.w FX_CACHE,y
    bne FXP_upload
    lda.w FX_CACHEBANK,y
    and #$00FF.w
    cmp scr3
    bne FXP_upload
    jmp FXP_next
FXP_upload:
    rep #$20
    .ACCU 16
    lda.w RT_FXUPLOAD
    beq FXP_do_upload
    ; A flying projectile's page is never optional: DrawSparks emitted
    ; cells from this exact frame and the same presentation shows them.
    ; Cosmetic sparks keep the one-page budget, but a projectile may use
    ; the second page (including two simultaneous projectiles).
    lda.w SPARKS+SPK_ATTR,x
    and #$0080.w
    beq FXP_next
FXP_do_upload:
    inc.w RT_FXUPLOAD
    ldy gk
    lda scr6
    sta.w FX_CACHE,y
    lda scr3
    and #$00FF.w
    sta.w FX_CACHEBANK,y
    lda #SPK1CHR.w
    ldx sidx
    beq +
    lda #SPK2CHR.w
+   sta.l VMADDL
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l VMAIN
    lda #1.b                            ; DMA mode 1 -> $2118/9
    sta.l $4360
    lda #$18.b
    sta.l $4361
    rep #$20
    .ACCU 16
    lda scr0
    sta.l $4362
    sep #$20
    .ACCU 8
    lda scr3
    sta.l $4364
    rep #$20
    .ACCU 16
    lda #2048.w
    sta.l $4365
    sep #$20
    .ACCU 8
    lda #$40.b
    sta.l MDMAEN
FXP_next:
    rep #$20
    .ACCU 16
    lda sidx
    clc
    adc #SPK_SIZE.w
    sta sidx
    cmp #SPK_SIZE*2
    bcs +
    jmp FXP_slot
+   sep #$20
    .ACCU 8
    rts

; X = side (0/1).  cptr -> picked CharX descriptor (bank byte set).
UpCharPals:
    phx
    txa
    asl a
    asl a
    asl a
    asl a
    sta scr5                            ; side*16 (word)
    ldy #CH_PAL
    lda #128.w
    jsr PalUpX
    ldy #CH_PALDIM
    lda #176.w
    jsr PalUpX
    ldy #CH_PALHI
    lda #208.w
    jsr PalUpX
    plx
    rts

; A(16) = base CGRAM index, Y = CH_ descriptor field, scr5 = side*16,
; cptr = CharX descriptor (24-bit).  Uploads 32 bytes (one OBJ palette).
PalUpX:
    clc
    adc scr5
    sep #$20
    .ACCU 8
    sta.l CGADD
    rep #$20
    .ACCU 16
    lda [cptr],y
    sta scr0
    iny
    iny
    lda [cptr],y
    and #$00FF.w
    sta scr3
    lda #32.w
    sta scr1
    jsr CgDma
    rep #$20
    .ACCU 16
    rts

; P2 mirror-match palette loader lives in the AltPals bank
; (src/engine/alt_pals.asm) so the Fight code bank stays under its 32 KiB
; ceiling.  See LoadCharPals.

; PVSnesLib keeps these three helpers in the free tail of bank 50's low
; half (same CPU bank as Fight) to keep the 32 KiB battle window under its
; limit.  The standalone build still has room in its Fight bank.
.IFNDEF PVSNESLIB
CharPtr:
    rep #$20
    .ACCU 16
    phx
    phy
    jsr DataFighterX
    lda FP+F_CHAR,x
    sta cptr
    sep #$20
    .ACCU 8
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    ply
    lda [cptr],y
    plx
    sta 0,x
    sep #$20
    .ACCU 8
    phx
    jsr DataFighterX
    sep #$20                            ; DataFighterX returns with A in 16-bit mode
    .ACCU 8
    lda FP+F_TBANK,x
    plx
    sta 2,x
    rep #$20
    .ACCU 16
    rts

; X = scr2, Y = CH_NAME.  Names live in the shared tables bank, so resolve
; the descriptor's low address then replace the bank byte returned by
; CharPtr (which assumes the character's F_TBANK).
NamePtr:
    jsr CharPtr
    sep #$20
    .ACCU 8
    lda.b #:ioriName
    sta scr2+2
    rep #$20
    .ACCU 16
    rts
.ENDIF

; X = fighter dp offset.  A(8) <- that fighter's metasprite bank: SprOfs is
; fetched at F_TBANK but its entries are offsets into the (possibly separate)
; meta bank named by descriptor byte CH_MBANK.  Preserves X; cptr clobbered.
MetaBankX:
    phx
    rep #$20
    .ACCU 16
    lda FP+F_CHAR,x
    sta cptr
    sep #$20
    .ACCU 8
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    ldy #CH_MBANK.w
    lda [cptr],y                        ; .db :xxxSprData -> low byte = bank
    plx
    sep #$20
    .ACCU 8
    rts

; A(16) = state, fofs = fighter offset. DB=$00.
EnterState:
    rep #$20
    .ACCU 16
    ldx fofs
    sta FP+F_STATE,x
    stz FP+F_LASTSCAN,x
    jsr CmdTrack                          ; practice command-list usage log
    stz FP+F_FRAME,x
    stz FP+F_STIME,x
    sep #$20
    .ACCU 8
    lda FP+F_TFLAGS,x                       ; mark "just entered": AnimTick
    and #$F3.b                            ;   drop ghost/xfreeze latches;
    ora #$02.b                            ;   skips the entry tick so elem0
    sta FP+F_TFLAGS,x                     ;   is collision-visible for dur ticks
    stz FP+F_INVUL,x                      ; fresh state: no carried-over
    stz FP+F_PFX,x                        ;   invuln or palette flash
    stz FP+F_VMUL,x                       ;   or VelMul damping
    rep #$20
    .ACCU 16
    ldy #CH_FLAGS                         ; hitdefpersist (FlagsTab bit2):
    ldx #lptr                             ;   the carried-over HitDef keeps
    jsr CharPtr                           ;   its already-hit latch across
    ldx fofs                              ;   EnterState so it cannot re-hit
    lda FP+F_STATE,x                      ;   the same target
    and #$00FF.w
    asl a
    tay
    lda [lptr],y
    and #$0004.w
    bne +
    sep #$20
    .ACCU 8
    stz FP+F_HITDONE,x                    ; byte store: offset 27 is F_TILEPG
    rep #$20
    .ACCU 16
+   stz FP+F_HTIMER,x
    stz FP+F_SLIDE,x
    sep #$20
    .ACCU 8
    stz FP+F_PROJDONE,x                  ; byte store: offset 60 is F_STIME
    rep #$20
    .ACCU 16
    ldy #CH_POWTAB                        ; poweradd: apply the new state's
    ldx #lptr                             ;   signed delta, clamped 0..3000
    jsr CharPtr                           ;   (lptr -> PowTab; reloaded below)
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    tay
    lda [lptr],y
    clc
    adc FP+F_POWER,x
    bpl +
    lda #0
+   cmp #3000.w
    bcc ++
    lda #3000.w
++  sta FP+F_POWER,x
    sep #$20                            ; FUSION: entering the MAX burst state
    .ACCU 8                             ;   (sid 96) arms a 240-frame window
    lda FP+F_STATE,x
    cmp #96.b
    bne +
    lda #240.b
    sta FP+F_MAX,x
+   rep #$20
    .ACCU 16
    ldy #CH_EVELTAB                       ; statedef velset: entry velocity
    ldx #lptr                             ;   (lptr reloaded for AnimTab next)
    jsr CharPtr
ES_vel:
    ldx fofs
    lda [lptr]
    and #$00FF.w
    cmp #$00FF.w
    beq ES_vdone
    cmp FP+F_STATE,x
    beq +
    lda lptr
    clc
    adc #5
    sta lptr
    bra ES_vel
+   ldy #1
    lda [lptr],y                          ; vx is forward-relative
    bit FP+F_FACING,x
    bpl +
    eor #$FFFF.w
    inc a
+   sta FP+F_VX,x
    ldy #3
    lda [lptr],y                          ; vy is screen-space (+ = down)
    sta FP+F_VY,x
ES_vdone:
    ldy #CH_ANIMTAB
    ldx #lptr
    jsr CharPtr                           ; lptr -> character anim table
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    tay
    lda [lptr],y
    ldx fofs
    sta FP+F_ANIM,x
    sta lptr
    lda [lptr]                          ; nframes | loopstart<<8
    ldx fofs
    sta FP+F_NFR,x
    ; fallthrough into AnimSetFrame
AnimSetFrame:
    jsr ProjTrySpawn
    rep #$20
    .ACCU 16
    ldy #CH_SPROFS
    ldx #boxp
    jsr CharPtr                           ; boxp -> character sprite table
    ldx fofs
    lda FP+F_ANIM,x
    clc
    adc #2
    sta lptr
    jsr DataFighterX
    sep #$20
    .ACCU 8
    lda FP+F_TBANK,x
    sta lptr+2
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_FRAME,x
    and #$00FF.w
    asl a
    asl a
    asl a                               ; frame*8 (sprid.w + 6 bytes)
    tay
    lda [lptr],y                        ; sprid
    sta scr0                            ; keep sprid for queue compare
    ldx fofs
    sep #$20
    .ACCU 8
    lda scr0
    cmp FP+F_PSPRID,x                   ; same tiles already queued/displayed?
    bne ASF_q_new
    lda scr0+1
    cmp FP+F_PSPRID_H,x
    bne ASF_q_new
    lda FP+F_DMAREQ,x
    bne ASF_q_wait
    stz scr6                            ; mode 0: offsets apply right away
    stz scr6+1
    rep #$20
    .ACCU 16
    bra ASF_boxes
ASF_q_new:
    .ACCU 8
    ; An in-flight upload must finish before the pending sprite id and
    ; DMA position are replaced, or a big sprite starves mid-copy.
    lda FP+F_DMAREQ,x
    bne ASF_q_drop
    lda scr0
    sta FP+F_PSPRID,x
    lda scr0+1
    sta FP+F_PSPRID_H,x
    lda #1.b
    sta FP+F_DMAREQ,x                   ; F_META committed when upload completes
    stz FP+F_DMAPOS,x
    ; Telemetry: timestamp the request and count it per side.
    txa
    bne +
    lda framecnt
    sta.w TEL_REQ_P1
    stz.w TEL_REQ_P1+1
    rep #$20
    .ACCU 16
    inc.w TEL_REQS_P1
    sep #$20
    .ACCU 8
    bra ++
+   lda framecnt
    sta.w TEL_REQ_P2
    stz.w TEL_REQ_P2+1
    rep #$20
    .ACCU 16
    inc.w TEL_REQS_P2
    sep #$20
    .ACCU 8
++  stz scr6
    stz scr6+1
    lda #1.b
    sta scr6                            ; mode 1: offsets commit with the tiles
    rep #$20
    .ACCU 16
    bra ASF_boxes
ASF_q_drop:
    ; A new pose arrived while the previous one was still uploading.  The
    ; animation clock keeps running (gameplay timing must not change), so the
    ; pose is coalesced away; count it so telemetry can show the loss rate.
    txa
    bne +
    rep #$20
    .ACCU 16
    inc.w TEL_DROP_P1
    sep #$20
    .ACCU 8
    bra ++
+   rep #$20
    .ACCU 16
    inc.w TEL_DROP_P2
    sep #$20
    .ACCU 8
++  bra ASF_q_wait
ASF_q_wait:
    .ACCU 8
    stz scr6
    stz scr6+1
    lda #2.b                            ; mode 2: leave the pending geometry
    sta scr6                            ;   alone; keep the displayed one in sync
    rep #$20
    .ACCU 16
ASF_boxes:
    ldx fofs
    lda FP+F_FRAME,x
    and #$00FF.w
    asl a
    asl a
    asl a
    tay
    iny
    iny
    sep #$20
    .ACCU 8
    lda [lptr],y                        ; ticks
    sta FP+F_FTICK,x
    iny
    lda scr6                            ; 2 = upload in flight: this frame's
    cmp #2.b                            ;   geometry is not displayed yet
    beq ASF_off_skip
    lda [lptr],y                        ; frame xoff -> pending
    sta FP+F_PXOFF,x
    iny
    lda [lptr],y                        ; frame yoff -> pending
    sta FP+F_PYOFF,x
    iny
    lda [lptr],y                        ; frame flags -> pending
    sta FP+F_PFLAGS,x
    iny
    bra ASF_off_apply
ASF_off_skip:
    iny
    iny
    iny
    bra ASF_off_done
ASF_off_apply:
    lda scr6                            ; 1 = wait for the DMA commit
    bne ASF_off_done
    lda FP+F_PXOFF,x                    ; same tiles are on screen: the new
    sta FP+F_XOFF,x                     ;   offsets are valid immediately
    lda FP+F_PYOFF,x
    sta FP+F_YOFF,x
    lda FP+F_PFLAGS,x
    sta FP+F_FLAGS,x
ASF_off_done:
    rep #$20
    .ACCU 16
    lda [lptr],y                        ; AIR Clsn1 aggregate id
    sta scr2
    iny
    lda [lptr],y                        ; AIR Clsn2 aggregate id
    sta scr3
    rep #$20
    .ACCU 16
    ldy #CH_BOXTAB
    ldx #boxp
    jsr CharPtr                           ; boxp -> character AIR table
    lda scr2
    and #$00FF.w
    asl a
    tay
    lda [boxp],y
    ldx fofs
    sta FP+F_ATKBOX,x                   ; collision follows the logical frame,
    ldy scr6                            ;   not the tile upload: a late sprite
    cpy #1.w                            ;   must not delay or drop a hit
    bne ASF_hurt_read
    sta FP+F_PATKBOX,x
ASF_hurt_read:
    lda scr3
    and #$00FF.w
    asl a
    tay
    lda [boxp],y
    ldx fofs
    sta FP+F_HURTBOX,x
    ldy scr6
    cpy #1.w
    bne ASF_collision_done
    sta FP+F_PHURTBOX,x
ASF_collision_done:
    ; PosAdd timeline: PosTab[state] rows {elem.b, dx.b} ended by $FF; on the
    ; tick an elem becomes current, add dx*facing pixels to F_X.
    ldy #CH_POSTAB.w
    ldx #boxp
    jsr CharPtr
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    tay
    lda [boxp],y
    beq PA_done16
    sta sptr
    jsr DataFighterX
    sep #$20
    .ACCU 8
    lda FP+F_TBANK,x
    sta sptr+2
    ldx fofs
    ldy #0
PA_row:
    lda [sptr],y                        ; anim elem (0-based frame index)
    cmp #$FF
    beq PA_done
    cmp FP+F_FRAME,x
    bne PA_next
    iny
    lda [sptr],y                        ; signed dx in pixels
    rep #$20
    .ACCU 16
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   xba                                 ; <<8 -> 8.8 fixed point
    and #$FF00.w
    sta scr4
    lda FP+F_FACING,x
    bpl +
    lda #0
    sec
    sbc scr4
    sta scr4
+   lda scr4
    jsr AddXClamped
    sep #$20
    .ACCU 8
    dey                                 ; matched row: y sits on dx; back to
                                        ;   the row head so PA_next +2 works
PA_next:
    iny
    iny
    bra PA_row
PA_done:
    rep #$20
    .ACCU 16
PA_done16:
    .ACCU 16
    ; ActTab: elem-triggered actions (throw sequence: self turn / posadd,
    ; target facing / life / state). Rows whose trigger has bit7 set are
    ; exact state-time events; only Time=0 runs here at state entry. Later
    ; time events are handled once per tick by ApplyTimeActions.
    ldy #CH_ACTTAB.w
    ldx #boxp
    jsr CharPtr
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    tay
    lda [boxp],y
    bne +
    rts
+   sta sptr
    jsr DataFighterX
    sep #$20
    .ACCU 8
    lda FP+F_TBANK,x
    sta sptr+2
    ldx fofs
    ldy #0
AA_row:
    cpy #64.w                           ; safety cap: a malformed table must
    bcs AA_done                         ;   not scan the whole data bank
    lda [sptr],y                        ; trigger; $FF ends the table
    cmp #$FF
    beq AA_done
    bmi AA_time
    cmp FP+F_FRAME,x
    bne AA_next
    bra AA_match
AA_time:
    cmp #$80.b                          ; only exact Time=0 belongs on the
    bne AA_next                         ; AnimSetFrame/state-entry path
    lda FP+F_STIME,x
    bne AA_next
AA_match:
    phy
    iny
    lda [sptr],y                        ; op
    sta scr6
    iny
    lda [sptr],y                        ; arg
    sta scr6+1
    iny
    lda [sptr],y                        ; cond: bit0=fwd, bit1=50% random
    sta scr5+1
    and #$01.b
    beq +
    lda FP+F_TFLAGS,x
    and #$01.b
    beq AA_skip
+   lda scr5+1
    and #$02.b
    beq +
    lda.b rng
    and #$01.b
    beq AA_skip
+   lda scr6
    jsr ActOp
AA_skip:
    ldx fofs
    ply                                 ; ply restores the row head, so a
    jmp AA_next                         ;   matched row still advances +4
AA_next:
    iny
    iny
    iny
    iny
    jmp AA_row
AA_done:
    rep #$20
    .ACCU 16
    rts

; Run exact Time=N actions for N>0.  EnterState/AnimSetFrame owns Time=0,
; avoiding a duplicate event on the transition tick.
ApplyTimeActions:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_STIME,x
    beq ATA_done
    cmp #$007F.w
    bcs ATA_done
    ldy #CH_ACTTAB.w
    ldx #boxp
    jsr CharPtr
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    tay
    lda [boxp],y
    beq ATA_done
    sta sptr
    jsr DataFighterX
    sep #$20
    .ACCU 8
    lda FP+F_TBANK,x
    sta sptr+2
    ldx fofs
    ldy #0
ATA_row:
    cpy #64.w
    bcs ATA_done8
    lda [sptr],y
    cmp #$FF.b
    beq ATA_done8
    bpl ATA_next                         ; animation-element row
    and #$7F.b
    cmp FP+F_STIME,x
    bne ATA_next
    phy
    iny
    lda [sptr],y
    sta scr6
    iny
    lda [sptr],y
    sta scr6+1
    iny
    lda [sptr],y
    sta scr5+1
    and #$01.b
    beq +
    lda FP+F_TFLAGS,x
    and #$01.b
    beq ATA_skip
+   lda scr5+1
    and #$02.b
    beq +
    lda.b rng
    and #$01.b
    beq ATA_skip
+   lda scr6
    jsr ActOp
ATA_skip:
    ldx fofs
    ply
ATA_next:
    iny
    iny
    iny
    iny
    bra ATA_row
ATA_done8:
    rep #$20
    .ACCU 16
ATA_done:
    rts

; ActOp: scr6.l = op, scr6.h = raw arg byte.  Called with acc8; returns
; acc8.  Target ops act on the bound victim only when it still belongs
; to this fighter's grab.
ActOp:
    .ACCU 8                             ; entered in acc8 (AA_row); without
    lda scr6                            ;   this directive the assembler
    bne +                               ;   emits 16-bit immediates and the
    jmp AO_turn                         ;   CPU hits BRK bytes mid-stream
+   cmp #1
    bne +
    jmp AO_padd
+   cmp #2
    bne +
    jmp AO_tface
+   cmp #3
    bne +
    jmp AO_tlife
+   cmp #4
    bne +
    jmp AO_tstat
+   cmp #5
    bne +
    jmp AO_velset
+   cmp #6
    bne +
    jmp AO_pause
+   cmp #7
    bne +
    jmp AO_sfx
+   cmp #8
    bne +
    jmp AO_pfx
+   cmp #9
    bne +
    jmp AO_ghost
+   cmp #10
    bne +
    jmp AO_shake
+   cmp #11
    bne +
    jmp AO_invul
+   cmp #6
    bne +
    jmp AO_jelem
+   cmp #13
    bne +
    jmp AO_xfrz
+   cmp #14
    bne +
    jmp AO_expl
+   cmp #15
    bne +
    jmp AO_velsety
+   cmp #16
    bne +
    jmp AO_velmul
+   cmp #17
    bne +
    jmp AO_velmuloff
+   rts
AO_pfx:                                 ; PalFX: arg = bright-flash ticks
    ldx fofs
    lda scr6+1
    sta FP+F_PFX,x
    rts
AO_ghost:                               ; AfterImage: arg != 0 -> trail on
    ldx fofs
    lda FP+F_TFLAGS,x
    ldy scr6+1
    cpy #0
    beq +
    ora #$04.b
    bra ++
+   and #$FB.b
++  sta FP+F_TFLAGS,x
    rts
AO_shake:                               ; EnvShake: arg = (ampl<<5)|ticks
    lda scr6+1
    jmp SetShake
AO_invul:                               ; NotHitBy: arg = ticks ($FF=state)
    ldx fofs
    lda scr6+1
    sta FP+F_INVUL,x
    rts
AO_xfrz:                                ; PosFreeze: arg = latch on/off
    ldx fofs
    lda FP+F_TFLAGS,x
    ldy scr6+1
    cpy #0
    beq +
    ora #$08.b
    bra ++
+   and #$F7.b
++  sta FP+F_TFLAGS,x
    rts
AO_expl:                                ; Explod: arg = char ExpTab row index
    lda scr6+1
    jmp ExplodSpawn
AO_jelem:                               ; ChangeAnim on contact: when the
    ldx fofs                              ;   HitDef already connected, jump
    lda FP+F_HITDONE,x                    ;   the frame cursor to arg
    beq AO_jout
    rep #$20
    .ACCU 16
    lda scr6+1
    and #$00FF.w
    cmp FP+F_FRAME,x                      ; already past? leave the anim be
    bcc +
    beq +
    sta FP+F_FRAME,x
    jsr AnimSetFrame                      ; reload meta/boxes/DMA request
+   sep #$20
    .ACCU 8
AO_jout:
    rts
AO_sfx:                                 ; PlaySnd: arg = generated SFX id
    lda scr6+1
    cmp #VOICE_BASE.b                     ; ids >= VOICE_BASE are per-char
    bcc +
    sec
    sbc #VOICE_BASE.b
    jmp VoicePlay
+   jsr SfxPlay
    rts
AO_turn:                                ; Turn: flip own facing
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_FACING,x
    eor #$FFFF.w                          ; facing is +-1, so negate with
    inc a                               ;   two's complement (xor alone
    sta FP+F_FACING,x                     ;   would yield $FFFE, not -1)
    sep #$20
    .ACCU 8
    rts
AO_padd:                                ; PosAdd x, facing-relative
    rep #$20
    .ACCU 16
    lda scr6+1
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   xba                                 ; <<8 fixed point
    sta scr0
    ldx fofs
    lda FP+F_FACING,x
    bpl +
    lda scr0
    eor #$FFFF.w
    inc a
    sta scr0
+   lda scr0
    jsr AddXClamped
    sep #$20
    .ACCU 8
    rts
AO_victim:                              ; -> acc16: A=$FFFF or scr5 = bound
    rep #$20                            ;   victim offset
    .ACCU 16
    ldx fofs
    txa
    eor #FP2OFS.w
    sta scr5
    tax
    lda FP+F_GRAB,x
    bit #$0001.w
    beq AO_vno
    lda FP+F_OWNER,x
    and #$00FF.w
    cmp fofs
    bne AO_vno
    lda #0
    rts
AO_vno:
    lda #$FFFF.w
    rts
AO_tface:                               ; TargetFacing: victim faces
    jsr AO_victim                         ;   attacker.facing * arg
    cmp #$FFFF.w
    beq AO_out16
    lda scr6+1
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w                        ; arg sign-extended
+   tay
    ldx fofs
    tya
    bpl +
    lda FP+F_FACING,x
    eor #$FFFF.w
    inc a
    bra ++
+   lda FP+F_FACING,x
++  ldx scr5
    sta FP+F_FACING,x
    bra AO_out16
AO_tlife:                               ; TargetLifeAdd: clamp 0..200
    jsr AO_victim
    cmp #$FFFF.w
    beq AO_out16
    lda scr6+1
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   bpl AO_tlife_apply                    ; positive life change is always fine
    pha
    ldx scr5
    jsr PracBlock
    rep #$20
    .ACCU 16
    bcs AO_tlife_skip                     ; practice: ignore throw/life damage
    pla
AO_tlife_apply:
    ldx scr5
    clc
    adc FP+F_HP,x
    bpl +
    lda #0
+   cmp #201.w
    bcc +
    lda #200.w
+   sta FP+F_HP,x
    bra AO_out16
AO_tlife_skip:
    pla
    bra AO_out16
AO_tstat:                               ; TargetState: victim EnterState
    jsr AO_victim
    cmp #$FFFF.w
    beq AO_out16
    lda scr6+1
    and #$00FF.w
    ldx scr5
    stx fofs
    jsr EnterState
    lda scr5
    eor #FP2OFS.w                         ; back to the attacker
    sta fofs
AO_out16:
    sep #$20
    .ACCU 8
    rts
AO_velset:                              ; VelSet x = arg px/frame, signed,
    rep #$20                            ;   facing-relative, 8.8 fixed
    .ACCU 16
    lda scr6+1
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   xba
    sta scr0
    ldx fofs
    lda FP+F_FACING,x
    bpl +
    lda scr0
    eor #$FFFF.w
    inc a
    sta scr0
+   lda scr0
    sta FP+F_VX,x
    sep #$20
    .ACCU 8
    rts
AO_velsety:                             ; VelSet y = arg quarter-px/frame,
    rep #$20                            ;   signed, screen-space (neg = up)
    .ACCU 16
    lda scr6+1
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   asl a                               ; <<6: quarter-px/f -> 8.8 px/f
    asl a
    asl a
    asl a
    asl a
    asl a
    ldx fofs
    sta FP+F_VY,x
    sep #$20
    .ACCU 8
    rts
AO_velmul:                              ; VelMul x: arg = Q8 factor; the
    ldx fofs                            ;   per-tick damping runs in
    lda scr6+1                          ;   ApplyVelMul until the state ends
    sta FP+F_VMUL,x                     ;   or op17 disarms it.
    rts
AO_velmuloff:
    ldx fofs
    stz FP+F_VMUL,x
    rts
AO_pause:                               ; Pause/SuperPause: freeze the whole
    sep #$20                            ;   match for arg ticks (pausecnt is
    .ACCU 8                             ;   decremented once per FightTick)
    lda scr6+1
    sta pausecnt
    rts

; A(8) = packed EnvShake byte ((ampl<<5)|ticks).  Keeps acc8.
.IFNDEF PVSNESLIB
SetShake:
    sep #$20
    .ACCU 8
    pha
    and #$1F.b
    sta shaketmr
    pla
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    sta shakeamp
    rts
.ENDIF

; Override the current animation with an AnimTab slot (get-hit anims live
; past the last state id).  A(16) = slot index, fofs = fighter.
SetAnimSlot:
    rep #$20
    .ACCU 16
    pha
    ldy #CH_ANIMTAB
    ldx #lptr
    jsr CharPtr                           ; lptr -> character AnimTab
    pla
    asl a
    tay
    lda [lptr],y                          ; anim data offset
    ldx fofs
    sta FP+F_ANIM,x
    sta lptr                              ; bank byte still = F_TBANK
    stz FP+F_FRAME,x
    lda [lptr]                            ; nframes | loopstart<<8
    sta FP+F_NFR,x
    jmp AnimSetFrame

; HitDef hitsound: generated HitSndTab[attacker state] -> runtime sfx id,
; $FF = silent (non-attack states).
PlayHitSfx:
    rep #$20
    .ACCU 16
    phx
    phy
    ldx aofs                              ; the sound is the attacker's
    stx fofs                              ;   state's hitsound row
    ldy #CH_HITSND.w
    ldx #boxp
    jsr CharPtr
    ldx aofs
    lda FP+F_STATE,x
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y
    cmp #$FF
    beq PH_done
    jsr SfxPlay
PH_done:
    rep #$20
    .ACCU 16
    ply
    plx
    rts

; ---------------------------------------------------------------------------
ReadPads:
    rep #$20
    .ACCU 16
    lda.l JOY1L
    ldx #0
    jsr StoreJoy
    lda.l JOY2L
    ldx #FP2OFS
    jsr StoreJoy
    sep #$20
    .ACCU 8
    rts
; Latch the real held state (ReadPads handles the $FFFF no-pad case) and
; consume only the edge bits so a held button cannot fabricate a press.
ConsumePadEdges:
    jsr ReadPads
    rep #$20
    .ACCU 16
    stz FP+F_JOYPR
    stz FP+F_JOYPR+FP2OFS
    sep #$20
    .ACCU 8
    rts
StoreJoy:
    ldy FP+F_JOY,x
    sta scr0
    cmp #$FFFF.w                        ; $FFFF = no pad connected
    bne +
    stz scr0
+
    tya
    eor #$FFFF.w
    and scr0
    sta FP+F_JOYPR,x
    lda scr0
    sta FP+F_JOY,x
    rts

; --- command input history -------------------------------------------------
; Per-fighter ring at CMDHIST_L (P1) / +$40 (P2): 16 entries of
; {dir.b, btn.b, tick.b} where dir uses facing-relative bits U=1 D=2 F=4 B=8
; and btn uses the generated token bits x=1 y=2 a=4 b=8 c=16 z=32 s=64.
; An entry is pushed only when the direction changes or a button is pressed,
; so taps are discrete events and holds collapse to a single entry.
; (PadDirR/L live in the AltPals bank, addressed with lda.l.)

JoyRelDir:                              ; X=fofs -> A(8): U=1 D=2 F=4 B=8
    sep #$20                            ;   (X clobbered; callers reload fofs)
    .ACCU 8
    lda FP+F_JOY+1,x                    ; UP=$08 DN=$04 LF=$02 RT=$01
    and #$0F
    rep #$20                            ; zero the hidden B byte so tay is clean
    .ACCU 16
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    lda FP+F_FACING,x                   ; low byte $FF when facing left
    bmi +
    tyx
    lda.l PadDirR,x
    bra JRD_out
+   tyx
    lda.l PadDirL,x
JRD_out:
    rts

PushHist:                               ; X=fofs, acc mode free
    sep #$20
    .ACCU 8
    jsr JoyRelDir
    sta ct_dir
    ldx fofs                            ; JoyRelDir clobbers X
    stz ct_tmp                          ; build pressed-button token byte
    lda FP+F_JOYPR+1,x                  ; Y=$40 B=$80 ST=$10 (face labels)
    pha
    and #$40                            ; Y -> x token (1)
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    tsb ct_tmp
    pla
    pha
    and #$80                            ; B -> a token (4)
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    tsb ct_tmp
    pla
    and #$10                            ; ST -> s token (64)
    asl a
    asl a
    tsb ct_tmp
    lda FP+F_JOYPR,x                    ; X=$40 A=$80 L=$20 R=$10
    pha
    and #$40                            ; X -> y token (2)
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    tsb ct_tmp
    pla
    pha
    and #$80                            ; A -> b token (8)
    lsr a
    lsr a
    lsr a
    lsr a
    tsb ct_tmp
    pla                                 ; L=$20 R=$10 -- FUSION routing:
    and #$30                            ;   L alone -> c (extra dodge),
    beq +                               ;   F/B+L -> roll; R alone -> y|b
    cmp #$30                            ;   (Blowback); L+R -> s (taunt)
    beq PHS_taunt
    cmp #$20
    bne ++                              ; R only -> y(2)|b(8): the "CD" cmd
    lda #$10                            ; L only -> c token
    tsb ct_tmp
    bra +
++  lda #$0A
    tsb ct_tmp
    bra +
PHS_taunt:
    lda #$40
    tsb ct_tmp
+   lda FP+F_JOY,x                      ; R *held* ($10) arms the z token on
    and #$10                            ;   later button entries -- that's how
    beq +                               ;   "R+YBX" (charge) differs from the
    lda #$20                            ;   plain YBX MAX burst
    tsb ct_tmp
+
    lda FP+F_HIST,x                     ; ring head; 0 = empty
    beq PHS_empty
    dec a
    and #$0F
    sta ct_off
    asl a
    clc
    adc ct_off
    clc
    adc fofs                            ; low byte holds 0/$30
    rep #$20                            ; clean index: kill hidden B byte
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l CMDHIST_L,x                   ; newest entry's dir
    and #$3F                            ; bit7 spent + bit6 fresh are markers
    ldx fofs
    stz ct_edir                         ; assume held-again: not a fresh press
    cmp ct_dir
    bne PHS_fresh                       ; direction changed
    lda ct_tmp
    beq PHS_done                        ; same dir, no new press
    bra PHS_push
PHS_fresh:
    lda #$40                            ; dir transition: bit6 = press edge
    sta ct_edir
    bra PHS_push
PHS_empty:
    lda ct_dir
    ora ct_tmp
    beq PHS_done                        ; nothing held/pressed yet
    stz ct_edir
    lda ct_dir
    beq PHS_push                        ; button-only entry
    lda #$40
    sta ct_edir                         ; first dir seen counts as fresh
PHS_push:
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_HIST,x
    sta ct_off
    asl a
    clc
    adc ct_off
    clc
    adc fofs
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax                                 ; ring offset -> X for long stores
    sep #$20
    .ACCU 8
    lda ct_dir
    ora ct_edir                         ; bit6 = fresh dir transition
    sta.l CMDHIST_L,x
    lda ct_tmp
    sta.l CMDHIST_L+1,x
    lda framecnt                        ; low byte (8-bit read of $24)
    sta.l CMDHIST_L+2,x
    ldx fofs
    lda ct_tmp                          ; press tokens or a live direction can
    ora ct_dir                          ;   complete a command; a release-to-0
    beq +                               ;   entry cannot
    lda #6                              ;   a match only completes on a push
    sta FP+F_HOT,x                      ;   tick (new edge/press), so a few
                                        ;   ticks cover input jitter; longer
                                        ;   hold entries stay in the ring
                                        ;   regardless of the hot window
+   lda FP+F_HIST,x
    inc a
    and #$0F
    sta FP+F_HIST,x
PHS_done:
    rep #$20
    .ACCU 16
    rts

; ---------------------------------------------------------------------------
; CmdTry: scan the generated CmdTab in file order (priority).  On a match the
; rule's state is entered via SetState16; on no match the routine returns so
; the caller's one-button fallback can run.  CmdTryCancel is the hit-cancel
; scan: it only accepts specials (48-66) and supers (85-89) so a normal that
; connected cannot turn into a taunt/dash/throw instead of a combo route.
CmdTry:                                 ; X=fofs
    sep #$20
    .ACCU 8
    stz ct_cancel
    bra CmdTryGo
CmdTryCancel:                           ; X=fofs, F_HITDONE already checked
    sep #$20
    .ACCU 8
    lda #1
    sta ct_cancel
CmdTryGo:
    ; The AI drives the pad with synthetic holds (guard, spacing, jump-in).
    ; Letting the command scanner see those holds turns a guard release and
    ; re-press into BB (backdash), FF (run) or a taunt: the CPU appeared to
    ; keep hopping backwards in place.  CPU-driven sides enter their specials,
    ; supers and throws through AI_StartMove, so they need no command scan.
    sep #$20
    .ACCU 8
    lda fofs
    beq CT_side1
    lda cpu2
    bra CT_side
CT_side1:
    lda cpu1
CT_side:
    beq CT_human_scan
    rep #$20                          ; every CmdTry exit runs 16-bit: StStand
    .ACCU 16                          ;   reads JOY/UP with word immediates
    clc                               ;   right after the call
    rts
CT_human_scan:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_HOT,x                      ; no fresh buffered input -> nothing
    and #$00FF.w                        ;   can complete: skip the whole scan
    bne +
    rts
+   dec a
    sep #$20                          ; F_HOT is a byte at offset 58; a 16-bit
    .ACCU 8                           ;   store would overwrite F_MAX (59)
    sta FP+F_HOT,x
    rep #$20
    .ACCU 16
    lda ct_cancel
    bne +
    ldx fofs
    lda FP+F_HIST,x
    cmp FP+F_LASTSCAN,x
    bne +
    rts
+   ldx fofs
    lda FP+F_HIST,x
    sta FP+F_LASTSCAN,x
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_CROUCH
    beq CT_c
    cmp #S_CDOWN
    beq CT_c
    cmp #S_CUP
    beq CT_c
    cmp #S_CPUNCH                       ; crouching attacks cancel with
    bcc +                               ;   posture C
    cmp #S_CSKICK+1
    bcc CT_c
+   lda FP+F_Y,x
    beq +
    lda #4                              ; airborne
    bra CT_p
+   lda #1                              ; standing
    bra CT_p
CT_c:
    lda #2                              ; crouching
CT_p:
    sta ct_post                         ; 16-bit store also clears ct_ei (ok)
    sep #$20
    .ACCU 8
    jsr JoyRelDir
    sta ct_dir
    jsr CmdSimpleNormal
    bcc +
    rts
+   rep #$20
    .ACCU 16
    ldy #CH_CMDTAB.w
    ldx #boxp
    jsr CharPtr                       ; boxp -> CmdTab
    ldy #CH_MOTTAB.w
    ldx #lptr
    jsr CharPtr                       ; lptr -> MotTab
    lda #CMDHIST_L & $FFFF.w          ; histp -> this fighter's ring
    clc
    adc fofs
    sta histp
    sep #$20
    .ACCU 8
    lda #$7E
    sta histp+2
    rep #$20
    .ACCU 16
    stz ct_row
CT_rule:
    rep #$20                            ; ct_row is a word: tables outgrew
    .ACCU 16                            ;   256 bytes with the super/block
    lda ct_row                          ;   commands, so index them in full
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y                      ; motion idx; $FF ends the table
    cmp #$FF
    bne +
    rep #$20
    .ACCU 16
    rts
+   sta ct_tmp                        ; motion idx
    iny
    lda [boxp],y                      ; required held dirs
    beq ++
    sta ct_win
    lda ct_dir
    and ct_win
    cmp ct_win
    beq ++
    jmp CT_next
++  iny
    lda [boxp],y                      ; forbidden held dirs
    beq ++
    and ct_dir
    beq ++
    jmp CT_next
++  iny
    lda [boxp],y                      ; posture mask
    and ct_post
    bne +
    jmp CT_next
+
    ; row+4 proximity byte (bit7 = victim must be throwable) and row+5
    ; forbidden state -- generated from p2bodydist/p2statetype/p2movetype
    ; and stateno != triggers (the throw command)
    rep #$20
    .ACCU 16
    lda ct_row
    clc
    adc #4
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y
    beq CT_ns                           ; no proximity gate
    sta ct_off
    bpl CT_dist                         ; bit7 clear: distance only
    ldx fofs                            ; throwable victim: grounded and
    txa                                 ;   not in a hit state (hitflag M-)
    eor #FP2OFS.b
    tax
    lda FP+F_GRAB,x
    beq +
    jmp CT_fail
+   lda FP+F_STATE,x
    cmp #S_HIT.b
    bne +
    jmp CT_fail
+   cmp #S_DOWN.b
    bne +
    jmp CT_fail
+   cmp #S_GETUP.b
    bne +
    jmp CT_fail
+   cmp #S_GHIT.b
    bne +
    jmp CT_fail
+   cmp #S_VSHAKE.b
    bcc +
    cmp #S_VTHROW+1.b
    bcs +
    jmp CT_fail
+   rep #$20
    .ACCU 16
    lda FP+F_Y,x
    beq +
    jmp CT_fail16
+   sep #$20
    .ACCU 8
CT_dist:
    ldx fofs                            ; |victim.x - attacker.x| in px
    txa
    eor #FP2OFS.b
    tax
    rep #$20
    .ACCU 16
    lda FP+F_X,x
    ldx fofs
    sec
    sbc FP+F_X,x
    bpl +
    eor #$FFFF.w
    inc a
+   xba
    and #$00FF.w                        ; whole pixels
    sta scr0
    lda ct_off
    and #$007F.w
    cmp scr0
    bcs +
    sep #$20
    .ACCU 8
    jmp CT_fail
+   sep #$20
    .ACCU 8
CT_ns:
    rep #$20                            ; forbidden-state gate (stateno !=)
    .ACCU 16
    lda ct_row
    clc
    adc #5
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y
    beq CT_gatesok
    ldx fofs
    cmp FP+F_STATE,x
    bne +
    jmp CT_fail
+   sep #$20                          ; noop: stays acc8
CT_gatesok:
    rep #$20
    .ACCU 16
    lda ct_tmp
    and #$00FF.w
    asl a
    tay
    lda [lptr],y
    sta sptr                          ; sptr -> motion record
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_TBANK,x
    sta sptr+2                        ; [sptr] reads the char's data bank
    ldy #0
    lda [sptr],y                      ; nelem -> byte offset of last elem
    asl a
    sta ct_ei
    sta ct_nelem
    iny
    lda [sptr],y                      ; window
    sta ct_win
    jsr CmdScanCap
    ldx fofs
    lda FP+F_HIST,x
    bne +                             ; empty ring cannot match
    jmp CT_next
+   dec a
    and #$0F
    sta ct_j                          ; scan from the newest entry back
    stz ct_scan
MM_scan:
    lda ct_j
    sta ct_off
    asl a
    clc
    adc ct_off                          ; j*3: entry offset within the ring
    rep #$20
    .ACCU 16
    and #$00FF.w
    tay
    sep #$20
    .ACCU 8
    lda [histp],y
    sta ct_edir
    iny
    lda [histp],y
    sta ct_ebtn
    iny
    lda [histp],y
    sta ct_ets
    lda framecnt
    sec
    sbc ct_ets
    cmp ct_cut
    bcc +
    jmp CT_next
+   rep #$20
    .ACCU 16
    lda ct_ei
    and #$00FF.w
    tay                                 ; elem dir @ rec+ct_ei, btn @ +1
    sep #$20
    .ACCU 8
    lda [sptr],y
    beq +
    bit #$40.b                        ; bit6 = ~X dir-release element
    bne MM_rel
    eor ct_edir                       ; exact direction match: a DF roll
    and #$0F                          ; compare direction nibble; bit5 marks
    beq ++                            ;   a charge, bits6/7 are ring metadata
    jmp MM_next                       ;   spent marker, bit6 the fresh edge
++  lda ct_edir                       ; motion dirs are press edges: an entry
    and #$40                          ;   that just re-reports a held dir (a
    bne +                             ;   button press while walking) cannot
    jmp MM_next                       ;   complete F,F.  Elem dir = 0 skips.
+   iny
    lda [sptr],y
    beq MM_elem                       ; no button required on this elem
    sta ct_tmp
    lda ct_ebtn
    and ct_tmp                        ; pressed set must include the elem bits
    cmp ct_tmp
    beq MM_elem
    jmp MM_next
; ~X release element: mugen treats directions as atomic keys, so ~D fires
; when the pad leaves the D key -- a D->DF roll counts (the engine mirrors this
; in IsDirToButton: a release step and the next press step complete on the
; same input event).  Boundary at cursor j: entry j is exactly X and entry
; j+1 -- possibly the slot the following element already consumed -- is not.
; The release consumes nothing itself.
MM_rel:
    lda [sptr],y
    and #$3F
    sta ct_rel
    lda ct_edir
    and #$3F
    cmp ct_rel
    beq +
    jmp MM_next
+   lda ct_j
    inc a
    and #$0F
    sta ct_off
    asl a
    clc
    adc ct_off                        ; (j+1)*3: the boundary entry
    tay
    lda [histp],y
    and #$3F
    cmp ct_rel
    bne +
    jmp MM_next
+   iny
    iny
    lda [histp],y
    sta ct_ets                        ; release-event tick = the boundary ts
    jmp MM_elem
MM_elem:
    lda ct_ei
    cmp ct_nelem                      ; newest elem sets the window anchor
    bne +
    lda ct_edir                       ; a press entry already spent on a
    bpl ++                            ;   command carries bit7: it cannot
    jmp MM_next                       ;   complete another command
++  lda ct_j
    sta ct_scan                       ; ring slot to mark if the rule fires
    lda ct_ets
    sta ct_ts0
+   lda ct_ei
    cmp #2                            ; first element just matched?
    beq MC_first
    jmp MM_decelem                    ;   no: keep matching older elements
MC_first:
    ldy #2
    lda [sptr],y
    and #$20
    beq MC_window                     ;   bit5 clear: ordinary motion
    lda ct_ts0
    sec
    sbc ct_ets                        ; hold duration: newest input minus B
    cmp #40.b
    bcs +
    jmp MM_next                       ; not charged long enough yet
+   cmp #240.b
    bcc +
    jmp MM_next                       ; stale charge prefix
+   lda #240                           ; the hold itself spans 40..239 ticks;
    sta ct_win                         ;   the short special window would
    jmp MM_match                       ;   reject every charged move
MC_window:
    lda ct_ts0
    sec
    sbc ct_ets
    cmp ct_win                        ; span <= window?
    beq MM_match
    bcc +
    jmp MM_next
+
MM_match:
    lda framecnt                      ; age of the OLDEST matched element:
    sec                               ;   the whole motion must be within
    sbc ct_ets                        ;   the window of now -- the 8-bit tick
    cmp ct_win                        ;   wraps every 256 frames, so the
    beq +                             ;   span check alone can resurrect a
    bcc +                             ;   stale prefix (old D,DF,F + fresh
    jmp MM_next                       ;   press = phantom special)
+   rep #$20                          ; power gate: a rule whose target state
    .ACCU 16                          ;   carries a negative poweradd is a
MM_pow:
    lda ct_row                        ;   spend -- require F_POWER >= cost
    clc                               ;   (the cmd's `power >= N` triggerall)
    adc #6
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y                      ; target sid
    sta ct_tmp
    sep #$20                          ; 85-89: the descriptor MAX mask
    .ACCU 8                           ;   decides whether this slot needs
    stz ct_win                        ;   the MAX window
    lda ct_tmp
    cmp #85.b
    bcc MM_pow_cost
    cmp #90.b
    bcs MM_pow_cost
    sec
    sbc #85.b
    tay
    lda #1
    cpy #0
    beq +
-   asl a
    dey
    bne -
+   sta ct_off
    ldx #sptr
    ldy #CH_MAXMASK
    jsr CharPtr
    sep #$20                          ; CharPtr leaves cptr = descriptor
    .ACCU 8
    lda [cptr],y                      ; scalar byte, not a table pointer
    and ct_off
    beq MM_pow_cost                   ; ordinary super
    lda #1
    sta ct_win
    ldx fofs
    lda FP+F_MAX,x
    bne MM_pow_cost                   ; MAX active: pay the base cost
    ; Quick SDM outside MAX: three stocks.  Pay all of it here and skip
    ; the base cost check; EnterState clamps the base deduction to 0.
    rep #$20
    .ACCU 16
    lda FP+F_POWER,x
    cmp #3000.w
    bcs +
    jmp MM_rej                        ; out of 8-bit branch range
+   sec
    sbc #3000.w
    sta FP+F_POWER,x
    sep #$20
    .ACCU 8
    bra MM_powok
MM_pow_cost:
    rep #$20
    .ACCU 16
    ldy #CH_POWTAB
    ldx #sptr                         ; sptr -> PowTab (motion record is dead
    jsr CharPtr                       ;   past the match; lptr stays = MotTab)
    lda ct_tmp
    and #$00FF.w
    asl a
    tay
    lda [sptr],y                      ; signed delta
    bpl MM_powok                      ; grants or free: no cost
    eor #$FFFF.w
    inc a                             ; cost magnitude
    ldx fofs
    cmp FP+F_POWER,x
    beq MM_powok
    bcc MM_powok
    ; FUSION: Extra-mode critical-health free DM -- when the meter cannot
    ; cover the cost, ordinary supers (sids 85-87) still fire if the
    ; fighter's HP is under 25%
    sep #$20
    .ACCU 8
    lda ct_tmp
    cmp #85.b
    bcc MM_rej2
    cmp #90.b
    bcs MM_rej2
    lda ct_win
    bne MM_rej2                       ; MAX/SDM is never free
    lda FP+F_HP,x
    cmp #50.b
    bcc MM_powok
MM_rej2:
    jmp CT_next                       ; not enough meter: try the next rule
MM_powok:
    sep #$20
    .ACCU 8
    lda ct_cancel                     ; hit-cancel scans only accept combo
    beq CMC_take                      ;   routes: specials 48-66, supers
    lda ct_tmp                        ;   ct_tmp = rule target sid (MM_pow)
    cmp #69.b                         ; FUSION Attack Cancel Evade
    beq CMC_roll
    cmp #94.b                         ; FUSION Attack Cancel Roll back
    beq CMC_roll
    cmp #95.b                         ; FUSION Attack Cancel Roll fwd
    beq CMC_roll
    cmp #S_SPECIAL.b
    bcc CMC_next                      ; normals/system are not cancels
    cmp #67.b                         ; 48..66 = specials (projectile,
    bcc CMC_take                      ;   anti-air, rekka, command special)
    cmp #S_SUPPER.b                   ; 67..84 = throw/victim/system slots
    bcc CMC_next
    cmp #90.b                         ; 85..89 = supers
    bcs CMC_next
    bra CMC_take
CMC_roll:
    ldx fofs
    lda FP+F_POWER,x
    cmp #1000.w                       ; one stock, like arcade attack cancel
    bcc CMC_next
    sec
    sbc #1000.w
    sta FP+F_POWER,x
CMC_take:
    sep #$20                          ; consume: flag the newest matched ring
    .ACCU 8                           ;   entry (bit7 of its dir byte).  Entries
    lda ct_scan                       ;   stay in the ring so a later press can
    sta ct_off                        ;   still complete a command sharing the
    asl a                             ;   prefix (FF -> run, then FF+a); only
    clc                               ;   this press is spent -- the same trick
    adc ct_off                        ;   an 8-bit tick diff tried and failed
    rep #$30                          ;   to do past frame 127.  Zero-extend:
    .ACCU 16                          ;   16-bit tay would drag B along and
    and #$00FF.w                      ;   bury the flag in the wrong slot.
    tay
    sep #$20
    .ACCU 8
    lda [histp],y
    ora #$80
    sta [histp],y
    ldx fofs                          ; keep the debug stamp for test dumps
    lda ct_ts0
    sta FP+F_LASTCT,x
    rep #$20
    .ACCU 16
    lda ct_row
    tay
    sep #$20
    .ACCU 8
    iny
    iny
    iny
    iny
    iny
    iny
    lda [boxp],y                      ; rule target state
    rep #$20
    .ACCU 16
    and #$00FF.w
    ply                               ; drop CmdTry's return address: the
    jmp SetState16                    ;   handler must not run its fallback
CMC_next:
    jmp CT_next                       ; not a cancel target: keep scanning
MM_decelem:
    .ACCU 8                             ; entered from acc8 paths only
    lda ct_ei
    sec
    sbc #2
    sta ct_ei
MM_next:
    .ACCU 8                             ; entered from acc8 paths only
    lda ct_j
    dec a
    and #$0F
    ldx fofs
    cmp FP+F_HIST,x                     ; wrapped to the head: only stale slots
    beq +                             ;   remain -> stop scanning
    sta ct_j
    jmp MM_scan
+
CT_fail16:
    rep #$20
    .ACCU 16
CT_fail:
    jmp CT_next
MM_rej:
    jmp CT_next                       ; SDM gate reject (out of bra range)

CT_next:
    sep #$20                          ; normalize mode; may arrive from 16-bit
    .ACCU 8
    rep #$20
    .ACCU 16
    lda ct_row
    clc
    adc #7
    sta ct_row
    jmp CT_rule

; ---------------------------------------------------------------------------
; Pause menu: SELECT during a fight freezes the match and offers
; CONTINUE / EXIT.  EXIT returns to the title in the solo modes
; (SINGLE PLAY, TEAM PLAY, SURVIVOR, PRACTICE) and to character select in
; the versus modes (SINGLE VS, TEAM VS).
PauseOpen:
    sep #$20
    .ACCU 8
    lda FP+F_JOYPR+1                    ; SELECT is $2000: test the high
    and #$20.b                          ;   byte so this stays 8-bit.
    beq PO_p2
    stz.w PZ_SIDE                       ; P1 opened: show P1's command list
    bra PO_open
PO_p2:
    lda FP+F_JOYPR+FP2OFS+1
    and #$20.b
    beq PO_no
    lda #1
    sta.w PZ_SIDE                       ; P2 opened: show P2's command list
PO_open:
    lda #1
    sta.w PZ_ON
    stz.w PZ_SEL
    lda.l $7E46F8                       ; menu clips already loaded with the
    bne +                               ; stage module? (never switch sets
    lda #1                              ;  mid-drain: FxDrainFar reads this)
    sta.w UI_SFXLOAD
+   lda #SFX_MOVE.b
    jsr SfxPlay
    jsl PauseDraw
    sec
    rts
PO_no:
    clc
    rts

PauseClose:
    sep #$20
    .ACCU 8
    stz.w PZ_ON
    lda #0                              ; STA (8-bit): STZ always writes a
    sta.w UI_SFXLOAD                    ;   word, clobbering the next byte
    jsr CmdListClearPanel
    lda #1
    sta.w RT_HUDFULL                    ; overlay rows 7-21 are outside the
    lda huddirty                        ;   live bands: force a full upload
    ora #HUD_FULL                       ;   so the text really leaves VRAM
    sta huddirty
    rts

PauseTick:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    ora FP+F_JOYPR+FP2OFS
    sta scr0
    and #JOY_SE.w
    beq PT_nav
    sep #$20
    .ACCU 8
    lda #SFX_BACK.b
    jsr SfxPlay
    jmp PauseClose
PT_nav:
    rep #$20
    .ACCU 16
    lda scr0
    and #JOY_UP.w
    beq PT_down
    sep #$20
    .ACCU 8
    lda.w PZ_SEL
    bne +
    rts
+   dec a
    sta.w PZ_SEL
    lda #SFX_MOVE.b
    jsr SfxPlay
    jsl PauseDraw
    rts
PT_down:
    rep #$20
    .ACCU 16
    lda scr0
    and #JOY_DN.w
    beq PT_confirm
    sep #$20
    .ACCU 8
    lda.w PZ_SEL
    cmp #2.b
    bcc +
    rts
+   inc a
    sta.w PZ_SEL
    lda #SFX_MOVE.b
    jsr SfxPlay
    jsl PauseDraw
    rts
PT_confirm:
    rep #$20
    .ACCU 16
    lda scr0
    and #(JOY_A|JOY_X|JOY_Y|JOY_ST).w
    beq PT_cancel
    sep #$20
    .ACCU 8
    lda.w PZ_SEL
    beq PT_continue
    cmp #1.b
    beq PT_cmdlist
    bra PT_exit
PT_continue:
    lda #SFX_SELECT.b
    jsr SfxPlay
    jmp PauseClose
PT_cmdlist:
    lda #SFX_SELECT.b
    jsr SfxPlay
    jmp CmdListOpenFromPause
PT_cancel:
    rep #$20
    .ACCU 16
    lda scr0
    and #JOY_B.w
    bne +
    jmp PT_out
+   sep #$20
    .ACCU 8
    lda #SFX_BACK.b
    jsr SfxPlay
    jmp PauseClose
PT_exit:
    lda #SFX_BACK.b                       ; EXIT is an exit/back action
    jsr SfxPlay
    stz.w PZ_ON
    lda #0                              ; STA (8-bit): STZ always writes a
    sta.w UI_SFXLOAD                    ;   word, clobbering the next byte
    jsr CmdListClearPanel
    lda.w G_MODE
    cmp #0
    beq PT_sel
    cmp #3
    beq PT_sel
    stz.b wins1                          ; solo modes: fresh title screen
    stz.b wins2
    lda #1
    sta.b roundno
    jsr CampReset
    jmp TitleEnter
PT_sel:
    jmp TT_free                          ; versus: back to character select
PT_out:
    rts

; ---------------------------------------------------------------------------
; Far entry points for the YOU LOSE code (bank 126).  The Fight section is
; full, so the menu itself lives in the free tail of the select/voice bank and
; reaches these routines through the long-call wrappers below.
YLFar_CmdClear:     jsr CmdListClearPanel
                    rtl
YLFar_WriteStrBig:  jsr WriteStrBigData
                    rtl
YLFar_StartFight:   jsr StartFight
                    rtl
YLFar_ShowSelect:   jsr ShowSelect
                    rtl
YLFar_CampReset:    jsr CampReset
                    rtl
YLFar_TitleEnter:   jsr TitleEnter
                    rtl

; ---------------------------------------------------------------------------
FightTick:
    sep #$20
    .ACCU 8
    lda.w DM_ON
    bne FT_live                           ; attract demo: pads must not pause
    lda.w PZ_ON                           ;   or claim a CPU side mid-bout
    beq +
    jsr PauseTick                        ; match frozen while the menu is up
    rep #$20
    .ACCU 16
    rts
+   lda.w CL_OPEN
    beq +
    jsr CmdListTick                      ; practice submenu owns the screen
    rep #$20
    .ACCU 16
    rts
+   jsr FightJoinCheck                   ; START joins a CPU-driven side
    bcc +
    rep #$20
    .ACCU 16
    rts
+   jsr PauseOpen
    bcc +
    rts
+ FT_live:
    jsr PracFillPower                    ; practice: human meter stays full
    jsr BannerTick                       ; FIGHT! logo countdown -> clear
    lda.l APUIO3                         ; snesmod: music position / status
    sta sfxdone
    lda.l APUIO1
    sta sfxenv
    sep #$20
    .ACCU 8
    lda.b pausecnt                      ; byte access: $74 is shaketmr, not a
    beq +                               ;   pausecnt high byte -- a word read
    dec a                               ;   here aliased EnvShake ticks into a
    sta.b pausecnt                      ;   ~1024-tick full-match freeze
    rts                                 ; global Pause/SuperPause freeze:
                                        ;   positions, anims and hit checks
                                        ;   all hold (mugen movetime = 0)
+   lda shaketmr                          ; EnvShake global countdown
    beq +
    dec a
    sta shaketmr
+   lda FUS_FLASH                         ; FUSION COUNTER banner
    beq +
    dec a
    sta FUS_FLASH
    bne +
    jsr CounterClear
    sep #$20
    .ACCU 8
+   lda rframe                            ; slow dizzy decay: once/second
    bne +
    lda FUS_DIZZY
    beq ++
    dec a
    sta FUS_DIZZY
++  lda FUS_DIZZY+FP2OFS
    beq +
    dec a
    sta FUS_DIZZY+FP2OFS
+   lda.w G_MODE
    cmp #5
    beq ++                                ; practice: the clock never runs
    inc rframe                            ; round timer: 60 ticks/second
    lda rframe
    cmp #60.b
    bcc ++
    stz rframe
    dec rsecs
    beq +
    jsr DrawTimer
    sep #$20
    .ACCU 8
    lda huddirty
    ora #HUD_TIMER
    sta huddirty
    bra ++
+   jmp TimeOver                          ; 0:00 -> poses + round end
++  jsr HitCheck                          ; the presentation may have just
                                        ; committed an active pose; test it
                                        ; before AnimSetFrame advances the
                                        ; logical frame over the box
    jsr PracDrive
    jsr FaceEachOther
    ldx #0
    stx fofs
    jsr TickFighter
    sep #$20
    .ACCU 8
    ldx #FP2OFS
    stx fofs
    jsr TickFighter
    sep #$20
    .ACCU 8
    jsr BodySep
    jsr HitCheck
    sep #$20
    .ACCU 8
    jsr ComboTick
    jsr TickSpark
    jsr DrawBars
    sep #$20
    .ACCU 8
    rep #$20
    .ACCU 16
    jsr BuildOam
    lda FP+F_HP
    beq +
    lda FP+F_HP+FP2OFS
    beq +
    sep #$20
    .ACCU 8
    rts
+   sep #$20
    .ACCU 8
    lda FP+F_HP                         ; score the round: survivor wins,
    beq +++                             ;   double KO is a draw
    lda #1
    bra ++
+++ lda FP+F_HP+FP2OFS
    beq ++
    lda #2
++  sta roundwin
    lda #2
    sta gamestate                       ; -> KoTick while kotimer runs down
    lda #KO_TIME.b
    sta kotimer
    lda #SFX_KO.b
    jsr SfxPlay
    sta.l DBGREG_L+96                     ; sticky marker: KO sfx dispatched
    rep #$20                              ;   (sfxlast is overwritten by the
    .ACCU 16                              ;   landing thud a few ticks later)
    lda #((9*32+13)*2).w                  ; real K.O. logo, centred
    sta scr0
    lda #KoLogo.w
    sta scr2
    jsr WriteBlock
    sep #$20
    .ACCU 8
    rts

KoTick:
    ; A KO can be entered during hit-stop.  FightTick owns the normal
    ; pause countdown, but gamestate 2 bypasses it.  Hit-stop has no purpose
    ; after the deciding hit, so clear it and let the KO timer run normally.
    sep #$20
    .ACCU 8
    stz.b pausecnt
    ldx #0
    jsr KoMute
    stx fofs
    jsr TickFighter
    sep #$20
    .ACCU 8
    ldx #FP2OFS
    jsr KoMute
    stx fofs
    jsr TickFighter
    ldx #0                                ; a zero-HP fighter must never spend
    jsr KoHoldDown                        ;   the KO banner standing up (tail)
    ldx #FP2OFS
    jsr KoHoldDown
    jsr TickSpark
    rep #$20
    .ACCU 16
    jsr BuildOam
    sep #$20
    .ACCU 8
    dec kotimer
    bne +
    jsr RoundEnd
+   lda kotimer                         ; ~2/3s after KO: winner poses
    cmp #200.b
    bne +
    rep #$20
    .ACCU 16
    lda FP+F_HP
    beq KP_p2_alive
    lda FP+F_HP+FP2OFS
    bne KP_done                          ; both alive: time-over already posed
    ldx #0
    bra KP_go
KP_p2_alive:
    lda FP+F_HP+FP2OFS
    beq KP_done                          ; double KO -> nobody poses
    ldx #FP2OFS
KP_go:
    stx fofs
    lda FP+F_STATE,x                      ; time-over already posed them
    and #$00FF.w
    cmp #S_WPOSE.w
    beq KP_done
    lda #S_WPOSE.w
    jsr EnterState
KP_done:
    sep #$20
    .ACCU 8
+   jsr DemoKoTick                        ; attract demo: winner -> intro
    rts

; Round decided: score the winner (roundwin 0=draw), then chain into the
; next round's intermission or show the match-over banner.  First to 2
; wins takes the match; undecided after round 3 goes to the wins leader.
RoundEnd:
    sep #$20
    .ACCU 8
    ; FUSION: preserve both meters for the next round / team member.  The
    ; team swap consumes the loser's carry while the winner keeps its own.
    rep #$20
    .ACCU 16
    lda FP+F_POWER
    sta FUS_CARRY
    lda FP+F_POWER+FP2OFS
    sta FUS_CARRY+FP2OFS
    sep #$20
    .ACCU 8
    jsr SurvSaveHP                        ; survivor: carry the human HP
    lda.w G_MODE
    cmp #2
    beq RE_team
    cmp #3
    bne +
RE_team:
    jmp TeamRoundEnd                      ; team elimination, not best-of-3
+   lda.w G_MODE
    cmp #4
    beq RE_survivor
    cmp #1
    beq RE_single
    cmp #5
    beq RE_single                         ; practice follows Single Play
    jmp RE_normal
RE_survivor:
    lda.b roundwin
    beq SRE_lost                          ; draw: nobody can carry 0 HP
    lda.w C_HUMAN_SIDE
    inc a
    cmp.b roundwin
    bne SRE_lost                          ; human dropped a round -> run over
    jmp RE_normal
SRE_lost:
    lda.w C_HUMAN_SIDE
    beq SRE_lost_p1
    lda #2
    sta.b wins1
    stz.b wins2
    bra SRE_lost_ready
SRE_lost_p1:
    stz.b wins1
    lda #2
    sta.b wins2
SRE_lost_ready:
    lda #2
    sta.b nextflag                        ; match-over banner -> CampResolve
    jmp ShowTitle
RE_single:
    lda.w C_IDX
    cmp #6.b
    beq RE_final_round
    jmp RE_normal
RE_final_round:
    lda.w C_HUMAN_SIDE
    beq RE_boss_cpu2
    lda.b sel1                            ; P1 is CPU when P2 won the campaign
    bra RE_boss_char_ready
RE_boss_cpu2:
    lda.b sel2
RE_boss_char_ready:
    cmp #14.b
    beq RE_omega
    lda.w C_HUMAN_SIDE
    inc a
    cmp roundwin
    beq RE_rugal_fell
    jmp RE_normal
RE_rugal_fell:
    lda.w C_HUMAN_SIDE
    beq RE_omega_cpu2
    lda #14.b                             ; first Rugal round won: Omega enters
    sta.b sel1
    bra RE_omega_ready
RE_omega_cpu2:
    lda #14.b
    sta.b sel2
RE_omega_ready:
    stz wins1
    stz wins2
    lda #1                              ; Omega is a fresh boss match: start at
    sta.b roundno                       ;   round 1 so StartFight plays his
                                        ;   intro (later rounds/rematches skip)
    lda #1
    sta nextflag
    jmp ShowTitle
RE_omega:
    lda.w C_HUMAN_SIDE
    inc a
    cmp roundwin
    bne RE_boss_loss
    lda.w C_HUMAN_SIDE
    beq RE_omega_p1
    lda #2.b
    sta wins2
    stz wins1
    bra RE_omega_score_ready
RE_omega_p1:
    lda #2.b
    sta wins1
    stz wins2
RE_omega_score_ready:
    lda #1.b
    sta.w MATWON
    jsl BossEndingFar                   ; no winner banner: fade -> ending1
    rts
RE_boss_loss:
    lda.w C_HUMAN_SIDE
    eor #1.b
    inc a
    cmp roundwin
    bne RE_boss_draw
    lda.w C_HUMAN_SIDE
    beq RE_loss_cpu2
    lda #2.b
    sta wins1
    stz wins2
    bra RE_loss_score_ready
RE_loss_cpu2:
    lda #2.b
    sta wins2
    stz wins1
RE_loss_score_ready:
    lda #2.b
    sta nextflag
    jmp ShowTitle
RE_boss_draw:
    inc roundno
    lda #1
    sta nextflag
    jmp ShowTitle
RE_normal:
    lda roundwin
    beq RE_check                          ; draw: nobody scores
    cmp #1
    bne +
    inc wins1
    bra RE_check
+   inc wins2
RE_check:
    lda wins1
    cmp #2.b
    bcs RE_over
    lda wins2
    cmp #2.b
    bcs RE_over
    lda roundno
    cmp #3.b
    bcs RE_over
    inc roundno
    lda #1
    sta nextflag
    bra RE_done
RE_over:
    lda #2
    sta nextflag
RE_done:
    jmp ShowTitle

KoMute:                                 ; X = fighter offset: swallow inputs
    rep #$20
    .ACCU 16
    stz FP+F_JOY,x
    stz FP+F_JOYPR,x
    rts

; Gamestate 4: intro anims run with inputs muted until both fighters reach
; the stand state (the generated TransTab exits 191 -> 0 at anim end).
; Once they stand, the READY+GO announcer clip starts and the round still
; waits GO_WAIT frames: inputs stay muted, so the first hit cannot begin
; while the announcer is still calling GO.
IntroTick:
    ldx #0
    jsr KoMute
    stx fofs
    jsr TickFighter
    ldx #FP2OFS
    jsr KoMute
    stx fofs
    jsr TickFighter
    jsr TickSpark
    jsr BuildOam
    sep #$20
    .ACCU 8
    lda.b gotime                          ; announcer already running?
    beq IT_entrance
    dec a                                 ; READY+GO still playing: keep both
    sta.b gotime                          ;   fighters idle until it finishes
    beq IT_start
    jsr BannerTick                        ; FIGHT! logo keeps its countdown
IT_out:
    rep #$20
    .ACCU 16
    rts
IT_entrance:
    rep #$20
    .ACCU 16
    lda FP+F_STATE
    ora FP+F_STATE+FP2OFS                 ; either one still mid-intro?
    bne IT_out
    sep #$20
    .ACCU 8
    lda #99.b                             ; clock is drawn now, but only
    sta rsecs                             ;   counts once gotime expires
    stz rframe
    jsr DrawTimer
    rep #$20                            ; FIGHT! logo across the centre
    .ACCU 16                            ;   rows; bantime clears it later
    lda #((9*32+12)*2).w
    sta scr0
    lda #FgLogo.w
    sta scr2
    jsr WriteBlock
    sep #$20
    .ACCU 8
    lda #45.b
    sta.w BANTIME
    lda #1                              ; rows 9/10 lie outside the live HUD
    sta.w RT_HUDFULL                    ;   bands: the banded live-play flush
    lda huddirty                        ;   would skip the GO! logo otherwise
    ora #HUD_FULL
    sta huddirty
    lda #SFX_FIGHT.b
    jsr SfxPlay
    lda #GO_WAIT.b
    sta.b gotime
    rep #$20
    .ACCU 16
    rts
IT_start:
    lda #1.b                              ; GO over -> round is live
    sta gamestate
    rep #$20
    .ACCU 16
    rts

; Round clock reached zero: the higher-HP fighter wins the pose, the loser
; takes the mugen 170 lose pose; on a tie both lose.  The KO banner flow
; reuses gamestate 2.
TimeOver:
    sep #$20
    .ACCU 8
    jsr SurvClearHit                      ; timer win: no special finish bonus
    rep #$20
    .ACCU 16
    lda FP+F_HP
    cmp FP+F_HP+FP2OFS
    beq TO_both
    bcc TO_p1lose
    ldx #0
    stx fofs
    lda #S_WPOSE.w
    jsr EnterState
    ldx #FP2OFS
    stx fofs
    lda #S_LOSE.w
    jsr EnterState
    bra TO_done
TO_p1lose:
    ldx #0
    stx fofs
    lda #S_LOSE.w
    jsr EnterState
    ldx #FP2OFS
    stx fofs
    lda #S_WPOSE.w
    jsr EnterState
    bra TO_done
TO_both:
    ldx #0
    stx fofs
    lda #S_LOSE.w
    jsr EnterState
    ldx #FP2OFS
    stx fofs
    lda #S_LOSE.w
    jsr EnterState
TO_done:
    ldx #0
    stx fofs
    lda FP+F_HP                         ; higher HP takes the round
    cmp FP+F_HP+FP2OFS
    sep #$20
    .ACCU 8
    beq +
    lda #1
    bcs ++
    lda #2
    bra ++
+   lda #0                              ; tie -> draw
++  sta roundwin
    lda #2
    sta gamestate
    lda #KO_TIME.b
    sta kotimer
    lda #SFX_KO.b
    jsr SfxPlay
    rep #$20
    .ACCU 16
    lda #((9*32+11)*2).w
    sta scr0
    lda #BStrTime.w
    sta scr2
    jsr WriteStrBigData
    sep #$20
    .ACCU 8
    lda huddirty
    ora #HUD_FULL
    sta huddirty
    rts

; Draw the 2-digit countdown at the top center of the HUD (rsecs), using
; the tall KOF98 timer digits (two 8x8 tiles per digit, gold attr).
DrawTimer:
    rep #$20
    .ACCU 16
    ldx #((2*32+15)*2).w                  ; fight.def [Time] center
    ldy #0
    sep #$20
    .ACCU 8
    lda rsecs
    cmp #100.b
    bcc +
    lda #99.b
+
-   cmp #10
    bcc +
    sec
    sbc #10
    iny
    bra -
+   pha                                ; ones; keep the timer off shared
    tya                                ; scratch used by the HUD renderer
    asl a
    clc
    adc #BIGD0.b                         ; tens -> tall digit pair
    sta HUDMAP,x
    inc a
    sta HUDMAP+64,x                       ; bottom half on row 3
    lda #ATT_YEL.b
    sta HUDMAP+1,x
    sta HUDMAP+65,x
    pla
    asl a
    clc
    adc #BIGD0.b                         ; units
    sta HUDMAP+2,x
    inc a
    sta HUDMAP+66,x
    lda #ATT_YEL.b
    sta HUDMAP+3,x
    sta HUDMAP+67,x
    rep #$20
    .ACCU 16
    rts

FaceEachOther:
    rep #$20
    .ACCU 16
    lda FP+F_X
    cmp FP+F_X+FP2OFS
    bcs FE_right
    ; p1 left of p2: p1 faces right, p2 faces left (grounded fighters only;
    ; MUGEN has noAutoTurn while airborne).  Only idle/movement states
    ; (0-4) auto-turn: attacks, hits, guards and throws own their facing
    ; (the throw bind would flip-flop facing every tick otherwise).
    lda FP+F_GRAB
    and #$00FF.w
    bne +
    lda FP+F_STATE
    and #$00FF.w
    cmp #5.w
    bcs +
    lda FP+F_Y
    bne +
    lda #1
    sta FP+F_FACING
+   lda FP+F_GRAB+FP2OFS
    and #$00FF.w
    bne FE_done
    lda FP+F_STATE+FP2OFS
    and #$00FF.w
    cmp #5.w
    bcs FE_done
    lda FP+F_Y+FP2OFS
    bne FE_done
    lda #$FFFF.w
    sta FP+F_FACING+FP2OFS
    bra FE_done
FE_right:
    lda FP+F_GRAB
    and #$00FF.w
    bne +
    lda FP+F_STATE
    and #$00FF.w
    cmp #5.w
    bcs +
    lda FP+F_Y
    bne +
    lda #$FFFF.w
    sta FP+F_FACING
+   lda FP+F_GRAB+FP2OFS
    and #$00FF.w
    bne FE_done
    lda FP+F_STATE+FP2OFS
    and #$00FF.w
    cmp #5.w
    bcs FE_done
    lda FP+F_Y+FP2OFS
    bne FE_done
    lda #1
    sta FP+F_FACING+FP2OFS
FE_done:
    rep #$20
    .ACCU 16
    rts

TickFighter:
    rep #$20
    .ACCU 16
    ldx fofs
    jsr PushHist
    ldx fofs
    inc FP+F_STIME,x
    sep #$20
    .ACCU 8
    lda FP+F_INVUL,x                      ; NotHitBy countdown; $FF means
    beq +                                 ;   "for the rest of the state"
    cmp #$FF.b
    beq +
    dec a
    sta FP+F_INVUL,x
+   lda FP+F_PFX,x                        ; PalFX flash countdown
    beq +
    dec a
    sta FP+F_PFX,x
+   lda FP+F_MAX,x                        ; FUSION: MAX-mode window ticks down
    beq +
    dec a
    sta FP+F_MAX,x
    beq +
    lda #2.b                           ; keep the bright MAX palette alive
    sta FP+F_PFX,x
+   rep #$20
    .ACCU 16
    jsr ApplyTimeActions
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    tax
    jsr (StateTab,x)
    jsr ApplyVelMul
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_TFLAGS,x                     ; PosFreeze latch: cancel whatever
    and #$08.b                            ;   velocity the state handler set
    beq +
    rep #$20
    .ACCU 16
    stz FP+F_VX,x
    stz FP+F_VY,x
+   jsr GhostTick                         ; afterimage push + ttl decay
    jsr DizzyCheck                        ; FUSION stun when neutral
    rep #$20
    .ACCU 16
    rts

ApplyVelMul:                            ; per-tick CNS VelMul: vx *= Q8/256
    sep #$20                            ;   while F_VMUL is armed (op16) for
    .ACCU 8                             ;   this state.
    ldx fofs
    lda FP+F_VMUL,x
    beq AVM_done
    rep #$20
    .ACCU 16
    lda FP+F_VX,x
    sta scr3                            ; signed original
    bpl +
    eor #$FFFF.w
    inc a
+   sta scr5                            ; |vx|
    sep #$20
    .ACCU 8
    lda scr5+1                          ; integer part
    sta scr0
    lda FP+F_VMUL,x
    sta scr1
    rep #$20
    .ACCU 16
    jsr Mul8                            ; scr2 = hi*f
    lda scr2
    sta scr4
    sep #$20
    .ACCU 8
    lda scr5                            ; fractional part
    sta scr0
    lda FP+F_VMUL,x
    sta scr1
    rep #$20
    .ACCU 16
    jsr Mul8                            ; scr2 = lo*f
    lda scr2
    xba
    and #$00FF.w                        ; (lo*f) >> 8
    clc
    adc scr4
    sta scr2
    lda scr3
    bpl +
    lda scr2
    eor #$FFFF.w
    inc a
    sta scr2
+   lda scr2
    sta FP+F_VX,x
    rep #$20
    .ACCU 16
    rts
AVM_done:
    rep #$20
    .ACCU 16
    rts

Mul8:                                   ; scr0.l * scr1.l -> scr2.w
    rep #$20
    .ACCU 16
    lda scr0
    and #$00FF.w
    sta scr0
    lda scr1
    and #$00FF.w
    sta scr1
    stz scr2
    ldy #8
-   lsr scr1
    bcc +
    lda scr2
    clc
    adc scr0
    sta scr2
+   asl scr0
    dey
    bne -
    rts

StateTab:
    .dw StStand, StWalk, StWalk, StCrouch, StJump
    .dw StAttack, StAttack, StAttack, StAttack
    .dw StHit, StDown, StDizzy
    .dw StCDown, StCUp, StJStart, StJump, StJump
    .dw StLand, StGetUp
    .dw StCrouchAtk, StCrouchAtk, StCrouchAtk, StCrouchAtk
    .dw StAirAtk, StAirAtk, StAirAtk, StAirAtk
    .dw StGuard, StCGuard, StAGuard, StGHit  ; 29 = air guard/air guard-hit
    ; 31-44 are AnimTab slots, not states -- never dispatched
    .dw StateRet, StateRet, StateRet, StateRet, StateRet, StateRet, StateRet
    .dw StateRet, StateRet, StateRet, StateRet, StateRet, StateRet, StAirThrow
    .dw StRun, StBackD, StSpecial          ; 45 run, 46 backdash, 47 taunt
    .dw StSpecial, StSpecial, StAirSpec, StAirSpec   ; 48-49 palm, 50-51 DP
    .dw StSpecial, StSpecial, StSpecial, StSpecial   ; 52-55 blow/zankou
    .dw StSpecial, StSpecial, StSpecial, StSpecial   ; 56-59 fast variants
    ; 60-69 Kung Fu Knee family: ground/lauch/land states are PosTab-driven
    ;   like the other specials; the air phases need gravity + TransTab
    .dw StSpecial, StAirSpec, StSpecial, StAirSpec, StSpecial ; 60-64
    .dw StSpecial, StAirSpec, StSpecial, StAirSpec, StAirSpec ; 65-69
    .dw StVictimShake, StVictimFly, StVictimWall, StVictimBounce ; 70-73
    ; 74 throw attempt (physics S, hitbox owns the grab), 75 bind seq,
    ; 76 bound victim, 77 thrown victim flight
    .dw StSpecial, StThrow, StVictimHeld, StVictimThrow
    ; 78-84 Kung Fu Blocking: parry stances, blocked freezes, air land
    .dw StBlock, StBlocked, StBlock, StBlocked, StBlockAir, StBlockAir
    .dw StBLand
    ; 85 Smash Kung Fu Upper (MoveHit -> 86), 86 success pose,
    ; 87-89 Triple Kung Fu Palm anim slices (velset-driven dash)
    .dw StAirSpec, StSpecial, StSuper, StSuper, StSuper
    ; 90 win pose, 91 time-over lose pose, 92 intro
    .dw StSpecial, StSpecial, StSpecial
    ; 93 AnimTab slot (never dispatched), 94 FUSION roll (velset-driven,
    ;   needs vx preserved), 95 FUSION extra dodge (stationary)
    .dw StateRet, StAirSpec, StSpecial
    ; 96 FUSION MAX activation burst, 97 FUSION manual charge (extra mode)
    ; 98 Yumebiki second hit (iori)
    .dw StSpecial, StCharge, StSpecial
    ; 99-102 counter-grab runtime slots: actor / held opponent (high, low)
    .dw StThrow, StVictimHeld, StThrow, StVictimHeld
    ; 103-106 ReversalDef counter-attack follow-ups (p1stateno without a
    ;   p2 held state): Yamazaki/Kyo/Shingo/Billy-style parry counters.
    .dw StSpecial, StSpecial, StSpecial, StSpecial
    ; 107+ per-character extended follow-ups.  Blue Mary uses these for the
    ;   Vertical Arrow air phases (107/108), the Goodnight throw (109) and
    ;   the Typhoon grabs (110/111).  They dispatch like ordinary specials.
    .dw StAirSpec, StAirSpec, StSpecial, StSpecial, StAirSpec

StateRet:
    rep #$20
    .ACCU 16
    jsr Physics
    ; MUGEN evaluates ChangeState triggers every tick, including on
    ; ground/special states that later become airborne (Athena 1020 jumps
    ; and lands into 1021).  StAirSpec/StBlockAir already do this; without
    ; the check here a special whose landing target is not a wired port
    ; state kept its looping animation on the last frame forever.
    jsr TransAir
    jsr AnimTick
    rts                                 ; ClampX lives in the FightMenuTail

; BodySep: grounded, non-grabbed fighters keep BODY_SEP pixels between
; axes (the mugen pushbox).  Without it a forward-moving attack glides
; through the opponent and its active frames never overlap a hurtbox.
; Pinned fighters (hitstun/down/guard-hit/victim/parry states) do not
; slide; if only one side is free it takes the whole deficit.  FightTick
; calls it after both TickFighter passes, so hitpause skips it via the
; global pausecnt early-out.
BodySep:
    rep #$20
    .ACCU 16
    lda FP+F_Y.w
    ora FP+F_Y+FP2OFS.w
    beq +
    jmp BS_done                           ; airborne pass-through
+   sep #$20
    .ACCU 8
    lda FP+F_GRAB.w
    ora FP+F_GRAB+FP2OFS.w
    beq +
    jmp BS_done                           ; throw/victim overlap is scripted
+   stz scr3                              ; pin flags: bit0 p1, bit1 p2
    lda FP+F_STATE.w
    jsr BS_pin
    beq +
    lda #1
    tsb scr3
+       lda FP+F_STATE+FP2OFS.w
    jsr BS_pin
    beq +
    lda #2
    tsb scr3
+   lda scr3
    and #3
    cmp #3
    bne +
    jmp BS_done                           ; nobody can move
+
    rep #$20
    .ACCU 16
    lda FP+F_X+FP2OFS.w
    sec
    sbc FP+F_X.w                          ; dx = p2 - p1 (signed, 8.8)
    sta scr0
    bpl +
    eor #$FFFF.w
    inc a
+   sta scr2                              ; |dx|
    lda #BODY_SEP
    sec
    sbc scr2
    bcc BS_done                           ; already far enough
    sta scr2                              ; deficit (8.8)
    lda scr3                              ; acc16 read: low byte holds flags
    and #$0003.w
    bne +                                 ; one pinned: full deficit
    lsr scr2                              ; both free: half each
+   lda scr0
    bmi BS_p1right                        ; dx<0 -> p1 stands right of p2
    lda scr3
    and #$0001.w
    bne +
    lda #0                                ; p1 free: push left
    sec
    sbc scr2
    ldx #0
    jsr AddXClamped
+   lda scr3
    and #$0002.w
    bne BS_done
    lda scr2                              ; p2 free: push right
    ldx #FP2OFS.w
    jsr AddXClamped
    bra BS_done
BS_p1right:
    lda scr3
    and #$0001.w
    bne +
    lda scr2                              ; p1 free: push right
    ldx #0
    jsr AddXClamped
+   lda scr3
    and #$0002.w
    bne BS_done
    lda #0                                ; p2 free: push left
    sec
    sbc scr2
    ldx #FP2OFS.w
    jsr AddXClamped
BS_done:
    rep #$20
    .ACCU 16
    rts
BS_pin:                                 ; acc8 A=state -> A!=0 when pinned
    .ACCU 8                               ;  call sites run acc8; the .ACCU
    cmp #S_HIT.b                          ;  hint keeps lda #imm byte-sized
    beq BS_pinned
    cmp #S_DOWN.b
    beq BS_pinned
    cmp #S_GHIT.b                         ; guard-hit carries own pushback
    beq BS_pinned
    cmp #S_VSHAKE.b                       ; 70-84 victim/parry family
    bcc +
    cmp #S_BLAND.b+1
    bcc BS_pinned
+   lda #0
    rts
BS_pinned:
    lda #1
    rts


; ---------------------------------------------------------------------------
; Combo counter.  combohit is indexed by the ATTACKER's fighter offset
; (0/$40 -> DP $8B/$CB).  A landed hit keeps counting while the victim sits
; in a damage animation (S_HIT, airborne fall S_DOWN = juggle, or the
; attacker-owned 70-84 victim chain); ComboBump runs in HO_apply before the
; victim's state switches, so the pre-hit state tells fresh hit vs
; continuation.  ComboTick starts a short (8t) clearing window the tick a
; victim leaves those states - long enough to bridge the 1-2 tick gap
; inside a rekka chain, short enough that a hit after the victim recovers
; or lies on the ground starts a new count.
ComboBump:
    .ACCU 16
    ldx vofs
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_HIT.w
    beq +
    cmp #S_DOWN.w
    beq +
    cmp #S_VSHAKE.w
    bcc CB_fresh
    cmp #S_BLAND.w+1
    bcs CB_fresh
+   sep #$20
    .ACCU 8
    ldx aofs
    lda combohit,x
    cmp #99.b
    bcs CB_draw
    inc a
    bra CB_draw
CB_fresh:
    sep #$20
    .ACCU 8
    ldx aofs
    lda combotmr,x                      ; victim barely recovered: rekka gap /
    beq +                               ;   juggle still continues the count
    lda combohit,x
    inc a
    bra CB_draw
+   lda #1
CB_draw:
    sta combohit,x
    stz combotmr,x
    jsr ComboDraw
    rep #$20
    .ACCU 16
    rts
ComboTick:                              ; per FightTick (acc16): a victim
    rep #$20
    .ACCU 16
    ldx #0                              ;   back in a free state ends the
    jsr CB_check                        ;   attacker's run and clears the HUD
    ldx #FP2OFS
    jsr CB_check
    rts
CB_check:                               ; X = fighter -> clear opponent's count
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_HIT.w
    beq +
    cmp #S_VSHAKE.w
    bcc ++
    cmp #S_BLAND.w+1
    bcc +
++  sep #$20
    .ACCU 8
    txa
    eor #FP2OFS.b
    tax
    lda combohit,x
    beq +++
    lda combotmr,x                      ; victim out of a hit state: keep the
    bne ++++                            ;   count (and the display) through a
    lda #8.b                            ;   short grace, then erase
    sta combotmr,x
    bra +++
++++
    dec a
    sta combotmr,x
    bne +++
    stz combohit,x
    jsr ComboDraw
+++ rep #$20
    .ACCU 16
+   rts
ComboDraw:                              ; acc8, X = attacker ofs: "<n> HITS"
    lda combohit,x                      ;   under the name (2+ hits; else erase)
    sta scr6
    rep #$20
    .ACCU 16
    txa
    bne +
    ldx #((11*32+2)*2).w                ; fight.def [Combo] y=195
    bra ++
+   ldx #((11*32+24)*2).w               ; P2 row
++  sep #$20
    .ACCU 8
    lda scr6
    cmp #2.b
    bcs CD_show
    ldy #6
    lda #0
-   sta HUDMAP,x                        ; blank tile, blank attr
    sta HUDMAP+1,x
    inx
    inx
    dey
    bne -
    bra CD_done
CD_show:
    lda #0
    sta scr5                            ; tens
    lda scr6
-   cmp #10.b
    bcc +
    sbc #10.b
    inc scr5
    bra -
+   tay                                 ; ones digit
    lda scr5
    beq +
    clc
    adc #27.b
    sta HUDMAP,x
    bra ++
+   stz HUDMAP,x
++  lda #$2C.b
    sta HUDMAP+1,x
    inx
    inx
    tya
    clc
    adc #27.b
    sta HUDMAP,x
    lda #$2C.b
    sta HUDMAP+1,x
    inx
    inx
    rep #$20                            ; "HITS" via WriteStr: absolute
    .ACCU 16                            ;   reads use DBR=$7E (WRAM), so the
    stx scr0                            ;   literal needs a far pointer
    lda #ComboHits.w
    sta scr2
    sep #$20
    .ACCU 8
    lda #:ComboHits.b
    sta scr2+2
    jsr WriteStr
CD_done:
    sep #$20                            ; WriteStr returns with A=16
    .ACCU 8                             ; the erase path already has A=8
    lda huddirty
    ora #HUD_COMBO
    sta huddirty
    rep #$20
    .ACCU 16
    rts
StAirSpec:                              ; knee-style air phases: gravity via
    rep #$20                            ; Physics; TransTab supplies the
    .ACCU 16                            ; live (kind 1 land / kind 2 follow-up
    jsr Physics                         ; press) ChangeState rules
    jsr TransAir
    jsr AnimTick
    jmp ClampX

; Fast-palm custom victim chain (MUGEN 1025-1028). F_GRAB bit1 makes
; CharPtr/animation DMA read the attacker's data for ChangeAnim2; bit0 keeps
; the victim out of normal hit/turn processing until SelfState 5100.
StVictimShake:                          ; 1025: frozen during victim hit-pause
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda FP+F_HTIMER,x
    beq VS_release
    dec a
    sta FP+F_HTIMER,x
    bne VS_anim
VS_release:
    lda #S_VFLY.w
    jsr EnterState
    ldx fofs
    lda FP+F_HITVX,x                    ; HitVelSet: velocity belongs to the
    sta FP+F_VX,x                       ; attacker's HitDef, not the victim
    lda FP+F_HITVY,x
    sta FP+F_VY,x
    rts
VS_anim:
    jmp AnimTick

StVictimFly:                            ; 1026: launched until wall/floor
    rep #$20
    .ACCU 16
    jsr Physics
    ldx fofs
    lda FP+F_Y,x
    bne VF_wall
    lda FP+F_VY,x
    bmi VF_wall
    jmp VictimSelfDown
VF_wall:
    lda FP+F_Y,x
    cmp #15<<8.w                        ; wall bounce only while clearly aloft
    bcc VF_anim
    lda FP+F_X,x
    cmp #(STAGE_L+20)<<8.w
    bcc VF_hitwall
    cmp #(STAGE_R-20)<<8.w
    bcs VF_hitwall
VF_anim:
    jsr AnimTick
    jmp ClampX
VF_hitwall:
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda #S_VWALL.w
    jsr EnterState
    jmp ClampX

StVictimWall:                           ; 1027: PosFreeze + ChangeAnim2
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_STIME,x
    cmp #1                                ; entry tick only
    bne VW_move
    lda FP+F_X,x                          ; mugen PosAdd x=15-BackEdgeBodyDist:
    cmp #68<<8.w                         ;   snap the victim flush to the wall
    bcs +
    lda #(STAGE_L+15)<<8.w                ;   it just hit, 15px in
    bra ++
+   lda #(STAGE_R-15)<<8.w
++  sta FP+F_X,x
    cmp #68<<8.w                         ; mugen Turn: face back toward the
    bcs +                                 ;   stage center to take the bounce
    lda #1.w
    bra ++
+   lda #$FFFF.w
++  sta FP+F_FACING,x
    lda FP+F_X,x                          ; wall-impact spark at chest height
    xba
    and #$00FF.w
    sta scr0
    lda #(GROUND_Y-28).w
    sta scr1
    lda #0                                ; SparkHit
    jsr SparkSpawnAt
VW_move:
    ldx fofs
    stz FP+F_VX,x
    stz FP+F_VY,x
    jsr AnimTick                         ; its end is intercepted below
    jmp ClampX

VictimBounceEnter:                      ; 1027 AnimTime=0 -> 1028
    rep #$20
    .ACCU 16
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_GRAB,x
    and #$01.b                           ; keep custom-state immunity, but
    sta FP+F_GRAB,x                      ; ChangeAnim now uses victim sprites
    rep #$20
    .ACCU 16
    lda FP+F_FACING,x                    ; VelSet x=1.6 before the wall Turn
    bmi +
    lda #$019A.w
    bra ++
+  lda #-$019A.w
++ sta FP+F_VX,x
    lda FP+F_FACING,x                    ; turn away from the wall after vx
    eor #$FFFF.w
    inc a
    sta FP+F_FACING,x
    lda #-$0600.w
    sta FP+F_VY,x
    lda #S_VBOUNCE.w
    jsr EnterState
    rts

StVictimBounce:                         ; 1028: own fall anim, 0.35 gravity
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_VY,x
    clc
    adc #VBOUNCEGRAV.w
    sta FP+F_VY,x
    lda FP+F_Y,x
    sec
    sbc FP+F_VY,x
    bpl +
    lda #0
+   sta FP+F_Y,x
    lda FP+F_VX,x
    jsr AddXClamped
    lda FP+F_Y,x
    bne VB_anim
    lda FP+F_VY,x
    bmi VB_anim
    jmp VictimSelfDown
VB_anim:
    jsr AnimTick
    jmp ClampX

VictimSelfDown:                         ; SelfState 5100: return to own data
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_GRAB,x                      ; clears F_GRAB + F_OWNER
    stz FP+F_Y,x
    stz FP+F_VY,x
    lda #30.w
    sta FUS_JUGGLE,x
    lda FP+F_JOY,x                       ; ukemi works off a throw landing
    and #(JOY_A|JOY_B).w                 ;   too: A+B -> recovery roll
    cmp #(JOY_A|JOY_B).w
    bne +
    jmp RollRecover
+   lda #S_DOWN.w
    jsr EnterState
    ldx fofs
    lda #LIEDOWN.w
    sta FP+F_HTIMER,x
    rts

; KOF98 recovery roll (ukemi): holding A+B on the tick the body reaches
; the floor rolls forward instead of lying down.  sid 94 = mugen 710
; (the FUSION roll state -- velset-driven StAirSpec); vx is applied here
; so the mugen VelSet's direction input is not required.
.DEFINE ROLLSPD     $0400               ; 4 px/tick forward
.DEFINE ROLLINV     18                  ; invuln ticks through the roll
RollRecover:                            ; tail call: fofs = victim, acc16
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_Y,x
    stz FP+F_VY,x
    lda #30.w
    sta FUS_JUGGLE,x
    lda #94.w
    jsr EnterState
    ldx fofs
    lda FP+F_FACING,x
    bmi +
    lda #ROLLSPD.w
    bra ++
+   lda #-ROLLSPD.w
++  sta FP+F_VX,x
    lda #ROLLINV.w
    sta FP+F_INVUL,x
    rts

; Kung Fu Throw (800 -> 810; victim 820 -> 821).  The attacker re-seats
; the bound victim every tick from the generated BindTab windows; the
; elem-gated ActTab rows (turn/posadd/target facing+life+state) fire
; inside AnimSetFrame alongside the PosTab timeline.
.DEFINE THROWGRAV   $0066               ;  0.4 px/tick^2 (state 821 VelAdd)
.DEFINE ESCWIN      12                  ; throw-tech window: ticks since grab
.DEFINE ESPUSH      $0300               ; escape pushback: 3 px/tick
.DEFINE ESSTUN      16                  ; escape flinch length

StThrow:                                ; 810: drive the held victim
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jsr Physics
    jsr TransAir                        ; bind states may end on a landing
                                        ;   rule (Chris 810 -> 820) rather
                                        ;   than AnimTime=0
    jsr AnimTick                        ; act rows land on the elem edge
    jsr ThrowBind
    jmp ClampX

ThrowBind:                              ; victim in S_VHELD tracks this
    rep #$20                            ; fighter's bind offsets
    .ACCU 16
    ldx fofs
    txa
    eor #FP2OFS.w
    sta scr5                            ; candidate victim offset
    tax
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_VHELD.w
    beq +
    cmp #S_CGRAB_HIV.w
    beq +
    cmp #S_CGRAB_LOV.w
    beq +
    jmp TB_out                          ; released already -> nothing bound
+
    ldy #CH_BINDTAB.w
    ldx #boxp
    jsr CharPtr                         ; boxp -> per-state BindTab ptrs
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    tay
    lda [boxp],y
    bne +
    rts
+   sta sptr
    jsr DataFighterX
    sep #$20
    .ACCU 8
    lda FP+F_TBANK,x
    sta sptr+2
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_FRAME,x
    and #$00FF.w
    sta scr6                            ; current elem (0-based)
    ldy #0
TB_row:
    sep #$20
    .ACCU 8
    lda [sptr],y                        ; window lo; $FF ends
    cmp #$FF
    beq TB_done8
    lda scr6
    cmp [sptr],y                        ; frame < lo -> next row
    bcc TB_next
    iny
    lda [sptr],y                        ; window hi
    cmp scr6                            ; hi < frame -> next row
    bcc TB_next1
    iny
    lda [sptr],y                        ; dx (s8)
    sta scr2
    iny
    lda [sptr],y                        ; dy (s8, mugen: negative = up)
    sta scr2+1
    rep #$20
    .ACCU 16
    bra TB_apply
TB_next1:
    dey                                 ; back to the row base
TB_next:
    rep #$20
    .ACCU 16
    tya
    clc
    adc #4
    tay
    bra TB_row
TB_apply:
    lda scr2                            ; dx in pixels, facing-relative
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   xba                                 ; <<8 fixed point
    ldx fofs
    ldy FP+F_FACING,x
    bpl +
    eor #$FFFF.w
    inc a
+   sta scr0                            ; facing*dx
    lda FP+F_X,x                        ; victim sits at attacker.x ...
    ldx scr5
    sta FP+F_X,x
    lda scr0
    jsr AddXClamped                     ; ... plus the bind offset, clamped
    lda scr2+1
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   xba
    eor #$FFFF.w                        ; our Y grows upward: -dy
    inc a
    ldx scr5
    sta FP+F_Y,x
TB_done8:
    rep #$20
    .ACCU 16
TB_out:
    rts

StVictimHeld:                           ; 820: bound pose, own anim data
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_OWNER,x
    and #$00FF.w
    tax
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_TSEQ.w
    beq +
    cmp #S_CGRAB_HI.w
    beq +
    cmp #S_CGRAB_LO.w
    beq +
    ; Imported throw follow-ups (Goodnight / Typhoon) are ordinary specials
    ; rather than 75/99/101, but they own the same TargetBind sequence.
    cmp #S_EXT_GRAB.w
    bcc VH_free
    cmp #(S_EXT_LAST+1).w
    bcs VH_free
+   ldx fofs
    ; KOF98 throw tech: a fresh strong-button press (Y or B -- the throw
    ;   inputs) inside the opening ticks of the bind breaks the hold.
    ; Counter-grab victim slots are guaranteed: skip the tech window.
    lda FP+F_STATE,x
    cmp #S_CGRAB_HIV.w
    beq VH_no_tech
    cmp #S_CGRAB_LOV.w
    beq VH_no_tech
    lda FP+F_STIME,x
    cmp #ESCWIN.w
    bcs VH_no_tech
    lda FP+F_JOYPR,x
    and #(JOY_Y|JOY_B).w
    bne VH_escape
VH_no_tech:
    jsr AnimTick                        ; victim's own anim 820; position
    rts                                 ;   is owned by the attacker's bind
VH_escape:                              ; tech: both fighters back to neutral
    ldx fofs
    stz FP+F_GRAB,x                     ; victim released (clears F_OWNER too)
    txa
    eor #FP2OFS.w
    tax
    stz FP+F_GRAB,x                     ; attacker: whiffed grab -> stand
    stx fofs
    lda #S_STAND.w
    jsr EnterState
    ldx fofs
    txa
    eor #FP2OFS.w
    tax
    stx fofs
    lda #S_HIT.w                        ; victim: brief flinch pushed back
    jsr EnterState                      ;   (htimer must follow EnterState,
    ldx fofs                            ;    which clears it)
    lda FP+F_FACING,x
    bmi +
    lda #-ESPUSH.w
    bra ++
+   lda #ESPUSH.w
++  sta FP+F_VX,x
    lda #ESSTUN.w
    sta FP+F_SLIDE,x                      ; slide window keeps vx alive
    sta FP+F_HTIMER,x
    jmp StateRet
VH_free:                                ; bind lost mid-throw (attacker hit):
    ldx fofs                            ;   SelfState 5050 -> plain fall
    stz FP+F_GRAB,x                     ;   (clears F_OWNER too)
    lda FP+F_Y,x
    beq +
    lda #S_HIT.w                        ; EnterState clears htimer, so the
    jsr EnterState                      ;   $FF stun must be written after
    ldx fofs
    lda #$FF.w                          ; hitstun outlasts any fall: a
    sta FP+F_HTIMER,x                   ;   release never recovers mid-air
    jmp StateRet
+   jmp VictimSelfDown

StVictimThrow:                          ; 821: thrown flight, VelAdd y=0.4
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_VY,x
    clc
    adc #THROWGRAV.w
    sta FP+F_VY,x
    lda FP+F_Y,x
    sec
    sbc FP+F_VY,x
    bpl +
    lda #0
+   sta FP+F_Y,x
    lda FP+F_VX,x
    jsr AddXClamped
    lda FP+F_Y,x
    bne VT_anim
    lda FP+F_VY,x
    bmi VT_anim
    jmp VictimSelfDown
VT_anim:
    jsr AnimTick
    jmp ClampX

; TransAir: fire the first live (kind 1/2/3/4) TransTab row for the current
; state.  kind 1: falling (vy > 0) and height <= arg px -> land.  kind 2:
; still rising (vy < -1px) and pad arg just pressed -> air follow-up.
; kind 3: MoveHit -- the state's HitDef already connected (supers).
; kind 4: distance gate -- arg.lo = max centre distance in px, arg.hi =
;         first animation frame (running grabs such as Takuma's Shouran
;         Kyaku, which grabs on contact after the run).
TransAir:
    ldy #CH_TRANSTAB
    ldx #sptr
    jsr CharPtr                           ; sptr -> character TransTab
TA_row:
    ldx fofs
    lda [sptr]
    and #$00FF.w
    cmp #$00FF.w
    beq TA_done
    cmp FP+F_STATE,x
    bne TA_next
    ldy #2
    lda [sptr],y                          ; kind byte
    and #$00FF.w
    cmp #1
    beq TA_land
    cmp #2
    beq TA_press
    cmp #3
    beq TA_hit
    cmp #4
    beq TA_dist
TA_next:
    lda sptr
    clc
    adc #5
    sta sptr
    bra TA_row
TA_land:
    lda FP+F_VY,x
    bmi TA_next                           ; still rising
    beq TA_next                           ; not launched yet (entry vy==0):
                                          ;   a 1-tick skip at the apex is
                                          ;   cheaper than instant-landing
                                          ;   states that rise via ActTab
    ldy #3                                ; vy == 0 is fine when F_Y already
    lda [sptr],y                          ;   reads 0 (Physics clamps before
    xba                                   ;   TransAir runs); the threshold
    cmp FP+F_Y,x                          ;   alone rejects the airborne apex
    bcc TA_next                           ; still above it: keep flying
    bra TA_fire
TA_press:
    lda FP+F_VY,x
    cmp #-256.w
    bpl TA_next                           ; mugen `Vel y < -1`: must be rising
                                          ; (vy+256 cannot overflow in 8.8)
    ldy #3
    lda [sptr],y                          ; single-button pad mask
    and FP+F_JOYPR,x                      ; fresh presses only
    cmp [sptr],y
    bne TA_next
TA_hit:
    lda FP+F_HITDONE,x                    ; MoveHit: the attack connected
    and #$00FF.w                          ;   (hit, guard or parry); one tick
    beq TA_next                           ;   late since HitCheck runs after
    bra TA_fire                           ;   the state handlers
TA_dist:
    jsr TransDistGate                     ; low-bank helper: C=1 -> grab
    bcc TA_next
TA_fire:
    ldy #1
    lda [sptr],y
    and #$00FF.w
    jmp EnterState                        ; tail: returns to our caller
TA_done:
    rts

; TransEnd: A(16) = target state of the first kind-0 (AnimTime = 0)
; TransTab row for the current state, or $FFFF when none.  Knee states
; chain ground -> air -> land through these.
TransEnd:
    ldy #CH_TRANSTAB
    ldx #sptr
    jsr CharPtr
TE_row:
    ldx fofs
    lda [sptr]
    and #$00FF.w
    cmp #$00FF.w
    beq TE_none
    cmp FP+F_STATE,x
    bne TE_next
    ldy #2
    lda [sptr],y
    and #$00FF.w
    bne TE_next                           ; kinds 1/2 are per-tick rules
    ldy #1
    lda [sptr],y
    and #$00FF.w
    rts
TE_next:
    lda sptr
    clc
    adc #5
    sta sptr
    bra TE_row
TE_none:
    lda #$FFFF.w
    rts

; TransLive: A(16) != 0 when the current state still has a live (kind 1/2)
; TransTab row -- AnimTick freezes on the last frame while such a state
; waits on its positional/input transition.  The body lives in the bank's
; low half (see TransLive at the tail) so the 32 KiB Fight window keeps its
; slack.

StStand:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_JOY,x
    and #(JOY_DN).w                        ; down first: D+button is a low hit
    beq +
    jmp StCrouchGo
+   lda.w G_MODE                          ; FUSION team assist: all four face
    and #$00FF.w                          ;   buttons (Y+B+X+A) call a partner
    cmp #2.w                              ;   strike -- team mode only, and it
    bne +                                 ;   rides the spark-pool projectile
    lda FP+F_JOYPR,x                      ;   slot like the fireballs
    and #(JOY_Y|JOY_B|JOY_X|JOY_A).w
    cmp #(JOY_Y|JOY_B|JOY_X|JOY_A).w
    bne +
    lda #0x0500.w                       ; assist strike: fast, 22 dmg
    sta scr0
    lda #(22 | (4<<8)).w                ; dmg 22 | SparkAnim 4 (flame)
    sta scr1
    lda #$A0.w                          ; guardable high or low (M|A)
    sta scr3
    stz.w RT_PROJAIR                    ; assist strike uses the char default
    jsr ProjSpawn
    jmp StateRet
+   lda FP+F_JOY,x                        ; Fusion MAX burst from neutral
    and #(JOY_Y|JOY_B|JOY_X|JOY_R).w
    cmp #(JOY_Y|JOY_B|JOY_X).w           ; Y+B+X without R activates MAX
    bne +
    lda FP+F_JOYPR,x
    and #(JOY_Y|JOY_B|JOY_X).w           ; one activation per press
    beq +
    lda FP+F_POWER,x
    cmp #1000.w
    bcc +
    lda #96
    jmp SetState16
+   lda FP+F_JOY,x                        ; FUSION charge: holding R+Y+B+X in
    and #(JOY_R|JOY_Y|JOY_B|JOY_X).w      ;   neutral keeps sid 97 alive across
    cmp #(JOY_R|JOY_Y|JOY_B|JOY_X).w      ;   anim loops (no edge needed)
    bne +
    lda #97
    jmp SetState16
+   jsr CmdTry
    ldx fofs                              ;   one-button fallback
    lda FP+F_JOYPR,x
    and #(JOY_B|JOY_Y|JOY_A|JOY_X).w
    beq +
    jmp StTryAttack
+
    lda FP+F_JOY,x
    and #(JOY_UP).w
    beq +
    jmp StJumpGo
+
    lda FP+F_JOY,x
    and #(JOY_RT|JOY_LF).w
    beq +
    jmp StGuardOrMove                     ; back vs threat -> guard pose
+
    stz FP+F_VX,x
    jmp StateRet

StWalk:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_JOY,x
    and #(JOY_DN).w
    beq +
    jmp StCrouchGo
+   jsr CmdTry
    ldx fofs
    lda FP+F_JOYPR,x
    and #(JOY_B|JOY_Y|JOY_A|JOY_X).w
    beq +
    jmp StTryAttack
+
    lda FP+F_JOY,x
    and #(JOY_UP).w
    beq +
    jmp StJumpGo
+
    lda FP+F_JOY,x
    and #(JOY_RT|JOY_LF).w
    beq +
    jmp StGuardOrMove                     ; back vs threat -> guard pose
+
    stz FP+F_VX,x
    sep #$20
    .ACCU 8
    lda #S_STAND
    jmp SetState

StGuardOrMove:                          ; dpad held: blocking stance only
    .ACCU 16                            ; reached via jmp with A already 16-bit
    jsr HoldsBack                         ; when walking *back* into an
    beq SM_walk                           ; incoming attack; else walk
    jsr EnemyAttacking
    beq SM_walk
    lda #S_GUARD
    jmp SetState16
SM_walk:
    .ACCU 16
    ldx fofs
    lda FP+F_JOY,x
    and #(JOY_RT|JOY_LF).w
    jmp StMove

StMove:
    ; A = held dpad mask; x = fofs; decide fwd/back by facing
    rep #$20
    .ACCU 16
    and #(JOY_RT).w
    bne +
        jmp SM_left
    + 
    lda FP+F_FACING,x
    bmi +
    lda #WALKSPD.w
    sta FP+F_VX,x
    lda #S_WALKF
    jmp StSetMove
+   lda #WALKSPD.w
    sta FP+F_VX,x
    lda #S_WALKB
    jmp StSetMove
SM_left:
    lda FP+F_FACING,x
    bmi +
    lda #-WALKSPD.w
    sta FP+F_VX,x
    lda #S_WALKB
    jmp StSetMove
+   lda #-WALKSPD.w
    sta FP+F_VX,x
    lda #S_WALKF
    jmp StSetMove

StSetMove:                              ; A(16) target sid, x = fofs.  Walk is
    cmp FP+F_STATE,x                    ;   re-requested every held tick: skip
    bne +                             ;   EnterState when already walking the
    jmp StateRet                      ;   same way, or the anim restarts every
+   jmp SetState16                    ;   tick (elem0 frozen, ftick never decs)

StTryAttack:                            ; A = pressed attack mask, standing
    ldy #CH_BUTTONS.w
    bra AtkScan
StTryCrouch:                            ; A = pressed attack mask, crouching
    ldy #CH_CBTN.w
    bra AtkScan
StTryAir:                               ; A = pressed attack mask, jumping
    ldy #CH_ABTN.w
AtkScan:
    ; A = pressed attack mask, Y = descriptor field of the button table
    rep #$20
    .ACCU 16
    sty scr4
    sta scr5
    ldy scr4
    ldx #boxp
    jsr CharPtr                           ; boxp -> character button table
    ldy #0
-   lda [boxp],y
    and scr5
    bne +
    iny
    iny
    iny
    iny
    cpy #16.w                             ; four mask,state pairs
    bcc -
    jmp StateRet
+   iny
    iny
    lda [boxp],y
    pha
    jsr ConsumePress                  ; the press is spent: don't let the
    rep #$20                          ;   matcher re-fire it on a later
    .ACCU 16                          ;   control tick (e.g. on landing)
    pla
    jmp SetState16

; Drop the button token of the ring entry pushed this tick so the matcher
; cannot re-fire it later.  Clobbers A,X and ct_off; returns with acc16.
ConsumePress:
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_HIST,x
    dec a
    and #$0F
    sta ct_off
    asl a
    clc
    adc ct_off
    clc
    adc fofs
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l CMDHIST_L+2,x                 ; only the press pushed THIS tick
    cmp framecnt
    bne +
    lda #0
    sta.l CMDHIST_L+1,x                 ; drop this frame's button token
+   rep #$20
    .ACCU 16
    rts

; CancelGate lives in the CancelData window (engine/cancel_gate.asm), which
; shares this CPU bank, so the hit path reaches it with a near JSR.

; ChainTry: normal-attack chain/cancel table.  Rows are 7 bytes:
;   .db from_sid, to_sid, held_dirs, t_norm, t_hit
;   .dw pad_mask
; A row fires while F_STATE == from_sid when pad_mask was just pressed,
; held_dirs are held, and the state frame reached t_norm -- or F_HITDONE
; (movecontact) is set and the frame reached t_hit.  $FF ends the table.
ChainTry:
    rep #$20
    .ACCU 16
    ldy #CH_CHAINTAB.w
    ldx #boxp
    jsr CharPtr                       ; boxp -> ChainTab
    stz ct_row
CN_row:
    rep #$20
    .ACCU 16
    lda ct_row
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y                      ; from sid; $FF ends the table
    cmp #$FF
    bne +
    rep #$20
    .ACCU 16
    rts
+   ldx fofs
    cmp FP+F_STATE,x
    bne CN_next
    iny
    lda [boxp],y                      ; to sid
    sta ct_tmp
    iny
    lda [boxp],y                      ; required held dirs
    sta ct_win
    iny
    lda [boxp],y                      ; t_norm
    sta ct_ei
    iny
    lda [boxp],y                      ; t_hit
    sta ct_ts0
    lda ct_win
    beq ++
    jsr JoyRelDir                     ; held dirs vs current (acc8 in/out)
    and ct_win
    cmp ct_win
    bne CN_next
++  rep #$20                          ; just-pressed pad mask (.dw field)
    .ACCU 16
    lda ct_row
    clc
    adc #5
    tay
    lda [boxp],y
    ldx fofs
    and FP+F_JOYPR,x
    beq CN_next
    sep #$20                          ; clock test: frame >= t_norm, or a
    .ACCU 8                           ;   contact and frame >= t_hit
    ldx fofs
    lda ct_ei
    cmp #$FF
    beq +
    cmp FP+F_FRAME,x
    beq CN_go
    bcc CN_go
+   lda FP+F_HITDONE,x
    beq CN_next
    lda ct_ts0
    cmp #$FF
    beq CN_next
    cmp FP+F_FRAME,x
    beq CN_go
    bcc CN_go
    bra CN_next
CN_go:
    jsr ConsumePress
    rep #$20
    .ACCU 16
    lda ct_tmp
    and #$00FF.w
    jmp SetState16
CN_next:
    rep #$20
    .ACCU 16
    lda ct_row
    clc
    adc #7
    sta ct_row
    jmp CN_row

StJumpGo:                               ; takeoff squat; takeoff velocity is
    rep #$20                            ; applied when anim 40 ends
    .ACCU 16
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_RUNF.w
    beq JG_run
    jsr DetectHighJump                  ; D -> U/UF/UB within five ticks
    bra JG_enter
JG_run:
    lda #2                              ; running forward forces a long jump
JG_enter:
    pha                                 ; EnterState clears the slide word
    lda #S_JSTART
    jsr EnterState
    pla
    sep #$20
    .ACCU 8
    ldx fofs
    sta FP+F_SLIDE+1,x                  ; 0 normal/hop, 1 high, 2 run high
    rep #$20
    .ACCU 16
    jsr JumpDirSample                   ; preserve a tapped diagonal at takeoff
    jmp StateRet

; The newest ring entry is the fresh U/UF/UB edge.  Look behind it for
; D/DF/DB, allowing brief neutral/horizontal transitions after releasing D.
; A held D can be arbitrarily old: the five-tick window starts at its release,
; not its initial press.  Tick subtraction works across the low-byte wrap.
DetectHighJump:
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_JOYPR+1,x
    and #$08                            ; require a new UP press
    beq DH_no
    lda FP+F_HIST,x
    sec
    sbc #2                              ; previous entry, before current U
    and #$0F
    sta ct_off
    lda #3
    sta ct_win
DH_scan:
    lda ct_off
    asl a
    clc
    adc ct_off
    clc
    adc fofs
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l CMDHIST_L,x
    and #$0F                            ; strip fresh/spent markers
    bit #$01                            ; another UP breaks the sequence
    bne DH_no
    bit #$02
    bne DH_yes
    lda framecnt                        ; first entry without D is its release
    sec
    sbc.l CMDHIST_L+2,x
    cmp #6                              ; longjump command window = 5 ticks
    bcs DH_no
    dec ct_off
    lda ct_off
    and #$0F
    sta ct_off
    dec ct_win
    bne DH_scan
DH_no:
    rep #$20
    .ACCU 16
    lda #0
    rts
DH_yes:
    rep #$20
    .ACCU 16
    lda #1
    rts

StCrouchGo:                             ; stand->crouch transition (anim 10)
    rep #$20
    .ACCU 16
    lda #S_CDOWN
    jmp SetState16

StCrouch:                               ; crouching (anim 11 loops)
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jsr CmdTry
    ldx fofs
    lda FP+F_JOYPR,x
    and #(JOY_B|JOY_Y|JOY_A|JOY_X).w
    beq +
    jmp StTryCrouch
+   lda FP+F_JOY,x
    and #(JOY_UP).w
    beq +
    jmp StJumpGo
+   lda FP+F_JOY,x
    and #(JOY_DN).w
    beq SC_rise
    jsr HoldsBack                         ; back+down under threat: guard low
    beq +
    jsr EnemyAttacking
    beq +
    lda #S_CGUARD
    jmp SetState16
+   jmp StateRet
SC_rise:
    lda #S_CUP                            ; released down -> rise to stand
    jmp SetState16

StCDown:                                ; still dropping; low hits allowed
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jsr CmdTry                          ; specials keep priority over the
    ldx fofs                            ;   crouch normal during the duck
    lda FP+F_JOYPR,x
    and #(JOY_B|JOY_Y|JOY_A|JOY_X).w
    beq +
    jmp StTryCrouch
+   lda FP+F_JOY,x
    and #(JOY_UP).w
    beq +
    jmp StJumpGo
+   lda FP+F_JOY,x
    and #(JOY_DN).w
    bne +
    lda #S_CUP                            ; let go early -> stand back up
    jmp SetState16
+   jmp StateRet                          ; anim end -> S_CROUCH (AnimTick)

StCUp:                                  ; rising; anim end -> S_STAND
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jsr CmdTry                          ; a command pressed while standing up
    ldx fofs                            ;   must not be swallowed by the
    lda FP+F_JOY,x                      ;   rise animation
    and #(JOY_UP).w
    beq +
    jmp StJumpGo
+   lda FP+F_JOY,x
    and #(JOY_DN).w
    beq +
    lda #S_CDOWN                          ; pressed down again -> duck
    jmp SetState16
+   jmp StateRet

StJStart:                               ; takeoff squat; samples jump dir in
    rep #$20                            ; F_SLIDE (-1 back, 0 neutral, +1 fwd)
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jsr JumpDirSample
    jmp StateRet                          ; anim end -> JumpTakeoff

; Update the direction while a horizontal input is held.  Releasing a tapped
; diagonal during the takeoff animation keeps its launch direction.
JumpDirSample:
    ldx fofs
    lda FP+F_JOY,x
    and #(JOY_RT|JOY_LF).w
    beq JS_none
    and #(JOY_RT).w
    beq JS_left
    lda FP+F_FACING,x                     ; right held: fwd if facing right
    bmi JS_back
    bra JS_fwd
JS_left:
    lda FP+F_FACING,x                     ; left held: fwd if facing left
    bmi JS_fwd
JS_back:
    sep #$20
    .ACCU 8
    lda #$FF.b
    bra JS_store
JS_fwd:
    sep #$20
    .ACCU 8
    lda #$01.b
    bra JS_store
JS_none:
    sep #$20
    .ACCU 8
    lda FP+F_SLIDE+1,x
    cmp #2
    bne JS_done
    lda FP+F_SLIDE,x
    bne JS_done
    lda #1                              ; dash jump keeps forward momentum
    bra JS_store
JS_store:
    sta FP+F_SLIDE,x
JS_done:
    rep #$20
    .ACCU 16
    rts

; Jump takeoff: S_JSTART anim ended. F_SLIDE holds the direction sampled while
; squatting, so the last direction held wins (MUGEN state 40 behaviour).
; Its high byte remembers D,U or a forward dash across the state change.
; Velocities are facing-relative: positive fwd moves toward the opponent.
JumpTakeoff:
    rep #$20
    .ACCU 16
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_SLIDE+1,x
    beq JT_normal
    lda FP+F_JOY+1,x
    and #$08                            ; released UP during startup: hyper
    beq JT_hyper
    lda FP+F_TFLAGS,x                    ; held: true high jump
    and #$EF.b
    sta FP+F_TFLAGS,x
    rep #$20
    .ACCU 16
    lda #HIGHJUMPVY.w
    bra JT_vy
JT_hyper:
    sep #$20
    .ACCU 8
    lda FP+F_TFLAGS,x
    ora #$10.b                           ; bit4 = hop/hyper-hop: no air guard
    sta FP+F_TFLAGS,x
    rep #$20
    .ACCU 16
    lda #HYPERHOPVY.w
    bra JT_vy
JT_normal:
    ; All takeoff branches arrive with byte A.  The preceding velocity
    ; path leaves the assembler in word mode; AND #$08 must stay a byte
    ; or its trailing $00 executes as BRK on an ordinary jump.
    sep #$20
    .ACCU 8
    lda FP+F_JOY+1,x
    and #$08                            ; released UP during startup: low hop
    beq JT_hop
    lda FP+F_TFLAGS,x
    and #$EF.b
    sta FP+F_TFLAGS,x
    rep #$20
    .ACCU 16
    lda #JUMPVY.w
    bra JT_vy
JT_hop:
    sep #$20
    .ACCU 8
    lda FP+F_TFLAGS,x
    ora #$10.b
    sta FP+F_TFLAGS,x
    rep #$20
    .ACCU 16
    lda #HOPVY.w
JT_vy:
    sta FP+F_VY,x
    lda #$0100.w                          ; leave the ground on this tick
    sta FP+F_Y,x
    sep #$20
    .ACCU 8
    lda FP+F_SLIDE,x
    beq JT_neutral
    bmi JT_back
    rep #$20
    .ACCU 16
    lda FP+F_SLIDE+1,x
    and #$00FF.w
    tay
    lda #JUMPVXF.w
    cpy #0
    beq JT_dir
    lda #HIGHJUMPVXF.w
    cpy #2
    bne JT_dir
    lda #RUNSPD.w
    bra JT_dir
JT_back:
    rep #$20
    .ACCU 16
    lda FP+F_SLIDE+1,x
    and #$00FF.w
    tay
    lda #JUMPVXB.w
    cpy #0
    beq JT_dir
    lda #HIGHJUMPVXB.w
JT_dir:                                   ; vx = magnitude * slide * facing:
    sta scr0                              ; back jumps negate when facing +
    sep #$20
    .ACCU 8
    lda FP+F_SLIDE,x                      ; $01 fwd / $FF back (signed byte)
    eor FP+F_FACING,x                     ; low bytes hold the facing sign
    rep #$20
    .ACCU 16
    bmi +
    lda scr0
    bra ++
+   lda scr0
    eor #$FFFF.w
    inc a
++  sta FP+F_VX,x
    sep #$20
    .ACCU 8
    lda FP+F_SLIDE,x
    bmi +
    lda #S_JUMPF.b
    bra JT_go
+   lda #S_JUMPB.b
    bra JT_go
JT_neutral:
    rep #$20
    .ACCU 16
    stz FP+F_VX,x
    sep #$20
    .ACCU 8
    lda #S_JUMP.b
JT_go:
    rep #$20
    .ACCU 16
    and #$00FF.w
    jmp EnterState

; A(16) = jump-pose state matching current horizontal momentum
; (neutral, forward or backward air anim).
PickJumpState:
    ldx fofs
    lda FP+F_VX,x
    beq PJ_neutral
    eor FP+F_FACING,x                     ; same sign = moving toward facing
    bmi PJ_back
    lda #S_JUMPF.w
    rts
PJ_back:
    lda #S_JUMPB.w
    rts
PJ_neutral:
    lda #S_JUMP.w
    rts

StJump:                                 ; S_JUMP / S_JUMPF / S_JUMPB
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne SJ_air
    lda FP+F_VY,x                         ; just-launched jumps still show y=0
    bmi SJ_air                            ; for one tick; do not land them
    stz FP+F_VX,x                         ; touched ground: land recovery
    stz FP+F_VY,x
    sep #$20
    .ACCU 8
    lda #SFX_LAND.b
    jsr SfxPlay
    rep #$20
    .ACCU 16
    lda #S_LAND
    jmp SetState16
SJ_air:
    ldx fofs
    lda FP+F_JOYPR,x
    and #(JOY_B|JOY_Y).w                  ; FUSION air throw before air normals
    beq +
    jsr AirThrowTry
    bcc +
    jmp StateRet
+   jsr CmdTry                            ; air commands (posture-A rows)
    ldx fofs
    lda FP+F_JOYPR,x
    and #(JOY_B|JOY_Y|JOY_A|JOY_X).w
    beq +
    jmp StTryAir
+   jmp StateRet

StAirAtk:                               ; air attack keeps jump momentum;
    rep #$20                            ; anim end -> jump pose (AnimTick)
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne +
    stz FP+F_VX,x                         ; landed mid-attack
    stz FP+F_VY,x
    sep #$20
    .ACCU 8
    lda #SFX_LAND.b
    jsr SfxPlay
    rep #$20
    .ACCU 16
    lda #S_LAND
    jmp SetState16
+   jsr TryQuickMax                       ; FUSION: air Quick MAX on contact
    bcc +
    jmp StateRet
+   jsr CancelGate                      ; connected air strong: on contact
    beq +                               ;   special/super cancel
    jsr CmdTryCancel
+   jsr ChainTry                          ; air chains (re-fire, x->y/b on hit)
    jmp StateRet

StLand:                                 ; grounded recovery, no control
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    stz FP+F_VY,x
    jmp StateRet                          ; anim end -> S_STAND

StGetUp:                                ; rising from knockdown
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    stz FP+F_VY,x
    jmp StateRet                          ; anim end -> S_STAND

StAttack:
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jsr TryQuickMax                     ; FUSION: Y+B+X on contact
    bcc +
    jmp StateRet
+   lda FP+F_HP                          ; no cancel scan on the KO contact:
    beq SA_koho                          ;   the round is already decided
    lda FP+F_HP+FP2OFS
    beq SA_koho
    jsr CancelGate                       ; first contact -> special/super
    beq +                                ;   (hit-confirm cancel)
    jsr CmdTryCancel                     ;   cancel (gate checks F_HITDONE)
+   jsr ChainTry                         ; then normal chains (whiff ok)
    jmp StateRet
SA_koho:
    jmp StateRet

StCrouchAtk:                            ; low hits; anim end -> S_CROUCH
    rep #$20
    .ACCU 16
    jsr PinVXUnlessVelSet                ; VelSet-driven crouching attacks
    jsr TryQuickMax                     ;   (M.Bison's sweep) keep F_VX
    bcc +
    jmp StateRet
+   jsr CancelGate                      ; connected crouching strong:
    beq +                               ;   cancel on first contact
    jsr CmdTryCancel                    ;   (including the 440 sweep)
+   jsr ChainTry
    jmp StateRet

StRun:                                  ; run while forward is held (anim 100
    rep #$20                            ;   loops via AT_loop)
    .ACCU 16
    ldx fofs
    jsr CmdTry                          ; ctrl state: the buffered F,F plus a
    ldx fofs                            ;   fresh a/b press completes the knee
    lda FP+F_JOY,x
    and #(JOY_UP).w
    beq +
    jmp StJumpGo
+   ldx fofs
    jsr JoyRelDir                       ; returns with acc8
    .ACCU 8                             ; assemble-time mode must match the
    and #$04                            ;   routine's exit state or -> BRK
    rep #$20                            ; still holding forward?
    .ACCU 16
    bne +
    rep #$20
    .ACCU 16
    lda #S_STAND
    jmp SetState16
+   rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_FACING,x
    bmi +
    lda #RUNSPD.w
    sta FP+F_VX,x
    jmp StateRet
+   lda #-RUNSPD.w
    sta FP+F_VX,x
    jmp StateRet

StBackD:                                ; hop back; lands -> stand
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne ++                              ; already hopping
    lda FP+F_VY,x                       ; on the floor: vy>0 means the hop
    beq +                               ;   just landed (Physics clamps y)
    bpl BD_land                         ;   -> exit instead of sitting out
+   lda FP+F_FRAME,x                    ;   the anim's remaining tail frames
    bne ++                              ; vy applied once, on the first frame
    lda #DASHVY.w
    sta FP+F_VY,x
++  lda FP+F_FACING,x
    bmi +
    lda #-DASHSPD.w
    sta FP+F_VX,x
    jmp StateRet
+   lda #DASHSPD.w
    sta FP+F_VX,x
    jmp StateRet
BD_land:
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda #S_STAND
    jmp SetState16

StCharge:                               ; FUSION sid 97: Extra-mode manual
    rep #$20                            ;   charge -- R+Y+B+X held fills the
    .ACCU 16                            ;   meter ~5/tick; release or full
    ldx fofs                            ;   meter drops back to stand
    lda FP+F_JOY,x
    and #(JOY_R|JOY_Y|JOY_B|JOY_X).w
    cmp #(JOY_R|JOY_Y|JOY_B|JOY_X).w
    bne StChargeOut
    lda FP+F_POWER,x
    clc
    adc #5
    cmp #3000.w
    bcc +
    lda #3000.w
+   sta FP+F_POWER,x
    cmp #3000.w
    beq StChargeOut
    jmp StateRet
StChargeOut:
    lda #S_STAND
    jmp SetState16

StSpecial:                              ; taunt + scripted specials (47-55):
    rep #$20                            ;   displacement comes from the
    .ACCU 16                            ;   generated PosTab in AnimSetFrame,
                                        ;   or from ActTab op5 (FlagsTab b12)
    ldx fofs
    jsr TryQuickMax                     ; FUSION: cancel a connected special
    bcc +
    jmp StateRet
+   ldx fofs
    lda FP+F_STATE,x                    ; FUSION: Extra dodge counter-attack
    and #$00FF.w                        ;   -- pressing X (strong punch) while
    cmp #95.w                           ;   sid 95 is live cancels into the
    bne +                               ;   stand strong punch
    lda FP+F_JOYPR,x
    and #(JOY_X).w
    beq +
    lda #6
    jmp SetState16
+   ldx fofs
    lda FP+F_STATE,x                    ; Yuri's forward roll (sid 95) applies
    and #$00FF.w                        ;   timed velocity through ActTab.
    cmp #95.w                           ; Preserve it until its time=23 stop.
    beq +
    jsr PinVXUnlessVelSet                ; VelSet-driven specials (ActTab op5)
    jmp StateRet                        ;   own their F_VX too: Physics
+   jmp StateRet                        ;   integrates it (FlagsTab bit12).

StHit:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne SH_tmr
    lda FP+F_VY,x
    beq SH_tmr
    bmi SH_tmr                            ; rising launch handled by Physics
    ; touched the ground while falling in hitstun: goes down
    ; (StDown plays the landing thud and switches to the lie pose)
    stz FP+F_VY,x
    lda FP+F_JOY,x                        ; KOF98 ukemi: A+B held at
    and #(JOY_A|JOY_B).w                  ;   touchdown -> recovery roll
    cmp #(JOY_A|JOY_B).w
    bne +
    jmp RollRecover
+   lda #S_DOWN
    jsr EnterState
    ldx fofs
    lda #LIEDOWN.w
    sta FP+F_HTIMER,x
    jmp StateRet
SH_tmr:
    lda FP+F_HTIMER,x
    beq +
    dec a
    sta FP+F_HTIMER,x
    bne SH_move
    lda FP+F_Y,x
    bne ++                                ; recovered mid-air: jump pose
    lda #S_STAND
    jmp SetState16
++  jsr PickJumpState
    jmp SetState16
+   ; still in hitstun: move this tick, then expire the slide window.  The
+   ; zero must come after Physics, otherwise the last counted slide tick
+   ; was killed before it could move the victim.
SH_move:
    jsr Physics
    ldx fofs
    lda FP+F_SLIDE,x
    beq SH_anim
    dec a
    sta FP+F_SLIDE,x
    bne SH_anim
    stz FP+F_VX,x
SH_anim:
    jsr TransAir
    jsr AnimTick
    jmp ClampX

StDown:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne SD_air                            ; falling through the air
    lda FP+F_VY,x
    bmi SD_air                            ; launch queued: Physics lifts off
    lda #30.w                             ; floor contact: reset juggle budget
    sta FUS_JUGGLE,x
    ; on the floor: bleed the slide off with friction instead of
    ; stopping dead (the "recuo" carries across the ground)
    lda FP+F_VX,x
    beq SD_vx0
    bpl +
    clc
    adc #DOWNFRI.w
    bmi ++
    bra SD_vx0
+   sec
    sbc #DOWNFRI.w
    bmi SD_vx0                            ; crossed zero: stop sliding
    bra ++
SD_vx0:
    ++  sta FP+F_VX,x
    stz FP+F_VY,x
    ldy #CH_ANIMTAB
    ldx #lptr
    jsr CharPtr                           ; lptr -> victim AnimTab
    ldy #ANIM_LIE*2
    lda [lptr],y
    ldx fofs
    cmp FP+F_ANIM,x
    beq SD_lying                          ; already in the lie-down pose
    lda FP+F_JOY,x                        ; first floor contact: A+B held
    and #(JOY_A|JOY_B).w                  ;   -> recovery roll instead of
    cmp #(JOY_A|JOY_B).w                  ;   the knockdown lie
    bne +
    jmp RollRecover
+   sep #$20
    .ACCU 8
    lda #SFX_LAND.b
    jsr SfxPlay                           ; thud as the body hits the floor
    rep #$20
    .ACCU 16
    lda #ANIM_LIE
    jsr SetAnimSlot                       ; hit the floor: lying sprite
    ldx fofs
SD_lying:
    lda FP+F_HP,x
    beq SD_stay                           ; KO'd fighters stay down
    lda FP+F_HTIMER,x
    beq +
    dec a
    sta FP+F_HTIMER,x
    bne SD_stay
+   lda #S_GETUP                          ; liedown timer done -> get up
    jmp SetState16
SD_air:
SD_stay:
    jmp StateRet

StWin:
    jmp StateRet

GCancelTry:                             ; FUSION guard cancels: Y+B edge
    rep #$20                            ;   -> guard-roll (back 94 / fwd 95),
    .ACCU 16                            ;   X+A edge -> guard-blowback (67);
    ldx fofs                            ;   both spend one full stock.
    lda FP+F_JOYPR,x                    ;   Returns via EnterState+StateRet
    and #(JOY_Y|JOY_B).w                ;   when it fires.
    cmp #(JOY_Y|JOY_B).w
    bne +
    jsr HoldsBack                       ; holding back -> back roll
    beq GC_fwd
    lda #94
    bra GCancelGo
GC_fwd:
    lda #95                             ; neutral/forward -> forward roll
    bra GCancelGo
+   lda FP+F_JOYPR,x
    and #(JOY_X|JOY_A).w
    cmp #(JOY_X|JOY_A).w
    bne +
    lda #67
    bra GCancelGo
+   rts                                 ; nothing held: caller continues
GCancelGo:
    pha                                 ; target sid survives EnterState
    ldx fofs
    lda FP+F_POWER,x
    cmp #1000.w
    bcc GC_fail
    sec
    sbc #1000.w
    sta FP+F_POWER,x
    pla
    pha
    jsr EnterState                      ; guard cancel consumes one stock
    pla                                 ; A = target sid
    cmp #94.w
    bcc GC_done                         ; 67: blowback
    cmp #96.w
    bcs GC_done
    ldx fofs
    lda #14.b                           ; GC roll: no vulnerable startup
    sta FP+F_INVUL,x
    lda #4.b
    sta FP+F_PFX,x
    bra GC_done
GC_done:
    pla                               ; drop GCancelTry's return address --
    jmp StateRet                      ;   the state changed under the caller
GC_fail:
    pla                               ; broke: treat as no cancel
    rts

StGuard:                                ; stand guard hold (anim 130 loops)
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jsr GCancelTry
    jsr HoldsBack
    beq SG_out
    ldx fofs
    lda FP+F_JOY,x
    and #(JOY_DN).w
    beq +
    lda #S_CGUARD                         ; back+down -> crouch guard
    jmp SetState16
+   jmp StateRet
SG_out:
    lda #S_STAND                          ; released back -> stand
    jmp SetState16

StCGuard:                               ; crouch guard hold (anim 131)
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jsr GCancelTry
    jsr HoldsBack
    beq CG_out
    ldx fofs
    lda FP+F_JOY,x
    and #(JOY_DN).w
    bne +
    lda #S_GUARD                          ; released down -> stand guard
    jmp SetState16
+   jmp StateRet
CG_out:
    ldx fofs
    lda FP+F_JOY,x                        ; released back: stay crouched if
    and #(JOY_DN).w                       ; down is still held
    beq +
    lda #S_CROUCH
    jmp SetState16
+   lda #S_STAND
    jmp SetState16

StGHit:                                 ; guard-hit: constant pushback for
    rep #$20                            ; the slide window, stun via htimer
    .ACCU 16
    ldx fofs
    jsr GCancelTry                      ; FUSION: GC works in blockstun too
    ldx fofs
    lda FP+F_SLIDE,x
    beq GH_timer
    dec a
    sta FP+F_SLIDE,x
    bne GH_timer
    stz FP+F_VX,x
GH_timer:
    lda FP+F_HTIMER,x
    beq GH_rec                            ; zero stun: recover immediately
    dec a
    sta FP+F_HTIMER,x
    bne GH_stay
GH_rec:                                   ; guardstun over: back into the
    lda FP+F_Y,x                          ; matching stance
    bne GH_air
    jsr HoldsBack
    beq GH_idle
    ldx fofs
    lda FP+F_JOY,x
    and #(JOY_DN).w
    beq GH_stg
    lda #S_CGUARD
    jmp SetState16
GH_stg:
    lda #S_GUARD
    jmp SetState16
GH_idle:
    ldx fofs
    lda FP+F_JOY,x
    and #(JOY_DN).w
    beq GH_std
    lda #S_CROUCH
    jmp SetState16
GH_std:
    lda #S_STAND
    jmp SetState16
GH_air:
    jsr PickJumpState
    jmp SetState16
GH_stay:
    jmp StateRet

StAGuard:                               ; 29: air guard / air guard-hit
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne AG_air
    stz FP+F_VX,x                        ; touched ground while guarding
    stz FP+F_VY,x
    lda #S_LAND.w
    jmp SetState16
AG_air:
    lda FP+F_HTIMER,x
    beq AG_rec
    dec a
    sta FP+F_HTIMER,x
    jsr Physics
    jsr AnimTick
    jmp ClampX
AG_rec:
    jsr PickJumpState
    jmp SetState16

; FUSION dizzy/stun: accumulate on hits, mash to recover faster.  The pose
; uses AnimTab slot 107 (mugen 5300) that every generated fighter carries.
DizzyBump:                              ; X = victim offset
    rep #$20
    .ACCU 16
    lda FP+F_HP,x
    beq DB_done
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_DIZZY.w
    beq DB_done
    sep #$20
    .ACCU 8
    stz FUS_DIZZYT,x                      ; a hit ends the previous stun
    lda FUS_DIZZY,x
    clc
    adc #2.b
    cmp #24.b
    bcc +
    lda #24.b
+   sta FUS_DIZZY,x
DB_done:
    rep #$20
    .ACCU 16
DB_done8:
    rts

; Called from TickFighter while the fighter is in a neutral ground state.
; Turns a full dizzy accumulator into the 107 stun state without cutting the
; current hitstun short.
CoverAttackTry:
    rep #$20
    .ACCU 16
    ldx fofs
    sep #$20
    .ACCU 8
    lda FUS_COVER,x
    beq +
    dec a
    sta FUS_COVER,x
    rep #$20
    .ACCU 16
    rts
+   lda.w G_MODE
    cmp #2.b
    bcc CC_no
    cmp #4.b
    bcs CC_no
    lda FUS_SYN,x
    beq CC_no
    cmp #1.b
    bne CC_go
    lda rng
    inc rng
    and #1.b
    bne CC_no
CC_go:
    rep #$20
    .ACCU 16
    lda #$0500.w
    sta scr0
    lda #(22 | (4<<8)).w
    sta scr1
    lda #$00A0.w
    sta scr3
    stz.w RT_PROJAIR                    ; team assist uses the char default
    jsr ProjSpawn
    sep #$20
    .ACCU 8
    ldx fofs
    lda #180.b
    sta FUS_COVER,x
CC_no:
    rep #$20
    .ACCU 16
    rts

StDizzy:                                ; 107: dizzy/stun hold
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_HP,x
    beq SDZ_ko
    jsr CoverAttackTry
    sep #$20
    .ACCU 8
    lda FUS_DIZZYT,x
    beq SDZ_out
    dec a
    sta FUS_DIZZYT,x
    lda FP+F_JOYPR,x
    beq +
    dec FUS_DIZZYT,x                    ; mashing shortens the stun
+   rep #$20
    .ACCU 16
    jsr AnimTick
    jmp StateRet
SDZ_ko:
    ldx fofs
    stz FP+F_VX,x
    stz FP+F_VY,x
    lda #S_DOWN.w
    jmp SetState16
SDZ_out:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne +
    lda #S_STAND.w
    jmp SetState16
+   jsr PickJumpState
    jmp SetState16

; FUSION generic air throw: strong button while airborne and close to an
; airborne opponent slams them to the floor.  Character-specific source air
; throws still use their own animations; this gives every fighter the system
; mechanic with the shared air strong-punch pose.
; --- Kung Fu Blocking (mugen 1300-1351) -----------------------------------
; The parry stances sit still while their RevTab window is armed -- HitOne
; redirects a matching hit into the blocked poses.  The blocked poses open
; with a global Pause (ActTab op6), then holdback exits to guard.

StBlock:                                ; 78/80: stand/crouch parry stance
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_VX,x
    jmp StateRet                          ; anim end -> stand via AnimTick

StBlocked:                              ; 79/81: frozen block pose; after
    rep #$20                            ;   the pause drains, holdback goes
    .ACCU 16                            ;   straight to the matching guard
    ldx fofs
    stz FP+F_VX,x
    jsr HoldsBack
    beq +
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_BHITC.w
    lda #S_GUARD.w                        ; 79 -> stand guard
    bcc ++
    lda #S_CGUARD.w                       ; 81 -> crouch guard
++  jmp SetState16
+   jmp StateRet

StBlockAir:                             ; 82/83: air parry keeps falling;
    rep #$20                            ;   TransAir lands it in 1351
    .ACCU 16
    jsr Physics
    jsr TransAir
    jsr AnimTick
    jmp ClampX

StBLand:                                ; 84 (1351): touch-down after the
    rep #$20                            ;   air parry; mugen restores ctrl
    .ACCU 16                            ;   at tick 3, so commands (another
    ldx fofs                            ;   `blocking`) work right away
    stz FP+F_VX,x
    stz FP+F_VY,x
    jsr CmdTry
    jmp StateRet                          ; anim 47 is 3 ticks -> stand

StSuper:                                ; 87-89 Triple Kung Fu Palm slices:
    jmp StateRet                          ;   Physics carries the velset
                                          ;   dash; AnimTick chains the
                                          ;   slices through TransEnd

HoldsBack:                              ; fofs fighter -> A(16) nonzero when
    rep #$20                            ; the pad holds "back" (away from
    .ACCU 16                            ; the facing direction)
    ldx fofs
    lda FP+F_FACING,x
    bmi +
    lda FP+F_JOY,x
    and #JOY_LF.w
    rts
+   lda FP+F_JOY,x
    and #JOY_RT.w
    rts

EnemyAttacking:                         ; fofs fighter -> A(16) nonzero when
    rep #$20                            ; the *other* fighter is in an
    .ACCU 16                            ; attack state (5-8, 19-26)
    ldx fofs
    bne +
    ldx #FP2OFS
    bra ++
+   ldx #0
++  lda FP+F_STATE,x
    and #$00FF.w
    sec
    sbc #S_PUNCH.w
    cmp #4
    bcc EA_yes
    lda FP+F_STATE,x
    and #$00FF.w
    sec
    sbc #S_CPUNCH.w
    cmp #8
    bcs EA_no
EA_yes:
    lda #1
    rts
EA_no:
    lda #0
    rts

; A(16) = state, x ignored (uses fofs)
SetState16:
    rep #$20
    .ACCU 16
    jsr EnterState
    jmp StateRet
SetState:                               ; A(8) variant
    rep #$20
    .ACCU 16
    and #$00FF.w
    jsr EnterState
    jmp StateRet

Physics:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_Y,x
    bne PH_air
    lda FP+F_VY,x
    bmi PH_air                            ; launch: upward vel lifts off ground
    bra PH_x                              ; grounded, no vertical motion
PH_air:
    lda FP+F_VY,x
    clc
    adc #GRAV.w
    sta FP+F_VY,x                         ; vy += yaccel (screen-space: + = down)
    lda FP+F_Y,x
    sec
    sbc FP+F_VY,x                         ; F_Y is height: subtract screen vel
    bpl +
    lda #0                              ; clamp at the floor; overshooting to
+   sta FP+F_Y,x                        ;   $FFFF would keep us airborne forever
PH_x:
    ldx fofs
    lda FP+F_VX,x
    jmp AddXClamped

AnimTick:
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_TFLAGS,x                       ; bit1: state entered this tick.
    and #$02.b                            ;   The entry already ran AnimSetFrame
    beq +                                 ;   for elem0; skipping the decrement
    lda FP+F_TFLAGS,x                     ;   keeps elem0 on screen for its full
    and #$FD.b                            ;   duration instead of losing a tick
    sta FP+F_TFLAGS,x                     ;   (the throw grab box lives there)
    rep #$20
    .ACCU 16
    rts
+   dec FP+F_FTICK,x
    beq +
    rep #$20
    .ACCU 16
    rts
+   inc FP+F_FRAME,x
    lda FP+F_FRAME,x
    cmp FP+F_NFR,x
    bcs +
    rep #$20
    .ACCU 16
    jmp AnimSetFrame
+   .ACCU 8                               ; the early-return rep #$20/.ACCU 16
    lda FP+F_STATE,x                      ; above is assemble-time only; the
    cmp #S_HIT                            ; dispatch path runs with M=1
    bne AT_nothit
    rep #$20
    .ACCU 16
    lda FP+F_HTIMER,x
    bne ++
    lda FP+F_Y,x
    bne +
    jmp AT_rec
+   jsr PickJumpState                     ; hitstun ended mid-air: fall again
    jsr EnterState
    rts
++  jmp AT_stay
AT_nothit:
    .ACCU 8                               ; runtime acc is still 8-bit here;
    cmp #97.b                            ; keep the charge pose cycling until
    beq AT_vloop                         ; release/full meter in StCharge
    cmp #S_VWALL
    bne +
    rep #$20
    .ACCU 16
    jmp VictimBounceEnter                 ; ChangeState 1027 -> 1028
+   sep #$20                              ; prior branch skips the 16-bit path
    .ACCU 8
    cmp #S_VBOUNCE
    beq AT_vloop
    cmp #S_VTHROW                         ; thrown flight: fall anim cycles
    beq AT_vloop
    cmp #S_VHELD                          ; bound pose holds its last frame
    beq AT_vstay
    bra +
AT_vloop:
    jmp AT_loop
AT_vstay:
    jmp AT_stay
+   lda FP+F_STATE,x
    cmp #S_DOWN                           ; the S_HIT block's .ACCU 16 above
    bne AT_nodown                         ; is assemble-time only
    rep #$20
    .ACCU 16
    lda FP+F_Y,x
    bne +
        sep #$20
        .ACCU 8
        jmp AT_stay                       ; on the floor: hold the lying pose
    +   sep #$20
        .ACCU 8
        jmp AT_loop                       ; airborne: keep cycling the fall anim
AT_nodown:
    .ACCU 8
    cmp #S_GUARD
    bne +
        jmp AT_loop                       ; the guard poses loop
    + 
    cmp #S_CGUARD
    bne +
        jmp AT_loop
    + 
    cmp #S_GHIT
    bne +
        jmp AT_stay                       ; guard-hit flinch holds its frame
    + 
    cmp #S_CDOWN
    bne +
        jmp AT_rec_crouch
    + 
    cmp #S_JSTART
    bne +
    rep #$20
    .ACCU 16
    jsr JumpTakeoff                       ; squat over: launch and pick air anim
    rts
    + 
    .ACCU 8
    sec
    sbc #S_CPUNCH.b
    cmp #4
    bcs +
        jmp AT_rec_crouch                 ; crouching hits recover to crouch
    + 
    lda FP+F_STATE,x
    sec
    sbc #S_APUNCH.b
    cmp #4
    bcs +
        jmp AT_rec_air                    ; air hits end back in the jump pose
    + 
    lda FP+F_STATE,x
    cmp #S_STAND
    bne +
        jmp AT_loop
    + 
    cmp #S_WALKF
    bne +
        jmp AT_loop
    + 
    cmp #S_WALKB
    bne +
        jmp AT_loop
    + 
    cmp #S_CROUCH
    bne +
        jmp AT_loop
    + 
    cmp #S_JUMP
    bne +
        jmp AT_loop
    + 
    cmp #S_JUMPF
    bne +
        jmp AT_loop
    + 
    cmp #S_JUMPB
    bne +
        jmp AT_loop
    + 
    cmp #S_WIN
    bne +
        jmp AT_loop
    +
    cmp #S_WPOSE
    bne +
        jmp AT_stay                       ; win pose: freeze on the last elem
    +
    cmp #S_LOSE
    bne +
        jmp AT_stay                       ; time-over: hold the lose pose
    +
    cmp #S_RUNF
    bne +
        jmp AT_loop                       ; run anim cycles while F held
    +
    rep #$20
    .ACCU 16
    jsr TransEnd                          ; AnimTime=0 ChangeState rules
    cmp #$FFFF.w
    bne +
    jsr TransLive                         ; still waiting on a live rule?
    bne ++                                ;   yes: freeze the last frame
    lda #S_STAND
    jsr EnterState
    rts
+   jsr EnterState
    rts
++  sep #$20
    .ACCU 8
    jmp AT_stay
AT_rec:
    rep #$20
    .ACCU 16
    lda #S_STAND
    jsr EnterState
    rts
AT_rec_crouch:
    rep #$20
    .ACCU 16
    lda #S_CROUCH
    jsr EnterState
    rts
AT_rec_air:
    rep #$20
    .ACCU 16
    jsr PickJumpState
    jsr EnterState
    rts
AT_stay:
    dec FP+F_FRAME,x
    jmp AnimSetFrame
AT_loop:
    sep #$20
    .ACCU 8
    lda FP+F_LOOP,x
    sta FP+F_FRAME,x
    jmp AnimSetFrame

; ---------------------------------------------------------------------------
; Hit detection: active-frame AABB using aggregated AIR boxes
; ---------------------------------------------------------------------------
; GuardCheck: fofs = victim, scr5 = attacker move flags word.
; Returns A(16) = guard-hit AnimTab slot when the incoming hit is blocked
; (0 = not guarded). Posture is taken from the victim's position + held
; pad, so the same routine works for the guard states and for a fighter
; that is simply holding "back" as the hit lands.
GuardCheck:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_PUNCH.w                        ; 0-4: stand/walk/crouch/jump
    bcc GC_ok
    cmp #S_CDOWN.w
    beq GC_ok
    cmp #S_CUP.w
    beq GC_ok
    cmp #S_JUMPF.w
    beq GC_ok
    cmp #S_JUMPB.w
    beq GC_ok
    sec
    sbc #S_GUARD.w                        ; 27-30: the guard states
    cmp #4
    bcs GC_no
GC_ok:
    jsr HoldsBack
    beq GC_no
    ldx fofs
    lda FP+F_Y,x
    bne GC_air                            ; airborne: try KOF98 air guard
    lda FP+F_JOY,x
    and #JOY_DN.w
    beq GC_stand
    lda scr5                              ; crouch block stops M|L attacks
    and #$0060.w
    beq GC_no
    lda #ANIM_GHIT_CR.w
    rts
GC_stand:
    lda scr5                              ; stand block stops M|H attacks
    and #$0030.w
    beq GC_no
    lda #ANIM_GHIT_HI.w
    rts
GC_air:
    ; FUSION/arcade air guard: neutral and back full jumps can block
    ; specials, supers, projectiles and air normals.  Hops, forward jumps
    ; and grounded normals stay unguardable in the air.
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_JUMPF.w
    beq GC_no
    cmp #S_JUMP.w
    beq GC_air_ok
    cmp #S_JUMPB.w
    beq GC_air_ok
    cmp #S_AGUARD.w
    beq GC_air_ok
    bra GC_no
GC_air_ok:
    lda FP+F_TFLAGS,x
    and #$0010.w                          ; bit4 = hop/hyper-hop in progress
    bne GC_no
    lda scr5
    bit #$2000.w                          ; bit13 = ground normal
    bne GC_no
    and #$00F0.w                          ; must stop some posture
    beq GC_no
    lda #ANIM_AGUARD.w
    rts
GC_no:
    lda #0
    rts

; RevCheck: fofs = victim (parry stance).  Returns A(16) = blocked sid when
; the victim's RevTab row exists and the attacker's posture is inside the
; row's mask (ct_post bits S=1 C=2 A=4).  The stance is armed for its whole
; duration -- mugen's HitOverride redirects every incoming hit, not just
; the ReversalDef window.  0 = no reversal: the hit proceeds to
; guard/damage as usual.
RevCheck:
    rep #$20
    .ACCU 16
    ldy #CH_REVTAB.w
    ldx #boxp
    jsr CharPtr                           ; boxp -> victim RevTab
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    tay
    lda [boxp],y
    bne +
RC_no:
    rep #$20
    .ACCU 16
    lda #0
    rts
+   sta boxp
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_TBANK,x
    sta boxp+2
    ; attacker posture bit: airborne -> 4, crouch states -> 2, else 1
    ldx aofs
    lda FP+F_Y,x                          ; 16-bit y: either byte nonzero
    ora FP+F_Y+1,x                        ;   means airborne
    bne RC_air
    lda FP+F_STATE,x
    cmp #S_CROUCH.b
    beq RC_cr
    cmp #S_CDOWN.b
    beq RC_cr
    cmp #S_CUP.b
    beq RC_cr
    sec
    sbc #S_CPUNCH.b
    cmp #4
    bcc RC_cr
    lda #1
    bra RC_m
RC_cr:
    lda #2
    bra RC_m
RC_air:
    lda #4
RC_m:
    ldy #2
    and [boxp],y                          ; attacker posture allowed?
    beq RC_no
    ldy #3
    lda [boxp],y                          ; counter-grab victim sid ($FF = parry)
    sta.b rev_vsid
    ldy #1
    lda [boxp],y                          ; blocked sid
    cmp #$FF.b                            ; unmapped follow-up: do not jump
    beq RC_no                             ;   into a non-existent state
    sta.b rev_bsid
    rep #$20
    .ACCU 16
    and #$00FF.w
    rts

; A(16) = earned power, X = fighter offset. Does not touch hit-test scratch.
AddPower:
    ; FUSION advantage: later team members build meter faster (25%/50%).
    sta FUS_TMP
    lda.w G_MODE
    and #$00FF.w
    cmp #2.w
    bcc AP_noadv
    cmp #4.w
    bcs AP_noadv
    cpx #0
    bne +
    lda.w T_I1
    bra ++
+   lda.w T_I2
++  and #$00FF.w
    beq AP_noadv
    cmp #1.w
    beq AP_25
    lda FUS_TMP
    lsr a
    clc
    adc FUS_TMP
    sta FUS_TMP
    bra AP_noadv
AP_25:
    lda FUS_TMP
    lsr a
    lsr a
    clc
    adc FUS_TMP
    sta FUS_TMP
AP_noadv:
    lda FUS_TMP
    clc
    adc FP+F_POWER,x
    cmp #3000.w
    bcc +
    lda #3000.w
+   sta FP+F_POWER,x
    rts

HitCheck:
    ldx #0
    ldy #FP2OFS
    jsr HitOne
    ldx #FP2OFS
    ldy #0
    jsr HitOne
    rts

; ---------------------------------------------------------------------------
; FUSION hit modifiers: counter-hit flag, juggle budget and banner.
; Called after GuardCheck says "not guarded", before damage/velocity.
; Returns carry set when the juggle budget rejects the hit.
; ---------------------------------------------------------------------------
IsAttackState:                          ; X = fighter offset -> A=1 attack
    rep #$20
    .ACCU 16
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #5.w
    bcc IA_no
    cmp #9.w
    bcc IA_yes
    cmp #19.w
    bcc IA_no
    cmp #27.w
    bcc IA_yes
    cmp #48.w
    bcc IA_no
    cmp #67.w
    bcc IA_yes
    cmp #85.w
    bcc IA_no
    cmp #90.w
    bcc IA_yes
IA_no:
    lda #0
    rts
IA_yes:
    lda #1
    rts

; FUSION Quick MAX: Y+B+X on a connected normal/special cancels into the
; shared MAX burst (state 96).  State 96's PowTab entry pays one stock.
HitModifiers:
    rep #$20
    .ACCU 16
    stz FUS_CTR
    ; --- juggle budget (airborne victims only) ---------------------------
    ldx vofs
    lda FP+F_Y,x
    beq HM_counter
    lda scr5
    and #$C000.w                        ; bits14-15 = cost tier
    xba
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    and #$0003.w
    bne +
    lda #1                              ; any real hit costs at least 1
+   sta scr0
    ldx vofs
    lda FUS_JUGGLE,x
    cmp scr0
    bcc HM_whiff
    sec
    sbc scr0
    sta FUS_JUGGLE,x
HM_counter:
    ; --- counter hit: victim was in an attack state ----------------------
    ldx vofs
    jsr IsAttackState
    sta FUS_CTR
    beq HM_ok
    sep #$20
    .ACCU 8
    lda #30.b
    sta FUS_FLASH
    rep #$20
    .ACCU 16
    jsr CounterDraw
    sep #$20
    .ACCU 8
    ldx aofs
    lda #6.b
    sta FP+F_PFX,x
    ldx vofs
    lda #6.b
    sta FP+F_PFX,x
    rep #$20
    .ACCU 16
HM_ok:
    rep #$20
    .ACCU 16
    clc
    rts
HM_whiff:
    rep #$20
    .ACCU 16
    ldx aofs
    stz FP+F_HITDONE,x                  ; a rejected juggle is not contact
    sec
    rts

HitOne:                                 ; X=attacker, Y=victim
    stx fofs
    stx aofs
    sty vofs
    sep #$20
    .ACCU 8
    lda FP+F_STATE,x
    sec
    sbc #S_PUNCH.b
    cmp #4
    bcc HO_atkst                          ; standing hits 5-8
    lda FP+F_STATE,x
    sec
    sbc #S_CPUNCH.b
    cmp #8
    bcc HO_atkst                          ; crouching/jumping hits 19-26
    lda FP+F_STATE,x
    sec
    sbc #S_SPECIAL.b
    cmp #S_KNEE-S_SPECIAL                 ; command specials + fast 48-59
    bcc HO_atkst
    lda FP+F_STATE,x
    sec
    sbc #S_KNEE.b
    cmp #10
    bcc HO_atkst                          ; knee family 60-69
    cmp #S_THROW-S_KNEE
    beq HO_atkst                          ; 74 = throw attempt
    lda FP+F_STATE,x
    sec
    sbc #S_SUPPER.b
    cmp #5
    bcc HO_atkst                          ; supers 85-89
    lda FP+F_STATE,x
    sec
    sbc #S_REVACT.b
    cmp #(S_EXT_LAST-S_REVACT+1)
    bcc HO_atkst                          ; parry counter follow-ups 103-106
                                          ;   + imported follow-ups 107-111
        jmp HO_no
HO_atkst:
    sep #$20
    .ACCU 8
    ; a custom-state victim, or one already down/rising, cannot be hit again
    ldy vofs
    lda FP+F_GRAB,y
    bne +
    lda FP+F_STATE,y
    cmp #S_DOWN.b
    beq +
    cmp #S_GETUP.b
    beq +
    bra ++
+       jmp HO_no
++  lda FP+F_INVUL,y                    ; NotHitBy: the attack passes
    beq +                               ;   through entirely
        jmp HO_no
+   ldx aofs
    lda FP+F_HITDONE,x
    beq +
        jmp HO_no
    +
    rep #$20
    .ACCU 16
    ldx aofs
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    sta scr4
    ldy #CH_ACTIVE
    ldx #boxp
    jsr CharPtr                           ; boxp -> attacker HitDef table
    ldy scr4
    lda [boxp],y                          ; HitDef start+1; 0 = no attack
    bne +
        jmp HO_no
    +
    dec a
    ldx aofs
    cmp FP+F_FRAME,x
    beq +                                 ; active from trigger frame onward
    bcc +
        jmp HO_no
    +
    ldx aofs
    lda FP+F_ATKBOX,x
    bne +
        jmp HO_no
    +
    sta boxp
    sep #$20
    .ACCU 8
    lda FP+F_TBANK,x
    sta boxp+2
    rep #$20
    .ACCU 16
    jsr MakeBox                           ; attacker -> box1
    lda box0
    sta box1
    lda box0+2
    sta box1+2
    lda box0+4
    sta box1+4
    lda box0+6
    sta box1+6
    ldx vofs
    stx fofs
    lda FP+F_HURTBOX,x
    bne +
        jmp HO_no
    + 
    sta boxp
    sep #$20
    .ACCU 8
    lda FP+F_TBANK,x
    sta boxp+2
    rep #$20
    .ACCU 16
    jsr MakeBox                           ; victim -> box0
    ; overlap: victim x0<x1' && x1>x0' && y0<y1' && y1>y0'
    ; signed compares: boxes near the left edge legitimately go negative
    lda box0
    cmp box1+4
    bvc +
    eor #$8000.w
+   bmi +
        jmp HO_nohit
    +
    lda box0+4
    cmp box1
    bvc +
    eor #$8000.w
+   bpl +
        jmp HO_nohit
    +
    lda box0+2
    cmp box1+6
    bvc +
    eor #$8000.w
+   bmi +
        jmp HO_nohit
    +
    lda box0+6
    cmp box1+2
    bvc +
    eor #$8000.w
+   bpl +
        jmp HO_nohit
    +
    ; HIT
    ldx aofs
    stx fofs
    sep #$20
    .ACCU 8
    lda #1
    sta FP+F_HITDONE,x
    rep #$20
    .ACCU 16
    lda FP+F_STATE,x
    and #$00FF.w
    asl a
    sta scr4
    ; attack flags word: bit0 knockdown, bit1 low hit, b4-7 guard H/M/L/A,
    ; b8-10 animtype
    ldy #CH_FLAGS
    ldx #boxp
    jsr CharPtr
    ldy scr4
    lda [boxp],y
    sta scr5
    ; a victim holding "back" in a guardable state blocks the hit when the
    ; attack's guardflag matches the blocking posture
    ldx vofs
    stx fofs
    lda scr5
    bit #$0008.w                          ; throw HitDefs bypass guard, but
    beq HO_chkgrd                         ;   only connect against a victim
    lda FP+F_Y,x                          ;   that is grounded and not in a
    bne HO_twhiff                         ;   hit state (hitflag M-)
    lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_HIT.w
    beq HO_twhiff
    cmp #S_GHIT.w
    beq HO_twhiff
    bra HO_apply
HO_twhiff:
    jmp HO_nohit
HO_chkgrd:
    jsr RevCheck                          ; armed parry takes priority over
    beq +                                 ;   the regular guard check
        jmp HO_rev
+   jsr GuardCheck
    beq +
        jmp HO_guard
    +
    jsr HitModifiers
    bcc +
        jmp HO_nohit
    +
    ; regular hit spark
    lda #0                                ; SparkHit
    jsr SparkSpawn
    jsr PlayHitSfx
HO_apply:
    ldx aofs                              ; damage/velocity rows come from
    stx fofs                              ; the attacker's tables
    ldy #CH_SHAKE                         ; HitDef envshake (supers): start
    ldx #boxp                             ;   a screen shake on contact
    jsr CharPtr
    lda scr4                              ; scr4 = sid*2 for .dw tables;
    lsr a                                 ;   ShakeTab is .db per sid
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y
    beq +
    jsr SetShake
+   rep #$20
    .ACCU 16
    ; hitstop: the HitDef pausetime[0] freezes both fighters for the
    ; contact flash -- without it the attacker's recovery runs through
    ; the hit and the blow looks like it cancels itself
    ldy #CH_P1PAUSE
    ldx #boxp
    jsr CharPtr
    lda scr4                            ; PauseTab is .db per sid
    lsr a
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y
    beq +
    sta pausecnt
+   rep #$20
    .ACCU 16
    ldy #CH_DAMAGE
    ldx #boxp
    jsr CharPtr
    ldy scr4
    lda [boxp],y
    sta scr0
    ; --- FUSION damage modifiers -----------------------------------------
    sep #$20
    .ACCU 8
    ldx aofs
    lda FP+F_MAX,x                        ; MAX mode: +25% damage
    beq HM_dmg_nomax
    rep #$20
    .ACCU 16
    lda scr0
    lsr a
    lsr a
    clc
    adc scr0
    sta scr0
    bra HM_dmg_ctr
HM_dmg_nomax:
    rep #$20
    .ACCU 16
HM_dmg_ctr:
    lda FUS_CTR                           ; counter hit: +25% damage
    beq HM_dmg_scale
    lda scr0
    lsr a
    lsr a
    clc
    adc scr0
    sta scr0
HM_dmg_scale:
    ; KOF-style combo decay: 2-3 hits -1/8, 4-6 -1/4, 7+ -3/8.
    ldx aofs
    lda combohit,x
    and #$00FF.w
    cmp #2.w
    bcc HM_dmg_done
    cmp #4.w
    bcs HM_dmg_s4
    lda scr0
    lsr a
    lsr a
    lsr a
    sta scr1
    lda scr0
    sec
    sbc scr1
    sta scr0
    bra HM_dmg_done
HM_dmg_s4:
    cmp #7.w
    bcs HM_dmg_s7
    lda scr0
    lsr a
    lsr a
    sta scr1
    lda scr0
    sec
    sbc scr1
    sta scr0
    bra HM_dmg_done
HM_dmg_s7:
    lda scr0
    lsr a
    lsr a
    lsr a
    sta scr1
    asl a
    clc
    adc scr1
    sta scr1
    lda scr0
    sec
    sbc scr1
    sta scr0
HM_dmg_done:
    lda scr0
    bne +
    lda #1
    sta scr0
+
    ldx aofs
    lda FP+F_STATE,x
    and #$00FF.w
    jsr SurvTrackHit                       ; survivor bonus tracks the last hit
    ldx vofs
    jsr PracBlock
    rep #$20
    .ACCU 16
    bcs HO_dmg_done                       ; practice: human HP cannot drop
    lda FP+F_HP,x
    sec
    sbc scr0
    bpl +
    lda #0
+   sta FP+F_HP,x
    ldx vofs
    jsr DizzyBump
HO_dmg_done:
    lda #75.w                            ; one award per contact (HitDone
    ldx aofs                             ; prevents repeat hits in a state)
    jsr AddPower
    lda #38.w
    ldx vofs
    jsr AddPower
    lda scr5                              ; HitDef flags: keep them across
    pha                                 ;   ComboBump -> ComboDraw, whose
    jsr ComboBump                         ;   HITS digits reuse scr5/scr6.
    pla
    sta scr5
    ldx aofs                              ; ComboDraw's WriteStr clobbers scr4:
    lda FP+F_STATE,x                      ;   rebuild the sid index from the
    and #$00FF.w                          ;   attacker's state before the tables
    asl a
    sta scr4
    ; knockback: HitVel records are 8 bytes/state = ground vx,vy + air vx,vy.
    ; x is a magnitude pushed away from the attacker; y keeps screen sign.
    ldy #CH_HITVEL
    ldx #boxp
    jsr CharPtr
    lda scr4
    asl a
    asl a                                 ; scr4 = state*2 -> y = state*8
    tay
    lda [boxp],y
    sta scr0
    iny
    iny
    lda [boxp],y
    sta scr1                              ; ground vy (upward launch)
    iny
    iny
    lda [boxp],y
    sta scr2                              ; air vx
    iny
    iny
    lda [boxp],y
    sta scr3                              ; air vy
    ldx vofs
    lda FP+F_Y,x
    beq +
    lda scr2                              ; airborne victim: use air.velocity
    sta scr0
    lda scr3
    sta scr1
+   ldx aofs
    lda FP+F_FACING,x
    bmi +
    lda scr0
    bra ++
+   lda scr0
    eor #$FFFF.w                          ; push away: -magnitude when the
    inc a                                 ;   attacker faces left
++  ldx vofs
    sta FP+F_VX,x
    lda scr1
    sta FP+F_VY,x
    ; FUSION MAX / counter hit: +25% knockback, like arcade MAX pushback.
    lda FUS_CTR
    bne +
    ldx aofs
    sep #$20
    .ACCU 8
    lda FP+F_MAX,x
    rep #$20
    .ACCU 16
    beq ++
+   ldx vofs
    lda FP+F_VX,x
    jsr BumpWord125
    sta FP+F_VX,x
    lda FP+F_VY,x
    jsr BumpWord125
    sta FP+F_VY,x
++  ldx vofs
    ; cornerpush: a grounded victim already against the stage bound cannot
    ; slide, so the knockback recoils onto the attacker -- breaks infinite
    ; strings in the corner.  StAttack zeroes vx every tick, so the recoil
    ; is applied as a direct ~6-tick displacement of the attacker's X.
    lda FP+F_Y,x
    bne HO_cp_done                          ; airborne victims still slide
    lda FP+F_VX,x
    sta scr2                                ; signed push velocity
    bmi +
    lda FP+F_X,x                            ; pushed right: at right bound?
    cmp #(STAGE_R-1)<<8.w
    bcc HO_cp_done
    bra HO_cp_recoil
+   lda FP+F_X,x                            ; pushed left: at left bound?
    cmp #(STAGE_L+1)<<8.w
    bcs HO_cp_done
HO_cp_recoil:
    lda scr2
    eor #$FFFF.w
    inc a                                   ; recoil points back at attacker
    sta scr3
    asl a
    clc
    adc scr3
    asl a                                   ; *6 of the denied slide
    sta scr3
    ldx aofs
    lda scr3
    jsr AddXClamped
    ldx vofs
HO_cp_done:
    stx fofs
    ; TargetState / p2stateno: switch to an attacker-owned victim state.
    ; The row also carries the victim side of HitDef pausetime.
    ldx aofs
    stx fofs
    ldy #CH_TARGETTAB
    ldx #boxp
    jsr CharPtr
    lda scr4
    asl a                                 ; TargetTab rows are 4 bytes
    tay
    lda [boxp],y
    and #$00FF.w
    cmp #$00FF.w
    bne +
    jmp HO_normalhit
+   sta scr6                              ; compact target runtime state
    iny
    sep #$20
    .ACCU 8
    lda [boxp],y
    sta ct_tmp                            ; preserve pause across EnterState
    iny
    lda [boxp],y
    sta ct_ei                             ; p1 state on hit ($FF = stay)
    iny
    lda [boxp],y
    sta ct_ets                            ; flags: bit0 = victim own sprites
    ldx vofs
    and #$01.b
    beq +
    lda #$01.b                            ; bound victim keeps its own data
    bra ++
+   lda #$03.b                            ; custom victim + ChangeAnim2 source
++  sta FP+F_GRAB,x
    lda aofs
    sta FP+F_OWNER,x
    rep #$20
    .ACCU 16
    lda FP+F_VX,x
    sta FP+F_HITVX,x
    lda FP+F_VY,x
    sta FP+F_HITVY,x
    sep #$20                              ; p1stateno redirect implies
    .ACCU 8                               ;   p1facing=1: square the attacker
    lda ct_ei                             ;   to the victim before facing it
    cmp #$FF.b
    beq HO_vface
    rep #$20
    .ACCU 16
    ldx vofs
    lda FP+F_X,x
    ldx aofs
    sec
    sbc FP+F_X,x                          ; victim - attacker
    lda #$0001.w
    bcs +
    lda #$FFFF.w
+   sta FP+F_FACING,x
HO_vface:
    rep #$20
    .ACCU 16
    ldx aofs                              ; p2facing=1: face the attacker
    lda FP+F_FACING,x
    eor #$FFFF.w
    inc a
    ldx vofs
    sta FP+F_FACING,x
    stx fofs
    lda scr6
    jsr EnterState
    ldx vofs
    lda ct_tmp
    and #$00FF.w
    sta FP+F_HTIMER,x
    sep #$20                              ; attacker joins the grab sequence
    .ACCU 8                               ;   (p1stateno -> throw's 810)
    lda ct_ei
    cmp #$FF.b
    beq HO_vdone
    ldx aofs
    stx fofs
    jsr JoyRelDir                         ; acc8: holdfwd at grab -> var(2)
    ldx fofs
    and #$04.b
    lsr a
    lsr a
    sta FP+F_TFLAGS,x
    rep #$20
    .ACCU 16
    lda ct_ei
    and #$00FF.w
    jsr EnterState
HO_vdone:
    jmp HO_done
HO_normalhit:
    ldx vofs
    stx fofs
    ; pick the get-hit anim while the victim state is still the pre-hit one:
    ; animtype>=3 (back/up/diagup) or airborne -> 5030; crouching -> 5020 base;
    ; standing victim of a low hit -> 5010; otherwise 5000 + animtype.
    lda scr5
    xba
    and #$0007.w
    sta scr6                              ; animtype
    cmp #3
    bcc +
    lda #ANIM_HIT_AIR
    bra HO_aset
+   ldx vofs
    lda FP+F_Y,x
    beq +
    lda #ANIM_HIT_AIR
    bra HO_aset
+   lda FP+F_STATE,x
    and #$00FF.w
    cmp #S_CROUCH
    beq HO_crhit
    cmp #S_CDOWN
    beq HO_crhit
    cmp #S_CUP
    beq HO_crhit
    cmp #S_CPUNCH
    bcc HO_shit
    cmp #S_APUNCH
    bcc HO_crhit                          ; 19-22 = crouching attacks
HO_shit:
    lda scr5
    and #$0002.w
    beq +
    lda #ANIM_HIT_LO                      ; low hit against a stander
    bra HO_base
+   lda #ANIM_HIT_HI
    bra HO_base
HO_crhit:
    lda #ANIM_HIT_CR
HO_base:
    clc
    adc scr6                              ; base + animtype (0-2)
HO_aset:
    sta scr6                              ; anim slot applied after EnterState
    ldx vofs
    lda FP+F_HP,x
    bne +
    jmp HO_ko                             ; finishing blow: dramatic knockdown
+
    lda scr5
    and #$0001.w
    beq +
    jmp HO_kdown                          ; knockdown: trip/sweep/fall hits
+
    lda scr4
    pha                                 ; EnterState/SetAnimSlot clobber the
    lda scr6                            ;   DP scratch regs -- keep sid index
    pha                                 ;   and anim slot alive across them
    lda #S_HIT
    jsr EnterState
    pla
    sta scr6
    jsr SetAnimSlot
    pla
    sta scr4
    ldx aofs
    stx fofs
    ldy #CH_HTTIME
    ldx #boxp
    jsr CharPtr
    ldy scr4
    lda [boxp],y
    sta scr0
    ldx vofs
    lda scr0
    sta FP+F_HTIMER,x
    ldx aofs
    stx fofs
    ldy #CH_SLIDE
    ldx #boxp
    jsr CharPtr
    ldy scr4
    lda [boxp],y
    sta scr0                              ; slidetime (full-speed window)
    ; The MUGEN hit shake is the global hitstop above (pausecnt), which
    ; freezes state time: F_HTIMER only starts draining once it runs out.
    ; Subtracting pausetime[1] here therefore ate almost the whole window
    ; (a 12/11 normal was left with a single tick, which StHit stopped
    ; before Physics could apply it) and the victim never slid out of
    ; point-blank range away from the corner.  Grounded hittime is measured
    ; from the end of the freeze now, so the slide window is the smaller of
    ; hittime and slidetime.  Airborne victims keep slidetime: their
    ; knockback is ballistic.
    ldx vofs
    lda FP+F_Y,x
    bne HO_slide_store
    lda FP+F_HTIMER,x                     ; hittime
    cmp scr0
    bcc +
    lda scr0                              ; slidetime is the shorter window
+   sta scr0
HO_slide_store:
    ldx vofs
    lda scr0
    sta FP+F_SLIDE,x
    jmp HO_done
HO_kdown:
    lda #S_DOWN
    jsr EnterState                        ; fofs is already the victim
    lda scr5
    and #$0800.w                          ; ground.type=Trip: crumple with
    beq +                                 ;   the 5070 trip-fall instead of
    lda #ANIM_TRIP                        ;   the launched 5050 fall
    jsr SetAnimSlot
+   ldx fofs
    lda #LIEDOWN.w
    sta FP+F_HTIMER,x
    jmp HO_done
HO_ko:                                    ; KO: boosted launch, stays down
    ldx vofs
    stx fofs
    lda FP+F_VX,x
    asl a                                 ; double the pushback...
    sta FP+F_VX,x                         ;   (KO_ForceDown caps it)
    lda FP+F_VY,x
    asl a                                 ; double the launch...
    sta FP+F_VY,x                         ;   (at least KOVY upward)
    jsr KO_ForceDown
    jmp HO_done
; A(16) = S_AGUARD for an airborne victim, else S_GHIT.  fofs = victim.
GuardState:
    ldx fofs
    lda FP+F_Y,x
    bne +
    lda #S_GHIT.w
    rts
+   lda #S_AGUARD.w
    rts

HO_guard:                               ; blocked hit: chip, pushback, stun
    sta scr6                              ; guard-hit anim slot
    ; guard hitstop: PauseTab holds guard.pausetime on guardable hits
    ldx aofs
    stx fofs
    ldy #CH_P1PAUSE
    ldx #boxp
    jsr CharPtr
    lda scr4
    lsr a
    tay
    sep #$20
    .ACCU 8
    lda [boxp],y
    beq +
    sta pausecnt
+   rep #$20
    .ACCU 16
    ; guard spark (SparkAnimTab[1]; A held the ANIM_GHIT_* slot = wild index)
    lda #1                                ; SparkGuard
    jsr SparkSpawn
    sep #$20
    .ACCU 8
    lda #SFX_GUARD.b
    jsr SfxPlay
    rep #$20
    .ACCU 16
    ; chip damage cannot KO: hp bottoms out at 1
    ldx aofs
    stx fofs
    ldy #CH_GDMG
    ldx #boxp
    jsr CharPtr
    ldy scr4
    lda [boxp],y
    sta scr0
    ldx vofs
    jsr PracBlock
    rep #$20
    .ACCU 16
    bcs HO_gdmg_done                      ; practice: no chip damage either
    lda FP+F_HP,x
    sec
    sbc scr0
    bpl +
    lda #1
    +   bne ++
    lda #1
    ++  sta FP+F_HP,x
HO_gdmg_done:
    lda #31.w
    ldx aofs
    jsr AddPower
    lda #19.w
    ldx vofs
    jsr AddPower
    ; guard pushback: GVel records are 6B/state = ground gx + air gx,gy
    ldx aofs
    stx fofs
    ldy #CH_GVEL
    ldx #boxp
    jsr CharPtr
    lda scr4                              ; = state*2
    asl a                                 ; state*4
    clc
    adc scr4                              ; state*6
    tay
    lda [boxp],y
    sta scr0
    stz scr1
    ldx vofs
    lda FP+F_Y,x
    beq +
    iny
    iny
    lda [boxp],y
    sta scr0                              ; air guard gx
    iny
    iny
    lda [boxp],y
    sta scr1                              ; air guard gy
+   ldx aofs
    lda FP+F_FACING,x
    bmi +
    lda scr0
    bra ++
+   lda scr0
    eor #$FFFF.w                          ; push away: -magnitude when the
    inc a                                 ;   attacker faces left
++  ldx vofs
    sta FP+F_VX,x
    lda scr1
    sta FP+F_VY,x
    ; cornerpush on block too: a guarding victim pinned to the stage bound
    ; cannot slide, so the denied pushback recoils onto the attacker --
    ; otherwise blocked strings are still infinite pressure in the corner.
    lda FP+F_Y,x
    bne HO_gcp_done                         ; airborne victims still slide
    lda FP+F_VX,x
    sta scr2                                ; signed push velocity
    bmi +
    lda FP+F_X,x                            ; pushed right: at right bound?
    cmp #(STAGE_R-1)<<8.w
    bcc HO_gcp_done
    bra HO_gcp_recoil
+   lda FP+F_X,x                            ; pushed left: at left bound?
    cmp #(STAGE_L+1)<<8.w
    bcs HO_gcp_done
HO_gcp_recoil:
    lda scr2
    eor #$FFFF.w
    inc a                                   ; recoil points back at attacker
    sta scr3
    asl a
    clc
    adc scr3
    asl a                                   ; *6 of the denied slide
    sta scr3
    ldx aofs
    lda scr3
    jsr AddXClamped
    ldx vofs
HO_gcp_done:
    stx fofs
    lda scr4                              ; EnterState/SetAnimSlot clobber the
    pha                                 ;   DP scratch regs -- keep sid index
    lda scr6                            ;   and anim slot alive across them
    pha
    jsr GuardState
    jsr EnterState
    pla
    sta scr6
    jsr SetAnimSlot
    pla
    sta scr4
    ldx aofs                              ; slide + stun timers come from
    stx fofs                              ; the attacker's tables
    ldy #CH_SLIDE
    ldx #boxp
    jsr CharPtr
    ldy scr4
    lda [boxp],y
    sta scr0
    ldx vofs
    lda scr0
    sta FP+F_SLIDE,x
    ldx aofs
    stx fofs
    ldy #CH_HTTIME
    ldx #boxp
    jsr CharPtr
    ldy scr4
    lda [boxp],y
    sta scr0
    ldx vofs
    lda scr0
    sta FP+F_HTIMER,x
    jmp HO_done
HO_rev:                                 ; parry / counter-grab: spark + block
    sep #$20                            ;   sound; RevCheck recorded the
    .ACCU 8                             ;   actor/victim sids in DP bytes.
    rep #$20
    .ACCU 16
    lda #1                              ;   The hit still counts as contact
    jsr SparkSpawn                      ;   (F_HITDONE) for cancels/MoveHit.
    sep #$20
    .ACCU 8
    lda #SFX_GUARD.b
    jsr SfxPlay
    lda.b rev_vsid
    cmp #$FF.b
    bne HO_cgrab
    rep #$20
    .ACCU 16
    ldx vofs
    stx fofs
    sep #$20
    .ACCU 8
    lda.b rev_bsid
    rep #$20
    .ACCU 16
    and #$00FF.w
    jsr EnterState                      ; victim -> blocked pose (1310+)
    jmp HO_done
HO_cgrab:                               ; ReversalDef p2stateno: the fighter
    ldx aofs                            ;   that got hit (aofs) becomes the
    lda #1.b                            ;   held victim; the reversal actor
    sta FP+F_GRAB,x                     ;   (vofs) becomes the thrower.
    lda vofs                            ;   F_GRAB bit0 marks the custom
    sta FP+F_OWNER,x                    ;   victim; bit1 clear keeps the
    stx fofs                            ;   generic held pose.
    lda.b rev_vsid
    rep #$20
    .ACCU 16
    and #$00FF.w
    jsr EnterState                      ; attacker -> held victim slot
    rep #$20
    .ACCU 16
    ldx vofs
    stx fofs
    sep #$20
    .ACCU 8
    lda.b rev_bsid
    rep #$20
    .ACCU 16
    and #$00FF.w
    jsr EnterState                      ; reversal actor -> throw follow-up
    jmp HO_done
HO_done:
HO_nohit:
HO_no:
    rep #$20
    .ACCU 16
    rts

; Convert boxp AIR rectangle (x0,y0,x1,y1) for fofs to screen box0.
MakeBox:
    sep #$20
    .ACCU 8
    ldy #0
    lda [boxp],y
    sta scr0
    iny
    lda [boxp],y
    sta scr1
    iny
    lda [boxp],y
    sta scr2
    iny
    lda [boxp],y
    sta scr3
    rep #$20
    .ACCU 16
    lda scr0                            ; sign-extend all AIR coordinates
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   sta scr0
    lda scr1
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   sta scr1
    lda scr2
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   sta scr2
    lda scr3
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   sta scr3
    ldx fofs
    lda FP+F_FACING,x
    bpl +
    lda scr2                            ; facing left: x' = -x1 .. -x0
    eor #$FFFF.w
    inc a
    sta scr4
    lda scr0
    eor #$FFFF.w
    inc a
    sta scr2
    lda scr4
    sta scr0
+   ; Airborne frames can start their Clsn1 union at the fist/foot, leaving
    ; the attacker's axis outside the hit box.  At point-blank -- and
    ; especially with a cornered victim who cannot be pushed back -- that
    ; makes a move visibly cross the body without registering.  Clamp the
    ; signed frame offsets so the hit box contains x=0 (the axis); the
    ; authored forward reach is unchanged.  The victim's hurt box keeps its
    ; authored geometry (fofs != aofs on that MakeBox call).
    lda fofs
    cmp aofs
    bne +
    lda scr0                            ; leftmost offset
    bmi ++
    stz scr0
++  lda scr2                            ; rightmost offset
    bpl +
    stz scr2
+   lda FP+F_X,x
    xba
    and #$00FF.w
    pha
    clc
    adc scr0
    sta box0
    pla
    clc
    adc scr2
    sta box0+4
    lda #GROUND_Y.w
    sta scr4
    lda FP+F_Y,x
    xba
    and #$00FF.w
    sta scr5
    lda scr4
    sec
    sbc scr5
    sta scr4                            ; base screen Y at character axis
    clc
    adc scr1
    sta box0+2
    lda scr4
    clc
    adc scr3
    sta box0+6
    rts

; ---------------------------------------------------------------------------
; PRACTICE: keep CPU-driven sides completely idle.  AI_sel still runs so
; SELECT can hand a side back to its pad, but every synthetic input is
; cleared before TickFighter reads it.
PracDrive:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #5
    beq PD_idle
    jmp AiDrive
PD_idle:
    jsr AiDrive
    sep #$20
    .ACCU 8
    lda.b cpu1
    beq +
    rep #$20
    .ACCU 16
    stz FP+F_JOY
    stz FP+F_JOYPR
    sep #$20
    .ACCU 8
+   lda.b cpu2
    beq +
    rep #$20
    .ACCU 16
    stz FP+F_JOY+FP2OFS
    stz FP+F_JOYPR+FP2OFS
    sep #$20
    .ACCU 8
+   rep #$20
    .ACCU 16
    rts

; ---------------------------------------------------------------------------
AiDrive:                                ; CPU control per select-screen flag
    rep #$20                            ;   (cpu1/cpu2): set => AI drives the
    .ACCU 16                            ;   fighter, human pad ignored.
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #5
    beq AD_idle                          ; practice: SELECT still toggles the
                                         ;   CPU flags, but the AI never runs
    lda cpu2
    beq +
    ldx #FP2OFS
    jsr AI_one
+   sep #$20
    .ACCU 8
    lda cpu1
    beq +
    ldx #0
    jsr AI_one
+
AD_idle:
    rep #$20
    .ACCU 16
    rts
; X = fighter offset.  Drives the fighter unconditionally (flag-gated by
; the caller) - the AI writes synthetic joy bits like a human pad.
; Every difficulty uses the character-aware AI; the level-scaled rates keep
; level 1 sparse (a few jump-ins/specials) and level 8 nearly relentless.
AI_one:
    sep #$20
    .ACCU 8
    stx fofs
    lda AI_LEVEL
    bne AI_smart                        ; level 0 is an invalid fallback
    jmp AI_classic
AI_classic:
    sep #$20
    .ACCU 8
    stz FP+F_JOY,x
    stz FP+F_JOY+1,x
    rep #$20
    .ACCU 16
    txa                                 ; opponent offset
    eor #$0040.w
    tay
    lda FP+F_X,y
    sec
    sbc FP+F_X,x
    bpl +
    eor #$FFFF.w
    inc a
+   xba                                 ; /256 -> distance px
    and #$00FF.w
    cmp #48
    bcs +
        jmp AI_attack
    + 
    sep #$20
    .ACCU 8
    lda FP+F_FACING,x
    bmi +
    lda #$01.b                          ; hold right
    bra ++
+   lda #$02.b                          ; hold left
++  sta FP+F_JOY+1,x
    rep #$20
    .ACCU 16
    rts
AI_attack:
    sep #$20
    .ACCU 8
    lda framecnt                        ; phase-desync the two CPUs
    cpx #0
    bne +
    eor #$10.b                          ; P1 attacks on offset phase
+   and #$3F.b
    cmp #$20.b
    bcc +
        jmp AI_done
    + 
    lda #$40.b                          ; press Y (weak punch)
    sta FP+F_JOYPR,x
    sta FP+F_JOY,x
AI_done:
    rep #$20
    .ACCU 16
    rts

; ---------------------------------------------------------------------------
; Character-aware CPU AI (difficulty 1..9).  The move table is generated by
; tools/build_fight.py from each fighter's own CmdTab; selection is by the
; active character id (sel1/sel2), with Kyo as the generic fallback.  The
; routine still writes synthetic pad bits like AI_classic, and enters
; evades/specials/supers directly only while the fighter is neutral.
; Airborne phases are driven here too: a jump-in keeps the takeoff direction
; held and then presses an air attack near the apex.
; ---------------------------------------------------------------------------
AI_smart:
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_JOY,x
    stz FP+F_JOYPR,x
    sep #$20
    .ACCU 8
    jsr AI_LoadTab
    ; per-side timers tick even while a move/anim owns the fighter
    lda AI_SIDE
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda AI_TIMER1,x
    beq +
    dec a
    sta AI_TIMER1,x
+   lda AI_JUMPCD,x
    beq +
    dec a
    sta AI_JUMPCD,x
+   lda AI_OFFCD,x
    beq +
    dec a
    sta AI_OFFCD,x
+   lda AI_TIMER2,x                     ; hit-confirm cancel throttle
    beq +
    dec a
    sta AI_TIMER2,x
+   ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_STATE,x
    cmp #S_PUNCH                        ; connected grounded normal: let the
    bcc AI_state_dispatch               ;   CPU hit-confirm into a special
    cmp #S_CSKICK+1                     ;   or super, like the player can
    bcs AI_state_dispatch
    jsr AI_ComboCheck
    bcs AI_done
AI_state_dispatch:
    ldx fofs
    lda FP+F_STATE,x
    cmp #S_JSTART
    beq AI_air_hold
    cmp #S_JUMP
    beq AI_air_fight
    cmp #S_JUMPF
    beq AI_air_fight
    cmp #S_JUMPB
    beq AI_air_fight
    cmp #S_LAND
    beq AI_air_reset
    cmp #S_STAND
    bne +
    jmp AI_ok
+   cmp #S_WALKF
    bne +
    jmp AI_ok
+   cmp #S_WALKB
    bne +
    jmp AI_ok
+   jmp AI_done
AI_air_reset:
    jsr AI_SideX
    stz AI_JUMP,x
    stz AI_AIRT,x
    jmp AI_done
AI_air_hold:                            ; takeoff squat: keep the full jump
    jsr AI_SideX                         ;   alive and preserve the launch
    lda AI_JUMP,x                       ;   direction sampled by the state
    beq AI_air_ret
    jsr AI_DirFwd
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_JOY,x
    ora #JOY_UP.w
    sta FP+F_JOY,x
    sep #$20
    .ACCU 8
    jsr AI_SideX
    lda AI_JUMP,x
    and #AI_J_ATK
    beq AI_air_ret
    lda AI_AIRT,x
    beq AI_air_ret
    dec a
    sta AI_AIRT,x
    jmp AI_done
AI_air_fight:                           ; airborne: press the jump-in attack
    jsr AI_SideX
    lda AI_JUMP,x
    and #AI_J_ATK
    beq AI_air_ret
    lda AI_AIRT,x
    beq AI_air_press
    dec a
    sta AI_AIRT,x
    jmp AI_done
AI_air_press:
    jsr AI_SideX
    stz AI_JUMP,x
    stz AI_AIRT,x
    inc.w AI_DBG_AIR
    ldx fofs
    jsr AI_Rand
    and #$01
    beq AI_air_punch
    lda #$80.b                          ; strong kick (A)
    sta FP+F_JOY+1,x
    sta FP+F_JOYPR+1,x
    jmp AI_done
AI_air_punch:
    lda #$80.b                          ; strong punch (X)
    sta FP+F_JOY,x
    sta FP+F_JOYPR,x
AI_air_ret:
    jmp AI_done
AI_ok:
    jsr AI_Perceive
    ; a committed action (block/approach/retreat) owns the pad for a while
    lda AI_SIDE
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda AI_TIMER1,x
    beq AI_think
    lda AI_HOLD1,x
    cmp #1
    beq AI_holdback
    cmp #2
    beq AI_holdfwd
    cmp #3
    beq AI_holdcrouch
    jmp AI_done
AI_holdback:
    jsr AI_DirBack
    jmp AI_done
AI_holdfwd:
    jsr AI_DirFwd
    jmp AI_done
AI_holdcrouch:
    jsr AI_DirBack
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_JOY,x
    ora #JOY_DN.w
    sta FP+F_JOY,x
    jmp AI_done

AI_think:
    sep #$20
    .ACCU 8
    ; --- projectiles: guard (levels 3+), jump or roll through them -------
    jsr AI_ProjThreat
    bcc AI_no_proj
    lda AI_LEVEL
    cmp #3
    bcc AI_no_proj
    ; A guardable shot is blocked when the read succeeds.  The 160 base
    ; rate scales with difficulty, so low levels still favour escape.
    ; Unblockable shots (no H/M/L ground bit) always fall through.
    lda AI_PDIST+1
    and #$70.b
    beq AI_proj_escape
    lda #160
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcs AI_proj_escape
    inc.w AI_DBG_PBLOCK
    lda AI_PDIST+1
    and #$30.b                          ; H|M: standing guard stops it
    bne AI_proj_block_stand
    jsr AI_HoldCrouch                   ; L-only shot: crouch guard
    jmp AI_done
AI_proj_block_stand:
    jsr AI_HoldBack
    jmp AI_done
AI_proj_escape:
    lda AI_MIX
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcs AI_no_proj
    inc.w AI_DBG_PROJ
    lda AI_LEVEL
    cmp #5
    bcc AI_proj_jump
    lda AI_PDIST
    cmp #72
    bcs AI_proj_jump
    lda AI_FLAGS
    and #AI_PF_PRESSURE
    beq AI_proj_jump
    lda #95                            ; forward roll through the projectile
    jmp AI_StartMove
AI_proj_jump:
    jsr AI_JumpUp
    jmp AI_done
AI_no_proj:
    ; AI_ProjThreat returns with M=8.  The earlier 16-bit branches above
    ; can leave WLA's assembly-time width at 16 here; an immediate such as
    ; lda #96 then gains a stray $00 byte that executes as BRK.
    sep #$20
    .ACCU 8

    ; --- anti-air first: a jump-in must not be answered with a ground block
    lda AI_OPPY
    beq AI_ground_threat
    lda AI_OPPFALL                       ; a falling jump-in gets the widest
    beq AI_aa_range_rise                 ;   window; a rising jump is safer
    lda #60                             ;   to contest later
    bra AI_aa_range
AI_aa_range_rise:
    lda #96
AI_aa_range:
    sta AI_TMP
    lda AI_DIST
    cmp AI_TMP
    bcs AI_ground_threat
    lda AI_AA
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcs AI_ground_threat
    inc.w AI_DBG_THREAT
    inc.w AI_DBG_AA
    lda AI_OPPFALL
    beq AI_aa_notfall
    inc.w AI_DBG_AAF
AI_aa_notfall:
    lda #1
    sta AI_SCANMODE
    jsr AI_ScanMove
    bcc AI_aa_normal
    jmp AI_have_move
AI_aa_normal:
    jsr AI_DoAntiAir
    jmp AI_done

AI_ground_threat:
    ; --- react to an incoming attack -------------------------------------
    lda AI_OPPATT
    bne +
    jmp AI_no_threat
+   lda AI_DIST
    cmp #140
    bcc +
    jmp AI_no_threat
+   lda AI_AGGR                        ; reaction/aggression, level-scaled
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcc +
    jmp AI_no_threat
+   inc.w AI_DBG_THREAT
    ; Evade or block: personality mix decides the dodge, defense decides
    ; the guard.  Level 7+ may read the attack and counter instead.
    lda AI_MIX
    jsr AI_Rate
    lsr a
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcc AI_evade
    lda AI_DEF
    jsr AI_Rate
    lsr a
    clc
    adc AI_TMP
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcc AI_block
    lda AI_LEVEL
    cmp #7
    bcc +
    jmp AI_no_threat                  ; counter-read: go on offense
+
AI_block:
    inc.w AI_DBG_BLOCK
    lda AI_LEVEL
    cmp #7                              ; crouch guard is a close-range read
    bcc AI_block_stand
    lda AI_DIST
    cmp #80
    bcs AI_block_stand
    jsr AI_Rand
    and #$03                            ; 1 in 4: guess a low attack
    beq AI_block_crouch
AI_block_stand:
    sep #$20
    .ACCU 8
    jsr AI_HoldBack
    jmp AI_done
AI_block_crouch:
    ; Commit the crouch exactly like the standing guard: without the hold
    ; timer the CPU re-rolled this every frame and visibly tapped down.
    jsr AI_HoldCrouch
    jmp AI_done
AI_evade:
    ; Entered directly in 8-bit mode, so the immediates below must stay
    ; byte-sized: a word immediate leaves a $00 opcode (BRK) in the stream.
    sep #$20
    .ACCU 8
    lda AI_LEVEL
    cmp #4
    bcc AI_block
    lda AI_DIST
    cmp #80
    bcs AI_evade_fwd
    ; At close range the CPU mostly rolls *through* the attack; giving
    ; ground is the rare option, so it no longer retreats in repeated taps.
    jsr AI_Rand
    and #$07
    beq AI_evade_back
    cmp #3
    bcc AI_evade_neutral
AI_evade_fwd:
    lda #95                            ; forward roll through the attack
    jmp AI_StartMove
AI_evade_back:
    lda #94                            ; backward roll (1 in 8)
    jmp AI_StartMove
AI_evade_neutral:
    lda #69                            ; neutral dodge (2 in 8)
    jmp AI_StartMove

AI_no_threat:
    ; --- punish hitstun and whiff recovery -------------------------------
    lda AI_OPPHIT
    beq AI_check_guard
    lda AI_LEVEL
    cmp #3
    bcc AI_check_guard
    lda AI_FLAGS
    and #AI_PF_ADAPT
    beq AI_check_guard
    lda AI_DIST
    cmp #96
    bcs AI_punish_move
    inc.w AI_DBG_PUNISH
    jsr AI_DoNormal
    jmp AI_done
AI_punish_move:
    jsr AI_HoldFwd
    jmp AI_done

AI_check_guard:
    ; --- a guarding foe gets thrown (grapplers do this much more) --------
    lda AI_OPPGRD
    beq AI_try_max
    lda AI_DIST
    cmp #52
    bcs AI_try_max
    lda AI_THROW
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcs AI_try_max
    lda #3
    sta AI_SCANMODE
    jsr AI_ScanMove
    bcc AI_try_max
    jmp AI_have_move

AI_try_max:
    ; --- spend a stock on the MAX burst when the kit supports it ---------
    rep #$20                            ; entry paths come from the 8-bit
    .ACCU 16                            ;   decision tree; the immediates below
    lda AI_LEVEL                        ;   are assembled as 16-bit
    cmp #5
    bcc AI_try_throw
    lda AI_FLAGS
    and #AI_PF_METER
    beq AI_try_throw
    ldx fofs
    sep #$20                            ; F_MAX is a byte; a 16-bit load
    .ACCU 8                             ;   would fold in F_STIME next door
    lda FP+F_MAX,x
    bne AI_try_throw
    rep #$20
    .ACCU 16
    lda FP+F_POWER,x
    cmp #2000.w                         ; leave one stock for the MAX super
    sep #$20
    .ACCU 8
    bcc AI_try_throw
    lda AI_MIX
    jsr AI_Rate
    lsr a
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcs AI_try_throw
    inc.w AI_DBG_MAX
    lda #0
    sta AI_SCANMODE
    lda #96                            ; FUSION MAX activation
    jmp AI_StartMove

AI_try_throw:
    ; --- command throw at point-blank range ------------------------------
    sep #$20                            ; all throw/super/special checks below
    .ACCU 8                             ;   are 8-bit, including calls from
    lda AI_DIST                         ;   AI_try_max before its mode switch
    cmp #52
    bcs AI_try_offense
    lda AI_THROW
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcs AI_try_offense
    lda #3
    sta AI_SCANMODE
    jsr AI_ScanMove
    bcc +
    jmp AI_have_move
+

AI_try_offense:
    ; --- pick one offensive option per neutral window --------------------
    ; A level-scaled cooldown spaces the repetitions: level 1 commits only
    ; every few seconds, level 8 is nearly continuous.
    jsr AI_SideX
    lda AI_OFFCD,x
    beq AI_offense_ready
    jmp AI_move
AI_offense_ready:
    ; The gate makes low levels act only on a fraction of idle frames; the
    ; chosen category then applies its own level-scaled commit rate.
    lda AI_LEVEL
    rep #$20
    .ACCU 16
    and #$00FF.w
    cmp #10.w
    bcc +
    lda #9.w
+   tax
    sep #$20
    .ACCU 8
    lda.l AIOffScale,x
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcc AI_offense_go
    jmp AI_move
AI_offense_go:
    ; Equal random categories keep specials, supers, blowbacks and jump-ins
    ; all represented at every level.
    jsr AI_Rand
    and #$03
    beq AI_try_super
    cmp #1
    beq AI_try_special
    cmp #2
    beq AI_try_blowback
    jmp AI_try_jumpin

AI_try_super:
    ; --- super / MAX-super decision --------------------------------------
    lda AI_SUPER
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcc AI_sup_ok
    jmp AI_offense_next
AI_sup_ok:
    lda #2
    sta AI_SCANMODE
    jsr AI_ScanMove
    bcs AI_sup_have
    jmp AI_offense_next
AI_sup_have:
    jmp AI_have_move
AI_try_special:
    lda AI_SPEC
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcc AI_spec_ok
    jmp AI_offense_next
AI_spec_ok:
    lda #0
    sta AI_SCANMODE
    jsr AI_ScanMove
    bcs AI_spec_have
    jmp AI_offense_next
AI_spec_have:
    jmp AI_have_move

AI_try_blowback:
    ; --- CD blowback: hard knockdown, guard crush and whiff punish -------
    lda AI_OPPY
    beq AI_blow_air_ok
    jmp AI_offense_next
AI_blow_air_ok:
    lda AI_OPPDOWN
    beq AI_blow_down_ok
    jmp AI_offense_next
AI_blow_down_ok:
    lda AI_DIST
    cmp #104
    bcc AI_blow_range_ok
    jmp AI_offense_next
AI_blow_range_ok:
    lda AI_MIX
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcc AI_blow_go
    jmp AI_offense_next
AI_blow_go:
    jsr AI_SetOffCD
    inc.w AI_DBG_BLOW
    stz AI_SCANMODE
    lda #67                            ; blowback (CD, state 250)
    jmp AI_StartMove

AI_try_jumpin:
    ; --- forward jump with an air attack ---------------------------------
    lda AI_OPPY
    beq AI_jump_air_ok
    jmp AI_offense_next
AI_jump_air_ok:
    lda AI_OPPDOWN
    beq AI_jump_down_ok
    jmp AI_offense_next
AI_jump_down_ok:
    lda AI_DIST
    cmp #24                            ; point-blank: use a throw/normal
    bcs AI_jump_min_ok
    jmp AI_offense_next
AI_jump_min_ok:
    cmp #150
    bcc AI_jump_range_ok
    jmp AI_offense_next
AI_jump_range_ok:
    jsr AI_SideX
    lda AI_JUMPCD,x
    beq AI_jump_cd_ok
    jmp AI_offense_next
AI_jump_cd_ok:
    lda AI_MIX
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcc AI_jump_go
    jmp AI_offense_next
AI_jump_go:
    jsr AI_SetOffCD
    inc.w AI_DBG_JUMP
    jsr AI_JumpIn
    jmp AI_done
AI_offense_next:
    jmp AI_move
AI_have_move:
    lda AI_SCANMODE
    cmp #2
    beq AI_hm_super
    cmp #3
    beq AI_hm_throw
    inc.w AI_DBG_SPEC
    bra AI_hm_start
AI_hm_super:
    inc.w AI_DBG_SUPER
    bra AI_hm_start
AI_hm_throw:
    inc.w AI_DBG_THROW
AI_hm_start:
    jsr AI_SetOffCD
    lda scr3                            ; AI_ScanMove left the sid here; A was
    jsr AI_StartMove                    ;   clobbered by the mode dispatch
    jmp AI_done

AI_move:
    ; --- normal attack at close range, aggression-scaled -----------------
    lda AI_DIST
    cmp #56
    bcs AI_move_space
    lda AI_AGGR
    jsr AI_Rate
    sta AI_TMP
    jsr AI_Rand
    cmp AI_TMP
    bcs AI_move_space
    jsr AI_DoNormal
    jmp AI_done
AI_move_space:
    jsr AI_Move
    jmp AI_done

; X=fofs.  Distance/facing/state snapshot used by the decision tree.
AI_Perceive:
    rep #$20
    .ACCU 16
    ldx fofs
    txa
    eor #FP2OFS.w
    tay
    lda FP+F_X,y
    sec
    sbc FP+F_X,x
    bpl +
    eor #$FFFF.w
    inc a
+   xba
    and #$00FF.w
    cmp #255.w
    bcc +
    lda #255.w
+   sta AI_DIST
    sep #$20
    .ACCU 8
    lda fofs
    beq +
    lda #1
    bra ++
+   lda #0
++  sta AI_SIDE
    lda FP+F_STATE,y
    sta AI_OPPST
    rep #$20
    .ACCU 16
    lda FP+F_Y,y
    beq +
    sep #$20
    lda #1
    bra ++
+   sep #$20
    lda #0
++  sta AI_OPPY
    stz AI_OPPFALL                       ; falling = height > 0 and vy > 0
    lda AI_OPPY
    beq AI_per_fall_done
    rep #$20
    .ACCU 16
    lda FP+F_VY,y
    bmi AI_per_fall16
    beq AI_per_fall16
    sep #$20
    .ACCU 8
    lda #1
    sta AI_OPPFALL
    bra AI_per_fall_done
AI_per_fall16:
    sep #$20
    .ACCU 8
AI_per_fall_done:
    lda AI_OPPST                        ; normal / special / super / throw
    cmp #S_PUNCH
    bcc +
    cmp #S_SKICK+1
    bcc AI_oppatt_yes
+   lda AI_OPPST
    cmp #S_CPUNCH
    bcc +
    cmp #S_ASKICK+1
    bcc AI_oppatt_yes
+   lda AI_OPPST
    cmp #S_SPECIAL
    bcc +
    cmp #67
    bcc AI_oppatt_yes
+   lda AI_OPPST
    cmp #S_SUPPER
    bcc +
    cmp #90
    bcc AI_oppatt_yes
+   lda AI_OPPST
    cmp #S_REVACT
    bcc +
    cmp #(S_EXT_LAST+1)
    bcc AI_oppatt_yes
+   lda AI_OPPST
    cmp #S_VSHAKE
    bcc AI_oppatt_no
    cmp #S_VTHROW+1
    bcc AI_oppatt_yes
AI_oppatt_no:
    lda #0
    bra AI_oppatt_set
AI_oppatt_yes:
    lda #1
AI_oppatt_set:
    sta AI_OPPATT
    stz AI_OPPGRD
    stz AI_OPPHIT
    stz AI_OPPDOWN
    lda AI_OPPST
    cmp #S_GUARD
    beq AI_per_guard
    cmp #S_CGUARD
    beq AI_per_guard
    cmp #S_BLOCK
    beq AI_per_guard
    cmp #S_BLOCKC
    beq AI_per_guard
    cmp #S_BHIT
    beq AI_per_guard
    cmp #S_BHITC
    beq AI_per_guard
    bra AI_per_hit
AI_per_guard:
    lda #1
    sta AI_OPPGRD
AI_per_hit:
    lda AI_OPPST
    cmp #S_HIT
    beq AI_per_hit_yes
    cmp #S_GHIT
    beq AI_per_hit_yes
    cmp #S_LAND
    beq AI_per_hit_yes
    bra AI_per_down
AI_per_hit_yes:
    lda #1
    sta AI_OPPHIT
AI_per_down:
    lda FP+F_HTIMER,y
    beq +
    lda #1
    sta AI_OPPHIT                    ; any remaining stun is punishable
+   lda AI_OPPST
    cmp #S_DOWN
    beq AI_per_down_yes
    cmp #S_GETUP
    beq AI_per_down_yes
    rts
AI_per_down_yes:
    lda #1
    sta AI_OPPDOWN
    rts

; Load the active character's AiTab into sptr + the header cache.  Kyo's
; table is the fallback if a character id ever falls outside the roster.
AI_LoadTab:
    sep #$20
    .ACCU 8
    lda fofs
    beq +
    lda #1
    bra ++
+   lda #0
++  sta AI_SIDE
    ldx #0
    lda AI_SIDE
    beq +
    inx
+   lda sel1,x
    cmp #49
    bcc +
    lda #0
+   rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    tax
    lda.l AiSelTab,x
    sta sptr
    sep #$20
    .ACCU 8
    ldx #0
    lda AI_SIDE
    beq +
    inx
+   lda sel1,x
    cmp #49
    bcc +
    lda #0
+   rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l AiSelBank,x
    sta sptr+2
    ldy #0
    lda [sptr],y
    sta AI_CNT
    iny
    lda [sptr],y
    sta AI_STYLE
    iny
    lda [sptr],y
    sta AI_AGGR
    iny
    lda [sptr],y
    sta AI_DEF
    iny
    lda [sptr],y
    sta AI_SPEC
    iny
    lda [sptr],y
    sta AI_SUPER
    iny
    lda [sptr],y
    sta AI_ZLO
    iny
    lda [sptr],y
    sta AI_ZHI
    iny
    lda [sptr],y
    sta AI_AA
    iny
    lda [sptr],y
    sta AI_THROW
    iny
    lda [sptr],y
    sta AI_MIX
    iny
    lda [sptr],y
    sta AI_FLAGS
    rts

; Scan the move table for the first valid entry after a random start.
; AI_SCANMODE: 0 special, 1 anti-air, 2 super, 3 throw.  Returns carry set
; and A=sid on a hit; carry clear on no match.
AI_ScanMove:
    lda AI_CNT
    bne +
    clc
    rts
+   sta scr1                            ; attempts left
    stz scr1+1
    jsr AI_Rand
    and #$0F
AI_scan_mod:
    cmp AI_CNT
    bcc +
    sec
    sbc AI_CNT
    bra AI_scan_mod
+   sta scr0                            ; current table index
    stz scr0+1
AI_scan_loop:
    lda scr0
    asl a
    sta scr2
    asl a
    clc
    adc scr2
    clc
    adc #12                             ; rows follow the 12-byte header
    tay
    lda [sptr],y
    sta scr3                            ; sid
    iny
    lda [sptr],y
    sta scr4                            ; min px
    iny
    lda [sptr],y
    sta scr5                            ; max px
    iny
    lda [sptr],y
    sta scr6                            ; flags
    sep #$20
    .ACCU 8
    lda AI_SCANMODE
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    cpx #1
    beq AI_scan_aa
    cpx #2
    beq AI_scan_super
    cpx #3
    beq AI_scan_throw
    lda scr6                            ; plain special
    and #(AI_F_SUPER|AI_F_THROW|AI_F_MAX)
    bne AI_scan_next
    bra AI_scan_range
AI_scan_aa:
    lda scr6
    and #AI_F_AA
    beq AI_scan_next
    bra AI_scan_range
AI_scan_super:
    lda scr6
    and #AI_F_SUPER
    beq AI_scan_next
    lda scr6
    and #AI_F_MAX
    beq AI_scan_range
    ldx fofs
    lda FP+F_MAX,x
    beq AI_scan_next
    bra AI_scan_range
AI_scan_throw:
    lda scr6
    and #AI_F_THROW
    beq AI_scan_next
AI_scan_range:
    lda AI_DIST
    cmp scr4
    bcc AI_scan_next
    cmp scr5
    beq AI_scan_range_ok
    bcs AI_scan_next
AI_scan_range_ok:
    iny
    lda [sptr],y
    sta AI_TMP                          ; cost/100
    beq AI_scan_prob
    cmp #30
    bcc +
    lda #30
+   asl a
    tax
    rep #$20
    .ACCU 16
    lda.l AICost100,x
    sta scr2
    ldx fofs
    lda FP+F_POWER,x                    ; 16-bit meter vs 16-bit cost
    cmp scr2
    sep #$20
    .ACCU 8
    bcc AI_scan_next
AI_scan_prob:
    iny
    lda [sptr],y
    sta AI_TMP                          ; weight 1..3
    jsr AI_Rand
    and #$03
    cmp AI_TMP
    bcs AI_scan_next
    lda scr3
    sec
    rts
AI_scan_next:
    inc scr0
    lda scr0
    cmp AI_CNT
    bcc +
    stz scr0
+   dec scr1
    beq AI_scan_no
    jmp AI_scan_loop
AI_scan_no:
    clc
    rts

; A = sid.  Enter the state directly (the normal state handler runs on the
; following TickFighter pass) and commit the AI for 18 frames.
AI_StartMove:
    sta AI_TMP
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_JOY,x
    stz FP+F_JOYPR,x
    lda AI_TMP
    and #$00FF.w
    jsr EnterState
    sep #$20
    .ACCU 8
    lda #18
    sta AI_TMP
    lda AI_SCANMODE
    cmp #2                              ; supers recover longer
    bne +
    lda #36
    sta AI_TMP
+   jmp AI_SetTimer

; Close-range normal: punch or kick, weak or strong, with a stronger bias
; when the foe is already inside the pushbox.
; Grounded anti-air answer when the move table has no DP/AA special:
; strong kick or strong punch through the normal pad path (the same path a
; human uses), so the state entry owns its animation and hitbox bookkeeping.
AI_DoAntiAir:
    rep #$20
    .ACCU 16
    ldx fofs
    stz FP+F_JOY,x
    stz FP+F_JOYPR,x
    sep #$20
    .ACCU 8
    stz AI_SCANMODE
    jsr AI_Rand
    and #$01
    beq AI_aa_strong_punch
    lda #$80.b                          ; strong kick (A)
    sta FP+F_JOY+1,x
    sta FP+F_JOYPR+1,x
    bra AI_aa_pressed
AI_aa_strong_punch:
    lda #$80.b                          ; strong punch (X)
    sta FP+F_JOY,x
    sta FP+F_JOYPR,x
AI_aa_pressed:
    lda #6
    sta AI_TMP
    jmp AI_SetTimer

; Personality-driven spacing.  The authored band is walking space, not a
; parking spot: the CPU keeps advancing until it reaches the inner edge of
; the band (or normal-attack range) instead of idling at the outer edge.
; The old per-frame "hold back" rolls made the CPU shuffle backwards in
; short taps; only a rare zoner reset remains, and it is committed by the
; hold timer so it cannot turn into a twitch.
AI_Move:
    lda AI_DIST
    cmp AI_ZLO
    bcc AI_move_close                  ; already inside the clinch band
    cmp #48
    bcc AI_move_close                  ; normal-attack range
    jmp AI_HoldFwd                     ; close the gap / walk the foe down
AI_move_close:
    lda AI_STYLE
    cmp #3
    beq AI_move_idle                   ; grappler wants the clinch
    cmp #1
    bne AI_move_idle                   ; everyone else holds the front line
    jsr AI_Rand
    and #$7F                           ; zoner gives ground very rarely
    beq AI_HoldBack
AI_move_idle:
    rts

; Hold toward / away from the opponent.
; X = AI_SIDE as a zero-extended word (0/1).  Never load AI_SIDE directly
; into X: the neighbouring AI_SCANMODE byte would become the high half.
AI_SideX:
    sep #$20
    .ACCU 8
    ldx #0
    lda AI_SIDE
    beq +
    inx
+   rts

AI_DirFwd:
    rep #$20
    .ACCU 16
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_FACING,x
    bmi +
    lda #$01.b
    bra ++
+   lda #$02.b
++  sta FP+F_JOY+1,x
    rts
AI_DirBack:
    rep #$20
    .ACCU 16
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_FACING,x
    bmi +
    lda #$02.b
    bra ++
+   lda #$01.b
++  sta FP+F_JOY+1,x
    rts

; Start a committed hold: direction plus a 14-frame timer.  Longer chunks
; make the walk read as continuous movement instead of little taps, and
; keep a guard up long enough to cover slow attacks.
AI_HoldFwd:
    jsr AI_DirFwd
    lda #14
    sta AI_TMP
    lda #2
    jmp AI_SetHold
AI_HoldBack:
    jsr AI_DirBack
    lda #14
    sta AI_TMP
    lda #1
    jmp AI_SetHold

; Hold back+down for fourteen frames: crouch guard against lows.
AI_HoldCrouch:
    jsr AI_DirBack
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_JOY,x
    ora #JOY_DN.w
    sta FP+F_JOY,x
    sep #$20
    .ACCU 8
    lda #14
    sta AI_TMP
    lda #3
    jmp AI_SetHold

; A = hold mode (1 back, 2 forward, 3 crouch back), AI_TMP = timer.
AI_SetHold:
    sta scr0
    lda AI_SIDE
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda scr0
    sta AI_HOLD1,x
    lda AI_TMP
    sta AI_TIMER1,x
    rts

; AI_TMP = timer, hold mode cleared (move/normal already started).
AI_SetTimer:
    lda AI_SIDE
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda AI_TMP
    sta AI_TIMER1,x
    stz AI_HOLD1,x
    rts

AI_Rand:
    sep #$20
    .ACCU 8
    lda rng
    eor framecnt
    eor AI_SIDE
    eor AI_LEVEL
    inc rng
    rts

; A = profile rate 0..255 -> level-scaled threshold 0..255.
; Level 1 keeps only a sliver of the authored personality (a few moves),
; level 8 is near-maximum and level 9 is full strength.  Uses Mul8
; (scr0 * scr1 -> scr2).
AI_Rate:
    sep #$20
    .ACCU 8
    sta scr0
    lda AI_LEVEL
    rep #$20
    .ACCU 16
    and #$00FF.w                       ; clear B before tax: a stale high
    cmp #10.w                          ;   byte would index past the table
    bcc +
    lda #9.w
+   tax
    sep #$20
    .ACCU 8
    lda.l AIRateScale,x
    sta scr1
    jsr Mul8
    sep #$20
    .ACCU 8
    lda scr2+1
    rts

AIRateScale:
    .db 0,4,24,56,88,120,152,184,224,255

; Probability that a neutral window even considers an offensive option.
; The per-category rate is applied afterwards, so low levels stay sparse
; even while the AI has many idle frames.
AIOffScale:
    .db 0,16,48,80,112,144,176,208,240,255

; Frames to wait after an offensive option before another one may start.
; Level 1 commits roughly every three seconds; level 8+ is almost continuous.
AIOffCDTab:
    .db 0,180,120,90,70,50,35,24,12,6

; Arm the per-side offense cooldown using the current level.
AI_SetOffCD:
    sep #$20
    .ACCU 8
    lda AI_LEVEL
    rep #$20
    .ACCU 16
    and #$00FF.w
    cmp #10.w
    bcc +
    lda #9.w
+   tax
    sep #$20
    .ACCU 8
    lda.l AIOffCDTab,x
    sta AI_TMP
    jsr AI_SideX
    lda AI_TMP
    sta AI_OFFCD,x
    rts


; Forward jump-in: arm the air attack, hold UP+forward while the takeoff
; squat samples the direction, then AI_air_fight presses the attack.
AI_JumpIn:
    jsr AI_SideX
    lda AI_JUMPCD,x
    bne JI_no
    lda #(AI_J_FWD|AI_J_ATK)
    sta AI_JUMP,x
    lda #6                             ; takeoff squat + rise before the press
    sta AI_AIRT,x
    lda #40
    sta AI_JUMPCD,x
    jsr AI_DirFwd
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_JOY,x
    ora #JOY_UP.w
    sta FP+F_JOY,x
    sep #$20
    .ACCU 8
JI_no:
    rts

; Neutral jump (used to clear projectiles).
AI_JumpUp:
    jsr AI_SideX
    stz AI_JUMP,x
    stz AI_AIRT,x
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_JOY,x
    ora #JOY_UP.w
    sta FP+F_JOY,x
    rts

; Nearest hostile projectile heading toward this fighter.  Carry set and
; AI_PDIST filled when one is inside 112 px.  Only hitbox sparks (bit7)
; owned by the other side (bit6) count.
AI_ProjThreat:
    rep #$20
    .ACCU 16
    stz AI_PDIST
    ldy #0
APT_loop:
    lda.w SPARKS+SPK_ANIM,y
    beq APT_next
    lda.w SPARKS+SPK_ATTR,y
    and #$0080.w
    beq APT_next
    lda.w SPARKS+SPK_ATTR,y
    and #$0040.w
    beq APT_owner0
    lda #1
    bra APT_owner
APT_owner0:
    lda #0
APT_owner:
    sep #$20
    .ACCU 8
    cmp AI_SIDE
    beq APT_next16
    rep #$20
    .ACCU 16
    lda.w SPARKS,y
    sta scr6
    ldx fofs
    lda FP+F_X,x
    xba
    and #$00FF.w
    sec
    sbc scr6
    beq APT_next16
    bmi APT_proj_right
    lda.w SPARKS+SPK_VX,y             ; projectile is left: needs vx > 0
    bmi APT_next16
    bra APT_abs
APT_proj_right:
    lda.w SPARKS+SPK_VX,y             ; projectile is right: needs vx < 0
    bpl APT_next16
APT_abs:
    lda FP+F_X,x
    xba
    and #$00FF.w
    sec
    sbc scr6
    bpl +
    eor #$FFFF.w
    inc a
+   cmp #112.w
    bcs APT_next16
    sta AI_PDIST
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_GRD,y              ; remember which postures stop it
    sta AI_PDIST+1                      ; high byte: distance fits in 112
    lda #1
    sec
    rts
APT_next16:
    rep #$20
    .ACCU 16
APT_next:
    tya
    clc
    adc #SPK_SIZE.w
    tay
    cpy #(SPK_SIZE*2).w
    bcc APT_loop
    lda #0
    sep #$20
    .ACCU 8
    clc
    rts

AICost100:
    .dw 0,100,200,300,400,500,600,700,800,900
    .dw 1000,1100,1200,1300,1400,1500,1600,1700,1800,1900
    .dw 2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000

; ---------------------------------------------------------------------------
; ---------------------------------------------------------------------------
; Hit sparks.  Two slots at SPARKS: x.w, y.w, animptr.w (tblbank, 0=free),
; frame index.b, ticks.b.  Generated anim record: .db nframes, .dw frameptr*n;
; frame record: .db ticks,ncells then ncells * (.db dx,dy / .dw tileindex)
; with absolute OBJ tile numbers in the static spark regions ($6C00/$7C00).
; ---------------------------------------------------------------------------

; Projectile contact: X = spark slot (acc8 caller). Owner flag bit6 picks
; the victim. Screen-space coordinates are checked against the victim's
; feet or torso before applying damage and impact feedback.
; Returns Z (beq) = miss / NZ = hit.
; Reflect an incoming projectile off an opponent's shield.  X = spark slot.
; ReflectTab (generated by tools/build_fight.py) lists every character/state
; window that can bounce a projectile: descriptor low word, state id, first
; and last active tick, then the forward-relative box x0,y0,x1,y1.  The box
; uses the fighter's feet as y=0, so it follows jumps automatically.
; Carry set when the projectile was bounced (owner and VX flipped).
ProjReflect:
    phx
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    and #$40.b                          ; bit6 = owner is P2
    beq +
    ldy #0                              ; owner P2 -> reflector is P1
    bra ++
+   ldy #FP2OFS.b                       ; owner P1 -> reflector is P2
++  sty fofs
    stz fofs+1
    txa                                 ; keep the spark slot in a word
    sta scr5
    stz scr5+1
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_CHAR,x
    sta scr0                            ; reflector descriptor low word
    lda #ReflectTab.w
    sta lptr
    sep #$20
    .ACCU 8
    lda #:ReflectTab.b
    sta lptr+2
    ldy #0
PR_scan:
    rep #$20
    .ACCU 16
    lda [lptr],y                        ; descriptor low word
    cmp #$FFFF.w
    bne +
    jmp PR_no
+   cmp scr0
    beq PR_row
    tya
    clc
    adc #9.w                            ; 2-byte descriptor + 7 box bytes
    tay
    bra PR_scan
PR_row:
    sep #$20
    .ACCU 8
    sty scr4                            ; row base (byte offset)
    stz scr4+1
    iny
    iny
    lda [lptr],y                        ; state id
    cmp FP+F_STATE,x
    beq +
    jmp PR_next
+
    iny
    lda [lptr],y                        ; first active tick
    sta scr1
    stz scr1+1
    iny
    lda [lptr],y                        ; last active tick (255 = no cutoff)
    sta scr2
    stz scr2+1
    rep #$20
    .ACCU 16
    lda FP+F_STIME,x
    cmp scr1
    bcs +
    jmp PR_next
+
    lda scr2
    cmp #$00FF.w
    beq PR_box
    lda FP+F_STIME,x
    cmp scr2
    bcc +
    jmp PR_next
+
PR_box:
    ldx fofs
    lda FP+F_X,x                        ; dx = proj.x - fighter.x
    xba
    and #$00FF.w
    sta scr0
    ldx scr5
    lda.w SPARKS,x
    sec
    sbc scr0
    sta scr2
    ldx fofs
    lda FP+F_FACING,x                   ; forward-relative
    bpl +
    lda scr2
    eor #$FFFF.w
    inc a
    sta scr2
+   sep #$20
    .ACCU 8
    ldy scr4
    iny
    iny
    iny
    iny
    iny                                 ; x0
    lda [lptr],y
    sta scr1
    stz scr1+1
    iny                                 ; y0
    lda [lptr],y
    sta scr3
    stz scr3+1
    iny                                 ; x1
    lda [lptr],y
    sta scr6
    stz scr6+1
    iny                                 ; y1
    lda [lptr],y
    sta scr0
    stz scr0+1
    lda scr3                            ; sign-extend the y edges
    bpl +
    lda #$FF.b
    sta scr3+1
+   lda scr0
    bpl +
    lda #$FF.b
    sta scr0+1
+   rep #$20
    .ACCU 16
    lda scr2                            ; dx >= x0?
    cmp scr1
    bcs +
    jmp PR_next
+
    lda scr6                            ; x1 >= dx?
    cmp scr2
    bcs +
    jmp PR_next
+
    ldx fofs
    lda FP+F_Y,x                        ; dy from the fighter's feet
    xba
    and #$00FF.w
    sta scr6
    lda #GROUND_Y.w
    sec
    sbc scr6
    sta scr6
    ldx scr5
    lda.w SPARKS+2,x
    sec
    sbc scr6
    sta scr2
    lda scr2                            ; dy >= y0?
    cmp scr3
    bpl +
    jmp PR_next
+
    lda scr0                            ; y1 >= dy?
    cmp scr2
    bcs +
    jmp PR_next
+
    sep #$20
    .ACCU 8
    ldx scr5
    lda.w SPARKS+SPK_ATTR,x
    eor #$50.b                          ; new owner + mirrored travel
    sta.w SPARKS+SPK_ATTR,x
    rep #$20
    .ACCU 16
    lda.w SPARKS+SPK_VX,x
    eor #$FFFF.w                        ; send it back
    inc a
    sta.w SPARKS+SPK_VX,x
    plx
    sec
    rts
PR_next:
    rep #$20
    .ACCU 16
    lda scr4
    clc
    adc #9.w
    tay
    jmp PR_scan
PR_no:
    plx
    clc
    rts

ProjHit:
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    and #$80.b                          ; hitbox sparks only: cosmetic
    bne +                               ;   sparks/explods never hit
    jmp PH_miss
+
    lda.w SPARKS+SPK_ATTR,x
    and #$40.b                          ; bit6 = owner is P2
    beq +
    lda #0                            ; owner P2 -> victim is P1
    bra ++
+   lda #FP2OFS.b                     ; owner P1 -> victim is P2
++  sta scr6                          ; victim struct offset
    stz scr6+1                          ; rendering may leave flags in high byte
    rep #$20
    .ACCU 16
    ldy scr6
    lda FP+F_STATE,y                  ; victim already down is a pass-through
    and #$00FF.w                      ;   (no hitting a knocked-down foe), but
    cmp #S_DOWN.w                     ;   a victim still in hitstun can be
    bne +                             ;   juggled by a projectile: that is
    jmp PH_miss                       ;   what lets cr.HP combo into a shot
+
    lda FP+F_INVUL,y                  ; invulnerable: flies through
    and #$00FF.w
    beq +
    jmp PH_miss
+
    lda #24.w
    sta scr5
.IFNDEF BASE4
    lda.w SPARKS+SPK_ANIM,x
    cmp #terryProjFxAnim.w
    beq PR_wide
    cmp #terryProjFx2Anim.w             ; Power Geyser's stationary pillar
    bne +
PR_wide:
    ; Power Wave extends ~24px from its origin and the geyser pillar is
    ; ~32px wide. Include the opponent's ~16px body radius so their leading
    ; edges connect on first contact.
    lda #40.w
    sta scr5
+
.ENDIF
    lda.w SPARKS,x                    ; current effect center vs. victim
    sta scr4                          ; keep signed/offscreen X; never wrap
    lda FP+F_X,y
    xba
    and #$00FF.w
    sec
    sbc scr4                          ; victim.x - proj.x
    bpl +
    eor #$FFFF.w
    inc a
+   cmp scr5
    bcc +
    jmp PH_miss
+
    ; Floor waves check the victim's feet; higher effects check the torso.
    ; This lets jumps evade floor waves while ordinary hits need no exact
    ; F_Y == 0 match.
    lda.w SPARKS+2,x
    cmp #(GROUND_Y-4).w
    bcc PH_body_height
    lda FP+F_Y,y
    xba
    and #$00FF.w
    sta scr5
    lda #GROUND_Y.w
    sec
    sbc scr5
    sta scr5
    lda.w SPARKS+2,x
    sec
    sbc scr5
    bpl +
    eor #$FFFF.w
    inc a
+   cmp #34.w
    bcc +
    jmp PH_miss
+
    bra PH_hit
PH_body_height:
    lda FP+F_Y,y
    xba
    and #$00FF.w
    sta scr5
    lda #GROUND_Y.w
    sec
    sbc scr5
    sec
    sbc #32.w
    sta scr5
    lda.w SPARKS+2,x
    sec
    sbc scr5
    bpl +
    eor #$FFFF.w
    inc a
+   cmp #36.w
    bcc +
    jmp PH_miss
+
PH_hit:
    ; --- a defender holding back blocks a guardable shot ---
    lda scr6
    sta fofs
    stz fofs+1
    lda.w SPARKS+SPK_GRD,x              ; H/M/L/A mask from ProjTab
    sta scr5
    phx
    jsr GuardCheck
    sta scr3
    plx
    lda scr3
    beq +
    jmp PH_guard
+
    ; --- hit: dmg + normal hitstun on the victim ---
    sep #$20
    .ACCU 8
    lda scr6
    sta fofs                          ; victim offset for EnterState
    stz fofs+1
    rep #$20
    .ACCU 16
    phx                                 ; EnterState may clobber both indexes
    lda scr6
    pha                                 ; EnterState uses the DP scratch area
    lda #S_HIT
    jsr EnterState                    ; EnterState zeroes slide/htmr, so
    pla
    tay                                 ; restore the hit victim offset
    plx                                 ; restore projectile slot base
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    jsr SurvTrackProj                     ; survivor: projectile finish type
    rep #$20
    .ACCU 16
    phx                                   ; PracBlock wants the victim in X
    tyx
    sep #$20
    .ACCU 8
    jsr PracBlock
    rep #$20
    .ACCU 16
    plx
    bcs PH_dmg_done                       ; practice: no projectile damage
    lda.w SPARKS+SPK_AY,x
    and #$00FF.w                      ; high byte is a sound ID, not damage
    sta scr4
    lda FP+F_HP,y
    sec
    sbc scr4
    bpl +
    lda #0
+   sta FP+F_HP,y
PH_dmg_done:
    lda #6<<8.w                       ; pushback like a light hit, away
    bit.w SPARKS+SPK_VX,x             ;   along the projectile's heading
    bpl +
    eor #$FFFF.w
    inc a
+   sta FP+F_VX,y
    lda FP+F_HP,y                     ; a killing shot must knock the victim
    beq PH_ko                         ;   down, not leave it on its feet
    sep #$20
    .ACCU 8
    lda #8.b                          ; brief projectile hitstun, no long freeze
    sta FP+F_HTIMER,y
    lda #5.b
    sta FP+F_SLIDE,y
    bra PH_fx
PH_ko:
    tya                                ; victim offset for the tail helper
    sta fofs
    phx                                ; the spark slot still owns X
    jsr KO_ForceDown                   ; launch + lie down
    plx
PH_fx:
    ; Play the launch state's HitDef sound, then replace this projectile with
    ; an impact spark. Freeing its slot first guarantees the spark even when
    ; the other effect slot is occupied.
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_AY+1,x
    cmp #$FF.b
    beq +
    jsr SfxPlay
+   rep #$20
    .ACCU 16
    lda.w SPARKS,x
    and #$00FF.w
    sta scr0
    lda.w SPARKS+2,x
    sec
    sbc #24.w
    sta scr1
    stz.w SPARKS+SPK_ANIM,x
    stz.w SPARKS+SPK_ANIM+1,x
    phx
    lda #0                                ; generic impact spark
    jsr SparkSpawnAt
    plx
    sep #$20
    .ACCU 8
    lda #1
    rts

; Blocked projectile: chip damage, guard spark/sound and guard-hit stun.
; scr3 = ANIM_GHIT_* slot from GuardCheck, scr6 = victim, X = spark slot.
; The shot is consumed (KOF98 fireballs vanish on block) and replaced by
; the guard spark; the slot base is restored for TickSpark's loop.
PH_guard:
    rep #$20
    .ACCU 16
    phx                                 ; TickSpark advances from this slot
    lda scr3
    pha                                 ; survives SparkSpawnAt's scratch use
    lda.w SPARKS,x
    sta scr0                            ; impact position
    lda.w SPARKS+2,x
    sta scr1
    lda.w SPARKS+SPK_VX,x
    sta scr5                            ; pushback direction
    lda.w SPARKS+SPK_AY,x
    and #$00FF.w
    sta scr4                            ; full damage
    lda.w SPARKS+SPK_ATTR,x
    and #$0040.w                        ; bit6 = owner is P2
    beq +
    lda #0
    bra ++
+   lda #FP2OFS.w
++  sta scr2                            ; owner offset for the power award
    sep #$20
    .ACCU 8
    lda #SFX_GUARD.b
    jsr SfxPlay
    rep #$20
    .ACCU 16
    stz.w SPARKS+SPK_ANIM,x             ; blocked shot is consumed
    stz.w SPARKS+SPK_ANIM+1,x
    lda scr1
    sec
    sbc #24.w
    sta scr1
    lda #1                              ; SparkGuard
    jsr SparkSpawnAt
    ; chip damage: an eighth of the shot, at least 1, never a K.O.
    lda scr4
    lsr a
    lsr a
    lsr a
    bne +
    lda #1
+   sta scr4
    ldx scr6
    jsr PracBlock
    rep #$20
    .ACCU 16
    bcs PH_gdmg_done                    ; practice: no chip damage either
    ldx scr6
    lda FP+F_HP,x
    sec
    sbc scr4
    bpl +
    lda #1
+   bne ++
    lda #1
++  sta FP+F_HP,x
PH_gdmg_done:
    ; meter: guard gain for the victim, attack gain for the owner
    lda #19.w
    ldx scr6
    jsr AddPower
    lda #31.w
    ldx scr2
    jsr AddPower
    ; pushback away along the shot's heading, like a light hit
    lda #6<<8.w
    bit scr5
    bpl +
    eor #$FFFF.w
    inc a
+   ldx scr6
    sta FP+F_VX,x
    ; guard-hit stun + pushback window (EnterState zeroes both)
    ldx scr6
    stx fofs
    jsr GuardState
    jsr EnterState
    rep #$20
    .ACCU 16
    pla                                 ; ANIM_GHIT_* slot
    jsr SetAnimSlot
    sep #$20
    .ACCU 8
    ldx fofs
    lda #10.b
    sta FP+F_HTIMER,x
    lda #4.b
    sta FP+F_SLIDE,x
    plx                                 ; restore the spark slot base
    rep #$20
    .ACCU 16
    lda #1
    rts

PH_miss:
    rep #$20
    .ACCU 16
    lda #0
    rts

; Places the character's own projectile clip at the fighter's torso.
; box0/box1 overlap from HitOne's test (both boxes still live here).
; Clobbers scr0/scr2/sptr, X and Y; keeps scr3/scr4/scr5/scr6 intact.
; FUSION projectile: scr0 = vx 8.8 magnitude, scr1 = dmg.b|anim<<8,
; scr3 = guard mask (H/M/L/A<<4), fofs = caster.  Rides a spark slot;
; SPK_ATTR bit7 = has hitbox, bit6 = owner is P2; SPK_AY carries the damage.
; Projectiles loop their compact flame frame until they hit or reach the
; 90-tick lifetime cap.
; Spawn a state's projectile only when the launch animation reaches the
; configured release frame.  ProjTab row (6B): vx.w, dmg.b, hitsfx.b,
; guard.b (H/M/L/A<<4), present.b.  Present bits: 0 = shot exists, 1 =
; fixed upper-torso height, 2 = alternate ProjFx clip, 3-7 = 1-based
; release frame (0 keeps the engine default).  Called from AnimSetFrame;
; F_PROJDONE prevents a ChangeAnim/loop from firing twice.
ProjTrySpawn:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_PROJDONE,x
    and #$00FF.w
    beq PTS_first
    jmp PTS_out                         ; the expanded release-row code put
PTS_first:                              ;   PTS_out beyond a short branch
    ldy #CH_PROJTAB.w
    ldx #lptr
    jsr CharPtr                         ; lptr -> ProjTab
    ldx fofs
    lda FP+F_STATE,x
    and #$00FF.w
    sta scr2
    asl a
    clc
    adc scr2
    asl a                               ; 6-byte rows
    tay
    lda [lptr],y                        ; vx magnitude (zero is stationary)
    sta scr0
    iny
    iny
    lda [lptr],y                        ; dmg.b | hitsfx.b<<8
    sta scr1
    iny
    iny
    stz.w RT_PROJAIR                    ; no per-shot height override by default
    stz.w RT_PROJREL                    ; no per-shot release override yet
    stz.w RT_PROJFX2                    ; use the character's primary clip
    lda [lptr],y                        ; guard.b | present.b<<8
    sta scr3
    xba
    and #$00FF.w                        ; present | air flag
    sta scr4
    and #$01.w                          ; bit0 = the shot exists
    beq PTS_out
    lda scr4
    and #$02.w                          ; bit1 = spawn at fixed upper torso
    beq +
    lda #1.w
    sta.w RT_PROJAIR
+   lda scr4
    and #$04.w                          ; bit2 = alternate ProjFx clip
    beq +
    lda #1.w
    sta.w RT_PROJFX2
+   lda scr4
    and #$F8.w                          ; bits3-7 = 1-based release frame
    beq +
    lsr a
    lsr a
    lsr a
    sta.w RT_PROJREL
+   lda scr3
    and #$00FF.w                        ; guard mask
    sta scr3
    ; Release early in the launch animation: the third frame (or the last
    ; frame of a shorter clip).  Waiting for the penultimate frame added the
    ; whole startup of the imported anim, and its long recovery frames pushed
    ; the shot past the normal's hitstun, so cr.HP could never combo into it.
    ; A row may pin a later source frame for stationary supers whose effect
    ; appears on the ground punch (Terry's Power Geyser: AnimElem 7).
    ldx fofs
    lda.w RT_PROJREL
    bne PTS_rel_have
    lda FP+F_NFR,x
    and #$00FF.w
    dec a                               ; last frame
    cmp #2.w
    bcc PTS_rel_short
    lda #2.w                            ; third frame (0-based: 2)
PTS_rel_short:
    inc a                               ; keep the value 1-based
    sta.w RT_PROJREL
PTS_rel_have:
    lda.w RT_PROJREL
    dec a
    cmp FP+F_FRAME,x
    bne PTS_out
    .ACCU 16
    jsr ProjSpawn
    bcc PTS_out                         ; no slot: retry on the next frame
    sep #$20
    .ACCU 8
    ldx fofs
    lda #1
    sta FP+F_PROJDONE,x
PTS_out:
    rep #$20
    .ACCU 16
    rts

ProjSpawn:
    rep #$20
    .ACCU 16
    ldx #0
    lda.w SPARKS+SPK_ANIM,x
    beq +
    ldx #SPK_SIZE
    lda.w SPARKS+SPK_ANIM,x
    beq +
    ; A projectile may evict a cosmetic spark, but never another active
    ; projectile. This prevents a hitbox from silently disappearing.
    ldx #0
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    bpl PS_slot
    ldx #SPK_SIZE
    lda.w SPARKS+SPK_ATTR,x
    bpl PS_slot
    rep #$20
    .ACCU 16
    inc.w RT_PROJDROP
    clc
    rts
PS_slot:
    rep #$20
    .ACCU 16
+   ldy fofs
    lda FP+F_X,y                        ; positions are 8.8 fixed point
    pha
    lda FP+F_FACING,y
    bmi +                               ; left-facing: spawn left of caster
    pla
    clc
    adc #14<<8.w
    bra ++
+   pla
    sec
    sbc #14<<8.w
++  xba                                ; sparks are stored in screen pixels
    and #$00FF.w
    sta.w SPARKS,x
    lda FP+F_Y,y                        ; convert world height to screen Y
    xba
    and #$00FF.w
    sta scr2
    lda #GROUND_Y.w
    sec
    sbc scr2
    sec
    sbc #40.w                           ; mid torso, ~40px above the floor
    sta.w SPARKS+2,x
    rep #$20
    .ACCU 16
    phx
    ldx #sptr.w
    ldy #CH_PROJFXTAB.w
    jsr CharPtr                         ; char-specific anim pointer table
    plx                                 ; restore spark slot base
    sep #$20
    .ACCU 8
    lda #:ProjFxGlobal
    sta sptr+2
    rep #$20
    .ACCU 16
    lda.w RT_PROJAIR                    ; per-shot override (air Shippuu Ken)
    and #$00FF.w
    beq PS_readmode
    lda #2.w
    bra PS_havemode
PS_readmode:
    ; ProjFxTab header: .dw primary anim, .dw alternate anim, .db height.
    ; The height byte is always at offset 4; reading offset 2 here would
    ; pick the low byte of the second anim pointer (non-zero), which sent
    ; every primary shot to the floor (hadouken at GROUND_Y instead of the
    ; caster's torso).  Ground rows keep mode 1 and are unaffected.
    ldy #4
    lda [sptr],y                        ; spawn-height mode
    and #$00FF.w                        ;   0 = caster torso, 1 = floor,
PS_havemode:
    beq +                               ;   2 = fixed upper torso (air shots)
    cmp #2.w
    bne PS_ground
    lda #(GROUND_Y-60).w                ; airborne throw: keep the ball at a
    sta.w SPARKS+2,x                    ;   height a standing victim can hit
    bra +
PS_ground:
    lda #GROUND_Y.w
    sta.w SPARKS+2,x
+
    ldy #0
    lda.w RT_PROJFX2                    ; 0 = primary ProjFxAnim,
    and #$0001.w                        ; 1 = the alternate geyser clip
    beq +
    ldy #2
+   lda [sptr],y
    sta.w SPARKS+SPK_ANIM,x
    sep #$20
    .ACCU 8
    lda #:ProjFxGlobal
    sta.w SPARKS+SPK_BANK,x
    rep #$20
    .ACCU 16
    lda scr0                            ; vx magnitude -> signed by facing
    ldy fofs
    lda FP+F_FACING,y
    bmi +
    lda scr0
    bra ++
+   lda scr0
    eor #$FFFF.w
    inc a
++  sta.w SPARKS+SPK_VX,x
    stz.w SPARKS+SPK_VY,x
    lda scr1                            ; dmg byte -> SPK_AY low
    and #$00FF.w
    sta.w SPARKS+SPK_AY,x
    sep #$20
    .ACCU 8
    lda scr1+1                          ; launch state's HitDef sound
    sta.w SPARKS+SPK_AY+1,x
    lda scr3                            ; per-shot guard mask (H/M/L/A<<4)
    sta.w SPARKS+SPK_GRD,x
    stz.w SPARKS+SPK_FIDX,x             ; begin at frame 0
    rep #$20
    .ACCU 16
    lda.w SPARKS+SPK_ANIM,x             ; anim rec: byte0 = nframes
    sta sptr
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_BANK,x
    sta sptr+2
    rep #$20
    .ACCU 16
    ldy #1                              ; first frame pointer -> ticks
    lda [sptr],y
    sta sptr
    sep #$20
    .ACCU 8
    lda [sptr]
    sta.w SPARKS+SPK_FTIM,x
    lda #90.b                           ; 1.5 seconds max flight, even on whiff
    sta.w SPARKS+SPK_TTL,x
    lda #$80.b                          ; projectile flag; OAM palette is per side
    ldy fofs
    cpy #FP2OFS.w                       ; Y remains 16-bit even with acc8
    bne +
    ora #$40.b                          ; owner = P2
+   sta.w SPARKS+SPK_ATTR,x
    sep #$20
    .ACCU 8
    lda.w RT_PROJFX2
    and #$01.b
    beq +
    lda.w SPARKS+SPK_ATTR,x
    ora #$08.b                          ; bit3 = one-shot clip (no loop)
    sta.w SPARKS+SPK_ATTR,x
+   ldy fofs
    lda FP+F_FACING+1,y                 ; bit4: projectile art faces left
    bpl +
    lda.w SPARKS+SPK_ATTR,x
    ora #$10.b
    sta.w SPARKS+SPK_ATTR,x
+   ldy fofs
    lda FP+F_STATE,y                     ; remember whether the launch state
    jsr IsSpecialState                    ;   was a special/super (survivor)
    bcc +
    lda.w SPARKS+SPK_ATTR,x
    ora #$20.b                           ; bit5 = special/super projectile
    sta.w SPARKS+SPK_ATTR,x
+   rep #$20
    .ACCU 16
    sec
    rts

SparkSpawn:
    rep #$20
    .ACCU 16
    pha
    ldx #0
    lda.w SPARKS+SPK_ANIM,x
    beq +
    ldx #SPK_SIZE
    lda.w SPARKS+SPK_ANIM,x
    beq +
    pla
    rts                                 ; both slots busy: drop it
+   ; x = (max(box0.x0,box1.x0) + min(box0.x1,box1.x1)) / 2
    lda box0
    cmp box1
    bcs +
    lda box1
+   sta scr0
    lda box0+4
    cmp box1+4
    bcc +
    lda box1+4
+   clc
    adc scr0
    lsr a
    sta scr0
    lda box0+2                          ; same for y
    cmp box1+2
    bcs +
    lda box1+2
+   sta scr1
    lda box0+6
    cmp box1+6
    bcc +
    lda box1+6
+   clc
    adc scr1
    lsr a
    sta scr1
SS_place:                               ; X = free slot, scr0/scr1 = pos
    lda scr0
    sta.w SPARKS,x
    lda scr1
    sta.w SPARKS+2,x
    stx scr3
    pla
    asl a
    tay
    lda #SparkAnimTab
    sta sptr
    sep #$20
    .ACCU 8
    lda tblbank
    sta sptr+2
    rep #$20
    .ACCU 16
    lda [sptr],y                        ; anim record ptr
    ldx scr3
    sta.w SPARKS+SPK_ANIM,x
    lda.w SPARKS+SPK_ANIM,x             ; reload anim ptr
    inc a                               ; -> frame pointer table
    sta sptr
    lda [sptr]                          ; frame0 record ptr
    sta sptr
    sep #$20
    .ACCU 8
    lda [sptr]                          ; frame0 ticks
    ldx scr3
    stz.w SPARKS+SPK_FIDX,x
    sta.w SPARKS+SPK_FTIM,x
    rep #$20
    .ACCU 16
    stz.w SPARKS+SPK_VX,x               ; hit sparks never move
    stz.w SPARKS+SPK_VY,x
    stz.w SPARKS+SPK_AY,x
    stz.w SPARKS+SPK_TTL,x              ; ttl=0: anim end frees the slot
    sep #$20
    .ACCU 8
    lda #$34.b                          ; prio 3, OBJ palette 2
    sta.w SPARKS+SPK_ATTR,x
    rep #$20
    .ACCU 16
    rts

; SparkSpawnAt: same as SparkSpawn but the position comes from the caller:
; A(16) = anim index, scr0 = x, scr1 = y (integer screen pixels).
SparkSpawnAt:
    rep #$20
    .ACCU 16
    pha
    ldx #0
    lda.w SPARKS+SPK_ANIM,x
    beq SS_place
    ldx #SPK_SIZE
    lda.w SPARKS+SPK_ANIM,x
    beq SS_place
    pla
    rts                                 ; both slots busy: drop it

; ExplodSpawn: spawn a compiled Explod (char ExpTab row) into a spark slot.
; A(8) = row index; fofs = owning fighter.  Row = 16 bytes:
;   +0 anim idx, +1 ttl, +2 attr, +3 anchor (bit0: y rel. to ground)
;   +4 xoff.w, +6 yoff.w, +8 vx.w, +10 vy.w, +12 ay.w  (vel/accel 8.8)
; Uses lptr, not sptr: the ActOp row scan keeps its cursor in sptr, and an
; Explod row can precede VelSet/VelMul rows (Kyo/Iori Oniyaki), which would
; otherwise be skipped and leave the move sliding at full speed.
ExplodSpawn:
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    asl a
    asl a
    asl a                               ; *16 = row size
    sta scr3                            ; row offset
    ldx #0
    lda.w SPARKS+SPK_ANIM,x
    beq XS_slot
    ldx #SPK_SIZE
    lda.w SPARKS+SPK_ANIM,x
    beq XS_slot
    ; Both slots busy: reuse the character-effect slot. This keeps Oniyaki's
    ; crest visible by replacing its rising pillar instead of dropping it.
XS_slot:
    stx scr6                            ; slot base
    ldx #lptr
    ldy #CH_EXPTAB
    jsr CharPtr                         ; lptr = char's ExpTab (tblbank)
    lda lptr
    clc
    adc scr3
    sta lptr                            ; -> this Explod row
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_TBANK,x                    ; per-char tables live in F_TBANK
    sta lptr+2                          ;   (ExpTab), not tblbank
    ldy #0
    lda [lptr],y                        ; anim index
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    tay
    lda #SparkAnimTab
    sta cptr
    sep #$20
    .ACCU 8
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    lda [cptr],y                        ; anim record ptr
    ldx scr6
    sta.w SPARKS+SPK_ANIM,x
    inc a                               ; -> frame pointer table
    sta cptr
    lda [cptr]                          ; frame0 record ptr
    sta cptr
    sep #$20
    .ACCU 8
    lda [cptr]                          ; frame0 ticks
    ldx scr6
    sta.w SPARKS+SPK_FTIM,x
    stz.w SPARKS+SPK_FIDX,x
    ldy #1
    lda [lptr],y                        ; ttl (0 = freed at anim end)
    sta.w SPARKS+SPK_TTL,x
    iny
    lda [lptr],y                        ; attr byte
    sta.w SPARKS+SPK_ATTR,x
    iny
    lda [lptr],y                        ; anchor flags
    sta scr5
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_FACING,x                   ; facing word (+1/-1)
    sta scr4
    ldy #4
    lda [lptr],y                        ; xoff in facing space
    ldx scr4
    bpl +
    eor #$FFFF.w
    inc a
+   ldx fofs
    sta scr0                            ; retain integer x offset
    lda FP+F_X,x
    xba                                 ; fighter X is 8.8; sparks store px
    and #$00FF.w
    clc
    adc scr0                            ; spawn x = fighter x + facing*xoff
    ldx scr6
    sta.w SPARKS,x
    lda scr5
    and #$0001.w                        ; anchor bit0: ground-relative y
    bne XS_ground
    ldx fofs
    lda #GROUND_Y.w
    sec
    sbc FP+F_Y,x                        ; feet screen y
    bra XS_yset
XS_ground:
    lda #GROUND_Y.w
XS_yset:
    ldy #6
    clc
    adc [lptr],y                        ; + yoff (signed)
    ldx scr6
    sta.w SPARKS+2,x
    ldy #8
    lda [lptr],y                        ; vx in facing space
    ldx scr4
    bpl +
    eor #$FFFF.w
    inc a
+   sta.w SPARKS+SPK_VX,x
    ldy #10
    lda [lptr],y
    sta.w SPARKS+SPK_VY,x
    ldy #12
    lda [lptr],y
    sta.w SPARKS+SPK_AY,x
    sep #$20                            ; ActOp callers expect acc8
    .ACCU 8
    rts

; Advance both spark/explod slots by one tick; frees finished slots.
; Explods also integrate velocity+accel (8.8 fixed point) and expire when
; their removetime ttl hits zero (ttl 0 = freed by the anim end instead).
TickSpark:
    rep #$20
    .ACCU 16
    jsr ProjClash
    ldx #0
TS_slot:
    lda.w SPARKS+SPK_ANIM,x
    bne +
        jmp TS_next
+   sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_TTL,x              ; removetime countdown
    beq +
    dec a
    sta.w SPARKS+SPK_TTL,x
    bne +
    stz.w SPARKS+SPK_ANIM,x             ; expired: free the slot
    stz.w SPARKS+SPK_ANIM+1,x
    jmp TS_next8
+   rep #$20
    .ACCU 16
    lda.w SPARKS+SPK_VX,x               ; px += vx>>8 (signed 8.8)
    xba
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   clc
    adc.w SPARKS,x
    sta.w SPARKS,x
    lda.w SPARKS+SPK_VY,x               ; py += vy>>8 ; vy += ay
    xba
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   clc
    adc.w SPARKS+2,x
    sta.w SPARKS+2,x
    lda.w SPARKS+SPK_ATTR,x             ; projectile AY stores damage, not gravity
    and #$0080.w
    bne TS_no_gravity
    lda.w SPARKS+SPK_VY,x
    clc
    adc.w SPARKS+SPK_AY,x
    sta.w SPARKS+SPK_VY,x
TS_no_gravity:
    sep #$20                            ; FUSION: projectile flag -> range
    .ACCU 8                             ;   check vs the victim's hurtbox
    lda.w SPARKS+SPK_ATTR,x
    bpl +
    jsr ProjReflect                    ; opponent shield: bounce it back
    bcc +
    jmp TS_next8                       ; reflected this tick
+   jsr ProjHit
    beq +                               ; miss: keep flying
    ; ProjHit already replaced the projectile with its impact spark.
    jmp TS_next8
+   sep #$20
    .ACCU 8
    dec.w SPARKS+SPK_FTIM,x
    bne TS_next8
    inc.w SPARKS+SPK_FIDX,x             ; next frame
    rep #$20
    .ACCU 16
    lda.w SPARKS+SPK_ANIM,x
    sta sptr
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    and #$80.b
    beq TS_global_bank
    lda.w SPARKS+SPK_BANK,x
    bra TS_bank_ready
TS_global_bank:
    lda tblbank
TS_bank_ready:
    sta sptr+2
    lda [sptr]                          ; nframes
    cmp.w SPARKS+SPK_FIDX,x
    bne TS_frame_load
    lda.w SPARKS+SPK_ATTR,x
    and #$80.b                          ; projectile: loop its flame until hit/TTL
    beq TS_anim_end
    lda.w SPARKS+SPK_ATTR,x
    and #$08.b                          ; one-shot projectile: free at anim end
    bne TS_anim_end
    stz.w SPARKS+SPK_FIDX,x
    bra TS_frame_load
TS_anim_end:
    stz.w SPARKS+SPK_ANIM,x             ; animation finished
    stz.w SPARKS+SPK_ANIM+1,x
    jmp TS_next8
TS_frame_load:
    rep #$20
    .ACCU 16
    lda.w SPARKS+SPK_FIDX,x
    and #$00FF.w
    asl a
    inc a                               ; anim + 1 + fidx*2
    tay
    lda [sptr],y                        ; frame record ptr
    sta sptr
    sep #$20
    .ACCU 8
    lda [sptr]                          ; frame ticks
    sta.w SPARKS+SPK_FTIM,x
TS_next8:
    rep #$20
    .ACCU 16
TS_next:
    txa
    clc
    adc #SPK_SIZE
    tax
    cmp #SPK_SIZE*2
    bcc +
    rts
+   jmp TS_slot

; ---------------------------------------------------------------------------
; Retire every afterimage snapshot.  FightTick normally ages these slots in
; GhostTick, but the ROUND/winner/select screens do not run it: without this
; the last trail stays in GHBUF and BuildOam keeps painting its cells over
; the intermission art.
ClearGhosts:
    rep #$20
    .ACCU 16
    ldx #0
    txa
-   sta.w GHBUF,x
    inx
    inx
    cpx #GHP2*2.w
    bne -
    sep #$20
    .ACCU 8
    rts

; ---------------------------------------------------------------------------
; Afterimage trail: while F_TFLAGS bit2 is set a snapshot of the current
; metasprite is pushed every 4 ticks; each slot self-expires via its ttl so
; the trail fades out a few frames after the move ends.  Slot layout at
; GHBUF (+GHP2 for P2), 12 bytes each, slot0 = newest:
;   +0 x.w, +2 y.w, +4 meta.w, +6 tilepg, +7 flip, +8 xoff, +9 yoff, +10 ttl
GhostTick:                              ; fofs = fighter; called once/tick
    rep #$20
    .ACCU 16
    ldx fofs
    txa
    beq +
    lda #GHP2.w
+   tax                                 ; X = ghost slot base (0 or GHP2)
    sep #$20
    .ACCU 8
    lda.w GHBUF+10,x                    ; ttl decay: expired slots free
    beq +                               ;   themselves for the renderer
    dec a
    sta.w GHBUF+10,x
    bne +
    stz.w GHBUF+4,x                     ; meta is a WORD: clear both bytes or
    stz.w GHBUF+5,x                     ;   the stale hi byte draws garbage
+   lda.w GHBUF+22,x
    beq +
    dec a
    sta.w GHBUF+22,x
    bne +
    stz.w GHBUF+16,x
    stz.w GHBUF+17,x
+   ldy fofs
    lda FP+F_TFLAGS,y                   ; push only while the trail is on
    and #$04.b
    beq GT_out
    lda framecnt
    and #$03.b
    bne GT_out
    jsr GhostPush
GT_out:
    rep #$20
    .ACCU 16
    rts

GhostPush:                              ; shift slot0->1, store current pose
    rep #$20
    .ACCU 16
    ldx fofs
    txa
    beq +
    lda #GHP2.w
+   tax
    lda.w GHBUF+0,x
    sta.w GHBUF+12,x
    lda.w GHBUF+2,x
    sta.w GHBUF+14,x
    lda.w GHBUF+4,x
    sta.w GHBUF+16,x
    lda.w GHBUF+6,x
    sta.w GHBUF+18,x
    lda.w GHBUF+8,x
    sta.w GHBUF+20,x
    lda.w GHBUF+10,x
    sta.w GHBUF+22,x
    ldy fofs
    lda FP+F_X,y
    sta.w GHBUF+0,x
    lda FP+F_Y,y
    sta.w GHBUF+2,x
    lda FP+F_META,y
    sta.w GHBUF+4,x
    sep #$20
    .ACCU 8
    lda FP+F_TILEPG,y
    sta.w GHBUF+6,x
    lda FP+F_FLAGS,y                      ; resolve flip = anim hflip ^ facing
    and #$01.b
    sta scr0
    lda FP+F_FACING+1,y
    bpl +
    lda scr0
    eor #$01.b
    sta scr0
+   lda scr0
    sta.w GHBUF+7,x
    lda FP+F_XOFF,y
    sta.w GHBUF+8,x
    lda FP+F_YOFF,y
    sta.w GHBUF+9,x
    lda #8.b
    sta.w GHBUF+10,x
    ; Remember which upload generation owns this physical tile page.
    lda.w GHBUF+6,x
    beq +
    lda #1.b
+   sta scr0
    ldy fofs
    cpy #0.w
    beq +
    lda scr0
    clc
    adc #2.b
    sta scr0
+   phx
    ldx scr0
    lda.w RT_GHOSTGEN,x
    plx
    sta.w GHBUF+11,x
    rep #$20
    .ACCU 16
    rts

; Emit ghost cells behind the fighter.  Same metasprite/tile-page math as
; DrawFighter, but cells carry the dim OBJ palette (+3 entries).
DrawGhost:
    rep #$20
    .ACCU 16
    ldx fofs
    txa
    beq +
    lda #GHP2.w
+   sta sidx
    stz gk
DG_slot:
    ldx sidx
    lda.w GHBUF+4,x                       ; meta ptr; 0 = slot free
    bne +
        jmp DG_next
+   sep #$20
    .ACCU 8
    lda.w GHBUF+6,x                       ; reject snapshots whose tile page
    beq +                                 ; has since been overwritten
    lda #1.b
+   sta scr0
    ldy fofs
    cpy #0.w
    beq +
    lda scr0
    clc
    adc #2.b
    sta scr0
+   phx
    ldx scr0
    lda.w RT_GHOSTGEN,x
    plx
    cmp.w GHBUF+11,x
    beq +
    stz.w GHBUF+4,x
    stz.w GHBUF+5,x
    rep #$20
    .ACCU 16
    jmp DG_next
+   rep #$20
    .ACCU 16
    lda.w GHBUF+4,x
    sta lptr
    ldx fofs
    jsr MetaBankX
    sta lptr+2
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    lda FP+F_CHAR,x
    sta cptr
    sep #$20
    .ACCU 8
    lda #$30.b                          ; per-side OBJ palette (P1 pal0,
    cpx #0                              ;   P2 pal1); palette +3 = dim copy
    beq +
    lda #$32.b
+   clc
    adc #$06.b
    sta aofs
    rep #$20
    .ACCU 16
    lda [lptr]                            ; ncells
    sta scr4
    bne +
    jmp DG_next                           ; empty ghost: skip shared cell loop
+
    lda lptr
    clc
    adc #9
    sta lptr                              ; -> first cell
    ldx sidx
    lda.w GHBUF+6,x                       ; tile page at push time
    and #$00FF.w
    sta pbase
    ldx fofs
    beq +
    lda pbase
    clc
    adc #P2TILEOF.w
    sta pbase
+   ldx sidx
    lda.w GHBUF+0,x                       ; sx/sy from the snapshot
    xba
    and #$00FF.w
    sta scr1
    lda.w GHBUF+2,x
    xba
    and #$00FF.w
    sta scr2
    lda #GROUND_Y.w
    sec
    sbc scr2
    sta scr2
    sep #$20
    .ACCU 8
    lda.w GHBUF+7,x                       ; resolved flip
    sta scr0
    lda.w GHBUF+8,x                       ; anim offsets at push time
    sta scr3
    lda.w GHBUF+9,x
    sta scr5
    rep #$20
    .ACCU 16
    lda scr3
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   sta scr3
    lda scr0
    and #$00FF.w
    beq +
    lda scr3
    eor #$FFFF.w
    inc a
    sta scr3                              ; -xoff when flipped
+   lda scr1
    clc
    adc scr3
    sta scr1
    lda scr5
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   clc
    adc scr2
    sta scr2
    ldx oamtop
    ldy #0
    jsr DF_cell                           ; shared OAM cell emitter
DG_next:
    rep #$20
    .ACCU 16
    lda sidx
    clc
    adc #12
    sta sidx
    lda gk
    inc a
    sta gk
    cmp #2
    bcs +
    jmp DG_slot
+   rts

; Emit OAM cells for active sparks before the fighters so the flash draws
; in front. Cells are 16x16 small OBJs with absolute tile indices and
; shared OBJ palette 2 (CGADD 160) at priority 3.
DrawSparks:
    rep #$20
    .ACCU 16
    stz sidx
DS_slot:
    ldx sidx
    lda.w SPARKS+SPK_ANIM,x
    bne +
        jmp DS_next
+   lda.w SPARKS,x
    sta scr1                            ; spark origin x
    lda.w SPARKS+2,x
    sta scr2                            ; spark origin y
    lda.w SPARKS+SPK_ANIM,x
    sta sptr
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    and #$80.b
    beq DS_global_bank
    lda.w SPARKS+SPK_BANK,x
    bra DS_bank_ready
DS_global_bank:
    lda tblbank
DS_bank_ready:
    sta sptr+2
    lda.w SPARKS+6,x                    ; frame index
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    inc a                               ; anim + 1 + fidx*2
    tay
    lda [sptr],y                        ; frame record ptr
    sta sptr
    lda sidx                            ; never draw cells against a stale FX page
    beq +
    lda #2.w
+   sta gk
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR,x
    bmi DS_cache_projectile
    rep #$20
    .ACCU 16
    lda #$FFFF.w
    sta scr5
    lda #(:SparkChr & $FF).w
    sta scr3
    bra DS_cache_check
DS_cache_projectile:
    rep #$20
    .ACCU 16
    lda sptr
    sta scr5
    ldy #4
    lda [sptr],y                        ; atlas bank stored in frame header
    and #$00FF.w
    sta scr3
    ; Do not gate projectile cells on FX_CACHE.  OAM is built at the end
    ; of a tick, but FxPrepareBoth streams the FX page at the following
    ; vblank, so the cache still points at the previous projectile frame.
    ; Skipping here made every multi-frame projectile invisible (Yuri's
    ; Ko'ou Ken).  FxPrepareBoth always uploads the projectile page.
    bra DS_cells
DS_cache_check:
    ldy gk
    lda.w FX_CACHE,y
    cmp scr5
    beq +
    jmp DS_next
+
    lda.w FX_CACHEBANK,y
    and #$00FF.w
    cmp scr3
    beq +
    jmp DS_next
+
DS_cells:
    ldy #1
    sep #$20
    .ACCU 8
    lda [sptr],y                        ; ncells
    bne +
        jmp DS_next                     ; empty explod frame: draw nothing
+   sta scr4
    lda.w SPARKS+SPK_ATTR,x             ; internal owner/projectile bits
    sta scr6+1                          ; retain projectile flag for header size
    bpl DS_palette_generic              ; ordinary sparks keep their palette
    lda #$34.b                          ; both projectiles use shared FX palette 2
DS_palette_set:
    sta scr6
    bra DS_palette_done
DS_palette_generic:
    sta scr6                            ; non-projectile spark/explod palette
DS_palette_done:
    ; Mirror projectile art when it was fired facing left.  The source
    ; SFF/AIR projectile cells are authored facing right, so a left-flying
    ; shot must flip both the cell tiles and their relative X positions.
    ; Bit4 of SPK_ATTR stores the firing facing; ProjReflect toggles it.
    stz scr0
    lda.w SPARKS+SPK_ATTR,x
    bpl +
    and #$10.b
    beq +
    lda #1
    sta scr0
    lda scr6
    ora #$40.b
    sta scr6
+
    ldy #2                              ; ordinary frame: ticks, ncells
    lda scr6+1
    bpl +
    ldy #5                              ; projectile also has a 24-bit atlas ptr
+
    ldx oamtop
DS_cell:
    sep #$20
    .ACCU 8
    lda [sptr],y                        ; dx
    sta scr3
    iny
    rep #$20
    .ACCU 16
    lda scr3
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
    sta scr3                            ; keep the signed dx for the mirror
+   clc
    adc scr1
    sta scr5                            ; cell x (signed)
    lda scr0
    and #$00FF.w
    beq +
    lda scr1
    sec
    sbc scr3                            ; sx' = origin - dx - 16
    sec
    sbc #16.w                           ; 16x16 cell: dx' = -dx-16
    sta scr5
+
    lda scr5
    sep #$20
    .ACCU 8
    sta.w OAMBUF,x
    lda [sptr],y                        ; dy
    sta scr3
    iny
    rep #$20
    .ACCU 16
    lda scr3
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   clc
    adc scr2
    sep #$20
    .ACCU 8
    sta.w OAMBUF+1,x
    rep #$20
    .ACCU 16
    lda [sptr],y                        ; absolute tile index
    iny
    iny
    sta scr3
    lda sidx                            ; FX page follows the live slot,
    beq +
    lda scr3
    ora #$0100.w
    sta scr3
+
    sep #$20
    .ACCU 8
    lda scr3                            ; page selection above clobbers A
    sta.w OAMBUF+2,x                    ; tile low byte
    lda scr6                            ; slot attr (prio+palette)
    sta.w OAMBUF+3,x
    lda scr3+1
    beq +
    lda.w OAMBUF+3,x
    ora #$01.b                          ; name msb (tile >= 256)
    sta.w OAMBUF+3,x
+   ; OAM hi table: x-sign + size bit (spark cells are always 16x16,
    ; the large size under OBJ mode 0)
    rep #$20
    .ACCU 16
    phx
    txa
    lsr a
    lsr a
    sta scr3
    and #$0003.w
    asl a
    tax
    lda #$0002.w
    phy
    ldy scr5
    bpl +
    ora #$0001.w
+   cpy #256.w
    bcc ++
    ora #$0001.w
++  cpx #0
    beq +
-   asl a
    dex
    bne -
+   sta scr5
    lda scr3
    lsr a
    lsr a
    tax
    sep #$20
    .ACCU 8
    lda scr5
    ora.w OAMHI,x
    sta.w OAMHI,x
    rep #$20
    .ACCU 16
    ply
    plx
    inx
    inx
    inx
    inx
    sep #$20
    .ACCU 8
    dec scr4
    rep #$20
    .ACCU 16
    beq +
    jmp DS_cell
+   stx oamtop
DS_next:
    rep #$20
    .ACCU 16
    lda sidx
    clc
    adc #SPK_SIZE
    sta sidx
    cmp #SPK_SIZE*2
    bcs +
    jmp DS_slot
+   rts

BuildOam:
    rep #$20
    .ACCU 16
    stz oamtop
    ldx #0
    txa
-   sta.w OAMHI,x
    inx
    inx
    cpx #32
    bne -
    ldx #0
    stx fofs
.IFDEF PVSNESLIB
    jsr DrawFighterCache
.ELSE
    jsr DrawFighter
.ENDIF
    ldx #FP2OFS
    stx fofs
.IFDEF PVSNESLIB
    jsr DrawFighterCache
.ELSE
    jsr DrawFighter
.ENDIF
    ; Reserve OAM for both playable bodies before cosmetic cells.  Equal
    ; priority OBJs with lower OAM indexes win, so a large spark/afterimage
    ; can no longer erase a fighter on dense frames.
    jsr DrawSparks
    ldx #0
    stx fofs
    jsr DrawGhost
    ldx #FP2OFS
    stx fofs
    jsr DrawGhost
    rep #$20
    .ACCU 16
    ldx oamtop
    lda #$F0F0.w
-   cpx #512.w
    bcs +
    sta.w OAMBUF,x
    inx
    inx
    bra -
+   rts

DrawFighter:
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_META,x
    bne +
        jmp DF_done
    + 
    sta lptr
    jsr DataFighterX
    jsr MetaBankX
    sta lptr+2
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    lda FP+F_CHAR,x
    sta cptr
    sep #$20
    .ACCU 8
    lda #$30.b                          ; per-side OBJ palette bits
    cpx #0                              ;   (P1 pal0, P2 pal1)
    beq +
    lda #$32.b
+   sta aofs
    ldx fofs
    lda FP+F_PFX,x                        ; PalFX: swap to the bright copy
    beq +
    lda aofs
    clc
    adc #$0A.b                            ; palette +5 (OBJ pal 5/6)
    sta aofs
+   lda [lptr]                          ; ncells
    sta scr4
    bne +
    rts                                 ; empty frame: avoid 255-cell underflow

+
    rep #$20
    .ACCU 16
    lda lptr
    clc
    adc #9
    sta lptr                            ; -> first cell
    ; tile base = ping-pong page (F_TILEPG) + P2 page offset
    ldx fofs
    lda FP+F_TILEPG,x
    and #$00FF.w
    sta pbase
    lda fofs
    beq +
    lda pbase
    clc
    adc #P2TILEOF.w
    sta pbase
+
    ; sx = (x>>8) + xoff*facing ; sy = GROUND_Y - (y>>8) + yoff
    ldx fofs
    lda FP+F_X,x
    xba
    and #$00FF.w
    sta scr1                            ; fx int
    lda FP+F_Y,x
    xba
    and #$00FF.w
    sta scr2
    lda #GROUND_Y.w
    sec
    sbc scr2
    sta scr2                            ; fy int (feet screen y)
    sep #$20
    .ACCU 8
    ldx fofs
    lda FP+F_XOFF,x
    sta scr3
    lda FP+F_YOFF,x
    sta scr5
    lda FP+F_FLAGS,x                    ; anim hflip
    sta scr0
    lda FP+F_FACING+1,x                 ; sign byte: $FF when facing left
    bpl +
    lda scr0
    eor #$01.b
    sta scr0
+   lda scr0
    and #$01.b
    sta scr0                            ; flip?
    rep #$20
    .ACCU 16
    lda scr3
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   sta scr3                            ; xoff signed
    lda scr0
    and #$00FF.w
    beq +
    lda scr3
    eor #$FFFF.w
    inc a
    sta scr3                            ; -xoff when flipped
+   lda scr1
    clc
    adc scr3
    sta scr1                            ; sx
    lda scr5
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   clc
    adc scr2
    sta scr2                            ; sy
    ldx oamtop
    ldy #0
DF_cell:
    ; A malformed frame must never walk beyond the 128-entry OAM shadow.
    ; Keep this guard here (rather than trusting ncells) because ghosts and
    ; effects share the same OAM cursor with both fighters.
    cpx #512.w
    bcc +
    inc.w RT_OAMDROP
    stx oamtop
    jmp DF_done
+
    ; peek the cell's tile word (y+2): bit15 marks an 8x8 sub-cell
    rep #$20
    .ACCU 16
    tya
    clc
    adc #2
    tay
    lda [lptr],y
    sta scr6                            ; raw tile word (size flag + index)
    tya
    sec
    sbc #2
    tay
    sep #$20
    .ACCU 8
    lda [lptr],y                        ; dx
    sta scr3
    iny
    rep #$20
    .ACCU 16
    lda scr3
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   sta scr3                            ; dx signed
    lda scr0
    and #$00FF.w
    beq +
    lda scr3
    eor #$FFFF.w
    inc a
    sec
    sbc #8
    bit scr6                            ; N = tile word bit15 (8x8 flag)
    bmi ++                              ; 8x8 cell: dx' = -dx-8
    sec
    sbc #8                              ; 16x16 cell: dx' = -dx-16
++  sta scr3
+   lda scr1
    clc
    adc scr3
    sta scr5                            ; full x (sign in bit15? pixel -256..511)
    sep #$20
    .ACCU 8
    sta.w OAMBUF,x                        ; cell x low byte
    sep #$20
    .ACCU 8
    lda [lptr],y                        ; dy
    sta scr3
    iny
    rep #$20
    .ACCU 16
    lda scr3
    and #$00FF.w
    bit #$0080.w
    beq +
    ora #$FF00.w
+   clc
    adc scr2
    bpl +
    lda #$00F0.w                        ; cell would start above the screen:
+   sep #$20                            ;   hide it instead of letting the
    .ACCU 8                             ;   8-bit OAM y wrap to the bottom
    sta.w OAMBUF+1,x                      ; cell y
    rep #$20
    .ACCU 16
    iny
    iny
    lda scr6
    and #$7FFF.w                        ; strip the 8x8 size flag
    clc
    adc pbase                           ; fighter page + ping-pong page
    sta scr3
    sep #$20
    .ACCU 8
    lda scr3
    sta.w OAMBUF+2,x
    lda aofs                              ; prio 3 + character OBJ palette
    sta.w OAMBUF+3,x
    lda scr3+1
    beq +
    lda.w OAMBUF+3,x
    ora #$01.b                          ; name msb
    sta.w OAMBUF+3,x
+   lda scr0
    beq +
    lda.w OAMBUF+3,x
    ora #$40.b                          ; hflip
    sta.w OAMBUF+3,x
+   ; OAM hi table: byte idx = (oampos>>4), bit pair at (oampos>>2 &3)*2.
    ; mask = (x-high | size)<<shift; 16x16 cells set the size bit, 8x8
    ; sub-cells (tile bit15) leave it clear under OBJ size mode 0.
    rep #$20
    .ACCU 16
    phx
    txa
    lsr a
    lsr a                               ; i = entry index
    sta scr3
    and #$0003.w
    asl a                               ; shift count
    tax
    lda #$0000.w
    bit scr6
    bmi +
    lda #$0002.w                        ; 16x16 cell: large OBJ size bit
+   phy                                 ; keep metasprite cell offset
    ldy scr5
    bpl ++
    ora #$0001.w
++  cpy #256.w
    bcc +++
    ora #$0001.w
+++ cpx #0
    beq +
-   asl a
    dex
    bne -
+   sta scr5                            ; mask (scr5 free now)
    lda scr3
    lsr a
    lsr a
    tax                                 ; x = OAMHI byte index
    sep #$20
    .ACCU 8
    lda scr5
    ora.w OAMHI,x
    sta.w OAMHI,x
    rep #$20
    .ACCU 16
    ply
    plx
    inx
    inx
    inx
    inx
    sep #$20
    .ACCU 8
    dec scr4
    rep #$20
    .ACCU 16
    beq +
    jmp DF_cell
+   stx oamtop
DF_done:
    rts

; ---------------------------------------------------------------------------
; Presentation telemetry ($51B0..$51DF).  The headless probe reads these
; counters straight from WRAM; writing 1 to TEL_CTRL resets the block.
; ---------------------------------------------------------------------------
TelReset:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0
    lda #0
-   sta.w TEL_FRAMES,x
    inx
    inx
    cpx #(TEL_MAX2+1-TEL_FRAMES)
    bne -
    rts

; Called once per presentation before any DMA starts.  Counts pending
; requests and request age (in frames) for both fighters.  A request is
; timestamped in ASF_q_new; a new pose rejected while DMA is busy increments
; TEL_DROP, which is the direct measure of animation poses that never made it
; to the screen.
TelPresent:
    rep #$20
    .ACCU 16
    lda.w TEL_CTRL
    beq +
    jsr TelReset
+   inc.w TEL_FRAMES
    sep #$20
    .ACCU 8
    lda FP+F_DMAREQ
    beq TP_no_p1
    rep #$20
    .ACCU 16
    inc.w TEL_DMA_P1
    ldx #0
    jsr TelAge
    sep #$20
    .ACCU 8
TP_no_p1:
    lda FP+F_DMAREQ+FP2OFS
    beq TP_no_p2
    rep #$20
    .ACCU 16
    inc.w TEL_DMA_P2
    ldx #2
    jsr TelAge
    sep #$20
    .ACCU 8
TP_no_p2:
    rts

; age = (framecnt - request_time) mod 256, accumulated and maxed.
; X = 0 for P1, 2 for P2 (the telemetry fields are interleaved).
TelAge:
    rep #$10
    sep #$20
    .ACCU 8
    lda framecnt
    sta scr0
    stz scr0+1
    rep #$20
    .ACCU 16
    lda scr0
    sec
    sbc.w TEL_REQ_P1,x
    bcs +
    adc #$0100.w
+   sta scr0
    clc
    adc.w TEL_AGE_SUM_P1,x
    sta.w TEL_AGE_SUM_P1,x
    lda scr0
    cmp.w TEL_AGE_MAX_P1,x
    bcc +
    sta.w TEL_AGE_MAX_P1,x
+   rts

; ---------------------------------------------------------------------------
; PVSnesLib owns the NMI.  Immediately after WaitForVBlank returns, present
; the engine's shadow buffers while forced blank is active.
; ---------------------------------------------------------------------------
.IFDEF PVSNESLIB
    sep #$20
    .ACCU 8
FightPresent:
    sep #$20
    .ACCU 8
    jsr TelPresent
    lda #$8F.b
    sta.l INIDISP
    jsr FxPrepareBoth
    ; The library ISR may have already sent this same shadow buffer, but
    ; doing it under forced blank makes this path valid even when the
    ; library skips a lag frame.
    jsr PushOamShadow
    ldx #0
    ; Both fighters streaming their sprite pages in the same vblank run two
    ; 1280-byte MSU->VRAM DMAs back to back.  The upload overruns vblank,
    ; forced blank is still on during the first visible lines, and the top
    ; of the screen flickers dark.  If both sides need tiles this frame,
    ; upload one of them now and let the other take the next vblank.
    stz sdmaside
    lda FP+F_DMAREQ
    beq FP_dma_pick
    lda FP+F_DMAREQ+FP2OFS
    beq FP_dma_pick
    lda framecnt
    and #1.b
    inc a                               ; 1 = P1 now, 2 = P2 now
    sta sdmaside
FP_dma_pick:
    lda sdmaside
    cmp #2.b
    beq FP_dma_p1done
    lda FP+F_DMAREQ,x
    beq FP_dma_p1done
    lda #<P1CHR
    sta scr5
    lda #>P1CHR
    sta scr5+1
    jsr SprDmaP
FP_dma_p1done:
    .ACCU 8
    lda sdmaside
    cmp #1.b
    beq FP_dma_done
    ldx #FP2OFS
    lda FP+F_DMAREQ,x
    beq FP_dma_done
    lda #<P2CHR
    sta scr5
    lda #>P2CHR
    sta scr5+1
    jsr SprDmaP
FP_dma_done:
    .ACCU 8
.IFDEF MSU_DIAG
    jsl MsuDiagOverlay
.ENDIF
    lda FP+F_DMAREQ                     ; a fighter upload is still in flight:
    ora FP+F_DMAREQ+FP2OFS              ;   don't start a second DMA engine
    bne +                               ;   transfer in this vblank
    lda.w RT_FXUPLOAD                   ; a spark/projectile page already used
    bne +                               ;   this vblank's DMA budget
    lda huddirty
    beq +
    jsr FlushHud
+   jsr StageAnimTick                     ; crowd pose commits (map only)
    jsr ShakeScroll                       ; EnvShake on BG1 (stage)
    lda gamestate                         ; intro/ending screens take over
    cmp #7.b                              ;   mode/M7 regs + palette fades;
    beq ++                                ;   run them last so they win
    cmp #8.b                              ;   over the fight setup
    beq ++
    cmp #10.b                             ; SURVIVOR ending also uses the
    bne +                                 ;   shared fade/palette flush
++  jsr OpnApply                          ;   (IN_FX==6 -> OpnFade flush)
    sep #$20
    .ACCU 8
+   lda #$0F.b
    sta.l INIDISP
    inc framecnt
    .ACCU 8
    rts
.ELSE
; Standalone build owns the native NMI vector.
; NMI fires on top of whatever the main loop was doing, and the upload
; routines below reuse the shared DP scratch (scr0-6, lptr, fofs, sidx,
; gk, ...).  Without a save, a vblank landing inside DrawFighter's cell
; loop restarts it with a garbage cell count and OAMBUF writes run away
; until they hit $4200 and kill the NMI enable.  Stash the scratch range
; on entry and put it back before RTI.  Live state ($20-$33: nmiflag,
; framecnt, huddirty, vbusy, sfx*; $73-$77: pausecnt/shake/timer) is
; intentionally NOT saved -- the vblank's own updates must persist.
FightVblank:
    rep #$38
    .ACCU 16
    .INDEX 16
    pha
    phx
    phy
    phd
    phb
    lda #ENGINE_DP.w
    tcd
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    ldx #$0F.w                          ; save DP $10-$1F
-   lda $10.b,x
    sta.l NmiDpSave,x
    dex
    bpl -
    ldx #$3E.w                          ; save DP $34-$72 (lptr..histp)
-   lda $34.b,x
    sta.l NmiDpSave+$10,x
    dex
    bpl -
    ldx #$07.w                          ; save DP $78-$7F (gk, msuok, win timer)
-   lda $78.b,x
    sta.l NmiDpSave+$50,x
    dex
    bpl -
    lda vbusy                           ; if an NMI ever re-enters while a
    beq +
    jmp FightVblank_skip                ; previous upload runs, drop it
+
    inc vbusy
    lda #$8F.b
    sta.l INIDISP
    jsr FxPrepareBoth

    ; OAM shadow -> hardware OAM via GPDMA ch6
    jsr PushOamShadow
    ; sprite tile uploads (chunked, hidden ping-pong page).  Two 1280-byte
    ; sprite DMAs in one vblank overrun it and leave forced blank on during
    ; the first visible lines (dark flicker at the top), so when both sides
    ; stream in the same frame give the slot to one side, alternating.
    stz sdmaside
    lda FP+F_DMAREQ
    beq FP_dma_pick
    lda FP+F_DMAREQ+FP2OFS
    beq FP_dma_pick
    lda framecnt
    and #1.b
    inc a                               ; 1 = P1 now, 2 = P2 now
    sta sdmaside
FP_dma_pick:
    ldx #0
    lda sdmaside
    cmp #2.b
    beq FP_dma_p1done
    lda FP+F_DMAREQ,x
    beq FP_dma_p1done
    lda #<P1CHR
    sta scr5
    lda #>P1CHR
    sta scr5+1
    jsr SprDmaP
FP_dma_p1done:
    lda sdmaside
    cmp #1.b
    beq FP_dma_done
    ldx #FP2OFS
    lda FP+F_DMAREQ,x
    beq FP_dma_done
    lda #<P2CHR
    sta scr5
    lda #>P2CHR
    sta scr5+1
    jsr SprDmaP
FP_dma_done:
    lda.w RT_FXUPLOAD                   ; a spark/projectile page already used
    bne +                               ;   this vblank's DMA budget
    lda huddirty
    beq +
    jsr FlushHud
+   jsr StageAnimTick                     ; crowd pose commits (map only)
    lda #$0F.b
    sta.l INIDISP
    sta nmiflag
    jsr ShakeScroll
    inc framecnt
    stz vbusy
FightVblank_skip:
    ldx #$0F.w                          ; restore DP $10-$1F
-   lda.l NmiDpSave,x
    sta $10.b,x
    dex
    bpl -
    ldx #$3E.w                          ; restore DP $34-$72
-   lda.l NmiDpSave+$10,x
    sta $34.b,x
    dex
    bpl -
    ldx #$07.w                          ; restore DP $78-$7F (gk, msuok, win timer)
-   lda.l NmiDpSave+$50,x
    sta $78.b,x
    dex
    bpl -
    plb
    pld
    ply
    plx
    rep #$20
    .ACCU 16
    pla
    rti
.ENDIF

; ---------------------------------------------------------------------------
; Per-stage BG1 anims (tools/build_stages.py:build_anims).  StgAnimTab maps
; stageidx -> clip list (.DB nclips / .DW clip ptrs).  Clip format:
;   .DB ncells, nposes, phase / .DW ticks[nposes] /
;   cells {mapidx, tileP0..tilePn} x ncells
; Every pose of every clip is resident in dynamic tiles 704+, so a pose
; commit is a tilemap write only and runs inside the forced-blank window
; after the HUD flush.  animT: 8 word timers ($94..), animP: 8 pose bytes
; ($A4..), both indexed by slot*2 so one X serves both arrays.
StageAnimTick:
    sep #$20
    .ACCU 8
    lda gamestate                         ; stage animations only while the
    cmp #1.b                              ;   stage BG is actually visible:
    beq SAI_ok                            ;   fights/KO/intro and the
    cmp #2.b                              ;   intermission.  Select/menu/
    beq SAI_ok                            ;   endings reuse BG1 VRAM for
    cmp #4.b                              ;   their own art.
    beq SAI_ok
    cmp #0.b
    bne SAI_skip
    lda nextflag
    beq SAI_skip
SAI_ok:
    rep #$10
    .INDEX 16
    lda stageidx
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl
    tax
    lda.l StgAnimTab,x                  ; -> clip list (0 = no anims)
    beq SA_exit
    sta lptr
    sep #$20
    .ACCU 8
    lda #:StgAnimTab
    sta lptr+2
    ldy #0
    rep #$20
    .ACCU 16
    lda [lptr],y                        ; nclips
    and #$00FF.w
    beq SA_exit
    sta sacnt
    lda #1
    sta saofs                           ; offset of clip-ptr list
    ldx #0                              ; clip slot (animT/animP, slot*2)
SA_clip:
    rep #$20
    .ACCU 16
    ldy saofs
    lda [lptr],y
    sta boxp
    sep #$20
    .ACCU 8
    lda #:StgAnimTab
    sta boxp+2
    jsr StageAnimOne                    ; NOTE: clobbers scr4/scr5
    rep #$20
    .ACCU 16
    inc saofs
    inc saofs
    inx
    inx
    dec sacnt
    bne SA_clip
SA_exit:
SAI_skip:
    rep #$10
    .INDEX 16
    rep #$20
    .ACCU 16
    rts

; boxp = clip long ptr, X = slot*2.  Advances the clip clock; on a pose
; boundary commits every cell's new tile index to the BG1 map.
StageAnimOne:
    rep #$20
    .ACCU 16
    lda animT,x
    clc
    adc #1
    sta animT,x
    sep #$20
    .ACCU 8
    lda animP,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl
    sta scr6                            ; pose*2
    clc
    adc #3
    tay                                 ; ticks[pose] at clip+3+pose*2
    lda animT,x
    cmp [boxp],y
    bcc SAO_out                         ; still inside this pose's window
    sec
    sbc [boxp],y                        ; keep the remainder (no drift)
    sta animT,x
    ldy #1
    lda [boxp],y                        ; clip+1 = nposes (clip+0 = ncells)
    and #$00FF.w
    sta scr5
    sep #$20
    .ACCU 8
    lda animP,x
    clc
    adc #1
    cmp scr5
    bcc +
    lda #0.b
+   sta animP,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl
    sta scr6                            ; new pose*2
    txa                                 ; debug: commits per clip slot
    clc
    adc #DBGREG+112
    sta scr3
    sep #$20
    .ACCU 8
    lda #$7E.b
    sta scr3+2
    lda [scr3]
    clc
    adc #1
    sta [scr3]
    lda #$80.b
    sta.l VMAIN
    rep #$20
    .ACCU 16
    lda [boxp]                          ; ncells (clip+0)
    and #$00FF.w
    sta scr4
    lda scr5                            ; nposes
    asl
    clc
    adc #2
    sta scr5                            ; cell stride = 2 + nposes*2 bytes
    clc
    adc #1                              ; first cell at 3+nposes*2 = stride+1
    sta scr2                            ; running cell offset
SAO_cell:
    ldy scr2
    lda [boxp],y                        ; mapidx
    clc
    adc #BG1MAP
    sta.l VMADDL
    lda scr2
    clc
    adc #2
    adc scr6                            ; tile word at cell+2+pose*2
    tay
    lda [boxp],y
    sta.l VMDATAL
    lda scr2
    clc
    adc scr5
    sta scr2
    dec scr4
    bne SAO_cell
SAO_out:
    rts

; Reset the anim clocks for the stage just picked: every clip starts at
; pose 0 with its timer preloaded by the clip's phase byte.
StageAnimInit:
    rep #$20
    .ACCU 16
    lda #0
    ldx #0
-   sta animT,x                         ; word-clear $94-$B3: animT words AND
    inx                                 ;   animP bytes are contiguous below
    inx                                 ;   sacnt (DP $AC)
    cpx #32.w
    bne -
    sep #$20
    .ACCU 8
    lda stageidx
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl
    tax
    lda.l StgAnimTab,x
    beq SAI_out
    sta lptr
    sep #$20
    .ACCU 8
    lda #:StgAnimTab
    sta lptr+2
    ldy #0
    rep #$20
    .ACCU 16
    lda [lptr],y                        ; nclips
    and #$00FF.w
    sta scr4
    lda #1
    sta scr5                            ; clip-ptr list offset
    ldx #0
SAI_clip:
    rep #$20
    .ACCU 16
    ldy scr5
    lda [lptr],y
    sta boxp
    sep #$20
    .ACCU 8
    lda #:StgAnimTab
    sta boxp+2
    ldy #2
    lda [boxp],y                        ; clip+2 = phase
    sta scr6
    rep #$20
    .ACCU 16
    lda scr6
    and #$00FF.w
    sta animT,x                         ; preload timer with the phase
    inc scr5
    inc scr5
    inx
    inx
    dec scr4
    bne SAI_clip
SAI_out:
    sep #$20                            ; callers write 8-bit regs after us
    .ACCU 8
    rts

; Load + queue the module that matches stageidx (StageModTab, module 0 =
; sfx). Runs after StagePick inside StartFight. spcLoad replaces the active
; module, so don't queue a separate STOP first: its asynchronous echo can
; race the direct load handshake and leave the SPC upload waiting forever.
.IF 0
StageMusic:
    sep #$20
    .ACCU 8
    lda.w MUSIC_VALID
    beq SM_changed
    lda.w MUSIC_STAGE
    cmp.b stageidx
    bne SM_changed
    jmp SM_music_out
SM_changed:
    lda audiordy
    beq SM_music_out_j
    bra SM_music_go
SM_music_out_j:
    jmp SM_music_out
SM_music_go:
    lda #0                              ; NMI off during the SPC upload: an
    sta.l NMITIMEN                      ;   interrupt mid-handshake corrupts
    lda.l $4210                         ;   clear a pending NMI flag
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #$2000                          ;   settle: an in-flight NMI may still
-   dex                                 ;   be running spcProcess's port writes
    bne -                               ;   -> let it finish before handshake
    phd                                 ; drain the previous winner command
    lda #0
    tcd
    jsl SpcFlushSafe
    pld
    sep #$20
    .ACCU 8
    lda stageidx                        ;   the port protocol (same guard as
    rep #$20                            ;   MusPlaySong)
    .ACCU 16
    and #$00FF.w
    tax
    lda.l StageModTab,x
    and #$00FF.w
    phd                                 ; save D=ENGINE_DP; snesmod wants 0
    pha                                 ; arg1: module index
    lda #0
    tcd
    jsl spcLoad                         ;   its SPC RAM with the new module
    rep #$20
    .ACCU 16
    pla
    jsl SpcFlushSafe                        ; match BootAudio: drain fifo before
    lda #8.w                            ; fight modules need 8 sources:
    sta.l $7E46F8                       ;   combat 0,1,2,5,6 + menu 4,13,12
    sep #$20                            ; byte var: an 8-bit STA keeps the
    .ACCU 8                             ;   neighbouring Q_LANG byte intact
    lda #0
    sta.w UI_SFXLOAD                    ;   (stage music must not reset quotes)
    rep #$20
    .ACCU 16
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
    lda.b stageidx
    sta.w MUSIC_STAGE
    lda #1
    sta.w MUSIC_VALID
    lda #1
    sta.w MUSON                         ; PLAY dispatched -- STOPs may echo
    lda #$81.b                          ; re-enable NMI now that the SPC
    sta.l NMITIMEN                      ;   handshake is done
SM_music_out:
    sep #$20                            ; callers continue in acc8 -- never
    .ACCU 8                             ;   leak the acc16 SPC path back out
    rts
.ENDIF
StageMusic:
    jsl StageMusicFar
    rts

; A(8) = announcer voice index (0..8 -> soundbank sources 7..15). Sources
; 12-13 (indices 5-6) are reused for menu back/navigation; index 7 is select
; entry and index 8 is FINAL ROUND. Load only the requested voice to bound
; the SPC handshake.
RoundVoice:
    pha                                 ; BIT tested the voice index and
    lda audiordy                        ; dropped indices 0, 2, 4, 6 and 8
    bne +
    pla
    rts
+   pla
    sep #$20
    .ACCU 8
    php
    rep #$30                            ; 16-bit pushes like SfxPlay
    .ACCU 16
    .INDEX 16
    pha
    phx
    phy
    phd
    rep #$20
    .ACCU 16
    lda #0
    sta.l NMITIMEN
    tcd                                 ; snesmod uses direct page zero
    jsl SpcFlushSafe                        ; retire queued music/effects first
    lda.l $00015A                       ; still streaming?  spcLoadEffect would
    and #$00FF.w                        ;   spin forever on a missed APU ack,
    beq +                               ;   freezing the fight with music alive
    jmp RV_skip                         ;   (drop the callout, retry no voice)
+   lda 7,s                             ; stacked A: voice index 0..8
    and #$00FF.w
    clc
    adc #7                              ; -> soundbank source 7..15
    pha                                 ; spcLoadEffect(source index)
    jsl spcLoadEffect                    ; A = newly allocated effect slot
    rep #$20
    .ACCU 16
    tax                                  ; keep the slot across the arg drop
    pla
    txa
    and #$00FF.w
    tay
    lda #$00F8.w                        ; vol15*16 + center pan
    pha                                 ; arg3: volpan
    phy                                 ; arg2: source
    pea 1                               ; arg1: pitch 1 = 4 kHz
    jsl spcEffect
    rep #$20
    .ACCU 16
    pla
    pla
    pla
    sep #$20
    .ACCU 8
    lda #$81.b
    sta.l NMITIMEN
    rep #$20
    .ACCU 16
    pld
    ply
    plx
    pla
    plp
    rts
RV_skip:                                ; stream still active: leave NMI/stack
    sep #$20                            ;   exactly as the played path does
    .ACCU 8
    lda #$81.b
    sta.l NMITIMEN
    rep #$20
    .ACCU 16
    pld
    ply
    plx
    pla
    plp
    rts

; A8 = per-char voice index (op7 arg - VOICE_BASE).  Terry's voice
; records point directly to ROM BRRs; other characters copy MSU samples
; to VOICE_BUF before playback.  D=ENGINE_DP on entry.
.IF 0
VoicePlay:
    sep #$20                            ; dispatcher may arrive in acc16;
    .ACCU 8                             ;   arg/push math below is acc8
    .INDEX 16                           ; X is the 16-bit fofs all through
    pha                                 ; local voice index (8-bit push)
    phx                                 ; op dispatcher needs X=fofs back
    lda audiordy
    bne +
    plx
    pla
    rts
+   ldx fofs
    phd                                 ; snesmod wants D=0 below
    rep #$20
    .ACCU 16
    lda FP+F_CHAR,x                     ; desc ptr -> scan VoicePtrTab
    sta scr5
    ldx #0
VP_scan:
    lda.l VoicePtrTab,x
    bne +
    jmp VP_out                          ; terminator: no voice table
+
    cmp.b scr5
    beq VP_got
    txa
    clc
    adc #8.w                            ; {desc.w,tab.w,tab.b,ofs.w,ofs.b}
    tax
    bra VP_scan
VP_got:
    stx scr4                            ; ptrtab index survives the waits
    lda.l VoicePtrTab+5,x               ; zero offset table = ROM voice
    bne VP_msu
    jmp VP_rom
VP_msu:
    lda.b msuok
    and #$00FF.w
    bne +
    jmp VP_out
+   ldx.b scr4
    sep #$20
    .ACCU 8
    lda.l VoicePtrTab+7,x
    sta lptr+2                          ; lptr -> VoiceOfs_<char>
    rep #$20
    .ACCU 16
    lda.l VoicePtrTab+5,x
    sta lptr
    lda 5,s                             ; saved local index (phx+phd pushed 4)
    and #$00FF.w
    sta scr5                            ; voice idx
    jsr VoiceQueueAdd
    bcc +                               ; full queue: use the old safe fallback
    jmp VP_out
+   lda scr5
    asl a
    asl a                               ; ofs stride 4 (.msu offset LE)
    tay
    sep #$20
    .ACCU 8
    lda [lptr],y                        ; .msu file offset, 32-bit LE
    sta.l MSU_STAT                      ; seek byte 0
    iny
    lda [lptr],y
    sta.l MSU_DATA                      ; seek byte 1
    iny
    lda [lptr],y
    sta.l $2002                         ; seek byte 2
    iny
    lda [lptr],y
    sta.l $2003                         ; seek byte 3 (starts the seek)
    ldx #$FFFF.w                        ; bounded wait for data ready
-   lda.l MSU_STAT
    bpl +
    dex
    bne -
    jmp VP_out                          ; seek never completed: drop voice
    ; byte count = blocks*9, read from VoiceTab[idx*8 + 3]
+   ldx.b scr4
    rep #$20
    .ACCU 16
    lda.l VoicePtrTab+2,x
    sta lptr                            ; lptr -> VoiceTab_<char>
    lda.b scr5
    asl a
    asl a
    asl a                               ; idx*8 (spcPlaySoundV stride)
    tay
    iny
    iny
    iny
    lda [lptr],y                        ; BRR block count
    sta scr6
    asl a
    asl a
    asl a
    clc
    adc.b scr6                          ; *9 = bytes to stream
    sta.b scr6
    ldx #0
    sep #$20
    .ACCU 8
-   lda.l MSU_DATA                      ; sequential .msu byte -> WRAM
    sta.l VOICE_BUF,x
    inx
    cpx.b scr6
    bne -
    .INDEX 16
    rep #$20
    .ACCU 16
    jmp VP_play
VP_rom:
    lda 5,s                             ; 8-bit index saved under X and D
    and #$00FF.w
    sta scr5
VP_play:
    ldx.b scr4
    lda.l VoicePtrTab+2,x               ; switch to this character's table
    sta.l $7E0050                       ;   the char's table (lib zp; .l)
    sep #$20
    .ACCU 8
    lda.l VoicePtrTab+4,x
    sta.l $7E0052                       ; SoundTable bank
    rep #$20
    .ACCU 16
    lda.b scr5
    pha                                 ; index (lib reads it at 8,s)
    lda #15.w
    pha                                 ; volume (lib reads it at 6,s)
    lda #0
    tcd
    jsl spcPlaySoundV
    rep #$20
    .ACCU 16
    tsc
    clc
    adc #4.w
    tcs
VP_out:
    pld
    sep #$20
    .ACCU 8
    plx                                 ; restore dispatcher's fofs
    pla                                 ; discard saved index
    rts
.ENDIF
VoicePlay:
    jsl VoicePlayFar
    rts

; Queue records are four bytes: VoicePtrTab offset and local voice index.
; Carry is set when accepted; a full queue lets VoicePlay use its synchronous
; fallback so an important callout is never silently discarded.
.IF 0
VoiceQueueAdd:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w VQ_TAIL
    sta scr6
    clc
    adc #4.w
    and #$001F.w
    cmp.w VQ_HEAD
    beq VQA_full
    ldy scr6
    lda scr4
    sta.w VQ_DATA,y
    lda scr5
    sta.w VQ_DATA+2,y
    tya
    clc
    adc #4.w
    and #$001F.w
    sta.w VQ_TAIL
    sec
    rts
VQA_full:
    clc
    rts

; Advance at most VOICE_CHUNK bytes per frame. Two 6 KiB bank-$7F buffers
; alternate so loading a new sample cannot overwrite one still read by SPC.
VoiceQueueTick:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w VQ_BUSY
    cmp #2.w
    bne VQT_not_ready
    lda.l $7E46F8
    beq VQT_play
    jmp VQT_ret                         ; effect reload owns the SPC handshake
VQT_not_ready:
    cmp #1.w
    beq VQT_chunk
    lda.w VQ_HEAD
    cmp.w VQ_TAIL
    beq VQT_ret
    tay
    lda.w VQ_DATA,y
    sta.w VQ_PTRIDX
    lda.w VQ_DATA+2,y
    sta.w VQ_INDEX
    tya
    clc
    adc #4.w
    and #$001F.w
    sta.w VQ_HEAD
    ; Resolve the 32-bit MSU offset.
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
    ; Copy pitch/pan/volume/block count from the generated record.
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
VQT_meta:
    sep #$20
    .ACCU 8
    lda [lptr],y
    sta.w VQ_TABLE,x
    rep #$20
    .ACCU 16
    iny
    inx
    cpx #5.w
    bne VQT_meta
    lda.w VQ_TABLE+3
    sta scr6
    asl a
    asl a
    asl a
    clc
    adc scr6                            ; BRR blocks * 9
    sta.w VQ_TOTAL
    stz.w VQ_POS
    lda.w VQ_SLOT
    eor #1.w
    and #1.w
    sta.w VQ_SLOT
    lda #1.w
    sta.w VQ_BUSY
VQT_chunk:
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
    rts
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
VQT_copy:
    lda.l MSU_DATA
    sta.l $7F0000,x
    inx
    dey
    bne VQT_copy
    rep #$20
    .ACCU 16
    lda.w VQ_POS
    clc
    adc.w VQ_COUNT
    sta.w VQ_POS
    cmp.w VQ_TOTAL
    bcc VQT_ret
    lda #2.w
    sta.w VQ_BUSY
    lda.l $7E46F8
    bne VQT_ret
VQT_play:
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
    pea 0                               ; sample index in the one-row table
    pea 15                              ; full volume
    lda #0
    tcd
    jsl spcPlaySoundV
    rep #$20
    .ACCU 16
    tsc
    clc
    adc #4.w
    tcs
    pld
    stz.w VQ_BUSY
VQT_ret:
    rep #$20
    .ACCU 16
    rts
.ENDIF

; The implementation lives in bank 126; keep same-bank callers small.
VoiceQueueAdd:
    php                                 ; the far loader uses rep #$30;
    jsl VoiceQueueAddFar                ;   restore the caller's M/X width
    plp
    rts
VoiceQueueTick:
    php
    jsl VoiceQueueTickFar
    plp
    rts

; Screen/fight transitions drop the shared voice ring (see voice_queue.asm).
; The tiny near wrappers live in bank 50's low half (VoiceResetWrappers) so
; the 32 KiB Fight section keeps its remaining slack.

; Drain the snesmod message fifo (see SpcFlushSafe in bank 126).

; A(8) = frontend song id (SONG_* -> SongModTab -> soundbank module).
; Same blocking SPC upload pattern as StageMusic.
; Relocated to engine/options.asm (OptionsCode bank) so the Fight
; section stays inside its 32 KiB window; jml + the far rts keeps
; the existing jsr call sites working.
MusPlaySong:
    jsl MusPlaySongFar
    rts

; Camera: fighting-game scroll on the 512px stage.  Fighters live in
; screen coordinates (x in [STAGE_L,STAGE_R]) -- the screen edge is the
; wall, so nobody leaves the view.  The BG pans under them: camx maps the
; fighters' midpoint range [24..232] onto the full 256px scroll span of
; the 512px art: camx = clamp((mid-24)*79/64, 0, 256).  A fighter's stage
; position is effectively camx + screen_x, so the whole stage is
; reachable.  EnvShake adds +/- shakeamp on top.  acc8 in/out.
ShakeScroll:
    rep #$20
    .ACCU 16
    lda FP+F_X                          ; 8.8 px -> integer midpoint
    xba
    and #$00FF.w
    sta scr5
    lda FP+F_X+FP2OFS
    xba
    and #$00FF.w
    clc
    adc scr5                            ; x1+x2 (px)
    lsr                                 ; mid
    sec
    sbc #STAGE_L.w
    bpl +
    lda #0
+   sta scr3                            ; v = mid-24 (0..208)
    lsr
    lsr
    adc scr3                            ; v + v/4
    sta scr5
    lda scr3
    lsr
    lsr
    lsr
    lsr
    lsr
    lsr                                 ; v/64
    sta scr3
    lda scr5
    sec
    sbc scr3                            ; v*79/64 ~= v*256/208
    cmp #256.w
    bcc +
    lda #256.w
+   sta camx
    sta scr5                            ; bg scroll = camx + shake
    sep #$20
    .ACCU 8
    stz scr3
    stz scr3+1                            ; signed hi byte of the offset
    lda shaketmr
    beq SS_wr                             ; inactive: keep shake at 0
    lda framecnt
    and #$01.b
    beq +
    lda shakeamp
    sta scr3
    bra SS_wr
+   lda #0
    sec
    sbc shakeamp                          ; -amp (8-bit wrap = negative)
    sta scr3
    lda #$FF.b
    sta scr3+1
SS_wr:
    rep #$20
    .ACCU 16
    lda scr3                            ; shake (signed word)
    sta scr4
    clc
    adc scr5                            ; hofs = scaled camx + shake
    sta scr3
    sep #$20
    .ACCU 8
    lda scr3
    sta.l BG1HOFS
    lda scr3+1
    sta.l BG1HOFS
    lda scr4
    sta.l BG1VOFS
    lda scr4+1
    sta.l BG1VOFS
    rts

; X = fighter ofs, scr5 = fighter's base page VRAM word addr (P?CHR).
; Sends up to DMACHUNK bytes of the queued sprite (F_PSPRID) into the hidden
; ping-pong page: GPDMA ch6 for ROM-resident CHR, ch7 from the MSU-1 data
; port for streamed CHR.  On completion flips F_TILEPG so the new tiles
; become visible and commits the pending meta and frame geometry to OAM.
SprDmaP:
    rep #$20
    .ACCU 16
    stx fofs
    sep #$20
    .ACCU 8
    lda FP+F_DMAPOS,x
    bne SD_gen_done
    lda FP+F_TILEPG,x                   ; invalidate the hidden physical page
    beq SD_hidden_b
    lda #0.b                            ; visible B -> hidden A
    bra SD_hidden_side
SD_hidden_b:
    lda #1.b                            ; visible A -> hidden B
SD_hidden_side:
    cpx #0.w
    beq +
    clc
    adc #2.b                            ; P2 generations are slots 2/3
+   tay
    lda.w RT_GHOSTGEN,y
    inc a
    sta.w RT_GHOSTGEN,y
SD_gen_done:
    rep #$20
    .ACCU 16
    ; pending meta = SprOfs[F_PSPRID]
    ldy #CH_SPROFS
    ldx #boxp
    jsr CharPtr
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_PSPRID,x
    sta scr6
    lda FP+F_PSPRID_H,x
    sta scr6+1
    rep #$20
    .ACCU 16
    lda scr6
    asl a
    tay
    lda [boxp],y
    sta scr6                            ; pending meta ofs
    sta lptr
    jsr DataFighterX
    jsr MetaBankX                       ; SprOfs entries point into CH_MBANK
    sta lptr+2
    rep #$20
    .ACCU 16
    ldy #1
    lda [lptr],y                        ; tilebase
    sta scr0
    iny
    iny
    lda [lptr],y                        ; dmalen
    sta scr1
    ; src = CH_CHR + tilebase*32 across aligned 32 KiB ROM half-banks
    jsr DataFighterX
    lda FP+F_CHAR,x
    sta cptr
    sep #$20
    .ACCU 8
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    ldy #CH_CHR
    lda [cptr],y
    sta scr2                            ; character CHR base offset
    ldy #CH_CHRBANK
    lda [cptr],y
    sta scr3                            ; {chr flags hi byte, bank/slice lo}
    xba
    and #$00FF.w
    sta msuf                            ; chr flags (bit0 = MSU-1 source)
    lda scr3
    and #$00FF.w
    sta scr3                            ; character CHR base bank
    lda msuf
    and #$0001.w
    beq +
    lda scr2                            ; MSU descriptors store the high
    xba                                 ; slice byte in unused CH_CHR
    ora scr3
    sta scr3                            ; full 16-bit 32 KiB slice index
    stz scr2                            ; MSU tiles start at slice offset 0
    +
    lda scr0                            ; tilebase
    sta scr4
    and #$03FF.w
    asl a
    asl a
    asl a
    asl a
    asl a
    clc
    adc scr2
    sta scr0                            ; src offset $8000-$FFE0
    lda scr4
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a                               ; tilebase >> 10
    clc
    adc scr3
    sta scr4                            ; src bank
    ; upload cursor, in bytes
    ldx fofs
    lda FP+F_DMAPOS,x
    and #$00FF.w
    asl a
    asl a
    asl a
    asl a
    asl a                               ; *32
    sta scr2                            ; pos
    ; dst = hidden page word addr + pos/2
    lda FP+F_TILEPG,x
    and #$00FF.w
    beq +
    lda #0                              ; page $60 visible: upload into base page
    bra ++
+   lda #PGOF.w
++  clc
    adc scr5
    sta scr3                            ; hidden page base
    lda scr2
    lsr a
    clc
    adc scr3
    sta.l VMADDL
    ; count = min(DMACHUNK, dmalen - pos, page bytes left).  A bad sprite
    ; entry or a stale cursor must never write past the 3 KiB ping-pong
    ; page: that wraps VRAM into BG1/BG3 and shreds the stage.
    lda #(PGOF*2).w
    sec
    sbc scr2
    bcs +
    jmp SD_commit                       ; pos already past this page
+   sta scr3                            ; page bytes left
    lda scr1
    sec
    sbc scr2
    bcs +
    jmp SD_commit                       ; pos >= dmalen
+   cmp scr3
    bcc +
    lda scr3
+   cmp #DMACHUNK.w
    bcc +
    lda #DMACHUNK.w
+   sta scr3                            ; count
    tax                                 ; STA doesn't set flags; a zero-byte
    bne SD_nonzero                      ;   DMA count means 64 KiB on the SNES
    jmp SD_commit                       ; empty sprite: just flip/commit
SD_nonzero:
    lda msuf
    and #$0001.w
    bne SD_msu                          ; chr stream lives in the .msu file
    ; GPDMA ch6: word writes to VMDATA
    sep #$20
    .ACCU 8
    lda #$80.b
    sta.l VMAIN
    lda #$01.b                          ; mode 1: alternate $2118/$2119
    sta.l $4360
    lda #$18.b
    sta.l $4361
    rep #$20
    .ACCU 16
    lda scr0
    clc
    adc scr2                            ; src offset + pos
    sta.l $4362
    sep #$20
    .ACCU 8
    lda scr4
    sta.l $4364                         ; src bank
    rep #$20
    .ACCU 16
    lda scr3
    sta.l $4365                         ; byte count
    sep #$20
    .ACCU 8
    lda #$40.b
    sta.l MDMAEN                        ; fire ch6
    ; advance cursor; on completion display the new page and commit meta
    rep #$20
    .ACCU 16
SD_advance:
    lda scr2
    clc
    adc scr3                            ; new pos
    ldx fofs
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a                               ; back to 32B units
    sep #$20
    .ACCU 8
    sta FP+F_DMAPOS,x
    rep #$20
    .ACCU 16
    lda scr2
    clc
    adc scr3
    cmp scr1
    bcs +
    jmp SD_ret                          ; more bytes to send
+   jmp SD_commit

; chr stream lives in kof98-snes.msu: scr4 = slice index (32 KiB units),
; scr0 = offset inside the slice space, scr2 = pos, scr3 = count.
; Seek the MSU-1 data pointer, then stream the chunk straight into VRAM with
; GPDMA ch7 ($00:2001 -> $2118/$2119, fixed source); no vblank CPU copy.
SD_msu:
    lda scr0
    clc
    adc scr2
    sta scr0                            ; offset within the 32 KiB slice
    cmp #$8000.w
    bcc +
    sec
    sbc #$8000.w
    sta scr0
    inc scr4                            ; chunk starts in the next slice
    +
    lda scr4
    lsr a
    sta scr4                            ; P_hi = slice >> 1
    bcc +
    lda scr0                            ; odd slice -> +$8000 in low word
    clc
    adc #$8000.w
    sta scr0
    bcc +
    inc scr4                            ; carry into byte 2 of the seek
+
    ; The sd2snes MSU extension refills its data cache from a 512-byte
    ; aligned file sector and points the SNES read pointer at the in-sector
    ; offset.  Live CHR chunks are only 32-byte aligned, so every chunk used
    ; to depend on a non-zero in-sector pointer (and on page-2 cache hits).
    ; Align the seek to the sector and stage prefix+payload; the VRAM DMA
    ; then starts at the saved prefix.  This starts every transfer at
    ; buffer offset 0 and keeps the whole read inside one 8 KiB cache page.
    lda scr0
    and #$01FF.w
    sta.w MSU_PREFIX
    lda scr0
    and #$FE00.w
    sta scr0                            ; sector-aligned seek address
    sep #$20
    .ACCU 8
    lda scr0
    sta.l MSU_STAT                      ; seek byte 0
    lda scr0+1
    sta.l MSU_DATA                      ; seek byte 1
    lda scr4
    sta.l $2002                         ; seek byte 2
    lda scr4+1
    sta.l $2003                         ; seek byte 3 (starts the seek)
.IFDEF MSU_DIAG
    jsl MsuDiagSpriteWait
    bcc SD_diag_ready
    jmp SD_ret
SD_diag_ready:
.ELSE
    ldx #MSU_POLL_LIMIT.w               ; bounded wait: retry next frame
-   lda.l MSU_STAT
    bpl +
    dex
    bne -
    rep #$20
    .ACCU 16
    inc.w RT_MSUFAIL
    jmp SD_ret                          ; never commit an incomplete page
+
.ENDIF
.IFDEF MSU_DIAG2
    jsl MsuDiagStagedUpload
    jmp SD_advance
.ELSE
    ; Stage the aligned MSU window in WRAM, then DMA the payload to VRAM.
    ; Kept out of this 32 KiB bank (Fight section) to leave ROM room here.
    jsl MsuStageUploadFar
.IFDEF MSU_DIAG
    jsl MsuDiagTransferred
    rep #$20
    .ACCU 16
    ; retain the stream probe used by the MSU diagnostics
    lda scr0
    sta.l $7E0910
    lda scr4
    sta.l $7E0912
.ENDIF
    rep #$20
    .ACCU 16
    jmp SD_advance
.ENDIF
SD_commit:
    ldx fofs
    sep #$20
    .ACCU 8
    lda FP+F_TILEPG,x
    eor #$60.b
    sta FP+F_TILEPG,x                   ; newly-uploaded page becomes visible
    stz FP+F_DMAREQ,x
    ; The tiles just became visible: publish their frame geometry in the
    ; same step so the OAM cells and their offsets always belong together.
    lda FP+F_PXOFF,x
    sta FP+F_XOFF,x
    lda FP+F_PYOFF,x
    sta FP+F_YOFF,x
    lda FP+F_PFLAGS,x
    sta FP+F_FLAGS,x
    rep #$20
    .ACCU 16
    lda scr6
    sta FP+F_META,x                     ; OAM now points at the new metasprite
    lda FP+F_PATKBOX,x
    sta FP+F_ATKBOX,x
    lda FP+F_PHURTBOX,x
    sta FP+F_HURTBOX,x
SD_ret:
    sep #$20
    .ACCU 8
    rts

; opening intro + title + mode menu (same bank so the near jsr calls
; resolve); asset data lives in engine/menus.asm
; ============================================================================
;  SINGLE PLAY / TEAM PLAY / SURVIVOR / PRACTICE campaign system
;  WRAM vars are defined in menucore.asm ($F040-$F051):
;    G_MODE 0 free / 1 single / 2 team / 3 team VS / 4 survivor / 5 practice
;    C_USED bitmask of CPU chars faced     C_WHARF wharf swap consumed
;    C_STAGE confrontation's base stage    STAGEF  forced StagePick idx
;    MATWON  confrontation outcome         T_*     team state
; ============================================================================

; ============================================================================
;  SURVIVOR / PRACTICE support
; ============================================================================

; A(8) = fighter state id -> carry set for special/super states (48-69 and
; 85-89).  Used by the survivor finishing-hit bonus.
IsSpecialState:
    cmp #S_SPECIAL.b
    bcc ISS_no
    cmp #(S_KNEE+10).b                    ; 48-69 = command/fast/knee specials
    bcc ISS_yes
    cmp #S_SUPPER.b
    bcc ISS_no
    cmp #90.b                             ; 85-89 = supers
    bcc ISS_yes
    cmp #S_REVACT.b
    bcc ISS_no
    cmp #(S_EXT_LAST+1).b                 ; 103-106 parry counters,
    bcc ISS_yes                           ; 107-111 imported follow-ups
ISS_no:
    clc
    rts
ISS_yes:
    sec
    rts

; X = victim offset.  Carry set when PRACTICE must ignore the HP loss.
; Both sides are protected in this mode: the CPU/P2 are training dummies.
PracBlock:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #5
    bne PB_no
    sec
    rts
PB_no:
    clc
    rts

; PRACTICE: keep both meters at 3000 (CPU/P2 included).
PracFillPower:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #5
    bne PFP_out
    rep #$20
    .ACCU 16
    lda #3000.w
    sta FP+F_POWER
    sta FP+F_POWER+FP2OFS
    sep #$20
    .ACCU 8
PFP_out:
    rts

; ============================================================================
;  PRACTICE command-list submenu
; ============================================================================
; START opens a scrollable list of the active side's character commands.
; Rows are {sid, category, namePtr, commandPtr}; the seen[] arrays are
; marked by CmdTrack whenever EnterState lands on a listed sid, so the menu
; shows which moves P1/P2 actually performed and which one was the latest.
; The overlay lives in the empty BG3 rows 7-21 and is cleared on close.

CmdListReset:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda #0
    ldx #0
-   .IFDEF PVSNESLIB
    sta.l $7E0000+CL_VARS,x
    .ELSE
    sta.w CL_VARS,x
    .ENDIF
    inx
    inx
    cpx #$80.w                           ; includes PZ_ON/PZ_SEL at +$70
    bne -
    sep #$20
    .ACCU 8
    rts

; X = fighter offset (0/FP2OFS) -> lptr = its command-list header.
; Preserves X, fofs and the caller's register widths.
CmdListPtr:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    phx
    lda fofs
    pha
    stx fofs
    ldy #CH_CMDLIST
    ldx #lptr
    jsr CharPtr
    sep #$20
    .ACCU 8
    ldy #CH_CMDLISTBANK                  ; mass-import lists live in a
    lda [cptr],y                          ;   separately allocated bank
    beq +
    sta lptr+2
+   rep #$20
    .ACCU 16
    pla
    sta fofs
    plx
    plp
    rts

; A(8) = state just entered, fofs = fighter.  Called from EnterState.
CmdTrack:
    php
    rep #$30
    .ACCU 16
    .INDEX 16
    phx
    phy
    pha
    sep #$20
    .ACCU 8
    sta.w CL_TMP
    lda.w G_MODE
    cmp.b #5
    bne CT_out
    lda.w CL_TMP
    cmp #S_PUNCH.b
    bcc CT_out
    cmp.b #98
    bcs CT_out
    ldx fofs
    jsr CmdListPtr
    ldy #0
    lda [lptr],y
    beq CT_out
    sta.w CL_COUNT
    and #$FF.b
    sta.b scr5
    stz.b scr5+1
    ldy #1
    ldx #0
CT_scan:
    cpx.b scr5
    bcs CT_out
    lda [lptr],y
    cmp.w CL_TMP
    beq CT_found
    rep #$20
    .ACCU 16
    tya
    clc
    adc #6
    tay
    sep #$20
    .ACCU 8
    inx
    bra CT_scan
CT_found:
    rep #$20
    .ACCU 16
    lda fofs
    bne CT_side2
    sep #$20
    .ACCU 8
    lda.b #1
    sta.w CL_SEEN1,x
    lda.w CL_TMP
    sta.w CL_LAST1
    rep #$20
    .ACCU 16
    lda framecnt
    sta.w CL_LASTT1
    bra CT_out
CT_side2:
    sep #$20
    .ACCU 8
    lda.b #1
    sta.w CL_SEEN2,x
    lda.w CL_TMP
    sta.w CL_LAST2
    rep #$20
    .ACCU 16
    lda framecnt
    sta.w CL_LASTT2
CT_out:
    rep #$20
    .ACCU 16
    pla
    ply
    plx
    plp
    rts

; Called by the pause menu: return to CONTINUE/COMMAND LIST/EXIT on close.
CmdListOpenFromPause:
    sep #$20
    .ACCU 8
    lda.b #1
    sta.w CL_FROM_PAUSE
    stz.w PZ_ON
    lda.w PZ_SIDE
CmdListOpenSide:
    sta.w CL_SIDE
    lda.b #1
    sta.w CL_OPEN
    stz.w CL_SEL
    stz.w CL_TOP
    jsr CmdListCount
    jmp CmdListDraw

CmdListClose:
    sep #$20
    .ACCU 8
    stz.w CL_OPEN
    lda.w CL_FROM_PAUSE
    beq CL_close_fight
    stz.w CL_FROM_PAUSE
    lda #1
    sta.w PZ_ON
    sta.w PZ_SEL
    jsl PauseDraw
    rep #$20
    .ACCU 16
    rts
CL_close_fight:
    jsr CmdListClearPanel
    sep #$20
    .ACCU 8
    lda #1
    sta.w RT_HUDFULL                    ; list rows live outside the live HUD
    lda huddirty                        ;   bands: upload the cleared map
    ora #HUD_FULL
    sta huddirty
    rep #$20
    .ACCU 16
    rts

; Refresh CL_COUNT + lptr for CL_SIDE's character.
CmdListCount:
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0
    sep #$20
    .ACCU 8
    lda.w CL_SIDE
    beq +
    ldx #FP2OFS
+   jsr CmdListPtr
    ldy #0
    lda [lptr],y
    sta.w CL_COUNT
    rep #$20
    .ACCU 16
    rts

; A(8) = row index -> Y = 1 + index*6 (command-list row byte offset).
CmdListRowOfs:
    rep #$20
    .ACCU 16
    and #$00FF.w
    sta scr4
    asl a
    clc
    adc scr4
    asl a
    clc
    adc #1
    tay
    rts

; A(8) = BG3 row -> A = row*64 (HUDMAP byte offset for column 0).
CmdListRowScr:
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    asl a
    asl a
    asl a
    asl a
    asl a
    rts

; Erase the 15 overlay rows.  Rows 7-21 are unused by the fight HUD.
CmdListClearPanel:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda #0
    ldx #(7*32*2).w
-   sta.w HUDMAP,x
    inx
    inx
    cpx #(22*32*2).w
    bne -
    sep #$20
    .ACCU 8
    rts

CmdListTick:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    ora FP+F_JOYPR+FP2OFS
    sta scr0
    and #(JOY_ST|JOY_B).w
    bne CTK_close
    rep #$20
    .ACCU 16
    lda scr0
    and #JOY_UP.w
    beq CTK_down
    sep #$20
    .ACCU 8
    lda.w CL_SEL
    beq CTK_done
    dec a
    sta.w CL_SEL
    cmp.w CL_TOP
    bcs CTK_up_draw
    sta.w CL_TOP
CTK_up_draw:
    jsr CmdListDraw
    rts
CTK_down:
    rep #$20
    .ACCU 16
    lda scr0
    and #JOY_DN.w
    beq CTK_side
    sep #$20
    .ACCU 8
    lda.w CL_SEL
    inc a
    cmp.w CL_COUNT
    bcs CTK_done
    sta.w CL_SEL
    sec
    sbc.w CL_TOP
    cmp.b #12
    bcc CTK_dn_draw
    lda.w CL_SEL
    sec
    sbc.b #11
    sta.w CL_TOP
CTK_dn_draw:
    jsr CmdListDraw
    rts
CTK_side:
    rep #$20
    .ACCU 16
    lda scr0
    and #(JOY_LF|JOY_RT).w
    beq CTK_done
    sep #$20
    .ACCU 8
    lda.w CL_SIDE
    eor.b #1
    sta.w CL_SIDE
    stz.w CL_SEL
    stz.w CL_TOP
    jsr CmdListCount
    jsr CmdListDraw
    rts
CTK_close:
    jmp CmdListClose
CTK_done:
    sep #$20
    .ACCU 8
    rts

CmdListDraw:
    rep #$30
    .ACCU 16
    .INDEX 16
    jsr CmdListCount
    jsr CmdListClearPanel
    rep #$30
    .ACCU 16
    .INDEX 16

    ; ---- header: COMMAND LIST + side ----
    lda #((7*32+2)*2).w
    sta scr0
    lda #CmdListTitle.w
    sta scr2
    lda #:CmdListTitle
    sta scr2+2
    jsr WriteStr
    rep #$20
    .ACCU 16
    lda #((7*32+29)*2).w
    sta scr0
    sep #$20
    .ACCU 8
    lda.w CL_SIDE
    bne +
    rep #$20
    .ACCU 16
    lda #CmdListSide1.w
    sta scr2
    lda #:CmdListSide1
    sta scr2+2
    bra ++
+   rep #$20
    .ACCU 16
    lda #CmdListSide2.w
    sta scr2
    lda #:CmdListSide2
    sta scr2+2
++  sep #$20
    .ACCU 8
    jsr WriteStr
    ; category legend
    rep #$20
    .ACCU 16
    lda #(8*32*2).w
    sta scr0
    lda #CmdListLegend.w
    sta scr2
    lda #:CmdListLegend
    sta scr2+2
    jsr WriteStr

CDL_list:
    sep #$20
    .ACCU 8
    stz.w CL_ROW
CDL_loop:
    sep #$20
    .ACCU 8
    lda.w CL_ROW
    cmp.b #12
    bcs CDL_help
    clc
    adc.w CL_TOP
    cmp.w CL_COUNT
    bcs CDL_help
    jsr CmdListDrawRow
    inc.w CL_ROW
    bra CDL_loop
CDL_help:
    rep #$20
    .ACCU 16
    lda #((21*32+1)*2).w
    sta scr0
    lda #CmdListHelp.w
    sta scr2
    lda #:CmdListHelp
    sta scr2+2
    sep #$20
    .ACCU 8
    jsr WriteStr
    sep #$20                            ; WriteStr returns with A=16; the
    .ACCU 8                             ; HUD flags below are byte accesses
    lda huddirty                        ; (a 16-bit ORA would swallow the STA
    ora #HUD_FULL                       ; opcode and derail the CPU)
    sta huddirty
    rep #$20
    .ACCU 16
    rts

; A(8) = list index.  Kept out of CmdListDraw's loop so the backward
; branch to CDL_loop stays a short relative branch.
CmdListDrawRow:
    sta.w CL_IDX
    ; rowbase = (index - top + 9) * 64
    lda.w CL_IDX
    sec
    sbc.w CL_TOP
    clc
    adc.b #9
    jsr CmdListRowScr
    sta.w CL_ROWBASE
    ; table row offset = 1 + index*6
    lda.w CL_IDX
    jsr CmdListRowOfs
    sty scr1
    ; cursor at column 0
    lda.w CL_ROWBASE
    sta scr0
    sep #$20
    .ACCU 8
    lda.w CL_IDX
    cmp.w CL_SEL
    bne CDL_cur_used
    lda #CMD_CUR_TILE.b
    bra CDL_cur_store
CDL_cur_used:
    lda.w CL_IDX
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.w CL_SIDE
    bne +
    lda.w CL_SEEN1,x
    bra ++
+   lda.w CL_SEEN2,x
++  beq +
    lda #CMD_USED_TILE.b
    bra CDL_cur_store
+   lda.b #0
CDL_cur_store:
    sta.b scr4
    rep #$20
    .ACCU 16
    lda scr0
    tax
    sep #$20
    .ACCU 8
    lda.b scr4
    sta HUDMAP,x
    lda #ATT_YEL.b
    sta HUDMAP+1,x
    ; name at column 2
    rep #$20
    .ACCU 16
    lda.w CL_ROWBASE
    clc
    adc #4
    sta scr0
    ldy scr1
    iny
    iny
    lda [lptr],y
    sta scr2
    lda lptr+2
    sta scr2+2
    sep #$20
    .ACCU 8
    jsr WriteStr
    ; command at column 18
    rep #$20
    .ACCU 16
    lda.w CL_ROWBASE
    clc
    adc #(18*2)
    sta scr0
    ldy scr1
    iny
    iny
    iny
    iny
    lda [lptr],y
    sta scr2
    lda lptr+2
    sta scr2+2
    sep #$20
    .ACCU 8
    jsr WriteStr
    ; category tag at column 29
    rep #$20
    .ACCU 16
    lda.w CL_ROWBASE
    clc
    adc #(29*2)
    sta scr0
    ldy scr1
    iny
    lda [lptr],y
    and #$00FF.w
    asl a
    tax
    lda.l CmdCatShortTab,x
    sta scr2
    lda tblbank
    sta scr2+2
    sep #$20
    .ACCU 8
    jsr WriteStr
    rep #$20
    .ACCU 16
    rts

; SURVIVOR: build and shuffle the eligible opponent list.  RomFlags marks
; the characters whose sprites are resident in the ROM; without MSU-1 only
; those qualify.
SurvBuild:
    rep #$10
    .INDEX 16
    sep #$20
    .ACCU 8
    ldx #0
    ldy #0
SB_fill:
    cpx #NROSTER.w
    bcs SB_filled
    lda.l HiddenTab,x
    bne SB_fskip0
    txa
    sta.w SURV_LIST,y
    iny
SB_fskip0:
    inx
    bra SB_fill
SB_filled:
    tya
    sta.w SURV_COUNT
    lda.b msuok
    bne SB_shuffle
    lda.w SURV_COUNT
    sta.b scr5
    stz.b scr5+1
    ldx #0
    ldy #0
SB_fnext:
    cpx scr5
    bcs SB_fdone
    lda.w SURV_LIST,x
    stx.b scr3
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l RomFlags,x
    sta.b scr4
    ldx.b scr3
    lda.b scr4
    beq SB_fskip                          ; MSU-only char: drop it
    lda.w SURV_LIST,x
    sta.w SURV_LIST,y
    iny
SB_fskip:
    inx
    bra SB_fnext
SB_fdone:
    tya
    sta.w SURV_COUNT
SB_shuffle:
    lda.w SURV_COUNT
    beq SB_done
    sta.b scr5
    stz.b scr5+1
    ldx #0
SB_sloop:
    cpx scr5
    bcs SB_boss
    stx.b scr3                           ; i
    inc.b rng
    lda.b rng                            ; j = (rng ^ framecnt) mod count
    eor.b framecnt
    sta.b scr0
SB_mod:
    lda.b scr0
    cmp.w SURV_COUNT
    bcc SB_mod_ok
    sec
    sbc.w SURV_COUNT
    sta.b scr0
    bra SB_mod
SB_mod_ok:
    sta.b scr1                           ; j
    stz.b scr1+1
    ldx.b scr3
    lda.w SURV_LIST,x
    sta.b scr2
    ldx.b scr1
    lda.w SURV_LIST,x
    ldx.b scr3
    sta.w SURV_LIST,x
    lda.b scr2
    ldx.b scr1
    sta.w SURV_LIST,x
    ldx.b scr3
    inx
    bra SB_sloop
SB_boss:
    lda.w SURV_COUNT
    beq SB_done
    sta.b scr5
    stz.b scr5+1
    ldx #0
SB_boss_find:
    cpx scr5
    bcs SB_done
    lda.w SURV_LIST,x
    cmp #14.b                             ; Omega Rugal is the final boss
    beq SB_boss_found
    inx
    bra SB_boss_find
SB_boss_found:
    stx.b scr3
SB_boss_shift:
    ldx.b scr3
    inx
    cpx scr5
    bcs SB_boss_put
    lda.w SURV_LIST,x
    dex
    sta.w SURV_LIST,x
    inx
    stx.b scr3
    bra SB_boss_shift
SB_boss_put:
    lda.w SURV_COUNT
    dec a
    tax
    lda #14.b
    sta.w SURV_LIST,x
SB_done:
    rep #$10
    .INDEX 16
    rts

; SURVIVOR: sel1/sel2 <- SURV_LIST[C_IDX] for the human side's opponent.
SurvPickFoe:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w C_IDX
    and #$00FF.w
    tax
    lda.w SURV_LIST,x
    and #$00FF.w
    sta.b scr0
    sep #$20
    .ACCU 8
    cmp #14.b                             ; final Omega Rugal: boss stage
    bne SPF_stage_done
    lda #5
    sta.w C_STAGE
SPF_stage_done:
    lda.w C_HUMAN_SIDE
    bne SPF_cpu1
    lda.b scr0
    sta.b sel2
    bra SPF_done
SPF_cpu1:
    lda.b scr0
    sta.b sel1
SPF_done:
    rep #$10
    .INDEX 16
    rts

; SURVIVOR: stash the human HP before the round result resets anything.
SurvSaveHP:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #4
    bne SVH_out
    rep #$20
    .ACCU 16
    lda.w C_HUMAN_SIDE
    and #$00FF.w
    beq +
    lda FP+F_HP+FP2OFS
    bra ++
+   lda FP+F_HP
++  sep #$20
    .ACCU 8
    sta.w SURV_HP
SVH_out:
    rts

; A timer-over round has no finishing blow.
SurvClearHit:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #4
    bne SCH_out
    stz.w SURV_KOSP
SCH_out:
    rts

; A(8) = attacker state.  Latch the human's latest connected hit:
; 0 = normal, 1 = special/super, 2 = special/super with the human above
; 50% HP before the blow (SURVIVOR next-opponent bonus).
SurvTrackHit:
    sep #$20
    .ACCU 8
    pha
    lda.w G_MODE
    cmp #4
    bne STH_out
    lda.w C_HUMAN_SIDE
    beq STH_p1
    lda.b aofs
    cmp #FP2OFS.b
    bne STH_out
    bra STH_check
STH_p1:
    lda.b aofs
    bne STH_out
STH_check:
    pla
    jsr IsSpecialState
    bcc STH_clear
    rep #$20
    .ACCU 16
    ldx aofs                              ; human attacker
    lda FP+F_HP,x
    cmp #101.w                            ; human above 50% at the finish?
    sep #$20
    .ACCU 8
    bcc +
    lda #2                                ; yes: next fight starts full
    bra STH_store
+   lda #1
    bra STH_store
STH_clear:
    lda #0
STH_store:
    sta.w SURV_KOSP
    rts
STH_out:
    pla
    rts

; A(8) = projectile SPK_ATTR.  Same latch for special/super projectiles,
; using bit5 (launch state) and bit6 (owner is P2).
SurvTrackProj:
    sep #$20
    .ACCU 8
    pha
    lda.w G_MODE
    cmp #4
    bne STP_out
    pla
    pha
    and #$40.b
    beq STP_owner_p1
    lda.w C_HUMAN_SIDE
    cmp #1
    bne STP_out
    bra STP_check
STP_owner_p1:
    lda.w C_HUMAN_SIDE
    bne STP_out
STP_check:
    pla
    and #$20.b
    beq STP_clear
    phx                                   ; keep the caller's projectile slot
    lda.w C_HUMAN_SIDE
    beq STP_hp_p1
    ldx #FP2OFS.w
    bra STP_hp_read
STP_hp_p1:
    ldx #0
STP_hp_read:
    rep #$20
    .ACCU 16
    lda FP+F_HP,x                         ; human HP at the projectile finish
    cmp #101.w
    sep #$20
    .ACCU 8
    bcc STP_hp_low
    lda #2
    bra STP_hp_store
STP_hp_low:
    lda #1
STP_hp_store:
    plx
    sta.w SURV_KOSP
    rts
STP_clear:
    lda #0
STP_store:
    sta.w SURV_KOSP
    rts
STP_out:
    pla
    rts

; StartFight HP/meter setup for the campaign variants.
CampInitHP:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    cmp #4
    beq CIH_surv
    cmp #5
    beq CIH_prac
    rts
CIH_surv:
    stz.w SURV_KOSP
    rep #$20
    .ACCU 16
    lda.w SURV_HP
    and #$00FF.w
    bne +
    lda #1                                ; safety: never start a round at 0
+   sta.b scr0
    lda.w C_HUMAN_SIDE
    and #$00FF.w
    beq CIH_surv_p1
    lda.b scr0
    sta FP+F_HP+FP2OFS
    lda #MAXHP.w
    sta FP+F_HP
    bra CIH_out
CIH_surv_p1:
    lda.b scr0
    sta FP+F_HP
    lda #MAXHP.w
    sta FP+F_HP+FP2OFS
CIH_out:
    sep #$20
    .ACCU 8
    rts
CIH_prac:
    rep #$20
    .ACCU 16
    lda #3000.w
    sta FP+F_POWER
    sta FP+F_POWER+FP2OFS
    bra CIH_out

; A -> A mod NPOOL and A -> A mod NSTAGES live in the FightMenuTail section
; (see menucore.asm) -- the battle bank is full and both sections share the
; bank, so their near callers still resolve.

BitMask3: .db 1, 2, 4                     ; sel -> C_USED bit

CampReset:
    sep #$20
    .ACCU 8
    stz.w G_MODE
    stz.w C_IDX
    stz.w C_PVP
    stz.w C_HUMAN_SIDE
    stz.w C_WHARF
    stz.w MATWON
    stz.w T_STEP
    stz.w T_I1
    stz.w T_I2
    stz.w T_SWAP
    stz.w T_PICK_SIDE
    stz.w T_START
    stz.w T_LASTFRAME
    stz.w CPU_USED_COUNT
    stz.w MUSIC_VALID
    stz.w FUS_VALID                       ; new match: fresh FUSION carry
    stz.w FUS_CARRY
    stz.w FUS_CARRY+1
    stz.w FUS_CARRY+FP2OFS
    stz.w FUS_CARRY+FP2OFS+1
    ; drop the fight camera too: ShakeScroll runs every frame even on the
    ; title/menu screens, so a stale camx from the last bout used to push
    ; BG1 half a screen sideways on return to "PRESS START"
    stz.w FP+F_X
    stz.w FP+F_X+1
    stz.w FP+F_X+FP2OFS
    stz.w FP+F_X+FP2OFS+1
    stz.b camx
    stz.b camx+1
    stz.b shaketmr
    lda #$FF.b
    sta.w STAGEF
    rts

; C_STAGE <- random permitted stage (Rugal's stage 5 excluded).
CampPickStage:
    sep #$20
    .ACCU 8
    inc rng
    lda.b rng
    eor.b framecnt
    jsr ModStg
    cmp #5
    beq CampPickStage                     ; Rugal's stage is boss-only
    sta.w C_STAGE
    rts

; A candidate char and scr6 = used-count -> carry set if already used.
CampIsUsed:
    sta.b scr0
    sep #$10
    .INDEX 8
    ldy #0
-   cpy.b scr6
    bcs +
    lda.w CPU_USED,y
    cmp.b scr0
    beq CampUsedYes
    iny
    bra -
+   clc
    rts
CampUsedYes:
    sec
    rts

; sel2 <- random common CPU character, excluding every previous opponent.
CampPickSel2:
    lda.w G_MODE
    cmp #4
    bne +
    jmp SurvPickFoe
+   sep #$30
    .ACCU 8
    .INDEX 8
    inc rng
    lda.b rng
    eor.b framecnt
    jsr ModPool
    tax
    stx.b scr1
    lda.w CPU_USED_COUNT
    sta.b scr6
    ldx.b scr1
    lda.l CpuPool,x
    jsr CampIsUsed
    bcc CPS_accept
    ldx.b scr1
    inx
    cpx #NPOOL.b
    bcc +
    ldx #0
+   stx.b scr1
    bra CPS_try
CPS_accept:
    lda.b msuok
    bne CPS_legal
    ldx.b scr0
    lda.l RomFlags,x
    beq CPS_advance                       ; MSU-only foe without MSU
CPS_legal:
    lda.b scr0
    lda.w C_HUMAN_SIDE
    bne CPS_cpu_p1
    lda.b scr0
    sta.b sel2                            ; CPU takes P2 when P1 carries on
    bra CPS_record
CPS_cpu_p1:
    lda.b scr0
    sta.b sel1                            ; CPU takes P1 when P2 carries on
CPS_record:
    ldx.b CPU_USED_COUNT
    sta.w CPU_USED,x
    lda.w CPU_USED_COUNT
    inc a
    sta.w CPU_USED_COUNT
    rts
CPS_try:
    lda.l CpuPool,x
    jsr CampIsUsed
    bcs CPS_advance
    bra CPS_accept
CPS_advance:
    ldx.b scr1
    inx
    cpx #NPOOL.b
    bcc +
    ldx #0
+   stx.b scr1
    bra CPS_try

; T_TEAM2 <- three random, distinct CpuPool fighters; history covers all
; prior campaign teams. CpuPool excludes Rugal and Omega Rugal.
CampPickTeam2:
    sep #$30
    .ACCU 8
    .INDEX 8
    stz.b scr5                            ; member index
CT2_member:
    inc rng
    lda.b rng
    eor.b framecnt
    jsr ModPool
    sta.b scr1                            ; initial pool index
    lda.w CPU_USED_COUNT
    sta.b scr6
CT2_try:
    ldx.b scr1
    lda.l CpuPool,x
    jsr CampIsUsed
    bcc CT2_accept
    ldx.b scr1
    inx
    cpx #NPOOL.b
    bcc +
    ldx #0
+   stx.b scr1
    bra CT2_try
CT2_accept:
    lda.b scr0
    ldy.b scr5
    lda.w C_HUMAN_SIDE
    bne CT2_cpu_side1
    lda.b scr0
    sta.w T_TEAM2,y
    bra CT2_store_history
CT2_cpu_side1:
    lda.b scr0
    sta.w T_TEAM1,y
CT2_store_history:
    ldx.b CPU_USED_COUNT
    lda.b scr0
    sta.w CPU_USED,x
    lda.w CPU_USED_COUNT
    inc a
    sta.w CPU_USED_COUNT
    inc.b scr5
    lda.b scr5
    cmp #3
    bcc CT2_member
    rts

; Called once when the selection locks -> fight 1 of a campaign.
CampStart:
    sep #$30
    .ACCU 8
    .INDEX 8
    stz.w C_IDX
    stz.w C_PVP
    stz.w C_HUMAN_SIDE
    stz.w MATWON
    stz.w C_WHARF
    stz.w T_SWAP
    ldx #0
-   lda #$FF.b
    sta.w CPU_USED,x
    inx
    cpx #18.b
    bcc -
    stz.w CPU_USED_COUNT
    stz.b wins1
    stz.b wins2
    lda #1
    sta.b roundno
    jsl ApplyDifficulty                   ; OPTIONS level -> AI_LEVEL
    jsr CampPickStage
    lda.w G_MODE
    cmp #2
    beq CS_team
    cmp #3
    beq CS_team
    cmp #4
    beq CS_survivor
    bra CS_solo
CS_survivor:
    jsr SurvBuild                         ; shuffled, MSU-aware roster
    stz.w C_IDX
    lda #MAXHP.b
    sta.w SURV_HP
    stz.w SURV_KOSP
CS_solo:
    lda.b cpu2
    beq CS_human_challenger
    lda.w G_MODE
    cmp #4
    bne +
    jsr CampPickSel2                      ; survivor: first random opponent
+   lda.b sel2
    sta.w CPU_USED                        ; record first CPU opponent
    lda #1.b
    sta.w CPU_USED_COUNT
    rep #$10
    .INDEX 16
    rts
CS_human_challenger:
    lda #1
    sta.w C_PVP                           ; P2 joined: winner starts CPU route
    stz.w CPU_USED_COUNT
    rep #$10
    .INDEX 16
    rts
CS_team:
    stz.w T_I1                            ; team: build the first CPU trio
    stz.w T_I2
    lda #3
    sta.w T_N2
    lda.b cpu2
    beq CS_team_challenger
    jsr CampPickTeam2
    stz.w T_STEP
    rep #$10
    .INDEX 16
    rts
CS_team_challenger:
    lda #1
    sta.w C_PVP
    stz.w CPU_USED_COUNT
    stz.w T_STEP
    rep #$10
    .INDEX 16
    rts

; Player won the current confrontation: next foe, or endings after Rugal.
CampNext:
    sep #$20
    .ACCU 8
    stz.w MUSIC_VALID                    ; winner theme ran; reload next battle
    lda.w G_MODE
    cmp #4
    beq CNF_survivor
    inc.w C_IDX
    lda.w C_IDX
    cmp #7
    bcc +
    jmp EndEnter                          ; Rugal beaten -> ending1
+   cmp #6
    beq CNF_boss
    stz.w C_WHARF                         ; common confrontation 2-6
    jsr CampPickStage
    lda.w G_MODE
    cmp #2
    beq +
    jsr CampPickSel2                      ; single: next unused CPU char
    jmp CNF_go
+   jsr CampPickTeam2                     ; team: fresh CPU trio
    stz.w T_I1                            ;   player trio back to full health
    stz.w T_I2
    jmp CNF_go
CNF_survivor:
    lda.w SURV_KOSP
    beq CNF_surv_next
    cmp #2
    beq CNF_surv_full
    lda.w SURV_HP                          ; +50% of the remaining HP
    lsr a
    clc
    adc.w SURV_HP
    cmp #MAXHP.b
    bcc +
    lda #MAXHP.b
+   sta.w SURV_HP
    bra CNF_surv_next
CNF_surv_full:
    lda #MAXHP.b                          ; human was above 50%: fill the bar
    sta.w SURV_HP
CNF_surv_next:
    inc.w C_IDX
    lda.w C_IDX
    cmp.w SURV_COUNT
    bcc CNF_surv_more
    lda.w SURV_COUNT
    dec a
    sep #$10
    .INDEX 8
    tax
    lda.w SURV_LIST,x
    cmp #14.b                             ; Omega Rugal was the final foe?
    rep #$10
    .INDEX 16
    beq CNF_surv_ending
    jmp EndEnter                          ; no boss available: normal ending
CNF_surv_ending:
    jmp SvEndEnter
CNF_surv_more:
    stz.w C_WHARF
    jsr CampPickStage
    jsr CampPickSel2                      ; SURV_LIST[C_IDX]
    bra CNF_go
CNF_boss:
    stz.w C_WHARF
    lda #5                                ; Rugal's exclusive stage
    sta.w C_STAGE
    lda.w G_MODE
    cmp #2
    beq CNF_team_boss
    cmp #3
    beq CNF_team_boss
    lda.w C_HUMAN_SIDE
    bne CNF_boss_single_cpu1
    lda.b msuok                          ; Rugal (3) streams from MSU-1;
    beq CNF_boss_single_omega2           ;   without it, skip to Omega (14)
    lda #3.b
    sta.b sel2                           ; single: Rugal first, then Omega
    bra CNF_go
CNF_boss_single_omega2:
    lda #14.b
    sta.b sel2
    bra CNF_go
CNF_boss_single_cpu1:
    lda.b msuok
    beq CNF_boss_single_omega1
    lda #3.b
    sta.b sel1
    bra CNF_go
CNF_boss_single_omega1:
    lda #14.b
    sta.b sel1
    bra CNF_go
CNF_team_boss:
    lda.w C_HUMAN_SIDE
    bne CNF_team_cpu1
    lda #3.b
    sta.w T_TEAM2                         ; Rugal
    lda #14.b
    sta.w T_TEAM2+1                       ; Omega Rugal
    bra CNF_team_boss_ready
CNF_team_cpu1:
    lda #3.b
    sta.w T_TEAM1
    lda #14.b
    sta.w T_TEAM1+1
CNF_team_boss_ready:
    stz.w T_I1                            ;   remaining player members enter
    stz.w T_I2
    lda #2
    sta.w T_N2
CNF_go:
    stz.b wins1
    stz.b wins2
    lda #1
    sta.b roundno
    jsr StartFight
    rts

; Match-over resolution for campaign modes (from TitleTick, acc8).
CampResolve:
    sep #$20
    .ACCU 8
    lda.w C_PVP
    beq CR_regular
    ; The first campaign match was P1 vs P2. Keep the winner's pad and
    ; replace the other side with the first CPU opponent.
    lda.w G_MODE
    cmp #1
    beq CR_pvp_solo
    cmp #4
    beq CR_pvp_solo
    cmp #5
    beq CR_pvp_solo
    bra CR_pvp_team
CR_pvp_solo:
    lda wins1
    cmp wins2
    bcc CR_pvp_p2
    lda #0
    sta.w C_HUMAN_SIDE
    bra CR_pvp_begin
CR_pvp_p2:
    lda #1
    sta.w C_HUMAN_SIDE
    bra CR_pvp_begin
CR_pvp_team:
    lda.w MATWON
    bne CR_pvp_p1
    lda #1                                ; side 2 team survived
    sta.w C_HUMAN_SIDE
    bra CR_pvp_begin
CR_pvp_p1:
    stz.w C_HUMAN_SIDE                   ; side 1 team survived
CR_pvp_begin:
    stz.w C_PVP
    stz.b wins1
    stz.b wins2
    lda.w C_HUMAN_SIDE
    beq +
    lda #1
    sta.b cpu1                            ; CPU takes P1; P2 winner remains human
    stz.b cpu2
    bra CR_cpu_configured
+  stz.b cpu1
    lda #1
    sta.b cpu2                            ; CPU takes P2; P1 winner remains human
CR_cpu_configured:
    jsr CampPickStage
    lda.w G_MODE
    cmp #2
    beq CR_pvp_team_cpu
    jsr CampPickSel2
    bra CR_pvp_launch
CR_pvp_team_cpu:
    stz.w T_I1
    stz.w T_I2
    lda #3
    sta.w T_N2
    jsr CampPickTeam2
CR_pvp_launch:
    lda #1
    sta.b roundno
    stz.b nextflag
    stz.w MUSIC_VALID
    jsr StartFight
    rts
CR_regular:
    lda.w G_MODE
    cmp #1
    beq CR_solo
    cmp #4
    beq CR_solo
    cmp #5
    beq CR_solo
    bra CR_team
CR_solo:
    lda.w C_HUMAN_SIDE
    bne CR_single_p2
    lda.b wins1                           ; solo: best-of-3 winner check
    cmp.b wins2
    bcc CR_lost
    bra CR_won
CR_single_p2:
    lda.b wins2
    cmp.b wins1
    bcc CR_lost
    bra CR_won
CR_team:
    lda.w C_HUMAN_SIDE
    bne CR_team_p2
    lda.w MATWON                          ; 1 = side 2 eliminated
    beq CR_lost
    bra CR_won
CR_team_p2:
    lda.w MATWON                          ; 0 = side 1 eliminated
    bne CR_lost
CR_won:
    jsr CampNext                          ; next foe (or jmp -> EndEnter)
    rts
CR_lost:
    lda.w G_MODE
    cmp #4.b
    beq CR_lost_survivor                  ; SURVIVAL: straight back to the title
    cmp #1.b
    beq CR_lost_youlose
    cmp #2.b
    beq CR_lost_youlose
    bra CR_lost_legacy                    ; PRACTICE keeps the select fallback
CR_lost_youlose:
    jsl YouLoseEnter                      ; keep C_IDX/C_STAGE/opponents intact
    rts
CR_lost_survivor:
    jsr CampReset
    stz.b wins1
    stz.b wins2
    lda #1
    sta.b roundno
    stz.b nextflag
    jmp TitleEnter
CR_lost_legacy:
    jsr CampReset                         ; defeat -> existing select flow
    stz.b wins1
    stz.b wins2
    lda #1
    sta.b roundno
    stz.b nextflag
    lda #SONG_KOF.b                       ; campaign defeat also returns with
    jsr MusPlaySong                       ;   the select theme (voice follows
    jsr ShowSelect                        ;   from ShowSelect's sfxtoken)
    rep #$20
    .ACCU 16
    lda #5
    sta.b gamestate
    rts

; Called by StartFight before StagePick: resolves STAGEF per mode/round.
CampStage:
    sep #$20
    .ACCU 8
    lda.w G_MODE
    beq CS_vs
    cmp #1
    beq CS_force
    cmp #2
    beq CS_force
    cmp #3
    beq CS_force
    cmp #4
    beq CS_force
    cmp #5
    beq CS_force
CS_random:
    lda #$FF.b                            ; free/versus: StagePick stays random
    sta.w STAGEF
    rts
CS_vs:
    lda.b roundno
    cmp #1.b
    beq CS_random                         ; choose a fresh stage for the match
    lda.b stageidx
    sta.w STAGEF                          ; Single VS keeps it for every round
    rts
CS_force:
    lda.w C_STAGE                         ; fixed for all rounds/members
    sta.w STAGEF
    rts

; Team play: a member fell -> eliminate, recover winner, swap in next.
; Called from RoundEnd (acc8) instead of the best-of-3 scoring.
TeamRoundEnd:
    rep #$10                            ; pin index16: callers differ
    .INDEX 16
    stz.w MATWON
    lda.b roundwin
    cmp #1
    beq TRE_p2out                         ; P1 won -> P2 member out
    cmp #2
    beq TRE_p1out
    lda #3                                ; draw: both members out
    bra TRE_out
TRE_p2out:
    lda #2
    bra TRE_out
TRE_p1out:
    lda #1
TRE_out:
    sta.w T_SWAP                          ; sides to swap (bit0 P1, bit1 P2)
    and #1
    beq TRE_no_p1_swap
    inc.w T_I1
TRE_no_p1_swap:
    lda.w T_SWAP
    and #2
    beq TRE_no_p2_swap
    inc.w T_I2
TRE_no_p2_swap:
    lda.w C_HUMAN_SIDE
    bne TRE_human_p2
    lda.w T_I1                            ; P1 carries the campaign
    cmp #3
    bcs TRE_side1_out
    lda.w T_I2                            ; P2 is the CPU team
    cmp.w T_N2
    bcs TRE_side2_out
    bra TRE_continue
TRE_human_p2:
    lda.w T_I2                            ; P2 carries the campaign
    cmp #3
    bcs TRE_side2_out
    lda.w T_I1                            ; P1 is the CPU team
    cmp.w T_N2
    bcs TRE_side1_out
    bra TRE_continue
TRE_side1_out:
    lda #0
    bra TRE_over
TRE_side2_out:
    lda #1
TRE_over:
    sta.w MATWON
    cmp.w C_HUMAN_SIDE                  ; out side == human side -> human lost
    beq TRE_show_winner
    lda.w G_MODE
    cmp #2.b                            ; only TEAM PLAY resolves a campaign
    bne TRE_show_winner
    lda.w C_IDX
    cmp #6.b                            ; boss team out (Omega was last)
    beq TRE_omega_ending
TRE_show_winner:
    ; Team play never scores round wins (RoundEnd hands every member KO to
    ; TeamRoundEnd), so wins1/wins2 are still 0-0 here and DrawBanner would
    ; pick DRAW instead of the survivor's WINS banner/quote.  MATWON holds the
    ; eliminated side: score the other side (wins1,x with x=survivor) 2.
    sep #$20
    .ACCU 8
    lda #0
    xba                                 ; clear B so TAX indexes with 0-1 only
    lda.w MATWON
    eor #1
    tax
    lda #2
    sta.b wins1,x
    sta.b nextflag
    jmp ShowTitle
TRE_omega_ending:
    jsl BossEndingFar                   ; no winner banner: fade -> ending1
    rts
TRE_continue:
    lda.b roundwin                        ; winner keeps fighting ->
    cmp #1                                ;   KOF'98 time-based HP recovery
    bne +
    ldx #0
    jsr TeamRecover
+   lda.b roundwin
    cmp #2
    bne +
    ldx #FP2OFS
    jsr TeamRecover
+   lda.w T_I1                            ; player's 3rd member entering a
    cmp #2                                ;   wharf stage -> arm the A/B
    bne +                                 ;   swap for CampStage
    lda.w C_WHARF
    bne +
    lda #1
    sta.w C_WHARF
+   lda #1
    sta.b nextflag                        ; intermission -> TeamSwap
    jmp ShowTitle

; scr6 = fofs.  Winner recovery: HP += recoveryBonus, capped at 144.
TeamRecover:
    rep #$30
    .ACCU 16
    .INDEX 16
    stx scr6
    lda FP+F_HP,x
    pha
    lda.b rsecs
    and #$00FF.w
    ldx #0
-   cmp #10.w
    bcc +
    sbc #10.w
    inx
    bra -
+   txa
    asl a
    asl a                                 ; 4 * floor(sec/10)
    clc
    adc #12.w
    cmp #32.w
    bcc +
    lda #32.w
+   clc
    adc 1,s                               ; + current HP
    cmp #144.w
    bcc +
    lda #MAXHP.w
+   ldx scr6
    sta FP+F_HP,x
    pla
    sep #$20
    .ACCU 8
    rts

; Member-change fight entry (T_SWAP bit0/bit1).  Resets only the dead
; side(s); the survivor keeps HP, meter and position.  -> gs 4 intro.
TeamSwap:
    sep #$20
    .ACCU 8
    lda #0                              ; vblank ISR clobbers DP scratch
    sta.l NMITIMEN                      ;   (lptr/cptr/boxp) -> hold it off
    rep #$10                            ; pin index16: callers differ
    .INDEX 16
    lda.w T_SWAP
    and #1
    beq +
    ldx #0
    jsr TeamMemberIn
+   lda.w T_SWAP
    and #2
    beq +
    ldx #FP2OFS
    jsr TeamMemberIn
+   rep #$20
    .ACCU 16
    ; TeamMemberIn spawns at the fixed home slot (80/176).  The survivor
    ; keeps its position, so when it is near that slot the newcomer lands
    ; on top of it ("colado") and its fixed facing can point away from the
    ; opponent for the whole intro.  Put the newcomer a full round-start
    ; gap (96 px) from the survivor instead, on its home side when the
    ; stage allows, and make both face each other.
    lda.w T_SWAP
    and #$0003.w
    cmp #$0003.w
    beq TS_face                         ; draw: 80/176 already 96 px apart
    and #$0001.w
    beq TS_place_p2
    lda FP+F_X+FP2OFS.w                 ; survivor P2
    cmp #((STAGE_L+TEAM_SPAWN_SEP)<<8).w
    bcs TS_place_p1_left                ; room on the left: enter there
    clc
    adc #(TEAM_SPAWN_SEP<<8).w          ; x2 < 120 -> stays inside the stage
    bra TS_place_p1_store
TS_place_p1_left:
    sec
    sbc #(TEAM_SPAWN_SEP<<8).w
TS_place_p1_store:
    sta FP+F_X.w
    bra TS_face
TS_place_p2:
    lda FP+F_X.w                        ; survivor P1
    cmp #((STAGE_R-TEAM_SPAWN_SEP)<<8).w
    beq TS_place_p2_right
    bcs TS_place_p2_left                ; no room on the right: enter left
TS_place_p2_right:
    clc
    adc #(TEAM_SPAWN_SEP<<8).w          ; x1 <= 136 -> stays inside the stage
    bra TS_place_p2_store
TS_place_p2_left:
    sec
    sbc #(TEAM_SPAWN_SEP<<8).w
TS_place_p2_store:
    sta FP+F_X+FP2OFS.w
TS_face:
    lda FP+F_X.w
    cmp FP+F_X+FP2OFS.w
    bcs +
    lda #1                              ; P1 left: faces right, P2 left
    sta FP+F_FACING.w
    lda #$FFFF.w
    sta FP+F_FACING+FP2OFS.w
    bra ++
+   lda #$FFFF.w                        ; P1 right: faces left, P2 right
    sta FP+F_FACING.w
    lda #1
    sta FP+F_FACING+FP2OFS.w
++  sep #$20
    .ACCU 8
    lda.b roundwin                        ; survivor back to stand state
    cmp #1                                ;   (draw: both just entered)
    bne +
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0
    stx fofs
    lda #S_STAND.w
    jsr EnterState
    bra TS_hud
+   sep #$20                              ; .ACCU must be re-declared at the
    .ACCU 8                               ;   join: the taken branch above
    cmp #2                                ;   emitted .ACCU 16
    bne TS_hud
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #FP2OFS
    stx fofs
    lda #S_STAND.w
    jsr EnterState
    sep #$20
    .ACCU 8
TS_hud:
    sep #$20
    .ACCU 8
    lda #$8F.b                          ; VRAM/CGRAM uploads need the blank
    sta.l INIDISP                       ;   context (same as PpuInit)
    jsr LoadPortraits
    sep #$20
    .ACCU 8
    lda #$0F.b
    sta.l INIDISP
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx #0                              ; full rebuild: the intermission's
    txa                                 ;   ROUND digit + "1P:"/"2P:" rows
-   sta HUDMAP,x                        ;   must not linger into the fight
    inx
    inx
    cpx #2048.w
    bne -
    ldx #0
-   lda.l HudTopMap,x
    sta HUDMAP,x
    inx
    inx
    cpx #(7*32*2).w
    bne -
    jsr PortraitMap
    ldx #0
-   lda.l HudBottomMap,x
    sta HUDMAP+(23*32*2),x
    inx
    inx
    cpx #(4*32*2).w
    bne -
    lda #((4*32+5)*2).w                   ; name plates: fight.def row 4
    sta scr0
    ldx #0
    stx fofs
    ldy #CH_NAME
    ldx #scr2
    jsr NamePtr
    jsr WriteStr
    lda #((4*32+23)*2).w
    sta scr0
    ldx #FP2OFS
    stx fofs
    ldy #CH_NAME
    ldx #scr2
    jsr NamePtr
    jsr WriteStr
    sep #$20
    .ACCU 8
    rep #$30
    .ACCU 16
    .INDEX 16
    jsr DrawBars
    jsr DrawWins
    jsr DrawLevel
    jsr DrawTimer                       ; keep the clock lit through the swap
    sep #$20
    .ACCU 8
    stz.w T_SWAP
    lda #$81.b                            ; NMI + autojoy back on
    sta.l NMITIMEN
    lda #4                                ; -> IntroTick until new member
    sta.b gamestate                       ;   finishes its entrance
    lda huddirty
    ora #HUD_FULL
    sta huddirty
    rts

; X = fofs (0 P1 / FP2OFS P2).  Loads T_TEAMx[T_Ix] into the fighter block,
; full HP, intro entrance.  Preserves Y.
TeamMemberIn:
    sep #$20
    .ACCU 8
    rep #$30
    .ACCU 16
    .INDEX 16
    cpx #0
    bne +
    lda.w T_I1                            ; read team sel for this side
    and #$00FF.w
    tay                                   ; T_I1 is a byte variable
    lda.w T_TEAM1,y
    and #$00FF.w
    sep #$20                              ; sel1/sel2 are adjacent DP bytes:
    .ACCU 8                               ;   a 16-bit store here cleared the
    sta.b sel1                            ;   other side's sel and made
    rep #$20                              ;   LoadCharPals upload Kyo's
    .ACCU 16                              ;   palette for the CPU
    lda #80<<8.w
    bra ++
+   lda.w T_I2
    and #$00FF.w
    tay                                   ; T_I2 is a byte variable
    lda.w T_TEAM2,y
    and #$00FF.w
    sep #$20
    .ACCU 8
    sta.b sel2
    rep #$20
    .ACCU 16
    lda #176<<8.w
++  sta FP+F_X,x                          ; spawn on the proper side
    stz FP+F_Y,x
    stz FP+F_VX,x
    stz FP+F_VY,x
    stz FP+F_GRAB,x
    stz FP+F_HITVX,x
    stz FP+F_HITVY,x
    stz FP+F_META,x
    sep #$20
    .ACCU 8
    stz FP+F_TFLAGS,x
    stz FP+F_DMAREQ,x
    stz FP+F_DMAPOS,x
    stz FP+F_TILEPG,x
    stz FP+F_MAX,x
    lda #$FF.b
    sta FP+F_PSPRID,x
    sta FP+F_PSPRID_H,x
    stz FP+F_PXOFF,x
    stz FP+F_PYOFF,x
    stz FP+F_PFLAGS,x
    stz FP+F_HIST,x
    stz FP+F_LASTCT,x
    rep #$20
    .ACCU 16
    cpx #0
    beq +
    lda #$FFFF.w                          ; P2 faces left
    bra ++
+   lda #0                                ; P1 faces right
++  sta FP+F_FACING,x
    lda #MAXHP.w                          ; the newcomer is fresh
    sta FP+F_HP,x
    lda FUS_CARRY,x                       ; FUSION: inherit carried meter
    sta FP+F_POWER,x
    lda #30.w
    sta FUS_JUGGLE,x
    sep #$20
    .ACCU 8
    stz FUS_DIZZY,x
    stz FUS_DIZZYT,x
    stz FUS_COVER,x
    rep #$20
    .ACCU 16
    cpx #0                                ; sel -> descriptor + table bank
    beq +
    lda.b sel2
    bra ++
+   lda.b sel1
++  and #$00FF.w
    stx scr6                              ; save fofs; lda.l supports only ,x
    asl a
    tax
    lda.l CharSelTab,x
    ldx scr6
    sta FP+F_CHAR,x
    rep #$20
    .ACCU 16
    cpx #0
    beq +
    lda.b sel2
    bra ++
+   lda.b sel1
++  and #$00FF.w                          ; sel is a byte; clear stale A-high
    tax
    sep #$20
    .ACCU 8
    lda.l BankSelTab,x
    ldx scr6
    sta FP+F_TBANK,x
    jsr LoadCharPals                      ; per-side OBJ palettes (clobbers X)
    jsr ProjFxLoadBoth                    ; reload effects for new active members
    rep #$30
    .ACCU 16
    .INDEX 16
    ldx scr6                              ; restore fofs (LCP leaves X=1)
    stx fofs
    lda #S_INTRO.w                        ; mugen 191 entrance
    jsr EnterState
    sep #$20
    .ACCU 8
    rts

; Team select tick: P1 locks three members, then the CPU trio is built
; and the first fight starts.  Same cell cursor as the regular select;
; START joins the side, B undoes the last pick (or hands P1 to the CPU
; before the first pick).  Picked members get a dim fill mark.
TeamSelTick:
    rep #$30
    .ACCU 16
    .INDEX 16
    sep #$20
    .ACCU 8
    lda.w T_START
    beq TTS_active
    lda.b framecnt
    cmp.w T_LASTFRAME
    beq TTS_wait
    sta.w T_LASTFRAME
    dec.w T_START
    bne TTS_wait
    jsr StartFight
    rts
TTS_wait:
    rts
TTS_active:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda.w T_PICK_SIDE
    and #$00FF.w
    beq TTS_p1_active
    jmp TTS_p2_active
TTS_p1_active:
    ; ---------- START: P1 joins ----------
    lda FP+F_JOYPR
    and #JOY_ST.w
    beq +
    sep #$20
    .ACCU 8
    lda.b cpu1
    beq +
    stz.b cpu1
    lda #SFX_SELECT.b
    jsr SfxPlay
+   ; ---------- B: undo pick / CPU ----------
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    and #JOY_ST.w
    beq TTS_p2_join_done
    sep #$20
    .ACCU 8
    lda.b cpu2
    beq TTS_p2_join_done
    stz.b cpu2
    lda #SFX_SELECT.b
    jsr SfxPlay
TTS_p2_join_done:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    and #JOY_B.w
    beq TTS_move
    sep #$20
    .ACCU 8
    lda.w T_STEP
    beq +
    dec a
    sta.w T_STEP                          ; undo the last member
    bra TTS_back
+   lda.b cpu1
    bne TTS_move
    lda.w JOIN_ACTIVE
    bne TTS_back                          ; mid-fight join: P1 stays human
    lda #1
    sta.b cpu1                            ; CPU finishes the trio itself
TTS_back:
    lda #SFX_BACK.b
    jsr SfxPlay
TTS_move:
    ; ---------- CPU side auto-picks every ~48 frames ----------
    sep #$20
    .ACCU 8
    lda.b cpu1
    bne +
    jmp TTS_hmove
+   lda.w T_STEP
    cmp #3
    bcc +
    jmp TTS_done
+   lda.b framecnt
    and #$3F.b
    beq TTS_reroll
    jmp TTS_done
TTS_reroll:
    inc.b rng                           ; rerolls must differ within the
    lda.b rng                           ;   frame or an MSU/empty cell hangs
    clc
    adc.b framecnt
-   cmp #SEL_NCELLS.b                     ; random cell
    bcc +
    sec
    sbc #SEL_NCELLS.b
    bra -
+   rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    bmi TTS_reroll                        ; empty -> reroll
    sta.b scr0                            ; candidate char
    lda.b msuok
    bne +
    lda.b scr0
    jsr CharFlags
    and #$01.b
    bne TTS_reroll                        ; external chr + no MSU -> reroll
+   stx.b scr1                            ; cell -> scr1 (16b scratch)
    lda.w T_STEP                          ; stage T_STEP (cpy.w would read
    sta.b scr6                            ;   T_I1 alongside -- index-width
    stz.b scr6+1                          ;   cmp needs the staged copy)
    rep #$20
    .ACCU 16
    ldy #0
-   cpy scr6                              ; dup check inside the trio
    bcs +
    sep #$20
    .ACCU 8
    lda.w T_TEAM1,y
    cmp.b scr0
    beq TTS_reroll                        ; dup -> reroll
    rep #$20
    .ACCU 16
    iny
    bra -
+   sep #$20
    .ACCU 8
    lda.b scr1                            ; accept: cursor + pick land here
    sta.w SCUR1
    lda.b scr0
    pha
    lda.w T_STEP                        ; T_STEP is a byte: an index-width
    tay                                 ;   load would pick up T_I1's high byte
    pla
    sta.w T_TEAM1,y
    inc.w T_STEP
    lda.w T_STEP
    cmp #3
    bcs TTS_team_full
    lda #SFX_SELECT.b
    jsr SfxPlay
    jmp TTS_done
TTS_team_full:
    lda.w JOIN_ACTIVE
    bne TTS_join_finish
    lda.w YL_REPICK
    bne TTS_repick_finish
    lda.b cpu2
    beq TTS_p2_join
    jsr CampStart                         ; trio locked -> fight 1
    sep #$20
    .ACCU 8
    lda #8
    sta.w T_START
    lda.b framecnt
    sta.w T_LASTFRAME
    rts
TTS_join_finish:
    jmp JoinFinish                        ; newcomer trio done: restart
TTS_repick_finish:
    jsl YouLoseRepickDone                 ; YOU LOSE re-pick: same bout
    rts
TTS_p2_join:
    lda #1
    sta.w T_PICK_SIDE
    stz.w T_STEP
    jmp TTS_done
TTS_hmove:
    rep #$20
    .ACCU 16
    lda.w T_STEP
    and #$00FF.w
    cmp #3
    bcc +
    jmp TTS_done
+   lda FP+F_JOYPR                        ; cursor move while picking
    and #$0F00.w
    beq TTS_lock
    lda FP+F_JOYPR
    ldx #0
    jsr SelMove
TTS_lock:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR                        ; face button locks a member
    and #(JOY_A|JOY_X|JOY_Y).w
    bne TTS_lock_go
    jmp TTS_done
TTS_lock_go:
    sep #$20
    .ACCU 8
    ; candidate = char under the cursor
    lda.w SCUR1
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    bmi TTS_deny                          ; empty cell
    sta.b scr0                            ; candidate char
    ; Omega Rugal: L+R held on P1 swaps the Rugal-cell pick to the
    ; ROM-resident omega form (id 14) -- works with or without MSU
    lda.b scr0
    cmp #3.b
    bne +
    rep #$20
    .ACCU 16
    lda FP+F_JOY
    and #(JOY_L|JOY_R).w
    cmp #(JOY_L|JOY_R).w
    sep #$20
    .ACCU 8
    bne +
    lda #14.b
    sta.b scr0
+   lda.b msuok
    bne +
    lda.b scr0
    jsr CharFlags
    and #$01.b
    bne TTS_deny                          ; external chr + no MSU -> deny
+   lda.w T_STEP
    sta.b scr6                            ; stage T_STEP as a 16-bit operand
    stz.b scr6+1                          ;   (cpy is index-width: cpy.w T_STEP
    rep #$20                              ;    would read T_I1 into the cmp)
    .ACCU 16
    ldy #0                                ; dup check inside the trio
-   cpy scr6                              ; 16-bit operand: scr6 = T_STEP
    bcs +
    sep #$20
    .ACCU 8
    lda.w T_TEAM1,y
    cmp.b scr0
    beq TTS_deny
    rep #$20
    .ACCU 16
    iny
    bra -
+   sep #$20
    .ACCU 8
    lda.b scr0
    sta.w T_TEAM1,y
    inc.w T_STEP
    sep #$20
    .ACCU 8
    lda #SFX_SELECT.b
    jsr SfxPlay
    lda.w T_STEP
    cmp #3
    bcc TTS_done
    lda.w JOIN_ACTIVE
    bne TTS_hm_join
    lda.w YL_REPICK
    bne TTS_hm_repick
    jsr CampStart                         ; trio locked -> fight 1
    jsr StartFight
    rts
TTS_hm_join:
    jsr JoinFinish                        ; newcomer trio done: restart
    rts
TTS_hm_repick:
    jsl YouLoseRepickDone                 ; YOU LOSE re-pick: same bout
    rts
TTS_done:
    jsr SelFaceSync                       ; name follows the P1 cursor
    jsr SelDrawOam
    rts
TTS_deny:
    lda #SFX_BACK.b
    jsr SfxPlay
    jmp TTS_done

; Optional second human in Team Play. P1 locks first, then P2 picks the
; opposing trio; the CPU is assigned against whichever player wins.
TTS_p2_active:
    rep #$20
    .ACCU 16
    lda.w T_STEP
    and #$00FF.w
    cmp #3
    bcc TTS_p2_input
    jmp TTS_done
TTS_p2_input:
    lda FP+F_JOYPR+FP2OFS
    and #$0F00.w
    beq TTS_p2_lock
    lda FP+F_JOYPR+FP2OFS
    ldx #1
    jsr SelMove
TTS_p2_lock:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR+FP2OFS
    and #(JOY_A|JOY_X|JOY_Y).w
    bne TTS_p2_go
    jmp TTS_p2_done
TTS_p2_go:
    sep #$20
    .ACCU 8
    lda.w SCUR2
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    bpl +
    jmp TTS_p2_deny
+
    sta.b scr0
    lda.b scr0
    cmp #3.b
    bne TTS_p2_msu
    rep #$20
    .ACCU 16
    lda FP+F_JOY+FP2OFS
    and #(JOY_L|JOY_R).w
    cmp #(JOY_L|JOY_R).w
    sep #$20
    .ACCU 8
    bne TTS_p2_msu
    lda #14.b
    sta.b scr0
TTS_p2_msu:
    lda.b msuok
    bne TTS_p2_dup
    lda.b scr0
    jsr CharFlags
    and #$01.b
    bne TTS_p2_deny
TTS_p2_dup:
    lda.w T_STEP
    sta.b scr6
    stz.b scr6+1
    rep #$20
    .ACCU 16
    ldy #0
TTS_p2_dup_loop:
    cpy scr6
    bcs TTS_p2_store
    sep #$20
    .ACCU 8
    lda.w T_TEAM2,y
    cmp.b scr0
    beq TTS_p2_deny
    rep #$20
    .ACCU 16
    iny
    bra TTS_p2_dup_loop
TTS_p2_store:
    sep #$20
    .ACCU 8
    lda.b scr0
    pha
    lda.w T_STEP                        ; zero-extend T_STEP (next byte is
    tay                                 ;   T_I1/T_I2, not part of the index)
    pla
    sta.w T_TEAM2,y
    inc.w T_STEP
    lda.w T_STEP
    cmp #3
    bcc TTS_p2_sfx
    lda.w JOIN_ACTIVE
    bne TTS_p2_join_finish
    lda.w YL_REPICK
    bne TTS_p2_repick
    jsr CampStart
    lda #8
    sta.w T_START
    lda.b framecnt
    sta.w T_LASTFRAME
    rts
TTS_p2_join_finish:
    jmp JoinFinish
TTS_p2_repick:
    jsl YouLoseRepickDone                 ; YOU LOSE re-pick: same bout
    rts
TTS_p2_sfx:
    lda #SFX_SELECT.b
    jsr SfxPlay
TTS_p2_done:
    jmp TTS_done
TTS_p2_deny:
    lda #SFX_BACK.b
    jsr SfxPlay
    jmp TTS_done

.INCLUDE "engine/menucore.asm"

.ENDS

; ---------------------------------------------------------------------------
; Per-fighter OAM draw cache.  A fighter whose pose, page, position, offsets
; and palette did not change replays its previous OAM cells instead of walking
; the whole metasprite every tick.  Entries are padded to a four-cell boundary
; so each fighter owns whole OAM-high-table bytes; the high bits can then be
; snapshotted/replayed without touching a neighbour.
; ---------------------------------------------------------------------------
.IFDEF PVSNESLIB
.BASE $C0
.BANK 50 SLOT 0
; The Fight bank's low half carries CancelData ($0000-$044D) and VegaMeta
; ($1000-$7022).  This section used to sit at $7E00, but the menu tail
; ($7100+) grew past it; park it in the free CancelData window instead
; (0x0A00 leaves ~2.5 KiB for CancelData growth and stays below VegaMeta).
.ORGA $0A00
.SECTION "OamCache" FORCE
CmdSimpleNormal:
    sep #$20
    .ACCU 8
    lda ct_cancel
    bne CSN_no
    lda ct_dir
    bne CSN_no
    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_JOYPR,x
    and #(JOY_B|JOY_Y|JOY_A|JOY_X)
    beq CSN_no16
    sta scr0
    dec a
    and scr0
    bne CSN_no16
    lda FP+F_JOYPR,x
    and #(JOY_ST|JOY_SE|JOY_L|JOY_R)
    bne CSN_no16
    sep #$20
    .ACCU 8
    lda FP+F_HIST,x
    beq CSN_yes
    sta scr1
    lda #6
    sta scr2
    rep #$20
    .ACCU 16
    lda #CMDHIST_L & $FFFF.w
    clc
    adc fofs
    sta histp
    sep #$20
    .ACCU 8
    lda #$7E
    sta histp+2
    lda scr1
    dec a
    and #$0F
    sta scr3
CSN_loop:
    lda scr3
    sta scr4
    asl a
    clc
    adc scr4
    tay
    lda [histp],y
    and #$3F
    bne CSN_no
    lda scr3
    dec a
    and #$0F
    sta scr3
    dec scr2
    bne CSN_loop
CSN_yes:
    sep #$20
    .ACCU 8
    lda #1
    sta.l DBGREG_L+170
    sec
    rep #$20
    .ACCU 16
    rts
CSN_no:
    rep #$20
    .ACCU 16
CSN_no16:
    sep #$20
    .ACCU 8
    lda #2
    sta.l DBGREG_L+170
    clc
    rts

CmdScanCap:
    sep #$20
    .ACCU 8
    lda ct_win
    cmp #30                            ; long double motions (QCFx2/HCBx2)
    bcc +                              ;   use 25-30 frame windows; the old
    lda #30                            ;   18-frame cap silently rejected
+   sta ct_cut                         ;   their first half
    ldy #2
    lda [sptr],y
    and #$20
    beq +
    lda #240
    sta ct_cut
+   rts

DrawFighterCache:
    rep #$20
    .ACCU 16
    ldx fofs
    bne +
    lda #OAMC1
    bra ++
+   lda #OAMC2
++  sta lptr
    sep #$20
    .ACCU 8
    lda #$7E
    sta lptr+2

    rep #$20
    .ACCU 16
    ldx fofs
    lda FP+F_META,x
    sta OAMC_TMP
    lda FP+F_X,x
    sta OAMC_TMP+2
    lda FP+F_Y,x
    sta OAMC_TMP+4
    sep #$20
    .ACCU 8
    lda FP+F_TILEPG,x
    sta OAMC_TMP+6
    lda FP+F_XOFF,x
    sta OAMC_TMP+7
    lda FP+F_YOFF,x
    sta OAMC_TMP+8
    lda FP+F_FLAGS,x
    sta OAMC_TMP+9
    lda FP+F_PFX,x
    sta OAMC_TMP+10
    lda FP+F_CHAR,x
    sta OAMC_TMP+11

    ldy #0
-   lda OAMC_TMP,y
    cmp [lptr],y
    bne DFC_miss
    iny
    cpy #12
    bne -
    rep #$20
    .ACCU 16
    ldy #12
    lda [lptr],y
    cmp oamtop
    bne DFC_miss

    ldy #14
    lda [lptr],y
    sta scr4
DFC_hit_high:
    rep #$20
    .ACCU 16
    lda scr4
    lsr a
    lsr a
    sta scr0
    beq DFC_adv
    lda lptr
    clc
    adc #(16+256)
    tax
    lda oamtop
    lsr a
    lsr a
    lsr a
    lsr a
    clc
    adc #OAMHI.w
    tay
    lda scr0
    dec a
    mvn $7E,$7E
DFC_adv:
    rep #$20
    .ACCU 16
    lda scr4
    asl a
    asl a
    clc
    adc oamtop
    sta oamtop
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    rep #$20
    .ACCU 16
    rts

DFC_miss:
    rep #$20
    .ACCU 16
    lda lptr
    sta OAMC_PTR
    sep #$20
    .ACCU 8
    lda lptr+2
    sta OAMC_PTR+2
    rep #$20
    .ACCU 16
    lda oamtop
    sta OAMC_START
    jsr DrawFighter
    rep #$20
    .ACCU 16
DFC_pad:
    lda oamtop
    cmp #512.w
    bcs DFC_pad_done
    and #$000F.w
    beq DFC_pad_done
    ldx oamtop
    lda #$F0F0.w
    sta.w OAMBUF,x
    sta.w OAMBUF+2,x
    lda oamtop
    clc
    adc #4
    sta oamtop
    bra DFC_pad
DFC_pad_done:
    lda oamtop
    sec
    sbc OAMC_START
    lsr a
    lsr a
    sta scr4

    lda OAMC_PTR
    sta lptr
    sep #$20
    .ACCU 8
    lda OAMC_PTR+2
    sta lptr+2
    ldy #0
-   lda OAMC_TMP,y
    sta [lptr],y
    iny
    cpy #12
    bne -
    rep #$20
    .ACCU 16
    ldy #12
    lda OAMC_START
    sta [lptr],y
    ldy #14
    lda scr4
    sta [lptr],y

    lda OAMC_START
    clc
    adc #OAMBUF.w
    tax
    lda OAMC_PTR
    clc
    adc #16
    tay
    lda scr4
    asl a
    asl a
    beq DFC_store_high
    dec a
    mvn $7E,$7E
DFC_store_high:
    rep #$20
    .ACCU 16
    lda scr4
    lsr a
    lsr a
    sta scr0
    beq DFC_store_done
    lda OAMC_START
    lsr a
    lsr a
    lsr a
    lsr a
    clc
    adc #OAMHI.w
    tax
    lda OAMC_PTR
    clc
    adc #(16+256)
    tay
    lda scr0
    dec a
    mvn $7E,$7E
DFC_store_done:
    rep #$20
    .ACCU 16
    sep #$20
    .ACCU 8
    lda #ENGINE_DB.b
    pha
    plb
    rep #$20
    .ACCU 16
    rts
.ENDS
.ENDIF

.IFDEF PVSNESLIB
; Tiny near wrappers for the voice-ring reset.  They sit in the free $0C00
; gap of bank 50's low half (same $F2 CPU bank as the Fight section), keeping
; the 32 KiB Fight window below its limit.  The implementations are in the
; bank-126 voice loader.
.BANK 50 SLOT 0
.ORGA $0C00
.SECTION "VoiceResetWrappers" FORCE
VoiceQueueDrop:
    php
    jsl VoiceQueueDropFar
    plp
    rts
VoiceQueueClear:
    php
    jsl VoiceQueueClearFar
    plp
    rts
VoiceQueueReset:
    php
    jsl VoiceQueueResetFar
    plp
    rts
.ENDS
.ENDIF

; Kind-4 distance gate for TransAir (running grabs such as Takuma's Shouran
; Kyaku).  Keeping it in the same low-bank gap as the wrappers above frees
; enough room in the 32 KiB Fight window.  In: X = fofs, sptr -> TransTab row.
; Out: C=1 when the frame and distance gates both pass.
.IFDEF PVSNESLIB
.BANK 50 SLOT 0
.ELSE
.BANK 70 SLOT 0
.ENDIF
.ORGA $0D00
.SECTION "TransDistGate" FORCE
TransDistGate:
    ldy #3
    lda [sptr],y                          ; arg = (first frame << 8) | dist
    sta scr2
    xba
    and #$00FF.w
    sta scr3                              ; first animation frame
    lda FP+F_FRAME,x
    cmp scr3
    bcs +
    clc
    rts                                   ; still in the run startup
+   lda fofs                              ; |opponent.x - self.x| in px
    eor #FP2OFS.w
    tax
    lda FP+F_X,x
    ldx fofs
    sec
    sbc FP+F_X,x
    bpl +
    eor #$FFFF.w
    inc a
+   xba
    and #$00FF.w
    sta scr3
    lda scr2
    and #$00FF.w
    cmp scr3
    rts                                   ; C=1: close enough to grab
.ENDS

; TransLive: A(16) != 0 when the current state still has a live (kind 1/2)
; TransTab row -- AnimTick freezes on the last frame while such a state
; waits on its positional/input transition.  It lives in the low half of
; the Fight bank (same CPU bank) so the 32 KiB battle window keeps slack.
.IFDEF PVSNESLIB
.BANK 50 SLOT 0
.ELSE
.BANK 70 SLOT 0
.ENDIF
.ORGA $0E00
.SECTION "TransLive" FORCE
TransLive:
    ldy #CH_TRANSTAB
    ldx #sptr
    jsr CharPtr
TL_row:
    ldx fofs
    lda [sptr]
    and #$00FF.w
    cmp #$00FF.w
    beq TL_no
    cmp FP+F_STATE,x
    bne TL_next
    ldy #2
    lda [sptr],y
    and #$00FF.w
    beq TL_next                           ; kind 0 is AnimTick's business
    lda #1
    rts
TL_next:
    lda sptr
    clc
    adc #5
    sta sptr
    bra TL_row
TL_no:
    lda #0
    rts
.ENDS

; The Fight bank is full, so the projectile-clash helper lives in the free
; window between TransLive ($0E36) and VegaMeta ($1000).  It is still inside
; the same 64K ROM bank, so TickSpark can keep using a 16-bit jsr.
.BANK 50 SLOT 0
.ORGA $0F00
.SECTION "ProjClash" FORCE
; Two opposing projectiles that meet annihilate each other.  Called before
; either slot advances, so both positions belong to the same tick and the
; test is symmetric.  A clash needs two live hitbox sparks (bit7) with
; different owners (bit6); projectiles are about 48 px wide, so a 24 px
; centre distance is first contact.  Vertical reach is a little wider to
; cover torso and air shots.  Both slots are freed, with no impact spark.
ProjClash:
    rep #$20
    .ACCU 16
    lda.w SPARKS+SPK_ANIM
    beq PC_out
    lda.w SPARKS+SPK_ANIM+SPK_SIZE
    beq PC_out
    sep #$20
    .ACCU 8
    lda.w SPARKS+SPK_ATTR
    and.w SPARKS+SPK_ATTR+SPK_SIZE
    and #$80.b                          ; both are hitbox projectiles
    beq PC_out8
    lda.w SPARKS+SPK_ATTR
    eor.w SPARKS+SPK_ATTR+SPK_SIZE
    and #$40.b                          ; and belong to opposite sides
    beq PC_out8
    rep #$20
    .ACCU 16
    lda.w SPARKS                        ; |dx| between the two centres
    sec
    sbc.w SPARKS+SPK_SIZE
    bpl +
    eor #$FFFF.w
    inc a
+   cmp #24.w
    bcs PC_out
    lda.w SPARKS+2                      ; |dy|
    sec
    sbc.w SPARKS+2+SPK_SIZE
    bpl +
    eor #$FFFF.w
    inc a
+   cmp #32.w
    bcs PC_out
    stz.w SPARKS+SPK_ANIM
    stz.w SPARKS+SPK_ANIM+1
    stz.w SPARKS+SPK_ANIM+SPK_SIZE
    stz.w SPARKS+SPK_ANIM+SPK_SIZE+1
    rts
PC_out8:
    rep #$20
    .ACCU 16
PC_out:
    rts
.ENDS

; Frequently-called Fight helpers that need no code changes when relocated:
; they stay in the same CPU bank ($F2), so every `jsr`/`jmp` keeps working.
; Bank 50's low half is free from $7EA9 to $7FFF after FightMenuTail.
.IFDEF PVSNESLIB
.BANK 50 SLOT 0
.ORGA $7F00
.SECTION "FightHelperTail" FORCE
CharPtr:
    rep #$20
    .ACCU 16
    phx
    phy
    jsr DataFighterX
    lda FP+F_CHAR,x
    sta cptr
    sep #$20
    .ACCU 8
    lda tblbank
    sta cptr+2
    rep #$20
    .ACCU 16
    ply
    lda [cptr],y
    plx
    sta 0,x
    sep #$20
    .ACCU 8
    phx
    jsr DataFighterX
    sep #$20                            ; DataFighterX returns with A in 16-bit mode
    .ACCU 8
    lda FP+F_TBANK,x
    plx
    sta 2,x
    rep #$20
    .ACCU 16
    rts

; X = scr2, Y = CH_NAME.  Names live in the shared tables bank, so resolve
; the descriptor's low address then replace the bank byte returned by
; CharPtr (which assumes the character's F_TBANK).
NamePtr:
    jsr CharPtr
    sep #$20
    .ACCU 8
    lda.b #:ioriName
    sta scr2+2
    rep #$20
    .ACCU 16
    rts

; A(8) = packed EnvShake byte ((ampl<<5)|ticks).  Keeps acc8.
SetShake:
    sep #$20
    .ACCU 8
    pha
    and #$1F.b
    sta shaketmr
    pla
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    sta shakeamp
    rts
.ENDS
.ENDIF


; ---------------------------------------------------------------------------
; Select cursor movement lives outside the full Fight bank.  Without MSU the
; cursor steps over characters whose sprite CHR can only come from the .msu
; file; with MSU present all cells remain freely selectable.  SelMove in the
; Fight bank calls here with jsl and this routine returns with rtl.
; ---------------------------------------------------------------------------
.BANK 126 SLOT 0
.ORGA $CC00                            ; free tail after YouLoseCode ($CAAA);
                                        ;   FightData may grow past $C000
.SECTION "SelMoveCode" FORCE
SelMoveFar:
    ; Keep the edge bits in Y: the snesmod NMI can clear lower DP scratch.
    stx.b scr6                            ; side
    tay
    tya
    and #JOY_RT.w
    bne SMC_r
    tya
    and #JOY_LF.w
    bne SMC_l
    tya
    and #JOY_UP.w
    bne SMC_u
    tya
    and #JOY_DN.w
    bne SMC_d
    sep #$20
    .ACCU 8
    rtl
SMC_l:
    rep #$20
    .ACCU 16
    lda #0
    bra SMC_go
SMC_r:
    rep #$20
    .ACCU 16
    lda #1
    bra SMC_go
SMC_u:
    rep #$20
    .ACCU 16
    lda #2
    bra SMC_go
SMC_d:
    rep #$20
    .ACCU 16
    lda #3
SMC_go:
    sta.b scr4                            ; direction, used immediately
    sep #$20
    .ACCU 8
    ; Pack side (bits 0-1) and direction (bits 6-7) into scr6, which is
    ; outside the NMI-cleared DP range and survives the CharFlags call.
    lda.b scr6
    and #$03.b
    sta.b scr6
    lda.b scr4
    asl a
    asl a
    asl a
    asl a
    asl a
    asl a
    ora.b scr6
    sta.b scr6
    lda.b scr6
    and #$03.b
    tax
    lda.w SCUR1,x                         ; current cell
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    asl a                                 ; cell*4
    clc
    adc.b scr4                            ; + dir
    tax
    sep #$20
    .ACCU 8
    lda.l SelMoveTab,x                    ; neighbor cell (or same)
    sta.l selcand
    ; Without MSU the ROM-resident roster is sparse and the left edge of
    ; Terry's cell would dead-end.  Link it to Shingo's cell so the legal
    ; fighters stay reachable with a plain cursor walk.
    lda.b msuok
    bne SMC_cand_ready
    lda.b scr4
    bne SMC_cand_ready                    ; only LEFT (direction 0)
    lda.b scr6
    and #$03.b
    tax
    lda.w SCUR1,x
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    cmp #15.b                             ; Terry
    bne SMC_cand_ready
    lda #36.b                             ; Shingo's cell
    sta.l selcand
SMC_cand_ready:
    lda #0
    sta.l selfallback
    lda.b msuok
    bne SMC_take                           ; MSU present: free selection
SMC_val:
    lda.b scr6
    and #$03.b
    tax
    lda.l selcand
    cmp.w SCUR1,x
    beq SMC_out                            ; wrapped back to current cell
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l SelCellChr,x
    bmi SMC_next                           ; empty cell -> keep looking
    cmp #3.b
    beq SMC_take                           ; Rugal cell: hidden Omega entry
    ; RomFlags is generated from the CHR slice map: 1 = tiles linked into
    ; the ROM, 0 = streamed from kof98-snes.msu.  Using the table instead of
    ; a hardcoded id range keeps every ROM-resident fighter reachable when
    ; the .msu file is absent (e.g. Terry, id 15).
    rep #$20
    .ACCU 16
    and #$00FF.w
    tax
    sep #$20
    .ACCU 8
    lda.l RomFlags,x
    bne SMC_take                           ; CHR resident in ROM: selectable
SMC_next:
    lda.l selfallback
    bne SMC_scan
    lda.b scr6                            ; recover direction: bits 6-7
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    sta.b scr4
    lda.l selcand
    rep #$20
    .ACCU 16
    and #$00FF.w
    asl a
    asl a
    clc
    adc.b scr4
    tax
    sep #$20
    .ACCU 8
    lda.l SelMoveTab,x
    cmp.l selcand
    beq SMC_fallback                      ; edge: no legal cell this way
    sta.l selcand
    bra SMC_val
SMC_fallback:
    lda #1
    sta.l selfallback
SMC_scan:
    lda.l selcand
    inc a
    cmp #SEL_NCELLS.b
    bcc +
    lda #0
+   sta.l selcand
    bra SMC_val
SMC_take:
    lda.b scr6
    and #$03.b
    tax
    lda.l selcand
    cmp.w SCUR1,x
    beq SMC_out
    sta.w SCUR1,x
    lda #SFX_MOVE.b
    jsl SfxPlayFar
SMC_out:
    sep #$20
    .ACCU 8
    rtl

; ---------------------------------------------------------------------------
; Drain the snesmod message fifo.  The library's spcFlush does
; "jsr spcProcessMessages", but that routine ends in plb/plp/rtl (it is
; the tail of spcProcess), so with a non-empty fifo it unwinds the wrong
; stack frame and returns into garbage.  Loop on spcProcess instead,
; which has a matching prologue.  D must be 0 (snesmod zeropage).
; All callers go far (jsl), so it lives in this bank's free tail.
SpcFlushSafe:
    php
    sep #$20
-   lda.l spc_fread
    cmp.l spc_fwrite
    beq +
    jsl spcProcess
    bra -
+   ; A module/effect load rewrites SPC RAM.  If a character voice is still
+   ; streaming, spcLoad/spcLoadEffect would race the stream and leave the
+   ; SPC (and the port handshake) in a corrupt state.  Pump spcProcess until
+   ; the stream finishes; 4.6 also aborts a stuck stream here.
    rep #$20
    .ACCU 16
    ldx #$0100.w
-   lda.l $00015A                       ; digi_active
    and #$00FF.w
    beq +
    phx
    jsl spcProcess
    plx
    dex
    bne -
+   plp
    rtl

; ---------------------------------------------------------------------------
; Per-frame SPC effect reload, pulled out of the full Fight bank.  Called
; from MainLoop with D=0 (snesmod zeropage): exactly one pending load drains
; per frame, right after spcProcess.  The slot returned by spcLoadEffect is
; authoritative -- the four UI effects do NOT always land in slots 0..3,
; so UI_SLOT_SEL/MOVE/BACK/WIN record the real allocation.
; ---------------------------------------------------------------------------
FxDrainFar:
    rep #$20
    .ACCU 16
    lda.l $7E46F8                       ; pending SPC effect reloads?
    bne +
    rtl
+   sep #$20
    .ACCU 8
    lda.b spc_v                         ; do not consume a pending entry until
    cmp.l $2141                         ; the SPC can accept its blocking load
    beq FD_ready
    rep #$20
    .ACCU 16
    rtl
FD_ready:
    ; A character voice can still be streaming even when spc_v matches the
    ; APU port.  spcLoadEffect's message handshake has no timeout, so loading
    ; an effect now can leave the CPU waiting forever (music keeps playing,
    ; fighters and the round clock stop).  Keep the pending reload for the
    ; next frame and only start it once the streamer is idle.
    lda.l $00015A
    and #$00FF.b
    beq +
    rtl
+   rep #$20
    .ACCU 16
    lda.l $7E46F8
    dec a                               ;   the fifo drains between syncs
    sta.l $7E46F8
    lda.l $7E0000+UI_SFXLOAD
    and #$00FF.w
    beq FD_base
    lda #3.w                            ; pending was decremented above:
                                        ; 3,2,1,0 -> UiSrc indices 0..3
    sec
    sbc.l $7E46F8
    sta.l UI_SLOT_ROW                   ; which UI slot row is loading now
    tax
    lda.l UiSrc,x
    and #$00FF.w
    tax
    bra FD_load
FD_base:
    lda #7.w                            ; fight modules load eight sources:
    sec                                 ;   0,1,2 (combat) + 5 (FIGHT!) and
    sbc.l $7E46F8                       ;   6 (K.O.) into slots 0..4, then
    sta.l UI_SLOT_ROW                   ;   4/13/12 (pause select/move/back)
    tax                                 ;   into slots 5..7.
    lda.l FightFxSrc,x
    and #$00FF.w
    tax
FD_load:
    sep #$20
    .ACCU 8
    lda #0                              ; spcLoadEffect uses the same APU
    sta.l NMITIMEN                      ; ports as spcProcess; don't let an
    lda.l $4210                         ; NMI interrupt its transfer handshake
    rep #$30
    .ACCU 16
    .INDEX 16
    phx
    phx
    jsl spcLoadEffect                   ; A = newly allocated effect slot
    rep #$30
    .ACCU 16
    .INDEX 16
    sta.l UI_SLOT_NEW
    pla
    plx
    lda.l $7E0000+UI_SFXLOAD            ; byte var: mask the high byte
    and #$00FF.w
    beq FD_rec_fight
    lda.l UI_SLOT_NEW
    pha
    lda.l UI_SLOT_ROW                   ; 0,1,2 -> UI_SLOT_SEL/MOVE/BACK
    tax
    pla
    sep #$20
    .ACCU 8
    sta.l $7E0000+UI_SLOT_SEL,x
    rep #$20
    .ACCU 16
    bra FD_nmi
FD_rec_fight:
    lda.l UI_SLOT_ROW                   ; fight rows 5,6,7 -> SEL,MOVE,BACK
    cmp #5
    bcc FD_nmi
    sec
    sbc #5
    tax
    lda.l UI_SLOT_NEW
    sep #$20
    .ACCU 8
    sta.l $7E0000+UI_SLOT_SEL,x
    rep #$20
    .ACCU 16
FD_nmi:
    sep #$20
    .ACCU 8
    lda #$81.b
    sta.l NMITIMEN
    rep #$20
    .ACCU 16
    rtl
.ENDS

; ---------------------------------------------------------------------------
; YOU LOSE screen (campaign defeat).  Lives in bank 126's free tail: the
; Fight section above is 32 KiB and already full.  Called with JSL; the
; wrappers in the Fight bank bridge StartFight/ShowSelect/CampReset/TitleEnter
; and PauseText, while SfxPlay/MusPlaySong/ConsumePadEdges use the existing
; OptCall trampolines.
; ---------------------------------------------------------------------------
.BANK 126 SLOT 0
.ORGA $C700
.SECTION "YouLoseCode" FORCE

; Pause menu text/panel helpers moved here with the YOU LOSE screen: they are
; shared by both menus and the Fight bank has no room left.
; A = string, X = top row, Y = style (0 selected, 1 unselected, 2 banner).
PauseText:
    sta scr2
    stx scr4                            ; row (reused as scratch)
    sty scr5                            ; style
    sep #$20
    .ACCU 8
    lda tblbank
    sta scr2+2
    ldy #0
    lda [scr2],y                        ; glyph count
    sta scr6
    stz scr6+1
    rep #$20
    .ACCU 16
    lda scr4
    asl a
    asl a
    asl a
    asl a
    asl a                               ; row*32
    sta scr1
    lda #32.w
    sec
    sbc scr6
    lsr a                               ; centred column
    sta scr3
    clc
    adc scr1
    asl a                               ; -> HUDMAP byte offset
    sta scr0
    jsl YLFar_WriteStrBig
    sep #$20
    .ACCU 8
    lda scr5
    cmp #1
    beq PT_dim
    cmp #0
    bne PT_done
    rep #$20                            ; selected: ">" cursor two cells left
    .ACCU 16
    lda scr0
    sec
    sbc #4
    tax
    sep #$20
    .ACCU 8
    lda #CMD_CUR_TILE.b
    sta HUDMAP,x
    lda #ATT_YEL.b
    sta HUDMAP+1,x
    bra PT_done
PT_dim:
    rep #$20
    .ACCU 16
    lda scr0
    tax
    sep #$20
    .ACCU 8
    lda scr6
    sta scr4
-   lda #ATT_TXT.b
    sta HUDMAP+1,x
    sta HUDMAP+65,x
    inx
    inx
    dec scr4
    bne -
PT_done:
    rep #$20
    .ACCU 16
    rts

PauseDraw:
    jsl YLFar_CmdClear
    rep #$20
    .ACCU 16
    ldx #7
    ldy #2
    lda #BStrPause.w
    jsr PauseText
    rep #$20
    .ACCU 16
    ldx #10
    ldy #1
    lda.w PZ_SEL
    and #$00FF.w
    bne +
    ldy #0
+   lda #BStrContinue.w
    jsr PauseText
    rep #$20
    .ACCU 16
    ldx #12
    ldy #1
    lda.w PZ_SEL
    and #$00FF.w
    cmp #1.w
    bne +
    ldy #0
+   lda #BStrCommand.w
    jsr PauseText
    rep #$20
    .ACCU 16
    ldx #14
    ldy #1
    lda.w PZ_SEL
    and #$00FF.w
    cmp #2.w
    bne +
    ldy #0
+   lda #BStrExit.w
    jsr PauseText
    sep #$20
    .ACCU 8
    lda huddirty
    ora #HUD_FULL
    sta huddirty
    rtl

YouLoseEnter:
    jsl VoiceQueueResetFar              ; this routine lives in bank 126, not
    sep #$20                            ;   the Fight bank: call it far
    .ACCU 8
    stz.b winvoice
    stz.w PZ_ON
    stz.w CL_OPEN
    stz.w CL_FROM_PAUSE
    stz.w JOIN_ACTIVE
    stz.w JOIN_SIDE
    stz.b nextflag
    stz.b pausecnt
    stz.b shaketmr
    stz.w YL_SEL
    stz.w YL_REPICK
    lda.l $7E46F8                       ; menu clips already resident with the
    bne +                               ;   stage module? (never switch sets
    lda #1                              ;   mid-drain: FxDrainFar reads this)
    sta.w UI_SFXLOAD
+   lda #$04.b                          ; only BG3 remains: clean black panel
    sta.l TM
    jsr YouLoseClearMap
    jsr YouLoseDraw
    lda #GS_YOULOSE
    sta.b gamestate
    jsl OptCall_ConsumePadEdges         ; ignore the button that ended the bout
    rtl

; Erase the full BG3 map (the fight HUD occupies rows outside the pause
; overlay's 7-21 window too).
YouLoseClearMap:
    rep #$30
    .ACCU 16
    .INDEX 16
    lda #0
    ldx #0
-   sta.w HUDMAP,x
    inx
    inx
    cpx #2048.w
    bne -
    sep #$20
    .ACCU 8
    rts

YouLoseDraw:
    jsr YouLoseClearMap
    rep #$20
    .ACCU 16
    lda #BStrYouLose.w
    ldx #8
    ldy #2
    jsr PauseText
    rep #$20
    .ACCU 16
    ldx #12
    ldy #1
    lda.w YL_SEL
    and #$00FF.w
    bne +
    ldy #0
+   lda #BStrContinue.w
    jsr PauseText
    rep #$20
    .ACCU 16
    ldx #14
    ldy #1
    lda.w YL_SEL
    and #$00FF.w
    cmp #1.w
    bne +
    ldy #0
+   lda #BStrSelectFighter.w
    jsr PauseText
    rep #$20
    .ACCU 16
    ldx #16
    ldy #1
    lda.w YL_SEL
    and #$00FF.w
    cmp #2.w
    bne +
    ldy #0
+   lda #BStrExit.w
    jsr PauseText
    sep #$20
    .ACCU 8
    lda huddirty
    ora #HUD_FULL
    sta huddirty
    rts

YouLoseTick:
    rep #$20
    .ACCU 16
    lda FP+F_JOYPR
    ora FP+F_JOYPR+FP2OFS
    sta scr0
    and #JOY_UP.w
    beq YLT_down
    sep #$20
    .ACCU 8
    lda.w YL_SEL
    beq YLT_out
    dec a
    sta.w YL_SEL
    jsr YouLoseDraw
    lda #SFX_MOVE.b
    jsl SfxPlayFar
YLT_out:
    sep #$20
    .ACCU 8
    rtl
YLT_down:
    rep #$20
    .ACCU 16
    lda scr0
    and #JOY_DN.w
    beq YLT_confirm
    sep #$20
    .ACCU 8
    lda.w YL_SEL
    cmp #2.b
    bcs YLT_out
    inc a
    sta.w YL_SEL
    jsr YouLoseDraw
    lda #SFX_MOVE.b
    jsl SfxPlayFar
    rtl
YLT_confirm:
    rep #$20
    .ACCU 16
    lda scr0
    and #(JOY_A|JOY_X|JOY_Y|JOY_ST).w
    bne YLT_confirm_go
    lda scr0                            ; B = back to the current fight, the
    and #JOY_B.w                        ;   same back action as the pause menu
    beq YLT_out
    sep #$20
    .ACCU 8
    lda #SFX_BACK.b
    jsl SfxPlayFar
    jmp YouLoseContinue
YLT_confirm_go:
    sep #$20
    .ACCU 8
    lda.w YL_SEL
    beq YLT_continue
    cmp #1.b
    beq YLT_select
    bra YLT_exit
YLT_continue:
    lda #SFX_SELECT.b
    jsl SfxPlayFar
    jmp YouLoseContinue
YLT_select:
    lda #SFX_SELECT.b
    jsl SfxPlayFar
    jmp YouLoseSelect
YLT_exit:
    lda #SFX_BACK.b
    jsl SfxPlayFar
    jmp YouLoseExit

; CONTINUE: replay the confrontation that was just lost.  Single play keeps
; the same opponent pick; team play retries with the last member that fell
; against the CPU member that eliminated it.
YouLoseContinue:
    sep #$20
    .ACCU 8
    stz.w YL_REPICK
    lda #0
    sta.w UI_SFXLOAD                    ; back to the stage effect slots
    stz.b nextflag
    stz.b pausecnt
    stz.b shaketmr
    stz.b wins1
    stz.b wins2
    stz.w MATWON
    stz.w T_SWAP
    stz.w C_PVP
    lda #1
    sta.b roundno
    lda.w G_MODE
    cmp #2
    bne YLC_start
    ; Full rematch: both trios restart from their first member, so the
    ; player faces the CPU team from the first to the last again.
    lda #0
    sta.w T_I1
    sta.w T_I2
YLC_start:
    jsl YLFar_StartFight
    rtl

; SELECT FIGHTER: open the normal character select for the human side only;
; the CPU side keeps its current pick.  The flag makes the select's final
; lock land in YouLoseRepickDone instead of CampStart.
YouLoseSelect:
    sep #$20
    .ACCU 8
    lda #1
    sta.w YL_REPICK
    stz.b nextflag
    stz.b pausecnt
    stz.b shaketmr
    stz.b wins1
    stz.b wins2
    stz.w MATWON
    stz.w T_SWAP
    stz.w T_STEP
    stz.w T_START
    stz.w T_LASTFRAME
    lda.w C_HUMAN_SIDE
    bne YLS_p2
    stz.b cpu1                          ; P1 picks; P2 is the CPU
    lda #1
    sta.b cpu2
    stz.w T_PICK_SIDE
    bra YLS_seed
YLS_p2:
    lda #1
    sta.b cpu1
    stz.b cpu2
    lda #1
    sta.w T_PICK_SIDE
YLS_seed:
    rep #$10
    .INDEX 16
    lda.w G_MODE
    cmp #2.b
    bne YLS_open                         ; single: sels already point at the pair
    lda.w C_HUMAN_SIDE
    bne YLS_team_p2
    lda.w T_TEAM1                        ; new P1 trio starts at member 1
    sta.b sel1
    lda.w T_TEAM2                        ; rematch: CPU starts at member 1
    sta.b sel2
    bra YLS_open
YLS_team_p2:
    lda.w T_TEAM2                        ; new P2 trio starts at member 1
    sta.b sel2
    lda.w T_TEAM1                        ; rematch: CPU starts at member 1
    sta.b sel1
YLS_open:
    lda #SONG_KOF.b
    jsl OptCall_MusPlaySong
    stz.w MUSIC_VALID
    jsl YLFar_ShowSelect
    ; ShowSelect clears both lock latches; keep the CPU side locked so its
    ; pick cannot be disturbed while the human chooses.
    sep #$20
    .ACCU 8
    lda.w C_HUMAN_SIDE
    bne YLS_lock_p1
    lda #1
    sta.b lock2
    stz.b lock1
    bra YLS_go
YLS_lock_p1:
    lda #1
    sta.b lock1
    stz.b lock2
YLS_go:
    rep #$20
    .ACCU 16
    lda #5
    sta.b gamestate
    rtl

; Select finished while YL_REPICK is set: keep the campaign route and start
; the current bout with the new pick.
YouLoseRepickDone:
    sep #$20
    .ACCU 8
    stz.w YL_REPICK
    ; Keep the cpu1/cpu2 split chosen by YouLoseSelect: the campaign side is
    ; human and the other side must stay under AI control (unlike JoinFinish,
    ; where both pads are human).
    stz.b lock1
    stz.b lock2
    stz.b nextflag
    stz.b pausecnt
    stz.b shaketmr
    stz.b wins1
    stz.b wins2
    stz.w MATWON
    stz.w T_SWAP
    stz.w T_STEP
    lda #1
    sta.b roundno
    lda.w G_MODE
    cmp #2
    bne YLR_start
    ; Full rematch: re-picking the human trio also restarts the CPU trio.
    lda #0
    sta.w T_I1
    sta.w T_I2
YLR_start:
    jsl YLFar_StartFight
    rtl

; EXIT: drop the campaign and go back to the title/PRESS START screen.
YouLoseExit:
    sep #$20
    .ACCU 8
    stz.w YL_REPICK
    lda #0                              ; STA (8-bit): STZ always writes a
    sta.w UI_SFXLOAD                    ;   word, clobbering the next byte
    jsl YLFar_CampReset
    stz.b wins1
    stz.b wins2
    lda #1
    sta.b roundno
    stz.b nextflag
    jsl YLFar_TitleEnter
    rtl

; ---------------------------------------------------------------------------
; Final-boss hand-off.  Kept here because the Fight bank is full; the Fight
; bank calls these with JSL.  BossFadeTickFar ends with JML so EndEnter does
; not return into the abandoned JSL frame.
; ---------------------------------------------------------------------------
; Omega Rugal defeated: skip the winner banner, fade the KO screen to black
; and let EndEnter fade ending1 in from black.
BossEndingFar:
    sep #$20
    .ACCU 8
    lda #1
    sta.w E_BLACKIN
    stz.b nextflag
    lda #15
    sta.b fadelevel
    lda #GS_BOSS_FADE.b
    sta.b gamestate
    rtl

; Gamestate 13: hold the KO screen while the display brightness walks to
; black, then hand off to ending1.  FightPresent/FightVblank re-write $0F
; earlier in the frame; this runs after them so the fade value wins.
BossFadeTickFar:
    sep #$20
    .ACCU 8
    lda.b framecnt
    and #$01.b
    bne BF_apply
    lda.b fadelevel
    beq BF_done
    dec a
    sta.b fadelevel
BF_apply:
    lda.b fadelevel
    sta.l INIDISP
    rep #$20
    .ACCU 16
    rtl
BF_done:
    lda #$80.b
    sta.l INIDISP
    jml EndEnter

.ENDS

; gen_fight/iori_chr.inc (sprite tile fetch assumes a contiguous bank run:
; CH_CHRBANK + tilebase>>10).  PVSnesLib banks 2+; ExHiROM uses 71+.
.INCLUDE "gen_fight/iori_chr.inc"


.IFDEF PVSNESLIB
.BANK 126 SLOT 0
.ELSE
.BANK 122 SLOT 0
.ENDIF
.ORGA $8000
.SECTION "FightData" FORCE
CharIori:
    .dw ioriSprOfs, ioriBoxTab, ioriAnimTab
    .dw ioriActiveTab, ioriDamageTab, ioriHitTimeTab
    .dw ioriSlideTab, ioriHitVelTab, ioriButtonTab
    .db $30, 0                            ; OBJ priority 3, palette 0
    .dw IoriChr
    .db :IoriChr, 0
    .dw IoriPal
    .db :IoriPal, 0
    .dw ioriName
    .dw ioriCButtonTab, ioriAButtonTab, ioriFlagsTab
    .dw ioriGVelTab, ioriGDmgTab
    .dw ioriCmdTab, ioriMotTab, ioriPosTab
    .dw ioriChainTab
    .dw ioriPowTab
    .dw ioriTransTab, ioriEVelTab
    .dw ioriTargetTab
    .dw ioriBindTab, ioriActTab, ioriRevTab
    .dw ioriHitSndTab
    .dw ioriShakeTab
    .dw ioriQuoteTab
    .dw ioriExpTab
    .dw ioriPauseTab
    .dw IoriPalDim                      ; +72 per-side palette uploads
    .db :IoriPalDim, 0                  ;   (pal+3 dim ghost, pal+5 flash)
    .dw IoriPalHi
    .db :IoriPalHi, 0
    .dw ioriProjTab
    .db :ioriSprData, 0                    ; CH_MBANK
    .dw ioriProjFxTab, ioriProjFxChr
    .dw ioriCmdList
    .db 0, ioriMaxMask
    .dw ioriCancelRow
CharKyo:
    .dw kyoSprOfs, kyoBoxTab, kyoAnimTab
    .dw kyoActiveTab, kyoDamageTab, kyoHitTimeTab
    .dw kyoSlideTab, kyoHitVelTab, kyoButtonTab
    .db $32, 0                            ; OBJ priority 3, palette 1
    .dw KyoChr
    .db :KyoChr, 0
    .dw KyoPal
    .db :KyoPal, 0
    .dw kyoName
    .dw kyoCButtonTab, kyoAButtonTab, kyoFlagsTab
    .dw kyoGVelTab, kyoGDmgTab
    .dw kyoCmdTab, kyoMotTab, kyoPosTab
    .dw kyoChainTab
    .dw kyoPowTab
    .dw kyoTransTab, kyoEVelTab
    .dw kyoTargetTab
    .dw kyoBindTab, kyoActTab, kyoRevTab
    .dw kyoHitSndTab
    .dw kyoShakeTab
    .dw kyoQuoteTab
    .dw kyoExpTab
    .dw kyoPauseTab
    .dw KyoPalDim
    .db :KyoPalDim, 0
    .dw KyoPalHi
    .db :KyoPalHi, 0
    .dw kyoProjTab
    .db :kyoSprData, 0                    ; CH_MBANK
    .dw kyoProjFxTab, kyoProjFxChr
    .dw kyoCmdList
    .db 0, kyoMaxMask
    .dw kyoCancelRow
CharShingo:
    .dw shingoSprOfs, shingoBoxTab, shingoAnimTab
    .dw shingoActiveTab, shingoDamageTab, shingoHitTimeTab
    .dw shingoSlideTab, shingoHitVelTab, shingoButtonTab
    .db $30, 0                            ; attr set per side at pick time
    .dw ShingoChr
    .db :ShingoChr, 0
    .dw ShingoPal
    .db :ShingoPal, 0
    .dw shingoName
    .dw shingoCButtonTab, shingoAButtonTab, shingoFlagsTab
    .dw shingoGVelTab, shingoGDmgTab
    .dw shingoCmdTab, shingoMotTab, shingoPosTab
    .dw shingoChainTab
    .dw shingoPowTab
    .dw shingoTransTab, shingoEVelTab
    .dw shingoTargetTab
    .dw shingoBindTab, shingoActTab, shingoRevTab
    .dw shingoHitSndTab
    .dw shingoShakeTab
    .dw shingoQuoteTab
    .dw shingoExpTab
    .dw shingoPauseTab
    .dw ShingoPalDim
    .db :ShingoPalDim, 0
    .dw ShingoPalHi
    .db :ShingoPalHi, 0
    .dw shingoProjTab
    .db :shingoSprData, 0                    ; CH_MBANK
    .dw kyoProjFxTab, kyoProjFxChr            ; shared Orochinagi flame
    .dw shingoCmdList
    .db :shingoCmdList, shingoMaxMask
    .dw shingoCancelRow
CharRugal:
    .dw rugalSprOfs, rugalBoxTab, rugalAnimTab
    .dw rugalActiveTab, rugalDamageTab, rugalHitTimeTab
    .dw rugalSlideTab, rugalHitVelTab, rugalButtonTab
    .db $30, 0
    .dw 0
    .db MSU_RUGAL_SLICE, 1
    .dw RugalPal
    .db :RugalPal, 0
    .dw rugalName
    .dw rugalCButtonTab, rugalAButtonTab, rugalFlagsTab
    .dw rugalGVelTab, rugalGDmgTab
    .dw rugalCmdTab, rugalMotTab, rugalPosTab
    .dw rugalChainTab
    .dw rugalPowTab
    .dw rugalTransTab, rugalEVelTab
    .dw rugalTargetTab
    .dw rugalBindTab, rugalActTab, rugalRevTab
    .dw rugalHitSndTab
    .dw rugalShakeTab
    .dw rugalQuoteTab
    .dw rugalExpTab
    .dw rugalPauseTab
    .dw RugalPalDim
    .db :RugalPalDim, 0
    .dw RugalPalHi
    .db :RugalPalHi, 0
    .dw rugalProjTab
    .db :rugalSprData, 0                    ; CH_MBANK
    .dw rugalProjFxTab, rugalProjFxChr
    .dw rugalCmdList
    .db 0, rugalMaxMask
    .dw rugalCancelRow
CharOmegaRugal:
    .dw omegarugalSprOfs, omegarugalBoxTab, omegarugalAnimTab
    .dw omegarugalActiveTab, omegarugalDamageTab, omegarugalHitTimeTab
    .dw omegarugalSlideTab, omegarugalHitVelTab, omegarugalButtonTab
    .db $30, 0
    .dw ORugalChr
    .db :ORugalChr, 0
    .dw OmegaRugalPal
    .db :OmegaRugalPal, 0
    .dw omegarugalName
    .dw omegarugalCButtonTab, omegarugalAButtonTab, omegarugalFlagsTab
    .dw omegarugalGVelTab, omegarugalGDmgTab
    .dw omegarugalCmdTab, omegarugalMotTab, omegarugalPosTab
    .dw omegarugalChainTab
    .dw omegarugalPowTab
    .dw omegarugalTransTab, omegarugalEVelTab
    .dw omegarugalTargetTab
    .dw omegarugalBindTab, omegarugalActTab, omegarugalRevTab
    .dw omegarugalHitSndTab
    .dw omegarugalShakeTab
    .dw omegarugalQuoteTab
    .dw omegarugalExpTab
    .dw omegarugalPauseTab
    .dw OmegaRugalPalDim
    .db :OmegaRugalPalDim, 0
    .dw OmegaRugalPalHi
    .db :OmegaRugalPalHi, 0
    .dw omegarugalProjTab
    .db :omegarugalSprData, 0                    ; CH_MBANK
    .dw omegarugalProjFxTab, omegarugalProjFxChr
    .dw omegarugalCmdList
    .db 0, omegarugalMaxMask
    .dw omegarugalCancelRow

.IFNDEF BASE4
CharSaisyu:
    .dw saisyuSprOfs, saisyuBoxTab, saisyuAnimTab
    .dw saisyuActiveTab, saisyuDamageTab, saisyuHitTimeTab
    .dw saisyuSlideTab, saisyuHitVelTab, saisyuButtonTab
    .db $30, 0
    .dw 0
    .db MSU_SAISYU_SLICE, 1
    .dw SaisyuPal
    .db :SaisyuPal, 0
    .dw saisyuName
    .dw saisyuCButtonTab, saisyuAButtonTab, saisyuFlagsTab
    .dw saisyuGVelTab, saisyuGDmgTab
    .dw saisyuCmdTab, saisyuMotTab, saisyuPosTab
    .dw saisyuChainTab
    .dw saisyuPowTab
    .dw saisyuTransTab, saisyuEVelTab
    .dw saisyuTargetTab
    .dw saisyuBindTab, saisyuActTab, saisyuRevTab
    .dw saisyuHitSndTab
    .dw saisyuShakeTab
    .dw saisyuQuoteTab
    .dw saisyuExpTab
    .dw saisyuPauseTab
    .dw SaisyuPalDim
    .db :SaisyuPalDim, 0
    .dw SaisyuPalHi
    .db :SaisyuPalHi, 0
    .dw saisyuProjTab
    .db :saisyuSprData, 0                    ; CH_MBANK
    .dw kyoProjFxTab, kyoProjFxChr            ; shared Yami Barai flame
    .dw saisyuCmdList
    .db 0, saisyuMaxMask
    .dw saisyuCancelRow
CharHeidern:
    .dw heidernSprOfs, heidernBoxTab, heidernAnimTab
    .dw heidernActiveTab, heidernDamageTab, heidernHitTimeTab
    .dw heidernSlideTab, heidernHitVelTab, heidernButtonTab
    .db $30, 0
    .dw 0
    .db MSU_HEIDERN_SLICE, 1
    .dw HeidernPal
    .db :HeidernPal, 0
    .dw heidernName
    .dw heidernCButtonTab, heidernAButtonTab, heidernFlagsTab
    .dw heidernGVelTab, heidernGDmgTab
    .dw heidernCmdTab, heidernMotTab, heidernPosTab
    .dw heidernChainTab
    .dw heidernPowTab
    .dw heidernTransTab, heidernEVelTab
    .dw heidernTargetTab
    .dw heidernBindTab, heidernActTab, heidernRevTab
    .dw heidernHitSndTab
    .dw heidernShakeTab
    .dw heidernQuoteTab
    .dw heidernExpTab
    .dw heidernPauseTab
    .dw HeidernPalDim
    .db :HeidernPalDim, 0
    .dw HeidernPalHi
    .db :HeidernPalHi, 0
    .dw heidernProjTab
    .db :heidernSprData, 0                    ; CH_MBANK
    .dw heidernProjFxTab, heidernProjFxChr
    .dw heidernCmdList
    .db 0, heidernMaxMask
    .dw heidernCancelRow
CharTakuma:
    .dw takumaSprOfs, takumaBoxTab, takumaAnimTab
    .dw takumaActiveTab, takumaDamageTab, takumaHitTimeTab
    .dw takumaSlideTab, takumaHitVelTab, takumaButtonTab
    .db $30, 0
    .dw 0
    .db MSU_TAKUMA_SLICE, 1
    .dw TakumaPal
    .db :TakumaPal, 0
    .dw takumaName
    .dw takumaCButtonTab, takumaAButtonTab, takumaFlagsTab
    .dw takumaGVelTab, takumaGDmgTab
    .dw takumaCmdTab, takumaMotTab, takumaPosTab
    .dw takumaChainTab
    .dw takumaPowTab
    .dw takumaTransTab, takumaEVelTab
    .dw takumaTargetTab
    .dw takumaBindTab, takumaActTab, takumaRevTab
    .dw takumaHitSndTab
    .dw takumaShakeTab
    .dw takumaQuoteTab
    .dw takumaExpTab
    .dw takumaPauseTab
    .dw TakumaPalDim
    .db :TakumaPalDim, 0
    .dw TakumaPalHi
    .db :TakumaPalHi, 0
    .dw takumaProjTab
    .db :takumaSprData, 0                    ; CH_MBANK
    .dw yuriProjFxTab, yuriProjFxChr         ; shared six-cel Ko'ou Ken
    .dw takumaCmdList
    .db 0, takumaMaxMask
    .dw takumaCancelRow
CharClark:
    .dw clarkSprOfs, clarkBoxTab, clarkAnimTab
    .dw clarkActiveTab, clarkDamageTab, clarkHitTimeTab
    .dw clarkSlideTab, clarkHitVelTab, clarkButtonTab
    .db $30, 0
    .dw 0
    .db MSU_CLARK_SLICE, 1
    .dw ClarkPal
    .db :ClarkPal, 0
    .dw clarkName
    .dw clarkCButtonTab, clarkAButtonTab, clarkFlagsTab
    .dw clarkGVelTab, clarkGDmgTab
    .dw clarkCmdTab, clarkMotTab, clarkPosTab
    .dw clarkChainTab
    .dw clarkPowTab
    .dw clarkTransTab, clarkEVelTab
    .dw clarkTargetTab
    .dw clarkBindTab, clarkActTab, clarkRevTab
    .dw clarkHitSndTab
    .dw clarkShakeTab
    .dw clarkQuoteTab
    .dw clarkExpTab
    .dw clarkPauseTab
    .dw ClarkPalDim
    .db :ClarkPalDim, 0
    .dw ClarkPalHi
    .db :ClarkPalHi, 0
    .dw clarkProjTab
    .db :clarkSprData, 0                    ; CH_MBANK
    .dw clarkProjFxTab, clarkProjFxChr
    .dw clarkCmdList
    .db 0, clarkMaxMask
    .dw clarkCancelRow
CharRalf:
    .dw ralfSprOfs, ralfBoxTab, ralfAnimTab
    .dw ralfActiveTab, ralfDamageTab, ralfHitTimeTab
    .dw ralfSlideTab, ralfHitVelTab, ralfButtonTab
    .db $30, 0
    .dw 0
    .db MSU_RALF_SLICE, 1
    .dw RalfPal
    .db :RalfPal, 0
    .dw ralfName
    .dw ralfCButtonTab, ralfAButtonTab, ralfFlagsTab
    .dw ralfGVelTab, ralfGDmgTab
    .dw ralfCmdTab, ralfMotTab, ralfPosTab
    .dw ralfChainTab
    .dw ralfPowTab
    .dw ralfTransTab, ralfEVelTab
    .dw ralfTargetTab
    .dw ralfBindTab, ralfActTab, ralfRevTab
    .dw ralfHitSndTab
    .dw ralfShakeTab
    .dw ralfQuoteTab
    .dw ralfExpTab
    .dw ralfPauseTab
    .dw RalfPalDim
    .db :RalfPalDim, 0
    .dw RalfPalHi
    .db :RalfPalHi, 0
    .dw ralfProjTab
    .db :ralfSprData, 0                    ; CH_MBANK
    .dw terryProjFxTab, terryProjFxChr        ; shared shockwave atlas
    .dw ralfCmdList
    .db 0, ralfMaxMask
    .dw ralfCancelRow
CharLeona:
    .dw leonaSprOfs, leonaBoxTab, leonaAnimTab
    .dw leonaActiveTab, leonaDamageTab, leonaHitTimeTab
    .dw leonaSlideTab, leonaHitVelTab, leonaButtonTab
    .db $30, 0
    .dw 0
    .db MSU_LEONA_SLICE, 1
    .dw LeonaPal
    .db :LeonaPal, 0
    .dw leonaName
    .dw leonaCButtonTab, leonaAButtonTab, leonaFlagsTab
    .dw leonaGVelTab, leonaGDmgTab
    .dw leonaCmdTab, leonaMotTab, leonaPosTab
    .dw leonaChainTab
    .dw leonaPowTab
    .dw leonaTransTab, leonaEVelTab
    .dw leonaTargetTab
    .dw leonaBindTab, leonaActTab, leonaRevTab
    .dw leonaHitSndTab
    .dw leonaShakeTab
    .dw leonaQuoteTab
    .dw leonaExpTab
    .dw leonaPauseTab
    .dw LeonaPalDim
    .db :LeonaPalDim, 0
    .dw LeonaPalHi
    .db :LeonaPalHi, 0
    .dw leonaProjTab
    .db :leonaSprData, 0                    ; CH_MBANK
    .dw terryProjFxTab, terryProjFxChr        ; shared ground-wave atlas
    .dw leonaCmdList
    .db 0, leonaMaxMask
    .dw leonaCancelRow
CharMature:
    .dw matureSprOfs, matureBoxTab, matureAnimTab
    .dw matureActiveTab, matureDamageTab, matureHitTimeTab
    .dw matureSlideTab, matureHitVelTab, matureButtonTab
    .db $30, 0
    .dw (MSU_MATURE_SLICE >> 8)
    .db (MSU_MATURE_SLICE & $FF), 1
    .dw MaturePal
    .db :MaturePal, 0
    .dw matureName
    .dw matureCButtonTab, matureAButtonTab, matureFlagsTab
    .dw matureGVelTab, matureGDmgTab
    .dw matureCmdTab, matureMotTab, maturePosTab
    .dw matureChainTab
    .dw maturePowTab
    .dw matureTransTab, matureEVelTab
    .dw matureTargetTab
    .dw matureBindTab, matureActTab, matureRevTab
    .dw matureHitSndTab
    .dw matureShakeTab
    .dw matureQuoteTab
    .dw matureExpTab
    .dw maturePauseTab
    .dw MaturePalDim
    .db :MaturePalDim, 0
    .dw MaturePalHi
    .db :MaturePalHi, 0
    .dw matureProjTab
    .db :matureSprData, 0                    ; CH_MBANK
    .dw matureProjFxTab, matureProjFxChr
    .dw matureCmdList
    .db 0, matureMaxMask
    .dw matureCancelRow
CharVice:
    .dw viceSprOfs, viceBoxTab, viceAnimTab
    .dw viceActiveTab, viceDamageTab, viceHitTimeTab
    .dw viceSlideTab, viceHitVelTab, viceButtonTab
    .db $30, 0
    .dw (MSU_VICE_SLICE >> 8)
    .db (MSU_VICE_SLICE & $FF), 1
    .dw VicePal
    .db :VicePal, 0
    .dw viceName
    .dw viceCButtonTab, viceAButtonTab, viceFlagsTab
    .dw viceGVelTab, viceGDmgTab
    .dw viceCmdTab, viceMotTab, vicePosTab
    .dw viceChainTab
    .dw vicePowTab
    .dw viceTransTab, viceEVelTab
    .dw viceTargetTab
    .dw viceBindTab, viceActTab, viceRevTab
    .dw viceHitSndTab
    .dw viceShakeTab
    .dw viceQuoteTab
    .dw viceExpTab
    .dw vicePauseTab
    .dw VicePalDim
    .db :VicePalDim, 0
    .dw VicePalHi
    .db :VicePalHi, 0
    .dw viceProjTab
    .db :viceSprData, 0                    ; CH_MBANK
    .dw viceProjFxTab, viceProjFxChr
    .dw viceCmdList
    .db 0, viceMaxMask
    .dw viceCancelRow
CharBenimaru:
    .dw benimaruSprOfs, benimaruBoxTab, benimaruAnimTab
    .dw benimaruActiveTab, benimaruDamageTab, benimaruHitTimeTab
    .dw benimaruSlideTab, benimaruHitVelTab, benimaruButtonTab
    .db $30, 0
    .dw BenimaruChr
    .db :BenimaruChr, 0
    .dw BenimaruPal
    .db :BenimaruPal, 0
    .dw benimaruName
    .dw benimaruCButtonTab, benimaruAButtonTab, benimaruFlagsTab
    .dw benimaruGVelTab, benimaruGDmgTab
    .dw benimaruCmdTab, benimaruMotTab, benimaruPosTab
    .dw benimaruChainTab
    .dw benimaruPowTab
    .dw benimaruTransTab, benimaruEVelTab
    .dw benimaruTargetTab
    .dw benimaruBindTab, benimaruActTab, benimaruRevTab
    .dw benimaruHitSndTab
    .dw benimaruShakeTab
    .dw benimaruQuoteTab
    .dw benimaruExpTab
    .dw benimaruPauseTab
    .dw BenimaruPalDim
    .db :BenimaruPalDim, 0
    .dw BenimaruPalHi
    .db :BenimaruPalHi, 0
    .dw benimaruProjTab
    .db :benimaruSprData, 0                    ; CH_MBANK
    .dw athenaProjFxTab, athenaProjFxChr      ; shared orb atlas
    .dw benimaruCmdList
    .db 0, benimaruMaxMask
    .dw benimaruCancelRow
CharDaimon:
    .dw daimonSprOfs, daimonBoxTab, daimonAnimTab
    .dw daimonActiveTab, daimonDamageTab, daimonHitTimeTab
    .dw daimonSlideTab, daimonHitVelTab, daimonButtonTab
    .db $30, 0
    .dw DaimonChr
    .db :DaimonChr, 0
    .dw DaimonPal
    .db :DaimonPal, 0
    .dw daimonName
    .dw daimonCButtonTab, daimonAButtonTab, daimonFlagsTab
    .dw daimonGVelTab, daimonGDmgTab
    .dw daimonCmdTab, daimonMotTab, daimonPosTab
    .dw daimonChainTab
    .dw daimonPowTab
    .dw daimonTransTab, daimonEVelTab
    .dw daimonTargetTab
    .dw daimonBindTab, daimonActTab, daimonRevTab
    .dw daimonHitSndTab
    .dw daimonShakeTab
    .dw daimonQuoteTab
    .dw daimonExpTab
    .dw daimonPauseTab
    .dw DaimonPalDim
    .db :DaimonPalDim, 0
    .dw DaimonPalHi
    .db :DaimonPalHi, 0
    .dw daimonProjTab
    .db :daimonSprData, 0                    ; CH_MBANK
    .dw terryProjFxTab, terryProjFxChr        ; shared shockwave atlas
    .dw daimonCmdList
    .db 0, daimonMaxMask
    .dw daimonCancelRow
.ENDIF

; sel index -> descriptor / generated-data bank.  Ids 0-13 = visible
; original roster, 14 = hidden Omega Rugal, 15+ = mass MSU import.
; CharPtr resolves tables through F_TBANK.  Generated tables (incl.
; CpuPool/NPOOL for the random CPU pick) live in newchars_tabs.inc.
.INCLUDE "gen_fight/newchars_tabs.inc"

HudPal:     .INCBIN "gen_fight/hud_pal.bin"
IoriPal:     .INCBIN "gen_fight/iori_pal.bin"
IoriPalDim:  .INCBIN "gen_fight/iori_pal_dim.bin"
IoriPalHi:   .INCBIN "gen_fight/iori_pal_hi.bin"
KyoPal: .INCBIN "gen_fight/kyo_pal.bin"
KyoPalDim: .INCBIN "gen_fight/kyo_pal_dim.bin"
KyoPalHi: .INCBIN "gen_fight/kyo_pal_hi.bin"
ShingoPal: .INCBIN "gen_fight/shingo_pal.bin"
ShingoPalDim: .INCBIN "gen_fight/shingo_pal_dim.bin"
ShingoPalHi: .INCBIN "gen_fight/shingo_pal_hi.bin"
RugalPal: .INCBIN "gen_fight/rugal_pal.bin"
RugalPalDim: .INCBIN "gen_fight/rugal_pal_dim.bin"
RugalPalHi: .INCBIN "gen_fight/rugal_pal_hi.bin"
.IFNDEF BASE4
SaisyuPal: .INCBIN "gen_fight/saisyu_pal.bin"
SaisyuPalDim: .INCBIN "gen_fight/saisyu_pal_dim.bin"
SaisyuPalHi: .INCBIN "gen_fight/saisyu_pal_hi.bin"
HeidernPal: .INCBIN "gen_fight/heidern_pal.bin"
HeidernPalDim: .INCBIN "gen_fight/heidern_pal_dim.bin"
HeidernPalHi: .INCBIN "gen_fight/heidern_pal_hi.bin"
TakumaPal: .INCBIN "gen_fight/takuma_pal.bin"
TakumaPalDim: .INCBIN "gen_fight/takuma_pal_dim.bin"
TakumaPalHi: .INCBIN "gen_fight/takuma_pal_hi.bin"
ClarkPal: .INCBIN "gen_fight/clark_pal.bin"
ClarkPalDim: .INCBIN "gen_fight/clark_pal_dim.bin"
ClarkPalHi: .INCBIN "gen_fight/clark_pal_hi.bin"
RalfPal: .INCBIN "gen_fight/ralf_pal.bin"
RalfPalDim: .INCBIN "gen_fight/ralf_pal_dim.bin"
RalfPalHi: .INCBIN "gen_fight/ralf_pal_hi.bin"
LeonaPal: .INCBIN "gen_fight/leona_pal.bin"
LeonaPalDim: .INCBIN "gen_fight/leona_pal_dim.bin"
LeonaPalHi: .INCBIN "gen_fight/leona_pal_hi.bin"
MaturePal: .INCBIN "gen_fight/mature_pal.bin"
MaturePalDim: .INCBIN "gen_fight/mature_pal_dim.bin"
MaturePalHi: .INCBIN "gen_fight/mature_pal_hi.bin"
VicePal: .INCBIN "gen_fight/vice_pal.bin"
VicePalDim: .INCBIN "gen_fight/vice_pal_dim.bin"
VicePalHi: .INCBIN "gen_fight/vice_pal_hi.bin"
BenimaruPal: .INCBIN "gen_fight/benimaru_pal.bin"
BenimaruPalDim: .INCBIN "gen_fight/benimaru_pal_dim.bin"
BenimaruPalHi: .INCBIN "gen_fight/benimaru_pal_hi.bin"
DaimonPal: .INCBIN "gen_fight/daimon_pal.bin"
DaimonPalDim: .INCBIN "gen_fight/daimon_pal_dim.bin"
DaimonPalHi: .INCBIN "gen_fight/daimon_pal_hi.bin"
OmegaRugalPal: .INCBIN "gen_fight/omegarugal_pal.bin"
OmegaRugalPalDim: .INCBIN "gen_fight/omegarugal_pal_dim.bin"
OmegaRugalPalHi: .INCBIN "gen_fight/omegarugal_pal_hi.bin"
.ENDIF
SparkChr:   .INCBIN "gen_fight/spark.chr"
SparkPal:   .INCBIN "gen_fight/spark_pal.bin"
WoodPal:    .INCBIN "gen_fight/wood_pal.bin"

.INCLUDE "gen_fight/hud.inc"
.INCLUDE "gen_fight/spark.inc"
.INCLUDE "gen_fight/stages_tab.inc"
.INCLUDE "gen_fight/stgmods.inc"
SongModTab: .db 11, 12, 13, 14, 15, 16, 17, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
; Sound-test ids 7..16 are the ten stage modules; the first seven are the
; frontend/ending songs used by SONG_*.
; Fight-module effect slots 0..4 <- soundbank sources.  Combat needs the
; swing/hit sources plus the FIGHT! and K.O. announcers only; slots 3/4 are
; reserved for the winner/select voices on UI modules.
FightFxSrc: .db 0, 1, 2, 5, 6, 4, 13, 12 ; combat 0-4 + menu select/move/back
UiSrc:      .db 4, 13, 12, 3            ; select, move, back, winner voice
.IFDEF PVSNESLIB
.INCLUDE "gen_audio/sbkeep.inc"
.ENDIF
; mass-import descriptors + palettes (F_TBANK-resident)
.INCLUDE "gen_fight/newchars_desc.inc"
.ENDS

; P2 mirror-match palettes + AltPalRow live in the AltPals bank window.
.INCLUDE "gen_fight/alt_pals.inc"
.BASE $C0                            ; alt_pals.inc links with .BASE $00;
                                     ;   restore the ROM window before the
                                     ;   full-bank data sections below

; KFM generated tables/metasprites overflowed the FightData bank once the
; throw sprites landed; they live in their own bank (F_TBANK addressed).
.IFDEF PVSNESLIB
.BANK 58 SLOT 0
.ELSE
.BANK 126 SLOT 0
.ENDIF
.ORGA $0000                          ; full 64 KiB HiROM window ($C0+)
.SECTION "IoriData" FORCE
.INCLUDE "gen_fight/iori_spr.inc"
.ENDS



; stage/HUD binaries sit in their own bank (referenced via :label); the
; FightData bank is reserved for tblbank-addressed tables
.IFDEF PVSNESLIB
.BANK 127 SLOT 0
.ELSE
.BANK 123 SLOT 0
.ENDIF
.ORGA $8000
.SECTION "StageData" FORCE
HudChr:     .INCBIN "gen_fight/hud.chr"
HudChr_End:
.INCLUDE "gen_fight/stage_anim.inc"
Portraits:  .INCBIN "gen_fight/portraits.chr"
Portraits_End:
PortraitPal: .INCBIN "gen_fight/portrait_pal.bin"
PortraitPal_End:
.INCLUDE "gen_fight/portraits.inc"
.ENDS

; ---------------------------------------------------------------------------
; KYO normalized tables live in their own bank because two generated
; metasprite/AIR sets no longer fit beside the stage data in bank 56.
.IFDEF PVSNESLIB
.BANK 60 SLOT 0
.ELSE
.BANK 127 SLOT 0
.ENDIF
.ORGA $0000                          ; full 64 KiB HiROM window ($C0+)
.SECTION "KyoData" FORCE
.INCLUDE "gen_fight/kyo_spr.inc"
.ENDS

; PVSnesLib banks 26+; standalone ExHiROM uses 95+.
.INCLUDE "gen_fight/kyo_chr.inc"

; ---------------------------------------------------------------------------
; SHINGO generated tables (own 64 KiB bank, F_TBANK-addressed).
.IFDEF PVSNESLIB
.BANK 62 SLOT 0
.ELSE
.BANK 124 SLOT 0
.ENDIF
.ORGA $0000
.SECTION "ShingoData" FORCE
.INCLUDE "gen_fight/shingo_spr.inc"
.ENDS

; PVSnesLib banks 70+.
.INCLUDE "gen_fight/shingo_chr.inc"

; ---------------------------------------------------------------------------
; RUGAL generated tables.
.IFDEF PVSNESLIB
.BANK 44 SLOT 0
.ELSE
.BANK 125 SLOT 0
.ENDIF
.ORGA $0000
.SECTION "RugalData" FORCE
.INCLUDE "gen_fight/rugal_spr.inc"
.ENDS

; Rugal's full AIR metasprite blob lives in a separate low-half bank
; (CH_MBANK).  Bank 17 is free: Iori's CHR uses its upper half, Benimaru's
; low run ends at bank 16.
.IFDEF PVSNESLIB
.BANK 17 SLOT 0
.ELSE
.BANK 17 SLOT 0
.ENDIF
.ORGA $0000
.SECTION "RugalMeta" FORCE
.INCLUDE "gen_fight/rugal_meta.inc"
.ENDS

; OMEGA RUGAL generated tables (F_TBANK) and metasprite blob (CH_MBANK).
; Splitting them keeps the 43K data set out of a single 32K slot: the
; tables live in the low half of bank 118, the 32.5K metasprite blob
; in bank 119's low half (both CPU-mapped via .BASE $00).
; Omega's CHR is ROM-resident in the high halves of banks 95-117.
.IFDEF PVSNESLIB
.BASE $00
.BANK 118 SLOT 0
.ELSE
.BASE $00
.BANK 115 SLOT 0
.ENDIF
.ORGA $1000
.SECTION "OmegaRugalTables" FORCE
.INCLUDE "gen_fight/omegarugal_spr.inc"
.ENDS

.IFDEF PVSNESLIB
.BASE $00
.BANK 119 SLOT 0
.ELSE
.BASE $00
.BANK 116 SLOT 0
.ENDIF
.ORGA $0000
.SECTION "OmegaRugalMeta" FORCE
.INCLUDE "gen_fight/omegarugal_meta.inc"
.ENDS
.BASE $C0

; omega rugal chr takes over the 95-107 run rugal vacated when he moved
; to kof98-snes.msu; rugal_chr.inc is now an empty placeholder.
.INCLUDE "gen_fight/rugal_chr.inc"
.INCLUDE "gen_fight/omegarugal_chr.inc"


; Random stage blobs: all SNES stages converted by tools/build_stages.py
; (banks 51-63 are free in both the standalone ExHiROM and PVSnesLib maps).
.INCLUDE "gen_fight/stages.inc"

; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
.IFNDEF BASE4
; New-char generated tables.  A char's tables must live in ONE CPU bank
; (F_TBANK-addressed), so each gets a full window at ORGA $0000 in a bank
; whose low half is free, or a $8000 half-bank when the data fits in 32K.
.IFDEF PVSNESLIB
.BANK 1 SLOT 0
.ORGA $8000
.SECTION "SaisyuData" FORCE
.INCLUDE "gen_fight/saisyu_spr.inc"
.ENDS
; heidern/ralf exceed 32K: Ralf shares bank 56's tail with SOUNDBANK5,
; leaving bank 59's full window for Heidern.
.BANK 56 SLOT 0
.ORGA $8000
.SECTION "RalfData" FORCE
.INCLUDE "gen_fight/ralf_spr.inc"
.ENDS
.BASE $00
.BANK 83 SLOT 0
.ORGA $0000
.SECTION "TakumaData" FORCE
.INCLUDE "gen_fight/takuma_spr.inc"
.ENDS
; Mature's second super makes the table larger than a 32 KiB half-bank.
; Bank 83's upper half is ShingoChrN, so use the free tail of the sound
; bank instead (the map shows $794C-$FFFF unused).  .BASE $C0 makes the
; full 64 KiB file bank reachable at CPU $F7; without it the $794C start
; sits below the HiROM $8000 window and the sprites read as empty.
.BASE $C0
.BANK 55 SLOT 0
.ORGA $794C                          ; 34484 bytes free in bank 55
.SECTION "MatureData" FORCE
.INCLUDE "gen_fight/mature_spr.inc"
.ENDS
.BASE $C0
.BANK 25 SLOT 0
.ORGA $8000
.SECTION "ClarkData" FORCE
.INCLUDE "gen_fight/clark_spr.inc"
.ENDS
.BANK 59 SLOT 0
.ORGA $0000
.SECTION "HeidernData" FORCE
.INCLUDE "gen_fight/heidern_spr.inc"
.ENDS
.BANK 57 SLOT 0
.ORGA $8000
.SECTION "LeonaData" FORCE
.INCLUDE "gen_fight/leona_spr.inc"
.ENDS
.BANK 60 SLOT 0
.ORGA $9000                          ; KyoData is allowed to grow to $9000;
                                     ; ViceData (<= $7000) fills the rest.
.SECTION "ViceData" FORCE
.INCLUDE "gen_fight/vice_spr.inc"
.ENDS
; benimaru tables fit a low half (bank 42, ends before $8000); daimon's
; ~41K spill past $8000, so it takes bank 44 -- free because Kyo runs
; 0.82 (18 slices, banks 26-43) instead of 0.85.
.BANK 61 SLOT 0
.ORGA $0000
.SECTION "BenimaruData" FORCE
.INCLUDE "gen_fight/benimaru_spr.inc"
.ENDS
.BANK 63 SLOT 0
.ORGA $0000
.SECTION "DaimonData" FORCE
.INCLUDE "gen_fight/daimon_spr.inc"
.ENDS
.ELSE
.BANK 90 SLOT 0
.ORGA $0000
.SECTION "SaisyuData" FORCE
.INCLUDE "gen_fight/saisyu_spr.inc"
.ENDS
.BANK 91 SLOT 0
.ORGA $0000
.SECTION "HeidernData" FORCE
.INCLUDE "gen_fight/heidern_spr.inc"
.ENDS
.BANK 92 SLOT 0
.ORGA $0000
.SECTION "TakumaData" FORCE
.INCLUDE "gen_fight/takuma_spr.inc"
.ENDS
.BANK 93 SLOT 0
.ORGA $0000
.SECTION "ClarkData" FORCE
.INCLUDE "gen_fight/clark_spr.inc"
.ENDS
.BANK 94 SLOT 0
.ORGA $0000
.SECTION "RalfData" FORCE
.INCLUDE "gen_fight/ralf_spr.inc"
.ENDS
.BANK 96 SLOT 0
.ORGA $0000
.SECTION "LeonaData" FORCE
.INCLUDE "gen_fight/leona_spr.inc"
.ENDS
.BANK 97 SLOT 0
.ORGA $0000
.SECTION "MatureData" FORCE
.INCLUDE "gen_fight/mature_spr.inc"
.ENDS
.BANK 98 SLOT 0
.ORGA $0000
.SECTION "ViceData" FORCE
.INCLUDE "gen_fight/vice_spr.inc"
.ENDS
.BANK 99 SLOT 0
.ORGA $0000
.SECTION "BenimaruData" FORCE
.INCLUDE "gen_fight/benimaru_spr.inc"
.ENDS
.BANK 100 SLOT 0
.ORGA $0000
.SECTION "DaimonData" FORCE
.INCLUDE "gen_fight/daimon_spr.inc"
.ENDS
.ENDIF

; MSU-1 build: the six/eight new chars stream tiles from kof98-snes.msu
; through $2000-$2007; their _chr.inc files are empty placeholders.
.INCLUDE "gen_fight/saisyu_chr.inc"
.INCLUDE "gen_fight/heidern_chr.inc"
.INCLUDE "gen_fight/takuma_chr.inc"
.INCLUDE "gen_fight/clark_chr.inc"
.INCLUDE "gen_fight/ralf_chr.inc"
.INCLUDE "gen_fight/leona_chr.inc"
.INCLUDE "gen_fight/mature_chr.inc"
.INCLUDE "gen_fight/vice_chr.inc"
.INCLUDE "gen_fight/benimaru_chr.inc"
.INCLUDE "gen_fight/daimon_chr.inc"
.ENDIF
; mass-import bank windows + chr placeholders
.INCLUDE "gen_fight/newchars_banks.inc"
