;#ADD004BASIC PIEs#
;-| Super Motions |--------------------------------------------------------

[Command]
name = "qcfhcb_x"
command = ~D, F, B, x
time = 45

[Command]
name = "qcfhcb_y"
command = ~D, F,  B,  y
time = 45

[Command]
name = "qcfhcb_xy"
command = ~D, F, B,  x+y
time = 45

[Command]
name = "qcfhcb_xy"
command = ~D, F, B,  c
time = 45

[Command]
name = "qcbhcf_x"
command = ~D, B,  F, x
time = 45

[Command]
name = "qcbhcf_y"
command = ~D, B,  F, y
time = 45

[Command]
name = "dfdf_a"
command = ~D, DF, F, D, DF, F, a
time = 45

[Command]
name = "dfdf_a"
command = ~D, DF, F, D, DF, F, b
time = 45

[Command]
name = "dfdf_y"
command = ~D, DF, F, D, DF, F, x+y
time = 45

[Command]
name = "dfdf_y"
command = ~D, DF, F, D, DF, F, c
time = 45


[Command]
name = "MAX2"
command = D, B, F, c
time = 45

[Command]
name = "MAX2"
command = D, B, F, x+y
time = 45



;-| Special Motions |------------------------------------------------------

[Command]
name = "dizzyrecover"
command = F,B
time = 20

[Command]
name = "qcf_x"
command = ~D,DF,F, x
time = 25

[Command]
name = "qcf_y"
command = ~D,DF,F, y
time = 25

[Command]
name = "qcb_a"
command = ~D, B, a
time = 15

[Command]
name = "qcb_b"
command = ~D, B, b
time = 15

[Command]
name = "dp_x"
command = ~F, D, DF, x
time = 20

[Command]
name = "dp_y"
command = ~F, D, DF, y
time = 20

[Command]
name = "dp_a"
command = ~F, D, DF, a
time = 15

[Command]
name = "dp_b"
command = ~F, D, DF, b
time = 15

[Command]
name = "charge_x"
command = ~B, $D,F, x
time = 15

[Command]
name = "charge_y"
command = ~B,$D, F, y
time = 15

[Command]
name = "wheel_x"
command = ~$x, $x, $x
time = 35

[Command]
name = "wheel_y"
command = ~$y, $y, $y
time = 30


[Command]
name = "wheel_x"
command = ~D,D,x
time = 35

[Command]
name = "wheel_y"
command = ~D,D,y
time = 30

[Command]
name = "ltp_x"
command = ~D,DF, F, x
time = 15

[Command]
name = "ltp_y"
command = ~D, DF,F, y
time = 15

[Command]
name = "df_x"
command = ~D,DF, F , x

[Command]
name = "df_y"
command = ~D, DF,F , y

[Command]
name = "db_x"
command = ~D, B, x
time = 15

[Command]
name = "db_y"
command = ~D, B, y
time = 15

[Command]
name = "longjump"
command = $D, $U
time = 18

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

[Command];stricker call
name = "striker"
command = a+y
time = 1

[Command]
name = "recovery"
command = z
time = 1

[Command]
name = "dodge"
command = a+x
time = 1

[Command]
name = "knockdown"
command = b+y
time = 1

[Command]
name = "abc"
command = a+b+c
time = 1

[Command]
name = "charge"
command = a+x+y
time = 1

;-| Dir + Button |---------------------------------------------------------

[Command]
name = "fwd_a"
command = /F, a
time = 1

[Command]
name = "fwd_b"
command = /F, b
time = 1

[Command]
name = "fwd_x"
command = /F, x
time = 1

[Command]
name = "fwd_y"
command = /F, y
time = 1

[Command]
name = "back_x"
command = /B, x

[Command]
name = "fwd_y"
command = /F, y
time = 1

[Command]
name = "back_y"
command = /B, y

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
name = "hold_c"
command = /c
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
command = /z
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






; 라이어 엘리멘탈 MAX2
[State -1]
type = ChangeState
value = 6000
triggerall = command = "MAX2" 
triggerall = power >= 3000 && var(19) > 0
trigger1 = statetype != A
trigger1 = ctrl = 1

; 사라만다 스트림 light
[State -1]
type = ChangeState
value = 1900
triggerall = command = "qcbhcf_x"
triggerall = power >= 1000 || var(18) > 0
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 1600 && movecontact
trigger3 = stateno = 1610 && movecontact
trigger4 = stateno = 1700 && movecontact
trigger5 = stateno = 1710 && movecontact

 사라만다 스트림 Max
[State -1]
type = ChangeState
value = 1910
triggerall = command = "qcbhcf_y"
triggerall = power >= 1000 && var(18) > 0
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 1600 && movecontact
trigger3 = stateno = 1610 && movecontact
trigger4 = stateno = 1700 && movecontact
trigger5 = stateno = 1710 && movecontact

