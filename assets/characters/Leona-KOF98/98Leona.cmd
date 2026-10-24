;--------------------------------------------------------------------------
;-| AI Motions |-----------------------------------------------------------
;--------------------------------------------------------------------------
[command]
name = "AI1"
command = B,D,a+c,z,c+b,s
time = 1
[command]
name = "AI2"
command = B,F,c+b,z,c+z,x,s
time = 1
[command]
name = "AI3"
command = B,U,a+b,y,c+y,s,z,D
time = 1
[command]
name = "AI4"
command = B,B,a+y,c,z+x,s
time = 1
[command]
name = "AI5"
command = B,B,a+b,z,c+b,s
time = 1
[command]
name = "AI6"
command = D,B,z+b,z,c+x,s
time = 1
[command]
name = "AI7"
command = B,U,a+b,z,c+x,s
time = 1
[command]
name = "AI8"
command = B,F,a+b,c,c+x,s
time = 1
[Command]
name = "AI9"
command = U,D,F,F,B,B,s
time = 1
[Command]
name = "AI10"
command = U,D,F,F,B,F,s
time = 1
[Command]
name = "AI11"
command = U,D,F,F,B,D,s
time = 1
[Command]
name = "AI12"
command = U,D,F,F,B,U,s
time = 1
[Command]
name = "AI13"
command = U,D,F,F,U,B,s
time = 1
[Command]
name = "AI14"
command = U,D,F,F,D,B,s
time = 1
[Command]
name = "AI15"
command = U,D,F,F,F,B,s
time = 1
[Command]
name = "AI16"
command = U,D,U,F,B,B,s
time = 1
[Command]
name = "AI17"
command = U,D,D,F,B,B,s
time = 1
[Command]
name = "AI18"
command = D,D,F,F,B,B,s
time = 1
[Command]
name = "AI19"
command = U,U,F,F,B,B,s
time = 1
[Command]
name = "AI20"
command = U,B,F,F,B,B,s
time = 1
[Command]
name = "AI21"
command = UB, U, F, a+b,s
time = 1
[Command]
name = "AI22"
command = UB, U, F, b+c,s
time = 1
[Command]
name = "AI23"
command = UB, U, F, a+c,s
time = 1
[Command]
name = "AI24"
command = UF, U, B, x+y,s
time = 1
[Command]
name = "AI25"
command = UF, U, B, y+z,s
time = 1
[Command]
name = "AI26"
command = UF, U, B, x+z,s
time = 1
[Command]
name = "AI27"
command = UB, U, F, x+y,s
time = 1
[Command]
name = "AI28"
command = UB, U, F, y+z,s
time = 1
[Command]
name = "AI29"
command = UB, U, F, x+z,s
time = 1
[Command]
name = "AI30"
command = UF, U, B, a+b,s
time = 1
[Command]
name = "AI31"
command = UF, U, B, b+c,s
time = 1
[Command]
name = "AI32"
command = UF, U, B, a+c,s
time = 1
[Command]
name = "AI33"
command = UF, DB, UB,DF ,x,s
time = 1
[Command]
name = "AI34"
command = UF, DB, UB,DF ,y,s
time = 1
[Command]
name = "AI35"
command = UF, DB, UB,DF , z,s
time = 1

;--------------------------------------------------------------------------
;-| Super Motions |--------------------------------------------------------
;--------------------------------------------------------------------------
; Grateful Dead
[Command]
name = "Grateful"
command = ~D, DF, F, D, DF, F, x
time = 25

[Command]
name = "Grateful"
command = ~D, DF, F, D, DF, F, y
time = 25

; Gravity Storm
[Command]
name = "Storm"
command = ~D, DF, F, D, DF, F, a
time = 25

[Command]
name = "Storm"
command = ~D, DF, F, D, DF, F, b
time = 25

; Rebel Spark
[Command]
name = "Rebel"
command = ~D, DB, B, DB, D, DF, F, a
time = 25

[Command]
name = "Rebel"
command = ~D, DB, B, DB, D, DF, F, b
time = 25

; V-Slaher
[Command]
name = "V_1"
command = ~D, DF, F, DF, D, DB, B, x
time = 25

[Command]
name = "V_2"
command = ~D, DF, F, DF, D, DB, B, y
time = 25

;--------------------------------------------------------------------------
;-| Special Motions |------------------------------------------------------
;--------------------------------------------------------------------------
; Earring Bomb
[Command]
name = "Bomb1"
command = ~F, DF, D, DB, B, a
time = 20
[Command]
name = "Bomb2"
command = ~F, DF, D, DB, B, b
time = 20

