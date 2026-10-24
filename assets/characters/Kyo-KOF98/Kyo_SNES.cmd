; Kyo_SNES.cmd -- synthetic command table for the SNES fight engine.
; The original Kyo.cmd is an ikaruga-style file: buttons/motions are decoded
; through helper vars, so the native command matcher finds nothing.  This
; file keeps the real motion definitions (same syntax as Kyo.cmd's [Command]
; section) and rewrites the [State -1] entries in kfm.cmd dialect so
; build_fight.py can compile ButtonTab/CmdTab/MotTab/ChainTab.
;
; SNES pad mapping (tools/build_fight.py "buttons"):
;   x = light punch (SNES B), y = strong punch (SNES Y)
;   a = light kick  (SNES A), b = strong kick  (SNES X)

;=========================[ Command definitions ]============================

[Command]
name = "MAX_SUPER"
command = ~F, DF, D, DB, B, F, DF, D, DB, B, x+y
time = 30

[Command]
name = "SUPER_X"
command = ~F, DF, D, DB, B, F, DF, D, DB, B, x
time = 30

[Command]
name = "QQCF_PP"
command = ~D, DF, F, D, DF, F, x+y
time = 25

[Command]
name = "QCBHCF_X"
command = ~D, DB, B, DB, D, DF, F, x
time = 25

[Command]
name = "QCBHCF_Y"
command = ~D, DB, B, DB, D, DF, F, y
time = 25

[Command]
name = "QQCF_X"
command = ~D, DF, F, D, DF, F, x
time = 25

[Command]
name = "QQCF_Y"
command = ~D, DF, F, D, DF, F, y
time = 25

[Command]
name = "HCB_A"
command = ~F, DF, D, DB, B, a
time = 20

[Command]
name = "HCB_B"
command = ~F, DF, D, DB, B, b
time = 20

[Command]
name = "DP_X"
command = ~F, D, DF, x
time = 15

[Command]
name = "DP_Y"
command = ~F, D, DF, y
time = 15

[Command]
name = "DP_A"
command = ~F, D, DF, a
time = 15

[Command]
name = "DP_B"
command = ~F, D, DF, b
time = 15

[Command]
name = "RDP_A"
command = ~B, D, DB, a
time = 15

[Command]
name = "RDP_B"
command = ~B, D, DB, b
time = 15

[Command]
name = "QCB_X"
command = ~D, DB, B, x
time = 15

[Command]
name = "QCB_Y"
command = ~D, DB, B, y
time = 15

[Command]
name = "QCB_A"
command = ~D, DB, B, a
time = 15

[Command]
name = "QCB_B"
command = ~D, DB, B, b
time = 15

[Command]
name = "QCF_X"
command = ~D, DF, F, x
time = 15

[Command]
name = "QCF_Y"
command = ~D, DF, F, y
time = 15

[Command]
name = "QCF_A"
command = ~D, DF, F, a
time = 15

[Command]
name = "QCF_B"
command = ~D, DF, F, b
time = 15

; Yami Barai (108 Shiki): match Kyo's original MUGEN 40-frame back charge,
; then forward + punch.  Extra variants accept the punch a tick later or a
; slight down-back roll while preserving the charge requirement.
[Command]
name = "BF_X"
command = ~40B, F+x
time = 240

[Command]
name = "BF_X"
command = ~40B, F, x
time = 240

[Command]
name = "BF_X"
command = ~40B, DB, F+x
time = 240

[Command]
name = "BF_Y"
command = ~40B, F+y
time = 240

[Command]
name = "BF_Y"
command = ~40B, F, y
time = 240

[Command]
name = "BF_Y"
command = ~40B, DB, F+y
time = 240

[Command]
name = "DF_B"
command = ~DF, b
time = 8

[Command]
name = "F_A"
command = ~F, a
time = 8

[Command]
name = "AIR_D_Y"
command = ~D, y
time = 8

[Command]
name = "CD"
command = y+b
time = 15

[Command]
name = "DODGE"
command = x+a
time = 15

[Command]
name = "FF"
command = F, F
time = 10

[Command]
name = "BB"
command = B, B
time = 10

[Command]
name = "ESQ_L"
command = c
time = 4

