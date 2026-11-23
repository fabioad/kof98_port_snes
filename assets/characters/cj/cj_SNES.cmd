; Native button fallbacks. Motion and six-button adaptations live in newroster.py.
[Command]
name = "FF"
command = F, F
time = 18

[Command]
name = "BB"
command = B, B
time = 18

[Command]
name = "ESQ_F"
command = /F, c
time = 14

[Command]
name = "ESQ_B"
command = /B, c
time = 14

[Command]
name = "ESQ_L"
command = c
time = 12

[Statedef -1]

[State -1, Forward roll]
type = ChangeState
value = 700
triggerall = command = "ESQ_F"
trigger1 = statetype = S
trigger1 = ctrl

[State -1, Back roll]
type = ChangeState
value = 710
triggerall = command = "ESQ_B"
trigger1 = statetype = S
trigger1 = ctrl

[State -1, Neutral dodge]
type = ChangeState
value = 720
triggerall = command = "ESQ_L"
triggerall = command != "holdfwd"
triggerall = command != "holdback"
trigger1 = statetype = S
trigger1 = ctrl

[State -1, Stand LP]
type = ChangeState
value = 200
triggerall = command = "x"
triggerall = command != "holddown"
trigger1 = statetype = S
[State -1, Stand HP]
type = ChangeState
value = 220
triggerall = command = "y"
triggerall = command != "holddown"
trigger1 = statetype = S
[State -1, Stand LK]
type = ChangeState
value = 230
triggerall = command = "a"
triggerall = command != "holddown"
trigger1 = statetype = S
[State -1, Stand HK]
type = ChangeState
value = 250
triggerall = command = "b"
triggerall = command != "holddown"
trigger1 = statetype = S

[State -1, Crouch LP]
type = ChangeState
value = 400
triggerall = command = "x"
triggerall = command = "holddown"
trigger1 = statetype = C
[State -1, Crouch HP]
type = ChangeState
value = 420
triggerall = command = "y"
triggerall = command = "holddown"
trigger1 = statetype = C
[State -1, Crouch LK]
type = ChangeState
value = 430
triggerall = command = "a"
triggerall = command = "holddown"
trigger1 = statetype = C
[State -1, Crouch HK]
type = ChangeState
value = 450
triggerall = command = "b"
triggerall = command = "holddown"
trigger1 = statetype = C

[State -1, Jump LP]
type = ChangeState
value = 600
triggerall = command = "x"
trigger1 = statetype = A
[State -1, Jump HP]
type = ChangeState
value = 620
triggerall = command = "y"
trigger1 = statetype = A
[State -1, Jump LK]
type = ChangeState
value = 630
triggerall = command = "a"
trigger1 = statetype = A
[State -1, Jump HK]
type = ChangeState
value = 650
triggerall = command = "b"
trigger1 = statetype = A
