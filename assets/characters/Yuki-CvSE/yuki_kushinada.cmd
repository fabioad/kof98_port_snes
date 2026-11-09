[Remap]
x = x
y = y
z = z
a = a
b = b
c = c
s = s

[Defaults]
command.time = 30
command.buffer.time = 1

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


;-| Hold Button |--------------------------------------------------------
[Command]
name = "holda"
command = /a
time = 1

[Command]
name = "holdb"
command = /b
time = 1

[Command]
name = "holdc"
command = /c
time = 1

[Command]
name = "holdx"
command = /x
time = 1

[Command]
name = "holdy"
command = /y
time = 1

[Command]
name = "holdz"
command = /z
time = 1

[Command]
name = "holdstart"
command = /s
time = 1


;-| CPU |----------------------------------------------------------------
[Command]
name = "a2"
command = a
time = 1

[Command]
name = "b2"
command = b
time = 1

[Command]
name = "c2"
command = c
time = 1

[Command]
name = "x2"
command = x
time = 1

[Command]
name = "y2"
command = y
time = 1

[Command]
name = "z2"
command = z
time = 1

[Command]
name = "start2"
command = s
time = 1

[Command]
name = "holdfwd2"
command = /$F
time = 1

[Command]
name = "holdback2"
command = /$B
time = 1

[Command]
name = "holdup2"
command = /$U
time = 1

[Command]
name = "holddown2"
command = /$D
time = 1

[Command]
name = "holda2"
command = /a
time = 1

[Command]
name = "holdb2"
command = /b
time = 1

[Command]
name = "holdc2"
command = /c
time = 1

[Command]
name = "holdx2"
command = /x
time = 1

[Command]
name = "holdy2"
command = /y
time = 1

[Command]
name = "holdz2"
command = /z
time = 1

[Command]
name = "holdstart2"
command = /s
time = 1

[Command]
name = "recovery2"
command = x+a
time = 1

;-| Super Motions |--------------------------------------------------------
[Command]
name = "Kyo's Saishuu Kessen Ougi Mu Shiki"
command = ~D, B, D, B, c
time = 30

[Command]
name = "Kyo's Saishuu Kessen Ougi Mu Shiki alt"
command = ~D, B, D, B, x+y
time = 30

[Command]
name = "EX Yuki-Chan no Trap"
command = ~F, B, D, F, a+b
time = 30

[Command]
name = "Yuki-Chan no Trap"
command = ~F, B, D, F, a
time = 30

[Command]
name = "Yuki-Chan no Trap"
command = ~F, B, D, F, b
time = 30

[Command]
name = "EX Naku Ko wa Tsuyoi"
command = ~D, F, D, F, x+y
time = 30

[Command]
name = "Naku Ko wa Tsuyoi"
command = ~D, F, D, F, x
time = 30

[Command]
name = "Naku Ko wa Tsuyoi"
command = ~D, F, D, F, y
time = 30

[Command]
name = "EX Ai no Kusanagi Dai Koushin!!"
command = ~D, B, D, F, x+y
time = 30

[Command]
name = "Ai no Kusanagi Dai Koushin!!"
command = ~D, B, D, F, x
time = 30

[Command]
name = "Ai no Kusanagi Dai Koushin!!"
command = ~D, B, D, F, y
time = 30

[Command]
name = "Yuki's Hamburger"
command = D, D, a+b
time = 20

;-| Special Motions |------------------------------------------------------
[Command]
name = "Hyakuretsu Terekakushi_x"
command = x, x, x
time = 25
buffer.time = 15

[Command]
name = "Hyakuretsu Terekakushi_y"
command = y, y, y, y
time = 30
buffer.time = 18

[Command]
name = "Valting Over"
command = ~F, D, DF, x
time = 11

[Command]
name = "Valting Over"
command = ~F, D, DF, y
time = 11

[Command]
name = "Sabaori 2000"
command = ~F, DF, D, DB, B, x
time = 15

[Command]
name = "Sabaori 2000"
command = ~F, DF, D, DB, B, y
time = 15

[Command]
name = "Kaban Barrier!?"
command = ~F, D, B, a
time = 15

[Command]
name = "Kaban Barrier!?"
command = ~F, D, B, b
time = 15

[Command]
name = "Yuki-Chan no Kaban no Nakami"
command = ~D, F, x
time = 15

[Command]
name = "Yuki-Chan no Kaban no Nakami"
command = ~D, F, y
time = 15

[Command]
name = "Otome no Sakebi"
command = ~D, F, a
time = 15

[Command]
name = "Otome no Sakebi"
command = ~D, F, b
time = 15

[Command]
name = "Yuki-Chan Furimawasu"
command = ~D, B, x
time = 15

[Command]
name = "Yuki-Chan Furimawasu"
command = ~D, B, y
time = 15

[Command]
name = "longjump"
command = ~$D, $U
time = 2

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
name = "holdb"
command = /$b
time = 1

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
command = x+a
time = 1