[Command]
name = "ESQ_F"
command = /F, c
time = 8

[Command]
name = "ESQ_B"
command = /B, c
time = 8

[Command]
name = "CHARGE"
command = x+y+a+z
time = 6

[Command]
name = "MAX_ON"
command = x+y+a
time = 6

[Command]
name = "recovery"
command = x+a

[Command]
name = "x"
command = x
time = 1

[Command]
name = "y"
command = y
time = 1

[Command]
name = "z"
command = z
time = 1

[Command]
name = "a"
command = a
time = 1

[Command]
name = "b"
command = b
time = 1

[Command]
name = "c"
command = c
time = 1

[Command]
name = "start"
command = s
time = 1

[Command]
name = "holdfwd"
command = /$F

[Command]
name = "holdback"
command = /$B

[Command]
name = "holdup"
command = /$U

[Command]
name = "holddown"
command = /$D

[Command]
name = "down_a"
command = /$D,a
time = 1

[Command]
name = "down_b"
command = /$D,b
time = 1

[Command]
name = "fwd"
command = F

[Command]
name = "back"
command = B

[Command]
name = "up"
command = U

[Command]
name = "down"
command = D

;=============================[ State entry ]=================================
; Supers first (longest motions), then specials, movement, throw, normals.

[Statedef -1]

[State -1, MAX Saishuu Kessen Ougi Mushiki]
type = ChangeState
value = 3550
triggerall = command = "MAX_SUPER"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, 108-Shiki '99]
type = ChangeState
value = 3305
triggerall = command = "QQCF_PP"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Saishuu Kessen Ougi Mushiki (strong)]
type = ChangeState
value = 3210
triggerall = command = "QQCF_Y"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Saishuu Kessen Ougi Mushiki (weak)]
type = ChangeState
value = 3200
triggerall = command = "QQCF_X"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Chou Hissatsu Waza]
type = ChangeState
value = 3500
triggerall = command = "SUPER_X"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Oboro Guruma (strong)]
type = ChangeState
value = 1510
triggerall = command = "QCB_B"
triggerall = statetype != A
trigger1 = ctrl

[State -1, Oboro Guruma (weak)]
type = ChangeState
value = 1500
triggerall = command = "QCB_A"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Oniyaki (strong)]
type = ChangeState
value = 1110
triggerall = command = "DP_Y"
triggerall = statetype != A
trigger1 = ctrl

[State -1, Oniyaki (weak)]
type = ChangeState
value = 1100
triggerall = command = "DP_X"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, R.E.D. Kick (strong)]
type = ChangeState
value = 1810
triggerall = command = "RDP_B"
triggerall = statetype != A
trigger1 = ctrl

[State -1, R.E.D. Kick (weak)]
type = ChangeState
value = 1800
triggerall = command = "RDP_A"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, 910-shiki (strong)]
type = ChangeState
value = 1310
triggerall = command = "QCB_Y"
triggerall = statetype != A
trigger1 = ctrl

[State -1, 910-shiki (weak)]
type = ChangeState
value = 1300
triggerall = command = "QCB_X"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, 75-shiki Kai (strong)]
type = ChangeState
value = 1210
triggerall = command = "QCF_B"
triggerall = statetype != A
trigger1 = ctrl

[State -1, 75-shiki Kai (weak)]
type = ChangeState
value = 1200
triggerall = command = "QCF_A"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Dokugami]
type = ChangeState
value = 1700
triggerall = command = "QCF_Y"
triggerall = statetype != A
trigger1 = ctrl

[State -1, 108-Shiki: Yami Barai (strong)]
type = ChangeState
value = 1010
triggerall = command = "BF_Y"
triggerall = statetype != A
trigger1 = ctrl

[State -1, 108-Shiki: Yami Barai (weak)]
type = ChangeState
value = 1000
triggerall = command = "BF_X"
triggerall = statetype != A
trigger1 = ctrl

[State -1, Aragami]
type = ChangeState
value = 1600
triggerall = command = "QCF_X"
triggerall = statetype != A
trigger1 = ctrl



;---------------------------------------------------------------------------


