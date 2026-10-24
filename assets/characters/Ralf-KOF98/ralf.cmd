
;-| Button Remapping |-----------------------------------------------------
; This section lets you remap the player's buttons (to easily change the
; button configuration). The format is:
;   old_button = new_button
; If new_button is left blank, the button cannot be pressed.
[Remap]
x = x
y = y
z = z
a = a
b = b
c = c
s = s

;-| Default Values |-------------------------------------------------------
command.time = 12
command.buffer.time = 1


;-| Super Motions |--------------------------------------------------------

[Command]
name = "236236a"
command = ~D, F,~D, DF, F, a
time = 25
[Command]
name = "236236x"
command = ~D, F,~D, DF, F, x
time = 25
[Command]
name = "236236b"
command = ~D, F,~D, DF, F, b
time = 25
[Command]
name = "236236y"
command = ~D, F,~D, DF, F, y
time = 25

[Command]
name = "2141236a"
command = ~D, DB, B, D, F, a
time = 25
[Command]
name = "2141236x"
command = ~D, DB, B, D, F, x
time = 25
[Command]
name = "2141236b"
command = ~D, DB, B, D, F, b
time = 25
[Command]
name = "2141236y"
command = ~D, DB, B, D, F, y
time = 25
[Command]
name = "2363214a"
command = ~D, DF, F, D, B, a
time = 25
[Command]
name = "2363214x"
command = ~D, DF, F, D, B, x
time = 25

;-| Special Motions |------------------------------------------------------

[Command]
name = "236a"
command = ~D, DF, F, a
[Command]
name = "236b"
command = ~D, DF, F, b
[Command]
name = "236x"
command = ~D, DF, F, x
[Command]
name = "236y"
command = ~D, DF, F, y

[Command]
name = "623a"
command = ~F, D, DF, a
[Command]
name = "623b"
command = ~F, D, DF, b
[Command]
name = "623x"
command = ~F, D, DF, x
[Command]
name = "623y"
command = ~F, D, DF, y

[Command]
name = "28b"
command = ~$D, $U, b
[Command]
name = "28y"
command = ~$D, $U, y

[Command]
name = "214a"
command = ~D, DB, B, a
[Command]
name = "214b"
command = ~D, DB, B, b
[Command]
name = "214x"
command = ~D, DB, B, x
[Command]
name = "214y"
command = ~D, DB, B, y

[Command]
name = "41236a"
command = ~B, DB, F, a
time = 20
[Command]
name = "41236a"
command = ~B, DF, F, a
time = 20
[Command]
name = "41236a"
command = DB, D, F, a
time = 20
[Command]
name = "41236b"
command = ~B, DB, F, b
time = 20
[Command]
name = "41236b"
command = ~B, DF, F, b
time = 20
[Command]
name = "41236b"
command = DB, D, F, b
time = 20
[Command]
name = "41236x"
command = ~B, DB, F, x
time = 20
[Command]
name = "41236x"
command = ~B, DF, F, x
time = 20
[Command]
name = "41236x"
command = DB, D, F, x
time = 20
[Command]
name = "41236y"
command = ~B, DB, F, y
time = 20
[Command]
name = "41236y"
command = ~B, DF, F, y
time = 20
[Command]
name = "41236y"
command = DB, D, F, y
time = 20

[Command]
name = "236K"
command = ~D, DF, F, b+y
[Command]
name = "236K"
command = ~D, DF, F, c
[Command]
name = "236K"
command = ~D, DF, F, z
[Command]
name = "623K"
command = ~F, D, DF, b+y
[Command]
name = "623K"
command = ~F, D, DF, c
[Command]
name = "623K"
command = ~F, D, DF, z
[Command]
name = "214K"
command = ~D, DB, B, b+y
[Command]
name = "214K"
command = ~D, DB, B, c
[Command]
name = "214K"
command = ~D, DB, B, z

[Command]
name = "46P"
command = ~B, F, x
time = 10

;-| Double Tap |-----------------------------------------------------------
[Command]
name = "FF"     ;Required (do not remove)
command = F, F
time = 10

[Command]
name = "BB"     ;Required (do not remove)
command = B, B
time = 10

;-| 2/3 Button Combination |-----------------------------------------------
[Command]
name = "recovery";Required (do not remove)
command = a+b
time = 1