; Ice Slasher
[Command]
name = "Slasher1"
command = ~F, DF, D, DB, B, x
time = 20
[Command]
name = "Slasher2"
command = ~F, DF, D, DB, B, y
time = 20

; Baltic Launcher
[Command]
name = "Baltic1"
command = ~30$B,F, x
time = 20
[Command]
name = "Baltic2"
command = ~30$B,F, y
time = 20

; X-Caliber
[Command]
name = "Caliber1"
command = ~D, DB, B, x
time = 20
[Command]
name = "Caliber2"
command = ~D, DB, B, y
time = 20

; Ground Saber
[Command]
name = "Saber1"
command = ~30$B,F, a
time = 20
[Command]
name = "Saber2"
command = ~30$B,F, b
time = 20

; Moon Slasher (Both)
[Command]
name = "Moon1"
command = ~30$D, U, x
time = 20
[Command]
name = "Moon1"
command = ~30$D, $U, x
time = 20
[Command]
name = "Moon1"
command = ~30$D, $U, ~x
time = 20
[Command]
name = "Moon2"
command = ~30$D, U, y
time = 20
[Command]
name = "Moon2"
command = ~30$D, $U, y
time = 20
[Command]
name = "Moon2"
command = ~30$D, $U, ~y
time = 20

;--------------------------------------------------------------------------
;-| Double Tap |-----------------------------------------------------------
;--------------------------------------------------------------------------

[Command]
name = "FF"
command = F, F
time = 10

[Command]
name = "BB"
command = B, B
time = 10

;--------------------------------------------------------------------------
;-| 2/3 Button Combination |-----------------------------------------------
;--------------------------------------------------------------------------

[Command]
name = "recovery"
command = x+a
time = 1

[Command]
name = "cd"
command = b+y
time = 1

[Command]
name = "ab"
command = a+x
time = 1

;--------------------------------------------------------------------------
;-| Dir + Button |---------------------------------------------------------
;--------------------------------------------------------------------------

[Command]
name = "down_a"
command = /$D,a
time = 1

[Command]
name = "down_b"
command = /$D,b
time = 1

;--------------------------------------------------------------------------
;-| Single Button |--------------------------------------------------------
;--------------------------------------------------------------------------

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
name = "hold_a"
command = /$a
time = 1

[Command]
name = "hold_b"
command = /$b
time = 1

[Command]
name = "hold_c"
command = /$c
time = 1

[Command]
name = "hold_x"
command = /$x
time = 1

[Command]
name = "hold_y"
command = /$y
time = 1

[Command]
name = "hold_z"
command = /$z
time = 1

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
name = "start"
command = s
time = 1

;--------------------------------------------------------------------------
;-| Hold Dir |-------------------------------------------------------------
;--------------------------------------------------------------------------

[Command]
name = "holdfwd";Required (do not remove)
command = /$F
time = 1

[Command]
name = "holdback";Required (do not remove)
command = /$B
time = 1

[Command]
name = "holdup" ;Required (do not remove)
command = /$U
time = 1

[Command]
name = "holddown";Required (do not remove)
command = /$D
time = 1

[Command]
name = "holddownfwd";Required (do not remove)
command = /$DF
time = 1

[Command]
name = "jump"
command = ~D, $U
time = 11

;--------------------------------------------------------------------------
;--------------------------------------------------------------------------
[Statedef -1]
;--------------------------------------------------------------------------
;--------------------------------------------------------------------------
;==========================================================================
; ADVANCE / EXTRA Motions
;==========================================================================
; ADVANCE
[State -1]
type = ChangeState
value = 790
triggerall = var(9) = 0
trigger1 = command = "a" && command = "y"
trigger1 = power >= 1000 && statetype = S && ctrl = 1 && var(7) <= 0

; EXTRA
[State -1]
type = changestate
value = 910
triggerall = var(9) = 0
triggerall = statetype = S
triggerall = Power < 3000
triggerall = ctrl = 1
trigger1 = command = "hold_x"
trigger1 = command = "hold_b"