;---------------------------------------------------------------------------
; FUSION MODE: R+Y+B+X held = manual charge (Extra), Y+B+X = MAX burst
[State -1, Fusion Charge]
type = ChangeState
value = 760
triggerall = command = "CHARGE"
triggerall = statetype = S
trigger1 = ctrl

[State -1, Fusion MAX Activate]
type = ChangeState
value = 750
triggerall = command = "MAX_ON"
triggerall = statetype = S
trigger1 = ctrl
;---------------------------------------------------------------------------  
; FUSION MODE: L = Extra dodge (stationary), F+L = Adv roll fwd, B+L = back
[State -1, Fusion Roll Fwd]
type = ChangeState
value = 700
triggerall = command = "ESQ_F"
triggerall = statetype = S
trigger1 = ctrl

[State -1, Fusion Roll Back]
type = ChangeState
value = 710
triggerall = command = "ESQ_B"
triggerall = statetype = S
trigger1 = ctrl
[State -1, Fusion Extra Dodge]
type = ChangeState
value = 720
triggerall = command = "ESQ_L"
triggerall = command != "holdfwd"
triggerall = command != "holdback"
triggerall = statetype = S
trigger1 = ctrl


[State -1, Attack Dodge]
type = ChangeState
value = 720
triggerall = command = "DODGE"
triggerall = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Blowback Attack]
type = ChangeState
value = 250
triggerall = command = "CD"
triggerall = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Run Fwd]
type = ChangeState
value = 100
trigger1 = command = "FF"
trigger1 = statetype = S
trigger1 = ctrl

[State -1, Run Back]
type = ChangeState
value = 105
trigger1 = command = "BB"
trigger1 = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Throw]
type = ChangeState
value = 800
triggerall = command = "y"
triggerall = statetype = S
triggerall = ctrl
trigger1 = command = "holdfwd"
trigger1 = p2bodydist x < 15
trigger1 = (p2statetype = S) || (p2statetype = C)
trigger2 = command = "holdback"
trigger2 = p2bodydist x < 15
trigger2 = (p2statetype = S) || (p2statetype = C)

;---------------------------------------------------------------------------
[State -1, Taunt]
type = ChangeState
value = 160
triggerall = command = "start"
trigger1 = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Stand Light Punch]
type = ChangeState
value = 200
triggerall = command = "x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl

[State -1, Stand Strong Punch]
type = ChangeState
value = 210
triggerall = command = "y"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl

[State -1, Stand Light Kick]
type = ChangeState
value = 230
triggerall = command = "a"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl

[State -1, Stand Strong Kick]
type = ChangeState
value = 240
triggerall = command = "b"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1, Crouching Light Punch]
type = ChangeState
value = 400
triggerall = command = "x"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl

[State -1, Crouching Strong Punch]
type = ChangeState
value = 410
triggerall = command = "y"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = (stateno = 400) || (stateno = 430)
trigger2 = (time > 9) || (movecontact && time > 5)

[State -1, Crouching Light Kick]
type = ChangeState
value = 430
triggerall = command = "a"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = (stateno = 400) || (stateno = 430)
trigger2 = (time > 9) || (movecontact && time > 5)

[State -1, Crouching Strong Kick]
type = ChangeState
value = 440
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = (stateno = 400) || (stateno = 430)
trigger2 = (time > 9) || (movecontact && time > 5)

;---------------------------------------------------------------------------
[State -1, Jump Light Punch]
type = ChangeState
value = 600
triggerall = command = "x"
trigger1 = statetype = A
trigger1 = ctrl
trigger2 = stateno = 600
trigger2 = statetime >= 7

[State -1, Jump Strong Punch]
type = ChangeState
value = 610
triggerall = command = "y"
trigger1 = statetype = A
trigger1 = ctrl
trigger2 = stateno = 600 || stateno = 630
trigger2 = movecontact

[State -1, Jump Light Kick]
type = ChangeState
value = 630
triggerall = command = "a"
trigger1 = statetype = A
trigger1 = ctrl

[State -1, Jump Strong Kick]
type = ChangeState
value = 640
triggerall = command = "b"
trigger1 = statetype = A
trigger1 = ctrl
trigger2 = stateno = 600 || stateno = 630
trigger2 = movecontact