[Command]
name = "blowback";Required (do not remove)
command = y+b
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

;---------------------------------------------------------------------------
; 2. State entry
; --------------------------------------------------------------------------
[Statedef -1]

; AI Helper Check
[State -1, AI Helper Check]
type = ChangeState
trigger1 = IsHelper(9741)
value = 9741

; AI Helper Check 2
[State -1, AI Helper Check 2]
type = ChangeState
trigger1 = IsHelper(9742)
value = 9742

;===========================================================================
; Ai Section
;===========================================================================
; Jump
[State -1, AI Jump]
type = ChangeState
triggerAll = var(0)
triggerAll = random < 200
triggerAll = statetype != A
triggerAll = ctrl
triggerAll = p2bodydist x >= 70
trigger1 = EnemyNear, AnimTime < -30
trigger1 = p2MoveType = A
trigger1 = p2statetype != A
trigger1 = p2stateNo = [1000,2999]
value = 40

; Jump Attacks
[State -1, AI Jump Attacks]
type = ChangeState
triggerAll = var(0)
triggerAll = statetype = A
triggerAll = ctrl
triggerAll = p2bodydist x <= 50
triggerall = random < 600
trigger1 = vel y > 0 && pos y = [-46,-35]
trigger1 = p2statetype != A
trigger1 = vel x != 0
value = ifelse(random < 300, 610, ifelse(random < 300, 640, ifelse(random < 500, 600, 630)))

; Jump Attacks
[State -1, AI Jump Attacks (neutral)]
type = ChangeState
triggerAll = var(0)
triggerAll = statetype = A
triggerAll = ctrl
triggerAll = p2bodydist x <= 50
triggerall = random < 600
trigger1 = vel y > 0 && pos y = [-46,-35]
trigger1 = p2statetype != A
trigger1 = vel x = 0
value = ifelse(random < 500, 645, 635)

; Roll Forwards
[State -1, AI Roll Forwards]
type = ChangeState
triggerAll = var(0)
triggerAll = random < 80
triggerAll = statetype != A
triggerAll = inguarddist
trigger1 = p2bodydist x = [25,105]
trigger1 = EnemyNear, AnimTime = [-53,-37]
trigger1 = p2statetype != A
trigger1 = ctrl || (stateno = [100,101]) || stateno = [120,131]
trigger2 = stateno = 100
trigger2 = p2bodydist x > 130
value = 900

; Stand Guard
[State -1, AI Standing Guard]
type = changestate
triggerall = NumEnemy
triggerall = RoundState = 2 && var(0)
triggerall = StateType != A
triggerall = P2StateType != C
triggerall = StateType = S
triggerall = (P2Movetype = A) || (Enemy, NumProj >= 1)
trigger1 = Ctrl && P2BodyDist X <= 90
trigger1 = random <= 800
value = 130

; Stand to Crouch Guard
[State -1, AI Stand to Crouch Guard]
type = ChangeState
triggerall = NumEnemy
triggerall = RoundState = 2 && var(0)
triggerall = StateType != A
triggerall = P2StateType = C
triggerall = (P2Movetype = A) || (Enemy, NumProj >= 1)
trigger1 = StateNo = 150
trigger1 = 1
value = 152

; Crouch Guard
[State -1, AI Crouch Guard]
type = ChangeState
triggerall = NumEnemy
triggerall = RoundState = 2 && var(0)
triggerall = StateType != A
triggerall = P2StateType = C
triggerall = (P2Movetype = A) || (Enemy, NumProj >= 1)
trigger1 = Ctrl
trigger1 = random <= 800
value = 131

; Crouch to Stand Guard
[State -1, AI Crouch to Stand Guard]
type = ChangeState
triggerall = NumEnemy
triggerall = RoundState = 2 && var(0)
triggerall = StateType != A
triggerall = P2StateType != C
triggerall = (P2Movetype = A) || (Enemy, NumProj >= 1)
trigger1 = StateNo = 152
trigger1 = 1
value = 150

; Jump Guard
[State -1, AI Jump Guard]
type = changestate
triggerall = NumEnemy
triggerall = RoundState = 2 && var(0)
triggerall = StateType = A
triggerall = (P2Movetype = A) || (Enemy, NumProj >= 1)
trigger1 = ctrl
trigger1 = random <= 800
value = 132

; Throw
[State -1, AI Throw]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
triggerall = ctrl && StateType != A
triggerall = P2statetype != A && P2statetype != L
triggerall = P2movetype = I && P2movetype != H
triggerall = P2bodyDist X <= 10
triggerall = P2stateno != 5120
trigger1 = Random < 150
value = 800

; Emergency Evade
[State -1, AI Emergency Evade]
type = ChangeState
triggerall = roundstate = 2 && var(0)
Triggerall = (ctrl || (stateno = 52 && animelemtime(1) > 0) || (stateno = [100, 101])) && statetype != A
triggerall = enemynear, hitdefattr = SCA,NA,SA,HA,NP,SP,HP
triggerall = p2bodydist x <= 70
triggerall = P2statetype != A
triggerall = P2MoveType = A
trigger1 = Random < 100
value = ifelse(random < 500, 900, 905)