;==========================================================================
; DMs/SDMs Attacks
;==========================================================================
; Grateful Dead
[State -1]
type = ChangeState
value = 3300 + ((var(7) > 0) * 50)
triggerall = var(9) = 0
triggerall = var(50) = 1
triggerall = statetype != A && power >= 1000
triggerall = command = "Grateful"
trigger1 = ctrl = 1
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Gravity Storm
[State -1]
type = ChangeState
value = 3200 + ((var(7) > 0) * 50)
triggerall = var(9) = 0
triggerall = statetype != A && power >= 1000
triggerall = command = "Storm"
trigger1 = ctrl = 1
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Rebel Spark
[State -1]
type = ChangeState
value = 3100 + ((var(7) > 0) * 50)
triggerall = var(9) = 0
triggerall = var(50) = 0
triggerall = statetype != A && power >= 1000
triggerall = command = "Rebel"
trigger1 = ctrl = 1
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; V-Slasher (W)
[State -1]
type = ChangeState
value = 3000 + ((var(7) > 0) * 50)
triggerall = var(9) = 0
triggerall = statetype = A
triggerall = power >= 1000 && command = "V_1"
trigger1 = ctrl = 1
trigger2 = stateno = 305 && MoveContact
trigger3 = stateno = 600 && MoveContact
trigger4 = stateno = 605 && MoveContact
trigger5 = stateno = 610 && MoveContact
trigger6 = stateno = 615 && MoveContact
trigger7 = stateno = 620 && MoveContact
trigger8 = stateno = 625 && MoveContact
trigger9 = stateno = 630 && MoveContact
trigger10 = stateno = 635 && MoveContact

; V-Slasher (S)
[State -1]
type = ChangeState
value = 3001 + ((var(7) > 0) * 49)
triggerall = var(9) = 0
triggerall = statetype = A
triggerall = power >= 1000 && command = "V_2"
trigger1 = ctrl = 1
trigger2 = stateno = 305 && MoveContact
trigger3 = stateno = 600 && MoveContact
trigger4 = stateno = 605 && MoveContact
trigger5 = stateno = 610 && MoveContact
trigger6 = stateno = 615 && MoveContact
trigger7 = stateno = 620 && MoveContact
trigger8 = stateno = 625 && MoveContact
trigger9 = stateno = 630 && MoveContact
trigger10 = stateno = 635 && MoveContact

;==========================================================================
; TECNICAS DE COMBATE
;==========================================================================
; Earring Bomb (W)
[State -1,]
type = ChangeState
value = 1500
triggerall = var(9) = 0
triggerall = var(50) = 0
triggerall = command = "Bomb1" && NumProj = 0
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Earring Bomb (S)
[State -1,]
type = ChangeState
value = 1510
triggerall = var(9) = 0
triggerall = var(50) = 0
triggerall = command = "Bomb2" && NumProj = 0
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Ice Slasher (W, Riot)
[State -1]
type = ChangeState
value = 1410
triggerall = var(9) = 0
triggerall = var(50) = 1
triggerall = command = "Slasher1"
trigger1 = statetype != A
trigger1 = Ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Ice Slasher (S, Riot)
[State -1]
type = ChangeState
value = 1411
triggerall = var(9) = 0
triggerall = var(50) = 1
triggerall = command = "Slasher2"
trigger1 = statetype != A
trigger1 = Ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Ice Slasher (W, Normal)
[State -1]
type = ChangeState
value = 1400
triggerall = var(9) = 0
triggerall = var(50) = 0
triggerall = command = "Slasher1"
trigger1 = statetype != A
trigger1 = Ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Ice Slasher (S, Normal)
[State -1]
type = ChangeState
value = 1401
triggerall = var(9) = 0
triggerall = var(50) = 0
triggerall = command = "Slasher2"
trigger1 = statetype != A
trigger1 = Ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Baltic Launcher (W)
[State -1,]
type = ChangeState
value = 1300
triggerall = var(9) = 0
triggerall = command = "Baltic1"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Baltic Launcher (S)
[State -1,]
type = ChangeState
value = 1305
triggerall = var(9) = 0
triggerall = command = "Baltic2"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; X-Caliber (WP)
[State -1]
type = ChangeState
value = 1200
triggerall = var(9) = 0
triggerall = command = "Caliber1"
trigger1 = statetype = A
trigger1 = ctrl
trigger2 = stateno = 305 && MoveContact
trigger3 = stateno = 600 && MoveContact
trigger4 = stateno = 605 && MoveContact
trigger5 = stateno = 610 && MoveContact
trigger6 = stateno = 615 && MoveContact
trigger7 = stateno = 620 && MoveContact
trigger8 = stateno = 625 && MoveContact
trigger9 = stateno = 630 && MoveContact
trigger10 = stateno = 635 && MoveContact

; X-Caliber (SP)
[State -1]
type = ChangeState
value = 1201
triggerall = var(9) = 0
triggerall = command = "Caliber2"
trigger1 = statetype = A
trigger1 = ctrl
trigger2 = stateno = 305 && MoveContact
trigger3 = stateno = 600 && MoveContact
trigger4 = stateno = 605 && MoveContact
trigger5 = stateno = 610 && MoveContact
trigger6 = stateno = 615 && MoveContact
trigger7 = stateno = 620 && MoveContact
trigger8 = stateno = 625 && MoveContact
trigger9 = stateno = 630 && MoveContact
trigger10 = stateno = 635 && MoveContact