; 사라만다 스트림 light
[State -1]
type = ChangeState
value = 1900
triggerall = command = "qcbhcf_y"
triggerall = power >= 1000 || var(18) > 0
trigger1 = statetype != A
trigger1 = ctrl = 1

; Flaming Stick Spin Hard Full
[State -1]
type = ChangeState
value = 1860
triggerall = command = "qcfhcb_xy"
triggerall = power >= 1000 
trigger1 = statetype != A
trigger1 = ctrl = 1

; Flaming Stick Spin light
[State -1]
type = ChangeState
value = 1800
triggerall = command = "qcfhcb_x"
triggerall = power >= 1000 || var(18) > 0
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 1600 && movecontact
trigger3 = stateno = 1610 && movecontact
trigger4 = stateno = 1700 && movecontact
trigger5 = stateno = 1710 && movecontact

; Flaming Stick Spin light long
[State -1]
type = ChangeState
value = 1850
triggerall = command = "qcfhcb_y"
triggerall = power >= 1000 || var(18) > 0
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 1600 && movecontact
trigger3 = stateno = 1610 && movecontact
trigger4 = stateno = 1700 && movecontact
trigger5 = stateno = 1710 && movecontact


; Super Stick Swing Hard
[State -1]
type = ChangeState
value = 2510
triggerall = command = "dfdf_y"
triggerall = power >= 2000 && var(19) > 0
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 1800 && movecontact
trigger3 = stateno = 1850 && movecontact
trigger4 = stateno = 1900 && movecontact




; Cho HongRenSalgon 
[State -1]
type = ChangeState
value = 2600
triggerall = command = "dfdf_a"
triggerall = power >= 1000 || var(18) > 0
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 1600 && movecontact
trigger3 = stateno = 1610 && movecontact
trigger4 = stateno = 1700 && movecontact
trigger5 = stateno = 1710 && movecontact

; HongRenSalgon light 2k2 mode cancel
[State -1]
type = ChangeState
value = 1580
triggerall = command = "dp_x" && var(18) > 0 && statetype != A 
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; HongRenSalgon light
[State -1]
type = ChangeState
value = 1500
triggerall = command = "dp_x"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; HongRenSalgon hard 2k2 mode cancel
[State -1]
type = ChangeState
value = 1590
triggerall = command = "dp_y" && var(18) > 0 && statetype != A
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; HongRenSalgon Hard
[State -1]
type = ChangeState
value = 1520
triggerall = command = "dp_y"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; Light Three Part Cane 2k2 mode cancel
[State -1]
type = ChangeState
value = 1720
triggerall = (command = "ltp_x" || command = "ltp_y") && var(18) > 0 && statetype != A
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; Light Three Part Cane
[State -1]
type = ChangeState
value = 1700
triggerall = command = "ltp_x"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; Hard Three Part Cane
[State -1]
type = ChangeState
value = 1710
triggerall = command = "ltp_y"
triggerall = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; Sparrow Killer 2k2 mode cancel
[State -1]
type = ChangeState
value = 1791
triggerall = (command = "db_x" || command = "db_y") && var(18) > 0 && statetype != A
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; Sparrow Killer
[State -1]
type = ChangeState
value = 1790
triggerall = command = "db_x"
triggerall = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; Sparrow Killer
[State -1]
type = ChangeState
value = 1790
triggerall = command = "db_y"
triggerall = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; Counter Attack (upper) 2k2 mode cancel
[State -1]
type = ChangeState
value = 1102
triggerall = command = "qcb_a" && var(18) > 0 && statetype != A
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; Counter Attack (upper)
[State -1]
type = ChangeState
value = 1100
triggerall = command = "qcb_a"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; Counter Attack (under) 2k2 mode cancel
[State -1]
type = ChangeState
value = 1111
triggerall = command = "qcb_b" && var(18) > 0 && statetype != A
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; Counter Attack (under)
[State -1]
type = ChangeState
value = 1105
triggerall = command = "qcb_b"
trigger1 = statetype != A
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; Strong Attack Flying Cane light 2k2 mode cancel
[State -1]
type = ChangeState
value = 1310
triggerall = command = "dp_a" && var(18) > 0 && statetype != A
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; Strong Attack Flying Cane light
[State -1]
type = ChangeState
value = 1300
triggerall = command = "dp_a"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

; Strong Attack Flying Cane Hard 2k2 mode cancel
[State -1]
type = ChangeState
value = 1315
triggerall = command = "dp_b" && var(18) > 0 && statetype != A
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; Strong Attack Flying Cane Hard
[State -1]
type = ChangeState
value = 1305
triggerall = command = "dp_b"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1
trigger3 = stateno = 410 && movecontact = 1