; Guard Cancel Blowback Attack
[State -1, AI Guard Cancel Blowback Attack]
type = ChangeState
triggerall = NumEnemy
triggerall = RoundState = 2 && var(0)
triggerall = Power >= 1000 && StateType != A
triggerall = P2BodyDist x <= 30
trigger1 = (stateno = 150 || stateno = 152)
trigger1 = random < 50
value = 915

;  Yuki-Chan ga Koronda!?
[State -1, AI Yuki-Chan ga Koronda!?]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
triggerall = ctrl && StateType != A
triggerall = P2statetype = C
trigger1 = p2movetype = I
trigger1 = P2bodydist X = [10,85]
trigger1 = random < 200
value = 700

;Yuki-Chan no Kaban no Nakami
[State -1, AI Yuki-Chan no Kaban no Nakami]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
triggerall = numproj = 0
triggerall = ctrl && StateType != A
triggerall = P2statetype != A
triggerall = p2movetype != A
trigger1 = prevstateno != 5120 || prevstateno != 1000
trigger1 = (P2bodydist X = [80,235]) && p2stateno != 5120 && random < 50
trigger2 = (P2bodydist X = [45,100]) && p2stateno = 5120 && random < 100
value = 1000

; Otome no Sakebi
[State -1, AI Otome no Sakebi]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
triggerall = ctrl && StateType != A && p2movetype != H
triggerall = FrontEdgeDist >= 40
triggerall = p2movetype != A
trigger1 = P2statetype = A && enemynear, vel x > 0 && enemynear, vel Y < 0 && (p2dist x = [70,155]) && (EnemyNear, Pos Y = [-120,-60]) && random < 100
trigger2 = P2statetype = A && enemynear, vel x = 0 && enemynear, vel Y < 0 && (p2dist x = [10,75]) && (EnemyNear, Pos Y = [-120,-60]) && random < 100
trigger3 = p2statetype != A && P2statetype != L && (p2dist x = [55,80]) && random < 50
value = 1100

; Valting Over Throw/Sabaori 2000
[State -1, AI Valting Over Throw/Sabaori 2000]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
Triggerall = (ctrl || (stateno = [100, 101])) && statetype != A
triggerall = p2statetype != A && P2statetype != L && p2movetype != H
triggerall = P2bodyDist X <= 25
triggerall = P2stateno != 5120
trigger1 = Random < 400
value = ifelse(random < 500, 1200, 1600)

; Kaban Barrier!?/Hyakuretsu Terekakushi
[State -1, AI Kaban Barrier!?/Hyakuretsu Terekakushi]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
triggerall = ctrl && StateType != A
triggerall = P2statetype != A && p2movetype != H
triggerall = p2movetype != A
trigger1 = prevstateno != 5120 || prevstateno != 1000
trigger1 = (P2bodydist X = [25,75]) && p2stateno != 5120 && random < 50
value = ifelse(random < 200, 1300, 1500)

; Yuki-Chan Furimawasu
[State -1, AI Yuki-Chan Furimawasu]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
triggerall = ctrl && StateType != A
triggerall = P2statetype != A && p2movetype != H
triggerall = p2movetype != A
trigger1 = prevstateno != 5120 || prevstateno != 1000
trigger1 = (P2bodydist X = [90,145]) && p2stateno != 5120 && random < 30
value = 1400

; Ai no Kusanagi Dai Koushin!!
[State -1, AI Ai no Kusanagi Dai Koushin!!]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
Triggerall = (ctrl || (stateno = [100, 101])) && statetype != A
triggerall = power >= 1000
triggerall = p2bodydist X = [0,60]
trigger1 = enemynear, movetype = A && enemynear, hitdefattr = SCA,NA,SA,HA && random < 100
value = 3300

; EX Ai no Kusanagi Dai Koushin!!
[State -1, AI EX Ai no Kusanagi Dai Koushin!!]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
Triggerall = (ctrl || (stateno = [100, 101])) && statetype != A
triggerall = power >= 2000
triggerall = p2bodydist X = [0,60]
trigger1 = enemynear, movetype = A && enemynear, hitdefattr = SCA,NA,SA,HA && random < 100
value = 3350