; Ground Saber (WK)
[State -1,]
type = ChangeState
value = 1100
triggerall = var(9) = 0
triggerall = command = "Saber1"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Ground Saber (SK)
[State -1,]
type = ChangeState
value = 1101
triggerall = var(9) = 0
triggerall = command = "Saber2"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 320 && MoveContact
trigger8 = stateno = 400 && MoveContact
trigger9 = stateno = 410 && MoveContact
trigger10 = stateno = 420 && MoveContact

; Moon Slasher (WP)
[State -1,]
type = ChangeState
value = 1000
triggerall = var(9) = 0
triggerall = command = "Moon1"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 52 || stateno = 40
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 200 && MoveContact
trigger4 = stateno = 205 && MoveContact
trigger5 = stateno = 215 && MoveContact
trigger6 = stateno = 225 && time = [7,10]
trigger7 = stateno = 235 && time = [13,15]
trigger8 = stateno = 320 && MoveContact
trigger9 = stateno = 400 && MoveContact
trigger10 = stateno = 410 && MoveContact
trigger11 = stateno = 420 && MoveContact

; Moon Slasher (SP)
[State -1,]
type = ChangeState
value = 1001
triggerall = var(9) = 0
triggerall = command = "Moon2"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 52 || stateno = 40
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 200 && MoveContact
trigger4 = stateno = 205 && MoveContact
trigger5 = stateno = 215 && MoveContact
trigger6 = stateno = 225 && time = [7,10]
trigger7 = stateno = 235 && time = [13,15]
trigger8 = stateno = 320 && MoveContact
trigger9 = stateno = 400 && MoveContact
trigger10 = stateno = 410 && MoveContact
trigger11 = stateno = 420 && MoveContact

;==========================================================================
; Pasos dobles
;==========================================================================
; Adelante
[State -1, Run Fwd]
type = ChangeState
value = 100
triggerall = var(9) = 0
trigger1 = command = "FF"
trigger1 = statetype = S
trigger1 = ctrl

; Atras
[State -1, Run Back]
type = ChangeState
value = 105
triggerall = var(9) = 0
trigger1 = command = "BB"
trigger1 = statetype = S
trigger1 = ctrl

;==========================================================================
; GRAPPLE ATTACKS
;==========================================================================
; Normal 1
[State -1]
type = ChangeState
value = 800
triggerall = var(9) = 0
triggerall = command = "y"
triggerall = command = "holdfwd"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = stateno != 100
trigger1 = p2bodydist x < 20
trigger1 = p2statetype != A
trigger1 = p2movetype != H
trigger1 = p2stateno != 5120
trigger1 = ctrl

; Normal 2
[State -1]
type = ChangeState
value = 850
triggerall = var(9) = 0
triggerall = command = "b"
triggerall = command = "holdfwd"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = stateno != 100
trigger1 = p2bodydist x < 20
trigger1 = p2statetype != A
trigger1 = p2movetype != H
trigger1 = p2stateno != 5120
trigger1 = ctrl

; Aereo
[State -1]
type = ChangeState
value = 880
triggerall = var(9) = 0
triggerall = command = "y"
triggerall = command = "holdfwd"
trigger1 = statetype = A
trigger1 = stateno != 100
trigger1 = p2bodydist x < 20
trigger1 = p2statetype = A
trigger1 = p2movetype != H
trigger1 = p2stateno != 5120
trigger1 = ctrl

;==========================================================================
; EVASIONES Y OTROS
;==========================================================================
; TIME BAR Escape Roll backward
[State -1]
type = ChangeState
value = 365
triggerall = var(9) = 0
trigger1 = command = "ab" && command = "holdback" && var(7) > 0 && stateno = [150,151]
; TIME BAR Escape Roll Forward
[State -1]
type = ChangeState
value = 355
triggerall = var(9) = 0
trigger1 = command = "ab" && var(7) > 0 && stateno = [150,151]

;Roll Backward
[State -1]
type = ChangeState
value = 360
triggerall = var(9) = 0
trigger1 = command = "ab" && command = "holdback" && statetype = S && ctrl = 1

;Roll Forward
[State -1]
type = ChangeState
value = 350
triggerall = var(9) = 0
trigger1 = command = "ab" && command = "holdfwd" && statetype = S && ctrl = 1

; Dodge
[State -1]
type = ChangeState
value = 310
triggerall = var(9) = 0
triggerall = command = "ab"
trigger1 = statetype = S
trigger1 = ctrl

