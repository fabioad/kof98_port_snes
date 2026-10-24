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
name = "qcbhcfx"
command = ~D, DB, B, DB, D, DF, F, x
time = 45

[Command]
name = "qcbhcfy"
command = ~D, DB, B, DB, D, DF, F, y
time = 45

[Command]
name = "qcbhcfp"
command = ~D, DB, B, DB, D, DF, F, x
time = 45

[Command]
name = "qcbhcfp"
command = ~D, DB, B, DB, D, DF, F, y
time = 45

[Command]
name = "qcfhcba"
command = ~D, DF, F, DF, D, DB, B, a
time = 45

[Command]
name = "qcfhcbb"
command = ~D, DF, F, DF, D, DB, B, b
time = 45

[Command]
name = "qcfhcbk"
command = ~D, DF, F, DF, D, DB, B, a
time = 45

[Command]
name = "qcfhcbk"
command = ~D, DF, F, DF, D, DB, B, b
time = 45

[Command]
name = "qcfhcbk2"
command = ~D, DF, F, DF, D, DB, B, a+b
time = 45

;-| Special Motions |------------------------------------------------------

[Command]
name = "qcb_x"
command = ~D, DB, B, x
time = 15

[Command]
name = "qcb_y"
command = ~D, DB, B, y
time = 15

[Command]
name = "rdp_a"
command = ~B, D, DB, a
time = 15

[Command]
name = "rdp_b"
command = ~B, D, DB, b
time = 15

[Command]
name = "charge_x"
command = ~30$B, F, x
time = 15

[Command]
name = "charge_y"
command = ~30$B, F, y
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
name = "dp_x"
command = ~F, D, DF, x
time = 15

[Command]
name = "dp_y"
command = ~F, D, DF, y
time = 15

[Command]
name = "hcf_x"
command = ~B, DB, D, DF, F, x
time = 15

[Command]
name = "hcf_y"
command = ~B, DB, D, DF, F, y
time = 15

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

; SDM Niku man o kuu
[State -1]
type = ChangeState
value = 2050
triggerall = (command = "qcb2p" && power >= 1000 && life <= 150) || (command = "qcb2y" && power >= 2000)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; DM Niku man o kuu
[State -1]
type = ChangeState
value = 2000
triggerall = command = "qcb2p" && (life <= 150 || power >= 1000)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; SDM Sen ki hakkei
[State -1]
type = ChangeState
value = 2150
triggerall = (command = "qcf2p" && power >= 1000 && life <= 150) || (command = "qcf2y" && power >= 2000)
triggerall = P2statetype != A && P2bodydist X < 30 && P2stateno != 40 && P2stateno != 5110 && P2stateno != 5120
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; DM Sen ki hakkei
[State -1]
type = ChangeState
value = 2100
triggerall = command = "qcf2p" && (life <= 150 || power >= 1000)
triggerall = P2statetype != A && P2bodydist X < 30 && P2stateno != 40 && P2stateno != 5110 && P2stateno != 5120
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; SDM Chouryuu renken
[State -1]
type = ChangeState
value = 2250
triggerall = (command = "qcbhcfp" && power >= 1000 && life <= 150) || (command = "qcbhcfy" && power >= 2000)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; DM Chouryuu renken
[State -1]
type = ChangeState
value = 2200
triggerall = command = "qcbhcfp" && (life <= 150 || power >= 1000)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

[State -1]
type = ChangeState
value = 2400
triggerall = ((command = "qcfhcba" || command = "qcfhcbb")  && power >= 1000 && life <= 150) || (command = "qcfhcbk2" && power >= 2000)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

[State -1]
type = ChangeState
value = IfElse(command = "qcfhcba",2300,2350)
triggerall = command = "qcfhcbk" && (life <= 150 || power >= 1000)
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Light Ryuu sou geki
[State -1]
type = ChangeState
value = 1100
triggerall = command = "qcb_x"
trigger1 = statetype = A && ctrl
trigger2 = stateno = 226 && AnimElem = 2, >= 0 && AnimElem = 4, < 0 && MoveContact

; Hard Ryuu sou geki
[State -1]
type = ChangeState
value = 1140
triggerall = command = "qcb_y"
trigger1 = statetype = A && ctrl
trigger2 = stateno = 226 && AnimElem = 2, >= 0 && AnimElem = 4, < 0 && MoveContact