; Kyo's Saishuu Kessen Ougi "Mu Shiki"
[State -1, AI Kyo's Saishuu Kessen Ougi "Mu Shiki"]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
Triggerall = (ctrl || (stateno = [100, 101])) && statetype != A
triggerall = power >= 3000
triggerall = p2bodydist X = [0,60]
trigger1 = enemynear, movetype = A && enemynear, hitdefattr = SCA,NA,SA,HA && random < 200
value = 3800

; Combo Starter 1 (Light Attacks)
[State -1, AI Combo Starter 1]
type = changestate
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
Triggerall = (ctrl || (stateno = 52 && animelemtime(1) > 0) || (stateno = [100, 101])) && statetype != A
triggerall = p2statetype != L && p2statetype != A
trigger1 = p2bodydist X <= 35
trigger1 = random < 500
value = ifelse((random < 250 && p2bodydist x <= 25),205,ifelse((random < 333 && p2bodydist x <= 25),235,ifelse(random < 500,400,430)))

; Combo Starter 2 (Strong Attacks)
[State -1, AI Combo Starter 2]
type = changestate
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
Triggerall = (ctrl || (stateno = 52 && animelemtime(1) > 0) || (stateno = [100, 101])) && statetype != A
triggerall = p2statetype != L && p2statetype != A
trigger1 = p2bodydist X <= 35
trigger1 = random < 900
value = ifelse(random < 500 && p2bodydist x <= 25, 245, ifelse(random < 500 && p2bodydist x <= 25, 215, ifelse(random < 500 && p2bodydist x <= 25, 210, 410)))

; Combo A
[State -1, AI Combo A]
type = changestate
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2statetype != A
triggerall = P2bodydist X <= 25
trigger1 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
trigger2 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499]) && random < 300
trigger3 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
value = 205

; Combo B
[State -1, AI Combo B]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2statetype != A
trigger1 = movecontact && stateno = 200 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
trigger2 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
trigger3 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499]) && random < 300
trigger4 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
value = 200

; Combo C
[State -1, AI Combo C]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2statetype != A
triggerall = P2bodydist X <= 25
trigger1 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
trigger2 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499]) && random < 300
trigger3 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
value = 235

; Combo D
[State -1, AI Combo D]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2statetype != A
trigger1 = movecontact && stateno = 200 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
trigger2 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
trigger3 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499]) && random < 300
trigger4 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
value = 400

; Combo E
[State -1, AI Combo E]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2statetype != A
trigger1 = movecontact && stateno = 200 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
trigger2 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
trigger3 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499]) && random < 300
trigger4 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499]) && random < 300
value = 430

; Combo F
[State -1, AI Combo F]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2statetype != A
trigger1 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0) && random < 500
trigger2 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 500
trigger3 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 500
trigger4 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0) && random < 500
value = ifelse(P2bodydist X <= 25 && random < 600, 720, 700)

; Combo G
[State -1, AI Combo G]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2statetype != A
triggerall = p2bodydist x <= 75
trigger1 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 800
trigger2 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0) && random < 800
trigger3 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0) && random < 800
trigger4 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 800
value = ifelse(p2bodydist x <= 17 && random < 300, 1300, ifelse(movehit && p2bodydist x <= 27 && random < 400, 1400, ifelse(p2bodydist x <= 50 && random < 500, 1500, 1000)))

; Combo H
[State -1, AI Combo H]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2statetype != A
triggerall = p2bodydist x <= 75
trigger1 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0) && random < 800
trigger2 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 800
trigger3 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 800
trigger4 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0) && random < 800
trigger5 = moveguarded && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0) && random < 800
trigger6 = movecontact && stateno = 710 && (animelemtime(2) < 0) && random < 800
trigger7 = moveguarded && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0) && random < 800
value = ifelse(p2bodydist x <= 17 && random < 200, 1300, ifelse(p2bodydist x <= 27 && random < 300, 1100, ifelse(movehit && P2bodydist x <= 27 && random < 500, 1400, ifelse(p2bodydist x <= 50 && random < 500, 1500, 1000))))

; Combo I
[State -1, AI Combo I]
type = ChangeState
triggerall = NumEnemy
triggerall = roundstate = 2 && var(0)
trigger1 = ctrl && numtarget(750) = 1 && (P2bodydist y = [-200,-185]) && random < 800
trigger2 = stateno = 720 && numtarget(750) = 1 && animtime = 0 && random < 800
value = ifelse(random < 700, 1500, ifelse(random < 100, 1400, 1000))

; Combo J
[State -1, AI Combo J]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2bodydist x < 50
triggerall = power >= 1000
triggerall = p2statetype != A
trigger1 = movehit && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0) && random < 100
trigger2 = movehit && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 100
trigger3 = movehit && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 100
trigger4 = movehit && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0) && random < 100
trigger5 = movehit && stateno = 710 && (animelemtime(2) < 0) && random < 100
trigger6 = movehit && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0) && random < 300
trigger7 = var(2) && movehit && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0) && random < 300
trigger8 = var(2) && movehit && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0) && random < 800
trigger9 = movehit && stateno = 1510 && (animelemtime(24) > 0 && animelemtime(25) <= 0) && random < 800
value = ifelse(random < 600, 3100, 3000)

