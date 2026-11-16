# Heidern: agarrão/dreno do Final Bringer e fase 3120/3160 (16/11/2026)

## Sintoma

O **Final Bringer** dava o dano do salto, mas a cadeia `3020-3023` rodava
sozinha: o Heidern executava a animação inteira, a vítima não ficava presa e o
dreno não aplicava dano. O **Heidern End** (`3100/3110/3150`) parava no golpe
de abertura; as fases `3120/3125/3126` (e `3160/3161/3162` no MAX) não estavam
ligadas.

## Causa

- O `HitDef` de contato não apontava a vítima para o estado nativo de preso
  (`S_VHELD`, 76) nem redirecionava o atacante para a fase seguinte.
- O `ActTab` do 3022 tem 13 ticks; os eventos de dreno em 20-56 nunca
  chegavam a rodar.
- As fases `3120/3160` não tinham `sid`, e os tempos 132/133 do fonte não
  cabem no byte de tempo do `ActTab` (o motor só aceita `Time < 127`).
- O `Turn` no início do 3021 invertia o Heidern; como o bind é relativo à
  direção, a vítima era presa atrás dele.

## Correção

- `tools/build_fight.py`
  - `target_flags` no `TargetTab`: um acerto normal pode pedir sprites
    próprios da vítima (`F_GRAB` bit0) sem entrar no gate de agarrão.
  - `VICTIM_STATE_IDS` aceita explicitamente `76 -> 76` e `77 -> 77` para as
    linhas `ActTab op4` autoradas pelo port.
  - `hitdef_override` de `103/88/89/66`: `p2state = 76`,
    `p1mugen = 3020/3120/3160`, `fall = 0`, `target_flags = 1`.
  - `STRIKE_GRABS` em `remaining_specials.py`: os strikes achatados
    `3010/3050` também redirecionam para `3020` em vez de terminar no
    knockdown.
  - Sids `115/116` compilam `3120/3160` (anim 3120); bind fixo em `88,-88`.
  - 3022: `tail_ticks` 1311 = 110 (dreno em 8/20/32/44/56, -3 cada) e 3023
    -15 + `TargetState 77` (voo de arremesso).
  - 3120/3160: `-28` em `Time 64` e `Time 120`, arremesso em `Time 121`.
  - `act_drop` do `Turn` no estado 3021.

Dano final (escala do port, 200 HP): fraco 35, forte 42, MAX 50 no Final
Bringer; 84/84/102 no Heidern End.

## Verificação

`python3 tools/test_heidern_grabs_headless.py`:

```
PASS Final Bringer weak:  dmg=35  path=[85,103,104,105,106,107,0] vpath=[0,76,77]
PASS Final Bringer strong: dmg=42  path=[86,104,105,106,107,0]     vpath=[0,76,77]
PASS Final Bringer MAX:   dmg=50  path=[87,104,105,106,107,0]     vpath=[0,76,77]
PASS Heidern End weak:    dmg=84  path=[88,115,0]                 vpath=[0,76,77,10,18]
PASS Heidern End strong:  dmg=84  path=[89,115,0]                 vpath=[0,76,77,10,18]
PASS Heidern End MAX:     dmg=102 path=[66,116,0]                 vpath=[0,76,77,10,18]
```

Build `make -f Makefile.pvsnes verify`: OK, checksum **`$8F39`**.

## Limites

- A vítima usa a pose genérica de preso (76) em vez das animações custom
  `3030/3125`; o bind, o dreno e o arremesso são nativos.
- A cadeia inteira dura ~4,8 s (cinemática de agarrão); o 3022 mantém 110
  ticks de dreno, próximo dos 120 do fonte.
