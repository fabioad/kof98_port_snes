;#ADD004BASIC PIEs#
[Remap]
x = x
y = y
z = z
a = a
b = b
c = c
s = s

;-| hyper|-------------------------------------------------------
[Command]
name = "Psycho Ball Gravity"
command = ~D,F,B, c
time = 30

[Command]
name = "Psycho Ball Gravity"
command = ~D,F,B, x+y
time = 30

;------------------------------------------------------------------------------
;-| Super |--------------------------------------------------------------
[Command]
name = "superball_4"
command = ~D, F, D, F, x+y
time = 30

[Command]
name = "superball_4"
command = ~D, F, D, F, c
time = 30

;------------------------------------------------------------------------------
;-| Dobles |--------------------------------------------------------------
[command]
name = "super_explocion_b"
command = ~D,F,D,F,b
time = 30

[command]
name = "super_explocion_a"
command = ~D,F,D,F,a
time = 30

[command]
name = "Psycho Ball Attack Max"
command = ~D,F,D,F, x
time = 30

[command]
name = "Psycho Ball Attack Max"
command = ~D,F,D,F, y
time = 30

;-| Especiales |-----------------------------------------------------------------
[Command]
name = "Psycho Ball Air Front"
command = ~D, B, x
time = 20

[command]
name = "bolita_x"
command = ~D,F,x
time = 15

[Command]
name = "escudo_x"
command = ~D, B, b

[Command]
name = "escudo_x"
command = ~D, D, D

[Command]
name = "escudo_y"
command = ~D, B, a

[Command]
name = "bolarriba_x"
command = ~D, F, y

[Command]
name = "bolaire_3"
command = ~D, F, a

[Command]
name = "balla_1"
command = ~D, B, y

[Command]
name = "bolilla_1"
command = ~D, B, x

[Command]
name = "bolilla_2"
command = ~D, B, y

[Command]
name = "aita_1"
command = ~D, F, b

[Command]
name = "aita_2"
command = ~D, F, a

;------------------------------------------------------------------------------
;-| basicos |-------------------------------------------------------------------
 [Command]
name = "dlnt_x"
command = /F,x
time = 1

;------------------------------------------------------------------------------
;-| botons|---------------------------------------------------------
[Command]
name = "FF"
command = F, F
time = 10

[Command]
name = "BB"
command = B, B
time = 10

;------------------------------------------------------------------------------
;-| recovery |-----------------------------------------------------------------
[Command]
name = "recovery"
command = x+a
time = 1

[Command]
name = "recovery"
command = z
time = 1

[Command]
name = "ztg_n"
command = y+b
time = 1

[Command]
name = "ztg_n"
command = c
time = 1

[Command]
name = "x+y"
command = x+y
time = 1

[Command]
name = "a+b"
command = a+b
time = 1

[Command]
name = "jump"
command = D, $U
time = 12

;------------------------------------------------------------------------------
;-| down |---------------------------------------------------------

[Command]
name = "down_a"
command = /$D,a
time = 1

[Command]
name = "down_b"
command = /$D,b
time = 1

;------------------------------------------------------------------------------
;-| comandos botones|---------------------------------------------------------------
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

;------------------------------------------------------------------------------
;-| direciones |-----------------------------------------------------
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

[Command]
name = "holdxy"
command = /$x+y
time = 1

[Command]
name = "holdc"
command = /$c
time = 1

[Command]
name = "holdx"
command = /$x
time = 1

[Command]
name = "holdy"
command = /$y
time = 1

[Command]
name = "holda"
command = /$a
time = 1

[Command]
name = "cabezaso_x"
command = /$D,a
time = 1

[Command]
name = "patada_a"
command = /DF,a
time = 1

;==============================================================================
[Statedef -1]