; Combo K
[State -1, AI Combo K]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2bodydist x < 50
triggerall = power >= 2000
triggerall = p2statetype != A
trigger1 = movehit && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0) && random < 100
trigger2 = movehit && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 100
trigger3 = movehit && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0) && random < 100
trigger4 = movehit && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0) && random < 100
trigger5 = movehit && stateno = 710 && (animelemtime(2) < 0) && random < 100
trigger6 = movehit && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0) && random < 100
trigger7 = var(2) && movehit && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0) && random < 100
trigger8 = var(2) && movehit && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0) && random < 100
trigger9 = movehit && stateno = 1510 && (animelemtime(24) > 0 && animelemtime(25) <= 0) && random < 100
value = ifelse(random < 500, 3150, 3050)

; Combo L
[State -1, AI Combo L]
type = ChangeState
triggerall = NumEnemy
Triggerall = roundstate = 2 && Var(0)
triggerall = p2bodydist x <= 45
triggerall = power >= 3000
trigger1 = !var(2) && movehit && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0) && random < 100
trigger2 = var(2) && movehit && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)&& random < 100
trigger3 = movehit && stateno = 1510 && (animelemtime(26) > 0 && animelemtime(27) <= 0) && random < 100
trigger4 = movehit && stateno = 3100 && (animelemtime(37) > 0 && animelemtime(38) <= 0) && random < 800
value = 3800


;===========================================================================
; Skill Section
;===========================================================================
;----------------------------------------------------------------------------
; Kyo's Saishuu Kessen Ougi "Mu Shiki"
[State -1, Hyper Kyo's Saishuu Kessen Ougi "Mu Shiki"]
type = ChangeState
value = 3800
triggerall = !var(0)
triggerall = !var(30) && Command = "Kyo's Saishuu Kessen Ougi Mu Shiki" || var(30) && Command = "Kyo's Saishuu Kessen Ougi Mu Shiki alt"
triggerall = numhelper(3815) = 0
triggerall = power >= 3000  || life <= 300 && power >= 1000
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)
trigger16 = movecontact && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0)
trigger18 = var(2) && movecontact && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0)
trigger19 = var(2) && movecontact && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)
trigger20 = movecontact && stateno = 1510 && (animelemtime(10) >= 0 && animelemtime(27) <= 0)
trigger21 = movecontact && stateno = 3100 && (animelemtime(7) > 0 && animelemtime(10) <= 0)
trigger22 = movecontact && stateno = 3100 && (animelemtime(14) > 0 && animelemtime(17) <= 0)
trigger23 = movecontact && stateno = 3100 && (animelemtime(21) > 0 && animelemtime(24) <= 0)
trigger24 = movecontact && stateno = 3100 && (animelemtime(29) > 0 && animelemtime(32) <= 0)
trigger25 = movecontact && stateno = 3100 && (animelemtime(35) > 0 && animelemtime(36) <= 0)
trigger26 = movecontact && stateno = 3100 && (animelemtime(37) > 0 && animelemtime(38) <= 0)
trigger27 = stateno = 3200 && (animelemtime(8) > 0 && animelemtime(21) <= 0)

;----------------------------------------------------------------------------
; EX Yuki-Chan no Trap
[State -1,Hyper EX Yuki-Chan no Trap]
type = ChangeState
value = 3050
triggerall = !var(0)
triggerall = Command = "EX Yuki-Chan no Trap"
triggerall = power >= 2000
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)
trigger16 = movecontact && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0)
trigger18 = var(2) && movecontact && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0)
trigger19 = var(2) && movecontact && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)
trigger20 = movecontact && stateno = 1510 && (animelemtime(10) >= 0 && animelemtime(27) <= 0)

;----------------------------------------------------------------------------
; Yuki-Chan no Trap
[State -1,Hyper Yuki-Chan no Trap]
type = ChangeState
value = 3000
triggerall = !var(0)
triggerall = Command = "Yuki-Chan no Trap"
triggerall = power >= 1000
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)
trigger16 = movecontact && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0)
trigger18 = var(2) && movecontact && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0)
trigger19 = var(2) && movecontact && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)
trigger20 = movecontact && stateno = 1510 && (animelemtime(10) >= 0 && animelemtime(27) <= 0)

;----------------------------------------------------------------------------
; EX Naku Ko wa Tsuyoi
[State -1,Hyper EX Naku Ko wa Tsuyoi]
type = ChangeState
value = 3150
triggerall = !var(0)
triggerall = Command = "EX Naku Ko wa Tsuyoi"
triggerall = power >= 2000
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)
trigger16 = movecontact && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0)
trigger18 = var(2) && movecontact && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0)
trigger19 = var(2) && movecontact && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)
trigger20 = movecontact && stateno = 1510 && (animelemtime(10) >= 0 && animelemtime(27) <= 0)

