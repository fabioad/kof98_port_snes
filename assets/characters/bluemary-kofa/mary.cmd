;#ADD004BASIC PIEs#
;-|Super Motions |--------------------------------------------------------
;============================max2==================================
;Infinity Rose
[Command]
name = "Infinity Rose"
command = ~D, DB, B, D, DB, B, c
time = 30

[Command]
name = "Infinity Roseb"
command = ~D, DF, F, D, DF, F, c
time = 30

;玛丽超级台风（空中发动）
[Command]
name = "dynamite"
command = ~D, DF, F, D, DF, F, c
time = 30

[Command]
name = "MAXdunk"
command = ~D, B, D, B, z
time = 30

;玛丽台风max
;[Command]
;name = "dynamite_d"
;command = ~D, DF, F, D, DF, F, z
;time = 30


;==================================================================
;Superdunk
[Command]
name = "superdunk"
command = ~D, B, D, B, x
time = 30

[Command]
name = "superdunk"
command = ~D, B, D, B, y
time = 30


;==================================================================
;玛丽台风（空中发动为近身投技）
[Command]
name = "dynamite_b"
command = ~D, DF, F, D, DF, F, a
time = 30

[Command]
name = "dynamite_b"
command = ~D, DF, F, D, DF, F, b
time = 30


;==================================================================
;Super splash
[Command]
name = "splash_a"
command = ~D, DF, F, D, DF, F, x
time = 30

[Command]
name = "splash_a"
command = ~D, DF, F, D, DF, F, y
time = 30

;Max splash
[Command]
name = "splash_c"
command = ~D, DF, F, D, DF, F, z
time = 30
;==================================================================
;玛丽野玫瑰
[Command]
name = "typhoon_b"
command = ~D, B, D, B, a
time = 30

[Command]
name = "typhoon_b"
command = ~D, B, D, B, b
time = 30

;玛丽野玫瑰max
[Command]
name = "typhoon_d"
command = ~D, B, D, B, c
time = 30
;==================================================================
;-| Special Motions |------------------------------------------------------
;Hi
[Command]
name = "RealCtr"
command = ~D, DB, B, x
time = 30

[Command]
name = "RealCtr"
command = ~D, DB, B, y
time = 30

;vertical air
[Command]
name = "uppercut_b"
command = ~F, D ,DF, a
time = 30

;vertical air
[Command]
name = "uppercut_d"
command = ~F, D ,DF, b
time = 30

;good night
[Command]
name = "goodnight"
command = ~B, DB, D, DF, F, x
time = 30

[Command]
name = "goodnight"
command = ~B, DB, D, DF, F, y
time = 30

[Command]
name = "HdCsh_a"
command = ~B, DB, D, DF, F, a
time = 30

[Command]
name = "HdCsh_b"
command = ~B, DB, D, DF, F, b
time = 30

;straight slicer a
[Command]
name = "slicer_a"
command = ~25$B, F, a
time = 30

;straight slicer b
[Command]
name = "slicer_b"
command = ~25$B, F, b
time = 30

[Command]
name = "tatsumaki_b"
command = ~D, DB, B, a
time = 30

[Command]
name = "tatsumaki_d"
command = ~D, DB, B, b
time = 30

;check
[Command]
name = "fireball_a"
command = ~D, DF, F, a
time = 30

[Command]
name = "fireball_c"
command = ~D, DF, F, b
time = 30

;Spinfall
[Command]
name = "spinfall_a"
command = ~D, DF, F, a
time = 30

[Command]
name = "spinfall_b"
command = ~D, DF, F, b
time = 30

[Command]
name = "闪电击"
command = ~D, DF, F, x
time = 30

[Command]
name = "闪电击"
command = ~D, DF, F, y
time = 30

;---------------------------------------------------------------------
; 关节连续技1
[Command]
name = "Reversal_a"
command = ~D, DB, B, a
time = 30

;---------------------------------------------------------------------
; 关节连续技2
[Command]
name = "Reversal_b"
command = ~D, DB, B, b
time = 30

;---------------------------------------------------------------------
[Command]
name = "Spinfall_x"
command = ~D, DF, F, x
time = 30

[Command]
name = "Spinfall_y"
command = ~D, DF, F, y
time = 30

