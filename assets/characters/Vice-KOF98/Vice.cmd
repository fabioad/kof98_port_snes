;=====================================================================
;  CMD File For "Vice"                                  Made By M.M.R.
;                                       Ver. 1.0           2002.Apr.14
;=====================================================================

;=====================================================================
; Definition of the Commands
;=====================================================================

;-| CPU Function |----------------------------------------------------
[Command]
name = "cpu"
command = ~D,DF, F, a
time = 1

[Command]
name = "cpu"
command = ~D,DF, F, b
time = 1

[Command]
name = "cpu"
command = ~D,DF, F, c
time = 1

[Command]
name = "cpu"
command = ~D,DB, B, a
time = 1

[Command]
name = "cpu"
command = ~D,DB, B, b
time = 1

[Command]
name = "cpu"
command = ~D,DB, B, c
time = 1

[Command]
name = "cpu"
command = ~D,DB, F, a
time = 1

[Command]
name = "cpu"
command = ~D,DB, F, b
time = 1

[Command]
name = "cpu"
command = ~D,DB, F, c
time = 1

[Command]
name = "cpu"
command = ~D,UB, F, a
time = 1

[Command]
name = "cpu"
command = ~D,UB, F, b
time = 1

[Command]
name = "cpu"
command = ~D,UB, F, c
time = 1

[Command]
name = "cpu"
command = ~D,DF, F, s
time = 1

[Command]
name = "cpu"
command = ~D,DB, B, s
time = 1

[Command]
name = "cpu"
command = ~D,UB, F, x
time = 1

[Command]
name = "cpu"
command = ~D,UB, F, y
time = 1

[Command]
name = "cpu"
command = ~D,UB, F, z
time = 1

[Command]
name = "cpu"
command = ~D,DB, F, x
time = 1

[Command]
name = "cpu"
command = ~D,DB, F, y
time = 1

[Command]
name = "cpu"
command = ~D,DB, F, z
time = 1

[Command]
name = "cpu"
command = ~D,DB, B, x
time = 1

[Command]
name = "cpu"
command = ~D,DB, B, y
time = 1

[Command]
name = "cpu"
command = ~D,DB, B, z
time = 1

[Command]
name = "cpu"
command = ~D,DF, F, x
time = 1

[Command]
name = "cpu"
command = ~D,DF, F, y
time = 1

[Command]
name = "cpu"
command = ~D,DF, F, z
time = 1


;-| Super Motions |---------------------------------------------------

;---------------------------------------------------------------------
; ウィザリングサーフェス  (Withering Surface)
[Command]
name = "ws_a"
command = ~D,DF, F, D,DF, F, x
time = 30

[Command]
name = "ws_b"
command = ~D,DF, F, D,DF, F, y
time = 30

[Command]
name = "ws_c"
command = ~D,DF, F, D,DF, F, x+y
time = 30

;---------------------------------------------------------------------
; ネガティヴゲイン  (Negative Gain)
[Command]
name = "ng_a"
command = ~F, D, B, F, D, B, a
time = 40

[Command]
name = "ng_a"
command = ~F, D, B, F, D, B, b
time = 40

[Command]
name = "ng_c"
command = ~F, D, B, F, D, B, a+b
time = 40

;-| Special Motions |-------------------------------------------------

;---------------------------------------------------------------------
; アウトレイジ／レイヴナス  (Outrage / Ravenous)
[Command]
name = "or_a"
command = ~D,DB, B, a
time = 20

[Command]
name = "or_b"
command = ~D,DB, B, b
time = 20

;---------------------------------------------------------------------
; ディーサイド  (Diesid)
[Command]
name = "ds_a"
command = ~B, D, F, a
time = 25

[Command]
name = "ds_b"
command = ~B, D, F, b
time = 25

;---------------------------------------------------------------------
; メイヘム  (Mayhem)
[Command]
name = "mh_a"
command = ~D,DB, B, x
time = 20

[Command]
name = "mh_b"
command = ~D,DB, B, y
time = 20

;---------------------------------------------------------------------
; ブラックンド  (Blackened)
[Command]
name = "black"
command = ~B, D, F, x
time = 25