;----------------------------------------------------------------------------
; Naku Ko wa Tsuyoi
[State -1, Hyper Naku Ko wa Tsuyoi]
type = ChangeState
value = 3100
triggerall = !var(0)
triggerall = Command = "Naku Ko wa Tsuyoi"
triggerall = power >= 1000
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)
trigger16 = movecontact && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0)
trigger18 = var(2) && movecontact && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0)
trigger19 = var(2) && movecontact && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)
trigger20 = movecontact && stateno = 1510 && (animelemtime(10) >= 0 && animelemtime(27) <= 0)

;----------------------------------------------------------------------------
; EX Ai no Kusanagi Dai Koushin!!
[State -1, Hyper EX Ai no Kusanagi Dai Koushin!!]
type = ChangeState
value = 3350
triggerall = !var(0)
triggerall = Command = "EX Ai no Kusanagi Dai Koushin!!"
triggerall = power >= 2000
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)
trigger16 = movecontact && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0)
trigger18 = var(2) && movecontact && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0)
trigger19 = var(2) && movecontact && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)
trigger20 = movecontact && stateno = 1510 && (animelemtime(10) >= 0 && animelemtime(27) <= 0)

;----------------------------------------------------------------------------
; Ai no Kusanagi Dai Koushin!!
[State -1, Hyper Ai no Kusanagi Dai Koushin!!]
type = ChangeState
value = 3300
triggerall = !var(0)
triggerall = Command = "Ai no Kusanagi Dai Koushin!!"
triggerall = power >= 1000
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)
trigger16 = movecontact && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0)
trigger18 = var(2) && movecontact && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0)
trigger19 = var(2) && movecontact && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)
trigger20 = movecontact && stateno = 1510 && (animelemtime(10) >= 0 && animelemtime(27) <= 0)

;----------------------------------------------------------------------------
; Yuki's Hamburger
[State -1, Hyper Yuki's Hamburger]
type = ChangeState
value = 3200
triggerall = !var(0)
triggerall = Command = "Yuki's Hamburger"
triggerall = power >= 1000
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)
trigger16 = movecontact && stateno = 1400 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 1400 && (animelemtime(12) >= 0 && animelemtime(13) <= 0)
trigger18 = var(2) && movecontact && stateno = 1400 && (animelemtime(18) >= 0 && animelemtime(19) <= 0)
trigger19 = var(2) && movecontact && stateno = 1400 && (animelemtime(24) >= 0 && animelemtime(25) <= 0)
trigger20 = movecontact && stateno = 1510 && (animelemtime(10) >= 0 && animelemtime(27) <= 0)

;----------------------------------------------------------------------------
; Valting Over
[State -1, Special Valting Over]
type = ChangeState
value = 1200
triggerall = !var(0)
triggerall = Command = "Valting Over"
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)

;----------------------------------------------------------------------------
; Sabaori 2000
[State -1, Special Sabaori 2000]
type = ChangeState
value = 1600
triggerall = !var(0)
triggerall = Command = "Sabaori 2000"
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)

;----------------------------------------------------------------------------
; Hyakuretsu Terekakushi
[State -1, Special Hyakuretsu Terekakushi]
type = ChangeState
value = 1500
triggerall = !var(0)
triggerall = Command = "Hyakuretsu Terekakushi_x" || command = "Hyakuretsu Terekakushi_y"
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = !movecontact && stateno = 200 && animelemtime(4) > 0
trigger6= !movecontact && stateno = 205 && animelemtime(4) > 0
trigger7 = !movecontact && stateno = 400 && animelemtime(3) > 0
trigger8 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger9 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger10 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger11 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger14 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger15 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger16 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger17 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger18 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)


;----------------------------------------------------------------------------
; Kaban Barrier!?
[State -1, Special Kaban Barrier!?]
type = ChangeState
value = 1300
triggerall = !var(0)
triggerall = Command = "Kaban Barrier!?"
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)

;----------------------------------------------------------------------------
; Yuki-Chan no Kaban no Nakami
[State -1, Special Yuki-Chan no Kaban no Nakami]
type = ChangeState
value = 1000
triggerall = !var(0)
triggerall = Command = "Yuki-Chan no Kaban no Nakami"
triggerall = numproj = 0
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)

;----------------------------------------------------------------------------
; Otome no Sakebi
[State -1, Special Otome no Sakebi]
type = ChangeState
value = 1100
triggerall = !var(0)
triggerall = Command = "Otome no Sakebi"
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)

;----------------------------------------------------------------------------
; Yuki-Chan Furimawasu
[State -1, Special Yuki-Chan Furimawasu]
type = ChangeState
value = 1400
triggerall = !var(0)
triggerall = Command = "Yuki-Chan Furimawasu"
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)
trigger14 = movecontact && stateno = 710 && (animelemtime(2) < 0)
trigger15 = movecontact && stateno = 720 && (animelemtime(9) >= 0 && animelemtime(10) <= 0)