;---------------------------------------------------------------------
; 玛丽小旋风
[Command]
name = "HdCsh98_a"
command = ~F ,DF, D, DB, B, F, a
time = 20

[Command]
name = "HdCsh98_b"
command = ~F ,DF, D, DB, B, F, b
time = 20

;-| Double Tap |-----------------------------------------------------------
[Command]
name = "FF"
command = F, F
time = 12

[Command]
name = "BB"
command = B, B
time = 12

[Command]
name = "longjump"
command = D, $U
time = 18

;-| 2/3 Button Combination |-----------------------------------------------

[Command]
name = "recovery";Required (do not remove)
command = a+b
time = 1

;dodge
[Command]
name = "a+x"
command = a+x
time = 1

;counter
[Command]
name = "b+y"
command = b+y
time = 1

;charge
;[Command]
;name = "c+z"
;command = c+z
;time = 1

;-| Hold Button |-----------------------------------------------------------

[Command]
name = "hold_a"
command = /a
time = 1

[Command]
name = "hold_b"
command = /b
time = 1

[Command]
name = "hold_c"
command = /c
time = 1

[Command]
name = "hold_x"
command = /x
time = 1

[Command]
name = "hold_y"
command = /y
time = 1

[Command]
name = "hold_z"
command = /z
time = 1

;-| Hold Dir |--------------------------------------------------------------
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

;-| Dir + Button |---------------------------------------------------------
[Command]
name = "throw_d"
command = /F,b;z
time = 1

[Command]
name = "throw_d"
command = /B,b;z
time = 1

[Command]
name = "throw_c"
command = /F,y
time = 1

[Command]
name = "throw_c"
command = /B,y
time = 1

[Command]
name = "fwd_a"
command = /F,a
time = 1

[Command]
name = "fwd_b"
command = /F,b
time = 1
[Command]
name = "fwd_b"
command = /F,x
time = 1

[Command]
name = "fwd_c"
command = /F,c
time = 1

[Command]
name = "fwd_c"
command = /F,y
time = 1

[Command]
name = "fwd_d"
command = /F,z
time = 1

[Command]
name = "back_c"
command = /B,c
time = 1
[Command]
name = "back_c"
command = /B,y
time = 1

;-| Single Button |---------------------------------------------------------
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
name = "s"
command = s
time = 1

;-| Hold Dir |--------------------------------------------------------------
[Command]
name = "holdfwd"
command = /$F
time = 1

[Command]
name = "holdback"
command = /$B
time = 1

;---------------------------------------------------------------------------
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



;---------------------------------------------------------------------------
[State -1, M. Infinity Rose];---------表模式
type = ChangeState
value = 3060
triggerall = command = "Infinity Rose"
triggerall = power >= 3000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

[State -1, Infinity Rose];---------EX模式
type = ChangeState
value = 50000
triggerall = command = "Infinity Roseb"
triggerall = power >= 3000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------

;Dynamite Dunk (level 2)---------双模式通用MAX2
[State -1]
type = ChangeState
value = 40000
triggerall = command = "dynamite"
triggerall = power >= 3000
triggerall = statetype = A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------

;Dynamite Dunk (level 1)---------EX双模式
[State -1]
type = ChangeState
value = 4000
triggerall = command = "dynamite_b"
triggerall = power >= 1000
triggerall = statetype = A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------