; Light Cho kyu dan
[State -1]
type = ChangeState
value = 1000
triggerall = command = "qcb_x" && Numproj = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Hard Cho kyu dan
[State -1]
type = ChangeState
value = 1010
triggerall = command = "qcb_y" && Numproj = 0
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Light Ryu geki sai
[State -1]
type = ChangeState
value = 1200
triggerall = command = "rdp_a"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Hard Ryu geki sai
[State -1]
type = ChangeState
value = 1230
triggerall = command = "rdp_b"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Ryuu renga: chiryuu
[State -1]
type = ChangeState
value = 1600
triggerall = command = "hcf_x"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Ryuu renga: tenryuu
[State -1]
type = ChangeState
value = 1650
triggerall = command = "hcf_y"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Light SenShippo
[State -1]
type = ChangeState
value = 1300
triggerall = command = "charge_x"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Hard SenShippo
[State -1]
type = ChangeState
value = 1330
triggerall = command = "charge_y"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Light Senkyuutai
[State -1]
type = ChangeState
value = 1400
triggerall = command = "qcf_a"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Hard Senkyuutai
[State -1]
type = ChangeState
value = 1425
triggerall = command = "qcf_b"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Light Ryu renda
[State -1]
type = ChangeState
value = 1500
triggerall = command = "dp_x"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Hard Ryu renda
[State -1]
type = ChangeState
value = 1525
triggerall = command = "dp_y"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Hard Ryu renda extra hits
[State -1]
type = VarAdd
v = 1
value = 1
trigger1 = stateno = 1525 && command = "y"

; Roll forward
[State -1]
type = ChangeState
value = 750
trigger1 = command = "dodge" ^^ command = "z"
trigger1 = command = "holdfwd" && statetype = S && ctrl

; Roll backwards
[State -1]
type = ChangeState
value = 775
trigger1 = command = "dodge" ^^ command = "z"
trigger1 = command = "holdback" && statetype = S && ctrl

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
trigger1 = statetype = S && ctrl && (command = "knockdown" || command = "c")

; Ko bokute
[State -1]
type = ChangeState
value = 215
triggerall = command = "fwd_x"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Standing light punch
[State -1]
type = ChangeState
value = 200
triggerall = command = "x" && command != "holddown"
trigger1 = statetype = S && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger5 = stateno = 420 && AnimElem = 3, >= 0 && AnimElem = 4, < 0

; Gosentai
[State -1]
type = ChangeState
value = 225
triggerall = command = "fwd_a"
trigger1 = statetype != A && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 240 && AnimElem = 9, >= 0 && AnimElem = 10, < 0
trigger5 = stateno = 250 && AnimElem = 5, >= 0 && AnimElem = 7, < 0
trigger6 = stateno = 270 && AnimElem = 4, >= 0 && AnimElem = 7, < 0
trigger7 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger8 = stateno = 440 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger9 = stateno = 460 && AnimElem = 3, >= 0 && AnimElem = 5, < 0

; Standing light kick (close)
[State -1]
type = ChangeState
value = 230
triggerall = command = "a"  && command != "holddown" && P2bodydist X <= 15
trigger1 = statetype = S && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger5 = stateno = 420 && AnimElem = 3, >= 0 && AnimElem = 4, < 0

; Standing light kick
[State -1]
type = ChangeState
value = 220
triggerall = command = "a" && command != "holddown"
trigger1 = statetype = S && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger5 = stateno = 420 && AnimElem = 3, >= 0 && AnimElem = 4, < 0

[State -1]
type = ChangeState
value = 800
trigger1 = command = "holdfwd" && command = "y" && statetype = S && stateno != 100 && P2bodydist X <= 10 && P2movetype != H && ctrl

; Standing hard punch (close)
[State -1]
type = ChangeState
value = 250
trigger1 = command = "y" && statetype = S && P2bodydist X <= 15 && command != "holddown" && ctrl

; Standing hard punch
[State -1]
type = ChangeState
value = 240
trigger1 = command = "y" && statetype = S && command != "holddown" && ctrl

[State -1]
type = ChangeState
value = 850
trigger1 = command = "holdfwd" && command = "b" && statetype = S && stateno != 100 && P2bodydist X <= 10 && P2movetype != H && ctrl

; Standing hard kick (close)
[State -1]
type = ChangeState
value = 270
trigger1 = command = "b" && statetype = S && P2bodydist X <= 15 && command != "holddown" && ctrl

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
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger5 = stateno = 420 && AnimElem = 3, >= 0 && AnimElem = 4, < 0

; Crouching light kick
[State -1]
type = ChangeState
value = 420
triggerall = command = "a"
trigger1 = statetype = C && ctrl
trigger2 = stateno = 200 && AnimElem = 3, >= 0 && AnimElem = 4, < 0
trigger3 = stateno = 230 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger4 = stateno = 400 && AnimElem = 2, >= 0 && AnimElem = 3, < 0
trigger5 = stateno = 420 && AnimElem = 3, >= 0 && AnimElem = 4, < 0

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
trigger1 = stateno != 950
trigger1 = command = "a" && statetype = A && Vel X = 0 && ctrl

; Diagonal jumping light kick
[State -1]
type = ChangeState
value = 630
trigger1 = command = "a" && statetype = A && ctrl

; Jumping hard punch
[State -1]
type = ChangeState
value = 640
trigger1 = command = "y" && statetype = A && ctrl

; Jumping hard kick
[State -1]
type = ChangeState
value = 660
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
value = 199
trigger1 = command = "s" && statetype = S && stateno != 199 && ctrl

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