;#ADD004BASIC PIEs#
;==============================================================================
[Remap]
x = x
y = y
z = z
a = a
b = b
c = c
s = s

;-| 標準化 |-------------------------------------------------------
[Defaults]
command.time = 15
command.buffer.time = 1

;------------------------------------------------------------------------------
;-| MAX2超必殺技 |--------------------------------------------------------------

[Command]
name = "98UMMAX"
command = ~$D, DF, F, $D, DF, F, c
time = 25
buffer.time = 15

[Command]
name = "デッドリーレイブ・ネオ"
command = ~F, DF, D, DB, B, F, x
time = 30

;------------------------------------------------------------------------------
;-| MAX超必殺技 |--------------------------------------------------------------

[Command]
name = "MAXシャインナックル"
command = ~D, DF, F, D, DF, F, a+b
time = 25

[Command]
name = "MAXレイジングストーム"
command = ~D, DF, F, D, DF, F, x+y
time = 25

;------------------------------------------------------------------------------
;-| 超必殺技 |-----------------------------------------------------------------

[Command]
name = "シャインナックル"
command = ~D, DF, F, D, DF, F, a
time = 25

[Command]
name = "シャインナックル"
command = ~D, DF, F, D, DF, F, b
time = 25

[Command]
name = "レイジングストーム"
command = ~D, DF, F, D, DF, F, x
time = 25

[Command]
name = "レイジングストーム"
command = ~D, DF, F, D, DF, F, y
time = 25

;------------------------------------------------------------------------------
;-| 必殺技 |-------------------------------------------------------------------

[Command]
name = "真空投げ"
command = ~D, B, F, y
time = 40

[Command]
name = "真空投げ"
command = ~F, DF, D, DB, B, UB, U, y
time = 40

[Command]
name = "真空投げ"
command = ~U, UF, F, DF, D, DB, B, y
time = 40

[Command]
name = "真空投げ"
command = ~B, UB, U, UF, F, DF, D, y
time = 40

[Command]
name = "真空投げ"
command = ~D, DF, F, UF, U, UB, B, y
time = 40

[Command]
name = "真空投げ"
command = ~B, DB, D, DF, F, UF, U, y
time = 40

[Command]
name = "真空投げ"
command = ~U, UB, B, DB, D, DF, F, y
time = 40

[Command]
name = "真空投げ"
command = ~F, UF, U, UB, B, DB, D, y
time = 40

[Command]
name = "弱ライジングタックル"
command = ~F, D, DF, x

[Command]
name = "強ライジングタックル"
command = ~F, D, DF, y

[Command]
name = "レイジランTYPE「ダンク」"
command = ~D, DB, B, a

[Command]
name = "レイジランTYPE「シフト」"
command = ~D, DB, B, b

[Command]
name = "弱ハードエッジ"
command = ~D, DB, B, x

[Command]
name = "強ハードエッジ"
command = ~D, DB, B, y

[Command]
name = "上段クラックカウンター"
command = ~D, DF, F, a

[Command]
name = "下段クラックカウンター"
command = ~D, DF, F, b

[Command]
name = "烈風拳"
command = ~D, DF, F, x

[Command]
name = "ダブル烈風拳"
command = ~D, DF, F, y

[Command]
name = "弱ライジングタックル"
command = ~20$D, $U, x
time = 30

[Command]
name = "強ライジングタックル"
command = ~20$D, $U, y
time = 30

[Command]
name = "jump"    
command = D, $U
time = 12

;------------------------------------------------------------------------------
;-| キー２回連続入力 |---------------------------------------------------------
[Command]
name = "FF"     ;要求済み (キーの変更は可能ですが名前を変えたり無効にしてはいけません)
command = F, F
time = 10

[Command]
name = "BB"     ;要求済み (キーの変更は可能ですが名前を変えたり無効にしてはいけません)
command = B, B
time = 10

;------------------------------------------------------------------------------
;-| 同時押し |-----------------------------------------------------------------
[Command]
name = "recovery"   ;要求済み (キーの変更は可能ですが名前を変えたり無効にしてはいけません)
command = x+a
time = 1

[Command]
name = "recovery"   ;要求済み (キーの変更は可能ですが名前を変えたり無効にしてはいけません)
command = z
time = 1

[Command]
name = "ふっとばし"
command = y+b
time = 1

[Command]
name = "ふっとばし"
command = c
time = 1

[Command]
name = "a+b"
command = a+b
time = 1

;------------------------------------------------------------------------------
;-| 方向キー＋ボタン |---------------------------------------------------------
[Command]
name = "down_a"
command = /$D,a
time = 1

[Command]
name = "down_b"
command = /$D,b
time = 1