;Super Goodnight---------EX模式
[State -1]
type = ChangeState;null;
value = 3000
triggerall = command = "superdunk"
triggerall = power >= 1000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;Super Goodnight---------EX模式
[State -1]
type = ChangeState;null;
value = 30000
triggerall = command = "MAXdunk"
triggerall = power >= 2000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;---------------------------------------------------------------------------
;Typhoon (level 2)
[State -1]
type = ChangeState
value = 3800
triggerall = command = "typhoon_d"
triggerall = power >= 2000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------
;Typhoon (level 1)
[State -1]
type = ChangeState
value = 3800
triggerall = command = "typhoon_b"
triggerall = power >= 1000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------
;Splash Rose (level 2 / level 1 if guage < 2)
[State -1]
type = ChangeState
value = 3400
triggerall = command = "splash_c"
triggerall = power >= 2000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------
;Splash Rose (level 1)
[State -1]
type = ChangeState
value = 3300
triggerall = command = "splash_a"
triggerall = power >= 1000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------
;Dynamite Swing (level 2)
;[State -1]
;type = ChangeState
;value = 3100
;triggerall = command = "dynamite_d"
;triggerall = power >= 2000
;triggerall = statetype != A
;trigger1 = ctrl
;trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------
;Dynamite Swing (level 1)
[State -1]
type = ChangeState
value = 3100
triggerall = command = "dynamite_b"
triggerall = power >= 1000
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;---------------------------------------------------------------------------
[State -1, HdCsh98]
type = ChangeState
value = 1900
triggerall = Command = "HdCsh98_a" || command = "HdCsh98_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;---------------------------------------------------------------------------
;Slicer_B
[State -1, straight slicer a]
type = ChangeState
value = 1600
triggerall = command = "slicer_a"
triggerall = command != "spinfall_a"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = [200, 299]
trigger2 = statetype != A
trigger2 = movecontact

;---------------------------------------------------------------------------
;Slicer_D
[State -1, straight slicer b]
type = ChangeState
value = 1610
triggerall = command = "slicer_b"
triggerall = command != "spinfall_b"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = [200, 299]
trigger2 = statetype != A
trigger2 = movecontact
;---------------------------------------------------------------------------
;Reversal_B
[State -1]
type = ChangeState
value = 1500
triggerall = command = "tatsumaki_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;---------------------------------------------------------------------------
;Reversal_D
[State -1]
type = ChangeState
value = 1520
triggerall = command = "tatsumaki_d"
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;---------------------------------------------------------------------------
;Goodnight (a)
[State -1, good night]
type = ChangeState
value = 1300
triggerall = command = "goodnight"
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

[State -1]
type = ChangeState
value = 1050
triggerall = !var(0)
triggerall = Command = "HdCsh_a" || Command = "HdCsh_b"
trigger1 = stateno = 250
;---------------------------------------------------------------------------
;Vertical_B
[State -1]
type = ChangeState
value = 1100
triggerall = command = "uppercut_b"
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;---------------------------------------------------------------------------
;Vertical_D
[State -1]
type = ChangeState
value = 1110
triggerall = command = "uppercut_d"
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;---------------------------------------------------------------------------
;Spider (chain from spinfall)
[State -1]
type = ChangeState
value = 1205
triggerall = !var(0)
triggerall = stateno = 1150
triggerall = movehit
triggerall = statetype = A
trigger1 = command = "fireball_a"
trigger2 = command = "fireball_c"

[State -1]
type = ChangeState
value = 1205
triggerall = !var(0)
triggerall = stateno = 1160
triggerall = movehit
triggerall = statetype = A
trigger1 = command = "fireball_a"
trigger2 = command = "fireball_c"


;---------------------------------------------------------------------------
;Spinfall_D
[State -1, spinfall_b]
type = ChangeState
value = 1160
triggerall = command = "spinfall_b";"fireball_d"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = [200, 299]
trigger2 = stateno != 220
trigger2 = stateno != 230
trigger2 = statetype != A
trigger2 = movecontact

;---------------------------------------------------------------------------
;Spinfall_B
[State -1, spinfall_a]
type = ChangeState
value = 1150
triggerall = command = "spinfall_a";"fireball_b"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = [200, 299]
trigger2 = stateno != 220
trigger2 = stateno != 230
trigger2 = statetype != A
trigger2 = movecontact

[State -1]
type = ChangeState
triggerall = !var(0)
value = IfElse(Vel X = 0,1810,1800)
triggerall = (Command = "Spinfall_x" || Command = "Spinfall_y")
trigger1 = StateType = A && Ctrl = 1

;---------------------------------------------------------------------------
[State -1, Hi]
type = ChangeState
value = 250
triggerall = command = "RealCtr"
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact

;---------------------------------------------------------------------------
;Dodge Forward
[State -1, dodge forward]
type = ChangeState
value = 260
triggerall = command = "z"  || command = "a+x"
triggerall = command != "holdback"
trigger1 = statetype != A && (ctrl || stateno = 100)

;---------------------------------------------------------------------------
[State -1]
type = ChangeState
value = 261
triggerall = command = "z" || command = "a+x"
triggerall = command != "holdback"
triggerall = power >= 1000
trigger1 = statetype != A
trigger1 = stateno = [150,153]

