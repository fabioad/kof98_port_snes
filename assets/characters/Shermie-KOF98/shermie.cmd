;-| Super Motions |--------------------------------------------------------

[Command]
name = "qcb2x"
command = ~D, DB, B, D, DB, B, x
time = 30

[Command]
name = "qcb2y"
command = ~D, DB, B, D, DB, B, y
time = 30

[Command]
name = "qcb2p"
command = ~D, DB, B, D, DB, B, x
time = 30

[Command]
name = "qcb2p"
command = ~D, DB, B, D, DB, B, y
time = 30

[Command]
name = "qcf2x"
command = ~D, DF, F, D, DF, F, x
time = 30

[Command]
name = "qcf2y"
command = ~D, DF, F, D, DF, F, y
time = 30

[Command]
name = "qcf2p"
command = ~D, DF, F, D, DF, F, x
time = 30

[Command]
name = "qcf2p"
command = ~D, DF, F, D, DF, F, y
time = 30

[Command]
name = "qcf2a"
command = ~D, DF, F, D, DF, F, a
time = 30

[Command]
name = "qcf2b"
command = ~D, DF, F, D, DF, F, b
time = 30

[Command]
name = "qcf2k"
command = ~D, DF, F, D, DF, F, a
time = 30

[Command]
name = "qcf2k"
command = ~D, DF, F, D, DF, F, b
time = 30

[Command]
name = "hcf2x"
command = ~DB, F, DB, F, x
time = 60

[Command]
name = "hcf2y"
command = ~DB, F, DB, F, y
time = 60

[Command]
name = "hcf2p"
command = ~DB, F, DB, F, x
time = 60

[Command]
name = "hcf2p"
command = ~DB, F, DB, F, y
time = 60

[Command]
name = "hcb2x"
command = ~DF, B, DF, B, x
time = 60

[Command]
name = "hcb2y"
command = ~DF, B, DF, B, y
time = 60

[Command]
name = "hcb2p"
command = ~DF, B, DF, B, x
time = 60

[Command]
name = "hcb2p"
command = ~DF, B, DF, B, y
time = 60

;-| Special Motions |------------------------------------------------------

[Command]
name = "dp_a"
command = ~F, D, DF, a
time = 15

[Command]
name = "dp_b"
command = ~F, D, DF, b
time = 15

[Command]
name = "qcf_a"
command = ~D, DF, F, a
time = 15

[Command]
name = "qcf_b"
command = ~D, DF, F, b
time = 15

[Command]
name = "qcf_k"
command = ~D, DF, F, a
time = 15

[Command]
name = "qcf_k"
command = ~D, DF, F, b
time = 15

[Command]
name = "qcb_x"
command = ~D, DB, B, x
time = 15

[Command]
name = "qcb_y"
command = ~D, DB, B, y
time = 15

[Command]
name = "qcb_a"
command = ~D, DB, B, a
time = 15

[Command]
name = "qcb_b"
command = ~D, DB, B, b
time = 15

[Command]
name = "qcb_k"
command = ~D, DB, B, a
time = 15

[Command]
name = "qcb_k"
command = ~D, DB, B, b
time = 15

[Command]
name = "hcf_x"
command = ~B, DB, D, DF, F, x
time = 30

[Command]
name = "hcf_y"
command = ~B, DB, D, DF, F, y
time = 30

[Command]
name = "hcf_p"
command = ~B, DB, D, DF, F, x
time = 30

[Command]
name = "hcf_p"
command = ~B, DB, D, DF, F, y
time = 30

[Command]
name = "hcf_a"
command = ~B, DB, D, DF, F, a
time = 30

[Command]
name = "hcf_b"
command = ~B, DB, D, DF, F, b
time = 30

[Command]
name = "longjump"
command = ~D, $U
time = 5

;-| Double Tap |-----------------------------------------------------------

[Command]
name = "FF"
command = F, F
time = 10

[Command]
name = "BB"
command = B, B
time = 10

;-| 2/3 Button Combination |-----------------------------------------------

[Command]
name = "recovery"
command = x+y
time = 1

[Command]
name = "dodge"
command = x+a
time = 1

[Command]
name = "knockdown"
command = y+b
time = 1

[Command]
name = "abc"
command = a+b+c
time = 1

;-| Dir + Button |---------------------------------------------------------