;------------------------------------------------------------------------------
;-| ボタン単発 |---------------------------------------------------------------
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
;-| 方向キー押しっぱなし |-----------------------------------------------------
[Command]
name = "holdfwd"   ;要求済み (キーの変更は可能ですが名前を変えたり無効にしてはいけません)
command = /$F
time = 1

[Command]
name = "holdback"  ;要求済み (キーの変更は可能ですが名前を変えたり無効にしてはいけません)
command = /$B
time = 1

[Command]
name = "holdup"    ;要求済み (キーの変更は可能ですが名前を変えたり無効にしてはいけません)
command = /$U
time = 1

[Command]
name = "holddown"  ;要求済み (キーの変更は可能ですが名前を変えたり無効にしてはいけません)
command = /$D
time = 1

[Command]
name = "holdx+a"
command = /$x+a
time = 1

[Command]
name = "holdx+y"
command = /$x+y
time = 1

;==============================================================================
;------------------------------------------------------------------------------
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



;==============================================================================
[State -1, TB]
type = ChangeState
value = 33300
triggerall = roundstate = 2
triggerall = command = "98UMMAX"
triggerall = power >= 3000
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 315 && movecontact
trigger10 = stateno = 330 && movecontact
trigger11 = stateno = 1150 && AnimElemtime(8) >= 0 && AnimElemtime(12) < 0 && movecontact
trigger12 = stateno = 2100 && AnimElemtime(8) >= 0 && AnimElemtime(11) <= 1 && movecontact

;デッドリーレイブ・ネオ
[State -1, DR]
type = ChangeState
value = 3000
triggerall = command = "デッドリーレイブ・ネオ"
triggerall = power >= 2000
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 315 && movecontact
trigger10 = stateno = 330 && movecontact
trigger11 = stateno = 1150 && AnimElemtime(8) >= 0 && AnimElemtime(12) < 0 && movecontact
trigger12 = stateno = 2100 && AnimElemtime(8) >= 0 && AnimElemtime(11) <= 1 && movecontact

;==============================================================================
;MAXシャインナックル
[State -1, MAX SN]
type = ChangeState
value = 2600
triggerall = command = "MAXシャインナックル"
triggerall = power >= 2000
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 315 && movecontact
trigger10 = stateno = 330 && movecontact
trigger11 = stateno = 1150 && AnimElemtime(8) >= 0 && AnimElemtime(12) < 0 && movecontact
trigger12 = stateno = 2100 && AnimElemtime(8) >= 0 && AnimElemtime(11) <= 1 && movecontact

;------------------------------------------------------------------------------
;MAXレイジングストーム
[State -1, MAX RS]
type = ChangeState
value = 2500
triggerall = command = "MAXレイジングストーム"
triggerall = power >= 2000
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 315 && movecontact
trigger10 = stateno = 330 && movecontact
trigger11 = stateno = 1150 && AnimElemtime(8) >= 0 && AnimElemtime(12) < 0 && movecontact
trigger12 = stateno = 2100 && AnimElemtime(8) >= 0 && AnimElemtime(11) <= 1 && movecontact

;------------------------------------------------------------------------------
;シャインナックル
[State -1, SN]
type = ChangeState
value = 2100
triggerall = command = "シャインナックル"
triggerall = power >= 1000
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 315 && movecontact
trigger10 = stateno = 330 && movecontact
trigger11 = stateno = 1150 && AnimElemtime(8) >= 0 && AnimElemtime(12) < 0 && movecontact

;------------------------------------------------------------------------------
;レイジングストーム
[State -1, RS]
type = ChangeState
value = 2000
triggerall = command = "レイジングストーム"
triggerall = power >= 1000
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 315 && movecontact
trigger10 = stateno = 330 && movecontact
trigger11 = stateno = 1150 && AnimElemtime(8) >= 0 && AnimElemtime(12) < 0 && movecontact

;------------------------------------------------------------------------------
;真空投げ
[State -1, SN]
type = ChangeState
value = 1500
triggerall = command = "真空投げ"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 1355 && AnimElemtime(8) >= 0

;------------------------------------------------------------------------------
;弱ライジングタックル
[State -1, RK]
type = ChangeState
value = 1200
triggerall = command = "弱ライジングタックル"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 40
trigger3 = stateno = 400 && movecontact
trigger4 = stateno = 410 && movecontact
trigger5 = stateno = 430 && movecontact
trigger6 = stateno = 440 && movecontact

;強ライジングタックル
[State -1, DRK]
type = ChangeState
value = 1250
triggerall = command = "強ライジングタックル"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 40
trigger3 = stateno = 400 && movecontact
trigger4 = stateno = 410 && movecontact
trigger5 = stateno = 430 && movecontact
trigger6 = stateno = 440 && movecontact