;---------------------------------------------------------------------------
;Dodge Back
[State -1, dodge back]
type = ChangeState
value = 265
triggerall = command = "z" || command = "a+x"
triggerall = command = "holdback"
trigger1 = statetype != A
trigger1 = ctrl

;---------------------------------------------------------------------------
[State -1]
type = ChangeState
value = 266
triggerall = command = "z" || command = "a+x"
triggerall = command = "holdback"
triggerall = power >= 1000
trigger1 = statetype != A
trigger1 = stateno = [150,153]

;---------------------------------------------------------------------------
[State -1, 倒地回避]
type = ChangeState
value = 267
triggerall = Vel Y > 0 && Pos Y >= -20 && alive && (StateNo = 5050 || StateNo = 5071)
trigger1 = command = "a+x" || command = "z"

;---------------------------------------------------------------------------
;RunFwd
[State -1]
type = ChangeState
value = 100
triggerall = command = "FF"
trigger1 = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
;RunB
[State -1]
type = ChangeState
value = 105
triggerall = command = "BB"
trigger1 = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
;Throw_C
[State -1]
type = ChangeState
value = 900
triggerall = statetype = S
triggerall = ctrl
triggerall = stateno != 100    ;Not running
triggerall = p2bodydist X < 6
trigger1 = command = "throw_c" ;Near, p2 stand
trigger1 = p2statetype = S
trigger1 = p2movetype != H
trigger2 = command = "throw_c" ;Near, p2 crouch
trigger2 = p2statetype = C
trigger2 = p2movetype != H

;---------------------------------------------------------------------------
;Throw_D
[State -1]
type = ChangeState
value = 920
triggerall = statetype = S
triggerall = ctrl
triggerall = stateno != 100    ;Not running
triggerall = p2bodydist X < 6
trigger1 = command = "throw_d" ;Near, p2 stand
trigger1 = p2statetype = S
trigger1 = p2movetype != H
trigger2 = command = "throw_d" ;Near, p2 crouch
trigger2 = p2statetype = C
trigger2 = p2movetype != H


;no agregar nada debajo
;---------------------------------------------------------------------------
;Taunt
[State -1]
type = ChangeState
value = 195
triggerall = command = "s"
triggerall = stateno != 195
trigger1 = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
;Counter
[State -1, air counter]
type = ChangeState
value = 241
triggerall = command = "c" || command = "b+y"
trigger1 = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;Counter
[State -1, stand counter]
type = ChangeState
value = 940
triggerall = command = "c" || command = "b+y"
triggerall = statetype != A
trigger1 = ctrl
trigger2=(stateno=[200,499]) && movecontact
;---------------------------------------------------------------------------

;CD attack(during guard)
;[State -1]
;type = ChangeState
;value = 243
;triggerall = command = "c" || command = "b+y"
;triggerall = power >= 1000
;trigger1 = statetype != A
;trigger1 = stateno = [150,153]

;---------------------------------------------------------------------------
















; fwd a
[State -1]
type = ChangeState
value = 204
triggerall = command = "holdfwd" || command = "holdback"
triggerall = command = "x"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 100

;Stand_A(close)
[State -1]       ;no funciona
type = ChangeState
value = 201
triggerall = P2bodydist X < 15
triggerall = command = "x"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 100

;Stand light punch
[State -1, stand light punch]
type = ChangeState
value = 200
triggerall = command = "x"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 100


;Stand Medium Punch Close
[State -1, Stand Medium Punch Close]
type = ChangeState
value = 215
triggerall = p2bodydist X <= 20
triggerall = command = "y"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,209])&& movecontact
trigger3 = (stateno = [230,239])&& movecontact
trigger4 = (stateno = [400,409])&& movecontact
trigger5 = (stateno = [430,439])&& movecontact
trigger6 = stateno = 100

;Stand Medium Punch
[State -1, Stand Medium Punch]
type = ChangeState
value = 210
triggerall = command = "y"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,209])&& movecontact
trigger3 = (stateno = [230,239])&& movecontact
trigger4 = (stateno = [400,409])&& movecontact
trigger5 = (stateno = [430,439])&& movecontact
trigger6 = stateno = 100