;-| Dir + Button |---------------------------------------------------------
[Command]
name = "down_a"
command = /$D,a
time = 1

[Command]
name = "down_b"
command = /$D,b
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
name = "start"
command = s
time = 1

[Command]
name = "abx"
command = a+b+x
time = 1

[Command]
name = "ab"
command = a+b
time = 1

[Command]
name = "ax"
command = a+x
time = 1

[Command]
name = "xy"
command = x+y
time = 1

[Command]
name = "down"
command = $D
time = 1

;-| Hold Dir |--------------------------------------------------------------
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
name = "ha"
command = /a
time = 1

[Command]
name = "hb"
command = /b
time = 1

[Command]
name = "hx"
command = /x
time = 1

[Command]
name = "hy"
command = /y
time = 1

[Statedef -1]

;===========================================================================
;地上無敵
[State 5050, 4] 
type = nothitby
triggerall = alive
triggerall = gethitvar(fall.recover) = 1
trigger1 = gethitvar(hittime) <= 0
trigger1 = statetype = L
value = SCA,AA,AT,AP
;===========================================================================
;空中無敵
[State -1, Strong Kung Fu Blow]
type = nothitby
triggerall = alive
trigger1 = var(9) <= 0 
trigger1 = gethitvar(fall) = 1
trigger1 = movetype = H
trigger1 = gethitvar(fall.recover) = 1
trigger1 = statetype = A 
trigger1 = (gethitvar(fall.recovertime)-gethitvar(fall.time))<=0
trigger2 = stateno = 5040
trigger2 = HitOver
value = SCA,AA,AT,AP

;---------------------------------------------------------------------------
;バリバリバルカンパンチクラシック
[State -1, HA1]
type = ChangeState
value = 501+(var(17)*49)
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = (command ="46P"&&helper(10000),var(14)>=30&&helper(10000),var(16)>=30)||var(21)=501+(var(17)*49)
triggerall = power>=1000
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1
;---------------------------------------------------------------------------
;バリバリバルカンパンチ
[State -1, HA1]
type = ChangeState
value = 500+(var(17)*50)
triggerall = var(59) = 0
triggerall = command ="2363214a"||command ="2363214x"||var(21)=500+(var(17)*50)
triggerall = power>=1000
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1
;---------------------------------------------------------------------------
;弱馬乗りバルカンパンチ
[State -1, HA1]
type = ChangeState
value = 510+(var(17)*50)
triggerall = var(59) = 0
triggerall = command ="2141236b"||var(21)=510+(var(17)*50)
triggerall = power>=1000
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;強馬乗りバルカンパンチ
[State -1, HA1]
type = ChangeState
value = 511+(var(17)*49)
triggerall = var(59) = 0
triggerall = command ="2141236y"||var(21)=511+(var(17)*49)
triggerall = power>=1000
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;弱ギャラクティカファントム
[State -1, HA1]
type = ChangeState
value = 520+(var(17)*50)
triggerall = var(59) = 0
triggerall = command ="236236a"||var(21)=510+(var(17)*50)
triggerall = power>=1000
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;強ギャラクティカファントム
[State -1, HA1]
type = ChangeState
value = 521+(var(17)*49)
triggerall = var(59) = 0
triggerall = command ="236236x"||var(21)=510+(var(17)*49)
triggerall = power>=1000
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;SAB
[State -1, Stand Light Punch]
type = ChangeState
value = 440
triggerall = var(59) = 0
triggerall = command="41236b"||command="41236y"||var(21)=440
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;弱ガトリングアタック
[State -1, Stand Light Punch]
type = ChangeState
value = 410
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = (command="a"&&command="holdfwd"&&helper(10000),var(14)>=30)||var(21)=410
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;強ガトリングアタック
[State -1, Stand Light Punch]
type = ChangeState
value = 411
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = (command="x"&&command="holdfwd"&&helper(10000),var(14)>=30)||var(21)=411
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;弱ラルフキック
[State -1, Stand Light Punch]
type = ChangeState
value = 430
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = (command="b"&&command="holdfwd"&&helper(10000),var(14)>=30)||var(21)=430
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;強ラルフキック
[State -1, Stand Light Punch]
type = ChangeState
value = 431
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = (command="y"&&command="holdfwd"&&helper(10000),var(14)>=30)||var(21)=431
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;弱爆弾パンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 450
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = (command="a"&&command="holdup"&&helper(10000),var(16)>=30)||var(21)=450
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;強爆弾パンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 451
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = (command="x"&&command="holdup"&&helper(10000),var(16)>=30)||var(21)=451
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;弱バーニングハンマー
[State -1, Stand Light Punch]
type = ChangeState
value = 420
triggerall = var(59) = 0
triggerall = command = "214a"||var(21)=420
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;強バーニングハンマー
[State -1, Stand Light Punch]
type = ChangeState
value = 421
triggerall = var(59) = 0
triggerall = command = "214x"||var(21)=421
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger5 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger7 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = movecontact||movereversed
trigger8 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = (stateno=[400,401])&&time<=1