;---------------------------------------------------------------------------
;レイジランTYPE「ダンク」
[State -1, RR D]
type = ChangeState
value = 1300
triggerall = command = "レイジランTYPE「ダンク」"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 300 && movecontact
trigger10 = stateno = 315 && movecontact
trigger11 = stateno = 330 && movecontact

;レイジランTYPE「シフト」
[State -1, RR S]
type = ChangeState
value = 1350
triggerall = command = "レイジランTYPE「シフト」"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 300 && movecontact
trigger10 = stateno = 315 && movecontact
trigger11 = stateno = 330 && movecontact

;------------------------------------------------------------------------------
;上段クラックカウンター
[State -1, HCC]
type = ChangeState
value = 1400
triggerall = command = "上段クラックカウンター"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 300 && movecontact
trigger10 = stateno = 315 && movecontact
trigger11 = stateno = 330 && movecontact

;下段クラックカウンター
[State -1, LCC]
type = ChangeState
value = 1450
triggerall = command = "下段クラックカウンター"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 300 && movecontact
trigger10 = stateno = 315 && movecontact
trigger11 = stateno = 330 && movecontact

;------------------------------------------------------------------------------
;弱ハードエッジ
[State -1, L HE]
type = ChangeState
value = 1100
triggerall = command = "弱ハードエッジ"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 300 && movecontact
trigger10 = stateno = 315 && movecontact
trigger11 = stateno = 330 && movecontact

;強ハードエッジ
[State -1, S HE]
type = ChangeState
value = 1150
triggerall = command = "強ハードエッジ"
triggerall = statetype != A
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 300 && movecontact
trigger10 = stateno = 315 && movecontact
trigger11 = stateno = 330 && movecontact

;------------------------------------------------------------------------------
;烈風拳
[State -1, RK]
type = ChangeState
value = 1000
triggerall = command = "烈風拳"
triggerall = statetype != A
triggerall = numprojID(1000) = 0
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 300 && movecontact
trigger10 = stateno = 315 && movecontact
trigger11 = stateno = 330 && movecontact

;ダブル烈風拳
[State -1, DRK]
type = ChangeState
value = 1050
triggerall = command = "ダブル烈風拳"
triggerall = statetype != A
triggerall = numprojID(1000) = 0
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact
trigger8 = stateno = 440 && movecontact
trigger9 = stateno = 300 && movecontact
trigger10 = stateno = 315 && movecontact
trigger11 = stateno = 330 && movecontact

;------------------------------------------------------------------------------
;後緊急回避
[State -1, T S]
type = ChangeState
value = 710
triggerall = command = "recovery" && command = "holdback"
triggerall = statetype != a
trigger1 = ctrl
trigger2 = power >= 1000
trigger2 = stateno = [150,153]

;---------------------------------------------------------------------------
;前緊急回避
[State -1, T S]
type = ChangeState
value = 700
triggerall = command = "recovery"
triggerall = statetype != a
trigger1 = ctrl
trigger2 = power >= 1000
trigger2 = stateno = [150,153]
trigger3 = stateno = 100

;---------------------------------------------------------------------------
;受身
[State -1, UKEMI]
type = ChangeState
value = 52000
triggerall = Vel Y > 0 && Pos Y >= -20 && alive && (StateNo = 5050 || StateNo = 5071)
trigger1 = command = "recovery"

;------------------------------------------------------------------------------
;ふっとばし
[State -1, Throw]
type = ChangeState
value = 300
triggerall = command = "ふっとばし"
triggerall = statetype != a
triggerall = stateno != 100
trigger1 = ctrl
trigger2 = power >= 1000
trigger2 = stateno = [150,153]

;------------------------------------------------------------------------------
;空中ふっとばし
[State -1, CD]
type = ChangeState
value = 650
triggerall = command = "ふっとばし"
triggerall = statetype = A
trigger1 = ctrl

;------------------------------------------------------------------------------
;P投げ
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
;K投げ
[State -1, Throw]
type = ChangeState
value = 800
triggerall = command = "b"
triggerall = command = "holdfwd" || command = "holdback"
triggerall = statetype = S
triggerall = stateno != 100
trigger1 = p2bodydist X < 15
trigger1 = p2statetype != A && p2movetype != H
trigger1 = ctrl

;------------------------------------------------------------------------------
;上段避け攻撃
[State -1, JSK]
type = ChangeState
value = 310
triggerall = command = "x"
triggerall = command = "holdfwd"
triggerall = statetype != A
triggerall = command != "holddown"
trigger1 = ctrl
trigger2 = stateno = 205 && movecontact
trigger3 = stateno = 215 && movecontact
trigger4 = stateno = 245 && movecontact
trigger5 = stateno = 400 && movecontact
trigger6 = stateno = 410 && movecontact
trigger7 = stateno = 430 && movecontact