;---------------------------------------------------------------------------

;Fwd B
[State -1]
type = ChangeState
value = 237
triggerall = command = "holdfwd" || (var(21) && command = "holdback")
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,209])&& movecontact
trigger3 = (stateno = [400,409])&& movecontact
trigger4 = stateno = 100

;Stand_B(close)
[State -1, stand near kick]
type = ChangeState
value = 236
triggerall = P2bodydist X < 10
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,209])&& movecontact
trigger3 = (stateno = [400,409])&& movecontact
trigger4 = stateno = 100

;Stand light kick
[State -1, stand light kick]
type = ChangeState
value = 230
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,209])&& movecontact
trigger3 = (stateno = [400,409])&& movecontact
trigger4 = stateno = 100


;Stand_D (close)
[State -1]
type = ChangeState
value = 246
triggerall = P2bodydist X < 20
triggerall = command = "b"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,219])&& movecontact
trigger3 = (stateno = [230,239])&& movecontact
trigger4 = (stateno = [400,419])&& movecontact
trigger5 = (stateno = [430,439])&& movecontact
trigger6 = stateno = 100

;Stand hard kick
[State -1, stand hard kick]
type = ChangeState
value = 240
triggerall = command = "b"
triggerall = command != "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,219])&& movecontact
trigger3 = (stateno = [230,239])&& movecontact
trigger4 = (stateno = [400,419])&& movecontact
trigger5 = (stateno = [430,439])&& movecontact
trigger6 = stateno = 100



;---------------------------------------------------------------------------

;Crouching Light Punch
[State -1, Crouching Light Punch]
type = ChangeState
value = 400
triggerall = command = "x"
triggerall = command = "holddown"
triggerall = statetype != A
trigger1 = ctrl  

;Crouching Medium Punch
[State -1, Crouching Medium Punch]
type = ChangeState
value = 410
triggerall = command = "y"
triggerall = command = "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,209])&& movecontact
trigger3 = (stateno = [230,239])&& movecontact
trigger4 = (stateno = [400,409])&& movecontact
trigger5 = (stateno = [430,439])&& movecontact   

;Crouching Light Kick
[State -1, Crouching Light Kick]
type = ChangeState
value = 430
triggerall = command = "a"
triggerall = command = "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,209])&& movecontact
trigger3 = (stateno = [400,409])&& movecontact  

;DFwd B
[State -1]
type = ChangeState
value = 445
triggerall = command = "b"
triggerall = command = "holddown"
triggerall = command = "holdfwd"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,219])&& movecontact
trigger3 = (stateno = [230,239])&& movecontact
trigger4 = (stateno = [400,419])&& movecontact
trigger5 = (stateno = [430,439])&& movecontact
trigger6 = stateno = 100  

;Crouching_D
[State -1, crouch ]
type = ChangeState
value = 440
triggerall = command = "b"
triggerall = command = "holddown"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = (stateno = [200,219])&& movecontact
trigger3 = (stateno = [230,239])&& movecontact
trigger4 = (stateno = [400,419])&& movecontact
trigger5 = (stateno = [430,439])&& movecontact
trigger6 = stateno = 100  

;---------------------------------------------------------------------------


;---------------------------------------------------------------------------
;air light punch
[State -1, air light punch]
type = ChangeState
value = 600
triggerall = command = "x"
trigger1 = statetype = A
trigger1 = ctrl


;air medium punch
[State -1, air medium punch]
type = ChangeState
value = 615
triggerall = command = "y"
triggerall = statetype = A
triggerall = ctrl
trigger1 = Vel X != 0
trigger2 = stateno = 2041

;air hard punch
[State -1, air hard punch]
type = ChangeState
value = 610
triggerall = command = "y"
trigger1 = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;Jumping_B
[State -1, air light kick]
type = ChangeState
value = 630
triggerall = command = "a"
trigger1 = statetype = A
trigger1 = ctrl


;Jumping_D
[State -1, air hard kick]
type = ChangeState
value = 640
triggerall = command = "b" && vel x = 0
trigger1 = statetype = A
trigger1 = ctrl

[State -1, air hard kick]
type = ChangeState
value = 645
triggerall = command = "b"
trigger1 = statetype = A
trigger1 = ctrl