;//==========================
;// add004-1-sctrls-start
;//==========================
;--- partner_standby
[state 0]
	type=selfstate
	trigger1=ctrl && numpartner && !ishelper && roundstate=2 && pos y=0
	trigger1=sysfvar(4)>0 && sysfvar(0)>0 && playeridexist(floor(sysfvar(0)))
	trigger1=playerid(floor(sysfvar(0))),var(0)=90900 && playerid(floor(sysfvar(0))),var(22)=4
	value=190190
	ctrl=0
	ignorehitpause=1
;//==========================
;// add004-1-sctrls-end
;//==========================



;------------------------------------------------------------------------------
[State -1, Combo condition Reset]
type = VarSet
trigger1 = 1
var(1) = 0

[State -1, Combo condition Check]
type = VarSet
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,299]) || (stateno = [400,499])
trigger2 = stateno = 340
trigger2 = stateno != 440 ;Except for sweep kick
trigger2 = movecontact
var(1) = 1

;------------------------------------------------------------------------------
;Hidden Move "Psycho Ball Gravity"
[State -1,Psycho Ball Gravity]
type = ChangeState
value = 3500
triggerall = command = "Psycho Ball Gravity"
triggerall = !Numhelper(3510)
triggerall = Power>= Ifelse(Life < Lifemax/2,2000,3000)
triggerall = statetype != A
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, super explocion ]
type = ChangeState
value = 950
triggerall = command = "super_explocion_a" || command = "super_explocion_b"
triggerall = power >= 1000
triggerall = statetype != A
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = hitdefattr = SC, NA, SA, HA
trigger2 = stateno !=900
trigger2 = stateno !=945 && movecontact
trigger2 = stateno !=1250
trigger2 = stateno !=1001 && movecontact
trigger2 = stateno !=3350
;Dream cancel con la super ball
;trigger3 = Stateno = 3000 && (Projcontacttime(3000) < 20 || NumprojID(3000)) && !Numprojid(3010)
Trigger16 = stateno = 1004 || stateno = 1900  && movecontact

[State -1, Psycho Ball Attack Max]
type = ChangeState
value = 3000
triggerall = Command = "Psycho Ball Attack Max"
triggerall = !Numproj
triggerall = Power >= 1000
triggerall = Statetype != A
trigger1 = Ctrl
trigger2 = hitdefattr = SC, NA, SA, HA
trigger2 = stateno !=900
trigger2 = stateno !=945 && movecontact
trigger2 = stateno !=1250
trigger2 = stateno !=1001 && movecontact
trigger2 = stateno !=3350

[State -1]
type = ChangeState
value = 3350
triggerall = command = "superball_4"
triggerall = !numproj && !NumHelper(3310)
triggerall = power >= 2000
triggerall = statetype = S
trigger1 = ctrl
trigger2 = stateno !=900
trigger2 = stateno !=945
trigger2 = stateno !=1001
trigger2 = stateno !=1250
trigger2 = stateno !=1450
trigger2 = stateno !=330
trigger2 = stateno !=600
trigger2 = stateno !=610
trigger2 = stateno !=630
trigger2 = stateno !=640
trigger2 = stateno !=645
trigger2 = stateno !=1003
trigger2 = stateno !=810
trigger2 = stateno !=830
Trigger16 = stateno = 1004 || stateno = 1900 || stateno = 950 && movecontact

;-------------------------------------------------------------------------------
;Psycho Ball Air Front
[State -1, Psycho Ball Air Front]
type = ChangeState
value = 1100
triggerall = command = "Psycho Ball Air Front"
triggerall = !Numproj
triggerall = statetype = A
trigger1 = Ctrl || Stateno = 106 ; Tine que ser 106 pero actualmente es 105 :S
trigger2 = stateno =[600,700)
trigger2 = Movetype = A && Movecontact

;bolita x
[State -1, bolita x]
type = ChangeState
value = 900
triggerall = command = "bolita_x"
triggerall = statetype != A
trigger1 = statetype = s
trigger1 = var(1) ;Use combo condition (above)
trigger2 = stateno !=900
trigger2 = stateno !=945
trigger2 = stateno !=950
trigger2 = stateno !=1900
trigger2 = stateno !=1001
trigger2 = stateno !=1004
trigger2 = stateno !=1250
trigger2 = movecontact