;---------------------------------------------------------------------------
;弱バルカンパンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 400
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = helper(10000),var(10)>=4
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=203&&animelemtime(5)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger5 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger7 = stateno=206&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = stateno=207&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger10 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger11 = stateno=222&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger12 = stateno=223&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(4)<1
trigger13 = movecontact||movereversed
trigger13 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1

;強バルカンパンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 401
triggerall = var(59) = 0
triggerall = numhelper(10000)
triggerall = helper(10000),var(12)>=4
trigger1 = statetype!=A&&ctrl||stateno=40||(stateno=[100,102])||(statetype!=A&&(stateno=[130,131]))
trigger2 = stateno=200&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = stateno=202&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(6)<1
trigger4 = stateno=203&&animelemtime(5)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger5 = stateno=204&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger6 = stateno=205&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0
trigger7 = stateno=206&&animelemtime(4)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger8 = stateno=207&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1
trigger9 = stateno=220&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger10 = stateno=221&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<1
trigger11 = stateno=222&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger12 = stateno=223&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(4)<1
trigger13 = movecontact||movereversed
trigger13 = stateno=210&&animelemtime(6)>=ifelse(movecontact,0,1)&&animelemtime(7)<1

[State 3000, 7]
type = velset
trigger1 = var(59)=0
trigger1 = (stateno=[400,401])&&animelem=2,>=0&&command="holdfwd"
x = 1.5
[State 3000, 7]
type = velset
trigger1 = var(59)=0
trigger1 = (stateno=[400,401])&&animelem=2,>=0&&command!="holdfwd"
x = 0

;---------------------------------------------------------------------------
;爆弾パンチ
[State -1, HA1]
type = ChangeState
value = 455
triggerall = var(59) = 0
triggerall = command="236a"||command="236x"||var(21)=455
triggerall = statetype=A
trigger1 = ctrl||stateno=132||stateno=105
trigger2 = movecontact||movereversed
trigger2 = stateno=230&&animelemtime(2)>=ifelse(movecontact,0,1)&&animelemtime(3)<1
trigger3 = movecontact||movereversed
trigger3 = stateno=231&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(4)<1
trigger4 = movecontact||movereversed
trigger4 = stateno=235&&animelemtime(4)>=ifelse(movecontact,0,1)
trigger5 = movecontact||movereversed
trigger5 = stateno=236&&animelemtime(3)>=ifelse(movecontact,0,1)&&animelemtime(5)<0

;===========================================================================
;---------------------------------------------------------------------------
;パワーMAX
[State -1, HA1]
type = ChangeState
value = 700
triggerall = var(59) = 0
triggerall = command = "abx"
triggerall = var(17) = 0
triggerall = power >= 1000
trigger1 = statetype != A
trigger1 = ctrl||(stateno=[130,131])

;---------------------------------------------------------------------------
;キャンセル歩行
[State -1, Run Fwd]
type = ChangeState
value = 20
triggerall = var(59) = 0
trigger1 = command = "holdfwd"
trigger1 = statetype != A
trigger1 = stateno=[130,131]
ctrl=1

;キャンセルジャンプ
[State -1, Run Fwd]
type = ChangeState
value = 40
triggerall = var(59) = 0
trigger1 = command = "holdup"
trigger1 = statetype != A
trigger1 = stateno=[130,131]