;----------------------------------------------------------------------------
; Emergency Evade (Backwards)
[State -1, Emergency Evade (Backwards)]
type = ChangeState
value = 905
triggerall = !var(0)
triggerall = Command = "holdback" && command = "recovery" || Command = "holdback" && command ="z"
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;----------------------------------------------------------------------------
; Emergency Evade (Forwards)
[State -1, Emergency Evade (Forwards)]
type = ChangeState
value = 900
triggerall = !var(0)
triggerall = command = "recovery" || command ="z"
trigger1 = ctrl && statetype != A
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;----------------------------------------------------------------------------
; Quick Emergency Evade
[State -1, Quick Emergency Evade]
type = ChangeState
value = 900
triggerall = !var(0)
triggerall = power >= 1000
triggerall = command = "recovery" || command ="z"
trigger1 = ctrl && statetype != A
trigger2 = movecontact && stateno = 200 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger3 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger4 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger5 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 230 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger7 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger8 = movecontact && stateno = 240 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)


;----------------------------------------------------------------------------
; Guard Cancel Emergency Evade (Backwards)
[State -1, Guard Cancel Emergency Evade (Backwards)]
type = ChangeState
value = 905
triggerall = !var(0)
triggerall = Command = "holdback" && command = "recovery" || Command = "holdback" && command ="z"
triggerall = Power >= 1000 && StateType != A
trigger1 = (stateno = 150 || stateno = 152)

;----------------------------------------------------------------------------
; Guard Cancel Emergency Evade (Forwards)
[State -1, Guard Cancel Emergency Evade (Forwards)]
type = ChangeState
value = 900
triggerall = !var(0)
triggerall = command = "recovery" || command = "z"
triggerall = Power >= 1000 && StateType != A
trigger1 = (stateno = 150 || stateno = 152)

;----------------------------------------------------------------------------
; Blowback Attack
[State -1, Blowback Attack]
type = ChangeState
value = 910
triggerall = Command = "c" || var(30) && Command = "blowback"
triggerall = !var(0)
trigger1 = StateType != A && Ctrl = 1
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;----------------------------------------------------------------------------
; Guard Cancel Blowback Attack
[State -1, Guard Cancel Blowback Attack]
type = ChangeState
value = 915
triggerall = !var(0)
triggerall = Command = "c" || var(30) && Command = "blowback"
triggerall = Power >= 1000 && StateType != A
trigger1 = (stateno = 150 || stateno = 152)

;---------------------------------------------------------------------------
;Air Blowback Attack
[State -1, Air Blowback Attack]
type = ChangeState
value = 920
triggerall = command = "c" || var(30) && Command = "blowback"
trigger1 = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;Run Fwd
[State -1, Run Fwd]
type = ChangeState
value = 100
trigger1 = command = "FF"
trigger1 = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
;Run Back
[State -1, Run Back]
type = ChangeState
value = 105
trigger1 = command = "BB"
trigger1 = statetype = S
trigger1 = ctrl

;---------------------------------------------------------------------------
;Taunt
[State -1, Taunt]
type = ChangeState
value = 195
triggerall = command = "start"
trigger1 = statetype != A
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;---------------------------------------------------------------------------
;Throw
[State -1, Throw]
type = ChangeState
value = 800
triggerall = command = "y" || command = "b"
triggerall = statetype = S
triggerall = ctrl
triggerall = stateno != 100
trigger1 = command = "holdfwd" || command = "holdback"
trigger1 = p2bodydist X < 5
trigger1 = (p2statetype = S) || (p2statetype = C)
trigger1 = p2movetype != H

;---------------------------------------------------------------------------
; Yuki-Chan ga Koronda!?
[State -1, Yuki-Chan ga Koronda!?]
type = ChangeState
value = 700
triggerall = !var(0)
triggerall = command = "holdfwd" && command = "holddown" && command = "a"
trigger1 = StateType != A && Ctrl = 1
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)

;---------------------------------------------------------------------------
; Stylish 1
[State -1, Stylish 1]
type = ChangeState
value = 720
triggerall = !var(0)
triggerall = command = "holdfwd" && command = "holddown" && command = "y"
trigger1 = StateType != A && Ctrl = 1
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 12
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger6 = movecontact && stateno = 210 && (animelemtime(7) >= 0 && animelemtime(8) <= 0)
trigger7 = movecontact && stateno = 215 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger8 = movecontact && stateno = 235 && (animelemtime(5) >= 0 && animelemtime(6) <= 0)
trigger9 = movecontact && stateno = 245 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger10 = movecontact && stateno = 400 && (animelemtime(2) >= 0 && animelemtime(3) <= 0)
trigger11 = movecontact && stateno = 410 && (animelemtime(4) >= 0 && animelemtime(6) <= 0)
trigger12 = movecontact && stateno = 430 && (animelemtime(3) >= 0 && animelemtime(4) <= 0)
trigger13 = movecontact && stateno = 440 && (animelemtime(6) >= 0 && animelemtime(7) <= 0)