[State -1, bolita x]
type = ChangeState
value = 920
triggerall = command = "bolilla_1"
triggerall = anim != 1540
triggerall = statetype != A
trigger1 = statetype = s
trigger1 = var(1) ;Use combo condition (above)
trigger2 = stateno !=900
trigger2 = stateno !=920
trigger2 = stateno !=945
trigger2 = stateno !=950
trigger2 = stateno !=1900
trigger2 = stateno !=1001
trigger2 = stateno !=1004
trigger2 = stateno !=1250
trigger2 = movecontact

[State -1]
type = ChangeState
value = 1900
triggerall = command = "escudo_x"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno !=900
trigger2 = stateno !=945
trigger2 = stateno !=950
trigger2 = stateno !=1900
trigger2 = stateno !=1001
trigger2 = stateno !=1004
trigger2 = stateno !=1250
trigger2 = movecontact

[State -1]
type = ChangeState
value = 945
triggerall = command = "bolarriba_x"
triggerall = !numproj
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno !=900
trigger2 = stateno !=945
trigger2 = stateno !=950
trigger2 = stateno !=1900
trigger2 = stateno !=1001
trigger2 = stateno !=1250
trigger2 = movecontact

[State -1]
type = ChangeState
value = 1001
triggerall = command = "balla_1"
triggerall = !numproj
triggerall = statetype = A
trigger1 = ctrl
trigger2 = stateno !=900
trigger2 = stateno !=945
trigger2 = stateno !=950
trigger2 = stateno !=1900
trigger2 = stateno !=1001
trigger2 = stateno !=1250
trigger2 = stateno !=1004
trigger2 = stateno !=1450
trigger2 = stateno !=330
trigger2 = stateno !=600
trigger2 = stateno !=610
trigger2 = stateno !=630
trigger2 = stateno !=640
trigger2 = stateno !=645
trigger2 = stateno !=3100
trigger2 = stateno !=3500
trigger2 = movecontact

[State -1]
type = ChangeState
value = 1004
triggerall = command = "bolilla_2"
triggerall = !numproj
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno !=1004
trigger2 = stateno !=1250
trigger2 = stateno !=900
trigger2 = stateno !=945
trigger2 = stateno !=950
trigger2 = stateno !=1900
trigger2 = stateno !=1001
trigger2 = stateno !=3500
trigger2 = movecontact

[State -1]
type = ChangeState
value = 1250
triggerall = command = "aita_1" || command = "aita_2"
triggerall = !numproj
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno !=1004
trigger2 = stateno !=900
trigger2 = stateno !=950
trigger2 = stateno !=1900
trigger2 = stateno !=1250
trigger2 = stateno !=1001
trigger2 = stateno !=1450
trigger2 = stateno !=330
trigger2 = stateno !=600
trigger2 = stateno !=610
trigger2 = stateno !=630
trigger2 = stateno !=640
trigger2 = stateno !=645
trigger2 = movecontact

[State -1]
type = ChangeState
value = 1400
triggerall = command = "bolaire_3"
triggerall = !numproj
triggerall = statetype = A
trigger1 = ctrl

[State -1]
type = ChangeState
value = 1500
triggerall = command = "escudo_y"
triggerall = !numproj
triggerall = statetype != A
trigger1 = ctrl

[State -1]
type = ChangeState
value = 1450
triggerall = command = "aita_1" || command = "aita_2"
triggerall = !numproj
triggerall = statetype = A
trigger1 = ctrl
trigger2 = stateno !=1004
trigger2 = stateno !=900
trigger2 = stateno !=950
trigger2 = stateno !=1900
trigger2 = stateno !=1250
trigger2 = stateno !=1001
trigger2 = stateno !=1450
trigger2 = stateno !=330
trigger2 = stateno !=600
trigger2 = stateno !=610
trigger2 = stateno !=630
trigger2 = stateno !=640
trigger2 = stateno !=645
trigger2 = (stateno =300||stateno = 420) && movehit
trigger2 = movecontact