[Command]
name = "black"
command = ~B, D, F, y
time = 25

;---------------------------------------------------------------------
; ゴアフェスト  (Gorefest)
[Command]
name = "gore"
command = ~F, D, B, F, x
time = 25

[Command]
name = "gore"
command = ~F, D, B, F, y
time = 25

;---------------------------------------------------------------------
; ミサンスロウプ  (Misanthrope)
[Command]
name = "mis"
command = ~D,DF, F, x
time = 20

[Command]
name = "mis"
command = ~D,DF, F, y
time = 20

;-| Double Tap |------------------------------------------------------
[Command]
name = "FF";Required (do not remove)
command = F, F
time = 10

[Command]
name = "BB";Required (do not remove)
command = B, B
time = 10

;-| 2/3 Button Combination |------------------------------------------
[Command]
name = "recovery";Required (do not remove)
command = a+x
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
name = "bx"
command = b+x
time = 1

[Command]
name = "by"
command = b+y
time = 1

[Command]
name = "ay"
command = a+y
time = 1

[Command]
name = "xy"
command = x+y
time = 1

[Command]
name = "abcd"
command = x+y+a+b
time = 1

[Command]
name = "abcd"
command = c+z
time = 1

;------------------- KOF Seriese only
[Command]
name = "gc_fwd"
command = a+x
time = 1

[Command]
name = "q_fwd"
command = a+x
time = 1

;-| Dir + Button |----------------------------------------------------
[Command]
name = "fwd_a"
command = /F,a
time = 1

[Command]
name = "fwd_b"
command = /F,b
time = 1

[Command]
name = "fwd_c"
command = /F,c
time = 1

[Command]
name = "fwd_x"
command = /F,x
time = 1

[Command]
name = "fwd_y"
command = /F,y
time = 1

[Command]
name = "fwd_z"
command = /F,z
time = 1

[Command]
name = "back_a"
command = /B,a
time = 1

[Command]
name = "back_b"
command = /B,b
time = 1

[Command]
name = "back_c"
command = /B,c
time = 1

[Command]
name = "back_x"
command = /B,x
time = 1

[Command]
name = "back_y"
command = /B,y
time = 1

[Command]
name = "back_z"
command = /B,z
time = 1

[Command]
name = "downfwd_y"
command = /DF,y
time = 1

;-----------------------------For KOF Seriese only
[Command]
name = "gc_fwd"
command = /DF, a+x
time = 1

[Command]
name = "gc_fwd"
command = /DF, z
time = 1

[Command]
name = "gc_fwd"
command = /F, a+x
time = 1

[Command]
name = "gc_fwd"
command = /F, z
time = 1

[Command]
name = "gc_back"
command = /DB, a+x
time = 1

[Command]
name = "gc_back"
command = /DB, z
time = 1

[Command]
name = "gc_back"
command = /B, a+x
time = 1

[Command]
name = "gc_back"
command = /B, z
time = 1

[Command]
name = "q_fwd"
command = /F, a+x
time = 1

[Command]
name = "q_fwd"
command = /F, z
time = 1

[Command]
name = "q_back"
command = /B, a+x
time = 1

[Command]
name = "q_back"
command = /B, z
time = 1

;-| Single Button |---------------------------------------------------
[Command]
name = "x"
command = x
time = 1

[Command]
name = "a"
command = a
time = 1

[Command]
name = "y"
command = y
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
name = "z"
command = z
time = 1

[Command]
name = "s"
command = s
time = 1

[Command]
name = "recovery"
command = z
time = 1

;----------------------------- KOF Seriese only
[Command]
name = "gc_fwd"
command = z
time = 1

[Command]
name = "q_fwd"
command = z
time = 1

;-| Hold Button |-----------------------------------------------------
[Command]
name = "hold_x"
command = /x
time = 1

[Command]
name = "hold_a"
command = /a
time = 1

[Command]
name = "hold_y"
command = /y
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
name = "hold_z"
command = /z
time = 1

[Command]
name = "hold_s"
command = /s
time = 1