; Dodge Ret
[State -1]
type = ChangeState
value = 320
triggerall = var(9) = 0
triggerall = stateno = 310
triggerall = AnimElem = 3, >= 0
trigger1 = command = "a"
trigger2 = command = "b"
trigger3 = command = "x"
trigger4 = command = "y"

;==========================================================================
; CD Attacks
;==========================================================================
; Standing
[State -1]
type = ChangeState
value = 240
triggerall = var(9) = 0
triggerall = command = "cd"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 101

; Jumping
[State -1]
type = ChangeState
value = 640
triggerall = var(9) = 0
triggerall = command = "cd"
trigger1 = statetype = A
trigger1 = ctrl

; Counter
[State -1]
type = ChangeState
value = 250
triggerall = var(9) = 0
trigger1 = command = "cd" && var(7) > 0 && stateno = [150,151]

;==========================================================================
; Dir + Button
;==========================================================================
; F + WK (normal)
[State -1, N]
type = ChangeState
value = 300
triggerall = var(9) = 0
triggerall = var(50) = 0
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = command = "holdfwd"
trigger1 = statetype = S 
trigger1 = ctrl

; F + WK (juggle)
[State -1, J]
type = ChangeState
value = 305
triggerall = var(9) = 0
triggerall = var(50) = 0
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = command = "holdfwd"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 200 && MoveContact
trigger3 = stateno = 205 && MoveContact
trigger4 = stateno = 215 && MoveContact
trigger5 = stateno = 225 && time = [7,10]
trigger6 = stateno = 235 && time = [13,15]
trigger7 = stateno = 400 && MoveContact
trigger8 = stateno = 410 && MoveContact
trigger9 = stateno = 420 && MoveContact

;==========================================================================
; standing Attacks (normales)
;==========================================================================
; WP
[State -1,]
type = ChangeState
value = 200
triggerall = var(9) = 0
triggerall = command = "x"
triggerall = command != "holddown"
triggerall = p2bodydist x > 19
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 101
trigger4 = stateno = 400 && MoveContact

; WK
[State -1]
type = ChangeState
value = 210
triggerall = var(9) = 0
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = command != "holdfwd"
triggerall = p2bodydist x > 19
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 101

; SP
[State -1]
type = ChangeState
value = 220
triggerall = var(9) = 0
triggerall = command = "y"
triggerall = command != "holddown"
triggerall = p2bodydist x > 19
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 101

; SK
[State -1]
type = ChangeState
value = 230
triggerall = var(9) = 0
triggerall = command = "b"
triggerall = command != "holddown"
triggerall = p2bodydist x > 19
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 101

;==========================================================================
; Close Attacks
;==========================================================================
; WP
[State -1]
type = ChangeState
value = 205
triggerall = var(9) = 0
triggerall = command = "x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 101
trigger4 = stateno = 400 && time = [5,11]

; WK
[State -1]
type = ChangeState
value = 215
triggerall = var(9) = 0
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = command != "holdfwd"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 101

;SP
[State -1]
type = ChangeState
value = 225
triggerall = var(9) = 0
triggerall = command = "y"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 101

; SK
[State -1]
type = ChangeState
value = 235
triggerall = var(9) = 0
triggerall = command = "b"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52
trigger2 = animelem = 1, >= 1
trigger3 = stateno = 101

;==========================================================================
; Ataques agachado
;==========================================================================
; WP
[State -1]
type = ChangeState
value = 400
triggerall = var(9) = 0
triggerall = command = "x"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 101
trigger3 = stateno = 400 && MoveContact

; WK
[State -1]
type = ChangeState
value = 410
triggerall = var(9) = 0
triggerall = command = "a"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 101
trigger3 = stateno = 215 && MoveContact
trigger4 = stateno = 410 && MoveContact

; SP
[State -1]
type = ChangeState
value = 420
triggerall = var(9) = 0
triggerall = command = "y"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 101

; SK
[State -1]
type = ChangeState
value = 430
triggerall = var(9) = 0
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 101

;==========================================================================
; Ataques aereos
;==========================================================================
; WP
[State -1]
type = ChangeState
value = 600
triggerall = var(9) = 0
triggerall = command = "x"
triggerall = vel x = 0
trigger1 = statetype = A
trigger1 = ctrl
; WP dir
[State -1]
type = ChangeState
value = 605
triggerall = var(9) = 0
triggerall = command = "x"
trigger1 = statetype = A
trigger1 = ctrl