;Whirlwind Cane (Light)
[State -1]
type = ChangeState
value = 1600
triggerall = command = "wheel_x"
triggerall = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 201 && movecontact = 1

;Rapid Wave Cane (Hard)
[State -1]
type = ChangeState
value = 1610
triggerall = command = "wheel_y"
triggerall = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 221 && movecontact = 1

;-----------기본기관련----------------------------------------------------------
; Jumping knockdown attack
[State -1]
type = ChangeState
value = 640
triggerall = statetype = A
triggerall = ctrl = 1
trigger1 = command = "knockdown"
trigger2 = command = "c"

; Jumping forward light punch
[State -1]
type = ChangeState
value = 600
trigger1 = command = "x"
trigger1 = statetype = A
trigger1 = Vel X != 0
trigger1 = ctrl = 1

; Jumping light punch
[State -1]
type = ChangeState
value = 605
trigger1 = command = "x"
trigger1 = statetype = A
trigger1 = ctrl = 1

; Jumping forward light kick
[State -1]
type = ChangeState
value = 615
trigger1 = command = "a"
trigger1 = statetype = A
trigger1 = Vel X != 0
trigger1 = ctrl = 1

; Jumping light kick
[State -1]
type = ChangeState
value = 610
trigger1 = command = "a"
trigger1 = statetype = A
trigger1 = ctrl = 1

; Jumping forward hard punch
[State -1]
type = ChangeState
value = 621
trigger1 = command = "y"
trigger1 = statetype = A
trigger1 = Vel X != 0
trigger1 = ctrl = 1

; Jumping hard punch
[State -1]
type = ChangeState
value = 620
trigger1 = command = "y"
trigger1 = statetype = A
trigger1 = ctrl = 1

; Jumping forward hard kick
[State -1]
type = ChangeState
value = 635
trigger1 = command = "b"
trigger1 = statetype = A
trigger1 = Vel X != 0
trigger1 = ctrl = 1

; Jumping hard kick
[State -1]
type = ChangeState
value = 630
trigger1 = command = "b"
trigger1 = statetype = A
trigger1 = ctrl = 1

; Hold type 2
[State -1]
type = ChangeState
value = 3020
trigger1 = command = "fwd_y"
trigger1 = statetype = S
trigger1 = stateno != 100
trigger1 = p2bodydist x <= 10
trigger1 = p2movetype != H
trigger1 = p2statetype != A
trigger1 = ctrl = 1

; Hold type 1
[State -1]
type = ChangeState
value = 3000
trigger1 = command = "fwd_b"
trigger1 = statetype = S
trigger1 = stateno != 100
trigger1 = p2bodydist x <= 10
trigger1 = p2movetype != H
trigger1 = p2statetype != A
trigger1 = ctrl = 1

; Crouching light punch
[State -1]
type = ChangeState
value = 400
trigger1 = statetype = C
trigger1 = command = "x"
trigger1 = ctrl = 1

; Crouching light kick
[State -1]
type = ChangeState
value = 410
trigger1 = statetype = C
trigger1 = command = "a"
trigger1 = ctrl = 1

; Crouching hard punch
[State -1]
type = ChangeState
value = 420
trigger1 = statetype = C
trigger1 = command = "y"
trigger1 = ctrl = 1

; Crouching hard kick
[State -1]
type = ChangeState
value = 430
trigger1 = statetype = C
trigger1 = command = "b"
trigger1 = ctrl = 1

;-----------회피관련------------------------------------------------------------
; 회피
[State -1]
type = ChangeState
value = 251
triggerall = command = "z" || command ="dodge"
triggerall = command != "holdfwd" && command != "holdback"
trigger1 = statetype = S
trigger1 = ctrl = 1

; 회피 (attack)
[State -1]
type = ChangeState
value = 252
triggerall = stateno = 251
triggerall = AnimElem = 2, >= 0
trigger1 = command = "x"
trigger2 = command = "y"
trigger3 = command = "a"
trigger4 = command = "b"

; 앞으로 회피 (run)
[State -1]
type = ChangeState
value = 256
triggerall = command = "holdfwd" && command ="z" || command ="holdfwd" && command ="dodge"
trigger1 = stateno = 100

; 앞으로 회피 2k2 mode cancel
[State -1]
type = ChangeState
value = 6200
triggerall = (command = "holdfwd" && command ="z" || command ="holdfwd" && command ="dodge") && var(18) > 0 && statetype = S
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; 앞으로 회피
[State -1]
type = ChangeState
value = 255
triggerall = command = "holdfwd" && command ="z" || command ="holdfwd" && command ="dodge"
trigger1 = statetype = S && ctrl = 1