;-| Hold Dir |--------------------------------------------------------
[Command]
name = "holdfwd";Required (do not remove)
command = /$F
time = 1

[Command]
name = "holdback";Required (do not remove)
command = /$B
time = 1

[Command]
name = "holdup";Required (do not remove)
command = /$U
time = 1

[Command]
name = "holddown";Required (do not remove)
command = /$D
time = 1

;------------------------ For KOF Series Only
[Command]
name = "holdupfwd"
command = /UF
time = 1

[Command]
name = "holdupback"
command = /UB
time = 1

;=====================================================================
; State Entry for Commands
;=====================================================================

[Statedef -1]

;=====================================================================
; CPU Function
;=====================================================================
;
;=====================================================================
; Super Arts
;=====================================================================

;---------------------------------------------------------------------
; ＭＡＸ版ネガティヴゲイン
[State -1]
type = ChangeState
value = 3400
triggerall = Command = "ng_c" && Power >= 2000
triggerall = !StateType = A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; ネガティヴゲイン
[State -1]
type = ChangeState
value = 3300
triggerall = Command = "ng_a" && Power >= 1000
triggerall = !StateType = A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; ＭＡＸ版ウィザリングサーフェス
[State -1]
type = ChangeState
value = 3200
triggerall = Command = "ws_c" && Power >= 2000
triggerall = !StateType = A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; ウィザリングサーフェス・強
[State -1]
type = ChangeState
value = 3100
triggerall = Command = "ws_b" && Power >= 1000
triggerall = !StateType = A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; ウィザリングサーフェス・弱
[State -1]
type = ChangeState
value = 3000
triggerall = Command = "ws_a" && Power >= 1000
triggerall = !StateType = A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;=====================================================================
; Special Arts 
;=====================================================================

;---------------------------------------------------------------------
; ゴアフェスト・弱／強共通
[State -1]
type = ChangeState
value = 1500
triggerall = Command = "gore"
triggerall = StateType != A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; ブラックンド・弱／強共通
[State -1]
type = ChangeState
value = 1400
triggerall = Command = "black"
triggerall = StateType != A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; ディーサイド・弱
[State -1]
type = ChangeState
value = 1200
triggerall = Command = "ds_a"
triggerall = StateType != A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; ディーサイド・強
[State -1]
type = ChangeState
value = 1250
triggerall = Command = "ds_b"
triggerall = StateType != A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; メイヘム・弱
[State -1]
type = ChangeState
value = 1300
triggerall = Command = "mh_a"
triggerall = StateType != A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; メイヘム・強
[State -1]
type = ChangeState
value = 1350
triggerall = Command = "mh_b"
triggerall = StateType != A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)

;---------------------------------------------------------------------
; アウトレイジ／レイヴナス・弱
[State -1]
type = ChangeState
value = IfElse(StateType != A,1000,1100)
triggerall = Command = "or_a"
trigger1 = Ctrl = 1 || StateNo = 100 || StateNo = 105
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)
trigger13 = MoveContact && (StateNo = 500 && AnimElemNo(0) <= 3)
trigger14 = MoveContact && (StateNo = 510 && AnimElemNo(0) <= 4)

;---------------------------------------------------------------------
; アウトレイジ／レイヴナス・強
[State -1]
type = ChangeState
value = IfElse(StateType != A,1050,1150)
triggerall = Command = "or_b"
trigger1 = Ctrl = 1 || StateNo = 100 || StateNo = 105
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)
trigger11 = MoveContact && (StateNo = 600 && AnimElemNo(0) <= 7)
trigger12 = MoveContact && (StateNo = 710 && AnimElemNo(0) <= 5)
trigger13 = MoveContact && (StateNo = 500 && AnimElemNo(0) <= 3)
trigger14 = MoveContact && (StateNo = 510 && AnimElemNo(0) <= 4)

;=====================================================================
; Basic Animation
;=====================================================================

;---------------------------------------------------------------------
;RunFwd
[State -1]
type = ChangeState
value = 100
trigger1 = Command = "FF" && StateType = S && Ctrl = 1 && StateNo != 100