; WK
[State -1]
type = ChangeState
value = 610
triggerall = var(9) = 0
triggerall = command = "a"
triggerall = vel x = 0
trigger1 = statetype = A
trigger1 = ctrl
; WK Dir
[State -1]
type = ChangeState
value = 615
triggerall = var(9) = 0
triggerall = command = "a"
trigger1 = statetype = A
trigger1 = ctrl

; SP
[State -1]
type = ChangeState
value = 620
triggerall = var(9) = 0
triggerall = command = "y"
triggerall = vel x = 0
trigger1 = statetype = A
trigger1 = ctrl
; SP dir
[State -1]
type = ChangeState
value = 625
triggerall = var(9) = 0
triggerall = command = "y"
trigger1 = statetype = A
trigger1 = ctrl

; SK
[State -1]
type = ChangeState
value = 630
triggerall = var(9) = 0
triggerall = command = "b"
triggerall = vel x = 0
trigger1 = statetype = A
trigger1 = ctrl
; SK dir
[State -1]
type = ChangeState
value = 635
triggerall = var(9) = 0
triggerall = command = "b"
trigger1 = statetype = A
trigger1 = ctrl

;==========================================================================
; Burla
;==========================================================================
[State -1]
type = ChangeState
value = 195
triggerall = var(9) = 0
trigger1 = command = "start"
trigger1 = Vel X = 0
trigger1 = stateno != 195
trigger1 = statetype = S
trigger1 = ctrl = 1
;---------------------------------------------------------------------------
;===========================================================================
;---------------------------- A I   M O T I O N S --------------------------
;===========================================================================
;---------------------------------------------------------------------------
[State -1, AI CMD]
type = VarSet
triggerall = alive
triggerall = stateno < 5500
trigger1 = command = "AI1"
trigger2 = command = "AI2"
trigger3 = command = "AI3"
trigger4 = command = "AI4"
trigger5 = command = "AI5"
trigger6 = command = "AI6"
trigger7 = command = "AI7"
trigger8 = command = "AI8"
trigger9 = command = "AI9"
trigger10 = command = "AI10"
trigger11 = command = "AI11"
trigger12 = command = "AI12"
trigger13 = command = "AI13"
trigger14 = command = "AI14"
trigger15 = command = "AI15"
trigger16 = command = "AI16"
trigger17 = command = "AI17"
trigger18 = command = "AI18"
trigger19 = command = "AI19"
trigger20 = command = "AI20"
trigger21 = command = "AI21"
trigger22 = command = "AI22"
trigger23 = command = "AI23"
trigger24 = command = "AI24"
trigger25 = command = "AI25"
trigger26 = command = "AI26"
trigger27 = command = "AI27"
trigger28 = command = "AI28"
trigger29 = command = "AI29"
trigger30 = command = "AI30"
trigger31 = command = "AI31"
trigger32 = command = "AI32"
trigger33 = command = "AI33"
trigger34 = command = "AI34"
trigger35 = command = "AI35"
v = 9
value = 1
ignorehitpause = 1
persistent = 1

[State -1, OFF]
type = VarSet
trigger1 = roundstate>2
trigger2 = !alive
trigger3 = stateno = 5500
v = 9
value = 0
ignorehitpause = 1
persistent = 1

;---------------------------------------------------------------------------
; Combos
;----------
[State AI, Close WK]
type = ChangeState
value = 215
triggerall = var(9) != 0
triggerall = p2stateno != [5050,5121]
triggerall = p2statetype != A
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [0,39]
triggerall = p2movetype != A
triggerall = statetype = S
trigger1 = ctrl

[State AI, WK Crouch]
type = ChangeState
value = 410
triggerall = var(9) != 0
triggerall = p2statetype != A
triggerall = movecontact
triggerall = random <= 999
trigger1 = stateno = 215

[State AI, F+WK]
type = ChangeState
value = 305
triggerall = var(9) != 0
triggerall = var(50) = 0
triggerall = power >= 2000
triggerall = p2statetype != A
triggerall = movecontact
triggerall = random <= 999
trigger1 = stateno = 410

[State AI, V-Slasher]
type = ChangeState
value = 3001 + ((var(7) > 0) * 49)
triggerall = var(9) != 0
triggerall = p2statetype != A
triggerall = power >= 1000
triggerall = movehit
triggerall = random <= 999
trigger1 = stateno = 305

[State AI, DM / SDM Gravity Storm]
type = ChangeState
value = 3200 + ((var(7) > 0) * 50)
triggerall = var(9) != 0
triggerall = var(50) = 1
triggerall = random <= 750
triggerall = power >= 1000
triggerall = p2statetype != A
triggerall = MoveHit
triggerall = random <= 999
trigger1 = stateno = 410