;---------------------------------------------------------------------------
[State -1, T S]
type = ChangeState
value = 710
triggerall = command = "recovery" && command = "holdback"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = power >= 1000
trigger2 = stateno = [150,151]

;---------------------------------------------------------------------------
[State -1, T S]
type = ChangeState
value = 700
triggerall = command = "recovery"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = power >= 1000
trigger2 = stateno = [150,151]
trigger3 = stateno = 100

;---------------------------------------------------------------------------
[State -1, UKEMI]
type = ChangeState
value = 52000
triggerall = command = "recovery"
triggerall = alive = 1
trigger1 = stateno = 5050
trigger1 = pos y > -30

;------------------------------------------------------------------------------
[State -1, Throw]
type = ChangeState
value = 300
triggerall = command = "ztg_n"
triggerall = statetype = S
triggerall = stateno != 100
trigger1 = ctrl
trigger2 = power >= 1000
trigger2 = stateno = [150,151]

;------------------------------------------------------------------------------
[State -1, CD]
type = ChangeState
value = 650
triggerall = command = "ztg_n"
triggerall = statetype = A
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, Throw]
type = ChangeState
value = 800
triggerall = command = "y"
triggerall = command = "holdfwd" || command = "holdback"
triggerall = statetype = S
triggerall = stateno != 100
trigger1 = p2bodydist X < 15
trigger1 = p2statetype != A && p2movetype != H
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, Throw]
type = ChangeState
value = 800
triggerall = command = "b"
triggerall = command = "holdfwd"
triggerall = statetype = S
triggerall = stateno != 100
trigger1 = p2bodydist X < 15
trigger1 = p2statetype != A && p2movetype != H
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, NARAKU]
type = ChangeState
value = 330
triggerall = command = "y"
triggerall = command = "holddown"
triggerall = statetype = A
trigger1 = ctrl
trigger2 = stateno = 105

;------------------------------------------------------------------------------
[State -1, 88]
type = ChangeState
value = 320
triggerall = command = "b"
triggerall = command = "holdfwd"
triggerall = command = "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 210 && movecontact
trigger4 = stateno = 215 && movecontact
trigger5 = stateno = 235 && movecontact
trigger6 = stateno = 245 && movecontact
trigger7 = stateno = 400 && movecontact
trigger8 = stateno = 410 && movecontact
trigger9 = stateno = 430 && movecontact
trigger10 = stateno = 440 && movecontact

;------------------------------------------------------------------------------
[State -1, GOUHU]
type = ChangeState
value = 310
triggerall = command = "a"
triggerall = command = "holdfwd"
triggerall = statetype = S
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 210 && movecontact
trigger4 = stateno = 215 && movecontact
trigger5 = stateno = 235 && movecontact
trigger6 = stateno = 245 && movecontact
trigger7 = stateno = 400 && movecontact
trigger8 = stateno = 410 && movecontact
trigger9 = stateno = 430 && movecontact
trigger10 = stateno = 440 && movecontact

[State -1]
type = ChangeState
value = 340
triggerall = command = "dlnt_x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 220
trigger3 = stateno = 210
trigger4 = stateno = 420
trigger5 = stateno =1452 && palno >= 7
trigger6 = stateno = 220 && time >= 4
trigger6 = palno <= 6 || palno >= 12
trigger7 = stateno = 210 && time >= 5
trigger7 = palno <= 6
trigger7 = palno <= 6 || palno >= 12
trigger8 = stateno = 420 && time >= 4
trigger8 = palno <= 6 || palno >= 12
trigger9 = stateno = 205 && time >= 5
trigger9 = palno <= 6 || palno >= 12
trigger10 = stateno = 205 && time >= 5
trigger10 = palno <= 6 || palno >= 12
trigger11 = stateno = 205
trigger12 = stateno = 215

;------------------------------------------------------------------------------
[State -1, Dash]
type = ChangeState
value = 100
trigger1 = command = "FF"
trigger1 = statetype = S
trigger1 = ctrl