;---------------------------------------------------------------------
;RunBack
[State -1]
type = ChangeState
value = 105
trigger1 = Command = "BB" && StateType = S && Ctrl = 1

;=====================================================================
; 2/3 Buttons
;=====================================================================
;
;=====================================================================
; Basic Throws
;=====================================================================

;---------------------------------------------------------------------
; デスブロウ（Ｐ通常投げ）
[State -1]
type = ChangeState
value = 800
triggerall = StateNo != 100 && StateType = S && Ctrl = 1
triggerall = P2MoveType != H && !P2StateType = A
trigger1 = Command = "fwd_y" && P2BodyDist X < 8
trigger2 = Command = "back_y" && P2BodyDist X < 20

;---------------------------------------------------------------------
; バックラッシュ（Ｋ通常投げ）
[State -1]
type = ChangeState
value = 850
triggerall = StateNo != 100 && StateType = S && Ctrl = 1
triggerall = P2MoveType != H && !P2StateType = A
trigger1 = Command = "fwd_b" && P2BodyDist X < 8
trigger2 = Command = "back_b" && P2BodyDist X < 20

;---------------------------------------------------------------------
; Special Attacks , Moves and so on.
;---------------------------------------------------------------------
;---------------------------------------------------------------------
; 地上ふっとばし攻撃
[State -1]
type = ChangeState
value = 600
triggerall = Command = "c" || Command = "by"
trigger1 = StateType != A && (Ctrl = 1 || StateNo = 100)

;---------------------------------------------------------------------
; 空中ふっとばし攻撃
[State -1]
type = ChangeState
value = 610
triggerall = Command = "c" || Command = "by"
trigger1 = StateType = A && Ctrl = 1

;---------------------------------------------------------------------
; ガードキャンセル緊急回避動作（前・後）
[State -1]
type = ChangeState
value = 4000
triggerall = Command = "gc_fwd" && Power >= 1000
triggerall = Var(4) = 1 && StateType != A
trigger1 = StateNo = 150 || StateNo = 152

;---------------------------------------------------------------------
; 緊急回避動作（前）
[State -1]
type = ChangeState
value = 4050
triggerall = Command = "q_fwd" && !Command = "holdback"
trigger1 = StateType = S && (Ctrl = 1 || StateNo = 100)

;---------------------------------------------------------------------
; 緊急回避動作（後）
[State -1]
type = ChangeState
value = 4150
triggerall = Command = "q_back" && !Command = "holdfwd"
trigger1 = StateType = S && (Ctrl = 1 || StateNo = 100)

;---------------------------------------------------------------------
; ガードキャンセル吹っ飛ばし攻撃
[State -1]
type = ChangeState
value = 4500
triggerall = Command = "by" || Command = "c"
triggerall = Var(4) = 1 && Power >= 1000 && StateType != A
trigger1 = StateNo = 150 || StateNo = 152

;=====================================================================
; Dir + Button
;=====================================================================

;---------------------------------------------------------------------
; モンストロシティー（→＋Ｘ）
[State -1]
type = ChangeState
value = IfElse(MoveContact,710,700)
triggerall = Command = "fwd_x" && !Command = "holddown"
triggerall = StateType != A
trigger1 = Ctrl = 1 || StateNo = 100
trigger2 = MoveContact && (StateNo = 200 && AnimElemNo(0) <= 4)
trigger3 = MoveContact && (StateNo = 210 && AnimElemNo(0) <= 5)
trigger4 = MoveContact && (StateNo = 220 && AnimElemNo(0) <= 4)
trigger5 = MoveContact && (StateNo = 230 && (AnimElemNo(0) = [6,7]))
trigger6 = MoveContact && (StateNo = 270 && AnimElemNo(0) <= 5)
trigger7 = MoveContact && (StateNo = 300 && AnimElemNo(0) <= 3)
trigger8 = MoveContact && (StateNo = 310 && AnimElemNo(0) <= 4)
trigger9 = MoveContact && (StateNo = 320 && AnimElemNo(0) <= 5)
trigger10 = MoveContact && (StateNo = 330 && AnimElemNo(0) <= 5)