; 뒤로 회피 2k2 mode cancel
[State -1]
type = ChangeState
value = 6201
triggerall = (command ="holdback" && command ="z" || command ="holdback" && command ="dodge") && var(18) > 0 && statetype = S
trigger1 = stateno = 200 && time <= 20
trigger2 = stateno = 210 && time <= 20
trigger3 = stateno = 211 && time <= 20
trigger4 = stateno = 220 && time <= 20
trigger5 = stateno = 230 && time <= 20
trigger6 = stateno = 231 && time <= 10
trigger7 = stateno = 240 && time <= 20 && movecontact != 1
trigger8 = stateno = 400 
trigger9 = stateno = 410 && movecontact != 1
trigger10= stateno = 420 && movecontact != 1
trigger11= stateno = 430 
trigger12= stateno = 1610 && Animtime <= 80
trigger13= stateno = 251 && movecontact = 1 ; 회피공격

; 뒤로 회피
[State -1]
type = ChangeState
value = 265
triggerall = command = "holdback" && command ="z" || command ="holdback" && command ="dodge"
trigger1 = statetype = S && ctrl = 1

; Guard cancel roll (backwards)
[State -1]
type = ChangeState
value = 260
triggerall = stateno >= 150
triggerall = stateno <= 151
triggerall = power >= 1000
triggerall = command = "holdback"
trigger1 = command = "dodge"
trigger2 = command = "z"

; Guard cancel roll (forward)
[State -1]
type = ChangeState
value = 250
triggerall = stateno >= 150
triggerall = stateno <= 151
triggerall = power >= 1000
trigger1 = command = "dodge"
trigger2 = command = "z"

; Guard cancel attack
[State -1]
type = ChangeState
value = 270
triggerall = stateno >= 150
triggerall = stateno <= 151
triggerall = power >= 1500
trigger1 = command = "knockdown"
trigger2 = command = "c"

; Standing knockdown attack
[State -1]
type = ChangeState
value = 240
triggerall = statetype != A
triggerall = ctrl = 1
trigger1 = command = "knockdown"
trigger2 = command = "c"

; Forward light punch
[State -1]
type = ChangeState
value = 216
triggerall = command = "fwd_x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = movehit = 1
trigger3 = stateno = 201
trigger3 = movehit = 1
trigger4 = stateno = 211
trigger4 = movehit = 1
trigger5 = stateno = 221
trigger5 = movehit = 1
trigger6 = stateno = 231
trigger6 = movehit = 1
trigger7 = stateno = 400
trigger7 = movehit = 1
trigger8 = stateno = 420
trigger8 = movehit = 1

; Standing light punch (close)
[State -1]
type = ChangeState
value = 201
trigger1 = command = "x"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger1 = P2bodydist X <= 25

; Standing light punch
[State -1]
type = ChangeState
value = 200
triggerall = command = "x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

; Standing hard punch (close)
[State -1]
type = ChangeState
value = 221
trigger1 = command = "y"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger1 = P2bodydist X <= 25

; Standing hard punch
[State -1]
type = ChangeState
value = 220
triggerall = command = "y"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

; Forward light kick
[State -1]
type = ChangeState
value = 215
triggerall = command = "fwd_a"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger2 = stateno = 200
trigger2 = movehit = 1
trigger3 = stateno = 201
trigger3 = movehit = 1
trigger4 = stateno = 211
trigger4 = movehit = 1
trigger5 = stateno = 221
trigger5 = movehit = 1
trigger6 = stateno = 231
trigger6 = movehit = 1
trigger7 = stateno = 400
trigger7 = movehit = 1
trigger8 = stateno = 420
trigger8 = movehit = 1

; Standing light kick (close)
[State -1]
type = ChangeState
value = 211
trigger1 = command = "a"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger1 = P2bodydist X <= 45

; Standing light kick
[State -1]
type = ChangeState
value = 210
triggerall = command = "a"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

; Standing hard kick (close)
[State -1]
type = ChangeState
value = 231
trigger1 = command = "b"
trigger1 = statetype = S
trigger1 = ctrl = 1
trigger1 = P2bodydist X <= 10

; Standing hard kick
[State -1]
type = ChangeState
value = 230
triggerall = command = "b"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

; Taunt
[State -1]
type = ChangeState
value = 195
trigger1 = command = "s"
trigger1 = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl = 1

; Run Forward
[State -1]
type = ChangeState
value = 100
trigger1 = command = "FF"
trigger1 = statetype = S
trigger1 = command != "holddown"
trigger1 = ctrl = 1

; Run Backwards
[State -1]
type = ChangeState
value = 105
trigger1 = command = "BB"
trigger1 = statetype = S
trigger1 = command != "holddown"
trigger1 = ctrl = 1

; Power charge
[State -1]
type = ChangeState
value = 3100
triggerall = command = "hold_b" && command = "hold_x"
trigger1 = power < 4000
trigger1 = statetype = S
trigger1 = ctrl = 1