;下段避け攻撃
[State -1, GSK]
type = ChangeState
value = 320
triggerall = command = "a"
triggerall = command = "holdfwd"
triggerall = statetype = S
trigger1 = ctrl

;コンビネーション
[State -1, C]
type = ChangeState
value = 330
triggerall = command = "b"
triggerall = command = "holdfwd"
triggerall = statetype = S
trigger1 = stateno = 245 && AnimElemtime(8) < 0 && movecontact

;------------------------------------------------------------------------------
;ダッシュ
[State -1, Dash]
type = ChangeState
value = 100
trigger1 = command = "FF"
trigger1 = statetype = S
trigger1 = ctrl

;バックステップ
[State -1, Back Step]
type = ChangeState
value = 105
trigger1 = command = "BB"
trigger1 = statetype = S
trigger1 = ctrl

;==============================================================================
;近距離立ち弱パンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 205
triggerall = command = "x"
triggerall = command != "holddown"
triggerall = statetype = S
triggerall = p2bodydist X < 20
trigger1 = ctrl

;遠距離立ち弱パンチ
[State -1, Stand Light Punch]
type = ChangeState
value = 200
triggerall = command = "x"
triggerall = command != "holddown"
triggerall = statetype = S
trigger1 = ctrl

;近距離立ち強パンチ
[State -1, Stand Strong Punch]
type = ChangeState
value = 215
triggerall = command = "y"
triggerall = command != "holddown"
triggerall = statetype = S
triggerall = p2bodydist X < 22
trigger1 = ctrl

;遠距離立ち強パンチ
[State -1, Stand Strong Punch]
type = ChangeState
value = 210
triggerall = command = "y"
triggerall = command != "holddown"
triggerall = statetype = S
trigger1 = ctrl

;------------------------------------------------------------------------------
;近距離立ち弱キック
[State -1, Stand Light Kick]
type = ChangeState
value = 235
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = statetype = S
triggerall = p2bodydist X < 12
trigger1 = ctrl

;遠距離立ち弱キック
[State -1, Stand Light Kick]
type = ChangeState
value = 230
triggerall = command = "a"
triggerall = command != "holddown"
triggerall = statetype = S
trigger1 = ctrl

;近距離立ち強キック
[State -1, Standing Strong Kick]
type = ChangeState
value = 245
triggerall = command = "b"
triggerall = command != "holddown"
triggerall = statetype = S
triggerall = p2bodydist X < 25
trigger1 = ctrl

;遠距離立ち強キック
[State -1, Standing Strong Kick]
type = ChangeState
value = 240
triggerall = command = "b"
triggerall = command != "holddown"
triggerall = statetype = S
trigger1 = ctrl

;------------------------------------------------------------------------------
;挑発
[State -1, Taunt]
type = ChangeState
value = 195
triggerall = command = "start"
triggerall = var(20) = 0
trigger1 = statetype != A
trigger1 = ctrl

;------------------------------------------------------------------------------

;しゃがみ弱パンチ
[State -1, Crouching Light Punch]
type = ChangeState
value = 400
triggerall = command = "x"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 430 && time >= 4 && movecontact

;しゃがみ強パンチ
[State -1, Crouching Strong Punch]
type = ChangeState
value = 410
triggerall = command = "y"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl

;------------------------------------------------------------------------------
;しゃがみ弱キック
[State -1, Crouching Light Kick]
type = ChangeState
value = 430
triggerall = command = "a"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl

;しゃがみ強キック
[State -1, Crouching Strong Kick]
type = ChangeState
value = 440
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl

;------------------------------------------------------------------------------
;ジャンプ弱パンチ
[State -1, Jump Light Punch]
type = ChangeState
value = 600
triggerall = command = "x"
triggerall = stateno != 105  ;バックステップ中は禁止
trigger1 = statetype = A
trigger1 = ctrl

;ジャンプ強パンチ
[State -1, Jump Strong Punch]
type = ChangeState
value = 610
triggerall = command = "y"
triggerall = stateno != 105
trigger1 = statetype = A
trigger1 = ctrl

;------------------------------------------------------------------------------
;ジャンプ弱キック
[State -1, Jump Light Kick]
type = ChangeState
value = 630
triggerall = command = "a"
triggerall = stateno != 105
trigger1 = statetype = A
trigger1 = ctrl

;ジャンプ強キック
[State -1, Jump Strong Kick]
type = ChangeState
value = 640
triggerall = command = "b"
triggerall = stateno != 105
trigger1 = statetype = A
trigger1 = ctrl