[Command]
name = "fwd_x"
command = /F,x

[Command]
name = "fwd_a"
command = /F,a
time = 1

[Command]
name = "fwd_b"
command = /F, b
time = 1

;-| Single Button |---------------------------------------------------------

[Command]
name = "a"
command = a
time = 1

[Command]
name = "hold_a"
command = /$a
time = 1

[Command]
name = "b"
command = b
time = 1

[Command]
name = "hold_b"
command = /$b
time = 1

[Command]
name = "c"
command = c
time = 1

[Command]
name = "x"
command = x
time = 1

[Command]
name = "hold_x"
command = /$x
time = 1

[Command]
name = "y"
command = y
time = 1

[Command]
name = "hold_y"
command = /$y
time = 1

[Command]
name = "z"
command = z
time = 1

[Command]
name = "hold_z"
command = /$z
time = 1

[Command]
name = "s"
command = s
time = 1

;-| Hold Dir |--------------------------------------------------------------

[Command]
name = "holdfwd_x"
command = /$F, x
time = 1

[Command]
name = "holdfwd_y"
command = /$F, y
time = 1

[Command]
name = "holdfwd"
command = /$F
time = 1

[Command]
name = "holdback"
command = /$B
time = 1

[Command]
name = "holdup"
command = /$U
time = 1

[Command]
name = "holddown"
command = /$D
time = 1

;-|Commands|------------------------------------------------------------------------------

[Statedef -1]

; SDM Shukumei, gen'ei, shinshi
[State -1]
type = ChangeState
value = 8050
triggerall = Var(4) && ((command = "qcf2k" && power >= 1000 && life <= 150) || (command = "qcf2b" && power >= 2000))
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; DM Shukumei, gen'ei, shinshi
[State -1]
type = ChangeState
value = 8000
triggerall = Var(4) && command = "qcf2k" && (life <= 150 || power >= 1000)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; SDM Ankoku raikohken
[State -1]
type = ChangeState
value = 8150
triggerall = Var(4) && ((command = "qcf2p" && power >= 1000 && life <= 150) || (command = "qcf2y" && power >= 2000))
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; DM Ankoku raikohken
[State -1]
type = ChangeState
value = 8100
triggerall = Var(4) && command = "qcf2p" && (life <= 150 || power >= 1000)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Light Shajitsu no odori
[State -1]
type = ChangeState
value = 7000
triggerall = command = "qcb_a" && Var(4)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Hard Shajitsu no odori
[State -1]
type = ChangeState
value = 7050
triggerall = command = "qcb_b" && Var(4)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Light Raijin no tsue
[State -1]
type = ChangeState
value = 7100
triggerall = command = "qcf_a" && Var(4)
trigger1 = statetype = A && ctrl

; Hard Raijin no tsue
[State -1]
type = ChangeState
value = 7150
triggerall = command = "qcf_b" && Var(4)
trigger1 = statetype = A && ctrl

; Close Mugetsu no raiun
[State -1]
type = ChangeState
value = 7200
triggerall = command = "hcf_x" && NumProj = 0 && Var(4)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Medium close Mugetsu no raiun
[State -1]
type = ChangeState
value = 7225
triggerall = command = "hcf_a" && NumProj = 0 && Var(4)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Medium far Mugetsu no raiun
[State -1]
type = ChangeState
value = 7250
triggerall = command = "hcf_y" && NumProj = 0 && Var(4)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Far Mugetsu no raiun
[State -1]
type = ChangeState
value = 7275
triggerall = command = "hcf_b" && NumProj = 0 && Var(4)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Light Yatanagi no muchi
[State -1]
type = ChangeState
value = 7300
triggerall = command = "qcb_x" && Var(4)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Hard Yatanagi no muchi
[State -1]
type = ChangeState
value = 7350
triggerall = command = "qcb_y" && Var(4)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; SDM Shermie flash
[State -1]
type = ChangeState
value = 2250
triggerall = Var(4) = 0 && ((command = "hcb2p" && power >= 1000 && life <= 150) || (command = "hcb2y" && power >= 2000))
triggerall = P2BodyDist X <= 25 && P2Statetype != A
trigger1 = statetype != A && ctrl
trigger1 = p2stateno != 5120
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; DM Shermie flash
[State -1]
type = ChangeState
value = 2200
triggerall = Var(4) = 0 && command = "hcb2p" && (life <= 150 || power >= 1000)
triggerall = P2BodyDist X <= 25 && P2Statetype != A
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Orochi no chikara o mezameru
[State -1]
type = ChangeState
value = 2000
trigger1 = command = "qcb2p" && power >= 2000 && Var(4) = 0 && statetype != A && ctrl