[State AI, Moon]
type = ChangeState
value = 1000
triggerall = var(9) != 0
triggerall = p2statetype != A
triggerall = movecontact
triggerall = random <= 999
trigger1 = stateno = 410

;--------------------------------------------
; DMs
;-----
[State AI, Grateful]
type = ChangeState
value = 3300 + ((var(7) > 0) * 50)
triggerall = var(50) = 1
triggerall = var(9) != 0
triggerall = power >= 1000
triggerall = RoundState = 2
triggerall = (p2stateno != [5020,5050])
triggerall = p2stateno != [154,155]
triggerall = random <= 400
triggerall = p2bodydist x = [50,200]
trigger1 = ctrl && enemynear,NumProj && statetype != A

[State AI, Rebel Spark]
type = ChangeState
value = 3100 + ((var(7) > 0) * 50)
triggerall = var(50) = 0
triggerall = var(9) != 0
triggerall = random <= 750
triggerall = power >= 1000
triggerall = p2statetype != A
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [0,80]
triggerall = p2movetype = A
triggerall = statetype = S
trigger1 = ctrl

[State AI, Rebel Spark]
type = ChangeState
value = 3100 + ((var(7) > 0) * 50)
triggerall = var(50) = 0
triggerall = var(9) != 0
triggerall = random <= 750
triggerall = power >= 1000
triggerall = p2statetype = A
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [0,50]
triggerall = statetype = S
trigger1 = ctrl

;--------------------------------------------
; Motions
;---------
[State AI, Ice Slasher]
type = ChangeState
value = 1400 + ((var(50) > 0) * 10)
triggerall = var(9) != 0
triggerall = random <= 200
triggerall = p2statetype != A
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2stateno != [400,499]
triggerall = p2bodydist x = [100,180]
triggerall = p2movetype = A
triggerall = statetype = S
trigger1 = ctrl

[State AI, Moon Slasher]
type = ChangeState
value = 1000
triggerall = var(9) != 0
triggerall = random <= 200
triggerall = p2statetype = A
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [0,80]
triggerall = p2movetype = A
triggerall = statetype = S
trigger1 = ctrl

[State AI, Baltic Launcher]
type = ChangeState
value = 1300
triggerall = var(9) != 0
triggerall = random <= 200
triggerall = p2statetype != A
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [30,50]
triggerall = p2stateno = [400,499]
triggerall = p2movetype = A
triggerall = statetype = S
trigger1 = ctrl

[State AI, Earring Bomb]
type = ChangeState
value = 1500
triggerall = var(50) = 0
triggerall = var(9) != 0
triggerall = random <= 300
triggerall = p2stateno != [5050,5121]
triggerall = roundstate = 2
triggerall = p2statetype != A
triggerall = ctrl && statetype != A
triggerall = statetype = S
triggerall = p2bodydist x = [150,180]
trigger1 = ctrl

[State AI, S Gound Saber]
type = ChangeState
value = 1101
triggerall = var(9) != 0
triggerall = random <= 75
triggerall = p2stateno != [5050,5121]
triggerall = roundstate = 2
triggerall = p2statetype != A
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [70,150]
triggerall = statetype = S
trigger1 = ctrl

[State AI, ADVANCE activation]
type = ChangeState
value = 790
triggerall = var(9) != 0
triggerall = var(7) = 0
triggerall = power >= 1000
triggerall = p2stateno = [5050,5121]
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [100,320]
triggerall = p2movetype = H
triggerall = statetype = S
trigger1 = ctrl

[State AI, Crouch SK]
type = ChangeState
value = 430
triggerall = var(9) != 0
triggerall = p2stateno != [5050,5121]
triggerall = p2statetype != A
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [40,70]
triggerall = p2movetype != A
triggerall = statetype = S
trigger1 = ctrl

[State -1, X-Caliber]
type = ChangeState
value = 1200
triggerall = var(9) != 0
triggerall = roundstate = 2
triggerall = random <= 70
triggerall = p2bodydist x = [100,150]
triggerall = statetype = A
trigger1 = ctrl

[State -1, SP V-Slasher]
type = ChangeState
value = 3001 + ((var(7) > 0) * 49)
triggerall = var(9) != 0
triggerall = random <= 50
triggerall = power >= 1000
triggerall = p2bodydist x = [100,200]
triggerall = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;Guardia & Extra Moves
[State AI, Guard]
type = ChangeState
value = 131
triggerall = var(9) != 0
triggerall = Roundstate = 2 && statetype != A && ctrl
trigger1 = random < 850
trigger1 = enemynear,statetype != A
trigger1 = enemynear, HitDefAttr = C,AA,AP && P2BodyDist X = [-30,80]
trigger1 = (EnemyNear,MoveType = A || p2movetype = A)
trigger2 = random < 900
trigger2 = enemynear,statetype != A && inguarddist