[State -1]
type = ChangeState
value = 105
trigger1 = command = "BB"
trigger1 = statetype = S
trigger1 = ctrl

;==============================================================================
[State -1, Stand Light Punch]
type = ChangeState
value = 205
triggerall = command = "x"
triggerall = command != "holddown"
triggerall = statetype = S
triggerall = p2bodydist X < 18
trigger1 = ctrl

[State -1, Stand Light Punch]
type = ChangeState
value = 200
triggerall = command = "x"
triggerall = command != "holddown"
triggerall = statetype = S
trigger1 = ctrl

[State -1, Stand Strong Punch]
type = ChangeState
value = 215
triggerall = command = "y"
triggerall = command != "holddown"
triggerall = statetype = S
triggerall = p2bodydist X < 24
trigger1 = ctrl

[State -1, Stand Strong Punch]
type = ChangeState
value = 210
triggerall = command = "y"
triggerall = command != "holddown"
triggerall = statetype = S
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, Stand Light Kick]
type = ChangeState
value = 235
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = statetype = S
triggerall = p2bodydist X < 14
trigger1 = ctrl

[State -1, Stand Light Kick]
type = ChangeState
value = 230
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = statetype = S
trigger1 = ctrl

[State -1, Standing Strong Kick]
type = ChangeState
value = 245
triggerall = command = "b"
triggerall = command != "holddown"
triggerall = statetype = S
triggerall = p2bodydist X < 20
trigger1 = ctrl

[State -1, Standing Strong Kick]
type = ChangeState
value = 240
triggerall = command = "b"
triggerall = command != "holddown"
triggerall = statetype = S
trigger1 = ctrl

[State -1, Crouching Light Kick]
type = ChangeState
value = 450
triggerall = command = "y"
triggerall = command = "holddown"
triggerall = command = "holdfwd"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = (stateno = 300) || (stateno = 320)
trigger2 = MoveContact

;------------------------------------------------------------------------------
[State -1, Taunt]
type = ChangeState
value = 195
triggerall = command = "start"
triggerall = var(20) = 0
trigger1 = statetype != A
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, Crouching Light Punch]
type = ChangeState
value = 400
triggerall = command = "x"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 430 && time >= 4 && movecontact

[State -1, Crouching Strong Punch]
type = ChangeState
value = 410
triggerall = command = "y"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl

[State -1]
type = ChangeState
value = 345
triggerall = command = "cabezaso_x"
trigger1 = statetype = A
trigger1 = ctrl

[State -1]
type = ChangeState
value = 316
triggerall = command = "patada_a"
trigger1 = statetype != A
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, Crouching Light Kick]
type = ChangeState
value = 430
triggerall = command = "a"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl

[State -1, Crouching Strong Kick]
type = ChangeState
value = 440
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, Jump Light Punch]
type = ChangeState
value = 600
triggerall = command = "x"
triggerall = stateno != 105
trigger1 = statetype = A
trigger1 = ctrl

[State -1, Jump Strong Punch]
type = ChangeState
value = 610
triggerall = command = "y"
triggerall = stateno != 105
trigger1 = statetype = A
trigger1 = ctrl

;------------------------------------------------------------------------------
[State -1, Jump Light Kick]
type = ChangeState
value = 630
triggerall = command = "a"
triggerall = stateno != 105
triggerall = vel X = 0
trigger1 = statetype = A
trigger1 = ctrl

[State -1, Jump Light Kick]
type = ChangeState
value = 635
triggerall = command = "a"
triggerall = stateno != 105
triggerall = vel X != 0
trigger1 = statetype = A
trigger1 = ctrl

[State -1, Jump Strong Kick]
type = ChangeState
value = 640
triggerall = command = "b"
triggerall = stateno != 105
triggerall = vel X = 0
trigger1 = statetype = A
trigger1 = ctrl

[State -1, Jump Strong Kick]
type = ChangeState
value = 645
triggerall = command = "b"
triggerall = statetype = A
trigger1 = ctrl