; SDM Shermie carnival
[State -1]
type = ChangeState
value = 2150
triggerall = Var(4) = 0 && ((command = "hcf2p" && power >= 1000 && life <= 150) || (command = "hcf2y" && power >= 2000))
triggerall = P2BodyDist X <= 25 && P2Statetype != A
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; DM Shermie carnival
[State -1]
type = ChangeState
value = 2100
triggerall = Var(4) = 0 && command = "hcf2p" && (life <= 150 || power >= 1000)
triggerall = P2BodyDist X <= 25 && P2Statetype != A
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Light Axle spin kick
[State -1]
type = ChangeState
value = 1000
triggerall = command = "qcb_a" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Hard Axle spin kick
[State -1]
type = ChangeState
value = 1050
triggerall = command = "qcb_b" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Light Shermie shoot
[State -1]
type = ChangeState
value = 1100
triggerall = command = "hcf_a" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Hard Shermie shoot
[State -1]
type = ChangeState
value = 1150
triggerall = command = "hcf_b" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Light Shermie whip
[State -1]
type = ChangeState
value = 1200
triggerall = command = "qcb_x" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Hard Shermie whip
[State -1]
type = ChangeState
value = 1250
triggerall = command = "qcb_y" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Shermie spiral
[State -1]
type = ChangeState
value = 1300
triggerall = command = "hcf_p" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Light Shermie clutch
[State -1]
type = ChangeState
value = 1400
triggerall = command = "dp_a" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Hard Shermie clutch
[State -1]
type = ChangeState
value = 1450
triggerall = command = "dp_b" && Var(4) = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger3 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger4 = stateno = 231 && AnimElem = 8, >= 0 && AnimElem = 9, < 0
trigger5 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger6 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger7 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Shermie cute
[State -1]
type = VarSet
var(8) = 1
trigger1 = command = "qcb_k"
trigger1 = (stateno = 1210 || stateno = 1260) && AnimElem = 14, >= 0 && AnimElem = 16, < 0
trigger2 = command = "qcb_k"
trigger2 = stateno = 1350 && AnimElem = 1, >= 0 && AnimElem = 3, < 0
trigger3 = command = "qcf_k"
trigger3 = (stateno = 1425 || stateno = 1475) && AnimElem = 1, >= 0 && AnimElem = 3, < 0

; Roll forward
[State -1]
type = ChangeState
value = 750
triggerall = command = "dodge" ^^ command = "z"
trigger1 = command = "holdfwd" && statetype = S && ctrl
trigger2 = (stateno = 150 || stateno = 152) && command != "holdback" && power >= 500

; Roll backwards
[State -1]
type = ChangeState
value = 775
triggerall = command = "dodge" ^^ command = "z"
trigger1 = command = "holdback" && statetype = S && ctrl
trigger2 = (stateno = 150 || stateno = 152) && power >= 500

; Dodge
[State -1]
type = ChangeState
value = 725
trigger1 = command = "dodge" ^^ command = "z"
trigger1 = statetype = S && ctrl

; Standing knockdown attack
[State -1]
type = ChangeState
value = 280
triggerall = command = "knockdown" ^^ command = "c"
trigger1 = statetype = S && ctrl
trigger2 = (stateno = 150 || stateno = 152) && power >= 500

; Standing light punch
[State -1]
type = ChangeState
value = 200
triggerall = command = "x" && command != "holddown"
trigger1 = statetype = S && ctrl
trigger2 = stateno = 200 && AnimElem = 5, >= 1
trigger3 = stateno = 400 && AnimElem = 5, >= 1
trigger4 = stateno = 420 && AnimElem = 8, >= 1