;---------------------------------------------------------------------------
;Stylish 2
[State -1, Stylish 2]
type = ChangeState
value = 730
triggerall = !var(0)
triggerall = command = "holddown" && command = "x"
trigger1 = statetype = A
trigger1 = ctrl

;----------------------------------------------------------------------------
;Stand Light Punch (close)
[State -1, Stand Light Punch (close)]
type = ChangeState
value = 205
triggerall = P2bodydist X <= 25
triggerall = command = "x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = !movecontact && stateno = 205 && animelemtime(4) > 0
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger6 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499])
trigger7 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499])

;----------------------------------------------------------------------------
;Stand Light Punch
[State -1, Stand Light Punch]
type = ChangeState
value = 200
triggerall = command = "x"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = !movecontact && stateno = 200 && animelemtime(4) > 0
trigger5 = movecontact && stateno = 200 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger6 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger7 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499])
trigger8 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499])


;---------------------------------------------------------------------------
;Stand Strong Punch (close)
[State -1, Stand Strong Punch (close)]
type = ChangeState
value = 215
triggerall = P2bodydist X <= 25
triggerall = command = "y"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;---------------------------------------------------------------------------
;Stand Strong Punch
[State -1, Stand Strong Punch]
type = ChangeState
value = 210
triggerall = command = "y"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;---------------------------------------------------------------------------
;---------------------------------------------------------------------------
;Stand Light Kick (close)
[State -1, Stand Light Kick (close)]
type = ChangeState
value = 235
triggerall = P2bodydist X <= 25
triggerall = command = "a"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger5 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499])
trigger6 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499])

;---------------------------------------------------------------------------
;Stand Light Kick
[State -1, Stand Light Kick]
type = ChangeState
value = 230
triggerall = command = "a"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = movecontact && stateno = 200 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger5 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger6 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499])
trigger7 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499])

;---------------------------------------------------------------------------
;Standing Strong Kick (close)
[State -1, Standing Strong Kick (close)]
type = ChangeState
value = 245
triggerall = P2bodydist X <= 25
triggerall = command = "b"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;---------------------------------------------------------------------------
;Standing Strong Kick
[State -1, Standing Strong Kick]
type = ChangeState
value = 240
triggerall = command = "b"
triggerall = command != "holddown"
trigger1 = statetype = S
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;---------------------------------------------------------------------------
;Crouching Light Punch
[State -1, Crouching Light Punch]
type = ChangeState
value = 400
triggerall = command = "x"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = !movecontact && stateno = 400 && animelemtime(3) > 0
trigger5 = movecontact && stateno = 200 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger6 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger7 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499])
trigger8 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499])

;---------------------------------------------------------------------------
;Crouching Strong Punch
[State -1, Crouching Strong Punch]
type = ChangeState
value = 410
triggerall = command = "y"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = stateno = 430 && (animelemtime(4) > 0 && animelemtime(5) < 0)

;---------------------------------------------------------------------------
;Crouching Light Kick
[State -1, Crouching Light Kick]
type = ChangeState
value = 430
triggerall = command = "a"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]
trigger4 = !movecontact && stateno = 430 && animelemtime(4) > 0
trigger5 = movecontact && stateno = 200 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger6 = movecontact && stateno = 205 && (animelemtime(3) >= 0) && (prevstateno != [200,499])
trigger7 = movecontact && stateno = 400 && (animelemtime(2) >= 0) && (prevstateno != [200,499])
trigger8 = movecontact && stateno = 430 && (animelemtime(3) >= 0) && (prevstateno != [200,499])

;---------------------------------------------------------------------------
;Crouching Strong Kick
[State -1, Crouching Strong Kick]
type = ChangeState
value = 440
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = C
trigger1 = ctrl
trigger2 = stateno = 52 && animelemtime(1) > 0
trigger3 = stateno = [100, 101]

;---------------------------------------------------------------------------
;Jump Light Punch
[State -1, Jump Light Punch]
type = ChangeState
value = 600
triggerall = command = "x"
trigger1 = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;---------------------------------------------------------------------------
;Jump Strong Punch
[State -1, Jump Strong Punch]
type = ChangeState
value = 610
triggerall = command = "y"
trigger1 = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;Jump Light Kick (neutral)
[State -1, Jump Light Kick (neutral)]
type = ChangeState
value = 635
triggerall = vel x = 0
triggerall = command = "a"
trigger1 = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;Jump Light Kick
[State -1, Jump Light Kick]
type = ChangeState
value = 630
triggerall = command = "a"
trigger1 = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;Jump Strong Kick (neutral)
[State -1, Jump Strong Kick (neutral)]
type = ChangeState
value = 645
triggerall = vel x = 0
triggerall = command = "b"
trigger1 = statetype = A
trigger1 = ctrl

;---------------------------------------------------------------------------
;Jump Strong Kick
[State -1, Jump Strong Kick]
type = ChangeState
value = 640
triggerall = vel x != 0
triggerall = command = "b"
trigger1 = statetype = A
trigger1 = ctrl