[State AI, Guard]
type = Changestate
value = 130
triggerall = var(9) != 0
triggerall = Roundstate = 2 && statetype != A && ctrl
trigger1 = random < 850
trigger1 = enemynear,statetype = A
trigger1 = enemynear, HitDefAttr = SA, AA, SA ,HA ,AP, SP, HP && P2BodyDist X = [-30,80]
trigger1 = (EnemyNear,MoveType = A || p2movetype = A)
trigger2 = random < 990
trigger2 = inGuardDist && Enemy, NumProj >= 1
trigger3 = random < 950
trigger3 = enemynear,statetype = A && inguarddist

[State AI, Random]
type = Varset
trigger1 = var(9) != 0 && stateno = 40 && time=1
sysvar(1) = ifelse(p2statetype=L, -1+((backedgedist <70)*2), 1-((random<50&!(p2dist X<50))*2)-((p2dist X<50)*1))

[State AI, Random]
type = VarSet
trigger1 = var(9) != 0 && stateno = 40 && time = 1
v = 4
value = ifelse(p2statetype=L||(enemy,numproj!=0), 0, ifelse(p2dist X<150, 1, 0))
ignorehitpause = 1
persistent = 1

[State AI, Random]
type = VarSet
trigger1 = var(9) != 0 && (stateno = 40) && time = 1 && random<300
v = 3
value = 3+((p2statetype=L)*1)
ignorehitpause = 1
persistent = 1

;[State AI]
;type = ChangeState
;triggerall = random <= 350
;trigger1 = var(9) != 0 && (stateno = 50 || (stateno = [120,140]) && pos Y < 0)
;trigger1 = vel Y > 0 && ifelse(p2statetype=C, p2dist Y<40, p2dist Y<60) || p2dist X < 50 && p2statetype = A || p2movetype = A && p2statetype != C
;value = 330

;[State AI]
;type = ChangeState
;trigger1 = var(9) != 0 && (stateno = 50 || (stateno = [120,140]) && pos Y < 0)
;trigger1 = vel Y > 0 && ifelse(p2statetype=C, p2dist Y<40, p2dist Y<60) || p2dist X < 50 && p2statetype = A || p2movetype = A && p2statetype != C
;value = ifelse(p2statetype=A||random<100, 645, ifelse(vel X = 0, 610+((random<500)*30), 610+((random<500)*35)))

[State AI, Run]
type = ChangeState
value = 102
triggerall = var(9) != 0
triggerall = var(50) = 0
triggerall = p2movetype != A
triggerall = p2bodydist x = [80,300]
triggerall = random <= 50
trigger1 = statetype != A
trigger1 = ctrl

[State AI, Rolling B]
type = ChangeState
value = 360
triggerall = var(9) != 0
triggerall = p2stateno = [5100,5121]
triggerall = random <= 100
triggerall = roundstate = 2
triggerall = ctrl && statetype != A
triggerall = p2bodydist x = [100,200]
triggerall = p2statetype != A
triggerall = statetype = S
trigger1 = ctrl

[State AI, Rolling F]
type = ChangeState
value = 350
triggerall = var(9) != 0
triggerall = p2statetype != L
triggerall = statetype != A
triggerall = InGuardDist = 1
triggerall = ctrl
triggerall = RoundState = 2
triggerall = random <= 790
triggerall = p2bodydist x = [70,300]
trigger1 = ctrl && enemynear,NumProj && statetype != A && random = [20,300]
trigger2 = inguarddist = [0,120]
trigger2 = ctrl && enemynear,NumProj && statetype != A

;---------------------------------------------------------------------------
;Run de AI
[Statedef 102]
type = S
movetype = I
physics = S
anim = 100
velset = 0
ctrl = 0

[State 100, 1]
type = VelSet
trigger1 = AnimElem = 3, >= 0
x = const(velocity.run.fwd.x)

[State 100, 5.1]
type = ChangeState
triggerall = var(9) = 0
trigger1 = AnimElem = 4, >= 0
trigger1 = command != "holdfwd"
value = 0
ctrl = 1

[State 100, 5.2]
type = ChangeState
triggerall = var(9) != 0
trigger1 = AnimElem = 4, >= 0
trigger1 = P2bodydist X <= 80
value = 0
ctrl = 1

;==========================================================================
;						   E N D   O F   F I L E .
;==========================================================================