;---------------------------------------------------------------------------
;Run Fwd
;ダッシュ
[State -1, Run Fwd]
type = ChangeState
value = 100
triggerall = var(59) = 0
trigger1 = command = "FF"
trigger1 = statetype != A
trigger1 = ctrl||(stateno=[130,131])

;---------------------------------------------------------------------------
;Run Back
;後退ダッシュ
[State -1, Run Back]
type = ChangeState
value = 105
triggerall = var(59) = 0
trigger1 = command = "BB"
trigger1 = statetype != A
trigger1 = ctrl||(stateno=[130,131])

;---------------------------------------------------------------------------
;パンチ投げ
[State -1, Kung Fu Throw]
type = ChangeState
value = 300
triggerall = var(59) = 0
triggerall = command="x"&&command!="a"&&p2bodydist X <= 15
triggerall = command="holdfwd"||command="holdback"
triggerall = statetype = S
triggerall = stateno != 100
triggerall = p2statetype != A
triggerall = p2movetype != H
trigger1 = ctrl||(stateno=[130,131])
trigger2 = stateno=101

;---------------------------------------------------------------------------
;キック投げ
[State -1, Kung Fu Throw]
type = ChangeState
value = 310
triggerall = var(59) = 0
triggerall = command = "y"&&command!="b"&&p2bodydist X <= 15
triggerall = command="holdfwd"||command="holdback"
triggerall = statetype = S
triggerall = stateno != 100
triggerall = p2statetype != A
triggerall = p2movetype != H
trigger1 = ctrl||(stateno=[130,131])
trigger2 = stateno=101

;---------------------------------------------------------------------------
;GC後転
[State -1, Stand Light Punch]
type = ChangeState
value = 262
triggerall = var(59) = 0
triggerall = (command ="ab"&&command="holdback")||var(21)=262
trigger1 = stateno=151||stateno=153
trigger1 = time<=1
trigger1 = power >= 1000

;---------------------------------------------------------------------------
;GC前転
[State -1, Stand Light Punch]
type = ChangeState
value = 261
triggerall = var(59) = 0
triggerall = (command="ab"&&command!="holdback")||var(21)=261
trigger1 = stateno=151||stateno=153
trigger1 = time<=1
trigger1 = power >= 1000

;---------------------------------------------------------------------------
;GCふっとばし
[State -1, Stand Light Punch]
type = ChangeState
value = 260
triggerall = var(59) = 0
triggerall = (command="xy")||var(21)=260
trigger1 = stateno=151||stateno=153
trigger1 = time<=1
trigger1 = power >= 1000

;---------------------------------------------------------------------------
;後転
[State -1, Stand Light Punch]
type = ChangeState
value = 251
triggerall = var(59) = 0
triggerall = command="ab"&&command="holdback"
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;前転
[State -1, Stand Light Punch]
type = ChangeState
value = 250
triggerall = var(59) = 0
triggerall = command="ab"&&command!="holdback"
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;先行入力前転
[State -1, Stand Light Punch]
type = ChangeState
value = var(21)
triggerall = var(21) = [250,251]
trigger1 = var(59) = 0
trigger1 = stateno=[100,101]

;===========================================================================
;---------------------------------------------------------------------------
;ふっとばし
[State -1, Stand Light Punch]
type = ChangeState
value = 210
triggerall = var(59) = 0
triggerall = command="xy"&command!="a"&command!="b"&&command!="holddown"
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;---------------------------------------------------------------------------
;立ち弱パンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 200
triggerall = var(59) = 0
triggerall = (command="a"&&command!="holddown")||var(21)=200
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
;---------------------------------------------------------------------------
;立ち強パンチ
[State -1, Stand Strong Punch]
type = ChangeState
value = 202
triggerall = var(59) = 0
triggerall = command="x"&&command!="holddown"
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
;---------------------------------------------------------------------------
;立ち弱キック
[State -1, Stand Light Punch]
type = ChangeState
value = 204
triggerall = var(59) = 0
triggerall = command="b"&&command!="holddown"
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])
;---------------------------------------------------------------------------
;立ち強キック
[State -1, Stand Strong Punch]
type = ChangeState
value = 206
triggerall = var(59) = 0
triggerall = command="y"&&command!="holddown"
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;---------------------------------------------------------------------------
;Taunt
;挑発
[State -1, Taunt]
type = ChangeState
value = 195+(((100*enemynear,life)/enemynear,lifeMax)>50)
triggerall = var(59) = 0
triggerall = command = "start"
triggerall = statetype!=A&&(stateno!=[190,199])
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;---------------------------------------------------------------------------
;屈弱パンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 220
triggerall = var(59) = 0
triggerall = (command="a"&&command="holddown")||var(21)=220
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;---------------------------------------------------------------------------
;屈強パンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 221
triggerall = var(59) = 0
triggerall = command="x"&&command="holddown"
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;---------------------------------------------------------------------------
;屈弱キック
[State -1, Stand Light Punch]
type = ChangeState
value = 222
triggerall = var(59) = 0
triggerall = (command="b"&&command="holddown")||var(21)=222
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;---------------------------------------------------------------------------
;屈強キック
[State -1, Stand Light Punch]
type = ChangeState
value = 223
triggerall = var(59) = 0
triggerall = command="y"&&command="holddown"
triggerall = statetype!=A
trigger1 = ctrl||(stateno=[100,101])||(stateno=[130,131])