; Shermie stand / Kourai (link)
[State -1]
type = ChangeState
value = 231
triggerall = command = "holdfwd" && command = "a"
trigger1 = stateno = 200 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger2 = stateno = 220 && AnimElem = 3, >= 0 && AnimElem = 4, < 2
trigger3 = stateno = 245 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger4 = stateno = 400 && AnimElem = 4, >= 0 && AnimElem = 6, < 0
trigger5 = stateno = 440 && AnimElem = 4, >= 0 && AnimElem = 6, < 0

; Shermie stand / Kourai
[State -1]
type = ChangeState
value = 230
trigger1 = command = "holdfwd" && command = "a"
trigger1 = statetype = S && ctrl

; Standing light kick
[State -1]
type = ChangeState
value = 220
triggerall = command = "a" && command != "holddown"
trigger1 = statetype = S && ctrl
trigger2 = stateno = 200 && AnimElem = 5, >= 1
trigger3 = stateno = 400 && AnimElem = 5, >= 1

; Shermie flash original / Bakurai
[State -1]
type = ChangeState
value = 800
trigger1 = command = "holdfwd" && command = "y"
trigger1 = statetype = S && ctrl && stateno != 100
trigger1 = P2bodydist X <= 10 && P2movetype != H && P2Stateno != 5120

; Standing hard punch (close)
[State -1]
type = ChangeState
value = 245
trigger1 = command = "y" && statetype = S && P2bodydist X <= 36 && command != "holddown" && ctrl

; Standing hard punch
[State -1]
type = ChangeState
value = 240
trigger1 = command = "y" && statetype = S && command != "holddown" && ctrl

; Front flash / Enrai
[State -1]
type = ChangeState
value = 850
trigger1 = command = "holdfwd" && command = "b"
trigger1 = statetype = S && ctrl && stateno != 100
trigger1 = P2bodydist X <= 10 && P2movetype != H && P2Stateno != 5120

; Standing hard kick
[State -1]
type = ChangeState
value = 260
trigger1 = command = "b" && statetype = S && command != "holddown" && ctrl

; Crouching light punch
[State -1]
type = ChangeState
value = 400
triggerall = command = "x"
trigger1 = statetype = C && ctrl
trigger2 = stateno = 200 && AnimElem = 5, >= 1
trigger3 = stateno = 400 && AnimElem = 5, >= 1

; Crouching light kick
[State -1]
type = ChangeState
value = 420
triggerall = command = "a"
trigger1 = statetype = C && ctrl
trigger2 = stateno = 200 && AnimElem = 5, >= 1
trigger3 = stateno = 400 && AnimElem = 5, >= 1

; Crouching hard punch
[State -1]
type = ChangeState
value = 440
trigger1 = command = "y" && statetype = C && ctrl

; Crouching hard kick
[State -1]
type = ChangeState
value = 460
trigger1 = command = "b" && statetype = C && ctrl

; Jumping knockdown attack
[State -1]
type = ChangeState
value = 680
trigger1 = statetype = A && ctrl
trigger1 = command = "knockdown" || command = "c"

; Jumping light punch
[State -1]
type = ChangeState
value = 600
trigger1 = command = "x" && statetype = A && ctrl

; Jumping light kick
[State -1]
type = ChangeState
value = 620
trigger1 = command = "a" && statetype = A &&  ctrl

; Jumping hard punch
[State -1]
type = ChangeState
value = 640
trigger1 = command = "y" && statetype = A && ctrl

; Jumping hard kick
[State -1]
type = ChangeState
value = 660
trigger1 = stateno != 950
trigger1 = command = "b" && statetype = A && Vel X = 0 && ctrl

; Diagonal jumping hard kick
[State -1]
type = ChangeState
value = 670
trigger1 = command = "b" && statetype = A && ctrl

; Power charge
[State -1]
type = ChangeState
value = 700
trigger1 = command = "hold_x" && command = "hold_a" && command = "hold_y"
trigger1 = power < 3000 && statetype = S && ctrl

; Taunt
[State -1]
type = ChangeState
value = IfElse((Var(4) = 0),195,6195)
trigger1 = command = "s" && statetype = S && ctrl
trigger1 = stateno != 195 && stateno != 6195

; Run Forward
[State -1]
type = ChangeState
value = 100
trigger1 = command = "FF" && statetype = S && command != "holddown" && ctrl

; Run Backwards
[State -1]
type = ChangeState
value = 105
trigger1 = command = "BB" && statetype = S && command != "holddown" && ctrl