;=====================================================================
; Taunts
;=====================================================================

;---------------------------------------------------------------------
; 挑発
[State -1]
type = ChangeState
value = 195
triggerall = command = "s"
trigger1 = StateType = S && Ctrl = 1

;=====================================================================
; Basic Arts
;=====================================================================

;---------------------------------------------------------------------
; 弱パンチ
[State -1]
type = ChangeState
value = IfElse(P2BodyDist X <= 20,200,200)
triggerall = Command = "x" && !Command = "holddown"
trigger1 = StateType = S && (Ctrl = 1 || StateNo = 100)
trigger2 = StateNo = 200 && AnimElemNo(0) >= 3
trigger3 = StateNo = 320 && AnimElemNo(0) >= 5

;---------------------------------------------------------------------
; 弱キック
[State -1]
type = ChangeState
value = IfElse(P2BodyDist X <= 18,220,270)
triggerall = Command = "a" && !Command = "holddown"
trigger1 = StateType = S && (Ctrl = 1 || StateNo = 100)

;---------------------------------------------------------------------
; 強パンチ
[State -1]
type = ChangeState
value = IfElse(P2BodyDist X <= 25,210,260)
triggerall = Command = "y" && !Command = "holddown"
trigger1 = StateType = S && (Ctrl = 1 || StateNo = 100)

;---------------------------------------------------------------------
; 強キック
[State -1]
type = ChangeState
value = IfElse(P2BodyDist X <= 20,230,280)
triggerall = Command = "b" && !Command = "holddown"
trigger1 = StateType = S && (Ctrl = 1 || StateNo = 100)

;---------------------------------------------------------------------
; しゃがみ弱パンチ
[State -1]
type = ChangeState
value = 300
triggerall = Command = "x" && Command = "holddown"
trigger1 = StateType = C && Ctrl = 1
trigger2 = StateNo = 100
trigger3 = StateNo = 200 && AnimElemNo(0) >= 3
trigger4 = StateNo = 320 && AnimElemNo(0) >= 5
trigger5 = StateNo = 310 && AnimElemNo(0) >= 4

;---------------------------------------------------------------------
; しゃがみ強パンチ
[State -1]
type = ChangeState
value = 310
triggerall = Command = "y" && Command = "holddown"
trigger1 = StateType = C && Ctrl = 1
trigger2 = StateNo = 100

;---------------------------------------------------------------------
; しゃがみ弱キック
[State -1]
type = ChangeState
value = 320
triggerall = Command = "a" && Command = "holddown"
trigger1 = StateType = C && Ctrl = 1
trigger2 = StateNo = 100
trigger3 = StateNo = 200 && AnimElemNo(0) >= 3
trigger4 = StateNo = 320 && AnimElemNo(0) >= 5

;---------------------------------------------------------------------
; しゃがみ強キック
[State -1]
type = ChangeState
value = 330
triggerall = Command = "b" && Command = "holddown"
trigger1 = StateType = C && Ctrl = 1
trigger2 = StateNo = 100

;---------------------------------------------------------------------
; ジャンプ弱パンチ
[State -1]
type = ChangeState
value = IfElse(Var(25) = 0 && Vel X = 0,500,500)
triggerall = Command = "x" && StateType = A && Ctrl = 1
trigger1 = StateNo != 105

;---------------------------------------------------------------------
; ジャンプ強パンチ
[State -1]
type = ChangeState
value = IfElse(Var(25) = 0 && Vel X = 0,510,510)
triggerall = Command = "y" && StateType = A && Ctrl = 1
trigger1 = StateNo != 105

;---------------------------------------------------------------------
; ジャンプ弱キック
[State -1]
type = ChangeState
value = IfElse(Var(25) = 0 && Vel X = 0,520,520)
triggerall = Command = "a" && StateType = A && Ctrl = 1
trigger1 = StateNo != 105

;---------------------------------------------------------------------
; ジャンプ強キック
[State -1]
type = ChangeState
value = IfElse(Var(25) = 0 && Vel X = 0,530,530)
triggerall = Command = "b" && StateType = A && Ctrl = 1
trigger1 = StateNo != 105