;---------------------------------------------------------------------------
;ジャンプふっとばし
[State -1, Stand Light Punch]
type = ChangeState
value = 234
triggerall = var(59) = 0
triggerall = command="xy"
triggerall = statetype=A
trigger1 = ctrl||stateno=132

;---------------------------------------------------------------------------
;空中弱パンチ
[State -1, Jump Light Punch]
type = ChangeState
value = 230
triggerall = var(59) = 0
triggerall = command="a"
triggerall = statetype=A
trigger1 = ctrl||stateno=132

;---------------------------------------------------------------------------
;空中強パンチ
[State -1, Jump Strong Punch]
type = ChangeState
value = 231
triggerall = var(59) = 0
triggerall = command="x"
triggerall = statetype=A
trigger1 = ctrl||stateno=132

;---------------------------------------------------------------------------
;空中弱キック
[State -1, Jump Light Punch]
type = ChangeState
value = 232
triggerall = var(59) = 0
triggerall = command="b"
triggerall = statetype=A
trigger1 = ctrl||stateno=132

;---------------------------------------------------------------------------
;空中強キック
[State -1, Jump Strong Punch]
type = ChangeState
value = 233
triggerall = var(59) = 0
triggerall = command="y"
triggerall = statetype=A
trigger1 = ctrl||stateno=132













[State 200, 5]
type = varset
trigger1 = animtime=-1&&(stateno=[200,229])&&(var(21)=[200,229])
var(21) = 0
[State 200, 5]
type = changestate
trigger1 = var(59)=0&&(ctrl=1||(stateno=[130,131]))&&statetype!=A
trigger1 = (var(21)!=[230,239])&&(var(21)!=[260,269])&&(var(21)!=[455,459])&&statetype!=L&&var(21)!=0
value = var(21)
[State 200, 5]
type = changestate
trigger1 = var(59)=0&&ctrl=1&&statetype=A&&((var(21)=[230,239])||(var(21)=[455,459]))&&var(21)!=0
value = var(21)
[State 200, 5]
type = changestate
trigger1 = var(59)=0&&power>=1000&&(var(21)=[260,262])&&var(21)!=0&&time<=1
trigger1 = stateno=151||stateno=153
value = var(21)


[State -1, Taunt];ジャンプ
type = varset
var(1) = 10
trigger1 = command = "down"

[State -1, Taunt]
type = helper
triggerall = teammode = single || teammode = turns
triggerall = numhelper(1210) = 0
triggerall = var(4) = 2
trigger1 = (stateno=[200,229])||(stateno=[300,599])||(stateno=[1000,1001])
stateno = 1210
id = 1210
ignorehitpause = 1 

[State -1, Taunt]
type = helper
triggerall = numhelper(1210) = 0
trigger1 = (stateno=[520,529])||(stateno=[570,579])
stateno = 1210
id = 1210
ignorehitpause = 1 

[State -1, Taunt]
type = nothitby
trigger1 = movecontact=1
value = SCA,AA,AT,AP
ignorehitpause = 1 
[State -1, Taunt]
type = playerpush
trigger1 = p2statetype=S&&p2dist Y>=50
trigger2 = (p2statetype=C||p2statetype=L)&&p2dist Y>=30
value = 0
ignorehitpause = 1 